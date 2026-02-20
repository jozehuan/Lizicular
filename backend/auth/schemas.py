from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import List, Any 
from pydantic import BaseModel, EmailStr, Field, ConfigDict
"""
Pydantic schemas for request/response validation.
"""

class UserBase(BaseModel):
    """Base schema with common user attributes."""
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=50, description="User's full name")


class UserCreate(UserBase):
    """Schema for user registration/signup."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User's password (min 8 characters)"
    )


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: str | None = Field(default=None, min_length=1, max_length=50)
    profile_picture: str | None = Field(default=None, description="Path to profile picture")


class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)."""
    id: UUID = Field(..., description="User's unique identifier")
    is_active: bool = Field(..., description="Whether the user account is active")
    oauth_provider: str | None = Field(default=None, description="OAuth provider (google, facebook, etc.)")
    profile_picture: str | None = Field(default=None, description="URL to profile picture")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Schema for token payload data."""
    email: str | None = Field(default=None)
    user_id: str | None = Field(default=None)


class OAuthUserInfo(BaseModel):
    """Schema for OAuth user information from providers."""
    email: EmailStr
    full_name: str
    profile_picture: str | None = Field(default=None)
    oauth_id: str
    oauth_provider: str

