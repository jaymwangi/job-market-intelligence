"""Database composition checker for acquisition strategy."""

from typing import Optional
import logging
from sqlalchemy.orm import Session

from app.models.job import Job
from .models import DatabaseComposition

logger = logging.getLogger(__name__)


class DatabaseCompositionChecker:
    """
    Queries the database to determine the current composition of jobs
    (tech vs non‑tech vs unclassified) for use in acquisition decisions.
    """

    def __init__(self, db_session: Session):
        """
        Initialize with a SQLAlchemy session.

        Args:
            db_session: Active database session.
        """
        self.session = db_session

    def get_composition(
        self,
        country: Optional[str] = None,
        include_unclassified: bool = True
    ) -> DatabaseComposition:
        """
        Retrieve the current job composition from the database.

        Args:
            country: Optional ISO country code to filter jobs.
            include_unclassified: Whether to count jobs with null is_tech_role.

        Returns:
            DatabaseComposition with total, tech, non‑tech, and unclassified counts.
        """
        query = self.session.query(Job)

        # Use the actual column name: country_code (from your Job model)
        if country:
            query = query.filter(Job.country_code == country)

        # Count totals
        total = query.count()

        # Count tech (is_tech_role == True)
        tech_count = query.filter(Job.is_tech_role == True).count()

        # Count non‑tech (is_tech_role == False)
        non_tech_count = query.filter(Job.is_tech_role == False).count()

        # Count unclassified (is_tech_role IS NULL)
        if include_unclassified:
            unclassified_count = query.filter(Job.is_tech_role.is_(None)).count()
        else:
            unclassified_count = 0

        logger.debug(
            f"Composition for {country or 'all'}: total={total}, "
            f"tech={tech_count}, non_tech={non_tech_count}, "
            f"unclassified={unclassified_count}"
        )

        return DatabaseComposition(
            total_jobs=total,
            tech_count=tech_count,
            non_tech_count=non_tech_count,
            unclassified_count=unclassified_count
        )

    def get_tech_deficit(self, country: Optional[str] = None) -> int:
        """
        Calculate how many tech jobs are needed to reach parity with non‑tech.

        Returns:
            Number of tech jobs needed, or 0 if already at or above parity.
        """
        comp = self.get_composition(country)
        return comp.tech_deficit

    def has_reached_parity(
        self,
        country: Optional[str] = None,
        tolerance: float = 0.05
    ) -> bool:
        """
        Check if the tech ratio is within tolerance of 0.5.

        Args:
            country: Optional country filter.
            tolerance: Allowed deviation from 0.5.

        Returns:
            True if tech ratio is between 0.5‑tolerance and 0.5+tolerance.
        """
        comp = self.get_composition(country)
        # Call the method on the composition object
        return comp.has_reached_parity(tolerance)