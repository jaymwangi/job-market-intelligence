# Job Market Intelligence

A production-oriented data engineering and analytics platform that collects, transforms, stores, and analyzes technology job market data from external sources. The system provides insights into skill demand, salary trends, hiring patterns, and workforce dynamics through a layered architecture consisting of an ETL pipeline, analytics engine, REST API, and interactive dashboard.

The project demonstrates production-ready software engineering practices, including clean architecture, layered design, repository and service patterns, data validation, analytics, and scalable backend development.

---

# Why This Project

Many portfolio projects stop after collecting data.

This project aims to simulate a real-world data platform by implementing:

* Modular ETL pipeline
* Layered architecture
* Repository and Service patterns
* Analytics engine
* Production-ready REST API
* Interactive dashboard
* Deployment-ready project structure

The goal is to demonstrate backend engineering, data engineering, and analytics skills within a single cohesive application.

---

# Features

* Extract job postings from external job APIs (currently Adzuna)
* Transform external job data into a standardized internal format
* Validate incoming data using Pydantic models
* Load validated data into PostgreSQL
* Prevent duplicate job records during ingestion
* Track ETL pipeline executions and metadata
* Perform analytics on skills, salaries, companies, locations, and hiring trends
* Aggregate job market insights through an Analytics Repository
* Expose job and analytics data through a FastAPI REST API
* Provide dashboard-oriented analytics through an Analytics Service
* Support filtering, pagination, and search for job data
* Provide health and database health endpoints
* Generate automatic OpenAPI documentation (Swagger & ReDoc)
* Visualize insights with a Streamlit dashboard *(planned)*

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

* Streamlit *(planned)*

## Development

* Git
* GitHub

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
              Streamlit Dashboard (Sprint 5)
```

---

# Project Structure

```text
app/
├── api/
│   ├── routes/
│   ├── dependencies.py
│   ├── exception_handlers.py
│   └── router.py
│
├── core/
│   ├── logging.py
│   └── settings.py
│
├── database/
├── etl/
│   ├── clients/
│   ├── extractors/
│   ├── loaders/
│   ├── transformers/
│   └── validators/
│
├── models/
├── repositories/
├── schemas/
├── services/
└── main.py

dashboard/
docs/
migrations/
scripts/
tests/
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
* Initial database schema
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

* Pydantic validation models
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
* Query optimization
* Repository improvements
* Dataset quality reporting
* Analytics integration testing

---

## ✅ Sprint 4 — FastAPI REST API

### Sprint 4.1 — FastAPI Foundation

* FastAPI application setup
* Centralized routing
* API versioning
* Health endpoint
* Dependency injection
* Global exception handling
* Logging configuration
* CORS middleware
* OpenAPI documentation

### Sprint 4.2 — Jobs API

* Job REST endpoints
* Pagination
* Filtering
* Search
* UUID support
* Response schemas
* Service layer integration

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
* Improved exception handling
* Structured logging
* Database health check
* Enhanced OpenAPI documentation
* Route consistency
* Dependency cleanup
* End-to-end API verification

---

# Current Status

## ✅ Completed

* Planning & Architecture
* Database Foundation
* Complete ETL Pipeline
* Analytics Engine
* FastAPI REST API
* Repository Layer
* Service Layer
* PostgreSQL Integration
* Pipeline Run Tracking
* OpenAPI Documentation
* Health Monitoring
* API Validation
* End-to-End ETL Testing

---

# Testing

The project includes testing for:

* ETL pipeline
* Repository layer
* Service layer
* Analytics engine
* REST API
* End-to-end ETL workflow

---

# Next Milestone

## 🚧 Sprint 5 — Streamlit Dashboard

* Dashboard layout
* Interactive charts
* API integration
* Filtering controls
* Dashboard pages
* User experience improvements

---

# Project Roadmap

* ✅ Sprint 0 — Planning
* ✅ Sprint 1 — Database Foundation
* ✅ Sprint 2 — ETL Pipeline
* ✅ Sprint 3 — Analytics Engine
* ✅ Sprint 4 — FastAPI REST API
* 🚧 Sprint 5 — Streamlit Dashboard
* ⏳ Sprint 6 — Testing, CI/CD & Deployment

---

# Future Enhancements

* Multiple job data sources
* Scheduled ETL execution
* Authentication & authorization
* Docker containerization
* CI/CD pipeline
* Cloud deployment
* Historical trend analysis
* Real-time analytics
* Background task processing
* API rate limiting and caching

---

# License

This project is licensed under the MIT License.
