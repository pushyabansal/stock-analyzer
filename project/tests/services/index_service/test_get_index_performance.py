import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.index_service import get_index_performance
from tests.mocks import MockDBFunctions

@pytest.fixture
def mock_execute_pandas_query():
    """Mock execute_pandas_query database function"""
    with patch("app.services.index_service.execute_pandas_query") as mock:
        # Create a sample DataFrame for index performance
        df = pd.DataFrame({
            "date": ["2023-01-02", "2023-01-03", "2023-01-04"],
            "daily_return": [0.01, 0.02, -0.01],
            "cumulative_return": [0.01, 0.03, 0.02]
        })
        mock.return_value = df
        yield mock

def test_get_index_performance_success(mock_execute_pandas_query):
    """Test successful retrieval of index performance data"""
    # Call the function
    result = get_index_performance("2023-01-01", "2023-01-31")
    
    # Check that the query was executed with the correct parameters
    mock_execute_pandas_query.assert_called_once()
    query_arg = mock_execute_pandas_query.call_args[0][0]
    assert "SELECT date, daily_return, cumulative_return" in query_arg
    assert "FROM index_performance" in query_arg
    assert "WHERE date >= ?" in query_arg
    assert "AND date <= ?" in query_arg
    assert "ORDER BY date" in query_arg
    
    params_arg = mock_execute_pandas_query.call_args[0][1]
    assert params_arg[0] == "2023-01-01"
    assert params_arg[1] == "2023-01-31"
    
    # Check the result
    assert isinstance(result, list)
    assert len(result) == 3
    
    # Check the first item in the result
    first_item = result[0]
    assert isinstance(first_item, dict)
    assert "date" in first_item
    assert "daily_return" in first_item
    assert "cumulative_return" in first_item
    assert first_item["date"] == "2023-01-02"
    assert first_item["daily_return"] == 0.01
    assert first_item["cumulative_return"] == 0.01

def test_get_index_performance_with_only_start_date(mock_execute_pandas_query):
    """Test get_index_performance with only start_date parameter"""
    # Call the function with only start_date
    result = get_index_performance("2023-01-01")
    
    # Check that the query was executed with the correct parameters
    mock_execute_pandas_query.assert_called_once()
    params_arg = mock_execute_pandas_query.call_args[0][1]
    assert params_arg[0] == "2023-01-01"
    # The function doesn't append end_date if it's None
    assert len(params_arg) == 1

def test_get_index_performance_empty_result():
    """Test get_index_performance with empty result"""
    # Set up the mock to return an empty DataFrame
    with patch("app.services.index_service.execute_pandas_query", return_value=pd.DataFrame()):
        # Call the function
        result = get_index_performance("2023-01-01", "2023-01-31")
        
        # Check that an empty list is returned
        assert result == []

def test_get_index_performance_format_values():
    """Test that get_index_performance correctly formats the values in the result"""
    # Create a sample DataFrame with float values that need formatting
    df = pd.DataFrame({
        "date": ["2023-01-02"],
        "daily_return": [0.012345],  # Should be formatted as percentage
        "cumulative_return": [0.123456]  # Should be formatted as percentage
    })
    
    with patch("app.services.index_service.execute_pandas_query", return_value=df):
        # Call the function
        result = get_index_performance("2023-01-01", "2023-01-31")
        
        # Check that the values are correctly formatted
        assert len(result) == 1
        assert result[0]["date"] == "2023-01-02"
        
        # Check if the values are correctly formatted as percentages
        # The exact format depends on the implementation of the function
        assert round(result[0]["daily_return"], 6) == 0.012345
        assert round(result[0]["cumulative_return"], 6) == 0.123456

def test_get_index_performance_with_mock_db_functions():
    """Test get_index_performance using MockDBFunctions"""
    # Create a custom mock function for execute_pandas_query
    def mock_pandas_query(query, params=None):
        if "FROM index_performance" in query:
            return pd.DataFrame({
                "date": ["2023-01-02", "2023-01-03", "2023-01-04"],
                "daily_return": [0.01, 0.02, -0.01],
                "cumulative_return": [0.01, 0.03, 0.02]
            })
        return pd.DataFrame()
    
    # Patch with our custom mock
    with patch("app.services.index_service.execute_pandas_query", side_effect=mock_pandas_query):
        # Call the function
        result = get_index_performance("2023-01-01", "2023-01-31")
        
        # Check the result
        assert len(result) == 3
        assert result[0]["date"] == "2023-01-02"
        assert result[1]["date"] == "2023-01-03"
        assert result[2]["date"] == "2023-01-04" 