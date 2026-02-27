from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.db.session import get_session
from app.models.fitness import FitnessRecord
from app.models.user import User
from app.schemas.fitness_schema import FitnessBulkIngest, FitnessResponse

router = APIRouter()

@router.post("/ingest/{user_id}")
def ingest_fitness_data(user_id: int, payload: FitnessBulkIngest, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    records_to_add = []
    for item in payload.records:
        record = FitnessRecord(
            user_id=user_id,
            timestamp=item.timestamp,
            heart_rate=item.heart_rate,
            steps=item.steps,
            calories=item.calories,
            distance=item.distance,
            activity_type=item.activity_type,
            source=item.source
        )
        records_to_add.append(record)
    
    if records_to_add:
        db.add_all(records_to_add)
        db.commit()
    
    return {"status": "success", "inserted_count": len(records_to_add)}

@router.get("/history/{user_id}", response_model=List[FitnessResponse])
def get_fitness_history(user_id: int, limit: int = 100, db: Session = Depends(get_session)):
    statement = select(FitnessRecord).where(FitnessRecord.user_id == user_id).order_by(FitnessRecord.timestamp.desc()).limit(limit)
    results = db.exec(statement).all()
    return results