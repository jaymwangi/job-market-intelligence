# Deployment, Rollback & Recovery

## 1. Deployment Overview

The production system is deployed across three primary services:

```text
GitHub
   |
   +--> GitHub Actions
   |      - Quality checks
   |      - Integration tests
   |      - E2E tests
   |      - Docker image validation
   |
   +--> Render
   |      - FastAPI backend
   |      - Docker runtime
   |      - Neon PostgreSQL connection
   |
   +--> Streamlit Community Cloud
          - Streamlit dashboard
          - Connects to the deployed API
```

The API is deployed to Render from the `main` branch using automatic deployment. The Render service uses the repository `Dockerfile` and the production configuration defined in `render.yaml`.

The API container runs `alembic upgrade head` before starting Uvicorn.

The production database is PostgreSQL hosted by Neon. The Streamlit dashboard is deployed separately through Streamlit Community Cloud.

The daily ETL workflow is defined in GitHub Actions. Its scheduled cron trigger is currently suspended pending Neon data-transfer remediation. ETL can still be triggered manually through `workflow_dispatch`.

## 2. Deployment Procedure

### 2.1 Build and Validate

Before deployment, changes should pass the repository's automated validation:

1. GitHub Actions runs the quality workflow.
2. Dependencies are installed using the pinned project requirements.
3. Ruff, Black, and MyPy checks are run.
4. Alembic migrations are applied against the CI PostgreSQL service.
5. Unit and integration tests are executed.
6. Docker Compose configuration is validated.
7. Backend and dashboard Docker images are built successfully.

The deployment should proceed only after the required CI checks pass.

### 2.2 Deploy the API

The API deployment flow is:

```text
Push to main
    ↓
GitHub Actions validation
    ↓
Render automatic deployment
    ↓
Docker image build
    ↓
Container startup
    ↓
alembic upgrade head
    ↓
Uvicorn starts on $PORT
    ↓
Render health check
    ↓
Deployment becomes live
```

Render uses the health check path:

```text
/api/v1/health/live
```

This endpoint verifies that the API process is alive. It does not verify database connectivity.

### 2.3 Deploy the Dashboard

The dashboard is deployed separately through Streamlit Community Cloud.

After deployment, verify that the dashboard loads successfully and can communicate with the deployed API.

### 2.4 Deployment Failure

If an API deployment fails:

1. Inspect the Render deployment logs.
2. Identify whether the failure occurred during image build, migration, application startup, or health checking.
3. Check external dependencies such as the Neon database when connection errors are reported.
4. Do not assume that a failure to open the application port means the port configuration is the root cause. For example, if `alembic upgrade head` fails before Uvicorn starts, no application port will be available.
5. If the previous deployment remains healthy and the new release is confirmed to be the cause, use the rollback procedure in Section 5.


## 3. Production Verification

### 3.1 API Health

After deployment, verify the Render health check:

```text
/api/v1/health/live
```

A successful response confirms that the API process is running and accepting requests.

Then verify the application health endpoint:

```text
/api/v1/health
```

This endpoint checks database connectivity and reports database response information.

If database-specific verification is required, use:

```text
/api/v1/health/database
```

### 3.2 Database and Migrations

When database connectivity is available, verify the deployed migration revision:

```bash
alembic current
```

The reported revision should correspond to the expected migration head.

The migration chain can also be inspected without a database connection:

```bash
alembic history --verbose
```

The current migration head is:

```text
74b5dc797be3
```

### 3.3 Dashboard

Open the deployed Streamlit dashboard and verify that:

1. The dashboard loads successfully.
2. API-backed data can be retrieved.
3. No API connection errors are displayed.
4. Key dashboard functionality responds normally.

### 3.4 ETL

The ETL workflow is currently manually triggered through GitHub Actions because its scheduled cron trigger is suspended pending Neon data-transfer remediation.

When an ETL run is performed, verify:

1. The workflow completes successfully.
2. No database connection errors occur.
3. The pipeline reports the expected processing metrics.
4. The `pipeline_runs` record is marked with the appropriate final status.

### 3.5 External Integrations

