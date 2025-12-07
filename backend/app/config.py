"""Application configuration using Pydantic Settings"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Qubic Risk Radar"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://qubic_radar:password@localhost:5432/qubic_radar_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # SMTP Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "Qubic Risk Radar"
    
    # Security
    WEBHOOK_SECRET: str = "change_me_in_production"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Discord Webhooks
    DISCORD_WEBHOOK_URL_CRITICAL: str = ""
    DISCORD_WEBHOOK_URL_WARNING: str = ""
    DISCORD_WEBHOOK_URL_INFO: str = ""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # SendGrid (keeping for alerts, not verification)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@qubicradar.io"
    
    # Discord Bot
    DISCORD_BOT_TOKEN: str = ""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    
    # Notification Settings
    NOTIFICATION_RETRY_MAX: int = 3
    NOTIFICATION_RETRY_DELAY: int = 1  # seconds
    NOTIFICATION_TIMEOUT: int = 10  # seconds
    
    # Rule Engine
    RULE_EVALUATION_ENABLED: bool = True
    DEDUPLICATION_ENABLED: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
