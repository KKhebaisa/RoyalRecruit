from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.entities import AuditLog
from backend.models.schemas import LogEventIn
from backend.services.server_service import get_server_by_discord_id

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("/")
def create_log(payload: LogEventIn, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, payload.discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    log = AuditLog(server_id=server.id, event_type=payload.event_type, details=payload.details)
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id}


@router.get("/{discord_server_id}")
def list_logs(discord_server_id: str, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return db.query(AuditLog).filter(AuditLog.server_id == server.id).order_by(AuditLog.created_at.desc()).limit(200).all()
