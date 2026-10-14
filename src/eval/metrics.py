"""Comprehensive evaluation metrics suite with bootstrap confidence intervals.

Implements all metrics mandated by AGENTS.md §3:
- Balanced Accuracy
- Macro-F1 & Binary F1
- Precision & Recall
- False Positive Rate (FPR) & False Negative Rate (FNR)
- ROC-AUC & PR-AUC
- Confusion Matrix (TN, FP, FN, TP)
- 95% Bootstrap Confidence Intervals via percentile bootstrap
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class ClassificationMetrics:
    """Stores point estimates and optional bootstrap 95% confidence intervals."""

    balanced_accuracy: float
    macro_f1: float
    precision: float
    recall: float
    f1: float
    fpr: float
    fnr: float
    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None
    tn: int = 0
    fp: int = 0
    fn: int = 0
    tp: int = 0
    ci_95: Optional[Dict[str, Tuple[float, float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)

    def summary_table(self) -> pd.DataFrame:
        """Return a formatted DataFrame of metrics and confidence intervals."""
        rows = [
            ("Balanced Accuracy", self.balanced_accuracy),
            ("Macro-F1", self.macro_f1),
            ("Precision (Ransomware)", self.precision),
            ("Recall (Ransomware)", self.recall),
            ("Binary F1", self.f1),
            ("False Positive Rate (FPR)", self.fpr),
            ("False Negative Rate (FNR)", self.fnr),
        ]
        if self.roc_auc is not None:
            rows.append(("ROC-AUC", self.roc_auc))
        if self.pr_auc is not None:
            rows.append(("PR-AUC", self.pr_auc))

        data = []
        for name, val in rows:
            key = name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
            # Map key to ci_95 key
            ci_key = {
                "balanced_accuracy": "balanced_accuracy",
                "macro_f1": "macro_f1",
                "precision_ransomware": "precision",
                "recall_ransomware": "recall",
                "binary_f1": "f1",
                "false_positive_rate_fpr": "fpr",
                "false_negative_rate_fnr": "fnr",
                "roc_auc": "roc_auc",
                "pr_auc": "pr_auc",
            }.get(key, key)

            ci_str = "—"
            if self.ci_95 and ci_key in self.ci_95:
                low, high = self.ci_95[ci_key]
                ci_str = f"[{low:.4f}, {high:.4f}]"

            data.append({"Metric": name, "Value": f"{val:.4f}", "95% CI": ci_str})

        return pd.DataFrame(data)


def compute_metrics(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    y_score: Optional[np.ndarray | pd.Series] = None,
    bootstrap_resamples: int = 0,
    seed: int = 42,
) -> ClassificationMetrics:
    """Compute binary classification metrics with optional bootstrap confidence intervals.

    Args:
        y_true: True binary labels (0 or 1).
        y_pred: Predicted binary labels (0 or 1).
        y_score: Predicted probabilities/scores for positive class (1). Optional.
        bootstrap_resamples: Number of bootstrap iterations for 95% CI. 0 to skip.
        seed: Random seed for bootstrap reproducibility.

    Returns:
        ClassificationMetrics instance with point estimates and optional 95% CIs.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    bal_acc = balanced_accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    binary_f1 = f1_score(y_true, y_pred, zero_division=0)

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    roc_auc = None
    pr_auc = None
    if y_score is not None:
        y_score = np.asarray(y_score, dtype=float)
        try:
            roc_auc = roc_auc_score(y_true, y_score)
            pr_auc = average_precision_score(y_true, y_score)
        except ValueError:
            pass

    ci_dict = None
    if bootstrap_resamples > 0:
        ci_dict = _compute_bootstrap_ci(
            y_true=y_true,
            y_pred=y_pred,
            y_score=y_score,
            n_resamples=bootstrap_resamples,
            seed=seed,
        )

    return ClassificationMetrics(
        balanced_accuracy=float(bal_acc),
        macro_f1=float(macro_f1),
        precision=float(precision),
        recall=float(recall),
        f1=float(binary_f1),
        fpr=float(fpr),
        fnr=float(fnr),
        roc_auc=float(roc_auc) if roc_auc is not None else None,
        pr_auc=float(pr_auc) if pr_auc is not None else None,
        tn=int(tn),
        fp=int(fp),
        fn=int(fn),
        tp=int(tp),
        ci_95=ci_dict,
    )


def _compute_bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_score: Optional[np.ndarray],
    n_resamples: int = 1000,
    seed: int = 42,
) -> Dict[str, Tuple[float, float]]:
    """Compute empirical percentile 95% bootstrap confidence intervals."""
    rng = np.random.default_rng(seed)
    n = len(y_true)

    boot_metrics: Dict[str, list] = {
        "balanced_accuracy": [],
        "macro_f1": [],
        "precision": [],
        "recall": [],
        "f1": [],
        "fpr": [],
        "fnr": [],
    }
    if y_score is not None:
        boot_metrics["roc_auc"] = []
        boot_metrics["pr_auc"] = []

    for _ in range(n_resamples):
        indices = rng.integers(0, n, size=n)
        b_true = y_true[indices]
        b_pred = y_pred[indices]

        # Ensure both classes exist in resample to avoid metric failures
        if len(np.unique(b_true)) < 2:
            continue

        cm = confusion_matrix(b_true, b_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        boot_metrics["balanced_accuracy"].append(balanced_accuracy_score(b_true, b_pred))
        boot_metrics["macro_f1"].append(f1_score(b_true, b_pred, average="macro"))
        boot_metrics["precision"].append(precision_score(b_true, b_pred, zero_division=0))
        boot_metrics["recall"].append(recall_score(b_true, b_pred, zero_division=0))
        boot_metrics["f1"].append(f1_score(b_true, b_pred, zero_division=0))
        boot_metrics["fpr"].append(fp / (fp + tn) if (fp + tn) > 0 else 0.0)
        boot_metrics["fnr"].append(fn / (fn + tp) if (fn + tp) > 0 else 0.0)

        if y_score is not None:
            b_score = y_score[indices]
            try:
                boot_metrics["roc_auc"].append(roc_auc_score(b_true, b_score))
                boot_metrics["pr_auc"].append(average_precision_score(b_true, b_score))
            except ValueError:
                pass

    ci_res = {}
    for metric_name, vals in boot_metrics.items():
        if len(vals) > 0:
            low = float(np.percentile(vals, 2.5))
            high = float(np.percentile(vals, 97.5))
            ci_res[metric_name] = (low, high)

    return ci_res
