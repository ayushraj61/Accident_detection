from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks, File, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import subprocess
import sys
import os
import datetime
import shutil
import json

from app import db_models, schemas, database
from app.services.dispatch_engine import find_nearest_ambulances
from app.services.hospital_matcher import rank_hospitals
from app.websocket.manager import manager

router = APIRouter(prefix="/api/v1/emergency", tags=["Emergency"])

VENV_PYTHON = "/Users/ayushraj/accident_detection/venv/bin/python"
SIM_PATH = "/Users/ayushraj/accident_detection/detection/simulator.py"

@router.post("/upload-video")
async def upload_accident_clip(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    lat: float = Form(28.6139), 
    lng: float = Form(77.2090),
    db: Session = Depends(database.get_db)
):
    upload_dir = "/tmp/ai_aiders_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    background_tasks.add_task(run_simulator, file_path, lat, lng)
    return {"status": "success", "message": "Video uploaded, processing started"}

def run_simulator(video_path: str, lat: float, lng: float):
    try:
        subprocess.Popen([VENV_PYTHON, SIM_PATH, "--video", video_path, "--lat", str(lat), "--lng", str(lng)])
        print(f"[AI ENGINE] Started simulation for {video_path} at {lat}, {lng}")
    except Exception as e:
        print(f"[AI ENGINE ERROR] {str(e)}")

@router.post("/alert")
async def receive_edge_alert(alert: dict, db: Session = Depends(database.get_db)):
    alert_id = alert.get("id")
    new_incident = db_models.Incident(
        id=alert_id,
        severity=alert.get("severity", "MEDIUM"),
        confidence=alert.get("confidence", 0.0),
        lat=alert.get("lat"),
        lng=alert.get("lng"),
        status="pending",
        video_clip_url=alert.get("video_clip_url"),
        thumbnail_b64=alert.get("thumbnail_b64"),
        created_at=datetime.datetime.utcnow()
    )
    hospitals = db.query(db_models.Hospital).all()
    class AlertObj: pass
    alert_obj = AlertObj()
    alert_obj.lat = alert.get("lat")
    alert_obj.lng = alert.get("lng")
    matched_hospitals = rank_hospitals(alert_obj, hospitals)
    if matched_hospitals:
        new_incident.hospital_id = matched_hospitals[0].id
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    payload = {
        "event": "NEW_ACCIDENT",
        "alert": schemas.IncidentResponse.from_orm(new_incident).dict(),
        "matched_hospitals": [schemas.HospitalResponse.from_orm(h).dict() for h in matched_hospitals[:3]] if matched_hospitals else []
    }
    await manager.broadcast(payload)
    return {"status": "success"}

@router.get("/incidents", response_model=List[schemas.IncidentResponse])
def get_incidents(db: Session = Depends(database.get_db)):
    return db.query(db_models.Incident).all()

@router.post("/assign-ambulances")
async def assign_ambulances(payload: dict, db: Session = Depends(database.get_db)):
    try:
        alert_id = payload.get("alert_id")
        hospital_id = payload.get("hospital_id")
        raw_ids = payload.get("ambulance_ids", [])
        ambulance_ids = [int(aid) for aid in raw_ids if aid is not None]
        
        incident = db.query(db_models.Incident).filter(db_models.Incident.id == alert_id).first()
        if not incident: return {"status": "error", "message": "Incident not found"}
        
        # 🛡️ SECURITY CHECK: Is this case already claimed?
        if incident.status == "dispatched" or incident.assigned_fleet:
             return {"status": "error", "message": "This case has already been claimed by another hospital."}
             
        ambs = db.query(db_models.Ambulance).filter(db_models.Ambulance.id.in_(ambulance_ids)).all()
        amb_names = [a.unit_name for a in ambs]
        for a in ambs: a.is_available = False
        
        incident.status = "dispatched"
        incident.hospital_id = hospital_id
        incident.assigned_fleet = ",".join(amb_names)
        incident.hospital_status = "inbound"
        db.commit()
        
        await manager.broadcast({
            "event": "AMBULANCE_ASSIGNED",
            "alert_id": alert_id,
            "hospital_id": hospital_id,
            "ambulance_ids": ambulance_ids,
            "ambulance_names": amb_names,
            "status": "dispatched"
        })
        return {"status": "success", "assigned": amb_names}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/hospital/status")
