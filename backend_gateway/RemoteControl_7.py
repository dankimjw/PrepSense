#!/usr/bin/env python3
"""
RemoteControl_7.py - Centralized mock data management system

This module provides centralized control over mock data features across the PrepSense backend.
It allows enabling/disabling mock data for different features and provides status information.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default mock data states
DEFAULT_MOCK_STATES = {
    "ocr_scan": False,
    "recipe_completion": False,
    "chat_recipes": False,
    "pantry_items": False,
    "spoonacular_api": False,
}

# Feature descriptions
FEATURE_DESCRIPTIONS = {
    "ocr_scan": {
        "description": "OCR image scanning and item detection",
        "endpoints": ["/ocr/scan-items", "/ocr/scan-receipt"],
    },
    "recipe_completion": {
        "description": "Recipe completion and pantry subtraction",
        "endpoints": ["/pantry/complete-recipe"],
    },
    "chat_recipes": {
        "description": "AI chat recipe recommendations",
        "endpoints": ["/chat/message"],
    },
    "pantry_items": {
        "description": "Pantry item management and queries",
        "endpoints": ["/pantry/items", "/pantry/add-item"],
    },
    "spoonacular_api": {
        "description": "External recipe API calls",
        "endpoints": ["/recipes/search", "/recipes/information"],
    },
}

# State file path
STATE_FILE_PATH = Path("logs/mock_states.json")


def _load_mock_states() -> dict[str, bool]:
    """Load mock states from file or return defaults"""
    try:
        if STATE_FILE_PATH.exists():
            with open(STATE_FILE_PATH) as f:
                data = json.load(f)
                # Merge with defaults to handle new features
                states = DEFAULT_MOCK_STATES.copy()
                states.update(data.get("states", {}))
                return states
        else:
            return DEFAULT_MOCK_STATES.copy()
    except Exception as e:
        logger.warning(f"Error loading mock states: {e}, using defaults")
        return DEFAULT_MOCK_STATES.copy()


def _save_mock_states(states: dict[str, bool], changed_by: str = "unknown"):
    """Save mock states to file"""
    try:
        # Ensure logs directory exists
        STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "states": states,
            "last_updated": datetime.now().isoformat(),
            "changed_by": changed_by,
        }

        with open(STATE_FILE_PATH, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Mock states saved by {changed_by}")
    except Exception as e:
        logger.error(f"Error saving mock states: {e}")


def get_mock_states() -> dict[str, Any]:
    """Get current mock states"""
    states = _load_mock_states()
    return {
        "states": states,
        "last_updated": datetime.now().isoformat(),
    }


def get_mock_summary() -> dict[str, Any]:
    """Get summary of mock states"""
    states = _load_mock_states()
    enabled_count = sum(1 for state in states.values() if state)
    total_features = len(states)

    return {
        "enabled_count": enabled_count,
        "total_features": total_features,
        "all_disabled": enabled_count == 0,
        "all_enabled": enabled_count == total_features,
        "last_updated": datetime.now().isoformat(),
    }


def is_mock_enabled(feature: str) -> bool:
    """Check if a specific mock feature is enabled"""
    states = _load_mock_states()
    return states.get(feature, False)


def set_mock(feature: str, enabled: bool, changed_by: str = "unknown") -> bool:
    """Set mock state for a specific feature"""
    if feature not in DEFAULT_MOCK_STATES:
        logger.warning(f"Unknown mock feature: {feature}")
        return False

    states = _load_mock_states()
    states[feature] = enabled
    _save_mock_states(states, changed_by)

    logger.info(f"Mock {feature} {'enabled' if enabled else 'disabled'} by {changed_by}")
    return True


def enable_all_mocks(changed_by: str = "unknown") -> dict[str, bool]:
    """Enable all mock features"""
    states = dict.fromkeys(DEFAULT_MOCK_STATES, True)
    _save_mock_states(states, changed_by)
    logger.info(f"All mock features enabled by {changed_by}")
    return states


def disable_all_mocks(changed_by: str = "unknown") -> dict[str, bool]:
    """Disable all mock features"""
    states = dict.fromkeys(DEFAULT_MOCK_STATES, False)
    _save_mock_states(states, changed_by)
    logger.info(f"All mock features disabled by {changed_by}")
    return states


# Convenience functions for specific features
def is_ocr_mock_enabled() -> bool:
    """Check if OCR mock is enabled"""
    return is_mock_enabled("ocr_scan")


def is_recipe_completion_mock_enabled() -> bool:
    """Check if recipe completion mock is enabled"""
    return is_mock_enabled("recipe_completion")


def is_chat_recipes_mock_enabled() -> bool:
    """Check if chat recipes mock is enabled"""
    return is_mock_enabled("chat_recipes")


def is_pantry_items_mock_enabled() -> bool:
    """Check if pantry items mock is enabled"""
    return is_mock_enabled("pantry_items")


def is_spoonacular_api_mock_enabled() -> bool:
    """Check if Spoonacular API mock is enabled"""
    return is_mock_enabled("spoonacular_api")


def get_available_features() -> dict[str, dict[str, Any]]:
    """Get all available features with descriptions and current states"""
    states = _load_mock_states()
    features = {}

    for feature, description in FEATURE_DESCRIPTIONS.items():
        features[feature] = {
            "description": description["description"],
            "endpoints": description["endpoints"],
            "enabled": states.get(feature, False),
        }

    return features


# Initialize mock states on module import
if not STATE_FILE_PATH.exists():
    _save_mock_states(DEFAULT_MOCK_STATES, "module_init")
