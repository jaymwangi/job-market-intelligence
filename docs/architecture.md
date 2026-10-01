# Job Market Intelligence — Architecture

## Purpose

This document describes the current architecture of Job Market Intelligence and the responsibilities of its major components.

It answers:

- How does data move through the system?
- Where does business logic live?
- How does the API access PostgreSQL?
- How does the dashboard consume the API?
- How is the ETL pipeline separated from the API?
- How is the production system deployed?

Development setup is documented in [`development.md`](development.md).

Testing strategy is documented in [`testing.md`](testing.md).

Deployment and recovery procedures are documented in [`deployment.md`](deployment.md).

---

# 1. System Architecture

Job Market Intelligence is a full-stack job-market analytics platform built around a Python ETL pipeline, PostgreSQL database, FastAPI backend, and Streamlit dashboard.

The current production ingestion source is Adzuna.

```text
                         Adzuna
                           │
                           ▼
                  ┌─────────────────┐
                  │ ETL Acquisition │
                  │    Extract      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Transformation  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Enrichment    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Validation    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │     Loader      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   PostgreSQL    │
                  │      Neon       │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Repositories   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    Services     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │     FastAPI     │
                  │      API       │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Streamlit       │
                  │ Dashboard       │
                  └─────────────────┘
````

The system is intentionally separated into data ingestion, persistence, backend application logic, and presentation layers.

---

# 2. Production Architecture

The production deployment separates source control, automation, API hosting, dashboard hosting, and database hosting.

```text
                              GitHub
                           /    │    \
                          /     │     \
                         ▼      ▼      ▼
                GitHub Actions Render  Streamlit
                  CI / ETL      API     Community
                                  │       Cloud
                                  │
                                  ▼
                                Neon
                             PostgreSQL
```

### GitHub

GitHub is the source repository and automation control plane.

It contains:

* Application source code
* Dashboard source code
* Database migrations
* Tests
* Documentation
* GitHub Actions workflows

### GitHub Actions

GitHub Actions provides:

* Continuous integration
* Quality checks
* Unit testing
* Integration testing
* E2E testing
* ETL execution

The ETL workflow is currently available through manual `workflow_dispatch`. Its scheduled trigger is suspended pending Neon data-transfer remediation.

### Render

Render hosts the FastAPI backend.

The API is deployed as a Docker container.

The container startup sequence runs:

```text
alembic upgrade head
        ↓
uvicorn
        ↓
FastAPI
```

Render uses:

```text
/api/v1/health/live
```

as its configured health-check path.

### Streamlit Community Cloud

Streamlit Community Cloud hosts the dashboard.

The dashboard communicates with the FastAPI API rather than accessing the production database directly.

### Neon

Neon provides the production PostgreSQL database.

Both the deployed API and production ETL workflow require database connectivity.

---

# 3. Data Flow

The production data flow is:

```text
Adzuna
   ↓
Acquisition
   ↓
Transformation
   ↓
Enrichment
   ↓
Validation
   ↓
Loading
   ↓
PostgreSQL / Neon
   ↓
FastAPI
   ↓
Streamlit Dashboard
```

Each stage has a distinct responsibility.

### Acquisition

Located primarily under:

```text
app/etl/acquisition/
app/etl/extractors/
app/etl/clients/
```

The acquisition layer obtains job data from the external source.

### Transformation

Located under:

```text
app/etl/transformers/
```

Raw source records are converted into the application's transformed representation.

### Enrichment

Located under:

```text
app/etl/enrichment/
```

Enrichment includes operations such as:

* Country normalization
* Currency normalization
* Language detection
* Skill extraction
* Technology classification
* Technology scoring
* Job classification

### Validation

Located under:

```text
app/etl/validators/
```

Validation ensures that records satisfy the application's expected data rules before loading.

### Loading

Located under:

```text
app/etl/loaders/
```

The loader persists validated records and associated information in PostgreSQL.

Pipeline metrics are recorded so ETL execution can be monitored operationally.

---

# 4. Backend Architecture

The backend follows a layered application structure.

```text
HTTP Request
     ↓
FastAPI Routes
     ↓
Services
     ↓
Repositories
     ↓
SQLAlchemy / Database
     ↓
