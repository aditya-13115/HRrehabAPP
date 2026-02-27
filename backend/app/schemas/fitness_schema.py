from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FitnessIngest(BaseModel):
    timestamp: datetime
    heart_rate: Optional[float] = None
    steps: Optional[int] = None
    calories: Optional[float] = None
    distance: Optional[float] = None
    activity_type: Optional[str] = None
    source: Optional[str] = None

class FitnessBulkIngest(BaseModel):
    records: List[FitnessIngest]

class FitnessResponse(BaseModel):
    id: int
    user_id: int
    timestamp: datetime
    heart_rate: Optional[float]
    steps: Optional[int]
    calories: Optional[float]
    distance: Optional[float]
    activity_type: Optional[str]
    source: Optional[str]
    created_at: datetime