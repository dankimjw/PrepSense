"""
Feature flags for safe deployment and testing of new features.
Configured via environment variables with sensible defaults for development.
"""
import os
from typing import Any, Callable, Optional, TypeVar, cast

from pydantic import BaseSettings, Field

T = TypeVar('T')

class FeatureFlags(BaseSettings):
    """Feature flags configuration with environment variable overrides."""
    
    # Example feature flag - enable new recipe recommendation system
    ENABLE_NEW_RECOMMENDATION_ENGINE: bool = Field(
        default=False,
        env='FEATURE_NEW_RECOMMENDATION_ENGINE',
        description='Enable the new AI-powered recipe recommendation system'
    )
    
    # Enable experimental API endpoints
    ENABLE_EXPERIMENTAL_APIS: bool = Field(
        default=False,
        env='FEATURE_EXPERIMENTAL_APIS',
        description='Enable experimental API endpoints'
    )
    
    # Enable new UI components
    ENABLE_NEW_UI: bool = Field(
        default=False,
        env='FEATURE_NEW_UI',
        description='Enable new UI components and layouts'
    )
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

# Initialize feature flags
feature_flags = FeatureFlags()

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    return getattr(feature_flags, feature_name, False)

def with_feature_flag(
    flag_name: str,
    enabled_fn: Callable[..., T],
    disabled_fn: Optional[Callable[..., T]] = None,
    *args: Any,
    **kwargs: Any
) -> T:
    """
    Execute different code paths based on feature flag status.
    
    Args:
        flag_name: Name of the feature flag to check
        enabled_fn: Function to call if the flag is enabled
        disabled_fn: Function to call if the flag is disabled (optional)
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the called function
    """
    if is_feature_enabled(flag_name):
        return enabled_fn(*args, **kwargs)
    elif disabled_fn is not None:
        return disabled_fn(*args, **kwargs)
    return cast(T, None)

# Example usage:
# def new_feature():
#     return "New feature is active!"
#
# def old_feature():
#     return "Old feature is active"
#
# result = with_feature_flag(
#     'ENABLE_NEW_FEATURE',
#     new_feature,
#     old_feature
# )
