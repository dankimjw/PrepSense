from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Union
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    is_admin: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserInDB(UserBase):
    id: str  # This is the string ID (e.g., 'samantha-smith-001')
    numeric_user_id: int  # Numeric ID from 'user' table (required)
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: str  # This is the string ID
    numeric_user_id: int  # Numeric ID (required)
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class UserProfilePreference(BaseModel):
    household_size: Optional[int] = None
    dietary_preference: Optional[Union[str, List[str]]] = None
    allergens: Optional[List[str]] = None
    cuisine_preference: Optional[Union[str, List[str]]] = None
    # Using 'pref_created_at' to avoid conflict if 'created_at' is directly from query result
    preference_created_at: Optional[datetime] = Field(None, alias="preference_created_at")

    def model_post_init(self, __context):
        # Convert lists to strings if needed
        if isinstance(self.dietary_preference, list):
            self.dietary_preference = ", ".join(self.dietary_preference) if self.dietary_preference else None
        if isinstance(self.cuisine_preference, list):
            self.cuisine_preference = ", ".join(self.cuisine_preference) if self.cuisine_preference else None

    class Config:
        from_attributes = True
        populate_by_name = True # Allows using alias
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserProfileResponse(UserBase):
    id: str
    # Using aliases to distinguish from preference created_at if needed
    user_created_at: datetime = Field(..., alias="user_created_at")
    user_updated_at: datetime = Field(..., alias="user_updated_at")
    password_hash: Optional[str] = None
    role: str
    api_key_enc: str
    preferences: Optional[UserProfilePreference] = None

    class Config:
        from_attributes = True
        populate_by_name = True
