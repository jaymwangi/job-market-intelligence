import re
from dataclasses import replace

import pytest

from app.etl.enrichment.classification_config import TitlePatternConfig
from app.etl.enrichment.tech_scorer import (
    DEFAULT_DIMINISHING_RETURNS,
    MAX_KEYWORD_CONTRIBUTION,
    Evidence,
    MatchResult,
    MatchSource,
    TechnologyScorer,
)
from app.etl.enrichment.title_pattern import TitlePattern


@pytest.fixture
def scorer():
    return TechnologyScorer()


class TestTechnologyScorerHelpers:
    def test_sanitize_normal_keyword(self, scorer):
        result = scorer._sanitize_keyword_for_regex("python")

        assert result == r"\bpython\b"

    def test_sanitize_phrase(self, scorer):
        result = scorer._sanitize_keyword_for_regex("machine learning")

        assert result == r"\bmachine\ learning\b"

    @pytest.mark.parametrize("keyword", ["C++", "C#", ".NET", "Node.js"])
    def test_sanitize_special_keyword(self, scorer, keyword):
        result = scorer._sanitize_keyword_for_regex(keyword)

        assert result == __import__("re").escape(keyword)

    def test_normalize_text(self, scorer):
        result = scorer._normalize_text("  Senior PYTHON!!!   Engineer,  ")

        assert result == "senior python engineer"

    def test_normalize_text_preserves_technology_characters(self, scorer):
        result = scorer._normalize_text("C++ C# .NET Node.js")

        assert result == "c++ c# .net node.js"

    def test_normalize_text_empty(self, scorer):
        assert scorer._normalize_text("") == ""
        assert scorer._normalize_text("   ") == ""

    def test_get_available_fields(self, scorer):
        result = scorer._get_available_fields(
            "Python Developer",
            "Build APIs",
            ["Python"],
        )

        assert result == {
            "title": True,
            "description": True,
            "skills": True,
        }

    def test_get_available_fields_with_missing_values(self, scorer):
        result = scorer._get_available_fields("", "   ", [])

        assert result == {
            "title": False,
            "description": False,
            "skills": False,
        }

    def test_redistribute_weights_all_fields_available(self, scorer):
        available = {
            "title": True,
            "description": True,
            "skills": True,
        }

        result = scorer._redistribute_weights(available)

        assert result == {
            "title": scorer.config.weights["title"],
            "description": scorer.config.weights["description"],
            "skills": scorer.config.weights["skills"],
        }

    def test_redistribute_weights_missing_description(self, scorer):
        available = {
            "title": True,
            "description": False,
            "skills": True,
        }

        result = scorer._redistribute_weights(available)

        assert result["description"] == 0.0
        assert result["title"] > 0
        assert result["skills"] > 0
        assert sum(result.values()) == pytest.approx(1.0)

    def test_redistribute_weights_only_title(self, scorer):
        available = {
            "title": True,
            "description": False,
            "skills": False,
        }

        result = scorer._redistribute_weights(available)

        assert result == {
            "title": 1.0,
            "description": 0.0,
            "skills": 0.0,
        }

    def test_redistribute_weights_no_fields(self, scorer):
        available = {
            "title": False,
            "description": False,
            "skills": False,
        }

        result = scorer._redistribute_weights(available)

        assert result == {
            "title": 0.0,
            "description": 0.0,
            "skills": 0.0,
        }

    def test_scan_text_for_keywords(self, scorer):
        result = scorer._scan_text_for_keywords("python developer builds python APIs")

        assert "python" in result
        assert result["python"].match_count == 2
        assert isinstance(result["python"], MatchResult)

    def test_scan_text_for_keywords_uses_fallback_when_pattern_missing(self, scorer):
        keyword = next(iter(scorer._all_keywords))

        scorer._keyword_patterns.pop(keyword)

        result = scorer._scan_text_for_keywords(f"{keyword} and {keyword}")

        assert keyword in result
        assert result[keyword].match_count == 2

    def test_scan_empty_text(self, scorer):
        assert scorer._scan_text_for_keywords("") == "" or scorer._scan_text_for_keywords("") == {}

    def test_matches_keyword(self, scorer):
        assert scorer._matches_keyword("senior python developer", "python")
        assert not scorer._matches_keyword("senior pythons developer", "python")

    def test_matches_keyword_empty_values(self, scorer):
        assert not scorer._matches_keyword("", "python")
        assert not scorer._matches_keyword("python", "")
        assert not scorer._matches_keyword("", "")

    def test_scan_text_for_keywords_fallback_matching(self, scorer):
        """Use substring counting when no compiled pattern exists."""
        scorer._keyword_patterns.pop("python", None)

        result = scorer._scan_text_for_keywords("python python developer")

        assert result["python"].match_count == 2

    def test_collect_evidence_unknown_category(self, scorer):
        """Return no evidence when the category does not exist."""
        result = scorer._collect_evidence_from_matches(
            {},
            "does_not_exist",
            {},
            MatchSource.DESCRIPTION,
        )

        assert result == []

    def test_collect_evidence_for_category_unknown_category(self, scorer):
        result = scorer._collect_evidence_for_category(
            {},
            {},
            [],
            "does_not_exist",
            {},
        )

        assert result == []

    def test_build_keyword_patterns_falls_back_on_invalid_regex(self, scorer, monkeypatch):
        original_compile = re.compile
        first_call = True

        def compile_with_failure(pattern, *args, **kwargs):
            nonlocal first_call
            if first_call:
                first_call = False
                raise re.error("forced invalid regex")
            return original_compile(pattern, *args, **kwargs)

        monkeypatch.setattr(re, "compile", compile_with_failure)

        scorer._build_keyword_patterns()

        assert scorer._keyword_patterns

    def test_compile_title_patterns_ignores_unknown_config_type(self, scorer, caplog):
        config = replace(
            scorer.config,
            tech_title_patterns=(object(),),
        )
        scorer.config = config

        scorer._compile_title_patterns()

        assert scorer._title_patterns == []
        assert "Unknown pattern config type" in caplog.text

    def test_compile_title_patterns_handles_invalid_config_weight(self, scorer, caplog):
        valid_config = TitlePatternConfig(
            pattern=r"\bpython\b",
            categories=("backend",),
        )
        invalid_config = replace(valid_config, weight="invalid")

        scorer.config = replace(
            scorer.config,
            tech_title_patterns=(invalid_config,),
        )

        scorer._compile_title_patterns()

        assert scorer._title_patterns == []
        assert "Invalid title pattern" in caplog.text

    def test_get_category_display_name(self, scorer):
        assert scorer.get_category_display_name("backend") == "Backend Development"


