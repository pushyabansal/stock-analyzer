import pytest
import os
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from app.db.database import (
    get_connection, execute_query, execute_script, 
    insert_many, execute_pandas_query, execute_sql_file
)

@pytest.fixture
def mock_duckdb_connection():
    """Mock DuckDB connection"""
    mock_conn = MagicMock()
    mock_conn.execute = MagicMock()
    mock_conn.execute.return_value = mock_conn
    mock_conn.fetchall = MagicMock(return_value=[("result1",), ("result2",)])
    mock_conn.df = MagicMock(return_value=pd.DataFrame({"column1": [1, 2], "column2": ["a", "b"]}))
    mock_conn.executemany = MagicMock()
    mock_conn.commit = MagicMock()
    mock_conn.close = MagicMock()
    return mock_conn

@pytest.fixture
def mock_path_mkdir():
    """Mock Path.mkdir"""
    with patch("app.db.database.Path.mkdir") as mock:
        yield mock

@pytest.fixture
def mock_duckdb_connect(mock_duckdb_connection):
    """Mock duckdb.connect"""
    with patch("app.db.database.duckdb.connect", return_value=mock_duckdb_connection) as mock:
        yield mock

@pytest.fixture
def mock_open_file():
    """Mock open function"""
    with patch("builtins.open", mock_open(read_data="MOCK SQL SCRIPT")) as mock:
        yield mock

class TestDatabase:
    """Tests for database functions"""
    
    def test_get_connection(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test get_connection creates parent directory and initializes the database"""
        # Call the function
        conn = get_connection()
        
        # Check that the parent directory was created
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Check that duckdb.connect was called with the correct DB path
        db_path = os.getenv("DB_PATH", os.path.join("data", "stock_index.ddb"))
        mock_duckdb_connect.assert_called_once_with(db_path)
        
        # Check that the schema file was opened and executed
        mock_open_file.assert_called_once()
        assert conn.execute.call_count == 1
        
        # Verify the return value matches what duckdb.connect returned
        assert conn == mock_duckdb_connect.return_value
    
    def test_execute_query_without_params(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test execute_query without parameters"""
        # Clear any previous calls to our mock connection
        mock_duckdb_connect.return_value.execute.reset_mock()
        
        # Call the function
        result = execute_query("SELECT * FROM test")
        
        # We need to allow for two calls: one for schema.sql, one for our query
        # Check that the query was executed at some point
        call_args_list = mock_duckdb_connect.return_value.execute.call_args_list
        assert any(call_args[0][0] == "SELECT * FROM test" for call_args in call_args_list)
        
        # Check that fetchall was called
        mock_duckdb_connect.return_value.fetchall.assert_called_once()
        
        # Check that close was called
        mock_duckdb_connect.return_value.close.assert_called_once()
        
        # Check the result
        assert result == [("result1",), ("result2",)]
    
    def test_execute_query_with_params(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test execute_query with parameters"""
        # Clear any previous calls
        mock_duckdb_connect.return_value.execute.reset_mock()
        
        # Call the function
        result = execute_query("SELECT * FROM test WHERE id = ?", (1,))
        
        # Check that the query was executed with parameters at some point
        call_args_list = mock_duckdb_connect.return_value.execute.call_args_list
        assert any(call_args[0][0] == "SELECT * FROM test WHERE id = ?" and
                  call_args[0][1] == (1,) for call_args in call_args_list)
        
        # Check the result
        assert result == [("result1",), ("result2",)]
    
    def test_execute_script(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test execute_script"""
        # Clear any previous calls
        mock_duckdb_connect.return_value.execute.reset_mock()
        
        # Call the function
        execute_script("CREATE TABLE test (id INTEGER)")
        
        # Check that the script was executed
        call_args_list = mock_duckdb_connect.return_value.execute.call_args_list
        assert any(call_args[0][0] == "CREATE TABLE test (id INTEGER)" for call_args in call_args_list)
        
        # Check that close was called
        mock_duckdb_connect.return_value.close.assert_called_once()
    
    def test_insert_many(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test insert_many"""
        # Call the function
        insert_many("test_table", ["column1", "column2"], [(1, "a"), (2, "b")])
        
        # Check that executemany was called with the correct query and values
        expected_query = "INSERT INTO test_table (column1, column2) VALUES (?, ?)"
        mock_duckdb_connect.return_value.executemany.assert_called_once_with(expected_query, [(1, "a"), (2, "b")])
        
        # Check that commit was called
        mock_duckdb_connect.return_value.commit.assert_called_once()
        
        # Check that close was called
        mock_duckdb_connect.return_value.close.assert_called_once()
    
    def test_insert_many_empty_values(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test insert_many with empty values"""
        # Call the function
        insert_many("test_table", ["column1", "column2"], [])
        
        # Check that executemany was not called
        mock_duckdb_connect.return_value.executemany.assert_not_called()
        
        # Check that close was not called
        mock_duckdb_connect.return_value.close.assert_not_called()
    
    def test_execute_pandas_query_without_params(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test execute_pandas_query without parameters"""
        # Clear any previous calls
        mock_duckdb_connect.return_value.execute.reset_mock()
        
        # Call the function
        result = execute_pandas_query("SELECT * FROM test")
        
        # Check that the query was executed
        call_args_list = mock_duckdb_connect.return_value.execute.call_args_list
        assert any(call_args[0][0] == "SELECT * FROM test" for call_args in call_args_list)
        
        # Check that df() was called
        mock_duckdb_connect.return_value.df.assert_called_once()
        
        # Check that close was called
        mock_duckdb_connect.return_value.close.assert_called_once()
        
        # Check the result
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["column1", "column2"]
        assert list(result["column1"]) == [1, 2]
        assert list(result["column2"]) == ["a", "b"]
    
    def test_execute_pandas_query_with_params(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test execute_pandas_query with parameters"""
        # Clear any previous calls
        mock_duckdb_connect.return_value.execute.reset_mock()
        
        # Call the function
        result = execute_pandas_query("SELECT * FROM test WHERE id = ?", (1,))
        
        # Check that the query was executed with parameters
        call_args_list = mock_duckdb_connect.return_value.execute.call_args_list
        assert any(call_args[0][0] == "SELECT * FROM test WHERE id = ?" and
                  call_args[0][1] == (1,) for call_args in call_args_list)
        
        # Check the result
        assert isinstance(result, pd.DataFrame)
    
    def test_execute_sql_file(self, mock_duckdb_connect, mock_path_mkdir, mock_open_file):
        """Test execute_sql_file"""
        # Clear any previous calls
        mock_duckdb_connect.return_value.execute.reset_mock()
        
        # Call the function
        execute_sql_file("/path/to/sql/file.sql")
        
        # Check that the file was opened
        mock_open_file.assert_any_call("/path/to/sql/file.sql", "r")
        
        # Check that the SQL was executed at some point
        call_args_list = mock_duckdb_connect.return_value.execute.call_args_list
        assert any(call_args[0][0] == "MOCK SQL SCRIPT" for call_args in call_args_list)
        
        # Check that close was called
        mock_duckdb_connect.return_value.close.assert_called_once() 