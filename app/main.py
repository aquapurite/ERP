from contextlib import asynccontextmanager
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.database import init_db, async_session_factory
from app.jobs.scheduler import start_scheduler, shutdown_scheduler


async def auto_seed_admin():
    """Create admin user on startup if no users exist."""
    from sqlalchemy import select, func
    from app.models.user import User, UserRole
    from app.models.role import Role, RoleLevel
    from app.core.security import get_password_hash

    try:
        async with async_session_factory() as session:
            # Check if any users exist
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar()

            if user_count == 0:
                print("No users found. Creating admin user...")

                # First, ensure super_admin role exists
                role_result = await session.execute(
                    select(Role).where(Role.code == "super_admin")
                )
                role = role_result.scalar_one_or_none()

                if not role:
                    role = Role(
                        name="Super Admin",
                        code="super_admin",
                        description="Full system access",
                        level=RoleLevel.SUPER_ADMIN,
                        is_system=True,
                    )
                    session.add(role)
                    await session.flush()
                    print("  Created super_admin role")

                # Create admin user
                admin = User(
                    email="admin@aquapurite.com",
                    phone="+919999999999",
                    password_hash=get_password_hash("Admin@123"),
                    first_name="Super",
                    last_name="Admin",
                    employee_code="EMP001",
                    department="Administration",
                    designation="System Administrator",
                    is_active=True,
                    is_verified=True,
                )
                session.add(admin)
                await session.flush()

                # Assign role
                user_role = UserRole(user_id=admin.id, role_id=role.id)
                session.add(user_role)

                await session.commit()
                print(f"  Created admin user: admin@aquapurite.com / Admin@123")
            else:
                print(f"Found {user_count} existing users. Skipping auto-seed.")
    except Exception as e:
        import traceback
        print(f"Auto-seed error: {e}")
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs on startup and shutdown.
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Initialize database tables
    await init_db()
    print("Database initialized")
    # Auto-seed admin user if needed
    await auto_seed_admin()
    # Start background job scheduler
    start_scheduler()
    print("Background scheduler started")
    yield
    # Shutdown
    shutdown_scheduler()
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


# Global exception handler to return detailed error for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return detailed error information for debugging."""
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": str(request.url.path),
        "method": request.method,
        "traceback": traceback.format_exc()
    }
    return JSONResponse(
        status_code=500,
        content=error_detail
    )


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
