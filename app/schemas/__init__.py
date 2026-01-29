"""
Pydantic schemas for request/response validation.
"""

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.search_config import (
    KeywordCreate,
    KeywordResponse,
    JournalCreate,
    JournalResponse,
    AuthorCreate,
    AuthorResponse,
    SearchConfigResponse,
    SearchConfigUpdate,
)
from app.schemas.paper import (
    PaperResponse,
    PaperStateUpdate,
    PaperListResponse,
)
from app.schemas.search import (
    SearchRunCreate,
    SearchRunResponse,
    SearchRunListResponse,
)

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    # Config
    "KeywordCreate",
    "KeywordResponse",
    "JournalCreate",
    "JournalResponse",
    "AuthorCreate",
    "AuthorResponse",
    "SearchConfigResponse",
    "SearchConfigUpdate",
    # Papers
    "PaperResponse",
    "PaperStateUpdate",
    "PaperListResponse",
    # Search
    "SearchRunCreate",
    "SearchRunResponse",
    "SearchRunListResponse",
]