class TestCategorySelection:
    def test_get_best_category_empty(self, scorer):
        assert scorer._get_best_category({}) == ("other", 0.0)

    def test_get_best_category_single(self, scorer):
        assert scorer._get_best_category({"backend": 20.0}) == ("backend", 20.0)

    def test_get_best_category_uses_priority_for_tie(self, scorer):
        priority = scorer.config.category_priority

        if len(priority) < 2:
            pytest.skip("Configuration does not contain enough category priorities")

        first, second = priority[:2]

        result = scorer._get_best_category(
            {
                first: 10.0,
                second: 10.0,
            }
        )

        assert result == (first, 10.0)

    def test_get_best_category_falls_back_alphabetically(self, scorer):
        class ConfigStub:
            category_priority = []

        original_config = scorer.config
        scorer.config = ConfigStub()

        try:
            result = scorer._get_best_category(
                {
                    "z_category": 10.0,
                    "a_category": 10.0,
                }
            )
        finally:
            scorer.config = original_config

        assert result == ("a_category", 10.0)

    def test_get_top_categories_empty(self, scorer):
        assert scorer._get_top_categories({}) == []

    def test_get_top_categories_limits_results(self, scorer):
        categories = list(scorer.config.categories)[:6]
        scores = {category: float(index + 1) for index, category in enumerate(categories)}

        result = scorer._get_top_categories(scores, n=3)

        assert len(result) == 3
        assert result[0][1] >= result[1][1] >= result[2][1]

    def test_get_top_categories_invalid_category_uses_other(self, scorer):
        result = scorer._get_top_categories(
            {"not_a_real_category": 50.0},
            n=1,
        )

        assert result[0][1] == 50.0
        assert result[0][0].value == "other"


