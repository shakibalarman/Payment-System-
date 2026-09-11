from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "PayFlow"
    env: str = "development"
    database_url: str = "sqlite:///./payflow.db"
    jwt_secret: str = "change-me-super-secret-jwt-key-min-32-chars!!"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    redis_url: str = "redis://localhost:6379/0"
    payment_provider_secret: str = "mock-provider-secret-dev-only"
    payment_provider_public_key: str = "mock-provider-public-dev-only"
    payment_provider_default: str = "mock"
    platform_fee_percent: float = 1.5
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@payflow.example.com"
    frontend_url: str = "http://localhost:3000"

    class Meta:
        pass

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
