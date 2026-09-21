import pytest
from pathlib import Path

from app.etl.enrichment.classification_config import (
    CategoryRole,
    ClassificationConfigLoader,
    ConfigurationError,
    TitlePatternConfig,
    competes,
    get_all_parents,
    get_all_specializations,
    get_category_config,
    get_children,
    get_classification_settings,
    get_competing_categories,
    get_compiled_title_patterns,
    get_config,
    get_effective_thresholds,
    get_parent,
    get_role,
    get_tech_title_patterns,
    is_parent,
    is_specialization,
    is_stopword,
    normalize_keyword,
    reload_config,
)
from dataclasses import replace

def test_title_pattern_config_defaults():
    config = TitlePatternConfig(pattern=r"\bpython\b")

    assert config.pattern == r"\bpython\b"
    assert config.categories == ()
    assert config.weight == 8.0
    assert config.strength == "potential"
    assert config.specificity == "medium"


def test_title_pattern_config_converts_list_categories_to_tuple():
    config = TitlePatternConfig(
        pattern=r"\bpython\b",
        categories=["backend", "ml_ai"],  # pyright: ignore[reportArgumentType]
    )

    assert config.categories == ("backend", "ml_ai")
    assert isinstance(config.categories, tuple)


def test_title_pattern_config_properties():
    strong = TitlePatternConfig(
        pattern="python",
        strength="strong",
        specificity="high",
    )
    potential = TitlePatternConfig(
        pattern="data",
        strength="potential",
        specificity="medium",
    )
    adjacent = TitlePatternConfig(
        pattern="analyst",
        strength="adjacent",
        specificity="low",
    )
    ambiguous = TitlePatternConfig(
        pattern="developer",
        strength="ambiguous",
        specificity="medium",
    )

    assert strong.is_strong is True
    assert strong.is_potential is False
    assert strong.is_adjacent is False
    assert strong.is_ambiguous is False
    assert strong.strength_priority == 4

    assert potential.is_strong is False
    assert potential.is_potential is True
    assert potential.strength_priority == 3

    assert adjacent.is_adjacent is True
    assert adjacent.strength_priority == 2

    assert ambiguous.is_ambiguous is True
    assert ambiguous.strength_priority == 1


def test_title_pattern_config_unknown_strength_has_zero_priority():
    config = TitlePatternConfig(
        pattern="python",
        strength="unknown",
    )

    assert config.strength_priority == 0


@pytest.mark.parametrize("pattern", ["", None])
def test_title_pattern_config_rejects_empty_or_non_string_pattern(pattern):
    with pytest.raises(ConfigurationError):
        TitlePatternConfig(pattern=pattern)


def test_title_pattern_config_rejects_invalid_regex():
    with pytest.raises(ConfigurationError):
        TitlePatternConfig(pattern="[")


def test_title_pattern_config_accepts_valid_regex():
    config = TitlePatternConfig(pattern=r"(?i)\bpython(?:\s+developer)?\b")

    assert config.pattern == r"(?i)\bpython(?:\s+developer)?\b"


def test_normalize_alias_table_strips_and_lowercases_aliases_and_targets():
    result = ClassificationConfigLoader._normalize_alias_table(
        {
            " Python ": " PYTHON3 ",
            " JS ": " JavaScript ",
        }
    )

    assert result == {
        "python": "python3",
        "js": "javascript",
    }


def test_normalize_alias_table_allows_many_aliases_to_one_target():
    result = ClassificationConfigLoader._normalize_alias_table(
        {
            "js": "javascript",
            "ecmascript": "javascript",
        }
    )

    assert result == {
        "js": "javascript",
        "ecmascript": "javascript",
    }


@pytest.mark.parametrize(
    ("aliases", "message"),
    [
        ({"   ": "python"}, "Empty alias key"),
        ({"python": "   "}, "Empty alias target"),
    ],
)
def test_normalize_alias_table_rejects_empty_alias_or_target(aliases, message):
    with pytest.raises(ConfigurationError, match=message):
        ClassificationConfigLoader._normalize_alias_table(aliases)


def test_normalize_alias_table_rejects_duplicate_normalized_alias():
    with pytest.raises(ConfigurationError, match="Duplicate alias key"):
        ClassificationConfigLoader._normalize_alias_table(
            {
                "Python": "python",
                " python ": "python3",
            }
        )


def test_normalize_keywords_normalizes_keywords_and_applies_aliases():
    result = ClassificationConfigLoader._normalize_keywords(
        {
            " Python ": 5,
            " JS ": 3,
        },
        {
            "python": "python3",
            "js": "javascript",
        },
        "backend",
    )

    assert result == {
        "python3": 5,
        "javascript": 3,
    }


def test_normalize_keywords_merges_weights_after_alias_collision():
    result = ClassificationConfigLoader._normalize_keywords(
        {
            "python": 5,
            "Python ": 3,
            "py": 2,
        },
        {
            "python": "python",
            "py": "python",
        },
        "backend",
    )

    assert result == {
        "python": 10,
    }


@pytest.mark.parametrize("weight", [0, -1, -0.5])
def test_normalize_keywords_rejects_non_positive_weights(weight):
    with pytest.raises(ConfigurationError, match="non-positive weight"):
        ClassificationConfigLoader._normalize_keywords(
            {"python": weight},
            {},
            "backend",
        )


@pytest.mark.parametrize("weight", [True, False, "5", None, object()])
def test_normalize_keywords_rejects_non_numeric_weights(weight):
    with pytest.raises(ConfigurationError, match="non-numeric weight"):
        ClassificationConfigLoader._normalize_keywords(
            {"python": weight},
            {},
            "backend",
        )


