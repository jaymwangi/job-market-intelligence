# Job Market Intelligence

A production-oriented data engineering and analytics platform that collects, transforms, stores, and analyzes technology job market data from external sources. The system provides insights into skill demand, salary trends, hiring patterns, and workforce dynamics through a layered architecture consisting of an ETL pipeline, analytics engine, REST API, and interactive dashboard.

The project is designed to demonstrate production-ready software engineering practices, including clean architecture, repository and service layers, data validation, analytics, and scalable backend development.

---

# Why This Project

Many portfolio projects stop after collecting data.

This project aims to simulate a real-world data platform by implementing:

- A modular ETL pipeline
- Layered architecture
- Repository and Service patterns
- Analytics engine
- REST API
- Interactive dashboard
- Deployment-ready project structure

The goal is to demonstrate backend engineering, data engineering, and analytics skills within a single cohesive application.

---

# Features

- Extract job postings from external job APIs (currently Adzuna)
- Transform external job data into a standardized internal format
- Validate incoming data using Pydantic models
- Load validated data into PostgreSQL
- Prevent duplicate job records during ingestion
- Track ETL pipeline executions and metadata
- Perform analytics on skills, salaries, companies, locations, and hiring trends
- Aggregate job market statistics through an Analytics Repository
- Provide an Analytics Service for dashboard-oriented summaries
- Serve analytics through a FastAPI backend *(planned)*
- Visualize insights with a Streamlit dashboard *(planned)*

---

# Tech Stack

## Current

### Backend

- Python 3.13
- SQLAlchemy 2.0
- Alembic
- Pydantic v2

### Database

- PostgreSQL

### Data Processing

- Pandas

### Development

- Git
- GitHub

## Planned

- FastAPI
- Streamlit

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
                  Analytics Service
                           ▲
                           │
                 FastAPI (Sprint 4)
                           ▲
                           │
              Streamlit Dashboard (Sprint 5)
```

---

# Project Structure

```text
app/
├── database/
├── etl/
│   ├── clients/
│   ├── extractors/
│   ├── transformers/
│   ├── validators/
│   └── loaders/
├── models/
├── repositories/
├── services/

api/
├── dependencies/
└── routes/

dashboard/
docs/
migrations/
scripts/
tests/
```

---

# Current Progress

## ✅ Sprint 0 — Planning & Design

- Requirements gathering
- System architecture
- Database design
- API contract
- Development roadmap

---

## ✅ Sprint 1 — Database Foundation

- Project initialization
- Configuration management
- PostgreSQL setup
- SQLAlchemy ORM models
- Database session management
- Alembic migrations
- Initial database schema
- Repository layer
- Database testing

---

## ✅ Sprint 2 — ETL Pipeline

### Sprint 2.1 — Extraction

- HTTP client
- Adzuna API integration
- Job extractor
- Extraction testing

### Sprint 2.2 — Transformation

- Standardized internal job schema
- Transformation layer
- Transformation testing

### Sprint 2.3 — Validation

- Pydantic validation models
- Business rule validation
- Data quality checks
- Validation testing

### Sprint 2.4 — Loading

- Repository-based persistence
- Duplicate detection
- Transaction management
- Pipeline execution tracking
- End-to-end ETL testing

---

## ✅ Sprint 3 — Analytics Engine

### Sprint 3.1 — Analytics Foundation

- Top skills
- Top companies
- Jobs by location
- Salary statistics
- Employment type distribution

### Sprint 3.2 — Advanced Analytics

- Salary by company
- Salary by location
- Salary distribution
- Posting trends
- Recent jobs
- Advanced aggregation queries

### Sprint 3.3 — Analytics Refinement

- Analytics Service layer
- Dashboard summary orchestration
- Optional source filtering
- Query optimization
- Repository improvements
- Analytics integration testing
- Dataset quality reporting

---

# Current Status

## ✅ Completed

- Planning & Architecture
- Database Foundation
- Complete ETL Pipeline
- Repository Layer
- PostgreSQL Integration
- Pipeline Run Tracking
- Analytics Repository
- Analytics Service
- Analytics Testing
- End-to-End ETL Testing

---

# Testing

The project includes testing for:

- ETL pipeline
- Repository layer
- Analytics Repository
- Analytics Service
- End-to-end ETL workflow

Run the analytics tests:

```bash
python -m scripts.test_analytics
```

---

# Next Milestone

## 🚧 Sprint 4 — FastAPI REST API

- FastAPI application
- Dependency injection
- API routes
- Pydantic response schemas
- Analytics endpoints
- Filtering & pagination
- OpenAPI documentation
- Health checks

---

# Project Roadmap

- ✅ Sprint 0 — Planning
- ✅ Sprint 1 — Database Foundation
- ✅ Sprint 2 — ETL Pipeline
- ✅ Sprint 3 — Analytics Engine
- 🚧 Sprint 4 — FastAPI REST API
- ⏳ Sprint 5 — Streamlit Dashboard
- ⏳ Sprint 6 — Deployment & CI/CD

---

# Future Enhancements

- Multiple job data sources
- Scheduled ETL pipeline execution
- Authentication and authorization
- Containerization with Docker
- CI/CD pipeline
- Cloud deployment
- Interactive analytics dashboard
- Historical trend analysis

---

# License

This project is licensed under the MIT License.