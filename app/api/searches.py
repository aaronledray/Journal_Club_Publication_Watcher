"""
Search execution API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.search_run import SearchRun
from app.models.paper import Paper
from app.schemas.search import SearchRunCreate, SearchRunResponse, SearchRunListResponse
from app.schemas.paper import PaperResponse
from app.services.search_service import run_user_search

router = APIRouter(prefix="/api/searches", tags=["searches"])


@router.post("", response_model=SearchRunResponse, status_code=status.HTTP_201_CREATED)
async def create_search(
    search: SearchRunCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a new search with the user's configuration.

    This executes synchronously for now. For large searches,
    consider using background tasks.
    """
    # Check if user has any search config
    config = current_user.search_config
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No search configuration found. Please add keywords and journals first.",
        )

    has_keywords = any(k.is_active for k in config.keywords)
    has_journals = any(j.is_active for j in config.journals)
    has_authors = any(a.is_active for a in config.authors)

    if not has_keywords and not has_journals and not has_authors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please add at least one keyword, journal, or author to search.",
        )

    # Run search
    search_run = run_user_search(
        user_id=current_user.id,
        db=db,
        start_date=search.start_date,
        end_date=search.end_date,
        search_mode=search.search_mode,
    )

    return search_run


@router.get("", response_model=SearchRunListResponse)
async def list_searches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    """List user's search runs."""
    query = (
        db.query(SearchRun)
        .filter(SearchRun.user_id == current_user.id)
        .order_by(SearchRun.started_at.desc())
    )

    total = query.count()
    search_runs = query.offset(skip).limit(limit).all()

    return SearchRunListResponse(
        search_runs=search_runs,
        total=total,
    )


@router.get("/{search_id}", response_model=SearchRunResponse)
async def get_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific search run."""
    search_run = (
        db.query(SearchRun)
        .filter(SearchRun.id == search_id, SearchRun.user_id == current_user.id)
        .first()
    )

    if not search_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search run not found",
        )

    return search_run


@router.get("/{search_id}/papers", response_model=list[PaperResponse])
async def get_search_papers(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    source: str | None = None,
):
    """Get papers from a specific search run."""
    search_run = (
        db.query(SearchRun)
        .filter(SearchRun.id == search_id, SearchRun.user_id == current_user.id)
        .first()
    )

    if not search_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search run not found",
        )

    query = db.query(Paper).filter(Paper.search_run_id == search_id)

    if source:
        query = query.filter(Paper.source == source)

    papers = query.all()
    return papers
