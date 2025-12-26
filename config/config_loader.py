"""
Configuration loader for the Journal Lookup Tool.
Handles YAML-based configuration files with validation.
"""

import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple
import yaml
from core.date_utils import validate_date, parse_lookup_frequency





def load_yaml_file(filepath: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}





def parse_authors(raw_authors: List[str]) -> Tuple[List[str], List[Dict[str, str]], List[str]]:
    """
    Parse author entries that may include ORCID IDs and names.
    
    Args:
        raw_authors: List of author strings, possibly with comments
        
    Returns:
        Tuple of (raw_authors, named_authors, orcids)
    """
    named_authors = []
    orcids = []
    
    for entry in raw_authors:
        if isinstance(entry, str) and '#' in entry:
            # Format: "0000-0000-0000-0000 # Author Name"
            orcid, name = entry.split('#', 1)
            orcid = orcid.strip()
            name = name.strip()
            
            named_authors.append({
                'orcid': orcid,
                'name': name
            })
            orcids.append(orcid)
            
        elif isinstance(entry, dict) and "orcid" in entry and "name" in entry:
            # Already structured
            named_authors.append(entry)
            orcids.append(entry['orcid'])
            
        elif isinstance(entry, str):
            # Only ORCID given, no name
            orcid = entry.strip()
            named_authors.append({
                'orcid': orcid,
                'name': None
            })
            orcids.append(orcid)
    
    return raw_authors, named_authors, orcids







def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration parameters with friendly errors.
    
    Raises:
        ValueError: On any validation problem.
    """
    email = (config.get('email') or "").strip()
    if not email:
        raise ValueError("Missing required configuration field: email")
    if '@' not in email or email.count('@') != 1:
        raise ValueError(f"Invalid email format: {email}")
    
    lookup_frequency = config.get('lookup_frequency')
    try:
        parse_lookup_frequency(lookup_frequency)
    except Exception as exc:
        raise ValueError(f"Invalid lookup_frequency '{lookup_frequency}': {exc}") from exc
    
    journals = config.get('journals', [])
    if not isinstance(journals, list) or not journals:
        raise ValueError("journals must be a non-empty list of journal names")
    if not all(isinstance(j, str) and j.strip() for j in journals):
        raise ValueError("journals entries must be non-empty strings")
    
    topics = config.get('topics', [])
    if not isinstance(topics, list) or not topics:
        raise ValueError("topics must be a non-empty list of keywords")
    if not all(isinstance(t, str) and t.strip() for t in topics):
        raise ValueError("topics entries must be non-empty strings")
    
    date_ranges = config.get('date_ranges', [])
    if date_ranges:
        if not isinstance(date_ranges, list):
            raise ValueError("date_ranges must be a list of [start, end] pairs")
        for idx, date_range in enumerate(date_ranges, start=1):
            if not isinstance(date_range, (list, tuple)) or len(date_range) != 2:
                raise ValueError(f"date_ranges entry #{idx} must be [start, end]")
            start, end = date_range
            try:
                validate_date(start)
                validate_date(end)
            except ValueError as exc:
                raise ValueError(f"date_ranges entry #{idx} has invalid date: {exc}") from exc






def load_config(config_dir: str = 'config') -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Load configuration from YAML files in the specified directory.
    
    Args:
        config_dir: Directory containing configuration files
        
    Returns:
        Tuple of (config_dict, keyword_frequency_dict)
    """
    config_path = Path(config_dir)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration directory not found: {config_path}")
    
    # Load individual config files
    try:
        meta = load_yaml_file(config_path / 'meta.yaml')
        journals = load_yaml_file(config_path / 'journals.yaml')
        topics = load_yaml_file(config_path / 'keywords.yaml')
        authors = load_yaml_file(config_path / 'authors.yaml')
        dates = load_yaml_file(config_path / 'dates.yaml')
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Missing configuration file: {e}")
    
    # Parse authors
    raw_authors = authors.get('authors', [])
    raw_authors, named_authors, orcids = parse_authors(raw_authors)
    
    # Build main configuration dictionary
    config_dict = {
        'email': meta.get('email'),
        'lookup_frequency': meta.get('lookup_frequency', '1 week'),
        'update_date': meta.get('update_date', 'N/A'),
        'journals': journals.get('journals', []),
        'topics': topics.get('topics', []),
        'authors': raw_authors,
        'named_authors': named_authors,
        'orcids': orcids,
        'date_ranges': dates.get('date_ranges', [])
    }
    
    # Validate configuration
    validate_config(config_dict)
    
    # Create keyword frequency dictionary
    keyword_frequency_dict = {kw: 0 for kw in config_dict['topics']}
    
    # Debug output
    print(f"  Loaded configuration:")
    print(f"  Email: {config_dict['email']}")
    print(f"  Journals: {len(config_dict['journals'])} configured")
    print(f"  Keywords: {len(config_dict['topics'])} configured")
    print(f"  Authors/ORCIDs: {len(config_dict['orcids'])} configured")
    print(f"  Date ranges: {len(config_dict['date_ranges'])} configured")
    
    return config_dict, keyword_frequency_dict






def create_sample_config(config_dir: str = 'config') -> None:
    """Create sample configuration files."""
    config_path = Path(config_dir)
    config_path.mkdir(exist_ok=True)
    
    # Sample meta.yaml
    meta_sample = {
        'email': 'your.email@institution.edu',
        'lookup_frequency': '1 week',
        'update_date': '20250815'
    }
    
    # Sample journals.yaml
    journals_sample = {
        'journals': [
            'Nature',
            'Science',
            'Cell',
            'Nature Biotechnology',
            'Journal of the American Chemical Society'
        ]
    }
    
    # Sample keywords.yaml
    keywords_sample = {
        'topics': [
            'CRISPR',
            'machine learning',
            'photosynthesis',
            'protein structure',
            'climate change'
        ]
    }
    
    # Sample authors.yaml
    authors_sample = {
        'authors': [
            '0000-0000-0000-0000 # Sample Author',
            '0000-0000-0000-0001 # Another Researcher'
        ]
    }
    
    # Sample dates.yaml
    dates_sample = {
        'date_ranges': [
            ['2024/01/01', '2024/01/31'],
            ['2024/02/01', '2024/02/29']
        ]
    }
    
    # Write sample files
    samples = {
        'meta.yaml': meta_sample,
        'journals.yaml': journals_sample,
        'keywords.yaml': keywords_sample,
        'authors.yaml': authors_sample,
        'dates.yaml': dates_sample
    }
    
    for filename, content in samples.items():
        filepath = config_path / filename
        if not filepath.exists():
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(content, f, default_flow_style=False, indent=2)
            print(f"Created sample configuration: {filepath}")






def main() -> None:
    """CLI helper for creating and validating config files."""
    parser = argparse.ArgumentParser(description="Manage Journal Lookup Tool configuration.")
    parser.add_argument(
        "--init-samples",
        action="store_true",
        help="Create sample YAML files in the config/ directory (does not overwrite existing files).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate existing config files and print a short summary.",
    )
    args = parser.parse_args()
    
    if args.init_samples:
        create_sample_config()
        print("Sample configuration files created. Edit them with your details.")
    
    if args.check:
        try:
            load_config()
            print("Configuration validation passed.")
        except Exception as exc:
            print(f"Configuration validation failed: {exc}")
            raise SystemExit(1)
    
    if not args.init_samples and not args.check:
        parser.print_help()


if __name__ == "__main__":
    main()
