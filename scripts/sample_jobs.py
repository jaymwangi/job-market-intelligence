#!/usr/bin/env python
"""
Stratified sampling of jobs for manual labeling.

This script exports a representative sample of jobs from the database
for manual labeling. It supports multiple stratification strategies
to ensure the sample is representative of the overall job distribution.

Stratification strategies:
- random: Simple random sampling (default)
- country: Stratify by country to ensure geographic diversity
- classifier: Stratify by classifier prediction (tech vs non-tech)
- ambiguity: Stratify by classifier ambiguity (low/medium/high)
  - This is the most useful for improving the classifier
  - It ensures you label edge cases and ambiguous jobs
- hybrid: Combined strategy (30% random + 30% ambiguous + 20% tech + 20% non-tech)
  - Intentionally oversamples difficult examples for manual review
  - This is an active learning strategy, not a purely representative sample

The output is a CSV file with job data that can be opened in Excel
or any spreadsheet software for manual labeling.

Performance Notes:
- All classifier scoring is done once and cached via JobMetadata
- This avoids the N+1 scoring problem present in earlier versions
- For large datasets, consider using --max-jobs to limit scope
- Uses ORDER BY RANDOM() which is fine for tens of thousands of jobs
  - For millions of jobs, consider using TABLESAMPLE or reservoir sampling

Usage:
    # Sample 500 jobs randomly
    python scripts/sample_jobs.py --count 500
    
    # Sample 1000 jobs stratified by ambiguity (best for classifier improvement)
    python scripts/sample_jobs.py --count 1000 --stratify ambiguity
    
    # Sample 500 jobs stratified by country
    python scripts/sample_jobs.py --count 500 --stratify country
    
    # Sample with reproducible random seed
    python scripts/sample_jobs.py --count 500 --seed 42
    
    # Sample with custom output path
    python scripts/sample_jobs.py --count 500 --output data/my_sample.csv
    
    # Increase max jobs for scoring (default: 10000)
    python scripts/sample_jobs.py --count 1000 --max-score-jobs 20000
"""

import argparse
import csv
import logging
import random
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import get_db_session
from app.models.job import Job
from app.etl.enrichment.tech_scorer import get_scorer
from app.etl.enrichment.classifier import classify_result
from app.etl.enrichment.policy import ClassificationPolicy
from sqlalchemy import func

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================

DEFAULT_SAMPLE_SIZE = 500
DEFAULT_OUTPUT = "data/sampled_jobs.csv"
DEFAULT_SEED = None
DEFAULT_MAX_JOBS_FOR_SCORING = 10000
DEFAULT_MAX_JOBS_FETCH = 50000

# Ambiguity thresholds (aligned with classifier)
AMBIGUITY_HIGH_THRESHOLD = 0.65
AMBIGUITY_MEDIUM_THRESHOLD = 0.35

# Minimum samples per country for geographic diversity
# Only applied when count >= number of countries
MIN_SAMPLES_PER_COUNTRY = 1

# CSV column order
CSV_COLUMNS = [
    'id', 'title', 'company', 'location', 'country',
    'source', 'posted_date', 'skills',
    'classifier_prediction', 'classifier_confidence',
    'classifier_ambiguity', 'classifier_category',
    'classifier_score', 'classifier_reason',
    'is_tech', 'category', 'difficulty', 'notes', 'description'
]


