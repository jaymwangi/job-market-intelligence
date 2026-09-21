"""Unit tests for the technology lexicon."""

from app.etl.enrichment.classification_config import CategoryConfig, CategoryRole
from app.etl.enrichment.technology_lexicon import (
    TechnologyLexicon,
    TechnologyMatch,
)


def make_category(
    category_id: str,
    keywords: list[str],
) -> CategoryConfig:
    return CategoryConfig(
        id=category_id,
        display_name=category_id.title(),
        icon="test",
        color="#000000",
        description=f"Test category: {category_id}",
        family="test",
        is_tech=True,
        weight=1.0,
        keywords={keyword: 1 for keyword in keywords},
        role=CategoryRole.STANDALONE,
    )


class FakeConfig:
    """Minimal configuration required by TechnologyLexicon."""

    def __init__(self):
        self.categories = {
            "backend": make_category(
                "backend",
                ["python", "django", "node.js"],
            ),
            "frontend": make_category(
                "frontend",
                ["react", "typescript"],
            ),
        }
        self.aliases = {
            "py": "python",
            "nodejs": "node.js",
            "ts": "typescript",
        }


class TestTechnologyLexicon:
    def test_builds_term_to_category_mapping(self):
        lexicon = TechnologyLexicon(FakeConfig())

        assert lexicon.term_to_category == {
            "python": "backend",
            "django": "backend",
            "node.js": "backend",
            "react": "frontend",
            "typescript": "frontend",
        }

    def test_builds_alias_map_and_adds_canonical_terms(self):
        lexicon = TechnologyLexicon(FakeConfig())

        assert lexicon.alias_to_canonical["py"] == "python"
        assert lexicon.alias_to_canonical["nodejs"] == "node.js"
        assert lexicon.alias_to_canonical["ts"] == "typescript"

        assert lexicon.alias_to_canonical["python"] == "python"
        assert lexicon.alias_to_canonical["django"] == "django"

    def test_builds_case_insensitive_alias_map(self):
        config = FakeConfig()
        config.aliases = {"PY": "Python"}

        lexicon = TechnologyLexicon(config)

        assert lexicon.alias_to_canonical["py"] == "python"

    def test_compiles_regex_with_terms_and_aliases(self):
        lexicon = TechnologyLexicon(FakeConfig())

        assert lexicon._compiled_regex.search("Python") is not None
        assert lexicon._compiled_regex.search("py") is not None
        assert lexicon._compiled_regex.search("React") is not None

    def test_find_technologies_returns_matches(self):
        lexicon = TechnologyLexicon(FakeConfig())

        matches = lexicon.find_technologies(
            "Python developer using React and Django"
        )

        assert matches == [
            TechnologyMatch(
                term="python",
                canonical="python",
                category="backend",
                start=0,
                end=6,
            ),
            TechnologyMatch(
                term="react",
                canonical="react",
                category="frontend",
                start=23,
                end=28,
            ),
            TechnologyMatch(
                term="django",
                canonical="django",
                category="backend",
                start=33,
                end=39,
            ),
        ]

    def test_find_technologies_resolves_aliases(self):
        lexicon = TechnologyLexicon(FakeConfig())

        matches = lexicon.find_technologies(
            "Experienced PY developer with nodejs and TS"
        )

        assert [match.canonical for match in matches] == [
            "python",
            "node.js",
            "typescript",
        ]

        assert [match.category for match in matches] == [
            "backend",
            "backend",
            "frontend",
        ]

    def test_find_technologies_is_case_insensitive(self):
        lexicon = TechnologyLexicon(FakeConfig())

        matches = lexicon.find_technologies("PYTHON REACT")

        assert [match.term for match in matches] == [
            "python",
            "react",
        ]

    def test_find_technologies_deduplicates_canonical_terms(self):
        lexicon = TechnologyLexicon(FakeConfig())

        matches = lexicon.find_technologies(
            "Python developer using py and Python"
        )

        assert len(matches) == 1
        assert matches[0].canonical == "python"

    def test_find_technologies_does_not_match_partial_words(self):
        lexicon = TechnologyLexicon(FakeConfig())

        matches = lexicon.find_technologies(
            "pythonic reactivate developer"
        )

        assert matches == []

    def test_find_technologies_returns_empty_for_no_matches(self):
        lexicon = TechnologyLexicon(FakeConfig())

        assert lexicon.find_technologies(
            "Project manager with accounting experience"
        ) == []

    def test_unknown_alias_can_produce_unknown_category(self):
        config = FakeConfig()
        config.aliases["unknown-tech"] = "unknown-tech"

        lexicon = TechnologyLexicon(config)

        matches = lexicon.find_technologies("unknown-tech")

        assert len(matches) == 1
        assert matches[0].canonical == "unknown-tech"
        assert matches[0].category == "unknown"

    def test_get_canonical_terms(self):
        lexicon = TechnologyLexicon(FakeConfig())

        assert set(lexicon.get_canonical_terms()) == {
            "python",
            "django",
            "node.js",
            "react",
            "typescript",
        }

    def test_get_aliases_returns_copy(self):
        lexicon = TechnologyLexicon(FakeConfig())

        aliases = lexicon.get_aliases()
        aliases["py"] = "changed"

        assert lexicon.alias_to_canonical["py"] == "python"

    def test_stats_returns_lexicon_counts(self):
        lexicon = TechnologyLexicon(FakeConfig())

        stats = lexicon.stats()

        assert stats == {
            "canonical_terms": 5,
            "aliases": 8,
            "categories": 2,
        }


def test_get_lexicon_returns_singleton(monkeypatch):
    import app.etl.enrichment.technology_lexicon as module

    class FakeLoadedConfig(FakeConfig):
        pass

    monkeypatch.setattr(
        module,
        "_lexicon",
        None,
    )

    monkeypatch.setattr(
        "app.etl.enrichment.classification_config.get_config",
        lambda: FakeLoadedConfig(),
    )

    first = module.get_lexicon()
    second = module.get_lexicon()

    assert first is second