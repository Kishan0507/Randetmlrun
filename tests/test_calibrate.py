"""Unit tests for probability calibration and threshold selection (T-P2-02)."""

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression

from src.models.calibrate import (
    CalibratedModelWrapper,
    evaluate_calibration,
    find_operating_threshold,
)


def test_find_operating_threshold_guarantees_budget():
    rng = np.random.default_rng(42)
    y_true = np.array([0] * 500 + [1] * 500)
    # Predicted probabilities with some noise
    y_prob = np.concatenate([
        rng.beta(1, 9, size=500),  # Goodware centered near 0.1
        rng.beta(9, 1, size=500),  # Ransomware centered near 0.9
    ])

    op_1pct = find_operating_threshold(y_true, y_prob, fpr_budget=0.01)
    assert op_1pct.empirical_fpr <= 0.01
    assert op_1pct.empirical_recall > 0.80

    op_5pct = find_operating_threshold(y_true, y_prob, fpr_budget=0.05)
    assert op_5pct.empirical_fpr <= 0.05
    assert op_5pct.threshold <= op_1pct.threshold
    assert op_5pct.empirical_recall >= op_1pct.empirical_recall


def test_evaluate_calibration_metrics():
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9])

    res = evaluate_calibration(y_true, y_prob, n_bins=2)
    assert "brier_score" in res
    assert "ece" in res
    assert 0.0 <= res["brier_score"] <= 1.0
    assert 0.0 <= res["ece"] <= 1.0


def test_calibrated_model_wrapper():
    rng = np.random.default_rng(42)
    X = rng.standard_normal((100, 10))
    y = rng.integers(0, 2, size=100)

    clf = LogisticRegression(solver="liblinear", random_state=42)
    clf.fit(X[:60], y[:60])

    wrapper = CalibratedModelWrapper(clf, method="sigmoid")
    wrapper.fit_calibration(X[60:80], y[60:80])

    probs = wrapper.predict_proba(X[80:])
    assert probs.shape == (20, 2)
    assert np.all((probs >= 0.0) & (probs <= 1.0))
    assert np.allclose(probs.sum(axis=1), 1.0)

    preds = wrapper.predict(X[80:], threshold=0.6)
    assert len(preds) == 20
