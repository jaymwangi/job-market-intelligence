# app/models/__init__.py
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.pipeline_run import PipelineRun
from app.models.skill import Skill

# Import all models so Alembic can detect them
__all__ = [
    "Job",
    "Skill",
    "JobSkill",
    "PipelineRun",
]
