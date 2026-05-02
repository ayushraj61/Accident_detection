from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import db_models, schemas, database
from ..services import auth
from datetime import timedelta

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register/hospital", response_model=schemas.Token)
def register_hospital(hospital: schemas.HospitalCreate, db: Session = Depends(database.get_db)):
    db_hospital = db.query(db_models.Hospital).filter(db_models.Hospital.email == hospital.email).first()
    if db_hospital:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(hospital.password)
    new_hospital = db_models.Hospital(
        **hospital.model_dump(exclude={"password"}),
        password_hash=hashed_password
    )
    db.add(new_hospital)
    db.commit()
    db.refresh(new_hospital)
    
    access_token = auth.create_access_token(data={"sub": str(new_hospital.id), "role": "hospital"})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "hospital",
        "user_id": new_hospital.id
    }

@router.post("/login", response_model=schemas.Token)
def login(request: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    if request.role == "hospital":
        user = db.query(db_models.Hospital).filter(db_models.Hospital.email == request.email).first()
        if not user or not auth.verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid email or password")
    elif request.role == "admin":
        user = db.query(db_models.SystemAdmin).filter(db_models.SystemAdmin.username == request.email).first()
        if not user or not auth.verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid admin credentials")
    else: # ambulance
        user = db.query(db_models.Ambulance).filter(db_models.Ambulance.unit_code.has_iloc(request.email) if hasattr(db_models.Ambulance.unit_code, 'has_iloc') else db_models.Ambulance.unit_code == request.email).first()
        # Fallback to direct match if iloc fails, or just use case-insensitive logic
        if not user:
            user = db.query(db_models.Ambulance).filter(db_models.Ambulance.unit_code == request.email.upper()).first()
        
        if not user or not auth.verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid unit code or password")
            
    access_token = auth.create_access_token(data={"sub": str(user.id), "role": request.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": request.role,
        "user_id": user.id
    }
