import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

def validate_date_range(start_date: str, end_date: Optional[str] = None) -> Tuple[str, str]:
    """
    Validate and normalize a date range.
    If end_date is not provided, use today.
    """
    try:
        # Parse start_date
        start = datetime.fromisoformat(start_date)
        
        # Parse end_date or use today
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()
        
        # Ensure start_date is before end_date
        if start > end:
            logger.warning(f"start_date {start} is after end_date {end}, swapping dates")
            start, end = end, start
        
        # Format dates as ISO strings
        return start.date().isoformat(), end.date().isoformat()
    
    except ValueError as e:
        logger.error(f"Error validating date range: {e}")
        raise ValueError(f"Invalid date format: {e}")

def date_range(start_date: str, end_date: str) -> List[str]:
    """
    Generate a list of dates between start_date and end_date (inclusive).
    Dates are returned as ISO format strings (YYYY-MM-DD).
    """
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    dates = []
    current = start
    
    while current <= end:
        dates.append(current.date().isoformat())
        current += timedelta(days=1)
    
    return dates

def format_number(value: float, decimal_places: int = 2) -> str:
    """Format a number with commas as thousand separators and fixed decimal places"""
    return f"{value:,.{decimal_places}f}"

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """Format a value as a percentage with fixed decimal places"""
    return f"{value * 100:.{decimal_places}f}%"

def format_market_cap(value: float) -> str:
    """Format market cap in billions or millions"""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    else:
        return f"${value:.2f}" 