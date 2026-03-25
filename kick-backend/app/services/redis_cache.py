"""Optional Redis-backed cache and rate limiter.

When ``REDIS_URL`` is set the module uses Redis for both API response caching
and per-IP rate limiting.  This gives several production benefits:

* State survives application restarts and deploys
* Works correctly across multiple worker processes / containers
* Inherently thread-safe (single-threaded Redis commands are atomic)

When ``REDIS_URL`` is **not** set the helpers fall back to the existing
in-memory ``OrderedDict`` / ``deque`` implementations so that local
development works without any extra infrastructure.
"""

import json
import logging
import os
import time
from collections import OrderedDict, deque
from typing import Optional

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "")

_redis_client = None
_redis_available = False


async def init_redis() -> None:
    """Initialise the module-level Redis connection pool (if configured)."""
    global _redis_client, _redis_available
    if not REDIS_URL:
        logger.info("REDIS_URL not set — using in-memory cache and rate limiter")
        return
    try:
        from redis.asyncio import from_url
        _redis_client = from_url(REDIS_URL, decode_responses=True)
        await _redis_client.ping()
        _redis_available = True
        logger.info("Connected to Redis at %s", REDIS_URL.split("@")[-1])
    except Exception:
        logger.warning("Failed to connect to Redis — falling back to in-memory", exc_info=True)
        _redis_client = None
        _redis_available = False


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _redis_client, _redis_available
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        _redis_available = False


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

_RATE_STORE_MAX_SIZE = 10_000
_rate_store: OrderedDict[str, deque[float]] = OrderedDict()


async def check_rate_limit(
    client_ip: str,
    window: int = 60,
    max_requests: int = 60,
) -> bool:
    """Return ``True`` if the request is allowed, ``False`` if rate-limited."""
    if _redis_available and _redis_client is not None:
        return await _check_rate_limit_redis(client_ip, window, max_requests)
    return _check_rate_limit_memory(client_ip, window, max_requests)


async def _check_rate_limit_redis(
    client_ip: str,
    window: int,
    max_requests: int,
) -> bool:
    key = f"rl:{client_ip}"
    now = time.time()
    pipe = _redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window)
    results = await pipe.execute()
    current_count = results[1]
    return current_count < max_requests


def _check_rate_limit_memory(
    client_ip: str,
    window: int,
    max_requests: int,
) -> bool:
    now = time.time()
    timestamps = _rate_store.get(client_ip, deque())
    while timestamps and now - timestamps[0] >= window:
        timestamps.popleft()
    if len(timestamps) >= max_requests:
        _rate_store[client_ip] = timestamps
        return False
    timestamps.append(now)
    _rate_store[client_ip] = timestamps
    _rate_store.move_to_end(client_ip)
    while len(_rate_store) > _RATE_STORE_MAX_SIZE:
        _rate_store.popitem(last=False)
    return True


# ---------------------------------------------------------------------------
# API response cache
# ---------------------------------------------------------------------------

_CACHE_MAX_SIZE = 500
_mem_cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()


async def get_cached(key: str, ttl: int = 30) -> Optional[dict]:
    """Return a cached value or ``None``."""
    if _redis_available and _redis_client is not None:
        return await _get_cached_redis(key)
    return _get_cached_memory(key, ttl)


async def set_cached(key: str, data: dict, ttl: int = 30) -> None:
    """Store a value in the cache."""
    if _redis_available and _redis_client is not None:
        await _set_cached_redis(key, data, ttl)
    else:
        _set_cached_memory(key, data)


async def _get_cached_redis(key: str) -> Optional[dict]:
    raw = await _redis_client.get(f"cache:{key}")
    if raw is not None:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


async def _set_cached_redis(key: str, data: dict, ttl: int) -> None:
    await _redis_client.setex(f"cache:{key}", ttl, json.dumps(data))


def _get_cached_memory(key: str, ttl: int) -> Optional[dict]:
    if key in _mem_cache:
        ts, data = _mem_cache[key]
        if time.time() - ts < ttl:
            _mem_cache.move_to_end(key)
            return data
        del _mem_cache[key]
    return None


def _set_cached_memory(key: str, data: dict) -> None:
    _mem_cache[key] = (time.time(), data)
    _mem_cache.move_to_end(key)
    while len(_mem_cache) > _CACHE_MAX_SIZE:
        _mem_cache.popitem(last=False)
