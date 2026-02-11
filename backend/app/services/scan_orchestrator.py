import uuid
from app.models.scan import Scan
from app.state.scan_state import ScanState

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
