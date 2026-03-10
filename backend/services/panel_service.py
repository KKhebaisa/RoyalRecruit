from sqlalchemy.orm import Session

from backend.models.entities import Panel, Server
from backend.models.schemas import PanelIn


def create_panel(db: Session, server: Server, payload: PanelIn) -> Panel:
    panel = Panel(server_id=server.id, **payload.model_dump())
    db.add(panel)
    db.commit()
    db.refresh(panel)
    return panel
