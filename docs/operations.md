# Operations Guide

## Purpose

This document explains how to monitor and operate the deployed Job Market Intelligence system during normal operation.

It focuses on:

- API health
- Database readiness
- ETL status
- ETL run history
- GitHub Actions
- Render
- Streamlit Community Cloud
- Production monitoring
- Operational checks
- Manual ETL execution

Deployment, rollback, and recovery procedures are documented separately in [`deployment.md`](deployment.md).

Failure diagnosis is documented in [`troubleshooting.md`](troubleshooting.md).

---

## Production Architecture

The production system consists of:

```text
GitHub
   │
   ├── GitHub Actions
   │       ├── CI
   │       └── ETL workflow
   │
   ├── Render
   │       └── FastAPI API
   │
   └── Streamlit Community Cloud
           └── Dashboard

Render API
   │
   ▼
Neon PostgreSQL
````

The API reads production data from Neon PostgreSQL.

The Streamlit dashboard consumes the API rather than connecting directly to the production database.

---

## API Health Monitoring

The API exposes several health endpoints under `/api/v1`.

### Liveness

```text
GET /api/v1/health/live
```

Purpose:

* Confirms that the API process is alive
* Used by Render as the liveness health-check endpoint

A successful liveness response does not prove that the database or external dependencies are available.

### Readiness

```text
GET /api/v1/health/ready
```

Purpose:

* Verifies that the API is ready to serve requests
* Checks database readiness
* Returns an unsuccessful status when the database is unavailable

### General Health

```text
GET /api/v1/health
```

Provides broader health information including:

* API health
* Database connectivity
* Database response time
* Environment
* Version
* Uptime
* Timestamp

### Database Health

```text
GET /api/v1/health/database
```

Checks the database connection and reports database response information.

---

## ETL Monitoring

The ETL pipeline records execution information in the `pipeline_runs` table.

The recorded information supports operational monitoring such as:

* Run status
* Start time
* Completion time
* Records processed
* Duration
* Failure information
* Rejected or failed records where recorded by the pipeline

The API exposes several ETL monitoring endpoints.

### Last ETL Run

```text
GET /api/v1/analytics/etl/last-run
```

Returns a human-readable relative time describing when the last ETL run occurred.

Example concept:

```text
{
  "last_run": "2 hours ago"
}
```

### Last ETL Run Time

```text
GET /api/v1/analytics/etl/last-run-time
```

Returns the actual datetime of the most recent ETL run.

Example structure:

```text
{
  "last_run_time": "2026-09-01T06:15:00"
}
```

The exact value depends on the most recent recorded production run.

### Current ETL Status

```text
GET /api/v1/analytics/etl/status
```

Returns the current ETL state.

Possible values include:

```text
Running
Idle
Unknown
```

### ETL Database Status

```text
GET /api/v1/analytics/etl/db-status
```

Reports the database status used by the ETL monitoring layer.

Possible values include:

```text
Operational
Degraded
Unknown
```

These endpoints are useful for operational monitoring but do not replace inspection of GitHub Actions logs when an ETL run fails.

---

## Normal Operational Check

A basic API operational check can be performed in this order:

```text
1. API liveness
       ↓
2. API readiness
       ↓
3. Database health
       ↓
4. ETL status
       ↓
5. Last ETL run
       ↓
6. Dashboard availability
```

For example:

```bash id="7g4k9c"
curl http://localhost:8000/api/v1/health/live
curl http://localhost:8000/api/v1/health/ready
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/database
curl http://localhost:8000/api/v1/analytics/etl/status
curl http://localhost:8000/api/v1/analytics/etl/last-run
curl http://localhost:8000/api/v1/analytics/etl/last-run-time
curl http://localhost:8000/api/v1/analytics/etl/db-status
```

For production, replace the local API address with the deployed API URL.

---

## ETL Automation

The ETL workflow is defined in:

```text
.github/workflows/etl-pipeline.yml
```

The workflow currently supports manual execution through `workflow_dispatch`.

The scheduled trigger is currently suspended pending remediation of the Neon data-transfer limitation.

Current state:

```text
Manual workflow_dispatch
        │
        ▼
      Available

Scheduled execution
        │
        ▼
      Suspended
```

The suspension should not be interpreted as removal of the ETL pipeline itself. The pipeline can still be executed manually.

---

## Manually Running the ETL Workflow

To run the ETL pipeline manually:

1. Open the repository on GitHub.
2. Open the **Actions** tab.
3. Select the **Daily ETL Pipeline** workflow.
4. Select **Run workflow**.
5. Select the required branch.
6. Start the workflow.
7. Monitor the workflow steps until completion.

The workflow performs:

```text
Checkout
   ↓
