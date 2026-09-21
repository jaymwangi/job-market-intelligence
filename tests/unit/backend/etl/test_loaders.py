"""
Unit tests for ETL job loader.
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch,MagicMock

from sqlalchemy.exc import IntegrityError

import pytest

from app.etl.loaders.job_loader import (
    JobLoader,
    LoadResult,
    SkillResult,
    UpsertResult,
)
from app.etl.loaders.job_loader import (
    JobLoader,
    LoadResult,
    SkillResult,
    UpsertResult,
)
from app.etl.schemas.validated import JobValidated
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill

class TestJobLoader:
    """Test suite for JobLoader."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def loader(self, mock_db):
        """Create a JobLoader instance."""
        return JobLoader(mock_db)

    @pytest.fixture
    def valid_jobs(self):
        """Create validated job objects."""
        return [
            JobValidated(
                source="test_source",
                source_id="job_1",
                title="Python Developer",
                company="TechCorp",
                location="Remote",
                description="Test job",
                salary_currency="USD",
                url="https://example.com/job/1",
                posted_date=datetime.now(UTC),
            ),
            JobValidated(
                source="test_source",
                source_id="job_2",
                title="Data Engineer",
                company="DataInc",
                location="NY",
                description="Test job 2",
                salary_currency="USD",
                url="https://example.com/job/2",
                posted_date=datetime.now(UTC),
            ),
        ]

    @pytest.fixture
    def mock_job_repo(self):
        """Create a mock job repository."""
        return Mock()

    @pytest.fixture
    def no_existing_jobs(self, mock_db):
        """Configure database queries to return no existing records."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        return mock_db

    def test_init(self, loader, mock_db):
        """Test loader initialization."""
        assert loader.db_session == mock_db

    def test_load_result_defaults(self):
        """Test LoadResult default values."""
        result = LoadResult()

        assert result.processed == 0
        assert result.inserted == 0
        assert result.updated == 0
        assert result.purged == 0
        assert result.skills_added == 0
        assert result.relationships_added == 0
        assert result.errors == []

    def test_upsert_result_defaults(self):
        """Test UpsertResult default values."""
        result = UpsertResult()

        assert result.inserted == 0
        assert result.updated == 0

    def test_skill_result_defaults(self):
        """Test SkillResult default values."""
        result = SkillResult()

        assert result.skills_added == 0
        assert result.relationships_added == 0

    def test_upsert_empty_list(self, loader, mock_db):
        """Test upserting an empty list."""
        result = loader.upsert_in_batches([])

        assert isinstance(result, LoadResult)
        assert result.processed == 0
        assert result.inserted == 0
        assert result.updated == 0
        assert result.purged == 0
        assert result.skills_added == 0
        assert result.relationships_added == 0
        assert result.errors == []

        mock_db.flush.assert_not_called()

    def test_upsert_new_jobs(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test inserting new jobs."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                result = loader.upsert_in_batches(valid_jobs)

        assert result.processed == 2
        assert result.inserted == 2
        assert result.updated == 0
        assert result.skills_added == 0
        assert result.relationships_added == 0
        assert result.purged == 0
        assert result.errors == []

        assert mock_job_repo.upsert_from_validated.call_count == 2
        no_existing_jobs.flush.assert_called()

    def test_upsert_existing_jobs(
        self,
        loader,
        valid_jobs,
        mock_db,
        mock_job_repo,
    ):
        """Test updating existing jobs."""
        existing_job_1 = Mock()
        existing_job_1.source_site = "test_source"
        existing_job_1.source_id = "job_1"

        existing_job_2 = Mock()
        existing_job_2.source_site = "test_source"
        existing_job_2.source_id = "job_2"

        mock_db.query.return_value.filter.return_value.all.return_value = [
            existing_job_1,
            existing_job_2,
        ]

        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                result = loader.upsert_in_batches(valid_jobs)

        assert result.processed == 2
        assert result.inserted == 0
        assert result.updated == 2
        assert result.errors == []

        assert mock_job_repo.upsert_from_validated.call_count == 2

    def test_upsert_mixed_new_and_existing_jobs(
        self,
        loader,
        valid_jobs,
        mock_db,
        mock_job_repo,
    ):
        """Test loading a mixture of new and existing jobs."""
        existing_job = Mock()
        existing_job.source_site = "test_source"
        existing_job.source_id = "job_1"

        mock_db.query.return_value.filter.return_value.all.return_value = [existing_job]

        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                result = loader.upsert_in_batches(valid_jobs)

        assert result.processed == 2
        assert result.inserted == 1
        assert result.updated == 1
        assert result.errors == []

        assert mock_job_repo.upsert_from_validated.call_count == 2

    def test_upsert_does_not_commit(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test that the loader does not commit transactions."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                loader.upsert_in_batches(valid_jobs)

        no_existing_jobs.commit.assert_not_called()

    def test_upsert_does_not_rollback(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test that the loader does not rollback transactions."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                loader.upsert_in_batches(valid_jobs)

        no_existing_jobs.rollback.assert_not_called()

    def test_upsert_flushes_database(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test that the loader flushes database changes."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                loader.upsert_in_batches(valid_jobs)

        no_existing_jobs.flush.assert_called()

    def test_upsert_in_batches(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test processing jobs in multiple batches."""
        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                result = loader.upsert_in_batches(
                    valid_jobs,
                    batch_size=1,
                )

        assert result.processed == 2
        assert result.inserted == 2
        assert result.updated == 0
        assert mock_job_repo.upsert_from_validated.call_count == 2

    def test_upsert_batch_empty(self, loader):
        """Test that an empty batch returns an empty result."""
        result = loader._upsert_batch([])

        assert result.processed == 0
        assert result.inserted == 0
        assert result.updated == 0
        assert result.skills_added == 0
        assert result.relationships_added == 0

    def test_upsert_jobs_empty(self, loader):
        """Test that an empty job list returns an empty upsert result."""
        result = loader._upsert_jobs([])

        assert result.inserted == 0
        assert result.updated == 0

    def test_upsert_batch_integrity_error_is_reraised(self, loader, valid_jobs):
        """Test that IntegrityError is logged and re-raised."""
        error = IntegrityError("INSERT", {}, Exception("duplicate"))

        with patch.object(loader, "_upsert_jobs", side_effect=error):
            with pytest.raises(IntegrityError):
                loader._upsert_batch(valid_jobs)

    def test_upsert_purges_old_jobs(
        self,
        loader,
        valid_jobs,
        no_existing_jobs,
        mock_job_repo,
    ):
        """Test purging old jobs when retention is enabled."""
        mock_job_repo.delete_jobs_older_than.return_value = 7

        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                30,
            ):
                result = loader.upsert_in_batches(valid_jobs)

        assert result.purged == 7
        mock_job_repo.delete_jobs_older_than.assert_called_once()

    def test_upsert_database_error_propagates(
        self,
        loader,
        valid_jobs,
        mock_db,
        mock_job_repo,
    ):
        """Test that database errors propagate to the caller."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_job_repo.upsert_from_validated.side_effect = Exception("Database error")

        with patch(
            "app.etl.loaders.job_loader.JobRepository",
            return_value=mock_job_repo,
        ):
            with patch(
                "app.etl.loaders.job_loader.settings.pipeline_retention_days",
                0,
            ):
                with pytest.raises(Exception, match="Database error"):
                    loader.upsert_in_batches(valid_jobs)

        mock_db.commit.assert_not_called()
        mock_db.rollback.assert_not_called()

    def test_to_metrics(self, loader):
        """Test conversion from LoadResult to PipelineMetrics."""
        result = LoadResult(
            processed=10,
            inserted=6,
            updated=4,
            purged=2,
            skills_added=8,
            relationships_added=15,
        )

        metrics = loader.to_metrics(result)

        assert metrics.inserted == 6
        assert metrics.updated == 4
        assert metrics.purged == 2
        assert metrics.skills_added == 8
        assert metrics.relationships_added == 15

    def test_to_metrics_ignores_errors(self, loader):
        """Test that LoadResult errors are not included in PipelineMetrics."""
        result = LoadResult(
            processed=5,
            inserted=3,
            updated=2,
            errors=["example error"],
        )

        metrics = loader.to_metrics(result)

        assert metrics.inserted == 3
        assert metrics.updated == 2
        assert metrics.purged == 0
        assert metrics.skills_added == 0
        assert metrics.relationships_added == 0


    def test_process_skills_empty_and_blank_skills(self, loader):
        """Test that missing and blank skills produce no work."""
        jobs = [
            Mock(skills=None),
            Mock(skills=[]),
            Mock(skills=["", "   "]),
        ]

        result = loader._process_skills(jobs)

        assert result.skills_added == 0
        assert result.relationships_added == 0
        loader.db_session.query.assert_not_called()


    def test_process_skills_adds_new_skills_and_relationships(self, loader):
        """Test creating new skills and their job relationships."""
        job = Mock(
            source="test_source",
            source_id="job_1",
            skills=["Python", " SQL ", "Python"],
        )

        python_skill = Mock()
        python_skill.name = "python"
        python_skill.id = "skill-python"

        sql_skill = Mock()
        sql_skill.name = "sql"
        sql_skill.id = "skill-sql"

        db_job = Mock()
        db_job.source_site = "test_source"
        db_job.source_id = "job_1"
        db_job.id = "job-1"

        skill_query = MagicMock()
        skill_query.filter.return_value.all.side_effect = [
            [],
            [python_skill, sql_skill],
        ]

        job_query = MagicMock()
        job_query.filter.return_value.all.return_value = [db_job]

        relationship_query = MagicMock()
        relationship_query.filter.return_value.all.return_value = []

        def query_side_effect(model):
            if model is Skill:
                return skill_query
            if model is Job:
                return job_query
            if model is JobSkill:
                return relationship_query
            raise AssertionError(f"Unexpected model: {model}")

        loader.db_session.query.side_effect = query_side_effect
        loader.db_session.begin_nested.return_value = MagicMock()

        result = loader._process_skills([job])

        assert result.skills_added == 2
        assert result.relationships_added == 2


    def test_process_skills_returns_skills_when_no_matching_jobs(
        self,
        loader,
    ):
        """Test the branch where skills exist but no database jobs match."""
        job = Mock(
            source="test_source",
            source_id="job_1",
            skills=["Python"],
        )

        python_skill = Mock()
        python_skill.name = "python"
        python_skill.id = "skill-python"

        skill_query = MagicMock()
        skill_query.filter.return_value.all.side_effect = [
            [],
            [python_skill],
        ]

        job_query = MagicMock()
        job_query.filter.return_value.all.return_value = []

        def query_side_effect(model):
            if model is Skill:
                return skill_query
            if model is Job:
                return job_query
            raise AssertionError(f"Unexpected model: {model}")

        loader.db_session.query.side_effect = query_side_effect

        result = loader._process_skills([job])

        assert result.skills_added == 1
        assert result.relationships_added == 0


    def test_process_skills_skips_duplicate_and_existing_relationships(
        self,
        loader,
    ):
        """Test duplicate pairs and already-existing relationships."""
        job = Mock(
            source="test_source",
            source_id="job_1",
            skills=["Python", "Python", "SQL"],
        )

        python_skill = Mock()
        python_skill.name = "python"
        python_skill.id = "skill-python"

        sql_skill = Mock()
        sql_skill.name = "sql"
        sql_skill.id = "skill-sql"

        db_job = Mock()
        db_job.source_site = "test_source"
        db_job.source_id = "job_1"
        db_job.id = "job-1"

        existing_relationship = Mock()
        existing_relationship.job_id = "job-1"
        existing_relationship.skill_id = "skill-sql"

        skill_query = MagicMock()
        skill_query.filter.return_value.all.side_effect = [
            [python_skill, sql_skill],
            [python_skill, sql_skill],
        ]

        job_query = MagicMock()
        job_query.filter.return_value.all.return_value = [db_job]

        relationship_query = MagicMock()
        relationship_query.filter.return_value.all.return_value = [
            existing_relationship
        ]

        def query_side_effect(model):
            if model is Skill:
                return skill_query
            if model is Job:
                return job_query
            if model is JobSkill:
                return relationship_query
            raise AssertionError(f"Unexpected model: {model}")

        loader.db_session.query.side_effect = query_side_effect
        loader.db_session.begin_nested.return_value = MagicMock()

        result = loader._process_skills([job])

        assert result.skills_added == 0
        assert result.relationships_added == 1


    def test_process_skills_relationship_integrity_error_fallback(
        self,
        loader,
    ):
        """Test fallback to individual relationship inserts after batch failure."""
        job = Mock(
            source="test_source",
            source_id="job_1",
            skills=["Python", "SQL"],
        )

        python_skill = Mock()
        python_skill.name = "python"
        python_skill.id = "skill-python"

        sql_skill = Mock()
        sql_skill.name = "sql"
        sql_skill.id = "skill-sql"

        db_job = Mock()
        db_job.source_site = "test_source"
        db_job.source_id = "job_1"
        db_job.id = "job-1"

        skill_query = MagicMock()
        skill_query.filter.return_value.all.side_effect = [
            [python_skill, sql_skill],
            [python_skill, sql_skill],
        ]

        job_query = MagicMock()
        job_query.filter.return_value.all.return_value = [db_job]

        relationship_query = MagicMock()
        relationship_query.filter.return_value.all.return_value = []

        def query_side_effect(model):
            if model is Skill:
                return skill_query
            if model is Job:
                return job_query
            if model is JobSkill:
                return relationship_query
            raise AssertionError(f"Unexpected model: {model}")

        loader.db_session.query.side_effect = query_side_effect

        class Nested:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

        loader.db_session.begin_nested.side_effect = lambda: Nested()

        batch_error = IntegrityError(
            "INSERT",
            {},
            Exception("duplicate batch"),
        )

        duplicate_error = IntegrityError(
            "INSERT",
            {},
            Exception("duplicate relationship"),
        )

        flush_calls = 0

        def flush_side_effect():
            nonlocal flush_calls
            flush_calls += 1

            # First flush: batch insert → IntegrityError.
            if flush_calls == 1:
                raise batch_error

            # Second flush: first individual relationship → succeeds.

            # Third flush: second individual relationship → IntegrityError.
            if flush_calls == 3:
                raise duplicate_error

        loader.db_session.flush.side_effect = flush_side_effect

        result = loader._process_skills([job])

        assert result.skills_added == 0
        assert result.relationships_added == 1
        assert loader.db_session.begin_nested.call_count == 3


    def test_process_skills_skips_missing_job_or_skill_mapping(self, loader):
        """Skip relationships when the job or skill mapping is missing."""
        job = Mock(
            source="test_source",
            source_id="job_1",
            skills=["Python"],
        )

        # Skill exists in the initial lookup, so no new skill is inserted.
        # But the second lookup deliberately returns no skill objects,
        # producing an empty skill_map.
        python_skill = Mock()
        python_skill.name = "python"
        python_skill.id = "skill-python"

        skill_query = MagicMock()
        skill_query.filter.return_value.all.side_effect = [
            [python_skill],
            [],
        ]

        db_job = Mock()
        db_job.source_site = "test_source"
        db_job.source_id = "job_1"
        db_job.id = "job-1"

        job_query = MagicMock()
        job_query.filter.return_value.all.return_value = [db_job]

        relationship_query = MagicMock()
        relationship_query.filter.return_value.all.return_value = []

        def query_side_effect(model):
            if model is Skill:
                return skill_query
            if model is Job:
                return job_query
            if model is JobSkill:
                return relationship_query
            raise AssertionError(f"Unexpected model: {model}")

        loader.db_session.query.side_effect = query_side_effect

        result = loader._process_skills([job])

        assert result.skills_added == 0
        assert result.relationships_added == 0