"""
Search run model for tracking search executions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class SearchRun(Base):
    """Record of a search execution."""

    __tablename__ = "search_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Status: pending, running, completed, failed
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)

    # Search parameters (snapshot at time of search)
    start_date = Column(String(10), nullable=False)  # YYYY/MM/DD
    end_date = Column(String(10), nullable=False)  # YYYY/MM/DD
    search_mode = Column(String(20), default="both")  # keywords, authors, both

    # Results summary
    total_papers_found = Column(Integer, default=0)
    keyword_papers_count = Column(Integer, default=0)
    author_papers_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="search_runs")
    papers = relationship(
        "Paper", back_populates="search_run", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SearchRun(id={self.id}, user_id={self.user_id}, status={self.status})>"

    @property
    def duration_seconds(self) -> float | None:
        """Calculate duration of the search run."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
