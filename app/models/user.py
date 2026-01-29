"""
User and authentication models.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    search_config = relationship(
        "SearchConfig", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    search_runs = relationship(
        "SearchRun", back_populates="user", cascade="all, delete-orphan"
    )
    paper_states = relationship(
        "UserPaperState", back_populates="user", cascade="all, delete-orphan"
    )
    magic_link_tokens = relationship(
        "MagicLinkToken", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class MagicLinkToken(Base):
    """Magic link tokens for passwordless authentication."""

    __tablename__ = "magic_link_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="magic_link_tokens")

    def __repr__(self):
        return f"<MagicLinkToken(id={self.id}, user_id={self.user_id}, used={self.used})>"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.used and not self.is_expired