PostgreSQL
```

## API Layer

Located under:

```text
app/api/
```

Responsibilities include:

* HTTP routing
* Dependency injection
* Request/response handling
* API middleware
* Exception handling

Routes are organized under:

```text
app/api/routes/
```

Current route groups include:

* `analytics.py`
* `health.py`
* `jobs.py`

The API is versioned under:

```text
/api/v1
```

---

## Service Layer

Located under:

```text
app/services/
```

Services contain application and business logic that should not be embedded directly in HTTP route functions.

Current service areas include:

* Job services
* Analytics services
* Translation services

The service layer coordinates repositories and other application-level operations.

---

## Repository Layer

Located under:

```text
app/repositories/
```

Repositories provide the database-access abstraction used by services. API routes construct the required repository dependencies and pass them to services. Some specialized service operations, such as ETL pipeline-status queries, instantiate a dedicated repository directly.

Current repositories include:

* `job_repository.py`
* `skill_repository.py`
* `analytics_repository.py`
* `pipeline_run_repository.py`

This separation keeps database-specific access patterns out of API route functions.

---

## Database Layer

Located under:

```text
app/database/
```

Responsibilities include:

* Database session management
* Database health checks
* SQLAlchemy base configuration

The production database is PostgreSQL hosted by Neon.

---

## Models and Schemas

Database models are located under:

```text
app/models/
```

Current model areas include:

* Jobs
* Skills
* Job-skill relationships
* Pipeline runs

API schemas are located under:

```text
app/schemas/
```

These define typed structures used by the API.

---

# 5. ETL Architecture

The ETL pipeline is intentionally separate from the request-serving API.

The pipeline supports two acquisition modes:

```text
Adaptive acquisition
External Source
      ↓
Acquisition Controller
      ↓
Batch Extraction
      ↓
Transformation
      ↓
Enrichment / Classification
      ↓
Classification Feedback
      └──────────────→ Acquisition Controller
      ↓
Loading
      ↓
Pipeline Metrics
```

When adaptive acquisition is disabled, the pipeline uses the legacy flow:

```text
External Source
      ↓
Extract All
      ↓
Transformation
      ↓
Enrichment
      ↓
Validation
      ↓
Loading
      ↓
Pipeline Metrics
```

The pipeline runner is:

```text
scripts/run_pipeline.py
```

The separation provides an important operational boundary:

* API requests do not perform the full ingestion pipeline.
* ETL execution can be scheduled or triggered independently.
* ETL failures can be inspected through pipeline execution records and workflow logs.
* Database loading is handled by dedicated ETL components.

The ETL pipeline records execution information in the `pipeline_runs` table.

---

# 6. Dashboard Architecture

The Streamlit dashboard is a separate application that consumes the FastAPI API.

Its source structure is:

```text
dashboard/
├── api/
├── core/
├── schemas/
├── services/
├── mappers/
├── components/
├── pages/
└── utils/
```

The dashboard therefore has its own internal application layers.

```text
Streamlit Pages
       ↓
Dashboard Services
       ↓
API Client
       ↓
FastAPI
```

For visualization-specific processing:

```text
API Response
     ↓
Dashboard Service
     ↓
Dashboard Schema
     ↓
Mapper
     ↓
Chart / UI Component
     ↓
