"""
Authentication-related Pydantic schemas.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request to initiate magic link login."""

    email: EmailStr


class TokenResponse(BaseModel):
    """Response containing JWT token."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User information response."""

    id: int
    email: str
    is_verified: bool
    created_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True
