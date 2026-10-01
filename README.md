# Job Market Intelligence

A production-oriented data engineering and analytics platform for collecting, transforming, enriching, storing, and analyzing technology job-market data.

The project combines an ETL pipeline, PostgreSQL database, analytics layer, FastAPI REST API, and Streamlit dashboard to turn job-posting data into insights about skills, salaries, companies, locations, employment types, and posting trends.

## What Is Job Market Intelligence?

Job Market Intelligence collects job-market data, processes it through a validation and enrichment pipeline, stores the resulting data in PostgreSQL, exposes analytics through a versioned REST API, and presents the results through an interactive dashboard.

The current production ingestion source is **Adzuna**.

The project is also a portfolio-scale demonstration of:

* Data engineering and ETL design
* Backend/API development
* PostgreSQL data modeling
* Analytics engineering
* Data validation and enrichment
* Automated testing
* Docker containerization
* CI/CD and production deployment
* Operational documentation and recovery procedures

## What Problem Does It Solve?

Raw job-posting data is difficult to analyze consistently because postings contain inconsistent titles, locations, salary formats, skills, employment types, and other fields.

The system provides a structured pipeline for:

1. Collecting job postings
2. Cleaning and validating incoming data
3. Enriching job records
4. Normalizing salary information
5. Extracting and organizing skills
6. Persisting structured data
7. Exposing analytical results through an API
8. Visualizing market patterns through a dashboard

This makes the data useful for exploring questions such as:

* Which skills appear most frequently?
* What salary ranges are being advertised?
* Which locations have the most postings?
* How are remote, hybrid, and onsite roles distributed?
* Which companies and job titles appear frequently?
* How does job-posting activity change over time?

## Features

### ETL Pipeline

* Adzuna job-posting extraction
* Transformation and normalization
* Validation and rejection handling
* Duplicate prevention
* Skill extraction and enrichment
* Salary normalization
* Configurable retention and cleanup
* Pipeline execution metrics and status tracking

### Analytics

The application provides analytics covering areas such as:

* Job volumes and trends
* Skills
* Salaries
* Companies
* Locations
* Employment types
* Remote-work patterns

### REST API

FastAPI provides a versioned API under:

```text
/api/v1
```

The API includes resources for jobs, skills, locations, salary analytics, remote-work analytics, trends, overview metrics, pipeline information, and health monitoring.

Interactive API documentation is available locally at:

```text
http://localhost:8000/docs
```

See [`docs/api_contract.md`](docs/api_contract.md) for the API contract.

### Interactive Dashboard

The Streamlit dashboard consumes the API and provides an interactive interface for exploring the job-market data.

### Data Quality and Operations

The system includes:

* Validation during ETL processing
* Database constraints and indexes
* Migration management with Alembic
* Structured application and ETL logging
* Pipeline-run tracking
* Health and readiness endpoints
* Automated test coverage
* Production deployment and recovery documentation

---

## Technology Stack

| Area                 | Technology                |
| -------------------- | ------------------------- |
| Language             | Python 3.13               |
| API                  | FastAPI, Uvicorn          |
| Database             | PostgreSQL                |
| ORM                  | SQLAlchemy                |
| Migrations           | Alembic                   |
| Validation           | Pydantic                  |
| Data processing      | Pandas                    |
| Dashboard            | Streamlit                 |
| Testing              | Pytest                    |
| Formatting           | Black                     |
| Linting              | Ruff                      |
| Type checking        | MyPy                      |
| Containers           | Docker, Docker Compose    |
| CI/CD                | GitHub Actions            |
| Production API       | Render                    |
| Production database  | Neon PostgreSQL           |
| Production dashboard | Streamlit Community Cloud |
| Job data source      | Adzuna                    |
| Translation          | DeepL                     |

---

## Architecture

### Application Architecture

```text
                    Adzuna
                      │
                      ▼
                ┌───────────┐
                │    ETL    │
                │ Extract   │
                │ Transform │
                │ Enrich    │
                │ Validate  │
                │ Load      │
                └─────┬─────┘
                      │
                      ▼
              ┌───────────────┐
              │  PostgreSQL   │
              └───────┬───────┘
                      │
                      ▼
                ┌───────────┐
                │  FastAPI  │
                │  REST API │
                └─────┬─────┘
                      │
                      ▼
                ┌───────────┐
                │ Streamlit │
                │ Dashboard │
                └───────────┘
```

### Production Deployment Architecture

```text
                         GitHub
                       /   |   \
                      /    |    \
                     ▼     ▼     ▼
              GitHub     Render   Streamlit
              Actions      │      Community
                │          │        Cloud
                │          │
             CI / ETL    FastAPI
                          │
                          ▼
                         Neon
                      PostgreSQL
```

