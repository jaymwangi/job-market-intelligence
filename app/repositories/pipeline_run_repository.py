# app/repositories/pipeline_run_repository.py
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.pipeline_run import PipelineRun
from app.repositories.base import BaseRepository

class PipelineRunRepository(BaseRepository[PipelineRun]):
    """
    Repository for PipelineRun operations.
    Starts empty - methods added when Sprint 2+ reveals actual needs.
    """
    
    def __init__(self, db: Session):
        super().__init__(PipelineRun, db)
    
    # No wrapper methods yet. Use BaseRepository directly:
    # - repo.create(pipeline_name="scraper", status="running", ...)
    # - repo.update(run_id, status="completed", completed_at=datetime.utcnow())
    # - repo.find_all(status="failed")
    # - repo.find_paginated(status="failed", order_by="started_at", descending=True)