When relevant functionality depends on external services, verify the configured integrations and inspect application or workflow logs for failures.

The production configuration currently uses DeepL for translation. ETL acquisition uses the configured external job-data provider.

A successful API health check alone does not prove that external integrations or ETL are functioning correctly.


## 4. Database Migration Procedure

### 4.1 Apply Migrations

Production migrations are applied automatically when the API container starts:

```text
alembic upgrade head
```

The Docker container runs this command before starting Uvicorn.

To apply migrations manually when appropriate:

```bash
alembic upgrade head
```

### 4.2 Verify the Migration

When the production database is reachable, verify the current revision:

```bash
alembic current
```

The expected migration head is:

```text
74b5dc797be3
```

The migration history can be inspected without connecting to the database:

```bash
alembic history --verbose
```

### 4.3 Migration Failure

If `alembic upgrade head` fails:

1. Inspect the migration error in the deployment logs.
2. Determine whether the failure is caused by database connectivity, configuration, or the migration itself.
3. Do not blindly run a downgrade.
4. Determine whether the migration made any partial schema changes before failing.
5. If recovery requires a destructive schema change, establish an appropriate database backup or recovery point before proceeding.
6. Verify the database state with `alembic current` once connectivity is restored.

A migration failure during container startup prevents Uvicorn from starting. Consequently, the deployment may fail its health check or report that no application port is available.

### 4.4 Migration Rollback Limitations

Although the migration files define `downgrade()` operations, database downgrades are not a routine application rollback mechanism.

Some downgrades can cause data loss. For example:

* `74b5dc797be3` removes the `tech_confidence` and `matched_tech_terms` columns.
* `3182e514fa7d` removes the `language` column and changes parts of the schema back to an earlier structure.
* `7ca651aafbc6` drops `job_skills`, `pipeline_runs`, `skills`, and `jobs`, resulting in loss of the application's stored job, skill, and pipeline-run data.

Therefore, do not use:

```bash
alembic downgrade
```

as an automatic response to a bad application deployment.

Before performing a destructive downgrade, establish an appropriate backup or recovery point and verify that the downgrade is actually required.

Application rollback and database migration rollback are separate operations. Rolling back an application deployment does not automatically undo database migrations.


## 5. Rollback Procedure

### 5.1 When to Roll Back

Consider an application rollback when a newly deployed release is confirmed to cause a production problem and the previous deployment is known to be usable.

Typical triggers include:

- API startup or runtime failures caused by the new application release.
- Regression in a critical API endpoint.
- Dashboard/API incompatibility introduced by the release.
- A deployment that passes CI but fails production verification.

First inspect the deployment logs and determine whether the problem is actually caused by the application release.

### 5.2 Application Rollback

For the Render API service:

1. Open the Render service dashboard.
2. Open the deployment history.
3. Identify the previous successful deployment.
4. Use Render's rollback action to restore that deployment.
5. Wait for the rollback deployment to complete.
6. Verify the Render health check:
   `/api/v1/health/live`
7. Verify application health:
   `/api/v1/health`
8. Run the relevant smoke tests.
9. Verify the dashboard if the API change affected dashboard functionality.

A Render application rollback restores the deployed application version. It does not automatically reverse database migrations.

### 5.3 Database Changes During Rollback

Before rolling back an application release, determine whether the release introduced database migrations.

If the release changed the database schema:

- Do not automatically downgrade the migration.
- Determine whether the previous application version is compatible with the current database schema.
- Prefer a backward-compatible application fix or roll-forward when possible.
- If a database downgrade is genuinely required, follow the migration rollback limitations in Section 4.4 and establish an appropriate recovery point first.

### 5.4 Roll-Forward

A roll-forward may be preferable when the database schema has already been changed and the previous application version is not compatible with the new schema.

The process is:

```text
Detect problem
     ↓
Identify cause
     ↓
Determine database compatibility
     ↓
Fix application/configuration
     ↓
Deploy corrected release
     ↓
Health check
     ↓
Smoke test
```

## 6. Recovery Procedures
### API Failure

If the API is unavailable:

