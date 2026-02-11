from fastapi import APIRouter, HTTPException, Header
from datetime import datetime
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultsResponse
from app.services.validation import validate_scan_request
from app.services.scan_orchestrator import create_scan_object
from app.api.projects import projects_db
from app.core.state_machine import transition, InvalidStateTransition

router = APIRouter()

# In-memory storage for now
scans_db = {}

@router.post("/scans", response_model=ScanResponse)
def trigger_scan(scan: ScanCreate):
    # 1. Validate project existence first
    if scan.project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    project = projects_db[scan.project_id]

    # 2. Validate request using policy
    try:
        validate_scan_request(scan, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Create Scan Object
    scan_obj = create_scan_object(
        project_id=scan.project_id,
        mode=scan.mode,
        selected_stages=scan.selected_stages,
    )

    # Store in DB
    scans_db[scan_obj.scan_id] = scan_obj

    # Update last scan status for project
    project["last_scan_state"] = scan_obj.state

    return {
        "scan_id": scan_obj.scan_id,
        "project_id": scan_obj.project_id,
        "state": scan_obj.state,
        "started_at": scan_obj.started_at
    }

@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str):
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan_obj = scans_db[scan_id]
    return {
        "scan_id": scan_obj.scan_id,
        "project_id": scan_obj.project_id,
        "state": scan_obj.state,
        "started_at": scan_obj.started_at
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

@router.post("/scans/{scan_id}/queue")
def queue_scan(scan_id: str):
    from app.state.scan_state import ScanState
    from app.services.jenkins_service import jenkins_service
    from app.core.handshake import build_jenkins_payload, calculate_checksum

    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_obj = scans_db[scan_id]

    # Idempotency: If already QUEUED or beyond, return success
    if scan_obj.state != ScanState.CREATED:
        if scan_obj.state in [ScanState.QUEUED, ScanState.RUNNING, ScanState.COMPLETED]:
            return {"status": "success", "state": scan_obj.state}
        raise HTTPException(status_code=409, detail=f"Cannot queue scan in {scan_obj.state} state")

    project = projects_db.get(scan_obj.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Prepare Payload and Checksum
    payload = build_jenkins_payload(scan_obj, project)
    checksum = calculate_checksum(payload)
    scan_obj.payload_checksum = checksum

    # 2. Transition State (Atomic-ish in memory)
    try:
        transition(scan_obj, ScanState.QUEUED)
    except InvalidStateTransition as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Trigger Jenkins
    success = jenkins_service.trigger_scan_job(scan_obj, project)

    if success:
        # Update last scan status for project
        project["last_scan_state"] = scan_obj.state
        return {"status": "success", "state": scan_obj.state}
    else:
        # Rollback
        scan_obj.state = ScanState.CREATED
        scan_obj.payload_checksum = None
        raise HTTPException(status_code=500, detail="Failed to trigger Jenkins job")

@router.post("/scans/{scan_id}/started")
def scan_started(scan_id: str, x_callback_token: str = Header(None)):
    from app.state.scan_state import ScanState
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_obj = scans_db[scan_id]

    # Verify token
    if x_callback_token != scan_obj.callback_token:
        raise HTTPException(status_code=403, detail="Invalid callback token")

    try:
        transition(scan_obj, ScanState.RUNNING)
        scan_obj.started_at = datetime.now()
    except InvalidStateTransition as e:
        # If it's already running, it's fine (idempotency)
        if scan_obj.state != ScanState.RUNNING:
            raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success"}

@router.post("/scans/{scan_id}/callback")
def scan_callback(scan_id: str, report: dict, x_callback_token: str = Header(None)):
    from app.state.scan_state import ScanState

    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_obj = scans_db[scan_id]

    # Verify token
    if x_callback_token != scan_obj.callback_token:
        raise HTTPException(status_code=403, detail="Invalid callback token")


    # Update stage results
    scan_obj.stage_results = report.get("stages", [])

    # Update state based on Jenkins result
    jenkins_status = report.get("status")
    next_state = None
    if jenkins_status == "SUCCESS":
        next_state = ScanState.COMPLETED
    elif jenkins_status in ["FAILURE", "ABORTED", "UNSTABLE"]:
        next_state = ScanState.FAILED

    if next_state:
        try:
            transition(scan_obj, next_state)
        except InvalidStateTransition as e:
            raise HTTPException(status_code=400, detail=str(e))

    # finishedAt
    finished_at_str = report.get("finishedAt")
    if finished_at_str:
        try:
            scan_obj.finished_at = datetime.fromisoformat(finished_at_str.replace('Z', '+00:00'))
        except:
            pass

    return {"status": "success"}
