"""Structured logging configuration for PrepSense backend using structlog."""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory
from structlog.types import EventDict

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def add_app_context(logger: Any, name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log events."""
    event_dict["service"] = "prepsense-backend"
    event_dict["version"] = "1.4.0"
    return event_dict


def add_timestamp_utc(logger: Any, name: str, event_dict: EventDict) -> EventDict:
    """Add UTC timestamp to log events."""
    import datetime

    event_dict["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    return event_dict


def setup_logging(
    level: str = "INFO", json_format: bool = None, enable_file_logging: bool = True
) -> None:
    """Setup structured logging with structlog.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON format. If None, auto-detect based on environment
        enable_file_logging: Whether to write logs to files
    """

    # Auto-detect JSON format based on environment
    if json_format is None:
        json_format = os.getenv("LOG_FORMAT", "").lower() == "json"

    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        add_app_context,
        add_timestamp_utc,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        # JSON format for production/structured logging
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Human-readable format for development
        processors.extend(
            [
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s", stream=sys.stdout, level=getattr(logging, level.upper())
    )

    # Setup file logging if enabled
    if enable_file_logging:
        setup_file_logging(level, json_format)

    # Configure third-party loggers
    configure_third_party_loggers(level)

    logger = structlog.get_logger()
    logger.info(
        "Logging configured", level=level, json_format=json_format, file_logging=enable_file_logging
    )


def setup_file_logging(level: str, json_format: bool) -> None:
    """Setup file logging handlers."""
    import logging.handlers

    # Main application log
    app_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "prepsense.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    app_handler.setLevel(getattr(logging, level.upper()))

    # Error log (only errors and above)
    error_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "errors.log", maxBytes=5 * 1024 * 1024, backupCount=3  # 5MB
    )
    error_handler.setLevel(logging.ERROR)

    # CrewAI specific log
    crewai_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "crewai.log", maxBytes=5 * 1024 * 1024, backupCount=3  # 5MB
    )
    crewai_handler.setLevel(logging.INFO)

    # Format for file logs
    if json_format:
        formatter = logging.Formatter("%(message)s")
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    for handler in [app_handler, error_handler, crewai_handler]:
        handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)

    # Add CrewAI handler to specific logger
    crewai_logger = logging.getLogger("crewai")
    crewai_logger.addHandler(crewai_handler)
    crewai_logger.setLevel(logging.INFO)


def configure_third_party_loggers(level: str) -> None:
    """Configure third-party library loggers."""

    # Reduce verbosity of noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)

    # Keep important ones at INFO
    for logger_name in ["sqlalchemy", "alembic", "fastapi"]:
        logging.getLogger(logger_name).setLevel(logging.INFO)

    # CrewAI loggers
    logging.getLogger("crewai").setLevel(logging.INFO)

    # Database query logging (only in DEBUG mode)
    if level.upper() == "DEBUG":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


# Helper functions for structured logging
def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_api_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    path: str,
    status_code: int = None,
    duration_ms: float = None,
    user_id: str = None,
    error: Exception = None,
) -> None:
    """Log API request with structured data."""
    log_data = {
        "event_type": "api_request",
        "method": method,
        "path": path,
    }

    if status_code:
        log_data["status_code"] = status_code
    if duration_ms:
        log_data["duration_ms"] = duration_ms
    if user_id:
        log_data["user_id"] = user_id
    if error:
        log_data["error"] = str(error)
        log_data["error_type"] = type(error).__name__

    if error:
        logger.error("API request failed", **log_data)
    elif status_code and status_code >= 400:
        logger.warning("API request error", **log_data)
    else:
        logger.info("API request completed", **log_data)


def log_crewai_execution(
    logger: structlog.stdlib.BoundLogger,
    agent_name: str,
    task_type: str,
    status: str = "started",
    duration_ms: float = None,
    input_data: Dict[str, Any] = None,
    output_data: Dict[str, Any] = None,
    error: Exception = None,
) -> None:
    """Log CrewAI agent execution with structured data."""
    log_data = {
        "event_type": "crewai_execution",
        "agent_name": agent_name,
        "task_type": task_type,
        "status": status,
    }

    if duration_ms:
        log_data["duration_ms"] = duration_ms
    if input_data:
        # Truncate large data for logging
        log_data["input_size"] = len(str(input_data))
        log_data["input_preview"] = str(input_data)[:200]
    if output_data:
        log_data["output_size"] = len(str(output_data))
        log_data["output_preview"] = str(output_data)[:200]
    if error:
        log_data["error"] = str(error)
        log_data["error_type"] = type(error).__name__

    if error:
        logger.error("CrewAI execution failed", **log_data)
    elif status == "completed":
        logger.info("CrewAI execution completed", **log_data)
    else:
        logger.info("CrewAI execution status", **log_data)


def log_database_query(
    logger: structlog.stdlib.BoundLogger,
    query_type: str,
    table: str = None,
    duration_ms: float = None,
    rows_affected: int = None,
    error: Exception = None,
) -> None:
    """Log database query with structured data."""
    log_data = {
        "event_type": "database_query",
        "query_type": query_type,
    }

    if table:
        log_data["table"] = table
    if duration_ms:
        log_data["duration_ms"] = duration_ms
    if rows_affected is not None:
        log_data["rows_affected"] = rows_affected
    if error:
        log_data["error"] = str(error)
        log_data["error_type"] = type(error).__name__

    if error:
        logger.error("Database query failed", **log_data)
    elif duration_ms and duration_ms > 1000:
        logger.warning("Slow database query", **log_data)
    else:
        logger.info("Database query completed", **log_data)


# Context manager for logging execution blocks
class LogExecutionTime:
    """Context manager to log execution time of code blocks."""

    def __init__(self, logger: structlog.stdlib.BoundLogger, operation: str, **context_data):
        self.logger = logger
        self.operation = operation
        self.context_data = context_data
        self.start_time = None

    def __enter__(self):
        import time

        self.start_time = time.time()
        self.logger.info(f"{self.operation} started", **self.context_data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        duration_ms = round((time.time() - self.start_time) * 1000, 2)

        if exc_type:
            self.logger.error(
                f"{self.operation} failed",
                duration_ms=duration_ms,
                error=str(exc_val),
                error_type=exc_type.__name__,
                **self.context_data,
            )
        else:
            self.logger.info(
                f"{self.operation} completed", duration_ms=duration_ms, **self.context_data
            )


# Example usage:
if __name__ == "__main__":
    # Setup logging
    setup_logging(level="DEBUG", json_format=False)

    # Get logger
    logger = get_logger(__name__)

    # Test logging
    logger.info("Test log message", user_id="12345", operation="test")

    # Test structured logging functions
    log_api_request(logger, "GET", "/api/v1/recipes", 200, 145.5, "user123")

    # Test execution time logging
    with LogExecutionTime(logger, "test operation", user_id="123"):
        import time

        time.sleep(0.1)  # Simulate work