class TestEvidence:
    def test_calculate_evidence_contributions_empty(self, scorer):
        assert scorer._calculate_evidence_contributions([]) == []

    def test_calculate_evidence_contributions_applies_diminishing_returns(self, scorer):
        evidence = [
            __import__("app.etl.enrichment.tech_scorer", fromlist=["Evidence"]).Evidence(
                keyword="python",
                category="backend",
                source=MatchSource.TITLE,
                base_weight=10.0,
                applied_weight=10.0,
                occurrence=1,
                contribution=0.0,
            ),
            __import__("app.etl.enrichment.tech_scorer", fromlist=["Evidence"]).Evidence(
                keyword="python",
                category="backend",
                source=MatchSource.DESCRIPTION,
                base_weight=10.0,
                applied_weight=10.0,
                occurrence=2,
                contribution=0.0,
            ),
        ]

        result = scorer._calculate_evidence_contributions(evidence)

        assert result[0].contribution == pytest.approx(10.0 * DEFAULT_DIMINISHING_RETURNS[0])
        assert result[1].contribution == pytest.approx(10.0 * DEFAULT_DIMINISHING_RETURNS[1])

    def test_calculate_evidence_contributions_caps_contribution(self, scorer):
        evidence = [
            __import__("app.etl.enrichment.tech_scorer", fromlist=["Evidence"]).Evidence(
                keyword="python",
                category="backend",
                source=MatchSource.TITLE,
                base_weight=100.0,
                applied_weight=100.0,
                occurrence=1,
                contribution=0.0,
            )
        ]

        result = scorer._calculate_evidence_contributions(evidence)

        assert result[0].contribution == MAX_KEYWORD_CONTRIBUTION

    def test_calculate_evidence_contributions_sets_zero_after_diminishing_returns(self, scorer):
        evidence = [
            Evidence(
                keyword="python",
                category="general_software",
                source=MatchSource.DESCRIPTION,
                base_weight=10.0,
                applied_weight=10.0,
                occurrence=1,
                contribution=0.0,
            ),
            Evidence(
                keyword="python",
                category="general_software",
                source=MatchSource.DESCRIPTION,
                base_weight=8.0,
                applied_weight=8.0,
                occurrence=2,
                contribution=0.0,
            ),
        ]

        scorer.diminishing_returns = [1.0, 0.0]

        result = scorer._calculate_evidence_contributions(evidence)

        assert result[0].contribution == 10.0
        assert result[1].contribution == 0.0

    def test_calculate_confidence_uses_fallback_when_theoretical_max_is_zero(self, scorer):
        scorer._theoretical_max_score = 0.0
        explanations = []

        confidence, normalized_score, threshold = scorer._calculate_confidence(
            50.0,
            "backend",
            explanations,
        )

        assert confidence == 0.5
        assert normalized_score == 0.5
        assert threshold == 15
        assert explanations


class TestScoring:
    def test_score_with_no_available_text(self, scorer):
        result = scorer.score("", "", [])

        assert result.primary_category_str == "other"
        assert result.raw_score == 0.0
        assert result.confidence == 0.0
        assert result.explanations == ["No text available for scoring"]

    def test_score_basic_technology_role(self, scorer):
        result = scorer.score(
            title="Senior Backend Engineer",
            description="Build APIs with Python and Django",
            skills=["Python", "Django"],
        )

        assert result.raw_score > 0
        assert result.confidence > 0
        assert result.primary_category_str != "other"
        assert result.evidence
        assert result.matched_keywords


