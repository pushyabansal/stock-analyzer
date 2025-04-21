import pytest
from datetime import datetime, date
from unittest.mock import patch

from app.utils.helpers import validate_date_range

def test_validate_date_range_with_both_dates():
    """Test validate_date_range with both start and end dates provided"""
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    
    # Call the function
    validated_start, validated_end = validate_date_range(start_date, end_date)
    
    # Check that the dates were validated correctly
    assert validated_start == start_date
    assert validated_end == end_date

def test_validate_date_range_with_only_start_date():
    """Test validate_date_range with only start date provided"""
    start_date = "2023-01-01"
    
    # Mock the current date
    today = date(2023, 1, 31)
    with patch("app.utils.helpers.datetime") as mock_datetime:
        mock_datetime.fromisoformat.return_value = datetime(2023, 1, 1)
        mock_datetime.now.return_value = datetime(2023, 1, 31)
        
        # Call the function
        validated_start, validated_end = validate_date_range(start_date)
        
        # Check that start_date is the provided one and end_date is today
        assert validated_start == start_date
        assert validated_end == today.isoformat()

def test_validate_date_range_with_swapped_dates():
    """Test validate_date_range with start_date after end_date"""
    start_date = "2023-01-31"
    end_date = "2023-01-01"
    
    # Call the function
    validated_start, validated_end = validate_date_range(start_date, end_date)
    
    # Check that the dates were swapped
    assert validated_start == end_date
    assert validated_end == start_date

def test_validate_date_range_with_invalid_date_format():
    """Test validate_date_range with an invalid date format"""
    start_date = "invalid-date"
    
    # Check that the function raises a ValueError
    with pytest.raises(ValueError):
        validate_date_range(start_date)

def test_validate_date_range_with_different_formats():
    """Test validate_date_range with different date formats"""
    # These are both ISO format dates but with different separators
    start_date = "2023-01-01"
    end_date = "2023/01/31"  # Not a valid ISO format
    
    # Check that the function raises a ValueError for the invalid format
    with pytest.raises(ValueError):
        validate_date_range(start_date, end_date) 