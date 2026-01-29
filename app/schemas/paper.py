"""
Paper-related Pydantic schemas.
"""

from datetime import datetime
from pydantic import BaseModel


class PaperResponse(BaseModel):
    """Paper response."""

    id: int
    title: str
    journal: str | None
    authors: list[str] | None
    date: str | None
    abstract: str | None
    keywords: list[str] | None
    institutions: list[str] | None
    link: str | None
    source: str
    doi: str | None
    pmid: str | None
    created_at: datetime

    # User-specific state (if requested)
    is_read: bool | None = None
    is_saved: bool | None = None

    class Config:
        from_attributes = True


class PaperStateUpdate(BaseModel):
    """Request to update paper state."""

    is_read: bool | None = None
    is_saved: bool | None = None
    notes: str | None = None


class PaperListResponse(BaseModel):
    """List of papers response."""

    papers: list[PaperResponse]
    total: int
    page: int
    per_page: int
    has_more: bool
