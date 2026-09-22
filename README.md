# Job Market Intelligence

A production-oriented data engineering and analytics platform that collects, transforms, stores, and analyzes technology job market data from external sources. The system provides insights into skill demand, salary trends, hiring patterns, and workforce dynamics through a layered architecture consisting of an ETL pipeline, analytics engine, REST API, and interactive analytics dashboard.

The project demonstrates production-ready software engineering practices, including clean architecture, layered design, repository and service patterns, data validation, analytics, scalable backend development, and modern frontend integration, all orchestrated in a containerized environment.

---

## Why This Project

Many portfolio projects stop after collecting data.

This project simulates a real-world data platform by implementing:

- Modular ETL pipeline
- Layered architecture
- Repository and Service patterns
- Analytics engine
- Production-ready REST API
- Interactive analytics dashboard
- API-driven frontend architecture
- Docker containerization
- CI/CD pipeline
- Deployment-ready project structure
- Automated ETL scheduling
- Production monitoring and observability

The goal is to demonstrate backend engineering, data engineering, analytics engineering, API development, frontend integration, and DevOps practices within a single cohesive application.

---

## Features

### ETL Pipeline

- Extract job postings from external job APIs (currently Adzuna)
- Transform external job data into a standardized internal format
- Validate incoming data using Pydantic models
- **Upsert** — Insert new jobs, update existing jobs by `source_id`
- Prevent duplicate job records during ingestion
- **90-day retention policy** — Automatic cleanup of jobs older than 90 days (based on `scraped_date`)
- Track ETL pipeline executions with detailed metrics
- **Automated daily execution** via GitHub Actions at 6:00 AM UTC

### Enrichment Layer

- **Language Detection** — Detect job posting language (ISO 639-1)
- **Skill Extraction** — Extract technical skills from job titles and descriptions
- **Technology Classification** — Classify jobs into 18 technology categories with confidence scoring
- **Geographic Enrichment** — Normalize country codes to ISO format
- **Currency Normalization** — Normalize currencies and convert to USD
- **Batch Processing** — Efficient skill persistence with duplicate handling

### Analytics Engine

- Analyze skill demand
- Analyze salary trends
- Analyze hiring companies
- Analyze job locations
- Analyze employment types
- Analyze posting trends
- Aggregate dashboard metrics
- Dataset summaries with unique counts
- Top skills, companies, and locations

### REST API

- Expose job data through FastAPI
- Expose analytics through REST endpoints
- Filtering, pagination, and search
- Health endpoints (`/live`, `/ready`, `/health`)
- Database health endpoint
- OpenAPI documentation (Swagger & ReDoc)
- Request validation
- Structured error handling
- Request correlation IDs
- Production logging

### Interactive Dashboard

- Interactive Streamlit dashboard
- API-driven frontend (no direct database access)
- Job explorer with search and filtering
- Interactive Plotly visualizations
- KPI dashboard with unique counts
- Dashboard caching
- Professional SVG icon system
- Loading states and empty-state components
- Friendly error handling
- Modular reusable UI components

### DevOps & Containerization

- Docker containerization for all services
- Docker Compose orchestration
- GitHub Actions CI/CD pipeline
- Automated linting, type checking, and testing
- Environment variable management
- Persistent database volumes
- Container health checks
- Non-root container users for security
- Automated database migrations on startup

### Production Automation

- **Automated ETL Pipeline** — Runs daily without manual intervention
- **Idempotent Processing** — Safe to run multiple times without duplicates
- **Data Lifecycle Management** — Automatic cleanup of old jobs
- **Operational Visibility** — Pipeline runs tracked with metrics
- **Concurrency Protection** — Prevents overlapping pipeline runs
- **Structured Logging** — JSON logs with request correlation
- **Health Monitoring** — Liveness, readiness, and detailed health checks

---

## Tech Stack

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2

### Database

- PostgreSQL 16

