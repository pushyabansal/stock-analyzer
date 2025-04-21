import pandas as pd
import os
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.services.index_service import (
    get_index_performance,
    get_index_composition,
    get_composition_changes,
    get_trading_dates
)

def create_performance_sheet(writer: pd.ExcelWriter, start_date: str, end_date: Optional[str] = None) -> None:
    """Create the index performance sheet"""
    # Get performance data
    performance_data = get_index_performance(start_date, end_date)
    
    # Convert to DataFrame if not already
    if isinstance(performance_data, list) and performance_data:
        df = pd.DataFrame(performance_data)
    elif isinstance(performance_data, pd.DataFrame):
        df = performance_data
    else:
        # Create an empty sheet
        pd.DataFrame().to_excel(writer, sheet_name="Performance", index=False)
        return
    
    # Check if the DataFrame is empty
    if df.empty:
        # Create an empty sheet
        pd.DataFrame().to_excel(writer, sheet_name="Performance", index=False)
        return
    
    # Write to Excel
    df.to_excel(writer, sheet_name="Performance", index=False)
    
    # Get the workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets["Performance"]
    
    # Define formats
    date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
    percent_format = workbook.add_format({"num_format": "0.00%"})
    
    # Set column formats
    worksheet.set_column("A:A", 12, date_format)  # Date column
    worksheet.set_column("B:C", 15, percent_format)  # Return columns
    
    # Add a chart
    chart = workbook.add_chart({"type": "line"})
    
    # Add series to the chart
    chart.add_series({
        "name": "Cumulative Return",
        "categories": ["Performance", 1, 0, len(df), 0],  # Dates
        "values": ["Performance", 1, 2, len(df), 2],  # Cumulative returns
        "line": {"width": 2.25, "color": "#1F77B4"}
    })
    
    # Set chart title and labels
    chart.set_title({"name": "Index Cumulative Performance"})
    chart.set_x_axis({"name": "Date"})
    chart.set_y_axis({"name": "Return", "num_format": "0.00%"})
    
    # Insert the chart into the worksheet
    worksheet.insert_chart("E2", chart, {"x_scale": 1.5, "y_scale": 1.5})

def create_compositions_sheet(writer: pd.ExcelWriter, start_date: str, end_date: Optional[str] = None) -> None:
    """Create the index compositions sheet"""
    # Get trading dates
    dates = get_trading_dates(start_date, end_date)
    
    if not dates:
        # Create an empty sheet
        pd.DataFrame().to_excel(writer, sheet_name="Compositions", index=False)
        return
    
    # Create a list to hold all compositions
    all_compositions = []
    
    # Get composition for each date
    for date in dates:
        composition = get_index_composition(date)
        
        # Check if composition exists and is not empty
        if isinstance(composition, list) and composition:
            for item in composition:
                all_compositions.append({
                    "date": date,
                    **item
                })
        elif isinstance(composition, pd.DataFrame) and not composition.empty:
            # If it's a DataFrame, add each row
            for _, row in composition.iterrows():
                all_compositions.append({
                    "date": date,
                    **row.to_dict()
                })
    
    if not all_compositions:
        # Create an empty sheet
        pd.DataFrame().to_excel(writer, sheet_name="Compositions", index=False)
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(all_compositions)
    
    # Write to Excel
    df.to_excel(writer, sheet_name="Compositions", index=False)
    
    # Get the workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets["Compositions"]
    
    # Define formats
    date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
    percent_format = workbook.add_format({"num_format": "0.00%"})
    number_format = workbook.add_format({"num_format": "#,##0.00"})
    market_cap_format = workbook.add_format({"num_format": "#,##0"})
    
    # Set column formats
    worksheet.set_column("A:A", 12, date_format)  # Date column
    worksheet.set_column("B:B", 10)  # Ticker column
    worksheet.set_column("C:C", 30)  # Name column
    worksheet.set_column("D:D", 15)  # Sector column
    worksheet.set_column("E:E", 10, percent_format)  # Weight column
    worksheet.set_column("F:F", 12, number_format)  # Price column
    worksheet.set_column("G:G", 18, market_cap_format)  # Market Cap column

def create_changes_sheet(writer: pd.ExcelWriter, start_date: str, end_date: Optional[str] = None) -> None:
    """Create the composition changes sheet"""
    # Get changes data
    changes_data = get_composition_changes(start_date, end_date)
    
    # Convert to DataFrame if not already
    if isinstance(changes_data, list) and changes_data:
        df = pd.DataFrame(changes_data)
    elif isinstance(changes_data, pd.DataFrame):
        df = changes_data
    else:
        # Create an empty sheet
        pd.DataFrame().to_excel(writer, sheet_name="Changes", index=False)
        return
    
    # Check if the DataFrame is empty
    if df.empty:
        # Create an empty sheet
        pd.DataFrame().to_excel(writer, sheet_name="Changes", index=False)
        return
    
    # Write to Excel
    df.to_excel(writer, sheet_name="Changes", index=False)
    
    # Get the workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets["Changes"]
    
    # Define formats
    date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
    
    # Set column formats
    worksheet.set_column("A:A", 12, date_format)  # Date column
    worksheet.set_column("B:B", 10)  # Ticker column
    worksheet.set_column("C:C", 30)  # Name column
    worksheet.set_column("D:D", 15)  # Sector column
    worksheet.set_column("E:E", 10)  # Event column
    
    # Add conditional formatting for entries and exits
    worksheet.conditional_format("E2:E1000", {
        "type": "cell",
        "criteria": "equal to",
        "value": '"ENTRY"',
        "format": workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
    })
    
    worksheet.conditional_format("E2:E1000", {
        "type": "cell",
        "criteria": "equal to",
        "value": '"EXIT"',
        "format": workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
    })

def export_data_to_excel(start_date: str, end_date: Optional[str] = None, filename: Optional[str] = None, output_dir: Optional[str] = None) -> str:
    """
    Export index data to Excel and return the path to the file.
    
    Args:
        start_date (str): Start date for the data in YYYY-MM-DD format
        end_date (Optional[str], optional): End date for the data in YYYY-MM-DD format. Defaults to current date.
        filename (Optional[str], optional): Custom filename for the Excel file. Defaults to None.
        output_dir (Optional[str], optional): Custom directory for saving the Excel file. Defaults to a temporary directory.
    
    Returns:
        str: Path to the created Excel file
    """
    # Create directory to store the file (temporary or custom)
    if output_dir:
        # Create the custom directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        dir_path = output_dir
    else:
        # Create a temporary directory
        dir_path = tempfile.mkdtemp()
    
    # Create a filename with the date range or use custom filename
    if not filename:
        end_date_str = end_date or datetime.now().strftime("%Y-%m-%d")
        filename = f"stock_index_{start_date}_to_{end_date_str}.xlsx"
    
    file_path = os.path.join(dir_path, filename)
    
    # Create an Excel writer
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        # Create sheets
        create_performance_sheet(writer, start_date, end_date)
        create_compositions_sheet(writer, start_date, end_date)
        create_changes_sheet(writer, start_date, end_date)
    
    return file_path 