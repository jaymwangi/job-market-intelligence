# Project Roadmap

This document tracks the development roadmap for Job Market Intelligence.

[← Back to README](../README.md)

**Final target:** `v1.0.0` — released at the end of Sprint 6.8.

---

## Roadmap Overview

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
| ✅ Sprint 6.7.1 | Complete | Integration Test Infrastructure |
| ✅ Sprint 6.7.2 | Complete | PostgreSQL Integration |
| ✅ Sprint 6.7.3 | Complete | ETL Integration |
| ✅ Sprint 6.7.4 | Complete | API Integration |
| ✅ Sprint 6.7.5 | Complete | Analytics Integration |
| ✅ Sprint 6.7.6 | Complete | Dashboard Integration |
| ✅ Sprint 6.7.7 | Complete | End-to-End Workflows |
| ✅ Sprint 6.7.8 | Complete | CI Integration Testing |
| ⏸️ Sprint 6.7.9 | Postponed | Production Smoke Testing |
| ⏸️ Sprint 6.7.10 | Postponed | ETL Automation Verification |
| ⏸️ Sprint 6.7.11 | Postponed | Regression & Final Validation |
| 🚧 Sprint 6.8 | Upcoming | Production Hardening & Documentation → **v1.0.0** |

> **Postponement note:** Sprints 6.7.9 – 6.7.11 are deferred until the Neon free-tier 5 GB storage refreshes next month. They will be resumed before the final release audit in Sprint 6.8.

> **End of roadmap:** Sprint 6.8 is the final planned sprint. After `v1.0.0`, work transitions to post-release maintenance driven by real defects, operational observations, and user feedback — not by extending the sprint plan.

---

## Completed Sprints

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
2. **Single Source of Truth** - `classifier.py` with `classify_result()` used by both production and validation
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

**Goal:** Replace uncontrolled acquisition (0.4% tech) with a balanced two-stream strategy achieving ~50% tech / ~50% non-tech.

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

**Query-Level Adaptation:**
| Batch | Query | Intent | Tech | Non-Tech | Adaptation |
|-------|-------|--------|------|----------|------------|
| 1 | software engineer | Tech | 24 | 1 | Tech-heavy start |
| 2 | nurse | Broad | 0 | 25 | Switched to broad |
| 3 | software developer | Tech | 24 | 1 | Switched to tech |
| 4 | doctor | Broad | 0 | 25 | Switched to broad |

**Successfully achieved** the targeted broad labor-market dataset with ~50% technology representation.

---

## Sprint 6.7 — Integration & End-to-End Testing

Sprint 6.7 validated that the complete platform works correctly as one integrated, production-like system — spanning PostgreSQL → ETL → enrichment → classification → analytics → API → dashboard → deployment.

The sprint was divided into 11 mini-sprints (validation stages, not feature work). Eight were completed; three were postponed due to Neon free-tier storage constraints.

### ✅ Sprint 6.7.1 — Integration Test Infrastructure

**Goal:** Establish a reliable environment in which integration tests can execute against real PostgreSQL.

- PostgreSQL test environment (`localhost:15432`)
- Dedicated test database: `job_market_intelligence_test`
- `TEST_DATABASE_URL` configuration
- Test isolation via transaction cleanup
- Replaced SQLite in-memory with PostgreSQL-backed engine
- Proper test fixtures (non-null `language` field)
- Verified Alembic migrations and test teardown

### ✅ Sprint 6.7.2 — PostgreSQL Integration

**Goal:** Verify persistence layer behavior against actual production database technology.

- Schema fixes: added `tech_confidence`, `matched_tech_terms` columns
- Alembic migration `74b5dc797be3`
- Check constraint: `ck_job_tech_confidence`
- Migrated test database to head
- Fixed ETL transaction/session lifecycle (`SessionLocal()` ownership)
- Verified connectivity, models, repositories, relationships, JSONB, transactions, upserts, duplicate handling, retention

### ✅ Sprint 6.7.3 — ETL Integration

**Goal:** Validate the complete ingestion pipeline as one integrated workflow.

