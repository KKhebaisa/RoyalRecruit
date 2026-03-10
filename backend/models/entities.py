from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    discord_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255))


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    discord_server_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    log_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ticket_counter: Mapped[int] = mapped_column(Integer, default=0)


class TicketConfig(Base):
    __tablename__ = "ticket_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    ticket_name: Mapped[str] = mapped_column(String(120))
    ticket_description: Mapped[str] = mapped_column(Text)
    ticket_category_channel: Mapped[str] = mapped_column(String(64))
    staff_role: Mapped[str] = mapped_column(String(64))
    panel_message: Mapped[str] = mapped_column(Text)
    panel_channel: Mapped[str] = mapped_column(String(64))


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(120), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    serial_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("server_id", "serial_number", name="uq_ticket_serial_per_server"),)


class ApplicationType(Base):
    __tablename__ = "application_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    application_name: Mapped[str] = mapped_column(String(255))
    category_channel: Mapped[str] = mapped_column(String(64))
    staff_role: Mapped[str] = mapped_column(String(64))

    questions: Mapped[list["Question"]] = relationship(cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_type: Mapped[int] = mapped_column(ForeignKey("application_types.id", ondelete="CASCADE"), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(120))
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    answers: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="submitted")


class Panel(Base):
    __tablename__ = "panels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    panel_type: Mapped[str] = mapped_column(String(30))
    channel_id: Mapped[str] = mapped_column(String(64))
    message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    buttons: Mapped[list] = mapped_column(JSON)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
