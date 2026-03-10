from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.entities import Panel
from backend.models.schemas import PanelIn
from backend.services.panel_service import create_panel
from backend.services.server_service import get_server_by_discord_id

router = APIRouter(prefix="/panels", tags=["panels"])


@router.post("/{discord_server_id}")
def create(discord_server_id: str, payload: PanelIn, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    panel = create_panel(db, server, payload)
    return panel


@router.get("/{discord_server_id}")
def list_panels(discord_server_id: str, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return db.query(Panel).filter(Panel.server_id == server.id).all()
