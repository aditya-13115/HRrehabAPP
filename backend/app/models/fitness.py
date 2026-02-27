from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class FitnessRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    
    heart_rate: Optional[float] = None
    steps: Optional[int] = None
    calories: Optional[float] = None
    distance: Optional[float] = None
    
    activity_type: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))