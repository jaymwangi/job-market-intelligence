"""Unit tests for the Job model."""

import pytest

from app.models.job import Job


class TestJobValidators:
    def test_validate_confidence_rejects_out_of_range(self):
        job = Job.__new__(Job)

        with pytest.raises(
            ValueError,
            match="tech_confidence must be between 0.0 and 1.0",
        ):
            job.validate_confidence("tech_confidence", 1.5)

    def test_validate_salary_currency_rejects_invalid_length(self):
        job = Job.__new__(Job)

        with pytest.raises(
            ValueError,
            match="salary_currency must be a 3-letter ISO 4217 code",
        ):
            job.validate_salary_currency("salary_currency", "US")

    def test_validate_country_code_rejects_invalid_length(self):
        job = Job.__new__(Job)

        with pytest.raises(
            ValueError,
            match="country_code must be a 2-letter ISO 3166-1 alpha-2 code",
        ):
            job.validate_country_code("country_code", "KEN")

    def test_validate_confidence_accepts_valid_value(self):
        job = Job.__new__(Job)

        result = job.validate_confidence("tech_confidence", 0.85)

        assert result == 0.85


class TestJobRepr:
    def test_repr_with_long_title(self):
        job = Job(
            title="A" * 60,
            company_name="TechCorp",
            source_site="adzuna",
            language="en",
            is_tech_role=True,
        )

        result = repr(job)

        assert result.startswith("<Job(")
        assert "title='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'" in result
        assert "company='TechCorp'" in result
        assert "source='adzuna'" in result
        assert "language='en'" in result
        assert "is_tech=True" in result

    def test_repr_with_missing_title_and_company(self):
        job = Job(
            title=None,
            company_name=None,
            source_site="adzuna",
            language="en",
            is_tech_role=False,
        )

        result = repr(job)

        assert "title=''" in result
        assert "company=''" in result
        assert "source='adzuna'" in result
        assert "language='en'" in result
        assert "is_tech=False" in result
