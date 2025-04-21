import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from app.services.data_acquisition import fetch_sp500_tickers
from tests.mocks import MOCK_STOCK_DATA

@pytest.fixture
def mock_pd_read_html():
    """Mock pandas read_html function"""
    mock = MagicMock()
    # Create a mock DataFrame with required columns
    df = pd.DataFrame(
        {
            "Symbol": ["AAPL", "MSFT", "AMZN", "GOOGL"],
            "Security": ["Apple Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Alphabet Inc."],
            "GICS Sector": ["Technology", "Technology", "Consumer Cyclical", "Communication Services"],
            "GICS Sub-Industry": ["Tech Hardware", "Software", "Internet Retail", "Internet Services"],
        }
    )
    mock.return_value = [df]
    return mock

@pytest.fixture
def mock_insert_many():
    """Mock insert_many database function"""
    with patch("app.services.data_acquisition.insert_many") as mock:
        mock.return_value = None
        yield mock

def test_fetch_sp500_tickers_success(mock_pd_read_html, mock_insert_many):
    """Test successful fetching of S&P 500 tickers"""
    # Set up the mock for pd.read_html
    with patch("pandas.read_html", mock_pd_read_html):
        # Call the function
        tickers = fetch_sp500_tickers()
        
        # Check that the function returned the expected tickers
        assert tickers == ["AAPL", "MSFT", "AMZN", "GOOGL"]
        
        # Check that insert_many was called with the correct parameters
        mock_insert_many.assert_called_once()
        args = mock_insert_many.call_args[0]
        assert args[0] == "stocks"
        assert args[1] == ["ticker", "name", "sector", "exchange"]
        assert len(args[2]) == 4

def test_fetch_sp500_tickers_handles_exception(mock_insert_many):
    """Test that the function handles exceptions gracefully"""
    # Set up the mock for pd.read_html to raise an exception
    with patch("pandas.read_html", side_effect=Exception("Test error")):
        # Call the function
        tickers = fetch_sp500_tickers()
        
        # Check that the function returns an empty list on error
        assert tickers == []
        
        # Check that insert_many was not called
        mock_insert_many.assert_not_called()

def test_fetch_sp500_tickers_handles_dots_in_symbols(mock_insert_many):
    """Test that the function correctly handles dots in ticker symbols"""
    # Create a mock DataFrame with dots in the Symbol column
    df = pd.DataFrame(
        {
            "Symbol": ["BRK.B", "BF.B"],
            "Security": ["Berkshire Hathaway Inc.", "Brown-Forman Corporation"],
            "GICS Sector": ["Financial Services", "Consumer Staples"],
            "GICS Sub-Industry": ["Multi-Sector Holdings", "Distillers & Vintners"],
        }
    )
    
    # Set up the mock for pd.read_html
    with patch("pandas.read_html", return_value=[df]):
        # Call the function
        tickers = fetch_sp500_tickers()
        
        # Check that dots are replaced with hyphens
        assert tickers == ["BRK-B", "BF-B"]
        
        # Check the values passed to insert_many
        mock_insert_many.assert_called_once()
        args = mock_insert_many.call_args[0]
        values = args[2]
        assert values[0][0] == "BRK-B"
        assert values[1][0] == "BF-B" 