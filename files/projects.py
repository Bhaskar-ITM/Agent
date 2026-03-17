import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.core.db import get_db
from app.models.db_models import ProjectDB

router = APIRouter()

@router.get("/projects", response_model=list[dict])
def list_projects(db: Session = Depends(get_db)):
    db_projects = db.query(ProjectDB).all()
    return [
        {
            "project_id": p.project_id,
            "name": p.name,
            "last_scan_state": p.last_scan_state or "NONE",
        }
        for p in db_projects
    ]

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
        status="CREATED"
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
    return dict(db_project.__dict__)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """
    Partially update a project's details.
    Only fields provided in the request body will be updated.
    """
    db_project = db.query(ProjectDB).filter(ProjectDB.project_id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            # Coerce URL fields to string (in case Pydantic parses them as URL objects)
            if field in ("git_url", "target_url") and value is not None:
                value = str(value)
            setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)
    return dict(db_project.__dict__)


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    db_project = db.query(ProjectDB).filter(ProjectDB.project_id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(db_project)
    db.commit()
    return {"detail": "Project deleted successfully"}
