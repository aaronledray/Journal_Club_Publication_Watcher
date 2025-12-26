"""
CrossRef API client for the Journal Lookup Tool.
Handles fetching publications from CrossRef using ORCID IDs and other criteria.
"""

import requests
import time
from typing import List, Dict, Any, Tuple, Optional
from core.date_utils import format_date_for_api
from utils.display import print_progress


# CrossRef API configuration
CROSSREF_BASE_URL = "https://api.crossref.org/works"
DEFAULT_USER_AGENT = "JournalClubLookupTool/3.5.0 (mailto:your.email@institution.edu)"
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0  # seconds between requests


class CrossRefClient:
    """Client for interacting with the CrossRef API."""
    
    def __init__(self, email: str = None, user_agent: str = None):
        """
        Initialize CrossRef client.
        
        Args:
            email: Contact email for API requests
            user_agent: Custom user agent string
        """
        self.email = email
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent
        })
        
        # Update user agent with email if provided
        if email:
            self.session.headers["User-Agent"] = f"{self.user_agent} (mailto:{email})"
    
    def search_by_orcid(
        self, 
        orcid: str, 
        start_date: str, 
        end_date: str, 
        rows: int = 100,
        sort: str = "published",
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Search for publications by ORCID ID within a date range.
        
        Args:
            orcid: ORCID identifier (with or without URL prefix)
            start_date: Start date in YYYY/MM/DD format
            end_date: End date in YYYY/MM/DD format
            rows: Maximum number of results to return
            sort: Sort field (published, relevance, etc.)
            order: Sort order (asc, desc)
            
        Returns:
            List of publication dictionaries
        """
        # Clean ORCID (remove URL prefix if present)
        clean_orcid = orcid.replace("https://orcid.org/", "").replace("http://orcid.org/", "")
        
        # Convert dates to CrossRef format
        crossref_start = format_date_for_api(start_date, 'crossref')
        crossref_end = format_date_for_api(end_date, 'crossref')
        
        # Build filter string
        filters = [
            f"orcid:{clean_orcid}",
            f"from-pub-date:{crossref_start}",
            f"until-pub-date:{crossref_end}"
        ]
        
        params = {
            "filter": ",".join(filters),
            "rows": min(rows, 1000),  # CrossRef limit
            "sort": sort,
            "order": order
        }
        
        try:
            print(f"   Searching CrossRef for ORCID: {clean_orcid}")
            response = self.session.get(
                CROSSREF_BASE_URL, 
                params=params, 
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get("message", {}).get("items", [])
            
            # Add source metadata
            for item in items:
                item["Source"] = "crossref"
                item["query_orcid"] = clean_orcid
            
            print(f"   Found {len(items)} papers for ORCID {clean_orcid}")
            return items
            
        except requests.RequestException as e:
            print(f"   ❌ Error fetching CrossRef data for ORCID {clean_orcid}: {e}")
            return []
    
    def search_by_query(
        self,
        query: str,
        start_date: str = None,
        end_date: str = None,
        rows: int = 100,
        filters: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for publications by text query.
        
        Args:
            query: Search query string
            start_date: Optional start date in YYYY/MM/DD format
            end_date: Optional end date in YYYY/MM/DD format
            rows: Maximum number of results
            filters: Additional filters dictionary
            
        Returns:
            List of publication dictionaries
        """
        params = {
            "query": query,
            "rows": min(rows, 1000)
        }
        
        # Add date filters if provided
        filter_list = []
        if start_date:
            crossref_start = format_date_for_api(start_date, 'crossref')
            filter_list.append(f"from-pub-date:{crossref_start}")
        
        if end_date:
            crossref_end = format_date_for_api(end_date, 'crossref')
            filter_list.append(f"until-pub-date:{crossref_end}")
        
        # Add custom filters
        if filters:
            for key, value in filters.items():
                filter_list.append(f"{key}:{value}")
        
        if filter_list:
            params["filter"] = ",".join(filter_list)
        
        try:
            print(f"   Searching CrossRef with query: {query}")
            response = self.session.get(
                CROSSREF_BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get("message", {}).get("items", [])
            
            # Add source metadata
            for item in items:
                item["Source"] = "crossref"
                item["search_query"] = query
            
            print(f"   Found {len(items)} papers for query: {query}")
            return items
            
        except requests.RequestException as e:
            print(f"   ❌ Error fetching CrossRef data for query '{query}': {e}")
            return []
    
    def get_work_details(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific DOI.
        
        Args:
            doi: DOI identifier
            
        Returns:
            Publication details dictionary or None
        """
        # Clean DOI
        clean_doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        url = f"{CROSSREF_BASE_URL}/{clean_doi}"
        
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            work = data.get("message", {})
            work["Source"] = "crossref"
            
            return work
            
        except requests.RequestException as e:
            print(f"   ❌ Error fetching details for DOI {clean_doi}: {e}")
            return None


def lookup_crossref(
    orcids: List[str], 
    start_end_date: Tuple[str, str], 
    rows: int = 100,
    email: str = None
) -> List[Dict[str, Any]]:
    """
    Fetch publications associated with ORCID IDs using CrossRef API.
    
    Args:
        orcids: List of ORCID identifiers
        start_end_date: Tuple of (start_date, end_date) in YYYY/MM/DD format
        rows: Maximum results per ORCID
        email: Contact email for API requests
        
    Returns:
        List of publication dictionaries from CrossRef
    """
    if not orcids:
        print("   No ORCIDs provided for CrossRef search")
        return []
    
    start_date, end_date = start_end_date
    client = CrossRefClient(email=email)
    all_publications = []
    
    print(f"  Searching CrossRef for {len(orcids)} ORCID(s)...")
    
    for i, orcid in enumerate(orcids):
        # Rate limiting
        if i > 0:
            time.sleep(RATE_LIMIT_DELAY)
        
        # Show progress
        print_progress(i + 1, len(orcids), "CrossRef search")
        
        try:
            publications = client.search_by_orcid(
                orcid=orcid,
                start_date=start_date,
                end_date=end_date,
                rows=rows
            )
            all_publications.extend(publications)
            
        except Exception as e:
            print(f"   ❌ Unexpected error for ORCID {orcid}: {e}")
            continue
    
    # Remove duplicates based on DOI
    unique_publications = remove_duplicate_dois(all_publications)
    
    print(f"  CrossRef search completed: {len(unique_publications)} unique papers found")
    return unique_publications


def search_crossref_by_keywords(
    keywords: List[str],
    start_end_date: Tuple[str, str],
    journals: List[str] = None,
    rows: int = 100,
    email: str = None
) -> List[Dict[str, Any]]:
    """
    Search CrossRef by keywords and optional journal filters.
    
    Args:
        keywords: List of search keywords
        start_end_date: Date range tuple
        journals: Optional list of journal names to filter
        rows: Maximum results per keyword
        email: Contact email for API requests
        
    Returns:
        List of publication dictionaries
    """
    if not keywords:
        print("   No keywords provided for CrossRef search")
        return []
    
    start_date, end_date = start_end_date
    client = CrossRefClient(email=email)
    all_publications = []
    
    print(f"  Searching CrossRef by keywords...")
    
    for i, keyword in enumerate(keywords):
        # Rate limiting
        if i > 0:
            time.sleep(RATE_LIMIT_DELAY)
        
        print_progress(i + 1, len(keywords), "Keyword search")
        
        # Build filters
        filters = {}
        if journals:
            # CrossRef uses container-title for journal names
            # This is a simplified approach - more sophisticated matching may be needed
            journal_query = " OR ".join(f'"{journal}"' for journal in journals)
            filters["container-title"] = journal_query
        
        try:
            publications = client.search_by_query(
                query=keyword,
                start_date=start_date,
                end_date=end_date,
                rows=rows,
                filters=filters
            )
            
            # Add keyword metadata
            for pub in publications:
                pub["search_keyword"] = keyword
            
            all_publications.extend(publications)
            
        except Exception as e:
            print(f"   Unexpected error for keyword '{keyword}': {e}")
            continue
    
    # Remove duplicates
    unique_publications = remove_duplicate_dois(all_publications)
    
    print(f"CrossRef keyword search completed: {len(unique_publications)} unique papers found")
    return unique_publications


def remove_duplicate_dois(publications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate publications based on DOI.
    
    Args:
        publications: List of publication dictionaries
        
    Returns:
        List with duplicates removed
    """
    seen_dois = set()
    unique_pubs = []
    
    for pub in publications:
        doi = pub.get("DOI", "").lower()
        if doi and doi not in seen_dois:
            seen_dois.add(doi)
            unique_pubs.append(pub)
        elif not doi:
            # Keep publications without DOIs (they might be unique)
            unique_pubs.append(pub)
    
    return unique_pubs





def validate_orcid(orcid: str) -> bool:
    """
    Validate ORCID format.
    
    Args:
        orcid: ORCID identifier to validate
        
    Returns:
        True if valid format, False otherwise
    """
    import re
    
    # Remove URL prefix if present
    clean_orcid = orcid.replace("https://orcid.org/", "").replace("http://orcid.org/", "")
    
    # ORCID format: 0000-0000-0000-0000
    pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    return bool(re.match(pattern, clean_orcid))




def get_crossref_api_status() -> Dict[str, Any]:
    """
    Check CrossRef API status and rate limits.
    
    Returns:
        Dictionary with API status information
    """
    try:
        response = requests.get(
            f"{CROSSREF_BASE_URL}?rows=1",
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=10
        )
        
        status_info = {
            "status_code": response.status_code,
            "available": response.status_code == 200,
            "rate_limit_limit": response.headers.get("X-Rate-Limit-Limit"),
            "rate_limit_interval": response.headers.get("X-Rate-Limit-Interval"),
            "response_time": response.elapsed.total_seconds()
        }
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("message", {})
            status_info["total_results"] = message.get("total-results", 0)
        
        return status_info
        
    except requests.RequestException as e:
        return {
            "available": False,
            "error": str(e)
        }


def format_crossref_citation(publication: Dict[str, Any]) -> str:
    """
    Format a CrossRef publication as a citation string.
    
    Args:
        publication: CrossRef publication dictionary
        
    Returns:
        Formatted citation string
    """
    # Extract basic information
    title = publication.get("title", ["Unknown title"])[0] if publication.get("title") else "Unknown title"
    
    # Authors
    authors = []
    for author in publication.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        if family:
            if given:
                authors.append(f"{family}, {given}")
            else:
                authors.append(family)
    
    author_str = ", ".join(authors[:3])
    if len(authors) > 3:
        author_str += " et al."
    
    # Journal
    journal = publication.get("container-title", ["Unknown journal"])
    journal_str = journal[0] if journal else "Unknown journal"
    
    # Date
    date_parts = publication.get("issued", {}).get("date-parts", [[None]])
    year = date_parts[0][0] if date_parts[0] and date_parts[0][0] else "Unknown year"
    
    # DOI
    doi = publication.get("DOI", "")
    doi_str = f" DOI: {doi}" if doi else ""
    
    return f"{author_str}. {title}. {journal_str}. {year}.{doi_str}"




if __name__ == "__main__":
    # Test the CrossRef client
    print("Testing CrossRef client...")
    
    # Test API status
    status = get_crossref_api_status()
    print(f"CrossRef API available: {status.get('available', False)}")
    
    # Test ORCID validation
    test_orcids = [
        "0000-0000-0000-0000",
        "https://orcid.org/0000-0000-0000-0000",
        "invalid-orcid"
    ]
    
    for orcid in test_orcids:
        valid = validate_orcid(orcid)
        print(f"ORCID '{orcid}' is valid: {valid}")
    

    