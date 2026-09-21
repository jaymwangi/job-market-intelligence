import json

import pytest

from app.etl.enrichment.skill_extractor import SkillExtractor


class TestSkillExtractor:
    def test_initializes_with_default_keywords(self):
        extractor = SkillExtractor()

        assert extractor.keywords
        assert extractor.patterns

    def test_initializes_with_custom_keywords(self):
        extractor = SkillExtractor(keywords=["Python", "SQL"])

        assert extractor.keywords == {"python", "sql"}
        assert set(extractor.patterns) == {"python", "sql"}

    def test_loads_keywords_from_json_list(self, tmp_path):
        data_file = tmp_path / "skills.json"
        data_file.write_text(json.dumps(["Python", "SQL", "Docker"]))

        extractor = SkillExtractor(
            keywords=["Fallback"],
            data_path=str(data_file),
        )

        assert extractor.keywords == {"Python", "SQL", "Docker"}

    def test_loads_keywords_from_json_dict(self, tmp_path):
        data_file = tmp_path / "skills.json"
        data_file.write_text(
            json.dumps({"skills": ["Python", "SQL", "Docker"]})
        )

        extractor = SkillExtractor(
            keywords=["Fallback"],
            data_path=str(data_file),
        )

        assert extractor.keywords == {"Python", "SQL", "Docker"}

    def test_falls_back_when_data_file_does_not_exist(self, tmp_path):
        missing_file = tmp_path / "missing.json"

        extractor = SkillExtractor(
            keywords=["Python", "SQL"],
            data_path=str(missing_file),
        )

        assert extractor.keywords == {"python", "sql"}

    def test_falls_back_when_json_is_invalid(self, tmp_path):
        data_file = tmp_path / "skills.json"
        data_file.write_text("{invalid json")

        extractor = SkillExtractor(
            keywords=["Python", "SQL"],
            data_path=str(data_file),
        )

        assert extractor.keywords == {"python", "sql"}

    def test_falls_back_when_json_has_unsupported_structure(self, tmp_path):
        data_file = tmp_path / "skills.json"
        data_file.write_text(json.dumps({"other": ["Python"]}))

        extractor = SkillExtractor(
            keywords=["Python", "SQL"],
            data_path=str(data_file),
        )

        assert extractor.keywords == {"python", "sql"}

    def test_extract_skills_from_title_and_description(self):
        extractor = SkillExtractor(
            keywords=["python", "sql", "docker"]
        )

        result = extractor.extract_skills(
            "Python Developer",
            "Experience with SQL and Docker required.",
        )

        assert result == ["docker", "python", "sql"]

    def test_extract_skills_is_case_insensitive(self):
        extractor = SkillExtractor(keywords=["python", "sql"])

        result = extractor.extract_skills(
            "PYTHON DEVELOPER",
            "SQL experience required.",
        )

        assert result == ["python", "sql"]

    def test_extract_skills_does_not_match_partial_words(self):
        extractor = SkillExtractor(keywords=["sql", "java"])

        result = extractor.extract_skills(
            "SQL Developer",
            "Experience with JavaScript.",
        )

        assert result == ["sql"]

    def test_extract_skills_returns_sorted_unique_skills(self):
        extractor = SkillExtractor(
            keywords=["python", "sql", "docker"]
        )

        result = extractor.extract_skills(
            "Python Python Developer",
            "Python and SQL. Docker experience.",
        )

        assert result == ["docker", "python", "sql"]

    def test_extract_skills_returns_empty_when_no_skill_found(self):
        extractor = SkillExtractor(keywords=["python", "sql"])

        assert extractor.extract_skills(
            "Marketing Manager",
            "Experience in sales and communication.",
        ) == []

    def test_extract_from_title(self):
        extractor = SkillExtractor(
            keywords=["python", "sql", "docker"]
        )

        assert extractor.extract_from_title("Senior Python Developer") == ["python"]

    def test_extract_from_title_does_not_use_description(self):
        extractor = SkillExtractor(keywords=["python", "sql"])

        assert extractor.extract_from_title("Senior Developer") == []
