from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
import hashlib
import json
import logging
from threading import RLock
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultsResponse
from app.services.validation import VALID_STAGES, validate_scan_request
from app.services.scan_orchestrator import create_scan_object
from app.api.projects import projects_db
from app.state.scan_state import ScanState

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for now
scans_db = {}
scans_db_lock = RLock()
TERMINAL_STATES = {ScanState.COMPLETED, ScanState.FAILED, ScanState.CANCELLED}
ACTIVE_STATES = {ScanState.CREATED, ScanState.QUEUED, ScanState.RUNNING}
MAX_SCAN_DURATION_HOURS = 2
MAX_ARTIFACT_URL_LENGTH = 2048
MAX_ARTIFACT_SIZE_BYTES = 50 * 1024 * 1024


def _json_digest(payload: dict) -> str:
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _validate_callback_artifacts(stages: list[dict]):
    for stage in stages:
        stage_name = stage.get("stage")
        if stage_name is not None and stage_name not in VALID_STAGES:
            raise HTTPException(status_code=400, detail=f"Invalid stage identifier: {stage_name}")

        artifact_url = stage.get("artifact_url")
        if artifact_url is not None:
            if not isinstance(artifact_url, str):
                raise HTTPException(status_code=400, detail="artifact_url must be a string")
            if len(artifact_url) > MAX_ARTIFACT_URL_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail="artifact_url exceeds maximum allowed length",
                )
            if not artifact_url.startswith(("http://", "https://", "/")):
                raise HTTPException(
                    status_code=400,
                    detail="artifact_url must be absolute HTTP(S) URL or absolute path",
                )

        artifact_size_bytes = stage.get("artifact_size_bytes")
        if artifact_size_bytes is not None:
            if not isinstance(artifact_size_bytes, int):
                raise HTTPException(status_code=400, detail="artifact_size_bytes must be an integer")
            if artifact_size_bytes < 0 or artifact_size_bytes > MAX_ARTIFACT_SIZE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail="artifact_size_bytes is out of allowed range",
                )

        artifact_sha256 = stage.get("artifact_sha256")
        if artifact_sha256 is not None:
            if not isinstance(artifact_sha256, str) or len(artifact_sha256) != 64:
                raise HTTPException(status_code=400, detail="artifact_sha256 must be a 64-char hex string")
            if any(c not in "0123456789abcdefABCDEF" for c in artifact_sha256):
                raise HTTPException(status_code=400, detail="artifact_sha256 must be hexadecimal")


def _expire_scan_if_timed_out(scan_obj):
    if scan_obj.state in TERMINAL_STATES:
        return

    now = datetime.utcnow()
    reference_time = scan_obj.started_at or scan_obj.created_at
    if now - reference_time > timedelta(hours=MAX_SCAN_DURATION_HOURS):
        scan_obj.state = ScanState.FAILED
        scan_obj.finished_at = now

        project = projects_db.get(scan_obj.project_id)
        if project:
            project["last_scan_state"] = scan_obj.state

        logger.warning(
            "Scan %s exceeded timeout window (%s hours) and was marked FAILED",
            scan_obj.scan_id,
            MAX_SCAN_DURATION_HOURS,
        )

@router.post("/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
def trigger_scan(scan: ScanCreate):
    # 1. Validate basic request
    try:
        validate_scan_request(scan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Validate project existence
    if scan.project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    with scans_db_lock:
        for existing_scan in scans_db.values():
            if existing_scan.project_id == scan.project_id and existing_scan.state in ACTIVE_STATES:
                raise HTTPException(
                    status_code=409,
                    detail="An active scan already exists for this project",
                )

        project = projects_db[scan.project_id]

        # 3. Create Scan Object (State = CREATED)
        scan_obj = create_scan_object(
            project_id=scan.project_id,
            scan_mode=scan.scan_mode,
            selected_stages=scan.selected_stages,
        )

        # Store in DB
        scans_db[scan_obj.scan_id] = scan_obj

        # Update last scan status for project
        project["last_scan_state"] = scan_obj.state

    return {
        "scan_id": scan_obj.scan_id,
        "project_id": scan_obj.project_id,
        "scan_mode": scan_obj.scan_mode,
        "state": scan_obj.state,
        "selected_stages": scan_obj.selected_stages,
        "created_at": scan_obj.created_at,
        "started_at": scan_obj.started_at,
        "finished_at": scan_obj.finished_at,
        "results": scan_obj.stage_results
    }

@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str):
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan_obj = scans_db[scan_id]
    _expire_scan_if_timed_out(scan_obj)
    return {
        "scan_id": scan_obj.scan_id,
        "project_id": scan_obj.project_id,
        "scan_mode": scan_obj.scan_mode,
        "state": scan_obj.state,
        "selected_stages": scan_obj.selected_stages,
        "created_at": scan_obj.created_at,
        "started_at": scan_obj.started_at,
        "finished_at": scan_obj.finished_at,
        "results": scan_obj.stage_results
    }

@router.get("/scans/{scan_id}/results", response_model=ScanResultsResponse)
def get_scan_results(scan_id: str):
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan_obj = scans_db[scan_id]
    _expire_scan_if_timed_out(scan_obj)

    # Map stored results to schema
    return {
        "scan_id": scan_obj.scan_id,
        "results": scan_obj.stage_results
    }

@router.post("/scans/{scan_id}/callback")
def scan_callback(scan_id: str, report: dict):
    with scans_db_lock:
        if scan_id not in scans_db:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan_obj = scans_db[scan_id]
        _expire_scan_if_timed_out(scan_obj)

        callback_digest = _json_digest(report)
        if callback_digest in scan_obj.callback_digests:
            return {"status": "success", "idempotent": True}

        if scan_obj.state in TERMINAL_STATES:
            logger.info("Ignoring callback for terminal scan %s", scan_id)
            scan_obj.callback_digests.add(callback_digest)
            return {"status": "success", "idempotent": True}

        stages = report.get("stages", [])
        if not isinstance(stages, list):
            raise HTTPException(status_code=400, detail="stages must be a list")
        _validate_callback_artifacts(stages)

        # Update stage results
        scan_obj.stage_results = stages

        # Update state based on Jenkins result
        jenkins_status = report.get("status")
        if jenkins_status == "SUCCESS":
            scan_obj.state = ScanState.COMPLETED
        elif jenkins_status in ["FAILURE", "ABORTED", "UNSTABLE"]:
            scan_obj.state = ScanState.FAILED
        else:
            raise HTTPException(status_code=400, detail="Invalid callback status")

        build_number = report.get("build_number")
        if build_number is not None:
            scan_obj.jenkins_build_number = str(build_number)

        queue_id = report.get("queue_id")
        if queue_id is not None:
            scan_obj.jenkins_queue_id = str(queue_id)

        # Keep project dashboard state in sync with scan terminal state.
        terminal_states = {ScanState.COMPLETED, ScanState.FAILED}
        if scan_obj.state in terminal_states:
            project = projects_db.get(scan_obj.project_id)
            if project:
                project["last_scan_state"] = scan_obj.state
                logger.info(
                    "Updated project %s last_scan_state to %s",
                    scan_obj.project_id,
                    scan_obj.state,
                )
            else:
                logger.warning(
                    "Project %s not found while syncing callback state %s",
                    scan_obj.project_id,
                    scan_obj.state,
                )

        # finishedAt
        finished_at_str = report.get("finishedAt")
        if finished_at_str:
            try:
                scan_obj.finished_at = datetime.fromisoformat(finished_at_str.replace('Z', '+00:00'))
            except:
                pass

        scan_obj.callback_digests.add(callback_digest)

    return {"status": "success"}
