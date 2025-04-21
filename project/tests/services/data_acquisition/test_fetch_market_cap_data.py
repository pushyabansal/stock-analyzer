import pytest
from unittest.mock import patch, MagicMock

from app.services.data_acquisition import fetch_market_cap_data
from tests.mocks import mock_yfinance_ticker

@pytest.fixture
def mock_yf_ticker():
    """Mock yfinance Ticker class"""
    with patch("app.services.data_acquisition.yf.Ticker", side_effect=mock_yfinance_ticker) as mock:
        yield mock

@pytest.fixture
def mock_time_sleep():
    """Mock time.sleep to avoid waiting during tests"""
    with patch("app.services.data_acquisition.time.sleep") as mock:
        yield mock

def test_fetch_market_cap_data_success(mock_yf_ticker, mock_time_sleep):
    """Test successful fetching of market cap data"""
    # Call the function
    tickers = ["AAPL", "MSFT", "AMZN", "GOOGL"]
    market_caps = fetch_market_cap_data(tickers)
    
    # Check that the function was called for each ticker
    assert mock_yf_ticker.call_count == len(tickers)
    
    # Check that we got market cap data for all tickers
    assert len(market_caps) == len(tickers)
    assert all(ticker in market_caps for ticker in tickers)
    
    # Check that time.sleep was called to avoid rate limiting
    assert mock_time_sleep.call_count >= len(tickers)  # Once per ticker at least

def test_fetch_market_cap_data_handles_exception(mock_yf_ticker, mock_time_sleep):
    """Test that the function handles exceptions gracefully"""
    # Set up the mock to raise an exception
    mock_yf_ticker.side_effect = Exception("Test error")
    
    # Call the function
    tickers = ["AAPL", "MSFT"]
    market_caps = fetch_market_cap_data(tickers)
    
    # Check that we got no market cap data
    assert len(market_caps) == 0

def test_fetch_market_cap_data_handles_missing_data(mock_time_sleep):
    """Test handling of missing market cap data in Ticker info"""
    # Create a mock Ticker with missing market cap
    mock_ticker = MagicMock()
    mock_ticker.info = {}  # No marketCap
    
    # Set up the mock to return our custom Ticker
    with patch("app.services.data_acquisition.yf.Ticker", return_value=mock_ticker):
        # Call the function
        tickers = ["AAPL"]
        market_caps = fetch_market_cap_data(tickers)
        
        # Check that we got no market cap data
        assert len(market_caps) == 0

def test_fetch_market_cap_data_handles_none_value(mock_time_sleep):
    """Test handling of None market cap value in Ticker info"""
    # Create a mock Ticker with None market cap
    mock_ticker = MagicMock()
    mock_ticker.info = {"marketCap": None}
    
    # Set up the mock to return our custom Ticker
    with patch("app.services.data_acquisition.yf.Ticker", return_value=mock_ticker):
        # Call the function
        tickers = ["AAPL"]
        market_caps = fetch_market_cap_data(tickers)
        
        # Check that we got no market cap data
        assert len(market_caps) == 0

def test_fetch_market_cap_data_with_batching(mock_yf_ticker, mock_time_sleep):
    """Test that the function correctly batches ticker requests"""
    # Create a larger list of tickers to test batching
    tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", 
               "NVDA", "BRK.B", "UNH", "JNJ", "JPM", "V"]
    
    # Call the function
    market_caps = fetch_market_cap_data(tickers)
    
    # Check that the function was called for each ticker
    assert mock_yf_ticker.call_count == len(tickers)
    
    # Check that we have more sleep calls than just one per ticker
    # This indicates batching with delays between batches
    assert mock_time_sleep.call_count > len(tickers) 