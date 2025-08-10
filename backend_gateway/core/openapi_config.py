"""
Enhanced OpenAPI configuration for PrepSense backend API
Provides comprehensive schema documentation, validation, and contract testing support
"""

import json
import logging
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

# Custom OpenAPI metadata
OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "Health check and system monitoring endpoints",
    },
    {
        "name": "users",
        "description": "User management and authentication operations",
    },
    {
        "name": "pantry",
        "description": "Pantry management and inventory tracking",
    },
    {
        "name": "recipes",
        "description": "Recipe management and AI-powered recommendations",
    },
    {
        "name": "ocr",
        "description": "Optical Character Recognition for receipt processing",
    },
    {
        "name": "images",
        "description": "Image processing and upload operations",
    },
    {
        "name": "crewai",
        "description": "AI agent operations and task execution",
    },
    {
        "name": "monitoring",
        "description": "Application monitoring and observability endpoints",
    },
    {
        "name": "admin",
        "description": "Administrative operations and system management",
    },
]

# API Contact and license info
API_CONTACT = {
    "name": "PrepSense Development Team",
    "email": "dev@prepsense.com",
    "url": "https://github.com/dankimjw/PrepSense",
}

API_LICENSE = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT",
}

# Servers configuration for different environments
SERVERS = [
    {
        "url": "http://localhost:8001",
        "description": "Development server",
    },
    {
        "url": "http://localhost:8002",
        "description": "Testing server",
    },
    {
        "url": "https://api.prepsense.com",
        "description": "Production server",
    },
]

# Common response schemas
COMMON_RESPONSES = {
    400: {
        "description": "Bad Request",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string", "example": "Invalid request parameters"},
                        "error_code": {"type": "string", "example": "INVALID_REQUEST"},
                        "timestamp": {"type": "string", "format": "date-time"},
                    },
                    "required": ["detail"],
                }
            }
        },
    },
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string", "example": "Authentication required"},
                        "error_code": {"type": "string", "example": "UNAUTHORIZED"},
                        "timestamp": {"type": "string", "format": "date-time"},
                    },
                    "required": ["detail"],
                }
            }
        },
    },
    403: {
        "description": "Forbidden",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string", "example": "Insufficient permissions"},
                        "error_code": {"type": "string", "example": "FORBIDDEN"},
                        "timestamp": {"type": "string", "format": "date-time"},
                    },
                    "required": ["detail"],
                }
            }
        },
    },
    404: {
        "description": "Not Found",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string", "example": "Resource not found"},
                        "error_code": {"type": "string", "example": "NOT_FOUND"},
                        "timestamp": {"type": "string", "format": "date-time"},
                    },
                    "required": ["detail"],
                }
            }
        },
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "loc": {"type": "array", "items": {"type": "string"}},
                                    "msg": {"type": "string"},
                                    "type": {"type": "string"},
                                },
                                "required": ["loc", "msg", "type"],
                            },
                        },
                        "error_code": {"type": "string", "example": "VALIDATION_ERROR"},
                        "timestamp": {"type": "string", "format": "date-time"},
                    },
                    "required": ["detail"],
                }
            }
        },
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string", "example": "Internal server error"},
                        "error_code": {"type": "string", "example": "INTERNAL_ERROR"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "incident_id": {"type": "string", "example": "inc_123456"},
                    },
                    "required": ["detail"],
                }
            }
        },
    },
}

# Security schemes
SECURITY_SCHEMES = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token authentication",
    },
    "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API key authentication for external services",
    },
}


