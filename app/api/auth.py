"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, UserResponse
from app.services.auth_service import (
    get_or_create_user,
    create_magic_link_token,
    verify_magic_link_token,
    create_session_token,
)
from app.services.email_service import send_magic_link_email
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Request a magic link login email.

    Creates or retrieves user, generates magic link token, and sends email.
    """
    # Get or create user
    user = get_or_create_user(db, request.email)

    # Create magic link token
    token = create_magic_link_token(db, user.id)

    # Send email (in dev mode, prints to console)
    await send_magic_link_email(request.email, token)

    return {
        "message": "Magic link sent! Check your email (or console in development mode).",
        "email": request.email,
    }


@router.get("/verify")
async def verify(token: str, response: Response, db: Session = Depends(get_db)):
    """
    Verify magic link token and create session.

    Redirects to dashboard on success, login page on failure.
    """
    user = verify_magic_link_token(db, token)

    if not user:
        # Redirect to login with error
        return RedirectResponse(
            url="/login?error=invalid_token",
            status_code=status.HTTP_302_FOUND,
        )

    # Create session token
    session_token = create_session_token(user)

    # Create redirect response
    redirect = RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_302_FOUND,
    )

    # Set session cookie
    redirect.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    return redirect


@router.post("/logout")
async def logout(response: Response):
    """
    Log out by clearing the session cookie.
    """
    redirect = RedirectResponse(
        url="/login",
        status_code=status.HTTP_302_FOUND,
    )
    redirect.delete_cookie("session_token")
    return redirect


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user info.
    """
    return current_user
