from typing import Any, List
from datetime import timedelta
import secrets
import uuid
import time

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from backend.auth.models import User, AuditAction, AuditCategory
from backend.auth.schemas import UserCreate, UserResponse, Token, UserLogin, OAuthUserInfo
from backend.auth.auth_utils import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    add_token_to_blacklist,
    is_token_blacklisted,
    get_current_active_user,
    get_user_by_email,
    set_refresh_token_cookie,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    ALGORITHM,
    oauth2_scheme
)
from jose import jwt, JWTError
from backend.auth.oauth_config import OAuthConfig
from backend.auth.oauth_utils import OAuthProvider, get_oauth_user
from backend.auth.database import get_db
from backend.auth.redis_client import get_redis
from backend.auth.audit_utils import log_auth_event, create_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Store for OAuth state tokens (usar Redis en producción)
oauth_states = {}


def clean_old_states():
    """Remove OAuth states older than 10 minutes."""
    current_time = time.time()
    expired = [
        state for state, data in oauth_states.items()
        if current_time - data.get("timestamp", 0) > 600
    ]
    for state in expired:
        oauth_states.pop(state, None)


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


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    request: Request,
    db: Any = Depends(get_db)
) -> UserResponse:
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        await log_auth_event(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            email=user_data.email,
            success=False,
            request=request,
            details="Signup attempt with existing email"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        oauth_provider=None
    )
    
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        await log_auth_event(
            db=db,
            action=AuditAction.LOGIN_SUCCESS,
            user_id=new_user.id,
            email=new_user.email,
            success=True,
            request=request,
            details="Local account created"
        )
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user. Email may already exist."
        )

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Any = Depends(get_db)
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        await log_auth_event(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            email=form_data.username,
            success=False,
            request=request,
            details="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": str(user.id)})
    set_refresh_token_cookie(response, refresh_token)
    await log_auth_event(
        db=db,
        action=AuditAction.LOGIN_SUCCESS,
        user_id=user.id,
        email=user.email,
        success=True,
        request=request
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/login/json", response_model=Token)
async def login_json(
    request: Request,
    response: Response,
    credentials: UserLogin,
    db: Any = Depends(get_db)
) -> Token:
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        await log_auth_event(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            email=credentials.email,
            success=False,
            request=request,
            details="Invalid JSON login"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": str(user.id)})
    set_refresh_token_cookie(response, refresh_token)
    await log_auth_event(
        db=db,
        action=AuditAction.LOGIN_SUCCESS,
        user_id=user.id,
        email=user.email,
        success=True,
        request=request
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/oauth/{provider}/login", summary="Initiate OAuth login", tags=["OAuth2"])
async def oauth_login(provider: str, request: Request, db: Any = Depends(get_db)):
    if provider not in OAuthConfig.get_enabled_providers():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not enabled or configured"
        )
    
    await log_auth_event(
        db=db,
        action=AuditAction.OAUTH_LOGIN,
        success=True,
        request=request,
        details=f"Initiating OAuth login with {provider}"
    )
    
    # Limpiar estados antiguos
    clean_old_states()
    
    # Generar nuevo estado
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "provider": provider,
        "timestamp": time.time()
    }
    
    oauth = OAuthProvider(provider)
    auth_url = oauth.get_authorization_url(state)
    return RedirectResponse(url=auth_url)

@router.get("/oauth/{provider}/callback", response_model=Token, summary="OAuth callback endpoint", tags=["OAuth2"])
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    response: Response,
    db: Any = Depends(get_db)
):
    if state not in oauth_states:
        await log_auth_event(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            success=False,
            request=request,
            details=f"Invalid OAuth state for {provider}"
        )
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
    
    try:
        oauth_info = await get_oauth_user(provider, code)
    except Exception as e:
        await log_auth_event(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            success=False,
            request=request,
            details=f"OAuth fetch info failed for {provider}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with {provider}: {str(e)}"
        )
    
    user = await get_or_create_oauth_user(db, oauth_info)
    access_token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": str(user.id)})
    set_refresh_token_cookie(response, refresh_token)
    
    await log_auth_event(
        db=db,
        action=AuditAction.OAUTH_LOGIN,
        user_id=user.id,
        email=user.email,
        success=True,
        request=request,
        provider=provider
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.post("/refresh", response_model=Token, summary="Refresh access token using refresh token from cookie", tags=["Authentication"])
async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(None),
    db: Any = Depends(get_db),
    redis: Any = Depends(get_redis)
) -> Token:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        jti: str = payload.get("jti")
        if email is None or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if jti and await is_token_blacklisted(redis, jti):
            raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")
    
    if jti:
        await add_token_to_blacklist(redis, jti, REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
    
    new_access_token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": user.email, "user_id": str(user.id)})
    set_refresh_token_cookie(response, new_refresh_token)
    
    return Token(access_token=new_access_token, token_type="bearer")

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    token: str = Depends(oauth2_scheme),
    redis: Any = Depends(get_redis)
):
    """
    Logout endpoint that invalidates both access and refresh tokens.
    """
    # Invalidar el access token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti:
            await add_token_to_blacklist(redis, jti, ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    except JWTError:
        pass
    
    # Invalidar el refresh token de la cookie
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                await add_token_to_blacklist(redis, jti, REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        except JWTError:
            pass
    
    # Eliminar cookie
    response.delete_cookie(key="refresh_token")
    
    return {"message": "Logged out successfully and tokens invalidated"}

# ⚠️ IMPORTANTE: Este endpoint debe estar FUERA del router con prefix="/auth"
# Por eso lo movemos a un router separado

users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.get("/me", response_model=UserResponse, summary="Get current user information")
async def read_users_me(
    request: Request,
    db: Any = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current authenticated user information.
    """
    # Log profile view
    await create_audit_log(
        db=db,
        category=AuditCategory.AUTH,
        action=AuditAction.USER_VIEW,
        user_id=current_user.id,
        payload={"path": str(request.url.path)},
        success=True,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    user_data_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "oauth_provider": current_user.oauth_provider,
        "profile_picture": current_user.profile_picture,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    }
    return UserResponse.model_validate(user_data_dict)

@router.get("/providers", summary="Get enabled OAuth providers", tags=["OAuth2"])
async def get_enabled_providers():
    return {
        "enabled_providers": OAuthConfig.get_enabled_providers(),
        "available_providers": ["google", "facebook", "github", "microsoft"]
    }