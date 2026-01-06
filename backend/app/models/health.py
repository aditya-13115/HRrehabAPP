from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone

class HealthRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="user.id")
    # Use timezone-aware UTC for accurate history
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # --- Vitals Inputs ---
    age: int
    weight: float
    resting_hr: int
    bp_systolic: int
    bp_diastolic: int
    borg_rating_before: int = Field(default=6)  # <--- NEW FIELD
    
    
    
    # --- AI Outputs ---
    predicted_intensity: str 
    mhr: int
    target_hr_min: int
    target_hr_max: int
    is_urgent: bool = Field(default=False)
    calories_burned: float = Field(default=0.0)  # NEW: For streaks/stats

    # --- Patient Feedback (Post-Workout) ---
    borg_rating: Optional[int] = Field(default=None) # Scale 6-20
    mood: Optional[str] = Field(default=None)        # Happy/Sad etc.
    symptoms: Optional[str] = Field(default=None)    # "Chest Pain", etc.

    # Relationships
    remarks: List["Remark"] = Relationship(back_populates="record")

class Remark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="healthrecord.id")
    doctor_id: int = Field(foreign_key="user.id")
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    record: Optional[HealthRecord] = Relationship(back_populates="remarks")