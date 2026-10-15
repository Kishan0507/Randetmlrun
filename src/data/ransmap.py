"""RanSMAP time-series data loader and windowing module (T-P4-02).

Loads RanSMAP execution data (ATA write CSVs), creates fixed-width time
windows, extracts per-window features, and labels windows according to
the early-detection protocol (D-004, docs/early_detection_protocol.md).

Key design decisions:
  - Unit of analysis: execution (windows never split across train/test)
  - AESCrypt is BENIGN (encrypts legitimately, per D-004 §3)
  - Entropy threshold for pre-encryption vs encryption is fit on train only
  - Group split by family/app, not random, to test generalisation

CSV format (no header):
  col0: timestamp_sec  (Unix epoch seconds)
  col1: timestamp_ns   (nanoseconds within that second)
  col2: LBA            (Logical Block Address)
  col3: size           (bytes, typically 4096)
  col4: entropy        (float 0–1, critical for encryption detection)
  col5: access_type    (int flag)
"""

from __future__ import annotations

import csv
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# ─── Label constants ─────────────────────────────────────────────────────────
LABEL_BENIGN = "benign"
LABEL_PRE_ENCRYPTION = "pre-encryption"
LABEL_ENCRYPTION = "encryption"

# Family → class mapping (per D-002)
RANSOMWARE_FAMILIES = {"Conti", "Darkside", "LockBit", "REvil", "Ryuk", "WannaCry"}
BENIGN_APPS = {"AESCrypt", "Firefox", "Idle", "Office", "SDelete", "Zip"}

# Column names for the headerless CSVs
ATA_COLUMNS = [
    "timestamp_sec",
    "timestamp_ns",
    "lba",
    "size",
    "entropy",
    "access_type",
]


# ─── Data containers ─────────────────────────────────────────────────────────
@dataclass
class Execution:
    """One RanSMAP execution (one folder of CSVs)."""

    execution_id: str  # e.g. "Conti-20221006_14-20-16"
    family: str  # e.g. "Conti"
    label: str  # "ransomware" or "benign"
    path: Path
    ata_write: Optional[pd.DataFrame] = None  # loaded lazily

    @property
    def is_ransomware(self) -> bool:
        return self.label == "ransomware"


@dataclass
class WindowedDataset:
    """Collection of windowed features from multiple executions."""

    X: np.ndarray  # shape (n_windows, n_features)
    y_binary: np.ndarray  # 1 = ransomware window, 0 = benign
    y_detail: np.ndarray  # 0=benign, 1=pre-encryption, 2=encryption
    execution_ids: np.ndarray  # which execution each window belongs to
    window_times: np.ndarray  # (n_windows, 2) start_sec, end_sec relative
    families: np.ndarray  # family name per window
    feature_names: List[str] = field(default_factory=list)


