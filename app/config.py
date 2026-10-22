import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AICTE BluePill Validation Workbench"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Storage & DB
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/bluepill.db"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    SYNTHETIC_DIR: Path = BASE_DIR / "synthetic_data"
    MODELS_DIR: Path = BASE_DIR / "models"
    MODEL_PATH: Path = MODELS_DIR / "qwen2.5-3b-instruct.gguf"
    
    # LLM Settings
    LLM_ENABLED: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    
    # Simulation & Adapters
    SIMULATION_MODE: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
