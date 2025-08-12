"""
Configuration globale de l'application FastAPI
"""

from functools import lru_cache
from pydantic import validator
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    """Configuration de l'application avec Pydantic"""
    
    # Application
    app_name: str = "Strava Poster API"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"
    
    # Strava API
    strava_client_id: str
    strava_client_secret: str
    strava_redirect_uri: str = "http://localhost:8000/auth/callback"
    
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Poster Generation
    poster_storage_path: str = "./storage/posters"
    max_poster_size_mb: int = 50
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: list[str] = ["*"]
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://your-frontend-domain.com"
    ]
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            return secrets.token_urlsafe(32)
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        if v.lower() not in ["development", "staging", "production"]:
            raise ValueError("Environment must be development, staging, or production")
        return v.lower()
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Instance globale
settings = get_settings()