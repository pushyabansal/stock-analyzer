import os
import duckdb
from pathlib import Path

# Get the DB file path from environment variable or use default
DB_PATH = os.getenv("DB_PATH", os.path.join("data", "stock_index.ddb"))

def get_connection():
    """Get a DuckDB connection"""
    # Create parent directory if it doesn't exist
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to DuckDB
    conn = duckdb.connect(DB_PATH)
    
    # Initialize the database by executing schema.sql
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        conn.execute(f.read())
    
    return conn

def execute_query(query, params=None):
    """Execute a query and return the result"""
    conn = get_connection()
    try:
        if params:
            result = conn.execute(query, params).fetchall()
        else:
            result = conn.execute(query).fetchall()
        return result
    finally:
        conn.close()

def execute_script(script):
    """Execute a SQL script"""
    conn = get_connection()
    try:
        conn.execute(script)
    finally:
        conn.close()

def insert_many(table, columns, values):
    """Insert multiple rows into a table"""
    if not values:
        return
    
    placeholders = ", ".join(["?" for _ in range(len(columns))])
    columns_str = ", ".join(columns)
    
    query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
    
    conn = get_connection()
    try:
        conn.executemany(query, values)
        conn.commit()
    finally:
        conn.close()

def execute_pandas_query(query, params=None):
    """Execute a query and return the result as a pandas DataFrame"""
    conn = get_connection()
    try:
        if params:
            return conn.execute(query, params).df()
        else:
            return conn.execute(query).df()
    finally:
        conn.close()

def execute_sql_file(file_path):
    """Execute an SQL file"""
    conn = get_connection()
    try:
        with open(file_path, 'r') as f:
            conn.execute(f.read())
    finally:
        conn.close() 