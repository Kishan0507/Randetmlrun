"""Data loading and preprocessing module for MLRan dataset.

Provides access to the 483-feature RFE subset released by Onwuegbuche et al. (JNCA 2026),
along with sample metadata, family labels, type labels, and chronological splits.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class MLRanDataset:
    """Container for the MLRan dataset splits and metadata."""

    X_train: pd.DataFrame
    y_train_binary: pd.Series
    y_train_type: pd.Series
    y_train_family: pd.Series
    meta_train: pd.DataFrame

    X_test: pd.DataFrame
    y_test_binary: pd.Series
    y_test_type: pd.Series
    y_test_family: pd.Series
    meta_test: pd.DataFrame

    feature_names_map: Dict[str, str]
    feature_names: List[str]

    @property
    def n_features(self) -> int:
        return self.X_train.shape[1]

    @property
    def n_train(self) -> int:
        return len(self.X_train)

    @property
    def n_test(self) -> int:
        return len(self.X_test)


def load_feature_names(data_dir: str | Path = "data/raw/mlran") -> Dict[str, str]:
    """Load the mapping from numeric column index to feature name.

    Args:
        data_dir: Directory containing RFE_selected_feature_names_dic.json.

    Returns:
        Dict mapping column index string (e.g. '5') to feature name string
        (e.g. 'API:NtProtectVirtualMemory').
    """
    path = Path(data_dir) / "RFE_selected_feature_names_dic.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_mlran_dataset(
    data_dir: str | Path = "data/raw/mlran",
    rename_features: bool = False,
) -> MLRanDataset:
    """Load the full MLRan train and test sets with labels and metadata.

    Args:
        data_dir: Directory where MLRan raw CSV files and JSON dictionaries reside.
        rename_features: If True, rename feature columns from index strings ('5', '8', ...)
            to their descriptive names ('API:NtProtectVirtualMemory', ...).

    Returns:
        MLRanDataset dataclass containing train/test matrices, labels, and metadata.
    """
    data_path = Path(data_dir)

    train_file = data_path / "MLRan_X_train_RFE.csv"
    test_file = data_path / "MLRan_X_test_RFE.csv"
    meta_file = data_path / "mlran_dataset_metadata.csv"

    if not train_file.exists() or not test_file.exists():
        raise FileNotFoundError(f"MLRan dataset files not found in {data_path.resolve()}")

    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)
    meta_df = pd.read_csv(meta_file)

    meta_df["first_submission_date_converted"] = pd.to_datetime(
        meta_df["first_submission_date_converted"]
    )

    label_cols = ["sample_id", "sample_type", "family_label", "type_label"]
    feature_cols = [c for c in train_df.columns if c not in label_cols]

    feat_names_map = load_feature_names(data_dir)

    train_df = train_df.set_index("sample_id")
    test_df = test_df.set_index("sample_id")
    meta_df = meta_df.set_index("sample_id")

    meta_train = meta_df.loc[train_df.index].copy()
    meta_test = meta_df.loc[test_df.index].copy()

    X_train = train_df[feature_cols].copy()
    y_train_binary = train_df["sample_type"].copy()
    y_train_family = train_df["family_label"].copy()
    y_train_type = train_df["type_label"].copy()

    X_test = test_df[feature_cols].copy()
    y_test_binary = test_df["sample_type"].copy()
    y_test_family = test_df["family_label"].copy()
    y_test_type = test_df["type_label"].copy()

    ordered_feature_names = [feat_names_map[c] for c in feature_cols]

    if rename_features:
        X_train.columns = ordered_feature_names
        X_test.columns = ordered_feature_names

    return MLRanDataset(
        X_train=X_train,
        y_train_binary=y_train_binary,
        y_train_type=y_train_type,
        y_train_family=y_train_family,
        meta_train=meta_train,
        X_test=X_test,
        y_test_binary=y_test_binary,
        y_test_type=y_test_type,
        y_test_family=y_test_family,
        meta_test=meta_test,
        feature_names_map=feat_names_map,
        feature_names=ordered_feature_names,
    )


def get_chronological_val_split(
    meta_train: pd.DataFrame,
    val_fraction: float = 0.20,
) -> Tuple[np.ndarray, np.ndarray]:
    """Split training samples chronologically into a train subset and validation slice.

    Samples are sorted by `first_submission_date_converted` (ascending).
    The earliest `1 - val_fraction` are assigned to train_sub, and the latest
    `val_fraction` are assigned to val.

    Args:
        meta_train: Metadata dataframe for training samples, indexed by sample_id.
        val_fraction: Fraction of training samples to allocate to validation (default 0.20).

    Returns:
        (train_idx, val_idx) as numpy arrays of sample_id values.
    """
    if "first_submission_date_converted" not in meta_train.columns:
        raise ValueError("Metadata must contain 'first_submission_date_converted' column")

    sorted_meta = meta_train.sort_values(
        by=["first_submission_date_converted", "sample_id"],
        ascending=True,
    )

    n_total = len(sorted_meta)
    n_val = int(np.round(n_total * val_fraction))
    n_train_sub = n_total - n_val

    train_ids = sorted_meta.index[:n_train_sub].to_numpy()
    val_ids = sorted_meta.index[n_train_sub:].to_numpy()

    return train_ids, val_ids
