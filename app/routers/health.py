from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings

router = APIRouter(tags=["System & Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """System health check endpoint."""
    db_healthy = False
    try:
        db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        db_healthy = False

    return {
        "status": "HEALTHY" if db_healthy else "UNHEALTHY",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database_connected": db_healthy,
        "llm_enabled": settings.LLM_ENABLED,
        "simulation_mode": settings.SIMULATION_MODE,
        "upload_dir_ready": settings.UPLOAD_DIR.exists()
    }
