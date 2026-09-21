"""Unit tests for acquisition data models."""

from app.etl.acquisition.models import (
    AcquisitionMode,
    AcquisitionResult,
    AcquisitionStats,
    DatabaseComposition,
)


class TestAcquisitionMode:
    def test_enum_values(self):
        assert AcquisitionMode.CATCH_UP.value == "catch_up"
        assert AcquisitionMode.BALANCED.value == "balanced"


class TestDatabaseComposition:
    def test_default_values(self):
        composition = DatabaseComposition()

        assert composition.total_jobs == 0
        assert composition.tech_count == 0
        assert composition.non_tech_count == 0
        assert composition.unclassified_count == 0
        assert composition.classified_total == 0
        assert composition.tech_ratio == 0.0
        assert composition.tech_deficit == 0
        assert composition.has_reached_parity() is False

    def test_classified_total(self):
        composition = DatabaseComposition(
            total_jobs=100,
            tech_count=40,
            non_tech_count=30,
            unclassified_count=30,
        )

        assert composition.classified_total == 70

    def test_tech_ratio(self):
        composition = DatabaseComposition(
            total_jobs=100,
            tech_count=40,
            non_tech_count=40,
        )

        assert composition.tech_ratio == 0.5

    def test_tech_deficit_when_non_tech_exceeds_tech(self):
        composition = DatabaseComposition(
            total_jobs=100,
            tech_count=30,
            non_tech_count=50,
        )

        assert composition.tech_deficit == 20

    def test_tech_deficit_never_negative(self):
        composition = DatabaseComposition(
            total_jobs=100,
            tech_count=60,
            non_tech_count=40,
        )

        assert composition.tech_deficit == 0

    def test_parity_at_exact_half(self):
        composition = DatabaseComposition(
            tech_count=50,
            non_tech_count=50,
        )

        assert composition.has_reached_parity() is True

    def test_parity_within_tolerance(self):
        composition = DatabaseComposition(
            tech_count=52,
            non_tech_count=48,
        )

        assert composition.has_reached_parity(tolerance=0.05) is True

    def test_parity_outside_tolerance(self):
        composition = DatabaseComposition(
            tech_count=60,
            non_tech_count=40,
        )

        assert composition.has_reached_parity(tolerance=0.05) is False


class TestAcquisitionStats:
    def test_remaining_tech_needed(self):
        stats = AcquisitionStats(
            tech_deficit=20,
            tech_classified_acquired=7,
        )

        assert stats.remaining_tech_needed == 13

    def test_remaining_tech_needed_never_negative(self):
        stats = AcquisitionStats(
            tech_deficit=5,
            tech_classified_acquired=10,
        )

        assert stats.remaining_tech_needed == 0

    def test_jobs_acquired_property(self):
        stats = AcquisitionStats(jobs_acquired_this_run=25)

        assert stats.jobs_acquired == 25

    def test_total_queries_used(self):
        stats = AcquisitionStats(
            broad_queries_used=4,
            tech_queries_used=6,
        )

        assert stats.total_queries_used == 10


class TestAcquisitionResult:
    def test_compute_metrics_with_final_composition(self):
        result = AcquisitionResult(
            unique_jobs=[{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}],
            duplicates=[{"id": 5}],
            tech_intent_jobs=[{"id": 1}, {"id": 2}, {"id": 3}],
            broad_intent_jobs=[{"id": 4}],
            tech_classified_jobs=[{"id": 1}, {"id": 2}],
            non_tech_classified_jobs=[{"id": 4}],
            unclassified_jobs=[{"id": 3}],
            final_composition=DatabaseComposition(
                tech_count=60,
                non_tech_count=50,
            ),
        )

        result.compute_metrics()

        assert result.unique_count == 4
        assert result.duplicate_count == 1
        assert result.tech_intent_count == 3
        assert result.broad_intent_count == 1
        assert result.tech_classified_count == 2
        assert result.non_tech_classified_count == 1
        assert result.unclassified_count == 1

        assert result.actual_classified_tech_ratio == 2 / 3
        assert result.reached_parity is False
        assert result.tech_deficit_remaining == 0

    def test_compute_metrics_with_initial_composition_only(self):
        result = AcquisitionResult(
            tech_classified_jobs=[{"id": 1}, {"id": 2}],
            non_tech_classified_jobs=[{"id": 3}],
            initial_composition=DatabaseComposition(
                tech_count=20,
                non_tech_count=30,
            ),
        )

        result.compute_metrics()

        assert result.actual_classified_tech_ratio == 2 / 3
        assert result.reached_parity is False
        assert result.tech_deficit_remaining == 8

    def test_compute_metrics_with_no_classified_jobs(self):
        result = AcquisitionResult()

        result.compute_metrics()

        assert result.actual_classified_tech_ratio == 0.0
        assert result.reached_parity is False
        assert result.tech_deficit_remaining == 0

    def test_compute_metrics_reaches_parity(self):
        result = AcquisitionResult(
            tech_classified_jobs=[{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
            non_tech_classified_jobs=[{"id": 6}, {"id": 7}, {"id": 8}, {"id": 9}, {"id": 10}],
        )

        result.compute_metrics()

        assert result.actual_classified_tech_ratio == 0.5
        assert result.reached_parity is True
        assert result.has_reached_parity is True

    def test_result_properties(self):
        result = AcquisitionResult(
            tech_classified_jobs=[{"id": 1}, {"id": 2}],
            non_tech_classified_jobs=[{"id": 3}],
            broad_queries_used=2,
            tech_queries_used=5,
        )

        result.compute_metrics()

        assert result.total_classified == 3
        assert result.total_queries_used == 7
        assert result.tech_ratio == 2 / 3
        assert result.has_reached_parity is False
