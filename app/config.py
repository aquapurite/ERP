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
        "https://aquapurite.org",
        # D2C Storefront
        "https://www.aquapurite.com",
        "https://aquapurite.com",
    ]

    # Email/SMTP Settings (Gmail)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # Your Gmail address
    SMTP_PASSWORD: str = ""  # Gmail App Password
    SMTP_FROM_EMAIL: str = ""  # Sender email (defaults to SMTP_USER)
    SMTP_FROM_NAME: str = "Aquapurite ERP"

    # Frontend URL for email links
    FRONTEND_URL: str = "https://erp-woad-eight.vercel.app"

    # Redis Cache Settings
    REDIS_URL: Optional[str] = None  # e.g., "redis://localhost:6379/0"
    CACHE_ENABLED: bool = True
    SERVICEABILITY_CACHE_TTL: int = 3600  # 1 hour for pincode serviceability
    PRODUCT_CACHE_TTL: int = 300  # 5 minutes for product data
    STOCK_CACHE_TTL: int = 30  # 30 seconds for real-time stock (short for accuracy)
    CATEGORY_CACHE_TTL: int = 1800  # 30 minutes for categories
    COMPANY_CACHE_TTL: int = 3600  # 1 hour for company info

    # Razorpay Payment Gateway
    RAZORPAY_KEY_ID: str = ""  # Razorpay Key ID
    RAZORPAY_KEY_SECRET: str = ""  # Razorpay Key Secret
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None  # For webhook verification

    # SMS Gateway (MSG91)
    MSG91_AUTH_KEY: str = ""  # MSG91 Auth Key
    MSG91_SENDER_ID: str = "AQUAPU"  # 6-char sender ID
    MSG91_TEMPLATE_ID_ORDER_CONFIRMED: str = ""  # DLT Template ID for order confirmation
    MSG91_TEMPLATE_ID_ORDER_SHIPPED: str = ""  # DLT Template ID for order shipped
    MSG91_TEMPLATE_ID_OTP: str = ""  # DLT Template ID for OTP

    # D2C Storefront URLs
    D2C_FRONTEND_URL: str = "https://www.aquapurite.com"

    # Shiprocket Integration
    SHIPROCKET_EMAIL: str = ""  # Shiprocket account email
    SHIPROCKET_PASSWORD: str = ""  # Shiprocket account password
    SHIPROCKET_API_URL: str = "https://apiv2.shiprocket.in/v1/external"
    SHIPROCKET_WEBHOOK_SECRET: Optional[str] = None  # For webhook verification
    SHIPROCKET_DEFAULT_PICKUP_LOCATION: str = ""  # Default pickup location name
    SHIPROCKET_AUTO_SHIP: bool = False  # Auto-assign courier on order creation

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
