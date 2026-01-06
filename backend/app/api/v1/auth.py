from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User, UserRole
from pydantic import BaseModel

router = APIRouter()

# Schema just for this endpoint
class UserCreate(BaseModel):
    username: str
    full_name: str
    role: UserRole

@router.post("/register")
def register_new_user(user_data: UserCreate, db: Session = Depends(get_session)):
    # 1. Check if username exists
    existing = db.exec(select(User).where(User.username == user_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username taken")
    
    # 2. Create User
    new_user = User(
        username=user_data.username,
        full_name=user_data.full_name,
        role=user_data.role,
        age=None,    # Will be updated later via profile
        gender=None  # Will be updated later via profile
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "success", "user_id": new_user.id}