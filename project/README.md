# Stock Index Analyzer

A backend service that tracks and manages a custom equal-weighted stock index comprising the top 100 US stocks by daily market capitalization.

## Features

- Constructs an equal-weighted index dynamically for any date or date range
- Retrieves historical performance and compositions
- Detects and shows composition changes over time
- Exports all outputs into well-formatted Excel files
- Uses Redis for caching and DuckDB for data storage

## Project Structure

```
stock_analyzer/
├── app/                       # Main application package
│   ├── cache/                 # Redis caching functionality
│   ├── config/                # Configuration settings
│   ├── db/                    # Database models and connections
│   ├── jobs/                  # Background jobs (data acquisition)
│   ├── models/                # Pydantic models for API
│   ├── routes/                # API route definitions
│   ├── services/              # Business logic services
│   └── utils/                 # Utility functions
├── data/                      # Data storage directory (created at runtime)
├── logs/                      # Log files directory (created at runtime)
├── tests/                     # Test suite
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker configuration
├── requirements.txt           # Python dependencies
├── run.py                     # Script to run the application
└── run_tests.py               # Script to run the test suite
```

## Data Source Comparison

Two common sources for market data were evaluated:

### Yahoo Finance (Selected)
- **Pros**: 
  - Free to use with no API key required
  - Comprehensive historical data for most US stocks
  - Provides market cap data directly
  - Ability to batch download multiple tickers at once
  - Well-maintained Python package (yfinance)
- **Cons**:
  - Rate limits can be reached with excessive requests
  - No official API, relies on web scraping underneath
  - Can be slower than paid alternatives

### Alpha Vantage
- **Pros**:
  - Official API with clear documentation
  - Provides fundamental data including market cap
  - More reliable uptime
- **Cons**:
  - Free tier is limited to 25 API calls per day
  - Requires API key
  - Cannot batch download multiple stocks in one request

Yahoo Finance was selected due to its ability to retrieve data for many stocks without requiring an API key, which makes the demo easier to run and test. For a production environment, a paid data provider with an SLA would be more appropriate.

## Setup Instructions

### Local Setup

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Set up Redis for caching - see [Redis Setup](docs_redis_setup.md) for details:
   - The application will work without Redis (caching disabled)
   - For better performance, follow the Redis setup instructions

4. Run the data acquisition job:

```bash
python -m app.jobs.data_acquisition
```

5. Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

6. Access the API documentation at http://localhost:8000/docs

### Docker Setup

1. Build and start the containers:

```bash
docker-compose up -d
```

2. Run the data acquisition job:

```bash
docker-compose exec app python -m app.jobs.data_acquisition
```

3. Access the API documentation at http://localhost:8000/docs

Docker setup includes Redis caching by default.

## API Usage

### Build Index

```bash
curl -X POST "http://localhost:8000/build-index" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2023-01-01", "end_date": "2023-01-31"}'
```

### Get Index Performance

```bash
curl -X GET "http://localhost:8000/index-performance?start_date=2023-01-01&end_date=2023-01-31"
```

### Get Index Composition

```bash
curl -X GET "http://localhost:8000/index-composition?date=2023-01-15"
```

### Get Composition Changes

```bash
curl -X GET "http://localhost:8000/composition-changes?start_date=2023-01-01&end_date=2023-01-31"
```

### Export Data

```bash
curl -X POST "http://localhost:8000/export-data" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2023-01-01", "end_date": "2023-01-31"}'
```

## Database Schema

### Tables

1. **stocks**
   - `ticker` (TEXT): Stock ticker symbol (primary key)
   - `name` (TEXT): Company name
   - `sector` (TEXT): Business sector
   - `exchange` (TEXT): Stock exchange

2. **daily_data**
   - `date` (DATE): Trading date
   - `ticker` (TEXT): Stock ticker symbol
   - `open` (FLOAT): Opening price
   - `high` (FLOAT): High price
   - `low` (FLOAT): Low price
   - `close` (FLOAT): Closing price
   - `volume` (BIGINT): Trading volume
   - `market_cap` (FLOAT): Market capitalization
   - Primary key: (date, ticker)

3. **index_composition**
   - `date` (DATE): Trading date
   - `ticker` (TEXT): Stock ticker symbol
   - `weight` (FLOAT): Weight in the index
   - Primary key: (date, ticker)

4. **index_performance**
   - `date` (DATE): Trading date (primary key)
   - `daily_return` (FLOAT): Day-over-day percentage return
   - `cumulative_return` (FLOAT): Cumulative return since inception

5. **composition_changes**
   - `date` (DATE): Trading date
   - `ticker` (TEXT): Stock ticker symbol
   - `event` (TEXT): 'ENTRY' or 'EXIT'
   - Primary key: (date, ticker)

## Production/Scaling Improvements

1. **Data Acquisition**
   - Implement incremental data loading
   - Add more robust error handling and retry mechanisms
   - Set up a proper scheduling system (Airflow, Prefect, etc.)
   - Use a paid data provider with better reliability and SLAs

2. **Database**
   - Migrate to a distributed database for horizontal scaling
   - Implement database sharding for large datasets
   - Add database replication for high availability
   - Set up regular backup procedures

3. **API Performance**
   - Implement response pagination for large result sets
   - Add more granular caching strategies
   - Consider GraphQL for more flexible data retrieval
   - Add API versioning for backwards compatibility

4. **Infrastructure**
   - Implement Kubernetes for container orchestration
   - Set up auto-scaling based on load
   - Implement proper monitoring and alerting
   - Use Infrastructure as Code (Terraform, CloudFormation)

5. **Security**
   - Add API authentication and authorization
   - Implement rate limiting
   - Set up proper secret management
   - Regularly scan for vulnerabilities

6. **Resiliency**
   - Implement circuit breakers for external services
   - Set up multiple availability zones/regions
   - Create chaos testing scenarios
   - Implement service mesh for better inter-service communication 