from pydantic import BaseSettings, AnyHttpUrl, validator
from typing import List

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] | List[str] = []
    BIGQUERY_PROJECT: str = ""
    BIGQUERY_DATASET: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i]
        return v

settings = Settings()

