"""Unit tests for stacking ensemble classifier (T-P10-01)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.datasets import make_classification

from src.models.ensemble import (
    StackingRansomwareClassifier,
    evaluate_ensemble_drift,
)


def test_stacking_classifier_fit_predict():
    X, y = make_classification(
        n_samples=200,
        n_features=20,
        n_informative=10,
        random_state=42,
    )

    clf = StackingRansomwareClassifier(n_splits=3, random_state=42)
    clf.fit(X[:150], y[:150])

    probs = clf.predict_proba(X[150:])
    preds = clf.predict(X[150:])

    assert probs.shape == (50, 2)
    assert np.allclose(probs.sum(axis=1), 1.0)
    assert len(preds) == 50
    assert set(preds).issubset({0, 1})

    weights = clf.get_meta_weights()
    assert "weight_lr" in weights
    assert "weight_lgb" in weights
    assert "weight_rf" in weights
    assert np.isfinite(weights["intercept"])


def test_evaluate_ensemble_drift():
    X, y = make_classification(
        n_samples=300,
        n_features=15,
        n_informative=8,
        random_state=42,
    )
    dates = pd.Series(["2021-05-01"] * 50 + ["2022-06-01"] * 50)

    df_drift = evaluate_ensemble_drift(
        X_train=X[:200],
        y_train=y[:200],
        X_test=X[200:],
        y_test=y[200:],
        test_dates=dates,
        random_state=42,
    )

    assert len(df_drift) >= 2
    assert "Ensemble BalAcc" in df_drift.columns
    assert "LR BalAcc" in df_drift.columns
    assert "LGBM BalAcc" in df_drift.columns