@dataclass
class JobMetadata:
    """Job with pre-computed classifier metadata."""
    job: Job
    is_tech: bool = False
    confidence: float = 0.0
    ambiguity: float = 0.0
    primary_category: str = "unknown"
    score: float = 0.0
    reason: str = "UNKNOWN"
    
    @property
    def ambiguity_level(self) -> str:
        """Get ambiguity level based on thresholds."""
        if self.ambiguity >= AMBIGUITY_HIGH_THRESHOLD:
            return "high"
        elif self.ambiguity >= AMBIGUITY_MEDIUM_THRESHOLD:
            return "medium"
        return "low"
    
    @property
    def id(self) -> uuid.UUID:
        """Convenience property for job ID."""
        return self.job.id
    
    def _get_skill_names(self) -> List[str]:
        """Extract skill names from Job skills relationship."""
        skill_names = []
        if self.job.skills:
            for skill in self.job.skills:
                if hasattr(skill, 'name'):
                    skill_names.append(skill.name)
                else:
                    skill_names.append(str(skill))
        return skill_names
    
    def to_dict(self, include_description: bool = True) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        skill_names = self._get_skill_names()
        
        row = {
            'id': self.job.id,
            'title': self._clean_text(self.job.title or ''),
            'company': self._clean_text(self.job.company_name or ''),
            'location': self._clean_text(self.job.location or ''),
            'country': self.job.country_code or '',
            'source': self.job.source_site or '',
            'posted_date': self.job.posted_date.strftime('%Y-%m-%d') if self.job.posted_date else '',
            'skills': ', '.join(skill_names),
            'classifier_prediction': "Tech" if self.is_tech else "Non-Tech",
            'classifier_confidence': round(self.confidence, 3),
            'classifier_ambiguity': round(self.ambiguity, 3),
            'classifier_category': self.primary_category,
            'classifier_score': round(self.score, 1),
            'classifier_reason': self.reason,
            'is_tech': '',  # Manual: True or False
            'category': '',  # Manual: backend, frontend, data_engineering, etc.
            'difficulty': '',  # Manual: 1=easy, 2=medium, 3=hard
            'notes': '',
        }
        
        if include_description:
            desc = self.job.description or ''
            row['description'] = self._truncate_text(desc, 2000)
        
        return row
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text: strip extra whitespace."""
        return ' '.join(text.split())
    
    @staticmethod
    def _truncate_text(text: str, max_length: int = 2000) -> str:
        """Truncate text at word boundary."""
        if not text or len(text) <= max_length:
            return text or ""
        
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + "..."


# ============================================================
# Helper Functions
# ============================================================

def deduplicate_jobs(jobs: List[Job]) -> List[Job]:
    """Remove duplicate jobs by source_id or normalized title+company_name+country."""
    seen_ids: Set[str] = set()
    unique_jobs: List[Job] = []
    
    for job in jobs:
        # Use source_site+source_id if available (most reliable)
        if job.source_id and job.source_site:
            key = f"{job.source_site}|{job.source_id}"
        else:
            # Fallback to normalized title+company_name+country
            title = ' '.join((job.title or '').split()).lower()
            company = ' '.join((job.company_name or '').split()).lower()
            country = (job.country_code or '').lower()
            key = f"{title}|{company}|{country}"
        
        if key not in seen_ids:
            seen_ids.add(key)
            unique_jobs.append(job)
    
    return unique_jobs


def exclude_selected(
    metadata_list: List[JobMetadata],
    selected: List[JobMetadata],
) -> List[JobMetadata]:
    """Exclude selected metadata by ID."""
    selected_ids = {m.id for m in selected}
    return [m for m in metadata_list if m.id not in selected_ids]


def fill_remaining(
    metadata_list: List[JobMetadata],
    sampled: List[JobMetadata],
    target_count: int,
    rng: random.Random,
) -> List[JobMetadata]:
    """
    Fill remaining slots with random sampling.
    
    Args:
        metadata_list: Full population
        sampled: Already sampled items
        target_count: Desired sample size
        rng: Random generator
    
    Returns:
        Extended sample list
    """
    if len(sampled) >= target_count:
        return sampled[:target_count]
    
    remaining = exclude_selected(metadata_list, sampled)
    if remaining:
        additional = rng.sample(
            remaining,
            min(target_count - len(sampled), len(remaining))
        )
        sampled.extend(additional)
        logger.info(f"  Added {len(additional)} additional random jobs")
    
    return sampled[:target_count]


# ============================================================
# Allocation Functions
# ============================================================

def _allocate_largest_remainder(
    groups: Dict[str, List[JobMetadata]],
    total: int,
    count: int,
    min_allocation: int = 0,
) -> Dict[str, int]:
    """
    Allocate samples to groups using largest remainder (Hamilton) method.
    
    Properly handles minimum allocations by reserving seats first.
    
    Args:
        groups: Dict of group_key -> list of items
        total: Total number of items
        count: Number of samples to allocate
        min_allocation: Minimum samples per group (applied before allocation)
    
    Returns:
        Dict of group_key -> allocation count
    """
    num_groups = len(groups)
    
    # Step 1: Reserve minimum allocations
    allocations = {}
    remaining_seats = count
    
    if min_allocation > 0 and count >= num_groups * min_allocation:
        # Reserve min seats for each group
        for key in groups:
            allocations[key] = min_allocation
            remaining_seats -= min_allocation
    else:
        # No minimum allocation if we can't guarantee it
        for key in groups:
            allocations[key] = 0
    
    # Step 2: If no seats left after minimums, return
    if remaining_seats <= 0:
        return allocations
    
    # Step 3: Distribute remaining seats using largest remainder
    # First, calculate proportional allocation for remaining seats
    group_sizes = {key: len(group) for key, group in groups.items()}
    
    # Floor allocations from proportional representation
    floor_allocations = {}
    remainders = {}
    allocated_so_far = 0
    
    for key in groups:
        if remaining_seats > 0:
            proportion = group_sizes[key] / total
            floor_allocation = int(remaining_seats * proportion)
            floor_allocations[key] = floor_allocation
            allocated_so_far += floor_allocation
            remainders[key] = (remaining_seats * proportion) - floor_allocation
        else:
            floor_allocations[key] = 0
            remainders[key] = 0
    
    # Step 4: Add floor allocations
    for key in groups:
        allocations[key] += floor_allocations[key]
    
    # Step 5: Distribute remaining seats to largest remainders
    seats_left = remaining_seats - allocated_so_far
    
    if seats_left > 0:
        sorted_remainders = sorted(
            remainders.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for key, _ in sorted_remainders:
            if seats_left <= 0:
                break
            if allocations[key] < group_sizes[key]:
                allocations[key] += 1
                seats_left -= 1
    
    # Step 6: If still have remaining seats, distribute to largest groups
    if seats_left > 0:
        sorted_by_size = sorted(
            groups.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        for key, group in sorted_by_size:
            if seats_left <= 0:
                break
            if allocations[key] < len(group):
                allocations[key] += 1
                seats_left -= 1
    
    return allocations


def _allocate_ambiguity_proportional(
    groups: Dict[str, List[JobMetadata]],
    total: int,
    count: int,
) -> Dict[str, int]:
    """
    Allocate ambiguity samples using largest remainder.
    
    Ensures more accurate proportional representation than simple int().
    """
    return _allocate_largest_remainder(groups, total, count, min_allocation=0)


# ============================================================
# Metadata Builder - Single Source of Truth for Scoring
# ============================================================

def build_metadata(
    jobs: List[Job],
    max_jobs: int = DEFAULT_MAX_JOBS_FOR_SCORING,
    progress_interval: int = 500,
) -> List[JobMetadata]:
    """
    Build metadata for all jobs in a single pass.
    
    This is the single source of truth for all classifier scoring.
    All sampling strategies use this metadata, avoiding repeated scoring.
    
    Args:
        jobs: List of jobs to score
        max_jobs: Maximum jobs to score (for performance)
        progress_interval: How often to log progress
    
    Returns:
        List of JobMetadata objects
    """
    logger.info("Building classifier metadata...")
    
    scorer = get_scorer()
    policy = ClassificationPolicy.default()
    metadata_list: List[JobMetadata] = []
    
    # Limit for performance
    jobs_to_score = jobs[:max_jobs]
    if len(jobs) > max_jobs:
        logger.info(f"  Limiting to {max_jobs} jobs for scoring (use --max-score-jobs to increase)")
    
    for i, job in enumerate(jobs_to_score):
        if i > 0 and i % progress_interval == 0:
            logger.info(f"    Scored {i}/{len(jobs_to_score)} jobs")
        
        try:
            # Extract skill names from Skill objects
            skill_names = []
            if job.skills:
                for skill in job.skills:
                    if hasattr(skill, 'name'):
                        skill_names.append(skill.name)
                    else:
                        skill_names.append(str(skill))
            
            result = scorer.score(
                job.title or "",
                job.description or "",
                skill_names
            )
            decision = classify_result(result, policy)
            
            metadata_list.append(JobMetadata(
                job=job,
                is_tech=decision.is_tech,
                confidence=decision.confidence,
                ambiguity=decision.ambiguity_score,
                primary_category=decision.primary_category,
                score=decision.score,
                reason=decision.reason.name if decision.reason else "UNKNOWN",
            ))
        except Exception as e:
            logger.debug(f"Could not score job {job.id}: {e}")
            # Default metadata for failed scoring
            metadata_list.append(JobMetadata(
                job=job,
                is_tech=False,
                confidence=0.0,
                ambiguity=1.0,  # Unknown = highly ambiguous
                primary_category="unknown",
                score=0.0,
                reason="ERROR",
            ))
    
    logger.info(f"  Built metadata for {len(metadata_list)} jobs")
    return metadata_list


# ============================================================
# Sampling Strategies (all use JobMetadata)
# ============================================================

def sample_random_from_metadata(
    metadata_list: List[JobMetadata],
    count: int,
    rng: random.Random,
) -> List[JobMetadata]:
    """
    Simple random sampling from metadata.
    
    Args:
        metadata_list: List of JobMetadata objects
        count: Number of jobs to sample
        rng: Random generator for reproducibility
    
    Returns:
        List of sampled JobMetadata objects
    """
    logger.info("  Random sampling...")
    if len(metadata_list) <= count:
        return metadata_list.copy()
    return rng.sample(metadata_list, count)


def sample_by_country_from_metadata(
    metadata_list: List[JobMetadata],
    count: int,
    rng: random.Random,
) -> List[JobMetadata]:
    """
    Stratified sampling by country using largest remainder method.
    
    Args:
        metadata_list: List of JobMetadata objects
        count: Number of jobs to sample
        rng: Random generator for reproducibility
    
    Returns:
        List of sampled JobMetadata objects
    """
    logger.info("  Grouping by country...")
    
    # Group by country
    country_groups: Dict[str, List[JobMetadata]] = defaultdict(list)
    for meta in metadata_list:
        country = meta.job.country_code or 'unknown'
        country_groups[country].append(meta)
    
    total = len(metadata_list)
    total_countries = len(country_groups)
    logger.info(f"  Found {total_countries} countries")
    
    # Only apply minimum allocation if we can guarantee at least one per country
    min_allocation = MIN_SAMPLES_PER_COUNTRY if count >= total_countries else 0
    
    # Allocate using largest remainder method
    allocations = _allocate_largest_remainder(
        country_groups, total, count, min_allocation
    )
    
    # Sample from each country
    sampled = []
    for country, sample_count in allocations.items():
        if sample_count > 0 and country in country_groups:
            group = country_groups[country]
            sampled.extend(rng.sample(group, min(sample_count, len(group))))
    
    logger.info(f"  Sampled from {len(allocations)} countries")
    
    # Fill remaining if needed
    return fill_remaining(metadata_list, sampled, count, rng)


def sample_by_classifier_from_metadata(
    metadata_list: List[JobMetadata],
    count: int,
    rng: random.Random,
) -> List[JobMetadata]:
    """
    Stratified sampling by classifier prediction (tech vs non-tech).
    
    Args:
        metadata_list: List of JobMetadata objects
        count: Number of jobs to sample
        rng: Random generator for reproducibility
    
    Returns:
        List of sampled JobMetadata objects
    """
    logger.info("  Partitioning by classifier prediction...")
    
    tech = [m for m in metadata_list if m.is_tech]
    non_tech = [m for m in metadata_list if not m.is_tech]
    
    logger.info(f"  Found {len(tech)} tech and {len(non_tech)} non-tech jobs")
    
    half = count // 2
    tech_sample_size = min(half, len(tech))
    non_tech_sample_size = min(count - tech_sample_size, len(non_tech))
    
    sampled = []
    if tech_sample_size > 0:
        sampled.extend(rng.sample(tech, tech_sample_size))
        logger.info(f"  Sampled {tech_sample_size} tech jobs")
    if non_tech_sample_size > 0:
        sampled.extend(rng.sample(non_tech, non_tech_sample_size))
        logger.info(f"  Sampled {non_tech_sample_size} non-tech jobs")
    
    # Fill remaining if needed
    return fill_remaining(metadata_list, sampled, count, rng)


def sample_by_ambiguity_from_metadata(
    metadata_list: List[JobMetadata],
    count: int,
    rng: random.Random,
) -> List[JobMetadata]:
    """
    Stratified sampling by classifier ambiguity using proportional allocation.
    
    Uses largest remainder allocation for accurate proportions.
    
    Args:
        metadata_list: List of JobMetadata objects
        count: Number of jobs to sample
        rng: Random generator for reproducibility
    
    Returns:
        List of sampled JobMetadata objects
    """
    logger.info("  Grouping by ambiguity level...")
    
    ambiguity_groups = {
        "high": [m for m in metadata_list if m.ambiguity_level == "high"],
        "medium": [m for m in metadata_list if m.ambiguity_level == "medium"],
        "low": [m for m in metadata_list if m.ambiguity_level == "low"],
    }
    
    logger.info(f"  High ambiguity: {len(ambiguity_groups['high'])}, "
                f"Medium: {len(ambiguity_groups['medium'])}, "
                f"Low: {len(ambiguity_groups['low'])}")
    
    total = len(metadata_list)
    
    # Proportional allocation using largest remainder
    allocations = _allocate_ambiguity_proportional(
        ambiguity_groups, total, count
    )
    
    sampled = []
    for level, alloc_count in allocations.items():
        group = ambiguity_groups[level]
        sample_size = min(alloc_count, len(group))
        if sample_size > 0:
            sampled.extend(rng.sample(group, sample_size))
            logger.info(f"  Sampled {sample_size} jobs from {level} ambiguity group")
    
    # Fill remaining if needed
    return fill_remaining(metadata_list, sampled, count, rng)


def sample_hybrid_from_metadata(
    metadata_list: List[JobMetadata],
    count: int,
    rng: random.Random,
) -> List[JobMetadata]:
    """
    Hybrid sampling strategy - active learning focused.
    
    Combines multiple strategies for a diverse sample:
    - 30% random (representative baseline)
    - 30% high ambiguity (edge cases - active learning)
    - 20% tech (tech examples)
    - 20% non-tech (non-tech examples)
    
    This intentionally oversamples difficult examples for manual review
    to improve the classifier. It is NOT a purely representative sample.
    
    Args:
        metadata_list: List of JobMetadata objects
        count: Number of jobs to sample
        rng: Random generator for reproducibility
    
    Returns:
        List of sampled JobMetadata objects
    """
    logger.info("  Running hybrid sampling (30% random + 30% ambiguous + 20% tech + 20% non-tech)...")
    logger.info("  Note: This strategy intentionally oversamples edge cases")
    
    if len(metadata_list) <= count:
        return metadata_list.copy()
    
    # Calculate group sizes
    random_count = int(count * 0.30)
    ambiguous_count = int(count * 0.30)
    tech_count = int(count * 0.20)
    non_tech_count = count - random_count - ambiguous_count - tech_count
    
    logger.info(f"  Random: {random_count}, Ambiguous: {ambiguous_count}, "
                f"Tech: {tech_count}, Non-tech: {non_tech_count}")
    
    sampled_lists = []
    
    # 1. Random sampling
    if random_count > 0:
        random_sample = sample_random_from_metadata(metadata_list, random_count, rng)
        sampled_lists.append(random_sample)
        logger.info(f"  Sampled {len(random_sample)} random jobs")
    
    # 2. Ambiguity sampling (high ambiguity only)
    if ambiguous_count > 0:
        high_ambiguity = [m for m in metadata_list if m.ambiguity_level == "high"]
        if high_ambiguity:
            ambiguity_sample = rng.sample(
                high_ambiguity,
                min(ambiguous_count, len(high_ambiguity))
            )
            sampled_lists.append(ambiguity_sample)
            logger.info(f"  Sampled {len(ambiguity_sample)} ambiguous jobs")
        else:
            # Fallback: use all ambiguity levels
            ambiguity_sample = sample_by_ambiguity_from_metadata(
                metadata_list, ambiguous_count, rng
            )
            sampled_lists.append(ambiguity_sample)
            logger.info(f"  Sampled {len(ambiguity_sample)} ambiguous jobs (fallback)")
    
    # 3. Tech sampling
    if tech_count > 0:
        tech_metadata = [m for m in metadata_list if m.is_tech]
        if tech_metadata:
            tech_sample = rng.sample(tech_metadata, min(tech_count, len(tech_metadata)))
            sampled_lists.append(tech_sample)
            logger.info(f"  Sampled {len(tech_sample)} tech jobs")
    
    # 4. Non-tech sampling
    if non_tech_count > 0:
        non_tech_metadata = [m for m in metadata_list if not m.is_tech]
        if non_tech_metadata:
            non_tech_sample = rng.sample(
                non_tech_metadata,
                min(non_tech_count, len(non_tech_metadata))
            )
            sampled_lists.append(non_tech_sample)
            logger.info(f"  Sampled {len(non_tech_sample)} non-tech jobs")
    
    # Merge and deduplicate using ID-based filtering
    seen_ids: Set[uuid.UUID] = set()
    result: List[JobMetadata] = []
    for lst in sampled_lists:
        for meta in lst:
            if meta.id not in seen_ids and len(result) < count:
                seen_ids.add(meta.id)
                result.append(meta)
    
    # Fill remaining if needed
    return fill_remaining(metadata_list, result, count, rng)


# ============================================================
# Strategy Map
# ============================================================

STRATEGIES = {
    "random": sample_random_from_metadata,
    "country": sample_by_country_from_metadata,
    "classifier": sample_by_classifier_from_metadata,
    "ambiguity": sample_by_ambiguity_from_metadata,
    "hybrid": sample_hybrid_from_metadata,
}


# ============================================================
# Export Functions
# ============================================================

def export_metadata_to_csv(
    sampled_metadata: List[JobMetadata],
    output_path: Path,
    include_description: bool = True,
) -> None:
    """
    Export JobMetadata to CSV for manual labeling.
    
    Args:
        sampled_metadata: List of JobMetadata objects
        output_path: Path to output CSV file
        include_description: Whether to include full description
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dictionaries
    data = []
    for meta in sampled_metadata:
        data.append(meta.to_dict(include_description))
    
    # Use predefined column order
    fieldnames = [col for col in CSV_COLUMNS if col != 'description' or include_description]
    
    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"✅ Exported {len(data)} jobs to {output_path}")
    logger.info("")
    logger.info("📋 Labeling Instructions:")
    logger.info("  - 'is_tech': True/False - Is this a technology role?")
    logger.info("  - 'category': Technical category (backend, frontend, data_engineering, etc.)")
    logger.info("  - 'difficulty': 1=easy, 2=medium, 3=hard - How difficult was this to classify?")
    logger.info("  - 'notes': Any additional notes about this job")
    logger.info("")
    logger.info("  Common categories: backend, frontend, full_stack, data_engineering,")
    logger.info("  data_science, ml_ai, devops, security, mobile, qa, other, non_tech")
    logger.info("")
    logger.info("  💡 The 'classifier_*' columns show what the classifier predicted.")
    logger.info("     Use this as a starting point, but correct it if wrong!")


