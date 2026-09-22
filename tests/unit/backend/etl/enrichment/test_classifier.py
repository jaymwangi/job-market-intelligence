from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.etl.enrichment.classifier import (
    UNKNOWN_CATEGORY,
    ClassificationDecision,
    DecisionReason,
    _calculate_ambiguity_score,
    _get_competing_categories,
    _get_sorted_categories,
    _is_tech_category,
    _make_decision,
    batch_classify,
    classify_result,
    get_batch_summary,
    get_decision_summary,
)
from app.etl.enrichment.policy import ClassificationPolicy, EffectiveThresholds


def make_result(
    category_scores=None,
    raw_score=10.0,
    confidence=0.8,
):
    return SimpleNamespace(
        category_scores=category_scores or {},
        raw_score=raw_score,
        confidence=confidence,
    )


class TestDecisionReason:
    @pytest.mark.parametrize(
        ("reason", "message"),
        [
            (DecisionReason.SUCCESS, "Classified as tech role"),
            (DecisionReason.SCORE_TOO_LOW, "Score below minimum threshold"),
            (DecisionReason.MARGIN_TOO_LOW, "Margin below minimum threshold"),
            (DecisionReason.NON_TECH_CATEGORY, "Category is marked as non-tech"),
            (DecisionReason.NO_CATEGORIES, "No category scores available"),
            (DecisionReason.UNKNOWN_CATEGORY, "Unknown category"),
            (DecisionReason.NO_COMPETITORS, "No competing categories found"),
        ],
    )
    def test_display_message(self, reason, message):
        assert reason.display_message() == message


class TestClassificationDecision:
    def test_valid_decision(self):
        decision = ClassificationDecision(
            is_tech=True,
            primary_category="backend",
            primary_score=10.0,
            margin=5.0,
            score=12.0,
            confidence=0.8,
            reason=DecisionReason.SUCCESS,
        )

        assert decision.passed_minimum_score is True
        assert decision.passed_margin is True
        assert decision.is_ambiguous is False
        assert decision.is_high_confidence is True
        assert decision.status_emoji == "✅"
        assert decision.status_label == "TECH"

    def test_non_tech_decision_properties(self):
        decision = ClassificationDecision(
            is_tech=False,
            primary_category="non_tech",
            primary_score=5.0,
            margin=1.0,
            score=5.0,
            confidence=0.4,
            reason=DecisionReason.NON_TECH_CATEGORY,
            ambiguity_score=0.8,
        )

        assert decision.passed_minimum_score is True
        assert decision.passed_margin is True
        assert decision.is_ambiguous is True
        assert decision.is_high_confidence is False
        assert decision.status_emoji == "❌"
        assert decision.status_label == "NON-TECH"

    def test_threshold_properties_with_thresholds(self):
        decision = ClassificationDecision(
            is_tech=True,
            primary_category="backend",
            primary_score=10.0,
            margin=3.0,
            score=12.0,
            confidence=0.7,
            reason=DecisionReason.SUCCESS,
            thresholds=EffectiveThresholds(
                tech_minimum=10.0,
                minimum_margin=3.0,
            ),
        )

        assert decision.passed_minimum_score is True
        assert decision.passed_margin is True

    def test_threshold_properties_fail_when_below_thresholds(self):
        decision = ClassificationDecision(
            is_tech=False,
            primary_category="backend",
            primary_score=9.0,
            margin=2.0,
            score=10.0,
            confidence=0.6,
            reason=DecisionReason.SCORE_TOO_LOW,
            thresholds=EffectiveThresholds(
                tech_minimum=10.0,
                minimum_margin=3.0,
            ),
        )

        assert decision.passed_minimum_score is False
        assert decision.passed_margin is False

    def test_threshold_properties_without_thresholds(self):
        decision = ClassificationDecision(
            is_tech=True,
            primary_category="backend",
            primary_score=1.0,
            margin=0.0,
            score=1.0,
            confidence=0.1,
            reason=DecisionReason.SUCCESS,
            thresholds=None,
        )

        assert decision.passed_minimum_score is True
        assert decision.passed_margin is True

    @pytest.mark.parametrize("confidence", [-0.1, 1.1])
    def test_rejects_invalid_confidence(self, confidence):
        with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
            ClassificationDecision(
                is_tech=False,
                primary_category="backend",
                primary_score=1.0,
                margin=0.0,
                score=1.0,
                confidence=confidence,
                reason=DecisionReason.SUCCESS,
            )

    @pytest.mark.parametrize("ambiguity", [-0.1, 1.1])
    def test_rejects_invalid_ambiguity_score(self, ambiguity):
        with pytest.raises(
            ValueError,
            match="ambiguity_score must be between 0 and 1",
        ):
            ClassificationDecision(
                is_tech=False,
                primary_category="backend",
                primary_score=1.0,
                margin=0.0,
                score=1.0,
                confidence=0.5,
                reason=DecisionReason.SUCCESS,
                ambiguity_score=ambiguity,
            )

    def test_to_dict(self):
        decision = ClassificationDecision(
            is_tech=True,
            primary_category="backend",
            primary_score=10.0,
            margin=5.0,
            score=12.0,
            confidence=0.8,
            reason=DecisionReason.SUCCESS,
            second_best_category="frontend",
            second_best_score=5.0,
            ambiguity_score=0.5,
            explanations=["example"],
            thresholds=EffectiveThresholds(8.0, 3.0, 0.15),
            all_scores={"backend": 10.0, "frontend": 5.0},
            competing_categories=[("frontend", 5.0)],
        )

        result = decision.to_dict()

        assert result["is_tech"] is True
        assert result["primary_category"] == "backend"
        assert result["reason"] == "SUCCESS"
        assert result["reason_message"] == "Classified as tech role"
        assert result["thresholds"] == {
            "tech_minimum": 8.0,
            "minimum_margin": 3.0,
            "min_confidence": 0.15,
        }
        assert result["passed_minimum_score"] is True
        assert result["passed_margin"] is True
        assert result["is_ambiguous"] is False
        assert result["is_high_confidence"] is True
        assert result["competing_categories"] == [("frontend", 5.0)]


