"""Unit tests for MLRan data loader (T-P0-06)."""

import numpy as np
import pytest

from src.data.load_mlran import (
    get_chronological_val_split,
    load_feature_names,
    load_mlran_dataset,
)


def test_load_feature_names():
    feat_names = load_feature_names()
    assert isinstance(feat_names, dict)
    assert len(feat_names) == 483
    # Check that keys are numeric strings and values are prefixed feature names
    for k, v in feat_names.items():
        assert k.isdigit()
        assert isinstance(v, str)
        assert len(v) > 0


def test_load_mlran_dataset_shapes_and_counts():
    ds = load_mlran_dataset()

    # Exact expected row and column shapes
    assert ds.n_train == 3905
    assert ds.n_test == 975
    assert ds.n_features == 483
    assert ds.X_train.shape == (3905, 483)
    assert ds.X_test.shape == (975, 483)

    # Class counts match paper: 2040/1865 train, 510/465 test
    train_counts = ds.y_train_binary.value_counts().to_dict()
    assert train_counts == {0: 2040, 1: 1865}

    test_counts = ds.y_test_binary.value_counts().to_dict()
    assert test_counts == {0: 510, 1: 465}

    # Multiclass labels
    assert ds.y_train_family.nunique() <= 65
    assert ds.y_test_family.nunique() <= 65
    # Combined families should be 65
    total_families = set(ds.y_train_family).union(set(ds.y_test_family))
    assert len(total_families) == 65

    # 5 types: goodware + 4 ransomware types
    total_types = set(ds.y_train_type).union(set(ds.y_test_type))
    assert len(total_types) == 5

    # No null values in feature matrices
    assert ds.X_train.isnull().sum().sum() == 0
    assert ds.X_test.isnull().sum().sum() == 0

    # All features are binary {0, 1}
    assert ((ds.X_train == 0) | (ds.X_train == 1)).all().all()
    assert ((ds.X_test == 0) | (ds.X_test == 1)).all().all()


def test_feature_renaming():
    ds_renamed = load_mlran_dataset(rename_features=True)
    first_col = ds_renamed.X_train.columns[0]
    assert ":" in first_col
    assert first_col == ds_renamed.feature_names[0]


def test_chronological_val_split():
    ds = load_mlran_dataset()
    train_ids, val_ids = get_chronological_val_split(ds.meta_train, val_fraction=0.20)

    # Disjoint and covers train
    assert len(train_ids) + len(val_ids) == 3905
    assert len(set(train_ids).intersection(set(val_ids))) == 0

    # Approx 20% val
    assert abs(len(val_ids) / 3905 - 0.20) < 0.01

    # Date ordering: max date in train_sub <= max date in val
    train_dates = ds.meta_train.loc[train_ids, "first_submission_date_converted"]
    val_dates = ds.meta_train.loc[val_ids, "first_submission_date_converted"]
    assert train_dates.max() <= val_dates.min()