Streamlit Page
```

---

## Dashboard API Layer

Located under:

```text
dashboard/api/
```

The API layer handles HTTP communication with the FastAPI backend.

It contains:

* Base client
* API client
* Endpoint definitions
* API exceptions

Dashboard pages should not implement raw HTTP requests directly.

---

## Dashboard Services

Located under:

```text
dashboard/services/
```

Services coordinate API calls and prepare application data for the dashboard.

Current service areas include:

* Analytics
* Jobs
* Health

---

## Dashboard Schemas

Located under:

```text
dashboard/schemas/
```

Schemas provide typed representations for dashboard data.

They help isolate the dashboard from raw API response structures.

---

## Dashboard Mappers

Located under:

```text
dashboard/mappers/
```

Mappers transform application data into presentation-oriented structures such as chart data.

This keeps visualization-specific transformation outside page orchestration.

---

## Dashboard Components

Located under:

```text
dashboard/components/
```

Reusable components include:

* Charts
* Tables
* Filters
* Metrics
* Alerts
* Loading states
* Pagination
* Job cards
* Job details
* Layout
* Sidebar
* Icons

Components should remain reusable and should not contain backend business logic.

---

## Dashboard Pages

Located under:

```text
dashboard/pages/
```

Current pages include:

* `overview.py`
* `jobs.py`
* `analytics.py`
* `about.py`

Pages primarily orchestrate the user interface and compose services and reusable components.

---

## Dashboard Utilities

Located under:

```text
dashboard/utils/
```

Utilities support cross-cutting dashboard concerns such as:

* Caching
* Formatting
* Application state
* Logging
* Service creation
* Helper functions

---

# 7. Caching

Caching is implemented within the dashboard application.

The purpose is to reduce repeated API requests for data that does not need to be retrieved on every page interaction.

Caching is therefore a dashboard optimization rather than a replacement for the API or database.

Cache behavior and endpoint-specific settings should be treated as implementation details of the dashboard rather than assumptions about database freshness.

---

# 8. Database and Migrations

The database schema is managed through Alembic migrations.

Migration files are located under:

```text
migrations/
```

The normal schema update operation is:

```bash
alembic upgrade head
```

The migration chain provides a reproducible schema history across environments.

The API container applies migrations during startup before starting Uvicorn.

The ETL workflow also runs migrations before executing the pipeline.

Database schema details are documented separately in [`database_schema.md`](database_schema.md).

---

# 9. Architectural Decisions

## PostgreSQL for Persistent Storage

PostgreSQL provides relational storage for:

* Jobs
* Skills
* Job-skill relationships
* Pipeline execution records

The relational model supports analytical queries and explicit relationships between jobs and skills.

## FastAPI for the Backend

FastAPI provides the HTTP boundary between the stored analytical data and consuming applications.

It also provides:

* Request validation
* Typed responses
* Dependency injection
* OpenAPI documentation

## Streamlit for the Dashboard

Streamlit provides a Python-native interface for presenting analytical results without requiring a separate frontend framework.

The dashboard remains decoupled from the database by consuming the API.

## Repository and Service Separation

Repositories isolate database access.

Services contain application logic.

This makes responsibilities clearer and allows backend logic to be tested without embedding all behavior inside route functions.

## Separate ETL and API Execution

ETL execution is separated from request handling so that large ingestion operations do not need to run inside normal API requests.

## Centralized Enrichment

Data enrichment is performed during ETL rather than independently by downstream consumers.

This creates a consistent representation of normalized and classified job data for the API and dashboard.

## Alembic Migrations

Schema changes are tracked as migrations rather than being applied through undocumented manual database changes.

---

# 10. Architectural Constraints

The following boundaries should be preserved.

### Backend

* Routes should remain thin.
* Business/application logic belongs in services.
* Database access belongs in repositories.
* Database sessions should not be created directly inside route functions.
* API schemas should remain separate from database models where appropriate.

### ETL

* Extraction should remain separate from transformation.
* Enrichment should remain separate from validation.
* Loading should operate on validated pipeline data.
* ETL execution should remain independently observable.

### Dashboard

* Pages should primarily orchestrate UI.
* Pages should not perform raw HTTP requests.
* Dashboard services should own API interaction.
* Mappers should handle presentation-oriented transformation.
* Reusable components should not contain backend business logic.
* Dashboard code should not connect directly to the production database.

### Production

* Production database changes should use Alembic migrations.
* Deployment configuration should not contain plaintext secrets.
* Application rollback should not be treated as database rollback.
* Operational monitoring should distinguish application failures from dependency failures.

---

# 11. Failure Boundaries

The architecture separates several failure domains:

```text
External API
     │
     ▼
    ETL
     │
     ▼
 Database
     │
     ▼
    API
     │
     ▼
 Dashboard
```

A failure in one component can affect dependent components.

For example:

```text
Database unavailable
       ↓
API readiness failure
       ↓
Dashboard data requests fail
```

Similarly:

```text
Database unavailable
       ↓
ETL cannot load data
       ↓
Data freshness is affected
```

The architecture therefore emphasizes **clear dependency boundaries and observable failure points**, rather than assuming that failures are completely isolated.

Detailed failure diagnosis is documented in [`troubleshooting.md`](troubleshooting.md).

---

# 12. Related Documentation

* [`README.md`](../README.md) — project overview and getting started
* [`development.md`](development.md) — local development workflow
* [`testing.md`](testing.md) — testing strategy
* [`operations.md`](operations.md) — normal system operations
* [`deployment.md`](deployment.md) — deployment, rollback, and recovery
* [`troubleshooting.md`](troubleshooting.md) — failure diagnosis
* [`api_contract.md`](api_contract.md) — API contract
* [`database_schema.md`](database_schema.md) — database structure
* [`roadmap.md`](roadmap.md) — development history and roadmap