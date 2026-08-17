#!/usr/bin/env python
"""
Validation framework for the technology classifier.

This script provides a comprehensive validation framework for the
technology classifier. It supports:
- Loading labeled datasets (JSON/CSV)
- Grid search over policy parameters
- Comprehensive metrics (precision, recall, F1, ROC AUC, PR AUC)
- Category-level metrics (accuracy, macro F1, weighted F1)
- Report generation with recommendations
- Stratified evaluation
- Reason breakdown for rejected classifications

Usage:
    # Validate with default policy
    python scripts/validate_classifier.py --data data/labeled_jobs.json
    
    # Find optimal thresholds
    python scripts/validate_classifier.py --data data/labeled_jobs.csv --optimize
    
    # Generate report
    python scripts/validate_classifier.py --data data/labeled_jobs.json --report reports/validation.json
    
    # Custom grid search ranges
    python scripts/validate_classifier.py --data data/labeled_jobs.json --optimize \
        --tech-min 5 --tech-max 15 --tech-step 1 \
        --margin-min 2.0 --margin-max 4.0 --margin-step 0.5
"""

import argparse
import hashlib
import json
import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import Counter

import pandas as pd
import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
    auc,
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.etl.enrichment.tech_scorer import (
    get_scorer,
    TechnologyScorer,
    TechScoreResult,
)
from app.etl.enrichment.classifier import (
    ClassificationDecision,
)
from app.etl.enrichment.policy import ClassificationPolicy, PolicyFormatter
from app.etl.enrichment.classification_config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# Constants
# ============================================================

UNKNOWN_REASON = "UNKNOWN"
DEFAULT_MIN_CONFIDENCE = 0.15  # Reporting only, not used for classification


# ============================================================
# Metrics Dataclass
# ============================================================
@dataclass
class ValidationMetrics:
    """Comprehensive metrics for classifier evaluation."""
    # Binary metrics
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    accuracy: float = 0.0
    specificity: float = 0.0
    balanced_accuracy: float = 0.0
    
    # Confusion matrix
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    # ROC/PR AUC (using primary_score, not confidence)
    roc_auc: float = 0.0
    pr_auc: float = 0.0
    
    # Category-level metrics
    category_accuracy: float = 0.0
    category_macro_f1: float = 0.0
    category_weighted_f1: float = 0.0
    category_samples: int = 0
    
    # Additional
    avg_ambiguity: float = 0.0
    ambiguous_count: int = 0
    reason_counts: Optional[Dict[str, int]] = None
    total: int = 0
    
    def __post_init__(self):
        if self.reason_counts is None:
            self.reason_counts = {}
    
    @property
    def confusion_matrix_list(self) -> List[List[int]]:
        return [
            [self.true_positives, self.false_positives],
            [self.false_negatives, self.true_negatives]
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "accuracy": round(self.accuracy, 4),
            "specificity": round(self.specificity, 4),
            "balanced_accuracy": round(self.balanced_accuracy, 4),
            "roc_auc": round(self.roc_auc, 4),
            "pr_auc": round(self.pr_auc, 4),
            "category_accuracy": round(self.category_accuracy, 4),
            "category_macro_f1": round(self.category_macro_f1, 4),
            "category_weighted_f1": round(self.category_weighted_f1, 4),
            "category_samples": self.category_samples,
            "avg_ambiguity": round(self.avg_ambiguity, 4),
            "ambiguous_count": self.ambiguous_count,
            "reason_counts": self.reason_counts,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "total": self.total,
            "confusion_matrix": self.confusion_matrix_list,
        }
    
    def summary(self) -> str:
        """Get a human-readable summary."""
        lines = [
            "=" * 60,
            "Validation Results",
            "=" * 60,
            f"Total samples:     {self.total}",
            "",
            f"Binary Classification:",
            f"  Precision:        {self.precision:.3f}",
            f"  Recall:           {self.recall:.3f}",
            f"  F1:               {self.f1:.3f}",
            f"  Accuracy:         {self.accuracy:.3f}",
            f"  Specificity:      {self.specificity:.3f}",
            f"  Balanced Acc:     {self.balanced_accuracy:.3f}",
            "",
            f"ROC/PR (using primary_score):",
            f"  ROC AUC:          {self.roc_auc:.3f}",
            f"  PR AUC:           {self.pr_auc:.3f}",
            "",
            f"Category:",
            f"  Category Acc:     {self.category_accuracy:.3f}",
            f"  Macro F1:         {self.category_macro_f1:.3f}",
            f"  Weighted F1:      {self.category_weighted_f1:.3f}",
            f"  Category Samples: {self.category_samples}",
            "",
            f"Ambiguity:",
            f"  Avg Ambiguity:    {self.avg_ambiguity:.3f}",
            f"  Ambiguous:        {self.ambiguous_count}",
            "",
            f"Decision Reasons:",
        ]
        
        reason_counts = self.reason_counts or {}
        for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {reason}: {count}")
        
        lines.extend([
            "",
            f"Confusion Matrix:",
            f"  TP: {self.true_positives}  FP: {self.false_positives}",
            f"  FN: {self.false_negatives}  TN: {self.true_negatives}",
            "=" * 60,
        ])
        return "\n".join(lines)


