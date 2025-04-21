import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.db.database import execute_pandas_query, insert_many, execute_query

logger = logging.getLogger(__name__)

def get_trading_dates(start_date: str, end_date: Optional[str] = None) -> List[str]:
    """Get all trading dates in the specified range"""
    query = """
    SELECT DISTINCT date
    FROM daily_data
    WHERE date >= ?
    """
    
    params = [start_date]
    
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " ORDER BY date"
    
    result = execute_query(query, params)
    return [row[0] for row in result]

def get_top_stocks_by_market_cap(date: str, limit: int = 100) -> pd.DataFrame:
    """Get the top stocks by market cap for a specific date"""
    query = """
    SELECT ticker, market_cap, close
    FROM daily_data
    WHERE date = ?
    ORDER BY market_cap DESC
    LIMIT ?
    """
    
    return execute_pandas_query(query, (date, limit))

def calculate_index_weights(date: str) -> pd.DataFrame:
    """Calculate equal weights for the index constituents on a specific date"""
    top_stocks = get_top_stocks_by_market_cap(date)
    
    if top_stocks.empty:
        logger.warning(f"No stocks found for date {date}")
        return pd.DataFrame()
    
    # Calculate equal weights
    num_stocks = len(top_stocks)
    weight = 1.0 / num_stocks
    
    # Create a DataFrame with weights
    weights_df = top_stocks.copy()
    weights_df['weight'] = weight
    weights_df['date'] = date
    
    return weights_df[['date', 'ticker', 'weight']]

def store_index_composition(compositions: pd.DataFrame) -> None:
    """Store index compositions in the database"""
    if compositions.empty:
        return
    
    # Prepare data for insertion
    values = []
    for _, row in compositions.iterrows():
        values.append((
            row['date'],
            row['ticker'],
            row['weight']
        ))
    
    # Insert into database
    insert_many('index_composition', ['date', 'ticker', 'weight'], values)

