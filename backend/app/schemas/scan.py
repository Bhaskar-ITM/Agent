from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional
from app.state.scan_state import ScanState
from datetime import datetime

class ScanBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

class ScanCreate(ScanBase):
    project_id: str
    mode: str  # AUTOMATED | MANUAL
    selected_stages: Optional[List[str]] = None

class StageResult(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    name: str
    status: str
    details: Optional[str] = None
    report_url: Optional[str] = None
    timestamp: str

class ScanResponse(ScanBase):
    scan_id: str
    project_id: str
    mode: str
    selected_stages: List[str]
    state: ScanState
    created_at: datetime
    stage_results: List[StageResult] = []
