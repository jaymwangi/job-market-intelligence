from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

from app.etl.enrichment.enricher import Enricher
from app.etl.schemas.transformed import JobTransformed
from app.shared.languages import LanguageCode


class TestEnricherSteps:
    def test_language_detection_disabled(self):
        """Language detection disabled should default to English."""
        language_detector = Mock()

        enricher = Enricher(
            language_detector=language_detector,
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
            language_detection_enabled=False,
        )

        job = Mock()
        job.title = "Développeur Python"
        job.description = "Développement logiciel"

        context = {}

        enricher._enrich_language(job, context)

        assert context["language"] == LanguageCode.ENGLISH
        language_detector.detect.assert_not_called()

    def test_language_detection_enabled(self):
        """Language detection should use title and description."""
        language_detector = Mock()
        language_detector.detect.return_value = LanguageCode.FRENCH

        enricher = Enricher(
            language_detector=language_detector,
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
            language_detection_enabled=True,
        )

        job = Mock()
        job.title = "Développeur Python"
        job.description = "Développement logiciel"

        context = {}

        enricher._enrich_language(job, context)

        assert context["language"] == LanguageCode.FRENCH
        language_detector.detect.assert_called_once_with(
            "Développeur Python Développement logiciel"
        )

    def test_skill_extraction(self):
        """Skills should be extracted from title and description."""
        skill_extractor = Mock()
        skill_extractor.extract_skills.return_value = [
            "Python",
            "Django",
            "PostgreSQL",
        ]

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=skill_extractor,
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        job = Mock()
        job.title = "Backend Developer"
        job.description = "Python Django PostgreSQL"

        context = {}

        enricher._enrich_skills(job, context)

        assert context["skills"] == ["Python", "Django", "PostgreSQL"]
        skill_extractor.extract_skills.assert_called_once_with(
            "Backend Developer",
            "Python Django PostgreSQL",
        )

    def test_skill_extraction_with_missing_description(self):
        """Missing description should be treated as an empty string."""
        skill_extractor = Mock()
        skill_extractor.extract_skills.return_value = ["Python"]

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=skill_extractor,
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        job = Mock()
        job.title = "Python Developer"
        job.description = None

        context = {}

        enricher._enrich_skills(job, context)

        assert context["skills"] == ["Python"]
        skill_extractor.extract_skills.assert_called_once_with(
            "Python Developer",
            "",
        )

    def test_technology_scoring(self):
        """Technology scoring should receive title, description and skills."""
        tech_decision = Mock()
        tech_scorer = Mock()
        tech_scorer.classify.return_value = tech_decision

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=tech_scorer,
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        job = Mock()
        job.title = "Backend Developer"
        job.description = "Build APIs"

        context = {
            "skills": ["Python", "FastAPI"],
        }

        enricher._enrich_tech_scoring(job, context)

        assert context["tech_decision"] is tech_decision
        tech_scorer.classify.assert_called_once_with(
            title="Backend Developer",
            description="Build APIs",
            skills=["Python", "FastAPI"],
        )

    def test_country_from_source_country(self):
        """Source country should take priority when it normalizes."""
        country_normalizer = Mock()
        country_normalizer.normalize.return_value = "US"

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=country_normalizer,
            currency_normalizer=Mock(),
        )

        job = Mock()
        job.source_country = "United States"
        job.location = "Nairobi, Kenya"

        context = {}

        enricher._enrich_country(job, context)

        assert context["country_code"] == "US"
        country_normalizer.normalize.assert_called_once_with("United States")

    def test_country_falls_back_to_location(self):
        """Location should be used when source country cannot be normalized."""
        country_normalizer = Mock()
        country_normalizer.normalize.side_effect = [None, "KE"]

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=country_normalizer,
            currency_normalizer=Mock(),
        )

        job = Mock()
        job.source_country = "Unknown"
        job.location = "Nairobi, Kenya"

        context = {}

        enricher._enrich_country(job, context)

        assert context["country_code"] == "KE"
        assert country_normalizer.normalize.call_count == 2

    def test_country_without_source_or_location(self):
        """Country should remain None when neither source nor location exists."""
        country_normalizer = Mock()

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=country_normalizer,
            currency_normalizer=Mock(),
        )

        job = Mock()
        job.source_country = None
        job.location = None

        context = {}

        enricher._enrich_country(job, context)

        assert context["country_code"] is None
        country_normalizer.normalize.assert_not_called()

    def test_currency_from_salary_currency(self):
        """Salary currency should have priority."""
        currency_normalizer = Mock()
        currency_normalizer.normalize.return_value = "EUR"

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=currency_normalizer,
        )

        job = Mock()
        job.salary_currency = "€"

        context = {
            "country_code": "DE",
        }

        enricher._enrich_currency(job, context)

        assert context["currency"] == "EUR"
        currency_normalizer.normalize.assert_called_once_with("€")

    def test_currency_inferred_from_country(self):
        """Country should be used when salary currency cannot be normalized."""
        currency_normalizer = Mock()
        currency_normalizer.normalize.return_value = None
        currency_normalizer.infer_currency_from_country.return_value = "KES"

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=currency_normalizer,
        )

        job = Mock()
        job.salary_currency = "UNKNOWN"

        context = {
            "country_code": "KE",
        }

        enricher._enrich_currency(job, context)

        assert context["currency"] == "KES"
        currency_normalizer.infer_currency_from_country.assert_called_once_with("KE")

    def test_currency_defaults_to_usd(self):
        """Currency should default to USD when no inference is possible."""
        currency_normalizer = Mock()
        currency_normalizer.normalize.return_value = None
        currency_normalizer.infer_currency_from_country.return_value = None

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=currency_normalizer,
        )

        job = Mock()
        job.salary_currency = None

        context = {
            "country_code": "XX",
        }

        enricher._enrich_currency(job, context)

        assert context["currency"] == "USD"

    def test_salary_normalization_disabled(self):
        """Salary normalization should produce no values when disabled."""
        currency_normalizer = Mock()

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=currency_normalizer,
            normalize_salaries=False,
        )

        job = Mock()
        job.salary_min = 50000
        job.salary_max = 80000

        context = {
            "currency": "KES",
        }

        enricher._enrich_salary(job, context)

        assert context["normalized_min"] is None
        assert context["normalized_max"] is None
        currency_normalizer.convert.assert_not_called()

    def test_salary_normalization_without_currency(self):
        """Salary normalization should stop when no currency is available."""
        currency_normalizer = Mock()

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=currency_normalizer,
            normalize_salaries=True,
        )

        job = Mock()
        job.salary_min = 50000
        job.salary_max = 80000

        context = {
            "currency": None,
        }

        enricher._enrich_salary(job, context)

        assert context["normalized_min"] is None
        assert context["normalized_max"] is None
        currency_normalizer.convert.assert_not_called()

    def test_salary_normalization_converts_min_and_max(self):
        """Both salary bounds should be converted when present."""
        currency_normalizer = Mock()
        currency_normalizer.convert.side_effect = [500.0, 800.0]

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=currency_normalizer,
            normalize_salaries=True,
        )

        job = Mock()
        job.salary_min = 50000
        job.salary_max = 80000

        context = {
            "currency": "KES",
        }

        enricher._enrich_salary(job, context)

        assert context["normalized_min"] == 500.0
        assert context["normalized_max"] == 800.0

        assert currency_normalizer.convert.call_count == 2
        currency_normalizer.convert.assert_any_call(
            amount=50000,
            from_currency="KES",
            to_currency="USD",
        )
        currency_normalizer.convert.assert_any_call(
            amount=80000,
            from_currency="KES",
            to_currency="USD",
        )

    def test_salary_normalization_only_min(self):
        """Only the minimum salary should be converted when max is missing."""
        currency_normalizer = Mock()
        currency_normalizer.convert.return_value = 500.0

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=currency_normalizer,
            normalize_salaries=True,
        )

        job = Mock()
        job.salary_min = 50000
        job.salary_max = None

        context = {
            "currency": "KES",
        }

        enricher._enrich_salary(job, context)

        assert context["normalized_min"] == 500.0
        assert context["normalized_max"] is None

        currency_normalizer.convert.assert_called_once_with(
            amount=50000,
            from_currency="KES",
            to_currency="USD",
        )

    def test_salary_normalization_only_max(self):
        """Only the maximum salary should be converted when min is missing."""
        currency_normalizer = Mock()
        currency_normalizer.convert.return_value = 800.0

        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=currency_normalizer,
            normalize_salaries=True,
        )

        job = Mock()
        job.salary_min = None
        job.salary_max = 80000

        context = {
            "currency": "KES",
        }

        enricher._enrich_salary(job, context)

        assert context["normalized_min"] is None
        assert context["normalized_max"] == 800.0

        currency_normalizer.convert.assert_called_once_with(
            amount=80000,
            from_currency="KES",
            to_currency="USD",
        )

    def test_build_job_without_tech_decision(self):
        """Missing tech decision should create a valid non-tech enriched job."""
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        job = JobTransformed(
            source_id="job-1",
            title="Accountant",
            company="Test Company",
            location="Nairobi, Kenya",
        )

        context = {
            "language": LanguageCode.ENGLISH,
            "skills": ["Excel"],
            "country_code": "KE",
            "currency": "KES",
            "normalized_min": None,
            "normalized_max": None,
        }

        enricher._enrich_build_job(job, context)

        enriched = context["enriched_job"]

        assert enriched.source_id == "job-1"
        assert enriched.title == "Accountant"
        assert enriched.language == "en"
        assert enriched.skills == ["Excel"]
        assert enriched.is_tech_role is False
        assert enriched.technology_category is None
        assert enriched.tech_confidence is None
        assert enriched.matched_tech_terms == []
        assert enriched.country_code == "KE"
        assert enriched.currency == "KES"

    def test_build_job_with_tech_decision(self):
        """A tech decision should populate technology classification fields."""
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        job = JobTransformed(
            source_id="job-2",
            title="Python Developer",
            company="Tech Company",
            location="Nairobi, Kenya",
        )

        tech_decision = Mock()
        tech_decision.is_tech = True
        tech_decision.primary_category = "backend"
        tech_decision.confidence = 0.92

        context = {
            "language": LanguageCode.ENGLISH,
            "skills": ["Python", "FastAPI"],
            "tech_decision": tech_decision,
            "matched_tech_terms": ["python", "fastapi"],
            "country_code": "KE",
            "currency": "KES",
            "normalized_min": 1000.0,
            "normalized_max": 2000.0,
        }

        enricher._enrich_build_job(job, context)

        enriched = context["enriched_job"]

        assert enriched.source_id == "job-2"
        assert enriched.language == "en"
        assert enriched.is_tech_role is True
        assert enriched.technology_category == "backend"
        assert enriched.tech_confidence == 0.92
        assert enriched.country_code == "KE"
        assert enriched.currency == "KES"
        assert enriched.normalized_salary_min == 1000.0
        assert enriched.normalized_salary_max == 2000.0

    def test_skill_extractor_settings_failure_uses_fallback(self):
        """SkillExtractor initialization failure should use the fallback."""
        fallback_extractor = Mock()

        with (
            patch(
                "app.etl.enrichment.enricher.SkillExtractor",
                side_effect=[Exception("settings failure"), fallback_extractor],
            ),
            patch(
                "app.etl.enrichment.enricher.logger.warning",
            ) as warning_mock,
        ):
            enricher = Enricher(
                language_detector=Mock(),
                tech_scorer=Mock(),
                country_normalizer=Mock(),
                currency_normalizer=Mock(),
            )

        assert enricher.skill_extractor is fallback_extractor
        warning_mock.assert_called_once()
        assert warning_mock.call_args.args[0] == (
            "Failed to initialize SkillExtractor with settings: %s"
        )
        assert str(warning_mock.call_args.args[1]) == "settings failure"


