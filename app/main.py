import os
import time
import uuid
import logging
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.database import Base, engine
from app.routers import (
    health,
    applications,
    documents,
    validations,
    agent,
    auth,
    workflow,
    monitoring,
    clock,
    todays_actions,
    undertakings,
    validity,
    evc,
    audit,
    rules_studio,
    colleges
)

logger = logging.getLogger("niriksha.server")
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)

# Create DB tables (safe startup)
try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    logger.warning(f"Database table verification deferred: {exc}")

app = FastAPI(
    title="NIRIKSHA — The AICTE Approval Control Room",
    description=(
        "NIRIKSHA: Problem Statement 26262 — Integrated AICTE Approval Workflow Automation, "
        "Compliance Monitoring, and Alert Management System.\n\n"
        "Motto: Rules-aware. Predictive. Auditable. Humans always decide.\n\n"
        "Five Foundational Verbs:\n"
        "- ROUTE: Statechart pathways as data with guarded transitions & mandatory revert reasons\n"
        "- WATCH: Working-day SLA monitoring with holiday/leave-aware auto-delegation\n"
        "- WARN: Early-Warning ML predictor (P(breach ≤ 7d)) with top 3 SHAP risk factors\n"
        "- ESCALATE: Multi-channel idempotent escalation ladder (Officer → Regional Head → Bureau Head)\n"
        "- PROVE: Proof-grade Schneier-Kelsey (1999) hash-chained audit ledger with live Verify"
    ),
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG or settings.ENVIRONMENT != "production" else "/docs",
    redoc_url="/redoc" if settings.DEBUG or settings.ENVIRONMENT != "production" else "/redoc"
)

# Pure ASGI Middleware for Correlation ID, Response Timing, and Security Headers
# Pure ASGI avoids BaseHTTPMiddleware stream channel deadlocks with GZipMiddleware
class ProductionSecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = str(uuid.uuid4())
        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration_ms = (time.time() - start_time) * 1000
                headers = list(message.get("headers", []))
                headers.append((b"x-correlation-id", correlation_id.encode()))
                headers.append((b"x-response-time-ms", f"{duration_ms:.2f}".encode()))
                if settings.SECURITY_HEADERS_ENABLED:
                    headers.append((b"x-content-type-options", b"nosniff"))
                    headers.append((b"x-frame-options", b"DENY"))
                    headers.append((b"x-xss-protection", b"1; mode=block"))
                    headers.append((b"referrer-policy", b"strict-origin-when-cross-origin"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

# 1. Production Security & Tracing (Pure ASGI)
app.add_middleware(ProductionSecurityMiddleware)

# 2. GZip Compression
if settings.COMPRESSION_ENABLED:
    app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Locate React Production Assets
base_path = Path(__file__).resolve().parent.parent
react_dist = base_path / "frontend" / "dist"
if not react_dist.exists():
    react_dist = base_path / "frontend-react" / "dist"

# Mount React static assets directory
if react_dist.exists() and (react_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(react_dist / "assets")), name="react-assets")

# Include Core Routers
app.include_router(health.router)
app.include_router(applications.router)
app.include_router(documents.router)
app.include_router(validations.router)
app.include_router(agent.router)

# Include NIRIKSHA Workflow & Control Room Routers
app.include_router(auth.router)
app.include_router(workflow.router)
app.include_router(monitoring.router)
app.include_router(clock.router)
app.include_router(todays_actions.router)
app.include_router(undertakings.router)
app.include_router(validity.router)
app.include_router(evc.router)
app.include_router(audit.router)
app.include_router(rules_studio.router)
app.include_router(colleges.router)

# Static root files helper
@app.get("/favicon.svg", include_in_schema=False)
def get_favicon():
    fav = react_dist / "favicon.svg"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/svg+xml")
    return Response(status_code=404)

@app.get("/icons.svg", include_in_schema=False)
def get_icons():
    ico = react_dist / "icons.svg"
    if ico.exists():
        return FileResponse(str(ico), media_type="image/svg+xml")
    return Response(status_code=404)

@app.post("/system/reseed", tags=["System & Health"])
def reseed_system():
    """Seed benchmark dataset with 60 AICTE institutions across 8 regions."""
    from app.data.seed_data import seed_database
    seed_database()
    return {"status": "SUCCESS", "message": "Database reseeded with 60 benchmark institutions"}

# Root and SPA Fallback Routing
@app.get("/", include_in_schema=False)
def serve_index():
    index_file = react_dist / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ONLINE",
        "documentation": "/docs",
        "health": "/health"
    }

# SPA client-side routing fallback (for non-API paths)
@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa_fallback(full_path: str):
    # Exclude system API prefixes from fallback
    api_prefixes = (
        "api", "applications", "documents", "validations", "agent",
        "auth", "workflow", "monitoring", "clock", "todays-actions",
        "undertakings", "validity", "evc", "audit", "rules",
        "health", "docs", "redoc", "openapi.json", "system"
    )
    if any(full_path.startswith(prefix) for prefix in api_prefixes):
        return JSONResponse(status_code=404, content={"status": "NOT_FOUND", "message": f"Endpoint /{full_path} not found"})

    index_file = react_dist / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(status_code=404, content={"status": "NOT_FOUND", "message": f"Resource /{full_path} not found"})
