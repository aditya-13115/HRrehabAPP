from sqlmodel import SQLModel, Field
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    role: UserRole
    full_name: Optional[str] = None