def test_parse_title_patterns_parses_string_pattern_with_defaults():
    result = ClassificationConfigLoader._parse_title_patterns(
        [r"\bpython\b"]
    )

    assert len(result) == 1
    assert result[0].pattern == r"\bpython\b"
    assert result[0].categories == ()
    assert result[0].weight == 8.0
    assert result[0].strength == "potential"
    assert result[0].specificity == "medium"


def test_parse_title_patterns_parses_full_dict_configuration():
    result = ClassificationConfigLoader._parse_title_patterns(
        [
            {
                "pattern": r"\bmachine learning\b",
                "categories": ["ml_ai", "data"],
                "weight": 12,
                "strength": "strong",
                "specificity": "high",
            }
        ]
    )

    assert len(result) == 1
    assert result[0].pattern == r"\bmachine learning\b"
    assert result[0].categories == ("ml_ai", "data")
    assert result[0].weight == 12.0
    assert result[0].strength == "strong"
    assert result[0].specificity == "high"


def test_parse_title_patterns_applies_dict_defaults():
    result = ClassificationConfigLoader._parse_title_patterns(
        [{"pattern": "developer"}]
    )

    assert result[0].categories == ()
    assert result[0].weight == 8.0
    assert result[0].strength == "potential"
    assert result[0].specificity == "medium"


def test_parse_title_patterns_rejects_invalid_pattern_type():
    with pytest.raises(ConfigurationError, match="Invalid title pattern type"):
        ClassificationConfigLoader._parse_title_patterns([123])


def test_parse_title_patterns_parses_multiple_patterns():
    result = ClassificationConfigLoader._parse_title_patterns(
        [
            "python",
            {"pattern": "data scientist", "weight": 10},
        ]
    )

    assert len(result) == 2
    assert result[0].pattern == "python"
    assert result[1].pattern == "data scientist"


def test_parse_config_applies_category_defaults():
    config = ClassificationConfigLoader._parse_config(
        {
            "categories": {
                "backend": {},
            }
        }
    )

    category = config.categories["backend"]

    assert category.id == "backend"
    assert category.display_name == "Backend"
    assert category.icon == "🌐"
    assert category.color == "#6B7280"
    assert category.description == ""
    assert category.family == "other"
    assert category.is_tech is False
    assert category.weight == 1.0
    assert category.keywords == {}
    assert category.negative_keywords == []
    assert category.regex == []
    assert category.parent is None
    assert category.role == CategoryRole.STANDALONE
    assert category.strength == "potential"
    assert category.specificity == "medium"

    assert config.aliases == {}
    assert config.stopwords == set()
    assert config.tech_title_patterns == []
    assert config.classification == {}
    assert config.title_pattern_boost == 3.0


def test_parse_config_normalizes_aliases_and_category_keywords():
    config = ClassificationConfigLoader._parse_config(
        {
            "aliases": {
                "Py ": " Python ",
                "JS": "JavaScript",
            },
            "categories": {
                "backend": {
                    "keywords": {
                        "PY": 5,
                        "JS": 3,
                    }
                }
            },
        }
    )

    assert config.aliases == {
        "py": "python",
        "js": "javascript",
    }
    assert config.categories["backend"].keywords == {
        "python": 5,
        "javascript": 3,
    }


def test_parse_config_parses_category_fields_and_role():
    config = ClassificationConfigLoader._parse_config(
        {
            "categories": {
                "ml_ai": {
                    "id": "ml_ai",
                    "display_name": "Machine Learning & AI",
                    "icon": "🤖",
                    "color": "#123456",
                    "description": "Machine learning technologies",
                    "family": "ai",
                    "is_tech": True,
                    "weight": 2.5,
                    "keywords": {"python": 5},
                    "negative_keywords": ["nontechnical"],
                    "regex": [r"\bml\b"],
                    "parent": "data",
                    "role": "specialization",
                    "strength": "strong",
                    "specificity": "high",
                }
            }
        }
    )

    category = config.categories["ml_ai"]

    assert category.id == "ml_ai"
    assert category.display_name == "Machine Learning & AI"
    assert category.icon == "🤖"
    assert category.color == "#123456"
    assert category.description == "Machine learning technologies"
    assert category.family == "ai"
    assert category.is_tech is True
    assert category.weight == 2.5
    assert category.keywords == {"python": 5}
    assert category.negative_keywords == ["nontechnical"]
    assert category.regex == [r"\bml\b"]
    assert category.parent == "data"
    assert category.role == CategoryRole.SPECIALIZATION
    assert category.strength == "strong"
    assert category.specificity == "high"


def test_parse_config_builds_display_name_lookup():
    config = ClassificationConfigLoader._parse_config(
        {
            "categories": {
                "ml_ai": {
                    "display_name": "Machine Learning & AI",
                },
                "backend": {
                    "display_name": "Backend Development",
                },
            }
        }
    )

    assert config._display_name_lookup == {
        "machine learning & ai": "ml_ai",
        "backend development": "backend",
    }


def test_parse_config_parses_title_patterns_and_classification_settings():
    config = ClassificationConfigLoader._parse_config(
        {
            "version": "3.2.1",
            "last_updated": "2026-09-08",
            "weights": {"title": 0.5, "description": 0.3, "skills": 0.2},
            "thresholds": {},
            "boosts": {},
            "category_priority": ["backend"],
            "matching": {},
            "categories": {"backend": {}},
            "tech_title_patterns": [
                "python developer",
                {
                    "pattern": "data scientist",
                    "categories": ["ml_ai"],
                    "weight": 10,
                    "strength": "strong",
                    "specificity": "high",
                },
            ],
            "classification": {
                "enabled": True,
                "mode": "balanced",
            },
            "title_pattern_boost": 5.5,
        }
    )

    assert config.version == "3.2.1"
    assert config.last_updated == "2026-09-08"
    assert len(config.tech_title_patterns) == 2
    assert config.tech_title_patterns[0].pattern == "python developer"
    assert config.tech_title_patterns[1].categories == ("ml_ai",)
    assert config.tech_title_patterns[1].weight == 10.0
    assert config.tech_title_patterns[1].is_strong is True
    assert config.classification == {
        "enabled": True,
        "mode": "balanced",
    }
    assert config.title_pattern_boost == 5.5


