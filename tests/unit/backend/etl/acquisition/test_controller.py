"""Unit tests for the acquisition controller."""

from datetime import datetime

from app.etl.acquisition.controller import AcquisitionController
from app.etl.acquisition.models import AcquisitionMode, AcquisitionStats, DatabaseComposition
from app.models.job import Job


class TestAcquisitionControllerInitialization:
    def test_default_queries_are_built(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=100,
        )

        assert len(controller.broad_queries) > 0
        assert len(controller.tech_queries) > 0

        assert all("what" in query for query in controller.broad_queries)
        assert all("what" in query for query in controller.tech_queries)

    def test_tech_queries_use_category_filter_by_default(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=100,
        )

        assert all(query.get("category") == "it-jobs" for query in controller.tech_queries)
        assert all("category" not in query for query in controller.broad_queries)

    def test_tech_category_filter_can_be_disabled(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=100,
            use_category_filter=False,
        )

        assert all("category" not in query for query in controller.tech_queries)

    def test_custom_queries_are_used(self, db_session):
        broad_queries = ["teacher", "driver"]
        tech_queries = ["python", "data scientist"]

        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=100,
            broad_queries=broad_queries,
            tech_queries=tech_queries,
        )

        assert controller.broad_queries == [
            {"what": "teacher"},
            {"what": "driver"},
        ]

        assert controller.tech_queries == [
            {"what": "python", "category": "it-jobs"},
            {"what": "data scientist", "category": "it-jobs"},
        ]

    def test_initial_empty_database_starts_balanced(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=100,
        )

        assert controller.initial_composition.total_jobs == 0
        assert controller.initial_composition.tech_count == 0
        assert controller.initial_composition.non_tech_count == 0
        assert controller.mode == AcquisitionMode.BALANCED

    def test_custom_target_ratio_is_stored(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            target_tech_ratio=0.6,
            max_jobs_per_run=100,
        )

        assert controller.target_tech_ratio == 0.6
        assert controller.tech_intent_target == 60
        assert controller.broad_intent_target == 40

    def test_catch_up_mode_when_database_has_tech_deficit(self, db_session):
        jobs = [
            Job(
                description="Test job",
                source_url=f"https://example.com/tech-{i}",
                language="en",
                title="Software Engineer",
                company_name="Tech Company",
                source_site="test",
                source_id=f"tech-{i}",
                is_tech_role=True,
                country_code="US",
            )
            for i in range(2)
        ]

        jobs.extend(
            Job(
                description="Test job",
                source_url=f"https://example.com/non-tech-{i}",
                language="en",
                title="Teacher",
                company_name="School",
                source_site="test",
                source_id=f"non-tech-{i}",
                is_tech_role=False,
                country_code="US",
            )
            for i in range(8)
        )

        db_session.add_all(jobs)
        db_session.flush()

        controller = AcquisitionController(
            db_session=db_session,
            target_tech_ratio=0.5,
            max_jobs_per_run=100,
        )

        assert controller.mode == AcquisitionMode.CATCH_UP
        assert controller.initial_composition.tech_count == 2
        assert controller.initial_composition.non_tech_count == 8
        assert controller.tech_intent_target == controller.initial_composition.tech_deficit
        assert controller.broad_intent_target == 0


