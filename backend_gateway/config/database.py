"""
Database configuration for PrepSense
Supports PostgreSQL backend only
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    POSTGRES = "postgres"


class DatabaseConfig:
    def __init__(self):
        # Always use PostgreSQL
        self.db_type = DatabaseType.POSTGRES

        # PostgreSQL configuration
        self.postgres_config = {
            "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DATABASE", "prepsense"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
        }

        # Cloud SQL specific
        self.cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")

    def get_database_service(self):
        """Get the PostgreSQL database service"""
        # Check if IAM authentication is enabled
        use_iam = os.getenv("POSTGRES_USE_IAM", "false").lower() == "true"

        if use_iam:
            from backend_gateway.services.postgres_iam_service import PostgresIAMService

            logger.info("Using PostgreSQL with IAM authentication")

            # Get user email from environment or use service account
            iam_user = os.getenv("POSTGRES_IAM_USER")
            if not iam_user:
                # Try to get from gcloud config
                import subprocess

                try:
                    result = subprocess.run(
                        ["gcloud", "config", "get-value", "account"], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        iam_user = result.stdout.strip()
                except:
                    pass

            if not iam_user:
                raise ValueError("POSTGRES_IAM_USER must be set when using IAM authentication")

            iam_config = self.postgres_config.copy()
            iam_config["user"] = iam_user
            # Remove password as it will be replaced with token
            iam_config.pop("password", None)

            return PostgresIAMService(iam_config)
        else:
            from backend_gateway.services.postgres_service import PostgresService

            logger.info("Using PostgreSQL with password authentication")

            # Use Cloud SQL proxy if connection name is provided
            if self.cloud_sql_connection_name and self.postgres_config["host"] == "127.0.0.1":
                logger.info("Using Cloud SQL Proxy connection")

            return PostgresService(self.postgres_config)

    def get_pantry_service(self):
        """Get pantry service with appropriate database backend"""
        from backend_gateway.services.pantry_service import PantryService

        db_service = self.get_database_service()
        return PantryService(db_service)

    def is_postgres(self) -> bool:
        """Check if using PostgreSQL"""
        return True  # Always using PostgreSQL


# Global instance
db_config = DatabaseConfig()


def get_database_service():
    """Get the configured database service"""
    return db_config.get_database_service()


def get_pantry_service():
    """Get the configured pantry service"""
    return db_config.get_pantry_service()