def test_parse_config_rejects_invalid_category_role():
    with pytest.raises(ConfigurationError, match="Invalid role"):
        ClassificationConfigLoader._parse_config(
            {
                "categories": {
                    "backend": {
                        "role": "invalid-role",
                    }
                }
            }
        )


def test_build_taxonomy_builds_parent_child_and_role_indexes():
    config = ClassificationConfigLoader._parse_config(
        {
            "categories": {
                "data": {
                    "role": "parent",
                },
                "data_engineering": {
                    "role": "specialization",
                    "parent": "data",
                },
                "analytics": {
                    "role": "standalone",
                },
            }
        }
    )

    result = ClassificationConfigLoader._build_taxonomy(config)

    assert result is not config
    assert result._parents == {
        "data": None,
        "data_engineering": "data",
        "analytics": None,
    }
    assert result._roles == {
        "data": CategoryRole.PARENT,
        "data_engineering": CategoryRole.SPECIALIZATION,
        "analytics": CategoryRole.STANDALONE,
    }
    assert result._children == {
        "data": {"data_engineering"},
    }


def test_build_taxonomy_allows_parent_without_children():
    config = ClassificationConfigLoader._parse_config(
        {
            "categories": {
                "data": {
                    "role": "parent",
                }
            }
        }
    )

    result = ClassificationConfigLoader._build_taxonomy(config)

    assert result._parents == {"data": None}
    assert result._roles == {"data": CategoryRole.PARENT}
    assert result._children == {}


def test_build_taxonomy_rejects_missing_parent():
    config = ClassificationConfigLoader._parse_config(
        {
            "categories": {
                "data_engineering": {
                    "role": "specialization",
                    "parent": "data",
                }
            }
        }
    )

    with pytest.raises(ConfigurationError, match="references parent 'data'"):
        ClassificationConfigLoader._build_taxonomy(config)


def test_build_taxonomy_rejects_specialization_without_parent():
    config = ClassificationConfigLoader._parse_config(
        {
            "categories": {
                "data_engineering": {
                    "role": "specialization",
                }
            }
        }
    )

    with pytest.raises(
        ConfigurationError,
        match="Specialization 'data_engineering' must have a parent",
    ):
        ClassificationConfigLoader._build_taxonomy(config)


def test_build_taxonomy_preserves_existing_config_data():
    config = ClassificationConfigLoader._parse_config(
        {
            "version": "3.1.0",
            "last_updated": "2026-09-08",
            "weights": {"title": 0.5},
            "thresholds": {"tech_minimum": 0.5},
            "boosts": {"title_exact_match": 5},
            "category_priority": ["backend"],
            "matching": {"exact_weight": 1},
            "aliases": {"py": "python"},
            "stopwords": ["the"],
            "categories": {
                "backend": {},
            },
            "category_thresholds": {"backend": {"minimum": 0.5}},
            "classification": {"enabled": True},
            "title_pattern_boost": 4.0,
        }
    )

    result = ClassificationConfigLoader._build_taxonomy(config)

    assert result.version == config.version
    assert result.last_updated == config.last_updated
    assert result.weights == config.weights
    assert result.thresholds == config.thresholds
    assert result.boosts == config.boosts
    assert result.category_priority == config.category_priority
    assert result.matching == config.matching
    assert result.aliases == config.aliases
    assert result.stopwords == config.stopwords
    assert result.categories == config.categories
    assert result.category_thresholds == config.category_thresholds
    assert result.classification == config.classification
    assert result.title_pattern_boost == config.title_pattern_boost
def test_validate_version_accepts_supported_major():
    config = ClassificationConfigLoader.get_config()

    assert ClassificationConfigLoader._validate_version(config) == []


def test_validate_version_rejects_unsupported_major():
    config = ClassificationConfigLoader.get_config()
    bad_config = replace(config, version="4.0.0")

    errors = ClassificationConfigLoader._validate_version(bad_config)

    assert any("Unsupported major version" in error for error in errors)


def test_validate_version_rejects_invalid_version():
    config = ClassificationConfigLoader.get_config()
    bad_config = replace(config, version="not-a-version")

    errors = ClassificationConfigLoader._validate_version(bad_config)

    assert any("Invalid version format" in error for error in errors)

def test_validate_weights_accepts_valid_weights():
    config = ClassificationConfigLoader.get_config()

    assert ClassificationConfigLoader._validate_weights(config) == []


def test_validate_weights_detects_missing_key():
    config = ClassificationConfigLoader.get_config()
    weights = dict(config.weights)
    weights.pop("title")

    bad_config = replace(config, weights=weights)

    errors = ClassificationConfigLoader._validate_weights(bad_config)

    assert any("Missing weight key" in error for error in errors)


def test_is_numeric_accepts_int_and_float():
    assert ClassificationConfigLoader._is_numeric(1) is True
    assert ClassificationConfigLoader._is_numeric(0.5) is True


def test_is_numeric_rejects_bool():
    assert ClassificationConfigLoader._is_numeric(True) is False
    assert ClassificationConfigLoader._is_numeric(False) is False


def test_is_numeric_rejects_non_numeric():
    assert ClassificationConfigLoader._is_numeric("1") is False
    assert ClassificationConfigLoader._is_numeric(None) is False

def test_validate_weights_detects_non_positive():
    config = ClassificationConfigLoader.get_config()
    weights = dict(config.weights)
    weights["title"] = 0

    bad_config = replace(config, weights=weights)

    errors = ClassificationConfigLoader._validate_weights(bad_config)

    assert any("must be positive" in error for error in errors)


