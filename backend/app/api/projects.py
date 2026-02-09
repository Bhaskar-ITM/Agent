from fastapi import APIRouter, HTTPException
from app.schemas.project import ProjectCreate, ProjectResponse
import uuid

router = APIRouter()

# In-memory storage for now
projects_db = {}

@router.get("/projects", response_model=list[dict])
def list_projects():
    # Return mapping for dashboard: [{project_id, name, last_scan_state}]
    return [
        {
            "project_id": p["project_id"],
            "name": p["name"],
            "last_scan_state": p.get("last_scan_state", "NONE")
        } for p in projects_db.values()
    ]

@router.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate):
    project_id = str(uuid.uuid4())
    project_data = project.model_dump()
    project_data["project_id"] = project_id
    project_data["status"] = "CREATED"
    projects_db[project_id] = project_data
    return project_data

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]
