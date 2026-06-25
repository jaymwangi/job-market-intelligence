# Job Market Intelligence

## Architecture Document

### Version

v1.0

---

# 1. Architecture Overview

Job Market Intelligence follows a layered architecture that separates:

* Data Collection
* Data Processing
* Data Storage
* Business Logic
* API Access
* User Interface

This separation improves:

* Maintainability
* Testability
* Scalability
* Reliability

---

# 2. High-Level System Architecture

```text
External Data Sources
          │
          ▼
    ETL Pipeline
          │
          ▼
      Validation
          │
          ▼
   Transformation
          │
          ▼
     PostgreSQL
          │
          ▼
   Repository Layer
          │
          ▼
   Analytics Services
          │
          ▼
       FastAPI
          │
          ▼
   Streamlit Dashboard
```

---

# 3. Architectural Principles

## Principle 1: Separation of Concerns

Each layer performs one responsibility.

Example:

```text
ETL Layer
    Collects Data

Repository Layer
    Accesses Data

Analytics Layer
    Generates Insights

API Layer
    Exposes Data

Dashboard Layer
    Displays Data
```

---

## Principle 2: Single Responsibility

Every component should have one reason to change.

Example:

```text
SkillAnalyticsService

Responsible ONLY for skill analytics.
```

Not:

```text
SkillAnalyticsService

Analytics
Database Access
UI Logic
```

---

## Principle 3: Dependency Direction

Dependencies must flow downward.

```text
Dashboard
    ↓

API
    ↓

Services
    ↓

Repositories
    ↓

Database
```

Lower layers must never depend on higher layers.

---

## Principle 4: Explicit Data Flow

Data movement should always be visible and traceable.

No hidden side effects.

No global state.

---

# 4. Data Flow Architecture

## ETL Flow

```text
Job Source
    ↓

Extract
    ↓

Validate
    ↓

Transform
    ↓

Load
    ↓

PostgreSQL
```

---

## Analytics Flow

```text
Dashboard Request
        ↓

FastAPI Endpoint
        ↓

Analytics Service
        ↓

Repository
        ↓

PostgreSQL
        ↓

Analytics Result
        ↓

Dashboard
```

---

# 5. Component Architecture

## ETL Layer

Purpose:

Collect and prepare job market data.

Responsibilities:

* Extract raw data
* Validate records
* Clean data
* Normalize fields
* Load into database

Directory:

```text
etl/
```

Modules:

```text
extract/
transform/
load/
```

---

## Database Layer

Purpose:

Persist processed job data.

Technology:

PostgreSQL

Responsibilities:

* Store jobs
* Store skills
* Store analytics data
* Store pipeline metadata

---

## Repository Layer

Purpose:

Provide database access abstraction.

Responsibilities:

* Query database
* Create records
* Update records
* Aggregate data

Directory:

```text
repositories/
```

Example:

```text
JobRepository
SkillRepository
PipelineRepository
```

Rule:

Repositories contain SQL/database logic only.

---

## Service Layer

Purpose:

Implement business logic.

Responsibilities:

* Analytics calculations
* Trend generation
* KPI calculations

Directory:

```text
services/
```

Examples:

```text
SkillAnalyticsService
SalaryAnalyticsService
LocationAnalyticsService
JobAnalyticsService
```

Rule:

Services never directly access the database.

Services use repositories.

---

## API Layer

Purpose:

Expose system functionality.

Technology:

FastAPI

Directory:

```text
api/
```

Responsibilities:

* Receive requests
* Validate requests
* Call services
* Return responses

Example Endpoints:

```text
/health

/jobs

/skills/top

/locations/top

/salary/stats
```

Rule:

No business logic inside routes.

---

## Dashboard Layer

Purpose:

Visualize insights.

Technology:

Streamlit

Directory:

```text
dashboard/
```

Pages:

```text
Overview

Skills

Locations

Salaries

Pipeline Status
```

Responsibilities:

* Display charts
* Display KPIs
* Apply filters
* Consume API data

Rule:

Dashboard never talks directly to PostgreSQL.

Dashboard communicates through FastAPI.

---

# 6. Project Structure

```text
job-market-intelligence/

├── app/
│
├── api/
│   ├── routes/
│   └── dependencies/
│
├── etl/
│   ├── extract/
│   ├── transform/
│   └── load/
│
├── repositories/
│
├── services/
│
├── models/
│
├── dashboard/
│
├── config/
│
├── tests/
│
├── docs/
│
├── scripts/
│
├── logs/
│
├── data/
│
├── .env
│
├── requirements.txt
│
└── README.md
```

---

# 7. Event Flow

Example:

User opens dashboard.

```text
Dashboard
    ↓

GET /skills/top

    ↓

FastAPI Route

    ↓

SkillAnalyticsService

    ↓

SkillRepository

    ↓

PostgreSQL

    ↓

Results Returned
```

---

# 8. Error Handling Strategy

Errors must be handled at layer boundaries.

Examples:

## ETL Errors

```text
Bad Record
Missing Fields
Invalid Salary
```

Action:

* Log error
* Skip record
* Continue processing

---

## Database Errors

```text
Connection Failure
Constraint Violation
```

Action:

* Log exception
* Return safe response

---

## API Errors

```text
Invalid Parameters
Missing Resources
```

Action:

* Return meaningful HTTP status codes

---

# 9. Logging Architecture

Logs should capture:

## ETL

```text
Records Extracted
Records Loaded
Pipeline Duration
Pipeline Failures
```

---

## API

```text
Request Count
Response Time
Errors
```

---

## Analytics

```text
Query Execution Time
Heavy Operations
```

---

# 10. Testing Architecture

## Unit Tests

Test:

```text
Transformations
Validators
Analytics Logic
```

---

## Integration Tests

Test:

```text
ETL → Database

Repository → Database

API → Services
```

---

## End-to-End Tests

Test:

```text
Data Collection
↓
Database
↓
API
↓
Dashboard
```

---

# 11. Security Architecture

Requirements:

* Environment variables for secrets
* Input validation
* SQL injection protection via ORM
* Dependency management
* Rate limiting (future)

---

# 12. Scalability Considerations

Future improvements may include:

```text
Scheduled ETL Jobs

Caching

Background Workers

Additional Data Sources

Data Warehouse Layer
```

These are not required for v1.

---

# 13. Architecture Constraints

The system must:

* Remain modular
* Use repository pattern
* Use service layer pattern
* Avoid business logic in routes
* Avoid direct database access from dashboard
* Avoid global mutable state

---

# 14. Definition of Good Architecture

A new developer should be able to understand:

* Data flow
* Component responsibilities
* Dependency relationships

within one day.

If this is not possible:

```text
The architecture is too complex.
```

---

End of Architecture Document
