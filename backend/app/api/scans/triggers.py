import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.scans.constants import TERMINAL_STATES, ACTIVE_STATES, STAGE_TIMEOUTS
from app.core.config import settings
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.db_models import ProjectDB, ScanDB
from app.schemas.scan import ScanCreate, ScanResponse
from app.services.validation import VALID_STAGES, validate_scan_request
from app.state.scan_state import ScanState
from app.tasks.jenkins_tasks import trigger_jenkins_scan_async
from app.websockets.manager import manager as websocket_manager
from app.api.scans.helpers import calculate_scan_timeout, scan_to_response

router = APIRouter()
logger = logging.getLogger(__name__)


def _create_scan_object(
    scan_id: str, project_id: str, scan_mode: str, selected_stages: list, db: Session
) -> ScanDB:
    """Create scan object in CREATED state"""
    return ScanDB(
        scan_id=scan_id,
        project_id=project_id,
        scan_mode=scan_mode,
        selected_stages=selected_stages or [],
        state=ScanState.CREATED,
        created_at=datetime.now(timezone.utc),
        started_at=None,
        jenkins_build_number=None,
        jenkins_queue_id=None,
        stage_results=[],
        callback_digests=[],
    )


@router.post("/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("1000/minute" if settings.ENV == "test" else "10/minute")
def trigger_scan(
    request: Request,
    scan: ScanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_scan_timeout: str | None = Header(default=None, alias="X-Scan-Timeout"),
):
    """Trigger a new scan for a project"""
    try:
        validate_scan_request(scan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    project = (
        db.query(ProjectDB).filter(ProjectDB.project_id == scan.project_id).first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.last_scan_state and project.last_scan_state in [
        state.value for state in ACTIVE_STATES
    ]:
        raise HTTPException(
            status_code=409,
            detail="An active scan already exists for this project",
        )

    scan_id = str(uuid.uuid4())
    scan_timeout = calculate_scan_timeout(scan.selected_stages)

    if x_scan_timeout:
        try:
            override_timeout = int(x_scan_timeout)
            if override_timeout > 0:
                scan_timeout = override_timeout
                logger.info(
                    f"Scan timeout overridden via header: {scan_timeout} seconds ({scan_timeout / 60:.1f} minutes)"
                )
        except ValueError:
            logger.warning(
                f"Invalid X-Scan-Timeout header value ({x_scan_timeout}), using calculated timeout"
            )

    try:
        scan_obj = _create_scan_object(
            scan_id, scan.project_id, scan.scan_mode, scan.selected_stages or [], db
        )
        db.add(scan_obj)
        project.last_scan_state = scan_obj.state.value
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if "ix_scans_project_state" in str(e.orig) or "uq_project_active_state" in str(
            e.orig
        ):
            logger.info(
                f"Duplicate scan prevented for project {scan.project_id} (database constraint)"
            )
            raise HTTPException(
                status_code=409, detail="An active scan already exists for this project"
            )
        raise

    db.refresh(scan_obj)

    background_tasks.add_task(
        websocket_manager.send_scan_update,
        scan_id=scan_obj.scan_id,
        project_id=scan_obj.project_id,
        data=scan_to_response(scan_obj),
    )

    project_data = {
        "project_id": project.project_id,
        "name": project.name,
        "git_url": project.git_url,
        "branch": project.branch,
        "credentials_id": project.credentials_id,
        "sonar_key": project.sonar_key,
        "target_ip": project.target_ip,
        "target_url": project.target_url,
        "status": project.status,
        "scan_timeout": scan_timeout,
    }

    logger.info(f"Project data before sending to celery: {project_data}")
    logger.info(
        f"Calculated scan timeout: {scan_timeout} seconds ({scan_timeout / 60:.1f} minutes)"
    )

    trigger_jenkins_scan_async.delay(
        scan_id=scan_obj.scan_id,
        scan_mode=scan_obj.scan_mode,
        selected_stages=scan_obj.selected_stages,
        project_data=project_data,
    )

    return scan_to_response(scan_obj)


@router.get("/scans", response_model=list[ScanResponse])
@limiter.limit("1000/minute" if settings.ENV == "test" else "50/minute")
def list_scans(request: Request, db: Session = Depends(get_db)):
    """List all scans with timeout checking."""
    from app.api.scans.helpers import expire_scan_if_timed_out

    scans = db.query(ScanDB).all()
    active_scans = [s for s in scans if s.state not in TERMINAL_STATES]

    if active_scans:
        project_ids = {s.project_id for s in active_scans}
        projects = (
            db.query(ProjectDB).filter(ProjectDB.project_id.in_(project_ids)).all()
        )
        project_map = {p.project_id: p for p in projects}

        now = datetime.now(timezone.utc)
        timeout_seconds = settings.SCAN_TIMEOUT
        any_expired = False

        for scan_obj in active_scans:
            project_obj = project_map.get(scan_obj.project_id)
            if project_obj:
                if expire_scan_if_timed_out(
                    db, scan_obj, project_obj, now, timeout_seconds, auto_commit=False
                ):
                    any_expired = True

        if any_expired:
            db.commit()

    return [scan_to_response(s) for s in scans]
