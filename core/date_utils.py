"""
Date utilities for the Journal Lookup Tool.
Handles date parsing, validation, and range calculations.
"""

import re
from datetime import datetime, timedelta
from typing import Tuple





def validate_date(date_str: str) -> None:
    """
    Validate date string format (YYYY/MM/DD).
    
    Args:
        date_str: Date string to validate
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        datetime.strptime(date_str, "%Y/%m/%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY/MM/DD") from e








def parse_lookup_frequency(freq_str: str) -> timedelta:
    """
    Parse frequency string and return timedelta object.
    
    Args:
        freq_str: Frequency string like "1 week", "7 days", "2 months"
        
    Returns:
        timedelta object representing the frequency
        
    Raises:
        ValueError: If frequency format is invalid or unsupported
    """
    if not freq_str or not freq_str.strip():
        raise ValueError("Lookup frequency cannot be empty")
    
    # Match pattern like "1 week", "7 days", "2 months"
    match = re.match(r"(\d+)\s*(\w+)", freq_str.strip().lower())
    if not match:
        raise ValueError(
            f"Invalid lookup frequency format: '{freq_str}'. "
            "Expected format like '1 week', '7 days', or '2 months'"
        )
    
    number = int(match.group(1))
    unit = match.group(2).lower()
    
    # Handle different time units
    if unit.startswith('day'):
        return timedelta(days=number)
    elif unit.startswith('week'):
        return timedelta(weeks=number)
    elif unit.startswith('month'):
        # Approximate months as 30 days
        return timedelta(days=number * 30)
    elif unit.startswith('year'):
        # Approximate years as 365 days
        return timedelta(days=number * 365)
    else:
        raise ValueError(
            f"Unsupported time unit: '{unit}'. "
            "Supported units: days, weeks, months, years"
        )






def calculate_date_range(frequency: str, end_date: str = '3000/01/01') -> Tuple[str, str]:
    """
    Calculate start and end dates based on frequency.
    
    Args:
        frequency: Frequency string like "1 week"
        end_date: End date string (default: far future)
        
    Returns:
        Tuple of (start_date, end_date) as strings in YYYY/MM/DD format
    """
    delta = parse_lookup_frequency(frequency)
    now = datetime.now()
    start_date = now - delta
    
    start_date_str = start_date.strftime("%Y/%m/%d")
    return start_date_str, end_date





def ask_user_date(lookup_frequency: str, end_date_default: str = '3000/01/01', auto_mode: bool = False) -> Tuple[str, str]:
    """
    Get date range from user or calculate automatically.
    
    Args:
        lookup_frequency: Frequency string for automatic calculation
        end_date_default: Default end date
        auto_mode: If True, skip user interaction
        
    Returns:
        Tuple of (start_date, end_date) as strings in YYYY/MM/DD format
    """
    if auto_mode:
        start_date_str, end_date_str = calculate_date_range(lookup_frequency, end_date_default)
        print(f" Auto mode - Date range:")
        print(f"   Start: {start_date_str}")
        print(f"   End: {end_date_str}")
        return start_date_str, end_date_str
    
    # Interactive mode
    print(f"\n Date Range Selection:")
    print(f"   Current lookup frequency: {lookup_frequency}")
    
    use_default = input(
        f"Use default mode? This will search from {lookup_frequency} ago "
        f"until {end_date_default}. (y/n) [y]: "
    ).strip().lower()
    
    if use_default in ('y', 'yes', ''):
        start_date_str, end_date_str = calculate_date_range(lookup_frequency, end_date_default)
        print(f"   Using default range: {start_date_str} to {end_date_str}")
        return start_date_str, end_date_str
    
    # Manual date entry
    print("\n Manual date entry:")
    
    while True:
        try:
            start_date = input("Enter start date (YYYY/MM/DD): ").strip()
            validate_date(start_date)
            break
        except ValueError as e:
            print(f"{e}")
    
    while True:
        try:
            end_date = input(f"Enter end date (YYYY/MM/DD) [{end_date_default}]: ").strip()
            if not end_date:
                end_date = end_date_default
            else:
                validate_date(end_date)
            break
        except ValueError as e:
            print(f"{e}")
    
    print(f"   Using manual range: {start_date} to {end_date}")
    return start_date, end_date






def format_date_for_api(date_str: str, api_format: str = 'crossref') -> str:
    """
    Convert date format for different APIs.
    
    Args:
        date_str: Date string in YYYY/MM/DD format
        api_format: Target API format ('crossref', 'pubmed')
        
    Returns:
        Formatted date string
    """
    if api_format == 'crossref':
        # CrossRef expects YYYY-MM-DD
        return date_str.replace('/', '-')
    elif api_format == 'pubmed':
        # PubMed typically uses YYYY/MM/DD (already correct)
        return date_str
    else:
        raise ValueError(f"Unsupported API format: {api_format}")





def parse_api_date(date_data, source: str = 'unknown') -> str:
    """
    Parse date from API response into standard format.
    
    Args:
        date_data: Date data from API (various formats)
        source: Source API name for format detection
        
    Returns:
        Standardized date string (YYYY/MM/DD) or error message
    """
    if not date_data:
        return "No date available"
    
    try:
        if source == 'crossref':
            # CrossRef date-parts format: [[2024, 1, 15]]
            if isinstance(date_data, dict) and 'date-parts' in date_data:
                date_parts = date_data['date-parts'][0]
                if len(date_parts) >= 3:
                    year, month, day = date_parts[:3]
                    return f"{year:04d}/{month:02d}/{day:02d}"
                elif len(date_parts) >= 2:
                    year, month = date_parts[:2]
                    return f"{year:04d}/{month:02d}/01"
                elif len(date_parts) >= 1:
                    year = date_parts[0]
                    return f"{year:04d}/01/01"
            
            # Direct string format
            elif isinstance(date_data, str):
                # Try parsing ISO format
                if '-' in date_data:
                    return date_data.replace('-', '/')
                
        elif source == 'pubmed':
            # PubMed date format: {'Year': '2024', 'Month': '01', 'Day': '15'}
            if isinstance(date_data, dict):
                year = date_data.get('Year', '')
                month = date_data.get('Month', '01')
                day = date_data.get('Day', '01')
                if year:
                    return f"{year}/{month.zfill(2)}/{day.zfill(2)}"
            
            # List format: [{'Year': '2024', 'Month': '01', 'Day': '15'}]
            elif isinstance(date_data, list) and date_data:
                return parse_api_date(date_data[0], source)
        
        # Fallback: try to extract year from string representation
        date_str = str(date_data)
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            return f"{year_match.group(1)}/01/01"
            
    except (IndexError, KeyError, ValueError, TypeError):
        pass
    
    return f"Invalid date format: {date_data}"





if __name__ == "__main__":
    # Test the functions
    print("Testing date utilities...")
    
    # Test frequency parsing
    frequencies = ["1 week", "7 days", "2 months", "1 year"]
    for freq in frequencies:
        try:
            delta = parse_lookup_frequency(freq)
            print(f"'{freq}' -> {delta.days} days")
        except ValueError as e:
            print(f"'{freq}' -> Error: {e}")
    
    # Test date range calculation
    start, end = calculate_date_range("1 week")
    print(f"Date range for '1 week': {start} to {end}")