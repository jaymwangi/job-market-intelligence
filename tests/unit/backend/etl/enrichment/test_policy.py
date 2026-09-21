import warnings

import pytest

from app.etl.enrichment.policy import (
    ClassificationPolicy,
    EffectiveThresholds,
    PolicyFormatter,
    ThresholdOverride,
    get_default_policy,
)


class TestEffectiveThresholds:
    def test_to_dict_returns_all_thresholds(self):
        thresholds = EffectiveThresholds(
            tech_minimum=10.0,
            minimum_margin=4.0,
            min_confidence=0.25,
        )

        assert thresholds.to_dict() == {
            "tech_minimum": 10.0,
            "minimum_margin": 4.0,
            "min_confidence": 0.25,
        }

    def test_to_dict_supports_none_confidence(self):
        thresholds = EffectiveThresholds(
            tech_minimum=10.0,
            minimum_margin=4.0,
            min_confidence=None,
        )

        assert thresholds.to_dict()["min_confidence"] is None


class TestThresholdOverride:
    def test_apply_to_overrides_all_values(self):
        base = EffectiveThresholds(
            tech_minimum=8.0,
            minimum_margin=3.0,
            min_confidence=0.15,
        )
        override = ThresholdOverride(
            tech_minimum=12.0,
            minimum_margin=5.0,
            min_confidence=0.30,
        )

        result = override.apply_to(base)

        assert result == EffectiveThresholds(
            tech_minimum=12.0,
            minimum_margin=5.0,
            min_confidence=0.30,
        )

    def test_apply_to_preserves_unspecified_values(self):
        base = EffectiveThresholds(
            tech_minimum=8.0,
            minimum_margin=3.0,
            min_confidence=0.15,
        )
        override = ThresholdOverride(tech_minimum=12.0)

        result = override.apply_to(base)

        assert result.tech_minimum == 12.0
        assert result.minimum_margin == 3.0
        assert result.min_confidence == 0.15

    def test_default_override_preserves_base(self):
        base = EffectiveThresholds(8.0, 3.0, 0.15)

        result = ThresholdOverride().apply_to(base)

        assert result == base


