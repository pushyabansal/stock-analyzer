import yfinance as yf
import pandas as pd
import polars as pl
import numpy as np
from datetime import datetime, timedelta
import logging
import time

from app.db.database import insert_many, execute_query, execute_pandas_query

logger = logging.getLogger(__name__)

def fetch_sp500_tickers():
    """
    Fetch S&P 500 tickers as a representative list of major US stocks.
    In a production environment, this would come from a more comprehensive source.
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df['Symbol'].str.replace('.', '-').tolist()
        company_data = df[['Symbol', 'Security', 'GICS Sector', 'GICS Sub-Industry']].copy()
        company_data['Symbol'] = company_data['Symbol'].str.replace('.', '-')
        
        # Insert stock metadata into database
        values = []
        for _, row in company_data.iterrows():
            values.append((row['Symbol'], row['Security'], row['GICS Sector'], 'NYSE/NASDAQ'))
        
        insert_many('stocks', ['ticker', 'name', 'sector', 'exchange'], values)
        
        return tickers
    except Exception as e:
        logger.error(f"Error fetching S&P 500 tickers: {e}")
        return []

def get_all_tickers():
    """Get all tickers from the database"""
    try:
        results = execute_query("SELECT ticker FROM stocks")
        return [row[0] for row in results]
    except Exception as e:
        logger.error(f"Error fetching tickers from database: {e}")
        return []

def fetch_stock_data(tickers, start_date, end_date):
    """
    Fetch historical stock data from Yahoo Finance for the specified tickers and date range.
    """
    if not tickers:
        logger.warning("No tickers provided")
        return pd.DataFrame()
    
    all_data = []
    
    # Split tickers into chunks to avoid API rate limits
    chunk_size = 50
    ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
    
    for chunk in ticker_chunks:
        try:
            tickers_str = " ".join(chunk)
            data = yf.download(tickers_str, start=start_date, end=end_date, group_by='ticker')
            
            if len(chunk) == 1:
                # Special handling for single ticker
                ticker = chunk[0]
                if data.empty:
                    continue
                
                df = data.copy()
                df.columns = df.columns.droplevel(0)
                df['ticker'] = ticker
                all_data.append(df.reset_index())
            else:
                # Multiple tickers
                for ticker in chunk:
                    if ticker not in data.columns.levels[0]:
                        continue
                    
                    ticker_data = data[ticker].copy()
                    ticker_data['ticker'] = ticker
                    all_data.append(ticker_data.reset_index())
        
        except Exception as e:
            logger.error(f"Error fetching data for chunk {chunk}: {e}")
    
    if not all_data:
        logger.warning("No data fetched from Yahoo Finance")
        return pd.DataFrame()
    
    # Combine all data into a single DataFrame
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Calculate market cap (shares outstanding * close price)
    # In a real scenario, we'd get accurate shares outstanding data from an API
    # For simplicity, we'll fetch market cap data separately
    return combined_data

def fetch_market_cap_data(tickers):
    """Fetch current market cap data for all tickers"""
    market_caps = {}
    
    logger.info(f"Fetching market cap data for {len(tickers)} tickers")
    
    # Process tickers in small batches to avoid rate limiting
    batch_size = 5
    batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
    
    for batch_index, batch in enumerate(batches):
        logger.info(f"Processing market cap batch {batch_index + 1}/{len(batches)}")
        
        for ticker in batch:
            try:
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                if 'marketCap' in info and info['marketCap'] is not None:
                    market_caps[ticker] = info['marketCap']
                    logger.info(f"Successfully fetched market cap for {ticker}: {market_caps[ticker]}")
            except Exception as e:
                logger.error(f"Error fetching market cap for {ticker}: {e}")
            
            # Add a delay to avoid rate limiting
            time.sleep(0.5)
        
        # Add a longer delay between batches
        if batch_index < len(batches) - 1:
            logger.info(f"Sleeping between batches to avoid rate limiting")
            time.sleep(2)
    
    logger.info(f"Successfully fetched market cap data for {len(market_caps)} out of {len(tickers)} tickers")
    return market_caps

def estimate_market_cap(data):
    """
    Fallback method to estimate market cap using price data and average volume.
    This is a rough approximation and should only be used when API data is unavailable.
    """
    logger.info("Using price data to estimate market caps")
    
    estimated_caps = {}
    
    # Group by ticker and calculate average values
    for ticker, group in data.groupby('ticker'):
        try:
            # Use a simplistic model: avg_price * avg_volume * 100 as a rough estimate
            avg_price = group['Close'].mean()
            avg_volume = group['Volume'].mean()
            # This is a very simplistic approach; in a real scenario you'd want to use actual shares outstanding
            estimated_market_cap = avg_price * avg_volume * 100
            estimated_caps[ticker] = estimated_market_cap
        except Exception as e:
            logger.error(f"Error estimating market cap for {ticker}: {e}")
    
    logger.info(f"Estimated market caps for {len(estimated_caps)} tickers")
    return estimated_caps

def store_stock_data(data, market_caps):
    """Store stock data in the database"""
    if data.empty:
        logger.warning("No data to store")
        return
    
    logger.info(f"Original data shape: {data.shape}")
    
    # Add market cap to the data
    data['market_cap'] = data.apply(
        lambda row: market_caps.get(row['ticker'], np.nan), axis=1
    )
    
    logger.info(f"Market caps retrieved: {len(market_caps)}")
    
    # Check if we have enough market cap data
    missing_pct = data['market_cap'].isna().mean() * 100
    logger.info(f"Percentage of rows with missing market cap: {missing_pct:.2f}%")
    
    # If most market caps are missing, use our estimation approach
    if missing_pct > 80:
        logger.warning("Most market caps are missing. Using estimation method.")
        estimated_caps = estimate_market_cap(data)
        data['market_cap'] = data.apply(
            lambda row: market_caps.get(row['ticker']) or estimated_caps.get(row['ticker'], np.nan), 
            axis=1
        )
        logger.info(f"After estimation, market caps retrieved: {len(estimated_caps)}")
    
    # Filter out rows with missing market cap
    data = data.dropna(subset=['market_cap'])
    
    logger.info(f"Data shape after filtering by market cap: {data.shape}")
    
    if data.empty:
        logger.warning("All data was filtered out due to missing market cap")
        return
    
    # Prepare data for insertion
    values = []
    for _, row in data.iterrows():
        try:
            values.append((
                row['Date'].strftime('%Y-%m-%d'),
                row['ticker'],
                float(row['Open']),
                float(row['High']),
                float(row['Low']),
                float(row['Close']),
                int(row['Volume']),
                float(row['market_cap'])
            ))
        except Exception as e:
            logger.error(f"Error processing row for {row['ticker']}: {e}")
    
    logger.info(f"Prepared {len(values)} rows for insertion into daily_data table")
    
    # Insert data into database
    try:
        insert_many(
            'daily_data',
            ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume', 'market_cap'],
            values
        )
        logger.info(f"Successfully inserted {len(values)} rows into daily_data table")
    except Exception as e:
        logger.error(f"Error inserting data into daily_data table: {e}")
        # Log the first row to help diagnose the issue
        if values:
            logger.error(f"First row: {values[0]}")

def acquire_data(days=30):
    """
    Main function to acquire stock data for the specified number of days.
    """
    logger.info("Starting acquire_data function")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates as strings
    end_date_str = end_date.strftime('%Y-%m-%d')
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    logger.info(f"Date range: {start_date_str} to {end_date_str}")
    
    # Fetch S&P 500 tickers (or any existing tickers in the database)
    tickers = get_all_tickers()
    logger.info(f"Tickers from database: {len(tickers)}")
    
    if not tickers:
        logger.info("No tickers in database, fetching S&P 500 tickers")
        tickers = fetch_sp500_tickers()
    
    logger.info(f"Total tickers: {len(tickers)}")
    
    if not tickers:
        logger.error("Failed to get tickers")
        return False
    
    logger.info(f"Using {len(tickers)} tickers: {tickers[:5]}...")
    
    # Fetch historical stock data
    logger.info("Fetching historical stock data...")
    data = fetch_stock_data(tickers, start_date_str, end_date_str)
    logger.info(f"Fetched data shape: {data.shape if not data.empty else 'Empty DataFrame'}")
    
    # Fetch market cap data
    logger.info("Fetching market cap data...")
    market_caps = fetch_market_cap_data(tickers)
    logger.info(f"Fetched market caps: {len(market_caps)}")
    
    # Store data in the database
    logger.info("Storing data in the database...")
    store_stock_data(data, market_caps)
    
    logger.info(f"Completed data acquisition for {len(tickers)} stocks")
    logger.info(f"Successfully acquired data for {len(tickers)} stocks from {start_date_str} to {end_date_str}")
    return True

if __name__ == "__main__":
    # Only configure basic logging if run directly and not through the job script
    # This prevents conflicts with the job's logging configuration
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)
    acquire_data() 