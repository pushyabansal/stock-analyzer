import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import xlsxwriter

from app.services.excel_service import create_changes_sheet
from app.services.index_service import get_composition_changes

@pytest.fixture
def mock_get_composition_changes():
    with patch("app.services.excel_service.get_composition_changes") as mock:
        # Create mock changes data
        mock.return_value = pd.DataFrame({
            "date": ["2023-01-15", "2023-01-15", "2023-02-01", "2023-02-01"],
            "ticker": ["AAPL", "GOOG", "MSFT", "AMZN"],
            "change_type": ["entry", "exit", "entry", "exit"],
            "market_cap": [2500000000000, 1800000000000, 1900000000000, 1700000000000]
        })
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

def test_create_changes_sheet(mock_get_composition_changes, mock_workbook):
    """Test that the create_changes_sheet function works correctly."""
    # Create a mock writer
    mock_writer = MagicMock()
    mock_writer.book = mock_workbook["workbook"]
    mock_writer.sheets = {"Changes": mock_workbook["worksheet"]}
    
    # Mock the DataFrame's to_excel method
    with patch('pandas.DataFrame.to_excel', return_value=None) as mock_to_excel:
        # Call the function
        create_changes_sheet(mock_writer, "2023-01-01", "2023-02-28")
        
        # Check that get_composition_changes was called with correct parameters
        mock_get_composition_changes.assert_called_once_with("2023-01-01", "2023-02-28")
        
        # Verify to_excel was called
        mock_to_excel.assert_called_once()

def test_create_changes_sheet_no_changes(mock_get_composition_changes, mock_workbook):
    """Test behavior when no composition changes are available."""
    # Set up mock to return empty DataFrame
    mock_get_composition_changes.return_value = pd.DataFrame(columns=["date", "ticker", "change_type", "market_cap"])
    
    # Create a mock writer
    mock_writer = MagicMock()
    mock_writer.book = mock_workbook["workbook"]
    mock_writer.sheets = {"Changes": mock_workbook["worksheet"]}
    
    # Mock the DataFrame's to_excel method
    with patch('pandas.DataFrame.to_excel', return_value=None) as mock_to_excel:
        # Call the function
        create_changes_sheet(mock_writer, "2023-01-01", "2023-02-28")
        
        # Check that get_composition_changes was called with correct parameters
        mock_get_composition_changes.assert_called_once_with("2023-01-01", "2023-02-28")
        
        # Verify to_excel was called with an empty DataFrame
        mock_to_excel.assert_called_once() 