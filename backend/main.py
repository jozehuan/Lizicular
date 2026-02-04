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
import uuid

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Cookie, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from backend.auth.models import Base, User, Workspace, WorkspaceMember, WorkspaceRole
from backend.auth.schemas import (
    UserCreate, UserResponse, Token, UserLogin, OAuthUserInfo,
    WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate,
    WorkspaceMemberAdd, WorkspaceMemberUpdate, WorkspaceMemberResponse,
    WorkspaceWithTendersResponse, TenderSummaryResponse
)
from backend.mongodb.tenders_utils import get_tenders_by_workspace
from backend.auth.auth_utils import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    add_token_to_blacklist,
    is_token_blacklisted,
    get_current_active_user,
    get_user_by_email,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
    ALGORITHM,
    oauth2_scheme
)
from jose import jwt, JWTError
from backend.auth.oauth_config import OAuthConfig
from backend.auth.oauth_utils import OAuthProvider, get_oauth_user
from backend.auth.database import engine, get_db
from backend.auth.redis_client import get_redis
from backend.auth.audit_utils import log_auth_event, create_audit_log, log_tender_event
from backend.auth.models import AuditAction, AuditCategory, WorkspaceRole, WorkspaceMember
from backend.mongodb.routes import router as tenders_router
from backend.mongodb.tenders_utils import MongoDB

# Store for OAuth state tokens (in production, use Redis or database)
oauth_states = {}


def set_refresh_token_cookie(response: Response, refresh_token: str):
    """Configura la cookie HttpOnly para el Refresh Token."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        expires=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
        secure=False,  # Cambiar a True en producción con HTTPS
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    """
    # Startup: PostgreSQL
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Startup: MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_db = os.getenv("MONGODB_DB_NAME", "lizicular_db")
    await MongoDB.connect_to_database(mongodb_url, mongodb_db)
    
    yield
    
    # Shutdown: Dispose engines
    await engine.dispose()
    await MongoDB.close_database_connection()


# Initialize FastAPI application
app = FastAPI(
    title="Lizicular API",
    description="Centralized authentication and Tender Management system",
    version="2.1.0",
    lifespan=lifespan
)

# Include routers
app.include_router(tenders_router)


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
    request: Request,
    db: Any = Depends(get_db)
) -> UserResponse:
    """
    Register a new user in the system with email/password.
    
    Args:
        user_data: User registration data (email, password, full_name)
        request: FastAPI Request object
        db: Database session
        
    Returns:
        Created user information (without password)
        
    Raises:
        HTTPException 400: If email already exists
    """
    # Check if user already exists
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

        # Log successful signup
        await log_auth_event(
            db=db,
            action=AuditAction.LOGIN_SUCCESS, # Could use a SIGNUP action if defined, but LOGIN_SUCCESS works for now or generic AuditAction
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


@app.post(
    "/auth/login",
    response_model=Token,
    summary="Login and get access token",
    tags=["Authentication"]
)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Any = Depends(get_db)
) -> Token:
    """
    Authenticate user and return JWT access token.
    
    Args:
        request: FastAPI Request object
        response: FastAPI Response object
        form_data: OAuth2 form with username (email) and password
        db: Database session
        
    Returns:
        Access token and token type
        
    Raises:
        HTTPException 401: If credentials are invalid
    """
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
    
    # Create access token (15 mins)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    # Create refresh token (7 days)
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    # Set refresh token in cookie
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


@app.post(
    "/auth/login/json",
    response_model=Token,
    summary="Login with JSON payload",
    tags=["Authentication"]
)
async def login_json(
    request: Request,
    response: Response,
    credentials: UserLogin,
    db: Any = Depends(get_db)
) -> Token:
    """
    Alternative login endpoint that accepts JSON instead of form data.
    
    Args:
        request: FastAPI Request object
        response: FastAPI Response object
        credentials: User login credentials (email and password)
        db: Database session
        
    Returns:
        Access token and token type
        
    Raises:
        HTTPException 401: If credentials are invalid
    """
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
    
    # Create access token (15 mins)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    # Create refresh token (7 days)
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    # Set refresh token in cookie
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


