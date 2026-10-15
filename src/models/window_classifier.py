"""Window-level classifier for RanSMAP early ransomware detection (T-P4-03).

Trains classifiers on fixed-width time window statistics (extracted by src.data.ransmap)
to predict per-window ransomware probability.

Key features:
  - Models: LogisticRegression (L2 scaled), LightGBM, RandomForest
  - Execution-grouped CV: guarantees windows from the same execution never cross folds
  - Family-held-out (Leave-One-Family-Out) CV: evaluates cross-family zero-day generalisation
  - Feature importance ranking (entropy, rate, locality)
  - Full metrics suite (Balanced Accuracy, Macro-F1, Precision, Recall, FPR, FNR, PR-AUC)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.data.ransmap import WINDOW_FEATURE_NAMES, WindowedDataset
from src.eval.metrics import ClassificationMetrics, compute_metrics


@dataclass
class WindowClassifierResult:
    """Evaluation results for a window classifier."""

    model_name: str
    metrics: ClassificationMetrics
    cv_scores: Optional[Dict[str, List[float]]] = None
    family_held_out: Optional[pd.DataFrame] = None
    feature_importances: Optional[pd.DataFrame] = None


def make_window_pipeline(
    model_type: str = "lgbm",
    seed: int = 42,
    **kwargs: Any,
) -> Pipeline:
    """Create a classifier pipeline with standard scaling where appropriate.

    Args:
        model_type: 'lr' (Logistic Regression), 'lgbm' (LightGBM), or 'rf' (Random Forest)
        seed: Random seed for reproducibility
        **kwargs: Extra parameters passed to the underlying estimator

    Returns:
        Configured sklearn Pipeline
    """
    if model_type == "lr":
        params = {"C": 1.0, "max_iter": 1000, "solver": "lbfgs", "random_state": seed}
        params.update(kwargs)
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(**params)),
        ])

    elif model_type == "lgbm":
        params = {
            "n_estimators": 100,
            "learning_rate": 0.05,
            "max_depth": 5,
            "num_leaves": 31,
            "random_state": seed,
            "verbose": -1,
            "n_jobs": 1,
        }
        params.update(kwargs)
        return Pipeline([
            ("clf", lgb.LGBMClassifier(**params)),
        ])

    elif model_type == "rf":
        params = {
            "n_estimators": 100,
            "max_depth": 8,
            "random_state": seed,
            "n_jobs": 1,
        }
        params.update(kwargs)
        return Pipeline([
            ("clf", RandomForestClassifier(**params)),
        ])

    else:
        raise ValueError(f"Unknown model_type: {model_type}. Expected 'lr', 'lgbm', or 'rf'.")


def evaluate_window_cv(
    dataset: WindowedDataset,
    model_type: str = "lgbm",
    n_splits: int = 5,
    seed: int = 42,
) -> Tuple[ClassificationMetrics, np.ndarray]:
    """Perform execution-grouped cross-validation on windowed dataset.

    Ensures all windows from any single execution stay entirely in train or val.

    Args:
        dataset: WindowedDataset containing features, labels, and execution_ids
        model_type: Classifier type ('lgbm', 'lr', 'rf')
        n_splits: Number of CV folds
        seed: Random seed

    Returns:
        (aggregated_metrics, out_of_fold_probabilities)
    """
    X = dataset.X
    y = dataset.y_binary
    groups = dataset.execution_ids

    unique_groups = np.unique(groups)
    effective_splits = min(n_splits, len(unique_groups))
    if effective_splits < 2:
        raise ValueError(f"Need at least 2 distinct executions for GroupKFold, found {len(unique_groups)}")

    gkf = GroupKFold(n_splits=effective_splits)
    oof_probs = np.zeros(len(y), dtype=np.float64)

    for train_idx, val_idx in gkf.split(X, y, groups=groups):
        pipe = make_window_pipeline(model_type=model_type, seed=seed)
        pipe.fit(X[train_idx], y[train_idx])
        oof_probs[val_idx] = pipe.predict_proba(X[val_idx])[:, 1]

    oof_preds = (oof_probs >= 0.5).astype(int)
    metrics = compute_metrics(y, oof_preds, y_score=oof_probs)
    return metrics, oof_probs


def evaluate_family_held_out(
    dataset: WindowedDataset,
    model_type: str = "lgbm",
    seed: int = 42,
) -> pd.DataFrame:
    """Perform Leave-One-Family-Out cross validation.

    In each fold, one family (e.g. Conti, LockBit, AESCrypt, Firefox) is completely
    held out, and the model is trained on all remaining families/apps.

    Returns:
        DataFrame summarizing performance on each held-out family
    """
    X = dataset.X
    y = dataset.y_binary
    families = dataset.families
    unique_families = sorted(np.unique(families))

    rows = []
    logo = LeaveOneGroupOut()

    for train_idx, test_idx in logo.split(X, y, groups=families):
        held_out_family = families[test_idx[0]]
        y_test = y[test_idx]

        # Check if train set has both classes
        y_train = y[train_idx]
        if len(np.unique(y_train)) < 2:
            warnings.warn(f"Skipping fold {held_out_family}: train set lacks two classes")
            continue

        pipe = make_window_pipeline(model_type=model_type, seed=seed)
        pipe.fit(X[train_idx], y_train)

        probs = pipe.predict_proba(X[test_idx])[:, 1]
        preds = (probs >= 0.5).astype(int)

        n_windows = len(y_test)
        is_ransomware = (y_test[0] == 1)

        if is_ransomware:
            # For ransomware family, compute recall (how many windows caught)
            recall = float(np.mean(preds == 1))
            fpr = np.nan
            bal_acc = recall
        else:
            # For benign app, compute FPR (false alarm rate on windows)
            recall = np.nan
            fpr = float(np.mean(preds == 1))
            bal_acc = 1.0 - fpr

        rows.append({
            "held_out_family": held_out_family,
            "type": "ransomware" if is_ransomware else "benign",
            "n_windows": n_windows,
            "mean_prob": float(np.mean(probs)),
            "window_detection_rate": recall if is_ransomware else (1.0 - fpr),
            "false_positive_rate": fpr if not is_ransomware else np.nan,
            "balanced_accuracy": bal_acc,
        })

    return pd.DataFrame(rows)


def extract_feature_importances(
    pipeline: Pipeline,
    feature_names: List[str],
) -> pd.DataFrame:
    """Extract and rank feature importances or coefficients from a fitted pipeline."""
    clf = pipeline.named_steps["clf"]

    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
        df = pd.DataFrame({
            "feature": feature_names,
            "importance": importances,
        }).sort_values("importance", ascending=False)
    elif hasattr(clf, "coef_"):
        coefs = clf.coef_[0]
        df = pd.DataFrame({
            "feature": feature_names,
            "coefficient": coefs,
            "abs_coefficient": np.abs(coefs),
        }).sort_values("abs_coefficient", ascending=False)
    else:
        df = pd.DataFrame({"feature": feature_names, "importance": np.zeros(len(feature_names))})

    df.reset_index(drop=True, inplace=True)
    return df
