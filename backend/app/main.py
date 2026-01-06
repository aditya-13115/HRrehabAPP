from fastapi import FastAPI
from app.db.session import create_db_and_tables, engine
from app.models.user import User, UserRole
from sqlmodel import Session, select
# --- IMPORT AUTH HERE ---
from app.api.v1 import patient, doctor, auth 

app = FastAPI(title="Cardiac Exercise AI")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
    # Seed Data
    with Session(engine) as session:
        if not session.exec(select(User)).first():
            # Note: We added age/gender to User model, so we can set defaults here
            patient = User(username="john_doe", role=UserRole.PATIENT, full_name="John Doe", age=30, gender="M")
            doctor = User(username="dr_house", role=UserRole.DOCTOR, full_name="Dr. Gregory House", age=50, gender="M")
            session.add(patient)
            session.add(doctor)
            session.commit()
            print("✅ Seeded test users: Patient (ID 1), Doctor (ID 2)")

# --- REGISTER THE ROUTERS ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"]) # <--- NEW
app.include_router(patient.router, prefix="/api/v1/patient", tags=["Patient"])
app.include_router(doctor.router, prefix="/api/v1/doctor", tags=["Doctor"])

@app.get("/")
def root():
    return {"message": "System Operational"}