GitHub Actions handles CI and the ETL workflow.

A push to the main branch can trigger the Render API deployment through Render's configured auto-deployment.

The production API runs on Render and connects to PostgreSQL on Neon.

The Streamlit dashboard is deployed separately through Streamlit Community Cloud.

### Production Data Flow

```text
Adzuna
   ↓
Extraction
   ↓
Transformation
   ↓
Enrichment
   ↓
Validation
   ↓
PostgreSQL / Neon
   ↓
FastAPI / Render
   ↓
Streamlit Community Cloud
```

For the detailed architecture and design decisions, see [`docs/architecture.md`](docs/architecture.md).

---

## Project Structure

```text
job-market-analytics-api/
├── app/
│   ├── api/              # FastAPI routes
│   ├── etl/              # Extraction, transformation, enrichment and loading
│   ├── models/            # SQLAlchemy models
│   ├── repositories/      # Data-access layer
│   └── services/          # Application/business services
│
├── config/                # Application configuration
├── dashboard/             # Streamlit dashboard
├── migrations/            # Alembic migrations
├── scripts/               # Operational and ETL scripts
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                  # Project documentation
├── compose.yml            # Local multi-service environment
├── Dockerfile             # API container
├── render.yaml            # Render deployment configuration
├── requirements.txt       # Python dependencies
└── pyproject.toml         # Python/tool configuration
```

---

## Getting Started

### Prerequisites

Install:

* Git
* Docker Desktop with Docker Compose
* Python 3.13 if running tools directly on the host

### Clone the Repository

```bash
git clone https://github.com/jaymwangi/job-market-intelligence.git
cd job-market-intelligence
```

### Create Local Configuration

Create a `.env` file containing the configuration required by the local environment.

Do not commit secrets or production credentials.

The exact configuration and environment variables are documented in [`docs/development.md`](docs/development.md).

### Start the Local Application

The recommended local workflow uses Docker Compose:

```bash
docker compose up --build
```

The local services are:

| Service    | Address                       |
| ---------- | ----------------------------- |
| PostgreSQL | `localhost:15432`             |
| FastAPI    | `http://localhost:8000`       |
| Swagger UI | `http://localhost:8000/docs`  |
| ReDoc      | `http://localhost:8000/redoc` |
| Streamlit  | `http://localhost:8501`       |

The API container applies Alembic migrations before starting Uvicorn.

For the complete development workflow, see [`docs/development.md`](docs/development.md).

---

## Configuration

Configuration is supplied through environment variables.

Important configuration areas include:

### Application

```text
ENVIRONMENT
DEBUG
SECRET_KEY
LOG_LEVEL
LOG_FORMAT
```

### Database

```text
DATABASE_URL
```

### Adzuna

```text
ADZUNA_APP_ID
ADZUNA_APP_KEY
```

### Translation

```text
TRANSLATION_PROVIDER
DEEPL_API_KEY
```

### ETL

```text
ETL_TIMEOUT_MINUTES
PIPELINE_RETENTION_DAYS
```

Actual variable names and validation rules should be treated as defined by the application's configuration module.

Never place real credentials in source control.

---

## API

The API is versioned under:

```text
/api/v1
```

Key areas include:

* Health and readiness
* Jobs
* Skills
* Locations
* Salary analytics
* Remote-work analytics
* Job trends
* Overview analytics
* Pipeline status and runs

### Health Endpoints

```text
GET /api/v1/health/live
GET /api/v1/health/ready
GET /api/v1/health
GET /api/v1/health/database
```

Their purposes differ:

* `health/live` checks that the API process is alive.
* `health/ready` verifies database readiness.
* `health` provides broader API/database health information.
* `health/database` checks database connectivity and response information.

See [`docs/api_contract.md`](docs/api_contract.md) for the detailed API contract.

---

## Testing

The project uses multiple testing layers:

```text
Unit Tests
    ↓
Integration Tests
    ↓
E2E Tests
    ↓
Production Smoke Tests
```

### Unit Tests

Test individual functions, services, repositories, ETL components, and dashboard components in isolation.

```bash
pytest tests/unit/ -v
```

### Integration Tests

Test interactions between application components and infrastructure such as the database and API.

```bash
pytest tests/integration/ -v
```

### E2E Tests

Test complete application workflows across multiple components.

```bash
pytest tests/e2e/ -v
```

### Full Test Suite

```bash
pytest
```

The test suite includes coverage configuration and strict pytest markers.

Production smoke testing is a separate verification layer. It has been postponed while the production Neon data-transfer quota issue is being resolved.

Detailed testing guidance belongs in [`docs/testing.md`](docs/testing.md).

---

## ETL Automation

