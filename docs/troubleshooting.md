# Troubleshooting Guide

## Purpose

This guide helps diagnose common failures in the Job Market Intelligence system.

Use this document when the system is not behaving as expected.

For normal operation, see [`operations.md`](operations.md).

For deployment, rollback, and recovery procedures, see [`deployment.md`](deployment.md).

For local development problems, see [`development.md`](development.md).

---

## Troubleshooting Approach

Start from the failing component and work outward.

```text
Symptom
   ↓
Identify component
   ↓
Check logs
   ↓
Check dependencies
   ↓
Check configuration
   ↓
Verify database/API connectivity
   ↓
Apply the smallest appropriate fix
   ↓
Re-run verification
````

Do not immediately roll back application code when the failure may be caused by an external dependency such as the database provider.

---

## Quick Diagnostic Map

| Symptom                        | First place to check                           |
| ------------------------------ | ---------------------------------------------- |
| API does not start             | Render logs and database connectivity          |
| API liveness fails             | Render service logs                            |
| API readiness fails            | Database connectivity                          |
| Database health fails          | Neon availability and connection configuration |
| ETL workflow fails             | GitHub Actions logs                            |
| ETL cannot connect to database | Neon availability, `DATABASE_URL`, quota       |
| Dashboard cannot load data     | Dashboard logs and API health                  |
| Migration fails                | Database connectivity and migration state      |
| Render reports no open port    | Container startup logs before Uvicorn          |
| Tests fail locally             | Test output, environment, database services    |
| CI fails                       | GitHub Actions workflow logs                   |

---

## API Startup Failure

### Symptoms

Typical symptoms include:

* Render deployment does not become live
* Container starts and then exits
* Render reports no open port
* `/api/v1/health/live` is unavailable

### First checks

Inspect the Render deployment logs.

Look for the sequence:

```text
Container startup
    ↓
alembic upgrade head
    ↓
uvicorn
```

The Docker startup command runs:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Therefore, if the migration command fails, Uvicorn does not start.

A later message such as:

```text
No open ports detected
```

may therefore be a downstream symptom rather than the root cause.

### Diagnostic steps

1. Check the earliest database or migration error in the Render logs.
2. Verify that Neon is available.
3. Verify the production `DATABASE_URL`.
4. Check whether the database provider has imposed a quota or connection restriction.
5. Only after the database is confirmed available, investigate application startup or migration code.

---

## Database Connection Failure

### Symptoms

Possible symptoms include:

* `/api/v1/health/ready` returns an error
* `/api/v1/health/database` reports failure
* ETL cannot start
* Alembic cannot connect
* Render deployment fails during startup
* GitHub Actions ETL fails during migration

### Checks

Verify the database from the environment where the failure occurs.

For local development:

```bash
alembic current
```

For production, inspect the Render or GitHub Actions logs and verify the Neon database status.

Do not assume that successful local database connectivity proves that production connectivity is working.

---

## Neon Data-Transfer Quota Failure

A real production deployment failure occurred because the Neon project exceeded its data-transfer quota.

The database connection error reported:

```text
Your project has exceeded the data transfer quota.
Upgrade your plan to increase limits.
```

Additional connection attempts reported:

```text
Network is unreachable
```

Render subsequently reported:

```text
No open ports detected, continuing to scan...
```

### Failure chain

```text
Neon data-transfer quota exceeded
            ↓
Database connection fails
            ↓
Alembic cannot connect
            ↓
Container startup command stops
            ↓
Uvicorn does not start
            ↓
Render cannot detect an application port
```

The important diagnostic point is that the Render port message was a downstream consequence of the database failure.

### Recovery

1. Confirm the Neon quota condition.
2. Resolve the database availability/data-transfer limitation.
3. Verify database connectivity.
4. Verify migration state with:

```bash
alembic current
```

5. Redeploy or restart the affected application if required.
6. Verify:

```text
/api/v1/health/live
/api/v1/health/ready
/api/v1/health
/api/v1/health/database
```

7. Run the appropriate API smoke checks after the database is available.

Do not use a database downgrade as the first response to a provider quota problem.

---

## Migration Failure

### Symptoms

* `alembic upgrade head` fails
* API container does not start
* ETL workflow stops during the migration step
* Database schema is not at the expected revision

### Checks

View the migration history without requiring a database connection:

```bash
alembic history --verbose
```

When the database is reachable, check the current revision:

```bash
alembic current
```

The normal production migration operation is:

```bash
alembic upgrade head
```

### Important distinction

Application rollback and database rollback are different operations.

Rolling the Render application back to an earlier deployment does not automatically reverse database migrations.

Do not use:

```bash
alembic downgrade
```

as a routine application rollback mechanism.

Some historical migrations in this project contain destructive operations. A downgrade can remove schema objects or data.

For production recovery involving database schema changes, follow the procedures in [`deployment.md`](deployment.md).

---

## ETL Workflow Failure

### Symptoms

* GitHub Actions ETL workflow fails
* Pipeline does not complete
* Database migration step fails
* ETL runner reports an exception
* Pipeline run is recorded as failed

### Diagnostic sequence

Check the workflow steps in order:

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
ETL execution
```

Identify the **first failed step**.

If migrations fail, investigate the database before investigating the ETL extraction code.

If configuration validation fails, check the relevant GitHub Actions secrets/configuration.

If the ETL runner fails, inspect the pipeline error and operational metrics.

---

## ETL Appears Stuck

Check the ETL status endpoint:

```text
GET /api/v1/analytics/etl/status
```

Possible states include:

```text
Running
Idle
Unknown
```

Then check the latest recorded run:

```text
GET /api/v1/analytics/etl/last-run
GET /api/v1/analytics/etl/last-run-time
```

