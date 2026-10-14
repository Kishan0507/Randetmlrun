"""Tests for family merge, hierarchical predict, and unknown-threshold helpers."""

import numpy as np
import pandas as pd

from src.models.family import (
    OTHER_LABEL,
    UNKNOWN_LABEL,
    choose_unknown_threshold,
    hierarchical_predict,
    merge_rare_families,
    per_family_recall,
)


def test_merge_rare_families_protects_goodware_and_uses_train_only():
    y_train = pd.Series([0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2])
    y_test = pd.Series([0, 1, 2, 2, 2])
    y_tr, y_te, rare = merge_rare_families(y_train, y_test, min_samples=5)
    assert 2 in rare
    assert 0 not in rare
    assert (y_tr[y_train == 2] == OTHER_LABEL).all()
    assert (y_te[y_test == 2] == OTHER_LABEL).all()
    assert (y_tr[y_train == 0] == 0).all()


def test_hierarchical_predict_overrides_family_when_binary_says_goodware():
    binary = np.array([0, 1, 1, 0])
    family = np.array([7, 3, 4, 9])
    out = hierarchical_predict(binary, family)
    np.testing.assert_array_equal(out, np.array([0, 3, 4, 0]))


def test_choose_unknown_threshold_and_per_family_recall():
    max_prob = np.array([0.2, 0.4, 0.6, 0.8, 1.0])
    tau = choose_unknown_threshold(max_prob, target_known_keep_rate=0.8)
    assert 0.0 <= tau <= 1.0
    y_true = np.array([1, 1, 2, 2])
    y_pred = np.array([1, 0, 2, 2])
    table = per_family_recall(y_true, y_pred)
    rec1 = table.loc[table["family_id"] == 1, "recall"].iloc[0]
    rec2 = table.loc[table["family_id"] == 2, "recall"].iloc[0]
    assert rec1 == 0.5
    assert rec2 == 1.0
    assert UNKNOWN_LABEL == -2
