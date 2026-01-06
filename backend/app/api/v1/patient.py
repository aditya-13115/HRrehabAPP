from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.db.session import get_session
from app.schemas.health_schema import HealthInput, HealthResponse, WorkoutFeedback, UserUpdate
from app.services.ml_service import ml_service
from app.models.health import HealthRecord
from app.models.user import User
from sqlalchemy.orm import selectinload # Need this for relationships

router = APIRouter()

# UPDATE PROFILE (Age/Gender)
@router.patch("/profile/{user_id}")
def update_profile(user_id: int, data: UserUpdate, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    user.age = data.age
    user.gender = data.gender
    db.add(user)
    db.commit()
    return {"status": "updated"}

# PREDICT (Now fetches Age/Gender from Profile)
@router.post("/predict/{user_id}", response_model=HealthResponse)
def predict_health(user_id: int, data: HealthInput, db: Session = Depends(get_session)):
    # 1. Get User Profile
    user = db.get(User, user_id)
    if not user or not user.age or not user.gender:
        raise HTTPException(400, "Please complete your profile (Age/Gender) first.")

    # 2. Format Conditions String for ML
    cond_list = []
    if data.has_htn: cond_list.append("HTN")
    if data.has_dm: cond_list.append("DM")
    conditions_str = ", ".join(cond_list) if cond_list else "None"

    # 3. ML Service
    result = ml_service.predict_and_audit(
        user.age, user.gender, data.weight, data.resting_hr, 
        data.bp_systolic, data.bp_diastolic,
        data.pulse_rate_before, data.respiratory_rate_before,
        data.borg_rating_before, conditions_str
    )

    # 4. Calories Calculation
    mets = {"Low": 3.5, "Moderate": 5.0, "High": 8.0}
    intensity = "Low" if result["is_urgent"] else result["predicted_intensity"]
    calories = mets.get(intensity, 3.5) * data.weight * 0.33

    # 5. Save Record
    record = HealthRecord(
        patient_id=user_id,
        weight=data.weight, resting_hr=data.resting_hr,
        bp_systolic=data.bp_systolic, bp_diastolic=data.bp_diastolic,
        pulse_rate_before=data.pulse_rate_before,
        respiratory_rate_before=data.respiratory_rate_before,
        borg_rating_before=data.borg_rating_before,
        conditions=conditions_str,
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
    # Convert list to string
    symptoms_str = ",".join(feedback.symptoms) if feedback.symptoms else "None"
    record.symptoms = symptoms_str
    
    # CRITICAL FIX: Flag urgency if dangerous symptoms are reported
    if "Chest Pain" in symptoms_str or "Dizziness" in symptoms_str:
        record.is_urgent = True
    
    db.add(record)
    db.commit()
    return {"status": "saved"}

# 3. HISTORY & LOGIN
@router.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_session)):
    # Use selectinload to fetch the remarks relationship efficiently
    statement = select(HealthRecord).where(HealthRecord.patient_id == user_id).options(selectinload(HealthRecord.remarks)).order_by(HealthRecord.timestamp.desc())
    results = db.exec(statement).all()
    
    # Format the response to include remark text
    history_data = []
    for record in results:
        rec_dict = record.dict()
        # Join all remarks into a single string
        if record.remarks:
            rec_dict["doctor_note"] = "; ".join([r.text for r in record.remarks])
        else:
            rec_dict["doctor_note"] = "No remarks"
        history_data.append(rec_dict)
        
    return history_data
@router.get("/login/{username}")
def login(username: str, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.username == username)).first()
    if not user: raise HTTPException(404, "User not found")
    return user