from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs on startup and shutdown.
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Initialize database tables (for development)
    # In production, use Alembic migrations
    # await init_db()
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Consumer Durable Backend API

    This API provides backend services for a Consumer Durable brand management system.

    ### Features:
    - **Authentication**: JWT-based authentication with access/refresh tokens
    - **Role-Based Access Control (RBAC)**: Hierarchical roles with granular permissions
    - **User Management**: Create, update, and manage users with role assignments
    - **Audit Logging**: Track all access control changes

    ### Role Hierarchy:
    1. SUPER_ADMIN - Full system access
    2. DIRECTOR - Strategic oversight
    3. HEAD - Department leadership
    4. MANAGER - Operational management
    5. EXECUTIVE - Task execution
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }
