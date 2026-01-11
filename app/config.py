from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, Union
from functools import lru_cache
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App Settings
    APP_NAME: str = "Consumer Durable Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS - accepts JSON string or list
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "https://erp-five-phi.vercel.app",
        "https://erp-woad-eight.vercel.app",
        "https://www.aquapurite.org",
        "https://aquapurite.org"
    ]

    # Email/SMTP Settings (Gmail)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # Your Gmail address
    SMTP_PASSWORD: str = ""  # Gmail App Password
    SMTP_FROM_EMAIL: str = ""  # Sender email (defaults to SMTP_USER)
    SMTP_FROM_NAME: str = "Aquapurite ERP"

    # Frontend URL for email links
    FRONTEND_URL: str = "https://erp-five-phi.vercel.app"

    # Redis Cache Settings
    REDIS_URL: Optional[str] = None  # e.g., "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    SERVICEABILITY_CACHE_TTL: int = 3600  # 1 hour in seconds
    PRODUCT_CACHE_TTL: int = 300  # 5 minutes in seconds

    # Razorpay Payment Gateway
    RAZORPAY_KEY_ID: str = ""  # Razorpay Key ID
    RAZORPAY_KEY_SECRET: str = ""  # Razorpay Key Secret
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None  # For webhook verification

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
