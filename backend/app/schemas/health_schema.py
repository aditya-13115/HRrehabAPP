from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

class UserUpdate(BaseModel):    # <--- THIS WAS MISSING OR NOT SAVED
    age: int
    gender: Literal["M", "F"]
class HealthInput(BaseModel):
    
    weight: float
    resting_hr: int
    bp_systolic: int
    bp_diastolic: int
    
    # New Inputs
    pulse_rate_before: int
    respiratory_rate_before: int
    borg_rating_before: int
    has_htn: bool
    has_dm: bool

class WorkoutFeedback(BaseModel):
    borg_rating: int
    mood: str
    symptoms: List[str] = []

class UserUpdate(BaseModel):
    age: int
    gender: Literal["M", "F"]

class HealthResponse(BaseModel):
    id: int
    patient_id: int
    timestamp: datetime
    predicted_intensity: str
    mhr: int
    target_hr_min: int
    target_hr_max: int
    is_urgent: bool
    calories_burned: float
    youtube_link: Optional[str] = None