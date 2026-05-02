from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import db_models, database
from ..services import auth
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    payload = auth.decode_access_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Invalid admin token")
    admin_id = int(payload.get("sub"))
    admin = db.query(db_models.SystemAdmin).filter(db_models.SystemAdmin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin

@router.get("/me")
def read_admin_me(admin: db_models.SystemAdmin = Depends(get_current_admin)):
    return {
        "id": admin.id, 
        "username": admin.username, 
        "role": "admin",
        "settings": {"auto_dispatch_window": admin.auto_dispatch_window}
    }

@router.put("/settings")
def update_settings(settings: dict, admin: db_models.SystemAdmin = Depends(get_current_admin), db: Session = Depends(database.get_db)):
    window = settings.get("auto_dispatch_window")
    if window is not None:
        admin.auto_dispatch_window = window
        db.commit()
    return {"status": "ok", "auto_dispatch_window": admin.auto_dispatch_window}
