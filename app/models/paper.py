"""
Paper and user paper state models.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Paper(Base):
    """Publication/paper found in a search."""

    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    search_run_id = Column(Integer, ForeignKey("search_runs.id"), nullable=False)

    # Core paper data (matches standardized format from paper_processor)
    title = Column(String(1000), nullable=False)
    journal = Column(String(255), nullable=True)
    authors = Column(JSON, nullable=True)  # List of author names
    date = Column(String(20), nullable=True)  # YYYY/MM/DD format
    abstract = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)  # List of keywords
    institutions = Column(JSON, nullable=True)  # List of institutions
    link = Column(String(500), nullable=True)

    # Source: keyword, pubmed_author, crossref
    source = Column(String(50), nullable=False)

    # Deduplication identifiers
    doi = Column(String(100), nullable=True, index=True)
    pmid = Column(String(20), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    search_run = relationship("SearchRun", back_populates="papers")
    user_states = relationship(
        "UserPaperState", back_populates="paper", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Paper(id={self.id}, title={self.title[:50]}...)>"

    def to_dict(self) -> dict:
        """Convert to dictionary matching the standardized paper format."""
        return {
            "id": self.id,
            "Title": self.title,
            "Journal": self.journal,
            "Authors": self.authors or [],
            "Date": self.date,
            "Abstract": self.abstract,
            "Keywords": self.keywords or [],
            "Institution": self.institutions or [],
            "Link": self.link,
            "Source": self.source,
            "doi": self.doi,
            "pmid": self.pmid,
        }


class UserPaperState(Base):
    """Track user-specific paper states (read, saved, notes)."""

    __tablename__ = "user_paper_states"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)

    is_read = Column(Boolean, default=False)
    is_saved = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    read_at = Column(DateTime, nullable=True)
    saved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uix_user_paper"),
    )

    # Relationships
    user = relationship("User", back_populates="paper_states")
    paper = relationship("Paper", back_populates="user_states")

    def __repr__(self):
        return f"<UserPaperState(user_id={self.user_id}, paper_id={self.paper_id}, read={self.is_read}, saved={self.is_saved})>"
