import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from app import db_models  # Import your existing models

# === CONFIGURATION ===
# Replace these with your actual PostgreSQL credentials
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "1234"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "postgres"

SQLITE_URL = "sqlite:///backend/accident_detection.db"
POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

def migrate():
    print("Starting migration: SQLite -> PostgreSQL")
    
    # 1. Connect to both databases
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    # 2. Create tables in PostgreSQL using your models
    print("Creating tables in PostgreSQL...")
    db_models.Base.metadata.create_all(postgres_engine)
    
    # 3. Setup Sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_db = SqliteSession()
    postgres_db = PostgresSession()
    
    # 4. Define tables to migrate (in order to respect Foreign Keys)
    tables = [
        db_models.SystemAdmin,
        db_models.Hospital,
        db_models.Ambulance,
        db_models.Incident
    ]
    
    try:
        for model in tables:
            table_name = model.__tablename__
            print(f"Migrating table: {table_name}...")
            
            # Fetch all rows from SQLite
            items = sqlite_db.query(model).all()
            
            if not items:
                print(f"   (Table {table_name} is empty, skipping...)")
                continue
            
            # Use 'merge' to insert data into Postgres (handles duplicates safely)
            for item in items:
                # We expunge the item from the sqlite session so we can add it to postgres
                sqlite_db.expunge(item)
                postgres_db.merge(item)
            
            postgres_db.commit()
            print(f"   Copied {len(items)} rows.")
            
        print("\nMigration complete!")
        print("Data is now in PostgreSQL.")
        
    except Exception as e:
        print(f"\nMigration failed: {str(e)}")
        postgres_db.rollback()
    finally:
        sqlite_db.close()
        postgres_db.close()

if __name__ == "__main__":
    # Ensure we are in the project root
    if not os.path.exists("backend/accident_detection.db"):
        print("Error: Could not find 'backend/accident_detection.db'. Run this from the project root.")
    else:
        migrate()
