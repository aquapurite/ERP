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


async def auto_link_vendors_to_supplier_codes():
    """Auto-link vendors to supplier codes if not already linked."""
    from sqlalchemy import select
    from app.models.vendor import Vendor
    from app.models.serialization import SupplierCode
    import uuid

    print("AUTO-LINK: Starting vendor-supplier code linking...")

    try:
        async with async_session_factory() as db:
            # Find vendors that match known supplier codes but aren't linked
            vendor_mappings = [
                ("STOS", "ST"),  # STOS Industrial -> ST supplier code
            ]

            for vendor_pattern, supplier_code in vendor_mappings:
                print(f"AUTO-LINK: Checking {vendor_pattern} -> {supplier_code}")

                # Check if supplier code exists and is linked
                sc_result = await db.execute(
                    select(SupplierCode).where(SupplierCode.code == supplier_code)
                )
                sc = sc_result.scalar_one_or_none()
                print(f"AUTO-LINK: Supplier code '{supplier_code}' exists: {sc is not None}, vendor_id: {sc.vendor_id if sc else 'N/A'}")

                if sc and sc.vendor_id:
                    print(f"AUTO-LINK: '{supplier_code}' already linked to vendor_id={sc.vendor_id}")
                    continue

                # Find vendor
                vendor_result = await db.execute(
                    select(Vendor).where(Vendor.name.ilike(f"%{vendor_pattern}%"))
                )
                vendor = vendor_result.scalar_one_or_none()
                print(f"AUTO-LINK: Vendor matching '{vendor_pattern}': {vendor.name if vendor else 'NOT FOUND'}")

                if not vendor:
                    print(f"AUTO-LINK: No vendor found matching '{vendor_pattern}', skipping")
                    continue

                # Check if vendor already linked to another code
                existing_link = await db.execute(
                    select(SupplierCode).where(SupplierCode.vendor_id == vendor.id)
                )
                existing_sc = existing_link.scalar_one_or_none()
                if existing_sc:
                    print(f"AUTO-LINK: Vendor already linked to code '{existing_sc.code}', skipping")
                    continue

                if sc:
                    # Link existing supplier code to vendor
                    sc.vendor_id = vendor.id
                    print(f"AUTO-LINK: SUCCESS - Linked vendor '{vendor.name}' to supplier code '{supplier_code}'")
                else:
                    # Create new supplier code
                    new_sc = SupplierCode(
                        id=uuid.uuid4(),
                        code=supplier_code,
                        name=vendor.name,
                        vendor_id=vendor.id,
                        description=f"Auto-linked to {vendor.name}",
                        is_active=True,
                    )
                    db.add(new_sc)
                    print(f"AUTO-LINK: SUCCESS - Created supplier code '{supplier_code}' for vendor '{vendor.name}'")

            await db.commit()
            print("AUTO-LINK: Completed successfully")
    except Exception as e:
        import traceback
        print(f"AUTO-LINK ERROR: {type(e).__name__}: {e}")
        print(f"AUTO-LINK TRACEBACK: {traceback.format_exc()}")


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
    # Auto-link vendors to supplier codes
    await auto_link_vendors_to_supplier_codes()
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
    # Get origin from request
    origin = request.headers.get("origin", "")

    # Build response with CORS headers for error responses
    response = JSONResponse(
        status_code=500,
        content=error_detail
    )

    # Add CORS headers if origin is allowed
    if origin in settings.CORS_ORIGINS or "*" in settings.CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"

    return response


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
