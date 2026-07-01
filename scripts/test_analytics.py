#!/usr/bin/env python
"""
Test Script for Analytics Repository

This script tests all analytics queries against the database.
It displays results in a readable format and handles empty databases gracefully.
"""

import sys
from pathlib import Path
from typing import Optional, List, Tuple, Any, Dict

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.repositories.analytics_repository import AnalyticsRepository


def format_number(num):
    """Format numbers with commas for readability."""
    if num is None:
        return "N/A"
    if isinstance(num, (int, float)):
        return f"{num:,.0f}" if num == int(num) else f"{num:,.2f}"
    return str(num)


def format_currency(amount):
    """Format currency values with £ symbol."""
    if amount is None:
        return "N/A"
    return f"£{format_number(amount)}"


def print_results(title: str, rows: List[Tuple[Any, int]], col1_width: int = 30, empty_message: Optional[str] = None):
    """
    Print formatted results with two columns.
    
    Args:
        title: Section title
        rows: List of tuples (label, value)
        col1_width: Width of the first column
        empty_message: Custom message when no data is available
    """
    print(f"\n{'='*10} {title} {'='*10}")
    
    if not rows:
        default_messages = {
            "TOP SKILLS": "No skill relationships have been loaded yet.",
            "TOP COMPANIES": "No companies found in the current dataset.",
            "JOBS BY LOCATION": "No location information found in the current dataset.",
            "EMPLOYMENT TYPE DISTRIBUTION": "No employment type information found in the current dataset.",
        }
        message = empty_message or default_messages.get(title, "No data available")
        print(message)
        return
    
    for label, value in rows:
        print(f"{str(label):<{col1_width}} {format_number(value)}")


def print_salary_results(title: str, rows: List[Tuple[str, float]], col1_width: int = 30, empty_message: Optional[str] = None):
    """
    Print formatted salary results with currency formatting.
    
    Args:
        title: Section title
        rows: List of tuples (label, salary_value)
        col1_width: Width of the first column
        empty_message: Custom message when no data is available
    """
    print(f"\n{'='*10} {title} {'='*10}")
    
    if not rows:
        message = empty_message or "No salary data available."
        print(message)
        return
    
    for label, value in rows:
        print(f"{str(label):<{col1_width}} {format_currency(value)}")


def print_salary_statistics(stats: Dict[str, Optional[float]]):
    """Print salary statistics in a formatted way."""
    print("\n" + "="*10 + " SALARY STATISTICS " + "="*10)
    
    if stats["avg_min"] is None and stats["avg_max"] is None:
        print("No salary information found in the current dataset.")
        return
    
    labels = [
        ("Average Min Salary", stats["avg_min"]),
        ("Average Max Salary", stats["avg_max"]),
        ("Minimum Salary", stats["min_salary"]),
        ("Maximum Salary", stats["max_salary"])
    ]
    
    max_label_len = max(len(label) for label, _ in labels if label)
    
    for label, value in labels:
        if value is not None:
            print(f"{label:<{max_label_len + 2}}: {format_currency(value)}")
        else:
            print(f"{label:<{max_label_len + 2}}: No data available for this metric")


def print_salary_distribution(stats: Dict[str, Optional[float]]):
    """Print comprehensive salary distribution statistics."""
    print("\n" + "="*10 + " SALARY DISTRIBUTION " + "="*10)
    
    if stats["average_salary"] is None:
        print("No salary data available for distribution analysis.")
        return
    
    labels = [
        ("Average Salary", stats["average_salary"]),
        ("Minimum Salary", stats["min_salary"]),
        ("Maximum Salary", stats["max_salary"]),
        ("Salary Records", stats["salary_records"])
    ]
    
    max_label_len = max(len(label) for label, _ in labels if label)
    
    for label, value in labels:
        if label == "Salary Records":
            print(f"{label:<{max_label_len + 2}}: {format_number(value)}")
        elif value is not None:
            print(f"{label:<{max_label_len + 2}}: {format_currency(value)}")
        else:
            print(f"{label:<{max_label_len + 2}}: No data")


