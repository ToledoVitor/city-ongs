import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_cached_data(
    key: str,
    fallback_func: Callable[[], T],
    timeout: Optional[int] = None,
    cache_type: str = "DYNAMIC",
) -> T:
    """
    Get data from cache with fallback to database and error handling.

    Args:
        key: Cache key
        fallback_func: Function to call if cache miss
        timeout: Optional custom timeout
        cache_type: Type of cache (STATIC, DYNAMIC, VOLATILE)

    Returns:
        Cached or fresh data
    """
    try:
        value = cache.get(key)
        if value is None:
            value = fallback_func()
            timeout = timeout or settings.CACHE_TIMEOUTS.get(cache_type, 300)
            cache.set(key, value, timeout=timeout)
            logger.info(f"Cache miss for key: {key}, set with timeout: {timeout}")
        else:
            logger.debug(f"Cache hit for key: {key}")
        return value
    except Exception as e:
        logger.error(f"Cache error for key {key}: {str(e)}")
        return fallback_func()


def get_multiple_cached_data(
    keys: list[str],
    fallback_func: Callable[[list[str]], dict[str, T]],
    timeout: Optional[int] = None,
    cache_type: str = "DYNAMIC",
) -> dict[str, T]:
    """
    Get multiple items from cache with fallback.

    Args:
        keys: List of cache keys
        fallback_func: Function to call for missing keys
        timeout: Optional custom timeout
        cache_type: Type of cache

    Returns:
        Dictionary of cached/fresh data
    """
    try:
        redis_client = cache.client.get_client()
        with redis_client.pipeline() as pipe:
            for key in keys:
                pipe.get(key)
            values = pipe.execute()

        # Find missing keys
        missing_keys = [key for key, value in zip(keys, values) if value is None]

        if missing_keys:
            # Get missing data from fallback
            fresh_data = fallback_func(missing_keys)
            timeout = timeout or settings.CACHE_TIMEOUTS.get(cache_type, 300)

            # Cache the fresh data
            with redis_client.pipeline() as pipe:
                for key, value in fresh_data.items():
                    pipe.set(key, value, timeout=timeout)
                pipe.execute()

            # Update values with fresh data
            for key in missing_keys:
                values[keys.index(key)] = fresh_data[key]

            logger.info(
                f"Cache miss for keys: {missing_keys}, set with timeout: {timeout}"
            )
        else:
            logger.debug(f"Cache hit for all keys: {keys}")

        return dict(zip(keys, values))
    except Exception as e:
        logger.error(f"Cache error for keys {keys}: {str(e)}")
        return fallback_func(keys)


def monitor_cache_operation(operation_name: str) -> Callable:
    """
    Decorator to monitor cache operation performance.

    Args:
        operation_name: Name of the operation for logging
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                operation_time = (time.time() - start_time) * 1000  # Convert to ms
                logger.info(
                    f"Cache {operation_name} took {operation_time:.3f}ms",
                    extra={
                        "operation": operation_name,
                        "time_ms": operation_time,
                        "args": args,
                        "kwargs": kwargs,
                    },
                )
                return result
            except Exception as e:
                operation_time = (time.time() - start_time) * 1000
                logger.error(
                    f"Cache {operation_name} failed after {operation_time:.3f}ms",
                    extra={
                        "operation": operation_name,
                        "time_ms": operation_time,
                        "error": str(e),
                        "args": args,
                        "kwargs": kwargs,
                    },
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def warm_cache(key: str, data: Any, timeout: Optional[int] = None) -> None:
    """
    Pre-warm cache with data.

    Args:
        key: Cache key
        data: Data to cache
        timeout: Optional custom timeout
    """
    try:
        timeout = timeout or settings.CACHE_TIMEOUTS.get("STATIC", 3600)
        cache.set(key, data, timeout=timeout)
        logger.info(f"Cache warmed for key: {key} with timeout: {timeout}")
    except Exception as e:
        logger.error(f"Cache warming failed for key {key}: {str(e)}")