- Controlled extraction fixtures (deterministic, no live Adzuna dependency)
- Transformation, enrichment, classification verified
- Skills, technology classification, country/currency normalization verified
- Validation: valid records accepted, invalid rejected
- Loading: inserts, updates, duplicates, commit, rollback
- Pipeline metrics internally consistent
- Failure handling verified — no partial commits

### ✅ Sprint 6.7.4 — API Integration

**Goal:** Verify FastAPI works against real PostgreSQL data.

- Jobs API: pagination, ordering, search, filters (country, category, salary, skills)
- Invalid parameters and nonexistent job handling
- Analytics API: country, company, skills, salary (avg/min/max/ranges/currency), technology, trends
- Health endpoints
- Error handling

### ✅ Sprint 6.7.5 — Analytics Integration

**Goal:** Verify analytical layer independently and through the API.

- Deterministic test data with known expected outputs (e.g., 10 jobs: US=4, GB=3, DE=2, CA=1)
- Aggregations verified for correctness, not just endpoint availability
- Empty dataset handling
- Filter interaction behavior

### ✅ Sprint 6.7.6 — Dashboard Integration

**Goal:** Verify Streamlit → FastAPI → PostgreSQL without replacing the API with mocks.

- Overview: total jobs, companies, countries, skills, salary, recent jobs
- Job Explorer: search, filters, pagination, job details
- Analytics: countries, skills, salary, technology, trends
- API failure handling — meaningful error state, no crash
- Empty data handling — meaningful empty state, no Python exception/blank screen

### ✅ Sprint 6.7.7 — End-to-End Workflows

**Goal:** Validate the complete application as a system.

Four E2E workflows verified:

1. **ETL → Database** — records inserted, fields/enrichment/classification/skills persisted
2. **Database → API** — jobs retrieved, filters applied, analytics calculated, expected values returned
3. **API → Dashboard** — dashboard loads, jobs appear, filters work, analytics appear
4. **Complete User Journey** — test data → ETL → PostgreSQL → FastAPI → job search → filtering → job details → analytics → dashboard

Existing E2E suite reviewed and converted from placeholders where technically practical.

### ✅ Sprint 6.7.8 — CI Integration Testing

**Goal:** Extend the existing CI pipeline so integration validation happens automatically.

- Integration tests run in CI
- PostgreSQL service
- Alembic migration execution
- Coverage generation
- Failure propagation (no `pytest || true`, no silent failures)
- Docker validation

### ⏸️ Sprint 6.7.9 — Production Smoke Testing *(Postponed)*

Deferred until Neon free-tier storage refreshes next month.

Planned scope:
- Production API smoke tests (`/api/v1/health`, `/api/v1/jobs`, analytics endpoints, Swagger)
- Database verification (connectivity, current schema, recent ETL data, expected tables, recent pipeline activity)
- Dashboard verification (homepage, Job Explorer, Analytics, API connectivity)
- Non-destructive only — no DELETE/UPDATE/INSERT against production

### ⏸️ Sprint 6.7.10 — ETL Automation Verification *(Postponed)*

Deferred until Neon free-tier storage refreshes next month.

Planned scope:
- Verify GitHub Actions scheduled ETL integrates with production
- Workflow startup, secrets availability, dependency install
- Database connection, ETL completion, record updates
- Pipeline metrics generated, failure visibility
- Dashboard reflects updated data

### ⏸️ Sprint 6.7.11 — Regression & Final Validation *(Postponed)*

Deferred until Neon free-tier storage refreshes next month.

Planned scope:
- Defect closure stage after all previous mini-sprints
- Every defect: reproduce → identify root cause → fix → regression test → relevant suite → full suite
- Full relevant test suite passes
- No known critical integration defects remain

### 📊 Sprint 6.7 Integration Test Results

```text
test_etl_pipeline.py          3 passed
test_analytics_pipeline.py   11 passed
test_api.py                   5 passed
test_dashboard_api.py        44 passed
─────────────────────────────────────
Total:                        74 passed
Warnings:                     2 (dependency/deprecation cleanup)