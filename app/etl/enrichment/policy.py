"""
Classification policy - single source of truth for all thresholds.

This module defines the ClassificationPolicy dataclass which encapsulates
all thresholds, margins, and configuration parameters used for making
classification decisions. Using a single policy object ensures consistency
between production and validation environments.

The policy supports:
- Minimum absolute score thresholds (prevents weak evidence)
- Margin-based classification (compares best vs second-best)
- Category-specific overrides with typed dataclasses
- Confidence thresholds (for reporting only, not classification)

Example:
    policy = ClassificationPolicy(
        tech_minimum=8.0,
        minimum_margin=3.0,
        min_confidence=0.15,
        category_overrides={
            'backend': ThresholdOverride(tech_minimum=10.0, minimum_margin=4.0)
        },
        version="1.0",
        name="production"
    )
    
    # Modify policy using dataclasses.replace
    from dataclasses import replace
    strict_policy = replace(policy, tech_minimum=12.0)
    
    # Get effective thresholds as typed object
    thresholds = policy.get_effective_thresholds('backend')
    print(thresholds.tech_minimum)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Mapping, Union
import warnings


# ============================================================
# Effective Thresholds - Typed return object
# ============================================================

@dataclass(frozen=True)
class EffectiveThresholds:
    """
    Fully resolved thresholds for a category.
    
    This is the typed return object for get_effective_thresholds().
    All values are resolved (no optionals) after applying overrides.
    
    Attributes:
        tech_minimum: Minimum absolute score required
        minimum_margin: Minimum margin over second-best category
        min_confidence: Minimum confidence for reporting (may be None)
    """
    tech_minimum: float
    minimum_margin: float
    min_confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            'tech_minimum': self.tech_minimum,
            'minimum_margin': self.minimum_margin,
            'min_confidence': self.min_confidence,
        }


# ============================================================
# Threshold Override - Typed alternative to nested dicts
# ============================================================

@dataclass(frozen=True)
class ThresholdOverride:
    """
    Category-specific threshold overrides.
    
    All fields are optional - only specified fields are overridden.
    
    Attributes:
        tech_minimum: Minimum absolute score required for this category
        minimum_margin: Minimum margin over second-best category
        min_confidence: Minimum confidence for reporting
    """
    tech_minimum: Optional[float] = None
    minimum_margin: Optional[float] = None
    min_confidence: Optional[float] = None
    
    def apply_to(self, base: EffectiveThresholds) -> EffectiveThresholds:
        """
        Apply this override to base thresholds.
        
        Returns a new EffectiveThresholds with overrides applied.
        """
        return EffectiveThresholds(
            tech_minimum=self.tech_minimum if self.tech_minimum is not None else base.tech_minimum,
            minimum_margin=self.minimum_margin if self.minimum_margin is not None else base.minimum_margin,
            min_confidence=self.min_confidence if self.min_confidence is not None else base.min_confidence,
        )


# ============================================================
# Classification Policy
# ============================================================

@dataclass(frozen=True)
class ClassificationPolicy:
    """
    Immutable classification policy.
    
    All classification decisions use this policy object to ensure
    consistency between production and validation environments.
    
    Attributes:
        tech_minimum: Minimum absolute score required to be considered tech.
                      Prevents classification based on very weak evidence.
        
        minimum_margin: Minimum margin required between the best category
                        and the second-best category. Handles ambiguous cases
                        where multiple categories have similar scores.
        
        min_confidence: Minimum confidence threshold for reporting.
                        This is used ONLY for reporting purposes, NOT for
                        classification decisions. It tells users how reliable
                        the decision is.
        
        category_overrides: Category-specific threshold overrides.
                            Uses typed ThresholdOverride objects.
                            Format: {category_id: ThresholdOverride}
        
        version: Optional version string for reproducibility.
                 Useful when persisting validation reports or experiment metadata.
        
        name: Optional human-readable name for this policy.
              Useful for tracking which policy was used in validation.
        
        description: Optional human-readable description.
    """
    
    # Core thresholds
    tech_minimum: float = 8.0
    minimum_margin: float = 3.0
    min_confidence: Optional[float] = 0.15
    
    # Category-specific overrides
    category_overrides: Mapping[str, ThresholdOverride] = field(default_factory=dict)
    
    # Metadata
    version: str = "1.0.0"
    name: str = ""
    description: str = ""
    
    def __post_init__(self) -> None:
        """Validate policy thresholds."""
        if self.tech_minimum < 0:
            raise ValueError(f"tech_minimum must be >= 0, got {self.tech_minimum}")
        
        if self.minimum_margin < 0:
            raise ValueError(f"minimum_margin must be >= 0, got {self.minimum_margin}")
        
        if self.min_confidence is not None:
            if not 0 <= self.min_confidence <= 1:
                raise ValueError(
                    f"min_confidence must be between 0 and 1, got {self.min_confidence}"
                )
        
        # Convert dict overrides to ThresholdOverride if needed
        if self.category_overrides:
            converted = {}
            for k, v in self.category_overrides.items():
                if isinstance(v, dict):
                    converted[k] = ThresholdOverride(**v)
                else:
                    converted[k] = v
            if converted:
                object.__setattr__(self, 'category_overrides', converted)
    
    def get_effective_thresholds(self, category_id: str) -> EffectiveThresholds:
        """
        Get fully resolved thresholds for a category.
        
        Combines global defaults with category-specific overrides.
        Returns a typed EffectiveThresholds object.
        
        Args:
            category_id: The category identifier (e.g., 'backend', 'frontend')
            
        Returns:
            EffectiveThresholds with all values resolved
        """
        base = EffectiveThresholds(
            tech_minimum=self.tech_minimum,
            minimum_margin=self.minimum_margin,
            min_confidence=self.min_confidence,
        )
        
        override = self.category_overrides.get(category_id)
        if override is not None:
            return override.apply_to(base)
        
        return base
    
    def get_thresholds_for_category(self, category_id: str) -> Dict[str, Any]:
        """
        Get effective thresholds as a dictionary.
        
        DEPRECATED: Use get_effective_thresholds() instead.
        This method exists for backward compatibility.
        
        Args:
            category_id: The category identifier
            
        Returns:
            Dictionary with threshold values
        """
        warnings.warn(
            "get_thresholds_for_category() is deprecated. "
            "Use get_effective_thresholds() which returns a typed object.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.get_effective_thresholds(category_id).to_dict()
    
    @staticmethod
    def _parse_overrides(overrides: Dict[str, Any]) -> Dict[str, ThresholdOverride]:
        """
        Parse and convert override data to ThresholdOverride objects.
        
        Handles both dict and ThresholdOverride inputs.
        """
        result = {}
        for category_id, override_data in overrides.items():
            if isinstance(override_data, ThresholdOverride):
                result[category_id] = override_data
            elif isinstance(override_data, dict):
                    # Only extract fields that ThresholdOverride accepts
                    safe_data = {
                        "tech_minimum": override_data.get("tech_minimum"),
                        "minimum_margin": override_data.get("minimum_margin"),
                        "min_confidence": override_data.get("min_confidence"),
                    }
                    # Remove None values
                    safe_data = {k: v for k, v in safe_data.items() if v is not None}
                    result[category_id] = ThresholdOverride(**safe_data)
            else:
                raise ValueError(
                    f"Invalid override type for {category_id}: {type(override_data)}"
                )
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary for serialization."""
        return {
            'tech_minimum': self.tech_minimum,
            'minimum_margin': self.minimum_margin,
            'min_confidence': self.min_confidence,
            'category_overrides': {
                k: {
                    'tech_minimum': v.tech_minimum,
                    'minimum_margin': v.minimum_margin,
                    'min_confidence': v.min_confidence,
                }
                for k, v in self.category_overrides.items()
            },
            'version': self.version,
            'name': self.name,
            'description': self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClassificationPolicy':
        """Create policy from dictionary."""
        overrides = data.get('category_overrides', {})
        parsed_overrides = cls._parse_overrides(overrides)
        
        return cls(
            tech_minimum=data.get('tech_minimum', 8.0),
            minimum_margin=data.get('minimum_margin', 3.0),
            min_confidence=data.get('min_confidence', 0.15),
            category_overrides=parsed_overrides,
            version=data.get('version', '1.0.0'),
            name=data.get('name', ''),
            description=data.get('description', ''),
        )
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'ClassificationPolicy':
        """
        Create policy from configuration dictionary.
        
        Args:
            config: Configuration dictionary with classification settings
            
        Returns:
            ClassificationPolicy instance
        """
        category_thresholds = config.get("category_thresholds", {})
        parsed_overrides = cls._parse_overrides(category_thresholds)
        
        return cls(
            tech_minimum=config.get('tech_minimum', 8.0),
            minimum_margin=config.get('minimum_margin', 3.0),
            min_confidence=config.get('min_confidence_for_reporting', 0.15),
            category_overrides=parsed_overrides,
            version=config.get('version', '1.0.0'),
            name=config.get('name', ''),
            description=config.get('description', 'From config'),
        )
    
    @classmethod
    def default(cls) -> 'ClassificationPolicy':
        """Get the default balanced policy."""
        return cls(
            tech_minimum=8.0,
            minimum_margin=3.0,
            min_confidence=0.15,
            version="1.0.0",
            name="balanced",
            description="Default balanced policy - good precision/recall tradeoff",
        )
    
    @classmethod
    def conservative(cls) -> 'ClassificationPolicy':
        """Get a conservative policy (higher thresholds, fewer false positives)."""
        return cls(
            tech_minimum=12.0,
            minimum_margin=4.0,
            min_confidence=0.25,
            version="1.0.0",
            name="conservative",
            description="Conservative policy - prioritizes precision over recall",
        )
    
    @classmethod
    def permissive(cls) -> 'ClassificationPolicy':
        """Get a permissive policy (lower thresholds, more false positives)."""
        return cls(
            tech_minimum=5.0,
            minimum_margin=2.0,
            min_confidence=0.08,
            version="1.0.0",
            name="permissive",
            description="Permissive policy - prioritizes recall over precision",
        )
    
    def __repr__(self) -> str:
        """Human-readable representation."""
        return (
            f"ClassificationPolicy("
            f"tech_minimum={self.tech_minimum}, "
            f"minimum_margin={self.minimum_margin}, "
            f"min_confidence={self.min_confidence}, "
            f"overrides={len(self.category_overrides)} categories, "
            f"version='{self.version}', "
            f"name='{self.name}')"
        )


# ============================================================
# Policy Formatter (separated from domain model)
# ============================================================

class PolicyFormatter:
    """Formats ClassificationPolicy for display and logging."""
    
    @staticmethod
    def summary(policy: ClassificationPolicy) -> str:
        """Get a detailed summary of the policy."""
        lines = [
            "=" * 60,
            "Classification Policy Summary",
            "=" * 60,
            f"  Name:             {policy.name or 'unnamed'}",
            f"  Version:          {policy.version}",
            f"  Tech Minimum:     {policy.tech_minimum}",
            f"  Minimum Margin:   {policy.minimum_margin}",
            f"  Min Confidence:   {policy.min_confidence}",
            "",
            f"  Category Overrides: {len(policy.category_overrides)} categories",
        ]
        
        for category_id, override in policy.category_overrides.items():
            lines.append(f"    - {category_id}: {override}")
        
        if policy.description:
            lines.append("")
            lines.append(f"  Description: {policy.description}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    @staticmethod
    def one_line(policy: ClassificationPolicy) -> str:
        """Get a one-line summary."""
        return (
            f"Policy(version='{policy.version}', "
            f"name='{policy.name}', "
            f"tech_minimum={policy.tech_minimum}, "
            f"margin={policy.minimum_margin}, "
            f"confidence={policy.min_confidence})"
        )


# ============================================================
# Convenience Functions
# ============================================================

def get_default_policy() -> ClassificationPolicy:
    """Get the default balanced policy."""
    return ClassificationPolicy.default()


# ============================================================
# Export
# ============================================================

__all__ = [
    'ClassificationPolicy',
    'ThresholdOverride',
    'EffectiveThresholds',
    'PolicyFormatter',
    'get_default_policy',
]