import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import date

from app.cache.redis_cache import (
    get_cache, set_cache, delete_cache, delete_pattern, 
    cache_response, invalidate_cache, DateTimeEncoder
)
from tests.mocks import MockRedisClient

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    with patch("app.cache.redis_cache.redis_client", MockRedisClient()) as mock:
        with patch("app.cache.redis_cache.redis_available", True):
            yield mock

@pytest.fixture
def mock_redis_unavailable():
    """Mock Redis client that is unavailable"""
    with patch("app.cache.redis_cache.redis_client", MockRedisClient(available=False)) as mock:
        with patch("app.cache.redis_cache.redis_available", False):
            yield mock

class TestRedisCache:
    """Tests for the Redis cache functions"""
    
    def test_get_cache_hit(self, mock_redis):
        """Test get_cache when the key exists"""
        # Set up the mock to return a value
        mock_redis.data["test_key"] = json.dumps({"test": "value"})
        
        # Call the function
        value = get_cache("test_key")
        
        # Check the result
        assert value == {"test": "value"}
    
    def test_get_cache_miss(self, mock_redis):
        """Test get_cache when the key doesn't exist"""
        # Call the function
        value = get_cache("nonexistent_key")
        
        # Check the result
        assert value is None
    
    def test_get_cache_redis_unavailable(self, mock_redis_unavailable):
        """Test get_cache when Redis is unavailable"""
        # Call the function
        value = get_cache("test_key")
        
        # Check the result
        assert value is None
    
    def test_set_cache_success(self, mock_redis):
        """Test set_cache successfully storing a value"""
        # Call the function
        result = set_cache("test_key", {"test": "value"})
        
        # Check the result
        assert result is True
        assert "test_key" in mock_redis.data
        assert json.loads(mock_redis.data["test_key"]) == {"test": "value"}
    
    def test_set_cache_with_expiry(self, mock_redis):
        """Test set_cache with a custom expiry time"""
        # Call the function
        result = set_cache("test_key", {"test": "value"}, expiry=60)
        
        # Check the result
        assert result is True
        assert "test_key" in mock_redis.data
    
    def test_set_cache_redis_unavailable(self, mock_redis_unavailable):
        """Test set_cache when Redis is unavailable"""
        # Call the function
        result = set_cache("test_key", {"test": "value"})
        
        # Check the result
        assert result is False
    
    def test_delete_cache_success(self, mock_redis):
        """Test delete_cache successfully removing a value"""
        # Set up the mock with an existing key
        mock_redis.data["test_key"] = json.dumps({"test": "value"})
        
        # Call the function
        result = delete_cache("test_key")
        
        # Check the result
        assert result is True
        assert "test_key" not in mock_redis.data
    
    def test_delete_cache_nonexistent_key(self, mock_redis):
        """Test delete_cache with a nonexistent key"""
        # Call the function
        result = delete_cache("nonexistent_key")
        
        # Check the result
        assert result is True  # Still returns True even if key doesn't exist
    
    def test_delete_cache_redis_unavailable(self, mock_redis_unavailable):
        """Test delete_cache when Redis is unavailable"""
        # Call the function
        result = delete_cache("test_key")
        
        # Check the result
        assert result is False
    
    def test_delete_pattern_success(self, mock_redis):
        """Test delete_pattern successfully removing matching keys"""
        # Set up the mock with some keys
        mock_redis.data["prefix:key1"] = json.dumps({"test": "value1"})
        mock_redis.data["prefix:key2"] = json.dumps({"test": "value2"})
        mock_redis.data["other:key"] = json.dumps({"test": "value3"})
        
        # Call the function
        result = delete_pattern("prefix:*")
        
        # Check the result
        assert result is True
        assert "prefix:key1" not in mock_redis.data
        assert "prefix:key2" not in mock_redis.data
        assert "other:key" in mock_redis.data
    
    def test_delete_pattern_no_matches(self, mock_redis):
        """Test delete_pattern with no matching keys"""
        # Set up the mock with some keys
        mock_redis.data["other:key"] = json.dumps({"test": "value"})
        
        # Call the function
        result = delete_pattern("prefix:*")
        
        # Check the result
        assert result is True  # Still returns True even if no keys match
    
    def test_delete_pattern_redis_unavailable(self, mock_redis_unavailable):
        """Test delete_pattern when Redis is unavailable"""
        # Call the function
        result = delete_pattern("prefix:*")
        
        # Check the result
        assert result is False

