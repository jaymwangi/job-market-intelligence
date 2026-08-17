"""
Technology role scorer for job postings.

This module provides scoring and classification of job postings
to determine if they are technology roles and which technology
category they belong to.

The scorer uses:
- Weighted evidence from title, description, and skills
- Dynamic weight redistribution when fields are missing
- Configurable category keywords and weights
- Phrase matching for multi-word keywords
- Title pattern matching (regex)
- Negative keywords with configurable penalties
- Confidence normalized against category thresholds
- Rich explanation for debugging
- Top N categories for hybrid roles
- Evidence tracking with source attribution

Performance optimizations:
- Inverted index (keyword → categories) for single-pass text scanning
- LRU cache for skill normalization
- Thread-safe with read/write lock
- Regex patterns compiled once at initialization

Example:
    scorer = TechnologyScorer()
    result = scorer.score(
        title="Senior Backend Engineer",
        description="Build APIs with Python and Django",
        skills=["Python", "Django", "PostgreSQL"]
    )
    # result.category_scores = {"backend": 85.0, ...}
    # result.confidence = 0.92
    
    decision = scorer.classify(
        title="Senior Backend Engineer",
        description="Build APIs with Python and Django",
        skills=["Python", "Django", "PostgreSQL"]
    )
    # decision.is_tech = True
    # decision.primary_category = TechnologyCategory.BACKEND
    # decision.confidence = 0.92
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from threading import Lock
from typing import Dict, List, Optional, Tuple, Set, NamedTuple

from app.etl.enrichment.classification_config import (
    ClassificationConfigLoader,
    TitlePatternConfig,
    get_config,
    normalize_keyword,
)
from app.etl.enrichment.data.technology_categories import (
    TechnologyCategory,
    get_category_display_name,
)
from app.etl.enrichment.classifier import ClassificationDecision, classify_result, DecisionReason
from app.etl.enrichment.policy import ClassificationPolicy
from app.etl.enrichment.title_pattern import TitlePattern

logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================

# Maximum contribution per keyword (prevents keyword stuffing)
MAX_KEYWORD_CONTRIBUTION = 15.0

# Maximum evidence items to return
MAX_EVIDENCE_RETURNED = 50

# Maximum explanations to return
MAX_EXPLANATIONS_RETURNED = 20

# Default diminishing returns multipliers (configurable)
DEFAULT_DIMINISHING_RETURNS = [1.0, 0.5, 0.333, 0.0]

# Default title pattern boost
DEFAULT_TITLE_BOOST = 15.0

# Max size of skill normalization cache
MAX_SKILL_CACHE_SIZE = 10000

# Characters that need special handling in regex
SPECIAL_CHARS = set('+*?^$.[]{}()|/\\')


class MatchSource(Enum):
    """Source of a match during classification."""
    TITLE = "title"
    DESCRIPTION = "description"
    SKILLS = "skills"
    TITLE_PATTERN = "title_pattern"
    NEGATIVE_PENALTY = "negative_penalty"


@dataclass
class Evidence:
    """
    A piece of evidence for classification.
    
    Attributes:
        keyword: The keyword or phrase that matched
        category: The category this evidence supports
        source: Where the match was found (title, description, skills, or pattern)
        base_weight: The raw weight from configuration
        applied_weight: The weight after source weighting
        occurrence: Which occurrence this is (1st, 2nd, etc.)
        contribution: The final contribution to the score
    """
    keyword: str
    category: str
    source: MatchSource
    base_weight: float
    applied_weight: float
    occurrence: int
    contribution: float


@dataclass
class TechScoreResult:
    """
    Result of technology scoring for a job posting (RAW SCORES ONLY).
    
    This contains only raw scores and evidence. It does NOT make
    a technology classification decision.
    
    For production classification, use TechnologyScorer.classify()
    which returns a ClassificationDecision.
    
    Attributes:
        primary_category: Best matching technology category (as enum)
        primary_category_str: String version for serialization
        confidence: Confidence score (0.0 - 1.0) - raw confidence from scoring
        raw_score: Raw score before normalization
        normalized_score: Score normalized against threshold
        threshold_used: The high_confidence threshold used
        category_scores: All category scores
        raw_category_scores: Raw scores before adjustments
        top_categories: Top N categories with scores (for hybrid roles)
        matched_keywords: Keywords that matched with their scores
        matched_phrases: Phrases that matched
        matched_negative_keywords: Negative keywords that matched with penalties
        title_pattern_matched: Whether a title pattern matched
        explanations: Human-readable explanations for the score
        family: The family of the primary category
        evidence: All evidence collected during scoring
        theoretical_max_score: The maximum achievable score
    """
    primary_category: TechnologyCategory = TechnologyCategory.OTHER
    primary_category_str: str = "other"
    confidence: float = 0.0
    raw_score: float = 0.0
    normalized_score: float = 0.0
    threshold_used: float = 70.0
    category_scores: Dict[str, float] = field(default_factory=dict)
    raw_category_scores: Dict[str, float] = field(default_factory=dict)
    top_categories: List[Tuple[TechnologyCategory, float]] = field(default_factory=list)
    matched_keywords: Dict[str, float] = field(default_factory=dict)
    matched_phrases: List[str] = field(default_factory=list)
    matched_negative_keywords: Dict[str, float] = field(default_factory=dict)
    title_pattern_matched: bool = False
    explanations: List[str] = field(default_factory=list)
    family: str = "other"
    evidence: List[Evidence] = field(default_factory=list)
    theoretical_max_score: float = 0.0


class MatchResult(NamedTuple):
    """Result of a keyword match in text."""
    keyword: str
    match_count: int  # Number of times the keyword matched
    positions: List[int]  # Positions where matches were found


class TechnologyScorer:
    """
    Scores job postings for technology classification.
    
    Uses configuration from tech_classification.yaml to determine
    category scores, weights, and thresholds.
    
    The scoring process:
    1. Normalize title, description, and skills
    2. Dynamically redistribute weights if fields are missing
    3. Collect evidence from all sources using word boundaries
    4. Score each category based on evidence (with diminishing returns)
    5. Apply title pattern boosts (only to relevant categories)
    6. Apply negative keyword penalties (before selecting winner)
    7. Determine primary category and confidence
    8. Return top N categories for hybrid roles
    
    Important: score() returns raw scores only. For production
    classification decisions, use classify() which applies policy.
    """

    def __init__(self):
        """Initialize the technology scorer with configuration."""
        self.config = get_config()
        self._compile_title_patterns()
        self._build_keyword_patterns()
        self._lock = Lock()
        
        # Load diminishing returns from config or use defaults
        self.diminishing_returns = getattr(
            self.config, 'diminishing_returns', DEFAULT_DIMINISHING_RETURNS
        )
        
        # Compute theoretical maximum score for normalization
        self._compute_theoretical_max_score()

    # ============================================================
    # Pattern Building
    # ============================================================

    def _sanitize_keyword_for_regex(self, keyword: str) -> str:
        """
        Sanitize a keyword for use in a regex pattern.
        
        Handles special cases like C++, C#, .NET, Node.js, etc.
        """
        # For keywords with special characters, use more lenient matching
        if any(c in SPECIAL_CHARS for c in keyword):
            # Escape the keyword but don't enforce word boundaries
            return re.escape(keyword)
        
        # For normal alphanumeric keywords, use word boundaries
        if re.match(r'^[a-zA-Z0-9\s]+$', keyword):
            if " " in keyword:
                # Phrase: boundaries at start and end
                return r'\b' + re.escape(keyword) + r'\b'
            else:
                # Single word: boundaries around it
                return r'\b' + re.escape(keyword) + r'\b'
        
        # Fallback: escape and use loose matching
        return re.escape(keyword)

    def _build_keyword_patterns(self) -> None:
        """
        Build regex patterns for all keywords with appropriate boundaries.
        
        Also builds an inverted index (keyword → categories) for
        efficient single-pass text scanning.
        """
        self._keyword_patterns: Dict[str, re.Pattern] = {}
        self._keyword_to_categories: Dict[str, Set[str]] = {}
        self._keyword_weights: Dict[str, Dict[str, float]] = {}
        self._all_keywords: Set[str] = set()
        
        for cat_id, category in self.config.categories.items():
            for keyword, weight in category.keywords.items():
                self._all_keywords.add(keyword)
                
                # Track which categories this keyword belongs to
                if keyword not in self._keyword_to_categories:
                    self._keyword_to_categories[keyword] = set()
                self._keyword_to_categories[keyword].add(cat_id)
                
                # Track weights per category
                if keyword not in self._keyword_weights:
                    self._keyword_weights[keyword] = {}
                self._keyword_weights[keyword][cat_id] = weight
                
                # Compile regex pattern once per keyword
                if keyword not in self._keyword_patterns:
                    pattern_str = self._sanitize_keyword_for_regex(keyword)
                    try:
                        self._keyword_patterns[keyword] = re.compile(
                            pattern_str, re.IGNORECASE
                        )
                    except re.error as e:
                        logger.warning(
                            "Invalid keyword pattern '%s' for category '%s': %s",
                            keyword, cat_id, e
                        )
                        # Fallback: simple escaped match
                        self._keyword_patterns[keyword] = re.compile(
                            re.escape(keyword), re.IGNORECASE
                        )

    def _compile_title_patterns(self) -> None:
        """Compile title patterns from configuration."""

        self._title_patterns: List[TitlePattern] = []

        patterns = getattr(self.config, "tech_title_patterns", [])

        if not patterns:
            logger.debug("No title patterns found in configuration")
            return

        for pattern_config in patterns:

            # Already a runtime TitlePattern
            if isinstance(pattern_config, TitlePattern):
                self._title_patterns.append(pattern_config)
                continue

            # Configuration-layer TitlePatternConfig
            if isinstance(pattern_config, TitlePatternConfig):
                try:
                    title_pattern = TitlePattern(
                        pattern=pattern_config.pattern,
                        categories=tuple(pattern_config.categories),
                        weight=float(pattern_config.weight),
                        strength=pattern_config.strength,
                        specificity=pattern_config.specificity,
                    )

                    self._title_patterns.append(title_pattern)

                    logger.debug(
                        "Compiled title pattern: %s "
                        "(weight=%.1f, strength=%s, specificity=%s, categories=%s)",
                        pattern_config.pattern,
                        pattern_config.weight,
                        pattern_config.strength,
                        pattern_config.specificity,
                        pattern_config.categories,
                    )

                except (re.error, ValueError, TypeError) as exc:
                    logger.warning(
                        "Invalid title pattern '%s': %s",
                        pattern_config.pattern,
                        exc,
                    )

                continue

            # Defensive support for dictionaries
            if isinstance(pattern_config, dict):
                try:
                    title_pattern = TitlePattern(
                        pattern=pattern_config["pattern"],
                        categories=tuple(
                            pattern_config.get("categories", [])
                        ),
                        weight=float(
                            pattern_config.get("weight", 8.0)
                        ),
                        strength=pattern_config.get(
                            "strength", "potential"
                        ),
                        specificity=pattern_config.get(
                            "specificity", "medium"
                        ),
                    )

                    self._title_patterns.append(title_pattern)

                except (KeyError, re.error, ValueError, TypeError) as exc:
                    logger.warning(
                        "Invalid title pattern config: %s",
                        exc,
                    )

                continue

            logger.warning(
                "Unknown pattern config type: %s",
                type(pattern_config),
            )

        logger.info(
            "Loaded %d title patterns",
            len(self._title_patterns),
        )

    def _get_title_strength(self, title: str) -> Tuple[str, Optional[TitlePattern], float]:
        """
        Get the strength of the strongest matching title pattern.
        
        Returns:
            Tuple of (strength, best_pattern, max_weight)
        """
        if not title or not self._title_patterns:
            return 'ambiguous', None, 0.0
        
        best_pattern = None
        max_weight = 0.0
        max_strength = 'ambiguous'
        
        # Priority order for strength
        strength_priority = {
            'strong': 4,
            'potential': 3,
            'adjacent': 2,
            'ambiguous': 1,
        }
        
        for pattern in self._title_patterns:
            if pattern.matches(title):
                # Get priority for this pattern
                current_priority = strength_priority.get(pattern.strength, 0)
                max_priority = strength_priority.get(max_strength, 0)
                
                # If this pattern is stronger, or same strength but higher weight
                if (current_priority > max_priority or 
                    (current_priority == max_priority and pattern.weight > max_weight)):
                    max_strength = pattern.strength
                    max_weight = pattern.weight
                    best_pattern = pattern
        
        return max_strength, best_pattern, max_weight
                
    def _compute_theoretical_max_score(self) -> None:
        """
        Compute the theoretical maximum achievable score for normalization.
        
        This correctly models how diminishing returns works and computes
        a realistic maximum based on the configuration.
        """
        max_possible = 0.0
        
        for cat_id, category in self.config.categories.items():
            category_max = 0.0
            
            # Sort keywords by weight (highest first) for optimal returns
            sorted_keywords = sorted(
                category.keywords.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Maximum contribution from keywords
            # Each keyword contributes its weight with diminishing returns
            # The theoretical max is the sum of all keyword contributions
            for keyword, base_weight in sorted_keywords:
                # Max weight after source weighting (using title source)
                max_weight = base_weight * 0.40  # title weight
                
                # First occurrence contributes fully
                factor = self.diminishing_returns[0] if self.diminishing_returns else 1.0
                contribution = min(max_weight * factor, MAX_KEYWORD_CONTRIBUTION)
                category_max += contribution
            
            max_possible = max(max_possible, category_max)
        
        # Add realistic title pattern boost (not all categories, just max possible)
        if self._title_patterns:
            boost_value = getattr(self.config, 'title_pattern_boost', DEFAULT_TITLE_BOOST) or DEFAULT_TITLE_BOOST
            # A single title pattern can boost at most the categories it targets
            # In the worst case, it could target all tech categories
            max_boost = boost_value * len(self.config.categories)
            max_possible += max_boost
        
        self._theoretical_max_score = max(100.0, max_possible)
        logger.debug("Theoretical max score: %.2f", self._theoretical_max_score)

    # ============================================================
    # Unified Matching Helpers (Single-Pass Scanning)
    # ============================================================

    def _scan_text_for_keywords(self, text: str) -> Dict[str, MatchResult]:
        """
        Scan text once and find all keyword matches.
        
        This is the core performance optimization - single-pass scanning
        instead of scanning for each keyword individually.
        
        Returns dict of keyword → MatchResult.
        """
        if not text:
            return {}
        
        matches: Dict[str, MatchResult] = {}
        text_lower = text.lower()
        
        # Scan each keyword once
        for keyword in self._all_keywords:
            pattern = self._keyword_patterns.get(keyword)
            if pattern:
                # Find all matches in one pass
                found = pattern.findall(text_lower)
                if found:
                    # Count occurrences and track positions (approximate)
                    match_count = len(found)
                    # For positions, we use the first few match positions
                    # (exact positions are expensive to compute, so we approximate)
                    positions = [i for i in range(min(match_count, 10))]
                    matches[keyword] = MatchResult(
                        keyword=keyword,
                        match_count=match_count,
                        positions=positions
                    )
            else:
                # Fallback: simple count
                match_count = text_lower.count(keyword.lower())
                if match_count > 0:
                    matches[keyword] = MatchResult(
                        keyword=keyword,
                        match_count=match_count,
                        positions=list(range(min(match_count, 10)))
                    )
        
        return matches

    def _collect_evidence_from_matches(
        self,
        matches: Dict[str, MatchResult],
        category_id: str,
        weights: Dict[str, float],
        source: MatchSource,
    ) -> List[Evidence]:
        """
        Collect evidence from pre-scanned matches for a category.
        
        This avoids re-scanning text by using the pre-computed matches.
        """
        evidence: List[Evidence] = []
        category = self.config.categories.get(category_id)
        if not category:
            return evidence

        keywords = category.keywords
        
        # Track occurrences for diminishing returns
        occurrence_count: Dict[str, int] = {}

        for keyword, base_weight in keywords.items():
            match = matches.get(keyword)
            if not match:
                continue
            
            occurrences = match.match_count
            source_weight = weights.get(source.value, 0.35)  # Default to description
            
            # Special handling for skills source
            if source == MatchSource.SKILLS:
                source_weight = weights.get("skills", 0.25) * 1.5
            elif source == MatchSource.TITLE:
                source_weight = weights.get("title", 0.40)
            elif source == MatchSource.DESCRIPTION:
                source_weight = weights.get("description", 0.35)
            
            for _ in range(occurrences):
                occurrence_count[keyword] = occurrence_count.get(keyword, 0) + 1
                applied_weight = base_weight * source_weight
                evidence.append(Evidence(
                    keyword=keyword,
                    category=category_id,
                    source=source,
                    base_weight=float(base_weight),
                    applied_weight=float(applied_weight),
                    occurrence=occurrence_count[keyword],
                    contribution=0.0,
                ))

        return evidence

    # ============================================================
    # Field Availability & Weight Redistribution
    # ============================================================

    def _get_available_fields(
        self,
        title: str,
        description: str,
        skills: Optional[List[str]],
    ) -> Dict[str, bool]:
        """Determine which fields are available for scoring."""
        return {
            "title": bool(title and title.strip()),
            "description": bool(description and description.strip()),
            "skills": bool(skills and len(skills) > 0),
        }

    def _redistribute_weights(
        self,
        available: Dict[str, bool],
    ) -> Dict[str, float]:
        """
        Redistribute weights when fields are missing.
        
        If description is missing, its weight is redistributed
        proportionally to title and skills.
        """
        weights = self.config.weights
        
        # If all fields available, return original weights
        if all(available.values()):
            return {
                "title": weights.get("title", 0.40),
                "description": weights.get("description", 0.35),
                "skills": weights.get("skills", 0.25),
            }
        
        # Start with available weights
        result = {}
        total_available = 0.0
        
        for field, available_flag in available.items():
            if available_flag:
                weight = weights.get(field, 0.0)
                result[field] = weight
                total_available += weight
        
        # Redistribute if some fields missing
        if total_available > 0 and total_available < 1.0:
            scale = 1.0 / total_available
            for field in result:
                result[field] *= scale
        
        # Ensure missing fields get 0
        for field in ["title", "description", "skills"]:
            if field not in result:
                result[field] = 0.0
        
        return result

    # ============================================================
    # Normalization (Thread-Safe with LRU Cache)
    # ============================================================

    @lru_cache(maxsize=MAX_SKILL_CACHE_SIZE)
    def _normalize_skill_cached(self, skill: str) -> str:
        """Cached version of skill normalization."""
        return normalize_keyword(skill)

    def _normalize_skill(self, skill: str) -> str:
        """Normalize a skill using LRU cache."""
        return self._normalize_skill_cached(skill)

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text: lowercase, remove extra whitespace.
        
        Also removes most punctuation to improve matching consistency.
        Preserves special characters that are meaningful (+, #, ., etc.)
        """
        if not text:
            return ""
        
        # Lowercase and strip
        normalized = text.lower().strip()
        
        # Replace common punctuation with spaces
        # Keep special chars that are meaningful in tech keywords
        # (+ # . - / are kept as they appear in C++, C#, .NET, Node.js, etc.)
        punctuation_to_space = '!@$%^&*()=[]{}|;:\'",<>?'
        for char in punctuation_to_space:
            normalized = normalized.replace(char, ' ')
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized

    # ============================================================
    # Evidence Collection (Using Single-Pass Scanning)
    # ============================================================

    def _collect_evidence_for_category(
        self,
        title_matches: Dict[str, MatchResult],
        description_matches: Dict[str, MatchResult],
        skills: List[str],
        category_id: str,
        weights: Dict[str, float],
    ) -> List[Evidence]:
        """
        Collect all evidence for a category using pre-scanned matches.
        
        This is much more efficient than scanning text for each category.
        """
        evidence: List[Evidence] = []
        category = self.config.categories.get(category_id)
        if not category:
            return evidence

        # Use title matches
        evidence.extend(
            self._collect_evidence_from_matches(
                title_matches, category_id, weights, MatchSource.TITLE
            )
        )
        
        # Use description matches
        evidence.extend(
            self._collect_evidence_from_matches(
                description_matches, category_id, weights, MatchSource.DESCRIPTION
            )
        )

        # Check skills - normalized through the same pipeline
        normalized_skills = [self._normalize_skill(skill) for skill in skills]
        skill_matches: Dict[str, MatchResult] = {}
        
        # For skills, we only consider exact matches
        for skill in normalized_skills:
            if skill in category.keywords:
                # Count occurrences (skills are usually unique, but handle duplicates)
                match_count = normalized_skills.count(skill)
                skill_matches[skill] = MatchResult(
                    keyword=skill,
                    match_count=match_count,
                    positions=list(range(min(match_count, 10)))
                )
        
        # Use skill matches
        evidence.extend(
            self._collect_evidence_from_matches(
                skill_matches, category_id, weights, MatchSource.SKILLS
            )
        )

        return evidence

    def _calculate_evidence_contributions(
        self,
        evidence: List[Evidence],
    ) -> List[Evidence]:
        """Calculate contributions for each evidence with diminishing returns."""
        if not evidence:
            return evidence

        # Group by keyword
        keyword_evidence: Dict[str, List[Evidence]] = {}
        for ev in evidence:
            keyword_evidence.setdefault(ev.keyword, []).append(ev)

        result = []
        for keyword, ev_list in keyword_evidence.items():
            # Sort by applied weight (highest first)
            ev_list.sort(key=lambda x: x.applied_weight, reverse=True)
            
            # Apply diminishing returns
            for i, ev in enumerate(ev_list):
                factor = self.diminishing_returns[i] if i < len(self.diminishing_returns) else 0
                if factor > 0:
                    contribution = ev.applied_weight * factor
                    # Cap individual contributions
                    contribution = min(contribution, MAX_KEYWORD_CONTRIBUTION)
                    ev.contribution = float(contribution)
                else:
                    ev.contribution = 0.0
                result.append(ev)

        return result

    # ============================================================
    # Category Selection
    # ============================================================

    def _check_title_patterns(self, title: str) -> Dict[str, float]:
        """
        Check if title matches any tech title patterns with role prior weights.
        
        Uses the strongest matching pattern to avoid double-counting.
        """
        if not title or not self._title_patterns:
            return {}
        
        # Find the strongest matching pattern
        best_weight = 0.0
        best_categories = []
        matched_patterns = []
        
        for title_pattern in self._title_patterns:
            if title_pattern.matches(title):
                matched_patterns.append(title_pattern)
                if title_pattern.weight > best_weight:
                    best_weight = title_pattern.weight
                    best_categories = title_pattern.categories
        
        if not best_categories:
            return {}
        
        # Apply the role prior to the matched categories
        boosts = {}
        for cat in best_categories:
            boosts[cat] = best_weight
        
        return boosts

    def _get_best_category(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """Get the best scoring category and its score."""
        if not scores:
            return "other", 0.0

        # Get category priority for tie-breaking
        priority = self.config.category_priority

        # Find max score
        max_score = max(scores.values())

        # Get all categories with max score
        candidates = [cat for cat, score in scores.items() if score == max_score]

        if len(candidates) == 1:
            return candidates[0], max_score

        # Tie-break by priority
        for cat in priority:
            if cat in candidates:
                return cat, max_score

        # Fallback: alphabetical
        return sorted(candidates)[0], max_score

    def _get_top_categories(
        self,
        scores: Dict[str, float],
        n: int = 5,
    ) -> List[Tuple[TechnologyCategory, float]]:
        """Get top N categories with scores as enum."""
        if not scores:
            return []

        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        result = []
        for cat_id, score in sorted_cats[:n]:
            try:
                cat_enum = TechnologyCategory(cat_id)
            except ValueError:
                cat_enum = TechnologyCategory.OTHER
            result.append((cat_enum, score))
        return result

    def _apply_negative_penalties(
        self,
        category_id: str,
        score: float,
        text: str,
        explanations: List[str],
        evidence: List[Evidence],
    ) -> Tuple[float, Dict[str, float]]:
        """
        Apply negative keyword penalties to a category score.
        
        Returns (adjusted_score, matched_negative_keywords)
        """
        category = self.config.categories.get(category_id)
        if not category:
            return score, {}

        # Get explicit negative keyword penalties
        negative_keywords = getattr(category, 'negative_keywords_penalties', {})
        if not negative_keywords:
            # Backward compatibility: fall back to old behavior
            negative_keywords = {
                neg: category.keywords.get(neg, 5.0)
                for neg in (category.negative_keywords or [])
            }
        
        if not negative_keywords:
            return score, {}

        matched = {}
        text_lower = text.lower()
        
        # Use unified matching with appropriate boundaries
        for neg, penalty in negative_keywords.items():
            if self._matches_keyword(text_lower, neg):
                matched[neg] = penalty
                # Add negative penalty as evidence
                evidence.append(Evidence(
                    keyword=f"neg_{neg}",
                    category=category_id,
                    source=MatchSource.NEGATIVE_PENALTY,
                    base_weight=penalty,
                    applied_weight=penalty,
                    occurrence=1,
                    contribution=-penalty
                ))
                explanations.append(f"Negative keyword '{neg}' penalty: -{penalty:.1f}")
        
        total_penalty = sum(matched.values())
        adjusted_score = max(0, score - total_penalty)
        
        return adjusted_score, matched

    def _calculate_confidence(
        self,
        raw_score: float,
        category_id: str,
        explanations: List[str],
    ) -> Tuple[float, float, float]:
        """
        Calculate confidence score using threshold-based normalization.
        
        Normalizes against the theoretical maximum score to preserve
        discrimination across different score ranges.
        
        Returns:
            Tuple[float, float, float]: (confidence, normalized_score, threshold_used)
        """
        if raw_score <= 0:
            return 0.0, 0.0, 70.0

        thresholds = self._get_effective_thresholds(category_id)
        high_confidence = thresholds.get("high_confidence", 70)

        # Normalize against theoretical max
        if self._theoretical_max_score > 0:
            normalized_score = min(1.0, raw_score / self._theoretical_max_score)
        else:
            normalized_score = min(1.0, raw_score / 100.0)
        
        # Confidence is the normalized score (consistent with normalization)
        confidence = normalized_score
        
        # Add explanation
        explanations.append(
            f"Raw score {raw_score:.1f}, theoretical max {self._theoretical_max_score:.1f}, "
            f"normalized confidence {confidence:.2f}"
        )
        
        return confidence, normalized_score, high_confidence

    def _matches_keyword(self, text: str, keyword: str) -> bool:
        """Check if a keyword matches in text using appropriate boundaries."""
        if not text or not keyword:
            return False
        
        pattern = self._keyword_patterns.get(keyword)
        if pattern:
            return bool(pattern.search(text))
        
        # Fallback: case-insensitive substring match
        return keyword.lower() in text.lower()

    def _get_effective_thresholds(self, category_id: str) -> Dict[str, float]:
        """Get effective thresholds for a category."""
        return ClassificationConfigLoader.get_effective_thresholds(category_id)

    def get_category_display_name(self, category_id: str) -> str:
        """Get display name for a category."""
        return get_category_display_name(category_id)

    # ============================================================
    # Public API
    # ============================================================

    def score(
        self,
        title: str,
        description: str = "",
        skills: Optional[List[str]] = None,
    ) -> TechScoreResult:
        """
        Score a job posting for technology classification (RAW SCORES ONLY).
        
        This method computes evidence and raw technology scores.
        It does NOT apply policy-based classification decisions.
        It does NOT determine if a job is a technology role.
        
        For production classification, use classify() instead.
        
        Args:
            title: Job title
            description: Job description (optional)
            skills: List of extracted skills (optional)
            
        Returns:
            TechScoreResult: Raw scoring result with evidence and explanations
                - category_scores: Raw scores for each category
                - confidence: Raw confidence from scoring
                - primary_category: Highest scoring category
                - NO is_tech_role field - that's a policy decision
        
        Example:
            scorer = TechnologyScorer()
            result = scorer.score(
                title="Senior Backend Engineer",
                description="Build APIs with Python",
                skills=["Python", "Django"]
            )
            
            # result.category_scores['backend'] = 85.0
            # result.confidence = 0.92
            # result.primary_category = TechnologyCategory.BACKEND
            # result does NOT have is_tech_role
        """
        if skills is None:
            skills = []

        explanations = []
        all_evidence: List[Evidence] = []
        
        # Check available fields
        available = self._get_available_fields(title, description, skills)
        weights = self._redistribute_weights(available)
        
        if not available["title"] and not available["description"] and not available["skills"]:
            return TechScoreResult(
                explanations=["No text available for scoring"],
            )

        # Normalize inputs
        title_norm = self._normalize_text(title)
        description_norm = self._normalize_text(description)

        # Single-pass scanning: scan title and description once
        title_matches = self._scan_text_for_keywords(title_norm)
        description_matches = self._scan_text_for_keywords(description_norm)

        # Collect evidence and score each category
        category_scores: Dict[str, float] = {}
        raw_category_scores: Dict[str, float] = {}

        for cat_id in self.config.categories:
            raw_evidence = self._collect_evidence_for_category(
                title_matches,
                description_matches,
                skills,
                cat_id,
                weights,
            )
            if raw_evidence:
                # Calculate contributions with diminishing returns
                evidence = self._calculate_evidence_contributions(raw_evidence)
                all_evidence.extend(evidence)
                
                # Calculate total score from contributions
                score = sum(ev.contribution for ev in evidence)
                if score > 0:
                    raw_category_scores[cat_id] = score
                    category_scores[cat_id] = score  # Will be adjusted later
                    explanations.append(
                        f"{cat_id}: {len(evidence)} evidence items, score {score:.1f}"
                    )

        # Check title patterns and apply targeted boosts
        title_pattern_boosts = self._check_title_patterns(title)
        if title_pattern_boosts:
            for cat_id, boost in title_pattern_boosts.items():
                # Initialize score if category doesn't exist yet
                if cat_id not in category_scores:
                    category_scores[cat_id] = 0.0
                    raw_category_scores[cat_id] = 0.0
                
                category_scores[cat_id] += boost
                explanations.append(
                    f"Title pattern boost for {cat_id}: +{boost:.1f}"
                )
                # Add evidence for the boost
                all_evidence.append(Evidence(
                    keyword="TITLE_PATTERN_BOOST",
                    category=cat_id,
                    source=MatchSource.TITLE_PATTERN,
                    base_weight=boost,
                    applied_weight=boost,
                    occurrence=1,
                    contribution=boost
                ))

        # Apply negative keyword penalties to ALL categories (before selecting winner)
        text_for_negatives = f"{title_norm} {description_norm}"
        all_negative_penalties: Dict[str, Dict[str, float]] = {}
        
        for cat_id in list(category_scores.keys()):
            adjusted_score, neg_matches = self._apply_negative_penalties(
                cat_id,
                category_scores[cat_id],
                text_for_negatives,
                explanations,
                all_evidence
            )
            category_scores[cat_id] = adjusted_score
            if neg_matches:
                all_negative_penalties[cat_id] = neg_matches

        # Get best category (now with penalties applied)
        best_category_id, raw_score = self._get_best_category(category_scores)
        
        # Convert to enum
        try:
            primary_category = TechnologyCategory(best_category_id)
        except ValueError:
            primary_category = TechnologyCategory.OTHER

        # Get top N categories
        top_categories = self._get_top_categories(category_scores, n=5)

        # Get matched keywords with scores (for the best category)
        matched_keywords = self._get_matched_keywords_with_scores(
            best_category_id,
            title_norm + " " + description_norm,
            skills,
        )

        # Get matched phrases (for the best category)
        matched_phrases = self._get_matched_phrases(
            best_category_id,
            title_norm + " " + description_norm,
        )

        # Calculate confidence using threshold-based normalization
        confidence, normalized_score, threshold_used = self._calculate_confidence(
            raw_score, best_category_id, explanations
        )

        # Get family
        category = self.config.categories.get(best_category_id)
        family = category.family if category else "other"

        # Get negative keywords for the best category
        best_negative_keywords = all_negative_penalties.get(best_category_id, {})

        return TechScoreResult(
            primary_category=primary_category,
            primary_category_str=best_category_id,
            confidence=confidence,
            raw_score=raw_score,
            normalized_score=normalized_score,
            threshold_used=threshold_used,
            category_scores=category_scores,
            raw_category_scores=raw_category_scores,
            top_categories=top_categories,
            matched_keywords=matched_keywords,
            matched_phrases=matched_phrases[:10],
            matched_negative_keywords=best_negative_keywords,
            title_pattern_matched=bool(title_pattern_boosts),
            explanations=explanations[:MAX_EXPLANATIONS_RETURNED],
            family=family,
            evidence=all_evidence[:MAX_EVIDENCE_RETURNED],
            theoretical_max_score=self._theoretical_max_score,
        )

    def _get_matched_keywords_with_scores(
        self,
        category_id: str,
        text: str,
        skills: List[str],
    ) -> Dict[str, float]:
        """Get keywords that matched with their scores using unified matching."""
        category = self.config.categories.get(category_id)
        if not category:
            return {}

        matched: Dict[str, float] = {}
        text_lower = text.lower()

        # Check text matches with appropriate boundaries
        for keyword, weight in category.keywords.items():
            if self._matches_keyword(text_lower, keyword):
                matched[keyword] = min(weight, MAX_KEYWORD_CONTRIBUTION)

        # Check skills matches using normalized skills
        normalized_skills = [self._normalize_skill(skill) for skill in skills]
        for skill in normalized_skills:
            if skill in category.keywords:
                score = min(category.keywords[skill] * 1.5, MAX_KEYWORD_CONTRIBUTION)
                if skill in matched:
                    matched[skill] = min(matched[skill] + score, MAX_KEYWORD_CONTRIBUTION)
                else:
                    matched[skill] = score

        return matched

    def _get_matched_phrases(self, category_id: str, text: str) -> List[str]:
        """Get matched multi-word phrases for a category using unified matching."""
        category = self.config.categories.get(category_id)
        if not category:
            return []

        matched = []
        text_lower = text.lower()

        for keyword in category.keywords:
            if " " in keyword and self._matches_keyword(text_lower, keyword):
                matched.append(keyword)

        return matched
    
    def classify(
        self,
        title: str,
        description: str = "",
        skills: Optional[List[str]] = None,
        policy: Optional[ClassificationPolicy] = None,
    ) -> ClassificationDecision:
        """
        Classify a job using evidence-aware decision logic.
        
        Strength levels:
        - strong: Title alone is sufficient for is_tech=True
        - potential: Title suggests tech, but needs supporting evidence from description/skills
        - adjacent: Title suggests tech-adjacent role, needs supporting evidence
        - ambiguous: Title alone is insufficient, needs strong supporting evidence
        """
        # First, score the job (computes raw scores)
        result = self.score(title, description, skills)
        
        # Use provided policy or load default
        if policy is None:
            policy = ClassificationPolicy.default()
        
        # Get base decision from policy
        base_decision = classify_result(result, policy)
        
        # Get title strength from pattern matching
        title_strength, best_pattern, max_weight = self._get_title_strength(title)
        
        # Get strength thresholds from config
        strength_thresholds = getattr(self.config, 'strength_thresholds', {
            'strong': {'requires_evidence': False},
            'potential': {'requires_evidence': True},
            'adjacent': {'requires_evidence': True},
            'ambiguous': {'requires_evidence': True},
        })
        
        threshold = strength_thresholds.get(title_strength, {})
        requires_evidence = threshold.get('requires_evidence', True)
        
        # Determine is_tech based on strength
        if title_strength == 'strong':
            # Strong title patterns classify from title alone - ALWAYS TECH
            is_tech = True
            primary_category = best_pattern.categories[0] if best_pattern and best_pattern.categories else 'general_software'
            reason = DecisionReason.SUCCESS
            explanations = [f"Strong title pattern matched: {best_pattern.pattern}"] if best_pattern else ["Strong title pattern matched"]
            
        else:
            # Need supporting evidence from description or skills (NOT title or title_pattern)
            supporting_evidence = []
            evidence_categories = set()
            
            for ev in result.evidence:
                # Exclude title and title_pattern evidence
                if ev.source.value in ['title', 'title_pattern']:
                    continue
                if ev.contribution > 0:
                    supporting_evidence.append(ev)
                    evidence_categories.add(ev.category)
            
            has_supporting_evidence = len(supporting_evidence) > 0
            
            # For adjacent titles, require meaningful evidence (at least 2 items)
            if title_strength == 'adjacent':
                has_supporting_evidence = len(supporting_evidence) >= 2
            
            if requires_evidence and not has_supporting_evidence:
                # No supporting evidence - not tech
                is_tech = False
                primary_category = 'non_tech'  # ENFORCE non_tech category
                reason = DecisionReason.SCORE_TOO_LOW
                explanations = [f"{title_strength} title '{title}' lacks sufficient supporting technical evidence"]
            else:
                # Use the base decision
                is_tech = base_decision.is_tech
                primary_category = base_decision.primary_category if is_tech else 'non_tech'
                reason = base_decision.reason
                explanations = base_decision.explanations
        
        # ENSURE: if not tech, category must be non_tech
        if not is_tech:
            primary_category = 'non_tech'
        
        return ClassificationDecision(
            is_tech=is_tech,
            primary_category=primary_category,
            primary_score=base_decision.primary_score,
            margin=base_decision.margin,
            score=base_decision.score,
            confidence=base_decision.confidence,
            reason=reason,
            second_best_category=base_decision.second_best_category,
            second_best_score=base_decision.second_best_score,
            ambiguity_score=base_decision.ambiguity_score,
            explanations=explanations,
            thresholds=base_decision.thresholds,
        )
# ============================================================
# Convenience Functions
# ============================================================

_scorer: Optional[TechnologyScorer] = None
_scorer_lock = Lock()


def get_scorer() -> TechnologyScorer:
    """Get a singleton instance of the technology scorer (thread-safe)."""
    global _scorer
    if _scorer is None:
        with _scorer_lock:
            if _scorer is None:
                _scorer = TechnologyScorer()
    return _scorer


def score_job(
    title: str,
    description: str = "",
    skills: Optional[List[str]] = None,
) -> TechScoreResult:
    """
    Convenience function to score a job.
    
    Returns raw scoring results without policy-based classification.
    Use classify_job() for production classification.
    
    Returns:
        TechScoreResult: Raw scores and evidence (no classification decision)
    """
    return get_scorer().score(title, description, skills)


def classify_job(
    title: str,
    description: str = "",
    skills: Optional[List[str]] = None,
    policy: Optional[ClassificationPolicy] = None,
) -> ClassificationDecision:
    """
    Convenience function to classify a job using the single source of truth.
    
    This is the recommended entry point for classification in production code.
    
    Args:
        title: Job title
        description: Job description (optional)
        skills: List of extracted skills (optional)
        policy: Classification policy (uses default if None)
    
    Returns:
        ClassificationDecision: Decision with all relevant information
    
    Example:
        from app.etl.enrichment.tech_scorer import classify_job
        
        decision = classify_job(
            title="Senior Backend Engineer",
            description="Build APIs with Python and Django",
            skills=["Python", "Django", "PostgreSQL"]
        )
        
        if decision.is_tech:
            print(f"Tech role: {decision.primary_category}")
    """
    return get_scorer().classify(title, description, skills, policy)


# ============================================================
# Export
# ============================================================

__all__ = [
    "MatchSource",
    "Evidence",
    "TechScoreResult",
    "TechnologyScorer",
    "get_scorer",
    "score_job",
    "classify_job",
]