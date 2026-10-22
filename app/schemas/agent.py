from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class AskBluePillRequest(BaseModel):
    application_id: str
    question: str
    include_statutory_citations: bool = True

class SourceCitation(BaseModel):
    document_name: str
    clause_or_page: str
    extracted_text_snippet: str

class AskBluePillResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceCitation] = []
    engine_used: str # DETERMINISTIC_EXPLAINER | LLM_OLLAMA
    latency_ms: float
    disclaimer: str

class AgentTraceResponse(BaseModel):
    id: str
    run_id: Optional[str]
    agent_name: str
    prompt_snapshot: Optional[str]
    tool_calls_json: Optional[str]
    sanitized_output: Optional[str]
    latency_ms: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
