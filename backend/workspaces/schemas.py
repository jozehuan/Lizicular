
from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from backend.workspaces.models import WorkspaceRole # Import WorkspaceRole

# --- Workspace Schemas ---

class CollaboratorCreate(BaseModel):
    """Schema for creating a collaborator with a specific role."""
    email: EmailStr = Field(..., description="Email of the collaborator")
    role: WorkspaceRole = Field(..., description="Role to assign to the collaborator")

class WorkspaceBase(BaseModel):
    """Base schema for a workspace."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the workspace")
    description: str | None = Field(default=None, description="Detailed description of the workspace")

class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a new workspace."""
    collaborators: List[CollaboratorCreate] = Field(default_factory=list, description="Collaborators to add to the workspace with their roles")

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

class WorkspaceDetailResponse(WorkspaceResponse):
    """Schema for the detailed response of a workspace, including members."""
    members: List[WorkspaceMemberResponse] = Field(..., description="List of members in the workspace")

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
    workspace_id: UUID = Field(..., description="ID of the workspace this tender belongs to")
    workspace_name: str = Field(..., description="Name of the workspace this tender belongs to")


class WorkspaceWithTendersResponse(WorkspaceResponse):
    """A detailed workspace view including the user's role and a list of tenders."""
    user_role: str = Field(..., description="The current user's role in this workspace")
    tenders: List[TenderSummaryResponse] = Field(..., description="List of tenders within this workspace")
    members: List[WorkspaceMemberResponse] = Field(default_factory=list, description="List of members in this workspace")

