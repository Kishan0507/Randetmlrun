"""Leak-free evaluation protocol and test-set access guard.

Enforces temporal discipline:
1. All feature selection, preprocessing, hyperparameter tuning, and decision thresholds
   must be performed on the training set or a chronological validation slice carved from train.
2. The final test set is guarded and can only be evaluated once for the final unbiased report.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.data.load_mlran import MLRanDataset, get_chronological_val_split
from src.eval.metrics import ClassificationMetrics, compute_metrics


class TestSnoopingGuardError(RuntimeError):
    """Raised when the test set is accessed without explicit unlock confirmation."""
    __test__ = False


@dataclass
class EvaluationSplit:
    """Holds train, validation, and guarded test data."""

    X_train_sub: pd.DataFrame
    y_train_sub: pd.Series
    meta_train_sub: pd.DataFrame

    X_val: pd.DataFrame
    y_val: pd.Series
    meta_val: pd.DataFrame

    _X_test: pd.DataFrame
    _y_test: pd.Series
    _meta_test: pd.DataFrame

    test_unlocked: bool = False
    test_eval_count: int = 0

    @property
    def X_test(self) -> pd.DataFrame:
        """Guarded test feature matrix."""
        if not self.test_unlocked:
            raise TestSnoopingGuardError(
                "Accessing test set before model selection and threshold tuning is forbidden! "
                "Call split.unlock_test_set() only after validation is complete."
            )
        return self._X_test

    @property
    def y_test(self) -> pd.Series:
        """Guarded test label series."""
        if not self.test_unlocked:
            raise TestSnoopingGuardError(
                "Accessing test set before model selection and threshold tuning is forbidden! "
                "Call split.unlock_test_set() only after validation is complete."
            )
        return self._y_test

    @property
    def meta_test(self) -> pd.DataFrame:
        """Guarded test metadata."""
        if not self.test_unlocked:
            raise TestSnoopingGuardError(
                "Accessing test set metadata before validation is complete is forbidden!"
            )
        return self._meta_test

    def unlock_test_set(self) -> None:
        """Explicitly unlock the test set for final one-shot evaluation."""
        self.test_unlocked = True

    def evaluate_test(
        self,
        model: Any,
        bootstrap_resamples: int = 1000,
        threshold: float = 0.5,
        seed: int = 42,
    ) -> ClassificationMetrics:
        """Evaluate a model on the test set once with full metrics suite."""
        self.unlock_test_set()
        self.test_eval_count += 1

        y_test_arr = self._y_test.to_numpy()
        X_test_input = self._X_test

        if hasattr(model, "predict_proba"):
            y_score = model.predict_proba(X_test_input)[:, 1]
            y_pred = (y_score >= threshold).astype(int)
        elif hasattr(model, "decision_function"):
            y_score = model.decision_function(X_test_input)
            score_min, score_max = y_score.min(), y_score.max()
            if score_max > score_min:
                y_prob = (y_score - score_min) / (score_max - score_min)
            else:
                y_prob = y_score
            y_pred = (y_score >= 0).astype(int)
            y_score = y_prob
        else:
            y_pred = model.predict(X_test_input)
            y_score = None

        return compute_metrics(
            y_true=y_test_arr,
            y_pred=y_pred,
            y_score=y_score,
            bootstrap_resamples=bootstrap_resamples,
            seed=seed,
        )


def make_leak_free_split(
    dataset: MLRanDataset,
    val_fraction: float = 0.20,
    target: str = "binary",
) -> EvaluationSplit:
    """Create a leak-free temporal evaluation split from a loaded MLRan dataset.

    Args:
        dataset: Loaded MLRanDataset.
        val_fraction: Fraction of train data allocated to validation (default 0.20).
        target: One of 'binary', 'type', or 'family'.

    Returns:
        EvaluationSplit object with guarded test set and chronological validation slice.
    """
    train_ids, val_ids = get_chronological_val_split(
        dataset.meta_train,
        val_fraction=val_fraction,
    )

    if target == "binary":
        y_train = dataset.y_train_binary
        y_test = dataset.y_test_binary
    elif target == "type":
        y_train = dataset.y_train_type
        y_test = dataset.y_test_type
    elif target == "family":
        y_train = dataset.y_train_family
        y_test = dataset.y_test_family
    else:
        raise ValueError(f"Unknown target: {target}")

    return EvaluationSplit(
        X_train_sub=dataset.X_train.loc[train_ids].copy(),
        y_train_sub=y_train.loc[train_ids].copy(),
        meta_train_sub=dataset.meta_train.loc[train_ids].copy(),
        X_val=dataset.X_train.loc[val_ids].copy(),
        y_val=y_train.loc[val_ids].copy(),
        meta_val=dataset.meta_train.loc[val_ids].copy(),
        _X_test=dataset.X_test.copy(),
        _y_test=y_test.copy(),
        _meta_test=dataset.meta_test.copy(),
    )


class ChronologicalExpandingKFold:
    """Expanding-window (rolling-origin) temporal cross-validator.

    Generates strictly temporal train/validation splits on chronologically sorted data:
    Fold 1: train on [0, t1], val on (t1, t2]
    Fold 2: train on [0, t2], val on (t2, t3]
    ...
    """

    def __init__(self, n_splits: int = 4):
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")
        self.n_splits = n_splits

    def split(
        self,
        X: pd.DataFrame | np.ndarray,
        dates: pd.Series | np.ndarray,
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """Generate indices for expanding window cross-validation."""
        n_samples = len(X)
        sorted_indices = np.argsort(dates)

        # Divvy samples into n_splits + 1 equal segments
        segment_size = n_samples // (self.n_splits + 1)

        for i in range(1, self.n_splits + 1):
            train_end = segment_size * i
            val_end = segment_size * (i + 1) if i < self.n_splits else n_samples

            train_idx = sorted_indices[:train_end]
            val_idx = sorted_indices[train_end:val_end]

            yield train_idx, val_idx
