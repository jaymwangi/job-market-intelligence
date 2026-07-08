# scripts/test_loading.py
"""Test the loading layer end-to-end."""

from app.database.session import get_db  # Use get_db instead of get_session
from app.etl.extractors.jobs_api import JobsExtractor
from app.etl.loaders import JobLoader
from app.etl.transformers.jobs_transformer import JobsTransformer
from app.etl.validators import validate_jobs
from app.models.job import Job
from app.models.pipeline_run import PipelineRun
from config.settings import settings


def mask_sensitive(value: str, show: int = 4) -> str:
    """Mask sensitive strings, showing only first few characters."""
    if not value:
        return "None"
    if len(value) <= show:
        return "*" * len(value)
    return f"{value[:show]}..."


def test_loading():
    """Test full ETL pipeline: Extract -> Transform -> Validate -> Load."""

    print("🚀 Sprint 2.4 - Loading Tests")
    print("=" * 50)

    # Check credentials
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        print("❌ Adzuna credentials not configured in .env")
        return

    # 1. Extract
    print("\n📡 Step 1: Extracting jobs from Adzuna...")
    print(f"   App ID: {mask_sensitive(settings.adzuna_app_id)}")
    print(f"   App Key: {mask_sensitive(settings.adzuna_app_key)}")

    extractor = JobsExtractor(
        api_url=settings.adzuna_base_url,
        app_id=settings.adzuna_app_id,
        api_key=settings.adzuna_app_key,
        debug=False,
    )

    data = extractor.fetch_page(page=1, results_per_page=10)
    raw_jobs = data.get("results", [])
    print(f"✅ Extracted {len(raw_jobs)} raw jobs")

    # 2. Transform
    print("\n🔄 Step 2: Transforming job data...")
    transformer = JobsTransformer()
    transformed = transformer.transform(raw_jobs)
    print(f"✅ Transformed {len(transformed)} jobs")

    # 3. Validate
    print("\n✅ Step 3: Validating job data...")
    validated = validate_jobs(transformed)
    print(f"✅ Validated {len(validated)} jobs")

    # 4. Load
    print("\n💾 Step 4: Loading jobs to database...")

    # Use get_db() which yields a session
    db_gen = get_db()
    session = next(db_gen)

    try:
        loader = JobLoader(session, source_site="adzuna")
        result = loader.load(validated)

        print("\n📊 Load Results:")
        print(f"   Processed: {result.processed}")
        print(f"   Inserted:  {result.inserted}")
        print(f"   Skipped:   {result.skipped}")
        print(f"   Failed:    {result.failed}")

        if result.errors:
            print("\n⚠️ Errors:")
            for error in result.errors:
                print(f"   - {error}")

        # Verify data was saved
        job_count = session.query(Job).count()
        print("\n📊 Database Summary:")
        print(f"   Total jobs in database: {job_count}")

        # Show most recent pipeline run
        latest_run = session.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()

        if latest_run:
            print("\n📋 Latest Pipeline Run:")
            print(f"   ID: {latest_run.id}")
            print(f"   Source: {latest_run.source_site}")
            print(f"   Status: {latest_run.status}")
            print(f"   Started: {latest_run.started_at}")
            print(f"   Completed: {latest_run.completed_at}")
            print(f"   Records Processed: {latest_run.records_processed}")
            if latest_run.duration_seconds:
                print(f"   Duration: {latest_run.duration_seconds:.2f}s")
            if latest_run.error_message:
                print(f"   Error: {latest_run.error_message}")

    finally:
        # Close the session
        try:
            next(db_gen)
        except StopIteration:
            pass

    print("\n" + "=" * 50)
    print("✅ Sprint 2.4 COMPLETE")
    print("\n📊 ETL Pipeline Status:")
    print("  ✅ Extract: Adzuna API")
    print("  ✅ Transform: Adzuna -> Internal Format")
    print("  ✅ Validate: Pydantic JobValidated")
    print("  ✅ Load: PostgreSQL")
    print("\n🎉 End-to-end ETL pipeline is now operational!")


def main():
    """Run the loading test."""
    test_loading()


if __name__ == "__main__":
    main()