# ─── Execution discovery ─────────────────────────────────────────────────────
def discover_executions(data_dir: str | Path = "data/raw/ransmap") -> List[Execution]:
    """Discover all downloaded RanSMAP executions.

    Expected layout:
        data_dir/<Family>/<Family-timestamp>/ata_write.csv

    Returns:
        List of Execution objects (data not yet loaded).
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"RanSMAP data directory not found: {data_path}")

    executions = []
    for family_dir in sorted(data_path.iterdir()):
        if not family_dir.is_dir() or family_dir.name.startswith("."):
            continue
        family = family_dir.name

        if family in RANSOMWARE_FAMILIES:
            label = "ransomware"
        elif family in BENIGN_APPS:
            label = "benign"
        else:
            warnings.warn(f"Unknown family '{family}', skipping")
            continue

        for exec_dir in sorted(family_dir.iterdir()):
            if not exec_dir.is_dir():
                continue
            ata_write = exec_dir / "ata_write.csv"
            if not ata_write.exists():
                continue
            executions.append(
                Execution(
                    execution_id=exec_dir.name,
                    family=family,
                    label=label,
                    path=exec_dir,
                )
            )

    return executions


# ─── Loading raw data ─────────────────────────────────────────────────────────
def load_ata_write(execution: Execution) -> pd.DataFrame:
    """Load the ata_write.csv for an execution.

    Normalises timestamps to start at 0 (relative seconds from execution start).

    Returns:
        DataFrame with columns: rel_time, lba, size, entropy, access_type
    """
    csv_path = execution.path / "ata_write.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"ata_write.csv not found in {execution.path}")

    df = pd.read_csv(
        csv_path,
        header=None,
        names=ATA_COLUMNS,
        on_bad_lines="skip",
    )
    # Drop any rows with NaN (e.g. truncated last line from max_bytes download)
    df = df.dropna()
    for col in ["timestamp_sec", "timestamp_ns", "lba", "size", "access_type"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["entropy"] = pd.to_numeric(df["entropy"], errors="coerce")
    df = df.dropna()

    if len(df) == 0:
        execution.ata_write = pd.DataFrame(columns=["rel_time", "lba", "size", "entropy", "access_type"])
        return execution.ata_write

    df["timestamp_sec"] = df["timestamp_sec"].astype(np.int64)
    df["timestamp_ns"] = df["timestamp_ns"].astype(np.int64)
    df["lba"] = df["lba"].astype(np.int64)
    df["size"] = df["size"].astype(np.int64)
    df["access_type"] = df["access_type"].astype(np.int64)

    # Compute relative time in seconds (float, sub-second precision)
    t0_sec = df["timestamp_sec"].iloc[0]
    t0_ns = df["timestamp_ns"].iloc[0]
    df["rel_time"] = (
        (df["timestamp_sec"] - t0_sec).astype(np.float64)
        + (df["timestamp_ns"] - t0_ns).astype(np.float64) * 1e-9
    )

    # Drop raw timestamp columns
    df = df[["rel_time", "lba", "size", "entropy", "access_type"]].copy()

    execution.ata_write = df
    return df


# ─── Window features ─────────────────────────────────────────────────────────
WINDOW_FEATURE_NAMES = [
    # Entropy statistics (primary signal for encryption detection)
    "entropy_mean",
    "entropy_std",
    "entropy_max",
    "entropy_min",
    "entropy_median",
    "entropy_q25",
    "entropy_q75",
    "entropy_iqr",
    "entropy_skew",
    "entropy_high_frac",  # fraction of writes with entropy > 0.9
    # Volume statistics
    "write_count",
    "write_bytes_total",
    "write_bytes_mean",
    "write_rate",  # writes per second
    # Address (LBA) statistics — spatial locality
    "lba_unique_count",
    "lba_range",
    "lba_std",
    "lba_sequential_frac",  # fraction of consecutive writes to adjacent LBAs
    # Temporal statistics
    "inter_write_time_mean",
    "inter_write_time_std",
    "burst_count",  # number of bursts (gaps > 0.1s between writes)
]


def extract_window_features(window_df: pd.DataFrame, window_duration: float) -> np.ndarray:
    """Extract feature vector from a single window of ATA write data.

    Args:
        window_df: DataFrame subset for this window (rel_time, lba, size, entropy, access_type)
        window_duration: Duration of the window in seconds

    Returns:
        1D numpy array of features (length = len(WINDOW_FEATURE_NAMES))
    """
    n = len(window_df)

    if n == 0:
        return np.zeros(len(WINDOW_FEATURE_NAMES), dtype=np.float64)

    ent = window_df["entropy"].values
    lba = window_df["lba"].values
    sizes = window_df["size"].values
    times = window_df["rel_time"].values

    # Entropy statistics
    entropy_mean = np.mean(ent)
    entropy_std = np.std(ent) if n > 1 else 0.0
    entropy_max = np.max(ent)
    entropy_min = np.min(ent)
    entropy_median = np.median(ent)
    entropy_q25 = np.percentile(ent, 25) if n > 1 else entropy_median
    entropy_q75 = np.percentile(ent, 75) if n > 1 else entropy_median
    entropy_iqr = entropy_q75 - entropy_q25
    if n > 2 and entropy_std > 0:
        entropy_skew = float(
            np.mean(((ent - entropy_mean) / entropy_std) ** 3)
        )
    else:
        entropy_skew = 0.0
    entropy_high_frac = np.mean(ent > 0.9) if n > 0 else 0.0

    # Volume statistics
    write_count = float(n)
    write_bytes_total = float(np.sum(sizes))
    write_bytes_mean = float(np.mean(sizes))
    write_rate = n / window_duration if window_duration > 0 else 0.0

    # LBA statistics
    lba_unique_count = float(len(np.unique(lba)))
    lba_range = float(np.max(lba) - np.min(lba)) if n > 1 else 0.0
    lba_std = float(np.std(lba)) if n > 1 else 0.0
    if n > 1:
        lba_diffs = np.abs(np.diff(lba))
        # Sequential = diff is exactly 1 sector (or within size/512 range)
        lba_sequential_frac = float(np.mean(lba_diffs <= 8))
    else:
        lba_sequential_frac = 0.0

    # Temporal statistics
    if n > 1:
        inter_times = np.diff(times)
        inter_write_time_mean = float(np.mean(inter_times))
        inter_write_time_std = float(np.std(inter_times))
        burst_count = float(np.sum(inter_times > 0.1))
    else:
        inter_write_time_mean = 0.0
        inter_write_time_std = 0.0
        burst_count = 0.0

    return np.array(
        [
            entropy_mean,
            entropy_std,
            entropy_max,
            entropy_min,
            entropy_median,
            entropy_q25,
            entropy_q75,
            entropy_iqr,
            entropy_skew,
            entropy_high_frac,
            write_count,
            write_bytes_total,
            write_bytes_mean,
            write_rate,
            lba_unique_count,
            lba_range,
            lba_std,
            lba_sequential_frac,
            inter_write_time_mean,
            inter_write_time_std,
            burst_count,
        ],
        dtype=np.float64,
    )


# ─── Windowing ───────────────────────────────────────────────────────────────
def create_windows(
    execution: Execution,
    window_sec: float = 2.0,
    stride_sec: float = 1.0,
    entropy_threshold: float = 0.9,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create fixed-width time windows from a single execution.

    Args:
        execution: Execution object (ata_write must be loaded already)
        window_sec: Window duration in seconds (default: 2.0 per D-004)
        stride_sec: Stride in seconds (default: 1.0 per D-004)
        entropy_threshold: Threshold for encryption labelling (fit on train)

    Returns:
        features:     (n_windows, n_features) window feature matrix
        y_binary:     (n_windows,) 1=ransomware, 0=benign
        y_detail:     (n_windows,) 0=benign, 1=pre-encryption, 2=encryption
        window_times: (n_windows, 2) [start_sec, end_sec] relative to execution
    """
    df = execution.ata_write
    if df is None:
        raise ValueError(f"ata_write not loaded for {execution.execution_id}")

    max_time = df["rel_time"].max()
    if max_time <= 0:
        return (
            np.zeros((0, len(WINDOW_FEATURE_NAMES))),
            np.zeros(0, dtype=np.int64),
            np.zeros(0, dtype=np.int64),
            np.zeros((0, 2)),
        )

    # Generate window boundaries
    starts = np.arange(0, max_time - window_sec + stride_sec, stride_sec)
    if len(starts) == 0:
        starts = np.array([0.0])

    features_list = []
    y_binary_list = []
    y_detail_list = []
    window_times_list = []

    # Track whether encryption has been detected (for pre vs during labels)
    encryption_seen = False

    for start in starts:
        end = start + window_sec
        mask = (df["rel_time"] >= start) & (df["rel_time"] < end)
        window_df = df[mask]

        # Extract features
        feats = extract_window_features(window_df, window_sec)
        features_list.append(feats)

        # Window times
        window_times_list.append([start, end])

        # Label assignment (per D-004 §3)
        if not execution.is_ransomware:
            y_binary_list.append(0)
            y_detail_list.append(0)  # benign
        else:
            y_binary_list.append(1)

            # Check if this window has high-entropy writes (encryption indicator)
            if len(window_df) > 0:
                mean_entropy = window_df["entropy"].mean()
                if mean_entropy >= entropy_threshold:
                    encryption_seen = True

            if encryption_seen:
                y_detail_list.append(2)  # encryption (or post-start)
            else:
                y_detail_list.append(1)  # pre-encryption

    return (
        np.array(features_list, dtype=np.float64),
        np.array(y_binary_list, dtype=np.int64),
        np.array(y_detail_list, dtype=np.int64),
        np.array(window_times_list, dtype=np.float64),
    )


