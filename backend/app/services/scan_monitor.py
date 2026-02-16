import logging
from datetime import datetime
from app.state.scan_state import ScanState
from app.services.jenkins_service import jenkins_service
from app.core.state_machine import transition, InvalidStateTransition

logger = logging.getLogger(__name__)

def monitor_scans(scans_db):
    """
    Controlled Polling logic as per Phase 5.
    Iterates through scans in QUEUED or RUNNING states and updates them based on Jenkins status.
    """
    for scan_id, scan in scans_db.items():
        if scan.state not in [ScanState.QUEUED, ScanState.RUNNING]:
            continue

        try:
            status = jenkins_service.get_build_status(scan_id)
            building = status.get("building", False)
            result = status.get("result")

            # Rule: QUEUED -> RUNNING
            if scan.state == ScanState.QUEUED and building:
                logger.info(f"Scan {scan_id} detected as RUNNING")
                transition(scan, ScanState.RUNNING)
                scan.started_at = datetime.utcnow()

            # Rule: RUNNING -> COMPLETED / FAILED
            elif scan.state == ScanState.RUNNING and not building and result is not None:
                if result in ["SUCCESS", "UNSTABLE"]:
                    logger.info(f"Scan {scan_id} detected as COMPLETED (Result: {result})")
                    transition(scan, ScanState.COMPLETED)
                    scan.completed_at = datetime.utcnow()
                elif result in ["FAILURE", "ABORTED"]:
                    logger.info(f"Scan {scan_id} detected as FAILED (Result: {result})")
                    transition(scan, ScanState.FAILED)
                    scan.completed_at = datetime.utcnow()

            # Additional terminal detection if build stopped but result is null (unexpected)
            elif scan.state == ScanState.RUNNING and not building and result is None:
                 # In a real system we might wait a few cycles or check for crashes
                 # For now, we stay in RUNNING until a result is reported
                 pass

        except InvalidStateTransition as e:
            logger.error(f"Invalid state transition for scan {scan_id}: {e}")
        except Exception as e:
            logger.error(f"Error polling status for scan {scan_id}: {e}")
