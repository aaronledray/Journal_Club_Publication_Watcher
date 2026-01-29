"""
User search configuration models.
Stores keywords, journals, and tracked authors for each user.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class SearchConfig(Base):
    """User's search configuration settings."""

    __tablename__ = "search_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Search frequency: daily, weekly, biweekly, monthly
    search_frequency = Column(String(20), default="weekly")
    last_scheduled_run = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="search_config")
    keywords = relationship(
        "Keyword", back_populates="search_config", cascade="all, delete-orphan"
    )
    journals = relationship(
        "Journal", back_populates="search_config", cascade="all, delete-orphan"
    )
    authors = relationship(
        "TrackedAuthor", back_populates="search_config", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SearchConfig(id={self.id}, user_id={self.user_id}, frequency={self.search_frequency})>"


class Keyword(Base):
    """Search keywords for a user's configuration."""

    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    search_config_id = Column(Integer, ForeignKey("search_configs.id"), nullable=False)
    keyword = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    search_config = relationship("SearchConfig", back_populates="keywords")

    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword={self.keyword})>"


class Journal(Base):
    """Journals to filter in a user's searches."""

    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    search_config_id = Column(Integer, ForeignKey("search_configs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    search_config = relationship("SearchConfig", back_populates="journals")

    def __repr__(self):
        return f"<Journal(id={self.id}, name={self.name})>"


class TrackedAuthor(Base):
    """Authors to track via ORCID in a user's searches."""

    __tablename__ = "tracked_authors"

    id = Column(Integer, primary_key=True, index=True)
    search_config_id = Column(Integer, ForeignKey("search_configs.id"), nullable=False)
    name = Column(String(255), nullable=True)  # Optional display name
    orcid = Column(String(20), nullable=False)  # Format: 0000-0000-0000-0000
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    search_config = relationship("SearchConfig", back_populates="authors")

    def __repr__(self):
        return f"<TrackedAuthor(id={self.id}, orcid={self.orcid}, name={self.name})>"
