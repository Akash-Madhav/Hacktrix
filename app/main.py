import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database import Base, engine
from app.routers import health, applications, documents, validations, agent

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AICTE BluePill Automated Application Validation Workbench.\n\n"
        "Features:\n"
        "- Deterministic statutory compliance validation (V01, V04, V05, V07, V10)\n"
        "- PDF Digital Integrity & Tampering Anomaly Detection (V12 Metadata, V13 Revisions)\n"
        "- Authoritative Application Verdict with Actionable Checklist of Missing Items & Deficiencies\n"
        "- Live Application Status Dashboard\n"
        "- Interactive 'Ask BluePill' Statutory Scrutiny Assistant powered by Qwen 2.5 with exact evidence citations\n"
        "- Fail-Closed Architecture with dynamic LLM Kill-Switch"
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

base_path = Path(__file__).resolve().parent.parent
react_dist = base_path / "frontend-react" / "dist"
frontend_dir = base_path / "frontend"

# Mount React production assets if available
if react_dist.exists() and (react_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(react_dist / "assets")), name="react-assets")

# Mount Vanilla frontend static files
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# Include Routers
app.include_router(health.router)
app.include_router(applications.router)
app.include_router(documents.router)
app.include_router(validations.router)
app.include_router(agent.router)

@app.get("/")
def get_frontend():
    # Prefer built React frontend
    if react_dist.exists() and (react_dist / "index.html").exists():
        return FileResponse(str(react_dist / "index.html"))
    # Fallback to vanilla frontend
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "documentation": "/docs",
        "health": "/health",
        "status": "ONLINE"
    }

@app.post("/system/reseed")
def reseed_system():
    from app.data.seed_data import seed_database
    seed_database()
    return {"status": "SUCCESS", "message": "Database reseeded with 3 benchmark applications"}
