"""
Main FastAPI application with authentication endpoints.
Supports both local authentication and OAuth2 (Google, Facebook, GitHub, Microsoft).
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import AsyncGenerator, List, Any, Annotated
import os
import secrets

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_

from backend.authentication.models import Base, User
from backend.authentication.schemas import UserCreate, UserResponse, Token, UserLogin, OAuthUserInfo
from backend.authentication.auth_utils import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_user_by_email,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.authentication.oauth_config import OAuthConfig
from backend.authentication.oauth_utils import OAuthProvider, get_oauth_user
from backend.authentication.database import engine, get_db

# Store for OAuth state tokens (in production, use Redis or database)
oauth_states = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    """
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown: Dispose engine
    await engine.dispose()


# Initialize FastAPI application
app = FastAPI(
    title="Authentication API with OAuth2",
    description="Centralized authentication system with JWT and OAuth2 (Google, Facebook, GitHub, Microsoft)",
    version="2.0.0",
    lifespan=lifespan
)


async def get_or_create_oauth_user(
    db: AsyncSession,
    oauth_info: OAuthUserInfo
) -> User:
    """
    Get existing OAuth user or create a new one.
    
    Args:
        db: Database session
        oauth_info: OAuth user information
        
    Returns:
        User object
    """
    # First, try to find by OAuth provider and ID
    result = await db.execute(
        select(User).where(
            User.oauth_provider == oauth_info.oauth_provider,
            User.oauth_id == oauth_info.oauth_id
        )
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Update user info in case it changed
        user.full_name = oauth_info.full_name
        user.profile_picture = oauth_info.profile_picture
        await db.commit()
        await db.refresh(user)
        return user
    
    # Check if user exists with same email (linking accounts)
    result = await db.execute(
        select(User).where(User.email == oauth_info.email)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Link OAuth account to existing user
        user.oauth_provider = oauth_info.oauth_provider
        user.oauth_id = oauth_info.oauth_id
        user.profile_picture = oauth_info.profile_picture
        await db.commit()
        await db.refresh(user)
        return user
    
    # Create new user
    new_user = User(
        email=oauth_info.email,
        full_name=oauth_info.full_name,
        oauth_provider=oauth_info.oauth_provider,
        oauth_id=oauth_info.oauth_id,
        profile_picture=oauth_info.profile_picture,
        is_active=True,
        hashed_password=None  # OAuth users don't have passwords
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@app.post(
    "/auth/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    tags=["Authentication"]
)
async def signup(
    user_data: UserCreate,
    db: Any = Depends(get_db)
) -> UserResponse:
    """
    Register a new user in the system with email/password.
    
    Args:
        user_data: User registration data (email, password, full_name)
        db: Database session
        
    Returns:
        Created user information (without password)
        
    Raises:
        HTTPException 400: If email already exists
    """
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        oauth_provider=None  # Local auth
    )
    
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user. Email may already exist."
        )
    
    return UserResponse.model_validate(new_user)


@app.post(
    "/auth/login",
    response_model=Token,
    summary="Login and get access token",
    tags=["Authentication"]
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Any = Depends(get_db)
) -> Token:
    """
    Authenticate user and return JWT access token.
    
    Args:
        form_data: OAuth2 form with username (email) and password
        db: Database session
        
    Returns:
        Access token and token type
        
    Raises:
        HTTPException 401: If credentials are invalid
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@app.post(
    "/auth/login/json",
    response_model=Token,
    summary="Login with JSON payload",
    tags=["Authentication"]
)
async def login_json(
    credentials: UserLogin,
    db: Any = Depends(get_db)
) -> Token:
    """
    Alternative login endpoint that accepts JSON instead of form data.
    
    Args:
        credentials: User login credentials (email and password)
        db: Database session
        
    Returns:
        Access token and token type
        
    Raises:
        HTTPException 401: If credentials are invalid
    """
    user = await authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@app.get(
    "/auth/{provider}/login",
    summary="Initiate OAuth login",
    tags=["OAuth2"]
)
async def oauth_login(provider: str, request: Request):
    """
    Initiate OAuth2 login flow with a provider.
    
    Supported providers: google, facebook, github, microsoft
    
    Args:
        provider: OAuth provider name
        request: Request object
        
    Returns:
        Redirect to OAuth provider's authorization page
    """
    if provider not in OAuthConfig.get_enabled_providers():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not enabled or configured"
        )
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "provider": provider,
        "timestamp": secrets.token_hex(16)
    }
    
    # Get OAuth provider and generate authorization URL
    oauth = OAuthProvider(provider)
    auth_url = oauth.get_authorization_url(state)
    
    return RedirectResponse(url=auth_url)


@app.get(
    "/auth/{provider}/callback",
    response_model=Token,
    summary="OAuth callback endpoint",
    tags=["OAuth2"]
)
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    db: Any = Depends(get_db)
):
    """
    Handle OAuth2 callback and authenticate user.
    
    Args:
        provider: OAuth provider name
        code: Authorization code from provider
        state: State token for CSRF validation
        db: Database session
        
    Returns:
        Access token
    """
    # Validate state token
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state token"
        )
    
    state_data = oauth_states.pop(state)
    
    if state_data["provider"] != provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider mismatch"
        )
    
    # Get user info from OAuth provider
    try:
        oauth_info = await get_oauth_user(provider, code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with {provider}: {str(e)}"
        )
    
    # Get or create user
    user = await get_or_create_oauth_user(db, oauth_info)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@app.get(
    "/users/me",
    response_model=UserResponse,
    summary="Get current user information",
    tags=["Users"]
)
async def read_users_me(
    current_user: Any = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get information about the currently authenticated user.
    
    This is a protected endpoint that requires a valid JWT token.
    
    Args:
        current_user: Current authenticated user (from JWT token)
        
    Returns:
        Current user information
    """
    return UserResponse.model_validate(current_user)


@app.get(
    "/auth/providers",
    summary="Get enabled OAuth providers",
    tags=["OAuth2"]
)
async def get_enabled_providers():
    """
    Get list of enabled OAuth2 providers.
    
    Returns:
        List of enabled provider names
    """
    return {
        "enabled_providers": OAuthConfig.get_enabled_providers(),
        "available_providers": ["google", "facebook", "github", "microsoft"]
    }


@app.get(
    "/",
    summary="Health check",
    tags=["Health"]
)
async def root():
    """
    Simple health check endpoint.
    
    Returns:
        Status message
    """
    return {
        "status": "ok",
        "message": "Authentication API with OAuth2 is running",
        "version": "2.0.0",
        "oauth_enabled": len(OAuthConfig.get_enabled_providers()) > 0
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
