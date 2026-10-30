import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("uvicorn.error")

db_url = settings.sync_database_url
is_sqlite = "sqlite" in db_url

if is_sqlite:
    engine = create_engine(
        db_url,
        echo=settings.DB_ECHO,
        connect_args={"check_same_thread": False}
    )
else:
    # Serverless-optimized engine for Neon PostgreSQL
    # - pool_pre_ping: tests dead/restarted connections before checkout (crucial for Neon auto-suspend)
    # - pool_recycle: periodically reconnects to avoid stale TCP sockets
    # - pool_size & max_overflow: handles burst traffic safely
    engine = create_engine(
        db_url,
        echo=settings.DB_ECHO,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> dict:
    """Verify active database connectivity and return diagnostic info."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            dialect = engine.dialect.name
            is_neon = "neon.tech" in db_url
            return {
                "status": "connected" if result == 1 else "unexpected_result",
                "dialect": dialect,
                "is_neon": is_neon,
                "serverless_resilience": {
                    "pool_pre_ping": settings.DB_POOL_PRE_PING,
                    "pool_recycle_seconds": settings.DB_POOL_RECYCLE
                } if not is_sqlite else "sqlite_local"
            }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "dialect": engine.dialect.name
        }
