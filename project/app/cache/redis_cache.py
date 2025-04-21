import os
import json
import redis
import logging
from functools import wraps
from datetime import date, datetime

# Get Redis connection details from environment variables or use defaults
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_EXPIRY = int(os.getenv("REDIS_EXPIRY", 3600))  # 1 hour default expiry

# Create logger
logger = logging.getLogger(__name__)

# Create Redis client with connection check
redis_client = None
redis_available = False

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2.0,  # Short timeout for initial connection
        socket_timeout=2.0,          # Short timeout for operations
    )
    # Check connection
    redis_client.ping()
    redis_available = True
    logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except (redis.ConnectionError, redis.exceptions.TimeoutError) as e:
    logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
except Exception as e:
    logger.error(f"Unexpected Redis error: {e}. Caching will be disabled.")

# Custom JSON encoder to handle date objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def get_cache(key):
    """Get a value from the cache"""
    if not redis_available:
        return None
        
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Redis get error: {e}")
        return None

def set_cache(key, value, expiry=REDIS_EXPIRY):
    """Set a value in the cache"""
    if not redis_available:
        return False
        
    try:
        redis_client.setex(key, expiry, json.dumps(value, cls=DateTimeEncoder))
        return True
    except Exception as e:
        logger.error(f"Redis set error: {e}")
        return False

def delete_cache(key):
    """Delete a value from the cache"""
    if not redis_available:
        return False
        
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Redis delete error: {e}")
        return False

def delete_pattern(pattern):
    """Delete all keys matching the pattern"""
    if not redis_available:
        return False
        
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        return True
    except Exception as e:
        logger.error(f"Redis delete pattern error: {e}")
        return False

def cache_response(prefix):
    """Decorator to cache API responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If Redis is not available, just execute the function
            if not redis_available:
                return await func(*args, **kwargs)
                
            try:
                # Create a cache key based on the function name and arguments
                # Convert date objects to strings for the key
                safe_kwargs = {}
                for k, v in kwargs.items():
                    if isinstance(v, (date, datetime)):
                        safe_kwargs[k] = v.isoformat()
                    else:
                        safe_kwargs[k] = v
                
                key = f"{prefix}:{func.__name__}:{json.dumps(safe_kwargs, sort_keys=True)}"
                
                # Try to get from cache
                cached_result = get_cache(key)
                if cached_result:
                    logger.debug(f"Cache hit for key: {key}")
                    return cached_result
                
                # If not in cache, call the original function
                logger.debug(f"Cache miss for key: {key}")
                result = await func(*args, **kwargs)
                
                # Cache the result
                set_cache(key, result)
                
                return result
            except Exception as e:
                logger.error(f"Cache error: {e}")
                # If caching fails, just execute the function
                return await func(*args, **kwargs)
        return wrapper
    return decorator

def invalidate_cache(prefix):
    """Invalidate all cache entries with the given prefix"""
    if not redis_available:
        logger.info(f"Redis not available, skipping cache invalidation for prefix: {prefix}")
        return False
        
    logger.info(f"Invalidating cache with prefix: {prefix}")
    return delete_pattern(f"{prefix}:*") 