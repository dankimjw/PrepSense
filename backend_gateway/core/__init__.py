"""Core utilities for the backend gateway."""

# This file makes the core directory a Python package
# Import core modules here to make them available when importing from backend_gateway.core
from .config import settings
from .security import (
    create_access_token,
    get_password_hash,
    reusable_oauth2,
    verify_password
)

__all__ = [
    'settings',
    'create_access_token',
    'get_password_hash',
    'reusable_oauth2',
    'verify_password',
]
