from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query, Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository with common CRUD operations.
    Assumes valid field names - no silent hasattr() checks.
    """

    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db

    def _build_query(self, **filters) -> Query:
        """Build a query with filters applied"""
        query = self.db.query(self.model)
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self.model, key) == value)
        return query

    def create(self, **kwargs) -> ModelType:
        """Create a new record"""
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.flush()
        return instance

    def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelType]:
        """Bulk create multiple records"""
        instances = [self.model(**item) for item in items]
        self.db.add_all(instances)
        self.db.flush()
        return instances

    def get(self, **filters) -> ModelType | None:
        """Get single record by filters"""
        return self._build_query(**filters).first()

    def get_by_id(self, id: UUID) -> ModelType | None:
        """Get record by primary key"""
        return self._build_query(id=id).first()

    def find_all(
        self, order_by: str | None = None, descending: bool = False, **filters
    ) -> list[ModelType]:
        """Find all records matching filters, with optional ordering"""
        query = self._build_query(**filters)

        if order_by:
            column = getattr(self.model, order_by)
            query = query.order_by(desc(column) if descending else asc(column))

        return query.all()

    def find_paginated(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        descending: bool = False,
        **filters,
    ) -> list[ModelType]:
        """Find records with pagination"""
        query = self._build_query(**filters)

        if order_by:
            column = getattr(self.model, order_by)
            query = query.order_by(desc(column) if descending else asc(column))

        return query.offset(skip).limit(limit).all()

    def update(self, id: UUID, **kwargs) -> ModelType | None:
        """Update a record by ID"""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.db.flush()
        return instance

    def delete(self, id: UUID) -> bool:
        """Delete a record by ID"""
        instance = self.get_by_id(id)
        if instance:
            self.db.delete(instance)
            self.db.flush()
            return True
        return False

    def exists(self, **filters) -> bool:
        """Check if any record exists matching filters"""
        return self.db.query(self._build_query(**filters).exists()).scalar()

    def count(self, **filters) -> int:
        """Count records matching filters"""
        return self._build_query(**filters).count()