def calculate_daily_returns(start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
    """Calculate daily returns for the index"""
    trading_dates = get_trading_dates(start_date, end_date)
    
    if not trading_dates:
        logger.warning(f"No trading dates found between {start_date} and {end_date}")
        return pd.DataFrame()
    
    daily_returns = []
    prev_composition = None
    cumulative_return = 1.0
    
    for i, date in enumerate(trading_dates):
        # Get the index composition for this date
        composition = get_top_stocks_by_market_cap(date)
        
        if composition.empty:
            logger.warning(f"No composition found for date {date}")
            continue
        
        # Store the composition
        weights_df = calculate_index_weights(date)
        store_index_composition(weights_df)
        
        # Skip return calculation for the first day
        if i == 0 or prev_composition is None:
            prev_composition = composition
            continue
        
        # Calculate the return compared to the previous day
        # In a real scenario, we'd need to adjust for changes in the index composition
        # This is a simplified version that assumes constant weights
        return_value = 0.0
        weight = 1.0 / len(composition)
        
        # Merge current and previous compositions to calculate returns
        merged = pd.merge(
            composition[['ticker', 'close']],
            prev_composition[['ticker', 'close']],
            on='ticker',
            how='inner',
            suffixes=('', '_prev')
        )
        
        if not merged.empty:
            # Calculate weighted returns
            merged['return'] = (merged['close'] / merged['close_prev'] - 1.0)
            return_value = (merged['return'] * weight).sum()
        
        cumulative_return *= (1.0 + return_value)
        
        daily_returns.append({
            'date': date,
            'daily_return': float(return_value),
            'cumulative_return': float(cumulative_return - 1.0)  # Convert to percentage gain/loss
        })
        
        prev_composition = composition
    
    return pd.DataFrame(daily_returns)

def store_index_performance(performance: pd.DataFrame) -> None:
    """Store index performance in the database"""
    if performance.empty:
        return
    
    # Prepare data for insertion
    values = []
    for _, row in performance.iterrows():
        values.append((
            row['date'],
            row['daily_return'],
            row['cumulative_return']
        ))
    
    # Insert into database
    insert_many('index_performance', ['date', 'daily_return', 'cumulative_return'], values)

def detect_composition_changes(start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
    """Detect changes in the index composition over time"""
    trading_dates = get_trading_dates(start_date, end_date)
    
    if len(trading_dates) < 2:
        logger.warning("Need at least two trading dates to detect changes")
        return pd.DataFrame()
    
    changes = []
    prev_tickers = set()
    
    for date in trading_dates:
        # Get the composition for this date
        query = """
        SELECT ticker
        FROM index_composition
        WHERE date = ?
        """
        
        result = execute_query(query, (date,))
        current_tickers = set(row[0] for row in result)
        
        if prev_tickers:
            # Detect entries (new stocks in the index)
            entries = current_tickers - prev_tickers
            for ticker in entries:
                changes.append({
                    'date': date,
                    'ticker': ticker,
                    'event': 'ENTRY'
                })
            
            # Detect exits (stocks removed from the index)
            exits = prev_tickers - current_tickers
            for ticker in exits:
                changes.append({
                    'date': date,
                    'ticker': ticker,
                    'event': 'EXIT'
                })
        
        prev_tickers = current_tickers
    
    # Store changes in the database
    if changes:
        values = [(change['date'], change['ticker'], change['event']) for change in changes]
        insert_many('composition_changes', ['date', 'ticker', 'event'], values)
    
    return pd.DataFrame(changes)

def index_exists_for_range(start_date: str, end_date: Optional[str] = None) -> bool:
    """
    Check if index data already exists for the specified date range.
    Returns True if data exists, False otherwise.
    """
    try:
        query = """
        SELECT COUNT(*) as count
        FROM index_performance
        WHERE date >= ?
        """
        
        params = [start_date]
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        result = execute_query(query, params)
        count = result[0][0] if result else 0
        
        return count > 0
    except Exception as e:
        logger.error(f"Error checking index existence: {e}")
        return False

def build_index(start_date: str, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Build the index for the specified date range.
    This function orchestrates the entire index building process.
    """
    logger.info(f"Building index from {start_date} to {end_date or 'present'}")
    
    # Check if index already exists for this date range
    if index_exists_for_range(start_date, end_date):
        logger.warning(f"Index already exists for date range {start_date} to {end_date or 'present'}")
        raise ValueError(f"Index already exists for date range {start_date} to {end_date or 'present'}")
    
    try:
        # Calculate daily returns
        performance = calculate_daily_returns(start_date, end_date)
        
        # Store performance data
        store_index_performance(performance)
        
        # Detect composition changes
        changes = detect_composition_changes(start_date, end_date)
        
        # Return summary
        return {
            'start_date': start_date,
            'end_date': end_date or datetime.now().strftime('%Y-%m-%d'),
            'trading_days': len(performance),
            'composition_changes': len(changes)
        }
    
    except Exception as e:
        logger.exception(f"Error building index: {e}")
        raise

def get_index_performance(start_date: str, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get index performance for the specified date range"""
    query = """
    SELECT date, daily_return, cumulative_return
    FROM index_performance
    WHERE date >= ?
    """
    
    params = [start_date]
    
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " ORDER BY date"
    
    df = execute_pandas_query(query, params)
    
    if df.empty:
        return []
    
    # Convert to list of dicts
    result = []
    for _, row in df.iterrows():
        result.append({
            'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], datetime) else row['date'],
            'daily_return': float(row['daily_return']),
            'cumulative_return': float(row['cumulative_return'])
        })
    
    return result

def get_index_composition(date: str) -> List[Dict[str, Any]]:
    """Get the index composition for a specific date"""
    query = """
    SELECT ic.ticker, ic.weight, s.name, s.sector, dd.close, dd.market_cap
    FROM index_composition ic
    JOIN stocks s ON ic.ticker = s.ticker
    JOIN daily_data dd ON ic.ticker = dd.ticker AND ic.date = dd.date
    WHERE ic.date = ?
    ORDER BY dd.market_cap DESC
    """
    
    df = execute_pandas_query(query, (date,))
    
    if df.empty:
        return []
    
    # Convert to list of dicts
    result = []
    for _, row in df.iterrows():
        result.append({
            'ticker': row['ticker'],
            'name': row['name'],
            'sector': row['sector'],
            'weight': float(row['weight']),
            'price': float(row['close']),
            'market_cap': float(row['market_cap'])
        })
    
    return result

def get_composition_changes(start_date: str, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get composition changes for the specified date range"""
    query = """
    SELECT cc.date, cc.ticker, cc.event, s.name, s.sector
    FROM composition_changes cc
    JOIN stocks s ON cc.ticker = s.ticker
    WHERE cc.date >= ?
    """
    
    params = [start_date]
    
    if end_date:
        query += " AND cc.date <= ?"
        params.append(end_date)
    
    query += " ORDER BY cc.date, cc.event"
    
    df = execute_pandas_query(query, params)
    
    if df.empty:
        return []
    
    # Convert to list of dicts
    result = []
    for _, row in df.iterrows():
        result.append({
            'date': row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], datetime) else row['date'],
            'ticker': row['ticker'],
            'name': row['name'],
            'sector': row['sector'],
            'event': row['event']
        })
    
    return result 