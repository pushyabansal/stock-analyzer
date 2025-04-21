import pytest
from unittest.mock import patch, MagicMock

from app.services.index_service import index_exists_for_range
from tests.mocks import MockDBFunctions

@pytest.fixture
def mock_execute_query():
    """Mock execute_query database function"""
    with patch("app.services.index_service.execute_query") as mock:
        yield mock

def test_index_exists_for_range_true(mock_execute_query):
    """Test index_exists_for_range returns True when index exists"""
    # Set up the mock to return a count > 0
    mock_execute_query.return_value = [(5,)]
    
    # Call the function
    result = index_exists_for_range("2023-01-01", "2023-01-31")
    
    # Check the result
    assert result is True
    
    # Check that the query was executed with the correct parameters
    mock_execute_query.assert_called_once()
    query_arg = mock_execute_query.call_args[0][0]
    assert "SELECT COUNT(*)" in query_arg
    assert "FROM index_performance" in query_arg
    assert "WHERE date >= ?" in query_arg
    assert "AND date <= ?" in query_arg
    
    params_arg = mock_execute_query.call_args[0][1]
    assert params_arg == ["2023-01-01", "2023-01-31"]

def test_index_exists_for_range_false(mock_execute_query):
    """Test index_exists_for_range returns False when index doesn't exist"""
    # Set up the mock to return a count of 0
    mock_execute_query.return_value = [(0,)]
    
    # Call the function
    result = index_exists_for_range("2023-01-01", "2023-01-31")
    
    # Check the result
    assert result is False

def test_index_exists_for_range_with_only_start_date(mock_execute_query):
    """Test index_exists_for_range with only start_date"""
    # Set up the mock to return a count > 0
    mock_execute_query.return_value = [(3,)]
    
    # Call the function with only start_date
    result = index_exists_for_range("2023-01-01")
    
    # Check the result
    assert result is True
    
    # Check that the query was executed with only one parameter
    mock_execute_query.assert_called_once()
    query_arg = mock_execute_query.call_args[0][0]
    assert "SELECT COUNT(*)" in query_arg
    assert "FROM index_performance" in query_arg
    assert "WHERE date >= ?" in query_arg
    assert "AND date <= ?" not in query_arg
    
    params_arg = mock_execute_query.call_args[0][1]
    assert params_arg == ["2023-01-01"]

def test_index_exists_for_range_handles_exception():
    """Test index_exists_for_range handles exceptions gracefully"""
    # Use a direct patch on the function without using the fixture
    with patch("app.services.index_service.execute_query") as mock_execute_query:
        # Set up the mock to raise an exception
        mock_execute_query.side_effect = Exception("Test error")
        
        # Mock the logger to avoid actual logging
        with patch("app.services.index_service.logger"):
            # Call the function
            result = index_exists_for_range("2023-01-01", "2023-01-31")
            
            # Check the result (should default to False on error)
            assert result is False
            
            # Verify the patched function was called
            mock_execute_query.assert_called_once()

def test_index_exists_for_range_with_empty_result(mock_execute_query):
    """Test index_exists_for_range with empty result"""
    # Set up the mock to return an empty result
    mock_execute_query.return_value = []
    
    # Call the function
    result = index_exists_for_range("2023-01-01", "2023-01-31")
    
    # Check the result (should default to False)
    assert result is False

def test_index_exists_for_range_with_mock_db_functions():
    """Test index_exists_for_range using MockDBFunctions"""
    # Use our common MockDBFunctions class
    with patch("app.services.index_service.execute_query", 
               side_effect=MockDBFunctions.execute_query_side_effect):
        # The mock returns [(0,)] for COUNT(*) queries by default
        result = index_exists_for_range("2023-01-01", "2023-01-31")
        
        # Check the result
        assert result is False 