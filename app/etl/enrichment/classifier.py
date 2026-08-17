"""
Single source of truth for classification logic.

This module provides the classify_result() function which is the single
source of truth for all classification decisions. Both production code
and validation frameworks use this same function to ensure consistency.

The classifier uses a ClassificationPolicy to determine thresholds and
returns a typed ClassificationDecision with all relevant information
including ambiguity scoring.

Example:
    from app.etl.enrichment.tech_scorer import get_scorer
    from app.etl.enrichment.policy import ClassificationPolicy
    
    scorer = get_scorer()
    result = scorer.score(title, description, skills)
    
    policy = ClassificationPolicy.default()
    decision = classify_result(result, policy)
    
    if decision.is_tech:
        print(f"Tech role: {decision.primary_category}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Ambiguity: {decision.ambiguity_score:.2f}")
"""

import logging
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from dataclasses import dataclass, field

# Use TYPE_CHECKING to avoid circular import
if TYPE_CHECKING:
    from app.etl.enrichment.tech_scorer import TechScoreResult

from app.etl.enrichment.policy import ClassificationPolicy, EffectiveThresholds

# Set up logger
logger = logging.getLogger(__name__)


# ============================================================
# Decision Reasons (structured, not magic strings)
# ============================================================

class DecisionReason(Enum):
    """Structured reasons for classification decisions."""
    SUCCESS = auto()
    SCORE_TOO_LOW = auto()
    MARGIN_TOO_LOW = auto()
    NON_TECH_CATEGORY = auto()
    NO_CATEGORIES = auto()
    UNKNOWN_CATEGORY = auto()
    NO_COMPETITORS = auto()  # No competing categories found
    
    def display_message(self) -> str:
        """Get human-readable message for this reason."""
        messages = {
            DecisionReason.SUCCESS: "Classified as tech role",
            DecisionReason.SCORE_TOO_LOW: "Score below minimum threshold",
            DecisionReason.MARGIN_TOO_LOW: "Margin below minimum threshold",
            DecisionReason.NON_TECH_CATEGORY: "Category is marked as non-tech",
            DecisionReason.NO_CATEGORIES: "No category scores available",
            DecisionReason.UNKNOWN_CATEGORY: "Unknown category",
            DecisionReason.NO_COMPETITORS: "No competing categories found",
        }
        return messages.get(self, "Unknown reason")


# ============================================================
# Constants
# ============================================================

UNKNOWN_CATEGORY = "unknown"


# ============================================================
# Classification Decision
# ============================================================

