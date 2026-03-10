from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RoyalRecruit API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/royalrecruit"
    discord_client_id: str = ""
    discord_client_secret: str = ""
    discord_redirect_uri: str = "http://localhost:3000/api/auth/callback"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    dashboard_origin: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
