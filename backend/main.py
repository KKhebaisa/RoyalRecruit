"""
RoyalRecruit Backend API
Main FastAPI application entry point — includes rate limiting and CORS.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from database.connection import engine, Base
from routers import auth, guilds, tickets, applications, panels, logs
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Rate limiter (shared instance imported by routers) ─────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown lifecycle."""
    logger.info("Starting RoyalRecruit API …")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")
    yield
    logger.info("Shutting down …")
    await engine.dispose()


app = FastAPI(
    title="RoyalRecruit API",
    description="Backend for RoyalRecruit Discord bot & dashboard",
    version="1.0.0",
    lifespan=lifespan,
    # Disable docs in production to reduce attack surface
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# ── Rate limiting middleware ───────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/api/auth",         tags=["Authentication"])
app.include_router(guilds.router,       prefix="/api/guilds",       tags=["Guilds"])
app.include_router(tickets.router,      prefix="/api/tickets",      tags=["Tickets"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(panels.router,       prefix="/api/panels",       tags=["Panels"])
app.include_router(logs.router,         prefix="/api/logs",         tags=["Logs"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "royalrecruit-api"}
