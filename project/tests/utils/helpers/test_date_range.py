import pytest
from datetime import datetime

from app.utils.helpers import date_range

def test_date_range_same_day():
    """Test date_range with start_date and end_date on the same day"""
    start_date = "2023-01-01"
    end_date = "2023-01-01"
    
    # Call the function
    dates = date_range(start_date, end_date)
    
    # Check that only one date is returned
    assert len(dates) == 1
    assert dates[0] == start_date

def test_date_range_consecutive_days():
    """Test date_range with two consecutive days"""
    start_date = "2023-01-01"
    end_date = "2023-01-02"
    
    # Call the function
    dates = date_range(start_date, end_date)
    
    # Check that both dates are returned
    assert len(dates) == 2
    assert dates[0] == start_date
    assert dates[1] == end_date

def test_date_range_multiple_days():
    """Test date_range with a range of dates"""
    start_date = "2023-01-01"
    end_date = "2023-01-05"
    
    # Call the function
    dates = date_range(start_date, end_date)
    
    # Check that the correct dates are returned
    assert len(dates) == 5
    assert dates[0] == "2023-01-01"
    assert dates[1] == "2023-01-02"
    assert dates[2] == "2023-01-03"
    assert dates[3] == "2023-01-04"
    assert dates[4] == "2023-01-05"

def test_date_range_across_months():
    """Test date_range across month boundaries"""
    start_date = "2023-01-30"
    end_date = "2023-02-02"
    
    # Call the function
    dates = date_range(start_date, end_date)
    
    # Check that the correct dates are returned
    assert len(dates) == 4
    assert dates[0] == "2023-01-30"
    assert dates[1] == "2023-01-31"
    assert dates[2] == "2023-02-01"
    assert dates[3] == "2023-02-02"

def test_date_range_across_years():
    """Test date_range across year boundaries"""
    start_date = "2022-12-30"
    end_date = "2023-01-02"
    
    # Call the function
    dates = date_range(start_date, end_date)
    
    # Check that the correct dates are returned
    assert len(dates) == 4
    assert dates[0] == "2022-12-30"
    assert dates[1] == "2022-12-31"
    assert dates[2] == "2023-01-01"
    assert dates[3] == "2023-01-02"

def test_date_range_invalid_dates():
    """Test date_range with invalid date format"""
    start_date = "invalid-date"
    end_date = "2023-01-02"
    
    # Check that the function raises a ValueError
    with pytest.raises(ValueError):
        date_range(start_date, end_date)

def test_date_range_invalid_order():
    """Test date_range with end_date before start_date"""
    start_date = "2023-01-05"
    end_date = "2023-01-01"
    
    # The function should still work but return dates in the right order
    # Since date_range itself doesn't validate, this would return an empty list
    dates = date_range(start_date, end_date)
    
    # Check that no dates are returned since start is after end
    assert len(dates) == 0 