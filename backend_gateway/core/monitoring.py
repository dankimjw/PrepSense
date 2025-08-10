# # PrepSense - Smart Pantry Management System
# # Copyright (c) 2025 Daniel Kim. All rights reserved.
# #
# # This software is proprietary and confidential. Unauthorized copying
# # of this file, via any medium, is strictly prohibited.

"""Error monitoring and performance tracking configuration for PrepSense backend."""

import logging
import os
import time
from functools import wraps
from typing import Any, Optional

import sentry_sdk
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)

CREWAI_REQUESTS = Counter(
    "crewai_requests_total", "Total CrewAI agent requests", ["agent_type", "status"]
)

DATABASE_QUERIES = Counter(
    "database_queries_total", "Total database queries", ["query_type", "status"]
)


def init_sentry(environment: str = "development") -> None:
    """Initialize Sentry error tracking."""
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.warning("SENTRY_DSN not configured, error tracking disabled")
        return

    # Configure integrations
    integrations = [
        FastApiIntegration(auto_enabling_integrations=True),
        SqlalchemyIntegration(),
        LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        ),
    ]

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        integrations=integrations,
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% for profiling
        # Set custom tags
        tags={
            "service": "prepsense-backend",
            "version": "1.4.0",
        },
        # Filter out health check requests
        before_send_transaction=lambda event, hint: (
            None if event.get("request", {}).get("url", "").endswith("/health") else event
        ),
        # Add context about the request
        send_default_pii=False,  # Don't send personal info
    )

    logger.info(f"Sentry initialized for environment: {environment}")


def capture_crewai_metrics(agent_type: str, status: str = "success") -> None:
    """Capture metrics for CrewAI agent interactions."""
    CREWAI_REQUESTS.labels(agent_type=agent_type, status=status).inc()


def capture_database_metrics(query_type: str, status: str = "success") -> None:
    """Capture metrics for database interactions."""
    DATABASE_QUERIES.labels(query_type=query_type, status=status).inc()


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Extract endpoint pattern (remove IDs)
        endpoint = self._clean_endpoint(request.url.path)
        method = request.method

        try:
            response = await call_next(request)
            status = str(response.status_code)

            # Record metrics
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(
                time.time() - start_time
            )

            return response

        except Exception:
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status="500").inc()
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(
                time.time() - start_time
            )
            raise

    def _clean_endpoint(self, path: str) -> str:
        """Clean endpoint path for metrics (remove IDs)."""
        import re

        # Replace common ID patterns with placeholders
        path = re.sub(r"/\d+", "/{id}", path)
        path = re.sub(
            r"/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "/{uuid}", path
        )
        return path


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        # Generate request ID for tracing
        import uuid

        request_id = str(uuid.uuid4())[:8]

        # Log request start
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
            },
        )

        try:
            response = await call_next(request)

            # Log successful response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                },
            )

            return response

        except Exception as e:
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                },
                exc_info=True,
            )
            raise


def monitor_crewai_agent(agent_name: str):
    """Decorator to monitor CrewAI agent performance."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                capture_crewai_metrics(agent_name, "success")

                logger.info(
                    "CrewAI agent completed",
                    extra={
                        "agent": agent_name,
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                capture_crewai_metrics(agent_name, "error")

                logger.error(
                    "CrewAI agent failed",
                    extra={
                        "agent": agent_name,
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "error": str(e),
                        "status": "error",
                    },
                    exc_info=True,
                )

                # Send to Sentry with context
                with sentry_sdk.configure_scope() as scope:
                    scope.set_tag("component", "crewai")
                    scope.set_tag("agent", agent_name)
                    scope.set_context(
                        "agent_execution",
                        {
                            "duration_ms": round((time.time() - start_time) * 1000, 2),
                            "args": str(args)[:500],  # Truncate long args
                            "kwargs": str(kwargs)[:500],
                        },
                    )
                    sentry_sdk.capture_exception(e)

                raise

        return wrapper

    return decorator


def monitor_database_query(query_type: str):
    """Decorator to monitor database query performance."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                capture_database_metrics(query_type, "success")

                duration_ms = round((time.time() - start_time) * 1000, 2)

                if duration_ms > 1000:  # Log slow queries
                    logger.warning(
                        "Slow database query detected",
                        extra={
                            "query_type": query_type,
                            "duration_ms": duration_ms,
                        },
                    )

                return result

            except Exception as e:
                capture_database_metrics(query_type, "error")

                logger.error(
                    "Database query failed",
                    extra={
                        "query_type": query_type,
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "error": str(e),
                    },
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def setup_monitoring(app: FastAPI, environment: str = "development") -> None:
    """Setup comprehensive monitoring for the FastAPI app."""

    # Initialize Sentry
    init_sentry(environment)

    # Add monitoring middleware
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Expose Prometheus metrics."""
        return StarletteResponse(generate_latest(), media_type="text/plain")

    # Add health check with monitoring info
    @app.get("/monitoring/health")
    async def monitoring_health():
        """Health check with monitoring information."""
        return {
            "status": "healthy",
            "monitoring": {
                "sentry_enabled": bool(os.getenv("SENTRY_DSN")),
                "metrics_enabled": True,
                "environment": environment,
            },
        }

    logger.info("Monitoring setup complete")


# Context manager for Sentry transaction tracking
class SentryTransaction:
    """Context manager for Sentry transaction tracking."""

    def __init__(self, operation: str, name: str, **kwargs):
        self.operation = operation
        self.name = name
        self.transaction = None
        self.kwargs = kwargs

    def __enter__(self):
        self.transaction = sentry_sdk.start_transaction(
            op=self.operation, name=self.name, **self.kwargs
        )
        return self.transaction

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.transaction.set_status("internal_error")
        else:
            self.transaction.set_status("ok")
        self.transaction.finish()


# Utility function for manual error reporting
def report_error(error: Exception, context: Optional[dict[str, Any]] = None) -> None:
    """Manually report an error to Sentry with context."""
    with sentry_sdk.configure_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_tag(key, value)
        sentry_sdk.capture_exception(error)
