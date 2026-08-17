"""Dashboard API endpoint definitions.

This module defines all API endpoints used by the dashboard,
matching the actual backend API structure.

Sprint 6.6 adds:
- Language analytics endpoints
- Technology analytics endpoints
- Enriched combined analytics endpoints
- Translation endpoint

Example:
    from dashboard.api.endpoints import endpoints
    
    # Get URL for top skills
    url = endpoints.TOP_SKILLS
"""


class Endpoints:
    """API endpoint definitions matching the actual API."""

    # ============================================================
    # Health
    # ============================================================
    HEALTH = "/api/v1/health"
    LIVE = "/api/v1/health/live"
    READY = "/api/v1/health/ready"

    # ============================================================
    # Jobs
    # ============================================================
    JOBS = "/api/v1/jobs"
    JOB_DETAIL = "/api/v1/jobs/{job_id}"
    
    # ============================================================
    # Sprint 6.6: Translation
    # ============================================================
    JOB_TRANSLATE = "/api/v1/jobs/{job_id}/translate"

    # ============================================================
    # Analytics - Top Lists
    # ============================================================
    TOP_SKILLS = "/api/v1/analytics/top-skills"
    TOP_COMPANIES = "/api/v1/analytics/top-companies"
    JOBS_BY_LOCATION = "/api/v1/analytics/jobs-by-location"

    # ============================================================
    # Analytics - Salary
    # ============================================================
    SALARY_STATISTICS = "/api/v1/analytics/salary-statistics"
    SALARY_BY_LOCATION = "/api/v1/analytics/salary-by-location"
    SALARY_BY_COMPANY = "/api/v1/analytics/salary-by-company"
    SALARY_DISTRIBUTION = "/api/v1/analytics/salary-distribution"

    # ============================================================
    # Analytics - Trends & Distribution
    # ============================================================
    EMPLOYMENT_TYPES = "/api/v1/analytics/employment-types"
    POSTING_TREND = "/api/v1/analytics/posting-trend"
    RECENT_JOBS = "/api/v1/analytics/recent-jobs"

    # ============================================================
    # Analytics - Summaries
    # ============================================================
    DATASET_SUMMARY = "/api/v1/analytics/dataset-summary"
    OVERVIEW = "/api/v1/analytics/overview"
    DASHBOARD_SUMMARY = "/api/v1/analytics/dashboard-summary"

    # ============================================================
    # Sprint 6.6: Language Analytics
    # ============================================================
    LANGUAGE_DISTRIBUTION = "/api/v1/analytics/language/distribution"
    LANGUAGE_BY_COUNTRY = "/api/v1/analytics/language/by-country"
    ENGLISH_VS_NON_ENGLISH = "/api/v1/analytics/language/english-vs-non-english"
    LANGUAGE_SALARY = "/api/v1/analytics/language/salary"

    # ============================================================
    # Sprint 6.6: Technology Analytics
    # ============================================================
    TECH_VS_NON_TECH = "/api/v1/analytics/tech/vs-non-tech"
    TECH_CATEGORY_DISTRIBUTION = "/api/v1/analytics/tech/category-distribution"
    TECH_BY_COUNTRY = "/api/v1/analytics/tech/by-country"
    TECH_SKILLS = "/api/v1/analytics/tech/skills"
    TECH_SALARY = "/api/v1/analytics/tech/salary"

    # ============================================================
    # Sprint 6.6: Enriched Combined Analytics (RESTful Resources)
    # ============================================================
    ENRICHED_SKILLS = "/api/v1/analytics/enriched/skills"
    ENRICHED_COUNTRIES = "/api/v1/analytics/enriched/countries"
    ENRICHED_TECHNOLOGY = "/api/v1/analytics/enriched/technology"
    ENRICHED_SALARY = "/api/v1/analytics/enriched/salary"


# Singleton instance
endpoints = Endpoints()

# ============================================================
# Export constants for direct import
# ============================================================

# Health
HEALTH = endpoints.HEALTH
LIVE = endpoints.LIVE
READY = endpoints.READY

# Jobs
JOBS = endpoints.JOBS
JOB_DETAIL = endpoints.JOB_DETAIL

# Sprint 6.6: Translation
JOB_TRANSLATE = endpoints.JOB_TRANSLATE

# Analytics - Top Lists
TOP_SKILLS = endpoints.TOP_SKILLS
TOP_COMPANIES = endpoints.TOP_COMPANIES
JOBS_BY_LOCATION = endpoints.JOBS_BY_LOCATION

# Analytics - Salary
SALARY_STATISTICS = endpoints.SALARY_STATISTICS
SALARY_BY_LOCATION = endpoints.SALARY_BY_LOCATION
SALARY_BY_COMPANY = endpoints.SALARY_BY_COMPANY
SALARY_DISTRIBUTION = endpoints.SALARY_DISTRIBUTION

# Analytics - Trends & Distribution
EMPLOYMENT_TYPES = endpoints.EMPLOYMENT_TYPES
POSTING_TREND = endpoints.POSTING_TREND
RECENT_JOBS = endpoints.RECENT_JOBS

# Analytics - Summaries
DATASET_SUMMARY = endpoints.DATASET_SUMMARY
OVERVIEW = endpoints.OVERVIEW
DASHBOARD_SUMMARY = endpoints.DASHBOARD_SUMMARY

# Sprint 6.6: Language Analytics
LANGUAGE_DISTRIBUTION = endpoints.LANGUAGE_DISTRIBUTION
LANGUAGE_BY_COUNTRY = endpoints.LANGUAGE_BY_COUNTRY
ENGLISH_VS_NON_ENGLISH = endpoints.ENGLISH_VS_NON_ENGLISH
LANGUAGE_SALARY = endpoints.LANGUAGE_SALARY

# Sprint 6.6: Technology Analytics
TECH_VS_NON_TECH = endpoints.TECH_VS_NON_TECH
TECH_CATEGORY_DISTRIBUTION = endpoints.TECH_CATEGORY_DISTRIBUTION
TECH_BY_COUNTRY = endpoints.TECH_BY_COUNTRY
TECH_SKILLS = endpoints.TECH_SKILLS
TECH_SALARY = endpoints.TECH_SALARY

# Sprint 6.6: Enriched Combined Analytics
ENRICHED_SKILLS = endpoints.ENRICHED_SKILLS
ENRICHED_COUNTRIES = endpoints.ENRICHED_COUNTRIES
ENRICHED_TECHNOLOGY = endpoints.ENRICHED_TECHNOLOGY
ENRICHED_SALARY = endpoints.ENRICHED_SALARY