def test_validate_weights_detects_bad_sum():
    config = ClassificationConfigLoader.get_config()
    weights = dict(config.weights)
    weights["title"] = 0.9
    weights["description"] = 0.9
    weights["skills"] = 0.9

    bad_config = replace(config, weights=weights)

    errors = ClassificationConfigLoader._validate_weights(bad_config)

    assert any("must sum to 1.0" in error for error in errors)

def test_validate_thresholds_accepts_valid_thresholds():
    config = ClassificationConfigLoader.get_config()

    assert ClassificationConfigLoader._validate_thresholds(config) == []


def test_validate_thresholds_detects_missing_key():
    config = ClassificationConfigLoader.get_config()
    thresholds = dict(config.thresholds)
    thresholds.pop("tech_minimum")

    bad_config = replace(config, thresholds=thresholds)

    errors = ClassificationConfigLoader._validate_thresholds(bad_config)

    assert any("Missing threshold key" in error for error in errors)


def test_validate_thresholds_detects_non_numeric():
    config = ClassificationConfigLoader.get_config()
    thresholds = dict(config.thresholds)
    thresholds["tech_minimum"] = "invalid"  # type: ignore[assignment]

    bad_config = replace(config, thresholds=thresholds)

    errors = ClassificationConfigLoader._validate_thresholds(bad_config)

    assert any("must be numeric" in error for error in errors)


def test_validate_thresholds_detects_negative():
    config = ClassificationConfigLoader.get_config()
    thresholds = dict(config.thresholds)
    thresholds["tech_minimum"] = -1

    bad_config = replace(config, thresholds=thresholds)

    errors = ClassificationConfigLoader._validate_thresholds(bad_config)

    assert any("must be non-negative" in error for error in errors)


def test_validate_boosts_accepts_valid_boosts():
    config = ClassificationConfigLoader.get_config()

    assert ClassificationConfigLoader._validate_boosts(config) == []


def test_validate_boosts_detects_missing_key():
    config = ClassificationConfigLoader.get_config()
    boosts = dict(config.boosts)
    boosts.pop("title_exact_match")

    bad_config = replace(config, boosts=boosts)

    errors = ClassificationConfigLoader._validate_boosts(bad_config)

    assert any("Missing boost key" in error for error in errors)


def test_validate_boosts_detects_non_numeric():
    config = ClassificationConfigLoader.get_config()
    boosts = dict(config.boosts)
    boosts["title_exact_match"] = "invalid"  # type: ignore[assignment]

    bad_config = replace(config, boosts=boosts)

    errors = ClassificationConfigLoader._validate_boosts(bad_config)

    assert any("must be numeric" in error for error in errors)


def test_validate_boosts_detects_negative():
    config = ClassificationConfigLoader.get_config()
    boosts = dict(config.boosts)
    boosts["title_exact_match"] = -1

    bad_config = replace(config, boosts=boosts)

    errors = ClassificationConfigLoader._validate_boosts(bad_config)

    assert any("must be non-negative" in error for error in errors)



def test_validate_matching_accepts_valid_matching():
    config = ClassificationConfigLoader.get_config()

    assert ClassificationConfigLoader._validate_matching(config) == []


def test_validate_matching_detects_missing_key():
    config = ClassificationConfigLoader.get_config()
    matching = dict(config.matching)
    matching.pop("exact_weight")

    bad_config = replace(config, matching=matching)

    errors = ClassificationConfigLoader._validate_matching(bad_config)

    assert any("Missing matching key" in error for error in errors)


def test_validate_matching_detects_non_numeric():
    config = ClassificationConfigLoader.get_config()
    matching = dict(config.matching)
    matching["exact_weight"] = "invalid"  # type: ignore[assignment]

    bad_config = replace(config, matching=matching)

    errors = ClassificationConfigLoader._validate_matching(bad_config)

    assert any("must be numeric" in error for error in errors)


def test_validate_matching_detects_negative():
    config = ClassificationConfigLoader.get_config()
    matching = dict(config.matching)
    matching["exact_weight"] = -1

    bad_config = replace(config, matching=matching)

    errors = ClassificationConfigLoader._validate_matching(bad_config)

    assert any("must be non-negative" in error for error in errors)


def test_get_config_returns_loaded_config():
    config = ClassificationConfigLoader.get_config()

    assert config is not None
    assert config is ClassificationConfigLoader.get_config()


def test_get_category_returns_existing_category():
    config = ClassificationConfigLoader.get_config()
    category_id = next(iter(config.categories))

    category = ClassificationConfigLoader.get_category(category_id)

    assert category == config.categories[category_id]


def test_get_category_returns_none_for_unknown():
    assert ClassificationConfigLoader.get_category("does_not_exist") is None


def test_get_tech_categories_returns_only_tech():
    config = ClassificationConfigLoader.get_config()

    result = ClassificationConfigLoader.get_tech_categories()

    assert result
    assert all(config.categories[cat_id].is_tech for cat_id in result)


def test_get_non_tech_categories_returns_only_non_tech():
    config = ClassificationConfigLoader.get_config()

    result = ClassificationConfigLoader.get_non_tech_categories()

    assert all(not config.categories[cat_id].is_tech for cat_id in result)

def test_normalize_keyword_applies_alias():
    config = ClassificationConfigLoader.get_config()

    if config.aliases:
        alias, target = next(iter(config.aliases.items()))

        assert ClassificationConfigLoader.normalize_keyword(f"  {alias.upper()}  ") == target


def test_normalize_keyword_returns_normalized_unknown():
    assert ClassificationConfigLoader.normalize_keyword("  SomeUnknownKeyword  ") == (
        "someunknownkeyword"
    )


def test_is_stopword_returns_true_for_configured_stopword():
    config = ClassificationConfigLoader.get_config()

    if config.stopwords:
        word = next(iter(config.stopwords))
        assert ClassificationConfigLoader.is_stopword(f"  {word.upper()}  ") is True


