import uuid
import shutil
from pathlib import Path
from datetime import timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.core.db import get_db
from app.models.db_models import ProjectDB, ScanDB
from app.core.config import settings
from app.state.scan_state import ScanState

router = APIRouter()

ACTIVE_STATES = {
    ScanState.CREATED.value,
    ScanState.QUEUED.value,
    ScanState.RUNNING.value,
}


def _get_last_scan_map(db: Session) -> dict[str, dict]:
    """
    Performance Optimization (Bolt ⚡): Fetches both scan_id and created_at in one go
    to avoid N+1 ScanDB lookups in list_projects.
    """
    subq = (
        db.query(
            ScanDB.project_id,
            func.max(ScanDB.created_at).label("max_created"),
        )
        .group_by(ScanDB.project_id)
        .subquery()
    )
    rows = (
        db.query(ScanDB.project_id, ScanDB.scan_id, ScanDB.created_at)
        .join(
            subq,
            and_(
                ScanDB.project_id == subq.c.project_id,
                ScanDB.created_at == subq.c.max_created,
            ),
        )
        .all()
    )
    return {row.project_id: {"scan_id": row.scan_id, "created_at": row.created_at} for row in rows}


@router.get("/projects", response_model=list[dict])
def list_projects(db: Session = Depends(get_db)):
    """
    Performance Optimization (Bolt ⚡):
    1. Eliminates N+1 database queries by batch fetching scan metadata and report summaries.
    2. Reduces frontend network requests from 1+N to 1 by inlining report data.
    """
    from app.models.db_models import ScanReportDB

    last_scan_map = _get_last_scan_map(db)
    db_projects = db.query(ProjectDB).all()

    # Batch fetch report summaries for all latest scans
    latest_scan_ids = [info["scan_id"] for info in last_scan_map.values()]
    reports = (
        db.query(ScanReportDB)
        .filter(ScanReportDB.scan_id.in_(latest_scan_ids))
        .all()
    ) if latest_scan_ids else []

    # Aggregate reports by project_id
    project_reports = {}
    for r in reports:
        if r.project_id not in project_reports:
            project_reports[r.project_id] = {
                "total_findings": 0,
                "severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
                "tools": []
            }

        summary = r.severity_summary or {}
        findings_count = sum(summary.values())

        report_info = project_reports[r.project_id]
        report_info["total_findings"] += findings_count
        report_info["severity"]["critical"] += summary.get("critical", 0)
        report_info["severity"]["high"] += summary.get("high", 0)
        report_info["severity"]["medium"] += summary.get("medium", 0)
        report_info["severity"]["low"] += summary.get("low", 0)
        report_info["severity"]["info"] += summary.get("info", 0)

        report_info["tools"].append({
            "tool": r.tool_name,
            "findings": findings_count,
            "critical": summary.get("critical", 0),
            "high": summary.get("high", 0),
            "medium": summary.get("medium", 0),
            "low": summary.get("low", 0),
            "link": r.report_url if r.tool_name == "sonar" else None
        })

    # Pre-calculate IST delta to avoid repeated object creation
    ist_delta = timedelta(hours=5, minutes=30)

    projects = []
    for p in db_projects:
        scan_info = last_scan_map.get(p.project_id)
        last_scan_id = scan_info["scan_id"] if scan_info else None
        last_scan_time = None

        if scan_info and scan_info["created_at"]:
            dt = scan_info["created_at"]
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ist_dt = dt + ist_delta
            last_scan_time = ist_dt.strftime("%Y-%m-%dT%H:%M:%S")

        projects.append(
            {
                "project_id": p.project_id,
                "name": p.name,
                "last_scan_state": p.last_scan_state,
                "last_scan_id": last_scan_id,
                "last_scan_time": last_scan_time,
                "report_summary": project_reports.get(p.project_id)
            }
        )
    return projects


@router.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    project_id = str(uuid.uuid4())
    db_project = ProjectDB(
        project_id=project_id,
        name=project.name,
        git_url=str(project.git_url) if project.git_url else None,
        branch=project.branch,
        credentials_id=project.credentials_id,
        sonar_key=project.sonar_key,
        target_ip=project.target_ip,
        target_url=str(project.target_url) if project.target_url else None,
        status="CREATED",
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    db_project = db.query(ProjectDB).filter(ProjectDB.project_id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    last_scan = (
        db.query(ScanDB)
        .filter(ScanDB.project_id == project_id)
        .order_by(ScanDB.created_at.desc())
        .first()
    )
    project_data = dict(db_project.__dict__)
    project_data.pop("_sa_instance_state", None)
    project_data["last_scan_state"] = db_project.last_scan_state
    project_data["last_scan_id"] = last_scan.scan_id if last_scan else None
    return project_data


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str, project: ProjectUpdate, db: Session = Depends(get_db)
):
    db_project = db.query(ProjectDB).filter(ProjectDB.project_id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    if db_project.last_scan_state in ACTIVE_STATES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project cannot be edited while a scan is active",
        )

    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)

    last_scan = (
        db.query(ScanDB)
        .filter(ScanDB.project_id == project_id)
        .order_by(ScanDB.created_at.desc())
        .first()
    )
    project_data = dict(db_project.__dict__)
    project_data.pop("_sa_instance_state", None)
    project_data["last_scan_state"] = db_project.last_scan_state
    project_data["last_scan_id"] = last_scan.scan_id if last_scan else None
    return project_data


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    db_project = db.query(ProjectDB).filter(ProjectDB.project_id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    scans = db.query(ScanDB).filter(ScanDB.project_id == project_id).all()
    scan_ids = [scan.scan_id for scan in scans]
    for scan in scans:
        db.delete(scan)
    db.delete(db_project)
    db.commit()
    deleted_artifacts = 0
    storage_root = Path(settings.STORAGE_PATH)
    for scan_id in scan_ids:
        scan_path = storage_root / scan_id
        if scan_path.exists():
            shutil.rmtree(scan_path, ignore_errors=True)
            deleted_artifacts += 1
    return {
        "detail": "Project deleted successfully",
        "deleted_scans": len(scan_ids),
        "deleted_artifact_paths": deleted_artifacts,
    }
