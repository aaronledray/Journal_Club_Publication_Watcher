"""
Browser utilities for the Journal Lookup Tool.
Handles opening publication links and managing browser interactions.
"""

import subprocess
import sys
import webbrowser
from typing import List, Dict, Any
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def format_doi_url(doi_or_url: str) -> str:
    """
    Format DOI or URL into a proper DOI URL.
    
    Args:
        doi_or_url: DOI identifier or URL
        
    Returns:
        Properly formatted DOI URL
    """
    if not doi_or_url or doi_or_url in ['No link available', '']:
        return None
    
    # If it's already a full URL, return as-is
    if doi_or_url.startswith(('http://', 'https://')):
        return doi_or_url
    
    # If it looks like a DOI, format it
    if '/' in doi_or_url and not doi_or_url.startswith('doi:'):
        return f"https://doi.org/{doi_or_url}"
    
    # Handle doi: prefix
    if doi_or_url.startswith('doi:'):
        return f"https://doi.org/{doi_or_url[4:]}"
    
    return doi_or_url


def extract_paper_url(component: Dict[str, Any]) -> str:
    """
    Extract URL from paper component.
    
    Args:
        component: Paper component dictionary
        
    Returns:
        Formatted URL or None if no valid URL found
    """
    link = component.get("Link")
    
    # Handle different link formats
    if isinstance(link, list) and link:
        # Take the last (most specific) link
        link = link[-1]
    
    if isinstance(link, str):
        return format_doi_url(link)
    elif hasattr(link, 'value'):
        # Handle special link objects
        return format_doi_url(link.value)
    elif hasattr(link, 'attributes') and link.attributes.get('EIdType') == 'doi':
        return f"https://doi.org/{link.value}"
    
    return None


