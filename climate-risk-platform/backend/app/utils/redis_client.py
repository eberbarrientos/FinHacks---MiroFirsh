"""Redis client utility with connection pooling"""

import redis
from redis.connection import ConnectionPool
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_redis_pool: Optional[ConnectionPool] = None


def get_redis_pool() -> ConnectionPool:
    """
    Get or create Redis connection pool.
    
    Returns:
        Redis connection pool
    """
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        logger.info("Redis connection pool created")
    
    return _redis_pool


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client from connection pool.
    
    Returns:
        Redis client or None if connection fails
    """
    try:
        pool = get_redis_pool()
        client = redis.Redis(connection_pool=pool)
        # Test connection
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Caching disabled.")
        return None


def check_redis_health() -> bool:
    """
    Check if Redis connection is healthy.
    
    Returns:
        True if Redis is accessible, False otherwise
    """
    try:
        client = get_redis_client()
        if client:
            client.ping()
            return True
        return False
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


def close_redis_pool():
    """Close Redis connection pool"""
    global _redis_pool
    
    if _redis_pool:
        _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")
