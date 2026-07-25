import asyncio
import datetime
from app.database import SessionLocal
from app.db_models import Incident
from app.websocket.manager import manager
from app import schemas

async def run_auto_verifier():
    """Auto-verifies pending incidents if no one acts within the time window."""
    print("[AutoVerifier] Started.")
    while True:
        try:
            db = SessionLocal()
            now = datetime.datetime.utcnow()
            
            # Find incidents that are pending and past their deadline
            overdue_incidents = db.query(Incident).filter(
                Incident.status == "pending",
                Incident.auto_dispatch_at <= now
            ).all()
            
            for incident in overdue_incidents:
                print(f"[AutoVerifier] Auto-verifying incident: {incident.id}")
                
                incident.status = "verified"
                # Use "CRITICAL" or "HIGH" as fallback if not set
                if not incident.severity:
                    incident.severity = "CRITICAL"
                
                db.commit()
                db.refresh(incident)
                
                # Notify the frontend via WebSocket
                payload = {
                    "event": "DISPATCH_VERIFIED",
                    "alert_id": incident.id,
                    "action": "auto_verify",
                    "alert": {
                        "id": incident.id,
                        "status": "verified",
                        "severity": incident.severity,
                        "impact_scale": "Significant",
                        "hospital_id": incident.hospital_id
                    }
                }
                await manager.broadcast(payload)
                
            db.close()
        except Exception as e:
            print(f"[AutoVerifier] Error: {str(e)}")
            
        await asyncio.sleep(10) # Run every 10 seconds for high precision