class TestClassificationPolicy:
    def test_default_values(self):
        policy = ClassificationPolicy()

        assert policy.tech_minimum == 8.0
        assert policy.minimum_margin == 3.0
        assert policy.min_confidence == 0.15
        assert policy.category_overrides == {}
        assert policy.version == "1.0.0"
        assert policy.name == ""
        assert policy.description == ""

    def test_rejects_negative_tech_minimum(self):
        with pytest.raises(ValueError, match="tech_minimum must be >= 0"):
            ClassificationPolicy(tech_minimum=-1.0)

    def test_rejects_negative_minimum_margin(self):
        with pytest.raises(ValueError, match="minimum_margin must be >= 0"):
            ClassificationPolicy(minimum_margin=-1.0)

    @pytest.mark.parametrize("confidence", [-0.01, 1.01])
    def test_rejects_invalid_confidence(self, confidence):
        with pytest.raises(
            ValueError,
            match="min_confidence must be between 0 and 1",
        ):
            ClassificationPolicy(min_confidence=confidence)

    def test_allows_none_confidence(self):
        policy = ClassificationPolicy(min_confidence=None)

        assert policy.min_confidence is None

    def test_converts_dict_overrides_to_threshold_override(self):
        policy = ClassificationPolicy(
            category_overrides={
                "backend": {
                    "tech_minimum": 10.0,
                    "minimum_margin": 4.0,
                }
            }
        )

        assert isinstance(
            policy.category_overrides["backend"],
            ThresholdOverride,
        )
        assert policy.category_overrides["backend"].tech_minimum == 10.0
        assert policy.category_overrides["backend"].minimum_margin == 4.0

    def test_preserves_threshold_override_objects(self):
        override = ThresholdOverride(tech_minimum=11.0)
        policy = ClassificationPolicy(
            category_overrides={"backend": override}
        )

        assert policy.category_overrides["backend"] is override

    def test_get_effective_thresholds_without_override(self):
        policy = ClassificationPolicy(
            tech_minimum=9.0,
            minimum_margin=4.0,
            min_confidence=0.2,
        )

        result = policy.get_effective_thresholds("backend")

        assert result == EffectiveThresholds(9.0, 4.0, 0.2)

    def test_get_effective_thresholds_with_override(self):
        policy = ClassificationPolicy(
            tech_minimum=8.0,
            minimum_margin=3.0,
            min_confidence=0.15,
            category_overrides={
                "backend": ThresholdOverride(
                    tech_minimum=12.0,
                    minimum_margin=5.0,
                )
            },
        )

        result = policy.get_effective_thresholds("backend")

        assert result.tech_minimum == 12.0
        assert result.minimum_margin == 5.0
        assert result.min_confidence == 0.15

    def test_get_effective_thresholds_unknown_category_uses_base(self):
        policy = ClassificationPolicy()

        result = policy.get_effective_thresholds("unknown")

        assert result == EffectiveThresholds(8.0, 3.0, 0.15)

    def test_get_thresholds_for_category_is_deprecated(self):
        policy = ClassificationPolicy()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            result = policy.get_thresholds_for_category("backend")

        assert result == {
            "tech_minimum": 8.0,
            "minimum_margin": 3.0,
            "min_confidence": 0.15,
        }
        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        assert "deprecated" in str(caught[0].message)

    def test_parse_overrides_accepts_threshold_override(self):
        override = ThresholdOverride(tech_minimum=10.0)

        result = ClassificationPolicy._parse_overrides(
            {"backend": override}
        )

        assert result == {"backend": override}

    def test_parse_overrides_accepts_dict(self):
        result = ClassificationPolicy._parse_overrides(
            {
                "backend": {
                    "tech_minimum": 10.0,
                    "minimum_margin": 4.0,
                    "min_confidence": 0.25,
                }
            }
        )

        assert result["backend"] == ThresholdOverride(
            tech_minimum=10.0,
            minimum_margin=4.0,
            min_confidence=0.25,
        )

    def test_parse_overrides_ignores_unknown_dict_fields(self):
        result = ClassificationPolicy._parse_overrides(
            {
                "backend": {
                    "tech_minimum": 10.0,
                    "unknown_field": 999,
                }
            }
        )

        assert result["backend"] == ThresholdOverride(
            tech_minimum=10.0
        )

    def test_parse_overrides_removes_none_values(self):
        result = ClassificationPolicy._parse_overrides(
            {
                "backend": {
                    "tech_minimum": 10.0,
                    "minimum_margin": None,
                    "min_confidence": None,
                }
            }
        )

        assert result["backend"] == ThresholdOverride(
            tech_minimum=10.0
        )

    def test_parse_overrides_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid override type"):
            ClassificationPolicy._parse_overrides(
                {"backend": "invalid"}
            )

    def test_to_dict_serializes_policy(self):
        policy = ClassificationPolicy(
            tech_minimum=10.0,
            minimum_margin=4.0,
            min_confidence=0.25,
            category_overrides={
                "backend": ThresholdOverride(
                    tech_minimum=12.0,
                    minimum_margin=5.0,
                )
            },
            version="2.0",
            name="test",
            description="Test policy",
        )

        result = policy.to_dict()

        assert result == {
            "tech_minimum": 10.0,
            "minimum_margin": 4.0,
            "min_confidence": 0.25,
            "category_overrides": {
                "backend": {
                    "tech_minimum": 12.0,
                    "minimum_margin": 5.0,
                    "min_confidence": None,
                }
            },
            "version": "2.0",
            "name": "test",
            "description": "Test policy",
        }

    def test_from_dict_creates_policy(self):
        data = {
            "tech_minimum": 10.0,
            "minimum_margin": 4.0,
            "min_confidence": 0.25,
            "category_overrides": {
                "backend": {
                    "tech_minimum": 12.0,
                }
            },
            "version": "2.0",
            "name": "custom",
            "description": "Custom policy",
        }

        policy = ClassificationPolicy.from_dict(data)

        assert policy.tech_minimum == 10.0
        assert policy.minimum_margin == 4.0
        assert policy.min_confidence == 0.25
        assert policy.version == "2.0"
        assert policy.name == "custom"
        assert policy.description == "Custom policy"
        assert policy.category_overrides["backend"].tech_minimum == 12.0

    def test_from_dict_uses_defaults_for_missing_values(self):
        policy = ClassificationPolicy.from_dict({})

        assert policy.tech_minimum == 8.0
        assert policy.minimum_margin == 3.0
        assert policy.min_confidence == 0.15
        assert policy.version == "1.0.0"
        assert policy.name == ""
        assert policy.description == ""

    def test_from_config_maps_configuration_names(self):
        config = {
            "tech_minimum": 11.0,
            "minimum_margin": 4.0,
            "min_confidence_for_reporting": 0.22,
            "category_thresholds": {
                "backend": {
                    "tech_minimum": 13.0,
                }
            },
            "version": "3.0",
            "name": "configured",
            "description": "Configured policy",
        }

        policy = ClassificationPolicy.from_config(config)

        assert policy.tech_minimum == 11.0
        assert policy.minimum_margin == 4.0
        assert policy.min_confidence == 0.22
        assert policy.version == "3.0"
        assert policy.name == "configured"
        assert policy.description == "Configured policy"
        assert policy.category_overrides["backend"].tech_minimum == 13.0

    def test_from_config_uses_default_description(self):
        policy = ClassificationPolicy.from_config({})

        assert policy.description == "From config"

    def test_default_policy(self):
        policy = ClassificationPolicy.default()

        assert policy.tech_minimum == 8.0
        assert policy.minimum_margin == 3.0
        assert policy.min_confidence == 0.15
        assert policy.version == "1.0.0"
        assert policy.name == "balanced"
        assert "precision/recall" in policy.description

    def test_conservative_policy(self):
        policy = ClassificationPolicy.conservative()

        assert policy.tech_minimum == 12.0
        assert policy.minimum_margin == 4.0
        assert policy.min_confidence == 0.25
        assert policy.name == "conservative"

    def test_permissive_policy(self):
        policy = ClassificationPolicy.permissive()

        assert policy.tech_minimum == 5.0
        assert policy.minimum_margin == 2.0
        assert policy.min_confidence == 0.08
        assert policy.name == "permissive"

    def test_repr_contains_key_information(self):
        policy = ClassificationPolicy(
            tech_minimum=10.0,
            minimum_margin=4.0,
            min_confidence=0.2,
            category_overrides={
                "backend": ThresholdOverride(tech_minimum=12.0),
                "frontend": ThresholdOverride(minimum_margin=5.0),
            },
            version="2.0",
            name="custom",
        )

        result = repr(policy)

        assert "ClassificationPolicy(" in result
        assert "tech_minimum=10.0" in result
        assert "minimum_margin=4.0" in result
        assert "min_confidence=0.2" in result
        assert "overrides=2 categories" in result
        assert "version='2.0'" in result
        assert "name='custom'" in result


