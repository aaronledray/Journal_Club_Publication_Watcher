"""
User search configuration API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.search_config import SearchConfig, Keyword, Journal, TrackedAuthor
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

router = APIRouter(prefix="/api/config", tags=["config"])


def get_user_config(user: User, db: Session) -> SearchConfig:
    """Get or create user's search config."""
    if not user.search_config:
        config = SearchConfig(user_id=user.id)
        db.add(config)
        db.commit()
        db.refresh(config)
        return config
    return user.search_config


# Search Config
@router.get("", response_model=SearchConfigResponse)
async def get_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's search configuration."""
    config = get_user_config(current_user, db)
    return config


@router.put("", response_model=SearchConfigResponse)
async def update_config(
    update: SearchConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's search configuration."""
    config = get_user_config(current_user, db)

    if update.search_frequency is not None:
        config.search_frequency = update.search_frequency

    db.commit()
    db.refresh(config)
    return config


# Keywords
@router.get("/keywords", response_model=list[KeywordResponse])
async def list_keywords(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's keywords."""
    config = get_user_config(current_user, db)
    return config.keywords


@router.post("/keywords", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword(
    keyword: KeywordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new keyword."""
    config = get_user_config(current_user, db)

    # Check for duplicates
    existing = (
        db.query(Keyword)
        .filter(
            Keyword.search_config_id == config.id,
            Keyword.keyword.ilike(keyword.keyword),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Keyword already exists",
        )

    db_keyword = Keyword(search_config_id=config.id, keyword=keyword.keyword)
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@router.delete("/keywords/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    keyword_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a keyword."""
    config = get_user_config(current_user, db)

    keyword = (
        db.query(Keyword)
        .filter(Keyword.id == keyword_id, Keyword.search_config_id == config.id)
        .first()
    )
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found",
        )

    db.delete(keyword)
    db.commit()


# Journals
@router.get("/journals", response_model=list[JournalResponse])
async def list_journals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's journals."""
    config = get_user_config(current_user, db)
    return config.journals


@router.post("/journals", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
async def create_journal(
    journal: JournalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new journal."""
    config = get_user_config(current_user, db)

    # Check for duplicates
    existing = (
        db.query(Journal)
        .filter(
            Journal.search_config_id == config.id,
            Journal.name.ilike(journal.name),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Journal already exists",
        )

    db_journal = Journal(search_config_id=config.id, name=journal.name)
    db.add(db_journal)
    db.commit()
    db.refresh(db_journal)
    return db_journal


@router.delete("/journals/{journal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal(
    journal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a journal."""
    config = get_user_config(current_user, db)

    journal = (
        db.query(Journal)
        .filter(Journal.id == journal_id, Journal.search_config_id == config.id)
        .first()
    )
    if not journal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal not found",
        )

    db.delete(journal)
    db.commit()


# Authors
@router.get("/authors", response_model=list[AuthorResponse])
async def list_authors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user's tracked authors."""
    config = get_user_config(current_user, db)
    return config.authors


@router.post("/authors", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    author: AuthorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new tracked author."""
    config = get_user_config(current_user, db)

    # Check for duplicates
    existing = (
        db.query(TrackedAuthor)
        .filter(
            TrackedAuthor.search_config_id == config.id,
            TrackedAuthor.orcid == author.orcid,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Author with this ORCID already exists",
        )

    db_author = TrackedAuthor(
        search_config_id=config.id,
        orcid=author.orcid,
        name=author.name,
    )
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author


@router.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a tracked author."""
    config = get_user_config(current_user, db)

    author = (
        db.query(TrackedAuthor)
        .filter(TrackedAuthor.id == author_id, TrackedAuthor.search_config_id == config.id)
        .first()
    )
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    db.delete(author)
    db.commit()