@dataclass(frozen=True)
class ClassificationDecision:
    """
    Immutable result of a classification decision.
    
    Contains everything needed to understand why a job was classified
    the way it was, including scores, margins, and explanations.
    
    Attributes:
        is_tech: Whether the job is classified as a technology role
        primary_category: The best matching category (e.g., 'backend', 'frontend')
        primary_score: The score of the primary category
        margin: Margin between primary and second-best category
        score: Overall raw score from the scorer
        confidence: Confidence score (0.0-1.0) for reporting only
        reason: Structured reason for the decision
        second_best_category: The second-best category (if any)
        second_best_score: Score of the second-best category (if any)
        ambiguity_score: 0.0 = clear winner, 1.0 = very ambiguous
        explanations: Human-readable explanations for the decision
        thresholds: The effective thresholds used for this decision
        all_scores: All category scores (for debugging)
        competing_categories: List of categories that compete with primary
    """
    is_tech: bool
    primary_category: str
    primary_score: float
    margin: float
    score: float
    confidence: float
    reason: DecisionReason
    second_best_category: Optional[str] = None
    second_best_score: Optional[float] = None
    ambiguity_score: float = 0.0
    explanations: List[str] = field(default_factory=list)
    thresholds: Optional[EffectiveThresholds] = None
    all_scores: Dict[str, float] = field(default_factory=dict)
    competing_categories: List[Tuple[str, float]] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate decision values."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(
                f"confidence must be between 0 and 1, got {self.confidence}"
            )
        
        if self.ambiguity_score < 0 or self.ambiguity_score > 1:
            raise ValueError(
                f"ambiguity_score must be between 0 and 1, got {self.ambiguity_score}"
            )
    
    @property
    def passed_minimum_score(self) -> bool:
        """Check if the primary score passed the minimum threshold."""
        if self.thresholds is None:
            return True
        return self.primary_score >= self.thresholds.tech_minimum
    
    @property
    def passed_margin(self) -> bool:
        """Check if the margin passed the minimum margin threshold."""
        if self.thresholds is None:
            return True
        return self.margin >= self.thresholds.minimum_margin
    
    @property
    def is_ambiguous(self) -> bool:
        """Check if the decision is ambiguous (ambiguity_score > 0.5)."""
        return self.ambiguity_score > 0.5
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high (> 0.7)."""
        return self.confidence >= 0.7
    
    @property
    def status_emoji(self) -> str:
        """Get status emoji for display."""
        return "✅" if self.is_tech else "❌"
    
    @property
    def status_label(self) -> str:
        """Get status label for display."""
        return "TECH" if self.is_tech else "NON-TECH"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary for serialization."""
        return {
            'is_tech': self.is_tech,
            'primary_category': self.primary_category,
            'primary_score': self.primary_score,
            'margin': self.margin,
            'score': self.score,
            'confidence': self.confidence,
            'reason': self.reason.name,
            'reason_message': self.reason.display_message(),
            'second_best_category': self.second_best_category,
            'second_best_score': self.second_best_score,
            'ambiguity_score': self.ambiguity_score,
            'explanations': self.explanations,
            'thresholds': self.thresholds.to_dict() if self.thresholds else None,
            'passed_minimum_score': self.passed_minimum_score,
            'passed_margin': self.passed_margin,
            'is_ambiguous': self.is_ambiguous,
            'is_high_confidence': self.is_high_confidence,
            'competing_categories': self.competing_categories,
        }


# ============================================================
# Helper Functions
# ============================================================

def _calculate_ambiguity_score(best_score: float, second_best_score: Optional[float]) -> float:
    """
    Calculate ambiguity score.
    
    0.0 = clear winner, 1.0 = very ambiguous.
    
    Args:
        best_score: Score of the best category
        second_best_score: Score of the second-best category (may be None)
    
    Returns:
        Float between 0.0 and 1.0
    """
    if second_best_score is None or second_best_score <= 0:
        return 0.0
    
    if best_score <= 0:
        return 1.0
    
    # Ratio of second-best to best - lower = clearer
    ratio = second_best_score / best_score
    
    # Clamp to [0, 1]
    return min(1.0, ratio)


def _get_sorted_categories(category_scores: Dict[str, float]) -> List[Tuple[str, float]]:
    """
    Get categories sorted by score descending.
    
    Args:
        category_scores: Dictionary of category_id -> score
    
    Returns:
        List of (category_id, score) tuples sorted by score descending
    """
    return sorted(
        category_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )


def _get_competing_categories(
    primary_category: str,
    sorted_categories: List[Tuple[str, float]]
) -> List[Tuple[str, float]]:
    """
    Get categories that compete with the primary category using taxonomy.
    
    Args:
        primary_category: The primary category ID
        sorted_categories: List of (category_id, score) tuples sorted descending
    
    Returns:
        List of (category_id, score) tuples that should compete
    """
    try:
        from app.etl.enrichment.classification_config import get_competing_categories
        return get_competing_categories(primary_category, sorted_categories)
    except Exception as e:
        logger.warning(f"Could not get competing categories: {e}")
        # Fallback: use all categories except primary
        return sorted_categories[1:]


