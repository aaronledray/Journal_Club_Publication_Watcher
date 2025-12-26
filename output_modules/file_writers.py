"""
File writing utilities for the Journal Lookup Tool.
Handles creation of text files, JSON exports, and other file outputs.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple


def make_json_safe(obj: Any) -> Any:
    """
    Convert objects to JSON-serializable format.
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, dict):
        return {key: make_json_safe(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, tuple):
        return [make_json_safe(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Convert custom objects to dictionaries
        return make_json_safe(obj.__dict__)
    elif hasattr(obj, 'value') and hasattr(obj, 'attributes'):
        # Handle special objects with value and attributes
        return {
            'value': str(obj.value),
            'attributes': make_json_safe(getattr(obj, 'attributes', {}))
        }
    else:
        # Try to convert to string for non-serializable objects
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


def write_txt_file(
    start_end_date: Tuple[str, str],
    config_file_dict: Dict[str, Any],
    components_keyword: List[Dict[str, Any]],
    components_orcid: List[Dict[str, Any]],
    keyword_frequency_dict: Dict[str, int],
    txt_name: str = "publications.txt",
    auto_mode: bool = False
) -> None:
    """
    Write search results to a text file.
    
    Args:
        start_end_date: Date range tuple
        config_file_dict: Configuration dictionary
        components_keyword: Keyword-based search results
        components_orcid: ORCID-based search results
        keyword_frequency_dict: Keyword frequency data
        txt_name: Output filename
        auto_mode: Whether running in automatic mode
    """
    # Check if file exists and get user permission if not in auto mode
    if Path(txt_name).exists() and not auto_mode:
        response = input(f"{txt_name} already exists. Overwrite? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Text file creation cancelled.")
            return
    
    start_date, end_date = start_end_date
    total_papers = len(components_keyword) + len(components_orcid)
    
    with open(txt_name, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("JOURNAL LOOKUP TOOL - SEARCH RESULTS\n")
        f.write("=" * 80 + "\n\n")
        
        # Metadata
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Date Range: {start_date} to {end_date}\n")
        f.write(f"User Email: {config_file_dict.get('email', 'Not specified')}\n")
        f.write(f"Lookup Frequency: {config_file_dict.get('lookup_frequency', 'Not specified')}\n\n")
        
        # Summary
        f.write("SEARCH SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Keyword-based results: {len(components_keyword)}\n")
        f.write(f"ORCID-based results: {len(components_orcid)}\n")
        f.write(f"Total papers found: {total_papers}\n\n")
        
        # Configuration details
        if config_file_dict.get('journals'):
            f.write("JOURNALS MONITORED\n")
            f.write("-" * 40 + "\n")
            for journal in config_file_dict['journals']:
                f.write(f"• {journal}\n")
            f.write("\n")
        
        if config_file_dict.get('topics'):
            f.write("KEYWORDS SEARCHED\n")
            f.write("-" * 40 + "\n")
            for topic in config_file_dict['topics']:
                frequency = keyword_frequency_dict.get(topic, 0)
                f.write(f"• {topic} (found in {frequency} papers)\n")
            f.write("\n")
        
        if config_file_dict.get('orcids'):
            f.write("AUTHORS MONITORED (ORCID)\n")
            f.write("-" * 40 + "\n")
            for orcid in config_file_dict['orcids']:
                f.write(f"• {orcid}\n")
            f.write("\n")
        
        # Keyword-based results
        if components_keyword:
            f.write("KEYWORD-BASED SEARCH RESULTS\n")
            f.write("=" * 50 + "\n\n")
            write_paper_sections(f, components_keyword)
        
        # ORCID-based results
        if components_orcid:
            f.write("AUTHOR/ORCID-BASED SEARCH RESULTS\n")
            f.write("=" * 50 + "\n\n")
            write_paper_sections(f, components_orcid)
        
        # Footer
        f.write("\n" + "=" * 80 + "\n")
        f.write("End of Report\n")
        f.write("=" * 80 + "\n")
    
    print(f"  Text report written to: {txt_name}")


def write_paper_sections(file_handle, components: List[Dict[str, Any]]) -> None:
    """
    Write paper information sections to file.
    
    Args:
        file_handle: Open file handle
        components: List of paper components
    """
    for i, component in enumerate(components, 1):
        file_handle.write(f"[{i:3d}] {component.get('Title', 'No title')}\n")
        file_handle.write("-" * 60 + "\n")
        
        # Authors
        authors = component.get('Authors', [])
        if authors and authors != ['No authors available']:
            if len(authors) > 5:
                author_str = f"{', '.join(authors[:5])} et al. ({len(authors)} total)"
            else:
                author_str = ', '.join(authors)
            file_handle.write(f"Authors: {author_str}\n")
        
        # Journal and date
        journal = component.get('Journal', 'Unknown journal')
        date = component.get('Date', 'Unknown date')
        file_handle.write(f"Journal: {journal}\n")
        file_handle.write(f"Date: {date}\n")
        
        # Source
        source = component.get('Source', 'Unknown')
        file_handle.write(f"Source: {source.title()}\n")
        
        # Link
        link = component.get('Link', 'No link available')
        if link != 'No link available':
            file_handle.write(f"Link: {link}\n")
        
        # Keywords
        keywords = component.get('Keywords', [])
        if keywords and keywords != ['No keywords available']:
            keyword_str = ', '.join(keywords[:10])  # Limit to first 10
            if len(keywords) > 10:
                keyword_str += f" (and {len(keywords) - 10} more)"
            file_handle.write(f"Keywords: {keyword_str}\n")
        
        # Abstract
        abstract = component.get('Abstract', 'No abstract available')
        if abstract != 'No abstract available':
            # Wrap abstract text
            wrapped_abstract = wrap_text(abstract, width=70, indent="    ")
            file_handle.write(f"Abstract:\n{wrapped_abstract}\n")
        
        # Institutions
        institutions = component.get('Institution', [])
        if institutions and institutions != ['No institution listed']:
            if len(institutions) > 3:
                inst_str = f"{'; '.join(institutions[:3])} (and {len(institutions) - 3} more)"
            else:
                inst_str = '; '.join(institutions)
            file_handle.write(f"Institutions: {inst_str}\n")
        
        file_handle.write("\n")


def wrap_text(text: str, width: int = 70, indent: str = "") -> str:
    """
    Wrap text to specified width with optional indentation.
    
    Args:
        text: Text to wrap
        width: Maximum line width
        indent: String to prepend to each line
        
    Returns:
        Wrapped text string
    """
    import textwrap
    
    # Clean up the text
    clean_text = ' '.join(text.split())
    
    # Wrap the text
    wrapped = textwrap.fill(
        clean_text,
        width=width - len(indent),
        initial_indent=indent,
        subsequent_indent=indent
    )
    
    return wrapped


def write_json_file(
    data: Dict[str, Any],
    filename: str = "results.json",
    auto_mode: bool = False
) -> None:
    """
    Write data to JSON file.
    
    Args:
        data: Data dictionary to write
        filename: Output filename
        auto_mode: Whether running in automatic mode
    """
    # Check if file exists and get permission if not in auto mode
    if Path(filename).exists() and not auto_mode:
        response = input(f"{filename} already exists. Overwrite? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("JSON file creation cancelled.")
            return
    
    # Make data JSON-safe
    safe_data = make_json_safe(data)
    
    # Write JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(safe_data, f, indent=2, ensure_ascii=False)
    
    print(f"  JSON data written to: {filename}")


def write_csv_file(
    components: List[Dict[str, Any]],
    filename: str = "publications.csv",
    auto_mode: bool = False
) -> None:
    """
    Write paper components to CSV file.
    
    Args:
        components: List of paper component dictionaries
        filename: Output filename
        auto_mode: Whether running in automatic mode
    """
    import csv
    
    if not components:
        print("No data to write to CSV.")
        return
    
    # Check if file exists and get permission
    if Path(filename).exists() and not auto_mode:
        response = input(f"{filename} already exists. Overwrite? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("CSV file creation cancelled.")
            return
    
    # Define CSV columns
    columns = [
        'Title', 'Authors', 'Journal', 'Date', 'Abstract', 
        'Keywords', 'Institution', 'Link', 'Source'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        
        for component in components:
            # Prepare row data
            row = {}
            for col in columns:
                value = component.get(col, '')
                
                # Handle list fields
                if isinstance(value, list):
                    row[col] = '; '.join(str(v) for v in value)
                else:
                    row[col] = str(value) if value else ''
            
            writer.writerow(row)
    
    print(f"  CSV data written to: {filename}")


def create_backup_file(filename: str) -> str:
    """
    Create a backup of an existing file.
    
    Args:
        filename: Original filename
        
    Returns:
        Backup filename
    """
    if not Path(filename).exists():
        return None
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{filename}.backup_{timestamp}"
    
    # Copy file
    import shutil
    shutil.copy2(filename, backup_name)
    
    return backup_name


def ensure_output_directory(output_dir: str) -> Path:
    """
    Ensure output directory exists.
    
    Args:
        output_dir: Directory path
        
    Returns:
        Path object for the directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


if __name__ == "__main__":
    # Test the file writers
    print("Testing file writers...")
    
    # Sample data
    sample_components = [
        {
            'Title': 'Test Paper 1',
            'Authors': ['John Doe', 'Jane Smith'],
            'Journal': 'Test Journal',
            'Date': '2024/01/15',
            'Abstract': 'This is a test abstract for the first paper.',
            'Source': 'test'
        },
        {
            'Title': 'Test Paper 2',
            'Authors': ['Alice Johnson'],
            'Journal': 'Another Journal',
            'Date': '2024/02/20',
            'Abstract': 'This is a test abstract for the second paper.',
            'Source': 'test'
        }
    ]
    
    sample_config = {
        'email': 'test@example.com',
        'lookup_frequency': '1 week',
        'topics': ['machine learning', 'AI'],
        'orcids': ['0000-0000-0000-0000']
    }
    
    # Test text file writing
    write_txt_file(
        start_end_date=('2024/01/01', '2024/12/31'),
        config_file_dict=sample_config,
        components_keyword=sample_components[:1],
        components_orcid=sample_components[1:],
        keyword_frequency_dict={'machine learning': 1, 'AI': 0},
        txt_name='test_output.txt',
        auto_mode=True
    )
    
    print("File writers test completed.")