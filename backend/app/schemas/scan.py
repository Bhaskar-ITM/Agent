from pydantic import BaseModel
from typing import List, Optional
from app.state.scan_state import ScanState
from datetime import datetime

class ScanCreate(BaseModel):
    project_id: str
    scan_mode: str  # automated | manual
    selected_stages: Optional[List[str]] = None

class StageResult(BaseModel):
    stage: str
    status: str
    summary: Optional[str] = None
    artifact_url: Optional[str] = None

class ScanResponse(BaseModel):
    scan_id: str
    project_id: str
    scan_mode: str
    state: ScanState
    selected_stages: Optional[List[str]] = []
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    results: List[StageResult] = []

class ScanResultsResponse(BaseModel):
    scan_id: str
    results: List[StageResult]
