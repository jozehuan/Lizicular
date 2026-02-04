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
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")


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


# --- Workspace Schemas ---

class WorkspaceBase(BaseModel):
    """Base schema for a workspace."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the workspace")
    description: str | None = Field(default=None, description="Detailed description of the workspace")


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a new workspace."""
    pass


class WorkspaceUpdate(WorkspaceBase):
    """Schema for updating an existing workspace."""
    name: str | None = Field(default=None, min_length=1, max_length=255, description="New name of the workspace")


class WorkspaceResponse(WorkspaceBase):
    """Schema for the response of a workspace."""
    id: UUID = Field(..., description="Unique identifier of the workspace")
    owner_id: UUID = Field(..., description="Unique identifier of the workspace owner")
    is_active: bool = Field(..., description="Whether the workspace is active")
    created_at: datetime = Field(..., description="Timestamp of workspace creation")
    updated_at: datetime = Field(..., description="Timestamp of last workspace update")
    
    model_config = ConfigDict(from_attributes=True)


# --- Workspace Member Schemas ---

class WorkspaceMemberAdd(BaseModel):
    """Schema for adding a member to a workspace."""
    user_email: EmailStr = Field(..., description="Email of the user to add")
    role: str = Field(..., description="Role to assign to the user (e.g., 'EDITOR', 'VIEWER')")


class WorkspaceMemberUpdate(BaseModel):
    """Schema for updating a member's role in a workspace."""
    role: str = Field(..., description="New role for the workspace member")


class WorkspaceMemberResponse(BaseModel):
    """Schema for responding with workspace member information."""
    user_id: UUID = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email")
    full_name: str = Field(..., description="User's full name")
    role: str = Field(..., description="User's role in the workspace")

    model_config = ConfigDict(from_attributes=True)


# --- Detailed Workspace Response Schemas ---

class TenderSummaryResponse(BaseModel):
    """A summarized view of a tender for lists."""
    id: str = Field(..., description="MongoDB ObjectId of the tender")
    name: str = Field(..., description="Name of the tender")
    created_at: datetime = Field(..., description="Timestamp of tender creation")

class WorkspaceWithTendersResponse(WorkspaceResponse):
    """A detailed workspace view including the user's role and a list of tenders."""
    user_role: str = Field(..., description="The current user's role in this workspace")
    tenders: List[TenderSummaryResponse] = Field(..., description="List of tenders within this workspace")