def _is_tech_category(category_id: str, policy: ClassificationPolicy) -> bool:
    """
    Check if a category is marked as tech.
    
    Uses the configuration as the source of truth for category metadata.
    The policy is used for thresholds, not for determining which categories are tech.
    
    Args:
        category_id: The category ID to check
        policy: Classification policy (unused but kept for API consistency)
    
    Returns:
        True if the category is a tech category, False otherwise
    """
    try:
        from app.etl.enrichment.classification_config import get_config
        config = get_config()
        category = config.categories.get(category_id)
        return category.is_tech if category else False
    except Exception as e:
        logger.warning(f"Could not determine if category '{category_id}' is tech: {e}")
        # Fallback: assume categories are tech unless they're explicitly non-tech
        return category_id != 'non_tech'


def _make_decision(
    is_tech: bool,
    primary_category: str,
    primary_score: float,
    margin: float,
    result: 'TechScoreResult',  # Forward reference
    reason: DecisionReason,
    thresholds: EffectiveThresholds,
    second_best_category: Optional[str] = None,
    second_best_score: Optional[float] = None,
    ambiguity_score: float = 0.0,
    explanations: Optional[List[str]] = None,
    competing_categories: Optional[List[Tuple[str, float]]] = None,
) -> ClassificationDecision:
    """
    Factory function to create ClassificationDecision with consistent defaults.
    
    Reduces duplication across multiple return points.
    """
    if explanations is None:
        explanations = []
    
    if competing_categories is None:
        competing_categories = []
    
    # Add reason message if not already present
    if not any(reason.display_message() in e for e in explanations):
        explanations.append(reason.display_message())
    
    return ClassificationDecision(
        is_tech=is_tech,
        primary_category=primary_category,
        primary_score=primary_score,
        margin=margin,
        score=result.raw_score,
        confidence=result.confidence,
        reason=reason,
        second_best_category=second_best_category,
        second_best_score=second_best_score,
        ambiguity_score=ambiguity_score,
        explanations=explanations,
        thresholds=thresholds,
        all_scores=result.category_scores,
        competing_categories=competing_categories,
    )


# ============================================================
# Main Classification Function - Single Source of Truth
# ============================================================

