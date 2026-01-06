from fastapi import FastAPI
from app.db.session import create_db_and_tables, engine
from app.models.user import User, UserRole
from sqlmodel import Session, select
from app.api.v1 import patient, doctor

app = FastAPI(title="Cardiac Exercise AI")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
    # Seed Data (Create 1 Patient and 1 Doctor if they don't exist)
    with Session(engine) as session:
        if not session.exec(select(User)).first():
            patient = User(username="john_doe", role=UserRole.PATIENT, full_name="John Doe")
            doctor = User(username="dr_house", role=UserRole.DOCTOR, full_name="Dr. Gregory House")
            session.add(patient)
            session.add(doctor)
            session.commit()
            print("✅ Seeded test users: Patient (ID 1), Doctor (ID 2)")

app.include_router(patient.router, prefix="/api/v1/patient", tags=["Patient"])
app.include_router(doctor.router, prefix="/api/v1/doctor", tags=["Doctor"])

@app.get("/")
def root():
    return {"message": "System Operational"}