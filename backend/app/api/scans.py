from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import logging
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultsResponse
from app.services.validation import validate_scan_request
from app.services.scan_orchestrator import create_scan_object
from app.api.projects import projects_db

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for now
scans_db = {}

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
        "created_at": scan_obj.created_at
    }

@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str):
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan_obj = scans_db[scan_id]
    return {
        "scan_id": scan_obj.scan_id,
        "project_id": scan_obj.project_id,
        "scan_mode": scan_obj.scan_mode,
        "state": scan_obj.state,
        "selected_stages": scan_obj.selected_stages,
        "created_at": scan_obj.created_at
    }

@router.get("/scans/{scan_id}/results", response_model=ScanResultsResponse)
def get_scan_results(scan_id: str):
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan_obj = scans_db[scan_id]

    # Map stored results to schema
    return {
        "scan_id": scan_obj.scan_id,
        "results": scan_obj.stage_results
    }

@router.post("/scans/{scan_id}/callback")
def scan_callback(scan_id: str, report: dict):
    from app.state.scan_state import ScanState

    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_obj = scans_db[scan_id]

    # Update stage results
    scan_obj.stage_results = report.get("stages", [])

    # Update state based on Jenkins result
    jenkins_status = report.get("status")
    if jenkins_status == "SUCCESS":
        scan_obj.state = ScanState.COMPLETED
    elif jenkins_status in ["FAILURE", "ABORTED", "UNSTABLE"]:
        scan_obj.state = ScanState.FAILED

    if scan_obj.state in [ScanState.COMPLETED, ScanState.FAILED]:
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

    return {"status": "success"}
