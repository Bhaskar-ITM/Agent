from datetime import datetime, timedelta
import hashlib
import json
import logging

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import settings
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultsResponse
from app.services.jenkins_service import jenkins_service
from app.services.scan_orchestrator import create_scan_object
from app.services.validation import VALID_STAGES, validate_scan_request
from app.state.persistence import persist_state
from app.state.scan_state import ScanState
from app.state.store import projects_db, scans_db, scans_db_lock

router = APIRouter()
logger = logging.getLogger(__name__)

TERMINAL_STATES = {ScanState.COMPLETED, ScanState.FAILED, ScanState.CANCELLED}
ACTIVE_STATES = {ScanState.CREATED, ScanState.QUEUED, ScanState.RUNNING}
MAX_ARTIFACT_URL_LENGTH = 2048
MAX_ARTIFACT_SIZE_BYTES = 50 * 1024 * 1024

JENKINS_STAGE_NAME_TO_ID = {
    "Git Checkout": "git_checkout",
    "Sonar Scanner": "sonar_scanner",
    "Sonar Quality Gate": "sonar_quality_gate",
    "NPM / PIP Install": "npm_pip_install",
    "Dependency Check": "dependency_check",
    "Trivy FS Scan": "trivy_fs_scan",
    "Docker Build": "docker_build",
    "Docker Push": "docker_push",
    "Trivy Image Scan": "trivy_image_scan",
    "Nmap Scan": "nmap_scan",
    "ZAP Scan": "zap_scan",
}

STAGE_STATUS_MAP = {
    "PASSED": "PASS",
    "FAILED": "FAIL",
    "SUCCESS": "PASS",
    "FAILURE": "FAIL",
    "SKIPPED": "SKIPPED",
    "WARN": "WARN",
    "UNSTABLE": "WARN",
}


def _json_digest(payload: dict) -> str:
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _validate_callback_auth(callback_token: str | None):
    if settings.ENV == "test":
        return
    expected = settings.CALLBACK_TOKEN.strip()
    if callback_token != expected:
        raise HTTPException(status_code=401, detail="Invalid callback token")


def _normalize_stage(stage: dict) -> dict:
    stage_id = stage.get("stage")
    if stage_id is None:
        stage_id = JENKINS_STAGE_NAME_TO_ID.get(stage.get("name"))
    if stage_id not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage identifier: {stage_id}")

    normalized_status = STAGE_STATUS_MAP.get(str(stage.get("status", "")).upper())
    if normalized_status is None:
        raise HTTPException(status_code=400, detail=f"Invalid stage status: {stage.get('status')}")

    return {
        "stage": stage_id,
        "status": normalized_status,
        "summary": stage.get("summary") or stage.get("details"),
        "artifact_url": stage.get("artifact_url") or stage.get("reportUrl"),
        "artifact_size_bytes": stage.get("artifact_size_bytes"),
        "artifact_sha256": stage.get("artifact_sha256"),
    }


def _validate_callback_artifacts(stages: list[dict]):
    for stage in stages:
        artifact_url = stage.get("artifact_url")
        if artifact_url is not None:
            if not isinstance(artifact_url, str):
                raise HTTPException(status_code=400, detail="artifact_url must be a string")
            if len(artifact_url) > MAX_ARTIFACT_URL_LENGTH:
                raise HTTPException(status_code=400, detail="artifact_url exceeds maximum allowed length")
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
                raise HTTPException(status_code=400, detail="artifact_size_bytes is out of allowed range")

        artifact_sha256 = stage.get("artifact_sha256")
        if artifact_sha256 is not None:
            if not isinstance(artifact_sha256, str) or len(artifact_sha256) != 64:
                raise HTTPException(status_code=400, detail="artifact_sha256 must be a 64-char hex string")
            if any(c not in "0123456789abcdefABCDEF" for c in artifact_sha256):
                raise HTTPException(status_code=400, detail="artifact_sha256 must be hexadecimal")


