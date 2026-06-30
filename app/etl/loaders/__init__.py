# app/etl/loaders/__init__.py
"""Data loaders for persisting validated data."""

from app.etl.loaders.job_loader import JobLoader, LoadResult

__all__ = ["JobLoader", "LoadResult"]