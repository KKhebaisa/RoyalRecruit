from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.entities import Server
from backend.models.schemas import ServerSyncRequest
from backend.services.server_service import get_or_create_server

router = APIRouter(prefix="/servers", tags=["servers"])


@router.post("/sync")
def sync_server(payload: ServerSyncRequest, db: Session = Depends(get_db)):
    server = get_or_create_server(db, payload.discord_server_id, payload.owner_id)
    return {"id": server.id, "discord_server_id": server.discord_server_id}


@router.get("/")
def list_servers(db: Session = Depends(get_db)):
    servers = db.query(Server).all()
    return servers
