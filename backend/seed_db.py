from app.database import SessionLocal, engine
from app import db_models
from app.services import auth

def seed():
    db = SessionLocal()
    db_models.Base.metadata.create_all(bind=engine)

    # Check if data already exists
    if db.query(db_models.Hospital).first():
        print("Database already seeded.")
        return

    # 1. Create a Demo Hospital
    demo_hospital = db_models.Hospital(
        email="city.hospital@example.com",
        password_hash=auth.get_password_hash("password"),
        name="City General Trauma Center",
        phone="011-23456789",
        address="123 Health Street",
        city="New Delhi",
        state="Delhi",
        lat=28.6139,
        lng=77.2090,
        total_beds=100,
        icu_beds=20,
        available_beds=15,
        icu_available=5,
        trauma_level="Level I",
        specialties=["Trauma", "Surgery", "Neurology", "Cardiac"],
        has_helipad=True,
        blood_bank=True,
        er_capacity=50,
        current_er_load=65
    )
    db.add(demo_hospital)
    db.commit()
    db.refresh(demo_hospital)

    # 2. Add Ambulances to the Hospital
    ambulance1 = db_models.Ambulance(
        hospital_id=demo_hospital.id,
        unit_name="Rescue Unit Alpha",
        unit_code="AMB-001",
        password_hash=auth.get_password_hash("1234"),
        driver_name="Rajesh Kumar",
        phone="9876543210",
        vehicle_type="ALS",
        lat=28.6200,
        lng=77.2100,
        license_plate="DL-1CA-1234",
        is_available=True
    )
    ambulance2 = db_models.Ambulance(
        hospital_id=demo_hospital.id,
        unit_name="Medic Beta",
        unit_code="AMB-002",
        password_hash=auth.get_password_hash("1234"),
        driver_name="Suresh Singh",
        phone="9876543211",
        vehicle_type="BLS",
        lat=28.6100,
        lng=77.2200,
        license_plate="DL-1CA-5678",
        is_available=True
    )
    db.add(ambulance1)
    db.add(ambulance2)
    db.commit()

    # 3. Create a System Admin
    admin_user = db_models.SystemAdmin(
        username="admin",
        password_hash=auth.get_password_hash("admin123")
    )
    db.add(admin_user)
    db.commit()

    print("Seeding complete: Created 1 hospital, 2 ambulances, and 1 system admin.")
    db.close()

if __name__ == "__main__":
    seed()
