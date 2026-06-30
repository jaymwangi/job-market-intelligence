# scripts/test_extraction.py
"""Verify job extraction works."""

import json
from config.settings import settings
from app.etl.extractors.jobs_api import JobsExtractor


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def main():
    """Test fetching real job data from Adzuna API."""
    
    # Check if credentials are configured
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        print("❌ Adzuna credentials not configured in .env")
        print("   Please set ADZUNA_APP_ID and ADZUNA_APP_KEY")
        return
    
    # Initialize extractor with settings - debug=False to hide credentials
    extractor = JobsExtractor(
        api_url=settings.adzuna_base_url,
        app_id=settings.adzuna_app_id,
        api_key=settings.adzuna_app_key,
        debug=False,  # Set to True only when debugging
    )
    
    print("📡 Fetching jobs from Adzuna API...")
    print(f"   URL: {settings.adzuna_base_url}/jobs/gb/search/1")
    print(f"   App ID: {mask_sensitive(settings.adzuna_app_id)}")
    print(f"   App Key: {mask_sensitive(settings.adzuna_app_key)}")
    
    try:
        # Fetch one page of jobs
        data = extractor.fetch_page(
            page=1,
            results_per_page=5
        )
        
        # Display results
        print(f"\n✅ Success! Fetched {data.get('count', 0)} matching jobs")
        print(f"📄 Jobs returned this page: {len(data.get('results', []))}")
        
        if data.get("results"):
            print("\n📋 First job preview:")
            first_job = data["results"][0]
            preview = json.dumps(first_job, indent=2)
            print(preview[:600] + "..." if len(preview) > 600 else preview)
            
            # Field inspection for Sprint 2.2
            print("\n🔍 Fields available in response:")
            for key in sorted(first_job.keys()):
                print(f"  - {key}")
        else:
            print("⚠️  No job results found")
            
    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")


if __name__ == "__main__":
    main()