"""
Configuration utilities for reading sensitive data from config files.
"""

import os
from pathlib import Path
from typing import Optional


def read_api_key_from_file(file_path: str) -> Optional[str]:
    """
    Read an API key from a file.
    
    Args:
        file_path: Path to the file containing the API key
        
    Returns:
        The API key as a string, or None if the file doesn't exist
        
    Raises:
        ValueError: If the file exists but is empty or contains only whitespace
    """
    if not file_path:
        return None
        
    path = Path(file_path)
    if not path.exists():
        return None
        
    try:
        api_key = path.read_text().strip()
        if not api_key:
            raise ValueError(f"API key file {file_path} is empty")
        return api_key
    except Exception as e:
        raise ValueError(f"Error reading API key from {file_path}: {e}")


def get_openai_api_key() -> str:
    """
    Get OpenAI API key from environment variable or config file.
    
    Priority:
    1. OPENAI_API_KEY environment variable (direct key)
    2. OPENAI_API_KEY_FILE environment variable (path to file)
    3. Default config file location: config/openai_key.txt
    
    Returns:
        The OpenAI API key
        
    Raises:
        ValueError: If no API key can be found or loaded
    """
    # Try direct environment variable first (for backward compatibility)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "your_openai_api_key_here":
        # Validate the key format
        if not api_key.startswith("sk-"):
            raise ValueError(
                f"Invalid OpenAI API key format. "
                f"OpenAI keys should start with 'sk-'. "
                f"Got: {api_key[:10]}..."
            )
        return api_key
    
    # Try config file specified in environment
    key_file = os.getenv("OPENAI_API_KEY_FILE")
    if key_file:
        api_key = read_api_key_from_file(key_file)
        if api_key:
            return api_key
    
    # Try default config file locations
    default_locations = [
        "config/openai_key.txt",           # When running from project root
        "../config/openai_key.txt",        # When running from backend_gateway
        "backend_gateway/config/openai_key.txt"  # Alternative path
    ]
    
    for key_file in default_locations:
        if os.path.exists(key_file):
            api_key = read_api_key_from_file(key_file)
            if api_key:
                return api_key
    
    # No API key found
    raise ValueError(
        "OpenAI API key not found. Please either:\n"
        "1. Set OPENAI_API_KEY environment variable in .env file, or\n"
        "2. Create config/openai_key.txt with your API key\n\n"
        "Get your API key at: https://platform.openai.com/api-keys\n"
        "Location of .env file: project_root/.env (NOT in backend_gateway/)"
    )


def get_google_credentials_path() -> str:
    """
    Get Google Cloud credentials file path.
    
    Returns:
        Path to the Google Cloud credentials file
        
    Raises:
        ValueError: If no credentials file can be found
    """
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    if not Path(creds_path).exists():
        raise ValueError(f"Google Cloud credentials file not found: {creds_path}")
    
    return creds_path