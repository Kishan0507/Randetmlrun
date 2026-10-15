"""Unit tests for active-learning loop and model retraining (T-P10-02)."""

import numpy as np
import pytest
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression

from src.models.active_learning import (
    ActiveLearningLoop,
    AnalystFeedback,
    RetrainingResult,
    UncertaintySampler,
)


def test_uncertainty_sampler():
    probs = np.array([0.95, 0.51, 0.10, 0.49, 0.88, 0.50])
    # Distances to 0.5: [0.45, 0.01, 0.40, 0.01, 0.38, 0.00]
    # Top 3 closest to 0.5 should be indices 5 (0.50), 1 or 3 (0.51 / 0.49)
    top_3 = UncertaintySampler.rank_by_uncertainty(probs, top_k=3)
    assert len(top_3) == 3
    assert set(top_3) == {1, 3, 5}


def test_active_learning_retraining_promotion():
    X, y = make_classification(
        n_samples=200,
        n_features=10,
        n_informative=6,
        random_state=42,
    )
    X_train, y_train = X[:120], y[:120]
    X_val, y_val = X[120:], y[120:]

    base_model = LogisticRegression(random_state=42)
    base_model.fit(X_train, y_train)

    loop = ActiveLearningLoop(base_model=base_model, feedback_weight=5.0, promotion_threshold=0.0)

    # Empty feedback case
    res_empty = loop.retrain_candidate(X_train, y_train, X_val, y_val)
    assert res_empty.status == "REJECTED"

    # Add 5 analyst feedback samples with ground truth labels
    for i in range(5):
        loop.add_feedback(
            sample_id=f"alert_{i}",
            feature_vector=X_val[i],
            original_verdict="ransomware" if y_val[i] == 0 else "goodware",
            original_prob=0.55,
            corrected_label=y_val[i],
            analyst_notes="Correction from threat response analyst",
        )

    res = loop.retrain_candidate(X_train, y_train, X_val, y_val)
    assert res.feedback_samples_used == 5
    assert res.status in {"PROMOTED", "REJECTED"}
    assert isinstance(res.recommendation, str)
    assert np.isfinite(res.candidate_bal_acc)
