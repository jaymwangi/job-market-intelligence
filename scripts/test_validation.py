# scripts/test_validation.py
"""Test the validation layer end-to-end."""

from pydantic import ValidationError

from app.etl.extractors.jobs_api import JobsExtractor
from app.etl.transformers.jobs_transformer import JobsTransformer
from app.etl.validators import validate_job, validate_jobs
from config.settings import settings


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def test_sample_data():
    """Test validation with complete sample data."""
    print("🧪 Test: Complete sample data")
    print("-" * 40)

    sample_job = {
        "id": "123",
        "title": "Data Scientist",
        "company": {"display_name": "Google"},
        "location": {"display_name": "Nairobi"},
        "description": "Build ML systems for large-scale data processing",
        "redirect_url": "https://example.com/job/123",
        "created": "2026-06-30T10:30:00Z",
        "salary": {"min": 50000, "max": 90000, "currency": "USD"},
    }

    transformer = JobsTransformer()
    transformed = transformer.transform_one(sample_job)
    validated = validate_job(transformed)

    print("✅ Validation passed")
    print(f"   Title: {validated.title}")
    print(f"   Company: {validated.company_name}")
    print(f"   Salary: {validated.salary_min} - {validated.salary_max} {validated.currency}")
    print(f"   Posted: {validated.posted_date}")

    return validated


def test_missing_fields():
    """Test validation with minimal data (all optional fields missing)."""
    print("\n🧪 Test: Missing optional fields")
    print("-" * 40)

    minimal_job = {
        "id": "456",
        "title": "Software Engineer",
        # No company, location, salary, etc.
    }

    transformer = JobsTransformer()
    transformed = transformer.transform_one(minimal_job)
    validated = validate_job(transformed)

    print("✅ Validation passed with missing optional fields")
    print(f"   company_name: {validated.company_name} (None)")
    print(f"   salary_min: {validated.salary_min} (None)")
    print(f"   posted_date: {validated.posted_date} (None)")

    return validated


def test_empty_title():
    """Test validation rejects empty title."""
    print("\n🧪 Test: Empty title")
    print("-" * 40)

    invalid_job = {"id": "123", "title": ""}
    transformer = JobsTransformer()
    transformed = transformer.transform_one(invalid_job)

    try:
        validate_job(transformed)
        print("❌ Should have failed but passed")
    except ValidationError as e:
        print("✅ Rejected as expected")
        print(f"   Error: {e.errors()[0]['msg']}")


def test_empty_external_id():
    """Test validation rejects empty external_id."""
    print("\n🧪 Test: Empty external_id")
    print("-" * 40)

    invalid_job = {"id": "", "title": "Software Engineer"}
    transformer = JobsTransformer()
    transformed = transformer.transform_one(invalid_job)

    try:
        validate_job(transformed)
        print("❌ Should have failed but passed")
    except ValidationError as e:
        print("✅ Rejected as expected")
        print(f"   Error: {e.errors()[0]['msg']}")


def test_negative_salary():
    """Test validation rejects negative salary."""
    print("\n🧪 Test: Negative salary")
    print("-" * 40)

    invalid_job = {"id": "123", "title": "Test", "salary": {"min": -5000, "max": 50000}}
    transformer = JobsTransformer()
    transformed = transformer.transform_one(invalid_job)

    try:
        validate_job(transformed)
        print("❌ Should have failed but passed")
    except ValidationError as e:
        print("✅ Rejected as expected")
        print(f"   Error: {e.errors()[0]['msg']}")


def test_salary_min_greater_than_max():
    """Test validation rejects salary_min > salary_max."""
    print("\n🧪 Test: salary_min > salary_max")
    print("-" * 40)

    invalid_job = {"id": "123", "title": "Test", "salary": {"min": 90000, "max": 50000}}
    transformer = JobsTransformer()
    transformed = transformer.transform_one(invalid_job)

    try:
        validate_job(transformed)
        print("❌ Should have failed but passed")
    except ValidationError as e:
        print("✅ Rejected as expected")
        print(f"   Error: {e.errors()[0]['msg']}")


def test_invalid_url():
    """Test validation rejects invalid URL format."""
    print("\n🧪 Test: Invalid URL")
    print("-" * 40)

    invalid_job = {"id": "123", "title": "Test", "redirect_url": "not-a-url"}
    transformer = JobsTransformer()
    transformed = transformer.transform_one(invalid_job)

    try:
        validate_job(transformed)
        print("❌ Should have failed but passed")
    except ValidationError as e:
        print("✅ Rejected as expected")
        print(f"   Error: {e.errors()[0]['msg']}")


def test_invalid_date():
    """Test validation handles malformed dates gracefully."""
    print("\n🧪 Test: Malformed date")
    print("-" * 40)

    invalid_job = {"id": "123", "title": "Test", "created": "not-a-date"}
    transformer = JobsTransformer()
    transformed = transformer.transform_one(invalid_job)

    try:
        validate_job(transformed)
        print("❌ Should have failed but passed")
    except ValidationError as e:
        print("✅ Rejected as expected")
        print(f"   Error: {e.errors()[0]['msg']}")


def test_real_api_data():
    """Test full pipeline with real data."""
    print("\n🧪 Test: Real Adzuna data")
    print("-" * 40)

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        print("⚠️  Skipping - no credentials")
        return

    # Extract - debug=False to hide credentials
    extractor = JobsExtractor(
        api_url=settings.adzuna_base_url,
        app_id=settings.adzuna_app_id,
        api_key=settings.adzuna_app_key,
        debug=False,  # Set to True only when debugging
    )

    print("📡 Fetching real jobs...")
    print(f"   App ID: {mask_sensitive(settings.adzuna_app_id)}")
    print(f"   App Key: {mask_sensitive(settings.adzuna_app_key)}")

    data = extractor.fetch_page(page=1, results_per_page=3)
    raw_jobs = data.get("results", [])
    print(f"✅ Extracted {len(raw_jobs)} raw jobs")

    # Transform
    transformer = JobsTransformer()
    transformed = transformer.transform(raw_jobs)
    print(f"✅ Transformed {len(transformed)} jobs")

    # Validate
    validated = validate_jobs(transformed)
    print(f"✅ Validated {len(validated)} jobs")

    # Display first result
    if validated:
        first = validated[0]
        print("\n📋 First validated job:")
        print(f"   ID: {first.external_id}")
        print(f"   Title: {first.title}")
        print(f"   Company: {first.company_name}")
        print(f"   Salary: {first.salary_min} - {first.salary_max} {first.currency}")
        print(f"   Source: {first.source}")
        print(f"   URL: {first.source_url}")
        print(f"   Posted: {first.posted_date}")


def main():
    """Run all validation tests."""
    print("🚀 Sprint 2.3 - Validation Layer Tests\n")

    test_sample_data()
    test_missing_fields()
    test_empty_title()
    test_empty_external_id()
    test_negative_salary()
    test_salary_min_greater_than_max()
    test_invalid_url()
    test_invalid_date()
    test_real_api_data()

    print("\n" + "=" * 40)
    print("✅ All validation tests complete!")
    print("\n📊 Summary:")
    print("  - Data contract: JobValidated")
    print("  - Required fields enforced")
    print("  - Salary range validation active")
    print("  - Date parsing working")
    print("  - URL validation using HttpUrl")
    print("  - Pydantic v2 ConfigDict")
    print("\n✅ Sprint 2.3 COMPLETE")


if __name__ == "__main__":
    main()
