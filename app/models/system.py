from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime
from app.database import Base

class SystemClock(Base):
    """Application-level injectable clock state for time simulation."""
    __tablename__ = "system_clock"

    id = Column(String(36), primary_key=True)
    simulated_now = Column(DateTime, nullable=False, default=datetime.utcnow)
    speed_multiplier = Column(Float, default=1.0)
    is_paused = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
