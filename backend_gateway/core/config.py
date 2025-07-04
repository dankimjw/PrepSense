"""
Configuration settings for PrepSense backend application.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
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
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8001
    VISION_URL: str = "http://localhost:8001/detect"
    
    # Database Configuration
    GCP_PROJECT_ID: str = "adsp-34002-on02-prep-sense"
    
    # Database Type Selection
    DB_TYPE: Optional[str] = "postgres"  # Only PostgreSQL is supported
    
    # PostgreSQL Configuration
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = 5432
    POSTGRES_DATABASE: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    CLOUD_SQL_CONNECTION_NAME: Optional[str] = None
    POSTGRES_USE_IAM: Optional[bool] = False
    POSTGRES_IAM_USER: Optional[str] = None
    
    # Google Cloud Configuration
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # OpenAI Configuration
    OPENAI_API_KEY_FILE: str = "config/openai_key.txt"
    
    # Spoonacular Configuration
    SPOONACULAR_API_KEY: Optional[str] = None
    
    # Development Settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()