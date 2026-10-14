"""Unit tests for leak-free evaluation protocol and test-snooping guard (T-P1-03)."""

import pytest
from sklearn.linear_model import LogisticRegression

from src.data.load_mlran import load_mlran_dataset
from src.eval.protocol import (
    ChronologicalExpandingKFold,
    TestSnoopingGuardError,
    make_leak_free_split,
)


def test_test_snooping_guard():
    ds = load_mlran_dataset()
    split = make_leak_free_split(ds, val_fraction=0.20)

    # Attempting to access test set before unlock must raise TestSnoopingGuardError
    with pytest.raises(TestSnoopingGuardError):
        _ = split.X_test

    with pytest.raises(TestSnoopingGuardError):
        _ = split.y_test

    # Validation and train_sub must be freely accessible
    assert len(split.X_train_sub) + len(split.X_val) == ds.n_train
    assert len(split.y_train_sub) + len(split.y_val) == ds.n_train

    # Unlock works
    split.unlock_test_set()
    assert len(split.X_test) == ds.n_test
    assert len(split.y_test) == ds.n_test


def test_guarded_test_evaluation():
    ds = load_mlran_dataset()
    split = make_leak_free_split(ds, val_fraction=0.20)

    # Fit a simple model on train_sub
    model = LogisticRegression(solver="liblinear", random_state=42)
    model.fit(split.X_train_sub, split.y_train_sub)

    # Evaluate on test via evaluate_test method
    metrics = split.evaluate_test(model, bootstrap_resamples=100)
    assert 0.80 <= metrics.balanced_accuracy <= 1.0
    assert split.test_eval_count == 1
    assert split.test_unlocked is True


def test_chronological_expanding_kfold():
    ds = load_mlran_dataset()
    cv = ChronologicalExpandingKFold(n_splits=3)
    dates = ds.meta_train["first_submission_date_converted"].to_numpy()

    splits = list(cv.split(ds.X_train, dates))
    assert len(splits) == 3

    prev_train_len = 0
    for train_idx, val_idx in splits:
        # Expanding window property: train set grows monotonically
        assert len(train_idx) > prev_train_len
        prev_train_len = len(train_idx)

        # Disjoint fold
        assert len(set(train_idx).intersection(set(val_idx))) == 0

        # Temporal ordering: max date in train <= min date in val
        assert dates[train_idx].max() <= dates[val_idx].min()