If the status remains unexpectedly `Running`, inspect the corresponding GitHub Actions workflow and `pipeline_runs` records.

Do not start repeated manual runs until the state of the existing run is understood.

---

## ETL Database Status Is Degraded

Check:

```text
GET /api/v1/analytics/etl/db-status
```

If the status is not operational:

1. Check Neon availability.
2. Check the database connection configuration.
3. Check for provider quota restrictions.
4. Check recent Render and GitHub Actions errors.
5. Retry the ETL only after database availability is confirmed.

---

## Dashboard Cannot Load Data

### Symptoms

The Streamlit dashboard loads, but data-backed pages fail or show errors.

### Diagnostic sequence

```text
Dashboard
    ↓
Can dashboard reach API?
    ↓
Is API live?
    ↓
Is API ready?
    ↓
Is database healthy?
```

Check:

```text
/api/v1/health/live
/api/v1/health/ready
/api/v1/health/database
```

If the API is unavailable, investigate the API before changing dashboard code.

If the API is healthy but the dashboard still fails, inspect Streamlit Community Cloud logs and the configured API URL.

---

## Local Development Database Failure

### Symptoms

* Application cannot connect to PostgreSQL
* Alembic commands fail
* Integration tests fail
* Docker backend remains unhealthy

### Checks

Verify the containers:

```bash
docker compose ps
```

The local PostgreSQL service uses host port:

```text
15432
```

The backend uses:

```text
8000
```

The dashboard uses:

```text
8501
```

Check PostgreSQL logs:

```bash
docker compose logs postgres
```

Check backend logs:

```bash
docker compose logs backend
```

If PostgreSQL is unhealthy, resolve the database service before debugging the application.

---

## Docker Compose Startup Failure

Run:

```bash
docker compose ps
```

Then inspect the relevant service:

```bash
docker compose logs postgres
docker compose logs backend
docker compose logs dashboard
```

The backend depends on PostgreSQL being healthy before it starts.

The dashboard depends on the backend being healthy.

Therefore:

```text
PostgreSQL
    ↓
Backend
    ↓
Dashboard
```

A failure upstream can produce downstream service failures.

---

## Tests Fail Locally

Start by running the failing test directly.

For example:

```bash
pytest tests/unit -v
```

or:

```bash
pytest tests/integration -v
```

or:

```bash
pytest tests/e2e -v
```

For one test file:

```bash
pytest path/to/test_file.py -v
```

Read the first meaningful failure rather than only the final summary.

For integration failures, check:

* PostgreSQL is running
* Environment variables are loaded
* Database schema is current
* Required dependencies are installed

For E2E failures, check:

* Required services are available
* API is reachable
* Dashboard is reachable
* Test environment configuration is correct

See [`testing.md`](testing.md) for the complete testing strategy.

---

## CI Failure

GitHub Actions currently runs:

* Ruff
* Black
* MyPy
* Unit tests
* Integration tests
* E2E tests

When CI fails:

1. Open the failed workflow run.
2. Identify the failed job.
3. Identify the first failed step.
4. Reproduce the relevant command locally.
5. Fix the underlying issue.
6. Run the relevant local checks.
7. Push the fix only after local verification.

Do not treat a CI failure as a deployment failure automatically.

---

## Configuration Problems

### Symptoms

* Application refuses to start
* ETL configuration validation fails
* Database connection fails
* Translation functionality fails

Check the environment configuration required by the affected component.

Never commit production secrets to the repository.

For the documented configuration variables, see the configuration section of [`README.md`](../README.md) and [`development.md`](development.md).

---

## External API Problems

The current production ETL ingestion source is Adzuna.

If extraction fails:

1. Check the GitHub Actions logs.
2. Determine whether the failure is authentication, rate limiting, network connectivity, or an API response problem.
3. Verify the relevant Adzuna credentials are configured as GitHub Actions secrets.
4. Check whether the failure affects extraction only or the complete ETL run.

Do not classify an external API failure as a database failure without evidence.

---

## When to Roll Back

Rollback should be considered when there is evidence that the deployed application version itself is responsible for the failure.

Do not roll back solely because:

* the database provider is unavailable
* Neon quota has been exceeded
* an external API is unavailable
* a network dependency is temporarily unavailable

First identify the failing dependency.

Application rollback and database recovery are separate concerns.

See [`deployment.md`](deployment.md) for the documented rollback and recovery procedure.

---

## When to Roll Forward

A roll-forward may be appropriate when:

* the deployed application has a known code defect
* a configuration-safe fix is available
* a backward-compatible migration or application fix can resolve the problem

Prefer a backward-compatible application fix when possible rather than relying on destructive database downgrades.

---

## Final Verification

After resolving a production issue, verify the affected layer and its dependencies.

For the API:

```text
/api/v1/health/live
/api/v1/health/ready
/api/v1/health
/api/v1/health/database
```

For ETL:

```text
/api/v1/analytics/etl/status
/api/v1/analytics/etl/last-run
/api/v1/analytics/etl/last-run-time
/api/v1/analytics/etl/db-status
```

Then verify the dashboard and any affected workflow.

A recovery is not complete until the original failure condition has been addressed and the dependent component has been verified.

---

## Related Documentation

* [`README.md`](../README.md) — project overview and getting started
* [`development.md`](development.md) — local development
* [`testing.md`](testing.md) — testing strategy
* [`operations.md`](operations.md) — normal production operations
* [`deployment.md`](deployment.md) — deployment, rollback, and recovery
* [`architecture.md`](architecture.md) — system architecture
* [`api_contract.md`](api_contract.md) — API contract
* [`database_schema.md`](database_schema.md) — database structure