class TestEnricherPipeline:
    def test_enrich_runs_all_steps_and_returns_enriched_job(self):
        """Enrich should execute every configured step and return the result."""
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        enriched_job = Mock()
        calls = []

        def make_step(
            name: str,
        ) -> Callable[[Any, dict[str, Any]], None]:
            def step(job: Any, context: dict[str, Any]) -> None:
                calls.append(name)
                if name == "build":
                    context["enriched_job"] = enriched_job

            return step

        enricher._steps = [
            ("language", make_step("language")),
            ("skills", make_step("skills")),
            ("tech_scoring", make_step("tech_scoring")),
            ("country", make_step("country")),
            ("currency", make_step("currency")),
            ("salary", make_step("salary")),
            ("build", make_step("build")),
        ]

        job = Mock()
        job.source_id = "job-123"

        result = enricher.enrich(job)

        assert result is enriched_job
        assert calls == [
            "language",
            "skills",
            "tech_scoring",
            "country",
            "currency",
            "salary",
            "build",
        ]

        stats = enricher.get_timing_stats()

        for step_name in [
            "language",
            "skills",
            "tech_scoring",
            "country",
            "currency",
            "salary",
            "total",
        ]:
            assert stats[step_name]["count"] == 1
            assert stats[step_name]["avg_ms"] >= 0
            assert stats[step_name]["min_ms"] >= 0
            assert stats[step_name]["max_ms"] >= 0

    def test_enrich_records_step_timings(self):
        """Enrich should store timing information in the context."""
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        captured_context = {}

        def step(job, context):
            captured_context.update(context)

        enricher._steps = [
            ("language", step),
        ]

        job = Mock()
        job.source_id = "job-456"

        # The build result normally comes from the final build step.
        def build_step(job, context):
            context["enriched_job"] = "enriched"

        enricher._steps = [
            ("language", step),
            ("build", build_step),
        ]

        result = enricher.enrich(job)

        assert result == "enriched"
        assert "timings" in captured_context
        assert "language" in captured_context["timings"]
        assert "build" in captured_context["timings"]
        assert all(timing >= 0 for timing in captured_context["timings"].values())

    def test_enrich_reraises_step_exception(self):
        """A failed enrichment step should be logged and re-raised."""
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        def failing_step(job, context):
            raise ValueError("enrichment failed")

        steps: list[tuple[str, Callable[[JobTransformed, dict[str, Any]], None]]] = [
            ("language", failing_step),
        ]
        enricher._steps = steps

        job = Mock()
        job.source_id = "job-789"

        try:
            enricher.enrich(job)
            raise AssertionError("Expected ValueError")
        except ValueError as exc:
            assert str(exc) == "enrichment failed"


