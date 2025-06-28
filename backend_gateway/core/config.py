"""
Configuration settings for PrepSense backend application.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    
    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8082",
        "exp://localhost:8082",
        "exp://192.168.1.195:8082",  # For Expo development
        "*"  # Allow all origins for development
    ]
    
    # Server Configuration
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8001"))
    VISION_URL: str = os.getenv("VISION_URL", "http://localhost:8001/detect")
    
    # Database Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "adsp-34002-on02-prep-sense")
    BIGQUERY_PROJECT: str = os.getenv("BIGQUERY_PROJECT", os.getenv("GCP_PROJECT_ID", "adsp-34002-on02-prep-sense"))
    BIGQUERY_DATASET: str = os.getenv("BIGQUERY_DATASET", "Inventory")
    
    # Google Cloud Configuration
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # OpenAI Configuration
    OPENAI_API_KEY_FILE: str = os.getenv("OPENAI_API_KEY_FILE", "config/openai_key.txt")
    
    # Development Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()