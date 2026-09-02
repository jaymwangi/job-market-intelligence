"""Unit tests for SkillRepository."""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.repositories.skill_repository import SkillRepository


class TestSkillRepository:
    """Test SkillRepository through the current BaseRepository contract."""

    @pytest.fixture
    def repository(self, db_session: Session):
        """Create repository using the test database session."""
        return SkillRepository(db_session)

    @pytest.fixture
    def create_test_skills(self, db_session: Session):
        """Create skills in the test database."""

        def _create_skills(names: list[str]) -> list[Skill]:
            skills = [Skill(name=name) for name in names]
            db_session.add_all(skills)
            db_session.flush()
            return skills

        return _create_skills

    def test_repository_uses_skill_model(self, repository):
        """Test repository is configured for the Skill model."""
        assert repository.model is Skill

    def test_create_skill(self, repository):
        """Test inherited create method."""
        skill = repository.create(name="Python")

        assert isinstance(skill, Skill)
        assert skill.name == "Python"
        assert skill.id is not None

    def test_get_skill_by_name(self, repository):
        """Test inherited get method."""
        created = repository.create(name="Python")

        result = repository.get(name="Python")

        assert result is not None
        assert result.id == created.id
        assert result.name == "Python"

    def test_get_skill_by_name_not_found(self, repository):
        """Test get returns None when skill does not exist."""
        result = repository.get(name="Python")

        assert result is None

    def test_get_by_id(self, repository):
        """Test inherited get_by_id method."""
        created = repository.create(name="Python")

        result = repository.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Python"

    def test_get_by_id_not_found(self, repository):
        """Test get_by_id returns None for missing ID."""
        result = repository.get_by_id(uuid4())

        assert result is None

    def test_find_all_skills(self, repository, create_test_skills):
        """Test inherited find_all method."""
        create_test_skills(["Python", "JavaScript", "Java"])

        skills = repository.find_all(order_by="name")

        assert len(skills) == 3
        assert [skill.name for skill in skills] == [
            "Java",
            "JavaScript",
            "Python",
        ]

    def test_find_all_with_filter(self, repository, create_test_skills):
        """Test find_all with a model field filter."""
        create_test_skills(["Python", "JavaScript", "Java"])

        skills = repository.find_all(name="Python")

        assert len(skills) == 1
        assert skills[0].name == "Python"

    def test_find_paginated(self, repository, create_test_skills):
        """Test inherited pagination method."""
        create_test_skills(["Python", "JavaScript", "Java"])

        skills = repository.find_paginated(
            skip=0,
            limit=2,
            order_by="name",
        )

        assert len(skills) == 2
        assert [skill.name for skill in skills] == [
            "Java",
            "JavaScript",
        ]

    def test_find_paginated_with_offset(self, repository, create_test_skills):
        """Test pagination offset."""
        create_test_skills(["Python", "JavaScript", "Java"])

        skills = repository.find_paginated(
            skip=1,
            limit=1,
            order_by="name",
        )

        assert len(skills) == 1
        assert skills[0].name == "JavaScript"

    def test_find_all_descending(self, repository, create_test_skills):
        """Test descending ordering."""
        create_test_skills(["Python", "JavaScript", "Java"])

        skills = repository.find_all(
            order_by="name",
            descending=True,
        )

        assert [skill.name for skill in skills] == [
            "Python",
            "JavaScript",
            "Java",
        ]

    def test_bulk_create_skills(self, repository):
        """Test inherited bulk_create method."""
        skills = repository.bulk_create(
            [
                {"name": "Go"},
                {"name": "Rust"},
                {"name": "TypeScript"},
            ]
        )

        assert len(skills) == 3
        assert [skill.name for skill in skills] == [
            "Go",
            "Rust",
            "TypeScript",
        ]
        assert all(skill.id is not None for skill in skills)

    def test_exists_true(self, repository):
        """Test inherited exists method when skill exists."""
        repository.create(name="Python")

        assert repository.exists(name="Python") is True

    def test_exists_false(self, repository):
        """Test inherited exists method when skill does not exist."""
        assert repository.exists(name="Python") is False

    def test_count(self, repository, create_test_skills):
        """Test inherited count method."""
        create_test_skills(["Python", "JavaScript", "Java"])

        assert repository.count() == 3

    def test_count_with_filter(self, repository, create_test_skills):
        """Test count with filters."""
        create_test_skills(["Python", "JavaScript", "Java"])

        assert repository.count(name="Python") == 1
    

    def test_update_skill(self, repository):
        """Test inherited update method."""
        skill = repository.create(name="Python")

        updated = repository.update(
            skill.id,
            name="Python 3",
        )

        assert updated is not None
        assert updated.id == skill.id
        assert updated.name == "Python 3"

    def test_update_missing_skill(self, repository):
        """Test update returns None for missing skill."""
        result = repository.update(
            uuid4(),
            name="Python",
        )

        assert result is None

    def test_delete_skill(self, repository):
        """Test inherited delete method."""
        skill = repository.create(name="Python")

        result = repository.delete(skill.id)

        assert result is True
        assert repository.get_by_id(skill.id) is None

    def test_delete_missing_skill(self, repository):
        """Test delete returns False for missing skill."""
        result = repository.delete(uuid4())

        assert result is False

