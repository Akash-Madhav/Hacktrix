from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

class FindingResponse(BaseModel):
    id: str
    run_id: str
    rule_id: str
    check_name: str
    category: str
    severity: str
    outcome: str
    explanation: str
    rule_citation: Optional[str] = None
    evidence_json: Optional[str] = None
    source_document_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ValidationRunCreate(BaseModel):
    engine_mode: str = "DETERMINISTIC_RULES" # or HYBRID_WITH_LLM

class ValidationRunResponse(BaseModel):
    id: str
    application_id: str
    run_timestamp: datetime
    rule_version: str
    engine_mode: str
    status: str
    overall_readiness: str
    findings_count: int
    findings: List[FindingResponse] = []

    class Config:
        from_attributes = True
