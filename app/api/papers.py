"""
Paper management API routes.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.paper import Paper, UserPaperState
from app.models.search_run import SearchRun
from app.schemas.paper import PaperResponse, PaperStateUpdate, PaperListResponse

router = APIRouter(prefix="/api/papers", tags=["papers"])


def get_paper_with_state(paper: Paper, user_id: int, db: Session) -> dict:
    """Get paper data with user-specific state."""
    state = (
        db.query(UserPaperState)
        .filter(UserPaperState.paper_id == paper.id, UserPaperState.user_id == user_id)
        .first()
    )

    paper_dict = {
        "id": paper.id,
        "title": paper.title,
        "journal": paper.journal,
        "authors": paper.authors,
        "date": paper.date,
        "abstract": paper.abstract,
        "keywords": paper.keywords,
        "institutions": paper.institutions,
        "link": paper.link,
        "source": paper.source,
        "doi": paper.doi,
        "pmid": paper.pmid,
        "created_at": paper.created_at,
        "is_read": state.is_read if state else False,
        "is_saved": state.is_saved if state else False,
    }

    return paper_dict


@router.get("", response_model=PaperListResponse)
async def list_papers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    per_page: int = 20,
    source: str | None = None,
    is_saved: bool | None = None,
    is_read: bool | None = None,
):
    """
    List papers from user's searches with optional filters.
    """
    # Get user's search run IDs
    search_run_ids = (
        db.query(SearchRun.id).filter(SearchRun.user_id == current_user.id).subquery()
    )

    # Base query for papers
    query = db.query(Paper).filter(Paper.search_run_id.in_(search_run_ids))

    # Apply source filter
    if source:
        query = query.filter(Paper.source == source)

    # Apply saved/read filters (requires join with UserPaperState)
    if is_saved is not None or is_read is not None:
        query = query.outerjoin(
            UserPaperState,
            (UserPaperState.paper_id == Paper.id)
            & (UserPaperState.user_id == current_user.id),
        )

        if is_saved is not None:
            if is_saved:
                query = query.filter(UserPaperState.is_saved == True)
            else:
                query = query.filter(
                    (UserPaperState.is_saved == False) | (UserPaperState.is_saved == None)
                )

        if is_read is not None:
            if is_read:
                query = query.filter(UserPaperState.is_read == True)
            else:
                query = query.filter(
                    (UserPaperState.is_read == False) | (UserPaperState.is_read == None)
                )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    papers = query.order_by(Paper.created_at.desc()).offset(offset).limit(per_page).all()

    # Build response with user states
    paper_responses = [get_paper_with_state(p, current_user.id, db) for p in papers]

    return PaperListResponse(
        papers=paper_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_more=(offset + len(papers)) < total,
    )


@router.get("/saved", response_model=list[PaperResponse])
async def list_saved_papers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all saved papers for current user."""
    saved_states = (
        db.query(UserPaperState)
        .filter(
            UserPaperState.user_id == current_user.id,
            UserPaperState.is_saved == True,
        )
        .all()
    )

    paper_ids = [s.paper_id for s in saved_states]
    papers = db.query(Paper).filter(Paper.id.in_(paper_ids)).all()

    return [get_paper_with_state(p, current_user.id, db) for p in papers]


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific paper."""
    # Verify paper belongs to user's searches
    search_run_ids = (
        db.query(SearchRun.id).filter(SearchRun.user_id == current_user.id).subquery()
    )

    paper = (
        db.query(Paper)
        .filter(Paper.id == paper_id, Paper.search_run_id.in_(search_run_ids))
        .first()
    )

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    return get_paper_with_state(paper, current_user.id, db)


@router.patch("/{paper_id}/state", response_model=PaperResponse)
async def update_paper_state(
    paper_id: int,
    update: PaperStateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update paper state (read/saved/notes)."""
    # Verify paper belongs to user's searches
    search_run_ids = (
        db.query(SearchRun.id).filter(SearchRun.user_id == current_user.id).subquery()
    )

    paper = (
        db.query(Paper)
        .filter(Paper.id == paper_id, Paper.search_run_id.in_(search_run_ids))
        .first()
    )

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    # Get or create user paper state
    state = (
        db.query(UserPaperState)
        .filter(
            UserPaperState.paper_id == paper_id,
            UserPaperState.user_id == current_user.id,
        )
        .first()
    )

    if not state:
        state = UserPaperState(user_id=current_user.id, paper_id=paper_id)
        db.add(state)

    # Update state
    if update.is_read is not None:
        state.is_read = update.is_read
        if update.is_read:
            state.read_at = datetime.utcnow()

    if update.is_saved is not None:
        state.is_saved = update.is_saved
        if update.is_saved:
            state.saved_at = datetime.utcnow()

    if update.notes is not None:
        state.notes = update.notes

    db.commit()
    db.refresh(state)

    return get_paper_with_state(paper, current_user.id, db)
