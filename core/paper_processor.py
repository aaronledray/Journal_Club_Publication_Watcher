"""
Paper processing utilities for the Journal Lookup Tool.
Handles extraction and standardization of paper metadata from different sources.
"""

from typing import List, Dict, Any, Tuple
from core.date_utils import parse_api_date





def extract_pubmed_authors(article_data: Dict[str, Any]) -> List[str]:
    """Extract authors from PubMed article data."""
    try:
        author_list = article_data.get("AuthorList", [])
        authors = []
        
        for author in author_list:
            if isinstance(author, dict):
                fore_name = author.get('ForeName', '')
                last_name = author.get('LastName', '')
                if fore_name and last_name:
                    authors.append(f"{fore_name} {last_name}")
                elif last_name:
                    authors.append(last_name)
        
        return authors if authors else ["No authors available"]
        
    except (KeyError, TypeError):
        return ["No authors available"]





def extract_pubmed_keywords(citation: Dict[str, Any]) -> List[str]:
    """Extract keywords from PubMed citation data."""
    try:
        keyword_list = citation.get("KeywordList")
        if keyword_list and isinstance(keyword_list, list):
            keywords = []
            for kw_group in keyword_list:
                if isinstance(kw_group, list):
                    keywords.extend([str(kw) for kw in kw_group])
                else:
                    keywords.append(str(kw_group))
            return keywords if keywords else ["No keywords available"]
        else:
            return ["No keywords available"]
    except (KeyError, TypeError):
        return ["No keywords available - KeyError!"]




def extract_pubmed_institutions(article_data: Dict[str, Any]) -> List[str]:
    """Extract institutions from PubMed article data."""
    try:
        author_list = article_data.get("AuthorList", [])
        institutions = []
        
        for author in author_list:
            if isinstance(author, dict) and "AffiliationInfo" in author:
                for aff in author["AffiliationInfo"]:
                    if isinstance(aff, dict) and "Affiliation" in aff:
                        institutions.append(str(aff["Affiliation"]))
        
        return institutions if institutions else ["No institution listed"]
        
    except (KeyError, TypeError):
        return ["No institution listed"]




def extract_crossref_title(paper: Dict[str, Any]) -> str:
    """Extract title from CrossRef paper data."""
    title = paper.get("title", ["No title available"])
    if isinstance(title, list) and title:
        return title[0]
    elif isinstance(title, str):
        return title
    else:
        return "No title available"





def extract_crossref_journal(paper: Dict[str, Any]) -> str:
    """Extract journal name from CrossRef paper data."""
    journal = paper.get("container-title", ["No journal available"])
    if isinstance(journal, list) and journal:
        return journal[0]
    elif isinstance(journal, str):
        return journal
    else:
        return "No journal available"





def extract_crossref_authors(paper: Dict[str, Any]) -> List[str]:
    """Extract authors from CrossRef paper data."""
    try:
        authors = []
        author_list = paper.get("author", [])
        
        for author in author_list:
            if isinstance(author, dict):
                given = author.get('given', '')
                family = author.get('family', '')
                full_name = f"{given} {family}".strip()
                if full_name:
                    authors.append(full_name)
        
        return authors if authors else ["No authors available"]
        
    except (KeyError, TypeError):
        return ["No authors available"]