class TestTitlePatterns:

    def test_compile_title_patterns_accepts_runtime_title_pattern(self, scorer):
        runtime_pattern = TitlePattern(
            pattern=r"\bdata engineer\b",
            categories=("data_engineering",),
            weight=12.0,
            strength="strong",
            specificity="high",
        )

        original_config = scorer.config

        class ConfigStub:
            tech_title_patterns = [runtime_pattern]

        scorer.config = ConfigStub()
        try:
            scorer._compile_title_patterns()
        finally:
            scorer.config = original_config

        assert len(scorer._title_patterns) == 1
        assert scorer._title_patterns[0] is runtime_pattern

    def test_compile_title_patterns_accepts_dict(self, scorer):
        original_config = scorer.config

        class ConfigStub:
            tech_title_patterns = [
                {
                    "pattern": r"\bdata engineer\b",
                    "categories": ["data_engineering"],
                    "weight": 12.0,
                    "strength": "strong",
                    "specificity": "high",
                }
            ]

        scorer.config = ConfigStub()
        try:
            scorer._compile_title_patterns()
        finally:
            scorer.config = original_config

        assert len(scorer._title_patterns) == 1
        pattern = scorer._title_patterns[0]
        assert pattern.pattern == r"\bdata engineer\b"
        assert pattern.categories == ("data_engineering",)
        assert pattern.weight == 12.0
        assert pattern.strength == "strong"
        assert pattern.specificity == "high"

    def test_compile_title_patterns_rejects_invalid_dict(self, scorer):
        original_config = scorer.config

        class ConfigStub:
            tech_title_patterns = [
                {
                    "categories": ["backend"],
                    "weight": 10.0,
                }
            ]

        scorer.config = ConfigStub()
        try:
            scorer._compile_title_patterns()
        finally:
            scorer.config = original_config

        assert scorer._title_patterns == []

    def test_compile_title_patterns_handles_empty_config(self, scorer):
        original_config = scorer.config

        class ConfigStub:
            tech_title_patterns = []

        scorer.config = ConfigStub()
        try:
            scorer._compile_title_patterns()
        finally:
            scorer.config = original_config

        assert scorer._title_patterns == []

    def test_get_title_strength_no_title(self, scorer):
        strength, pattern, weight = scorer._get_title_strength("")

        assert strength == "ambiguous"
        assert pattern is None
        assert weight == 0.0

    def test_get_title_strength_no_patterns(self, scorer):
        original = scorer._title_patterns
        scorer._title_patterns = []

        try:
            strength, pattern, weight = scorer._get_title_strength("Senior Backend Engineer")
        finally:
            scorer._title_patterns = original

        assert strength == "ambiguous"
        assert pattern is None
        assert weight == 0.0

    def test_get_title_strength_prefers_stronger_pattern(self, scorer):
        if len(scorer._title_patterns) < 2:
            pytest.skip("Configuration does not contain enough title patterns")

        matching = [p for p in scorer._title_patterns if p.matches("Senior Backend Engineer")]
        if not matching:
            pytest.skip("Configuration has no matching backend title pattern")

        strength, pattern, weight = scorer._get_title_strength("Senior Backend Engineer")

        assert pattern is not None
        assert strength in {"strong", "potential", "adjacent", "ambiguous"}
        assert weight == pattern.weight


class TestNegativePenalties:
    def test_negative_penalty_unknown_category(self, scorer):
        result = scorer._apply_negative_penalties(
            "does_not_exist",
            50.0,
            "python developer",
            [],
            [],
        )

        assert result == (50.0, {})

    def test_negative_penalty_without_configured_penalties(self, scorer):
        category_id = next(iter(scorer.config.categories))
        category = scorer.config.categories[category_id]

        if getattr(category, "negative_keywords_penalties", {}):
            pytest.skip("Selected category has explicit negative penalties")

        if not getattr(category, "negative_keywords", []):
            pytest.skip("Selected category has no negative keywords")

        result = scorer._apply_negative_penalties(
            category_id,
            50.0,
            " ".join(category.negative_keywords),
            [],
            [],
        )

        assert result[0] <= 50.0

    def test_negative_penalty_matches_keyword(self, scorer):
        candidates = [
            (cat_id, cat)
            for cat_id, cat in scorer.config.categories.items()
            if getattr(cat, "negative_keywords_penalties", {})
        ]

        if not candidates:
            pytest.skip("No category has negative keyword penalties")

        category_id, category = candidates[0]
        negative = next(iter(category.negative_keywords_penalties))
        explanations = []
        evidence = []

        adjusted, matched = scorer._apply_negative_penalties(
            category_id,
            50.0,
            negative,
            explanations,
            evidence,
        )

        assert negative in matched
        assert adjusted < 50.0
        assert evidence
        assert evidence[-1].source == MatchSource.NEGATIVE_PENALTY
        assert evidence[-1].contribution < 0
        assert explanations

    def test_apply_negative_penalties_without_negative_keywords(self, scorer):
        category_id = next(
            category_id
            for category_id, category in scorer.config.categories.items()
            if not getattr(category, "negative_keywords_penalties", {})
            and not getattr(category, "negative_keywords", [])
        )

        score, matched = scorer._apply_negative_penalties(
            category_id=category_id,
            score=50.0,
            text="python developer",
            explanations=[],
            evidence=[],
        )

        assert score == 50.0
        assert matched == {}


