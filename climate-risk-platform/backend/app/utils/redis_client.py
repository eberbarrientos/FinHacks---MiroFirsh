"""Redis client utility - falls back to in-memory cache when Redis unavailable"""

import json
import time
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache that mimics Redis interface for local dev"""
    
    def __init__(self):
        self._store = {}
        self._expiry = {}
    
    def get(self, key: str):
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._store[key]
            del self._expiry[key]
            return None
        return self._store.get(key)
    
    def setex(self, key: str, ttl: int, value: str):
        self._store[key] = value
        self._expiry[key] = time.time() + ttl
    
    def delete(self, *keys):
        count = 0
        for key in keys:
            if key in self._store:
                del self._store[key]
                self._expiry.pop(key, None)
                count += 1
        return count
    
    def keys(self, pattern: str = "*"):
        import fnmatch
        return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]
    
    def ping(self):
        return True


_cache_instance: Optional[InMemoryCache] = None
_redis_available: Optional[bool] = None


def get_redis_client():
    """Get Redis client or in-memory fallback."""
    global _cache_instance, _redis_available
    
    if _redis_available is False:
        return _cache_instance
    
    if _redis_available is None:
        try:
            import redis
            client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            client.ping()
            _redis_available = True
            _cache_instance = client
            logger.info("Connected to Redis")
            return client
        except Exception:
            _redis_available = False
            _cache_instance = InMemoryCache()
            logger.info("Redis unavailable, using in-memory cache")
            return _cache_instance
    
    return _cache_instance


def check_redis_health() -> bool:
    """Check if cache is healthy (always true with fallback)."""
    try:
        client = get_redis_client()
        if client:
            client.ping()
            return True
        return False
    except Exception:
        return False


def close_redis_pool():
    """Close Redis connection pool"""
    global _cache_instance, _redis_available
    if _redis_available and _cache_instance:
        try:
            _cache_instance.close()
        except Exception:
            pass
    _cache_instance = None
    _redis_available = None
