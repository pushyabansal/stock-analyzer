# Redis Setup for Stock Analyzer Application

This document explains how to set up Redis for the Stock Analyzer application in different environments.

## Redis Configuration

The application uses Redis for caching API responses. The Redis connection is configured using the following environment variables:

- `REDIS_HOST`: The hostname or IP address of the Redis server (default: `localhost`)
- `REDIS_PORT`: The port on which Redis is running (default: `6379`)
- `REDIS_DB`: The Redis database index to use (default: `0`)
- `REDIS_EXPIRY`: The default expiry time for cached items in seconds (default: `3600` = 1 hour)

## Setup Options

### Option 1: Running with Docker Compose (Recommended)

The easiest way to run the application with Redis is to use Docker Compose:

```bash
docker-compose up -d
```

This will start both the application and a Redis container, and configure them to communicate with each other automatically.

### Option 2: Running Redis Locally

If you're running the application directly on your machine (not in Docker), you'll need to run Redis locally:

#### Install Redis:

##### On macOS (using Homebrew):
```bash
brew install redis
brew services start redis
```

##### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

##### On Windows:
Windows is not officially supported by Redis. However, you can use:
- [Redis for Windows](https://github.com/tporadowski/redis/releases)
- Windows Subsystem for Linux (WSL)
- Docker Desktop for Windows

#### Verify Redis is Running:
```bash
redis-cli ping
```
Should return `PONG` if Redis is running correctly.

### Option 3: Using a Remote Redis Server

If you want to use a remote Redis server (such as Redis Cloud, AWS ElastiCache, etc.), set the appropriate environment variables:

```bash
export REDIS_HOST=your-redis-server.example.com
export REDIS_PORT=6379
```

### Option 4: Disabling Redis

The application can now run without Redis. If Redis is not available, caching will be disabled automatically, and the application will function normally (just without caching benefits).

## Troubleshooting

### Connection Issues

1. **Check if Redis is running**:
   ```bash
   redis-cli ping
   ```

2. **Check Redis connection settings**:
   Make sure the `REDIS_HOST` and `REDIS_PORT` environment variables are set correctly.

3. **Check firewall settings**:
   If using a remote Redis server, ensure that your firewall allows connections on the Redis port.

4. **Check Redis logs**:
   ```bash
   # If using systemd
   sudo journalctl -u redis-server
   
   # If using Docker
   docker logs stock_index_redis
   ```

### Performance Considerations

- When running without Redis, API responses will not be cached, which may impact performance for repeated queries
- Consider implementing Redis in production environments for best performance
- For high-traffic applications, consider:
  - Increasing `maxmemory` in Redis configuration
  - Setting an appropriate eviction policy (e.g., `volatile-lru`)
  - Using Redis Cluster for horizontal scaling 