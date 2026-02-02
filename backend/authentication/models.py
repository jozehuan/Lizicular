"""
Database models for the authentication system.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from typing import List, Any, Annotated


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """
    User model for authentication and identity management.
    
    Supports both local authentication and OAuth2 third-party providers.
    
    Attributes:
        id: Unique identifier for the user (UUID)
        email: User's email address (unique and indexed)
        hashed_password: Bcrypt hashed password (nullable for OAuth users)
        full_name: User's full name
        is_active: Whether the user account is active
        oauth_provider: OAuth provider name (google, facebook, github, microsoft, None for local)
        oauth_id: User ID from OAuth provider
        profile_picture: URL to user's profile picture
        created_at: Timestamp when the user was created
        updated_at: Timestamp when the user was last updated
    """
    __tablename__ = "users"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password = Column(
        String(255),
        nullable=True  # Nullable for OAuth users
    )
    full_name = Column(
        String(255),
        nullable=False
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )
    oauth_provider = Column(
        String(50),
        nullable=True,  # NULL for local auth, 'google', 'facebook', etc. for OAuth
        index=True
    )
    oauth_id = Column(
        String(255),
        nullable=True,  # OAuth provider's user ID
        index=True
    )
    profile_picture = Column(
        Text,
        nullable=True  # URL to profile picture
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Additional indexes for common queries
    __table_args__ = (
        Index('ix_users_email_active', 'email', 'is_active'),
        Index('ix_users_oauth_provider_id', 'oauth_provider', 'oauth_id'),
    )
    
    @property
    def is_oauth_user(self) -> bool:
        """Check if user is authenticated via OAuth."""
        return self.oauth_provider is not None
    
    def __repr__(self) -> str:
        auth_method = f"OAuth({self.oauth_provider})" if self.is_oauth_user else "Local"
        return f"<User(id={self.id}, email={self.email}, auth={auth_method})>"
