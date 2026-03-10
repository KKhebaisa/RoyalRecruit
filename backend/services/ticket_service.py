from sqlalchemy.orm import Session

from backend.models.entities import Server, Ticket, TicketConfig
from backend.models.schemas import TicketConfigIn, TicketCreateIn


def create_ticket_config(db: Session, server: Server, payload: TicketConfigIn) -> TicketConfig:
    config = TicketConfig(server_id=server.id, **payload.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def create_ticket(db: Session, server: Server, payload: TicketCreateIn) -> Ticket:
    server.ticket_counter += 1
    ticket = Ticket(
        server_id=server.id,
        type=payload.type,
        user_id=payload.user_id,
        channel_id=payload.channel_id,
        serial_number=server.ticket_counter,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket
