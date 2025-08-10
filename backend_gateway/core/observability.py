"""OpenTelemetry observability configuration for PrepSense backend."""

import logging
from typing import Optional

from fastapi import FastAPI
from opentelemetry import metrics, trace

# from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # Temporarily disabled due to dependency issues
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

logger = logging.getLogger(__name__)


def setup_tracing(
    service_name: str = "prepsense-backend",
    service_version: str = "1.4.0",
    environment: str = "development",
    jaeger_endpoint: Optional[str] = None,
) -> None:
    """Setup distributed tracing with OpenTelemetry."""

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "environment": environment,
        }
    )

    # Setup tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Setup Jaeger exporter if endpoint provided (temporarily disabled)
    # if jaeger_endpoint or os.getenv("JAEGER_ENDPOINT"):
    #     endpoint = jaeger_endpoint or os.getenv("JAEGER_ENDPOINT")
    #
    #     jaeger_exporter = JaegerExporter(
    #         agent_host_name=endpoint.split("://")[-1].split(":")[0],
    #         agent_port=int(endpoint.split(":")[-1]) if ":" in endpoint else 14268,
    #     )
    #
    #     span_processor = BatchSpanProcessor(jaeger_exporter)
    #     tracer_provider.add_span_processor(span_processor)
    #
    #     logger.info(f"Jaeger tracing configured: {endpoint}")
    logger.info("Jaeger tracing temporarily disabled due to dependency issues")
    # else:
    #     logger.info("Tracing configured without Jaeger exporter")


def setup_metrics(
    service_name: str = "prepsense-backend",
    service_version: str = "1.4.0",
    environment: str = "development",
) -> None:
    """Setup metrics collection with OpenTelemetry."""

    # Create resource
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "environment": environment,
        }
    )

    # Setup metrics provider (basic setup - can be enhanced with exporters)
    meter_provider = MeterProvider(resource=resource)
    metrics.set_meter_provider(meter_provider)

    logger.info("Metrics collection configured")


def instrument_fastapi(app: FastAPI, enable_db_instrumentation: bool = True) -> None:
    """Instrument FastAPI application with OpenTelemetry."""

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics,docs,redoc,openapi.json")

    # Add custom tracing for specific operations
    setup_custom_tracing(app)

    logger.info("FastAPI instrumentation configured")


def setup_custom_tracing(app: FastAPI) -> None:
    """Setup custom tracing for specific operations."""

    # Get tracer
    tracer = trace.get_tracer(__name__)

    # Custom middleware for enhanced tracing
    @app.middleware("http")
    async def tracing_middleware(request, call_next):
        # Start a span for the request
        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname,
                "user_agent.original": request.headers.get("user-agent", ""),
            },
        ) as span:

            # Process request
            response = await call_next(request)

            # Add response attributes
            span.set_attributes(
                {
                    "http.status_code": response.status_code,
                    "http.response_size": response.headers.get("content-length", 0),
                }
            )

            # Set span status
            if response.status_code >= 400:
                span.set_status(trace.Status(trace.StatusCode.ERROR))

            return response


class TracedService:
    """Base class for services with tracing support."""

    def __init__(self, service_name: str):
        self.tracer = trace.get_tracer(service_name)
        self.service_name = service_name

    def trace_method(self, method_name: str, **attributes):
        """Context manager for tracing service methods."""
        return self.tracer.start_as_current_span(
            f"{self.service_name}.{method_name}", attributes=attributes
        )


class CrewAITracer(TracedService):
    """Specialized tracer for CrewAI operations."""

    def __init__(self):
        super().__init__("crewai")

    def trace_agent_execution(self, agent_name: str, task_type: str, **attributes):
        """Trace CrewAI agent execution."""
        return self.tracer.start_as_current_span(
            f"crewai.agent.{agent_name}",
            attributes={"agent.name": agent_name, "agent.task_type": task_type, **attributes},
        )

    def trace_crew_execution(self, crew_name: str, **attributes):
        """Trace CrewAI crew execution."""
        return self.tracer.start_as_current_span(
            f"crewai.crew.{crew_name}", attributes={"crew.name": crew_name, **attributes}
        )


class DatabaseTracer(TracedService):
    """Specialized tracer for database operations."""

    def __init__(self):
        super().__init__("database")

    def trace_query(self, operation: str, table: str = None, **attributes):
        """Trace database queries."""
        span_name = f"db.{operation}"
        if table:
            span_name += f".{table}"

        return self.tracer.start_as_current_span(
            span_name, attributes={"db.operation": operation, "db.table": table, **attributes}
        )


# Global tracer instances
crewai_tracer = CrewAITracer()
database_tracer = DatabaseTracer()


def get_crewai_tracer() -> CrewAITracer:
    """Get CrewAI tracer instance."""
    return crewai_tracer


def get_database_tracer() -> DatabaseTracer:
    """Get database tracer instance."""
    return database_tracer


# Decorator for tracing functions
def trace_function(operation_name: str = None, **span_attributes):
    """Decorator to add tracing to functions."""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name, attributes=span_attributes) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name, attributes=span_attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def setup_observability(
    app: FastAPI,
    service_name: str = "prepsense-backend",
    service_version: str = "1.4.0",
    environment: str = "development",
) -> None:
    """Setup complete observability stack."""

    # Setup tracing
    setup_tracing(
        service_name=service_name, service_version=service_version, environment=environment
    )

    # Setup metrics
    setup_metrics(
        service_name=service_name, service_version=service_version, environment=environment
    )

    # Instrument FastAPI
    instrument_fastapi(app)

    logger.info(
        "Observability stack configured",
        service_name=service_name,
        service_version=service_version,
        environment=environment,
    )


# Example usage for CrewAI agents
def trace_crewai_agent(agent_name: str, task_type: str = "unknown"):
    """Decorator for tracing CrewAI agents."""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_crewai_tracer()

            with tracer.trace_agent_execution(agent_name=agent_name, task_type=task_type) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("agent.result_size", len(str(result)) if result else 0)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


# Example usage for database operations
def trace_database_operation(operation: str, table: str = None):
    """Decorator for tracing database operations."""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_database_tracer()

            with tracer.trace_query(operation=operation, table=table) as span:
                try:
                    result = await func(*args, **kwargs)

                    # Add result metadata
                    if hasattr(result, "__len__"):
                        span.set_attribute("db.rows_affected", len(result))

                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator
