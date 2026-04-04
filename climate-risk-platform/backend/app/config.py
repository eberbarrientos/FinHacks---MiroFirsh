"""Application configuration using Pydantic BaseSettings"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings with environment-based configuration"""
    
    # Database - defaults to SQLite for zero-setup local dev
    database_url: str = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'climate_risk.db')}"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_recycle: int = 3600
    
    # Redis (optional - works without it)
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_ttl: int = 3600
    
    # MiroFish
    mirofish_api_url: str = "http://localhost:8080"
    mirofish_timeout: int = 60
    mirofish_retry_attempts: int = 3
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Application
    log_level: str = "INFO"
    max_upload_size: int = 10_000_000  # 10MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
