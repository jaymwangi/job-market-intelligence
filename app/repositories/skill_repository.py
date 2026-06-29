# app/repositories/skill_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.repositories.base import BaseRepository

class SkillRepository(BaseRepository[Skill]):
    """
    Repository for Skill operations.
    Starts empty - methods added when Sprint 2+ reveals actual needs.
    """
    
    def __init__(self, db: Session):
        super().__init__(Skill, db)
    
    # No wrapper methods yet. Use BaseRepository directly:
    # - repo.create(name="Python")
    # - repo.get(name="Python")
    # - repo.find_all(order_by="name")
    # - repo.find_paginated(order_by="name", skip=0, limit=50)
    # - repo.exists(name="Python")