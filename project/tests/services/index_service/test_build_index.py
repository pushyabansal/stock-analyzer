import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.index_service import build_index
from tests.mocks import MockDBFunctions

@pytest.fixture
def mock_deps():
    """Mock all dependencies for build_index"""
    with patch("app.services.index_service.index_exists_for_range") as mock_exists, \
         patch("app.services.index_service.calculate_daily_returns") as mock_returns, \
         patch("app.services.index_service.store_index_performance") as mock_store, \
         patch("app.services.index_service.detect_composition_changes") as mock_changes:
        
        # Set up default return values
        mock_exists.return_value = False
        
        # Create a DataFrame with test returns
        returns_df = pd.DataFrame({
            "date": ["2023-01-02", "2023-01-03", "2023-01-04"],
            "daily_return": [0.01, 0.02, -0.01],
            "cumulative_return": [0.01, 0.03, 0.02]
        })
        mock_returns.return_value = returns_df
        
        # Create a DataFrame with test changes
        changes_df = pd.DataFrame({
            "date": ["2023-01-03", "2023-01-04"],
            "ticker": ["AAPL", "MSFT"],
            "event": ["ENTRY", "EXIT"]
        })
        mock_changes.return_value = changes_df
        
        yield {
            "exists": mock_exists,
            "returns": mock_returns,
            "store": mock_store,
            "changes": mock_changes
        }

def test_build_index_success(mock_deps):
    """Test successful index building process"""
    # Call the function
    result = build_index("2023-01-01", "2023-01-31")
    
    # Check that all the necessary functions were called
    mock_deps["exists"].assert_called_once_with("2023-01-01", "2023-01-31")
    mock_deps["returns"].assert_called_once_with("2023-01-01", "2023-01-31")
    mock_deps["store"].assert_called_once()
    mock_deps["changes"].assert_called_once_with("2023-01-01", "2023-01-31")
    
    # Check the result structure
    assert isinstance(result, dict)
    assert "trading_days" in result
    assert result["trading_days"] == 3
    assert "start_date" in result
    assert result["start_date"] == "2023-01-01"
    assert "end_date" in result
    assert result["end_date"] == "2023-01-31"

def test_build_index_already_exists():
    """Test when index already exists for the specified range"""
    # Set up the mock to indicate the index already exists
    with patch("app.services.index_service.index_exists_for_range", return_value=True):
        # Call the function and expect a message about existing data
        try:
            result = build_index("2023-01-01", "2023-01-31")
            # If no error is raised, check that the result has an appropriate message
            assert "already exists" in result.get("message", "")
        except ValueError as e:
            # If a ValueError is raised, check that it has the correct message
            assert "already exists" in str(e)

def test_build_index_no_trading_dates(mock_deps):
    """Test when no trading dates are found"""
    # Set up the mock to return no trading dates
    mock_deps["returns"].return_value = pd.DataFrame()
    
    # Call the function
    result = build_index("2023-01-01", "2023-01-31")
    
    # Check the result
    assert isinstance(result, dict)
    assert "trading_days" in result
    assert result["trading_days"] == 0  # Now correctly returns 0 for empty performance DataFrame
    assert "start_date" in result
    assert result["start_date"] == "2023-01-01"
    assert "end_date" in result
    assert result["end_date"] == "2023-01-31"

def test_build_index_no_returns(mock_deps):
    """Test when no returns are calculated"""
    # Set up the mocks
    mock_deps["returns"].return_value = pd.DataFrame()  # Empty DataFrame
    
    # Call the function
    result = build_index("2023-01-01", "2023-01-31")
    
    # Check the result
    assert isinstance(result, dict)
    assert "trading_days" in result
    assert "start_date" in result
    assert result["start_date"] == "2023-01-01"
    assert "end_date" in result
    assert result["end_date"] == "2023-01-31"

def test_build_index_with_only_start_date(mock_deps):
    """Test build_index with only start_date parameter"""
    # Mock datetime.now to return a fixed date for testing
    mock_now = datetime(2023, 1, 31)
    with patch("app.services.index_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat = datetime.fromisoformat
        
        # Call the function with only start_date
        result = build_index("2023-01-01")
        
        # Check that the functions were called with correct parameters
        mock_deps["exists"].assert_called_once_with("2023-01-01", None)
        mock_deps["returns"].assert_called_once_with("2023-01-01", None)
        mock_deps["changes"].assert_called_once_with("2023-01-01", None)
        
        # Check the result
        assert result["start_date"] == "2023-01-01"
        assert result["end_date"] == "2023-01-31"  # Should match our mocked datetime.now 