def test_is_stopword_returns_false_for_unknown_word():
    assert ClassificationConfigLoader.is_stopword("definitely_not_a_stopword") is False

def test_get_compiled_regex_returns_empty_for_unknown_category():
    assert ClassificationConfigLoader.get_compiled_regex("does_not_exist") == []


def test_get_compiled_regex_returns_empty_when_category_has_no_regex():
    config = ClassificationConfigLoader.get_config()

    category_id = next(
        (
            cat_id
            for cat_id, cat in config.categories.items()
            if not cat.regex
        ),
        None,
    )

    if category_id is not None:
        assert ClassificationConfigLoader.get_compiled_regex(category_id) == []


def test_get_compiled_regex_compiles_category_patterns():
    config = ClassificationConfigLoader.get_config()

    category_id = next(
        (
            cat_id
            for cat_id, cat in config.categories.items()
            if cat.regex
        ),
        None,
    )

    if category_id is not None:
        patterns = ClassificationConfigLoader.get_compiled_regex(category_id)

        assert patterns
        assert all(hasattr(pattern, "search") for pattern in patterns)


def test_get_compiled_regex_uses_cache():
    config = ClassificationConfigLoader.get_config()

    category_id = next(
        (
            cat_id
            for cat_id, cat in config.categories.items()
            if cat.regex
        ),
        None,
    )

    if category_id is not None:
        first = ClassificationConfigLoader.get_compiled_regex(category_id)
        second = ClassificationConfigLoader.get_compiled_regex(category_id)

        assert first is second

def test_get_compiled_title_patterns_returns_all_strength_groups():
    result = ClassificationConfigLoader.get_compiled_title_patterns()

    assert set(result) == {
        "strong",
        "potential",
        "adjacent",
        "ambiguous",
    }


def test_get_compiled_title_patterns_contains_compiled_patterns():
    result = ClassificationConfigLoader.get_compiled_title_patterns()

    for patterns in result.values():
        assert all(hasattr(pattern, "search") for pattern in patterns)


def test_get_effective_thresholds_returns_global_thresholds():
    config = ClassificationConfigLoader.get_config()

    result = ClassificationConfigLoader.get_effective_thresholds(
        "category_without_specific_override"
    )

    assert result["tech_minimum"] == config.thresholds.get("tech_minimum", 30)
    assert result["high_confidence"] == config.thresholds.get("high_confidence", 70)
    assert result["medium_confidence"] == config.thresholds.get("medium_confidence", 50)
    assert result["low_confidence"] == config.thresholds.get("low_confidence", 30)

def test_get_effective_thresholds_with_defaults_uses_custom_defaults():
    defaults = {
        "tech_minimum": 999.0,
        "minimum_margin": 888.0,
        "min_confidence": 777.0,
    }

    result = ClassificationConfigLoader.get_effective_thresholds_with_defaults(
        "does_not_exist",
        defaults,
    )

    assert result["tech_minimum"] != 999.0  # global config overrides it
    assert result["minimum_margin"] == 888.0
    assert result["min_confidence"] == 777.0


def test_get_effective_thresholds_with_defaults_uses_builtin_defaults():
    result = ClassificationConfigLoader.get_effective_thresholds_with_defaults(
        "does_not_exist"
    )

    assert "tech_minimum" in result
    assert "minimum_margin" in result
    assert "min_confidence" in result

def test_get_classification_settings_returns_copy():
    config = ClassificationConfigLoader.get_config()

    result = ClassificationConfigLoader.get_classification_settings()

    assert result == config.classification

    if result:
        result["__test_only__"] = True
        assert "__test_only__" not in config.classification


def test_get_tech_title_patterns_returns_configured_patterns():
    config = ClassificationConfigLoader.get_config()

    assert ClassificationConfigLoader.get_tech_title_patterns() == (
        config.tech_title_patterns
    )


def test_get_category_families_groups_categories():
    config = ClassificationConfigLoader.get_config()

    result = ClassificationConfigLoader.get_category_families()

    assert result

    for family, category_ids in result.items():
        assert all(config.categories[cat_id].family == family for cat_id in category_ids)



def test_get_category_by_id_or_display_name_finds_by_id():
    config = ClassificationConfigLoader.get_config()
    category_id = next(iter(config.categories))

    assert (
        ClassificationConfigLoader.get_category_by_id_or_display_name(category_id)
        == config.categories[category_id]
    )


def test_get_category_by_id_or_display_name_finds_by_display_name():
    config = ClassificationConfigLoader.get_config()
    category_id, category = next(iter(config.categories.items()))

    result = ClassificationConfigLoader.get_category_by_id_or_display_name(
        category.display_name
    )

    assert result == category


def test_get_category_by_id_or_display_name_returns_none_for_unknown():
    assert (
        ClassificationConfigLoader.get_category_by_id_or_display_name(
            "does_not_exist"
        )
        is None
    )


def test_get_category_by_display_name_finds_category():
    config = ClassificationConfigLoader.get_config()
    category = next(iter(config.categories.values()))

    assert (
        ClassificationConfigLoader.get_category_by_display_name(category.display_name)
        == category
    )


def test_get_category_by_display_name_returns_none_for_unknown():
    assert (
        ClassificationConfigLoader.get_category_by_display_name(
            "Definitely Unknown Category"
        )
        is None
    )


def test_competes_returns_false_for_same_category():
    config = ClassificationConfigLoader.get_config()
    category_id = next(iter(config.categories))

    assert ClassificationConfigLoader.competes(category_id, category_id) is False


