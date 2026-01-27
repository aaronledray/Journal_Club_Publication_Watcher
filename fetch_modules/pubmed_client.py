"""
PubMed API client for the Journal Lookup Tool.
Handles fetching publications from PubMed using keywords and author searches.
"""

import time
from typing import List, Dict, Any, Tuple
from urllib.error import HTTPError
from Bio import Entrez
from utils.display import print_progress


# PubMed API configuration
DEFAULT_RETRY_ATTEMPTS = 2
API_DELAY = 1.0  # seconds between requests
MAX_RESULTS = 1000  # Maximum results per query


class PubMedClient:
    """Client for interacting with the PubMed API using Biopython."""
    
    def __init__(self, email: str, tool: str = "JournalLookupTool"):
        """
        Initialize PubMed client.
        
        Args:
            email: Contact email for API requests (required by NCBI)
            tool: Tool name for API requests
        """
        self.email = email
        self.tool = tool
        Entrez.email = email
        Entrez.tool = tool
    
    def search_pmids(self, query: str, retmax: int = MAX_RESULTS) -> List[str]:
        """
        Search PubMed and return list of PMIDs.
        
        Args:
            query: PubMed search query
            retmax: Maximum number of results to return
            
        Returns:
            List of PMID strings
        """
        try:
            # print(f"   Executing PubMed query: {query}")
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=retmax,
                sort="relevance"
            )
            search_results = Entrez.read(handle)
            handle.close()
            
            pmids = search_results.get("IdList", [])
            # print(f"   Found {len(pmids)} PMIDs")
            return pmids
            
        except Exception as e:
            print(f"   Error in PubMed search: {e}")
            return []
    
    def fetch_paper_details(self, pmid: str, retry_attempts: int = DEFAULT_RETRY_ATTEMPTS) -> Dict[str, Any]:
        """
        Fetch detailed paper information for a given PMID.
        
        Args:
            pmid: PubMed ID
            retry_attempts: Number of retry attempts for failed requests
            
        Returns:
            Paper details dictionary or None if failed
        """
        for attempt in range(retry_attempts):
            try:
                time.sleep(API_DELAY)  # Rate limiting
                
                handle = Entrez.efetch(
                    db="pubmed",
                    id=pmid,
                    rettype="medline",
                    retmode="xml"
                )
                paper_data = Entrez.read(handle)
                handle.close()
                
                return paper_data
                
            except HTTPError as e:
                print(f"   ⚠️  HTTPError for PMID {pmid} (attempt {attempt + 1}): {e}")
                if attempt == retry_attempts - 1:
                    print(f"   Failed to fetch PMID {pmid} after {retry_attempts} attempts")
                    return None
                time.sleep(API_DELAY * (attempt + 1))  # Exponential backoff
                
            except Exception as e:
                print(f"   Unexpected error for PMID {pmid}: {e}")
                return None
        
        return None
    
    def build_keyword_query(
        self, 
        keyword: str, 
        start_date: str, 
        end_date: str, 
        journals: List[str] = None
    ) -> str:
        """
        Build a PubMed search query for keyword-based search.
        
        Args:
            keyword: Search keyword
            start_date: Start date in YYYY/MM/DD format
            end_date: End date in YYYY/MM/DD format
            journals: Optional list of journal names to filter
            
        Returns:
            Formatted PubMed query string
        """
        # Convert dates to PubMed format (YYYY/MM/DD)
        date_filter = f'("{start_date}"[Date - Entry] : "{end_date}"[Date - Entry])'
        
        # Build base query with keyword and date filter
        query_parts = [f'({keyword})', date_filter]
        
        # Add journal filter if provided
        if journals:
            journal_terms = []
            for journal in journals:
                # Search in both journal name and abbreviation fields
                journal_terms.extend([
                    f'"{journal}"[Journal]',
                    f'"{journal}"[TA]'  # Title Abbreviation
                ])
            
            if journal_terms:
                journal_query = "(" + " OR ".join(journal_terms) + ")"
                query_parts.append(journal_query)
        
        return " AND ".join(query_parts)
    
    def build_author_query(self, author_name: str, start_date: str, end_date: str) -> str:
        """
        Build a PubMed search query for author-based search.
        
        Args:
            author_name: Author name to search
            start_date: Start date in YYYY/MM/DD format
            end_date: End date in YYYY/MM/DD format
            
        Returns:
            Formatted PubMed query string
        """
        date_filter = f'("{start_date}"[Date - Entry] : "{end_date}"[Date - Entry])'
        author_filter = f'{author_name}[Author]'
        
        return f'{author_filter} AND {date_filter}'
    
    def search_by_keywords(
        self,
        keywords: List[str],
        start_date: str,
        end_date: str,
        journals: List[str] = None,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Search PubMed by keywords with optional journal filtering.
        
        Args:
            keywords: List of search keywords
            start_date: Start date in YYYY/MM/DD format
            end_date: End date in YYYY/MM/DD format
            journals: Optional list of journal names
            retry_attempts: Number of retry attempts for failed requests
            
        Returns:
            Tuple of (papers_list, keyword_frequency_dict)
        """
        if not keywords:
            print("   No keywords provided for PubMed search")
            return [], {}
        
        # print(f"🔍 Starting PubMed keyword search for {len(keywords)} keywords...")
        
        all_papers = []
        keyword_frequencies = {}
        
        for i, keyword in enumerate(keywords):
            # print(f"   [{i+1}/{len(keywords)}] Searching for: {keyword}")
            
            # Build and execute query
            query = self.build_keyword_query(keyword, start_date, end_date, journals)
            pmids = self.search_pmids(query)
            keyword_frequencies[keyword] = len(pmids)
            
            # Fetch paper details
            keyword_papers = []
            if pmids:
                # print(f"   Fetching details for {len(pmids)} papers...")
                
                for j, pmid in enumerate(pmids):
                    print_progress(j + 1, len(pmids), f"Fetching papers for '{keyword}'")
                    
                    paper_data = self.fetch_paper_details(pmid, retry_attempts)
                    if paper_data:
                        # Add metadata
                        paper_data["Source"] = "keyword"
                        paper_data["search_keyword"] = keyword
                        keyword_papers.append(paper_data)
            
            all_papers.extend(keyword_papers)
            #print(f"   Completed keyword '{keyword}': {len(keyword_papers)} papers retrieved")
        
        #print(f"PubMed keyword search completed: {len(all_papers)} total papers")
        return all_papers, keyword_frequencies
    
    def search_by_authors(
        self,
        named_authors: List[Dict[str, str]],
        start_date: str,
        end_date: str,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    ) -> List[Dict[str, Any]]:
        """
        Search PubMed by author names.
        
        Args:
            named_authors: List of author dictionaries with 'name' and 'orcid' keys
            start_date: Start date in YYYY/MM/DD format
            end_date: End date in YYYY/MM/DD format
            retry_attempts: Number of retry attempts for failed requests
            
        Returns:
            List of paper dictionaries
        """
        if not named_authors:
            print("   No authors provided for PubMed search")
            return []
        
        # print(f"🔍 Starting PubMed author search for {len(named_authors)} authors...")
        
        all_papers = []
        
        for i, author in enumerate(named_authors):
            author_name = author.get("name")
            author_orcid = author.get("orcid", "")
            
            if not author_name:
                print(f"   ⚠️  Skipping author with missing name: {author}")
                continue
            
            # print(f"   [{i+1}/{len(named_authors)}] Searching for: {author_name}")
            
            # Build and execute query
            query = self.build_author_query(author_name, start_date, end_date)
            # print(f"   Query: {query}")
            
            pmids = self.search_pmids(query)
            
            # Fetch paper details
            author_papers = []
            if pmids:
                # print(f"   Fetching details for {len(pmids)} papers...")
                
                for j, pmid in enumerate(pmids):
                    print_progress(j + 1, len(pmids), f"Fetching papers for '{author_name}'")
                    
                    paper_data = self.fetch_paper_details(pmid, retry_attempts)
                    if paper_data:
                        # Add metadata
                        paper_data["Source"] = "pubmed_author"
                        paper_data["search_author"] = author_name
                        paper_data["search_orcid"] = author_orcid
                        author_papers.append(paper_data)
            
            all_papers.extend(author_papers)
            #print(f"   Completed author '{author_name}': {len(author_papers)} papers retrieved")
        
        #print(f"PubMed author search completed: {len(all_papers)} total papers")
        return all_papers


def lookup_pubmed(
    config_file_dict: Dict[str, Any], 
    start_end_date: Tuple[str, str], 
    mode: str = "keywords", 
    attempt_number: int = DEFAULT_RETRY_ATTEMPTS
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Search PubMed using keywords and/or author-based searches.
    
    Args:
        config_file_dict: Configuration dictionary containing search parameters
        start_end_date: Tuple of (start_date, end_date) in YYYY/MM/DD format
        mode: Search mode ("keywords", "authors", or "both")
        attempt_number: Number of retry attempts for failed requests
        
    Returns:
        Tuple of (keyword_papers, author_papers, keyword_frequency_dict)
    """
    email = config_file_dict.get('email')
    if not email:
        raise ValueError("Email is required for PubMed API access")
    
    # Initialize client
    client = PubMedClient(email=email)
    
    # Extract search parameters
    start_date, end_date = start_end_date
    journals = config_file_dict.get('journals', [])
    keywords = config_file_dict.get('topics', [])
    named_authors = config_file_dict.get('named_authors', [])
    
    keyword_papers = []
    author_papers = []
    keyword_frequency_dict = {}
    
    # Keyword-based search
    if mode in ["keywords", "both"] and keywords:
        print("  Starting keyword-based PubMed search...")
        keyword_papers, keyword_frequency_dict = client.search_by_keywords(
            keywords=keywords,
            start_date=start_date,
            end_date=end_date,
            journals=journals,
            retry_attempts=attempt_number
        )
        
        if not keyword_papers:
            print("   No papers found from keyword-based search.")
    
    # Author-based search
    if mode in ["authors", "both"] and named_authors:
        print("  Starting author-based PubMed search...")
        author_papers = client.search_by_authors(
            named_authors=named_authors,
            start_date=start_date,
            end_date=end_date,
            retry_attempts=attempt_number
        )
        
        if not author_papers:
            print("   No papers found from author-based search.")
    
    return keyword_papers, author_papers, keyword_frequency_dict


def validate_pubmed_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration for PubMed searches.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Check required email
    if not config.get('email'):
        errors.append("Email is required for PubMed API access")
    
    # Check that at least one search method is configured
    has_keywords = bool(config.get('topics'))
    has_authors = bool(config.get('named_authors'))
    
    if not (has_keywords or has_authors):
        errors.append("At least one of 'topics' (keywords) or 'named_authors' must be configured")
    
    # Validate author format
    named_authors = config.get('named_authors', [])
    for i, author in enumerate(named_authors):
        if not isinstance(author, dict):
            errors.append(f"Author {i+1} must be a dictionary with 'name' and 'orcid' keys")
        elif not author.get('name'):
            errors.append(f"Author {i+1} is missing required 'name' field")
    
    return errors


def test_pubmed_connection(email: str) -> bool:
    """
    Test connection to PubMed API.
    
    Args:
        email: Contact email for API requests
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = PubMedClient(email=email)
        
        # Try a simple search
        pmids = client.search_pmids("test[Title]", retmax=1)
        
        print(f"✅ PubMed connection successful (found {len(pmids)} result(s))")
        return True
        
    except Exception as e:
        print(f"❌ PubMed connection failed: {e}")
        return False


def get_pubmed_stats() -> Dict[str, Any]:
    """
    Get basic statistics about PubMed database.
    
    Returns:
        Dictionary with PubMed statistics
    """
    try:
        # Use a broad search to get total count estimate
        handle = Entrez.esearch(db="pubmed", term="*", retmax=0)
        results = Entrez.read(handle)
        handle.close()
        
        return {
            "total_records": int(results.get("Count", 0)),
            "available": True
        }
        
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test the PubMed client
    print("Testing PubMed client...")
    
    # Test configuration validation
    test_config = {
        'email': 'test@example.com',
        'topics': ['machine learning'],
        'named_authors': [{'name': 'John Doe', 'orcid': '0000-0000-0000-0000'}]
    }
    
    errors = validate_pubmed_config(test_config)
    if errors:
        print(f"Configuration errors: {errors}")
    else:
        print("Configuration validation passed")

    print("PubMed client test completed.")