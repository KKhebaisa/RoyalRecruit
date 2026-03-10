from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.security import create_access_token
from backend.database.session import get_db
from backend.models.entities import User
from backend.models.schemas import OAuthCallbackRequest, TokenResponse
from backend.services.discord_oauth import exchange_code, fetch_discord_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/discord/callback", response_model=TokenResponse)
async def discord_callback(payload: OAuthCallbackRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        token_payload = await exchange_code(payload.code)
        data = await fetch_discord_user(token_payload["access_token"])
        user_data = data["user"]
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Discord OAuth failed") from exc

    user = db.query(User).filter(User.discord_id == user_data["id"]).first()
    if not user:
        user = User(discord_id=user_data["id"], username=user_data["username"])
        db.add(user)
    else:
        user.username = user_data["username"]
    db.commit()

    jwt_token = create_access_token(subject=user.discord_id)
    return TokenResponse(access_token=jwt_token)