class TestDateTimeEncoder:
    """Tests for the DateTimeEncoder JSON encoder"""
    
    def test_datetime_encoder_with_date(self):
        """Test DateTimeEncoder with a date object"""
        # Create a date object
        test_date = date(2023, 1, 15)
        
        # Encode it using our custom encoder
        encoded = json.dumps({"date": test_date}, cls=DateTimeEncoder)
        
        # Check the result
        assert encoded == '{"date": "2023-01-15"}'
    
    def test_datetime_encoder_with_regular_types(self):
        """Test DateTimeEncoder with regular types"""
        # Create a dictionary with various types
        data = {
            "string": "test",
            "integer": 123,
            "float": 123.45,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        
        # Encode it using our custom encoder
        encoded = json.dumps(data, cls=DateTimeEncoder)
        
        # Check the result by decoding it back
        decoded = json.loads(encoded)
        assert decoded == data

@pytest.mark.asyncio
class TestCacheDecorator:
    """Tests for the cache_response decorator"""
    
    async def test_cache_response_hit(self, mock_redis):
        """Test cache_response decorator with a cache hit"""
        # Create a mock function to decorate
        mock_function = MagicMock()
        mock_function.return_value = {"test": "value"}
        mock_function.__name__ = "test_function"
        
        # Decorate the function
        decorated = cache_response("test")(mock_function)
        
        # Set up a cache hit
        key = 'test:test_function:{"arg1": "value1"}'
        mock_redis.data[key] = json.dumps({"test": "cached_value"})
        
        # Call the decorated function
        result = await decorated(arg1="value1")
        
        # Check that the function wasn't called (cache hit)
        mock_function.assert_not_called()
        
        # Check that the cached value was returned
        assert result == {"test": "cached_value"}
    
    async def test_cache_response_miss(self, mock_redis):
        """Test cache_response decorator with a cache miss"""
        # Create a mock function to decorate
        mock_function = MagicMock()
        mock_function.return_value = {"test": "value"}
        mock_function.__name__ = "test_function"
        
        # Decorate the function
        decorated = cache_response("test")(mock_function)
        
        # Call the decorated function
        result = await decorated(arg1="value1")
        
        # Check that the function was called (cache miss)
        mock_function.assert_called_once_with(arg1="value1")
        
        # Check that the function result was returned
        assert result == {"test": "value"}
        
        # Check that the result was cached
        key = 'test:test_function:{"arg1": "value1"}'
        assert key in mock_redis.data
    
    async def test_cache_response_redis_unavailable(self, mock_redis_unavailable):
        """Test cache_response decorator when Redis is unavailable"""
        # Create a mock function to decorate
        mock_function = MagicMock()
        mock_function.return_value = {"test": "value"}
        mock_function.__name__ = "test_function"
        
        # Decorate the function
        decorated = cache_response("test")(mock_function)
        
        # Call the decorated function
        result = await decorated(arg1="value1")
        
        # Check that the function was called
        mock_function.assert_called_once_with(arg1="value1")
        
        # Check that the function result was returned
        assert result == {"test": "value"}

class TestInvalidateCache:
    """Tests for the invalidate_cache function"""
    
    def test_invalidate_cache_success(self, mock_redis):
        """Test invalidate_cache successfully removing keys with a prefix"""
        # Set up the mock with some keys
        mock_redis.data["test:key1"] = json.dumps({"test": "value1"})
        mock_redis.data["test:key2"] = json.dumps({"test": "value2"})
        mock_redis.data["other:key"] = json.dumps({"test": "value3"})
        
        # Call the function
        result = invalidate_cache("test")
        
        # Check the result
        assert result is True
        assert "test:key1" not in mock_redis.data
        assert "test:key2" not in mock_redis.data
        assert "other:key" in mock_redis.data
    
    def test_invalidate_cache_redis_unavailable(self, mock_redis_unavailable):
        """Test invalidate_cache when Redis is unavailable"""
        # Call the function
        result = invalidate_cache("test")
        
        # Check the result
        assert result is False 