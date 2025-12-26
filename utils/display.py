"""
Display utilities for the Journal Lookup Tool.
Handles console output formatting and user interface elements.
"""

from typing import List, Dict, Any


def print_opener(version: str, update_date: str) -> None:
    """Print the opening banner for the application."""
    banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          Journal Lookup Tool                                 ║
║                            by AP Ledray (aaronledray@gamil.com)              ║
║                                                                              ║
║  Version: {version:<20} Last Updated: {update_date:<20}            ║
╚══════════════════════════════════════════════════════════════════════════════╝

         ░█████                                                      ░██ 
           ░██                                                       ░██ 
           ░██   ░███████  ░██    ░██ ░██░████ ░████████   ░██████   ░██ 
           ░██  ░██    ░██ ░██    ░██ ░███     ░██    ░██       ░██  ░██ 
     ░██   ░██  ░██    ░██ ░██    ░██ ░██      ░██    ░██  ░███████  ░██ 
     ░██   ░██  ░██    ░██ ░██   ░███ ░██      ░██    ░██ ░██   ░██  ░██ 
      ░██████    ░███████   ░█████░██ ░██      ░██    ░██  ░█████░██ ░██ 
                                                                                                                                          
                                                                         
         ░██       ░██               ░██               ░██        ░██        
         ░██       ░██               ░██               ░██        ░██        
         ░██  ░██  ░██  ░██████   ░████████  ░███████  ░████████  ░██        
         ░██ ░████ ░██       ░██     ░██    ░██    ░██ ░██    ░██ ░██        
         ░██░██ ░██░██  ░███████     ░██    ░██        ░██    ░██ ░██        
         ░████   ░████ ░██   ░██     ░██    ░██    ░██ ░██    ░██            
         ░███     ░███  ░█████░██     ░████  ░███████  ░██    ░██ ░██        
                                                                                                                                              