class TestEnricherBatch:
    def test_enrich_batch_returns_all_successful_jobs(self):
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        job1 = JobTransformed(
            source_id="job-1",
            title="Developer",
            company="Company A",
            location="Nairobi",
        )
        job2 = JobTransformed(
            source_id="job-2",
            title="Analyst",
            company="Company B",
            location="Nairobi",
        )

        enriched1 = Mock()
        enriched2 = Mock()
        enricher.enrich = Mock(side_effect=[enriched1, enriched2])

        result = enricher.enrich_batch([job1, job2])

        assert result == [enriched1, enriched2]
        assert enricher.enrich.call_count == 2

    def test_enrich_batch_continues_when_one_job_fails(self):
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        job1 = JobTransformed(
            source_id="job-1",
            title="Developer",
            company="Company A",
            location="Nairobi",
        )
        job2 = JobTransformed(
            source_id="job-2",
            title="Analyst",
            company="Company B",
            location="Nairobi",
        )
        job3 = JobTransformed(
            source_id="job-3",
            title="Engineer",
            company="Company C",
            location="Nairobi",
        )

        enriched1 = Mock()
        enriched3 = Mock()
        enricher.enrich = Mock(
            side_effect=[enriched1, RuntimeError("enrichment failed"), enriched3]
        )

        result = enricher.enrich_batch([job1, job2, job3])

        assert result == [enriched1, enriched3]
        assert enricher.enrich.call_count == 3

    def test_enrich_batch_empty_list(self):
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        enricher.enrich = Mock()

        result = enricher.enrich_batch([])

        assert result == []
        enricher.enrich.assert_not_called()


