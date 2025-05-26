"""Convenience imports for model classes used throughout the API."""

# This file makes the models directory a Python package
# Import models here to make them available when importing from backend_gateway.models
from .user import UserCreate, UserInDB, UserResponse

__all__ = [
    'UserCreate',
    'UserInDB',
    'UserResponse',
]