### Data Processing

- Pandas

### Dashboard

- Streamlit
- Plotly

### Development & DevOps

- Git
- GitHub
- Docker
- Docker Compose
- GitHub Actions
- Ruff
- Black
- MyPy
- Pytest
- Code Coverage

---

## Architecture

```text
                    GitHub Actions
                  (Daily at 6:00 AM UTC)
                           │
                           ▼
                    External Job APIs
                           │
                           ▼
                     HTTP Client Layer
                           │
                           ▼
                        Extractor
                           │
                           ▼
                      Transformer
                           │
                           ▼
                     Enrichment Layer
                ┌─────────┼─────────┐
                │         │         │
          Language    Skills    Tech
          Detection Extraction Classification
                │         │         │
                └─────────┼─────────┘
                           ▼
                  Validator (Pydantic)
                           │
                           ▼
             Loader (Upsert + Purge)
                           │
                           ▼
                  Repository Layer
                           │
                           ▼
                      PostgreSQL
                           ▲
                           │
                 Analytics Repository
                           ▲
                           │
                     Service Layer
                           ▲
                           │
                 FastAPI REST API
                           ▲
                           │
                    API Client Layer
                           ▲
                           │
                  Dashboard Services
                           ▲
                           │
                  Streamlit Dashboard
                           ▲
                           │
                           User
```

---

## Project Structure

