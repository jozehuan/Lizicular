
"""
Database models for workspaces and their members.
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Index, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.auth.models import Base

class WorkspaceRole(str, enum.Enum):
    """Roles disponibles en un workspace."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

class Workspace(Base):
    """
    Workspace model para organizar licitaciones.
    """
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="owned_workspaces")
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan", passive_deletes=True)
    
    __table_args__ = (Index('ix_workspaces_owner_active', 'owner_id', 'is_active'),)

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name={self.name}, owner_id={self.owner_id})>"

class WorkspaceMember(Base):
    """
    Tabla asociativa para miembros de workspace con roles.
    """
    __tablename__ = "workspace_members"

    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Enum(WorkspaceRole), default=WorkspaceRole.VIEWER, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="workspace_memberships")
    workspace = relationship("Workspace", back_populates="members")
    
    __table_args__ = (
        Index('ix_workspace_members_user_id', 'user_id'),
        Index('ix_workspace_members_workspace_id', 'workspace_id'),
    )

    def __repr__(self) -> str:
        return f"<WorkspaceMember(workspace_id={self.workspace_id}, user_id={self.user_id}, role={self.role})>"
