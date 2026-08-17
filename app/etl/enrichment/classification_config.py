"""
Configuration loader for technology classification.

This module loads and caches the technology classification configuration
from YAML files. It provides a clean interface for accessing:
- Category definitions (keywords, weights, metadata)
- Aliases for keyword normalization
- Stopwords
- Thresholds and weights
- Category priority
- Classification policy loading
- Category hierarchy and taxonomy
- Title patterns with strength metadata

The configuration is loaded once and cached for performance.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Tuple
import yaml
from packaging.version import Version


# ============================================================
# Custom Exceptions
# ============================================================

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


# ============================================================
# Enums
# ============================================================

class CategoryRole(str, Enum):
    """Role of a category in the hierarchy."""
    PARENT = "parent"          # Top-level parent category
    SPECIALIZATION = "specialization"  # Child of a parent
    STANDALONE = "standalone"  # Independent category


# ============================================================
# Data Classes
# ============================================================

@dataclass(frozen=True, slots=True)
class CategoryConfig:
    """Configuration for a single technology category with strength and specificity metadata."""

    id: str
    display_name: str
    icon: str
    color: str
    description: str
    family: str
    is_tech: bool
    weight: float
    keywords: Mapping[str, int] = field(default_factory=dict)
    negative_keywords: List[str] = field(default_factory=list)
    regex: List[str] = field(default_factory=list)
    
    # Hierarchy metadata
    parent: Optional[str] = None
    role: CategoryRole = CategoryRole.STANDALONE
    
    # Title pattern metadata
    strength: str = "potential"  # strong, potential, adjacent, ambiguous
    specificity: str = "medium"   # high, medium, low


@dataclass(frozen=True, slots=True)
class TitlePatternConfig:
    """Configuration for a title pattern with strength metadata."""
    
    pattern: str
    categories: Tuple[str, ...] = field(default_factory=tuple)
    weight: float = 8.0
    strength: str = "potential"
    specificity: str = "medium"
    
    def __post_init__(self):
        """Validate pattern and compile regex."""
        if not self.pattern or not isinstance(self.pattern, str):
            raise ConfigurationError(f"Title pattern must be a non-empty string, got {type(self.pattern)}")
        if isinstance(self.categories, list):
            object.__setattr__(self, 'categories', tuple(self.categories))
        try:
            re.compile(self.pattern, re.IGNORECASE)
        except re.error as e:
            raise ConfigurationError(f"Invalid regex pattern '{self.pattern}': {e}")
    
    @property
    def is_strong(self) -> bool:
        return self.strength == "strong"
    
    @property
    def is_potential(self) -> bool:
        return self.strength == "potential"
    
    @property
    def is_adjacent(self) -> bool:
        return self.strength == "adjacent"
    
    @property
    def is_ambiguous(self) -> bool:
        return self.strength == "ambiguous"
    
    @property
    def strength_priority(self) -> int:
        priorities = {"strong": 4, "potential": 3, "adjacent": 2, "ambiguous": 1}
        return priorities.get(self.strength, 0)


@dataclass(frozen=True, slots=True)
class ClassificationConfig:
    """Complete classification configuration."""

    version: str
    last_updated: str

    # Weights and thresholds
    weights: Mapping[str, float]
    thresholds: Mapping[str, float]
    boosts: Mapping[str, float]
    category_priority: List[str]

    # Matching
    matching: Mapping[str, float]

    # Aliases and stopwords
    aliases: Mapping[str, str]
    stopwords: Set[str]

    # Categories
    categories: Mapping[str, CategoryConfig]

    # Category-specific thresholds (single source of truth)
    category_thresholds: Mapping[str, Mapping[str, float]]
    
    # Title patterns with strength metadata
    tech_title_patterns: List[TitlePatternConfig] = field(default_factory=list)

    # Classification policy settings
    classification: Mapping[str, Any] = field(default_factory=dict)
    title_pattern_boost: float = 3.0

    # Precomputed display name lookup (O(1))
    _display_name_lookup: Mapping[str, str] = field(default_factory=dict, repr=False)
    
    # Precomputed taxonomy structures (O(1) lookups)
    _children: Mapping[str, Set[str]] = field(default_factory=dict, repr=False)
    _parents: Mapping[str, Optional[str]] = field(default_factory=dict, repr=False)
    _roles: Mapping[str, CategoryRole] = field(default_factory=dict, repr=False)


# ============================================================
# Configuration Loader
# ============================================================

class ClassificationConfigLoader:
    """Load and cache classification configuration from YAML."""

    _config: Optional[ClassificationConfig] = None
    _config_path: Optional[Path] = None

    # Compiled regex patterns cache
    _compiled_regex: Dict[str, List[re.Pattern]] = {}
    _compiled_title_patterns: Dict[str, re.Pattern] = {}

    # Supported major version
    SUPPORTED_MAJOR_VERSION = 3

    # Required top-level sections
    REQUIRED_SECTIONS = {
        "weights",
        "thresholds",
        "boosts",
        "matching",
        "category_priority",
        "aliases",
        "stopwords",
        "categories",
    }

    # Required keys in weights
    REQUIRED_WEIGHT_KEYS = {"title", "description", "skills"}

    # Required keys in thresholds
    REQUIRED_THRESHOLD_KEYS = {
        "tech_minimum",
        "high_confidence",
        "medium_confidence",
        "low_confidence",
        "min_confidence_to_classify",
    }

    # Required keys in boosts
    REQUIRED_BOOST_KEYS = {
        "title_exact_match",
        "title_regex_match",
        "description_keyword",
        "skill_keyword",
        "multiple_category_bonus",
    }

    # Required keys in matching
    REQUIRED_MATCHING_KEYS = {
        "exact_weight",
        "stemmed_weight",
        "fuzzy_weight",
        "regex_weight",
    }

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> ClassificationConfig:
        """Load configuration from YAML file.

        Args:
            config_path: Path to the YAML configuration file.
                        Defaults to config/tech_classification.yaml.

        Returns:
            ClassificationConfig: The loaded configuration.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        # Determine config path
        if config_path is None:
            config_path = cls._get_default_config_path()

        # Check cache
        if (
            cls._config is not None
            and cls._config_path is not None
            and cls._config_path == config_path
        ):
            return cls._config

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        # Load raw data
        try:
            with config_path.open("r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {config_path}: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e

        # Validate required sections exist
        cls._validate_required_sections(raw_data)

        # Parse and validate
        config = cls._parse_config(raw_data)
        cls._validate_config(config)
        
        # Build taxonomy structures
        config = cls._build_taxonomy(config)

        # Store and return
        cls._config = config
        cls._config_path = config_path
        cls._compiled_regex.clear()
        cls._compiled_title_patterns.clear()

        return config

    @classmethod
    def reload(cls) -> ClassificationConfig:
        """Force reload of configuration."""
        cls._config = None
        cls._config_path = None
        cls._compiled_regex.clear()
        cls._compiled_title_patterns.clear()

        # Clear function caches
        get_config.cache_clear()
        get_category_config.cache_clear()

        return cls.load()

    @classmethod
    def _get_default_config_path(cls) -> Path:
        """Get the default configuration path."""
        return Path(__file__).resolve().parents[3] / "config" / "tech_classification.yaml"

    @classmethod
    def _validate_required_sections(cls, raw_data: Dict[str, Any]) -> None:
        """Validate all required sections exist in raw data."""
        missing = cls.REQUIRED_SECTIONS - set(raw_data.keys())
        if missing:
            raise ConfigurationError(
                f"Missing required sections: {', '.join(sorted(missing))}"
            )

    @classmethod
    def _normalize_alias_table(cls, raw_aliases: Dict[str, str]) -> Dict[str, str]:
        """Normalize aliases: strip, lowercase, and detect duplicate keys."""
        normalized: Dict[str, str] = {}
        
        for alias, target in raw_aliases.items():
            normalized_alias = alias.strip().lower()
            normalized_target = target.strip().lower()
            
            if not normalized_alias:
                raise ConfigurationError(f"Empty alias key: '{alias}'")
            if not normalized_target:
                raise ConfigurationError(f"Empty alias target: '{target}'")
            
            # Check for duplicate alias key only (allow many-to-one mappings)
            if normalized_alias in normalized:
                raise ConfigurationError(
                    f"Duplicate alias key: '{alias}' and '{normalized_alias}' both map to "
                    f"'{normalized_target}' (previous target: '{normalized[normalized_alias]}')"
                )
            
            normalized[normalized_alias] = normalized_target
        
        return normalized

    @classmethod
    def _normalize_keywords(
        cls,
        raw_keywords: Dict[str, int],
        aliases: Dict[str, str],
        category_id: str,
    ) -> Dict[str, int]:
        """Normalize keywords using aliases, handling collisions."""
        normalized: Dict[str, int] = {}

        for raw_kw, weight in raw_keywords.items():
            # Validate weight
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise ConfigurationError(
                    f"Keyword '{raw_kw}' in category '{category_id}' "
                    f"has non-numeric weight: {weight}"
                )
            if weight <= 0:
                raise ConfigurationError(
                    f"Keyword '{raw_kw}' in category '{category_id}' "
                    f"has non-positive weight: {weight}"
                )

            # Normalize keyword
            normalized_kw = aliases.get(raw_kw.strip().lower(), raw_kw.strip().lower())

            # Handle collisions (multiple keywords mapping to same normalized form)
            if normalized_kw in normalized:
                # Merge weights (add them)
                normalized[normalized_kw] += weight
            else:
                normalized[normalized_kw] = weight

        return normalized

    @classmethod
    def _parse_title_patterns(cls, raw_patterns: List[Any]) -> List[TitlePatternConfig]:
        """Parse title patterns from raw configuration."""
        patterns: List[TitlePatternConfig] = []
        
        for pattern_config in raw_patterns:
            if isinstance(pattern_config, str):
                # Simple string pattern
                patterns.append(TitlePatternConfig(
                    pattern=pattern_config,
                    categories=(),
                    weight=8.0,
                    strength="potential",
                    specificity="medium"
                ))
            elif isinstance(pattern_config, dict):
                # Full pattern configuration
                patterns.append(TitlePatternConfig(
                    pattern=pattern_config.get('pattern', ''),
                    categories=tuple(pattern_config.get('categories', [])),
                    weight=float(pattern_config.get('weight', 8.0)),
                    strength=pattern_config.get('strength', 'potential'),
                    specificity=pattern_config.get('specificity', 'medium')
                ))
            else:
                raise ConfigurationError(
                    f"Invalid title pattern type: {type(pattern_config)}"
                )
        
        return patterns

    @classmethod
    def _parse_config(cls, raw_data: Dict[str, Any]) -> ClassificationConfig:
        """Parse raw YAML data into a ClassificationConfig."""

        # Normalize aliases first (they're used in keyword normalization)
        raw_aliases = raw_data.get("aliases", {})
        aliases = cls._normalize_alias_table(raw_aliases)

        # Parse categories with normalized keywords
        categories: Dict[str, CategoryConfig] = {}
        display_name_lookup: Dict[str, str] = {}

        for cat_id, cat_data in raw_data.get("categories", {}).items():
            raw_keywords = cat_data.get("keywords", {})
            normalized_keywords = cls._normalize_keywords(
                raw_keywords,
                aliases,
                cat_id,
            )

            # Parse role
            role_str = cat_data.get("role", "standalone")
            try:
                role = CategoryRole(role_str)
            except ValueError:
                raise ConfigurationError(
                    f"Invalid role '{role_str}' for category '{cat_id}'. "
                    f"Must be one of: {[r.value for r in CategoryRole]}"
                )

            category = CategoryConfig(
                id=cat_data.get("id", cat_id),
                display_name=cat_data.get("display_name", cat_id.title()),
                icon=cat_data.get("icon", "🌐"),
                color=cat_data.get("color", "#6B7280"),
                description=cat_data.get("description", ""),
                family=cat_data.get("family", "other"),
                is_tech=cat_data.get("is_tech", False),
                weight=float(cat_data.get("weight", 1.0)),
                keywords=normalized_keywords,
                negative_keywords=cat_data.get("negative_keywords", []),
                regex=cat_data.get("regex", []),
                parent=cat_data.get("parent"),
                role=role,
                strength=cat_data.get("strength", "potential"),
                specificity=cat_data.get("specificity", "medium"),
            )

            categories[cat_id] = category
            display_name_lookup[category.display_name.lower()] = cat_id

        # Parse title patterns
        raw_patterns = raw_data.get("tech_title_patterns", [])
        title_patterns = cls._parse_title_patterns(raw_patterns)

        # Get classification settings
        classification = raw_data.get("classification", {})

        return ClassificationConfig(
            version=raw_data.get("version", "1.0.0"),
            last_updated=raw_data.get("last_updated", ""),
            weights=raw_data.get("weights", {}),
            thresholds=raw_data.get("thresholds", {}),
            boosts=raw_data.get("boosts", {}),
            category_priority=raw_data.get("category_priority", []),
            matching=raw_data.get("matching", {}),
            aliases=aliases,
            stopwords=set(raw_data.get("stopwords", [])),
            categories=categories,
            category_thresholds=raw_data.get("category_thresholds", {}),
            tech_title_patterns=title_patterns,
            classification=classification,
            title_pattern_boost=raw_data.get("title_pattern_boost", 3.0),
            _display_name_lookup=display_name_lookup,
            # Taxonomy structures will be built after validation
            _children=defaultdict(set),
            _parents={},
            _roles={},
        )

    @classmethod
    def _build_taxonomy(cls, config: ClassificationConfig) -> ClassificationConfig:
        """Build taxonomy structures for O(1) lookups."""
        children: Dict[str, Set[str]] = defaultdict(set)
        parents: Dict[str, Optional[str]] = {}
        roles: Dict[str, CategoryRole] = {}

        for cat_id, cat in config.categories.items():
            parents[cat_id] = cat.parent
            roles[cat_id] = cat.role
            
            if cat.parent:
                # Validate parent exists
                if cat.parent not in config.categories:
                    raise ConfigurationError(
                        f"Category '{cat_id}' references parent '{cat.parent}' "
                        f"which does not exist"
                    )
                children[cat.parent].add(cat_id)

        # Validate role consistency
        for cat_id, role in roles.items():
            if role == CategoryRole.PARENT:
                # Parent should have at least one child
                if cat_id not in children or not children[cat_id]:
                    # Allow parent with no children (future-proofing)
                    pass
            elif role == CategoryRole.SPECIALIZATION:
                # Specialization must have a parent
                if not parents.get(cat_id):
                    raise ConfigurationError(
                        f"Specialization '{cat_id}' must have a parent defined"
                    )
            # STANDALONE can have either parent or not

        # Create a new config with taxonomy structures
        return ClassificationConfig(
            version=config.version,
            last_updated=config.last_updated,
            weights=config.weights,
            thresholds=config.thresholds,
            boosts=config.boosts,
            category_priority=config.category_priority,
            matching=config.matching,
            aliases=config.aliases,
            stopwords=config.stopwords,
            categories=config.categories,
            category_thresholds=config.category_thresholds,
            tech_title_patterns=config.tech_title_patterns,
            classification=config.classification,
            title_pattern_boost=config.title_pattern_boost,
            _display_name_lookup=config._display_name_lookup,
            _children=dict(children),
            _parents=parents,
            _roles=roles,
        )

    @classmethod
    def _validate_config(cls, config: ClassificationConfig) -> None:
        """Validate configuration and raise ConfigurationError on issues."""
        errors = []

        # Run all validation checks
        errors.extend(cls._validate_version(config))
        errors.extend(cls._validate_weights(config))
        errors.extend(cls._validate_thresholds(config))
        errors.extend(cls._validate_boosts(config))
        errors.extend(cls._validate_matching(config))
        errors.extend(cls._validate_priority(config))
        errors.extend(cls._validate_categories(config))
        errors.extend(cls._validate_aliases(config))
        errors.extend(cls._validate_category_thresholds(config))
        errors.extend(cls._validate_title_patterns(config))

        # If there are errors, raise
        if errors:
            error_msg = "\n  - ".join([""] + errors)
            raise ConfigurationError(f"Configuration validation failed:{error_msg}")

    @classmethod
    def _is_numeric(cls, value: Any) -> bool:
        """Check if a value is numeric (int or float, not bool)."""
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @classmethod
    def _validate_version(cls, config: ClassificationConfig) -> List[str]:
        """Validate version compatibility."""
        errors = []
        version_str = config.version

        try:
            version = Version(version_str)
            if version.major != cls.SUPPORTED_MAJOR_VERSION:
                errors.append(
                    f"Unsupported major version: {version.major}. "
                    f"Expected {cls.SUPPORTED_MAJOR_VERSION}.x.x"
                )
        except Exception:
            errors.append(f"Invalid version format: {version_str}")

        return errors

    @classmethod
    def _validate_weights(cls, config: ClassificationConfig) -> List[str]:
        """Validate weights section."""
        errors = []
        weights = config.weights

        # Check required keys
        for key in cls.REQUIRED_WEIGHT_KEYS:
            if key not in weights:
                errors.append(f"Missing weight key: '{key}'")
            else:
                value = weights[key]
                if not cls._is_numeric(value):
                    errors.append(f"Weight '{key}' must be numeric (got {type(value).__name__})")
                elif value <= 0:
                    errors.append(f"Weight '{key}' must be positive (got {value})")

        # Check sum
        if weights:
            total = sum(weights.values())
            if not (0.99 <= total <= 1.01):
                errors.append(f"Weights must sum to 1.0 (currently {total:.2f})")

        return errors

    @classmethod
    def _validate_thresholds(cls, config: ClassificationConfig) -> List[str]:
        """Validate thresholds section."""
        errors = []
        thresholds = config.thresholds

        for key in cls.REQUIRED_THRESHOLD_KEYS:
            if key not in thresholds:
                errors.append(f"Missing threshold key: '{key}'")
            else:
                value = thresholds[key]
                if not cls._is_numeric(value):
                    errors.append(f"Threshold '{key}' must be numeric (got {type(value).__name__})")
                elif value < 0:
                    errors.append(f"Threshold '{key}' must be non-negative (got {value})")

        return errors

    @classmethod
    def _validate_boosts(cls, config: ClassificationConfig) -> List[str]:
        """Validate boosts section."""
        errors = []
        boosts = config.boosts

        for key in cls.REQUIRED_BOOST_KEYS:
            if key not in boosts:
                errors.append(f"Missing boost key: '{key}'")
            else:
                value = boosts[key]
                if not cls._is_numeric(value):
                    errors.append(f"Boost '{key}' must be numeric (got {type(value).__name__})")
                elif value < 0:
                    errors.append(f"Boost '{key}' must be non-negative (got {value})")

        return errors

    @classmethod
    def _validate_matching(cls, config: ClassificationConfig) -> List[str]:
        """Validate matching section."""
        errors = []
        matching = config.matching

        for key in cls.REQUIRED_MATCHING_KEYS:
            if key not in matching:
                errors.append(f"Missing matching key: '{key}'")
            else:
                value = matching[key]
                if not cls._is_numeric(value):
                    errors.append(f"Matching '{key}' must be numeric (got {type(value).__name__})")
                elif value < 0:
                    errors.append(f"Matching '{key}' must be non-negative (got {value})")

        return errors

    @classmethod
    def _validate_priority(cls, config: ClassificationConfig) -> List[str]:
        """Validate category priority."""
        errors = []
        for cat_id in config.category_priority:
            if cat_id not in config.categories:
                errors.append(f"Category '{cat_id}' in priority list not found in categories")
        return errors

    @classmethod
    def _validate_categories(cls, config: ClassificationConfig) -> List[str]:
        """Validate category definitions."""
        errors = []
        seen_ids = set()
        seen_display_names = set()

        for cat_id, cat in config.categories.items():
            # Check unique ID
            if cat_id in seen_ids:
                errors.append(f"Duplicate category ID: {cat_id}")
            seen_ids.add(cat_id)

            # Check unique display name
            display_name_lower = cat.display_name.lower()
            if display_name_lower in seen_display_names:
                errors.append(f"Duplicate display name: {cat.display_name}")
            seen_display_names.add(display_name_lower)

            # Check category ID matches key
            if cat.id != cat_id:
                errors.append(f"Category ID mismatch: key='{cat_id}', id='{cat.id}'")

            # Validate regex patterns
            for pattern in cat.regex:
                try:
                    re.compile(pattern, re.IGNORECASE)
                except re.error as e:
                    errors.append(
                        f"Invalid regex in category '{cat_id}': '{pattern}' - {e}"
                    )

            # Validate keywords (already validated during parsing, but double-check)
            for kw, weight in cat.keywords.items():
                if not cls._is_numeric(weight) or weight <= 0:
                    errors.append(
                        f"Keyword '{kw}' in category '{cat_id}' "
                        f"has invalid weight: {weight}"
                    )

            # Validate strength value
            valid_strengths = {"strong", "potential", "adjacent", "ambiguous"}
            if cat.strength not in valid_strengths:
                errors.append(
                    f"Invalid strength '{cat.strength}' in category '{cat_id}'. "
                    f"Must be one of: {valid_strengths}"
                )

            # Validate specificity value
            valid_specificities = {"high", "medium", "low"}
            if cat.specificity not in valid_specificities:
                errors.append(
                    f"Invalid specificity '{cat.specificity}' in category '{cat_id}'. "
                    f"Must be one of: {valid_specificities}"
                )

        return errors

    @classmethod
    def _validate_aliases(cls, config: ClassificationConfig) -> List[str]:
        """Validate aliases."""
        errors = []

        for alias, target in config.aliases.items():
            if not alias:
                errors.append(f"Empty alias key: '{alias}' -> '{target}'")
            if not target:
                errors.append(f"Empty alias target: '{alias}' -> '{target}'")

        return errors
    
    @classmethod
    def _validate_category_thresholds(cls, config: ClassificationConfig) -> List[str]:
        """Validate category-specific thresholds reference existing categories."""
        errors = []
        for cat_id in config.category_thresholds:
            if cat_id not in config.categories:
                errors.append(
                    f"Category '{cat_id}' in category_thresholds not found in categories"
                )
            else:
                # Validate threshold values
                for key, value in config.category_thresholds[cat_id].items():
                    if not cls._is_numeric(value):
                        errors.append(
                            f"Threshold '{key}' for category '{cat_id}' "
                            f"must be numeric (got {type(value).__name__})"
                        )
                    elif value < 0:
                        errors.append(
                            f"Threshold '{key}' for category '{cat_id}' "
                            f"must be non-negative (got {value})"
                        )
        return errors

    @classmethod
    def _validate_title_patterns(cls, config: ClassificationConfig) -> List[str]:
        """Validate title patterns."""
        errors = []
        valid_strengths = {"strong", "potential", "adjacent", "ambiguous"}
        valid_specificities = {"high", "medium", "low"}
        
        for idx, pattern in enumerate(config.tech_title_patterns):
            # Validate strength
            if pattern.strength not in valid_strengths:
                errors.append(
                    f"Title pattern #{idx} has invalid strength '{pattern.strength}'. "
                    f"Must be one of: {valid_strengths}"
                )
            
            # Validate specificity
            if pattern.specificity not in valid_specificities:
                errors.append(
                    f"Title pattern #{idx} has invalid specificity '{pattern.specificity}'. "
                    f"Must be one of: {valid_specificities}"
                )
            
            # Validate weight
            if not cls._is_numeric(pattern.weight) or pattern.weight <= 0:
                errors.append(
                    f"Title pattern #{idx} has invalid weight '{pattern.weight}'. "
                    f"Must be positive numeric value"
                )
            
            # Validate categories exist
            for cat_id in pattern.categories:
                if cat_id not in config.categories:
                    errors.append(
                        f"Title pattern #{idx} references unknown category '{cat_id}'"
                    )
        
        return errors

    @classmethod
    def get_config(cls) -> ClassificationConfig:
        """Get the loaded configuration."""
        if cls._config is None:
            return cls.load()
        return cls._config

    @classmethod
    def get_category(cls, category_id: str) -> Optional[CategoryConfig]:
        """Get configuration for a specific category."""
        config = cls.get_config()
        return config.categories.get(category_id)

    @classmethod
    def get_tech_categories(cls) -> List[str]:
        """Get all tech category IDs."""
        config = cls.get_config()
        return [cat_id for cat_id, cat in config.categories.items() if cat.is_tech]

    @classmethod
    def get_non_tech_categories(cls) -> List[str]:
        """Get all non-tech category IDs."""
        config = cls.get_config()
        return [cat_id for cat_id, cat in config.categories.items() if not cat.is_tech]

    @classmethod
    def normalize_keyword(cls, keyword: str) -> str:
        """Normalize a keyword using aliases only."""
        config = cls.get_config()
        keyword = keyword.strip().lower()
        return config.aliases.get(keyword, keyword)

    @classmethod
    def is_stopword(cls, word: str) -> bool:
        """Check if a word is a stopword."""
        config = cls.get_config()
        return word.strip().lower() in config.stopwords

    @classmethod
    def get_compiled_regex(cls, category_id: str) -> List[re.Pattern]:
        """Get compiled regex patterns for a category."""
        config = cls.get_config()
        category = config.categories.get(category_id)
        if not category or not category.regex:
            return []

        cache_key = category_id
        if cache_key in cls._compiled_regex:
            return cls._compiled_regex[cache_key]

        patterns = []
        for pattern_str in category.regex:
            try:
                patterns.append(re.compile(pattern_str, re.IGNORECASE))
            except re.error:
                # Should have been caught during validation, but just in case
                continue
        cls._compiled_regex[cache_key] = patterns
        return patterns

    @classmethod
    def get_compiled_title_patterns(cls) -> Dict[str, List[re.Pattern]]:
        """Get compiled title patterns grouped by strength."""
        config = cls.get_config()
        patterns_by_strength: Dict[str, List[re.Pattern]] = {
            "strong": [],
            "potential": [],
            "adjacent": [],
            "ambiguous": [],
        }
        
        for pattern_config in config.tech_title_patterns:
            try:
                compiled = re.compile(pattern_config.pattern, re.IGNORECASE)
                patterns_by_strength[pattern_config.strength].append(compiled)
            except re.error:
                # Should have been caught during validation
                continue
        
        return patterns_by_strength

    @classmethod
    def get_effective_thresholds(cls, category_id: str) -> Dict[str, float]:
        """Get effective thresholds for a category (global + category-specific)."""
        config = cls.get_config()

        # Start with global thresholds
        thresholds = {
            "tech_minimum": config.thresholds.get("tech_minimum", 30),
            "high_confidence": config.thresholds.get("high_confidence", 70),
            "medium_confidence": config.thresholds.get("medium_confidence", 50),
            "low_confidence": config.thresholds.get("low_confidence", 30),
            "min_confidence_to_classify": config.thresholds.get("min_confidence_to_classify", 0.3),
        }

        # Apply category-specific overrides from category_thresholds (single source of truth)
        if category_id in config.category_thresholds:
            thresholds.update(config.category_thresholds[category_id])

        return thresholds

    @classmethod
    def get_effective_thresholds_with_defaults(
        cls,
        category_id: str,
        defaults: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Get effective thresholds with custom defaults.

        This is useful for validation and testing where you want to
        override the default thresholds.

        Args:
            category_id: Category identifier
            defaults: Custom default thresholds

        Returns:
            Dictionary of effective thresholds
        """
        if defaults is None:
            defaults = {
                "tech_minimum": 8.0,
                "minimum_margin": 3.0,
                "min_confidence": 0.15,
            }

        thresholds = defaults.copy()
        config = cls.get_config()

        # Apply global thresholds from config
        thresholds["tech_minimum"] = config.thresholds.get("tech_minimum", thresholds["tech_minimum"])
        thresholds["high_confidence"] = config.thresholds.get("high_confidence", 70.0)
        thresholds["medium_confidence"] = config.thresholds.get("medium_confidence", 50.0)
        thresholds["low_confidence"] = config.thresholds.get("low_confidence", 30.0)
        thresholds["min_confidence_to_classify"] = config.thresholds.get(
            "min_confidence_to_classify", thresholds.get("min_confidence", 0.15)
        )

        # Apply category-specific overrides
        if category_id in config.category_thresholds:
            thresholds.update(config.category_thresholds[category_id])

        return thresholds

    @classmethod
    def get_classification_settings(cls) -> Dict[str, Any]:
        """Get classification policy settings from configuration."""
        config = cls.get_config()
        return dict(config.classification) if config.classification else {}

    @classmethod
    def get_tech_title_patterns(cls) -> List[TitlePatternConfig]:
        """Get tech title patterns from configuration."""
        config = cls.get_config()
        return config.tech_title_patterns

    @classmethod
    def get_category_families(cls) -> Dict[str, List[str]]:
        """Get categories grouped by family."""
        config = cls.get_config()
        families = defaultdict(list)
        for cat_id, cat in config.categories.items():
            families[cat.family].append(cat_id)
        return dict(families)

    @classmethod
    def get_category_by_id_or_display_name(cls, name: str) -> Optional[CategoryConfig]:
        """Get category by either ID or display name (O(1) lookup)."""
        config = cls.get_config()

        # Try by ID first
        if name in config.categories:
            return config.categories[name]

        # Try by display name (O(1) precomputed lookup)
        name_lower = name.lower()
        cat_id = config._display_name_lookup.get(name_lower)
        if cat_id:
            return config.categories.get(cat_id)

        return None

    @classmethod
    def get_category_by_display_name(cls, display_name: str) -> Optional[CategoryConfig]:
        """Get category by display name (O(1) lookup)."""
        config = cls.get_config()
        name_lower = display_name.lower()
        cat_id = config._display_name_lookup.get(name_lower)
        if cat_id:
            return config.categories.get(cat_id)
        return None

    # ============================================================
    # Taxonomy Methods
    # ============================================================

    @classmethod
    def competes(cls, first: str, second: str) -> bool:
        """
        Determine if two categories should compete.

        Rules:
        - A category does NOT compete with its parent
        - A category does NOT compete with its children
        - Sibling categories DO compete
        - Categories with no parent compete with each other

        Args:
            first: First category ID
            second: Second category ID

        Returns:
            bool: True if categories should compete, False otherwise
        """
        if first == second:
            return False

        config = cls.get_config()
        
        # Check if second is the parent of first
        if config._parents.get(first) == second:
            return False

        # Check if first is the parent of second
        if config._parents.get(second) == first:
            return False

        return True

    @classmethod
    def get_competing_categories(
        cls,
        primary_category: str,
        sorted_categories: List[Any],
    ) -> List[Any]:
        """
        Get categories that should legitimately compete with the primary.

        Args:
            primary_category: The primary category ID
            sorted_categories: List of (category_id, score) tuples, sorted descending

        Returns:
            List of (category_id, score) tuples that should compete
        """
        config = cls.get_config()
        
        if primary_category not in config.categories:
            return sorted_categories[1:]

        return [
            item for item in sorted_categories[1:]
            if cls.competes(primary_category, item[0])
        ]

    @classmethod
    def is_parent(cls, category_id: str) -> bool:
        """Check if a category is a parent category."""
        config = cls.get_config()
        return config._roles.get(category_id) == CategoryRole.PARENT

    @classmethod
    def is_specialization(cls, category_id: str) -> bool:
        """Check if a category is a specialization."""
        config = cls.get_config()
        return config._roles.get(category_id) == CategoryRole.SPECIALIZATION

    @classmethod
    def get_children(cls, category_id: str) -> List[str]:
        """Get all children of a category."""
        config = cls.get_config()
        return list(config._children.get(category_id, set()))

    @classmethod
    def get_parent(cls, category_id: str) -> Optional[str]:
        """Get the parent of a category."""
        config = cls.get_config()
        return config._parents.get(category_id)

    @classmethod
    def get_role(cls, category_id: str) -> Optional[CategoryRole]:
        """Get the role of a category."""
        config = cls.get_config()
        return config._roles.get(category_id)

    @classmethod
    def get_all_parents(cls) -> List[str]:
        """Get all parent category IDs."""
        config = cls.get_config()
        return [
            cat_id for cat_id, role in config._roles.items()
            if role == CategoryRole.PARENT
        ]

    @classmethod
    def get_all_specializations(cls) -> List[str]:
        """Get all specialization category IDs."""
        config = cls.get_config()
        return [
            cat_id for cat_id, role in config._roles.items()
            if role == CategoryRole.SPECIALIZATION
        ]


# ============================================================
# Convenience Functions
# ============================================================

@lru_cache(maxsize=1)
def get_config() -> ClassificationConfig:
    """Get cached configuration."""
    return ClassificationConfigLoader.load()


@lru_cache(maxsize=128)
def get_category_config(category_id: str) -> Optional[CategoryConfig]:
    """Get configuration for a specific category (cached)."""
    return ClassificationConfigLoader.get_category(category_id)


def normalize_keyword(keyword: str) -> str:
    """Normalize a keyword using aliases."""
    return ClassificationConfigLoader.normalize_keyword(keyword)


def is_stopword(word: str) -> bool:
    """Check if a word is a stopword."""
    return ClassificationConfigLoader.is_stopword(word)


def reload_config() -> ClassificationConfig:
    """Reload configuration."""
    return ClassificationConfigLoader.reload()


def get_classification_settings() -> Dict[str, Any]:
    """Get classification policy settings from configuration."""
    return ClassificationConfigLoader.get_classification_settings()


def get_tech_title_patterns() -> List[TitlePatternConfig]:
    """Get tech title patterns from configuration."""
    return ClassificationConfigLoader.get_tech_title_patterns()


def get_compiled_title_patterns() -> Dict[str, List[re.Pattern]]:
    """Get compiled title patterns grouped by strength."""
    return ClassificationConfigLoader.get_compiled_title_patterns()


def get_effective_thresholds(
    category_id: str,
    defaults: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Get effective thresholds with custom defaults."""
    return ClassificationConfigLoader.get_effective_thresholds_with_defaults(
        category_id, defaults
    )


# ============================================================
# Taxonomy Convenience Functions
# ============================================================

def competes(first: str, second: str) -> bool:
    """Determine if two categories should compete."""
    return ClassificationConfigLoader.competes(first, second)


def get_competing_categories(
    primary_category: str,
    sorted_categories: List[Any],
) -> List[Any]:
    """Get categories that should compete with the primary."""
    return ClassificationConfigLoader.get_competing_categories(
        primary_category, sorted_categories
    )


def is_parent(category_id: str) -> bool:
    """Check if a category is a parent category."""
    return ClassificationConfigLoader.is_parent(category_id)


def is_specialization(category_id: str) -> bool:
    """Check if a category is a specialization."""
    return ClassificationConfigLoader.is_specialization(category_id)


def get_children(category_id: str) -> List[str]:
    """Get all children of a category."""
    return ClassificationConfigLoader.get_children(category_id)


def get_parent(category_id: str) -> Optional[str]:
    """Get the parent of a category."""
    return ClassificationConfigLoader.get_parent(category_id)


def get_role(category_id: str) -> Optional[CategoryRole]:
    """Get the role of a category."""
    return ClassificationConfigLoader.get_role(category_id)


def get_all_parents() -> List[str]:
    """Get all parent category IDs."""
    return ClassificationConfigLoader.get_all_parents()


def get_all_specializations() -> List[str]:
    """Get all specialization category IDs."""
    return ClassificationConfigLoader.get_all_specializations()


# ============================================================
# Export
# ============================================================

__all__ = [
    "ConfigurationError",
    "ClassificationConfig",
    "CategoryConfig",
    "TitlePatternConfig",
    "CategoryRole",
    "ClassificationConfigLoader",
    "get_config",
    "get_category_config",
    "normalize_keyword",
    "is_stopword",
    "reload_config",
    "get_classification_settings",
    "get_tech_title_patterns",
    "get_compiled_title_patterns",
    "get_effective_thresholds",
    # Taxonomy functions
    "competes",
    "get_competing_categories",
    "is_parent",
    "is_specialization",
    "get_children",
    "get_parent",
    "get_role",
    "get_all_parents",
    "get_all_specializations",
]