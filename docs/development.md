# Development Guide

## Purpose

This guide explains how to set up, run, test, and work on Job Market Intelligence locally.

It is intended for a developer who is starting with the repository and needs a reliable local development workflow.

## Prerequisites

- Git
- Docker
- Docker Compose
- Python 3.13 for host-based development

## Getting the Project

Clone the repository:

```bash
git clone https://github.com/jaymwangi/job-market-intelligence.git
cd job-market-intelligence
````

Create the local environment file:

```bash
cp .env.example .env
```

Do not commit `.env` or real credentials.

## Docker Development

The recommended local workflow uses Docker Compose.

Start the complete application:

```bash
docker compose up --build
```

The local stack contains three services:

```text
PostgreSQL
    ↓
FastAPI backend
    ↓
Streamlit dashboard
```

Docker Compose waits for PostgreSQL to become healthy before starting the backend. The backend then runs pending Alembic migrations before starting FastAPI. The dashboard waits for the backend health check before starting.

### Local Services

| Service    | Address                       |
| ---------- | ----------------------------- |
| PostgreSQL | `localhost:15432`             |
| FastAPI    | `http://localhost:8000`       |
| Swagger UI | `http://localhost:8000/docs`  |
| ReDoc      | `http://localhost:8000/redoc` |
| Streamlit  | `http://localhost:8501`       |

### Useful Commands

Start the application:

```bash
docker compose up
```

Start in the background:

```bash
docker compose up -d
```

Rebuild images:

```bash
docker compose up --build
```

View service logs:

```bash
docker compose logs -f
```

View backend logs:

```bash
docker compose logs -f backend
```

View dashboard logs:

```bash
docker compose logs -f dashboard
```

Stop the services:

```bash
docker compose down
```

Stop the services and remove the local PostgreSQL volume:

```bash
docker compose down -v
```

The `-v` option deletes the local PostgreSQL data volume.

## Environment Configuration

Application configuration is loaded from environment variables.

Start with:

```bash
cp .env.example .env
```

Important local configuration includes:

* Application environment
* Database credentials
* Adzuna credentials for ETL execution
* Logging configuration
* Pipeline settings
* Dashboard/API configuration

The complete configuration template is maintained in `.env.example`.

Never place production credentials in the repository.

## Database and Migrations

The local PostgreSQL service uses PostgreSQL 16.

The backend automatically runs:

```bash
alembic upgrade head
```

during container startup.

For manual migration work from an environment where the database is reachable:

```bash
alembic upgrade head
```

Inspect the migration history:

```bash
alembic history --verbose
```

Check the current database revision:

```bash
alembic current
```

Database migrations are part of the application's startup process, so migration failures can prevent the API from starting.

## Running the ETL Pipeline

The ETL runner is:

```bash
python -m scripts.run_pipeline
```

When running the application inside Docker, execute it from the backend container using the project's configured environment:

```bash
docker compose exec backend python -m scripts.run_pipeline
```

The ETL pipeline requires the relevant database and external API configuration.

The production GitHub Actions workflow is documented separately in `docs/automation.md`.

## Testing

Pytest discovers tests under:

```text
tests/
```

The project defines these test markers:

* `unit`
* `integration`
* `e2e`

Run the complete test suite:

```bash
pytest
```

Run unit tests:

```bash
pytest tests/unit/ -v
```

Run integration tests:

```bash
pytest tests/integration/ -v
```

Run end-to-end tests:

```bash
pytest tests/e2e/ -v
```

Run a specific test file:

```bash
pytest path/to/test_file.py -v
```

## Code Quality

Run Ruff:

```bash
ruff check .
```

Check Black formatting:

```bash
black --check .
```

Run MyPy:

```bash
mypy app
```

The project uses strict MyPy configuration for the application code.

## Project Navigation

The main areas of the repository are:

```text
app/
├── api/            FastAPI routes and API infrastructure
├── database/       Database/session infrastructure
├── etl/            Extraction, transformation, enrichment, validation, loading
├── models/         SQLAlchemy models
├── repositories/   Database access
├── schemas/        API/application schemas
└── services/       Business and analytics logic

dashboard/
├── api/             Dashboard API integration
├── components/      Reusable UI components
├── pages/           Dashboard pages
├── services/        Dashboard services
└── app.py           Streamlit entry point

config/
└── settings.py      Application configuration

migrations/
└── versions/        Alembic migration history

scripts/
└── run_pipeline.py  ETL execution entry point

tests/
├── unit/
├── integration/
├── e2e/
└── fixtures/
```

## Development Workflow

For a normal change:

1. Start from an up-to-date branch.
2. Understand the affected layer before changing code.
3. Make the smallest change that solves the problem.
4. Run targeted tests first.
5. Run relevant linting/type checks.
6. Inspect the diff.
7. Run the broader test suite when appropriate.
8. Commit only the intended files.

Avoid unrelated refactoring while working on a focused change.

## Common Development Pitfalls

### Database changes

If models change, determine whether a corresponding Alembic migration is required.

Do not treat application rollback as a database rollback. Database migrations have their own lifecycle.

### Environment variables

A local `.env` may contain credentials and should remain untracked.

Use `.env.example` as the shareable configuration reference.

### Docker database state

Removing the PostgreSQL volume with:

```bash
docker compose down -v
```

deletes the local database data.

Use this deliberately when a clean local database is required.

### ETL execution

The ETL pipeline can modify the database and may consume external API resources.

Use appropriate test/local configuration when developing ETL behavior.

### Production changes

Local development and production operation are separate concerns.

For production deployment, rollback, migrations, and recovery procedures, see:

* `docs/deployment.md`
* `docs/operations.md`

For API usage, see:

* `docs/api_contract.md`

For system architecture, see:

* `docs/architecture.md`