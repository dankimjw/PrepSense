"""Initialization for the ``backend_gateway`` package.

This module exposes the FastAPI application instance so that external
tools like ``uvicorn`` can discover and run the API using
``backend_gateway.app:app``.
"""

# Import key components for easier access
# Only import app when not in test mode
import os
if not os.environ.get('TESTING'):
    try:
        from .app import app
    except ImportError:
        pass  # Allow imports to work during testing