class TestHelpers:
    @pytest.mark.parametrize(
        ("best", "second", "expected"),
        [
            (10.0, None, 0.0),
            (10.0, 0.0, 0.0),
            (0.0, 5.0, 1.0),
            (10.0, 5.0, 0.5),
            (10.0, 15.0, 1.0),
        ],
    )
    def test_calculate_ambiguity_score(self, best, second, expected):
        assert _calculate_ambiguity_score(best, second) == expected

    def test_get_sorted_categories(self):
        result = _get_sorted_categories({"frontend": 5.0, "backend": 10.0, "data": 7.0})

        assert result == [
            ("backend", 10.0),
            ("data", 7.0),
            ("frontend", 5.0),
        ]

    def test_get_competing_categories_uses_taxonomy(self):
        categories = [
            ("backend", 10.0),
            ("frontend", 5.0),
        ]

        with patch(
            "app.etl.enrichment.classification_config.get_competing_categories",
            return_value=[("frontend", 5.0)],
        ):
            result = _get_competing_categories("backend", categories)

        assert result == [("frontend", 5.0)]

    def test_get_competing_categories_falls_back_on_error(self):
        categories = [
            ("backend", 10.0),
            ("frontend", 5.0),
            ("data", 2.0),
        ]

        with patch(
            "app.etl.enrichment.classification_config.get_competing_categories",
            side_effect=RuntimeError("taxonomy unavailable"),
        ):
            result = _get_competing_categories("backend", categories)

        assert result == [
            ("frontend", 5.0),
            ("data", 2.0),
        ]

    def test_is_tech_category_uses_configuration(self):
        policy = ClassificationPolicy()

        category = SimpleNamespace(is_tech=True)

        with patch("app.etl.enrichment.classification_config.get_config") as get_config:
            get_config.return_value.categories = {"backend": category}

            assert _is_tech_category("backend", policy) is True

    def test_is_tech_category_returns_false_for_missing_category(self):
        policy = ClassificationPolicy()

        with patch("app.etl.enrichment.classification_config.get_config") as get_config:
            get_config.return_value.categories = {}

            assert _is_tech_category("missing", policy) is False

    def test_is_tech_category_fallback(self):
        policy = ClassificationPolicy()

        with patch(
            "app.etl.enrichment.classification_config.get_config",
            side_effect=RuntimeError("config unavailable"),
        ):
            assert _is_tech_category("backend", policy) is True
            assert _is_tech_category("non_tech", policy) is False


