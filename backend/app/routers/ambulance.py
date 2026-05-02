from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import db_models, schemas, database
from ..services import auth
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/api/v1/ambulance", tags=["Ambulance Dashboard"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_ambulance(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    payload = auth.decode_access_token(token)
    if not payload or payload.get("role") != "ambulance":
        raise HTTPException(status_code=401, detail="Could not validate ambulance credentials")
    ambulance_id = int(payload.get("sub"))
    ambulance = db.query(db_models.Ambulance).filter(db_models.Ambulance.id == ambulance_id).first()
    if not ambulance:
        raise HTTPException(status_code=404, detail="Ambulance not found")
    return ambulance

@router.get("/me")
def read_ambulance_me(ambulance: db_models.Ambulance = Depends(get_current_ambulance)):
    return {
        "id": ambulance.id,
        "unit_name": ambulance.unit_name,
        "unit_code": ambulance.unit_code,
        "hospital_id": ambulance.hospital_id,
        "hospital_name": ambulance.hospital.name,
        "lat": ambulance.lat,
        "lng": ambulance.lng,
        "role": "ambulance"
    }

@router.put("/location")
def update_location(location: schemas.LocationSchema, ambulance: db_models.Ambulance = Depends(get_current_ambulance), db: Session = Depends(database.get_db)):
    ambulance.lat = location.lat
    ambulance.lng = location.lng
    db.commit()
    return {"status": "updated"}

@router.get("/active-incident", response_model=Optional[schemas.IncidentResponse])
def get_active_incident(ambulance: db_models.Ambulance = Depends(get_current_ambulance), db: Session = Depends(database.get_db)):
    # Find the most recent incident assigned to this ambulance's hospital that is not resolved
    incident = db.query(db_models.Incident).filter(
        db_models.Incident.hospital_id == ambulance.hospital_id,
        db_models.Incident.status.in_(["dispatched", "verified", "arrived"])
    ).order_by(db_models.Incident.created_at.desc()).first()
    return incident