def classify_result(
    result: 'TechScoreResult',  # Forward reference
    policy: ClassificationPolicy,
) -> ClassificationDecision:
    """
    Single source of truth for classification.
    
    Both production and validation call this function to ensure
    consistent classification logic.
    
    The decision process:
    1. Sort categories by score (highest first)
    2. Identify competing categories using taxonomy (excludes parents/children)
    3. Check minimum score threshold (prevents weak evidence)
    4. Check margin over second-best competing category (handles ambiguity)
    5. Calculate ambiguity score (for reporting)
    6. Return typed decision with explanations
    
    Args:
        result: Raw scoring result from TechnologyScorer
        policy: Classification policy with all thresholds
    
    Returns:
        ClassificationDecision with all relevant information
    """
    explanations = []
    
    # Get category scores from result
    category_scores = result.category_scores
    
    # ============================================================
    # Step 0: Check if there are any categories
    # ============================================================
    if not category_scores:
        return _make_decision(
            is_tech=False,
            primary_category=UNKNOWN_CATEGORY,
            primary_score=0.0,
            margin=0.0,
            result=result,
            reason=DecisionReason.NO_CATEGORIES,
            thresholds=EffectiveThresholds(0.0, 0.0),
            explanations=['No category scores available'],
        )
    
    # Sort categories by score
    sorted_categories = _get_sorted_categories(category_scores)
    
    # Best category
    primary_category = sorted_categories[0][0]
    primary_score = sorted_categories[0][1]
    
    # ============================================================
    # Step 1: Identify competing categories using taxonomy
    # This excludes parent/child relationships
    # ============================================================
    competing_categories = _get_competing_categories(primary_category, sorted_categories)
    
    # If there are no competing categories, we can't compute a meaningful margin
    if not competing_categories:
        # Log this case - it might indicate a taxonomy issue
        logger.debug(
            f"No competing categories found for '{primary_category}'. "
            f"Categories: {[c[0] for c in sorted_categories]}"
        )
        
        # Get effective thresholds
        thresholds = policy.get_effective_thresholds(primary_category)
        
        # Check if primary score meets minimum
        if primary_score < thresholds.tech_minimum:
            explanations.append(
                f"Primary score {primary_score:.1f} below tech_minimum {thresholds.tech_minimum}"
            )
            return _make_decision(
                is_tech=False,
                primary_category=primary_category,
                primary_score=primary_score,
                margin=0.0,
                result=result,
                reason=DecisionReason.SCORE_TOO_LOW,
                thresholds=thresholds,
                second_best_category=None,
                second_best_score=None,
                ambiguity_score=0.0,
                explanations=explanations,
                competing_categories=competing_categories,
            )
        
        # Check if category is tech
        if not _is_tech_category(primary_category, policy):
            explanations.append(
                f"Category '{primary_category}' is marked as non-tech"
            )
            return _make_decision(
                is_tech=False,
                primary_category=primary_category,
                primary_score=primary_score,
                margin=0.0,
                result=result,
                reason=DecisionReason.NON_TECH_CATEGORY,
                thresholds=thresholds,
                second_best_category=None,
                second_best_score=None,
                ambiguity_score=0.0,
                explanations=explanations,
                competing_categories=competing_categories,
            )
        
        # Success case with no competitors
        explanations.append(
            f"Classified as tech (category: {primary_category}, "
            f"score: {primary_score:.1f}, "
            f"no competing categories)"
        )
        return _make_decision(
            is_tech=True,
            primary_category=primary_category,
            primary_score=primary_score,
            margin=0.0,
            result=result,
            reason=DecisionReason.SUCCESS,
            thresholds=thresholds,
            second_best_category=None,
            second_best_score=None,
            ambiguity_score=0.0,
            explanations=explanations,
            competing_categories=competing_categories,
        )
    
    # ============================================================
    # Step 2: Get second-best competing category
    # ============================================================
    second_best_category = competing_categories[0][0]
    second_best_score = competing_categories[0][1]
    
    # Calculate margin using competing categories only
    margin = primary_score - second_best_score
    
    # Get effective thresholds for the primary category
    thresholds = policy.get_effective_thresholds(primary_category)
    
    # Calculate ambiguity score
    ambiguity_score = _calculate_ambiguity_score(primary_score, second_best_score)
    
    # ============================================================
    # Step 3: Check minimum score threshold
    # ============================================================
    if primary_score < thresholds.tech_minimum:
        explanations.append(
            f"Primary score {primary_score:.1f} below tech_minimum {thresholds.tech_minimum}"
        )
        return _make_decision(
            is_tech=False,
            primary_category=primary_category,
            primary_score=primary_score,
            margin=margin,
            result=result,
            reason=DecisionReason.SCORE_TOO_LOW,
            thresholds=thresholds,
            second_best_category=second_best_category,
            second_best_score=second_best_score,
            ambiguity_score=ambiguity_score,
            explanations=explanations,
            competing_categories=competing_categories,
        )
    
    # ============================================================
    # Step 4: Check margin over second-best competing category
    # ============================================================
    if margin < thresholds.minimum_margin:
        explanations.append(
            f"Margin {margin:.1f} below minimum_margin {thresholds.minimum_margin} "
            f"(best: {primary_score:.1f}, second competing: {second_best_score:.1f})"
        )
        return _make_decision(
            is_tech=False,
            primary_category=primary_category,
            primary_score=primary_score,
            margin=margin,
            result=result,
            reason=DecisionReason.MARGIN_TOO_LOW,
            thresholds=thresholds,
            second_best_category=second_best_category,
            second_best_score=second_best_score,
            ambiguity_score=ambiguity_score,
            explanations=explanations,
            competing_categories=competing_categories,
        )
    
    # ============================================================
    # Step 5: Check if primary category is actually a tech category
    # ============================================================
    if not _is_tech_category(primary_category, policy):
        explanations.append(
            f"Category '{primary_category}' is marked as non-tech"
        )
        return _make_decision(
            is_tech=False,
            primary_category=primary_category,
            primary_score=primary_score,
            margin=margin,
            result=result,
            reason=DecisionReason.NON_TECH_CATEGORY,
            thresholds=thresholds,
            second_best_category=second_best_category,
            second_best_score=second_best_score,
            ambiguity_score=ambiguity_score,
            explanations=explanations,
            competing_categories=competing_categories,
        )
    
    # ============================================================
    # Step 6: Classification succeeded
    # ============================================================
    explanations.append(
        f"Classified as tech (category: {primary_category}, "
        f"score: {primary_score:.1f}, "
        f"margin over competing category: {margin:.1f}, "
        f"confidence: {result.confidence:.2f}, "
        f"ambiguity: {ambiguity_score:.2f})"
    )
    
    return _make_decision(
        is_tech=True,
        primary_category=primary_category,
        primary_score=primary_score,
        margin=margin,
        result=result,
        reason=DecisionReason.SUCCESS,
        thresholds=thresholds,
        second_best_category=second_best_category,
        second_best_score=second_best_score,
        ambiguity_score=ambiguity_score,
        explanations=explanations,
        competing_categories=competing_categories,
    )


