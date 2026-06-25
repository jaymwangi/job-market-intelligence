# Job Market Intelligence

## API Contract Document

### Version

v1.0

---

# 1. Overview

This document defines the public API contract for Job Market Intelligence.

The API provides access to:

* System health information
* Job market analytics
* Skills analytics
* Location analytics
* Salary analytics
* Pipeline monitoring

Technology:

* FastAPI
* REST Architecture
* JSON Responses

Base URL:

```text
/api/v1
```

---

# 2. API Design Principles

## Consistent Responses

All endpoints return JSON.

---

## Clear Status Codes

Examples:

```text
200 OK
201 Created
400 Bad Request
404 Not Found
500 Internal Server Error
```

---

## Validation First

All request parameters must be validated before processing.

---

## Versioned API

Versioning strategy:

```text
/api/v1
/api/v2
```

Future changes should not break existing clients.

---

# 3. Standard Response Format

## Success Response

```json
{
  "success": true,
  "data": {},
  "message": "Request completed successfully"
}
```

---

## Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request"
  }
}
```

---

# 4. Health Endpoints

## GET /health

Purpose:

Verify API availability.

### Request

```http
GET /api/v1/health
```

### Response

```json
{
  "success": true,
  "data": {
    "status": "healthy"
  }
}
```

### Status Codes

```text
200 OK
500 Internal Server Error
```

---

## GET /health/database

Purpose:

Verify database connectivity.

### Response

```json
{
  "success": true,
  "data": {
    "database": "connected"
  }
}
```

---

# 5. Jobs Endpoints

## GET /jobs

Purpose:

Retrieve job postings.

---

### Query Parameters

| Parameter   | Type    | Required |
| ----------- | ------- | -------- |
| page        | integer | No       |
| page_size   | integer | No       |
| role        | string  | No       |
| skill       | string  | No       |
| location    | string  | No       |
| remote_type | string  | No       |

---

### Example Request

```http
GET /api/v1/jobs?skill=Python
```

---

### Response

```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "uuid",
        "title": "Data Engineer",
        "company": "Example Corp",
        "location": "Berlin",
        "remote_type": "HYBRID"
      }
    ]
  }
}
```

---

## GET /jobs/{job_id}

Purpose:

Retrieve a specific job.

### Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Data Engineer",
    "company": "Example Corp",
    "location": "Berlin",
    "description": "..."
  }
}
```

---

# 6. Skills Analytics Endpoints

## GET /skills/top

Purpose:

Return most requested skills.

### Query Parameters

| Parameter | Type    | Required |
| --------- | ------- | -------- |
| limit     | integer | No       |

Default:

```text
10
```

---

### Example Request

```http
GET /api/v1/skills/top?limit=10
```

---

### Response

```json
{
  "success": true,
  "data": [
    {
      "skill": "Python",
      "count": 1542
    },
    {
      "skill": "SQL",
      "count": 1410
    }
  ]
}
```

---

## GET /skills/search

Purpose:

Search skills.

### Query Parameters

| Parameter | Type   |
| --------- | ------ |
| query     | string |

---

### Example Response

```json
{
  "success": true,
  "data": [
    "Python",
    "PySpark",
    "Pandas"
  ]
}
```

---

# 7. Location Analytics Endpoints

## GET /locations/top

Purpose:

Return locations with highest job demand.

---

### Query Parameters

| Parameter | Type    |
| --------- | ------- |
| limit     | integer |

---

### Response

```json
{
  "success": true,
  "data": [
    {
      "location": "Berlin",
      "count": 850
    },
    {
      "location": "Munich",
      "count": 720
    }
  ]
}
```

---

# 8. Salary Analytics Endpoints

## GET /salary/stats

Purpose:

Return salary statistics.

---

### Query Parameters

| Parameter | Type   |
| --------- | ------ |
| role      | string |
| location  | string |

---

### Response

```json
{
  "success": true,
  "data": {
    "average_salary": 85000,
    "median_salary": 80000,
    "minimum_salary": 60000,
    "maximum_salary": 140000
  }
}
```

---

## GET /salary/distribution

Purpose:

Return salary distribution data.

---

### Response

```json
{
  "success": true,
  "data": [
    {
      "range": "50000-60000",
      "count": 125
    }
  ]
}
```

---

# 9. Remote Work Analytics Endpoints

## GET /analytics/remote

Purpose:

Analyze work arrangement trends.

---

### Response

```json
{
  "success": true,
  "data": {
    "remote": 42,
    "hybrid": 38,
    "onsite": 20
  }
}
```

Values represent percentages.

---

# 10. Job Trends Endpoints

## GET /analytics/jobs/trending

Purpose:

Return most common job titles.

---

### Query Parameters

| Parameter | Type    |
| --------- | ------- |
| limit     | integer |

---

### Response

```json
{
  "success": true,
  "data": [
    {
      "title": "Data Engineer",
      "count": 580
    },
    {
      "title": "Software Engineer",
      "count": 540
    }
  ]
}
```

---

# 11. Dashboard KPI Endpoints

## GET /analytics/overview

Purpose:

Return dashboard KPIs.

---

### Response

```json
{
  "success": true,
  "data": {
    "total_jobs": 15000,
    "total_skills": 250,
    "remote_percentage": 42,
    "average_salary": 85000
  }
}
```

---

# 12. Pipeline Monitoring Endpoints

## GET /pipeline/status

Purpose:

Return latest ETL status.

---

### Response

```json
{
  "success": true,
  "data": {
    "status": "SUCCESS",
    "last_run": "2026-06-25T09:00:00Z",
    "records_loaded": 1200
  }
}
```

---

## GET /pipeline/runs

Purpose:

Return ETL execution history.

---

### Query Parameters

| Parameter | Type    |
| --------- | ------- |
| limit     | integer |

---

### Response

```json
{
  "success": true,
  "data": [
    {
      "status": "SUCCESS",
      "records_loaded": 1200,
      "duration_seconds": 45
    }
  ]
}
```

---

# 13. Validation Rules

## Pagination

```text
page >= 1
page_size <= 100
```

---

## Limit

```text
1 <= limit <= 100
```

---

## Remote Type

Allowed values:

```text
REMOTE
HYBRID
ONSITE
UNKNOWN
```

---

# 14. Error Codes

## VALIDATION_ERROR

```json
{
  "code": "VALIDATION_ERROR"
}
```

---

## RESOURCE_NOT_FOUND

```json
{
  "code": "RESOURCE_NOT_FOUND"
}
```

---

## DATABASE_ERROR

```json
{
  "code": "DATABASE_ERROR"
}
```

---

## INTERNAL_SERVER_ERROR

```json
{
  "code": "INTERNAL_SERVER_ERROR"
}
```

---

# 15. API Security (v1)

Current Version:

```text
No Authentication
Read-Only Analytics API
```

Future Versions:

```text
API Keys
OAuth2
Rate Limiting
Role-Based Access
```

---

# 16. Definition of Done

The API contract is complete when:

* Every endpoint has a defined request structure
* Every endpoint has a defined response structure
* Validation rules are documented
* Error responses are standardized
* API versioning strategy is documented

---

End of API Contract Document