@app.get(
    "/auth/{provider}/login",
    summary="Initiate OAuth login",
    tags=["OAuth2"]
)
async def oauth_login(provider: str, request: Request, db: Any = Depends(get_db)):
    """
    Initiate OAuth2 login flow with a provider.
    
    Supported providers: google, facebook, github, microsoft
    
    Args:
        provider: OAuth provider name
        request: Request object
        db: Database session
        
    Returns:
        Redirect to OAuth provider's authorization page
    """
    if provider not in OAuthConfig.get_enabled_providers():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not enabled or configured"
        )
    
    # Log attempt
    await log_auth_event(
        db=db,
        action=AuditAction.OAUTH_LOGIN,
        success=True,
        request=request,
        details=f"Initiating OAuth login with {provider}"
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
    request: Request,
    response: Response,
    db: Any = Depends(get_db)
):
    """
    Handle OAuth2 callback and authenticate user.
    
    Args:
        provider: OAuth provider name
        code: Authorization code from provider
        state: State token for CSRF validation
        request: FastAPI Request object
        response: FastAPI Response object
        db: Database session
        
    Returns:
        Access token
    """
    # Validate state token
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
    
    # Get user info from OAuth provider
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
    
    # Get or create user
    user = await get_or_create_oauth_user(db, oauth_info)
    
    # Create access token (15 mins)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    # Create refresh token (7 days)
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    # Set refresh token in cookie
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


@app.post(
    "/auth/refresh",
    response_model=Token,
    summary="Refresh access token using refresh token from cookie",
    tags=["Authentication"]
)
async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(None),
    db: Any = Depends(get_db),
    redis: Any = Depends(get_redis)
) -> Token:
    """
    Endpoint para obtener un nuevo Access Token usando el Refresh Token de la cookie.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Validar el refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        jti: str = payload.get("jti")
        
        if email is None or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
        # Comprobar si el refresh token ha sido invalidado
        if jti and await is_token_blacklisted(redis, jti):
            raise HTTPException(status_code=401, detail="Refresh token has been revoked")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Verificar que el usuario existe y está activo
    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")

    # Invalida el refresh token antiguo (rotación)
    if jti:
        await add_token_to_blacklist(redis, jti, REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)

    # Generar nuevo Access Token (15 mins)
    new_access_token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})

    # Generar nuevo Refresh Token y actualizar cookie
    new_refresh_token = create_refresh_token(data={"sub": user.email, "user_id": str(user.id)})
    set_refresh_token_cookie(response, new_refresh_token)

    return Token(access_token=new_access_token, token_type="bearer")


@app.post(
    "/auth/logout",
    summary="Logout and clear refresh token cookie",
    tags=["Authentication"]
)
async def logout(
    response: Response,
    token: str = Depends(oauth2_scheme),
    refresh_token: str | None = Cookie(None),
    redis: Any = Depends(get_redis)
):
    """
    Cierra la sesión eliminando la cookie del refresh token e invalidando los tokens actuales en Redis.
    """
    # Invalidar Access Token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if jti:
            await add_token_to_blacklist(redis, jti, ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    except JWTError:
        pass # Token ya inválido o malformado

    # Invalidar Refresh Token
    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                await add_token_to_blacklist(redis, jti, REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        except JWTError:
            pass

    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully and tokens invalidated"}


@app.get(
    "/users/me",
    response_model=UserResponse,
    summary="Get current user information",
    tags=["Users"]
)
async def read_users_me(
    request: Request,
    db: Any = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get information about the currently authenticated user.
    
    This is a protected endpoint that requires a valid JWT token.
    
    Args:
        request: FastAPI Request object
        db: Database session
        current_user: Current authenticated user (from JWT token)
        
    Returns:
        Current user information
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

# ============================================================================
# WORKSPACES ENDPOINTS
# ============================================================================
from backend.auth.schemas import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate, WorkspaceMemberAdd, WorkspaceMemberUpdate, WorkspaceMemberResponse
from backend.auth.models import Workspace
from sqlalchemy.orm import selectinload

workspaces_router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@workspaces_router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    new_workspace = Workspace(
        name=workspace_data.name,
        description=workspace_data.description,
        owner_id=current_user.id
    )
    
    # The creator automatically becomes the owner
    member = WorkspaceMember(
        workspace=new_workspace,
        user=current_user,
        role=WorkspaceRole.OWNER
    )
    
    db.add(new_workspace)
    db.add(member)
    await db.commit()
    await db.refresh(new_workspace)
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.WORKSPACE_CREATE,
        user_id=current_user.id,
        workspace_id=new_workspace.id,
        payload={"name": new_workspace.name},
        ip_address=request.client.host
    )
    
    return new_workspace

@workspaces_router.get("/", response_model=List[WorkspaceResponse])
async def get_user_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Workspace).join(WorkspaceMember).where(
            WorkspaceMember.user_id == current_user.id
        )
    )
    return result.scalars().all()

@workspaces_router.get("/detailed/", response_model=List[WorkspaceWithTendersResponse])
async def get_user_workspaces_with_tenders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a detailed list of workspaces for the current user, including their role
    and a summary of tenders in each workspace.
    """
    # 1. Get all workspace memberships for the user
    result = await db.execute(
        select(WorkspaceMember)
        .where(WorkspaceMember.user_id == current_user.id)
        .options(selectinload(WorkspaceMember.workspace))
    )
    memberships = result.scalars().all()
    
    response_list = []
    
    # 2. For each membership, fetch tenders from MongoDB
    for member in memberships:
        workspace = member.workspace
        if not workspace:
            continue
            
        tenders_from_mongo = await get_tenders_by_workspace(MongoDB.database, str(workspace.id))
        
        # 3. Create the nested response object
        workspace_details = WorkspaceWithTendersResponse(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            owner_id=workspace.owner_id,
            is_active=workspace.is_active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            user_role=member.role,
            tenders=[
                TenderSummaryResponse(
                    id=str(t.id),
                    name=t.name,
                    created_at=t.created_at
                ) for t in tenders_from_mongo
            ]
        )
        response_list.append(workspace_details)
        
    return response_list