class TestScoringBehavior:
    def test_score_with_skills_only(self, scorer):
        result = scorer.score(
            title="",
            description="",
            skills=["Python", "Django"],
        )

        assert result.raw_score >= 0
        assert result.evidence or result.primary_category_str == "other"

    def test_score_with_description_only(self, scorer):
        result = scorer.score(
            title="",
            description="Python Django PostgreSQL backend APIs",
            skills=[],
        )

        assert result.raw_score > 0
        assert result.primary_category_str != "other"
        assert result.evidence

    def test_score_with_title_pattern(self, scorer):
        patterns = [p for p in scorer._title_patterns if p.matches("Senior Backend Engineer")]

        if not patterns:
            pytest.skip("Configuration has no matching title pattern")

        result = scorer.score(
            title="Senior Backend Engineer",
            description="",
            skills=[],
        )

        assert result.title_pattern_matched is True
        assert any(ev.source == MatchSource.TITLE_PATTERN for ev in result.evidence)

    def test_score_returns_matched_phrases(self, scorer):
        phrase_categories = [
            (cat_id, cat)
            for cat_id, cat in scorer.config.categories.items()
            if any(" " in keyword for keyword in cat.keywords)
        ]

        if not phrase_categories:
            pytest.skip("No multi-word keywords configured")

        category_id, category = phrase_categories[0]
        phrase = next(keyword for keyword in category.keywords if " " in keyword)

        result = scorer.score(
            title=phrase,
            description="",
            skills=[],
        )

        assert isinstance(result.matched_phrases, list)

    def test_score_caps_explanations_and_evidence(self, scorer):
        result = scorer.score(
            title="Senior Backend Engineer",
            description=(
                "Python Django PostgreSQL FastAPI APIs backend "
                "Python Django PostgreSQL FastAPI APIs backend"
            ),
            skills=["Python", "Django", "PostgreSQL", "FastAPI"],
        )

        assert len(result.explanations) <= 20
        assert len(result.evidence) <= 50

    def test_score_accepts_none_for_skills(self, scorer):
        result = scorer.score(
            title="Python Developer",
            description="Build software applications",
            skills=None,
        )

        assert result is not None

    def test_score_initializes_category_from_title_pattern_boost(self, scorer, monkeypatch):
        monkeypatch.setattr(
            scorer,
            "_check_title_patterns",
            lambda title: {"general_software": 10.0},
        )

        monkeypatch.setattr(
            scorer,
            "_collect_evidence_for_category",
            lambda *args: [],
        )

        result = scorer.score(
            title="Software Developer",
            description="",
            skills=[],
        )

        assert result.category_scores["general_software"] == 10.0

    def test_score_records_negative_penalties(self, scorer, monkeypatch):
        monkeypatch.setattr(
            scorer,
            "_apply_negative_penalties",
            lambda category_id, score, text, explanations, evidence: (
                score - 5.0,
                {"test_negative": 5.0},
            ),
        )

        result = scorer.score(
            title="Python Developer",
            description="Python backend development",
            skills=["Python"],
        )

        assert result is not None

    def test_score_uses_other_for_invalid_best_category(self, scorer, monkeypatch):
        monkeypatch.setattr(
            scorer,
            "_get_best_category",
            lambda scores: ("not_a_real_category", 50.0),
        )

        result = scorer.score(
            title="Python Developer",
            description="Python backend development",
            skills=["Python"],
        )

        assert result.primary_category.value == "other"


