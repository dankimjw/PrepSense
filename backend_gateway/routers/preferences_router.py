"""
User preferences router - manages user dietary preferences, allergens, and cuisine preferences
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from backend_gateway.routers.users import get_current_active_user
from backend_gateway.models.user import UserInDB
from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/preferences",
    tags=["User Preferences"],
    responses={404: {"description": "Not found"}},
)


class UserPreferences(BaseModel):
    allergens: List[str] = []
    dietary_restrictions: List[str] = []
    cuisine_preferences: List[str] = []
    household_size: Optional[int] = 1


class PreferencesResponse(BaseModel):
    user_id: int
    preferences: UserPreferences
    updated_at: str


@router.get("/", response_model=PreferencesResponse)
async def get_user_preferences(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get user's current preferences"""
    try:
        db_service = get_database_service()
        
        query = """
            SELECT user_id, preferences, household_size, updated_at
            FROM user_preferences
            WHERE user_id = %(user_id)s
        """
        params = {"user_id": current_user.numeric_user_id}
        
        result = db_service.execute_query(query, params)
        
        if result:
            row = result[0]
            prefs_data = row.get('preferences', {})
            
            preferences = UserPreferences(
                allergens=prefs_data.get('allergens', []),
                dietary_restrictions=prefs_data.get('dietary_restrictions', []),
                cuisine_preferences=prefs_data.get('cuisine_preferences', []),
                household_size=row.get('household_size', 1)
            )
            
            return PreferencesResponse(
                user_id=current_user.numeric_user_id,
                preferences=preferences,
                updated_at=str(row.get('updated_at'))
            )
        else:
            # Return default preferences if none exist
            default_preferences = UserPreferences()
            return PreferencesResponse(
                user_id=current_user.numeric_user_id,
                preferences=default_preferences,
                updated_at=""
            )
            
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")


@router.post("/", response_model=PreferencesResponse)
async def save_user_preferences(
    preferences: UserPreferences,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Save or update user preferences"""
    try:
        db_service = get_database_service()
        
        # Convert preferences to JSONB format
        prefs_json = {
            "allergens": preferences.allergens,
            "dietary_restrictions": preferences.dietary_restrictions,
            "cuisine_preferences": preferences.cuisine_preferences
        }
        
        # Use INSERT ... ON CONFLICT DO UPDATE to handle both insert and update
        query = """
            INSERT INTO user_preferences (user_id, preferences, household_size, updated_at)
            VALUES (%(user_id)s, %(preferences)s, %(household_size)s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                preferences = %(preferences)s,
                household_size = %(household_size)s,
                updated_at = CURRENT_TIMESTAMP
            RETURNING user_id, preferences, household_size, updated_at
        """
        
        import json
        params = {
            "user_id": current_user.numeric_user_id,
            "preferences": json.dumps(prefs_json),
            "household_size": preferences.household_size
        }
        
        result = db_service.execute_query(query, params)
        
        if result:
            row = result[0]
            return PreferencesResponse(
                user_id=current_user.numeric_user_id,
                preferences=preferences,
                updated_at=str(row.get('updated_at'))
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save preferences")
            
    except Exception as e:
        logger.error(f"Error saving user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save preferences: {str(e)}")


@router.delete("/")
async def clear_user_preferences(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Clear all user preferences"""
    try:
        db_service = get_database_service()
        
        query = """
            DELETE FROM user_preferences
            WHERE user_id = %(user_id)s
        """
        params = {"user_id": current_user.numeric_user_id}
        
        db_service.execute_query(query, params)
        
        return {"message": "Preferences cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear preferences: {str(e)}")