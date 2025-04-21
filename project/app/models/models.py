from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime

class DateRange(BaseModel):
    start_date: date
    end_date: Optional[date] = None

class Stock(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    exchange: Optional[str] = None

class DailyData(BaseModel):
    date: date
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    market_cap: float

class IndexComposition(BaseModel):
    date: date
    ticker: str
    weight: float

class IndexPerformance(BaseModel):
    date: date
    daily_return: float
    cumulative_return: float

class CompositionChange(BaseModel):
    date: date
    ticker: str
    event: str  # 'ENTRY' or 'EXIT'

class IndexCompositionResponse(BaseModel):
    date: date
    compositions: List[Dict[str, Any]]

class IndexPerformanceResponse(BaseModel):
    start_date: date
    end_date: date
    performances: List[Dict[str, Any]]

class CompositionChangesResponse(BaseModel):
    start_date: date
    end_date: date
    changes: List[Dict[str, Any]]

class ExportRequest(BaseModel):
    start_date: date
    end_date: Optional[date] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None 