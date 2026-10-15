"""Ensemble and stacking classifier for ransomware detection (T-P10-01).

Combines complementary architectures:
- Logistic Regression (L2): linear, well-calibrated, robust under concept drift
- LightGBM: gradient boosted decision trees capturing non-linear interactions
- Random Forest: bagged decision trees providing variance reduction

Uses out-of-fold stacking meta-learner to prevent label leakage.
Evaluates performance gains and temporal robustness across submission years.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.eval.metrics import ClassificationMetrics, compute_metrics


class StackingRansomwareClassifier(BaseEstimator, ClassifierMixin):
    """Stacking ensemble combining linear (LR) and tree-based (LightGBM, RF) models.

    Uses out-of-fold cross-validation predictions to train a meta-learner,
    preventing over-fitting and maintaining temporal discipline.
    """

    def __init__(
        self,
        c_lr: float = 1.0,
        n_estimators_lgb: int = 100,
        n_estimators_rf: int = 100,
        meta_c: float = 1.0,
        n_splits: int = 5,
        random_state: int = 42,
    ):
        self.c_lr = c_lr
        self.n_estimators_lgb = n_estimators_lgb
        self.n_estimators_rf = n_estimators_rf
        self.meta_c = meta_c
        self.n_splits = n_splits
        self.random_state = random_state

        self.lr_base: Optional[Pipeline] = None
        self.lgb_base: Optional[lgb.LGBMClassifier] = None
        self.rf_base: Optional[RandomForestClassifier] = None
        self.meta_learner: Optional[LogisticRegression] = None
        self.classes_: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> StackingRansomwareClassifier:
        """Fit base models and train meta-learner on out-of-fold predictions."""
        X_arr = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.int64)
        self.classes_ = np.unique(y_arr)

        # 1. Initialize base estimators
        self.lr_base = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=self.c_lr, max_iter=1000, random_state=self.random_state)),
        ])
        self.lgb_base = lgb.LGBMClassifier(
            n_estimators=self.n_estimators_lgb,
            learning_rate=0.05,
            max_depth=5,
            random_state=self.random_state,
            verbose=-1,
            n_jobs=1,
        )
        self.rf_base = RandomForestClassifier(
            n_estimators=self.n_estimators_rf,
            max_depth=12,
            random_state=self.random_state,
            n_jobs=1,
        )

        # 2. Generate out-of-fold predictions for meta-learner training
        cv = KFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        oof_lr = cross_val_predict(self.lr_base, X_arr, y_arr, cv=cv, method="predict_proba")[:, 1]
        oof_lgb = cross_val_predict(self.lgb_base, X_arr, y_arr, cv=cv, method="predict_proba")[:, 1]
        oof_rf = cross_val_predict(self.rf_base, X_arr, y_arr, cv=cv, method="predict_proba")[:, 1]

        meta_X = np.column_stack([oof_lr, oof_lgb, oof_rf])

        # 3. Fit meta-learner on OOF predictions
        self.meta_learner = LogisticRegression(
            C=self.meta_c,
            max_iter=1000,
            random_state=self.random_state,
        )
        self.meta_learner.fit(meta_X, y_arr)

        # 4. Refit all base models on full training data
        self.lr_base.fit(X_arr, y_arr)
        self.lgb_base.fit(X_arr, y_arr)
        self.rf_base.fit(X_arr, y_arr)

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities via stacked meta-learner."""
        X_arr = np.asarray(X, dtype=np.float64)
        p_lr = self.lr_base.predict_proba(X_arr)[:, 1]
        p_lgb = self.lgb_base.predict_proba(X_arr)[:, 1]
        p_rf = self.rf_base.predict_proba(X_arr)[:, 1]

        meta_X = np.column_stack([p_lr, p_lgb, p_rf])
        return self.meta_learner.predict_proba(meta_X)

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Predict binary class label using decision threshold."""
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(np.int64)

    def get_meta_weights(self) -> Dict[str, float]:
        """Return the linear weights assigned by meta-learner to each base model."""
        if self.meta_learner is None:
            return {}
        coefs = self.meta_learner.coef_[0]
        return {
            "weight_lr": float(coefs[0]),
            "weight_lgb": float(coefs[1]),
            "weight_rf": float(coefs[2]),
            "intercept": float(self.meta_learner.intercept_[0]),
        }


def evaluate_ensemble_drift(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    test_dates: pd.Series,
    random_state: int = 42,
) -> pd.DataFrame:
    """Evaluate ensemble vs standalone models across submission years (concept drift)."""
    # 1. Fit individual models
    lr = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=random_state)),
    ])
    lgb_clf = lgb.LGBMClassifier(n_estimators=100, learning_rate=0.05, random_state=random_state, verbose=-1, n_jobs=1)
    ensemble = StackingRansomwareClassifier(random_state=random_state)

    lr.fit(X_train, y_train)
    lgb_clf.fit(X_train, y_train)
    ensemble.fit(X_train, y_train)

    years = pd.to_datetime(test_dates, errors="coerce").dt.year
    unique_years = sorted([y for y in years.dropna().unique() if y >= 2020])

    rows = []
    for yr in unique_years + ["Overall"]:
        if yr == "Overall":
            mask = np.ones(len(y_test), dtype=bool)
            label = "Overall Test"
        else:
            mask = (years == yr).values
            label = f"Year {int(yr)}"

        if mask.sum() < 5:
            continue

        X_slice = X_test[mask]
        y_slice = y_test[mask]

        m_lr = compute_metrics(y_slice, lr.predict(X_slice), lr.predict_proba(X_slice)[:, 1])
        m_lgb = compute_metrics(y_slice, lgb_clf.predict(X_slice), lgb_clf.predict_proba(X_slice)[:, 1])
        m_ens = compute_metrics(y_slice, ensemble.predict(X_slice), ensemble.predict_proba(X_slice)[:, 1])

        rows.append({
            "Slice": label,
            "N": int(mask.sum()),
            "LR BalAcc": f"{m_lr.balanced_accuracy*100:.2f}%",
            "LGBM BalAcc": f"{m_lgb.balanced_accuracy*100:.2f}%",
            "Ensemble BalAcc": f"{m_ens.balanced_accuracy*100:.2f}%",
            "LR FPR": f"{m_lr.fpr*100:.2f}%",
            "LGBM FPR": f"{m_lgb.fpr*100:.2f}%",
            "Ensemble FPR": f"{m_ens.fpr*100:.2f}%",
            "Ensemble Macro-F1": f"{m_ens.macro_f1:.4f}",
        })

    return pd.DataFrame(rows)
