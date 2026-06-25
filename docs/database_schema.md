# Job Market Intelligence

## Database Schema Document

### Version

v1.0

---

# 1. Overview

The database is responsible for storing:

* Job postings
* Skills
* Job-to-skill relationships
* ETL pipeline execution history

Database Technology:

PostgreSQL

Design Goals:

* Simplicity
* Data integrity
* Query performance
* Analytics support
* Future extensibility

---

# 2. Entity Relationship Diagram (ERD)

```text
jobs
  │
  │ many-to-many
  │
job_skills
  │
  │
skills


pipeline_runs
```

---

# 3. Tables

## jobs

Stores normalized job posting information.

### Columns

| Column        | Type         | Constraints |
| ------------- | ------------ | ----------- |
| id            | UUID         | PK          |
| title         | VARCHAR(255) | NOT NULL    |
| company       | VARCHAR(255) | NOT NULL    |
| location      | VARCHAR(255) | NOT NULL    |
| remote_type   | VARCHAR(20)  | NOT NULL    |
| salary_min    | INTEGER      | NULL        |
| salary_max    | INTEGER      | NULL        |
| currency      | VARCHAR(10)  | NULL        |
| description   | TEXT         | NOT NULL    |
| source        | VARCHAR(100) | NOT NULL    |
| source_job_id | VARCHAR(255) | NOT NULL    |
| posted_date   | DATE         | NULL        |
| created_at    | TIMESTAMP    | NOT NULL    |
| updated_at    | TIMESTAMP    | NOT NULL    |

---

### Business Rules

remote_type values:

```text
REMOTE
HYBRID
ONSITE
UNKNOWN
```

source examples:

```text
ADZUNA
LINKEDIN
CSV
MANUAL
```

---

### Uniqueness Constraint

Prevent duplicate jobs.

```text
(source, source_job_id)
```

Must be unique.

---

# 4. skills

Stores normalized skill names.

### Columns

| Column     | Type         | Constraints |
| ---------- | ------------ | ----------- |
| id         | UUID         | PK          |
| name       | VARCHAR(100) | UNIQUE      |
| created_at | TIMESTAMP    | NOT NULL    |

---

### Examples

```text
Python
SQL
Docker
AWS
FastAPI
Spark
TensorFlow
```

---

# 5. job_skills

Many-to-many relationship table.

One job can require many skills.

One skill can appear in many jobs.

---

### Columns

| Column   | Type | Constraints  |
| -------- | ---- | ------------ |
| job_id   | UUID | FK jobs.id   |
| skill_id | UUID | FK skills.id |

---

### Composite Primary Key

```text
(job_id, skill_id)
```

Prevents duplicate mappings.

---

# 6. pipeline_runs

Tracks ETL execution history.

Provides observability and monitoring.

---

### Columns

| Column            | Type        | Constraints |
| ----------------- | ----------- | ----------- |
| id                | UUID        | PK          |
| started_at        | TIMESTAMP   | NOT NULL    |
| completed_at      | TIMESTAMP   | NULL        |
| status            | VARCHAR(20) | NOT NULL    |
| records_extracted | INTEGER     | DEFAULT 0   |
| records_loaded    | INTEGER     | DEFAULT 0   |
| records_failed    | INTEGER     | DEFAULT 0   |
| duration_seconds  | INTEGER     | NULL        |
| error_message     | TEXT        | NULL        |

---

### Status Values

```text
RUNNING
SUCCESS
FAILED
PARTIAL_SUCCESS
```

---

# 7. Index Strategy

Indexes improve analytics performance.

---

## jobs

Create indexes on:

```text
title
location
remote_type
posted_date
created_at
```

---

## skills

Create index on:

```text
name
```

---

## job_skills

Create indexes on:

```text
job_id
skill_id
```

---

## pipeline_runs

Create indexes on:

```text
started_at
status
```

---

# 8. Constraints

## Salary Validation

salary_min:

```text
>= 0
```

salary_max:

```text
>= salary_min
```

---

## Skill Name Validation

Skill names:

```text
NOT NULL
TRIMMED
UNIQUE
```

---

## Required Job Fields

Required:

```text
title
company
location
description
source
source_job_id
remote_type
```

---

# 9. Data Normalization Rules

## Skills

Normalize:

```text
python
PYTHON
Python
```

to:

```text
Python
```

---

## Remote Status

Normalize:

```text
Remote
remote
REMOTE
```

to:

```text
REMOTE
```

---

## Empty Values

Convert:

```text
N/A
Unknown
Blank
```

to:

```text
NULL
```

where appropriate.

---

# 10. Analytics Supported

This schema supports:

### Top Skills

```sql
Count skill occurrences
```

---

### Top Locations

```sql
Count jobs by location
```

---

### Salary Analytics

```sql
Average salary
Median salary
Salary ranges
```

---

### Remote Work Analytics

```sql
Remote vs Hybrid vs Onsite
```

---

### Job Trends

```sql
Jobs by title
Jobs by posting date
```

---

# 11. Future Expansion

Not included in v1.

Possible future tables:

```text
companies
countries
cities
salary_snapshots
job_categories
trend_snapshots
users
```

These should only be added when justified by requirements.

---

# 12. Design Decisions

## Why UUIDs?

Benefits:

* Globally unique
* Safe for distributed systems
* Easy future scaling

---

## Why Separate Skills?

Benefits:

* Avoid duplication
* Easier analytics
* Better normalization

---

## Why Track Pipeline Runs?

Benefits:

* Monitoring
* Debugging
* Observability
* Reliability metrics

---

# 13. Definition of a Valid Job Record

A valid job record must contain:

```text
Title
Company
Location
Description
Source
Source Job ID
Remote Type
```

Optional:

```text
Salary
Posted Date
Currency
```

Records that fail validation should not be loaded.

---

End of Database Schema Document
