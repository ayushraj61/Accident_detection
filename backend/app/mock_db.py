from app.models import Ambulance, Hospital, Location

# Simulated Local Database Records (Replacing the empty arrays)

mock_hospitals = [
    Hospital(
        id="HOSP-001",
        name="City General Trauma Center",
        location=Location(lat=40.7128, lon=-74.0060),
        available_beds=12,
        icu_available=True,
        specialties=["Trauma", "Surgery", "Neurology"],
        historical_acceptance_rate=0.95,
        current_er_load=65
    ),
    Hospital(
        id="HOSP-002",
        name="Mercy Regional Clinic",
        location=Location(lat=40.7350, lon=-73.9920),
        available_beds=4,
        icu_available=False,
        specialties=["General", "Pediatrics"],
        historical_acceptance_rate=0.80,
        current_er_load=92
    ),
    Hospital(
        id="HOSP-003",
        name="Metro Advanced Life Support",
        location=Location(lat=40.7600, lon=-73.9800),
        available_beds=22,
        icu_available=True,
        specialties=["Trauma", "Burn Center"],
        historical_acceptance_rate=0.99,
        current_er_load=40
    )
]

mock_ambulances = [
    Ambulance(
        id="Rescue Unit 4",
        organization="State EMD",
        location=Location(lat=40.7200, lon=-74.0000), # Very close to City General
        is_available=True
    ),
    Ambulance(
        id="Medic 9",
        organization="Private Transport",
        location=Location(lat=40.7800, lon=-73.9500),
        is_available=True
    ),
    Ambulance(
        id="Rescue Unit 12",
        organization="State EMD",
        location=Location(lat=40.7100, lon=-74.0100),
        is_available=False # Busy on another call
    )
]