The ETL pipeline can be executed manually through GitHub Actions using the `workflow_dispatch` trigger.

The scheduled daily trigger is currently **suspended pending remediation of the Neon data-transfer limitation**.

This means:

```text
Manual workflow_dispatch → available
Scheduled execution      → suspended
```

The workflow:

1. Checks out the repository
2. Sets up Python
3. Installs dependencies
4. Runs database migrations
5. Validates production configuration
6. Executes the ETL pipeline

The workflow also uses concurrency protection to prevent overlapping ETL runs.

See [`docs/deployment.md`](docs/deployment.md) and the operational documentation for current production procedures.

---

## Production Deployment

### API

The FastAPI service is deployed to Render using the project's Dockerfile and `render.yaml`.

The container:

1. Installs dependencies
2. Copies the application
3. Runs as a non-root user
4. Applies Alembic migrations
5. Starts Uvicorn

Render uses:

```text
/api/v1/health/live
```

as the liveness endpoint.

### Database

Production PostgreSQL is hosted on Neon.

Database migrations are managed with Alembic.

Normal migration operation is:

```bash
alembic upgrade head
```

### Dashboard

The Streamlit dashboard is deployed separately through Streamlit Community Cloud.

### ETL

ETL execution is managed through GitHub Actions.

The scheduled trigger is currently suspended pending Neon data-transfer remediation; manual execution remains available.

For deployment, rollback, recovery, and production verification procedures, see [`docs/deployment.md`](docs/deployment.md).

---

## Database Migrations

Alembic manages the database schema.

Useful commands:

```bash
alembic history --verbose
alembic current
alembic upgrade head
```

`alembic current` requires a reachable database.

`alembic history --verbose` can be used to inspect the migration chain without connecting to the database.

Database downgrades are not treated as a routine production rollback mechanism because older revisions may remove schema or data. Application rollback and database rollback are separate concerns.

See [`docs/development.md`](docs/development.md) and [`docs/deployment.md`](docs/deployment.md) for the detailed procedures.

---

## Troubleshooting

| Symptom                     | First check                                                         |
| --------------------------- | ------------------------------------------------------------------- |
| API does not start          | Container logs, database connectivity, and migrations               |
| Dashboard cannot reach API  | API URL and API health endpoint                                     |
| Database connection failure | `DATABASE_URL`, database availability, and provider status          |
| Migration failure           | Migration logs and current Alembic revision                         |
| ETL failure                 | GitHub Actions logs and pipeline-run information                    |
| Render reports no open port | Check whether startup failed before Uvicorn bound to `$PORT`        |
| Neon data-transfer error    | Check the Neon project quota before attempting application rollback |

One documented production failure involved Neon rejecting database connections after the project's data-transfer quota was exceeded. The resulting absence of an open API port was a downstream effect of the migration/startup failure.

For detailed diagnosis and recovery procedures, see [`docs/troubleshooting.md`](docs/troubleshooting.md) and [`docs/deployment.md`](docs/deployment.md).

---

## Documentation

| Document                                             | Purpose                                    |
| ---------------------------------------------------- | ------------------------------------------ |
| [`docs/architecture.md`](docs/architecture.md)       | System architecture and design             |
| [`docs/api_contract.md`](docs/api_contract.md)       | API usage and contract                     |
| [`docs/database_schema.md`](docs/database_schema.md) | Database structure                         |
| [`docs/development.md`](docs/development.md)         | Local development workflow                 |
| [`docs/deployment.md`](docs/deployment.md)           | Deployment, rollback and recovery          |
| [`docs/testing.md`](docs/testing.md)                 | Testing strategy and execution             |
| [`docs/operations.md`](docs/operations.md)           | Production operations and monitoring       |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Diagnosis and recovery of common failures  |
| [`docs/requirements.md`](docs/requirements.md)       | Functional and non-functional requirements |
| [`docs/roadmap.md`](docs/roadmap.md)                 | Development roadmap and history            |
| [`docs/sprint_plan.md`](docs/sprint_plan.md)         | Original sprint planning                   |
| [`docs/Project About.md`](docs/Project%20About.md)   | Project and portfolio narrative            |

---

## Roadmap

The project is in the **6.8.x hardening and documentation phase**.

Current work includes:

* Deployment and recovery documentation
* Developer experience improvements
* Testing documentation
* Operations documentation
* Troubleshooting documentation
* Architecture documentation cleanup
* Final documentation consistency checks

See [`docs/roadmap.md`](docs/roadmap.md) for the detailed development history.

---

## License

This project is licensed under the MIT License.

## Contact

**GitHub:** [jaymwangi](https://github.com/jaymwangi)

**Project:** [job-market-intelligence](https://github.com/jaymwangi/job-market-intelligence)
