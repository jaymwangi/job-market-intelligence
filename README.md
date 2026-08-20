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
- **Upsert** - Insert new jobs, update existing jobs by `source_id`
- Prevent duplicate job records during ingestion
- **90-day retention policy** - Automatic cleanup of jobs older than 90 days (based on `scraped_date`)
- Track ETL pipeline executions with detailed metrics
- **Automated daily execution** via GitHub Actions at 6:00 AM UTC

### Enrichment Layer (Sprint 6.6)

- **Language Detection** - Detect job posting language (ISO 639-1)
- **Skill Extraction** - Extract technical skills from job titles and descriptions
- **Technology Classification** - Classify jobs into 18 technology categories with confidence scoring
- **Geographic Enrichment** - Normalize country codes to ISO format
- **Currency Normalization** - Normalize currencies and convert to USD
- **Batch Processing** - Efficient skill persistence with duplicate handling

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

- **Automated ETL Pipeline** - Runs daily without manual intervention
- **Idempotent Processing** - Safe to run multiple times without duplicates
- **Data Lifecycle Management** - Automatic cleanup of old jobs
- **Operational Visibility** - Pipeline runs tracked with metrics
- **Concurrency Protection** - Prevents overlapping pipeline runs
- **Structured Logging** - JSON logs with request correlation
- **Health Monitoring** - Liveness, readiness, and detailed health checks

---

## Tech Stack

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2

### Database

- PostgreSQL

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
│   └── operations.md
│
├── migrations/
├── scripts/
│   ├── run_pipeline.py
│   └── sample_jobs.py
├── tests/
│   └── smoke/
│       └── test_production.py
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

## Current Progress

### ✅ Sprint 0 — Planning & Design

- Requirements gathering
- System architecture
- Database design
- API contract
- Development roadmap

### ✅ Sprint 1 — Database Foundation

- Project initialization
- Configuration management
- PostgreSQL setup
- SQLAlchemy ORM models
- Database session management
- Alembic migrations
- Repository layer
- Database testing

### ✅ Sprint 2 — ETL Pipeline

#### Sprint 2.1 — Extraction
- HTTP client
- Adzuna API integration
- Job extractor
- Extraction testing

#### Sprint 2.2 — Transformation
- Standardized internal job schema
- Transformation layer
- Transformation testing

#### Sprint 2.3 — Validation
- Pydantic validation
- Business rule validation
- Data quality checks
- Validation testing

#### Sprint 2.4 — Loading
- Repository-based persistence
- Duplicate detection
- Transaction management
- Pipeline execution tracking
- End-to-end ETL testing

### ✅ Sprint 3 — Analytics Engine

#### Sprint 3.1 — Analytics Foundation
- Top skills
- Top companies
- Jobs by location
- Salary statistics
- Employment type distribution

#### Sprint 3.2 — Advanced Analytics
- Salary by company
- Salary by location
- Salary distribution
- Posting trends
- Recent jobs
- Advanced aggregation queries

#### Sprint 3.3 — Analytics Refinement
- Analytics Service layer
- Dashboard summary orchestration
- Repository improvements
- Query optimization
- Dataset quality reporting
- Analytics integration testing

### ✅ Sprint 4 — FastAPI REST API

#### Sprint 4.1 — FastAPI Foundation
- FastAPI application setup
- Centralized routing
- API versioning
- Health endpoint
- Database health endpoint
- Dependency injection
- Global exception handling
- Structured logging
- CORS middleware
- OpenAPI documentation

#### Sprint 4.2 — Jobs API
- Job REST endpoints
- Pagination
- Filtering
- Search
- UUID support
- Response schemas
- Repository and Service integration

#### Sprint 4.3 — Analytics API
- Analytics REST endpoints
- Dashboard summary endpoint
- Overview endpoint
- Analytics response schemas
- Service orchestration
- Repository reuse

#### Sprint 4.4 — API Quality & Production Hardening
- Request validation
- Consistent response models
- Structured logging
- Enhanced exception handling
- Dependency cleanup
- Route consistency
- Database health monitoring
- OpenAPI improvements
- End-to-end API verification

### ✅ Sprint 5 — Interactive Analytics Dashboard

#### Sprint 5.1 — Dashboard Foundation
- Streamlit application
- API client layer
- Dashboard Services
- Navigation
- Shared layout
- Configuration management
- Error handling
- Loading states

#### Sprint 5.2 — Job Explorer
- Job browsing
- Search
- Filtering
- Pagination
- Job detail view
- API integration