class TestAcquisitionControllerQuerySelection:
    def test_get_next_query_returns_none_when_run_capacity_is_reached(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=2,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        controller.all_jobs = [{"id": "1"}, {"id": "2"}]

        assert controller.get_next_query() is None

    def test_catch_up_mode_selects_tech_query(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        controller.mode = AcquisitionMode.CATCH_UP

        query = controller.get_next_query()

        assert query == {"what": "python", "category": "it-jobs"}
        assert controller.tech_queries_used == 1
        assert controller.broad_queries_used == 0

    def test_next_tech_query_skips_used_queries(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            tech_queries=["python", "django"],
            broad_queries=["teacher"],
        )

        first = controller._next_tech_query()
        controller.used_query_keys.add("tech:django")

        second = controller._next_tech_query()

        assert first == {"what": "python", "category": "it-jobs"}
        assert second is None
        assert controller.tech_queries_used == 1

    def test_next_broad_query_skips_used_queries(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            broad_queries=["teacher", "driver"],
            tech_queries=["python"],
        )

        first = controller._next_broad_query()
        controller.used_query_keys.add("broad:driver")

        second = controller._next_broad_query()

        assert first == {"what": "teacher"}
        assert second is None
        assert controller.broad_queries_used == 1

    def test_balanced_mode_selects_tech_when_below_target_ratio(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        controller.mode = AcquisitionMode.BALANCED
        controller.projected_composition.tech_count = 2
        controller.projected_composition.non_tech_count = 8
        controller.projected_composition.total_jobs = 10

        controller.tech_intent_target = 5
        controller.broad_intent_target = 5

        query = controller.get_next_query()

        assert query == {"what": "python", "category": "it-jobs"}

    def test_balanced_mode_selects_broad_when_above_target_ratio(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        controller.mode = AcquisitionMode.BALANCED
        controller.projected_composition.tech_count = 8
        controller.projected_composition.non_tech_count = 2
        controller.projected_composition.total_jobs = 10

        controller.tech_intent_target = 5
        controller.broad_intent_target = 5

        query = controller.get_next_query()

        assert query == {"what": "teacher"}

    def test_balanced_mode_returns_none_when_targets_are_met(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        controller.mode = AcquisitionMode.BALANCED
        controller.tech_intent_target = 5
        controller.broad_intent_target = 5

        controller.balanced_mode_tech_start = 0
        controller.balanced_mode_broad_start = 0

        controller.tech_intent_jobs = [{"id": str(i)} for i in range(5)]
        controller.broad_intent_jobs = [{"id": str(i)} for i in range(5)]

        assert controller.get_next_query() is None

    def test_catch_up_switches_to_balanced_after_reaching_parity(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        controller.mode = AcquisitionMode.CATCH_UP
        controller.projected_composition.tech_count = 5
        controller.projected_composition.non_tech_count = 5
        controller.projected_composition.total_jobs = 10

        query = controller.get_next_query()

        assert controller.mode == AcquisitionMode.BALANCED
        assert controller.mode_changed is True
        assert query is not None
        assert query.get("what") == "python"


class TestAcquisitionControllerJobHandling:
    def test_add_jobs_records_tech_intent(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        jobs = [
            {"id": "tech-1", "title": "Python Developer"},
            {"id": "tech-2", "title": "Data Engineer"},
        ]
        query = {"what": "python", "category": "it-jobs"}

        new_count, duplicate_count = controller.add_jobs(jobs, query, "US")

        assert new_count == 2
        assert duplicate_count == 0
        assert len(controller.all_jobs) == 2
        assert len(controller.tech_intent_jobs) == 2
        assert len(controller.broad_intent_jobs) == 0
        assert jobs[0]["_acquisition_tech_intent"] is True
        assert jobs[0]["_acquisition_query"] == query
        assert jobs[0]["_acquisition_country"] == "US"
        assert jobs[0]["_acquisition_mode"] == controller.mode.value
        assert jobs[0]["_acquisition_query_number"] == 0

    def test_add_jobs_records_broad_intent(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        query = {"what": "teacher"}
        jobs = [{"id": "job-1", "title": "Teacher"}]

        new_count, duplicate_count = controller.add_jobs(jobs, query, "KE")

        assert new_count == 1
        assert duplicate_count == 0
        assert len(controller.broad_intent_jobs) == 1
        assert len(controller.tech_intent_jobs) == 0
        assert jobs[0]["_acquisition_tech_intent"] is False
        assert jobs[0]["_acquisition_country"] == "KE"

    def test_add_jobs_detects_duplicate_jobs(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            broad_queries=["teacher"],
            tech_queries=["python"],
        )

        query = {"what": "teacher"}
        first = [{"id": "job-1", "title": "Teacher"}]
        second = [{"id": "job-1", "title": "Teacher"}]

        assert controller.add_jobs(first, query, "US") == (1, 0)
        assert controller.add_jobs(second, query, "US") == (0, 1)

        assert len(controller.all_jobs) == 1
        assert len(controller.duplicates) == 1
        assert second[0]["_is_duplicate"] is True

    def test_get_job_id_from_dict_id(self, db_session):
        controller = AcquisitionController(db_session=db_session)

        assert controller._get_job_id({"id": 123}) == "123"

    def test_get_job_id_from_redirect_url(self, db_session):
        controller = AcquisitionController(db_session=db_session)

        url = "https://example.com/jobs/123"

        assert controller._get_job_id({"redirect_url": url}) == url

    def test_get_job_id_from_dict_title_and_company(self, db_session):
        controller = AcquisitionController(db_session=db_session)

        job = {
            "title": "Python Developer",
            "company": "Example Corp",
        }

        result = controller._get_job_id(job)

        assert isinstance(result, str)
        assert len(result) == 32

    def test_get_job_id_from_object_source_id(self, db_session):
        controller = AcquisitionController(db_session=db_session)

        class JobObject:
            source_id = "source-123"
            id = "database-123"

        assert controller._get_job_id(JobObject()) == "source-123"

    def test_get_job_id_from_object_id(self, db_session):
        controller = AcquisitionController(db_session=db_session)

        class JobObject:
            source_id = None
            id = "database-123"

        assert controller._get_job_id(JobObject()) == "database-123"

    def test_get_job_id_from_object_title_and_company(self, db_session):
        controller = AcquisitionController(db_session=db_session)

        class JobObject:
            source_id = None
            id = None
            title = "Python Developer"
            company_name = "Example Corp"

        result = controller._get_job_id(JobObject())

        assert isinstance(result, str)
        assert len(result) == 32

    def test_get_job_id_falls_back_to_object_identity(self, db_session):
        controller = AcquisitionController(db_session=db_session)

        class BrokenJob:
            @property
            def source_id(self):
                raise RuntimeError("broken")

            @property
            def title(self):
                raise RuntimeError("broken")

        job = BrokenJob()
        result = controller._get_job_id(job)

        assert isinstance(result, str)
        assert len(result) == 32


class TestAcquisitionControllerClassification:
    @staticmethod
    def make_enriched(
        source_id,
        is_tech_role,
        technology_category=None,
        tech_confidence=None,
    ):
        from app.etl.schemas.enriched import JobEnriched

        return JobEnriched(
            source_id=source_id,
            title="Test Job",
            company="Test Company",
            location="Nairobi, Kenya",
            description="Test job description",
            is_tech_role=is_tech_role,
            technology_category=technology_category,
            tech_confidence=tech_confidence,
        )

    def test_empty_classification_does_not_change_state(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
        )

        controller.update_classification([])

        assert controller.query_count == 0
        assert controller.tech_classified_jobs == []
        assert controller.non_tech_classified_jobs == []
        assert controller.unclassified_jobs == []

    def test_update_classification_records_tech_job(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
        )

        controller.add_jobs(
            [{"id": "tech-1", "title": "Python Developer"}],
            {"what": "python", "category": "it-jobs"},
            "US",
        )

        job = self.make_enriched(
            "tech-1",
            True,
            technology_category="backend",
            tech_confidence=0.95,
        )

        controller.update_classification([job])

        assert len(controller.tech_classified_jobs) == 1
        assert controller.tech_classified_jobs[0]["source_id"] == "tech-1"
        assert controller.projected_composition.tech_count == 1
        assert controller.projected_composition.non_tech_count == 0
        assert controller.query_count == 1

    def test_update_classification_records_non_tech_job(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
        )

        controller.add_jobs(
            [{"id": "teacher-1", "title": "Teacher"}],
            {"what": "teacher"},
            "US",
        )

        job = self.make_enriched(
            "teacher-1",
            False,
        )

        controller.update_classification([job])

        assert len(controller.non_tech_classified_jobs) == 1
        assert controller.non_tech_classified_jobs[0]["source_id"] == "teacher-1"
        assert controller.projected_composition.non_tech_count == 1
        assert controller.projected_composition.tech_count == 0
        assert controller.query_count == 1

    def test_update_classification_records_unclassified_job(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
        )

        controller.add_jobs(
            [{"id": "unknown-1", "title": "Unknown Job"}],
            {"what": "unknown"},
            "US",
        )

        job = self.make_enriched(
            "unknown-1",
            False,
        )

        # Force the tri-state branch used by the controller.
        object.__setattr__(job, "is_tech_role", None)

        controller.update_classification([job])

        assert len(controller.unclassified_jobs) == 1
        assert controller.projected_composition.unclassified_count == 1
        assert controller.projected_composition.total_jobs == 1
        assert controller.query_count == 1

    def test_update_classification_ignores_unacquired_job(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
        )

        controller.add_jobs(
            [{"id": "acquired-1", "title": "Python Developer"}],
            {"what": "python", "category": "it-jobs"},
            "US",
        )

        foreign_job = self.make_enriched(
            "foreign-1",
            True,
            technology_category="backend",
            tech_confidence=0.9,
        )

        controller.update_classification([foreign_job])

        assert controller.tech_classified_jobs == []
        assert controller.non_tech_classified_jobs == []
        assert controller.unclassified_jobs == []
        assert controller.query_count == 1

    def test_update_classification_records_query_metrics(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
        )

        selected_query = controller.get_next_query()
        assert selected_query is not None

        controller.add_jobs(
            [{"id": "tech-1", "title": "Python Developer"}],
            selected_query,
            "US",
        )

        job = self.make_enriched(
            "tech-1",
            True,
            technology_category="backend",
            tech_confidence=0.9,
        )

        controller.update_classification([job])

        assert len(controller.query_metrics) == 1

        metrics = controller.query_metrics[0]

        assert metrics["query"] == selected_query
        assert metrics["tech_intent"] is True
        assert metrics["new_jobs"] == 1
        assert metrics["tech_classified"] == 1
        assert metrics["non_tech_classified"] == 0
        assert metrics["unclassified"] == 0
        assert metrics["mode"] == controller.mode.value

    def test_catch_up_switches_to_balanced_after_classification(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
        )

        controller.mode = AcquisitionMode.CATCH_UP

        controller.projected_composition.tech_count = 0
        controller.projected_composition.non_tech_count = 1
        controller.projected_composition.total_jobs = 1

        controller.add_jobs(
            [{"id": "tech-1", "title": "Python Developer"}],
            {"what": "python", "category": "it-jobs"},
            "US",
        )

        job = self.make_enriched(
            "tech-1",
            True,
            technology_category="backend",
            tech_confidence=0.9,
        )

        controller.update_classification([job])

        assert controller.mode == AcquisitionMode.BALANCED
        assert controller.mode_changed is True
        assert controller.balanced_mode_tech_start == 1
        assert controller.balanced_mode_broad_start == 0
        assert controller.tech_intent_target == 4
        assert controller.broad_intent_target == 5


class TestAcquisitionControllerRemainingBranches:
    def test_database_composition_filters_by_country(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
        )

        db_session.add_all(
            [
                Job(
                    source_id="ke-tech",
                    title="Software Engineer",
                    description="Test",
                    company_name="Kenya Tech",
                    source_site="test",
                    source_url="https://example.com/ke-tech",
                    language="en",
                    country_code="KE",
                    is_tech_role=True,
                ),
                Job(
                    source_id="us-tech",
                    title="Software Engineer",
                    description="Test",
                    company_name="US Tech",
                    source_site="test",
                    source_url="https://example.com/us-tech",
                    language="en",
                    country_code="US",
                    is_tech_role=True,
                ),
            ]
        )
        db_session.flush()

        composition = controller._get_database_composition("KE")

        assert composition.total_jobs == 1
        assert composition.tech_count == 1
        assert composition.non_tech_count == 0

    def test_determine_mode_returns_balanced_when_parity_reached(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
        )

        controller.initial_composition = DatabaseComposition(
            total_jobs=10,
            tech_count=5,
            non_tech_count=5,
            unclassified_count=0,
        )

        assert controller._determine_mode() == AcquisitionMode.BALANCED

    def test_balanced_mode_fetches_broad_when_tech_intent_target_met(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
        )

        controller.mode = AcquisitionMode.BALANCED
        controller.tech_intent_target = 5
        controller.broad_intent_target = 5

        controller.balanced_mode_tech_start = 0
        controller.balanced_mode_broad_start = 0

        controller.tech_intent_jobs.extend([{"id": str(i)} for i in range(5)])

        query = controller._get_balanced_query(AcquisitionStats())

        assert query is not None
        assert query == controller.broad_queries[0]

    def test_balanced_mode_fetches_tech_when_broad_intent_target_met(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
        )

        controller.mode = AcquisitionMode.BALANCED
        controller.tech_intent_target = 5
        controller.broad_intent_target = 5

        controller.balanced_mode_tech_start = 0
        controller.balanced_mode_broad_start = 0

        controller.broad_intent_jobs.extend([{"id": str(i)} for i in range(5)])

        query = controller._get_balanced_query(AcquisitionStats())

        assert query is not None
        assert query["what"] == controller.tech_queries[0]["what"]

    def test_balanced_mode_tie_breaker_fetches_broad(self, db_session):
        controller = AcquisitionController(
            db_session=db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
        )

        controller.mode = AcquisitionMode.BALANCED
        controller.tech_intent_target = 10
        controller.broad_intent_target = 10

        controller.balanced_mode_tech_start = 0
        controller.balanced_mode_broad_start = 0

        controller.tech_intent_jobs.extend([{"id": f"tech-{i}"} for i in range(2)])
        controller.broad_intent_jobs.extend([{"id": "broad-1"}])

        controller.projected_composition.tech_count = 5
        controller.projected_composition.non_tech_count = 5
        controller.projected_composition.total_jobs = 10

        query = controller._get_balanced_query(AcquisitionStats())

        assert query is not None
        assert query == controller.broad_queries[0]


class TestAcquisitionControllerStateAndResults:
    def test_get_stats_reflects_current_controller_state(self, db_session):
        controller = AcquisitionController(
            db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
        )

        controller.all_jobs = [{"id": "1"}, {"id": "2"}]
        controller.tech_intent_jobs = [{"id": "1"}]
        controller.broad_intent_jobs = [{"id": "2"}]
        controller.tech_classified_jobs = [{"id": "1"}]
        controller.non_tech_classified_jobs = [{"id": "2"}]
        controller.duplicates = [{"id": "2"}]
        controller.broad_queries_used = 1
        controller.tech_queries_used = 2

        stats = controller.get_stats()

        assert stats.jobs_acquired_this_run == 2
        assert stats.tech_intent_acquired == 1
        assert stats.broad_intent_acquired == 1
        assert stats.tech_classified_acquired == 1
        assert stats.non_tech_classified_acquired == 1
        assert stats.duplicates_this_run == 1
        assert stats.broad_queries_used == 1
        assert stats.tech_queries_used == 2

    def test_get_result_filters_duplicate_dict_jobs(self, db_session):
        controller = AcquisitionController(
            db_session,
            max_jobs_per_run=10,
        )

        unique_job = {"id": "unique-1", "title": "Teacher"}
        duplicate_job = {
            "id": "duplicate-1",
            "title": "Teacher",
            "_is_duplicate": True,
        }

        controller.all_jobs = [unique_job, duplicate_job]  # type: ignore[assignment]
        controller.tech_intent_jobs = []
        controller.broad_intent_jobs = [unique_job, duplicate_job]  # type: ignore[assignment]
        controller.duplicates = [duplicate_job]  # type: ignore[assignment]

        result = controller.get_result()

        assert result.jobs == [unique_job, duplicate_job]
        assert result.unique_jobs == [unique_job]
        assert result.duplicates == [duplicate_job]

    def test_get_result_filters_duplicate_object_jobs(self, db_session):
        controller = AcquisitionController(
            db_session,
            max_jobs_per_run=10,
        )

        class JobObject:
            def __init__(self, job_id, is_duplicate=False):
                self.id = job_id
                self._is_duplicate = is_duplicate

        unique_job = JobObject("unique-1")
        duplicate_job = JobObject("duplicate-1", is_duplicate=True)

        controller.all_jobs = [unique_job, duplicate_job]  # type: ignore[assignment]
        controller.broad_intent_jobs = [unique_job, duplicate_job]  # type: ignore[assignment]
        controller.duplicates = [duplicate_job]  # type: ignore[assignment]

        result = controller.get_result()

        assert result.unique_jobs == [unique_job]
        assert result.jobs == [unique_job, duplicate_job]

    def test_get_progress_returns_current_controller_state(self, db_session):
        controller = AcquisitionController(
            db_session,
            max_jobs_per_run=10,
            target_tech_ratio=0.5,
        )

        controller.all_jobs = [{"id": "1"}, {"id": "2"}]
        controller.tech_intent_jobs = [{"id": "1"}]
        controller.tech_classified_jobs = [{"id": "1"}]
        controller.non_tech_classified_jobs = [{"id": "2"}]
        controller.broad_queries_used = 1
        controller.tech_queries_used = 2
        controller.query_count = 3
        controller.mode_changed = True
        controller.query_metrics = [
            {"query": "old"},
            {"query": "middle"},
            {"query": "latest"},
        ]

        progress = controller.get_progress()

        assert progress["db_total"] == controller.initial_composition.total_jobs
        assert progress["db_tech"] == controller.initial_composition.tech_count
        assert progress["db_non_tech"] == controller.initial_composition.non_tech_count
        assert progress["projected_tech"] == controller.projected_composition.tech_count
        assert progress["projected_non_tech"] == controller.projected_composition.non_tech_count
        assert progress["tech_intent_acquired"] == 1
        assert progress["tech_classified_acquired"] == 1
        assert progress["non_tech_classified_acquired"] == 1
        assert progress["mode"] == controller.mode.value
        assert progress["mode_changed"] is True
        assert progress["query_count"] == 3
        assert progress["target_tech_ratio"] == controller.target_tech_ratio
        assert progress["max_jobs_per_run"] == controller.max_jobs_per_run
        assert progress["broad_queries_used"] == 1
        assert progress["tech_queries_used"] == 2
        assert progress["jobs_acquired"] == 2
        assert progress["query_metrics"] == controller.query_metrics
        assert progress["total_queries"] == 3

    def test_reset_restores_controller_to_initial_runtime_state(self, db_session):
        controller = AcquisitionController(
            db_session,
            max_jobs_per_run=10,
        )

        controller.broad_index = 4
        controller.tech_index = 5
        controller.used_query_keys.add("tech:python")
        controller.seen_job_ids.add("job-1")
        controller.all_jobs = [{"id": "job-1"}]
        controller.tech_intent_jobs = [{"id": "job-1"}]
        controller.broad_intent_jobs = [{"id": "job-2"}]
        controller.tech_classified_jobs = [{"id": "job-1"}]
        controller.non_tech_classified_jobs = [{"id": "job-2"}]
        controller.unclassified_jobs = [{"id": "job-3"}]
        controller.duplicates = [{"id": "job-4"}]
        controller.broad_queries_used = 4
        controller.tech_queries_used = 5

        controller.current_query = {"what": "python"}
        controller.current_query_start_time = datetime.now()
        controller.current_query_new_jobs = 10
        controller.current_query_classified = 8
        controller.current_query_tech = 6
        controller.current_query_non_tech = 2
        controller.current_query_unclassified = 0
        controller.current_query_mode = AcquisitionMode.BALANCED
        controller.query_metrics = [{"query": "python"}]
        controller.query_count = 7
        controller.mode_changed = True
        controller.balanced_mode_tech_start = 10
        controller.balanced_mode_broad_start = 8

        controller.reset()

        assert controller.broad_index == 0
        assert controller.tech_index == 0
        assert controller.used_query_keys == set()
        assert controller.seen_job_ids == set()
        assert controller.all_jobs == []
        assert controller.tech_intent_jobs == []
        assert controller.broad_intent_jobs == []
        assert controller.tech_classified_jobs == []
        assert controller.non_tech_classified_jobs == []
        assert controller.unclassified_jobs == []
        assert controller.duplicates == []
        assert controller.broad_queries_used == 0
        assert controller.tech_queries_used == 0

        assert controller.current_query is None
        assert controller.current_query_start_time is None
        assert controller.current_query_new_jobs == 0
        assert controller.current_query_classified == 0
        assert controller.current_query_tech == 0
        assert controller.current_query_non_tech == 0
        assert controller.current_query_unclassified == 0
        assert controller.current_query_mode is None

        assert controller.query_metrics == []
        assert controller.query_count == 0
        assert controller.mode_changed is False
        assert controller.balanced_mode_tech_start == 0
        assert controller.balanced_mode_broad_start == 0
