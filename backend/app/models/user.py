from sqlmodel import SQLModel, Field
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    role: UserRole
    
    # NEW: Profile Fields
    age: Optional[int] = Field(default=None)
    gender: Optional[str] = Field(default=None) # "M" or "F"  
