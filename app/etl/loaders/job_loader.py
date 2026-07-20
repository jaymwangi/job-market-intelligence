"""Job loader for persisting validated jobs to the database."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID
from typing import Set

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.etl.schemas.validated import JobValidated
from app.etl.schemas.metrics import PipelineMetrics
from app.repositories.job_repository import JobRepository
from app.models.skill import Skill
from app.models.job_skill import JobSkill
from app.models.job import Job
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class UpsertResult:
    """Result of a job upsert operation."""

    inserted: int = 0
    updated: int = 0


@dataclass
class SkillResult:
    """Result of skill processing operation."""

    skills_added: int = 0
    relationships_added: int = 0


@dataclass
class LoadResult:
    """Summary of a loading operation."""

    processed: int = 0
    inserted: int = 0
    updated: int = 0
    purged: int = 0
    skills_added: int = 0
    relationships_added: int = 0
    errors: list[str] = field(default_factory=list)


class JobLoader:
    """
    Loads validated jobs into the database with upsert support.

    Transaction management belongs to the caller.
    This class never commits or rolls back.

    All-or-nothing semantics: if any job fails, the entire batch fails.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.job_repo = JobRepository(db_session)

    def upsert(self, jobs: list[JobValidated]) -> LoadResult:
        """
        Upsert validated jobs into the database.

        All-or-nothing semantics: if any job fails, the entire batch fails.

        Args:
            jobs: List of validated JobValidated objects

        Returns:
            LoadResult: Summary of the loading operation

        Raises:
            Exception: If any database operation fails

        Note:
            Caller owns the transaction. This method only flushes.
            Caller must commit or rollback.
        """
        result = LoadResult(processed=len(jobs))

        if not jobs:
            return result

        # Phase 1: Upsert jobs
        upsert_result = self._upsert_jobs(jobs)
        result.inserted = upsert_result.inserted
        result.updated = upsert_result.updated

        # Phase 2: Process skills and relationships
        skill_result = self._process_skills(jobs)
        result.skills_added = skill_result.skills_added
        result.relationships_added = skill_result.relationships_added

        # Phase 3: Apply retention policy (if configured)
        if settings.pipeline_retention_days > 0:
            result.purged = self._purge_old_jobs()

        # Final flush - caller handles commit
        self.db_session.flush()

        logger.info(
            "Load complete: inserted=%d, updated=%d, "
            "skills=%d, relationships=%d, purged=%d",
            result.inserted,
            result.updated,
            result.skills_added,
            result.relationships_added,
            result.purged,
        )

        return result

    def _upsert_jobs(self, jobs: list[JobValidated]) -> UpsertResult:
        """
        Upsert jobs via repository.

        All-or-nothing: any exception aborts the entire batch.

        Returns:
            UpsertResult with inserted and updated counts
        """
        inserted = 0
        updated = 0

        # Get existing jobs to track insert vs update
        source_ids = [j.source_id for j in jobs]
        existing_jobs = self.db_session.query(Job).filter(
            Job.source_id.in_(source_ids)
        ).all()
        existing_source_ids = {j.source_id for j in existing_jobs}

        for job in jobs:
            is_existing = job.source_id in existing_source_ids

            # Let exceptions propagate - all-or-nothing
            self.job_repo.upsert_from_validated(job)

            if is_existing:
                updated += 1
            else:
                inserted += 1
                existing_source_ids.add(job.source_id)

        # Flush to get job IDs for skill relationships
        self.db_session.flush()

        return UpsertResult(
            inserted=inserted,
            updated=updated,
        )

    def _process_skills(self, jobs: list[JobValidated]) -> SkillResult:
        """
        Process skills and create relationships.

        Uses PostgreSQL ON CONFLICT DO NOTHING via savepoints
        to handle duplicates gracefully.

        All-or-nothing for non-duplicate errors.

        Returns:
            SkillResult with skills_added and relationships_added counts
        """
        # Collect all unique skills and job-skill pairs
        all_skills: Set[str] = set()
        job_skills: list[tuple[str, str]] = []  # (source_id, skill_name)

        for job in jobs:
            if not job.skills:
                continue

            for skill in job.skills:
                skill_lower = skill.lower()
                all_skills.add(skill_lower)
                job_skills.append((job.source_id, skill_lower))

        if not all_skills:
            return SkillResult()

        # Bulk insert new skills using add_all()
        existing_skills = self.db_session.query(Skill).filter(
            Skill.name.in_(all_skills)
        ).all()
        existing_skill_names = {s.name for s in existing_skills}

        new_skills = [
            Skill(name=name)
            for name in all_skills
            if name not in existing_skill_names
        ]

        skills_added = 0
        if new_skills:
            self.db_session.add_all(new_skills)
            self.db_session.flush()  # Need IDs for relationships
            skills_added = len(new_skills)

        # Build skill name to ID mapping
        all_skill_objects = self.db_session.query(Skill).filter(
            Skill.name.in_(all_skills)
        ).all()
        skill_map = {s.name: s.id for s in all_skill_objects}

        # Get job IDs by source_id
        source_ids = [j.source_id for j in jobs]
        jobs_db = self.db_session.query(Job).filter(
            Job.source_id.in_(source_ids)
        ).all()
        job_map = {j.source_id: j.id for j in jobs_db}

        # Build relationships (deduplicate before insert)
        relationships: list[JobSkill] = []
        seen: set[tuple[UUID, UUID]] = set()

        for source_id, skill_name in job_skills:
            job_id = job_map.get(source_id)
            skill_id = skill_map.get(skill_name)

            if job_id and skill_id:
                key = (job_id, skill_id)
                if key not in seen:
                    seen.add(key)
                    relationships.append(
                        JobSkill(job_id=job_id, skill_id=skill_id)
                    )

        # Bulk insert relationships with duplicate handling
        # using savepoint to isolate duplicate errors
        relationships_added = 0
        if relationships:
            # Split into smaller batches to avoid query size limits
            batch_size = 100
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i:i + batch_size]
                try:
                    with self.db_session.begin_nested():
                        self.db_session.add_all(batch)
                        relationships_added += len(batch)
                except IntegrityError:
                    # Some duplicates exist - fall back to individual inserts
                    # Each insert is isolated by the savepoint
                    with self.db_session.begin_nested():
                        added = 0
                        for rel in batch:
                            try:
                                self.db_session.add(rel)
                                self.db_session.flush()
                                added += 1
                            except IntegrityError:
                                # Duplicate - skip (ON CONFLICT DO NOTHING equivalent)
                                pass
                        relationships_added += added

        return SkillResult(
            skills_added=skills_added,
            relationships_added=relationships_added,
        )

    def _purge_old_jobs(self) -> int:
        """
        Delete jobs older than retention period.

        The repository handles all deletion logic including relationships.
        """
        cutoff_date = datetime.now(UTC) - timedelta(
            days=settings.pipeline_retention_days
        )

        purged_count = self.job_repo.delete_jobs_older_than(cutoff_date)

        logger.info(
            "Purged %d jobs older than %d days",
            purged_count,
            settings.pipeline_retention_days,
        )

        return purged_count

    def to_metrics(self, result: LoadResult) -> PipelineMetrics:
        """
        Convert LoadResult to PipelineMetrics.

        Args:
            result: LoadResult from upsert operation

        Returns:
            PipelineMetrics with typed metrics
        """
        return PipelineMetrics(
            inserted=result.inserted,
            updated=result.updated,
            purged=result.purged,
            skills_added=result.skills_added,
            relationships_added=result.relationships_added,
        )