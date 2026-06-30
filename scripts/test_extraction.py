# scripts/test_extraction.py
"""Verify job extraction works."""

import json
from config.settings import settings
from app.etl.extractors.jobs_api import JobsExtractor


def main():
    """Test fetching real job data from Adzuna API."""
    
    # Check if credentials are configured
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        print("❌ Adzuna credentials not configured in .env")
        print("   Please set ADZUNA_APP_ID and ADZUNA_APP_KEY")
        return
    
    # Initialize extractor with settings - using GB market
    extractor = JobsExtractor(
        api_url=settings.adzuna_base_url,
        app_id=settings.adzuna_app_id,
        api_key=settings.adzuna_app_key,
    )
    
    print("📡 Fetching jobs from Adzuna API...")
    print(f"   App ID: {settings.adzuna_app_id[:4]}...")
    
    try:
        # Fetch one page of jobs
        data = extractor.fetch_page(
            page=1,
            results_per_page=5
        )
        
        # Display results - Fixed to use correct fields
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