from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.db.session import get_session
from app.schemas.health_schema import HealthInput, HealthResponse, WorkoutFeedback
from app.services.ml_service import ml_service
from app.models.health import HealthRecord
from app.models.user import User

router = APIRouter()

# 1. PREDICT & CALCULATE CALORIES
@router.post("/predict/{user_id}", response_model=HealthResponse)
def predict_health(user_id: int, data: HealthInput, db: Session = Depends(get_session)):
    # Run ML
    result = ml_service.predict_and_audit(
        data.age, data.weight, data.resting_hr, data.bp_systolic, data.bp_diastolic, data.borg_rating_before
    )

    # Calculate Calories (Formula: METs * Weight * Hours)
    # 20 min workout = 0.33 hours
    mets = {"Low": 3.5, "Moderate": 5.0, "High": 8.0}
    intensity = "Low" if result["is_urgent"] else result["predicted_intensity"]
    calories = mets.get(intensity, 3.5) * data.weight * 0.33

    record = HealthRecord(
        patient_id=user_id,
        age=data.age, weight=data.weight,
        resting_hr=data.resting_hr,
        bp_systolic=data.bp_systolic, bp_diastolic=data.bp_diastolic,
        borg_rating_before=data.borg_rating_before,
        predicted_intensity=result["predicted_intensity"],
        mhr=result["mhr"],
        target_hr_min=result["target_hr_min"],
        target_hr_max=result["target_hr_max"],
        is_urgent=result["is_urgent"],
        calories_burned=round(calories, 1)
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    resp = HealthResponse(**record.dict())
    resp.youtube_link = result["youtube_link"]
    return resp

# 2. SUBMIT FEEDBACK (Mood/Borg)
@router.patch("/feedback/{record_id}")
def submit_feedback(record_id: int, feedback: WorkoutFeedback, db: Session = Depends(get_session)):
    record = db.get(HealthRecord, record_id)
    if not record: raise HTTPException(404, "Record not found")
    
    record.borg_rating = feedback.borg_rating
    record.mood = feedback.mood
    record.symptoms = ",".join(feedback.symptoms) if feedback.symptoms else "None"
    
    db.add(record)
    db.commit()
    return {"status": "saved"}

# 3. HISTORY & LOGIN
@router.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_session)):
    return db.exec(select(HealthRecord).where(HealthRecord.patient_id == user_id).order_by(HealthRecord.timestamp.desc())).all()

@router.get("/login/{username}")
def login(username: str, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.username == username)).first()
    if not user: raise HTTPException(404, "User not found")
    return user