def open_url_safari(url: str) -> bool:
    """
    Open URL in Safari using AppleScript (macOS only).
    
    Args:
        url: URL to open
        
    Returns:
        True if successful, False otherwise
    """
    if sys.platform != 'darwin':
        return False
    
    try:
        script = f'tell application "Safari" to open location "{url}"'
        subprocess.run(['osascript', '-e', script], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def open_url_chrome(url: str) -> bool:
    """
    Open URL in Chrome.
    
    Args:
        url: URL to open
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', '-a', 'Google Chrome', url], check=True)
        elif sys.platform == 'win32':
            subprocess.run(['start', 'chrome', url], shell=True, check=True)
        else:
            subprocess.run(['google-chrome', url], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def open_url_firefox(url: str) -> bool:
    """
    Open URL in Firefox.
    
    Args:
        url: URL to open
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', '-a', 'Firefox', url], check=True)
        elif sys.platform == 'win32':
            subprocess.run(['start', 'firefox', url], shell=True, check=True)
        else:
            subprocess.run(['firefox', url], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def open_url_default_browser(url: str) -> bool:
    """
    Open URL in the default system browser.
    
    Args:
        url: URL to open
        
    Returns:
        True if successful, False otherwise
    """
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def open_single_url(url: str, browser_preference: str = 'default') -> bool:
    """
    Open a single URL in the specified browser.
    
    Args:
        url: URL to open
        browser_preference: Preferred browser ('safari', 'chrome', 'firefox', 'default')
        
    Returns:
        True if successful, False otherwise
    """
    if not url or not is_valid_url(url):
        print(f"   ❌ Invalid URL: {url}")
        return False
    
    success = False
    
    # Try preferred browser first
    if browser_preference == 'safari':
        success = open_url_safari(url)
    elif browser_preference == 'chrome':
        success = open_url_chrome(url)
    elif browser_preference == 'firefox':
        success = open_url_firefox(url)
    
    # Fall back to default browser if preferred browser fails
    if not success:
        success = open_url_default_browser(url)
    
    if success:
        print(f"     Opened: {url}")
    else:
        print(f"   ❌ Failed to open: {url}")
    
    return success


def open_links_in_safari(
    components: List[Dict[str, Any]], 
    auto_mode: bool = False,
    browser_preference: str = 'safari',
    max_links: int = 20
) -> None:
    """
    Open publication links in browser.
    
    Args:
        components: List of paper component dictionaries
        auto_mode: If True, skip user interaction
        browser_preference: Preferred browser
        max_links: Maximum number of links to open
    """
    if auto_mode:
        print("  Auto mode: Skipping browser link opening")
        return
    
    if not components:
        print("  No papers found - no links to open")
        return
    
    # Extract valid URLs
    valid_urls = []
    for component in components:
        url = extract_paper_url(component)
        if url and is_valid_url(url):
            valid_urls.append({
                'url': url,
                'title': component.get('Title', 'Unknown title')[:50]
            })
    
    if not valid_urls:
        print("  No valid publication links found")
        return
    
    # Limit number of links
    if len(valid_urls) > max_links:
        print(f"⚠️  Found {len(valid_urls)} links, limiting to {max_links} to avoid overwhelming your browser")
        valid_urls = valid_urls[:max_links]
    
    # Ask user permission
    print(f"\n  Found {len(valid_urls)} publication links")
    print(f"   Browser preference: {browser_preference.title()}")
    
    if len(valid_urls) > 5:
        print(f"   Warning: This will open {len(valid_urls)} browser tabs")
    
    user_input = input("Open links in browser? (y/n) [n]: ").strip().lower()
    
    if user_input not in ['y', 'yes']:
        print("  Links not opened - you can find them in the generated report files")
        return
    
    # Open links
    print(f"\n  Opening {len(valid_urls)} links in {browser_preference}...")
    
    successful = 0
    failed = 0
    
    for i, link_info in enumerate(valid_urls):
        url = link_info['url']
        title = link_info['title']
        
        print(f"   [{i+1:2d}/{len(valid_urls)}] {title}...")
        
        if open_single_url(url, browser_preference):
            successful += 1
        else:
            failed += 1
        
        # Add small delay between opens to avoid overwhelming the browser
        import time
        time.sleep(0.5)
    
    # Summary
    print(f"\n  Browser opening complete:")
    print(f"   Successfully opened: {successful}")
    if failed > 0:
        print(f"   Failed to open: {failed}")


def open_links_interactive(
    components: List[Dict[str, Any]],
    browser_preference: str = 'default'
) -> None:
    """
    Interactive link opening with user selection.
    
    Args:
        components: List of paper component dictionaries
        browser_preference: Preferred browser
    """
    if not components:
        print("No papers found.")
        return
    
    # Extract and display papers with links
    papers_with_links = []
    for i, component in enumerate(components):
        url = extract_paper_url(component)
        if url and is_valid_url(url):
            papers_with_links.append({
                'index': i,
                'title': component.get('Title', 'Unknown title'),
                'journal': component.get('Journal', 'Unknown journal'),
                'url': url
            })
    
    if not papers_with_links:
        print("No papers with valid links found.")
        return
    
    print(f"\nFound {len(papers_with_links)} papers with links:")
    print("-" * 80)
    
    for i, paper in enumerate(papers_with_links, 1):
        title = paper['title'][:60] + "..." if len(paper['title']) > 60 else paper['title']
        print(f"[{i:2d}] {title}")
        print(f"     Journal: {paper['journal']}")
        print(f"     URL: {paper['url']}")
        print()
    
    while True:
        try:
            selection = input(
                f"Enter paper numbers to open (1-{len(papers_with_links)}, "
                "comma-separated, 'all' for all, or 'q' to quit): "
            ).strip().lower()
            
            if selection == 'q':
                break
            elif selection == 'all':
                selected_papers = papers_with_links
            else:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                selected_papers = [papers_with_links[i] for i in indices if 0 <= i < len(papers_with_links)]
            
            if selected_papers:
                print(f"\nOpening {len(selected_papers)} paper(s)...")
                for paper in selected_papers:
                    print(f"Opening: {paper['title'][:50]}...")
                    open_single_url(paper['url'], browser_preference)
                break
            else:
                print("No valid selections made.")
                
        except (ValueError, IndexError):
            print("Invalid input. Please enter valid paper numbers.")


def get_browser_preference() -> str:
    """
    Get user's browser preference interactively.
    
    Returns:
        Browser preference string
    """
    browsers = {
        '1': 'safari',
        '2': 'chrome', 
        '3': 'firefox',
        '4': 'default'
    }
    
    print("\nChoose your preferred browser:")
    print("1. Safari (macOS)")
    print("2. Chrome")
    print("3. Firefox") 
    print("4. System default")
    
    while True:
        choice = input("Enter choice (1-4) [4]: ").strip()
        if not choice:
            choice = '4'
        
        if choice in browsers:
            return browsers[choice]
        else:
            print("Invalid choice. Please enter 1-4.")


def validate_browser_availability(browser: str) -> bool:
    """
    Check if specified browser is available on the system.
    
    Args:
        browser: Browser name
        
    Returns:
        True if browser is available, False otherwise
    """
    test_url = "https://www.example.com"
    
    if browser == 'safari':
        return sys.platform == 'darwin'
    elif browser == 'chrome':
        return open_url_chrome(test_url) or True  # We can't really test without opening
    elif browser == 'firefox':
        return open_url_firefox(test_url) or True
    else:
        return True  # Default browser should always be available


def create_link_summary(components: List[Dict[str, Any]]) -> str:
    """
    Create a summary of all paper links.
    
    Args:
        components: List of paper component dictionaries
        
    Returns:
        Text summary of links
    """
    summary_lines = ["PUBLICATION LINKS SUMMARY", "=" * 50, ""]
    
    for i, component in enumerate(components, 1):
        title = component.get('Title', 'Unknown title')
        url = extract_paper_url(component)
        
        summary_lines.append(f"[{i:3d}] {title}")
        if url:
            summary_lines.append(f"      {url}")
        else:
            summary_lines.append("      No link available")
        summary_lines.append("")
    
    return "\n".join(summary_lines)


def save_links_to_file(
    components: List[Dict[str, Any]], 
    filename: str = "publication_links.txt"
) -> None:
    """
    Save all publication links to a text file.
    
    Args:
        components: List of paper component dictionaries
        filename: Output filename
    """
    summary = create_link_summary(components)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"  Links saved to: {filename}")


if __name__ == "__main__":
    # Test the browser utilities
    print("Testing browser utilities...")
    
    # Test URL validation
    test_urls = [
        "https://doi.org/10.1038/nature12373",
        "10.1038/nature12373",
        "doi:10.1038/nature12373",
        "invalid-url",
        ""
    ]
    
    for url in test_urls:
        formatted = format_doi_url(url)
        valid = is_valid_url(formatted) if formatted else False
        print(f"URL: '{url}' -> '{formatted}' (valid: {valid})")
    
    # Test browser availability
    browsers = ['safari', 'chrome', 'firefox', 'default']
    for browser in browsers:
        available = validate_browser_availability(browser)
        print(f"Browser '{browser}' available: {available}")
    
    print("Browser utilities test completed.")