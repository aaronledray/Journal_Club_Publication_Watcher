"""
Search service that wraps existing PubMed and CrossRef clients.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session

# Add project root to path to import existing modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from app.models.user import User
from app.models.search_config import SearchConfig
from app.models.search_run import SearchRun
from app.models.paper import Paper

# Import existing clients
from fetch_modules.pubmed_client import PubMedClient, lookup_pubmed
from fetch_modules.crossref_client import lookup_crossref
from core.paper_processor import process_papers


def calculate_date_range_from_frequency(frequency: str) -> tuple[str, str]:
    """
    Calculate date range based on search frequency.

    Args:
        frequency: One of 'daily', 'weekly', 'biweekly', 'monthly'

    Returns:
        Tuple of (start_date, end_date) in YYYY/MM/DD format
    """
    end_date = datetime.now()

    if frequency == "daily":
        start_date = end_date - timedelta(days=1)
    elif frequency == "weekly":
        start_date = end_date - timedelta(weeks=1)
    elif frequency == "biweekly":
        start_date = end_date - timedelta(weeks=2)
    elif frequency == "monthly":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(weeks=1)

    return (
        start_date.strftime("%Y/%m/%d"),
        end_date.strftime("%Y/%m/%d"),
    )


def extract_doi_from_link(link: str | None) -> str | None:
    """Extract DOI from a link or return None."""
    if not link:
        return None
    if "doi.org/" in link:
        return link.split("doi.org/")[-1]
    if link.startswith("10."):
        return link
    return None


def run_user_search(
    user_id: int,
    db: Session,
    start_date: str | None = None,
    end_date: str | None = None,
    search_mode: str = "both",
) -> SearchRun:
    """
    Execute a search for a user using their saved configuration.

    Args:
        user_id: User ID
        db: Database session
        start_date: Start date (YYYY/MM/DD), or None to calculate from frequency
        end_date: End date (YYYY/MM/DD), or None to use today
        search_mode: 'keywords', 'authors', or 'both'

    Returns:
        SearchRun object with results
    """
    user = db.query(User).get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    config = user.search_config
    if not config:
        raise ValueError(f"User {user_id} has no search configuration")

    # Calculate date range if not provided
    if not start_date or not end_date:
        start_date, end_date = calculate_date_range_from_frequency(config.search_frequency)

    # Create search run record
    search_run = SearchRun(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        search_mode=search_mode,
        status="running",
    )
    db.add(search_run)
    db.commit()
    db.refresh(search_run)

    try:
        # Build config dict compatible with existing functions
        config_dict = {
            "email": user.email,
            "topics": [k.keyword for k in config.keywords if k.is_active],
            "journals": [j.name for j in config.journals if j.is_active],
            "orcids": [a.orcid for a in config.authors if a.is_active],
            "named_authors": [
                {"name": a.name, "orcid": a.orcid}
                for a in config.authors
                if a.is_active
            ],
        }

        keyword_papers = []
        author_papers = []
        crossref_papers = []
        keyword_freq = {}

        # Execute searches based on mode
        if search_mode in ["keywords", "both"] and config_dict["topics"] and config_dict["journals"]:
            try:
                keyword_papers, author_papers, keyword_freq = lookup_pubmed(
                    config_file_dict=config_dict,
                    start_end_date=(start_date, end_date),
                    mode="keywords" if search_mode == "keywords" else "both",
                )
            except Exception as e:
                print(f"PubMed search error: {e}")

        if search_mode in ["authors", "both"] and config_dict["orcids"]:
            try:
                crossref_papers = lookup_crossref(
                    orcids=config_dict["orcids"],
                    start_end_date=(start_date, end_date),
                    email=user.email,
                )
            except Exception as e:
                print(f"CrossRef search error: {e}")

        # Process papers using existing processor
        components_keyword, components_orcid = process_papers(
            keyword_papers, author_papers, crossref_papers
        )

        # Store papers in database
        all_components = components_keyword + components_orcid
        for paper_data in all_components:
            paper = Paper(
                search_run_id=search_run.id,
                title=paper_data.get("Title", "Untitled"),
                journal=paper_data.get("Journal"),
                authors=paper_data.get("Authors", []),
                date=paper_data.get("Date"),
                abstract=paper_data.get("Abstract"),
                keywords=paper_data.get("Keywords", []),
                institutions=paper_data.get("Institution", []),
                link=paper_data.get("Link"),
                source=paper_data.get("Source", "unknown"),
                doi=extract_doi_from_link(paper_data.get("Link")),
            )
            db.add(paper)

        # Update search run
        search_run.status = "completed"
        search_run.completed_at = datetime.utcnow()
        search_run.total_papers_found = len(all_components)
        search_run.keyword_papers_count = len(components_keyword)
        search_run.author_papers_count = len(components_orcid)

    except Exception as e:
        search_run.status = "failed"
        search_run.error_message = str(e)
        search_run.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(search_run)

    return search_run
