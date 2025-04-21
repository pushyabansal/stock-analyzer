import pytest
import os
import pandas as pd
from unittest.mock import patch, MagicMock
import tempfile
from datetime import datetime

from app.services.excel_service import export_data_to_excel
from tests.mocks import MockXlsxWriter

@pytest.fixture
def mock_tempfile_mkdtemp():
    """Mock tempfile.mkdtemp to avoid creating actual directories"""
    with patch("tempfile.mkdtemp") as mock:
        mock.return_value = "/tmp/mock_temp_dir"
        yield mock

@pytest.fixture
def mock_pd_excelwriter():
    """Mock pandas ExcelWriter to avoid creating actual Excel files"""
    mock_writer = MagicMock()
    mock_writer.__enter__ = MagicMock(return_value=mock_writer)
    mock_writer.__exit__ = MagicMock(return_value=None)
    mock_writer.book = MagicMock()
    mock_writer.sheets = {
        "Performance": MagicMock(),
        "Compositions": MagicMock(),
        "Changes": MagicMock()
    }
    
    with patch("pandas.ExcelWriter", return_value=mock_writer) as mock_excelwriter:
        yield mock_excelwriter, mock_writer

@pytest.fixture
def mock_create_performance_sheet():
    """Mock create_performance_sheet function"""
    with patch("app.services.excel_service.create_performance_sheet") as mock:
        yield mock

@pytest.fixture
def mock_create_compositions_sheet():
    """Mock create_compositions_sheet function"""
    with patch("app.services.excel_service.create_compositions_sheet") as mock:
        yield mock

@pytest.fixture
def mock_create_changes_sheet():
    """Mock create_changes_sheet function"""
    with patch("app.services.excel_service.create_changes_sheet") as mock:
        yield mock

@pytest.fixture
def mock_excel_functions():
    """Mock all the Excel sheet creation functions and pandas Excel writer."""
    with patch("app.services.excel_service.create_performance_sheet") as mock_performance, \
         patch("app.services.excel_service.create_compositions_sheet") as mock_compositions, \
         patch("app.services.excel_service.create_changes_sheet") as mock_changes, \
         patch("pandas.ExcelWriter") as mock_writer, \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs") as mock_makedirs, \
         patch("tempfile.mkdtemp", return_value="/tmp/mock_temp_dir"):
        
        # Set up mock ExcelWriter to return a context manager
        mock_writer_instance = MagicMock()
        mock_writer.return_value.__enter__.return_value = mock_writer_instance
        
        yield {
            "create_performance_sheet": mock_performance,
            "create_compositions_sheet": mock_compositions,
            "create_changes_sheet": mock_changes,
            "excel_writer": mock_writer,
            "writer_instance": mock_writer_instance,
            "makedirs": mock_makedirs
        }

def test_export_data_to_excel_success(
    mock_tempfile_mkdtemp,
    mock_pd_excelwriter,
    mock_create_performance_sheet,
    mock_create_compositions_sheet,
    mock_create_changes_sheet
):
    """Test successful export of data to Excel"""
    mock_excelwriter, mock_writer = mock_pd_excelwriter
    
    # Call the function
    file_path = export_data_to_excel("2023-01-01", "2023-01-31")
    
    # Check that a temporary directory was created
    mock_tempfile_mkdtemp.assert_called_once()
    
    # Check that ExcelWriter was created with the correct file path
    expected_file_path = "/tmp/mock_temp_dir/stock_index_2023-01-01_to_2023-01-31.xlsx"
    mock_excelwriter.assert_called_once_with(expected_file_path, engine="xlsxwriter")
    
    # Check that all three sheet creation functions were called
    mock_create_performance_sheet.assert_called_once_with(mock_writer, "2023-01-01", "2023-01-31")
    mock_create_compositions_sheet.assert_called_once_with(mock_writer, "2023-01-01", "2023-01-31")
    mock_create_changes_sheet.assert_called_once_with(mock_writer, "2023-01-01", "2023-01-31")
    
    # Check that the correct file path was returned
    assert file_path == expected_file_path