class TestClassifyResult:

    def test_make_decision_defaults_explanations_to_empty_list(self):
        decision = _make_decision(
            is_tech=True,
            primary_category="backend",
            primary_score=10.0,
            margin=5.0,
            result=make_result({"backend": 10.0}),
            reason=DecisionReason.SUCCESS,
            thresholds=EffectiveThresholds(
                tech_minimum=8.0,
                minimum_margin=3.0,
            ),
        )

        assert decision.explanations == [DecisionReason.SUCCESS.display_message()]

    def test_existing_reason_message_is_not_duplicated(self):
        message = DecisionReason.SUCCESS.display_message()

        decision = _make_decision(
            is_tech=True,
            primary_category="backend",
            primary_score=10.0,
            margin=5.0,
            result=make_result({"backend": 10.0}),
            reason=DecisionReason.SUCCESS,
            thresholds=EffectiveThresholds(
                tech_minimum=8.0,
                minimum_margin=3.0,
            ),
            explanations=[
                "Some unrelated explanation",
                f"Explanation: {message}",
            ],
        )

        assert decision.explanations == [
            "Some unrelated explanation",
            f"Explanation: {message}",
        ]

    def test_no_categories(self):
        result = make_result()

        decision = classify_result(result, ClassificationPolicy.default())

        assert decision.is_tech is False
        assert decision.primary_category == UNKNOWN_CATEGORY
        assert decision.primary_score == 0.0
        assert decision.reason is DecisionReason.NO_CATEGORIES
        assert "No category scores available" in decision.explanations

    def test_single_category_score_too_low(self):
        result = make_result({"backend": 5.0})

        with patch(
            "app.etl.enrichment.classification_config.get_competing_categories",
            return_value=[],
        ):
            decision = classify_result(result, ClassificationPolicy.default())

        assert decision.is_tech is False
        assert decision.reason is DecisionReason.SCORE_TOO_LOW
        assert decision.primary_category == "backend"
        assert decision.primary_score == 5.0

    def test_single_category_non_tech(self):
        result = make_result({"non_tech": 10.0})

        with (
            patch(
                "app.etl.enrichment.classification_config.get_competing_categories",
                return_value=[],
            ),
            patch("app.etl.enrichment.classification_config.get_config") as get_config,
        ):
            category = SimpleNamespace(is_tech=False)
            get_config.return_value.categories = {"non_tech": category}

            decision = classify_result(result, ClassificationPolicy.default())

        assert decision.is_tech is False
        assert decision.reason is DecisionReason.NON_TECH_CATEGORY

    def test_single_category_success(self):
        result = make_result({"backend": 10.0}, raw_score=12.0, confidence=0.85)

        with (
            patch(
                "app.etl.enrichment.classification_config.get_competing_categories",
                return_value=[],
            ),
            patch("app.etl.enrichment.classification_config.get_config") as get_config,
        ):
            get_config.return_value.categories = {"backend": SimpleNamespace(is_tech=True)}

            decision = classify_result(result, ClassificationPolicy.default())

        assert decision.is_tech is True
        assert decision.reason is DecisionReason.SUCCESS
        assert decision.primary_category == "backend"
        assert decision.margin == 0.0
        assert decision.second_best_category is None
        assert decision.second_best_score is None

    def test_competing_category_score_too_low(self):
        result = make_result(
            {"backend": 5.0, "frontend": 2.0},
            raw_score=5.0,
        )

        with patch(
            "app.etl.enrichment.classification_config.get_competing_categories",
            return_value=[("frontend", 2.0)],
        ):
            decision = classify_result(result, ClassificationPolicy.default())

        assert decision.is_tech is False
        assert decision.reason is DecisionReason.SCORE_TOO_LOW
        assert decision.margin == 3.0

    def test_competing_category_margin_too_low(self):
        result = make_result(
            {"backend": 10.0, "frontend": 8.0},
            raw_score=10.0,
        )

        with patch(
            "app.etl.enrichment.classification_config.get_competing_categories",
            return_value=[("frontend", 8.0)],
        ):
            decision = classify_result(result, ClassificationPolicy.default())

        assert decision.is_tech is False
        assert decision.reason is DecisionReason.MARGIN_TOO_LOW
        assert decision.margin == 2.0
        assert decision.second_best_category == "frontend"

    def test_competing_category_non_tech(self):
        result = make_result(
            {"non_tech": 10.0, "backend": 5.0},
            raw_score=10.0,
        )

        with (
            patch(
                "app.etl.enrichment.classification_config.get_competing_categories",
                return_value=[("backend", 5.0)],
            ),
            patch("app.etl.enrichment.classification_config.get_config") as get_config,
        ):
            get_config.return_value.categories = {"non_tech": SimpleNamespace(is_tech=False)}

            decision = classify_result(result, ClassificationPolicy.default())

        assert decision.is_tech is False
        assert decision.reason is DecisionReason.NON_TECH_CATEGORY

    def test_competing_category_success(self):
        result = make_result(
            {"backend": 12.0, "frontend": 5.0},
            raw_score=14.0,
            confidence=0.9,
        )

        with (
            patch(
                "app.etl.enrichment.classification_config.get_competing_categories",
                return_value=[("frontend", 5.0)],
            ),
            patch("app.etl.enrichment.classification_config.get_config") as get_config,
        ):
            get_config.return_value.categories = {"backend": SimpleNamespace(is_tech=True)}

            decision = classify_result(result, ClassificationPolicy.default())

        assert decision.is_tech is True
        assert decision.reason is DecisionReason.SUCCESS
        assert decision.margin == 7.0
        assert decision.second_best_category == "frontend"
        assert decision.second_best_score == 5.0
        assert decision.ambiguity_score == pytest.approx(5 / 12)
        assert decision.all_scores == {
            "backend": 12.0,
            "frontend": 5.0,
        }

    def test_category_override_is_used(self):
        policy = ClassificationPolicy(
            category_overrides={
                "backend": {
                    "tech_minimum": 12.0,
                    "minimum_margin": 4.0,
                }
            }
        )
        result = make_result({"backend": 10.0, "frontend": 2.0})

        with patch(
            "app.etl.enrichment.classification_config.get_competing_categories",
            return_value=[("frontend", 2.0)],
        ):
            decision = classify_result(result, policy)

        assert decision.reason is DecisionReason.SCORE_TOO_LOW
        assert decision.thresholds.tech_minimum == 12.0


