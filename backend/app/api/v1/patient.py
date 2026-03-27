from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.db.session import get_session
from app.schemas.health_schema import HealthInput, HealthResponse, WorkoutFeedback, UserUpdate
from app.services.ml_service import ml_service
from app.models.health import HealthRecord
from app.models.user import User
from app.api.v1.auth import get_current_user
from sqlalchemy.orm import selectinload 

router = APIRouter()

def verify_patient_access(user_id: int, current_user: User):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")

@router.patch("/profile/{user_id}")
def update_profile(user_id: int, data: UserUpdate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    verify_patient_access(user_id, current_user)
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    user.age = data.age
    user.gender = data.gender
    db.add(user)
    db.commit()
    return {"status": "updated"}

@router.post("/predict/{user_id}", response_model=HealthResponse)
def predict_health(user_id: int, data: HealthInput, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    verify_patient_access(user_id, current_user)
    user = db.get(User, user_id)
    if not user or not user.age or not user.gender:
        raise HTTPException(400, "Please complete your profile (Age/Gender) first.")

    cond_list = []
    if data.has_htn: cond_list.append("HTN")
    if data.has_dm: cond_list.append("DM")
    conditions_str = ", ".join(cond_list) if cond_list else "None"

    mhr = 220 - user.age
    
    is_urgent = False
    predicted_intensity = "Warmup"
    youtube_links = [
        "https://www.youtube.com/watch?v=8VKntE2gUfc", 
        "https://www.youtube.com/watch?v=j6_KqEkea3M"
    ]

    if data.resting_hr > 100 or data.bp_systolic > 160 or data.bp_diastolic > 100 or data.borg_rating_before >= 15:
        is_urgent = True
        predicted_intensity = "Rest"
        youtube_links = ["https://www.youtube.com/watch?v=ZToicYcHIOU"]

    record = HealthRecord(
        patient_id=user_id,
        weight=data.weight, resting_hr=data.resting_hr,
        bp_systolic=data.bp_systolic, bp_diastolic=data.bp_diastolic,
        pulse_rate_before=data.pulse_rate_before,
        respiratory_rate_before=data.respiratory_rate_before,
        borg_rating_before=data.borg_rating_before,
        conditions=conditions_str,
        predicted_intensity=predicted_intensity, 
        mhr=mhr,
        target_hr_min=int(0.50 * mhr),
        target_hr_max=int(0.70 * mhr),
        is_urgent=is_urgent,
        calories_burned=0.0 
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    resp = HealthResponse(**record.dict())
    resp.youtube_links = youtube_links 
    return resp

@router.patch("/feedback/{record_id}")
def submit_feedback(record_id: int, feedback: WorkoutFeedback, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    record = db.get(HealthRecord, record_id)
    if not record: raise HTTPException(404, "Record not found")
    verify_patient_access(record.patient_id, current_user)
    
    user = db.get(User, record.patient_id)
    
    record.borg_rating_after = feedback.borg_rating
    record.pulse_rate_after = feedback.pulse_rate_after
    record.mood = feedback.mood
    
    symptoms_str = ",".join(feedback.symptoms) if feedback.symptoms else "None"
    record.symptoms = symptoms_str
    
    mets = {"Low": 3.5, "Moderate": 5.0, "High": 8.0, "Warmup": 3.0, "Rest": 1.0}
    current_intensity = record.predicted_intensity
    calories = mets.get(current_intensity, 3.5) * record.weight * 0.33
    record.calories_burned = round(calories, 1)
    
    if "Chest Pain" in symptoms_str or "Dizziness" in symptoms_str or feedback.borg_rating >= 17:
        record.is_urgent = True
        record.predicted_intensity = "Rest"
        youtube_links = ["https://www.youtube.com/watch?v=ZToicYcHIOU"]
    else:
        borg_change = feedback.borg_rating - record.borg_rating_before
        hr_percent_mhr = feedback.pulse_rate_after / float(220 - user.age)
        pulse_change = feedback.pulse_rate_after - record.pulse_rate_before
        
        ml_result = ml_service.evaluate_post_workout(
            borg_after=feedback.borg_rating,
            borg_change=borg_change,
            hr_percent_mhr=hr_percent_mhr,
            pulse_change=pulse_change,
            borg_before=record.borg_rating_before,
            age=user.age,
            resp_before=record.respiratory_rate_before
        )
        record.predicted_intensity = ml_result["predicted_intensity"]
        youtube_links = ml_result["youtube_links"]

    db.add(record)
    db.commit()
    
    return {
        "status": "saved", 
        "predicted_intensity": record.predicted_intensity,
        "is_urgent": record.is_urgent,
        "youtube_links": youtube_links
    }

@router.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    verify_patient_access(user_id, current_user)
    statement = select(HealthRecord).where(HealthRecord.patient_id == user_id).options(selectinload(HealthRecord.remarks)).order_by(HealthRecord.timestamp.desc())
    results = db.exec(statement).all()
    
    history_data = []
    for record in results:
        rec_dict = record.dict()
        if record.remarks:
            rec_dict["doctor_note"] = "; ".join([r.text for r in record.remarks])
        else:
            rec_dict["doctor_note"] = "No remarks"
        history_data.append(rec_dict)
        
    return history_data