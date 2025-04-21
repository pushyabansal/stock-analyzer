import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import xlsxwriter

from app.services.excel_service import create_compositions_sheet
from app.services.index_service import get_trading_dates, get_index_composition

@pytest.fixture
def mock_get_trading_dates():
    with patch("app.services.excel_service.get_trading_dates") as mock:
        # Create mock trading dates
        mock.return_value = ["2023-01-01", "2023-01-15", "2023-02-01"]
        yield mock

@pytest.fixture
def mock_get_index_composition():
    with patch("app.services.excel_service.get_index_composition") as mock:
        # Define a side effect function to return different compositions based on date
        def side_effect(date):
            compositions = {
                "2023-01-01": pd.DataFrame({
                    "ticker": ["AAPL", "MSFT", "GOOG"],
                    "weight": [0.4, 0.35, 0.25],
                    "market_cap": [2500000000000, 2000000000000, 1500000000000]
                }),
                "2023-01-15": pd.DataFrame({
                    "ticker": ["AAPL", "GOOG", "AMZN"],
                    "weight": [0.45, 0.3, 0.25],
                    "market_cap": [2600000000000, 1600000000000, 1400000000000]
                }),
                "2023-02-01": pd.DataFrame({
                    "ticker": ["AAPL", "GOOG", "META"],
                    "weight": [0.4, 0.35, 0.25],
                    "market_cap": [2700000000000, 1700000000000, 1000000000000]
                })
            }
            return compositions.get(date, pd.DataFrame(columns=["ticker", "weight", "market_cap"]))
            
        mock.side_effect = side_effect
        yield mock

@pytest.fixture
def mock_workbook():
    """Create a mock Excel workbook and worksheet."""
    # Create a mock workbook
    mock_wb = MagicMock(spec=xlsxwriter.Workbook)
    
    # Create a mock worksheet
    mock_ws = MagicMock()
    mock_wb.add_worksheet.return_value = mock_ws
    
    # Create mock formats
    mock_formats = {}
    
    def add_format_side_effect(params=None):
        if params is None:
            params = {}
        format_key = str(params)
        if format_key not in mock_formats:
            mock_formats[format_key] = MagicMock()
        return mock_formats[format_key]
    
    mock_wb.add_format.side_effect = add_format_side_effect
    
    return {
        "workbook": mock_wb,
        "worksheet": mock_ws
    }

def test_create_compositions_sheet(mock_get_trading_dates, mock_get_index_composition, mock_workbook):
    """Test that the create_compositions_sheet function works correctly."""
    # Create a mock writer
    mock_writer = MagicMock()
    mock_writer.book = mock_workbook["workbook"]
    mock_writer.sheets = {"Compositions": mock_workbook["worksheet"]}
    
    # Mock the DataFrame's to_excel method
    with patch('pandas.DataFrame.to_excel', return_value=None) as mock_to_excel:
        # Call the function
        create_compositions_sheet(mock_writer, "2023-01-01", "2023-02-28")
        
        # Check that get_trading_dates was called with correct parameters
        mock_get_trading_dates.assert_called_once_with("2023-01-01", "2023-02-28")
        
        # Check that get_index_composition was called for each date
        assert mock_get_index_composition.call_count == len(mock_get_trading_dates.return_value)
        
        # Verify to_excel was called
        mock_to_excel.assert_called_once()

def test_create_compositions_sheet_no_trading_dates(mock_get_trading_dates, mock_get_index_composition, mock_workbook):
    """Test behavior when no trading dates are available."""
    # Set up mock to return empty list
    mock_get_trading_dates.return_value = []
    
    # Create a mock writer
    mock_writer = MagicMock()
    mock_writer.book = mock_workbook["workbook"]
    mock_writer.sheets = {"Compositions": mock_workbook["worksheet"]}
    
    # Mock the DataFrame's to_excel method
    with patch('pandas.DataFrame.to_excel', return_value=None) as mock_to_excel:
        # Call the function
        create_compositions_sheet(mock_writer, "2023-01-01", "2023-02-28")
        
        # Check that get_trading_dates was called with correct parameters
        mock_get_trading_dates.assert_called_once_with("2023-01-01", "2023-02-28")
        
        # Check that get_index_composition was not called (since there are no dates)
        mock_get_index_composition.assert_not_called()
        
        # Verify to_excel was called with an empty DataFrame
        mock_to_excel.assert_called_once()
