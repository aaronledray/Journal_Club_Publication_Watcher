"""
Search configuration Pydantic schemas.
"""

from datetime import datetime
from pydantic import BaseModel, field_validator
import re


class KeywordCreate(BaseModel):
    """Request to create a new keyword."""

    keyword: str

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Keyword cannot be empty")
        if len(v) > 255:
            raise ValueError("Keyword must be 255 characters or less")
        return v


class KeywordResponse(BaseModel):
    """Keyword response."""

    id: int
    keyword: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class JournalCreate(BaseModel):
    """Request to create a new journal."""

    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Journal name cannot be empty")
        if len(v) > 255:
            raise ValueError("Journal name must be 255 characters or less")
        return v


class JournalResponse(BaseModel):
    """Journal response."""

    id: int
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthorCreate(BaseModel):
    """Request to create a new tracked author."""

    orcid: str
    name: str | None = None

    @field_validator("orcid")
    @classmethod
    def validate_orcid(cls, v: str) -> str:
        v = v.strip()
        # Remove URL prefix if present
        if "orcid.org/" in v:
            v = v.split("orcid.org/")[-1]
        # Validate ORCID format
        pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$"
        if not re.match(pattern, v):
            raise ValueError("Invalid ORCID format. Expected: 0000-0000-0000-0000")
        return v


class AuthorResponse(BaseModel):
    """Tracked author response."""

    id: int
    orcid: str
    name: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SearchConfigUpdate(BaseModel):
    """Request to update search configuration."""

    search_frequency: str | None = None

    @field_validator("search_frequency")
    @classmethod
    def validate_frequency(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_frequencies = ["daily", "weekly", "biweekly", "monthly"]
        if v not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {', '.join(valid_frequencies)}")
        return v


class SearchConfigResponse(BaseModel):
    """Search configuration response."""

    id: int
    search_frequency: str
    last_scheduled_run: datetime | None
    keywords: list[KeywordResponse]
    journals: list[JournalResponse]
    authors: list[AuthorResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
