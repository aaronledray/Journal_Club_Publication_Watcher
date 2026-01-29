"""
Search run Pydantic schemas.
"""

from datetime import datetime
from pydantic import BaseModel, field_validator


class SearchRunCreate(BaseModel):
    """Request to create a new search run."""

    start_date: str | None = None  # YYYY/MM/DD, if None will calculate from frequency
    end_date: str | None = None  # YYYY/MM/DD, if None will use today
    search_mode: str = "both"  # keywords, authors, both

    @field_validator("search_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        valid_modes = ["keywords", "authors", "both"]
        if v not in valid_modes:
            raise ValueError(f"Search mode must be one of: {', '.join(valid_modes)}")
        return v


class SearchRunResponse(BaseModel):
    """Search run response."""

    id: int
    started_at: datetime
    completed_at: datetime | None
    status: str
    error_message: str | None
    start_date: str
    end_date: str
    search_mode: str
    total_papers_found: int
    keyword_papers_count: int
    author_papers_count: int

    class Config:
        from_attributes = True


class SearchRunListResponse(BaseModel):
    """List of search runs response."""

    search_runs: list[SearchRunResponse]
    total: int
