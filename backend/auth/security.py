from datetime import datetime, timedelta, timezone
from jose import jwt

from backend.core.config import get_settings


def create_access_token(subject: str, expires_minutes: int = 60 * 24) -> str:
    settings = get_settings()
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)
    return jwt.encode({"sub": subject, "exp": expire}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
