"""Centralized OpenAI client factory to ensure consistent initialization across services."""

import logging
from typing import Optional

from openai import OpenAI

from .config_utils import get_openai_api_key

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """
    Get or create a singleton OpenAI client instance.

    Returns:
        OpenAI: Configured OpenAI client instance

    Raises:
        ValueError: If OpenAI API key is not configured
    """
    global _client

    if _client is None:
        try:
            api_key = get_openai_api_key()
            _client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing OpenAI client: {e}")
            raise ValueError(f"Failed to initialize OpenAI client: {e}")

    return _client


def reset_client():
    """Reset the client instance. Useful for testing."""
    global _client
    _client = None
