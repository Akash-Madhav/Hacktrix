from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.agent import AgentTrace
from app.schemas.agent import (
    AskBluePillRequest,
    AskBluePillResponse,
    AgentTraceResponse
)
from app.services.agent_runtime import (
    answer_ask_bluepill_query,
    run_sa01_classify_document
)

router = APIRouter(prefix="/agent", tags=["Agent & Scrutiny Assistant"])

@router.post("/ask", response_model=AskBluePillResponse)
async def ask_bluepill(payload: AskBluePillRequest, db: Session = Depends(get_db)):
    """
    'Ask BluePill' Statutory Scrutiny Assistant:
    Accepts natural language questions from scrutiny officers about an application
    and synthesizes answers supported by exact document evidence citations.
    """
    try:
        return await answer_ask_bluepill_query(
            db=db,
            application_id=payload.application_id,
            question=payload.question,
            include_statutory_citations=payload.include_statutory_citations
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/classify/{document_id}")
async def classify_document_with_agent(document_id: str, db: Session = Depends(get_db)):
    """
    Triggers SA-01 Document Classification Agent to corroborate document type.
    """
    res = await run_sa01_classify_document(db, document_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/traces", response_model=List[AgentTraceResponse])
def list_agent_traces(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieves immutable agent audit logs and execution traces."""
    traces = db.query(AgentTrace).order_by(AgentTrace.created_at.desc()).limit(limit).all()
    return [AgentTraceResponse.from_orm(t) for t in traces]

@router.get("/config")
def get_system_config():
    """Returns runtime AI configuration, kill-switch status, and local model path."""
    model_exists = settings.MODEL_PATH.exists()
    model_size = settings.MODEL_PATH.stat().st_size if model_exists else 0
    return {
        "llm_enabled": settings.LLM_ENABLED,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "local_model_path": str(settings.MODEL_PATH),
        "local_model_exists": model_exists,
        "local_model_size_bytes": model_size,
        "simulation_mode": settings.SIMULATION_MODE,
        "fail_closed_mode": True,
        "explanation": "When LLM_ENABLED is false, system executes 100% deterministic rule scrutiny."
    }

@router.post("/config/toggle-llm")
def toggle_llm_mode(enable: bool = Query(...)):
    """Toggles LLM Kill Switch dynamically."""
    settings.LLM_ENABLED = enable
    return {
        "llm_enabled": settings.LLM_ENABLED,
        "message": f"LLM Kill Switch is now {'ACTIVATED (LLM Enabled)' if enable else 'DEACTIVATED (Deterministic Rules Only)'}"
    }
