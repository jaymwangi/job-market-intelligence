# Job Market Intelligence

A production-oriented data engineering and analytics platform that collects, transforms, stores, and analyzes technology job market data from external sources. The system provides insights into skill demand, salary trends, hiring patterns, and workforce dynamics through a layered architecture consisting of an ETL pipeline, analytics engine, REST API, and interactive analytics dashboard.

The project demonstrates production-ready software engineering practices, including clean architecture, layered design, repository and service patterns, data validation, analytics, scalable backend development, and modern frontend integration, all orchestrated in a containerized environment.

---

# Why This Project

Many portfolio projects stop after collecting data.

This project simulates a real-world data platform by implementing:

* Modular ETL pipeline
* Layered architecture
* Repository and Service patterns
* Analytics engine
* Production-ready REST API
* Interactive analytics dashboard
* API-driven frontend architecture
* Docker containerization
* CI/CD pipeline
* Deployment-ready project structure

The goal is to demonstrate backend engineering, data engineering, analytics engineering, API development, frontend integration, and DevOps practices within a single cohesive application.

---

# Features

### ETL Pipeline

* Extract job postings from external job APIs (currently Adzuna)
* Transform external job data into a standardized internal format
* Validate incoming data using Pydantic models
* Load validated data into PostgreSQL
* Prevent duplicate job records during ingestion
* Track ETL pipeline executions and metadata

### Analytics Engine

* Analyze skill demand
* Analyze salary trends
* Analyze hiring companies
* Analyze job locations
* Analyze employment types
* Analyze posting trends
* Aggregate dashboard metrics
* Generate dataset summaries

### REST API

* Expose job data through FastAPI
* Expose analytics through REST endpoints
* Filtering
* Pagination
* Search
* Health endpoints
* Database health endpoint
* OpenAPI documentation (Swagger & ReDoc)
* Request validation
* Structured error handling

### Interactive Dashboard

* Interactive Streamlit dashboard
* API-driven frontend (no direct database access)
* Job explorer
* Interactive Plotly visualizations
* KPI dashboard
* Dashboard caching
* Professional SVG icon system
* Loading states
* Friendly error handling
* Empty-state components
* Modular reusable UI components

### DevOps & Containerization

* Docker containerization for all services
* Docker Compose orchestration
* GitHub Actions CI/CD pipeline
* Automated linting, type checking, and testing
* Environment variable management
* Persistent database volumes
* Container health checks
* Non-root container users for security
* Automated database migrations on startup

---

# Tech Stack

## Backend

* Python 3.13
* FastAPI
* SQLAlchemy 2.0
* Alembic
* Pydantic v2

## Database

* PostgreSQL

## Data Processing

* Pandas

## Dashboard

* Streamlit
* Plotly

## Development & DevOps

* Git
* GitHub
* Docker
* Docker Compose
* GitHub Actions
* Ruff
* Black
* MyPy
* Pytest
* Code Coverage

---

# Architecture

```text
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
                  Validator (Pydantic)
                           │
                           ▼
                         Loader
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

# Project Structure

```text
job-market-intelligence/
│
├── .github/
│   └── workflows/
│       └── quality.yml
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
│   │   ├── extractors/
│   │   ├── loaders/
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
├── migrations/
├── scripts/
├── tests/
│
├── Dockerfile
├── compose.yml
├── .dockerignore
├── .env.example
├── Makefile
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

# Current Progress

## ✅ Sprint 0 — Planning & Design

* Requirements gathering
* System architecture
* Database design
* API contract
* Development roadmap

---

## ✅ Sprint 1 — Database Foundation

* Project initialization
* Configuration management
* PostgreSQL setup
* SQLAlchemy ORM models
* Database session management
* Alembic migrations
* Repository layer
* Database testing

---

## ✅ Sprint 2 — ETL Pipeline

### Sprint 2.1 — Extraction

* HTTP client
* Adzuna API integration
* Job extractor
* Extraction testing

### Sprint 2.2 — Transformation

* Standardized internal job schema
* Transformation layer
* Transformation testing

### Sprint 2.3 — Validation

* Pydantic validation
* Business rule validation
* Data quality checks
* Validation testing

### Sprint 2.4 — Loading

* Repository-based persistence
* Duplicate detection
* Transaction management
* Pipeline execution tracking
* End-to-end ETL testing

---

## ✅ Sprint 3 — Analytics Engine

### Sprint 3.1 — Analytics Foundation

* Top skills
* Top companies
* Jobs by location
* Salary statistics
* Employment type distribution

### Sprint 3.2 — Advanced Analytics

* Salary by company
* Salary by location
* Salary distribution
* Posting trends
* Recent jobs
* Advanced aggregation queries

### Sprint 3.3 — Analytics Refinement

* Analytics Service layer
* Dashboard summary orchestration
* Repository improvements
* Query optimization
* Dataset quality reporting
* Analytics integration testing

---

## ✅ Sprint 4 — FastAPI REST API

### Sprint 4.1 — FastAPI Foundation

* FastAPI application setup
* Centralized routing
* API versioning
* Health endpoint
* Database health endpoint
* Dependency injection
* Global exception handling
* Structured logging
* CORS middleware
* OpenAPI documentation

