from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from app.state.scan_state import ScanState
from datetime import datetime

class ScanCreate(BaseModel):
    project_id: str
    mode: str  # AUTOMATED | MANUAL
    selected_stages: Optional[List[str]] = None
    target_url: Optional[str] = None # For manual trigger overrides if allowed

class StageResult(BaseModel):
    stage: str
    status: str
    summary: Optional[str] = None
    artifact_url: Optional[str] = None
    findings: Optional[dict] = None  # {critical: int, high: int, ...}
    artifacts: Optional[List[str]] = []

class ScanResponse(BaseModel):
    scan_id: str
    project_id: str
    state: ScanState
    stage_gating: Optional[dict] = None
    started_at: Optional[datetime] = None

class ScanResultsResponse(BaseModel):
    scan_id: str
    results: List[StageResult]
