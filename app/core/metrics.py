"""
Basic operational metrics collection for production monitoring.
"""

import logging
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and store operational metrics for monitoring."""

    def __init__(self) -> None:
        self.start_time: float = time.perf_counter()
        self.request_counts: dict[str, int] = defaultdict(int)
        self.error_counts: dict[str, int] = defaultdict(int)
        self.response_times: dict[str, list[float]] = defaultdict(list)
        self.max_samples_per_endpoint: int = 1000

    def record_request(self, endpoint: str, status_code: int, duration_ms: float) -> None:
        """
        Record a request metric.

        Args:
            endpoint: API endpoint path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
        """
        # Extract base endpoint without parameters for aggregation
        base_endpoint = self._normalize_endpoint(endpoint)

        self.request_counts[base_endpoint] += 1

        if status_code >= 400:
            self.error_counts[base_endpoint] += 1

        # Keep only the last N samples to bound memory usage
        if len(self.response_times[base_endpoint]) >= self.max_samples_per_endpoint:
            self.response_times[base_endpoint].pop(0)
        self.response_times[base_endpoint].append(duration_ms)

    def _normalize_endpoint(self, endpoint: str) -> str:
        """Normalize endpoint path by removing IDs for aggregation."""
        import re

        # Remove UUIDs
        normalized = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            endpoint,
        )
        # Remove numeric IDs
        normalized = re.sub(r"/\d+", "/{id}", normalized)
        return normalized

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics."""
        uptime = time.perf_counter() - self.start_time

        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())

        metrics: dict[str, Any] = {
            "uptime_seconds": round(uptime, 1),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (
                round(total_errors / total_requests * 100, 2) if total_requests > 0 else 0
            ),
            "endpoints": {},
            "timestamp": datetime.now(UTC).isoformat(),
        }

        for endpoint, times in self.response_times.items():
            if times:
                avg_time = sum(times) / len(times)
                sorted_times = sorted(times)
                p95_index = int(len(sorted_times) * 0.95)
                p95_time = sorted_times[p95_index] if len(sorted_times) > 1 else avg_time
                min_time = min(times)
                max_time = max(times)
            else:
                avg_time = p95_time = min_time = max_time = 0

            metrics["endpoints"][endpoint] = {
                "requests": self.request_counts.get(endpoint, 0),
                "errors": self.error_counts.get(endpoint, 0),
                "avg_response_ms": round(avg_time, 2),
                "p95_response_ms": round(p95_time, 2),
                "min_response_ms": round(min_time, 2),
                "max_response_ms": round(max_time, 2),
            }

        return metrics

    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        self.request_counts.clear()
        self.error_counts.clear()
        self.response_times.clear()
        self.start_time = time.perf_counter()


# Global metrics collector instance
metrics_collector = MetricsCollector()
