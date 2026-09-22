"""Unit tests for pipeline metrics schema."""

import pytest

from app.etl.schemas.metrics import PipelineMetrics


class TestPipelineMetrics:
    """Test suite for PipelineMetrics."""

    def test_total_processed(self):
        """Test total processed jobs."""
        metrics = PipelineMetrics(extracted=25)

        assert metrics.total_processed() == 25

    def test_total_loaded(self):
        """Test total loaded jobs."""
        metrics = PipelineMetrics(inserted=15, updated=7)

        assert metrics.total_loaded() == 22

    def test_success_rate_with_processed_jobs(self):
        """Test success rate when jobs were processed."""
        metrics = PipelineMetrics(extracted=100, validated=85)

        assert metrics.success_rate() == pytest.approx(85.0)

    def test_success_rate_with_no_processed_jobs(self):
        """Test success rate when no jobs were processed."""
        metrics = PipelineMetrics()

        assert metrics.success_rate() == 100.0
