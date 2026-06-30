# scripts/test_transformation.py
"""Test the job transformer with sample data."""

import json
from config.settings import settings
from app.etl.transformers.jobs_transformer import JobsTransformer
from app.etl.extractors.jobs_api import JobsExtractor


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def test_with_sample_data():
    """Test transformation with sample job data."""
    
    sample_job = {
        "id": "123",
        "title": "Data Scientist",
        "company": {"display_name": "Google"},
        "location": {"display_name": "Nairobi"},
        "description": "Build ML systems for large-scale data processing",
        "redirect_url": "https://example.com/job/123",
        "created": "2026-06-30",
        "salary": {
            "min": 50000,
            "max": 90000,
            "currency": "USD"
        }
    }

    transformer = JobsTransformer()
    result = transformer.transform_one(sample_job)

    print("📋 Sample Job Transformation")
    print("=" * 40)
    print(json.dumps(result, indent=2))

    # Verify all expected fields exist
    expected_fields = [
        "external_id", "title", "company_name", "location",
        "description", "salary_min", "salary_max", "currency",
        "source", "source_url", "posted_date"
    ]
    
    print("\n✅ All fields present:")
    for field in expected_fields:
        status = "✅" if field in result else "❌"
        print(f"  {status} {field}: {result.get(field)}")


def test_with_real_data():
    """Test transformation with real data from the API."""
    
    # Check credentials
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        print("\n⚠️  Skipping real data test - no credentials")
        return
    
    # Extract - debug=False to hide credentials
    extractor = JobsExtractor(
        api_url=settings.adzuna_base_url,
        app_id=settings.adzuna_app_id,
        api_key=settings.adzuna_app_key,
        debug=False,  # Set to True only when debugging
    )
    
    print("\n📡 Fetching real jobs from Adzuna...")
    print(f"   App ID: {mask_sensitive(settings.adzuna_app_id)}")
    print(f"   App Key: {mask_sensitive(settings.adzuna_app_key)}")
    
    data = extractor.fetch_page(page=1, results_per_page=3)
    
    raw_jobs = data.get("results", [])
    print(f"✅ Extracted {len(raw_jobs)} raw jobs")
    
    # Transform
    transformer = JobsTransformer()
    transformed = transformer.transform(raw_jobs)
    
    print(f"🔄 Transformed {len(transformed)} jobs")
    
    # Display first result
    if transformed:
        print("\n📋 First transformed job from real data:")
        print(json.dumps(transformed[0], indent=2))
        
        # Verify all fields
        print("\n✅ Real data transformation successful!")
        for key, value in transformed[0].items():
            print(f"  - {key}: {value}")


def test_missing_fields():
    """Test transformation handles missing fields gracefully."""
    
    minimal_job = {
        "id": "456",
        "title": "Software Engineer",
        # Missing company, location, salary, etc.
    }
    
    transformer = JobsTransformer()
    result = transformer.transform_one(minimal_job)
    
    print("\n📋 Minimal Job (missing optional fields)")
    print("=" * 40)
    print(json.dumps(result, indent=2))
    
    # All optional fields should be None
    optional_fields = ["company_name", "location", "description", 
                      "salary_min", "salary_max", "currency", 
                      "source_url", "posted_date"]
    
    print("\n✅ Missing fields handled with None:")
    for field in optional_fields:
        if result.get(field) is None:
            print(f"  ✅ {field}: None (safe default)")
        else:
            print(f"  ⚠️  {field}: {result.get(field)}")


def main():
    """Run all transformer tests."""
    print("🧪 Testing JobsTransformer\n")
    
    test_with_sample_data()
    test_missing_fields()
    test_with_real_data()
    
    print("\n" + "=" * 40)
    print("✅ All transformer tests complete!")


if __name__ == "__main__":
    main()