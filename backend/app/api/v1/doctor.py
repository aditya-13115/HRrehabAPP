from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.db.session import get_session
from app.models.health import HealthRecord, Remark
from app.schemas.health_schema import HealthResponse

router = APIRouter()

@router.get("/dashboard")
def get_dashboard(only_urgent: bool = False, db: Session = Depends(get_session)):
    query = select(HealthRecord).order_by(HealthRecord.timestamp.desc())
    if only_urgent: query = query.where(HealthRecord.is_urgent == True)
    return db.exec(query).all()

@router.patch("/override/{record_id}")
def override_intensity(record_id: int, new_intensity: str, db: Session = Depends(get_session)):
    record = db.get(HealthRecord, record_id)
    if not record: raise HTTPException(404, "Record not found")
    
    # Recalculate HR Zones based on new intensity
    mhr = record.mhr
    if new_intensity == "Low": factor_min, factor_max = 0.50, 0.63
    elif new_intensity == "Moderate": factor_min, factor_max = 0.64, 0.76
    else: factor_min, factor_max = 0.77, 0.93

    record.predicted_intensity = new_intensity
    record.target_hr_min = int(factor_min * mhr)
    record.target_hr_max = int(factor_max * mhr)
    record.is_urgent = False # Doctor override clears urgency
    
    db.add(record)
    db.commit()
    return {"status": "updated", "intensity": new_intensity}