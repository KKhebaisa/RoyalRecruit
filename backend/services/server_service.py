from sqlalchemy.orm import Session

from backend.models.entities import Server


def get_or_create_server(db: Session, discord_server_id: str, owner_id: str) -> Server:
    server = db.query(Server).filter(Server.discord_server_id == discord_server_id).first()
    if server:
        return server
    server = Server(discord_server_id=discord_server_id, owner_id=owner_id)
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


def get_server_by_discord_id(db: Session, discord_server_id: str) -> Server | None:
    return db.query(Server).filter(Server.discord_server_id == discord_server_id).first()
