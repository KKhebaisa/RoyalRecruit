from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.entities import Ticket, TicketConfig
from backend.models.schemas import TicketConfigIn, TicketCreateIn
from backend.services.server_service import get_server_by_discord_id
from backend.services.ticket_service import create_ticket, create_ticket_config

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/config/{discord_server_id}")
def create_config(discord_server_id: str, payload: TicketConfigIn, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    config = create_ticket_config(db, server, payload)
    return {"id": config.id}


@router.get("/config/{discord_server_id}")
def list_config(discord_server_id: str, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return db.query(TicketConfig).filter(TicketConfig.server_id == server.id).all()


@router.post("/")
def open_ticket(payload: TicketCreateIn, db: Session = Depends(get_db)):
    server = get_server_by_discord_id(db, payload.discord_server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    ticket = create_ticket(db, server, payload)
    return {"id": ticket.id, "serial": f"{ticket.serial_number:03d}"}


@router.post("/{ticket_id}/status")
def update_status(ticket_id: int, status: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = status
    db.commit()
    return {"ok": True}
