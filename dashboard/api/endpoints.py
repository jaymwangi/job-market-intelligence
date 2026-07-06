class Endpoints:
    """API endpoint definitions matching the actual API."""

    # Health
    HEALTH = "/api/v1/health"

    # Jobs
    JOBS = "/api/v1/jobs"
    JOB_DETAIL = "/api/v1/jobs/{job_id}"

    # Analytics
    TOP_SKILLS = "/api/v1/analytics/top-skills"
    TOP_COMPANIES = "/api/v1/analytics/top-companies"
    JOBS_BY_LOCATION = "/api/v1/analytics/jobs-by-location"
    SALARY_STATISTICS = "/api/v1/analytics/salary-statistics"
    EMPLOYMENT_TYPES = "/api/v1/analytics/employment-types"
    SALARY_BY_LOCATION = "/api/v1/analytics/salary-by-location"
    SALARY_BY_COMPANY = "/api/v1/analytics/salary-by-company"
    POSTING_TREND = "/api/v1/analytics/posting-trend"
    RECENT_JOBS = "/api/v1/analytics/recent-jobs"
    SALARY_DISTRIBUTION = "/api/v1/analytics/salary-distribution"
    DATASET_SUMMARY = "/api/v1/analytics/dataset-summary"
    OVERVIEW = "/api/v1/analytics/overview"
    DASHBOARD_SUMMARY = "/api/v1/analytics/dashboard-summary"


endpoints = Endpoints()

# Export constants for direct import
HEALTH = endpoints.HEALTH
JOBS = endpoints.JOBS
JOB_DETAIL = endpoints.JOB_DETAIL
