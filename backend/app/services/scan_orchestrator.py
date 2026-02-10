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

    # Explicitly start in CREATED
    scan.state = ScanState.CREATED
    return scan

def orchestrate_scan(scan: Scan, project_data: dict):
    """
    Transitions to QUEUED, triggers Jenkins, and keeps the scan in QUEUED state.
    The scan will transition to RUNNING when Jenkins calls back 'STARTED'.
    """
    from app.core.state_machine import transition

    # 1. Transition to QUEUED
    transition(scan, ScanState.QUEUED)

    # 2. Trigger Jenkins
    success = jenkins_service.trigger_scan_job(scan, project_data)

    if success:
        # Keep state as QUEUED as per "Queue-Only" pattern
        return True

    scan.state = ScanState.FAILED
    return False
