from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ToolSummary(BaseModel):
    tool: str
    findings: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    link: Optional[str] = None


class ReportSummary(BaseModel):
    project_id: str
    total_findings: int
    severity: SeveritySummary
    tools: List[ToolSummary]

class ProjectCreate(BaseModel):
    name: str
    git_url: str
    branch: str = "main"
    credentials_id: str
    sonar_key: str
    target_ip: Optional[str] = None
    target_url: Optional[str] = None

class ProjectUpdate(BaseModel):
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
    last_scan_state: Optional[str] = None
    last_scan_id: Optional[str] = None
    last_scan_time: Optional[str] = None
    report_summary: Optional[ReportSummary] = None
