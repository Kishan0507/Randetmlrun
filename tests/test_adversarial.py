"""Unit tests for feature-space adversarial evasion attacks and hardening (T-P7-02, T-P7-03)."""

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.adversarial.attacks import (
    random_bit_flip_attack,
    benign_padding_attack,
    top_shap_suppression_attack,
    gradient_guided_greedy_attack,
    evaluate_evasion_curve,
    train_adversarial_hardened_model,
)


@pytest.fixture
def mock_dataset_and_model():
    rng = np.random.RandomState(42)
    n_samples, n_features = 100, 30
    X = rng.binomial(1, 0.2, size=(n_samples, n_features)).astype(float)
    y = np.array([1 if i < 50 else 0 for i in range(n_samples)])

    # Inject strong positive weights on features 0, 1
    X[:50, 0] = 1.0
    X[:50, 1] = 1.0

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(random_state=42)),
    ])
    pipe.fit(X, y)

    return X, y, pipe


def test_random_bit_flip_attack():
    X = np.zeros((10, 20))
    X_pert = random_bit_flip_attack(X, budget=3, seed=42)
    # Exactly 3 features per sample should have changed from 0 to 1
    assert (np.sum(X_pert, axis=1) == 3).all()


def test_benign_padding_attack():
    X = np.zeros((5, 10))
    priority = [2, 4, 6, 8]
    X_pert = benign_padding_attack(X, benign_priority_indices=priority, budget=2)
    # Features 2 and 4 should be 1
    assert (X_pert[:, 2] == 1.0).all()
    assert (X_pert[:, 4] == 1.0).all()
    assert (X_pert[:, 6] == 0.0).all()


def test_top_shap_suppression_attack():
    X = np.ones((5, 10))
    priority = [1, 3, 5]
    X_pert = top_shap_suppression_attack(X, malicious_priority_indices=priority, budget=2)
    # Features 1 and 3 should be 0
    assert (X_pert[:, 1] == 0.0).all()
    assert (X_pert[:, 3] == 0.0).all()
    assert (X_pert[:, 5] == 1.0).all()


def test_gradient_guided_greedy_attack(mock_dataset_and_model):
    X, y, model = mock_dataset_and_model
    X_ran = X[:50]
    X_pert = gradient_guided_greedy_attack(X_ran, budget=3, target_model=model)
    assert X_pert.shape == X_ran.shape
    # Log-odds probability of perturbed samples should be <= original
    probs_orig = model.predict_proba(X_ran)[:, 1]
    probs_pert = model.predict_proba(X_pert)[:, 1]
    assert np.mean(probs_pert) <= np.mean(probs_orig)


def test_evaluate_evasion_curve(mock_dataset_and_model):
    X, y, model = mock_dataset_and_model
    X_ran = X[:50]
    df_curve = evaluate_evasion_curve(
        model, X_ran, random_bit_flip_attack, budgets=[1, 2, 5], threshold=0.5
    )
    assert len(df_curve) == 4  # budget 0, 1, 2, 5
    assert "evasion_rate" in df_curve.columns


def test_train_adversarial_hardened_model(mock_dataset_and_model):
    X, y, model = mock_dataset_and_model
    hardened = train_adversarial_hardened_model(X, y, seed=42, augment_fraction=0.3)
    assert hasattr(hardened, "predict")
    clean_preds = hardened.predict(X)
    assert len(clean_preds) == len(y)
