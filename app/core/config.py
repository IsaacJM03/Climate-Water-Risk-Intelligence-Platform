from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+aiomysql://climate_user:climate_pass@localhost:3306/climate_db"
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


settings = Settings()
