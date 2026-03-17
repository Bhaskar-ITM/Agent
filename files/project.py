from pydantic import BaseModel, HttpUrl
from typing import Optional


class ProjectCreate(BaseModel):
    name: str
    git_url: str
    branch: str = "main"
    credentials_id: str
    sonar_key: str
    target_ip: Optional[str] = None
    target_url: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Partial update schema — all fields optional."""
    name: Optional[str] = None
    git_url: Optional[str] = None
    branch: Optional[str] = None
    credentials_id: Optional[str] = None
    sonar_key: Optional[str] = None
    target_ip: Optional[str] = None
    target_url: Optional[str] = None


class ProjectResponse(ProjectCreate):
    project_id: str
    status: str = "CREATED"
