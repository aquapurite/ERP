import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.models.user import User
from app.core.security import get_password_hash


router = APIRouter(tags=["Authentication"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


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


# Store reset tokens in memory (for production, use Redis or database)
password_reset_tokens: dict = {}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: DB,
):
    """
    Request a password reset. Generates a reset token.
    In production, this would send an email with the reset link.
    """
    # Find user by email
    stmt = select(User).where(User.email == data.email.lower())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user:
        return {
            "message": "If this email exists, a password reset link has been sent.",
            "token": None  # Don't reveal if user exists
        }

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    # Store token (in production, store in database or Redis)
    password_reset_tokens[reset_token] = {
        "user_id": str(user.id),
        "email": user.email,
        "expires_at": expires_at
    }

    # For development/testing, return the token directly
    # In production, send email instead
    return {
        "message": "Password reset token generated. Use this token to reset your password.",
        "token": reset_token,
        "expires_in": "1 hour",
        "reset_url": f"/reset-password?token={reset_token}"
    }


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: DB,
):
    """
    Reset password using a valid reset token.
    """
    # Validate token
    token_data = password_reset_tokens.get(data.token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if datetime.utcnow() > token_data["expires_at"]:
        # Remove expired token
        del password_reset_tokens[data.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )

    # Find user
    stmt = select(User).where(User.email == token_data["email"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    # Update password
    user.password_hash = get_password_hash(data.new_password)
    await db.commit()

    # Remove used token
    del password_reset_tokens[data.token]

    return {"message": "Password has been reset successfully. You can now login with your new password."}
