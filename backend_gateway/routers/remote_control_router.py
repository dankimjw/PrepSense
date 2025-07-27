"""Router for centralized mock data control"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

import backend_gateway.RemoteControl_7 as RemoteControl

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/remote-control",
    tags=["Remote Control"],
    responses={404: {"description": "Not found"}},
)


class MockToggleRequest(BaseModel):
    """Request model for toggling a specific mock feature"""
    feature: str
    enabled: bool
    changed_by: str = "api"


class BulkToggleRequest(BaseModel):
    """Request model for toggling all mock features"""
    enabled: bool
    changed_by: str = "api"


class MockStateResponse(BaseModel):
    """Response model for mock state queries"""
    success: bool
    states: Dict[str, bool]
    summary: Dict[str, Any]
    message: str


@router.get("/status", response_model=MockStateResponse, summary="Get all mock data states")
async def get_mock_status() -> MockStateResponse:
    """Get the current state of all mock data toggles"""
    try:
        states = RemoteControl.get_mock_states()
        summary = RemoteControl.get_mock_summary()
        
        return MockStateResponse(
            success=True,
            states=states["states"],
            summary=summary,
            message=f"{summary['enabled_count']} of {summary['total_features']} mock features enabled"
        )
    except Exception as e:
        logger.error(f"Error getting mock status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/toggle", response_model=MockStateResponse, summary="Toggle a specific mock feature")
async def toggle_mock_feature(request: MockToggleRequest) -> MockStateResponse:
    """Toggle a specific mock data feature on or off"""
    try:
        success = RemoteControl.set_mock(
            request.feature, 
            request.enabled, 
            request.changed_by
        )
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown feature: {request.feature}"
            )
        
        states = RemoteControl.get_mock_states()
        summary = RemoteControl.get_mock_summary()
        
        return MockStateResponse(
            success=True,
            states=states["states"],
            summary=summary,
            message=f"Mock data for '{request.feature}' {'enabled' if request.enabled else 'disabled'}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling mock feature: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/toggle-all", response_model=MockStateResponse, summary="Toggle all mock features")
async def toggle_all_mocks(request: BulkToggleRequest) -> MockStateResponse:
    """Enable or disable all mock data features at once"""
    try:
        if request.enabled:
            states_dict = RemoteControl.enable_all_mocks(request.changed_by)
        else:
            states_dict = RemoteControl.disable_all_mocks(request.changed_by)
        
        summary = RemoteControl.get_mock_summary()
        
        return MockStateResponse(
            success=True,
            states=states_dict,
            summary=summary,
            message=f"All mock data {'enabled' if request.enabled else 'disabled'}"
        )
    except Exception as e:
        logger.error(f"Error toggling all mocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=MockStateResponse, summary="Reset all mock data to disabled")
async def reset_mock_data() -> MockStateResponse:
    """Reset all mock data toggles to disabled state"""
    try:
        states_dict = RemoteControl.disable_all_mocks("reset")
        summary = RemoteControl.get_mock_summary()
        
        return MockStateResponse(
            success=True,
            states=states_dict,
            summary=summary,
            message="All mock data reset to disabled state"
        )
    except Exception as e:
        logger.error(f"Error resetting mock data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features", summary="List all available mock features")
async def list_mock_features() -> Dict[str, Any]:
    """Get a list of all available mock features and their descriptions"""
    return {
        "features": {
            "ocr_scan": {
                "description": "Mock OCR scan data for receipt scanning",
                "endpoints": ["/ocr/scan-receipt", "/ocr/scan-pantry-item"],
                "enabled": RemoteControl.is_ocr_mock_enabled()
            },
            "recipe_completion": {
                "description": "Mock recipe completion response for testing pantry subtraction",
                "endpoints": ["/pantry/recipe/complete"],
                "enabled": RemoteControl.is_recipe_completion_mock_enabled()
            },
            "chat_recipes": {
                "description": "Mock recipes in chat recommendations",
                "endpoints": ["/chat/message"],
                "enabled": RemoteControl.is_chat_recipes_mock_enabled()
            },
            "pantry_items": {
                "description": "Mock pantry items (future feature)",
                "endpoints": [],
                "enabled": RemoteControl.is_mock_enabled("pantry_items")
            },
            "spoonacular_api": {
                "description": "Mock Spoonacular API responses (future feature)",
                "endpoints": [],
                "enabled": RemoteControl.is_mock_enabled("spoonacular_api")
            }
        }
    }


# Backward compatibility endpoints
@router.post("/ocr/toggle", summary="Toggle OCR mock data (backward compatibility)")
async def toggle_ocr_mock(enabled: bool = True) -> Dict[str, Any]:
    """Toggle OCR mock data - for backward compatibility"""
    RemoteControl.set_mock("ocr_scan", enabled, "legacy_api")
    return {
        "success": True,
        "feature": "ocr_scan",
        "enabled": enabled,
        "message": f"OCR mock data {'enabled' if enabled else 'disabled'}"
    }


@router.post("/recipes/toggle", summary="Toggle recipe mock data (backward compatibility)")
async def toggle_recipe_mock(enabled: bool = True) -> Dict[str, Any]:
    """Toggle recipe completion mock data - for backward compatibility"""
    RemoteControl.set_mock("recipe_completion", enabled, "legacy_api")
    RemoteControl.set_mock("chat_recipes", enabled, "legacy_api")
    return {
        "success": True,
        "features": ["recipe_completion", "chat_recipes"],
        "enabled": enabled,
        "message": f"Recipe mock data {'enabled' if enabled else 'disabled'}"
    }