def _expire_scan_if_timed_out(scan_obj, now=None, timeout_seconds=None):
    # Performance Optimization (Bolt ⚡): Accepts pre-calculated 'now' and 'timeout_seconds'
    # to avoid redundant datetime.utcnow() and setting lookups during bulk processing.
    if scan_obj.state in TERMINAL_STATES:
        return False

    if now is None:
        now = datetime.utcnow()
    if timeout_seconds is None:
        timeout_seconds = settings.SCAN_TIMEOUT

    reference_time = scan_obj.started_at or scan_obj.created_at
    if now - reference_time > timedelta(seconds=timeout_seconds):
        scan_obj.state = ScanState.FAILED
        scan_obj.finished_at = now

        project = projects_db.get(scan_obj.project_id)
        if project:
            project["last_scan_state"] = scan_obj.state

        logger.warning("Scan %s exceeded timeout (%s sec) and was marked FAILED", scan_obj.scan_id, timeout_seconds)
        return True
    return False


def _scan_to_response(scan_obj):
    return {
        "scan_id": scan_obj.scan_id,
        "project_id": scan_obj.project_id,
        "scan_mode": scan_obj.scan_mode,
        "state": scan_obj.state,
        "selected_stages": scan_obj.selected_stages,
        "created_at": scan_obj.created_at,
        "started_at": scan_obj.started_at,
        "finished_at": scan_obj.finished_at,
        "results": scan_obj.stage_results,
    }




@router.get("/scans", response_model=list[ScanResponse])
def list_scans():
    with scans_db_lock:
        # Performance Optimization (Bolt ⚡): Pre-calculating values and batching persistence.
        # Prevents O(N) disk writes by persisting once after checking all scans.
        now = datetime.utcnow()
        timeout_seconds = settings.SCAN_TIMEOUT
        mutated = False
        for scan_obj in scans_db.values():
            if _expire_scan_if_timed_out(scan_obj, now=now, timeout_seconds=timeout_seconds):
                mutated = True
        if mutated:
            persist_state(scans_db, projects_db)
        return [_scan_to_response(s) for s in scans_db.values()]


