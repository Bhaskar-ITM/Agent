from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    git_url: str
    branch: str = "main"
    credentials_id: str
    sonar_key: str
    target_ip: Optional[str] = None
    target_url: Optional[str] = None

class ProjectResponse(ProjectCreate):
    project_id: str
    status: str = "CREATED"
    project_type: Optional[str] = "unknown"
    has_dockerfile: bool = False
    has_frontend: bool = False
    has_backend: bool = False
    dependency_type: Optional[str] = None