def print_recent_jobs(jobs: List, days: int):
    """
    Print recent jobs in a formatted table.
    
    Args:
        jobs: List of Job ORM objects
        days: Number of days used in the query
    """
    print(f"\n{'='*10} RECENT JOBS (last {days} days) {'='*10}")
    
    if not jobs:
        print(f"No jobs found in the last {days} days.")
        return
    
    print(f"Total: {len(jobs)} jobs")
    print("\n" + "-" * 80)
    print(f"{'Title':<40} {'Company':<20} {'Location':<20}")
    print("-" * 80)
    
    for job in jobs:
        title = job.title[:37] + "..." if len(job.title) > 40 else job.title
        company = job.company_name[:17] + "..." if len(job.company_name) > 20 else job.company_name
        location = job.location[:17] + "..." if job.location and len(job.location) > 20 else job.location or "Unknown"
        print(f"{title:<40} {company:<20} {location:<20}")


def print_dataset_summary(repo: AnalyticsRepository):
    """
    Print a summary of the dataset to help understand what data is available.
    
    Args:
        repo: AnalyticsRepository instance
    """
    from app.models.job import Job
    from app.models.job_skill import JobSkill
    
    print("\n" + "="*10 + " DATASET SUMMARY " + "="*10)
    
    # Count total jobs
    total_jobs = repo.db.query(Job).count()
    print(f"Total jobs in database: {total_jobs:,}")
    
    if total_jobs == 0:
        print("\nNo jobs found in the database.")
        return
    
    # Count jobs with various fields populated
    jobs_with_company = repo.db.query(Job).filter(Job.company_name.isnot(None)).count()
    jobs_with_location = repo.db.query(Job).filter(Job.location.isnot(None)).count()
    jobs_with_salary = repo.db.query(Job).filter(Job.salary_min.isnot(None)).count()
    jobs_with_employment = repo.db.query(Job).filter(Job.employment_type.isnot(None)).count()
    jobs_with_date = repo.db.query(Job).filter(Job.posted_date.isnot(None)).count()
    
    # Calculate percentages
    def pct(count):
        return (count / total_jobs * 100) if total_jobs > 0 else 0
    
    print("\n📋 Field Coverage:")
    print(f"  Company name     : {jobs_with_company:>5,} / {total_jobs:,} ({pct(jobs_with_company):>5.1f}%)")
    print(f"  Location         : {jobs_with_location:>5,} / {total_jobs:,} ({pct(jobs_with_location):>5.1f}%)")
    print(f"  Salary data      : {jobs_with_salary:>5,} / {total_jobs:,} ({pct(jobs_with_salary):>5.1f}%)")
    print(f"  Employment type  : {jobs_with_employment:>5,} / {total_jobs:,} ({pct(jobs_with_employment):>5.1f}%)")
    print(f"  Posted date      : {jobs_with_date:>5,} / {total_jobs:,} ({pct(jobs_with_date):>5.1f}%)")
    
    # Skill coverage
    skill_links = repo.db.query(JobSkill).count()
    print(f"\n🔗 Skill Coverage:")
    print(f"  Skill-job relationships: {skill_links:,}")
    if total_jobs > 0:
        avg_skills = skill_links / total_jobs
        print(f"  Average skills per job : {avg_skills:.1f}")


def test_analytics():
    """Main test function to execute all analytics queries."""
    
    print("🚀 Starting Analytics Repository Test")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        
        try:
            repo = AnalyticsRepository(db)
            
            # Sprint 3.1 Queries
            print_results("TOP SKILLS", repo.get_top_skills())
            print_results("TOP COMPANIES", repo.get_top_companies())
            print_results("JOBS BY LOCATION", repo.get_jobs_by_location())
            print_salary_statistics(repo.get_salary_statistics())
            print_results("EMPLOYMENT TYPE DISTRIBUTION", repo.get_employment_type_distribution())
            
            # Sprint 3.2 Queries
            print_salary_results("SALARY BY LOCATION", repo.get_salary_by_location())
            print_salary_results("SALARY BY COMPANY", repo.get_salary_by_company())
            
            # Posting trend
            print("\n" + "="*10 + " POSTING TREND " + "="*10)
            trend_data = repo.get_jobs_posted_by_date()
            if trend_data:
                for date, count in trend_data:
                    print(f"{date.strftime('%Y-%m-%d')} {count:>8,}")
            else:
                print("No posting date data available.")
            
            # Recent jobs
            recent_jobs = repo.get_recent_jobs(days=30, limit=20)
            print_recent_jobs(recent_jobs, 30)
            
            # Salary distribution
            print_salary_distribution(repo.get_salary_distribution())
            
            # Dataset summary
            print_dataset_summary(repo)
            
            print("\n" + "="*60)
            print("✅ Sprint 3.2 Complete ✓")
            print("="*60)
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_analytics()