# ─── Entropy threshold fitting ───────────────────────────────────────────────
def fit_entropy_threshold(
    executions: List[Execution],
    percentile: float = 95.0,
) -> float:
    """Fit the encryption-detection entropy threshold on training executions.

    Uses the 95th percentile of per-window mean entropy from benign executions
    as the threshold (per D-004 §3: "fit on training ransomware/benign only").

    Args:
        executions: Training executions (must have ata_write loaded)
        percentile: Percentile of benign entropy to use as threshold

    Returns:
        Entropy threshold (float)
    """
    benign_entropies = []
    for ex in executions:
        if ex.is_ransomware:
            continue
        df = ex.ata_write
        if df is None or len(df) == 0:
            continue
        # Collect mean entropy over 2-second windows
        max_time = df["rel_time"].max()
        for start in np.arange(0, max_time, 2.0):
            mask = (df["rel_time"] >= start) & (df["rel_time"] < start + 2.0)
            window = df[mask]
            if len(window) > 0:
                benign_entropies.append(window["entropy"].mean())

    if not benign_entropies:
        warnings.warn("No benign entropies found; using default threshold 0.9")
        return 0.9

    threshold = float(np.percentile(benign_entropies, percentile))
    return threshold


# ─── Full dataset builder ─────────────────────────────────────────────────────
def build_windowed_dataset(
    executions: List[Execution],
    window_sec: float = 2.0,
    stride_sec: float = 1.0,
    entropy_threshold: float = 0.9,
    load_data: bool = True,
) -> WindowedDataset:
    """Build a complete windowed feature dataset from a list of executions.

    Args:
        executions: List of Execution objects
        window_sec: Window duration in seconds
        stride_sec: Window stride in seconds
        entropy_threshold: Threshold for encryption labelling
        load_data: If True, load ata_write.csv for executions that haven't been loaded

    Returns:
        WindowedDataset with all windows from all executions
    """
    all_features = []
    all_y_binary = []
    all_y_detail = []
    all_exec_ids = []
    all_times = []
    all_families = []

    for ex in executions:
        if load_data and ex.ata_write is None:
            try:
                load_ata_write(ex)
            except Exception as e:
                warnings.warn(f"Could not load {ex.execution_id}: {e}")
                continue

        if ex.ata_write is None or len(ex.ata_write) == 0:
            continue

        features, y_bin, y_det, times = create_windows(
            ex, window_sec, stride_sec, entropy_threshold
        )

        n_windows = len(features)
        if n_windows == 0:
            continue

        all_features.append(features)
        all_y_binary.append(y_bin)
        all_y_detail.append(y_det)
        all_exec_ids.extend([ex.execution_id] * n_windows)
        all_times.append(times)
        all_families.extend([ex.family] * n_windows)

    if not all_features:
        return WindowedDataset(
            X=np.zeros((0, len(WINDOW_FEATURE_NAMES))),
            y_binary=np.zeros(0, dtype=np.int64),
            y_detail=np.zeros(0, dtype=np.int64),
            execution_ids=np.array([], dtype=str),
            window_times=np.zeros((0, 2)),
            families=np.array([], dtype=str),
            feature_names=WINDOW_FEATURE_NAMES,
        )

    return WindowedDataset(
        X=np.vstack(all_features),
        y_binary=np.concatenate(all_y_binary),
        y_detail=np.concatenate(all_y_detail),
        execution_ids=np.array(all_exec_ids),
        window_times=np.vstack(all_times),
        families=np.array(all_families),
        feature_names=WINDOW_FEATURE_NAMES,
    )


