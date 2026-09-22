from unittest.mock import patch

import pytest

from app.core.metrics import MetricsCollector


class TestMetricsCollector:
    def test_initializes_with_empty_metrics(self):
        collector = MetricsCollector()

        assert collector.request_counts == {}
        assert collector.error_counts == {}
        assert collector.response_times == {}
        assert collector.max_samples_per_endpoint == 1000
        assert isinstance(collector.start_time, float)

    def test_record_request_records_successful_request(self):
        collector = MetricsCollector()

        collector.record_request("/api/jobs", 200, 125.5)

        assert collector.request_counts["/api/jobs"] == 1
        assert collector.error_counts["/api/jobs"] == 0
        assert collector.response_times["/api/jobs"] == [125.5]

    def test_record_request_records_error(self):
        collector = MetricsCollector()

        collector.record_request("/api/jobs", 404, 50.0)

        assert collector.request_counts["/api/jobs"] == 1
        assert collector.error_counts["/api/jobs"] == 1
        assert collector.response_times["/api/jobs"] == [50.0]

    @pytest.mark.parametrize("status_code", [400, 401, 404, 500, 503])
    def test_record_request_counts_all_error_status_codes(self, status_code):
        collector = MetricsCollector()

        collector.record_request("/api/jobs", status_code, 10.0)

        assert collector.error_counts["/api/jobs"] == 1

    def test_record_request_does_not_count_success_as_error(self):
        collector = MetricsCollector()

        collector.record_request("/api/jobs", 399, 10.0)

        assert collector.error_counts["/api/jobs"] == 0

    def test_normalize_endpoint_replaces_uuid(self):
        collector = MetricsCollector()

        endpoint = "/api/jobs/550e8400-e29b-41d4-a716-446655440000"

        assert collector._normalize_endpoint(endpoint) == "/api/jobs/{id}"

    def test_normalize_endpoint_replaces_numeric_id(self):
        collector = MetricsCollector()

        assert collector._normalize_endpoint("/api/jobs/12345") == "/api/jobs/{id}"

    def test_normalize_endpoint_replaces_multiple_numeric_ids(self):
        collector = MetricsCollector()

        endpoint = "/api/users/123/jobs/456"

        assert collector._normalize_endpoint(endpoint) == "/api/users/{id}/jobs/{id}"

    def test_normalize_endpoint_leaves_non_id_path_unchanged(self):
        collector = MetricsCollector()

        endpoint = "/api/jobs/search"

        assert collector._normalize_endpoint(endpoint) == endpoint

    def test_record_request_aggregates_normalized_endpoints(self):
        collector = MetricsCollector()

        collector.record_request("/api/jobs/123", 200, 10.0)
        collector.record_request("/api/jobs/456", 200, 20.0)

        assert collector.request_counts["/api/jobs/{id}"] == 2
        assert collector.response_times["/api/jobs/{id}"] == [10.0, 20.0]

    def test_record_request_removes_oldest_sample_when_limit_reached(self):
        collector = MetricsCollector()
        collector.max_samples_per_endpoint = 2

        collector.record_request("/api/jobs", 200, 10.0)
        collector.record_request("/api/jobs", 200, 20.0)
        collector.record_request("/api/jobs", 200, 30.0)

        assert collector.response_times["/api/jobs"] == [20.0, 30.0]

    def test_get_metrics_with_no_requests(self):
        collector = MetricsCollector()

        with (
            patch("app.core.metrics.time.perf_counter", return_value=10.0),
            patch("app.core.metrics.datetime") as mock_datetime,
        ):
            collector.start_time = 5.0
            mock_datetime.now.return_value.isoformat.return_value = "2026-09-08T00:00:00+00:00"

            metrics = collector.get_metrics()

        assert metrics["uptime_seconds"] == 5.0
        assert metrics["total_requests"] == 0
        assert metrics["total_errors"] == 0
        assert metrics["error_rate"] == 0
        assert metrics["endpoints"] == {}
        assert metrics["timestamp"] == "2026-09-08T00:00:00+00:00"

    def test_get_metrics_calculates_request_statistics(self):
        collector = MetricsCollector()
        collector.start_time = 10.0

        collector.record_request("/api/jobs", 200, 10.0)
        collector.record_request("/api/jobs", 200, 20.0)
        collector.record_request("/api/jobs", 500, 30.0)
        collector.record_request("/api/users", 404, 40.0)

        with patch("app.core.metrics.time.perf_counter", return_value=15.0):
            metrics = collector.get_metrics()

        assert metrics["uptime_seconds"] == 5.0
        assert metrics["total_requests"] == 4
        assert metrics["total_errors"] == 2
        assert metrics["error_rate"] == 50.0

        jobs = metrics["endpoints"]["/api/jobs"]
        assert jobs["requests"] == 3
        assert jobs["errors"] == 1
        assert jobs["avg_response_ms"] == 20.0
        assert jobs["p95_response_ms"] == 30.0
        assert jobs["min_response_ms"] == 10.0
        assert jobs["max_response_ms"] == 30.0

        users = metrics["endpoints"]["/api/users"]
        assert users["requests"] == 1
        assert users["errors"] == 1
        assert users["avg_response_ms"] == 40.0
        assert users["p95_response_ms"] == 40.0
        assert users["min_response_ms"] == 40.0
        assert users["max_response_ms"] == 40.0

    def test_get_metrics_handles_empty_response_times(self):
        collector = MetricsCollector()

        collector.request_counts["/api/empty"] = 1
        collector.error_counts["/api/empty"] = 0
        collector.response_times["/api/empty"] = []

        metrics = collector.get_metrics()

        endpoint = metrics["endpoints"]["/api/empty"]

        assert endpoint["requests"] == 1
        assert endpoint["errors"] == 0
        assert endpoint["avg_response_ms"] == 0
        assert endpoint["p95_response_ms"] == 0
        assert endpoint["min_response_ms"] == 0
        assert endpoint["max_response_ms"] == 0

    def test_reset_clears_all_metrics(self):
        collector = MetricsCollector()

        collector.record_request("/api/jobs", 500, 100.0)
        old_start_time = collector.start_time

        with patch("app.core.metrics.time.perf_counter", return_value=999.0):
            collector.reset()

        assert collector.request_counts == {}
        assert collector.error_counts == {}
        assert collector.response_times == {}
        assert collector.start_time == 999.0
        assert collector.start_time != old_start_time