class TestBatchAndSummaries:
    def test_batch_classify(self):
        policy = ClassificationPolicy.default()
        results = [
            make_result({"backend": 10.0}),
            make_result({"frontend": 12.0}),
        ]

        with patch("app.etl.enrichment.classifier.classify_result") as mock_classify:
            mock_classify.side_effect = [
                SimpleNamespace(is_tech=True),
                SimpleNamespace(is_tech=False),
            ]

            decisions = batch_classify(results, policy)

        assert len(decisions) == 2
        assert mock_classify.call_count == 2

    def test_get_decision_summary_without_competitors(self):
        decision = ClassificationDecision(
            is_tech=True,
            primary_category="backend",
            primary_score=12.0,
            margin=0.0,
            score=12.0,
            confidence=0.8,
            reason=DecisionReason.SUCCESS,
            ambiguity_score=0.0,
        )

        summary = get_decision_summary(decision)

        assert "✅ TECH" in summary
        assert "Category: backend" in summary
        assert "score: 12.0" in summary
        assert "Confidence: 0.80" in summary
        assert "Ambiguity: 0.00" in summary
        assert "competitors" not in summary

    def test_get_decision_summary_with_competitors(self):
        decision = ClassificationDecision(
            is_tech=True,
            primary_category="backend",
            primary_score=12.0,
            margin=5.0,
            score=12.0,
            confidence=0.8,
            reason=DecisionReason.SUCCESS,
            competing_categories=[
                ("frontend", 5.0),
                ("data", 3.0),
            ],
        )

        summary = get_decision_summary(decision)

        assert "(competitors: 2)" in summary

    def test_get_batch_summary_empty(self):
        assert get_batch_summary([]) == {
            "total": 0,
            "tech_count": 0,
            "non_tech_count": 0,
        }

    def test_get_batch_summary(self):
        decisions = [
            ClassificationDecision(
                is_tech=True,
                primary_category="backend",
                primary_score=10.0,
                margin=5.0,
                score=10.0,
                confidence=0.9,
                reason=DecisionReason.SUCCESS,
                ambiguity_score=0.2,
            ),
            ClassificationDecision(
                is_tech=False,
                primary_category="frontend",
                primary_score=5.0,
                margin=1.0,
                score=5.0,
                confidence=0.5,
                reason=DecisionReason.MARGIN_TOO_LOW,
                ambiguity_score=0.8,
            ),
            ClassificationDecision(
                is_tech=True,
                primary_category="data",
                primary_score=12.0,
                margin=7.0,
                score=12.0,
                confidence=0.75,
                reason=DecisionReason.SUCCESS,
                ambiguity_score=0.1,
            ),
        ]

        summary = get_batch_summary(decisions)

        assert summary["total"] == 3
        assert summary["tech_count"] == 2
        assert summary["non_tech_count"] == 1
        assert summary["tech_percentage"] == pytest.approx(66.6666667)
        assert summary["ambiguous_count"] == 1
        assert summary["ambiguous_percentage"] == pytest.approx(33.3333333)
        assert summary["high_confidence_count"] == 2
        assert summary["high_confidence_percentage"] == pytest.approx(66.6666667)
