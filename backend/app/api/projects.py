import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.project import ProjectCreate, ProjectResponse
from app.state.persistence import persist_state
from app.state.store import projects_db, scans_db

router = APIRouter()


@router.get("/projects", response_model=list[dict])
def list_projects():
    return [
        {
            "project_id": p["project_id"],
            "name": p["name"],
            "last_scan_state": p.get("last_scan_state", "NONE"),
        }
        for p in projects_db.values()
    ]


@router.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate):
    project_id = str(uuid.uuid4())
    project_data = project.model_dump()
    project_data["project_id"] = project_id
    project_data["status"] = "CREATED"
    projects_db[project_id] = project_data
    persist_state(scans_db, projects_db)
    return project_data


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]
