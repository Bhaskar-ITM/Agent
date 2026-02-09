import uuid
from app.models.scan import Scan
from app.state.scan_state import ScanState
from app.services.jenkins_service import jenkins_service
from datetime import datetime

def create_scan_object(project_id: str, mode: str, selected_stages: list[str] | None):
    scan_id = str(uuid.uuid4())

    scan = Scan(
        scan_id=scan_id,
        project_id=project_id,
        mode=mode,
        selected_stages=selected_stages,
    )

    scan.state = ScanState.QUEUED
    return scan

def orchestrate_scan(scan: Scan, project_data: dict):
    """
    Handles the transition from QUEUED to RUNNING by triggering Jenkins.
    """
    success = jenkins_service.trigger_scan_job(scan, project_data)

    if success:
        scan.state = ScanState.RUNNING
        scan.started_at = datetime.utcnow()
        return True

    scan.state = ScanState.FAILED
    return False
