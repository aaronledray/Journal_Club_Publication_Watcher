"""
Database models package.
Import all models here so Alembic can discover them.
"""

from app.models.user import User, MagicLinkToken
from app.models.search_config import SearchConfig, Keyword, Journal, TrackedAuthor
from app.models.search_run import SearchRun
from app.models.paper import Paper, UserPaperState

__all__ = [
    "User",
    "MagicLinkToken",
    "SearchConfig",
    "Keyword",
    "Journal",
    "TrackedAuthor",
    "SearchRun",
    "Paper",
    "UserPaperState",
]
