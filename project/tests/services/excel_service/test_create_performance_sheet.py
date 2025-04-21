import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import xlsxwriter

from app.services.excel_service import create_performance_sheet
from app.services.index_service import get_index_performance

@pytest.fixture
def mock_get_index_performance():
    with patch("app.services.excel_service.get_index_performance") as mock:
        # Create mock performance data
        mock.return_value = pd.DataFrame({
            "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
            "price": [100.0, 102.0, 101.5, 103.0, 104.5],
            "daily_return": [0.0, 0.02, -0.0049, 0.0148, 0.0146],
            "cumulative_return": [0.0, 0.02, 0.015, 0.03, 0.045]
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
    
    # Create a mock chart
    mock_chart = MagicMock()
    mock_wb.add_chart.return_value = mock_chart
    
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
        "worksheet": mock_ws,
        "chart": mock_chart
    }

def test_create_performance_sheet(mock_get_index_performance, mock_workbook):
    """Test that the create_performance_sheet function works correctly."""
    # Create a mock writer
    mock_writer = MagicMock()
    mock_writer.book = mock_workbook["workbook"]
    mock_writer.sheets = {"Performance": mock_workbook["worksheet"]}
    
    # Mock the DataFrame's to_excel method
    with patch('pandas.DataFrame.to_excel', return_value=None) as mock_to_excel:
        # Call the function
        create_performance_sheet(mock_writer, "2023-01-01", "2023-01-31")
        
        # Check that get_index_performance was called with correct parameters
        mock_get_index_performance.assert_called_once_with("2023-01-01", "2023-01-31")
        
        # Verify to_excel was called
        mock_to_excel.assert_called_once()

def test_create_performance_sheet_no_data(mock_get_index_performance, mock_workbook):
    """Test behavior when no performance data is available."""
    # Set up mock to return empty DataFrame
    mock_get_index_performance.return_value = pd.DataFrame(columns=["date", "price", "daily_return", "cumulative_return"])
    
    # Create a mock writer
    mock_writer = MagicMock()
    mock_writer.book = mock_workbook["workbook"]
    mock_writer.sheets = {"Performance": mock_workbook["worksheet"]}
    
    # Mock the DataFrame's to_excel method
    with patch('pandas.DataFrame.to_excel', return_value=None) as mock_to_excel:
        # Call the function
        create_performance_sheet(mock_writer, "2023-01-01", "2023-01-31")
        
        # Check that get_index_performance was called with correct parameters
        mock_get_index_performance.assert_called_once_with("2023-01-01", "2023-01-31")
        
        # Verify to_excel was called with an empty DataFrame
        mock_to_excel.assert_called_once() 