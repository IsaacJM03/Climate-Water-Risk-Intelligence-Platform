from __future__ import annotations

from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Low-level DB connection components — prefer these for local setups
    DB_USER: str = "climate_user"
    DB_PASSWORD: str = "S3cureP4ssw0rd2026!"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "climate_db"

    # Full URL may be provided directly; if omitted we build it from components
    DATABASE_URL: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-this-to-a-long-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FLOOD_RISK_THRESHOLD: float = 70.0
    DROUGHT_RISK_THRESHOLD: float = 65.0
    ALERT_THROTTLE_MINUTES: int = 30
    RISK_CACHE_TTL: int = 300
    APP_ENV: str = "production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL:
            password = quote_plus(self.DB_PASSWORD)
            self.DATABASE_URL = (
                f"mysql+aiomysql://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )


settings = Settings()
