# dashboard/utils/cache.py
"""Caching utilities with proper typing for Pylance."""

import functools
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

# Type variables for proper decorator typing
P = ParamSpec("P")
R = TypeVar("R")


class CacheManager:
    """Simple in-memory cache manager."""

    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if datetime.now() > entry["expires_at"]:
                del self._cache[key]
                return None

            return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set cache value with TTL."""
        with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=ttl_seconds),
                "created_at": datetime.now(),
            }

    def clear(self) -> None:
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def clear_pattern(self, pattern: str) -> None:
        """Clear cache entries matching pattern."""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            logger.info(f"Cleared {len(keys_to_delete)} cache entries matching pattern: {pattern}")


def cached(ttl: int = 300) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator for caching function results with proper typing.

    Args:
        ttl: Time to live in seconds

    Returns:
        Decorated function with caching

    Example:
        @cached(ttl=300)
        def get_skills(self, limit: int) -> List[TopSkill]:
            ...
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Get self from args (for instance methods)
            self = args[0] if args else None

            # Generate cache key from function name and arguments
            args_key = args[1:] if args else args
            cache_key = f"{func.__name__}:{str(args_key)}:{str(kwargs)}"

            # Check if cache_manager exists on self
            cache_manager = getattr(self, "cache_manager", None) if self else None

            if cache_manager is None:
                return func(*args, **kwargs)

            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


# Explicit exports for the module
__all__ = ["CacheManager", "cached"]
