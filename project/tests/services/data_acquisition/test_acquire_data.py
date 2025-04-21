import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

from app.services.data_acquisition import acquire_data
from tests.mocks import create_mock_daily_data

@pytest.fixture
def mock_get_all_tickers():
    """Mock get_all_tickers function"""
    with patch("app.services.data_acquisition.get_all_tickers") as mock:
        mock.return_value = ["AAPL", "MSFT", "AMZN", "GOOGL"]
        yield mock

@pytest.fixture
def mock_fetch_sp500_tickers():
    """Mock fetch_sp500_tickers function"""
    with patch("app.services.data_acquisition.fetch_sp500_tickers") as mock:
        mock.return_value = ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]
        yield mock

@pytest.fixture
def mock_fetch_stock_data():
    """Mock fetch_stock_data function"""
    with patch("app.services.data_acquisition.fetch_stock_data") as mock:
        # Return a mock daily data DataFrame
        mock.return_value = create_mock_daily_data()
        yield mock

@pytest.fixture
def mock_fetch_market_cap_data():
    """Mock fetch_market_cap_data function"""
    with patch("app.services.data_acquisition.fetch_market_cap_data") as mock:
        # Return mock market cap data
        mock.return_value = {
            "AAPL": 2000000000000,
            "MSFT": 1800000000000,
            "AMZN": 1600000000000,
            "GOOGL": 1400000000000
        }
        yield mock

@pytest.fixture
def mock_store_stock_data():
    """Mock store_stock_data function"""
    with patch("app.services.data_acquisition.store_stock_data") as mock:
        yield mock

def test_acquire_data_with_existing_tickers(
    mock_get_all_tickers, 
    mock_fetch_sp500_tickers,
    mock_fetch_stock_data,
    mock_fetch_market_cap_data,
    mock_store_stock_data
):
    """Test acquire_data when tickers already exist in the database"""
    # Call the function
    result = acquire_data(days=10)
    
    # Check the result
    assert result is True
    
    # Check that get_all_tickers was called
    mock_get_all_tickers.assert_called_once()
    
    # Check that fetch_sp500_tickers was not called since we had tickers from the database
    mock_fetch_sp500_tickers.assert_not_called()
    
    # Check that fetch_stock_data was called with the correct parameters
    mock_fetch_stock_data.assert_called_once()
    days_ago = datetime.now() - timedelta(days=10)
    days_ago_str = days_ago.strftime('%Y-%m-%d')
    today_str = datetime.now().strftime('%Y-%m-%d')
    args = mock_fetch_stock_data.call_args[0]
    assert args[0] == ["AAPL", "MSFT", "AMZN", "GOOGL"]  # Tickers
    assert args[1] == days_ago_str  # Start date
    assert args[2] == today_str  # End date
    
    # Check that fetch_market_cap_data was called with the correct parameters
    mock_fetch_market_cap_data.assert_called_once_with(["AAPL", "MSFT", "AMZN", "GOOGL"])
    
    # Check that store_stock_data was called
    mock_store_stock_data.assert_called_once()

def test_acquire_data_with_no_existing_tickers(
    mock_get_all_tickers, 
    mock_fetch_sp500_tickers,
    mock_fetch_stock_data,
    mock_fetch_market_cap_data,
    mock_store_stock_data
):
    """Test acquire_data when no tickers exist in the database"""
    # Set up get_all_tickers to return an empty list
    mock_get_all_tickers.return_value = []
    
    # Call the function
    result = acquire_data(days=10)
    
    # Check the result
    assert result is True
    
    # Check that get_all_tickers was called
    mock_get_all_tickers.assert_called_once()
    
    # Check that fetch_sp500_tickers was called since we had no tickers
    mock_fetch_sp500_tickers.assert_called_once()
    
    # Check that fetch_stock_data was called with the S&P 500 tickers
    mock_fetch_stock_data.assert_called_once()
    args = mock_fetch_stock_data.call_args[0]
    assert args[0] == ["AAPL", "MSFT", "AMZN", "GOOGL", "META"]  # S&P 500 tickers
    
    # Check that fetch_market_cap_data was called with the S&P 500 tickers
    mock_fetch_market_cap_data.assert_called_once_with(["AAPL", "MSFT", "AMZN", "GOOGL", "META"])
    
    # Check that store_stock_data was called
    mock_store_stock_data.assert_called_once()

def test_acquire_data_handles_both_ticker_sources_failing(
    mock_get_all_tickers, 
    mock_fetch_sp500_tickers,
    mock_fetch_stock_data,
    mock_fetch_market_cap_data,
    mock_store_stock_data
):
    """Test acquire_data when both ticker sources fail"""
    # Set up get_all_tickers and fetch_sp500_tickers to return empty lists
    mock_get_all_tickers.return_value = []
    mock_fetch_sp500_tickers.return_value = []
    
    # Call the function
    result = acquire_data(days=10)
    
    # Check the result
    assert result is False
    
    # Check that both ticker functions were called
    mock_get_all_tickers.assert_called_once()
    mock_fetch_sp500_tickers.assert_called_once()
    
    # Check that no data fetching or storing happened
    mock_fetch_stock_data.assert_not_called()
    mock_fetch_market_cap_data.assert_not_called()
    mock_store_stock_data.assert_not_called()

def test_acquire_data_with_empty_stock_data(
    mock_get_all_tickers, 
    mock_fetch_stock_data,
    mock_fetch_market_cap_data,
    mock_store_stock_data
):
    """Test acquire_data when fetch_stock_data returns empty data"""
    # Set up fetch_stock_data to return an empty DataFrame
    mock_fetch_stock_data.return_value = pd.DataFrame()
    
    # Call the function
    result = acquire_data(days=10)
    
    # Check the result
    assert result is True  # Function still returns True as it completed without errors
    
    # Check that fetch_stock_data was called
    mock_fetch_stock_data.assert_called_once()
    
    # Check that fetch_market_cap_data was called (even with empty data)
    mock_fetch_market_cap_data.assert_called_once()
    
    # Check that store_stock_data was called with empty data
    mock_store_stock_data.assert_called_once()
    args = mock_store_stock_data.call_args[0]
    assert args[0].empty  # First arg is the DataFrame, which should be empty 