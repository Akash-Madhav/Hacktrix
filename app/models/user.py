from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="SCRUTINY_OFFICER")
    # Roles: INSTITUTION, SCRUTINY_OFFICER, REGIONAL_OFFICER, BUREAU_OFFICER, ADMIN
    region = Column(String(64), nullable=True) # Northern, Western, Southern, etc.
    institution_id = Column(String(36), nullable=True) # If role is INSTITUTION
    is_active = Column(Boolean, default=True)
    is_on_leave = Column(Boolean, default=False)
    leave_until = Column(DateTime, nullable=True)
    deputy_user_id = Column(String(36), nullable=True) # Leave-aware auto-delegation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