def test_competes_returns_false_for_parent_and_child():
    config = ClassificationConfigLoader.get_config()

    parent_id = next(
        (
            cat_id
            for cat_id, role in config._roles.items()
            if role == CategoryRole.PARENT and config._children.get(cat_id)
        ),
        None,
    )

    if parent_id is not None:
        child_id = next(iter(config._children[parent_id]))

        assert ClassificationConfigLoader.competes(child_id, parent_id) is False
        assert ClassificationConfigLoader.competes(parent_id, child_id) is False


def test_competes_returns_true_for_distinct_categories():
    config = ClassificationConfigLoader.get_config()

    category_ids = list(config.categories)

    if len(category_ids) >= 2:
        first, second = category_ids[:2]

        if (
            config._parents.get(first) != second
            and config._parents.get(second) != first
        ):

            assert ClassificationConfigLoader.competes(first, second) is True
            assert ClassificationConfigLoader.competes(second, first) is True

def test_get_competing_categories_unknown_primary_returns_everything_except_first():
    sorted_categories = [
        ("unknown", 100),
        ("category_a", 90),
        ("category_b", 80),
    ]

    result = ClassificationConfigLoader.get_competing_categories(
        "does_not_exist",
        sorted_categories,
    )

    assert result == sorted_categories[1:]


def test_get_competing_categories_filters_parent_child_relationships():
    config = ClassificationConfigLoader.get_config()

    parent_id = next(
        (
            cat_id
            for cat_id, role in config._roles.items()
            if role == CategoryRole.PARENT and config._children.get(cat_id)
        ),
        None,
    )

    if parent_id is not None:
        child_id = next(iter(config._children[parent_id]))

        sorted_categories = [
            (child_id, 100),
            (parent_id, 90),
        ]

        result = ClassificationConfigLoader.get_competing_categories(
            child_id,
            sorted_categories,
        )

        assert (parent_id, 90) not in result


def test_is_parent_identifies_parent_category():
    config = ClassificationConfigLoader.get_config()

    parent_id = next(
        (
            cat_id
            for cat_id, role in config._roles.items()
            if role == CategoryRole.PARENT
        ),
        None,
    )

    if parent_id is not None:
        assert ClassificationConfigLoader.is_parent(parent_id) is True


def test_is_specialization_identifies_specialization_category():
    config = ClassificationConfigLoader.get_config()

    specialization_id = next(
        (
            cat_id
            for cat_id, role in config._roles.items()
            if role == CategoryRole.SPECIALIZATION
        ),
        None,
    )

    if specialization_id is not None:
        assert ClassificationConfigLoader.is_specialization(specialization_id) is True


def test_taxonomy_accessors_return_none_or_false_for_unknown():
    assert ClassificationConfigLoader.is_parent("does_not_exist") is False
    assert ClassificationConfigLoader.is_specialization("does_not_exist") is False
    assert ClassificationConfigLoader.get_parent("does_not_exist") is None
    assert ClassificationConfigLoader.get_role("does_not_exist") is None


def test_get_children_returns_children_for_parent():
    config = ClassificationConfigLoader.get_config()

    parent_id = next(
        (
            cat_id
            for cat_id in config._children
            if config._children[cat_id]
        ),
        None,
    )

    if parent_id is not None:
        result = ClassificationConfigLoader.get_children(parent_id)

        assert set(result) == config._children[parent_id]


def test_get_children_returns_empty_for_unknown():
    assert ClassificationConfigLoader.get_children("does_not_exist") == []


def test_get_parent_returns_parent_for_child():
    config = ClassificationConfigLoader.get_config()

    child_id = next(
        (
            cat_id
            for cat_id, parent in config._parents.items()
            if parent is not None
        ),
        None,
    )

    if child_id is not None:
        assert (
            ClassificationConfigLoader.get_parent(child_id)
            == config._parents[child_id]
        )


def test_get_role_returns_configured_role():
    config = ClassificationConfigLoader.get_config()
    category_id = next(iter(config.categories))

    assert (
        ClassificationConfigLoader.get_role(category_id)
        == config._roles[category_id]
    )


def test_get_all_parents_matches_taxonomy():
    config = ClassificationConfigLoader.get_config()

    expected = [
        cat_id
        for cat_id, role in config._roles.items()
        if role == CategoryRole.PARENT
    ]

    assert ClassificationConfigLoader.get_all_parents() == expected


def test_get_all_specializations_matches_taxonomy():
    config = ClassificationConfigLoader.get_config()

    expected = [
        cat_id
        for cat_id, role in config._roles.items()
        if role == CategoryRole.SPECIALIZATION
    ]

    assert ClassificationConfigLoader.get_all_specializations() == expected

def test_module_level_config_helpers():
    config = get_config()

    assert config is ClassificationConfigLoader.get_config()

    category_id = next(iter(config.categories))

    assert get_category_config(category_id) == config.categories[category_id]


def test_module_level_normalization_helpers():
    assert normalize_keyword("  Python  ") == (
        ClassificationConfigLoader.normalize_keyword("  Python  ")
    )

    assert is_stopword("  the  ") == ClassificationConfigLoader.is_stopword("  the  ")


def test_module_level_classification_helpers():
    assert get_classification_settings() == (
        ClassificationConfigLoader.get_classification_settings()
    )

    assert get_tech_title_patterns() == (
        ClassificationConfigLoader.get_tech_title_patterns()
    )

    assert get_compiled_title_patterns() == (
        ClassificationConfigLoader.get_compiled_title_patterns()
    )


def test_module_level_threshold_helper():
    result = get_effective_thresholds("does_not_exist")

    expected = ClassificationConfigLoader.get_effective_thresholds_with_defaults(
        "does_not_exist"
    )

    assert result == expected