#### Sprint 5.3 — Analytics Dashboard
- KPI overview
- Skills analytics
- Company analytics
- Location analytics
- Salary analytics
- Employment analytics
- Posting trends
- Reusable Plotly chart library

#### Sprint 5.4 — Dashboard Polish & Production Readiness
- Dashboard caching
- Centralized configuration
- Professional SVG icon system
- Responsive layouts
- Enhanced loading states
- Empty-state components
- Accessibility improvements
- Structured dashboard logging
- Architecture documentation
- Regression verification
- Code quality improvements
- Ruff, Black, MyPy compliance

### ✅ Sprint 6.1 — Production Hardening

- Configuration improvements
- Testing improvements
- Code quality improvements
- API reliability improvements

### ✅ Sprint 6.2 — Containerization & CI/CD

- Docker containerization
  - Backend Docker image
  - Dashboard Docker image
  - PostgreSQL container
- Docker Compose orchestration
  - Environment variable management
  - Persistent database volumes
  - Container health checks
  - Non-root container users
- Database Initialization
  - Automatic PostgreSQL startup
  - Database health verification
  - Automatic Alembic migrations
  - Backend startup dependency management
- Continuous Integration
  - GitHub Actions workflow
  - Automated linting (Ruff)
  - Code formatting validation (Black)
  - Static type checking (MyPy)
  - Unit testing with PostgreSQL
  - Integration testing
  - Docker image build validation

### ✅ Sprint 6.3 — Production Readiness & Health Monitoring

- **Health Endpoints** - Liveness (`/live`), Readiness (`/ready`), and Detailed (`/health`)
- **Request Correlation** - X-Request-ID middleware for tracing
- **Structured JSON Logging** - Production-ready logging with UTC timestamps
- **Production Configuration** - Validation and environment-based settings
- **Database Connection Pooling** - Configurable pool settings
- **Smoke Tests** - Production deployment verification
- **Deployment Configuration** - Render.com deployment with health checks

### ✅ Sprint 6.4 — ETL Pipeline Enhancement

- **Upsert Support** - Insert new jobs, update existing jobs by `source_id`
- **Targeted Lookup** - Bulk source_id lookup (O(batch_size), no N+1 queries)
- **90-Day Retention Policy** - Automatic cleanup based on `scraped_date`
- **Pipeline Metrics** - Track inserted, updated, deleted, failed counts
- **Clean Transaction Boundaries** - Caller (`run_pipeline.py`) owns commit/rollback
- **Repository Pattern** - Pure database operations, no business logic
- **Single Flush** - Efficient batch operations

### ✅ Sprint 6.5 — Pipeline Automation

- **GitHub Actions Workflow** - Daily ETL at 6:00 AM UTC
- **Concurrency Protection** - Prevents overlapping pipeline runs
- **Manual Trigger** - `workflow_dispatch` for on-demand runs
- **Entry Point Script** - `scripts/run_pipeline.py` with transaction ownership
- **Secrets Management** - DATABASE_URL, ADZUNA_APP_ID, ADZUNA_APP_KEY
- **Documentation** - `docs/automation.md` with setup guide
- **Analytics Enhancement** - Unique counts in dashboard summary

### ✅ Sprint 6.6 — Enrichment Layer (Skill Extraction & Intelligence)

- **Skill Extraction** - Extract technical skills from job titles and descriptions
- **Technology Classification** - Classify jobs into categories (backend, frontend, ml_ai, etc.)
- **Country Normalization** - Normalize country codes to ISO format
- **Currency Normalization** - Normalize currencies and convert to USD
- **Typed ETL Pipeline** - Extract → Transform → Enrich → Validate → Load
- **Enrichment Schemas** - `JobTransformed`, `JobEnriched`, `JobValidated`, `PipelineMetrics`
- **Enrichment Data** - Country maps, currency maps, technology categories, skills keywords
- **Database Enrichment Fields** - `technology_category`, `is_tech_role`, `country_code`, `currency`
- **API Enrichment Endpoints** - `/analytics/enriched/skills`, `/analytics/enriched/countries`, `/analytics/enriched/technology`, `/analytics/enriched/salary`
- **Dashboard Integration** - Enrichment data available through API
- **Batch Processing** - Efficient skill persistence with duplicate handling
- **Idempotent Pipeline** - Safe to run multiple times without duplication

### ✅ Sprint 6.6.1 — Classifier Refactor & UI Improvements

**Goal:** Fix classifier accuracy issues and improve UI experience.

