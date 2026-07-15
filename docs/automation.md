# Pipeline Automation

The ETL pipeline runs automatically every day at 6:00 AM UTC via GitHub Actions.

## How It Works

1. GitHub Actions triggers on schedule
2. Checks out code
3. Installs dependencies
4. Runs database migrations
5. Executes the ETL pipeline

## Pipeline Steps

1. **Extract** - Fetch jobs from Adzuna API
2. **Transform** - Convert to internal schema
3. **Validate** - Ensure data quality
4. **Upsert** - Insert new jobs, update existing jobs
5. **Delete** - Remove jobs older than retention period (based on scraped_date)
6. **Record** - Track execution metrics

## Retention Policy

Jobs are retained for a configurable number of days based on **when they were last scraped**, not when they were originally posted. This prevents jobs from being repeatedly deleted and re-inserted if they are reposted.

## Configuration

Settings in `config/settings.py`:

- `pipeline_results_per_page`: 25
- `pipeline_max_pages`: 5
- `pipeline_retention_days`: 90

## Secrets Required

- `DATABASE_URL` - Neon PostgreSQL connection string
- `ADZUNA_APP_ID` - Adzuna API app ID
- `ADZUNA_APP_KEY` - Adzuna API app key

## Monitoring

- View workflow runs: GitHub Actions → Daily ETL Pipeline
- Concurrency protection prevents overlapping runs

## Manual Trigger

1. Go to GitHub Actions
2. Select "Daily ETL Pipeline"
3. Click "Run workflow"
4. Select branch → Run workflow