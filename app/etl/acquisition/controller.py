"""Acquisition controller for balanced dataset collection."""

from typing import Dict, List, Optional, Any, Tuple
import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session
from app.models.job import Job
from app.etl.schemas.enriched import JobEnriched
from .models import AcquisitionMode, AcquisitionStats, AcquisitionResult, DatabaseComposition

logger = logging.getLogger(__name__)


class AcquisitionController:
    """
    Query-level adaptive acquisition controller.
    
    The controller operates at the query level:
    1. Get next query based on current mode
    2. Execute query → raw jobs (up to batch_size per query)
    3. Transform + Classify
    4. Update projected composition with classification results
    5. Check if mode should change
    6. Get next query (repeats)
    
    Note: batch_size controls the maximum jobs per query, not the total run.
    The total run is controlled by max_jobs_per_run.
    """

    def __init__(
        self,
        db_session: Session,
        target_tech_ratio: float = 0.5,
        max_jobs_per_run: int = 2000,
        batch_size: int = 100,
        broad_queries: Optional[List[str]] = None,
        tech_queries: Optional[List[str]] = None,
        use_category_filter: bool = True,
        country: Optional[str] = None,
        parity_tolerance: float = 0.05
    ):
        self.db_session = db_session
        self.target_tech_ratio = target_tech_ratio
        self.max_jobs_per_run = max_jobs_per_run
        self.batch_size = batch_size  # Maximum jobs per query
        self.use_category_filter = use_category_filter
        self.country = country
        self.parity_tolerance = parity_tolerance
        self.start_time = datetime.now()
        
        # Query lists
        self.broad_queries = self._build_queries(
            broad_queries or self._get_default_broad_queries(), 
            is_tech=False
        )
        self.tech_queries = self._build_queries(
            tech_queries or self._get_default_tech_queries(), 
            is_tech=True
        )
        
        # Query tracking
        self.broad_index = 0
        self.tech_index = 0
        self.used_query_keys = set()
        self.broad_queries_used = 0
        self.tech_queries_used = 0
        self.current_query = None
        
        # Results tracking
        self.seen_job_ids = set()
        self.all_jobs = []
        
        # INTENT-based collections
        self.tech_intent_jobs = []
        self.broad_intent_jobs = []
        
        # CLASSIFICATION-based collections
        self.tech_classified_jobs = []
        self.non_tech_classified_jobs = []
        self.unclassified_jobs = []
        
        self.duplicates = []
        self.mode_changed = False
        
        # Query tracking
        self.query_count = 0
        
        # Track query-level metrics
        self.query_metrics = []
        self.current_query_start_time = None
        self.current_query_new_jobs = 0
        self.current_query_classified = 0
        self.current_query_tech = 0
        self.current_query_non_tech = 0
        self.current_query_unclassified = 0
        self.current_query_mode = None  # Track mode at query start
        
        # Check database composition
        self.initial_composition = self._get_database_composition(country=country)
        
        # Projected composition (starts as initial, updated after classification)
        self.projected_composition = DatabaseComposition(
            total_jobs=self.initial_composition.total_jobs,
            tech_count=self.initial_composition.tech_count,
            non_tech_count=self.initial_composition.non_tech_count,
            unclassified_count=self.initial_composition.unclassified_count
        )
        
        # Determine mode
        self.mode = self._determine_mode()
        
        # Track balanced mode start counts for target accounting
        self.balanced_mode_tech_start = 0
        self.balanced_mode_broad_start = 0
        
        # Calculate targets for this run
        self.tech_intent_target = self._calculate_tech_target()
        self.broad_intent_target = self._calculate_broad_target()
        
        logger.info(
            f"AcquisitionController initialized: "
            f"mode={self.mode.value}, "
            f"db_total={self.initial_composition.total_jobs}, "
            f"db_tech={self.initial_composition.tech_count}, "
            f"db_non_tech={self.initial_composition.non_tech_count}, "
            f"tech_deficit={self.initial_composition.tech_deficit}, "
            f"has_parity={self.initial_composition.has_reached_parity(self.parity_tolerance)}, "
            f"batch_size={self.batch_size} (per query), "
            f"max_jobs_per_run={self.max_jobs_per_run}"
        )
    
    def _get_default_broad_queries(self) -> List[str]:
        return [
            "nurse", "doctor", "healthcare", "medical",
            "teacher", "professor", "educator",
            "retail", "cashier", "customer service", "barista",
            "driver", "delivery", "logistics",
            "construction", "electrician", "plumber", "carpenter", "mechanic",
            "accountant", "administrative", "receptionist", "clerk",
            "chef", "hospitality", "hotel"
        ]
    
    def _get_default_tech_queries(self) -> List[str]:
        return [
            "software engineer", "software developer",
            "backend developer", "frontend developer", "full stack developer",
            "devops engineer", "site reliability engineer",
            "data scientist", "data engineer", "data analyst",
            "machine learning engineer", "ai engineer",
            "cloud engineer", "cloud architect",
            "security engineer", "network engineer", "systems administrator",
            "ios developer", "android developer", "mobile developer",
            "qa engineer", "test automation engineer", "quality assurance",
            "game developer", "unity developer", "unreal developer",
            "embedded engineer", "firmware engineer", "iot engineer",
            "blockchain developer", "web3 developer", "smart contract developer"
        ]
    
    def _get_database_composition(self, country: Optional[str] = None) -> DatabaseComposition:
        """Query the database for current job composition."""
        query = self.db_session.query(Job)
        if country:
            query = query.filter(Job.country_code == country)
        
        total = query.count()
        tech = query.filter(Job.is_tech_role == True).count()
        non_tech = query.filter(Job.is_tech_role == False).count()
        unclassified = query.filter(Job.is_tech_role.is_(None)).count()
        
        return DatabaseComposition(
            total_jobs=total,
            tech_count=tech,
            non_tech_count=non_tech,
            unclassified_count=unclassified
        )
    
    def _build_queries(self, terms: List[str], is_tech: bool) -> List[Dict[str, Any]]:
        queries = []
        for term in terms:
            query = {"what": term}
            if is_tech and self.use_category_filter:
                query["category"] = "it-jobs"
            queries.append(query)
        return queries
    
    def _determine_mode(self) -> AcquisitionMode:
        comp = self.initial_composition
        if comp.classified_total == 0:
            logger.info("No classified jobs found, starting in BALANCED mode")
            return AcquisitionMode.BALANCED
        
        if comp.has_reached_parity(self.parity_tolerance):
            logger.info(f"Parity reached, starting in BALANCED mode")
            return AcquisitionMode.BALANCED
        
        logger.info(f"Tech deficit: {comp.tech_deficit}, starting in CATCH_UP mode")
        return AcquisitionMode.CATCH_UP
    
    def _calculate_tech_target(self) -> int:
        if self.mode == AcquisitionMode.CATCH_UP:
            deficit = self.initial_composition.tech_deficit
            return min(deficit, self.max_jobs_per_run)
        else:
            return int(self.max_jobs_per_run * self.target_tech_ratio)
    
    def _calculate_broad_target(self) -> int:
        if self.mode == AcquisitionMode.CATCH_UP:
            return 0
        else:
            return self.max_jobs_per_run - self.tech_intent_target
    
    def get_next_query(self) -> Optional[Dict[str, Any]]:
        """
        Get the next query based on current mode and projected composition.
        
        This is called repeatedly during acquisition, allowing the controller
        to adapt as classification results come in.
        """
        stats = self.get_stats()
        
        # ✅ Only check max_jobs_per_run (total budget)
        if stats.jobs_acquired_this_run >= self.max_jobs_per_run:
            logger.info(f"Reached max jobs per run: {self.max_jobs_per_run}")
            return None
        
        # ❌ REMOVED: batch_size check
        # if stats.jobs_acquired_this_run >= self.batch_size:
        #     logger.info(f"Reached batch size limit: {self.batch_size}")
        #     return None
        
        # Track query start state
        self.current_query_start_time = datetime.now()
        self.current_query_new_jobs = 0
        self.current_query_classified = 0
        self.current_query_tech = 0
        self.current_query_non_tech = 0
        self.current_query_unclassified = 0
        self.current_query_mode = self.mode  # Capture mode at query start
        
        if self.mode == AcquisitionMode.CATCH_UP:
            return self._get_catch_up_query(stats)
        else:
            return self._get_balanced_query(stats)
    
    def _get_catch_up_query(self, stats: AcquisitionStats) -> Optional[Dict[str, Any]]:
        """
        Get a query during catch-up mode.
        
        Uses projected composition to determine if we still need tech jobs.
        """
        # Use projected composition to check if we've reached parity
        if self.projected_composition.has_reached_parity(self.parity_tolerance):
            logger.info(
                f"Projected composition reached parity! "
                f"tech={self.projected_composition.tech_ratio:.1%}, "
                f"switching to balanced mode"
            )
            self.mode = AcquisitionMode.BALANCED
            self.mode_changed = True
            
            # Track balanced mode start counts
            self.balanced_mode_tech_start = len(self.tech_intent_jobs)
            self.balanced_mode_broad_start = len(self.broad_intent_jobs)
            
            # Calculate remaining capacity for balanced mode
            remaining_capacity = self.max_jobs_per_run - stats.jobs_acquired_this_run
            
            # Set targets as remaining counts for balanced mode
            self.tech_intent_target = int(remaining_capacity * self.target_tech_ratio)
            self.broad_intent_target = remaining_capacity - self.tech_intent_target
            
            logger.info(
                f"New targets for balanced mode: "
                f"tech={self.tech_intent_target}, "
                f"broad={self.broad_intent_target}"
            )
            return self._get_balanced_query(stats)
        
        # Still need tech jobs
        logger.info(
            f"Still in catch-up mode: "
            f"projected_tech_ratio={self.projected_composition.tech_ratio:.1%}, "
            f"target={self.target_tech_ratio:.1%}"
        )
        return self._next_tech_query()
    
    def _get_balanced_query(self, stats: AcquisitionStats) -> Optional[Dict[str, Any]]:
        """
        Get a query that maintains balance based on PROJECTED composition.
        
        Uses actual classification feedback from previous queries to decide
        whether to fetch more tech or broad jobs.
        
        Projected composition is the PRIMARY decision driver.
        Intent targets act as guardrails to prevent over-acquisition.
        """
        # Calculate acquired counts since entering balanced mode
        tech_acquired_in_balanced = len(self.tech_intent_jobs) - self.balanced_mode_tech_start
        broad_acquired_in_balanced = len(self.broad_intent_jobs) - self.balanced_mode_broad_start
        
        tech_remaining = self.tech_intent_target - tech_acquired_in_balanced
        broad_remaining = self.broad_intent_target - broad_acquired_in_balanced
        
        # Intent targets as guardrails (prevent over-acquisition)
        if tech_remaining <= 0 and broad_remaining <= 0:
            logger.info("Both tech and broad intent targets met")
            return None
        if tech_remaining <= 0:
            logger.info("Tech intent target met, fetching broad query")
            return self._next_broad_query()
        if broad_remaining <= 0:
            logger.info("Broad intent target met, fetching tech query")
            return self._next_tech_query()
        
        # PRIMARY: Use PROJECTED composition (actual classification feedback)
        projected_tech_ratio = self.projected_composition.tech_ratio
        target_ratio = self.target_tech_ratio
        
        if projected_tech_ratio < target_ratio - self.parity_tolerance:
            # Need more tech jobs
            logger.info(
                f"Projected tech ratio {projected_tech_ratio:.1%} below target {target_ratio:.1%}, "
                f"fetching tech query"
            )
            return self._next_tech_query()
        elif projected_tech_ratio > target_ratio + self.parity_tolerance:
            # Need more non-tech jobs
            logger.info(
                f"Projected tech ratio {projected_tech_ratio:.1%} above target {target_ratio:.1%}, "
                f"fetching broad query"
            )
            return self._next_broad_query()
        else:
            # Within tolerance - use intent progress as tie-breaker
            logger.info(
                f"Projected tech ratio {projected_tech_ratio:.1%} within tolerance, "
                f"using intent progress as tie-breaker"
            )
            if tech_acquired_in_balanced <= broad_acquired_in_balanced:
                return self._next_tech_query()
            else:
                return self._next_broad_query()
    
    def _next_broad_query(self) -> Optional[Dict[str, Any]]:
        while self.broad_index < len(self.broad_queries):
            query = self.broad_queries[self.broad_index]
            query_key = f"broad:{query.get('what')}"
            if query_key not in self.used_query_keys:
                self.used_query_keys.add(query_key)
                self.broad_index += 1
                self.broad_queries_used += 1
                self.current_query = query
                logger.info(f"Broad query: {query.get('what')}")
                return query
            self.broad_index += 1
        logger.warning("No more broad queries available")
        return None
    
    def _next_tech_query(self) -> Optional[Dict[str, Any]]:
        while self.tech_index < len(self.tech_queries):
            query = self.tech_queries[self.tech_index]
            query_key = f"tech:{query.get('what')}"
            if query_key not in self.used_query_keys:
                self.used_query_keys.add(query_key)
                self.tech_index += 1
                self.tech_queries_used += 1
                self.current_query = query
                logger.info(f"Tech query: {query.get('what')}")
                return query
            self.tech_index += 1
        logger.warning("No more tech queries available")
        return None
    
    def add_jobs(
        self,
        jobs: List[Dict[str, Any]],
        query: Dict[str, Any],
        country: str
    ) -> Tuple[int, int]:
        new_count = 0
        dup_count = 0
        is_tech_intent = query.get('category') == 'it-jobs'
        
        for job in jobs:
            job_id = self._get_job_id(job)
            if job_id in self.seen_job_ids:
                dup_count += 1
                job['_is_duplicate'] = True
                self.duplicates.append(job)
                continue
            
            self.seen_job_ids.add(job_id)
            self.all_jobs.append(job)
            new_count += 1
            
            job['_acquisition_tech_intent'] = is_tech_intent
            job['_acquisition_query'] = query
            job['_acquisition_country'] = country
            job['_acquisition_mode'] = self.mode.value
            job['_acquisition_query_number'] = self.query_count
            
            # Track new jobs from this query
            self.current_query_new_jobs += 1
            
            if is_tech_intent:
                self.tech_intent_jobs.append(job)
            else:
                self.broad_intent_jobs.append(job)
        
        logger.info(
            f"Added {new_count} new jobs, {dup_count} duplicates "
            f"(tech_intent={is_tech_intent}, mode={self.mode.value})"
        )
        return new_count, dup_count
    
    def _record_query_metrics(self):
        """Record metrics for the current query."""
        if self.current_query_start_time:
            duration = (datetime.now() - self.current_query_start_time).total_seconds()
            
            # Capture query safely with copy
            query_copy = self.current_query.copy() if self.current_query else None
            
            # ✅ Add tech_intent from the query's category
            is_tech_intent = self.current_query.get('category') == 'it-jobs' if self.current_query else False
            
            self.query_metrics.append({
                'query': query_copy,
                'tech_intent': is_tech_intent,  # ✅ Add this field
                'new_jobs': self.current_query_new_jobs,
                'tech_classified': self.current_query_tech,
                'non_tech_classified': self.current_query_non_tech,
                'unclassified': self.current_query_unclassified,
                'duration_seconds': duration,
                'mode': self.current_query_mode.value if self.current_query_mode else self.mode.value,
            })
        
        # Reset for next query
        self.current_query_start_time = None
        self.current_query_new_jobs = 0
        self.current_query_classified = 0
        self.current_query_tech = 0
        self.current_query_non_tech = 0
        self.current_query_unclassified = 0
        self.current_query_mode = None
        
    def update_classification(self, classified_jobs: List[JobEnriched]):
        """
        Update projected composition based on actual classification results.

        Matches enriched jobs back to jobs acquired by this controller using
        the stable source_id propagated from the original acquisition ID.
        """
        if not classified_jobs:
            logger.warning("No classified jobs to update")
            return

        # IDs of jobs actually acquired by this controller.
        acquired_job_ids = {
            self._get_job_id(job)
            for job in self.all_jobs
        }

        tech_count = 0
        non_tech_count = 0
        unclassified_count = 0
        
        # Track which jobs belong to current query
        current_query_jobs = []

        for job in classified_jobs:
            # JobEnriched.source_id comes from the original raw job["id"]
            job_id = str(job.source_id)

            # Ignore jobs that were not acquired by this controller.
            if job_id not in acquired_job_ids:
                logger.debug(
                    "Skipping job %s: not acquired by this controller",
                    job_id,
                )
                continue

            is_tech = job.is_tech_role
            
            # Track current query jobs
            current_query_jobs.append(job)

            if is_tech is True:
                tech_count += 1
                self.tech_classified_jobs.append(job)
                self.current_query_tech += 1

            elif is_tech is False:
                non_tech_count += 1
                self.non_tech_classified_jobs.append(job)
                self.current_query_non_tech += 1

            else:
                unclassified_count += 1
                self.unclassified_jobs.append(job)
                self.current_query_unclassified += 1

        # Update current query metrics
        self.current_query_classified = len(current_query_jobs)
        
        # Record metrics for this query (after classification)
        self._record_query_metrics()

        # Update projected composition using ACTUAL classifications.
        self.projected_composition.tech_count += tech_count
        self.projected_composition.non_tech_count += non_tech_count
        self.projected_composition.unclassified_count += unclassified_count
        self.projected_composition.total_jobs += (
            tech_count + non_tech_count + unclassified_count
        )

        self.query_count += 1

        logger.info(
            f"Classification updated: "
            f"tech={tech_count}, "
            f"non_tech={non_tech_count}, "
            f"unclassified={unclassified_count}, "
            f"query={self.query_count}"
        )

        logger.info(
            f"Projected composition: "
            f"tech={self.projected_composition.tech_count}, "
            f"non_tech={self.projected_composition.non_tech_count}, "
            f"ratio={self.projected_composition.tech_ratio:.2%}, "
            f"parity={self.projected_composition.has_reached_parity(self.parity_tolerance)}"
        )

        # Check if we should switch to balanced mode.
        if (
            self.mode == AcquisitionMode.CATCH_UP
            and self.projected_composition.has_reached_parity(
                self.parity_tolerance
            )
        ):
            logger.info(
                "🎯 Projected composition reached parity! "
                "Switching to balanced mode"
            )

            self.mode = AcquisitionMode.BALANCED
            self.mode_changed = True

            # Track balanced mode start counts
            self.balanced_mode_tech_start = len(self.tech_intent_jobs)
            self.balanced_mode_broad_start = len(self.broad_intent_jobs)

            # Recalculate targets for remaining capacity.
            stats = self.get_stats()
            remaining_capacity = (
                self.max_jobs_per_run - stats.jobs_acquired_this_run
            )

            self.tech_intent_target = int(
                remaining_capacity * self.target_tech_ratio
            )
            self.broad_intent_target = (
                remaining_capacity - self.tech_intent_target
            )

            logger.info(
                f"New targets for balanced mode: "
                f"tech={self.tech_intent_target}, "
                f"broad={self.broad_intent_target}"
            )
    
    def _get_job_id(self, job: Any) -> str:
        """Get a unique identifier for a job, handling both dict and object."""
        # Try dict access first (for raw jobs)
        if isinstance(job, dict):
            job_id = job.get('id')
            if job_id:
                return str(job_id)
            url = job.get('redirect_url')
            if url:
                return url
            key = f"{job.get('title', '')}_{job.get('company', '')}"
        else:
            # Try attribute access (for JobEnriched objects)
            try:
                job_id = getattr(job, 'source_id', None) or getattr(job, 'id', None)
                if job_id:
                    return str(job_id)
            except:
                pass
            
            try:
                title = getattr(job, 'title', '')
                company = getattr(job, 'company_name', '')
                key = f"{title}_{company}"
            except:
                key = str(id(job))  # Fallback
        
        import hashlib
        return hashlib.md5(key.encode()).hexdigest()
    
    def get_stats(self) -> AcquisitionStats:
        """Get current acquisition statistics."""
        return AcquisitionStats(
            # Database composition
            db_total=self.initial_composition.total_jobs,
            db_tech=self.initial_composition.tech_count,
            db_non_tech=self.initial_composition.non_tech_count,
            db_unclassified=self.initial_composition.unclassified_count,
            db_tech_ratio=self.initial_composition.tech_ratio,
            db_has_parity=self.initial_composition.has_reached_parity(self.parity_tolerance),
            tech_deficit=self.initial_composition.tech_deficit,
            
            # Intent counts
            tech_intent_acquired=len(self.tech_intent_jobs),
            broad_intent_acquired=len(self.broad_intent_jobs),
            
            # Classification counts
            tech_classified_acquired=len(self.tech_classified_jobs),
            non_tech_classified_acquired=len(self.non_tech_classified_jobs),
            unclassified_acquired=len(self.unclassified_jobs),
            
            # Overall
            jobs_acquired_this_run=len(self.all_jobs),
            duplicates_this_run=len(self.duplicates),
            
            # Mode and queries
            mode=self.mode,
            broad_queries_used=self.broad_queries_used,
            tech_queries_used=self.tech_queries_used,
            
            # Targets
            target_tech_ratio=self.target_tech_ratio,
            max_jobs_per_run=self.max_jobs_per_run
        )
    
    def get_result(self) -> AcquisitionResult:
        """Get the final acquisition result."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        # Filter unique jobs (handle both dict and object)
        unique_jobs = []
        for job in self.all_jobs:
            if isinstance(job, dict):
                is_dup = job.get('_is_duplicate', False)
            else:
                is_dup = getattr(job, '_is_duplicate', False)
            
            if not is_dup:
                unique_jobs.append(job)
        
        result = AcquisitionResult(
            jobs=self.all_jobs,
            tech_intent_jobs=self.tech_intent_jobs,
            broad_intent_jobs=self.broad_intent_jobs,
            tech_classified_jobs=self.tech_classified_jobs,
            non_tech_classified_jobs=self.non_tech_classified_jobs,
            unclassified_jobs=self.unclassified_jobs,
            unique_jobs=unique_jobs,
            duplicates=self.duplicates,
            initial_composition=self.initial_composition,
            final_composition=self.projected_composition,
            mode=self.mode,
            mode_changed=self.mode_changed,
            broad_queries_used=self.broad_queries_used,
            tech_queries_used=self.tech_queries_used,
            target_tech_ratio=self.target_tech_ratio,
            duration_seconds=duration,
            query_metrics=self.query_metrics,
        )
        result.compute_metrics()
        return result
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information."""
        stats = self.get_stats()
        return {
            'db_total': stats.db_total,
            'db_tech': stats.db_tech,
            'db_non_tech': stats.db_non_tech,
            'db_tech_ratio': stats.db_tech_ratio,
            'db_has_parity': stats.db_has_parity,
            'tech_deficit': stats.tech_deficit,
            'projected_tech': self.projected_composition.tech_count,
            'projected_non_tech': self.projected_composition.non_tech_count,
            'projected_has_parity': self.projected_composition.has_reached_parity(self.parity_tolerance),
            'tech_intent_acquired': stats.tech_intent_acquired,
            'tech_classified_acquired': stats.tech_classified_acquired,
            'non_tech_classified_acquired': stats.non_tech_classified_acquired,
            'mode': stats.mode.value if hasattr(stats.mode, 'value') else str(stats.mode),
            'mode_changed': self.mode_changed,
            'remaining_tech_needed': stats.remaining_tech_needed,
            'query_count': self.query_count,
            'target_tech_ratio': stats.target_tech_ratio,
            'max_jobs_per_run': stats.max_jobs_per_run,
            'broad_queries_used': stats.broad_queries_used,
            'tech_queries_used': stats.tech_queries_used,
            'jobs_acquired': stats.jobs_acquired_this_run,
            # Query metrics
            'query_metrics': self.query_metrics[-10:],
            'total_queries': len(self.query_metrics),
        }
    
    def reset(self):
        """Reset the controller state."""
        self.broad_index = 0
        self.tech_index = 0
        self.used_query_keys = set()
        self.seen_job_ids = set()
        self.all_jobs = []
        self.tech_intent_jobs = []
        self.broad_intent_jobs = []
        self.tech_classified_jobs = []
        self.non_tech_classified_jobs = []
        self.unclassified_jobs = []
        self.duplicates = []
        self.broad_queries_used = 0
        self.tech_queries_used = 0
        
        # Reset all query tracking state
        self.current_query = None
        self.current_query_start_time = None
        self.current_query_new_jobs = 0
        self.current_query_classified = 0
        self.current_query_tech = 0
        self.current_query_non_tech = 0
        self.current_query_unclassified = 0
        self.current_query_mode = None
        self.query_metrics = []
        self.query_count = 0
        self.mode_changed = False
        
        # Reset balanced mode tracking
        self.balanced_mode_tech_start = 0
        self.balanced_mode_broad_start = 0
        
        self.start_time = datetime.now()
        logger.info("AcquisitionController reset")