**Changes:**
1. **Policy System** - Created `policy.py` as single source of truth for classification thresholds
2. **Single Source of Truth** - `classifier.py` with `classify_result()` function used by both production and validation
3. **Stricter Classification** - Higher thresholds (`tech_minimum: 8`, `min_confidence: 0.15`), margin-based classification
4. **Category Overrides** - Different thresholds per category with `get_effective_thresholds()`
5. **Non-Tech Indicators** - Comprehensive negative keyword list (occupation-based only)
6. **Sampling Framework** - `scripts/sample_jobs.py` with 5 strategies for manual labeling
7. **SVG Icon System** - Professional icons replacing emojis
8. **Filter Redesign** - Clean, modern UI with expandable sections
9. **Translate Button** - Language translation in job detail view
10. **Language Detection Fix** - German jobs now correctly labeled
11. **Performance Optimization** - Cache `get_scorer()` in `enricher.py`

**Results:**
- Reduced false positives in tech/non-tech classification
- Clear classification decisions with explanations
- Professional, consistent UI across all dashboard pages
- Reproducible sampling for continuous classifier improvement

**Fixes:**
- ✅ German job labeled as English → Fixed
- ✅ No Translate button in UI → Added
- ✅ Non-tech jobs labeled as tech → Fixed
- ✅ Ugly filters in job page → Redesigned
- ✅ Double tech role filters → Removed duplicates
- ✅ ETL last run stuck at 2 hours → Fixed
- ✅ Emojis instead of SVG icons → Replaced with SVG

### ✅ Sprint 6.6.2 — Acquisition Strategy & Balanced Dataset

**Goal:** Replace the uncontrolled acquisition (0.4% tech) with a balanced two-stream strategy achieving ~50% tech / ~50% non-tech.

**Changes:**
1. Made `JobsExtractor` query-aware with `extract_with_params(country, search_params)`
2. Added `AcquisitionController` with two-phase strategy:
   - **CATCH_UP:** Tech-only queries until parity (`tech_count >= non_tech_count`)
   - **BALANCED:** Alternating tech/broad queries maintaining ~50/50
3. Created broad & tech query families with 30+ occupation terms each
4. Implemented batch-level feedback loop: extract → classify → update controller → next query
5. Fixed `JobEnriched` schema to include `currency`, `normalized_salary_min`, `normalized_salary_max`
6. Fixed `technology_category` → `None` and `tech_confidence` → `None` for non-tech jobs
7. Fixed acquisition controller to use attribute access (`.is_tech_role`) on Pydantic models
8. Fixed repository `currency` → `salary_currency` mapping
9. Removed batch-size termination from `get_next_query()`

**Results:**
- **100 jobs processed:** 50 tech-intent, 50 broad-intent → 48 tech, 52 non-tech
- **Tech ratio:** 48% (target: 50%) — within tolerance ✅
- **Queries:** 4 batches of 25 jobs each, alternating tech → broad → tech → broad
- **Pipeline:** Extraction → Transform → Enrich → Validate → Load all successful

**Query-Level Adaptation:**
| Batch | Query | Intent | Tech | Non-Tech | Adaptation |
|-------|-------|--------|------|----------|------------|
| 1 | software engineer | Tech | 24 | 1 | Tech-heavy start |
| 2 | nurse | Broad | 0 | 25 | Switched to broad |
| 3 | software developer | Tech | 24 | 1 | Switched to tech |
| 4 | doctor | Broad | 0 | 25 | Switched to broad |

**Successfully achieved** the targeted broad labor-market dataset with ~50% technology representation.

---

### 🚧 Sprint 6.7 — E2E & Integration Tests (Planned)

After completing Sprint 6.6.2, the next step is to ensure the entire system works together correctly through comprehensive end-to-end and integration testing.

```
SPRINT 6.7
│
├── 6.7.1 E2E Test Framework
│   ├── API end-to-end tests
│   ├── ETL pipeline end-to-end tests
│   ├── Dashboard end-to-end tests
│   └── Cross-service integration tests
│
├── 6.7.2 Integration Tests
│   ├── Database integration tests
│   ├── API integration tests
│   ├── ETL integration tests
│   └── Dashboard API client tests
│
├── 6.7.3 Performance Tests
│   ├── API load testing
│   ├── ETL performance testing
│   └── Database query optimization
│
├── 6.7.4 Test Coverage & Reporting
│   ├── Coverage report generation
│   ├── Test result reporting
│   └── CI/CD integration
│
└── 6.7.5 Deployment Preparation
    ├── Production readiness review
    ├── Documentation updates
    └── Final deployment
```

---

## Current Status

### ✅ Completed

