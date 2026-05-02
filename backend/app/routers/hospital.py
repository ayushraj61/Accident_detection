from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import db_models, schemas, database
from ..services import auth
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/api/v1/hospital", tags=["Hospital Management"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_hospital(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    payload = auth.decode_access_token(token)
    if not payload or payload.get("role") != "hospital":
        raise HTTPException(status_code=401, detail="Could not validate hospital credentials")
    hospital_id = int(payload.get("sub"))
    hospital = db.query(db_models.Hospital).filter(db_models.Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital

@router.get("/me", response_model=schemas.HospitalResponse)
def read_hospital_me(hospital: db_models.Hospital = Depends(get_current_hospital)):
    return hospital

@router.put("/update", response_model=schemas.HospitalResponse)
def update_hospital_stats(update: schemas.HospitalUpdate, hospital: db_models.Hospital = Depends(get_current_hospital), db: Session = Depends(database.get_db)):
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(hospital, key, value)
    db.commit()
    db.refresh(hospital)
    return hospital

@router.post("/ambulance", response_model=schemas.AmbulanceResponse)
def add_ambulance(ambulance: schemas.AmbulanceCreate, hospital: db_models.Hospital = Depends(get_current_hospital), db: Session = Depends(database.get_db)):
    hashed_password = auth.get_password_hash(ambulance.password)
    new_ambulance = db_models.Ambulance(
        **ambulance.model_dump(exclude={"password"}),
        hospital_id=hospital.id,
        password_hash=hashed_password
    )
    db.add(new_ambulance)
    db.commit()
    db.refresh(new_ambulance)
    return new_ambulance

@router.get("/ambulances", response_model=List[schemas.AmbulanceResponse])
def get_fleet(hospital: db_models.Hospital = Depends(get_current_hospital), db: Session = Depends(database.get_db)):
    return hospital.ambulances

@router.get("/incidents", response_model=List[schemas.IncidentResponse])
def get_hospital_incidents(hospital: db_models.Hospital = Depends(get_current_hospital), db: Session = Depends(database.get_db)):
    return hospital.incidents