def custom_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema

    # Generate base schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
        servers=SERVERS,
    )

    # Add contact and license information
    openapi_schema["info"]["contact"] = API_CONTACT
    openapi_schema["info"]["license"] = API_LICENSE

    # Add extended description with examples
    openapi_schema["info"][
        "description"
    ] = f"""
{app.description}

## Features

- **AI-Powered Recipe Recommendations**: Get personalized recipe suggestions based on your pantry contents
- **Smart Pantry Management**: Track inventory with expiration dates and automated notifications
- **Receipt OCR Processing**: Automatically extract items from receipts using advanced AI
- **Multi-Agent AI System**: CrewAI-powered agents for comprehensive food management
- **Real-time Monitoring**: Comprehensive observability with Sentry, Prometheus, and structured logging

## Authentication

This API uses JWT Bearer tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

For service-to-service communication, use API key authentication:

```
X-API-Key: <your-api-key>
```

## Rate Limiting

API endpoints are rate limited to ensure fair usage:
- Authentication endpoints: 5 requests per minute
- General endpoints: 100 requests per minute
- File upload endpoints: 10 requests per minute

## Error Handling

All API errors follow a consistent format with appropriate HTTP status codes.
Each error response includes:
- `detail`: Human-readable error message
- `error_code`: Machine-readable error identifier
- `timestamp`: ISO 8601 timestamp of the error
- `incident_id`: Unique identifier for tracking (server errors only)

## Monitoring and Observability

This API includes comprehensive monitoring:
- Health check endpoint: `/api/v1/health`
- Metrics endpoint: `/metrics` (Prometheus format)
- Status dashboard: `/monitoring/health`

## Support

For questions or issues, please contact the development team or visit our GitHub repository.
    """

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES

    # Add common response schemas
    if "responses" not in openapi_schema["components"]:
        openapi_schema["components"]["responses"] = {}
    openapi_schema["components"]["responses"].update(COMMON_RESPONSES)

    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "PrepSense GitHub Repository",
        "url": "https://github.com/dankimjw/PrepSense",
    }

    # Add custom extensions for contract testing
    openapi_schema["x-api-version"] = app.version
    openapi_schema["x-api-stability"] = "stable"
    openapi_schema["x-contract-testing"] = {
        "enabled": True,
        "tools": ["schemathesis", "spectral"],
        "validation_rules": ["spectral:.spectral.yml"],
    }

    # Cache the schema
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_enhanced_docs(app: FastAPI) -> None:
    """Setup enhanced API documentation with custom styling."""

    # Custom Swagger UI
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Interactive API Documentation",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
            swagger_ui_parameters={
                "displayRequestDuration": True,
                "tryItOutEnabled": True,
                "filter": True,
                "deepLinking": True,
                "displayOperationId": True,
                "defaultModelsExpandDepth": 2,
                "defaultModelExpandDepth": 2,
                "docExpansion": "list",
            },
        )

    # Custom ReDoc documentation
    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - API Reference",
            redoc_js_url="https://unpkg.com/redoc@2.1.0/bundles/redoc.standalone.js",
            with_google_fonts=True,
        )

    # OpenAPI schema endpoint with custom metadata
    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi_schema():
        return custom_openapi_schema(app)

    # API status page
    @app.get("/api/status", include_in_schema=False)
    async def api_status():
        return HTMLResponse(
            f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{app.title} - Status</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
                .header {{ background: linear-gradient(135deg, #297A56 0%, #34A853 100%); color: white; padding: 30px; border-radius: 8px; }}
                .section {{ margin: 20px 0; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }}
                .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
                .status.healthy {{ background: #d4edda; color: #155724; }}
                a {{ color: #297A56; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{app.title}</h1>
                <p>{app.description}</p>
                <span class="status healthy">● OPERATIONAL</span>
            </div>

            <div class="section">
                <h2>📚 API Documentation</h2>
                <p><a href="/docs">Interactive API Documentation (Swagger UI)</a></p>
                <p><a href="/redoc">API Reference Documentation (ReDoc)</a></p>
                <p><a href="/openapi.json">OpenAPI Schema (JSON)</a></p>
            </div>

            <div class="section">
                <h2>🔍 Monitoring & Health</h2>
                <p><a href="/api/v1/health">Health Check Endpoint</a></p>
                <p><a href="/metrics">Prometheus Metrics</a></p>
                <p><a href="/monitoring/health">Detailed Health Dashboard</a></p>
            </div>

            <div class="section">
                <h2>📝 Version Information</h2>
                <p><strong>Version:</strong> {app.version}</p>
                <p><strong>Environment:</strong> Development</p>
                <p><strong>Last Updated:</strong> {app.openapi_schema.get('info', {}).get('x-build-time', 'Unknown') if app.openapi_schema else 'Unknown'}</p>
            </div>
        </body>
        </html>
        """
        )

    logger.info("Enhanced API documentation endpoints configured")


def export_openapi_schema(app: FastAPI, output_file: str = "openapi.json") -> None:
    """Export OpenAPI schema to file for contract testing."""
    try:
        schema = custom_openapi_schema(app)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

        logger.info(f"OpenAPI schema exported to {output_file}")

    except Exception as e:
        logger.error(f"Failed to export OpenAPI schema: {e}")
        raise


def validate_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Validate OpenAPI schema structure and completeness."""
    schema = custom_openapi_schema(app)
    validation_results = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "stats": {
            "total_paths": len(schema.get("paths", {})),
            "total_schemas": len(schema.get("components", {}).get("schemas", {})),
            "documented_responses": 0,
            "undocumented_responses": 0,
        },
    }

    # Check for missing documentation
    paths = schema.get("paths", {})
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                # Check for missing summaries
                if not operation.get("summary"):
                    validation_results["warnings"].append(
                        f"Missing summary for {method.upper()} {path}"
                    )

                # Check for missing descriptions
                if not operation.get("description"):
                    validation_results["warnings"].append(
                        f"Missing description for {method.upper()} {path}"
                    )

                # Check for response documentation
                responses = operation.get("responses", {})
                if responses:
                    validation_results["stats"]["documented_responses"] += 1
                else:
                    validation_results["stats"]["undocumented_responses"] += 1
                    validation_results["warnings"].append(
                        f"Missing response documentation for {method.upper()} {path}"
                    )

    # Check for security scheme usage
    security_schemes = schema.get("components", {}).get("securitySchemes", {})
    if not security_schemes:
        validation_results["warnings"].append("No security schemes defined")

    # Set validation status
    if validation_results["errors"]:
        validation_results["valid"] = False

    logger.info(f"OpenAPI schema validation completed: {validation_results['stats']}")

    return validation_results
