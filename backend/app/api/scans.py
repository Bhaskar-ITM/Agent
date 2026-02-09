from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas.scan import ScanCreate, ScanResponse
from app.services.validation import validate_scan_request, validate_manual_targets
from app.services.scan_orchestrator import create_scan_object, orchestrate_scan
from app.api.projects import projects_db

router = APIRouter()

# In-memory storage for now
scans_db = {}

@router.post("/scans", response_model=ScanResponse)
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

    # 3. Mode-specific validation
    if scan.mode == "MANUAL":
        try:
            validate_manual_targets(
                scan.selected_stages,
                project.get("target_ip"),
                project.get("target_url")
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 4. Create Scan Object
    scan_obj = create_scan_object(
        project_id=scan.project_id,
        mode=scan.mode,
        selected_stages=scan.selected_stages,
    )

    # 5. Orchestrate (Handshake with Jenkins)
    success = orchestrate_scan(scan_obj, project)
    if not success:
        scans_db[scan_obj.scan_id] = scan_obj
        raise HTTPException(status_code=500, detail="Failed to trigger scan in Jenkins")

    # Store in DB
    scans_db[scan_obj.scan_id] = scan_obj

    return scan_obj.__dict__

@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str):
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scans_db[scan_id].__dict__

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

    # finishedAt
    finished_at_str = report.get("finishedAt")
    if finished_at_str:
        try:
            scan_obj.finished_at = datetime.fromisoformat(finished_at_str.replace('Z', '+00:00'))
        except:
            pass

    return {"status": "success"}
