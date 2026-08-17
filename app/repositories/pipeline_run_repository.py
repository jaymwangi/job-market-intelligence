"""Pipeline run repository for tracking ETL runs."""

import logging
from datetime import UTC, datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.pipeline_run import PipelineRun

# Setup logger
logger = logging.getLogger(__name__)


class PipelineRunRepository:
    """Repository for PipelineRun model operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        source_site: str,
        started_at: datetime | None = None,
        status: str = "running",
    ) -> PipelineRun:
        """Create a new pipeline run."""
        if started_at is None:
            started_at = datetime.now(UTC)

        run = PipelineRun(
            source_site=source_site,
            started_at=started_at,
            status=status,
            records_processed=0,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def finish(
        self,
        run: PipelineRun,
        status: str,
        records_processed: int = 0,
        error_message: str | None = None,
    ) -> PipelineRun:
        """Finish a pipeline run with results."""
        run.completed_at = datetime.now(UTC)
        run.status = status
        run.records_processed = records_processed

        # Calculate duration in seconds using local variables
        started = run.started_at
        completed = run.completed_at
        if started is not None and completed is not None:
            run.duration_seconds = (completed - started).total_seconds()

        if error_message:
            run.error_message = error_message

        self.session.flush()
        return run

    # ============================================================
    # ETL Status Methods - For Dashboard Overview
    # ============================================================

    def get_latest_completed_run(self) -> Optional[Dict]:
        """
        Get the most recent completed pipeline run.
        Returns dict with all fields from the pipeline_runs table.
        """
        try:
            result = self.session.execute(
                text("""
                    SELECT 
                        id,
                        started_at,
                        completed_at,
                        status,
                        records_processed,
                        duration_seconds,
                        error_message,
                        source_site,
                        created_at,
                        updated_at
                    FROM pipeline_runs 
                    WHERE status IN ('completed', 'failed')
                    ORDER BY completed_at DESC, started_at DESC
                    LIMIT 1
                """)
            )
            row = result.fetchone()
            if row:
                # Convert row to dict
                return {
                    'id': row[0],
                    'started_at': row[1],
                    'completed_at': row[2],
                    'status': row[3],
                    'records_processed': row[4],
                    'duration_seconds': row[5],
                    'error_message': row[6],
                    'source_site': row[7],
                    'created_at': row[8],
                    'updated_at': row[9],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting latest completed run: {e}")
            return None

    def get_running_run(self) -> Optional[Dict]:
        """
        Check if there's a currently running pipeline.
        Returns dict with all fields from the pipeline_runs table.
        """
        try:
            result = self.session.execute(
                text("""
                    SELECT 
                        id,
                        started_at,
                        completed_at,
                        status,
                        records_processed,
                        duration_seconds,
                        error_message,
                        source_site,
                        created_at,
                        updated_at
                    FROM pipeline_runs 
                    WHERE status = 'running'
                    ORDER BY started_at DESC
                    LIMIT 1
                """)
            )
            row = result.fetchone()
            if row:
                return {
                    'id': row[0],
                    'started_at': row[1],
                    'completed_at': row[2],
                    'status': row[3],
                    'records_processed': row[4],
                    'duration_seconds': row[5],
                    'error_message': row[6],
                    'source_site': row[7],
                    'created_at': row[8],
                    'updated_at': row[9],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting running run: {e}")
            return None

    def get_last_run_time(self) -> Optional[datetime]:
        """Get the time of the last completed run."""
        run = self.get_latest_completed_run()
        if run:
            return run.get('completed_at') or run.get('started_at')
        return None

    def format_last_run_time(self) -> str:
        """
        Get formatted last run time (e.g., '2 hours ago').
        Uses the completed_at time from the latest completed run.
        """
        run = self.get_latest_completed_run()
        
        if not run:
            logger.debug("No completed runs found in pipeline_runs table")
            return "No runs yet"
        
        # Use completed_at if available, otherwise started_at
        last_time = run.get('completed_at') or run.get('started_at')
        
        if not last_time:
            return "No runs yet"
        
        # Ensure it's a datetime
        if isinstance(last_time, str):
            try:
                # Use datetime.fromisoformat directly
                last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
            except ValueError:
                return "Invalid date"
        
        now = datetime.now(UTC)
        
        # Handle timezone-aware comparison
        if last_time.tzinfo is None:
            # If last_time is naive, make it UTC-aware
            last_time = last_time.replace(tzinfo=UTC)
        
        delta = now - last_time
        
        # Format the time difference
        if delta.days > 0:
            return f"{delta.days}d {delta.seconds//3600}h ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}h {minutes}m ago"
            return f"{hours}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds//60}m ago"
        else:
            return "Just now"