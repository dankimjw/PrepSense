from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    is_admin: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserInDB(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