Python setup
   ↓
Dependency installation
   ↓
Database migrations
   ↓
Production configuration validation
   ↓
ETL pipeline execution
```

The workflow uses concurrency protection so that overlapping ETL runs are not intentionally started against the same production pipeline.

---

## Monitoring an ETL Run

When monitoring a manually triggered ETL run, check:

1. Workflow started successfully
2. Dependencies installed successfully
3. Database migrations completed
4. Production configuration validation passed
5. ETL extraction completed
6. Transformation and enrichment completed
7. Validation completed
8. Database loading completed
9. Pipeline summary was recorded
10. Workflow completed successfully

If a run fails, inspect the GitHub Actions logs before attempting another run.

Repeated manual retries should not be used as a substitute for diagnosing the failure.

---

## Render Operations

The FastAPI API is deployed on Render.

The normal deployment path is:

```text
GitHub push
    ↓
Render auto-deploy
    ↓
Docker build
    ↓
Container startup
    ↓
Alembic migrations
    ↓
Uvicorn
    ↓
/api/v1/health/live
    ↓
Live
```

When checking the API deployment, verify:

* Deployment completed successfully
* Container started
* Database migrations completed
* Uvicorn started
* Liveness health check succeeds
* API endpoints respond normally

Render application rollback is documented in [`deployment.md`](deployment.md).

A Render application rollback does not automatically undo database migrations or restore database data.

---

## Neon PostgreSQL Operations

Neon provides the production PostgreSQL database.

Operational checks should include:

* Database availability
* Data-transfer quota
* Database connectivity from Render
* Database connectivity from GitHub Actions when ETL runs
* Migration state
* Query performance where relevant

A database-provider problem can appear as an API problem.

For example, if the API container cannot connect to Neon during startup, Alembic may fail before Uvicorn starts. Render may subsequently report that no application port is available.

Therefore, check database availability before treating a startup failure as an application-code failure.

---

## Streamlit Community Cloud Operations

The Streamlit dashboard is deployed separately from the FastAPI API.

Operational checks include:

* Dashboard application is running
* Dashboard can reach the configured API
* API URL is correct
* API is healthy
* Dashboard pages load
* API-backed data can be retrieved

A dashboard failure does not necessarily indicate an API failure, and an API failure can cause dashboard errors even when the dashboard deployment itself is healthy.

---

## Logs

Use the component responsible for the operation being investigated.

| Component | Primary logs                     |
| --------- | -------------------------------- |
| FastAPI   | Render service logs              |
| ETL       | GitHub Actions workflow logs     |
| Database  | Neon project/database monitoring |
| Dashboard | Streamlit Community Cloud logs   |
| CI        | GitHub Actions workflow logs     |

Do not rely on a single component's logs when diagnosing a cross-service failure.

---

## Routine Operational Checks

A practical production check should verify:

### API

* Liveness succeeds
* Readiness succeeds
* Database health succeeds
* Main API requests respond

### Database

* Neon is available
* Data-transfer limits are not blocking connections
* API can connect
* ETL can connect when executed

### ETL

* Latest run time is known
* ETL status is not unexpectedly `Running`
* Latest workflow completed successfully
* Pipeline metrics are recorded

### Dashboard

* Dashboard loads
* API-backed pages load
* No widespread API connection errors occur

### Automation

* GitHub Actions workflows are available
* Manual ETL trigger works when required
* Scheduled ETL state is understood

---

## ETL Scheduling Limitation

The scheduled ETL trigger is currently suspended because of the Neon data-transfer limitation.

This means operational monitoring must not assume that a new ETL run occurs automatically every day.

Until the scheduling limitation is resolved:

```text
Production data refresh
        │
        ▼
Manual workflow_dispatch
        │
        ▼
ETL execution
```

Once scheduled execution is restored, this document and the relevant deployment/automation documentation should be updated to reflect the new operational state.

---

## Operational Boundaries

This document describes normal operation.

Use the following documentation for other situations:

* [`development.md`](development.md) — local development
* [`testing.md`](testing.md) — automated testing
* [`deployment.md`](deployment.md) — deployment, rollback, and recovery
* [`troubleshooting.md`](troubleshooting.md) — failure diagnosis
* [`architecture.md`](architecture.md) — system architecture
* [`api_contract.md`](api_contract.md) — API behavior
* [`database_schema.md`](database_schema.md) — database structure
