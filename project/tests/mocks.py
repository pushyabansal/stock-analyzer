"""
Common mock objects and functions for tests.
This file contains reusable mock objects that can be shared across test modules.
"""

import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime, date

# Mock Stock Data
MOCK_STOCK_DATA = [
    ("AAPL", "Apple Inc.", "Technology", "NASDAQ"),
    ("MSFT", "Microsoft Corporation", "Technology", "NASDAQ"),
    ("AMZN", "Amazon.com Inc.", "Consumer Cyclical", "NASDAQ"),
    ("GOOGL", "Alphabet Inc.", "Communication Services", "NASDAQ"),
    ("META", "Meta Platforms Inc.", "Communication Services", "NASDAQ"),
    ("TSLA", "Tesla Inc.", "Consumer Cyclical", "NASDAQ"),
    ("BRK.B", "Berkshire Hathaway Inc.", "Financial Services", "NYSE"),
    ("UNH", "UnitedHealth Group Inc.", "Healthcare", "NYSE"),
    ("JNJ", "Johnson & Johnson", "Healthcare", "NYSE"),
    ("JPM", "JPMorgan Chase & Co.", "Financial Services", "NYSE"),
]

# Mock Daily Data
def create_mock_daily_data(date_str="2023-01-15"):
    """Create a mock daily data DataFrame with the given date"""
    data = []
    
    # Create data for 10 stocks
    for i, ticker in enumerate([
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", 
        "TSLA", "BRK.B", "UNH", "JNJ", "JPM"
    ]):
        # Decreasing market cap so we have a clear order
        market_cap = 2_000_000_000_000 - (i * 100_000_000_000)
        price = 100 + (i * 10)
        
        data.append({
            "date": date_str,
            "ticker": ticker,
            "open": price - 2,
            "high": price + 5,
            "low": price - 5,
            "close": price,
            "volume": 10_000_000 + (i * 1_000_000),
            "market_cap": market_cap
        })
    
    return pd.DataFrame(data)

# Mock for DB Function
class MockDBFunctions:
    """Mock class for database functions"""
    @staticmethod
    def execute_query_side_effect(query, params=None):
        """Mock side effect for execute_query"""
        if "SELECT DISTINCT date" in query:
            return [("2023-01-15",), ("2023-01-16",)]
        elif "SELECT ticker FROM stocks" in query:
            return [("AAPL",), ("MSFT",), ("AMZN",), ("GOOGL",)]
        elif "SELECT ticker FROM index_composition" in query:
            return [("AAPL",), ("MSFT",), ("AMZN",)]
        elif "SELECT COUNT(*)" in query:
            return [(0,)]  # For index_exists_for_range
        else:
            return []

    @staticmethod
    def execute_pandas_query_side_effect(query, params=None):
        """Mock side effect for execute_pandas_query"""
        if "SELECT ticker, market_cap, close FROM daily_data" in query:
            return pd.DataFrame({
                "ticker": ["AAPL", "MSFT", "AMZN", "GOOGL"],
                "market_cap": [2000000000000, 1800000000000, 1600000000000, 1400000000000],
                "close": [150.0, 300.0, 3000.0, 2000.0]
            })
        elif "SELECT ic.ticker, ic.weight" in query:
            return pd.DataFrame({
                "ticker": ["AAPL", "MSFT", "AMZN", "GOOGL"],
                "weight": [0.25, 0.25, 0.25, 0.25],
                "name": ["Apple Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Alphabet Inc."],
                "sector": ["Technology", "Technology", "Consumer Cyclical", "Communication Services"],
                "close": [150.0, 300.0, 3000.0, 2000.0],
                "market_cap": [2000000000000, 1800000000000, 1600000000000, 1400000000000]
            })
        elif "SELECT date, daily_return, cumulative_return" in query:
            return pd.DataFrame({
                "date": pd.to_datetime(["2023-01-15", "2023-01-16"]),
                "daily_return": [0.01, 0.02],
                "cumulative_return": [0.01, 0.0302]
            })
        elif "SELECT cc.date, cc.ticker" in query:
            return pd.DataFrame({
                "date": pd.to_datetime(["2023-01-16", "2023-01-16"]),
                "ticker": ["META", "JNJ"],
                "event": ["ENTRY", "EXIT"],
                "name": ["Meta Platforms Inc.", "Johnson & Johnson"],
                "sector": ["Communication Services", "Healthcare"]
            })
        else:
            return pd.DataFrame()

# Mock Data for Excel Testing
class MockXlsxWriter:
    """A mock class to avoid file system operations in tests"""
    def __init__(self, *args, **kwargs):
        self.filename = "mock.xlsx"
        self.sheets = {}
        self.book = MagicMock()
        self.book.add_format.return_value = MagicMock()
        self.book.add_chart.return_value = MagicMock()
        self.sheets = {
            "Performance": MagicMock(),
            "Compositions": MagicMock(),
            "Changes": MagicMock()
        }
        
    def close(self):
        pass

# Mock Data for service functions
def mock_yfinance_ticker(ticker):
    """Create a mock for yfinance Ticker object"""
    mock_ticker = MagicMock()
    mock_ticker.info = {
        'marketCap': 2_000_000_000_000 - (ord(ticker[0]) % 10) * 100_000_000_000,
        'shortName': f"{ticker} Inc.",
        'sector': "Technology",
        'industry': "Software",
    }
    return mock_ticker

def mock_download_data(tickers, start=None, end=None, group_by=None):
    """Create mock for yfinance download data"""
    # If a single ticker is provided as a string
    if isinstance(tickers, str) and " " not in tickers:
        # Create single-ticker format
        df = pd.DataFrame({
            'Open': [150.0, 152.0],
            'High': [155.0, 157.0],
            'Low': [148.0, 151.0],
            'Close': [153.0, 156.0],
            'Volume': [10000000, 12000000],
        }, index=pd.DatetimeIndex(['2023-01-15', '2023-01-16'], name='Date'))
        return df
    
    # For multiple tickers
    tickers_list = tickers.split() if isinstance(tickers, str) else tickers
    multi_df = pd.MultiIndex.from_product(
        [tickers_list, ['Open', 'High', 'Low', 'Close', 'Volume']],
        names=['Ticker', 'Data']
    )
    
    data = {}
    dates = pd.DatetimeIndex(['2023-01-15', '2023-01-16'], name='Date')
    
    for ticker in tickers_list:
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col == 'Volume':
                data[(ticker, col)] = [10000000, 12000000]
            else:
                base = 100 + ord(ticker[0]) % 10 * 10
                data[(ticker, col)] = [base, base + 3]
                
    return pd.DataFrame(data, index=dates)

# Mock redis client
class MockRedisClient:
    """Mock Redis client for testing cache functions"""
    def __init__(self, available=True):
        self.data = {}
        self.available = available
        
    def ping(self):
        if not self.available:
            raise Exception("Redis not available")
        return True
        
    def get(self, key):
        if not self.available:
            raise Exception("Redis not available")
        return self.data.get(key)
        
    def setex(self, key, time, value):
        if not self.available:
            raise Exception("Redis not available")
        self.data[key] = value
        
    def delete(self, *keys):
        if not self.available:
            raise Exception("Redis not available")
        for key in keys:
            if key in self.data:
                del self.data[key]
                
    def keys(self, pattern):
        if not self.available:
            raise Exception("Redis not available")
        # Very simplified pattern matching
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return [k for k in self.data.keys() if k.startswith(prefix)]
        return [] 