@router.post("/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
def trigger_scan(scan: ScanCreate):
    try:
        validate_scan_request(scan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    with scans_db_lock:
        project = projects_db[scan.project_id]

        # Performance Optimization (Bolt ⚡): O(1) lookup of active scan state via project metadata.
        # Previously, this was an O(N) linear search over the entire scans_db, which degraded as history grew.
        if project.get("last_scan_state") in ACTIVE_STATES:
            raise HTTPException(
                status_code=409,
                detail="An active scan already exists for this project",
            )
        scan_obj = create_scan_object(
            project_id=scan.project_id,
            scan_mode=scan.scan_mode,
            selected_stages=scan.selected_stages,
        )

        scan_obj.state = ScanState.QUEUED
        scans_db[scan_obj.scan_id] = scan_obj
        project["last_scan_state"] = scan_obj.state
        persist_state(scans_db, projects_db)

    accepted, queue_id = jenkins_service.trigger_scan_job(scan_obj, project)

    with scans_db_lock:
        if not accepted:
            scan_obj.state = ScanState.FAILED
            scan_obj.finished_at = datetime.utcnow()
            project["last_scan_state"] = scan_obj.state
        else:
            scan_obj.state = ScanState.RUNNING
            scan_obj.started_at = datetime.utcnow()
            if queue_id is not None:
                scan_obj.jenkins_queue_id = str(queue_id)
            project["last_scan_state"] = scan_obj.state

        persist_state(scans_db, projects_db)

    return _scan_to_response(scan_obj)


@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str):
    with scans_db_lock:
        if scan_id not in scans_db:
            raise HTTPException(status_code=404, detail="Scan not found")
        scan_obj = scans_db[scan_id]
        if _expire_scan_if_timed_out(scan_obj):
            persist_state(scans_db, projects_db)
        return _scan_to_response(scan_obj)


@router.get("/scans/{scan_id}/results", response_model=ScanResultsResponse)
def get_scan_results(scan_id: str):
    with scans_db_lock:
        if scan_id not in scans_db:
            raise HTTPException(status_code=404, detail="Scan not found")
        scan_obj = scans_db[scan_id]
        if _expire_scan_if_timed_out(scan_obj):
            persist_state(scans_db, projects_db)

        return {
            "scan_id": scan_obj.scan_id,
            "results": scan_obj.stage_results,
        }


@router.get("/scans/{scan_id}/overview")
def get_scan_overview(scan_id: str):
    with scans_db_lock:
        if scan_id not in scans_db:
            raise HTTPException(status_code=404, detail="Scan not found")
        scan_obj = scans_db[scan_id]
        if _expire_scan_if_timed_out(scan_obj):
            persist_state(scans_db, projects_db)
        return {
            "scan_id": scan_obj.scan_id,
            "project_id": scan_obj.project_id,
            "scan_mode": scan_obj.scan_mode,
            "state": scan_obj.state,
            "created_at": scan_obj.created_at,
            "started_at": scan_obj.started_at,
            "finished_at": scan_obj.finished_at,
            "results": scan_obj.stage_results,
        }


@router.post("/scans/{scan_id}/callback")
def scan_callback(
    scan_id: str,
    report: dict,
    x_callback_token: str | None = Header(default=None, alias="X-Callback-Token"),
):
    _validate_callback_auth(x_callback_token)

    with scans_db_lock:
        if scan_id not in scans_db:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan_obj = scans_db[scan_id]
        if _expire_scan_if_timed_out(scan_obj):
            persist_state(scans_db, projects_db)

        callback_digest = _json_digest(report)
        if callback_digest in scan_obj.callback_digests:
            return {"status": "success", "idempotent": True}

        if scan_obj.state in TERMINAL_STATES:
            logger.info("Ignoring callback for terminal scan %s", scan_id)
            scan_obj.callback_digests.add(callback_digest)
            persist_state(scans_db, projects_db)
            return {"status": "success", "idempotent": True}

        stages = report.get("stages", [])
        if not isinstance(stages, list):
            raise HTTPException(status_code=400, detail="stages must be a list")

        normalized_stages = [_normalize_stage(stage) for stage in stages]
        _validate_callback_artifacts(normalized_stages)
        scan_obj.stage_results = normalized_stages

        jenkins_status = str(report.get("status", "")).upper()
        if jenkins_status == "SUCCESS":
            scan_obj.state = ScanState.COMPLETED
        elif jenkins_status in {"FAILURE", "ABORTED", "UNSTABLE"}:
            scan_obj.state = ScanState.FAILED
        else:
            raise HTTPException(status_code=400, detail="Invalid callback status")

        build_number = report.get("build_number")
        if build_number is None:
            build_number = report.get("buildNumber")
        if build_number is not None:
            scan_obj.jenkins_build_number = str(build_number)

        queue_id = report.get("queue_id")
        if queue_id is None:
            queue_id = report.get("queueId")
        if queue_id is not None:
            scan_obj.jenkins_queue_id = str(queue_id)

        project = projects_db.get(scan_obj.project_id)
        if project:
            project["last_scan_state"] = scan_obj.state

        finished_at_str = report.get("finishedAt")
        if finished_at_str:
            try:
                scan_obj.finished_at = datetime.fromisoformat(finished_at_str.replace("Z", "+00:00"))
            except ValueError:
                scan_obj.finished_at = datetime.utcnow()
        elif scan_obj.state in TERMINAL_STATES:
            scan_obj.finished_at = datetime.utcnow()

        scan_obj.callback_digests.add(callback_digest)
        persist_state(scans_db, projects_db)

    return {"status": "success"}