class TestPolicyFormatter:
    def test_summary_includes_policy_information(self):
        policy = ClassificationPolicy(
            version="2.0",
            name="production",
            tech_minimum=10.0,
            minimum_margin=4.0,
            min_confidence=0.25,
            description="Production policy",
        )

        result = PolicyFormatter.summary(policy)

        assert "Classification Policy Summary" in result
        assert "Name:             production" in result
        assert "Version:          2.0" in result
        assert "Tech Minimum:     10.0" in result
        assert "Minimum Margin:   4.0" in result
        assert "Min Confidence:   0.25" in result
        assert "Category Overrides: 0 categories" in result
        assert "Description: Production policy" in result

    def test_summary_uses_unnamed_when_name_empty(self):
        policy = ClassificationPolicy()

        result = PolicyFormatter.summary(policy)

        assert "Name:             unnamed" in result

    def test_summary_includes_category_overrides(self):
        policy = ClassificationPolicy(
            category_overrides={
                "backend": ThresholdOverride(tech_minimum=12.0)
            }
        )

        result = PolicyFormatter.summary(policy)

        assert "Category Overrides: 1 categories" in result
        assert "backend:" in result
        assert "ThresholdOverride" in result

    def test_one_line_formats_policy(self):
        policy = ClassificationPolicy(
            version="2.0",
            name="production",
            tech_minimum=10.0,
            minimum_margin=4.0,
            min_confidence=0.25,
        )

        result = PolicyFormatter.one_line(policy)

        assert result == (
            "Policy(version='2.0', name='production', "
            "tech_minimum=10.0, margin=4.0, confidence=0.25)"
        )


def test_get_default_policy():
    policy = get_default_policy()

    assert policy == ClassificationPolicy.default()
