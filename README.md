# Job Market Intelligence

A production-oriented data engineering and analytics platform that collects, processes, and analyzes technology job market data to uncover skill demand, salary trends, hiring patterns, and workforce insights. The project follows a layered architecture with a complete ETL pipeline, REST API, analytics engine, and interactive dashboard.

## Features

* Extract job postings from external job APIs (currently Adzuna)
* Transform external job data into a standardized internal format
* Validate incoming data using Pydantic models
* Load validated data into PostgreSQL
* Prevent duplicate job records during ingestion
* Track ETL pipeline executions and metadata
* Analyze technology skills, salaries, and hiring trends
* Serve data through a FastAPI backend
* Visualize insights with a Streamlit dashboard

## Tech Stack

### Backend

* Python 3.13
* FastAPI
* SQLAlchemy 2.0
* Alembic
* Pydantic v2

### Database

* PostgreSQL

### Data Processing

* Pandas

### Dashboard

* Streamlit

### Development

* Git
* GitHub

## Architecture

```text
Adzuna API
      │
      ▼
HTTP Client
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
```

## Project Structure

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

## Current Progress

### ✅ Sprint 0 — Planning & Design

* Requirements gathering
* System architecture
* Database design
* API contract
* Development roadmap

### ✅ Sprint 1 — Database Foundation

* Project initialization
* Configuration management
* PostgreSQL setup
* SQLAlchemy ORM models
* Database session management
* Alembic migrations
* Initial database schema
* Repository layer
* Database testing

### ✅ Sprint 2 — ETL Pipeline

#### Sprint 2.1 — Extraction

* HTTP client
* Adzuna API integration
* Job extractor
* Extraction testing

#### Sprint 2.2 — Transformation

* Data transformation layer
* Standardized internal job schema
* Transformation testing

#### Sprint 2.3 — Validation

* Pydantic validation models
* Business rule validation
* Data quality checks
* Validation testing

#### Sprint 2.4 — Loading

* Loading (Persistence) layer
* Repository-based persistence
* Duplicate detection
* Transaction management
* Pipeline execution tracking
* End-to-end ETL integration test

## Current Status

### ✅ Completed

* Planning & Architecture
* Database Foundation
* Complete ETL Pipeline

  * Extraction
  * Transformation
  * Validation
  * Loading
* Repository Layer
* PostgreSQL Integration
* Pipeline Run Tracking
* End-to-End ETL Testing

## Next Milestone

### 🚧 Sprint 3 — REST API

* FastAPI application
* CRUD endpoints
* Filtering and pagination
* Search functionality
* API documentation
* Health checks
* Repository integration

## Project Roadmap

* ✅ Sprint 0 — Planning
* ✅ Sprint 1 — Database Foundation
* ✅ Sprint 2 — ETL Pipeline
* 🚧 Sprint 3 — REST API
* ⏳ Sprint 4 — Analytics Engine
* ⏳ Sprint 5 — Streamlit Dashboard
* ⏳ Sprint 6 — Deployment & CI/CD