# ─── Train/test split by execution ───────────────────────────────────────────
def split_by_execution(
    executions: List[Execution],
    test_fraction: float = 0.2,
    seed: int = 42,
) -> Tuple[List[Execution], List[Execution]]:
    """Split executions into train/test, grouped by family.

    Ensures no family is present only in test (stratified split).
    Per D-004 §6: split by execution_id, stratify by family.

    Args:
        executions: All available executions
        test_fraction: Fraction of executions per family for testing
        seed: Random seed for reproducibility

    Returns:
        (train_executions, test_executions)
    """
    rng = np.random.RandomState(seed)

    # Group by family
    families: Dict[str, List[Execution]] = {}
    for ex in executions:
        families.setdefault(ex.family, []).append(ex)

    train = []
    test = []

    for family, execs in sorted(families.items()):
        n = len(execs)
        n_test = max(1, int(round(n * test_fraction)))
        n_train = n - n_test

        if n < 2:
            # Too few executions; put all in train
            train.extend(execs)
            warnings.warn(
                f"Family '{family}' has only {n} execution(s); all go to train"
            )
            continue

        indices = rng.permutation(n)
        for i in indices[:n_train]:
            train.append(execs[i])
        for i in indices[n_train:]:
            test.append(execs[i])

    return train, test