- Planning & Architecture
- Database Foundation
- Complete ETL Pipeline with Upsert
- Analytics Engine with Dashboard Metrics
- FastAPI REST API with Health Checks
- Interactive Streamlit Dashboard
- Repository Layer
- Service Layer
- API Client Layer
- Dashboard Service Layer
- PostgreSQL Integration
- OpenAPI Documentation
- Interactive Plotly Visualizations
- Dashboard Caching
- Health Monitoring
- Request Validation
- End-to-End ETL Testing
- API Testing
- Dashboard Regression Testing
- Production Hardening
- Docker Containerization
- CI/CD with GitHub Actions
- Automated ETL Pipeline
- 90-Day Retention Policy
- Pipeline Run Tracking
- Structured JSON Logging
- Request Correlation
- Production Deployment Configuration
- **Enrichment Layer (Sprint 6.6)**
  - Skill Extraction
  - Technology Classification
  - Country Normalization
  - Currency Normalization
  - Typed ETL Pipeline
  - Enrichment API Endpoints
  - Dashboard Integration
- **Classifier Refactor & UI Improvements (Sprint 6.6.1)**
  - Policy System (`policy.py`)
  - Single Source of Truth (`classifier.py`)
  - Sampling Framework (`sample_jobs.py`)
  - Professional SVG Icon System
  - Language Detection Fixes
  - UI Improvements (Translate button, filter redesign)
  - 7 Critical Issues Fixed
- **Acquisition Strategy & Balanced Dataset (Sprint 6.6.2)**
  - Two-Phase Acquisition Strategy (CATCH-UP → BALANCED)
  - Batch-Level Feedback Loop
  - Tech/Broad Query Families
  - 50/50 Tech/Non-Tech Target Achieved (48%)
  - 4 Batches of 25 Jobs Each
  - Query-Level Adaptation Metrics

### 📋 Pending

- **E2E & Integration Tests** - Planned for Sprint 6.7

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

**Example verification:**
```bash
python scripts/verify_sprint5.py
```

**Smoke Tests:**
```bash
pytest tests/smoke/ -v -m smoke
```

**Continuous Integration:**
Testing is automatically validated through GitHub Actions. The CI pipeline executes:

- Ruff linting
- Black formatting checks
- MyPy type checking
- Unit tests
- PostgreSQL integration tests
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

## Project Roadmap

| Sprint | Status | Description |
|--------|--------|-------------|
| ✅ Sprint 0 | Complete | Planning & Design |
| ✅ Sprint 1 | Complete | Database Foundation |
| ✅ Sprint 2 | Complete | ETL Pipeline |
| ✅ Sprint 3 | Complete | Analytics Engine |
| ✅ Sprint 4 | Complete | FastAPI REST API |
| ✅ Sprint 5 | Complete | Interactive Analytics Dashboard |
| ✅ Sprint 6.1 | Complete | Production Hardening |
| ✅ Sprint 6.2 | Complete | Docker & CI/CD |
| ✅ Sprint 6.3 | Complete | Production Readiness & Health Monitoring |
| ✅ Sprint 6.4 | Complete | ETL Pipeline Enhancement |
| ✅ Sprint 6.5 | Complete | Pipeline Automation |
| ✅ Sprint 6.6 | Complete | Enrichment Layer (Skill Extraction & Intelligence) |
| ✅ Sprint 6.6.1 | Complete | Classifier Refactor & UI Improvements |
| ✅ Sprint 6.6.2 | Complete | Acquisition Strategy & Balanced Dataset |
| 🚧 Sprint 6.7 | Planned | E2E & Integration Tests |

---

## Future Enhancements

- Support multiple job data sources (Indeed, LinkedIn, Glassdoor)
- Scheduled ETL execution with monitoring dashboard
- Authentication & authorization (JWT, OAuth2)
- Background task processing (Celery, Redis)
- Historical trend analysis
- Real-time analytics with WebSocket support
- API rate limiting
- Distributed caching (Redis)
- Kubernetes deployment
- Cloud-native infrastructure (AWS/Azure/GCP)
- Monitoring with Prometheus/Grafana
- Production logging pipeline (ELK Stack)
- Role-based access control
- Export analytics (CSV/PDF)
- Machine learning job demand forecasting
- Recommendation engine for skills and careers
- Email notifications for failed pipelines
- SLA monitoring and alerting
- Active learning pipeline for continuous classifier improvement

---

## License

This project is licensed under the MIT License.

---

## Contact

**Author:** Jay Mwangi

**GitHub:** [jaymwangi](https://github.com/jaymwangi)

**Project:** [job-market-intelligence](https://github.com/jaymwangi/job-market-intelligence)
```