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
            print(f"{label:<{max_label_len + 2}}: {format_number(value)}")
        else:
            print(f"{label:<{max_label_len + 2}}: No data available for this metric")


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
    
    # Calculate percentages
    def pct(count):
        return (count / total_jobs * 100) if total_jobs > 0 else 0
    
    print("\n📋 Field Coverage:")
    print(f"  Company name     : {jobs_with_company:>5,} / {total_jobs:,} ({pct(jobs_with_company):>5.1f}%)")
    print(f"  Location         : {jobs_with_location:>5,} / {total_jobs:,} ({pct(jobs_with_location):>5.1f}%)")
    print(f"  Salary data      : {jobs_with_salary:>5,} / {total_jobs:,} ({pct(jobs_with_salary):>5.1f}%)")
    print(f"  Employment type  : {jobs_with_employment:>5,} / {total_jobs:,} ({pct(jobs_with_employment):>5.1f}%)")
    
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
    print("-" * 50)
    
    try:
        db = SessionLocal()
        
        try:
            repo = AnalyticsRepository(db)
            
            # Execute all queries with descriptive empty messages
            print_results("TOP SKILLS", repo.get_top_skills())
            print_results("TOP COMPANIES", repo.get_top_companies())
            print_results("JOBS BY LOCATION", repo.get_jobs_by_location())
            print_salary_statistics(repo.get_salary_statistics())
            print_results("EMPLOYMENT TYPE DISTRIBUTION", repo.get_employment_type_distribution())
            
            # Add dataset summary (diagnostic, not prescriptive)
            print_dataset_summary(repo)
            
            print("\n" + "="*50)
            print("✅ Analytics test completed successfully!")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_analytics()