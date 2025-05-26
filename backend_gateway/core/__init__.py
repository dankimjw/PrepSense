"""Exports configuration settings and security utilities for use across the gateway."""

# This file makes the core directory a Python package
# Import core modules here to make them available when importing from backend_gateway.core
from .config import settings
from .security import (
    create_access_token,
    get_current_active_user,
    get_password_hash,
    reusable_oauth2,
    verify_password
)

__all__ = [
    'settings',
    'create_access_token',
    'get_current_active_user',
    'get_password_hash',
    'reusable_oauth2',
    'verify_password',
]