@workspaces_router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Workspace).join(WorkspaceMember).where(
            Workspace.id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
    )
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
        
    return workspace

@workspaces_router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    workspace_data: WorkspaceUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not an owner of the workspace")

    update_data = workspace_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workspace, key, value)
    
    await db.commit()
    await db.refresh(workspace)
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.WORKSPACE_UPDATE,
        user_id=current_user.id,
        workspace_id=workspace.id,
        payload=update_data,
        ip_address=request.client.host
    )
    
    return workspace

@workspaces_router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not an owner of the workspace")

    await db.delete(workspace)
    await db.commit()
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.WORKSPACE_DELETE,
        user_id=current_user.id,
        workspace_id=workspace.id,
        ip_address=request.client.host
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Workspace Members Endpoints ---

@workspaces_router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: str,
    member_data: WorkspaceMemberAdd,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if current user is owner or admin
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can add members")

    # Find user to add
    user_to_add = await get_user_by_email(db, member_data.user_email)
    if not user_to_add:
        raise HTTPException(status_code=404, detail=f"User with email {member_data.user_email} not found")
        
    # Check if user is already a member
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_to_add.id))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")

    new_member = WorkspaceMember(workspace_id=workspace_id, user_id=user_to_add.id, role=member_data.role.upper())
    db.add(new_member)
    await db.commit()
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.MEMBER_ADD,
        user_id=current_user.id,
        workspace_id=workspace_id,
        payload={"added_user_email": user_to_add.email, "role": new_member.role},
        ip_address=request.client.host
    )
    
    return WorkspaceMemberResponse(
        user_id=user_to_add.id,
        email=user_to_add.email,
        full_name=user_to_add.full_name,
        role=new_member.role
    )

@workspaces_router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if current user is a member
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
        
    # Get all members
    result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id).options(selectinload(WorkspaceMember.user))
    )
    members = result.scalars().all()
    
    return [
        WorkspaceMemberResponse(
            user_id=member.user.id,
            email=member.user.email,
            full_name=member.user.full_name,
            role=member.role
        ) for member in members
    ]

@workspaces_router.put("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_workspace_member(
    workspace_id: str,
    user_id: str,
    member_data: WorkspaceMemberUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if current user is owner or admin
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can update members")

    # Get member to update
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id).options(selectinload(WorkspaceMember.user)))
    member_to_update = res.scalar_one_or_none()
    if not member_to_update:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")
        
    member_to_update.role = member_data.role.upper()
    await db.commit()
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.ROLE_CHANGE,
        user_id=current_user.id,
        workspace_id=workspace_id,
        payload={"updated_user_id": str(member_to_update.user_id), "new_role": member_to_update.role},
        ip_address=request.client.host
    )
    
    return WorkspaceMemberResponse(
        user_id=member_to_update.user.id,
        email=member_to_update.user.email,
        full_name=member_to_update.user.full_name,
        role=member_to_update.role
    )

@workspaces_router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if current user is owner or admin
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
    current_member = res.scalar_one_or_none()
    if not current_member or current_member.role not in [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only workspace owners or admins can remove members")
        
    # Get member to remove
    res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id))
    member_to_remove = res.scalar_one_or_none()
    if not member_to_remove:
        raise HTTPException(status_code=404, detail="Member not found in this workspace")
        
    # Prevent owner from being removed
    if member_to_remove.role == WorkspaceRole.OWNER:
        raise HTTPException(status_code=400, detail="Workspace owner cannot be removed")

    await db.delete(member_to_remove)
    await db.commit()
    
    await create_audit_log(
        db,
        category=AuditCategory.WORKSPACE,
        action=AuditAction.MEMBER_REMOVE,
        user_id=current_user.id,
        workspace_id=workspace_id,
        payload={"removed_user_id": str(user_id)},
        ip_address=request.client.host
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

app.include_router(workspaces_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
