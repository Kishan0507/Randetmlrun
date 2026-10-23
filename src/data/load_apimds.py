"""APIMDS (API-based Malware Detection System) dataset loader and feature extractor.

Handles loading and feature representation for the 23,146 sample API sequence dataset
(Ki et al., HCRL / Korea University; MDAPI benchmark):
- Parses SHA-256 hashes, AV family labels, and ordered API call sequences.
- Normalizes sample categorization:
    * Benign (not-a-virus / AdWare / grayware / tools): 3,137 samples
    * Ransomware (Trojan-Ransom.*): 447 samples
    * Other Malware (Trojans, Worms, Viruses, Backdoors): 13,684 samples
    * Unlabeled: 5,878 samples
- Extracts Bag-of-Words, TF, Bigram transitions, and ransomware lifecycle patterns.
"""

from __future__ import annotations

import collections
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

import numpy as np
import pandas as pd

from src.features.sequence import (
    CRYPTO_APIS,
    DISCOVERY_APIS,
    OPEN_APIS,
    READ_WRITE_APIS,
    TAMPER_DELETE_APIS,
    CallEvent,
    match_ransomware_pipeline_patterns,
)

DEFAULT_APIMDS_PATH = Path("data/raw/malware_API_dataset.csv")


@dataclass
class APIMDSSample:
    """Represents a single executable trace from the APIMDS dataset."""

    sha256: str
    raw_label: str
    category: str  # 'benign', 'ransomware', 'other_malware', 'unlabeled'
    is_malware: Optional[int]  # 1 for malware, 0 for benign, None for unlabeled
    is_ransomware: int  # 1 for ransomware, 0 otherwise
    api_sequence: List[str]
    sequence_length: int = field(init=False)

    def __post_init__(self) -> None:
        self.sequence_length = len(self.api_sequence)


def categorize_label(raw_label: str) -> Tuple[str, Optional[int], int]:
    """Categorize Kaspersky-style raw labels into standardized security classes.

    Returns:
        (category, is_malware, is_ransomware)
    """
    if not raw_label or raw_label.strip() == "":
        return "unlabeled", None, 0

    lower = raw_label.lower()
    if "not-a-virus" in lower:
        return "benign", 0, 0

    if "ransom" in lower:
        return "ransomware", 1, 1

    return "other_malware", 1, 0


def load_apimds_samples(
    csv_path: Union[str, Path] = DEFAULT_APIMDS_PATH,
    max_samples: Optional[int] = None,
    filter_unlabeled: bool = False,
    only_ransom_and_benign: bool = False,
) -> List[APIMDSSample]:
    """Load and parse APIMDS samples from raw CSV file."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"APIMDS dataset not found at: {path.resolve()}")

    samples: List[APIMDSSample] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row or len(row) < 3:
                continue

            raw_label = row[0].strip()
            sha256 = row[1].strip()
            apis = [api.strip() for api in row[2:] if api.strip()]

            category, is_malware, is_ransomware = categorize_label(raw_label)

            if filter_unlabeled and category == "unlabeled":
                continue

            if only_ransom_and_benign and category not in {"benign", "ransomware"}:
                continue

            sample = APIMDSSample(
                sha256=sha256,
                raw_label=raw_label,
                category=category,
                is_malware=is_malware,
                is_ransomware=is_ransomware,
                api_sequence=apis,
            )
            samples.append(sample)

            if max_samples is not None and len(samples) >= max_samples:
                break

    return samples


def extract_vocabulary(
    samples: Sequence[APIMDSSample],
    min_freq: int = 5,
    max_features: Optional[int] = 300,
) -> List[str]:
    """Build a sorted vocabulary of the most frequent APIs across samples."""
    counts: collections.Counter = collections.Counter()
    for s in samples:
        counts.update(s.api_sequence)

    valid_apis = [api for api, cnt in counts.most_common() if cnt >= min_freq]
    if max_features is not None:
        valid_apis = valid_apis[:max_features]
    return sorted(valid_apis)


def build_feature_matrix(
    samples: Sequence[APIMDSSample],
    vocab: Optional[List[str]] = None,
    include_presence: bool = True,
    include_frequency: bool = False,
    include_lifecycle: bool = True,
    max_vocab_size: int = 250,
) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Build a numerical feature matrix (DataFrame) and label Series from APIMDS samples.

    Features include:
    - API presence / frequency indicators
    - Lifecycle behavioral features (discovery-to-open, open-to-write, write-to-delete, crypto calls)
    - Sequence length summary statistics

    Returns:
        (X_df, y_series, feature_names)
    """
    if vocab is None:
        vocab = extract_vocabulary(samples, min_freq=10, max_features=max_vocab_size)

    vocab_set = set(vocab)
    vocab_idx = {api: i for i, api in enumerate(vocab)}

    records = []
    labels = []

    for s in samples:
        row: Dict[str, Union[int, float]] = {}

        # 1. Sequence basic stats
        row["seq_length"] = float(s.sequence_length)
        row["unique_apis_count"] = float(len(set(s.api_sequence)))

        # 2. Vocabulary API presence / frequency
        counts = collections.Counter(s.api_sequence)
        for api in vocab:
            cnt = counts.get(api, 0)
            if include_presence:
                row[f"API_PRES:{api}"] = 1.0 if cnt > 0 else 0.0
            if include_frequency:
                row[f"API_FREQ:{api}"] = float(cnt) / max(1.0, float(s.sequence_length))

        # 3. Domain API category totals
        row["discovery_calls"] = float(sum(counts.get(a, 0) for a in DISCOVERY_APIS))
        row["open_calls"] = float(sum(counts.get(a, 0) for a in OPEN_APIS))
        row["read_write_calls"] = float(sum(counts.get(a, 0) for a in READ_WRITE_APIS))
        row["delete_tamper_calls"] = float(sum(counts.get(a, 0) for a in TAMPER_DELETE_APIS))
        row["crypto_calls"] = float(sum(counts.get(a, 0) for a in CRYPTO_APIS))

        # 4. Behavioral lifecycle pattern matches
        if include_lifecycle:
            # Wrap API strings in dummy CallEvents for lifecycle matching
            call_events = [
                CallEvent(api=a, category="", time=float(idx), tid=0, arguments={})
                for idx, a in enumerate(s.api_sequence)
            ]
            full_matches, d2o, o2w, w2d = match_ransomware_pipeline_patterns(call_events)
            row["lifecycle_full_pipeline"] = float(full_matches)
            row["discovery_to_open_transitions"] = float(d2o)
            row["open_to_write_transitions"] = float(o2w)
            row["write_to_delete_transitions"] = float(w2d)

        records.append(row)
        labels.append(s.is_malware if s.is_malware is not None else -1)

    import re

    X_df = pd.DataFrame(records)
    # Sanitize feature names for LightGBM/JSON compatibility (replace ':', ',', ' ', etc. with '_')
    clean_columns = [re.sub(r"[^\w]", "_", col) for col in X_df.columns]
    X_df.columns = clean_columns
    y_series = pd.Series(labels, name="label")
    feature_names = list(X_df.columns)

    return X_df, y_series, feature_names
