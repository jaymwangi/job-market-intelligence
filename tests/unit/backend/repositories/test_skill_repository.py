"""
Unit tests for skill repository.
"""

import pytest

from app.repositories.skill_repository import SkillRepository


class TestSkillRepository:
    """Test suite for skill repository operations."""

    @pytest.fixture
    def repository(self, db_session):
        return SkillRepository(db_session)

    def test_create_skill(self, repository):
        """Test creating a skill."""
        skill = repository.create(name="Python", category="Programming Language")

        assert skill.id is not None
        assert skill.name == "Python"
        assert skill.category == "Programming Language"

    def test_get_skill_by_id(self, repository, create_test_skills):
        """Test retrieving skill by ID."""
        skills = create_test_skills(["Python"])
        skill_id = skills[0].id

        skill = repository.get_by_id(skill_id)
        assert skill is not None
        assert skill.name == "Python"

    def test_get_skill_by_name(self, repository, create_test_skills):
        """Test retrieving skill by name."""
        create_test_skills(["Python", "JavaScript"])

        skill = repository.get_by_name("Python")
        assert skill is not None
        assert skill.name == "Python"

        skill = repository.get_by_name("NonExistent")
        assert skill is None

    def test_get_all_skills(self, repository, create_test_skills):
        """Test retrieving all skills."""
        create_test_skills(["Python", "JavaScript", "Java"])

        skills = repository.get_all()
        assert len(skills) == 3

    def test_get_skills_by_category(self, repository, create_test_skills):
        """Test retrieving skills by category."""
        create_test_skills(["Python", "JavaScript"])

        skills = repository.get_by_category("Programming Language")
        assert len(skills) == 2

    def test_update_skill(self, repository, create_test_skills):
        """Test updating a skill."""
        skills = create_test_skills(["Python"])
        skill_id = skills[0].id

        updated = repository.update(skill_id, category="Backend Language")
        assert updated.category == "Backend Language"

    def test_delete_skill(self, repository, create_test_skills):
        """Test deleting a skill."""
        skills = create_test_skills(["Python"])
        skill_id = skills[0].id

        result = repository.delete(skill_id)
        assert result is True

        deleted = repository.get_by_id(skill_id)
        assert deleted is None

    def test_bulk_create_skills(self, repository):
        """Test bulk creating skills."""
        skill_names = ["Go", "Rust", "TypeScript"]
        skills = repository.bulk_create(skill_names)

        assert len(skills) == 3
        assert all(skill.id is not None for skill in skills)

    def test_get_or_create(self, repository):
        """Test get or create skill."""
        # First call - create
        skill, created = repository.get_or_create("Python")
        assert created is True
        assert skill.id is not None

        # Second call - get existing
        skill, created = repository.get_or_create("Python")
        assert created is False
        assert skill.id is not None

    def test_get_skill_counts(self, repository, create_test_skills):
        """Test getting skill counts."""
        create_test_skills(["Python", "JavaScript", "Java"])

        counts = repository.get_counts()
        assert counts["Programming Language"] == 3
