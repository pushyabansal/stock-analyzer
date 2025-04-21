-- Create stocks table to store stock metadata
CREATE TABLE IF NOT EXISTS stocks (
    ticker TEXT PRIMARY KEY,
    name TEXT,
    sector TEXT,
    exchange TEXT
);

-- Create daily_data table to store daily stock prices and market caps
CREATE TABLE IF NOT EXISTS daily_data (
    date DATE,
    ticker TEXT,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    market_cap FLOAT,
    PRIMARY KEY (date, ticker),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- Create index_composition table to store daily index compositions
CREATE TABLE IF NOT EXISTS index_composition (
    date DATE,
    ticker TEXT,
    weight FLOAT,
    PRIMARY KEY (date, ticker),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- Create index_performance table to store index performance
CREATE TABLE IF NOT EXISTS index_performance (
    date DATE PRIMARY KEY,
    daily_return FLOAT,
    cumulative_return FLOAT
);

-- Create composition_changes table to store entry/exit events
CREATE TABLE IF NOT EXISTS composition_changes (
    date DATE,
    ticker TEXT,
    event TEXT CHECK (event IN ('ENTRY', 'EXIT')),
    PRIMARY KEY (date, ticker),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
); 