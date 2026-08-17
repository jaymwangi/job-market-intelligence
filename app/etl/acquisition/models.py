# app/etl/acquisition/models.py

"""Data models for acquisition strategy."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import StrEnum


class AcquisitionMode(StrEnum):
    """Acquisition modes."""
    CATCH_UP = "catch_up"
    BALANCED = "balanced"


@dataclass
class DatabaseComposition:
    """Composition of jobs in the database."""
    total_jobs: int = 0
    tech_count: int = 0
    non_tech_count: int = 0
    unclassified_count: int = 0

    @property
    def classified_total(self) -> int:
        return self.tech_count + self.non_tech_count

    @property
    def tech_ratio(self) -> float:
        if self.classified_total == 0:
            return 0.0
        return self.tech_count / self.classified_total

    @property
    def tech_deficit(self) -> int:
        """Number of tech jobs needed to reach parity (non_tech_count - tech_count)."""
        return max(0, self.non_tech_count - self.tech_count)

    def has_reached_parity(self, tolerance: float = 0.05) -> bool:
        """Check if tech ratio is within tolerance of 0.5."""
        return abs(self.tech_ratio - 0.5) <= tolerance


@dataclass
class AcquisitionStats:
    """Statistics for acquisition progress."""
    # Database composition
    db_total: int = 0
    db_tech: int = 0
    db_non_tech: int = 0
    db_unclassified: int = 0
    db_tech_ratio: float = 0.0
    db_has_parity: bool = False
    tech_deficit: int = 0

    # Intent counts
    tech_intent_acquired: int = 0
    broad_intent_acquired: int = 0

    # Classification counts
    tech_classified_acquired: int = 0
    non_tech_classified_acquired: int = 0
    unclassified_acquired: int = 0

    # Overall
    jobs_acquired_this_run: int = 0
    duplicates_this_run: int = 0

    # Mode and queries
    mode: AcquisitionMode = AcquisitionMode.BALANCED
    broad_queries_used: int = 0
    tech_queries_used: int = 0

    # Targets
    target_tech_ratio: float = 0.5
    max_jobs_per_run: int = 2000
    
    # Batch tracking
    batch_count: int = 0

    @property
    def remaining_tech_needed(self) -> int:
        """How many more tech jobs are needed to reach parity."""
        return max(0, self.tech_deficit - self.tech_classified_acquired)

    @property
    def jobs_acquired(self) -> int:
        return self.jobs_acquired_this_run

    @property
    def total_queries_used(self) -> int:
        """Total number of queries used (broad + tech)."""
        return self.broad_queries_used + self.tech_queries_used


@dataclass
class AcquisitionResult:
    """Complete result of an acquisition run."""
    jobs: List[Dict[str, Any]] = field(default_factory=list)
    tech_intent_jobs: List[Dict[str, Any]] = field(default_factory=list)
    broad_intent_jobs: List[Dict[str, Any]] = field(default_factory=list)
    tech_classified_jobs: List[Dict[str, Any]] = field(default_factory=list)
    non_tech_classified_jobs: List[Dict[str, Any]] = field(default_factory=list)
    unclassified_jobs: List[Dict[str, Any]] = field(default_factory=list)
    unique_jobs: List[Dict[str, Any]] = field(default_factory=list)
    duplicates: List[Dict[str, Any]] = field(default_factory=list)

    # Composition
    initial_composition: Optional[DatabaseComposition] = None
    final_composition: Optional[DatabaseComposition] = None

    # Mode
    mode: AcquisitionMode = AcquisitionMode.BALANCED
    mode_changed: bool = False

    # Counts
    unique_count: int = 0
    duplicate_count: int = 0
    tech_intent_count: int = 0
    broad_intent_count: int = 0
    tech_classified_count: int = 0
    non_tech_classified_count: int = 0
    unclassified_count: int = 0
    broad_queries_used: int = 0
    tech_queries_used: int = 0

    # Ratios and status
    target_tech_ratio: float = 0.5
    actual_classified_tech_ratio: float = 0.0
    reached_parity: bool = False
    tech_deficit_remaining: int = 0

    # Batch tracking
    batch_count: int = 0

    # Duration (optional)
    duration_seconds: float = 0.0

    # ✅ Query metrics - tracks per-query performance
    query_metrics: List[Dict[str, Any]] = field(default_factory=list)

    def compute_metrics(self):
        """Compute derived metrics."""
        self.unique_count = len(self.unique_jobs)
        self.duplicate_count = len(self.duplicates)
        self.tech_intent_count = len(self.tech_intent_jobs)
        self.broad_intent_count = len(self.broad_intent_jobs)
        self.tech_classified_count = len(self.tech_classified_jobs)
        self.non_tech_classified_count = len(self.non_tech_classified_jobs)
        self.unclassified_count = len(self.unclassified_jobs)

        classified_total = self.tech_classified_count + self.non_tech_classified_count
        if classified_total > 0:
            self.actual_classified_tech_ratio = self.tech_classified_count / classified_total
        else:
            self.actual_classified_tech_ratio = 0.0

        # Check parity against target (with tolerance)
        self.reached_parity = abs(self.actual_classified_tech_ratio - self.target_tech_ratio) <= 0.05

        # Tech deficit remaining
        if self.final_composition:
            self.tech_deficit_remaining = self.final_composition.tech_deficit
        elif self.initial_composition:
            deficit = self.initial_composition.tech_deficit
            remaining = max(0, deficit - self.tech_classified_count)
            self.tech_deficit_remaining = remaining
        else:
            self.tech_deficit_remaining = 0

    @property
    def total_classified(self) -> int:
        """Total number of classified jobs."""
        return self.tech_classified_count + self.non_tech_classified_count

    @property
    def total_queries_used(self) -> int:
        """Total number of queries used (broad + tech)."""
        return self.broad_queries_used + self.tech_queries_used

    @property
    def tech_ratio(self) -> float:
        """Alias for actual_classified_tech_ratio."""
        return self.actual_classified_tech_ratio

    @property
    def has_reached_parity(self) -> bool:
        """Alias for reached_parity."""
        return self.reached_parity