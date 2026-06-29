# Job Market Intelligence

A production-oriented data engineering and analytics platform that collects, processes, and analyzes technology job market data to uncover skill demand, salary trends, hiring patterns, and workforce insights. The project follows a modular architecture with an ETL pipeline, REST API, analytics layer, and interactive dashboard.

## Features

* Collect job postings from multiple sources
* Normalize and validate job data
* Store data in PostgreSQL
* Track ETL pipeline executions
* Analyze technology skills, salaries, and hiring trends
* Serve data through a FastAPI backend
* Visualize insights with a Streamlit dashboard

## Tech Stack

### Backend

* Python 3.13
* FastAPI
* SQLAlchemy 2.0
* Alembic
* Pydantic

### Database

* PostgreSQL

### Data Processing

* Pandas

### Dashboard

* Streamlit

### Development

* Git
* GitHub

## Project Structure

```text
app/
├── database/
├── models/
├── repositories/
├── services/

api/
├── dependencies/
└── routes/

etl/
├── extract/
├── transform/
└── load/

dashboard/
docs/
scripts/
tests/
migrations/
```

## Current Progress

### ✅ Sprint 0 — Planning & Design

* Requirements documentation
* System architecture
* Database schema
* API contract
* Sprint roadmap

### ✅ Sprint 1 — Database Foundation

* Project structure
* Configuration management
* PostgreSQL setup
* SQLAlchemy ORM
* Database session management
* Alembic migrations
* Initial database schema
* Repository layer skeleton
* Database testing scripts

### 🚧 Sprint 2 — ETL Pipeline (Next)

* Data extraction
* Validation
* Transformation
* Loading into PostgreSQL
* Pipeline execution tracking

## Status

**Current Sprint:** ✅ Sprint 1 Complete

**Next Milestone:** Sprint 2 — ETL Pipeline Development
