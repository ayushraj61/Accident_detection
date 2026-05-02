from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    name = Column(String)
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    total_beds = Column(Integer, default=0)
    icu_beds = Column(Integer, default=0)
    available_beds = Column(Integer, default=0)
    icu_available = Column(Integer, default=0)
    trauma_level = Column(String) # e.g., "Level I"
    specialties = Column(JSON) # List of strings
    has_helipad = Column(Boolean, default=False)
    blood_bank = Column(Boolean, default=False)
    er_capacity = Column(Integer, default=0)
    current_er_load = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ambulances = relationship("Ambulance", back_populates="hospital")
    incidents = relationship("Incident", back_populates="hospital")

class Ambulance(Base):
    __tablename__ = "ambulances"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    unit_name = Column(String)
    unit_code = Column(String, unique=True, index=True) # Used for "login"
    password_hash = Column(String) # Driver PIN or password
    driver_name = Column(String)
    phone = Column(String)
    vehicle_type = Column(String) # BLS, ALS, etc.
    lat = Column(Float)
    lng = Column(Float)
    license_plate = Column(String)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    hospital = relationship("Hospital", back_populates="ambulances")

class SystemAdmin(Base):
    __tablename__ = "system_admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    auto_dispatch_window = Column(Integer, default=2) # Default 2 minutes
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True) # Event ID from simulator
    severity = Column(String)
    confidence = Column(Float)
    lat = Column(Float)
    lng = Column(Float)
    status = Column(String, default="pending") 
    impact_scale = Column(String, nullable=True) # Minor, Significant, Mass Casualty
    incident_type = Column(String, nullable=True) # Collision, Pedestrian, etc.
    video_clip_url = Column(String, nullable=True)
    thumbnail_b64 = Column(String, nullable=True)
    assigned_fleet = Column(String, nullable=True)
    hospital_status = Column(String, default="notified")
    
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    auto_dispatch_at = Column(DateTime, nullable=True) # Timestamp for auto-verify
    resolved_at = Column(DateTime, nullable=True)

    hospital = relationship("Hospital", back_populates="incidents")
