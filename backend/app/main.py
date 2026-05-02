from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import emergency, auth, hospital, ambulance, admin
from app.database import engine, Base
from app import db_models
import asyncio
import os
from app.redis_listener import listen_to_redis

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-AIDERS Backend API", description="Core dispatch and matching engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(emergency.router)
app.include_router(auth.router)
app.include_router(hospital.router)
app.include_router(ambulance.router)
app.include_router(admin.router)

# Serve video clips from the permanent data directory
clips_dir = "data/clips"
os.makedirs(clips_dir, exist_ok=True)
app.mount("/clips", StaticFiles(directory=clips_dir), name="clips")

@app.on_event("startup")
async def startup_event():
    print("[Backend] Connecting async workers...")
    asyncio.create_task(listen_to_redis())
    # Optional: Seed demo data here if needed, or do it via a separate script

@app.get("/")
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "AI-AIDERS API is running"}
