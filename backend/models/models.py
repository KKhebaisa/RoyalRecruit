"""
RoyalRecruit – SQLAlchemy ORM models.
All tables are defined here and imported by Alembic / the lifespan handler.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.connection import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class TicketStatus(str, enum.Enum):
    open   = "open"
    closed = "closed"
    locked = "locked"


class ApplicationStatus(str, enum.Enum):
    pending  = "pending"
    approved = "approved"
    rejected = "rejected"


class PanelType(str, enum.Enum):
    ticket      = "ticket"
    application = "application"


# ─────────────────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    discord_id    = Column(String(32), unique=True, nullable=False, index=True)
    username      = Column(String(100), nullable=False)
    discriminator = Column(String(10), nullable=True)
    avatar        = Column(String(256), nullable=True)
    access_token  = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True), default=utcnow)
    updated_at    = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    tickets      = relationship("Ticket",      back_populates="user")
    applications = relationship("Application", back_populates="user")


# ─────────────────────────────────────────────────────────────────────────────
# Servers (Guilds)
# ─────────────────────────────────────────────────────────────────────────────

class Server(Base):
    __tablename__ = "servers"

    id               = Column(Integer, primary_key=True, index=True)
    discord_server_id= Column(String(32), unique=True, nullable=False, index=True)
    name             = Column(String(200), nullable=False)
    icon             = Column(String(256), nullable=True)
    owner_discord_id = Column(String(32), nullable=False)
    log_channel_id   = Column(String(32), nullable=True)
    created_at       = Column(DateTime(timezone=True), default=utcnow)

    ticket_types      = relationship("TicketType",      back_populates="server", cascade="all, delete-orphan")
    application_types = relationship("ApplicationType", back_populates="server", cascade="all, delete-orphan")
    panels            = relationship("Panel",           back_populates="server", cascade="all, delete-orphan")
    tickets           = relationship("Ticket",          back_populates="server")
    applications      = relationship("Application",     back_populates="server")
    ticket_counters   = relationship("TicketCounter",   back_populates="server", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# Ticket Types (configurations)
# ─────────────────────────────────────────────────────────────────────────────

class TicketType(Base):
    __tablename__ = "ticket_types"

    id                    = Column(Integer, primary_key=True, index=True)
    server_id             = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    ticket_name           = Column(String(100), nullable=False)
    ticket_description    = Column(Text, nullable=True)
    ticket_category_id    = Column(String(32), nullable=True)   # Discord category channel ID
    staff_role_id         = Column(String(32), nullable=True)   # Discord role ID
    panel_message         = Column(Text, nullable=True)
    button_label          = Column(String(80), nullable=True)
    button_emoji          = Column(String(50), nullable=True)
    created_at            = Column(DateTime(timezone=True), default=utcnow)

    server  = relationship("Server",  back_populates="ticket_types")
    tickets = relationship("Ticket",  back_populates="ticket_type")
    panels  = relationship("Panel",   secondary="panel_ticket_types", back_populates="ticket_types")


# ─────────────────────────────────────────────────────────────────────────────
# Application Types (configurations)
# ─────────────────────────────────────────────────────────────────────────────

class ApplicationType(Base):
    __tablename__ = "application_types"

    id                 = Column(Integer, primary_key=True, index=True)
    server_id          = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    application_name   = Column(String(100), nullable=False)
    category_id        = Column(String(32), nullable=True)
    staff_role_id      = Column(String(32), nullable=True)
    welcome_message    = Column(Text, nullable=True)
    completion_message = Column(Text, nullable=True)
    button_label       = Column(String(80), nullable=True)
    button_emoji       = Column(String(50), nullable=True)
    created_at         = Column(DateTime(timezone=True), default=utcnow)

    server       = relationship("Server",      back_populates="application_types")
    questions    = relationship("Question",    back_populates="application_type",
                                cascade="all, delete-orphan", order_by="Question.order_index")
    applications = relationship("Application", back_populates="application_type")
    panels       = relationship("Panel",       secondary="panel_application_types",
                                back_populates="application_types")


# ─────────────────────────────────────────────────────────────────────────────
# Questions
# ─────────────────────────────────────────────────────────────────────────────

class Question(Base):
    __tablename__ = "questions"

    id                  = Column(Integer, primary_key=True, index=True)
    application_type_id = Column(Integer, ForeignKey("application_types.id", ondelete="CASCADE"), nullable=False)
    question_text       = Column(Text, nullable=False)
    order_index         = Column(Integer, nullable=False, default=0)

    application_type = relationship("ApplicationType", back_populates="questions")


# ─────────────────────────────────────────────────────────────────────────────
# Ticket Counter (per-server serial numbers)
# ─────────────────────────────────────────────────────────────────────────────

class TicketCounter(Base):
    __tablename__ = "ticket_counters"
    __table_args__ = (UniqueConstraint("server_id", "ticket_type_id"),)

    id             = Column(Integer, primary_key=True)
    server_id      = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    ticket_type_id = Column(Integer, ForeignKey("ticket_types.id", ondelete="CASCADE"), nullable=False)
    counter        = Column(Integer, nullable=False, default=0)

    server = relationship("Server", back_populates="ticket_counters")


# ─────────────────────────────────────────────────────────────────────────────
# Tickets
# ─────────────────────────────────────────────────────────────────────────────

class Ticket(Base):
    __tablename__ = "tickets"

    id             = Column(Integer, primary_key=True, index=True)
    server_id      = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    ticket_type_id = Column(Integer, ForeignKey("ticket_types.id"), nullable=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_id     = Column(String(32), nullable=True)   # Discord channel ID
    serial         = Column(Integer,    nullable=False)
    status         = Column(Enum(TicketStatus), default=TicketStatus.open, nullable=False)
    transcript     = Column(Text, nullable=True)
    created_at     = Column(DateTime(timezone=True), default=utcnow)
    closed_at      = Column(DateTime(timezone=True), nullable=True)

    server      = relationship("Server",     back_populates="tickets")
    user        = relationship("User",       back_populates="tickets")
    ticket_type = relationship("TicketType", back_populates="tickets")


# ─────────────────────────────────────────────────────────────────────────────
# Applications
# ─────────────────────────────────────────────────────────────────────────────

class Application(Base):
    __tablename__ = "applications"

    id                  = Column(Integer, primary_key=True, index=True)
    server_id           = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    application_type_id = Column(Integer, ForeignKey("application_types.id"), nullable=False)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_id          = Column(String(32), nullable=True)
    answers             = Column(JSON, nullable=True)   # {question_id: answer_text}
    status              = Column(Enum(ApplicationStatus), default=ApplicationStatus.pending, nullable=False)
    reviewer_discord_id = Column(String(32), nullable=True)
    review_note         = Column(Text, nullable=True)
    created_at          = Column(DateTime(timezone=True), default=utcnow)
    reviewed_at         = Column(DateTime(timezone=True), nullable=True)

    server           = relationship("Server",          back_populates="applications")
    user             = relationship("User",            back_populates="applications")
    application_type = relationship("ApplicationType", back_populates="applications")


# ─────────────────────────────────────────────────────────────────────────────
# Panels
# ─────────────────────────────────────────────────────────────────────────────

class Panel(Base):
    __tablename__ = "panels"

    id                = Column(Integer, primary_key=True, index=True)
    server_id         = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    panel_type        = Column(Enum(PanelType), nullable=False)
    title             = Column(String(256), nullable=False)
    description       = Column(Text, nullable=True)
    color             = Column(Integer, nullable=True, default=0x5865F2)  # Discord blurple
    channel_id        = Column(String(32), nullable=True)
    message_id        = Column(String(32), nullable=True)
    created_at        = Column(DateTime(timezone=True), default=utcnow)

    server            = relationship("Server",          back_populates="panels")
    ticket_types      = relationship("TicketType",      secondary="panel_ticket_types",
                                     back_populates="panels")
    application_types = relationship("ApplicationType", secondary="panel_application_types",
                                     back_populates="panels")


# ─────────────────────────────────────────────────────────────────────────────
# Association tables
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Table

panel_ticket_types = Table(
    "panel_ticket_types", Base.metadata,
    Column("panel_id",       Integer, ForeignKey("panels.id",       ondelete="CASCADE"), primary_key=True),
    Column("ticket_type_id", Integer, ForeignKey("ticket_types.id", ondelete="CASCADE"), primary_key=True),
)

panel_application_types = Table(
    "panel_application_types", Base.metadata,
    Column("panel_id",            Integer, ForeignKey("panels.id",            ondelete="CASCADE"), primary_key=True),
    Column("application_type_id", Integer, ForeignKey("application_types.id", ondelete="CASCADE"), primary_key=True),
)


# ─────────────────────────────────────────────────────────────────────────────
# Audit Logs
# ─────────────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id            = Column(Integer, primary_key=True, index=True)
    server_id     = Column(Integer, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False)
    event_type    = Column(String(64), nullable=False)
    actor_discord_id = Column(String(32), nullable=True)
    target_discord_id= Column(String(32), nullable=True)
    details       = Column(JSON, nullable=True)
    created_at    = Column(DateTime(timezone=True), default=utcnow)

    server = relationship("Server")
