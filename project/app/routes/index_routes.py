from fastapi import APIRouter, Query, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from typing import Optional
import os
import logging
from datetime import date

from app.models.models import DateRange, ExportRequest
from app.services.index_service import (
    build_index,
    get_index_performance,
    get_index_composition,
    get_composition_changes
)
from app.services.excel_service import export_data_to_excel
from app.cache.redis_cache import cache_response, invalidate_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/build-index")
async def build_index_endpoint(date_range: DateRange):
    """
    Build the index for the specified date range.
    This endpoint will construct the equal-weighted index dynamically.
    """
    try:
        # Convert dates to strings
        start_date = date_range.start_date.isoformat()
        end_date = date_range.end_date.isoformat() if date_range.end_date else None
        
        # Build the index
        result = build_index(start_date, end_date)
        
        # Invalidate caches after building the index
        invalidate_cache("index_performance")
        invalidate_cache("index_composition")
        invalidate_cache("composition_changes")
        
        return result
    except ValueError as e:
        # Check if this is the "index already exists" error
        if "Index already exists for date range" in str(e):
            logger.warning(f"Attempted to rebuild existing index: {e}")
            raise HTTPException(status_code=409, detail=str(e))
        else:
            logger.exception(f"Value error building index: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error building index: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/index-performance")
@cache_response("index_performance")
async def get_index_performance_endpoint(
    start_date: date = Query(..., description="Start date"),
    end_date: Optional[date] = Query(None, description="End date")
):
    """
    Get index performance for the specified date range.
    Returns daily returns and cumulative returns.
    """
    try:
        # Convert dates to strings
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat() if end_date else None
        
        # Get performance data
        performance = get_index_performance(start_date_str, end_date_str)
        
        if not performance:
            raise HTTPException(status_code=404, detail="No performance data found for the specified date range")
        
        return {
            "start_date": start_date_str,
            "end_date": end_date_str if end_date else date.today().isoformat(),
            "performances": performance
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting index performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/index-composition")
@cache_response("index_composition")
async def get_index_composition_endpoint(
    date: date = Query(..., description="Date for composition")
):
    """
    Get the index composition for a specific date.
    Returns the list of stocks in the index with their weights.
    """
    try:
        # Convert date to string
        date_str = date.isoformat()
        
        # Get composition data
        composition = get_index_composition(date_str)
        
        if not composition:
            raise HTTPException(status_code=404, detail=f"No composition data found for date {date}")
        
        return {
            "date": date_str,
            "compositions": composition
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting index composition: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/composition-changes")
@cache_response("composition_changes")
async def get_composition_changes_endpoint(
    start_date: date = Query(..., description="Start date"),
    end_date: Optional[date] = Query(None, description="End date")
):
    """
    Get composition changes for the specified date range.
    Returns the list of stocks that entered or exited the index.
    """
    try:
        # Convert dates to strings
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat() if end_date else None
        
        # Get changes data
        changes = get_composition_changes(start_date_str, end_date_str)
        
        return {
            "start_date": start_date_str,
            "end_date": end_date_str if end_date else date.today().isoformat(),
            "changes": changes
        }
    except Exception as e:
        logger.exception(f"Error getting composition changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export-data")
async def export_data_endpoint(
    export_request: ExportRequest,
    background_tasks: BackgroundTasks
):
    """
    Export index data to Excel.
    Returns a downloadable Excel file.
    """
    try:
        # Convert dates to strings
        start_date_str = export_request.start_date.isoformat()
        end_date_str = export_request.end_date.isoformat() if export_request.end_date else None
        
        # Export data to Excel
        file_path = export_data_to_excel(start_date_str, end_date_str)
        
        # Schedule file deletion after it's been downloaded
        def delete_file():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                # Also remove parent directory if it's empty
                parent_dir = os.path.dirname(file_path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
        
        background_tasks.add_task(delete_file)
        
        # Return the file
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logger.exception(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 