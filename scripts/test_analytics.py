#!/usr/bin/env python
"""
Test Script for Analytics Repository

This script tests all analytics queries against the database.
It displays results in a readable format and handles empty databases gracefully.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService


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


def print_results(title, rows, col1_width=30):
    """Print formatted results with two columns."""
    print(f"\n{'='*10} {title} {'='*10}")
    if not rows:
        print("No data available.")
        return
    for label, value in rows:
        print(f"{str(label):<{col1_width}} {format_number(value)}")


def print_salary_results(title, rows, col1_width=30):
    """Print formatted salary results with currency formatting."""
    print(f"\n{'='*10} {title} {'='*10}")
    if not rows:
        print("No salary data available.")
        return
    for label, value in rows:
        print(f"{str(label):<{col1_width}} {format_currency(value)}")


def print_salary_statistics(stats):
    """Print salary statistics in a formatted way."""
    print("\n" + "="*10 + " SALARY STATISTICS " + "="*10)
    if stats["avg_min"] is None:
        print("No salary data available.")
        return
    
    labels = [
        ("Average Min Salary", stats["avg_min"]),
        ("Average Max Salary", stats["avg_max"]),
        ("Minimum Salary", stats["min_salary"]),
        ("Maximum Salary", stats["max_salary"])
    ]
    max_label_len = max(len(label) for label, _ in labels)
    for label, value in labels:
        print(f"{label:<{max_label_len + 2}}: {format_currency(value)}")


def print_salary_distribution(stats):
    """Print comprehensive salary distribution statistics."""
    print("\n" + "="*10 + " SALARY DISTRIBUTION " + "="*10)
    if stats["average_salary"] is None:
        print("No salary data available.")
        return
    
    labels = [
        ("Average Salary", stats["average_salary"]),
        ("Minimum Salary", stats["min_salary"]),
        ("Maximum Salary", stats["max_salary"]),
        ("Salary Records", stats["salary_records"])
    ]
    max_label_len = max(len(label) for label, _ in labels)
    for label, value in labels:
        if label == "Salary Records":
            print(f"{label:<{max_label_len + 2}}: {format_number(value)}")
        else:
            print(f"{label:<{max_label_len + 2}}: {format_currency(value)}")


def print_recent_jobs(jobs, days):
    """Print recent jobs in a formatted table."""
    print(f"\n{'='*10} RECENT JOBS (last {days} days) {'='*10}")
    if not jobs:
        print(f"No jobs found in the last {days} days.")
        return
    
    print(f"Total: {len(jobs)} jobs")
    print("\n" + "-" * 80)
    print(f"{'Title':<40} {'Company':<20} {'Location':<20}")
    print("-" * 80)
    
    for job in jobs[:10]:
        title = job.title[:37] + "..." if len(job.title) > 40 else job.title
        company = job.company_name[:17] + "..." if len(job.company_name) > 20 else job.company_name
        location = job.location[:17] + "..." if job.location and len(job.location) > 20 else job.location or "Unknown"
        print(f"{title:<40} {company:<20} {location:<20}")
    
    if len(jobs) > 10:
        print(f"\n... and {len(jobs) - 10} more jobs")


def print_dataset_summary(repo):
    """Print a summary of the dataset using repository methods."""
    print("\n" + "="*10 + " DATASET SUMMARY " + "="*10)
    
    total_jobs = repo.get_total_jobs()
    print(f"Total jobs: {total_jobs:,}")
    
    if total_jobs == 0:
        print("No jobs found.")
        return
    
    jobs_with_company = repo.get_jobs_with_company_count()
    jobs_with_location = repo.get_jobs_with_location_count()
    jobs_with_salary = repo.get_jobs_with_salary_count()
    jobs_with_employment = repo.get_jobs_with_employment_type_count()
    jobs_with_date = repo.get_jobs_with_posted_date_count()
    
    def pct(count):
        return (count / total_jobs * 100) if total_jobs > 0 else 0
    
    print("\n📋 Field Coverage:")
    print(f"  Company name     : {jobs_with_company:>5,} / {total_jobs:,} ({pct(jobs_with_company):>5.1f}%)")
    print(f"  Location         : {jobs_with_location:>5,} / {total_jobs:,} ({pct(jobs_with_location):>5.1f}%)")
    print(f"  Salary data      : {jobs_with_salary:>5,} / {total_jobs:,} ({pct(jobs_with_salary):>5.1f}%)")
    print(f"  Employment type  : {jobs_with_employment:>5,} / {total_jobs:,} ({pct(jobs_with_employment):>5.1f}%)")
    print(f"  Posted date      : {jobs_with_date:>5,} / {total_jobs:,} ({pct(jobs_with_date):>5.1f}%)")
    
    skill_links = repo.get_skill_relationship_count()
    print(f"\n🔗 Skill Coverage:")
    print(f"  Skill-job relationships: {skill_links:,}")
    if total_jobs > 0:
        print(f"  Average skills per job : {skill_links / total_jobs:.1f}")
    
    # Get distinct source sites - efficient count using repository method
    source_sites = repo.get_distinct_source_sites()
    print(f"\n📡 Data Sources:")
    if source_sites:
        for site in source_sites:
            # Defensive: site could be a string or a tuple
            site_name = site[0] if isinstance(site, tuple) else site
            count = repo.count_jobs_by_source_site(site_name)  # Efficient COUNT(*)
            print(f"  {site_name}: {count} jobs")
    else:
        print("  No data sources found")


def print_dashboard_summary(service):
    """Print the dashboard summary from the service layer."""
    print("\n" + "="*10 + " DASHBOARD SUMMARY " + "="*10)
    try:
        summary = service.get_dashboard_summary()
        print(f"\n📊 Overview:")
        print(f"  Total Jobs: {summary['total_jobs']}")
        print(f"  Recent Jobs (30 days): {summary['recent_jobs_count']}")
        
        if summary['top_companies']:
            print(f"\n🏢 Top Companies:")
            for company, count in summary['top_companies'][:3]:
                print(f"  {company}: {count} jobs")
        
        if summary['top_locations']:
            print(f"\n📍 Top Locations:")
            for location, count in summary['top_locations'][:3]:
                print(f"  {location}: {count} jobs")
        
        if summary['salary_statistics']['avg_min'] is not None:
            print(f"\n💰 Salary Insights:")
            print(f"  Average Min: {format_currency(summary['salary_statistics']['avg_min'])}")
            print(f"  Average Max: {format_currency(summary['salary_statistics']['avg_max'])}")
        
        if summary['employment_types']:
            print(f"\n💼 Employment Types:")
            for emp_type, count in summary['employment_types'][:3]:
                print(f"  {emp_type}: {count} jobs")
                
    except Exception as e:
        print(f"Error generating dashboard summary: {str(e)}")


def test_analytics():
    """Main test function to execute all analytics queries."""
    
    print("🚀 Starting Analytics Repository Test")
    print("=" * 60)
    
    try:
        db = SessionLocal()
        try:
            # Initialize repository and service
            repo = AnalyticsRepository(db)
            service = AnalyticsService(repo)
            
            # ============ Sprint 3.1 Queries ============
            print_results("TOP SKILLS", repo.get_top_skills())
            print_results("TOP COMPANIES", repo.get_top_companies())
            print_results("JOBS BY LOCATION", repo.get_jobs_by_location())
            print_salary_statistics(repo.get_salary_statistics())
            print_results("EMPLOYMENT TYPE DISTRIBUTION", repo.get_employment_type_distribution())
            
            # ============ Sprint 3.2 Queries ============
            print_salary_results("SALARY BY LOCATION", repo.get_salary_by_location())
            print_salary_results("SALARY BY COMPANY", repo.get_salary_by_company())
            
            # Posting trend
            print("\n" + "="*10 + " POSTING TREND " + "="*10)
            trend_data = repo.get_jobs_posted_by_date()
            if trend_data:
                for date, count in trend_data[-10:]:
                    print(f"{date.strftime('%Y-%m-%d')} {count:>8,}")
            else:
                print("No data available.")
            
            # Recent jobs
            recent_jobs = repo.get_recent_jobs(days=30, limit=20)
            print_recent_jobs(recent_jobs, 30)
            
            # Salary distribution
            print_salary_distribution(repo.get_salary_distribution())
            
            # ============ Sprint 3.3 Queries ============
            # Dataset Summary
            print_dataset_summary(repo)
            
            # Dashboard Summary (Service orchestration)
            print_dashboard_summary(service)
            
            # Filtering Test
            print("\n" + "="*10 + " FILTERING TEST " + "="*10)
            source_sites = repo.get_distinct_source_sites()
            if source_sites:
                test_source = source_sites[0]
                # Defensive: if it's a tuple, extract the string
                if isinstance(test_source, tuple):
                    test_source = test_source[0]
                
                # Show count for this source using efficient method
                count = repo.count_jobs_by_source_site(test_source)
                print(f"Source: {test_source} ({count} jobs)")
                
                companies = repo.get_top_companies(limit=3, source_site=test_source)
                print(f"Top 3 companies from {test_source}:")
                for company, count in companies:
                    print(f"  {company}: {count} jobs")
                
                # Test salary by location with filter
                salary_by_loc = repo.get_salary_by_location(limit=3, source_site=test_source)
                if salary_by_loc:
                    print(f"\nTop 3 salaries by location from {test_source}:")
                    for location, salary in salary_by_loc:
                        print(f"  {location}: {format_currency(salary)}")
            else:
                print("No source sites available for filtering test.")
            
            # Limit Test
            print("\n" + "="*10 + " LIMIT TEST " + "="*10)
            for limit in [1, 3]:
                companies = repo.get_top_companies(limit=limit)
                print(f"Top {limit} companies returned: {len(companies)}")
                if companies:
                    print(f"  First: {companies[0][0]} ({companies[0][1]} jobs)")
            
            print("\n" + "="*60)
            print("✅ Sprint 3.3 Complete ✓")
            print("   Analytics layer refined and ready for FastAPI")
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