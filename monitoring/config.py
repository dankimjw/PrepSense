"""
Monitoring and alerting configuration for PrepSense.
"""
import logging
from typing import Optional

from pydantic import ConfigDict, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings


class MonitoringConfig(BaseSettings):
    """Configuration for monitoring and alerting."""

    # General settings
    ENABLED: bool = Field(
        default=True,
        env="MONITORING_ENABLED",
        description="Enable/disable all monitoring"
    )

    # Error tracking
    SENTRY_DSN: Optional[HttpUrl] = Field(
        default=None,
        env="SENTRY_DSN",
        description="Sentry DSN for error tracking"
    )

    # Performance monitoring
    ENABLE_PERFORMANCE_MONITORING: bool = Field(
        default=True,
        env="ENABLE_PERFORMANCE_MONITORING",
        description="Enable performance monitoring"
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # Alert thresholds
    ERROR_RATE_THRESHOLD: float = Field(
        default=0.01,  # 1% error rate
        env="ERROR_RATE_THRESHOLD",
        description="Error rate threshold for triggering alerts"
    )

    # Alert channels
    ALERT_EMAILS: list[str] = Field(
        default_factory=list,
        env="ALERT_EMAILS",
        description="List of email addresses to receive alerts"
    )

    # Feature-specific monitoring
    API_RESPONSE_TIME_WARNING_MS: int = Field(
        default=1000,  # 1 second
        env="API_RESPONSE_TIME_WARNING_MS",
        description="Warning threshold for API response time in milliseconds"
    )

    # Database monitoring
    DB_QUERY_WARNING_MS: int = Field(
        default=500,  # 0.5 seconds
        env="DB_QUERY_WARNING_MS",
        description="Warning threshold for database query time in milliseconds"
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that LOG_LEVEL is a valid logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


# Initialize monitoring config
monitoring_config = MonitoringConfig()


def configure_logging() -> None:
    """Configure logging based on the monitoring configuration."""
    log_level = getattr(logging, monitoring_config.LOG_LEVEL)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            # Add file handler if needed
            # logging.FileHandler('app.log')
        ]
    )

    # Set log level for external libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
