import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "NIRIKSHA — AICTE Approval Control Room"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    
    # Security & CORS
    SECRET_KEY: str = os.getenv("SECRET_KEY", "niriksha-production-secret-change-in-prod-f83b28d94e")
    CORS_ORIGINS: Union[str, List[str]] = os.getenv("CORS_ORIGINS", "*")
    ALLOWED_HOSTS: Union[str, List[str]] = os.getenv("ALLOWED_HOSTS", "*")
    SECURITY_HEADERS_ENABLED: bool = True
    COMPRESSION_ENABLED: bool = True

    # Storage & DB (Neon PostgreSQL with fallback)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATABASE_URL: str = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL") or f"sqlite:///{BASE_DIR}/bluepill.db"
    
    # Neon / PostgreSQL Connection Pool Settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "15"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "25"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "300"))
    DB_ECHO: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def sync_database_url(self) -> str:
        """Normalize database URL for SQLAlchemy with Neon/PostgreSQL support."""
        url = self.DATABASE_URL.strip()
        
        # If user inadvertently passed Neon's REST/HTTP API endpoint instead of the PostgreSQL connection string
        if url.startswith("https://") or url.startswith("http://"):
            import logging
            logging.getLogger("uvicorn.error").warning(
                f"[DATABASE CONFIG WARNING] Provided DATABASE_URL '{url}' is an HTTP/REST endpoint. "
                "SQLAlchemy and psycopg2 require the PostgreSQL Wire Protocol connection string: "
                "'postgresql://<user>:<password>@<neon-host>-pooler.neon.tech/<dbname>?sslmode=require'. "
                f"Falling back to local SQLite at {self.BASE_DIR / 'bluepill.db'} until PostgreSQL connection string with credentials is provided."
            )
            return f"sqlite:///{self.BASE_DIR}/bluepill.db"

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        # If remote Postgres (such as Neon) and no sslmode parameter is present, append sslmode=require
        if ("neon.tech" in url or "postgres" in url) and "sqlite" not in url and "?" not in url:
            url += "?sslmode=require"
        return url

    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    SYNTHETIC_DIR: Path = BASE_DIR / "synthetic_data"
    MODELS_DIR: Path = BASE_DIR / "models"
    MODEL_PATH: Path = MODELS_DIR / "qwen2.5-3b-instruct.gguf"
    
    # LLM Settings
    LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "true").lower() in ("true", "1", "yes")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    
    # Simulation & Adapters
    SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "true").lower() in ("true", "1", "yes")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
