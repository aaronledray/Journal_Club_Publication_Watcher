"""
FastAPI application entry point.
"""

from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, create_tables
from app.api import auth, config, searches, papers
from app.api.deps import get_current_user_optional
from app.models.user import User

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Track and discover academic publications based on keywords, journals, and authors.",
    version="1.0.0",
)

# Get paths
APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Set up templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Include API routers
app.include_router(auth.router)
app.include_router(config.router)
app.include_router(searches.router)
app.include_router(papers.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    create_tables()


# HTML Routes
@app.get("/")
async def home(request: Request, user: User | None = Depends(get_current_user_optional)):
    """Home page - redirects to dashboard if logged in, otherwise to login."""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login")
async def login_page(
    request: Request,
    error: str | None = None,
    user: User | None = Depends(get_current_user_optional),
):
    """Login page."""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "error": error},
    )


@app.get("/dashboard")
async def dashboard_page(
    request: Request,
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Main dashboard page."""
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Get user's search config
    config = user.search_config

    # Get recent search runs
    from app.models.search_run import SearchRun

    recent_searches = (
        db.query(SearchRun)
        .filter(SearchRun.user_id == user.id)
        .order_by(SearchRun.started_at.desc())
        .limit(5)
        .all()
    )

    # Get stats
    total_papers = sum(s.total_papers_found for s in recent_searches)
    total_searches = len(recent_searches)

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "user": user,
            "config": config,
            "recent_searches": recent_searches,
            "total_papers": total_papers,
            "total_searches": total_searches,
        },
    )


@app.get("/dashboard/results/{search_id}")
async def results_page(
    request: Request,
    search_id: int,
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Search results page."""
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    from app.models.search_run import SearchRun
    from app.models.paper import Paper

    search_run = (
        db.query(SearchRun)
        .filter(SearchRun.id == search_id, SearchRun.user_id == user.id)
        .first()
    )

    if not search_run:
        return RedirectResponse(url="/dashboard", status_code=302)

    papers = db.query(Paper).filter(Paper.search_run_id == search_id).all()

    return templates.TemplateResponse(
        "dashboard/results.html",
        {
            "request": request,
            "user": user,
            "search_run": search_run,
            "papers": papers,
        },
    )


@app.get("/dashboard/settings")
async def settings_page(
    request: Request,
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Settings page for managing keywords, journals, and authors."""
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    config = user.search_config

    return templates.TemplateResponse(
        "settings/index.html",
        {
            "request": request,
            "user": user,
            "config": config,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