# ============================================================
# Policy Hash Helper
# ============================================================

def policy_hash(policy: ClassificationPolicy) -> str:
    """Generate a stable hash for a policy."""
    content = (
        f"{policy.tech_minimum}|"
        f"{policy.minimum_margin}|"
        f"{policy.min_confidence}|"
        f"{sorted(policy.category_overrides.keys())}"
    )
    return hashlib.md5(content.encode()).hexdigest()[:8]


# ============================================================
# Validator Class
# ============================================================

class ClassifierValidator:
    """
    Validate and tune the technology classifier.
    
    This class provides a comprehensive validation framework with:
    - Labeled dataset loading
    - Policy evaluation with full metrics
    - Grid search for optimal thresholds
    - Report generation
    
    Example:
        validator = ClassifierValidator('data/labeled_jobs.json')
        
        # Evaluate a policy
        metrics = validator.evaluate(ClassificationPolicy.default())
        print(metrics.summary())
        
        # Find optimal policy
        result = validator.find_optimal_policy()
        print(f"Best policy: {result['best_policy']}")
        
        # Generate report
        validator.generate_report('reports/validation.json')
    """
    
    # Cache version - increment when scoring logic changes
    CACHE_VERSION = "1.0.0"
    
    def __init__(self, labeled_data_path: Optional[Path] = None):
        """
        Initialize the validator.
        
        Args:
            labeled_data_path: Path to labeled dataset (JSON or CSV)
        """
        self.labeled_data: List[Dict] = []
        self.scores_cache: Dict[str, TechScoreResult] = {}
        self.scorer: TechnologyScorer = get_scorer()
        self.config = get_config()
        
        if labeled_data_path and Path(labeled_data_path).exists():
            self.labeled_data = self._load_labeled_data(Path(labeled_data_path))
            logger.info(f"Loaded {len(self.labeled_data)} labeled jobs")
    
    def _load_labeled_data(self, path: Path) -> List[Dict]:
        """Load labeled job data."""
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'jobs' in data:
                    return data['jobs']
                elif isinstance(data, dict):
                    # Single job object, wrap in list
                    return [data]
                elif isinstance(data, list):
                    return data
                else:
                    logger.warning(f"Unexpected JSON format in {path}")
                    return []
        elif path.suffix == '.csv':
            df = pd.read_csv(path)
            return df.to_dict('records')
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")
    
    def _get_cache_key(self, job: Dict) -> str:
        """
        Create cache key from job content using SHA-256.
        
        Includes cache version to invalidate when scoring changes.
        """
        title = job.get('title', '')
        description = job.get('description', '')
        skills = sorted(job.get('skills', []))
        
        # Combine all fields with cache version
        content = f"{self.CACHE_VERSION}\n{title}\n{description}\n{','.join(skills)}"
        
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _precompute_scores(self) -> None:
        """Precompute scores for all labeled jobs."""
        for job in self.labeled_data:
            key = self._get_cache_key(job)
            if key not in self.scores_cache:
                result = self.scorer.score(
                    job.get('title', ''),
                    job.get('description', ''),
                    job.get('skills', [])
                )
                self.scores_cache[key] = result
    
    def _classify_with_policy(
        self,
        job: Dict,
        policy: ClassificationPolicy,
    ) -> ClassificationDecision:
        """
        Classify a job with a specific policy using production path.
        
        This uses scorer.classify() which includes all production logic:
        - Title-strength scoring
        - Title pattern matching
        - All override logic
        """
        return self.scorer.classify(
            title=job.get('title', ''),
            description=job.get('description', ''),
            skills=job.get('skills', []),
            policy=policy,
        )
    
    def _get_reason_name(self, decision: ClassificationDecision) -> str:
        """Safely get the reason name from a decision."""
        if decision.reason is not None:
            return decision.reason.name
        return UNKNOWN_REASON
    
    def evaluate(
        self,
        policy: ClassificationPolicy,
        verbose: bool = True,
    ) -> ValidationMetrics:
        """
        Evaluate classifier with a specific policy.
        
        Args:
            policy: Classification policy to evaluate
            verbose: Whether to log progress
        
        Returns:
            ValidationMetrics object
        """
        if not self.labeled_data:
            logger.warning("No labeled data loaded")
            return ValidationMetrics()
        
        # Precompute scores once
        self._precompute_scores()
        
        # Collect predictions
        y_true = []
        y_pred = []
        y_scores = []  # Using primary_score for ROC/PR
        y_categories_true = []
        y_categories_pred = []
        ambiguities = []
        reasons = []
        
        for job in self.labeled_data:
            actual = job.get('is_tech_role', False)
            expected_category_raw = job.get('expected_category', '')
            expected_category = str(expected_category_raw).strip() if expected_category_raw else ''
            
            # Get prediction using policy (production path)
            decision = self._classify_with_policy(job, policy)
            predicted = decision.is_tech
            
            y_true.append(actual)
            y_pred.append(predicted)
            # Use primary_score for ROC/PR (not confidence)
            y_scores.append(decision.primary_score)
            ambiguities.append(decision.ambiguity_score)
            reasons.append(self._get_reason_name(decision))
            
            if expected_category:
                y_categories_true.append(expected_category)
                y_categories_pred.append(decision.primary_category)
        
        # Binary metrics using sklearn
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        accuracy = accuracy_score(y_true, y_pred)
        
        # Confusion matrix - SAFE: ensure 2x2 with labels
        cm = confusion_matrix(y_true, y_pred, labels=[False, True])
        tn, fp, fn, tp = cm.ravel()
        
        # Specificity
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        
        # Balanced accuracy
        balanced_accuracy = (recall + specificity) / 2
        
        # ROC/PR AUC using primary_score (not confidence)
        roc_auc = 0.0
        pr_auc = 0.0
        if len(set(y_true)) > 1:
            try:
                roc_auc = roc_auc_score(y_true, y_scores)
                precision_vals, recall_vals, _ = precision_recall_curve(y_true, y_scores)
                pr_auc = auc(recall_vals, precision_vals)
            except Exception as e:
                if verbose:
                    logger.debug(f"Could not compute ROC/PR AUC: {e}")
        
        # Category-level metrics
        category_accuracy = 0.0
        category_macro_f1 = 0.0
        category_weighted_f1 = 0.0
        category_samples = len(y_categories_true)
        
        if y_categories_true:
            category_accuracy = accuracy_score(y_categories_true, y_categories_pred)
            category_macro_f1 = f1_score(
                y_categories_true, y_categories_pred, 
                average='macro', zero_division=0
            )
            category_weighted_f1 = f1_score(
                y_categories_true, y_categories_pred,
                average='weighted', zero_division=0
            )
        
        # Ambiguity
        avg_ambiguity = np.mean(ambiguities) if ambiguities else 0.0
        ambiguous_count = sum(1 for a in ambiguities if a > 0.5)
        
        # Reason counts
        reason_counts = dict(Counter(reasons))
        return ValidationMetrics(
            precision=float(precision),
            recall=float(recall),
            f1=float(f1),
            accuracy=float(accuracy),
            specificity=float(specificity),
            balanced_accuracy=float(balanced_accuracy),
            true_positives=int(tp),
            false_positives=int(fp),
            true_negatives=int(tn),
            false_negatives=int(fn),
            roc_auc=float(roc_auc),
            pr_auc=float(pr_auc),
            category_accuracy=float(category_accuracy),
            category_macro_f1=float(category_macro_f1),
            category_weighted_f1=float(category_weighted_f1),
            category_samples=int(category_samples),
            avg_ambiguity=float(avg_ambiguity),
            ambiguous_count=int(ambiguous_count),
            reason_counts=reason_counts,
            total=int(len(y_true)),
        )
        
    def find_optimal_policy(
        self,
        tech_minimum_range: Optional[List[int]] = None,
        margin_range: Optional[List[float]] = None,
        optimize_for: str = "f1",
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Find optimal policy by grid search."""
        # Set default ranges if not provided
        if tech_minimum_range is None:
            tech_minimum_range = list(range(3, 20))
        if margin_range is None:
            margin_range = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        
        # Guard against empty ranges
        if not tech_minimum_range or not margin_range:
            logger.error("Empty parameter ranges provided")
            return {
                'error': 'Empty parameter ranges',
                'best_policy': None,
                'best_metrics': None,
            }
        
        if not self.labeled_data:
            logger.warning("No labeled data loaded. Cannot find optimal policy.")
            return {'error': 'No labeled data'}
        
        best_score = -float('inf')  # Initialize with negative infinity
        best_policy = None
        best_metrics = None
        results = []
        
        metric_map = {
            "f1": lambda m: m.f1,
            "precision": lambda m: m.precision,
            "recall": lambda m: m.recall,
            "accuracy": lambda m: m.accuracy,
        }
        score_fn = metric_map.get(optimize_for, lambda m: m.f1)
        
        total_combinations = len(tech_minimum_range) * len(margin_range)
        
        logger.info(f"Evaluating {total_combinations} combinations...")
        logger.info(f"Optimizing for: {optimize_for}")
        
        count = 0
        for tech_min in tech_minimum_range:
            for margin in margin_range:
                count += 1
                
                # Create policy for this combination
                policy = ClassificationPolicy(
                    tech_minimum=float(tech_min),
                    minimum_margin=margin,
                    min_confidence=DEFAULT_MIN_CONFIDENCE,
                    name=f"grid_{tech_min}_{margin}",
                    description=f"Grid search: tech_min={tech_min}, margin={margin}",
                )
                
                metrics = self.evaluate(policy, verbose=False)
                
                result_entry = {
                    'tech_minimum': tech_min,
                    'minimum_margin': margin,
                    'policy_hash': policy_hash(policy),
                    'precision': metrics.precision,
                    'recall': metrics.recall,
                    'f1': metrics.f1,
                    'accuracy': metrics.accuracy,
                    'roc_auc': metrics.roc_auc,
                    'pr_auc': metrics.pr_auc,
                    'category_accuracy': metrics.category_accuracy,
                    'category_macro_f1': metrics.category_macro_f1,
                    'category_weighted_f1': metrics.category_weighted_f1,
                    'avg_ambiguity': metrics.avg_ambiguity,
                }
                results.append(result_entry)
                
                current_score = score_fn(metrics)
                
                # Tie-breaking with math.isclose
                is_better = (
                    current_score > best_score
                    or (
                        math.isclose(current_score, best_score, abs_tol=1e-9)
                        and best_metrics is not None
                        and metrics.precision > best_metrics.precision
                    )
                )
                
                if is_better:
                    best_score = current_score
                    best_policy = policy
                    best_metrics = metrics
                
                if verbose and count % 50 == 0:
                    logger.info(f"  Progress: {count}/{total_combinations}")
        
        # Log summary - FIXED with None checks
        if best_policy is not None and best_metrics is not None:
            logger.info(f"\n{'='*60}")
            logger.info(f"Best {optimize_for}: {best_score:.4f}")
            logger.info(f"Best Policy:")
            logger.info(f"  tech_minimum:     {best_policy.tech_minimum}")
            logger.info(f"  minimum_margin:   {best_policy.minimum_margin}")
            logger.info(f"  policy_hash:      {policy_hash(best_policy)}")
            logger.info(f"\nMetrics:")
            logger.info(f"  Precision:        {best_metrics.precision:.4f}")
            logger.info(f"  Recall:           {best_metrics.recall:.4f}")
            logger.info(f"  F1:               {best_metrics.f1:.4f}")
            logger.info(f"  Accuracy:         {best_metrics.accuracy:.4f}")
            logger.info(f"  ROC AUC:          {best_metrics.roc_auc:.4f}")
            logger.info(f"  PR AUC:           {best_metrics.pr_auc:.4f}")
            logger.info(f"  Category Acc:     {best_metrics.category_accuracy:.4f}")
            logger.info(f"  Category Macro F1:{best_metrics.category_macro_f1:.4f}")
            logger.info(f"  Avg Ambiguity:    {best_metrics.avg_ambiguity:.4f}")
            logger.info(f"Confusion Matrix:   {best_metrics.confusion_matrix_list}")
            logger.info(f"\nDecision Reasons:")
            if best_metrics.reason_counts:
                for reason, count in sorted(best_metrics.reason_counts.items(), key=lambda x: -x[1]):
                    logger.info(f"  {reason}: {count}")
            logger.info(f"{'='*60}\n")
        else:
            logger.error("No valid policy found during optimization")
            return {
                'error': 'No valid policy found',
                'best_policy': None,
                'best_metrics': None,
                'optimize_for': optimize_for,
                'total_combinations': total_combinations,
                'all_results': results,
            }
        
        return {
            'best_policy': best_policy,
            'best_metrics': best_metrics,
            'optimize_for': optimize_for,
            'total_combinations': total_combinations,
            'all_results': results,
        }
    
    def generate_report(
        self,
        output_path: Path,
        tech_minimum_range: Optional[List[int]] = None,
        margin_range: Optional[List[float]] = None,
        optimize_for: str = "f1",
        include_all_results: bool = False,
    ) -> None:
        """
        Generate a comprehensive validation report.
        
        Args:
            output_path: Path to write the report
            tech_minimum_range: Tech minimum values used in optimization
            margin_range: Margin values used in optimization
            optimize_for: Metric optimized for
            include_all_results: Whether to include all grid search results
        """
        if not self.labeled_data:
            logger.warning("No labeled data loaded. Cannot generate report.")
            return
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get default policy evaluation
        default_policy = ClassificationPolicy.default()
        default_metrics = self.evaluate(default_policy)
        
        # Find optimal policy with the same parameters
        optimization_results = self.find_optimal_policy(
            tech_minimum_range=tech_minimum_range,
            margin_range=margin_range,
            optimize_for=optimize_for,
            verbose=False,
        )
        
        # Build report
        report = {
            'generated_at': datetime.now().isoformat(),
            'cache_version': self.CACHE_VERSION,
            'dataset_size': len(self.labeled_data),
            'class_distribution': self._get_class_distribution(),
            'optimization_config': {
                'tech_minimum_range': tech_minimum_range,
                'margin_range': margin_range,
                'optimize_for': optimize_for,
            },
            'default_policy': {
                'policy': default_policy.to_dict(),
                'policy_hash': policy_hash(default_policy),
                'metrics': default_metrics.to_dict(),
            },
            'optimization': {
                'best_policy': optimization_results['best_policy'].to_dict(),
                'best_policy_hash': policy_hash(optimization_results['best_policy']),
                'best_metrics': optimization_results['best_metrics'].to_dict(),
                'optimize_for': optimization_results['optimize_for'],
                'total_combinations': optimization_results['total_combinations'],
            },
            'recommendations': self._get_recommendations(
                default_metrics,
                optimization_results['best_metrics'],
                optimization_results['best_policy'],
            ),
        }
        
        # Optionally include all results
        if include_all_results and 'all_results' in optimization_results:
            report['optimization']['all_results'] = optimization_results['all_results']
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Report saved to {output_path}")
    
    def _get_class_distribution(self) -> Dict[str, int]:
        """Get distribution of tech vs non-tech in dataset."""
        tech_count = sum(1 for job in self.labeled_data if job.get('is_tech_role', False))
        return {
            'tech': tech_count,
            'non_tech': len(self.labeled_data) - tech_count,
        }
    
    def _get_recommendations(
        self,
        default_metrics: ValidationMetrics,
        best_metrics: ValidationMetrics,
        best_policy: ClassificationPolicy,
    ) -> Dict[str, Any]:
        """Generate recommendations based on validation results."""
        f1_improvement = best_metrics.f1 - default_metrics.f1
        
        notes = [
            f"Optimal policy found with F1={best_metrics.f1:.3f}",
            f"Default policy F1={default_metrics.f1:.3f}",
            f"Improvement: {f1_improvement:+.3f}",
        ]
        
        if f1_improvement > 0.02:
            notes.append("✅ Consider using the recommended policy in production")
            notes.append(f"   F1 improvement of {f1_improvement:.3f} is meaningful")
        elif f1_improvement > 0.005:
            notes.append("⚠️ Slight improvement - evaluate on larger dataset")
            notes.append("   Consider cross-validation before deploying")
        else:
            notes.append("ℹ️ Default policy performs similarly - keep default")
            notes.append("   The small improvement may not justify switching")
        
        # Add reason-specific recommendations
        if best_metrics.reason_counts:
            top_reason = max(best_metrics.reason_counts.items(), key=lambda x: x[1])
            notes.append(f"Top rejection reason: {top_reason[0]} ({top_reason[1]} jobs)")
        
        notes.append("📊 Monitor performance over time and re-validate periodically")
        
        return {
            'recommended_policy': best_policy.to_dict(),
            'recommended_policy_hash': policy_hash(best_policy),
            'improvement_over_default': {
                'f1': f1_improvement,
                'precision': best_metrics.precision - default_metrics.precision,
                'recall': best_metrics.recall - default_metrics.recall,
            },
            'notes': notes,
        }


# ============================================================
# CLI Entry Point
# ============================================================

def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate and tune the technology classifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to labeled dataset (JSON or CSV)",
    )
    
    parser.add_argument(
        "--report",
        type=str,
        default="reports/validation_report.json",
        help="Path to save validation report (default: reports/validation_report.json)",
    )
    
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Find optimal thresholds via grid search",
    )
    
    parser.add_argument(
        "--optimize-for",
        type=str,
        default="f1",
        choices=["f1", "precision", "recall", "accuracy"],
        help="Metric to optimize (default: f1)",
    )
    
    parser.add_argument(
        "--tech-min",
        type=int,
        default=3,
        help="Minimum tech_minimum to test (default: 3)",
    )
    
    parser.add_argument(
        "--tech-max",
        type=int,
        default=20,
        help="Maximum tech_minimum to test (default: 20)",
    )
    
    parser.add_argument(
        "--tech-step",
        type=int,
        default=1,
        help="Step size for tech_minimum (default: 1)",
    )
    
    parser.add_argument(
        "--margin-min",
        type=float,
        default=1.0,
        help="Minimum margin to test (default: 1.0)",
    )
    
    parser.add_argument(
        "--margin-max",
        type=float,
        default=5.0,
        help="Maximum margin to test (default: 5.0)",
    )
    
    parser.add_argument(
        "--margin-step",
        type=float,
        default=0.5,
        help="Step size for margin (default: 0.5)",
    )
    
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all grid search results in report",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate data file exists
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    # Initialize validator
    validator = ClassifierValidator(data_path)
    
    if not validator.labeled_data:
        logger.error("No labeled data loaded")
        sys.exit(1)
    
    logger.info(f"Loaded {len(validator.labeled_data)} labeled jobs")
    logger.info(f"Class distribution: {validator._get_class_distribution()}")
    
    # Build parameter ranges
    tech_range = list(range(args.tech_min, args.tech_max + 1, args.tech_step))
    margin_range = [
        round(args.margin_min + i * args.margin_step, 1)
        for i in range(int((args.margin_max - args.margin_min) / args.margin_step) + 1)
    ]
    
    # Evaluate default policy
    logger.info("\n" + "=" * 60)
    logger.info("Evaluating Default Policy")
    logger.info("=" * 60)
    
    default_policy = ClassificationPolicy.default()
    default_metrics = validator.evaluate(default_policy)
    logger.info(default_metrics.summary())
    
    # Find optimal policy if requested
    if args.optimize:
        logger.info("\n" + "=" * 60)
        logger.info("Finding Optimal Policy")
        logger.info("=" * 60)
        
        logger.info(f"tech_minimum range: {tech_range}")
        logger.info(f"margin range: {margin_range}")
        logger.info(f"Optimizing for: {args.optimize_for}")
        
        optimization_results = validator.find_optimal_policy(
            tech_minimum_range=tech_range,
            margin_range=margin_range,
            optimize_for=args.optimize_for,
            verbose=args.verbose,
        )
        
        best_policy = optimization_results['best_policy']
        best_metrics = optimization_results['best_metrics']
        
        logger.info("\n" + best_metrics.summary())
        
        logger.info("\n" + "=" * 60)
        logger.info("Recommendation")
        logger.info("=" * 60)
        logger.info(PolicyFormatter.summary(best_policy))
    
    # Generate report with consistent parameters
    logger.info("\nGenerating report...")
    validator.generate_report(
        output_path=Path(args.report),
        tech_minimum_range=tech_range if args.optimize else None,
        margin_range=margin_range if args.optimize else None,
        optimize_for=args.optimize_for if args.optimize else "f1",
        include_all_results=args.include_all,
    )
    
    logger.info("\n✅ Validation complete!")


if __name__ == "__main__":
    main()