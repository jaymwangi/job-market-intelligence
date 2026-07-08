"""
Unit tests for dashboard cache utilities.
"""

import time

import pytest

from dashboard.utils.cache import CacheManager, cached


class TestCacheManager:
    """Test suite for CacheManager."""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache manager."""
        return CacheManager()

    def test_set_and_get(self, cache):
        """Test setting and getting cache values."""
        cache.set("key", "value", ttl_seconds=60)
        assert cache.get("key") == "value"

    def test_get_missing_key(self, cache):
        """Test getting missing key."""
        assert cache.get("missing") is None

    def test_ttl_expiration(self, cache):
        """Test TTL expiration."""
        cache.set("key", "value", ttl_seconds=1)
        assert cache.get("key") == "value"

        time.sleep(1.1)
        assert cache.get("key") is None

    def test_clear_all(self, cache):
        """Test clearing all cache."""
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_clear_pattern(self, cache):
        """Test clearing cache entries matching pattern."""
        cache.set("job_1", "value1", ttl_seconds=60)
        cache.set("job_2", "value2", ttl_seconds=60)
        cache.set("skill_1", "value3", ttl_seconds=60)

        cache.clear_pattern("job_")
        assert cache.get("job_1") is None
        assert cache.get("job_2") is None
        assert cache.get("skill_1") == "value3"

    def test_clear_pattern_no_matches(self, cache):
        """Test clearing pattern with no matches."""
        cache.set("job_1", "value1", ttl_seconds=60)
        cache.clear_pattern("nonexistent")
        assert cache.get("job_1") == "value1"


class TestCachedDecorator:
    """Test suite for cached decorator."""

    def test_cached_decorator_basic(self):
        """Test basic cached decorator functionality."""

        class TestService:
            def __init__(self):
                self.cache_manager = CacheManager()
                self.call_count = 0

            @cached(ttl=60)
            def get_data(self, param: str) -> str:
                self.call_count += 1
                return f"data_{param}"

        service = TestService()

        # First call - should execute
        result1 = service.get_data("test")
        assert result1 == "data_test"
        assert service.call_count == 1

        # Second call - should use cache
        result2 = service.get_data("test")
        assert result2 == "data_test"
        assert service.call_count == 1

        # Different param - should execute
        result3 = service.get_data("other")
        assert result3 == "data_other"
        assert service.call_count == 2

    def test_cached_decorator_ttl_expiration(self):
        """Test cached decorator TTL expiration."""

        class TestService:
            def __init__(self):
                self.cache_manager = CacheManager()
                self.call_count = 0

            @cached(ttl=1)
            def get_data(self, param: str) -> str:
                self.call_count += 1
                return f"data_{param}"

        service = TestService()

        # First call
        service.get_data("test")
        assert service.call_count == 1

        # Second call - cache hit
        service.get_data("test")
        assert service.call_count == 1

        # Wait for TTL to expire
        time.sleep(1.1)

        # Third call - should execute again
        service.get_data("test")
        assert service.call_count == 2

    def test_cached_decorator_without_cache_manager(self):
        """Test cached decorator when no cache_manager exists."""

        class TestService:
            def __init__(self):
                self.call_count = 0
                # No cache_manager attribute

            @cached(ttl=60)
            def get_data(self, param: str) -> str:
                self.call_count += 1
                return f"data_{param}"

        service = TestService()

        # Should work without cache
        result1 = service.get_data("test")
        assert result1 == "data_test"
        assert service.call_count == 1

        result2 = service.get_data("test")
        assert result2 == "data_test"
        assert service.call_count == 2  # No caching

    def test_cached_decorator_different_args(self):
        """Test cached decorator with different argument types."""

        class TestService:
            def __init__(self):
                self.cache_manager = CacheManager()
                self.call_count = 0

            @cached(ttl=60)
            def get_data(self, param: str, limit: int = 10) -> str:
                self.call_count += 1
                return f"data_{param}_{limit}"

        service = TestService()

        service.get_data("test", limit=10)
        assert service.call_count == 1

        # Same args - cache hit
        service.get_data("test", limit=10)
        assert service.call_count == 1

        # Different args - cache miss
        service.get_data("test", limit=20)
        assert service.call_count == 2
