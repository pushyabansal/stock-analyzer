import pytest
from unittest.mock import patch, MagicMock

from app.services.index_service import get_trading_dates
from tests.mocks import MockDBFunctions

@pytest.fixture
def mock_execute_query():
    """Mock execute_query database function"""
    with patch("app.services.index_service.execute_query") as mock:
        # Set up the mock to return date results
        mock.return_value = [("2023-01-02",), ("2023-01-03",), ("2023-01-04",)]
        yield mock

def test_get_trading_dates_with_start_date_only(mock_execute_query):
    """Test get_trading_dates with only start_date parameter"""
    # Call the function
    dates = get_trading_dates("2023-01-01")
    
    # Check the result
    assert len(dates) == 3
    assert dates == ["2023-01-02", "2023-01-03", "2023-01-04"]
    
    # Check that the query was executed with the correct parameters
    mock_execute_query.assert_called_once()
    query_arg = mock_execute_query.call_args[0][0]
    assert "SELECT DISTINCT date" in query_arg
    assert "FROM daily_data" in query_arg
    assert "WHERE date >= ?" in query_arg
    assert "ORDER BY date" in query_arg
    
    params_arg = mock_execute_query.call_args[0][1]
    assert params_arg == ["2023-01-01"]

def test_get_trading_dates_with_date_range(mock_execute_query):
    """Test get_trading_dates with both start_date and end_date parameters"""
    # Call the function
    dates = get_trading_dates("2023-01-01", "2023-01-31")
    
    # Check the result
    assert len(dates) == 3
    
    # Check that the query was executed with the correct parameters
    mock_execute_query.assert_called_once()
    query_arg = mock_execute_query.call_args[0][0]
    assert "SELECT DISTINCT date" in query_arg
    assert "FROM daily_data" in query_arg
    assert "WHERE date >= ?" in query_arg
    assert "AND date <= ?" in query_arg
    assert "ORDER BY date" in query_arg
    
    params_arg = mock_execute_query.call_args[0][1]
    assert params_arg == ["2023-01-01", "2023-01-31"]

def test_get_trading_dates_empty_result():
    """Test get_trading_dates with empty result"""
    # Set up the mock to return an empty result
    with patch("app.services.index_service.execute_query", return_value=[]):
        # Call the function
        dates = get_trading_dates("2023-01-01")
        
        # Check that an empty list is returned
        assert dates == []

def test_get_trading_dates_with_db_mocks():
    """Test get_trading_dates using the MockDBFunctions class"""
    # Use our common MockDBFunctions class with a custom side effect for this test
    mock_query_fn = MagicMock(side_effect=lambda query, params=None: [
        ("2023-01-02",), ("2023-01-03",), ("2023-01-04",)
    ] if "SELECT DISTINCT date" in query else [])
    
    with patch("app.services.index_service.execute_query", mock_query_fn):
        # Call the function
        dates = get_trading_dates("2023-01-01")
        
        # Check the result
        assert len(dates) == 3
        assert dates == ["2023-01-02", "2023-01-03", "2023-01-04"] 