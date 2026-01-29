"""
API dependencies for authentication and database access.
"""

from fastapi import Depends, HTTPException, status, Request, Cookie
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_user_from_token


async def get_current_user(
    request: Request,
    session_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the currently authenticated user from JWT cookie.

    Args:
        request: FastAPI request object
        session_token: JWT token from cookie
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If not authenticated
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_from_token(db, session_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


async def get_current_user_optional(
    request: Request,
    session_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Get the currently authenticated user, or None if not authenticated.
    Used for pages that work both with and without authentication.
    """
    if not session_token:
        return None

    user = get_user_from_token(db, session_token)
    if not user or not user.is_active:
        return None

    return user
