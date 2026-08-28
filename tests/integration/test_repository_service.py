"""Integration tests for repositories and repository-level services.

These tests run against the real PostgreSQL test database configured by
the integration-test fixtures.

The suite covers:
- BaseRepository
- SkillRepository
- JobRepository
- AnalyticsRepository
- PipelineRunRepository
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.base import BaseRepository
from app.repositories.job_repository import JobRepository
from app.repositories.pipeline_run_repository import PipelineRunRepository
from app.repositories.skill_repository import SkillRepository
from app.schemas.job import JobFilters


class TestBaseRepository:
    """Integration tests for the generic BaseRepository."""

    def test_create_and_get(self, db_session):
        repository = BaseRepository(Skill, db_session)

        skill = repository.create(name=f"Python-{uuid4().hex[:8]}")

        assert skill.id is not None
        assert skill.name.startswith("Python-")

        fetched = repository.get(id=skill.id)

        assert fetched is not None
        assert fetched.id == skill.id
        assert fetched.name == skill.name

    def test_get_by_id(self, db_session):
        repository = BaseRepository(Skill, db_session)

        skill = repository.create(name=f"SQL-{uuid4().hex[:8]}")

        fetched = repository.get_by_id(skill.id)

        assert fetched is not None
        assert fetched.id == skill.id

    def test_find_all_and_count(self, db_session):
        repository = BaseRepository(Skill, db_session)

        names = [f"Skill-{uuid4().hex[:8]}" for _ in range(3)]

        repository.bulk_create([{"name": name} for name in names])

        skills = repository.find_all()
        count = repository.count()

        assert len(skills) >= 3
        assert count >= 3

    def test_find_paginated(self, db_session):
        repository = BaseRepository(Skill, db_session)

        repository.bulk_create(
            [
                {"name": f"Pagination-{uuid4().hex[:8]}"}
                for _ in range(5)
            ]
        )

        results = repository.find_paginated(
            skip=0,
            limit=2,
        )

        assert len(results) == 2

    def test_find_all_with_ordering(self, db_session):
        repository = BaseRepository(Skill, db_session)

        names = [
            f"Order-C-{uuid4().hex[:8]}",
            f"Order-A-{uuid4().hex[:8]}",
            f"Order-B-{uuid4().hex[:8]}",
        ]

        repository.bulk_create([{"name": name} for name in names])

        results = repository.find_all(order_by="name")

        result_names = [skill.name for skill in results]

        assert result_names == sorted(result_names)

    def test_find_all_descending(self, db_session):
        repository = BaseRepository(Skill, db_session)

        names = [
            f"Descending-A-{uuid4().hex[:8]}",
            f"Descending-B-{uuid4().hex[:8]}",
            f"Descending-C-{uuid4().hex[:8]}",
        ]

        repository.bulk_create([{"name": name} for name in names])

        results = repository.find_all(
            order_by="name",
            descending=True,
        )

        result_names = [skill.name for skill in results]

        assert result_names == sorted(result_names, reverse=True)

    def test_find_paginated_with_ordering(self, db_session):
        repository = BaseRepository(Skill, db_session)

        names = [
            f"Page-A-{uuid4().hex[:8]}",
            f"Page-B-{uuid4().hex[:8]}",
            f"Page-C-{uuid4().hex[:8]}",
        ]

        repository.bulk_create([{"name": name} for name in names])

        results = repository.find_paginated(
            skip=0,
            limit=2,
            order_by="name",
        )

        assert len(results) == 2

    def test_update(self, db_session):
        repository = BaseRepository(Skill, db_session)

        skill = repository.create(
            name=f"Original-{uuid4().hex[:8]}",
        )

        updated = repository.update(
            skill.id,
            name=f"Updated-{uuid4().hex[:8]}",
        )

        assert updated is not None
        assert updated.name.startswith("Updated-")

        fetched = repository.get_by_id(skill.id)

        assert fetched is not None
        assert fetched.name == updated.name

    def test_update_missing_record(self, db_session):
        repository = BaseRepository(Skill, db_session)

        result = repository.update(
            uuid4(),
            name="Does Not Exist",
        )

        assert result is None

    def test_delete(self, db_session):
        repository = BaseRepository(Skill, db_session)

        skill = repository.create(
            name=f"Delete-{uuid4().hex[:8]}",
        )

        skill_id = skill.id

        assert repository.delete(skill_id) is True
        assert repository.get_by_id(skill_id) is None

    def test_delete_missing_record(self, db_session):
        repository = BaseRepository(Skill, db_session)

        assert repository.delete(uuid4()) is False

    def test_exists(self, db_session):
        repository = BaseRepository(Skill, db_session)

        skill = repository.create(
            name=f"Exists-{uuid4().hex[:8]}",
        )

        assert repository.exists(id=skill.id) is True
        assert repository.exists(id=uuid4()) is False

    def test_get_with_filters(self, db_session):
        repository = BaseRepository(Skill, db_session)

        name = f"Filter-{uuid4().hex[:8]}"

        repository.create(name=name)

        result = repository.get(name=name)

        assert result is not None
        assert result.name == name

    def test_count_with_filters(self, db_session):
        repository = BaseRepository(Skill, db_session)

        name = f"Count-{uuid4().hex[:8]}"

        repository.create(name=name)

        count = repository.count(name=name)

        assert count == 1


class TestSkillRepository:
    """Integration tests for SkillRepository."""

    def test_create_and_find_skill(self, db_session):
        repository = SkillRepository(db_session)

        name = f"PostgreSQL-{uuid4().hex[:8]}"

        skill = repository.create(name=name)

        assert skill.id is not None
        assert skill.name == name

        fetched = repository.get(name=name)

        assert fetched is not None
        assert fetched.id == skill.id

    def test_skill_repository_inherits_base_operations(self, db_session):
        repository = SkillRepository(db_session)

        skill = repository.create(
            name=f"Inheritance-{uuid4().hex[:8]}",
        )

        assert repository.exists(id=skill.id) is True
        assert repository.count(id=skill.id) == 1

    def test_skill_repository_pagination(self, db_session):
        repository = SkillRepository(db_session)

        repository.bulk_create(
            [
                {"name": f"SkillPage-{uuid4().hex[:8]}"}
                for _ in range(4)
            ]
        )

        results = repository.find_paginated(
            skip=0,
            limit=2,
            order_by="name",
        )

        assert len(results) == 2


class TestJobRepository:
    """Integration tests for JobRepository."""

    def _create_job(
        self,
        db_session,
        *,
        source_site: str | None = None,
        source_id: str | None = None,
        title: str = "Senior Python Engineer",
        company_name: str = "Test Company",
        location: str = "Nairobi",
        country_code: str = "KE",
        language: str = "en",
        technology_category: str | None = "backend",
        is_tech_role: bool = True,
        employment_type: str = "full-time",
        salary_min: Decimal = Decimal("50000"),
        salary_max: Decimal = Decimal("100000"),
        posted_date: datetime | None = None,
        is_active: bool = True,
        is_deleted: bool = False,
    ) -> Job:
        job = Job(
            title=title,
            description="Integration test job",
            company_name=company_name,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="USD",
            source_site=source_site or f"test-{uuid4().hex[:8]}",
            source_id=source_id or uuid4().hex,
            source_url="https://example.com/job",
            posted_date=posted_date or datetime.now(UTC),
            scraped_date=datetime.now(UTC),
            is_active=is_active,
            is_deleted=is_deleted,
            technology_category=technology_category,
            is_tech_role=is_tech_role,
            country_code=country_code,
            employment_type=employment_type,
            language=language,
        )

        db_session.add(job)
        db_session.flush()

        return job

    def test_get_by_id_returns_active_job(self, db_session):
        repository = JobRepository(db_session)

        job = self._create_job(db_session)

        result = repository.get_by_id(job.id)

        assert result is not None
        assert result.id == job.id
        assert result.title == "Senior Python Engineer"

    def test_get_by_id_excludes_deleted_job(self, db_session):
        repository = JobRepository(db_session)

        job = self._create_job(db_session)

        job.is_deleted = True
        db_session.flush()

        result = repository.get_by_id(job.id)

        assert result is None

    def test_get_by_id_excludes_inactive_job(self, db_session):
        repository = JobRepository(db_session)

        job = self._create_job(
            db_session,
            is_active=False,
        )

        result = repository.get_by_id(job.id)

        assert result is None

    def test_count_jobs(self, db_session):
        repository = JobRepository(db_session)

        self._create_job(db_session)
        self._create_job(db_session)

        count = repository.count_jobs(
            filters=JobFilters(),
        )

        assert count >= 2

    def test_count_jobs_with_company_filter(self, db_session):
        repository = JobRepository(db_session)

        company = f"Filter Company {uuid4().hex[:8]}"

        self._create_job(
            db_session,
            company_name=company,
        )

        self._create_job(
            db_session,
            company_name="Different Company",
        )

        count = repository.count_jobs(
            filters=JobFilters(company_name=company),
        )

        assert count == 1

    def test_get_jobs_with_company_filter(self, db_session):
        repository = JobRepository(db_session)

        company = f"Python Company {uuid4().hex[:8]}"

        job = self._create_job(
            db_session,
            company_name=company,
        )

        results = repository.get_jobs(
            filters=JobFilters(company_name=company),
            offset=0,
            limit=10,
        )

        assert any(result.id == job.id for result in results)

    def test_get_jobs_with_country_filter(self, db_session):
        repository = JobRepository(db_session)

        job = self._create_job(
            db_session,
            country_code="KE",
        )

        self._create_job(
            db_session,
            country_code="DE",
        )

        results = repository.get_jobs(
            filters=JobFilters(country_code="KE"),
            offset=0,
            limit=10,
        )

        assert any(result.id == job.id for result in results)
        assert all(result.country_code == "KE" for result in results)

    def test_get_jobs_with_technology_category_filter(self, db_session):
        repository = JobRepository(db_session)

        job = self._create_job(
            db_session,
            technology_category="backend",
        )

        self._create_job(
            db_session,
            technology_category="frontend",
        )

        results = repository.get_jobs(
            filters=JobFilters(
                technology_category="backend",
            ),
            offset=0,
            limit=10,
        )

        assert any(result.id == job.id for result in results)
        assert all(
            result.technology_category == "backend"
            for result in results
        )

    def test_get_jobs_with_tech_role_filter(self, db_session):
        repository = JobRepository(db_session)

        tech_job = self._create_job(
            db_session,
            is_tech_role=True,
            technology_category="backend",
        )

        self._create_job(
            db_session,
            is_tech_role=False,
            technology_category=None,
        )

        results = repository.get_jobs(
            filters=JobFilters(is_tech_role=True),
            offset=0,
            limit=10,
        )

        assert any(result.id == tech_job.id for result in results)
        assert all(result.is_tech_role is True for result in results)

    def test_get_jobs_with_search_query(self, db_session):
        repository = JobRepository(db_session)

        job = self._create_job(
            db_session,
            title="Unique Machine Learning Engineer",
        )

        results = repository.get_jobs(
            filters=JobFilters(),
            offset=0,
            limit=10,
            search_query="Machine Learning",
        )

        assert any(result.id == job.id for result in results)

    def test_get_jobs_respects_limit(self, db_session):
        repository = JobRepository(db_session)

        for _ in range(5):
            self._create_job(db_session)

        results = repository.get_jobs(
            filters=JobFilters(),
            offset=0,
            limit=2,
        )

        assert len(results) == 2

    def test_get_jobs_excludes_deleted_and_inactive(self, db_session):
        repository = JobRepository(db_session)

        active_job = self._create_job(db_session)

        self._create_job(
            db_session,
            is_deleted=True,
        )

        self._create_job(
            db_session,
            is_active=False,
        )

        results = repository.get_jobs(
            filters=JobFilters(),
            offset=0,
            limit=100,
        )

        result_ids = {result.id for result in results}

        assert active_job.id in result_ids
        assert len(result_ids) == 1

    def test_get_country_distribution(self, db_session):
        repository = JobRepository(db_session)

        self._create_job(
            db_session,
            country_code="KE",
        )

        self._create_job(
            db_session,
            country_code="KE",
        )

        results = repository.get_country_distribution()

        kenya = next(
            row for row in results
            if row["country"] == "KE"
        )

        assert kenya["count"] >= 2

    def test_get_technology_distribution(self, db_session):
        repository = JobRepository(db_session)

        self._create_job(
            db_session,
            technology_category="backend",
        )

        results = repository.get_technology_distribution()

        assert any(
            row["category"] == "backend"
            for row in results
        )

    def test_get_top_skills(self, db_session):
        repository = JobRepository(db_session)

        skill = Skill(
            name=f"Python-{uuid4().hex[:8]}",
        )

        db_session.add(skill)
        db_session.flush()

        job = self._create_job(db_session)

        job_skill = JobSkill(
            job_id=job.id,
            skill_id=skill.id,
        )

        db_session.add(job_skill)
        db_session.flush()

        results = repository.get_top_skills()

        assert any(
            row["skill"] == skill.name
            for row in results
        )

    def test_get_top_skills_with_country_filter(self, db_session):
        repository = JobRepository(db_session)

        skill = Skill(
            name=f"Python-{uuid4().hex[:8]}",
        )

        db_session.add(skill)
        db_session.flush()

        kenya_job = self._create_job(
            db_session,
            country_code="KE",
        )

        germany_job = self._create_job(
            db_session,
            country_code="DE",
        )

        db_session.add_all(
            [
                JobSkill(
                    job_id=kenya_job.id,
                    skill_id=skill.id,
                ),
                JobSkill(
                    job_id=germany_job.id,
                    skill_id=skill.id,
                ),
            ]
        )

        db_session.flush()

        results = repository.get_top_skills(
            country_code="KE",
        )

        assert any(
            row["skill"] == skill.name
            for row in results
        )

    def test_get_stats(self, db_session):
        repository = JobRepository(db_session)

        self._create_job(db_session)

        stats = repository.get_stats()

        assert stats["total_jobs"] >= 1
        assert stats["total_companies"] >= 1
        assert stats["total_countries"] >= 1
        assert stats["total_skills"] >= 0
        assert stats["tech_roles"] >= 1

        assert (
            stats["average_salary_min"] is None
            or isinstance(stats["average_salary_min"], float)
        )

        assert (
            stats["average_salary_max"] is None
            or isinstance(stats["average_salary_max"], float)
        )

    def test_delete_jobs_older_than(self, db_session):
        repository = JobRepository(db_session)

        old_job = self._create_job(
            db_session,
        )

        old_job.scraped_date = datetime.now(UTC) - timedelta(days=60)

        recent_job = self._create_job(
            db_session,
        )

        recent_job.scraped_date = datetime.now(UTC)

        db_session.flush()

        deleted_count = repository.delete_jobs_older_than(
            datetime.now(UTC) - timedelta(days=30),
        )

        assert deleted_count >= 1

        assert (
            db_session.query(Job)
            .filter(Job.id == old_job.id)
            .first()
            is None
        )

        assert (
            db_session.query(Job)
            .filter(Job.id == recent_job.id)
            .first()
            is not None
        )


class TestAnalyticsRepository:
    """Integration tests for AnalyticsRepository."""

    def _create_job(
        self,
        db_session,
        *,
        country_code: str = "KE",
        language: str = "en",
        is_tech_role: bool = True,
        technology_category: str | None = "backend",
        company_name: str = "Analytics Company",
        salary_min: Decimal = Decimal("60000"),
        salary_max: Decimal = Decimal("120000"),
    ) -> Job:
        job = Job(
            title="Analytics Test Engineer",
            description="PostgreSQL integration test",
            company_name=company_name,
            location="Nairobi",
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="USD",
            source_site=f"analytics-{uuid4().hex[:8]}",
            source_id=uuid4().hex,
            source_url="https://example.com/analytics-job",
            posted_date=datetime.now(UTC),
            scraped_date=datetime.now(UTC),
            is_active=True,
            is_deleted=False,
            language=language,
            technology_category=technology_category,
            is_tech_role=is_tech_role,
            country_code=country_code,
            employment_type="full-time",
        )

        db_session.add(job)
        db_session.flush()

        return job

    def test_get_total_jobs(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(db_session)

        assert repository.get_total_jobs() >= 1

    def test_get_top_companies(self, db_session):
        repository = AnalyticsRepository(db_session)

        company = f"Top Company-{uuid4().hex[:8]}"

        self._create_job(
            db_session,
            company_name=company,
        )

        results = repository.get_top_companies(limit=10)

        assert any(
            row["company"] == company
            for row in results
        )

    def test_get_jobs_by_location(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(db_session)

        results = repository.get_jobs_by_location(limit=10)

        assert any(
            row["location"] == "Nairobi"
            for row in results
        )

    def test_get_salary_statistics(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(db_session)

        result = repository.get_salary_statistics()

        assert result["sample_size"] >= 1
        assert result["average"] is not None
        assert result["minimum"] is not None
        assert result["maximum"] is not None
        assert result["median"] is not None

    def test_get_employment_type_distribution(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(db_session)

        results = repository.get_employment_type_distribution()

        assert any(
            row["employment_type"] == "full-time"
            for row in results
        )

    def test_get_salary_by_location(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(db_session)

        results = repository.get_salary_by_location(limit=10)

        assert any(
            row["location"] == "Nairobi"
            for row in results
        )

    def test_get_salary_by_company(self, db_session):
        repository = AnalyticsRepository(db_session)

        company = f"Salary Company-{uuid4().hex[:8]}"

        self._create_job(
            db_session,
            company_name=company,
        )

        results = repository.get_salary_by_company(limit=10)

        assert any(
            row["company"] == company
            for row in results
        )

    def test_get_jobs_posted_by_date(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(db_session)

        results = repository.get_jobs_posted_by_date(days=30)

        assert results

    def test_get_recent_jobs(self, db_session):
        repository = AnalyticsRepository(db_session)

        job = self._create_job(db_session)

        results = repository.get_recent_jobs(
            days=30,
            limit=20,
        )

        assert any(
            result.id == job.id
            for result in results
        )

    def test_get_salary_distribution(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(db_session)

        results = repository.get_salary_distribution()

        assert len(results) == 8
        assert all(
            "range" in row and "count" in row
            for row in results
        )

    def test_get_language_distribution(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            language="en",
        )

        results = repository.get_language_distribution()

        assert any(
            row["language"] == "en"
            for row in results
        )

    def test_get_language_by_country(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            country_code="KE",
            language="en",
        )

        results = repository.get_language_by_country()

        assert any(
            row["country"] == "KE"
            and row["language"] == "en"
            for row in results
        )

    def test_get_english_vs_non_english(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            language="en",
        )

        self._create_job(
            db_session,
            language="fr",
        )

        result = repository.get_english_vs_non_english()

        assert result["total_count"] >= 2
        assert result["english_count"] >= 1
        assert result["non_english_count"] >= 1
        assert 0 <= result["english_percentage"] <= 100

    def test_get_language_salary_stats(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            language="en",
        )

        results = repository.get_language_salary_stats()

        assert any(
            row["language"] == "en"
            for row in results
        )

    def test_get_tech_vs_non_tech(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            is_tech_role=True,
        )

        self._create_job(
            db_session,
            is_tech_role=False,
            technology_category=None,
        )

        result = repository.get_tech_vs_non_tech()

        assert result["total_count"] >= 2
        assert result["tech_count"] >= 1
        assert result["non_tech_count"] >= 1
        assert 0 <= result["tech_percentage"] <= 100

    def test_get_technology_category_distribution(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            technology_category="backend",
            is_tech_role=True,
        )

        results = repository.get_technology_category_distribution()

        assert any(
            row["category"] == "backend"
            for row in results
        )

    def test_get_tech_by_country(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            country_code="KE",
            is_tech_role=True,
        )

        results = repository.get_tech_by_country()

        assert any(
            row["country"] == "KE"
            and row["tech_count"] >= 1
            for row in results
        )

    def test_get_tech_skills(self, db_session):
        repository = AnalyticsRepository(db_session)

        skill = Skill(
            name=f"Python-{uuid4().hex[:8]}",
        )

        db_session.add(skill)
        db_session.flush()

        job = self._create_job(
            db_session,
            is_tech_role=True,
        )

        db_session.add(
            JobSkill(
                job_id=job.id,
                skill_id=skill.id,
            )
        )

        db_session.flush()

        results = repository.get_tech_skills()

        assert any(
            row["skill"] == skill.name
            for row in results
        )

    def test_get_tech_salary_stats(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            is_tech_role=True,
        )

        result = repository.get_tech_salary_stats()

        assert result["sample_size"] >= 1
        assert result["average"] is not None
        assert result["minimum"] is not None
        assert result["maximum"] is not None
        assert result["median"] is not None

    def test_get_enriched_top_skills(self, db_session):
        repository = AnalyticsRepository(db_session)

        skill = Skill(
            name=f"Python-{uuid4().hex[:8]}",
        )

        db_session.add(skill)
        db_session.flush()

        job = self._create_job(
            db_session,
            country_code="KE",
            is_tech_role=True,
        )

        db_session.add(
            JobSkill(
                job_id=job.id,
                skill_id=skill.id,
            )
        )

        db_session.flush()

        results = repository.get_enriched_top_skills(
            limit=20,
            country_code="KE",
            tech_only=True,
        )

        assert any(
            row["skill"] == skill.name
            for row in results
        )

    def test_get_country_distribution(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            country_code="KE",
        )

        results = repository.get_country_distribution()

        assert any(
            row["country"] == "KE"
            for row in results
        )

    def test_get_enriched_salary_statistics(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            country_code="KE",
            is_tech_role=True,
        )

        result = repository.get_enriched_salary_statistics(
            country_code="KE",
            tech_only=True,
        )

        assert result["average_min"] is not None
        assert result["average_max"] is not None
        assert result["minimum"] is not None
        assert result["maximum"] is not None
        assert result["median"] is not None
        assert result["currency"] == "USD"

    def test_get_technology_distribution_alias(self, db_session):
        repository = AnalyticsRepository(db_session)

        self._create_job(
            db_session,
            technology_category="backend",
            is_tech_role=True,
        )

        results = repository.get_technology_distribution()

        assert any(
            row["category"] == "backend"
            for row in results
        )


class TestPipelineRunRepository:
    """Integration tests for PipelineRunRepository."""

    def test_create_pipeline_run(self, db_session):
        repository = PipelineRunRepository(db_session)

        run = repository.create(
            source_site="integration-test",
        )

        assert run.id is not None
        assert run.source_site == "integration-test"
        assert run.status == "running"
        assert run.records_processed == 0

    def test_create_pipeline_run_with_custom_started_at(self, db_session):
        repository = PipelineRunRepository(db_session)

        started_at = datetime.now(UTC) - timedelta(seconds=10)

        run = repository.create(
            source_site="integration-test",
            started_at=started_at,
        )

        assert run.started_at == started_at

    def test_finish_pipeline_run(self, db_session):
        repository = PipelineRunRepository(db_session)

        started_at = datetime.now(UTC) - timedelta(seconds=5)

        run = repository.create(
            source_site="integration-test",
            started_at=started_at,
        )

        finished = repository.finish(
            run,
            status="completed",
            records_processed=10,
        )

        assert finished.status == "completed"
        assert finished.records_processed == 10
        assert finished.completed_at is not None
        assert finished.duration_seconds is not None
        assert finished.duration_seconds >= 0

    def test_finish_pipeline_run_with_error(self, db_session):
        repository = PipelineRunRepository(db_session)

        run = repository.create(
            source_site="integration-test",
        )

        finished = repository.finish(
            run,
            status="failed",
            records_processed=5,
            error_message="Integration test failure",
        )

        assert finished.status == "failed"
        assert finished.records_processed == 5
        assert finished.error_message == "Integration test failure"
        assert finished.completed_at is not None

    def test_get_running_run(self, db_session):
        repository = PipelineRunRepository(db_session)

        repository.create(
            source_site="integration-test",
        )

        result = repository.get_running_run()

        assert result is not None
        assert result["status"] == "running"
        assert result["source_site"] == "integration-test"

    def test_get_latest_completed_run(self, db_session):
        repository = PipelineRunRepository(db_session)

        run = repository.create(
            source_site="integration-test",
        )

        repository.finish(
            run,
            status="completed",
            records_processed=25,
        )

        result = repository.get_latest_completed_run()

        assert result is not None
        assert result["status"] == "completed"
        assert result["records_processed"] == 25
        assert result["source_site"] == "integration-test"

    def test_get_last_run_time(self, db_session):
        repository = PipelineRunRepository(db_session)

        run = repository.create(
            source_site="integration-test",
        )

        repository.finish(
            run,
            status="completed",
            records_processed=1,
        )

        result = repository.get_last_run_time()

        assert result is not None
        assert isinstance(result, datetime)

    def test_format_last_run_time(self, db_session):
        repository = PipelineRunRepository(db_session)

        run = repository.create(
            source_site="integration-test",
        )

        repository.finish(
            run,
            status="completed",
            records_processed=1,
        )

        result = repository.format_last_run_time()

        assert isinstance(result, str)
        assert result != "No runs yet"