async def update_hospital_status(payload: dict, db: Session = Depends(database.get_db)):
    alert_id = payload.get("alert_id")
    new_status = payload.get("status")
    incident = db.query(db_models.Incident).filter(db_models.Incident.id == alert_id).first()
    if incident:
        incident.hospital_status = new_status
        # FORCE RELEASE FLEET ON ADMISSION
        if new_status == "admitted" and incident.assigned_fleet:
            amb_names = [n.strip() for n in incident.assigned_fleet.split(',')]
            db.query(db_models.Ambulance).filter(db_models.Ambulance.unit_name.in_(amb_names)).update({"is_available": True}, synchronize_session=False)
            db.commit()
            await manager.broadcast({"event": "FLEET_RELEASED", "ambulance_names": amb_names})
        db.commit()
        await manager.broadcast({"event": "HOSPITAL_STATUS_UPDATED", "alert_id": alert_id, "status": new_status})
        return {"status": "success"}
    return {"status": "error"}

@router.post("/hospital/discharge")
async def discharge_patient(payload: dict, db: Session = Depends(database.get_db)):
    alert_id = payload.get("alert_id")
    incident = db.query(db_models.Incident).filter(db_models.Incident.id == alert_id).first()
    if incident:
        # 1. Archive the case
        incident.status = "resolved"
        incident.hospital_status = "discharged"
        # 2. Safety Check: Ensure fleet is released if not already
        if incident.assigned_fleet:
            amb_names = [n.strip() for n in incident.assigned_fleet.split(',')]
            db.query(db_models.Ambulance).filter(db_models.Ambulance.unit_name.in_(amb_names)).update({"is_available": True}, synchronize_session=False)
            db.commit()
            await manager.broadcast({"event": "FLEET_RELEASED", "ambulance_names": amb_names})
        await manager.broadcast({"event": "CASE_RESOLVED", "alert_id": alert_id})
        return {"status": "success"}
    return {"status": "error"}

@router.post("/incident/{incident_id}/eta")
async def update_incident_eta(incident_id: str, eta: int, db: Session = Depends(database.get_db)):
    incident = db.query(db_models.Incident).filter(db_models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    incident.eta_minutes = eta
    db.commit()
    
    # Broadcast update to all listeners
    await manager.broadcast({
        "type": "INCIDENT_UPDATED",
        "incident": schemas.IncidentResponse.from_orm(incident).model_dump()
    })
    return {"status": "updated"}

@router.post("/ambulance/status")
async def update_ambulance_status(payload: dict, db: Session = Depends(database.get_db)):
    alert_id = payload.get("alert_id")
    status = payload.get("status")
    
    incident = db.query(db_models.Incident).filter(db_models.Incident.id == alert_id).first()
    if incident:
        incident.ambulance_status = status
        db.commit()
        
        await manager.broadcast({
            "event": "AMBULANCE_STATUS_UPDATED",
            "alert_id": alert_id,
            "status": status
        })
        return {"status": "success"}
    return {"status": "error", "message": "Incident not found"}

@router.post("/update-location")
async def update_ambulance_location(payload: dict, db: Session = Depends(database.get_db)):
    amb_id = payload.get("ambulance_id")
    lat = payload.get("lat")
    lng = payload.get("lng")
    await manager.broadcast({"event": "LOCATION_UPDATE", "ambulance_id": amb_id, "lat": lat, "lng": lng})
    return {"status": "success"}

@router.post("/verify")
async def verify_or_dismiss_alert(body: dict, db: Session = Depends(database.get_db)):
    alert_id = body.get("alert_id")
    action = body.get("action", "verify_dispatch")
    db_incident = db.query(db_models.Incident).filter(db_models.Incident.id == alert_id).first()
    if db_incident:
        db_incident.status = "verified" if action == "verify_dispatch" else "dismissed"
        if action == "verify_dispatch":
            if body.get("severity"): db_incident.severity = body.get("severity")
            if body.get("impact_scale"): db_incident.impact_scale = body.get("impact_scale")
        db.commit()
    await manager.broadcast({
        "event": "DISPATCH_VERIFIED" if action == "verify_dispatch" else "FALSE_ALARM",
        "alert": schemas.IncidentResponse.from_orm(db_incident).dict() if db_incident else None,
        "alert_id": alert_id, "action": action
    })
    return {"status": "success"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