def remove_duplicate_papers(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate papers based on title.
    
    Args:
        components: List of paper component dictionaries
        
    Returns:
        Deduplicated list of paper components
    """
    seen_titles = set()
    unique_components = []
    
    for component in components:
        title = component.get("Title", "").strip().lower()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_components.append(component)
    
    return unique_components





def process_pubmed_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process PubMed papers into standardized format.
    
    Args:
        papers: List of PubMed paper dictionaries
        
    Returns:
        List of standardized paper components
    """
    components = []
    
    for paper in papers:
        # Handle PubMed format with nested structure
        if "PubmedArticle" in paper:
            for article in paper["PubmedArticle"]:
                if "MedlineCitation" in article and "Article" in article["MedlineCitation"]:
                    component = extract_pubmed_paper_info(article)
                    components.append(component)
        else:
            # Handle direct article format
            if "MedlineCitation" in paper and "Article" in paper["MedlineCitation"]:
                component = extract_pubmed_paper_info(paper)
                components.append(component)
    
    return components





def process_crossref_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process CrossRef papers into standardized format.
    
    Args:
        papers: List of CrossRef paper dictionaries
        
    Returns:
        List of standardized paper components
    """
    components = []
    
    for paper in papers:
        component = extract_crossref_paper_info(paper)
        components.append(component)
    
    return components





def process_papers(
    keyword_papers: List[Dict[str, Any]], 
    pubmed_author_papers: List[Dict[str, Any]], 
    crossref_papers: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process all papers and separate into keyword-based and ORCID-based results.
    
    Args:
        keyword_papers: Papers from keyword searches
        pubmed_author_papers: Papers from PubMed author searches
        crossref_papers: Papers from CrossRef ORCID searches
        
    Returns:
        Tuple of (keyword_components, orcid_components)
    """
    # Process keyword-based papers
    components_keyword = process_pubmed_papers(keyword_papers)
    for component in components_keyword:
        component["Source"] = "keyword"
    
    # Process PubMed author-based papers
    components_pubmed_author = process_pubmed_papers(pubmed_author_papers)
    for component in components_pubmed_author:
        component["Source"] = "pubmed_author"
    
    # Process CrossRef papers
    components_crossref = process_crossref_papers(crossref_papers)
    for component in components_crossref:
        component["Source"] = "crossref"
    
    # Combine ORCID-based results
    components_orcid = components_pubmed_author + components_crossref
    
    # Remove duplicates within each category
    components_keyword = remove_duplicate_papers(components_keyword)
    components_orcid = remove_duplicate_papers(components_orcid)
    
    return components_keyword, components_orcid


def combine_components(
    components_keyword: List[Dict[str, Any]], 
    components_orcid: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Combine all components and remove duplicates across categories.
    
    Args:
        components_keyword: Keyword-based components
        components_orcid: ORCID-based components
        
    Returns:
        Combined and deduplicated list of components
    """
    all_components = components_keyword + components_orcid
    return remove_duplicate_papers(all_components)





def filter_papers_by_criteria(
    components: List[Dict[str, Any]], 
    criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Filter papers based on various criteria.
    
    Args:
        components: List of paper components
        criteria: Filter criteria dictionary
        
    Returns:
        Filtered list of components
    """
    filtered = components
    
    # Filter by journals
    if criteria.get('journals'):
        target_journals = [j.lower() for j in criteria['journals']]
        filtered = [
            comp for comp in filtered 
            if any(journal.lower() in comp.get('Journal', '').lower() 
                  for journal in target_journals)
        ]
    
    # Filter by keywords in title or abstract
    if criteria.get('keywords'):
        target_keywords = [k.lower() for k in criteria['keywords']]
        filtered = [
            comp for comp in filtered
            if any(
                keyword in comp.get('Title', '').lower() or 
                keyword in comp.get('Abstract', '').lower()
                for keyword in target_keywords
            )
        ]
    

    return filtered







def enrich_paper_metadata(component: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich paper metadata with additional computed fields.
    
    Args:
        component: Paper component dictionary
        
    Returns:
        Enriched component dictionary
    """
    enriched = component.copy()
    
    # Add computed fields
    enriched['has_abstract'] = bool(
        component.get('Abstract') and 
        component['Abstract'] != 'No abstract available'
    )
    
    enriched['author_count'] = len(component.get('Authors', []))
    
    enriched['has_doi'] = 'doi.org' in component.get('Link', '')
    
    # Extract year from date
    date_str = component.get('Date', '')
    if '/' in date_str:
        try:
            year = date_str.split('/')[0]
            enriched['year'] = int(year) if year.isdigit() else None
        except (ValueError, IndexError):
            enriched['year'] = None
    else:
        enriched['year'] = None
    
    return enriched





def get_paper_source_stats(components: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get statistics about paper sources.
    
    Args:
        components: List of paper components
        
    Returns:
        Dictionary with source statistics
    """
    stats = {}
    for component in components:
        source = component.get('Source', 'unknown')
        stats[source] = stats.get(source, 0) + 1
    return stats






def filter_papers_by_date_range(
    components: List[Dict[str, Any]], 
    start_date: str, 
    end_date: str
) -> List[Dict[str, Any]]:
    """
    Filter papers by date range.
    
    Args:
        components: List of paper components
        start_date: Start date in YYYY/MM/DD format
        end_date: End date in YYYY/MM/DD format
        
    Returns:
        Filtered list of components
    """
    from datetime import datetime
    
    try:
        start_dt = datetime.strptime(start_date, "%Y/%m/%d")
        end_dt = datetime.strptime(end_date, "%Y/%m/%d")
    except ValueError:
        print("Invalid date format for filtering")
        return components
    
    filtered = []
    for component in components:
        date_str = component.get('Date', '')
        if '/' in date_str:
            try:
                paper_dt = datetime.strptime(date_str.split('/')[0] + '/01/01', "%Y/%m/%d")
                if start_dt <= paper_dt <= end_dt:
                    filtered.append(component)
            except ValueError:
                # Include papers with unparseable dates
                filtered.append(component)
        else:
            # Include papers without dates
            filtered.append(component)
    
    return filtered





def sort_papers_by_date(
    components: List[Dict[str, Any]], 
    reverse: bool = True
) -> List[Dict[str, Any]]:
    """
    Sort papers by publication date.
    
    Args:
        components: List of paper components
        reverse: If True, sort newest first
        
    Returns:
        Sorted list of components
    """
    from datetime import datetime
    
    def get_sort_date(component):
        date_str = component.get('Date', '')
        if '/' in date_str:
            try:
                # Extract year from date string
                year = int(date_str.split('/')[0])
                return year
            except (ValueError, IndexError):
                pass
        return 0  # Default for unparseable dates
    
    return sorted(components, key=get_sort_date, reverse=reverse)





def get_author_frequencies(components: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get frequency count of authors across papers.
    
    Args:
        components: List of paper components
        
    Returns:
        Dictionary mapping author names to frequency counts
    """
    author_counts = {}
    
    for component in components:
        authors = component.get('Authors', [])
        for author in authors:
            if author and author != 'No authors available':
                author_counts[author] = author_counts.get(author, 0) + 1
    
    return author_counts





def get_journal_frequencies(components: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Get frequency count of journals across papers.
    
    Args:
        components: List of paper components
        
    Returns:
        Dictionary mapping journal names to frequency counts
    """
    journal_counts = {}
    
    for component in components:
        journal = component.get('Journal', '')
        if journal and journal != 'No journal available':
            journal_counts[journal] = journal_counts.get(journal, 0) + 1
    
    return journal_counts





def extract_keywords_from_text(
    components: List[Dict[str, Any]], 
    target_keywords: List[str]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract papers that mention specific keywords in title or abstract.
    
    Args:
        components: List of paper components
        target_keywords: List of keywords to search for
        
    Returns:
        Dictionary mapping keywords to lists of matching papers
    """
    keyword_matches = {kw: [] for kw in target_keywords}
    
    for component in components:
        title = component.get('Title', '').lower()
        abstract = component.get('Abstract', '').lower()
        text_content = f"{title} {abstract}"
        
        for keyword in target_keywords:
            if keyword.lower() in text_content:
                keyword_matches[keyword].append(component)
    
    return keyword_matches






def validate_paper_component(component: Dict[str, Any]) -> List[str]:
    """
    Validate a paper component and return list of issues.
    
    Args:
        component: Paper component dictionary
        
    Returns:
        List of validation error messages
    """
    issues = []
    
    # Check required fields
    required_fields = ['Title', 'Journal', 'Authors', 'Date']
    for field in required_fields:
        if not component.get(field):
            issues.append(f"Missing {field}")
        elif isinstance(component[field], list) and not component[field]:
            issues.append(f"Empty {field} list")
        elif isinstance(component[field], str) and component[field].startswith('No '):
            issues.append(f"No {field.lower()} available")
    
    # Check URL validity
    link = component.get('Link', '')
    if link and link != 'No link available':
        if not any(link.startswith(prefix) for prefix in ['http://', 'https://', 'doi:']):
            issues.append("Invalid link format")
    
    return issues






def clean_paper_data(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and standardize paper data.
    
    Args:
        components: List of paper components
        
    Returns:
        Cleaned list of components
    """
    cleaned = []
    
    for component in components:
        # Create a copy to avoid modifying original
        cleaned_component = component.copy()
        
        # Clean title
        title = cleaned_component.get('Title', '')
        if title:
            # Remove extra whitespace and normalize
            cleaned_component['Title'] = ' '.join(title.split())
        
        # Clean authors list
        authors = cleaned_component.get('Authors', [])
        if isinstance(authors, list):
            cleaned_authors = []
            for author in authors:
                if author and isinstance(author, str) and author.strip():
                    cleaned_authors.append(author.strip())
            cleaned_component['Authors'] = cleaned_authors
        
        # Clean abstract
        abstract = cleaned_component.get('Abstract', '')
        if abstract and isinstance(abstract, str):
            cleaned_component['Abstract'] = ' '.join(abstract.split())
        
        # Ensure consistent date format
        date = cleaned_component.get('Date', '')
        if date and isinstance(date, str):
            # Normalize date separators
            date = date.replace('-', '/').replace('.', '/')
            cleaned_component['Date'] = date
        
        cleaned.append(cleaned_component)
    
    return cleaned




def extract_crossref_paper_info(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract paper information from CrossRef format.
    
    Args:
        paper: CrossRef paper dictionary
        
    Returns:
        Standardized paper component dictionary
    """
    component = {
        "Title": extract_crossref_title(paper),
        "Journal": extract_crossref_journal(paper),
        "Link": paper.get("URL", "No link available"),
        "Authors": extract_crossref_authors(paper),
        "Keywords": ["No keywords (CrossRef)"],  # CrossRef rarely has keywords
        "Institution": ["No institution listed (CrossRef)"],  # CrossRef rarely has institutions
        "Abstract": paper.get("abstract", "No abstract available"),
        "Date": parse_api_date(paper.get("issued"), "crossref"),
        "Source": "crossref"
    }
    
    return component





def extract_pubmed_title(article_data: Dict[str, Any]) -> str:
    """Extract title from PubMed article data."""
    return article_data.get("ArticleTitle", "No title available")






def extract_pubmed_abstract(article_data: Dict[str, Any]) -> str:
    """Extract abstract from PubMed article data."""
    abstract_block = article_data.get("Abstract", {})
    abstract_text = abstract_block.get("AbstractText", ["No abstract available"])
    
    if isinstance(abstract_text, list) and abstract_text:
        return abstract_text[0]
    elif isinstance(abstract_text, str):
        return abstract_text
    else:
        return "No abstract available"




def extract_pubmed_link(article_data: Dict[str, Any]) -> str:
    """Extract DOI/link from PubMed article data."""
    elocation = article_data.get("ELocationID")
    
    if isinstance(elocation, list):
        for loc in elocation:
            # Handle StringElement objects (your custom class)
            if hasattr(loc, 'attributes') and hasattr(loc, 'value'):
                if loc.attributes.get('EIdType') == 'doi':
                    return f"https://doi.org/{loc.value}"
            # Handle StringElement objects without .value attribute
            elif hasattr(loc, 'attributes'):
                if loc.attributes.get('EIdType') == 'doi':
                    return f"https://doi.org/{str(loc)}"
            # Handle regular strings
            elif isinstance(loc, str):
                return f"https://doi.org/{loc}"
        
        # Return first available if no DOI found
        if elocation:
            first_loc = elocation[0]
            if hasattr(first_loc, 'value'):
                return str(first_loc.value)
            else:
                return str(first_loc)
        return "No link available"
        
    elif isinstance(elocation, str):
        return f"https://doi.org/{elocation}"
    elif hasattr(elocation, 'value'):
        return f"https://doi.org/{elocation.value}"
    elif elocation:
        return f"https://doi.org/{str(elocation)}"
    else:
        return "No link available"



        

def extract_pubmed_paper_info(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract paper information from PubMed article format.
    
    Args:
        article: PubMed article dictionary
        
    Returns:
        Standardized paper component dictionary
    """
    citation = article.get("MedlineCitation", {})
    article_data = citation.get("Article", {})
    
    component = {
        "Title": article_data.get("ArticleTitle", "No title available"),
        "Journal": article_data.get("Journal", {}).get("Title", "No journal available"),
        "Link": extract_pubmed_link(article_data),
        "Authors": extract_pubmed_authors(article_data),
        "Keywords": extract_pubmed_keywords(citation),
        "Institution": extract_pubmed_institutions(article_data),
        "Abstract": extract_pubmed_abstract(article_data),
        "Date": parse_api_date(article_data.get("ArticleDate"), "pubmed"),
        "Source": "pubmed"
    }
    
    return component








if __name__ == "__main__":
    # Test the functions with sample data
    print("Testing paper processor...")
    
    # Sample PubMed data
    sample_pubmed = {
        "MedlineCitation": {
            "Article": {
                "ArticleTitle": "Test Article",
                "Journal": {"Title": "Test Journal"},
                "AuthorList": [
                    {"ForeName": "John", "LastName": "Doe"},
                    {"ForeName": "Jane", "LastName": "Smith"}
                ]
            }
        }
    }
    
    component = extract_pubmed_paper_info(sample_pubmed)
    print(f"Extracted component: {component['Title']}")
    print(f"Authors: {component['Authors']}")
    

    issues = validate_paper_component(component)
    print(f"Validation issues: {issues}")
    
    print("Paper processor test completed.")



    