"""
    print(banner)


def print_results_summary(
    components_keyword: List[Dict[str, Any]], 
    components_orcid: List[Dict[str, Any]]
) -> None:
    """
    Print a summary of search results.
    
    Args:
        components_keyword: Keyword-based search results
        components_orcid: ORCID-based search results
    """
    total_results = len(components_keyword) + len(components_orcid)
    
    print("\n" + "="*80)
    print("SEARCH RESULTS SUMMARY")
    print("="*80)
    print(f"Keyword-based results: {len(components_keyword):>10}")
    print(f"Author/ORCID results:  {len(components_orcid):>10}")
    print(f"Total unique papers:   {total_results:>10}")
    print("="*80)
    
    if total_results == 0:
        print_no_results()
    else:
        print_paper_breakdown(components_keyword, components_orcid)


def print_no_results() -> None:
    """Print message when no papers are found."""
    art = """
    /^ ^\\
   / 0 0 \\    Oh, heck! No papers found.
   V\\ Y /V    
    / - \\     Try adjusting your search criteria:
   /    |     • Broaden date range
  V__) ||     • Check keyword spelling
             • Verify ORCID IDs
             • Expand journal list
    """
    print(art)


def print_success() -> None:
    """Print success message."""
    art = """
         .-'
    '--./ /     _.---.
    '-,  (__..-`       \\
       \\          .     |    Success! 🎉
        `,.__.   ,__.--/     
          '._/_.'___.-`       Files generated successfully!
    """
    print(art)


def print_paper_breakdown(
    components_keyword: List[Dict[str, Any]], 
    components_orcid: List[Dict[str, Any]]
) -> None:
    """
    Print detailed breakdown of papers by source.
    
    Args:
        components_keyword: Keyword-based search results
        components_orcid: ORCID-based search results
    """
    print("\nPaper Sources Breakdown:")
    
    # Count by source
    keyword_sources = count_by_source(components_keyword)
    orcid_sources = count_by_source(components_orcid)
    
    print("\n   Keyword-based searches:")
    for source, count in keyword_sources.items():
        print(f"     • {source.title()}: {count}")
    
    print("\n   Author/ORCID searches:")
    for source, count in orcid_sources.items():
        print(f"     • {source.title()}: {count}")
    
    # Show top journals
    all_components = components_keyword + components_orcid
    top_journals = get_top_journals(all_components, limit=5)
    
    if top_journals:
        print(f"\n Top {len(top_journals)} Journals:")
        for journal, count in top_journals:
            print(f"     • {journal}: {count} papers")


def count_by_source(components: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count papers by their source."""
    source_counts = {}
    for component in components:
        source = component.get('Source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    return source_counts


def get_top_journals(components: List[Dict[str, Any]], limit: int = 5) -> List[tuple]:
    """Get top journals by paper count."""
    journal_counts = {}
    
    for component in components:
        journal = component.get('Journal', 'Unknown Journal')
        if journal != 'No journal available':
            journal_counts[journal] = journal_counts.get(journal, 0) + 1
    
    # Sort by count and return top N
    sorted_journals = sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_journals[:limit]


def print_progress(current: int, total: int, operation: str = "Processing") -> None:
    """
    Print progress indicator.
    
    Args:
        current: Current item number
        total: Total number of items
        operation: Description of the operation
    """
    if total == 0:
        return
    
    percentage = (current / total) * 100
    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\r{operation}: [{bar}] {percentage:.1f}% ({current}/{total})", end='')
    
    if current == total:
        print()  # New line when complete


def print_config_summary(config: Dict[str, Any]) -> None:
    """Print configuration summary."""
    print("\n⚙️  Configuration Summary:")
    print(f"   Email: {config.get('email', 'Not set')}")
    print(f"   Lookup frequency: {config.get('lookup_frequency', 'Not set')}")
    
    journals = config.get('journals', [])
    topics = config.get('topics', [])
    orcids = config.get('orcids', [])
    
    print(f"   Journals: {len(journals)} configured")
    if journals and len(journals) <= 5:
        for journal in journals:
            print(f"      • {journal}")
    elif journals:
        print(f"      • {journals[0]} (and {len(journals)-1} more)")
    
    print(f"   Keywords: {len(topics)} configured")
    if topics and len(topics) <= 5:
        for topic in topics:
            print(f"      • {topic}")
    elif topics:
        print(f"      • {topics[0]} (and {len(topics)-1} more)")
    
    print(f"   ORCIDs: {len(orcids)} configured")


def print_file_outputs(output_dir: str, auto_mode: bool = False) -> None:
    """Print information about generated output files."""
    from pathlib import Path
    
    output_path = Path(output_dir)
    files = [
        ("Text report", "publications.txt"),
        ("PowerPoint", "publications.pptx"),
        ("HTML dashboard", "publications.html"),
        ("JSON data", "results.json")
    ]
    
    print(f"\n📁 Output files in '{output_path.resolve()}':")
    for description, filename in files:
        filepath = output_path / filename
        status = "Success" if filepath.exists() else "Failure"
        print(f"   {status} {description}: {filename}")
    
    if not auto_mode:
        print("\n Tip: The HTML dashboard will open automatically in your browser!")


def format_paper_preview(component: Dict[str, Any], max_length: int = 100) -> str:
    """
    Format a paper component for preview display.
    
    Args:
        component: Paper component dictionary
        max_length: Maximum length for abstract preview
        
    Returns:
        Formatted string for display
    """
    title = component.get('Title', 'No title')
    authors = component.get('Authors', [])
    journal = component.get('Journal', 'Unknown journal')
    abstract = component.get('Abstract', 'No abstract')
    
    # Truncate abstract if too long
    if len(abstract) > max_length:
        abstract = abstract[:max_length-3] + "..."
    
    # Format authors
    if len(authors) > 3:
        author_str = f"{authors[0]} et al. ({len(authors)} authors)"
    else:
        author_str = ", ".join(authors[:3])
    
    return f"""
{title}
   {author_str}
   {journal}
   {abstract}
"""


def print_error(message: str, suggestion: str = None) -> None:
    """
    Print formatted error message.
    
    Args:
        message: Error message
        suggestion: Optional suggestion for fixing the error
    """
    print(f"\n Error: {message}")
    if suggestion:
        print(f"💡 Suggestion: {suggestion}")


def print_warning(message: str) -> None:
    """Print formatted warning message."""
    print(f"\n Warning: {message}")


def print_info(message: str) -> None:
    """Print formatted info message."""
    print(f"  {message}")


if __name__ == "__main__":
    # Test the display functions
    print_opener("3.5.0", "20250815")
    
    # Test results summary
    sample_keyword = [{"Source": "keyword", "Title": "Test 1", "Journal": "Nature"}]
    sample_orcid = [{"Source": "crossref", "Title": "Test 2", "Journal": "Science"}]
    
    print_results_summary(sample_keyword, sample_orcid)
    print_success()