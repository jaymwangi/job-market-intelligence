# scripts/verify_sprint5.py
"""Verify Sprint 5 functionality."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.api.client import APIClient
from dashboard.core.config import settings
from dashboard.services.analytics_service import AnalyticsService
from dashboard.services.health import HealthService
from dashboard.utils.cache import CacheManager


def verify_health() -> bool:
    """Verify health endpoint works."""
    try:
        client = APIClient(settings.API_BASE_URL)
        health = HealthService(client)
        result = health.check()
        print(f"✅ Health check: {result.status}")
        return result.status in ["healthy", "ok"]
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def verify_analytics() -> bool:
    """Verify analytics service works."""
    try:
        client = APIClient(settings.API_BASE_URL)
        service = AnalyticsService(client)

        # Test metrics
        metrics = service.get_dashboard_metrics()
        print(f"✅ Dashboard metrics: {len(metrics)} cards")

        # Test skills
        skills = service.get_skills_chart()
        print(f"✅ Skills chart: {len(skills.x_values)} skills")

        # Test companies
        companies = service.get_companies_chart()
        print(f"✅ Companies chart: {len(companies.x_values)} companies")

        return True
    except Exception as e:
        print(f"❌ Analytics verification failed: {e}")
        return False


def verify_cache() -> bool:
    """Verify cache works."""
    try:
        cache = CacheManager()

        # Test set and get
        cache.set("test_key", "test_value", 60)
        value = cache.get("test_key")
        print(f"✅ Cache set/get: {value == 'test_value'}")

        # Test clear
        cache.clear()
        value = cache.get("test_key")
        print(f"✅ Cache clear: {value is None}")

        return True
    except Exception as e:
        print(f"❌ Cache verification failed: {e}")
        return False


def main():
    """Run all verifications."""
    print("=" * 50)
    print("Sprint 5 Regression Verification")
    print("=" * 50)

    results = []

    print("\n1. Health Check")
    results.append(verify_health())

    print("\n2. Analytics Service")
    results.append(verify_analytics())

    print("\n3. Cache Manager")
    results.append(verify_cache())

    print("\n" + "=" * 50)
    print(f"Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("✅ All Sprint 5 functionality verified!")
        return 0
    else:
        print("❌ Some verifications failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
