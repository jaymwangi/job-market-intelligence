# app/repositories/job_repository.py
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.job import Job
from app.repositories.base import BaseRepository

class JobRepository(BaseRepository[Job]):
    """
    Repository for Job operations.
    Starts empty - methods added when Sprint 2+ reveals actual needs.
    """
    
    def __init__(self, db: Session):
        super().__init__(Job, db)
    
    # No wrapper methods yet. Use BaseRepository directly:
    # - repo.create(external_id="...", title="...", ...)
    # - repo.get_by_id(id)
    # - repo.exists(external_id="...")
    # - repo.find_all(source="linkedin")
    # - repo.find_paginated(source="linkedin", skip=0, limit=50)
    # - repo.update(id, is_active=False)
    # - repo.delete(id)