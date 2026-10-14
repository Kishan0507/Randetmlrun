"""Unit tests for evaluation metrics suite (T-P1-05)."""

import numpy as np
import pytest

from src.eval.metrics import compute_metrics


def test_perfect_predictions():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_pred = np.array([0, 0, 0, 1, 1, 1])
    y_score = np.array([0.1, 0.2, 0.05, 0.9, 0.85, 0.95])

    m = compute_metrics(y_true, y_pred, y_score, bootstrap_resamples=100)

    assert m.balanced_accuracy == 1.0
    assert m.macro_f1 == 1.0
    assert m.precision == 1.0
    assert m.recall == 1.0
    assert m.f1 == 1.0
    assert m.fpr == 0.0
    assert m.fnr == 0.0
    assert m.roc_auc == 1.0
    assert m.pr_auc == 1.0
    assert m.tn == 3
    assert m.fp == 0
    assert m.fn == 0
    assert m.tp == 3
    assert m.ci_95 is not None
    assert "balanced_accuracy" in m.ci_95


def test_known_confusion_matrix():
    # 498 TN, 12 FP, 6 FN, 459 TP (from paper Fig 12)
    y_true = np.array([0] * 510 + [1] * 465)
    y_pred = np.array([0] * 498 + [1] * 12 + [0] * 6 + [1] * 459)

    m = compute_metrics(y_true, y_pred, bootstrap_resamples=0)

    assert m.tn == 498
    assert m.fp == 12
    assert m.fn == 6
    assert m.tp == 459

    expected_fpr = 12 / 510
    expected_fnr = 6 / 465
    expected_recall = 459 / 465
    expected_prec = 459 / (459 + 12)
    expected_bal_acc = (498 / 510 + 459 / 465) / 2

    assert abs(m.fpr - expected_fpr) < 1e-6
    assert abs(m.fnr - expected_fnr) < 1e-6
    assert abs(m.recall - expected_recall) < 1e-6
    assert abs(m.precision - expected_prec) < 1e-6
    assert abs(m.balanced_accuracy - expected_bal_acc) < 1e-6


def test_bootstrap_ci_coverage():
    rng = np.random.default_rng(42)
    y_true = rng.integers(0, 2, size=200)
    y_pred = y_true.copy()
    # Flip 10% predictions to introduce noise
    flip_idx = rng.choice(200, size=20, replace=False)
    y_pred[flip_idx] = 1 - y_pred[flip_idx]

    m = compute_metrics(y_true, y_pred, bootstrap_resamples=200, seed=42)

    assert m.ci_95 is not None
    low, high = m.ci_95["balanced_accuracy"]
    assert low <= m.balanced_accuracy <= high
    assert 0.0 <= low < high <= 1.0