### Sprint 4.2 — Jobs API

* Job REST endpoints
* Pagination
* Filtering
* Search
* UUID support
* Response schemas
* Repository and Service integration

### Sprint 4.3 — Analytics API

* Analytics REST endpoints
* Dashboard summary endpoint
* Overview endpoint
* Analytics response schemas
* Service orchestration
* Repository reuse

### Sprint 4.4 — API Quality & Production Hardening

* Request validation
* Consistent response models
* Structured logging
* Enhanced exception handling
* Dependency cleanup
* Route consistency
* Database health monitoring
* OpenAPI improvements
* End-to-end API verification

---

## ✅ Sprint 5 — Interactive Analytics Dashboard

### Sprint 5.1 — Dashboard Foundation

* Streamlit application
* API client layer
* Dashboard Services
* Navigation
* Shared layout
* Configuration management
* Error handling
* Loading states

### Sprint 5.2 — Job Explorer

* Job browsing
* Search
* Filtering
* Pagination
* Job detail view
* API integration

### Sprint 5.3 — Analytics Dashboard

* KPI overview
* Skills analytics
* Company analytics
* Location analytics
* Salary analytics
* Employment analytics
* Posting trends
* Reusable Plotly chart library

### Sprint 5.4 — Dashboard Polish & Production Readiness

* Dashboard caching
* Centralized configuration
* Professional SVG icon system
* Responsive layouts
* Enhanced loading states
* Empty-state components
* Accessibility improvements
* Structured dashboard logging
* Architecture documentation
* Regression verification
* Code quality improvements
* Ruff, Black, MyPy compliance

---

## ✅ Sprint 6.1 — Production Hardening

* Configuration improvements
* Testing improvements
* Code quality improvements
* API reliability improvements

---

## ✅ Sprint 6.2 — Containerization & CI/CD

* Docker containerization
  * Backend Docker image
  * Dashboard Docker image
  * PostgreSQL container
* Docker Compose orchestration
  * Environment variable management
  * Persistent database volumes
  * Container health checks
  * Non-root container users
* Database Initialization
  * Automatic PostgreSQL startup
  * Database health verification
  * Automatic Alembic migrations
  * Backend startup dependency management
* Continuous Integration
  * GitHub Actions workflow
  * Automated linting (Ruff)
  * Code formatting validation (Black)
  * Static type checking (MyPy)
  * Unit testing with PostgreSQL
  * Integration testing
  * Docker image build validation

---

# Current Status

## ✅ Completed

* Planning & Architecture
* Database Foundation
* Complete ETL Pipeline
* Analytics Engine
* FastAPI REST API
* Interactive Streamlit Dashboard
* Repository Layer
* Service Layer
* API Client Layer
* Dashboard Service Layer
* PostgreSQL Integration
* OpenAPI Documentation
* Interactive Plotly Visualizations
* Dashboard Caching
* Health Monitoring
* Request Validation
* End-to-End ETL Testing
* API Testing
* Dashboard Regression Testing
* Production Hardening
* Docker Containerization
* CI/CD with GitHub Actions

---

# Docker Development

## Quick Start

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

## Startup Flow

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

## Application Access

| Service | URL |
|---|---|
| FastAPI API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| Streamlit Dashboard | http://localhost:8501 |
| PostgreSQL | localhost:5432 |

## Useful Commands

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

---

# Testing

The project includes testing for:

* ETL pipeline
* Repository layer
* Service layer
* Analytics engine
* FastAPI REST API
* Dashboard services
* Dashboard utilities
* Dashboard caching
* API integration
* End-to-end ETL workflow
* Sprint regression verification

**Example verification:**
```bash
python scripts/verify_sprint5.py
```

**Continuous Integration:**
Testing is automatically validated through GitHub Actions. The CI pipeline executes:

* Ruff linting
* Black formatting checks
* MyPy type checking
* Unit tests
* PostgreSQL integration tests
* Docker image builds

---

# Project Roadmap

| Sprint | Status | Description |
|---|---|---|
| ✅ Sprint 0 | Complete | Planning & Design |
| ✅ Sprint 1 | Complete | Database Foundation |
| ✅ Sprint 2 | Complete | ETL Pipeline |
| ✅ Sprint 3 | Complete | Analytics Engine |
| ✅ Sprint 4 | Complete | FastAPI REST API |
| ✅ Sprint 5 | Complete | Interactive Analytics Dashboard |
| ✅ Sprint 6.1 | Complete | Production Hardening |
| ✅ Sprint 6.2 | Complete | Docker & CI/CD |
| 🚧 Sprint 6.3 | Planned | Cloud Deployment & Monitoring |

---

# Future Enhancements

* Support multiple job data sources
* Scheduled ETL execution
* Authentication & authorization
* Background task processing
* Historical trend analysis
* Real-time analytics
* API rate limiting
* Distributed caching (Redis)
* Kubernetes deployment
* Cloud-native infrastructure
* AWS/Azure deployment
* Monitoring with Prometheus/Grafana
* Production logging pipeline
* Role-based access control
* Export analytics (CSV/PDF)
* Machine learning job demand forecasting
* Recommendation engine for skills and careers

---

# License

This project is licensed under the MIT License.