"""Job loader for persisting validated jobs to the database."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import tuple_
from sqlalchemy.exc import IntegrityError, PendingRollbackError
from sqlalchemy.orm import Session

from app.etl.schemas.metrics import PipelineMetrics
from app.etl.schemas.validated import JobValidated
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill
from app.repositories.job_repository import JobRepository
from config.settings import settings

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

        try:
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
                "Load complete: inserted=%d, updated=%d, " "skills=%d, relationships=%d, purged=%d",
                result.inserted,
                result.updated,
                result.skills_added,
                result.relationships_added,
                result.purged,
            )

            return result

        except (IntegrityError, PendingRollbackError):
            logger.exception("Database error during job load")
            raise

    def _upsert_jobs(self, jobs: list[JobValidated]) -> UpsertResult:
        """
        Upsert jobs via repository.

        Uses the composite key (source_site, source_id) to match
        the database unique constraint 'uq_job_source'.

        All-or-nothing: any exception aborts the entire batch.

        Returns:
            UpsertResult with inserted and updated counts.
        """
        if not jobs:
            return UpsertResult()

        # Build composite keys matching uq_job_source
        source_keys = {(job.source, job.source_id) for job in jobs}

        existing_jobs = (
            self.db_session.query(Job)
            .filter(tuple_(Job.source_site, Job.source_id).in_(source_keys))
            .all()
        )

        existing_keys = {(job.source_site, job.source_id) for job in existing_jobs}

        job_repo = JobRepository(self.db_session)

        inserted = 0
        updated = 0

        for job in jobs:
            key = (job.source, job.source_id)

            # Let exceptions propagate - all-or-nothing
            job_repo.upsert_from_validated(job)

            if key in existing_keys:
                updated += 1
            else:
                inserted += 1
                existing_keys.add(key)

        # Flush to get job IDs for skill relationships
        self.db_session.flush()

        return UpsertResult(
            inserted=inserted,
            updated=updated,
        )

    def _process_skills(self, jobs: list[JobValidated]) -> SkillResult:
        """
        Process skills and create job-skill relationships.

        Uses composite key (source_site, source_id) for job lookups
        to maintain consistency with the database unique constraint.

        Database reads are completed before relationship inserts.
        Relationships are inserted in batches using savepoints for
        transaction isolation and duplicate handling.

        Returns:
            SkillResult with skills_added and relationships_added counts.
        """
        all_skills: set[str] = set()
        # Store (source_site, source_id, skill_name) for composite key consistency
        job_skills: list[tuple[str, str, str]] = []

        # ------------------------------------------------------------
        # 1. Collect unique skills and job-skill pairs in memory
        # ------------------------------------------------------------
        for job in jobs:
            if not job.skills:
                continue

            for skill in job.skills:
                skill_name = skill.strip().lower()

                if not skill_name:
                    continue

                all_skills.add(skill_name)
                # Store the full composite key to avoid source_id ambiguity
                job_skills.append((job.source, job.source_id, skill_name))

        if not all_skills:
            return SkillResult()

        # ------------------------------------------------------------
        # 2. Load existing skills
        # ------------------------------------------------------------
        existing_skills = self.db_session.query(Skill).filter(Skill.name.in_(all_skills)).all()

        existing_skill_names = {skill.name for skill in existing_skills}

        # ------------------------------------------------------------
        # 3. Insert missing skills
        # ------------------------------------------------------------
        new_skills = [Skill(name=name) for name in all_skills if name not in existing_skill_names]

        skills_added = 0

        if new_skills:
            self.db_session.add_all(new_skills)
            self.db_session.flush()
            skills_added = len(new_skills)

        # ------------------------------------------------------------
        # 4. Build skill → ID mapping
        # ------------------------------------------------------------
        all_skill_objects = self.db_session.query(Skill).filter(Skill.name.in_(all_skills)).all()

        skill_map = {skill.name: skill.id for skill in all_skill_objects}

        # ------------------------------------------------------------
        # 5. Load all corresponding jobs using composite key
        # ------------------------------------------------------------
        source_keys = list({(source_site, source_id) for source_site, source_id, _ in job_skills})

        jobs_db = (
            self.db_session.query(Job)
            .filter(tuple_(Job.source_site, Job.source_id).in_(source_keys))
            .all()
        )

        job_map = {(job.source_site, job.source_id): job.id for job in jobs_db}

        if not job_map:
            return SkillResult(
                skills_added=skills_added,
                relationships_added=0,
            )

        # ------------------------------------------------------------
        # 6. Load existing relationships ONCE
        # ------------------------------------------------------------
        job_ids = list(job_map.values())
        skill_ids = list(skill_map.values())

        existing_relationships = (
            self.db_session.query(JobSkill)
            .filter(
                JobSkill.job_id.in_(job_ids),
                JobSkill.skill_id.in_(skill_ids),
            )
            .all()
        )

        existing_pairs = {
            (relationship.job_id, relationship.skill_id) for relationship in existing_relationships
        }

        # ------------------------------------------------------------
        # 7. Build new relationships entirely in memory
        # ------------------------------------------------------------
        relationships: list[JobSkill] = []
        seen: set[tuple[UUID, UUID]] = set()

        # Use the stored composite key (source_site, source_id, skill_name)
        for source_site, source_id, skill_name in job_skills:
            key = (source_site, source_id)
            job_id = job_map.get(key)
            skill_id = skill_map.get(skill_name)

            if job_id is None or skill_id is None:
                continue

            pair_key = (job_id, skill_id)

            if pair_key in seen:
                continue

            if pair_key in existing_pairs:
                continue

            seen.add(pair_key)

            relationships.append(
                JobSkill(
                    job_id=job_id,
                    skill_id=skill_id,
                )
            )

        # ------------------------------------------------------------
        # 8. Insert relationships in batches with savepoints
        # ------------------------------------------------------------
        relationships_added = 0
        batch_size = 100

        for start in range(0, len(relationships), batch_size):
            batch = relationships[start : start + batch_size]

            try:
                with self.db_session.begin_nested():
                    self.db_session.add_all(batch)
                    self.db_session.flush()

                relationships_added += len(batch)

            except IntegrityError as e:
                logger.warning(
                    "Relationship batch contained duplicate/conflicting rows; "
                    "falling back to individual inserts for %d rows: %s",
                    len(batch),
                    e,
                )

                for relationship in batch:
                    try:
                        with self.db_session.begin_nested():
                            self.db_session.add(relationship)
                            self.db_session.flush()

                        relationships_added += 1

                    except IntegrityError as duplicate_error:
                        logger.debug(
                            "Skipping conflicting job-skill relationship "
                            "job_id=%s skill_id=%s: %s",
                            relationship.job_id,
                            relationship.skill_id,
                            duplicate_error,
                        )
                        continue

        logger.info(
            "Skills processed: skills_added=%d, "
            "relationships_added=%d, relationships_skipped=%d",
            skills_added,
            relationships_added,
            len(job_skills) - relationships_added,
        )

        return SkillResult(
            skills_added=skills_added,
            relationships_added=relationships_added,
        )

    def _purge_old_jobs(self) -> int:
        """
        Delete jobs older than retention period.

        The repository handles all deletion logic including relationships.
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=settings.pipeline_retention_days)

        job_repo = JobRepository(self.db_session)
        purged_count = job_repo.delete_jobs_older_than(cutoff_date)

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
