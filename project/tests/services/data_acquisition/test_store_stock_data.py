import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from app.services.data_acquisition import store_stock_data
from tests.mocks import create_mock_daily_data

@pytest.fixture
def mock_insert_many():
    """Mock insert_many database function"""
    with patch("app.services.data_acquisition.insert_many") as mock:
        mock.return_value = None
        yield mock

def test_store_stock_data_success(mock_insert_many):
    """Test successful storage of stock data"""
    # Create test data and market caps
    data = pd.DataFrame({
        "ticker": ["AAPL", "MSFT"],
        "Date": pd.to_datetime(["2023-01-15", "2023-01-15"]),
        "Open": [148.0, 248.0],
        "High": [152.0, 252.0],
        "Low": [147.0, 247.0],
        "Close": [150.0, 250.0],
        "Volume": [10000000, 8000000]
    })
    
    market_caps = {
        "AAPL": 2000000000000,
        "MSFT": 1800000000000
    }
    
    # Mock the logger to avoid actual logging in the test
    with patch("app.services.data_acquisition.logger"):
        # Call the function
        store_stock_data(data, market_caps)
        
        # Check that insert_many was called with the correct parameters
        mock_insert_many.assert_called_once()
        args = mock_insert_many.call_args[0]
        assert args[0] == "daily_data"
        assert args[1] == ["date", "ticker", "open", "high", "low", "close", "volume", "market_cap"]
        assert len(args[2]) == 2  # Two rows

def test_store_stock_data_with_missing_market_caps(mock_insert_many):
    """Test storage of data with missing market caps that need estimation"""
    # Create test data and market caps (with some missing)
    data = pd.DataFrame({
        "ticker": ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "BRK.B"],
        "Date": pd.to_datetime(["2023-01-15"] * 8),
        "Open": [148.0, 248.0, 2980.0, 1980.0, 200.0, 180.0, 400.0, 300.0],
        "High": [152.0, 252.0, 3020.0, 2020.0, 205.0, 185.0, 410.0, 310.0],
        "Low": [147.0, 247.0, 2970.0, 1970.0, 195.0, 175.0, 390.0, 290.0],
        "Close": [150.0, 250.0, 3000.0, 2000.0, 202.0, 183.0, 405.0, 305.0],
        "Volume": [10000000, 8000000, 5000000, 3000000, 7000000, 12000000, 6000000, 4000000]
    })
    
    # Only provide market caps for a small number of tickers (below the 80% threshold)
    market_caps = {
        "AAPL": 2000000000000
    }
    
    # Mock the estimate_market_cap function
    with patch("app.services.data_acquisition.estimate_market_cap") as mock_estimate, \
         patch("app.services.data_acquisition.logger"):
        # Set up the mock to return estimated market caps
        mock_estimate.return_value = {
            "MSFT": 1800000000000,
            "AMZN": 1600000000000,
            "GOOGL": 1400000000000,
            "META": 1200000000000,
            "TSLA": 1000000000000,
            "NVDA": 900000000000,
            "BRK.B": 800000000000
        }
        
        # Force the missing percentage to be above the threshold
        with patch("app.services.data_acquisition.pd.Series.isna") as mock_isna, \
             patch("app.services.data_acquisition.pd.Series.mean") as mock_mean:
            mock_isna.return_value = pd.Series([True] * 7 + [False], index=data.index)
            mock_mean.return_value = 0.875  # 7/8 missing
            
            # Call the function
            store_stock_data(data, market_caps)
            
            # Check that estimate_market_cap was called
            mock_estimate.assert_called_once()
            
            # Check that insert_many was called with the correct parameters
            mock_insert_many.assert_called_once()
            args = mock_insert_many.call_args[0]
            assert args[0] == "daily_data"
            assert args[1] == ["date", "ticker", "open", "high", "low", "close", "volume", "market_cap"]

def test_store_stock_data_empty_data():
    """Test handling of empty DataFrame"""
    # Create empty test data
    data = pd.DataFrame()
    market_caps = {}
    
    # Mock the insert_many function to ensure it's not called
    with patch("app.services.data_acquisition.insert_many") as mock_insert_many, \
         patch("app.services.data_acquisition.logger"):
        # Call the function
        store_stock_data(data, market_caps)
        
        # Check that insert_many was not called
        mock_insert_many.assert_not_called()

def test_store_stock_data_handles_insert_exception(mock_insert_many):
    """Test that the function handles exceptions from insert_many"""
    # Create test data and market caps
    data = pd.DataFrame({
        "ticker": ["AAPL"],
        "Date": pd.to_datetime(["2023-01-15"]),
        "Open": [148.0],
        "High": [152.0],
        "Low": [147.0],
        "Close": [150.0],
        "Volume": [10000000]
    })
    
    market_caps = {"AAPL": 2000000000000}
    
    # Set up the mock to raise an exception
    mock_insert_many.side_effect = Exception("Test error")
    
    # Mock the logger to avoid actual logging in the test
    with patch("app.services.data_acquisition.logger"):
        # Call the function - should not raise the exception
        store_stock_data(data, market_caps)
        
        # Check that insert_many was called
        mock_insert_many.assert_called_once()

def test_store_stock_data_handles_row_processing_error():
    """Test that the function handles errors when processing individual rows"""
    # Create test data with a problematic row (non-numeric value in a numeric column)
    data = pd.DataFrame({
        "ticker": ["AAPL", "MSFT"],
        "Date": pd.to_datetime(["2023-01-15", "2023-01-15"]),
        "Open": [148.0, "invalid"],  # Invalid type for numeric column
        "High": [152.0, 252.0],
        "Low": [147.0, 247.0],
        "Close": [150.0, 250.0],
        "Volume": [10000000, 8000000]
    })
    
    market_caps = {
        "AAPL": 2000000000000,
        "MSFT": 1800000000000
    }
    
    # Mock the logger to avoid actual logging in the test
    with patch("app.services.data_acquisition.logger"):
        # Mock the insert_many function
        with patch("app.services.data_acquisition.insert_many") as mock_insert_many:
            # Call the function
            store_stock_data(data, market_caps)
            
            # Check that insert_many was called with only the valid row
            mock_insert_many.assert_called_once()
            args = mock_insert_many.call_args[0]
            assert len(args[2]) == 1  # Only one valid row 