1. Check the Render deployment status.
2. Inspect the latest deployment and application logs.
3. Verify `/api/v1/health/live`.
4. Verify `/api/v1/health` to distinguish process failure from database connectivity failure.
5. If the failure was introduced by a release, follow the rollback procedure in Section 5.
6. If the failure is caused by an external dependency, resolve that dependency before attempting an application rollback.
7. Re-run the relevant smoke tests after recovery.

### Database Unavailable

If the API cannot connect to PostgreSQL:

1. Check the API logs for database connection errors.
2. Verify that `DATABASE_URL` is correctly configured.
3. Check the availability and status of the Neon database.
4. If Neon reports a quota or data-transfer limit, resolve the database availability issue before attempting application rollback.
5. Once connectivity is restored, verify the migration revision with:
   `alembic current`
6. Verify `/api/v1/health`.
7. Run the relevant smoke tests.

A database connectivity failure can prevent the API container from starting because the container runs `alembic upgrade head` before starting Uvicorn.

A recent example was a deployment failure caused by Neon reporting that the project had exceeded its data-transfer quota. The resulting failure to start Uvicorn caused Render to report that no application port was detected. In this situation, the port message was a downstream symptom of the database failure.

### ETL Failure

If an ETL run fails:

1. Open the GitHub Actions workflow run.
2. Identify the failing stage from the workflow logs.
3. Check for database, external API, configuration, timeout, or data-validation errors.
4. Inspect the corresponding `pipeline_runs` record when database access is available.
5. Correct the underlying cause.
6. Re-run the ETL workflow manually through `workflow_dispatch`.
7. Verify the final pipeline status and processing metrics.

The ETL workflow uses concurrency control to prevent overlapping runs.

The scheduled ETL cron trigger is currently suspended pending Neon data-transfer remediation. Manual execution remains available.

### Deployment Failure

If a deployment fails:

1. Inspect the Render deployment logs.
2. Identify whether the failure occurred during image build, migration, application startup, or health checking.
3. Check external dependencies when the logs show connection failures.
4. If the previous deployment remains healthy, keep it serving while the failure is investigated.
5. Roll back only when the new application release is confirmed to be the cause.
6. If the failure is caused by infrastructure or an external dependency, resolve that dependency instead.
7. After recovery, perform the production verification procedure.

Do not treat every failed deployment as an application-code problem.

### External API Failure

If an external API used by the application or ETL fails:

1. Inspect the relevant application or GitHub Actions logs.
2. Identify the external service and failure type.
3. Check configuration such as API credentials and provider settings.
4. Determine whether the failure is temporary, quota-related, authentication-related, or caused by the provider.
5. Resolve the external service issue or configuration problem.
6. Re-run the affected workflow or operation.
7. Verify the resulting application or ETL behavior.

An external API failure should not automatically trigger an application rollback unless evidence shows that the deployed application release caused the failure.

## 7. Operational Limitations

### 7.1 ETL Scheduling

The scheduled ETL cron trigger is currently suspended because of the Neon data-transfer/egress limitation.

ETL remains available through manual `workflow_dispatch` execution.

### 7.2 Database Rollback

Application rollback and database rollback are separate operations.

Alembic downgrade operations exist, but some are destructive and can result in data loss. Database downgrades therefore require deliberate assessment and an appropriate recovery point.

### 7.3 Deployment Logs

Render deployment logs are subject to the platform's log-retention limits. Historical logs may no longer be available after the retention period.

When investigating a production incident, capture relevant deployment and application log evidence while it is available.

### 7.4 Health Check Scope

The Render health check uses:

```text
/api/v1/health/live
```

This endpoint verifies that the API process is alive. It does not verify database connectivity, ETL execution, or external API availability.

Production verification must therefore include additional checks when those dependencies are relevant.

### 7.5 Application Rollback Scope

Rolling back the API deployment does not automatically roll back database migrations or restore database data.

Database recovery must be handled separately according to the migration and backup/recovery procedures.

### 7.6 Dashboard Deployment

The production dashboard is deployed separately through Streamlit Community Cloud. Rolling back the Render API deployment does not automatically roll back the dashboard deployment.

API and dashboard compatibility should therefore be included in production verification after relevant releases.