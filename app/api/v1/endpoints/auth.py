from fastapi import APIRouter, HTTPException, status, Request

from app.api.deps import DB, CurrentUser
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService


router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    data: LoginRequest,
    db: DB,
):
    """
    Authenticate user and return access/refresh tokens.
    """
    auth_service = AuthService(db)
    audit_service = AuditService(db)

    user = await auth_service.authenticate_user(data.email, data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token, expires_in = await auth_service.create_tokens(user)

    # Log the login
    await audit_service.log_user_login(
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: DB,
):
    """
    Refresh access token using a valid refresh token.
    """
    auth_service = AuthService(db)

    result = await auth_service.refresh_tokens(data.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, refresh_token, expires_in = result

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: CurrentUser,
    db: DB,
):
    """
    Logout current user (log the action).
    Note: JWT tokens are stateless, so actual invalidation
    would require a token blacklist (not implemented here).
    """
    audit_service = AuditService(db)

    await audit_service.log_user_logout(
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(
    current_user: CurrentUser,
):
    """
    Get current authenticated user's information.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "department": current_user.department,
        "designation": current_user.designation,
        "is_active": current_user.is_active,
        "roles": [
            {
                "id": str(role.id),
                "name": role.name,
                "code": role.code,
                "level": role.level.name,
            }
            for role in current_user.roles
        ],
        "region": {
            "id": str(current_user.region.id),
            "name": current_user.region.name,
            "code": current_user.region.code,
            "type": current_user.region.type.value,
        } if current_user.region else None,
    }
