from app.state.scan_state import ScanState
from datetime import datetime
import secrets

class Scan:
    def __init__(
        self,
        scan_id: str,
        project_id: str,
        mode: str,  # AUTOMATED | MANUAL
        selected_stages: list[str] | None,
        state: ScanState = ScanState.CREATED,
    ):
        self.scan_id = scan_id
        self.project_id = project_id
        self.mode = mode
        self.selected_stages = selected_stages or []
        self.state = state
        self.callback_token = secrets.token_urlsafe(32)
        self.payload_checksum = None
        self.stage_gating = {}
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.finished_at = None
        self.stage_results = []