class TestEnricherStats:
    def test_get_timing_stats_returns_zeroes_before_enrichment(self):
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        stats = enricher.get_timing_stats()

        assert stats["language"] == {
            "avg_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "count": 0,
        }

    def test_get_pipeline_stats_returns_current_configuration(self):
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
            normalize_salaries=True,
            language_detection_enabled=False,
        )

        stats = enricher.get_pipeline_stats()

        assert "language_cache" in stats
        assert "timing_stats" in stats
        assert stats["normalize_salaries"] is True
        assert stats["language_detection_enabled"] is False

    def test_reset_timing_stats_clears_recorded_stats(self):
        enricher = Enricher(
            language_detector=Mock(),
            skill_extractor=Mock(),
            tech_scorer=Mock(),
            country_normalizer=Mock(),
            currency_normalizer=Mock(),
        )

        enricher._record_timing("language", 10.0)
        assert enricher.get_timing_stats()["language"]["count"] == 1

        enricher.reset_timing_stats()

        assert enricher.get_timing_stats()["language"] == {
            "avg_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "count": 0,
        }


class TestEnricherConvenienceFunctions:
    def test_get_enricher_initializes_singleton(self, monkeypatch):
        import app.etl.enrichment.enricher as enricher_module

        monkeypatch.setattr(enricher_module, "_enricher", None)

        first = enricher_module.get_enricher()
        second = enricher_module.get_enricher()

        assert first is second
        assert isinstance(first, Enricher)

    def test_enrich_job_delegates_to_global_enricher(self, monkeypatch):
        import app.etl.enrichment.enricher as enricher_module

        mock_enricher = Mock()
        expected = Mock()
        mock_enricher.enrich.return_value = expected

        monkeypatch.setattr(enricher_module, "get_enricher", lambda: mock_enricher)

        job = JobTransformed(
            source_id="job-1",
            title="Developer",
            company="Company",
            location="Nairobi",
        )

        result = enricher_module.enrich_job(job)

        assert result is expected
        mock_enricher.enrich.assert_called_once_with(job)

    def test_enrich_jobs_delegates_to_global_enricher(self, monkeypatch):
        import app.etl.enrichment.enricher as enricher_module

        mock_enricher = Mock()
        expected = [Mock(), Mock()]
        mock_enricher.enrich_batch.return_value = expected

        monkeypatch.setattr(enricher_module, "get_enricher", lambda: mock_enricher)

        jobs = [
            JobTransformed(
                source_id="job-1",
                title="Developer",
                company="Company A",
                location="Nairobi",
            ),
            JobTransformed(
                source_id="job-2",
                title="Analyst",
                company="Company B",
                location="Nairobi",
            ),
        ]

        result = enricher_module.enrich_jobs(jobs)

        assert result is expected
        mock_enricher.enrich_batch.assert_called_once_with(jobs)
