"""
Authentication service for magic link authentication.
"""

import secrets
from datetime import datetime, timedelta
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, MagicLinkToken
from app.models.search_config import SearchConfig


def get_or_create_user(db: Session, email: str) -> User:
    """
    Get existing user or create new one.

    Args:
        db: Database session
        email: User email address

    Returns:
        User object
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create default search config for new user
        search_config = SearchConfig(user_id=user.id)
        db.add(search_config)
        db.commit()

    return user


def create_magic_link_token(db: Session, user_id: int) -> str:
    """
    Create a magic link token for user authentication.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Token string
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=settings.MAGIC_LINK_EXPIRATION_MINUTES)

    db_token = MagicLinkToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()

    return token


def verify_magic_link_token(db: Session, token: str) -> User | None:
    """
    Verify a magic link token and return the associated user.

    Args:
        db: Database session
        token: Token string to verify

    Returns:
        User object if valid, None otherwise
    """
    db_token = (
        db.query(MagicLinkToken)
        .filter(
            MagicLinkToken.token == token,
            MagicLinkToken.used == False,
            MagicLinkToken.expires_at > datetime.utcnow(),
        )
        .first()
    )

    if not db_token:
        return None

    # Mark token as used
    db_token.used = True

    # Update user
    user = db.query(User).get(db_token.user_id)
    if user:
        user.is_verified = True
        user.last_login = datetime.utcnow()

    db.commit()

    return user


def create_session_token(user: User) -> str:
    """
    Create a JWT session token for authenticated user.

    Args:
        user: User object

    Returns:
        JWT token string
    """
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(days=settings.JWT_EXPIRATION_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def get_user_from_token(db: Session, token: str) -> User | None:
    """
    Get user from JWT token.

    Args:
        db: Database session
        token: JWT token string

    Returns:
        User object if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
        return db.query(User).get(user_id)
    except (JWTError, ValueError, TypeError):
        return None