```text
job-market-intelligence/
│
├── .github/
│   ├── workflows/
│   │   ├── quality.yml        # CI/CD pipeline
│   │   └── etl-pipeline.yml   # Daily ETL automation
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   ├── dependencies.py
│   │   ├── exception_handlers.py
│   │   └── router.py
│   │
│   ├── core/
│   │   ├── logging.py
│   │   └── settings.py
│   │
│   ├── database/
│   ├── etl/
│   │   ├── clients/
│   │   ├── enrichment/
│   │   │   ├── data/
│   │   │   │   ├── country_map.py
│   │   │   │   ├── currency_map.py
│   │   │   │   ├── skills.py
│   │   │   │   └── technology_categories.py
│   │   │   ├── country_normalizer.py
│   │   │   ├── currency_normalizer.py
│   │   │   ├── enricher.py
│   │   │   ├── skill_extractor.py
│   │   │   └── technology_classifier.py
│   │   ├── extractors/
│   │   ├── loaders/
│   │   ├── schemas/
│   │   │   ├── enriched.py
│   │   │   ├── metrics.py
│   │   │   ├── transformed.py
│   │   │   └── validated.py
│   │   ├── transformers/
│   │   └── validators/
│   │
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── dashboard/
│   ├── api/
│   ├── components/
│   ├── core/
│   ├── pages/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── app.py
│
├── docs/
│   ├── automation.md
│   ├── deployment_checklist.md
│   ├── operations.md
│   └── roadmap.md
│
├── migrations/
├── scripts/
│   ├── run_pipeline.py
│   └── sample_jobs.py
├── tests/
│   ├── smoke/
│   │   └── test_production.py
│   ├── integration/
│   │   ├── test_database.py
│   │   ├── test_repository_service.py
│   │   ├── test_etl_pipeline.py
│   │   ├── test_analytics_pipeline.py
│   │   ├── test_api.py
│   │   └── test_dashboard_api.py
│   └── unit/
│
├── Dockerfile
├── compose.yml
├── render.yaml
├── .dockerignore
├── .env.example
├── Makefile
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Roadmap

This project follows a sprint-based development roadmap, progressing from database foundation through ETL, analytics, API, dashboard, integration testing, and finally production hardening.

**Current status:** Sprint 6.7.1 – 6.7.8 complete — PostgreSQL-backed integration and end-to-end test infrastructure established (74 tests passing).

**Next up:**
- ⏸️ Sprint 6.7.9 – 6.7.11 (Production Smoke Testing, ETL Automation Verification, Regression & Final Validation) — postponed until the Neon free-tier storage refreshes next month.
- 🚧 Sprint 6.8 — Production Hardening & Documentation — **the final sprint**, producing the `v1.0.0` release candidate.

After `v1.0.0`, the project leaves the planned development roadmap. New work is driven by real defects, operational observations, and user feedback — not by extending the sprint plan.

📖 **[View the full roadmap →](docs/roadmap.md)**

---

## Docker Development

### Quick Start

Clone the repository:

```bash
git clone https://github.com/jaymwangi/job-market-intelligence.git
cd job-market-intelligence
```

Create environment configuration:

```bash
cp .env.example .env
```

Start the application:

```bash
docker compose up --build
```

### Startup Flow

```text
docker compose up
│
▼
PostgreSQL container starts
│
▼
Database health check passes
│
▼
Alembic migrations execute
│
▼
FastAPI backend starts
│
▼
Backend health check passes
│
▼
Streamlit dashboard starts
```

### Application Access

| Service | URL |
|---------|-----|
| FastAPI API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Streamlit Dashboard | http://localhost:8501 |
| PostgreSQL | localhost:5432 |

### Useful Commands

**Start application:**
```bash
docker compose up
```

**Run in background:**
```bash
docker compose up -d
```

**View logs:**
```bash
docker compose logs -f
```

**Stop containers:**
```bash
docker compose down
```

**Remove database volume:**
```bash
docker compose down -v
```

**Run migrations:**
```bash
docker compose exec backend alembic upgrade head
```

**Run tests:**
```bash
docker compose exec backend pytest
```

**Run linting checks:**
```bash
docker compose exec backend ruff check .
```

**Run type checking:**
```bash
docker compose exec backend mypy app
```

**Run ETL pipeline manually:**
```bash
docker compose exec backend python scripts/run_pipeline.py
```

---

## Testing

The project includes testing for:

- ETL pipeline
- Repository layer
- Service layer
- Analytics engine
- FastAPI REST API
- Dashboard services
- Dashboard utilities
- Dashboard caching
- API integration
- End-to-end ETL workflow
- Production smoke tests
- Sprint regression verification
- **Integration tests** (PostgreSQL-backed)
  - Database connectivity and schema
  - Repository and service operations
  - ETL pipeline processing
  - Analytics engine queries
  - API endpoint validation
  - Dashboard API client integration

**Example verification:**
```bash
python scripts/verify_sprint5.py
```

**Smoke Tests:**
```bash
pytest tests/smoke/ -v -m smoke
```

**Integration Tests:**
```bash
pytest tests/integration/ -v
```

**Run specific integration test:**
```bash
pytest tests/integration/test_dashboard_api.py -v
```

**Continuous Integration:**
Testing is automatically validated through GitHub Actions. The CI pipeline executes:

- Ruff linting
- Black formatting checks
- MyPy type checking
- Unit tests
- PostgreSQL integration tests (74+ tests)
- Docker image builds

---

## Production Deployment

### Render Deployment

The application can be deployed to Render using the provided `render.yaml`:

```yaml
services:
  - type: web
    name: job-market-intelligence-api
    runtime: docker
    plan: free
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: job-market-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: ENVIRONMENT
        value: production
```

### GitHub Actions Automation

The ETL pipeline runs automatically every day:

```text
GitHub Actions (6:00 AM UTC)
        │
        ▼
Checkout Code
        │
        ▼
Install Dependencies
        │
        ▼
Run Migrations
        │
        ▼
Execute ETL Pipeline
        │
        ▼
Update Database
        │
        ▼
Record Pipeline Run
```

---

## License

This project is licensed under the MIT License.

---

## Contact

**Author:** Jay Mwangi

**GitHub:** [jaymwangi](https://github.com/jaymwangi)

**Project:** [job-market-intelligence](https://github.com/jaymwangi/job-market-intelligence)
```

