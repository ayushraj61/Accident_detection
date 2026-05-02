from pydantic import BaseModel
from typing import List, Optional

class Location(BaseModel):
    lat: float
    lon: float

class Ambulance(BaseModel):
    id: str
    organization: str
    location: Location
    is_available: bool

class Hospital(BaseModel):
    id: str
    name: str
    location: Location
    available_beds: int
    icu_available: bool
    specialties: List[str]
    historical_acceptance_rate: float
    current_er_load: int  # e.g., 0 to 100 percentage

class AccidentAlert(BaseModel):
    id: str
    location: Location
    severity: str  # "low", "medium", "high"
    confidence: float
    video_clip_url: Optional[str] = None
    thumbnail_b64: Optional[str] = None