class TestClassification:
    def test_classify_strong_title_is_tech(self, scorer):
        result = scorer.classify(
            "Senior Backend Engineer",
            "",
            [],
        )

        assert result.is_tech is True
        assert result.primary_category == "backend"

    def test_classify_ambiguous_title_without_evidence_is_non_tech(self, scorer):
        result = scorer.classify(
            "Office Administrator",
            "",
            [],
        )

        assert result.is_tech is False
        assert result.primary_category == "non_tech"

    def test_classify_potential_title_with_supporting_evidence(self, scorer):
        candidates = [p for p in scorer._title_patterns if p.strength == "potential"]

        if not candidates:
            pytest.skip("No potential title patterns configured")

        pattern = candidates[0]
        title = pattern.pattern
        category = pattern.categories[0] if pattern.categories else "general_software"

        category_config = scorer.config.categories.get(category)
        if not category_config or not category_config.keywords:
            pytest.skip("No usable keywords for potential title category")

        keyword = next(iter(category_config.keywords))

        result = scorer.classify(
            title,
            f"Experience with {keyword}",
            [keyword],
        )

        assert isinstance(result.is_tech, bool)
        if result.is_tech:
            assert result.primary_category != "non_tech"

    def test_classify_adjacent_title_requires_two_supporting_items(self, scorer):
        candidates = [p for p in scorer._title_patterns if p.strength == "adjacent"]

        if not candidates:
            pytest.skip("No adjacent title patterns configured")

        pattern = candidates[0]

        result = scorer.classify(
            pattern.pattern,
            "",
            [],
        )

        assert result.is_tech is False
        assert result.primary_category == "non_tech"

    def test_classify_adjacent_title_with_two_supporting_evidence_items(self, scorer, monkeypatch):
        candidates = [
            pattern for pattern in scorer._title_patterns if pattern.strength == "adjacent"
        ]

        if not candidates:
            pytest.skip("No adjacent title pattern configured")

        pattern = candidates[0]

        monkeypatch.setattr(
            scorer,
            "_get_title_strength",
            lambda title: ("adjacent", pattern, pattern.weight),
        )

        result = scorer.classify(
            pattern.pattern,
            "Python backend development",
            ["Python"],
        )

        assert isinstance(result.is_tech, bool)


class TestConvenienceFunctions:
    def test_get_scorer_returns_singleton(self, monkeypatch):
        import app.etl.enrichment.tech_scorer as module

        original = module._scorer
        module._scorer = None

        try:
            first = module.get_scorer()
            second = module.get_scorer()

            assert first is second
            assert isinstance(first, TechnologyScorer)
        finally:
            module._scorer = original

    def test_score_job_delegates_to_singleton(self, monkeypatch):
        from unittest.mock import Mock

        import app.etl.enrichment.tech_scorer as module

        mock_scorer = Mock()
        expected = object()
        mock_scorer.score.return_value = expected

        monkeypatch.setattr(module, "get_scorer", lambda: mock_scorer)

        result = module.score_job(
            "Backend Engineer",
            "Python APIs",
            ["Python"],
        )

        assert result is expected
        mock_scorer.score.assert_called_once_with(
            "Backend Engineer",
            "Python APIs",
            ["Python"],
        )

    def test_classify_job_delegates_to_singleton(self, monkeypatch):
        from unittest.mock import Mock

        import app.etl.enrichment.tech_scorer as module

        mock_scorer = Mock()
        expected = object()
        mock_scorer.classify.return_value = expected

        monkeypatch.setattr(module, "get_scorer", lambda: mock_scorer)

        result = module.classify_job(
            "Backend Engineer",
            "Python APIs",
            ["Python"],
        )

        assert result is expected
        mock_scorer.classify.assert_called_once_with(
            "Backend Engineer",
            "Python APIs",
            ["Python"],
            None,
        )
