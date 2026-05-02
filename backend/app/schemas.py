from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Shared Schemas
class LocationSchema(BaseModel):
    lat: float
    lng: float

# Hospital Schemas
class HospitalBase(BaseModel):
    email: EmailStr
    name: str
    phone: str
    address: str
    city: str
    state: str
    lat: float
    lng: float
    total_beds: int
    icu_beds: int
    trauma_level: str
    specialties: List[str]
    has_helipad: bool = False
    blood_bank: bool = False
    er_capacity: int
    current_er_load: int = 0

class HospitalCreate(HospitalBase):
    password: str

class HospitalUpdate(BaseModel):
    available_beds: Optional[int] = None
    icu_available: Optional[int] = None
    current_er_load: Optional[int] = None

class HospitalResponse(HospitalBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Ambulance Schemas
class AmbulanceBase(BaseModel):
    unit_name: str
    unit_code: str
    driver_name: str
    phone: str
    vehicle_type: str
    lat: float
    lng: float
    license_plate: str
    is_available: bool = True

class AmbulanceCreate(AmbulanceBase):
    password: str # Driver PIN or password

class AmbulanceResponse(AmbulanceBase):
    id: int
    hospital_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str # "hospital" or "ambulance"
    user_id: int

class LoginRequest(BaseModel):
    email: str # email for hospital, unit_code for ambulance
    password: str
    role: str # "hospital" or "ambulance"

# Incident / Alert Schemas
class IncidentResponse(BaseModel):
    id: str
    severity: str
    confidence: float
    lat: float
    lng: float
    status: str
    impact_scale: Optional[str] = None
    incident_type: Optional[str] = None
    assigned_fleet: Optional[str] = None
    hospital_status: Optional[str] = 'notified'
    video_clip_url: Optional[str] = None
    thumbnail_b64: Optional[str] = None
    hospital_id: Optional[int] = None
    eta_minutes: Optional[int] = None
    created_at: Optional[datetime] = None
    auto_dispatch_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class AdminSettings(BaseModel):
    auto_dispatch_window: int
    class Config:
        from_attributes = True
