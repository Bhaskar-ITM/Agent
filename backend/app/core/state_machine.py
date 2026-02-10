from app.state.scan_state import ScanState

VALID_TRANSITIONS = {
    ScanState.CREATED: [ScanState.QUEUED, ScanState.CANCELLED],
    ScanState.QUEUED: [ScanState.RUNNING, ScanState.CANCELLED, ScanState.FAILED],
    ScanState.RUNNING: [ScanState.COMPLETED, ScanState.FAILED, ScanState.CANCELLED],
    ScanState.COMPLETED: [],
    ScanState.FAILED: [],
    ScanState.CANCELLED: []
}

class InvalidStateTransition(Exception):
    pass

def transition(scan, next_state: ScanState):
    # Support string input
    if isinstance(next_state, str):
        next_state = ScanState(next_state)

    if next_state not in VALID_TRANSITIONS.get(scan.state, []):
        raise InvalidStateTransition(f"Cannot transition from {scan.state} to {next_state}")

    scan.state = next_state
