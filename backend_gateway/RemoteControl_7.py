"""
RemoteControl.py - Centralized control for all mock data toggles in PrepSense

This module provides a single source of truth for enabling/disabling mock data
across different features of the application.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RemoteControl:
    """Centralized control for mock data toggles"""

    def __init__(self):
        # Initialize all mock data flags
        self._mock_states = {
            "ocr_scan": False,  # Mock OCR scan data (receipt scanning)
            "recipe_completion": False,  # Mock recipe completion response
            "chat_recipes": False,  # Mock recipes in chat recommendations
            "pantry_items": False,  # Mock pantry items (future)
            "spoonacular_api": False,  # Mock Spoonacular API responses (future)
        }

        # Track when each toggle was last changed
        self._last_changed = {key: None for key in self._mock_states}

        # Track who changed each toggle (for audit purposes)
        self._changed_by = {key: None for key in self._mock_states}

        logger.info("RemoteControl initialized with all mock data disabled")

    def get_state(self, feature: str) -> bool:
        """Get the current state of a mock data toggle"""
        if feature not in self._mock_states:
            logger.warning(f"Unknown feature requested: {feature}")
            return False
        return self._mock_states[feature]

    def set_state(self, feature: str, enabled: bool, changed_by: str = "system") -> bool:
        """Set the state of a mock data toggle"""
        if feature not in self._mock_states:
            logger.error(f"Attempted to set unknown feature: {feature}")
            return False

        old_state = self._mock_states[feature]
        self._mock_states[feature] = enabled
        self._last_changed[feature] = datetime.now()
        self._changed_by[feature] = changed_by

        logger.info(
            f"Mock data for '{feature}' changed from {old_state} to {enabled} " f"by {changed_by}"
        )
        return True

    def set_all(self, enabled: bool, changed_by: str = "system") -> Dict[str, bool]:
        """Enable or disable all mock data at once"""
        logger.info(f"Setting all mock data to {enabled} by {changed_by}")

        for feature in self._mock_states:
            self.set_state(feature, enabled, changed_by)

        return self.get_all_states()

    def get_all_states(self) -> Dict[str, Any]:
        """Get the current state of all mock data toggles"""
        return {
            "states": self._mock_states.copy(),
            "last_changed": {
                k: v.isoformat() if v else None for k, v in self._last_changed.items()
            },
            "changed_by": self._changed_by.copy(),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of mock data status"""
        enabled_count = sum(1 for v in self._mock_states.values() if v)

        return {
            "total_features": len(self._mock_states),
            "enabled_count": enabled_count,
            "disabled_count": len(self._mock_states) - enabled_count,
            "all_enabled": enabled_count == len(self._mock_states),
            "all_disabled": enabled_count == 0,
            "features": self._mock_states.copy(),
        }

    def reset(self) -> Dict[str, bool]:
        """Reset all mock data toggles to disabled state"""
        logger.info("Resetting all mock data to disabled state")
        return self.set_all(False, "reset")


# Global instance for use across the application
_remote_control = RemoteControl()


# Convenience functions for external use
def is_mock_enabled(feature: str) -> bool:
    """Check if mock data is enabled for a specific feature"""
    return _remote_control.get_state(feature)


def enable_mock(feature: str, changed_by: str = "system") -> bool:
    """Enable mock data for a specific feature"""
    return _remote_control.set_state(feature, True, changed_by)


def disable_mock(feature: str, changed_by: str = "system") -> bool:
    """Disable mock data for a specific feature"""
    return _remote_control.set_state(feature, False, changed_by)


def set_mock(feature: str, enabled: bool, changed_by: str = "system") -> bool:
    """Set mock data state for a specific feature"""
    return _remote_control.set_state(feature, enabled, changed_by)


def enable_all_mocks(changed_by: str = "system") -> Dict[str, bool]:
    """Enable all mock data features"""
    _remote_control.set_all(True, changed_by)
    return _remote_control._mock_states.copy()


def disable_all_mocks(changed_by: str = "system") -> Dict[str, bool]:
    """Disable all mock data features"""
    _remote_control.set_all(False, changed_by)
    return _remote_control._mock_states.copy()


def get_mock_states() -> Dict[str, Any]:
    """Get all mock data states"""
    return _remote_control.get_all_states()


def get_mock_summary() -> Dict[str, Any]:
    """Get summary of mock data status"""
    return _remote_control.get_summary()


# Specific feature checks for easier imports
def is_ocr_mock_enabled() -> bool:
    """Check if OCR scan mock data is enabled"""
    return is_mock_enabled("ocr_scan")


def is_recipe_completion_mock_enabled() -> bool:
    """Check if recipe completion mock data is enabled"""
    return is_mock_enabled("recipe_completion")


def is_chat_recipes_mock_enabled() -> bool:
    """Check if chat recipes mock data is enabled"""
    return is_mock_enabled("chat_recipes")