def test_export_data_to_excel_with_only_start_date(
    mock_tempfile_mkdtemp,
    mock_pd_excelwriter,
    mock_create_performance_sheet,
    mock_create_compositions_sheet,
    mock_create_changes_sheet
):
    """Test export_data_to_excel with only start_date parameter"""
    mock_excelwriter, mock_writer = mock_pd_excelwriter
    
    # Mock datetime.now to return a fixed date
    mock_now = datetime(2023, 1, 31)
    with patch("app.services.excel_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_now
        
        # Call the function with only start_date
        file_path = export_data_to_excel("2023-01-01")
        
        # Check that the filename includes the current date
        expected_file_path = "/tmp/mock_temp_dir/stock_index_2023-01-01_to_2023-01-31.xlsx"
        mock_excelwriter.assert_called_once_with(expected_file_path, engine="xlsxwriter")
        
        # Check that the sheet creation functions were called with correct parameters
        mock_create_performance_sheet.assert_called_once_with(mock_writer, "2023-01-01", None)
        mock_create_compositions_sheet.assert_called_once_with(mock_writer, "2023-01-01", None)
        mock_create_changes_sheet.assert_called_once_with(mock_writer, "2023-01-01", None)

def test_export_data_to_excel_file_path_format(mock_tempfile_mkdtemp, mock_pd_excelwriter):
    """Test that the correct file path is generated"""
    mock_excelwriter, _ = mock_pd_excelwriter
    
    # Mock the sheet creation functions to do nothing
    with patch("app.services.excel_service.create_performance_sheet"), \
         patch("app.services.excel_service.create_compositions_sheet"), \
         patch("app.services.excel_service.create_changes_sheet"):
        
        # Call the function with different date formats
        file_path = export_data_to_excel("2023-01-01", "2023-12-31")
        
        # Check that the filename contains the dates and proper format
        assert "stock_index_2023-01-01_to_2023-12-31.xlsx" in file_path 

def test_export_data_to_excel(mock_excel_functions):
    """Test the export_data_to_excel function with default parameters."""
    start_date = "2023-01-01"
    end_date = "2023-03-31"
    
    # Call the function
    result = export_data_to_excel(start_date, end_date)
    
    # Verify the temp directory was used
    assert "/tmp/mock_temp_dir" in result
    
    # Check that each sheet creation function was called once with the writer instance
    mock_excel_functions["create_performance_sheet"].assert_called_once()
    mock_excel_functions["create_compositions_sheet"].assert_called_once()
    mock_excel_functions["create_changes_sheet"].assert_called_once()
    
    # Verify parameters for each sheet creation function
    for mock_fn in ["create_performance_sheet", "create_compositions_sheet", "create_changes_sheet"]:
        args, kwargs = mock_excel_functions[mock_fn].call_args
        # First arg should be the writer instance
        assert args[0] == mock_excel_functions["writer_instance"]
        # Check that dates were passed correctly
        assert start_date in args or start_date in kwargs.values()
        assert end_date in args or end_date in kwargs.values()

def test_export_data_to_excel_custom_filename(mock_excel_functions):
    """Test export_data_to_excel with a custom filename."""
    start_date = "2023-01-01"
    end_date = "2023-03-31"
    custom_filename = "custom_index_report.xlsx"
    
    # Call the function with custom filename
    result = export_data_to_excel(start_date, end_date, filename=custom_filename)
    
    # Verify the custom filename was used
    assert custom_filename in result
    
    # Check that each sheet creation function was called once
    mock_excel_functions["create_performance_sheet"].assert_called_once()
    mock_excel_functions["create_compositions_sheet"].assert_called_once()
    mock_excel_functions["create_changes_sheet"].assert_called_once()

def test_export_data_to_excel_custom_directory(mock_excel_functions):
    """Test export_data_to_excel with a custom output directory."""
    start_date = "2023-01-01"
    end_date = "2023-03-31"
    custom_directory = "/custom/output/directory"
    
    # Call the function with custom directory
    result = export_data_to_excel(start_date, end_date, output_dir=custom_directory)
    
    # Verify the custom directory was used
    assert custom_directory in result
    
    # Check that the directory was created
    mock_excel_functions["makedirs"].assert_called_once_with(custom_directory, exist_ok=True)
    
    # Check that each sheet creation function was called once
    mock_excel_functions["create_performance_sheet"].assert_called_once()
    mock_excel_functions["create_compositions_sheet"].assert_called_once()
    mock_excel_functions["create_changes_sheet"].assert_called_once() 