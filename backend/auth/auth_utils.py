"""
Authentication utilities for password hashing and JWT token management.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import uuid
from .models import User
from .schemas import TokenData
from .database import get_db
from .redis_client import get_redis


# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT token (Access or Refresh) with a unique JTI.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # Añadir JTI único para identificación y lista negra
    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4())
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Helper to create an access token."""
    token_data = data.copy()
    token_data.update({"type": "access"})
    return create_token(token_data, expires_delta=expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(data: dict) -> str:
    """Helper to create a refresh token (7 days)."""
    token_data = data.copy()
    token_data.update({"type": "refresh"})
    return create_token(token_data, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


async def add_token_to_blacklist(redis_client: Any, jti: str, expire_seconds: int):
    """Añade un token JTI a la lista negra en Redis."""
    await redis_client.setex(f"blacklist:{jti}", expire_seconds, "true")


async def is_token_blacklisted(redis_client: Any, jti: str) -> bool:
    """Comprueba si un token JTI está en la lista negra."""
    return await redis_client.get(f"blacklist:{jti}") is not None


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Retrieve a user by email address.
    
    Args:
        db: Database session
        email: User's email address
        
    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = await get_user_by_email(db, email)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Any = Depends(get_db),
    redis: Any = Depends(get_redis)
) -> Any:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        redis: Redis client
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        
        if email is None or payload.get("type") != "access":
            raise credentials_exception
        
        # Comprobar si el token ha sido invalidado en Redis
        if jti and await is_token_blacklisted(redis, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(email=email)
        
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(db, email=token_data.email)
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return user

async def get_current_active_user(
    current_user: Any = Depends(get_current_user)
) -> Any:
    """
    Dependency to ensure the current user is active.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


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
