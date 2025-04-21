import pytest
from unittest.mock import patch, MagicMock

from app.services.data_acquisition import get_all_tickers
from tests.mocks import MockDBFunctions

@pytest.fixture
def mock_execute_query():
    """Mock execute_query database function"""
    with patch("app.services.data_acquisition.execute_query") as mock:
        # Set up the side effect to return ticker results
        mock.return_value = [("AAPL",), ("MSFT",), ("AMZN",), ("GOOGL",)]
        yield mock

def test_get_all_tickers_success(mock_execute_query):
    """Test successful retrieval of all tickers from the database"""
    # Call the function
    tickers = get_all_tickers()
    
    # Check that the function returned the expected tickers
    assert tickers == ["AAPL", "MSFT", "AMZN", "GOOGL"]
    
    # Check that execute_query was called with the correct query
    mock_execute_query.assert_called_once_with("SELECT ticker FROM stocks")

def test_get_all_tickers_handles_exception():
    """Test that the function handles exceptions gracefully"""
    # Set up the mock for execute_query to raise an exception
    with patch("app.services.data_acquisition.execute_query", side_effect=Exception("Test error")):
        # Call the function
        tickers = get_all_tickers()
        
        # Check that the function returns an empty list on error
        assert tickers == []

def test_get_all_tickers_empty_result():
    """Test handling of empty result set"""
    # Set up the mock for execute_query to return an empty list
    with patch("app.services.data_acquisition.execute_query", return_value=[]):
        # Call the function
        tickers = get_all_tickers()
        
        # Check that the function returns an empty list
        assert tickers == []

def test_get_all_tickers_with_db_mocks():
    """Test get_all_tickers using the MockDBFunctions class"""
    # Set up the mock using our common mock class
    with patch("app.services.data_acquisition.execute_query", 
               side_effect=MockDBFunctions.execute_query_side_effect):
        # Call the function
        tickers = get_all_tickers()
        
        # Check the result
        assert len(tickers) == 4
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "AMZN" in tickers
        assert "GOOGL" in tickers 