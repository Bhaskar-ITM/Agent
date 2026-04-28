"""Scan management endpoints - reset, cancel, force-unlock."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.scans.constants import TERMINAL_STATES
from app.api.scans.helpers import scan_to_response
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.db_models import ScanDB, ProjectDB, MAX_RETRY_COUNT
from app.schemas.scan import ScanCancelResponse
from app.state.scan_state import ScanState
from app.websockets.manager import manager as websocket_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/scans/{scan_id}/reset", response_model=ScanCancelResponse)
@limiter.limit("10/minute")
def reset_scan(
    scan_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Reset a stuck or failed scan to allow re-running.

    This endpoint:
    - Resets scan state to CREATED
    - Clears error messages
    - Increments retry_count (max MAX_RETRY_COUNT)
    - Allows new scan to be triggered
    - Does NOT update project.last_scan_state (dashboard will show no active scan)
    """
    # Find scan
    scan_obj = db.query(ScanDB).filter(ScanDB.scan_id == scan_id).first()
    if not scan_obj:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Find project
    project_obj = db.query(ProjectDB).filter(ProjectDB.project_id == scan_obj.project_id).first()
    if not project_obj:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check retry limit
    current_retry_count = scan_obj.retry_count or 0
    if current_retry_count >= MAX_RETRY_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum retry count ({MAX_RETRY_COUNT}) reached. Cannot reset scan."
        )

    # Reset scan state
    scan_obj.state = ScanState.CREATED
    scan_obj.retry_count = current_retry_count + 1
    scan_obj.started_at = None
    scan_obj.finished_at = None
    scan_obj.error_message = None
    scan_obj.error_type = None
    scan_obj.jenkins_console_url = None
    scan_obj.stage_results = []
    scan_obj.callback_digests = []

    # Note: We do NOT update project_obj.last_scan_state here
    # This allows the dashboard to correctly show "no active scan" after reset
    # The project state will be updated when a new scan is triggered

    db.commit()
    db.refresh(scan_obj)

    # Broadcast reset update (Phase 3.1)
    background_tasks.add_task(
        websocket_manager.send_scan_update,
        scan_id=scan_obj.scan_id,
        project_id=scan_obj.project_id,
        data=scan_to_response(scan_obj)
    )

    logger.info(f"Scan {scan_id} reset successfully (retry count: {scan_obj.retry_count}/{MAX_RETRY_COUNT})")

    return scan_to_response(scan_obj)


@router.post("/scans/{scan_id}/cancel", response_model=ScanCancelResponse)
@limiter.limit("10/minute")
def cancel_scan(
    scan_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Cancel a running scan.

    This endpoint:
    - Marks scan as CANCELLED
    - Updates project's last_scan_state
    - Note: Does NOT cancel Jenkins job (would need Jenkins integration)
    """
    # Find scan
    scan_obj = db.query(ScanDB).filter(ScanDB.scan_id == scan_id).first()
    if not scan_obj:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Check if scan can be cancelled
    if scan_obj.state in TERMINAL_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel scan in {scan_obj.state.value} state"
        )

    # Cancel scan
    scan_obj.state = ScanState.CANCELLED
    scan_obj.finished_at = datetime.now(timezone.utc)
    scan_obj.error_message = "Cancelled by user"
    scan_obj.error_type = "USER_CANCELLED"

    # Update project state
    project_obj = db.query(ProjectDB).filter(ProjectDB.project_id == scan_obj.project_id).first()
    if project_obj:
        project_obj.last_scan_state = ScanState.CANCELLED.value

    db.commit()

    # Broadcast cancellation update (Phase 3.1)
    background_tasks.add_task(
        websocket_manager.send_scan_update,
        scan_id=scan_obj.scan_id,
        project_id=scan_obj.project_id,
        data=scan_to_response(scan_obj)
    )

    logger.info(f"Scan {scan_id} cancelled")

    return ScanCancelResponse(
        status="success",
        message=f"Scan {scan_id} cancelled successfully",
        scan_id=scan_id
    )


@router.post("/scans/{scan_id}/force-unlock")
@limiter.limit("10/minute")
def force_unlock_scan(
    scan_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Admin endpoint to force-unlock a stuck scan.

    This endpoint:
    - Marks scan as FAILED with ADMIN_RECOVERY error type
    - Updates project's last_scan_state to FAILED
    - Allows new scan to be triggered for the project

    Note: In test mode, authentication is bypassed. In production,
    this endpoint requires admin privileges.
    """
    # Find scan
    scan_obj = db.query(ScanDB).filter(ScanDB.scan_id == scan_id).first()
    if not scan_obj:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Check if scan is in an active state (can only unlock active scans)
    if scan_obj.state in TERMINAL_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot unlock scan in {scan_obj.state.value} state (already in terminal state)"
        )

    # Force-unlock the scan
    scan_obj.state = ScanState.FAILED
    scan_obj.finished_at = datetime.now(timezone.utc)
    scan_obj.error_message = "Scan unlocked by administrator"
    scan_obj.error_type = "ADMIN_RECOVERY"

    # Update project state
    project_obj = db.query(ProjectDB).filter(ProjectDB.project_id == scan_obj.project_id).first()
    if project_obj:
        project_obj.last_scan_state = ScanState.FAILED.value

    db.commit()

    # Broadcast unlock update
    background_tasks.add_task(
        websocket_manager.send_scan_update,
        scan_id=scan_obj.scan_id,
        project_id=scan_obj.project_id,
        data=scan_to_response(scan_obj)
    )

    logger.info(f"Scan {scan_id} force-unlocked by administrator")

    return {
        "status": "success",
        "message": f"Scan {scan_id} unlocked successfully",
        "scan_id": scan_id
    }