def test_module_level_taxonomy_helpers():
    config = ClassificationConfigLoader.get_config()

    category_ids = list(config.categories)

    assert competes(category_ids[0], category_ids[0]) is False

    assert is_parent(category_ids[0]) == ClassificationConfigLoader.is_parent(
        category_ids[0]
    )

    assert is_specialization(category_ids[0]) == (
        ClassificationConfigLoader.is_specialization(category_ids[0])
    )

    assert get_children(category_ids[0]) == (
        ClassificationConfigLoader.get_children(category_ids[0])
    )

    assert get_parent(category_ids[0]) == (
        ClassificationConfigLoader.get_parent(category_ids[0])
    )

    assert get_role(category_ids[0]) == (
        ClassificationConfigLoader.get_role(category_ids[0])
    )

    assert get_all_parents() == ClassificationConfigLoader.get_all_parents()

    assert get_all_specializations() == (
        ClassificationConfigLoader.get_all_specializations()
    )


def test_module_level_competing_categories_helper():
    categories = [
        ("category_a", 100),
        ("category_b", 90),
        ("category_c", 80),
    ]

    assert get_competing_categories(
        "does_not_exist",
        categories,
    ) == categories[1:]



def test_load_raises_for_missing_config_file(tmp_path):
    missing = tmp_path / "missing.yaml"

    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        ClassificationConfigLoader.load(missing)


