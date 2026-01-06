from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class HealthInput(BaseModel):
    age: int
    weight: float
    resting_hr: int
    bp_systolic: int
    bp_diastolic: int
    borg_rating_before: int

# NEW: Schema for the Post-Workout Feedback
class WorkoutFeedback(BaseModel):
    borg_rating: int
    mood: str
    symptoms: List[str] = [] # Received as list, stored as string

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
    # Feedback fields (Optional because they are empty initially)
    borg_rating: Optional[int] = None
    mood: Optional[str] = None
    symptoms: Optional[str] = None
    
    youtube_link: Optional[str] = None