# ============================================================
# Validation Functions
# ============================================================

def validate_args(args: argparse.Namespace) -> bool:
    """Validate command line arguments."""
    if args.count <= 0:
        logger.error("Count must be positive")
        return False
    
    if args.limit <= 0:
        logger.error("Limit must be positive")
        return False
    
    if args.max_score_jobs <= 0:
        logger.error("max-score-jobs must be positive")
        return False
    
    if args.count > args.limit:
        logger.warning(
            f"Count ({args.count}) exceeds limit ({args.limit}). "
            "Consider increasing --limit"
        )
    
    return True


# ============================================================
# Main Entry Point
# ============================================================

def main():
    """Main entry point for the sampling script."""
    parser = argparse.ArgumentParser(
        description="Stratified sampling of jobs for manual labeling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help=f"Number of jobs to sample (default: {DEFAULT_SAMPLE_SIZE})",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV file path (default: {DEFAULT_OUTPUT})",
    )
    
    parser.add_argument(
        "--stratify",
        type=str,
        default="random",
        choices=["random", "country", "classifier", "ambiguity", "hybrid"],
        help="Stratification strategy (default: random)",
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility (default: None)",
    )
    
    parser.add_argument(
        "--no-description",
        action="store_true",
        help="Exclude description from output (reduces file size)",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_MAX_JOBS_FETCH,
        help=f"Maximum jobs to fetch from database (default: {DEFAULT_MAX_JOBS_FETCH})",
    )
    
    parser.add_argument(
        "--max-score-jobs",
        type=int,
        default=DEFAULT_MAX_JOBS_FOR_SCORING,
        help=f"Maximum jobs to score (default: {DEFAULT_MAX_JOBS_FOR_SCORING})",
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not validate_args(args):
        sys.exit(1)
    
    # Set random seed for reproducibility
    rng = random.Random()
    if args.seed is not None:
        rng.seed(args.seed)
        logger.info(f"Using random seed: {args.seed}")
    
    # Connect to database
    logger.info("Connecting to database...")
    with get_db_session() as session:
        # Get jobs with random ordering for true randomness
        # Note: ORDER BY RANDOM() is fine for tens of thousands of jobs
        # For larger datasets, consider using TABLESAMPLE or reservoir sampling
        logger.info(f"Fetching jobs (limit: {args.limit})...")
        jobs = session.query(Job).order_by(func.random()).limit(args.limit).all()
        
        if not jobs:
            logger.error("No jobs found in database")
            sys.exit(1)
        
        logger.info(f"Found {len(jobs)} jobs")
        
        # Deduplicate jobs
        logger.info("Deduplicating jobs...")
        unique_jobs = deduplicate_jobs(jobs)
        logger.info(f"Unique jobs: {len(unique_jobs)} (removed {len(jobs) - len(unique_jobs)} duplicates)")
        
        # Build metadata once (single pass)
        metadata_list = build_metadata(unique_jobs, args.max_score_jobs)
        
        if not metadata_list:
            logger.error("No metadata built")
            sys.exit(1)
        
        # Sample based on strategy
        logger.info(f"Sampling {args.count} jobs using '{args.stratify}' strategy...")
        
        sampling_func = STRATEGIES.get(args.stratify)
        if sampling_func is None:
            logger.error(f"Unknown strategy: {args.stratify}")
            sys.exit(1)
        
        sampled_metadata = sampling_func(metadata_list, args.count, rng)
        
        if not sampled_metadata:
            logger.error("No jobs sampled")
            sys.exit(1)
        
        logger.info(f"✅ Sampled {len(sampled_metadata)} jobs")
        
        # Export to CSV
        output_path = Path(args.output)
        export_metadata_to_csv(
            sampled_metadata,
            output_path,
            include_description=not args.no_description,
        )


if __name__ == "__main__":
    main()