# ============================================================
# Batch Processing
# ============================================================

def batch_classify(
    results: List['TechScoreResult'],  # Forward reference
    policy: ClassificationPolicy,
) -> List[ClassificationDecision]:
    """
    Classify multiple results using the same policy.
    
    This is useful for batch processing and validation.
    
    Args:
        results: List of TechScoreResult objects
        policy: Classification policy
    
    Returns:
        List of ClassificationDecision objects
    """
    return [classify_result(result, policy) for result in results]


# ============================================================
# Summary Helpers
# ============================================================

def get_decision_summary(decision: ClassificationDecision) -> str:
    """
    Get a human-readable summary of a classification decision.
    
    Args:
        decision: ClassificationDecision object
    
    Returns:
        Summary string
    """
    status = decision.status_emoji + " " + decision.status_label
    
    competing_info = ""
    if decision.competing_categories:
        competing_info = f" (competitors: {len(decision.competing_categories)})"
    
    return (
        f"{status} | Category: {decision.primary_category} "
        f"(score: {decision.primary_score:.1f}, margin: {decision.margin:.1f}) "
        f"| Confidence: {decision.confidence:.2f} "
        f"| Ambiguity: {decision.ambiguity_score:.2f}"
        f"{competing_info}"
    )


def get_batch_summary(decisions: List[ClassificationDecision]) -> Dict[str, Any]:
    """
    Get summary statistics for a batch of decisions.
    
    Args:
        decisions: List of ClassificationDecision objects
    
    Returns:
        Dictionary with summary statistics
    """
    if not decisions:
        return {'total': 0, 'tech_count': 0, 'non_tech_count': 0}
    
    tech_count = sum(1 for d in decisions if d.is_tech)
    ambiguous_count = sum(1 for d in decisions if d.is_ambiguous)
    high_confidence_count = sum(1 for d in decisions if d.is_high_confidence)
    
    return {
        'total': len(decisions),
        'tech_count': tech_count,
        'non_tech_count': len(decisions) - tech_count,
        'tech_percentage': (tech_count / len(decisions)) * 100,
        'ambiguous_count': ambiguous_count,
        'ambiguous_percentage': (ambiguous_count / len(decisions)) * 100,
        'high_confidence_count': high_confidence_count,
        'high_confidence_percentage': (high_confidence_count / len(decisions)) * 100,
    }


# ============================================================
# Export
# ============================================================

__all__ = [
    'DecisionReason',
    'ClassificationDecision',
    'classify_result',
    'batch_classify',
    'get_decision_summary',
    'get_batch_summary',
    'UNKNOWN_CATEGORY',
]