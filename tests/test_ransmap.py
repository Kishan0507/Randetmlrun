"""Unit tests for RanSMAP data loader, windowing, and execution-level split (T-P4-02)."""

from pathlib import Path
import numpy as np
import pytest

from src.data.ransmap import (
    Execution,
    discover_executions,
    load_ata_write,
    create_windows,
    extract_window_features,
    fit_entropy_threshold,
    build_windowed_dataset,
    split_by_execution,
    WINDOW_FEATURE_NAMES,
)


def test_discover_executions():
    data_dir = Path("data/raw/ransmap")
    if not data_dir.exists():
        pytest.skip("data/raw/ransmap not found")

    execs = discover_executions(data_dir)
    assert len(execs) > 0
    # Check that discovered executions have valid attributes
    for ex in execs:
        assert ex.family in {"Conti", "Darkside", "LockBit", "REvil", "Ryuk", "WannaCry", "AESCrypt", "Firefox", "Idle", "Office", "SDelete", "Zip"}
        assert ex.label in {"ransomware", "benign"}
        assert (ex.path / "ata_write.csv").exists()


def test_load_ata_write():
    data_dir = Path("data/raw/ransmap")
    if not data_dir.exists():
        pytest.skip("data/raw/ransmap not found")

    execs = discover_executions(data_dir)
    if not execs:
        pytest.skip("No executions discovered")

    ex = execs[0]
    df = load_ata_write(ex)
    assert len(df) > 0
    assert "rel_time" in df.columns
    assert "lba" in df.columns
    assert "entropy" in df.columns
    # First timestamp should be relative 0.0
    assert df["rel_time"].iloc[0] == pytest.approx(0.0, abs=1e-6)
    # Timestamps should be non-decreasing
    assert (df["rel_time"].diff().dropna() >= -1e-6).all()


def test_windowing_and_features():
    data_dir = Path("data/raw/ransmap")
    if not data_dir.exists():
        pytest.skip("data/raw/ransmap not found")

    execs = discover_executions(data_dir)
    if not execs:
        pytest.skip("No executions discovered")

    ex = execs[0]
    if ex.ata_write is None:
        load_ata_write(ex)

    features, y_bin, y_det, times = create_windows(
        ex, window_sec=2.0, stride_sec=1.0, entropy_threshold=0.85
    )

    assert len(features) == len(y_bin) == len(y_det) == len(times)
    if len(features) > 0:
        assert features.shape[1] == len(WINDOW_FEATURE_NAMES)
        assert times.shape[1] == 2
        # Check window end - start == window_sec
        assert np.allclose(times[:, 1] - times[:, 0], 2.0)
        # All feature values should be finite
        assert np.isfinite(features).all()


def test_split_by_execution_leak_free():
    data_dir = Path("data/raw/ransmap")
    if not data_dir.exists():
        pytest.skip("data/raw/ransmap not found")

    execs = discover_executions(data_dir)
    if len(execs) < 2:
        pytest.skip("Need at least 2 executions to test split")

    train, test = split_by_execution(execs, test_fraction=0.3, seed=42)

    train_ids = {e.execution_id for e in train}
    test_ids = {e.execution_id for e in test}

    # Strict leak-free guarantee: no execution in both train and test
    assert train_ids.isdisjoint(test_ids)
    assert len(train) + len(test) == len(execs)
