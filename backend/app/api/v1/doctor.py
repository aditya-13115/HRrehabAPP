from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.db.session import get_session
from app.models.health import HealthRecord, Remark
from app.models.user import User # Import User model

router = APIRouter()

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_session)):
    # JOIN HealthRecord with User to get the username
    statement = select(HealthRecord, User.username).join(User, HealthRecord.patient_id == User.id).order_by(HealthRecord.timestamp.desc())
    results = db.exec(statement).all()
    
    # Flatten the result into a clean list of dictionaries
    clean_data = []
    for record, username in results:
        rec_dict = record.dict()
        rec_dict["patient_username"] = username # <--- ADD USERNAME HERE
        clean_data.append(rec_dict)
        
    return clean_data

# ... (Keep existing override/remark endpoints same as before) ...
@router.post("/remark/{record_id}")
def add_remark(record_id: int, text: str, user_id: int, db: Session = Depends(get_session)):
    record = db.get(HealthRecord, record_id)
    if not record: raise HTTPException(404, "Record not found")
    new_remark = Remark(record_id=record_id, doctor_id=user_id, text=text)
    db.add(new_remark)
    db.commit()
    return {"status": "saved"}

@router.patch("/override/{record_id}")
def override_intensity(record_id: int, new_intensity: str, db: Session = Depends(get_session)):
    record = db.get(HealthRecord, record_id)
    if not record: raise HTTPException(404, "Record not found")
    
    mhr = record.mhr
    if new_intensity == "Low": factor_min, factor_max = 0.50, 0.63
    elif new_intensity == "Moderate": factor_min, factor_max = 0.64, 0.76
    else: factor_min, factor_max = 0.77, 0.93

    record.predicted_intensity = new_intensity
    record.target_hr_min = int(factor_min * mhr)
    record.target_hr_max = int(factor_max * mhr)
    record.is_urgent = False 
    
    db.add(record)
    db.commit()
    return {"status": "updated", "intensity": new_intensity}