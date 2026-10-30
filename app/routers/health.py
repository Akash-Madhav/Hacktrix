from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.database import get_db, check_db_connection
from app.config import settings

router = APIRouter(tags=["System & Health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive system health and environment diagnostics."""
    db_diag = check_db_connection()
    db_healthy = db_diag.get("status") == "connected"

    return {
        "status": "HEALTHY" if db_healthy else "UNHEALTHY",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_diag,
        "database_connected": db_healthy,
        "llm_enabled": settings.LLM_ENABLED,
        "simulation_mode": settings.SIMULATION_MODE,
        "storage": {
            "upload_dir": str(settings.UPLOAD_DIR),
            "upload_dir_ready": settings.UPLOAD_DIR.exists(),
            "synthetic_dir_ready": settings.SYNTHETIC_DIR.exists()
        }
    }

@router.get("/health/live")
def liveness_probe():
    """Kubernetes / Docker container liveness probe (checks process responsiveness)."""
    return {"status": "ALIVE", "app": settings.APP_NAME, "version": settings.APP_VERSION}

@router.get("/health/ready")
def readiness_probe(response: Response):
    """Kubernetes / Docker container readiness probe (checks downstream DB connectivity)."""
    db_diag = check_db_connection()
    if db_diag.get("status") != "connected":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "NOT_READY", "reason": "Database unreachable", "details": db_diag}
    return {"status": "READY", "database": db_diag.get("dialect", "connected")}
