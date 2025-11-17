"""
User request/response schemas
"""

from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(UserBase):
    """User response model (excludes password)"""

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation model for Clerk webhook"""

    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    bio: Optional[str] = None


class UserUpdate(BaseModel):
    """User update model for Clerk webhook"""

    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    bio: Optional[str] = None
