"""Project scan history endpoint."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.db_models import ScanDB, ProjectDB
from app.schemas.scan import ScanHistoryResponse, ScanError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/projects/{project_id}/scans", response_model=List[ScanHistoryResponse])
@limiter.limit("30/minute")
def get_project_scan_history(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """
    Get scan history for a project.

    Returns list of all scans for the project with:
    - Scan ID and state
    - Timestamps
    - Error details (if failed)
    - Retry count
    """
    # Verify project exists
    project_obj = db.query(ProjectDB).filter(ProjectDB.project_id == project_id).first()
    if not project_obj:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get scans ordered by created_at descending (newest first)
    scans = db.query(ScanDB).filter(
        ScanDB.project_id == project_id
    ).order_by(ScanDB.created_at.desc()).offset(offset).limit(limit).all()

    # Convert to response format
    history = []
    for scan_obj in scans:
        error = None
        if scan_obj.error_message:
            error = ScanError(
                message=scan_obj.error_message,
                error_type=scan_obj.error_type,
                jenkins_console_url=scan_obj.jenkins_console_url
            )

        history.append(ScanHistoryResponse(
            scan_id=scan_obj.scan_id,
            state=scan_obj.state,
            created_at=scan_obj.created_at,
            finished_at=scan_obj.finished_at,
            retry_count=int(scan_obj.retry_count or 0),
            error=error
        ))

    return history
