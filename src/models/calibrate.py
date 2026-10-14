"""Probability calibration and threshold selection under FPR budgets (T-P2-02).

Provides:
- ProbabilityCalibrator using Platt scaling (Logistic Regression on logits) or Isotonic Regression on validation slices.
- Operating threshold selection satisfying strict false positive rate budgets (e.g. FPR <= 1%).
- Expected Calibration Error (ECE) and Brier score metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from pathlib import Path

from sklearn.metrics import brier_score_loss, confusion_matrix


@dataclass
class OperatingPoint:
    """Represents a chosen classification threshold and its empirical performance."""

    threshold: float
    target_fpr_budget: float
    empirical_fpr: float
    empirical_recall: float
    empirical_precision: float
    empirical_bal_acc: float
    tp: int
    fp: int
    tn: int
    fn: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "threshold": self.threshold,
            "target_fpr_budget": self.target_fpr_budget,
            "empirical_fpr": self.empirical_fpr,
            "empirical_recall": self.empirical_recall,
            "empirical_precision": self.empirical_precision,
            "empirical_bal_acc": self.empirical_bal_acc,
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
        }


def find_operating_threshold(
    y_true: np.ndarray | pd.Series,
    y_prob: np.ndarray | pd.Series,
    fpr_budget: float = 0.01,
) -> OperatingPoint:
    """Find the optimal probability threshold that satisfies FPR <= fpr_budget.

    Scans descending probability thresholds to maximize Recall while guaranteeing
    that False Positive Rate does not exceed the specified budget.

    Args:
        y_true: True binary labels (0 or 1).
        y_prob: Predicted positive-class probabilities [0, 1].
        fpr_budget: Maximum allowed False Positive Rate (default 0.01 = 1%).

    Returns:
        OperatingPoint containing the optimal threshold and associated metrics.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)

    thresholds = np.linspace(0.01, 0.99, 197)
    best_op: Optional[OperatingPoint] = None

    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        bal = 0.5 * ((tn / (tn + fp)) + rec) if (tn + fp) > 0 and (tp + fn) > 0 else 0.0

        if fpr <= fpr_budget:
            best_op = OperatingPoint(
                threshold=float(t),
                target_fpr_budget=float(fpr_budget),
                empirical_fpr=float(fpr),
                empirical_recall=float(rec),
                empirical_precision=float(prec),
                empirical_bal_acc=float(bal),
                tp=int(tp),
                fp=int(fp),
                tn=int(tn),
                fn=int(fn),
            )
            break

    if best_op is None:
        best_op = OperatingPoint(
            threshold=1.0,
            target_fpr_budget=float(fpr_budget),
            empirical_fpr=0.0,
            empirical_recall=0.0,
            empirical_precision=0.0,
            empirical_bal_acc=0.5,
            tp=0,
            fp=0,
            tn=int((y_true == 0).sum()),
            fn=int((y_true == 1).sum()),
        )

    return best_op


def evaluate_calibration(
    y_true: np.ndarray | pd.Series,
    y_prob: np.ndarray | pd.Series,
    n_bins: int = 10,
) -> Dict[str, Any]:
    """Compute calibration curve, Brier score, and Expected Calibration Error (ECE).

    Args:
        y_true: True binary labels (0 or 1).
        y_prob: Predicted positive-class probabilities in [0, 1].
        n_bins: Number of bins for calibration curve (default 10).

    Returns:
        Dict containing brier_score, ece, prob_true, and prob_pred.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)

    brier = float(brier_score_loss(y_true, y_prob))
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_assignments = np.digitize(y_prob, bin_edges) - 1
    bin_assignments = np.clip(bin_assignments, 0, n_bins - 1)

    ece = 0.0
    n = len(y_prob)
    for b in range(n_bins):
        mask = bin_assignments == b
        if np.any(mask):
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += (np.sum(mask) / n) * np.abs(bin_acc - bin_conf)

    return {
        "brier_score": brier,
        "ece": float(ece),
        "prob_true": prob_true.tolist(),
        "prob_pred": prob_pred.tolist(),
    }


def save_reliability_curve(
    y_true: np.ndarray | pd.Series,
    curves: Dict[str, np.ndarray | pd.Series],
    out_path: str | Path,
    n_bins: int = 10,
) -> Path:
    """Save a reliability (calibration) plot for one or more probability series."""
    import matplotlib.pyplot as plt

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    y_true_arr = np.asarray(y_true, dtype=int)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Perfect")
    for name, probs in curves.items():
        pt, pp = calibration_curve(y_true_arr, np.asarray(probs, dtype=float), n_bins=n_bins, strategy="uniform")
        ax.plot(pp, pt, marker="o", label=name)
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_title("Reliability curve")
    ax.legend()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


class CalibratedModelWrapper:
    """Applies Platt scaling or Isotonic Regression on prefit model outputs using a validation slice."""

    def __init__(self, base_estimator: Any, method: str = "sigmoid"):
        self.base_estimator = base_estimator
        self.method = method
        if method == "sigmoid":
            self.calibrator = LogisticRegression(solver="lbfgs", random_state=42)
        elif method == "isotonic":
            self.calibrator = IsotonicRegression(out_of_bounds="clip")
        else:
            raise ValueError(f"Unknown calibration method: {method}")
        self.is_fitted = False

    def _get_base_scores(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        if hasattr(self.base_estimator, "predict_proba"):
            scores = self.base_estimator.predict_proba(X)[:, 1]
        elif hasattr(self.base_estimator, "decision_function"):
            scores = self.base_estimator.decision_function(X)
        else:
            scores = self.base_estimator.predict(X)
        return np.asarray(scores, dtype=float)

    def fit_calibration(self, X_val: np.ndarray | pd.DataFrame, y_val: np.ndarray | pd.Series) -> CalibratedModelWrapper:
        """Fit calibration curve on the held-out validation slice."""
        val_scores = self._get_base_scores(X_val)
        y_val_arr = np.asarray(y_val, dtype=int)

        if self.method == "sigmoid":
            # Reshape 1D score to 2D for LogisticRegression
            self.calibrator.fit(val_scores.reshape(-1, 1), y_val_arr)
        else:
            self.calibrator.fit(val_scores, y_val_arr)

        self.is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Calibrator has not been fitted yet!")
        scores = self._get_base_scores(X)
        if self.method == "sigmoid":
            p1 = self.calibrator.predict_proba(scores.reshape(-1, 1))[:, 1]
        else:
            p1 = self.calibrator.predict(scores)
            p1 = np.clip(p1, 0.0, 1.0)
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, X: np.ndarray | pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(int)
