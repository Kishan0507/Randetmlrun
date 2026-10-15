"""Unit tests for window classifiers (T-P4-03) and streaming early detection (T-P4-04)."""

import numpy as np
import pytest

from src.data.ransmap import WindowedDataset, WINDOW_FEATURE_NAMES, Execution
from src.models.window_classifier import (
    make_window_pipeline,
    evaluate_window_cv,
    evaluate_family_held_out,
    extract_feature_importances,
)
from src.eval.streaming import (
    apply_streaming_rule,
    evaluate_execution_stream,
    evaluate_streaming_system,
)


@pytest.fixture
def synthetic_windowed_dataset():
    """Create a small synthetic WindowedDataset for unit testing."""
    rng = np.random.RandomState(42)
    n_windows = 100
    n_features = len(WINDOW_FEATURE_NAMES)
    X = rng.randn(n_windows, n_features)

    # 4 executions: 2 ransomware (Conti, LockBit), 2 benign (AESCrypt, Firefox)
    exec_ids = []
    families = []
    y_binary = []
    y_detail = []
    times = []

    exec_configs = [
        ("Conti-01", "Conti", 1, 25),
        ("LockBit-01", "LockBit", 1, 25),
        ("AESCrypt-01", "AESCrypt", 0, 25),
        ("Firefox-01", "Firefox", 0, 25),
    ]

    for eid, fam, label, count in exec_configs:
        exec_ids.extend([eid] * count)
        families.extend([fam] * count)
        y_binary.extend([label] * count)
        y_detail.extend([label * 2] * count)
        for i in range(count):
            times.append([float(i), float(i + 2.0)])

    # Inject strong entropy signal for ransomware (feature index 0 is entropy_mean)
    X_mod = X.copy()
    y_arr = np.array(y_binary)
    X_mod[y_arr == 1, 0] += 3.0  # high entropy for ransomware

    return WindowedDataset(
        X=X_mod,
        y_binary=y_arr,
        y_detail=np.array(y_detail),
        execution_ids=np.array(exec_ids),
        window_times=np.array(times),
        families=np.array(families),
        feature_names=WINDOW_FEATURE_NAMES,
    )


def test_window_pipeline_creation():
    pipe_lr = make_window_pipeline("lr")
    assert "scaler" in pipe_lr.named_steps
    assert "clf" in pipe_lr.named_steps

    pipe_lgb = make_window_pipeline("lgbm")
    assert "clf" in pipe_lgb.named_steps


def test_evaluate_window_cv(synthetic_windowed_dataset):
    metrics, oof_probs = evaluate_window_cv(
        synthetic_windowed_dataset, model_type="lr", n_splits=4, seed=42
    )
    assert 0.0 <= metrics.balanced_accuracy <= 1.0
    assert len(oof_probs) == len(synthetic_windowed_dataset.y_binary)
    assert np.all(oof_probs >= 0.0) and np.all(oof_probs <= 1.0)


def test_evaluate_family_held_out(synthetic_windowed_dataset):
    df_held_out = evaluate_family_held_out(
        synthetic_windowed_dataset, model_type="lr", seed=42
    )
    assert len(df_held_out) == 4
    assert set(df_held_out["held_out_family"]) == {"Conti", "LockBit", "AESCrypt", "Firefox"}
    assert "window_detection_rate" in df_held_out.columns


def test_feature_importances(synthetic_windowed_dataset):
    pipe = make_window_pipeline("lr", seed=42)
    pipe.fit(synthetic_windowed_dataset.X, synthetic_windowed_dataset.y_binary)
    df_imp = extract_feature_importances(pipe, synthetic_windowed_dataset.feature_names)
    assert len(df_imp) == len(WINDOW_FEATURE_NAMES)
    # The first feature (entropy_mean) was augmented and should have a high coefficient
    assert df_imp.iloc[0]["feature"] == "entropy_mean"


def test_streaming_rules():
    probs = np.array([0.1, 0.2, 0.8, 0.9, 0.3])

    # Raw rule
    raw_alerts = apply_streaming_rule(probs, rule="raw", threshold=0.7)
    assert np.array_equal(raw_alerts, [False, False, True, True, False])

    # EWMA rule
    ewma_alerts = apply_streaming_rule(probs, rule="ewma", threshold=0.5, alpha=0.5)
    assert isinstance(ewma_alerts, np.ndarray)

    # k-of-n rule (2 of 3 >= 0.7)
    kofn_alerts = apply_streaming_rule(probs, rule="k_of_n", threshold=0.7, k=2, n=3)
    assert kofn_alerts[3] == True  # at idx 3, both idx 2 and 3 are >= 0.7


def test_streaming_evaluation_system():
    ex_ran = Execution(execution_id="Ran-1", family="Conti", label="ransomware", path=None)
    ex_ben = Execution(execution_id="Ben-1", family="Office", label="benign", path=None)

    # 5 windows, times [0, 2], [1, 3], [2, 4], [3, 5], [4, 6]
    times = np.array([[i, i + 2.0] for i in range(5)])
    ran_probs = np.array([0.1, 0.2, 0.9, 0.95, 0.99])
    ben_probs = np.array([0.05, 0.1, 0.05, 0.08, 0.02])

    execution_probs = {
        "Ran-1": (ran_probs, times),
        "Ben-1": (ben_probs, times),
    }

    result = evaluate_streaming_system(
        executions=[ex_ran, ex_ben],
        execution_probs=execution_probs,
        rule="raw",
        threshold=0.5,
        checkpoints=(2, 5, 10),
    )

    assert result.n_ransomware == 1
    assert result.n_detected == 1
    assert result.detection_rate == 1.0
    assert result.censored_count == 0
    assert result.median_ttd_detected == pytest.approx(4.0)  # right edge of window 2 [2, 4]
    assert result.detect_at_t[5] == 1.0
    assert result.detect_at_t[2] == 0.0
    assert result.benign_alerts == 0
    assert result.execution_fpr == 0.0
