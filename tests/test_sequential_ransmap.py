"""Unit tests for RanSMAP sequential feature augmentation (T-P5-04)."""

from pathlib import Path
import numpy as np
import pytest

from src.data.ransmap import (
    build_windowed_dataset,
    discover_executions,
    fit_entropy_threshold,
)
from src.features.sequential_ransmap import (
    SEQUENTIAL_EXTRA_FEATURE_NAMES,
    build_sequential_dataset,
)


def test_build_sequential_dataset():
    data_dir = Path("data/raw/ransmap")
    if not data_dir.exists():
        pytest.skip("data/raw/ransmap not found")

    execs = discover_executions(data_dir)
    if not execs:
        pytest.skip("No executions discovered")

    threshold = fit_entropy_threshold(execs, percentile=90.0)
    static_dataset = build_windowed_dataset(
        execs,
        window_sec=2.0,
        stride_sec=1.0,
        entropy_threshold=threshold,
    )

    seq_dataset = build_sequential_dataset(static_dataset)

    # Check shapes
    assert seq_dataset.X.shape[0] == static_dataset.X.shape[0]
    expected_dim = static_dataset.X.shape[1] + len(SEQUENTIAL_EXTRA_FEATURE_NAMES)
    assert seq_dataset.X.shape[1] == expected_dim
    assert len(seq_dataset.feature_names) == expected_dim

    # Check finite values
    assert np.isfinite(seq_dataset.X).all()

    # Verify execution boundary resets:
    # For every execution, the first window must have lag-1 = 0
    idx_lag1 = seq_dataset.feature_names.index("delta_entropy_mean_lag1")
    unique_exec_ids = np.unique(seq_dataset.execution_ids)

    for ex_id in unique_exec_ids:
        indices = np.where(seq_dataset.execution_ids == ex_id)[0]
        # First window of this execution
        first_idx = indices[0]
        assert seq_dataset.X[first_idx, idx_lag1] == 0.0
