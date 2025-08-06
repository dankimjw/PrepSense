"""
Configuration settings for PrepSense backend application.
"""

from typing import List, Optional
from pydantic import field_validator, ValidationError, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Allow direct OpenAI key if present (run_app may persist it)
    OPENAI_API_KEY: Optional[str] = None
    
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
    
    # CrewAI Configuration
    SERPER_API_KEY: Optional[str] = None
    
    # Development Settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DEMO_USER_ID: Optional[str] = None
    
    @field_validator('SPOONACULAR_API_KEY')
    @classmethod
    def validate_spoonacular_key(cls, v: Optional[str]) -> str:
        """Validate Spoonacular API key is provided."""
        if not v or v.strip() == "":
            raise ValueError(
                "SPOONACULAR_API_KEY is required. "
                "Get your API key at https://spoonacular.com/food-api"
            )
        if v == "your-spoonacular-api-key-here":
            raise ValueError(
                "SPOONACULAR_API_KEY has not been configured. "
                "Replace the placeholder with your actual API key."
            )
        return v.strip()
    
    @field_validator('POSTGRES_HOST')
    @classmethod
    def validate_postgres_host(cls, v: Optional[str]) -> str:
        """Validate PostgreSQL host is provided."""
        if not v or v.strip() == "":
            raise ValueError(
                "POSTGRES_HOST is required. "
                "This should be the Google Cloud SQL instance IP address."
            )
        return v.strip()
    
    @field_validator('POSTGRES_DATABASE')
    @classmethod
    def validate_postgres_database(cls, v: Optional[str]) -> str:
        """Validate PostgreSQL database name is provided."""
        if not v or v.strip() == "":
            raise ValueError(
                "POSTGRES_DATABASE is required. "
                "This should be 'prepsense' for the production database."
            )
        return v.strip()
    
    @field_validator('POSTGRES_USER')
    @classmethod
    def validate_postgres_user(cls, v: Optional[str]) -> str:
        """Validate PostgreSQL user is provided."""
        if not v or v.strip() == "":
            raise ValueError(
                "POSTGRES_USER is required. "
                "This should be 'postgres' or your assigned database user."
            )
        return v.strip()
    
    @field_validator('POSTGRES_PASSWORD')
    @classmethod
    def validate_postgres_password(cls, v: Optional[str]) -> str:
        """Validate PostgreSQL password is provided."""
        if not v or v.strip() == "":
            raise ValueError(
                "POSTGRES_PASSWORD is required. "
                "Get the database password from your team lead."
            )
        if v in ["your-password-here", "changeme", "password"]:
            raise ValueError(
                "POSTGRES_PASSWORD has not been properly configured. "
                "Replace the placeholder with the actual database password."
            )
        return v.strip()
    
    model_config = ConfigDict(
        env_file="../.env",
        case_sensitive=True,
        extra='allow'
    )


# Create settings instance
settings = Settings()