def test_load_raises_for_invalid_yaml(tmp_path):
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(":\n  - invalid: [", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Invalid YAML"):
        ClassificationConfigLoader.load(config_file)


def test_load_raises_for_generic_file_error(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("placeholder: true", encoding="utf-8")

    def raise_error(*args, **kwargs):
        raise OSError("read failure")

    monkeypatch.setattr(Path, "open", raise_error)

    with pytest.raises(ConfigurationError, match="Failed to load configuration"):
        ClassificationConfigLoader.load(config_file)


def test_validate_required_sections_rejects_missing_sections():
    with pytest.raises(ConfigurationError, match="Missing required sections"):
        ClassificationConfigLoader._validate_required_sections({})


def test_validate_config_raises_aggregated_error():
    config = ClassificationConfigLoader.get_config()
    bad_config = replace(config, version="4.0.0")

    with pytest.raises(ConfigurationError, match="Configuration validation failed"):
        ClassificationConfigLoader._validate_config(bad_config)


def test_validate_priority_detects_unknown_category():
    config = ClassificationConfigLoader.get_config()
    bad_config = replace(
        config,
        category_priority=(*config.category_priority, "unknown-category"),
    )

    errors = ClassificationConfigLoader._validate_priority(bad_config)

    assert any("not found in categories" in error for error in errors)


def test_validate_categories_detects_duplicate_display_name():
    config = ClassificationConfigLoader.get_config()
    categories = dict(config.categories)

    category_ids = list(categories)
    first_id = category_ids[0]
    second_id = category_ids[1]

    categories[second_id] = replace(
        categories[second_id],
        display_name=categories[first_id].display_name,
    )

    bad_config = replace(config, categories=categories)

    errors = ClassificationConfigLoader._validate_categories(bad_config)

    assert any("Duplicate display name" in error for error in errors)


def test_validate_categories_detects_id_mismatch():
    config = ClassificationConfigLoader.get_config()
    categories = dict(config.categories)

    category_id = next(iter(categories))
    categories[category_id] = replace(
        categories[category_id],
        id="different-id",
    )

    bad_config = replace(config, categories=categories)

    errors = ClassificationConfigLoader._validate_categories(bad_config)

    assert any("Category ID mismatch" in error for error in errors)


def test_validate_categories_detects_invalid_regex():
    config = ClassificationConfigLoader.get_config()
    categories = dict(config.categories)

    category_id = next(iter(categories))
    categories[category_id] = replace(
        categories[category_id],
        regex=["["],
    )

    bad_config = replace(config, categories=categories)

    errors = ClassificationConfigLoader._validate_categories(bad_config)

    assert any("Invalid regex" in error for error in errors)


def test_validate_categories_detects_invalid_keyword_weight():
    config = ClassificationConfigLoader.get_config()
    categories = dict(config.categories)

    category_id = next(iter(categories))
    category = categories[category_id]

    categories[category_id] = replace(
        category,
        keywords={"python": -1},
    )

    bad_config = replace(config, categories=categories)

    errors = ClassificationConfigLoader._validate_categories(bad_config)

    assert any("has invalid weight" in error for error in errors)


def test_validate_categories_detects_invalid_strength():
    config = ClassificationConfigLoader.get_config()
    categories = dict(config.categories)

    category_id = next(iter(categories))
    categories[category_id] = replace(
        categories[category_id],
        strength="invalid",
    )

    bad_config = replace(config, categories=categories)

    errors = ClassificationConfigLoader._validate_categories(bad_config)

    assert any("Invalid strength" in error for error in errors)


def test_validate_categories_detects_invalid_specificity():
    config = ClassificationConfigLoader.get_config()
    categories = dict(config.categories)

    category_id = next(iter(categories))
    categories[category_id] = replace(
        categories[category_id],
        specificity="invalid",
    )

    bad_config = replace(config, categories=categories)

    errors = ClassificationConfigLoader._validate_categories(bad_config)

    assert any("Invalid specificity" in error for error in errors)


def test_validate_aliases_detects_empty_alias_and_target():
    config = ClassificationConfigLoader.get_config()
    bad_config = replace(
        config,
        aliases={"": ""},
    )

    errors = ClassificationConfigLoader._validate_aliases(bad_config)

    assert any("Empty alias key" in error for error in errors)
    assert any("Empty alias target" in error for error in errors)


def test_validate_category_thresholds_detects_unknown_category():
    config = ClassificationConfigLoader.get_config()
    bad_config = replace(
        config,
        category_thresholds={"unknown-category": {"high_confidence": 80}},
    )

    errors = ClassificationConfigLoader._validate_category_thresholds(bad_config)

    assert any("not found in categories" in error for error in errors)


def test_validate_category_thresholds_detects_invalid_value():
    config = ClassificationConfigLoader.get_config()
    category_id = next(iter(config.categories))

    bad_config = replace(
        config,
        category_thresholds={
            category_id: {"high_confidence": "invalid"},
        },
    )

    errors = ClassificationConfigLoader._validate_category_thresholds(bad_config)

    assert any("must be numeric" in error for error in errors)


def test_validate_category_thresholds_detects_negative_value():
    config = ClassificationConfigLoader.get_config()
    category_id = next(iter(config.categories))

    bad_config = replace(
        config,
        category_thresholds={
            category_id: {"high_confidence": -1},
        },
    )

    errors = ClassificationConfigLoader._validate_category_thresholds(bad_config)

    assert any("must be non-negative" in error for error in errors)


def test_validate_title_patterns_detects_invalid_strength():
    config = ClassificationConfigLoader.get_config()
    pattern = replace(
        config.tech_title_patterns[0],
        strength="invalid",
    )

    bad_config = replace(
        config,
        tech_title_patterns=[pattern],
    )

    errors = ClassificationConfigLoader._validate_title_patterns(bad_config)

    assert any("invalid strength" in error for error in errors)


def test_validate_title_patterns_detects_invalid_specificity():
    config = ClassificationConfigLoader.get_config()
    pattern = replace(
        config.tech_title_patterns[0],
        specificity="invalid",
    )

    bad_config = replace(
        config,
        tech_title_patterns=[pattern],
    )

    errors = ClassificationConfigLoader._validate_title_patterns(bad_config)

    assert any("invalid specificity" in error for error in errors)


def test_validate_title_patterns_detects_invalid_weight():
    config = ClassificationConfigLoader.get_config()
    pattern = replace(
        config.tech_title_patterns[0],
        weight=0,
    )

    bad_config = replace(
        config,
        tech_title_patterns=[pattern],
    )

    errors = ClassificationConfigLoader._validate_title_patterns(bad_config)

    assert any("invalid weight" in error for error in errors)


def test_validate_title_patterns_detects_unknown_category():
    config = ClassificationConfigLoader.get_config()
    pattern = replace(
        config.tech_title_patterns[0],
        categories=("unknown-category",),
    )

    bad_config = replace(
        config,
        tech_title_patterns=[pattern],
    )

    errors = ClassificationConfigLoader._validate_title_patterns(bad_config)

    assert any("references unknown category" in error for error in errors)


def test_get_compiled_regex_skips_invalid_pattern_defensively():
    config = ClassificationConfigLoader.get_config()
    category_id = next(iter(config.categories))
    category = config.categories[category_id]

    categories = dict(config.categories)
    categories[category_id] = replace(
        category,
        regex=["["],
    )

    bad_config = replace(config, categories=categories)

    original_config = ClassificationConfigLoader._config
    original_path = ClassificationConfigLoader._config_path

    try:
        ClassificationConfigLoader._config = bad_config
        ClassificationConfigLoader._config_path = original_path
        ClassificationConfigLoader._compiled_regex.clear()

        result = ClassificationConfigLoader.get_compiled_regex(category_id)

        assert result == []
    finally:
        ClassificationConfigLoader._config = original_config
        ClassificationConfigLoader._config_path = original_path
        ClassificationConfigLoader._compiled_regex.clear()


def test_reload_config_returns_reloaded_configuration():
    result = reload_config()

    assert result is ClassificationConfigLoader.get_config()


def test_get_effective_thresholds_applies_category_override():
    config = ClassificationConfigLoader.get_config()
    category_id = next(iter(config.categories))

    bad_config = replace(
        config,
        category_thresholds={
            category_id: {"high_confidence": 99},
        },
    )

    original_config = ClassificationConfigLoader._config
    original_path = ClassificationConfigLoader._config_path

    try:
        ClassificationConfigLoader._config = bad_config
        ClassificationConfigLoader._config_path = original_path

        result = ClassificationConfigLoader.get_effective_thresholds(category_id)
        assert result["high_confidence"] == 99

        result_with_defaults = (
            ClassificationConfigLoader.get_effective_thresholds_with_defaults(
                category_id
            )
        )
        assert result_with_defaults["high_confidence"] == 99
    finally:
        ClassificationConfigLoader._config = original_config
        ClassificationConfigLoader._config_path = original_path

def test_get_compiled_title_patterns_skips_invalid_pattern_defensively():
    config = ClassificationConfigLoader.get_config()
    original_config = ClassificationConfigLoader._config
    original_path = ClassificationConfigLoader._config_path

    from types import SimpleNamespace

    invalid_pattern = SimpleNamespace(
        pattern="[",
        strength=config.tech_title_patterns[0].strength,
    )

    try:
        ClassificationConfigLoader._config = replace(
            config,
            tech_title_patterns=[invalid_pattern],
        )
        ClassificationConfigLoader._config_path = original_path

        result = ClassificationConfigLoader.get_compiled_title_patterns()

        assert result[invalid_pattern.strength] == []
    finally:
        ClassificationConfigLoader._config = original_config
        ClassificationConfigLoader._config_path = original_path

def test_validate_weights_detects_non_numeric(monkeypatch):
    """Test validation rejects a weight reported as non-numeric."""
    config = ClassificationConfigLoader.get_config()

    monkeypatch.setattr(
        ClassificationConfigLoader,
        "_is_numeric",
        classmethod(lambda cls, value: False),
    )

    errors = ClassificationConfigLoader._validate_weights(config)

    assert any("must be numeric" in error for error in errors)

def test_get_config_loads_when_config_is_none(monkeypatch):
    """Test get_config loads configuration when no config is cached."""
    expected = object()

    monkeypatch.setattr(ClassificationConfigLoader, "_config", None)
    monkeypatch.setattr(
        ClassificationConfigLoader,
        "load",
        lambda: expected,
    )

    assert ClassificationConfigLoader.get_config() is expected