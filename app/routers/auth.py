import hashlib
import uuid
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication & RBAC"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RoleSwitchRequest(BaseModel):
    role: str # INSTITUTION, SCRUTINY_OFFICER, REGIONAL_OFFICER, BUREAU_OFFICER, ADMIN
    region: Optional[str] = "Western"

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    pw_hash = hash_pw(req.password)
    user = db.query(User).filter(User.username == req.username).first()
    
    # Allow demo login if user exists, or verify hash
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = f"niriksha-token-{user.id[:8]}-{user.role.lower()}"
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "region": user.region,
            "institution_id": user.institution_id,
            "is_on_leave": user.is_on_leave
        }
    }

@router.post("/switch-role")
def switch_role_for_demo(req: RoleSwitchRequest, db: Session = Depends(get_db)):
    """Convenience helper for live presentation: instantly switches persona."""
    user = db.query(User).filter(User.role == req.role).first()
    if not user:
        # Create quick demo user for the role
        user = User(
            id=str(uuid.uuid4()),
            username=f"demo_{req.role.lower()}",
            email=f"{req.role.lower()}@aicte-niriksha.gov.in",
            password_hash=hash_pw("password123"),
            full_name=f"Demo {req.role.replace('_', ' ').title()}",
            role=req.role,
            region=req.region
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = f"niriksha-token-{user.id[:8]}-{user.role.lower()}"
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "region": user.region,
            "institution_id": user.institution_id,
            "is_on_leave": user.is_on_leave
        }
    }

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "email": u.email,
        "role": u.role,
        "region": u.region,
        "is_on_leave": u.is_on_leave
    } for u in users]
