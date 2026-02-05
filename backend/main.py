"""
Main FastAPI application entrypoint.
This file initializes the FastAPI app, includes the different routers,
and handles the application's lifespan events.
"""
from __future__ import annotations
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.auth.models import Base
from backend.auth.schemas import OAuthUserInfo
from backend.auth.oauth_config import OAuthConfig
from backend.auth.oauth_utils import OAuthProvider, get_oauth_user
from backend.auth.database import engine
from backend.tenders.routes import router as tenders_router
from backend.workspaces.routes import router as workspaces_router
from backend.auth.routes import router as auth_router, users_router
from backend.tenders.tenders_utils import MongoDB

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

# Add CORS Middleware
origins = [
    "http://localhost:3000",  # Frontend development server
    # Add other origins for production if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tenders_router)
app.include_router(workspaces_router)


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