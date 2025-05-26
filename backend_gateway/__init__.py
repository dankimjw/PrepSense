"""Initialization for the ``backend_gateway`` package.

This module exposes the FastAPI application instance so that external
tools like ``uvicorn`` can discover and run the API using
``backend_gateway.app:app``.
"""

# Import key components for easier access
from .app import app