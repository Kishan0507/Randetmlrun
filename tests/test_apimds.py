"""Unit tests for the APIMDS dataset loader and feature extraction."""

from __future__ import annotations

from pathlib import Path
import pytest
import pandas as pd

from src.data.load_apimds import (
    APIMDSSample,
    categorize_label,
    load_apimds_samples,
    extract_vocabulary,
    build_feature_matrix,
    DEFAULT_APIMDS_PATH,
)


def test_categorize_label() -> None:
    # Benign / grayware / not-a-virus
    cat, is_m, is_r = categorize_label("not-a-virus:AdWare.Win32.MegaSearch.am")
    assert cat == "benign"
    assert is_m == 0
    assert is_r == 0

    cat, is_m, is_r = categorize_label("HEUR:not-a-virus:AdWare.Win32.ScreenSaver.gen")
    assert cat == "benign"
    assert is_m == 0
    assert is_r == 0

    # Ransomware
    cat, is_m, is_r = categorize_label("Trojan-Ransom.Win32.Foreign.cifo")
    assert cat == "ransomware"
    assert is_m == 1
    assert is_r == 1

    # Other malware
    cat, is_m, is_r = categorize_label("Worm.Win32.Zwr.c")
    assert cat == "other_malware"
    assert is_m == 1
    assert is_r == 0

    # Unlabeled
    cat, is_m, is_r = categorize_label("")
    assert cat == "unlabeled"
    assert is_m is None
    assert is_r == 0


def test_load_apimds_samples_subset() -> None:
    if not DEFAULT_APIMDS_PATH.exists():
        pytest.skip("APIMDS dataset file not present in data/raw/")

    # Load 50 samples
    samples = load_apimds_samples(max_samples=50)
    assert len(samples) == 50
    for s in samples:
        assert isinstance(s, APIMDSSample)
        assert len(s.sha256) == 64
        assert s.sequence_length > 0
        assert isinstance(s.api_sequence, list)


def test_build_feature_matrix() -> None:
    # Create synthetic samples for deterministic test
    samples = [
        APIMDSSample(
            sha256="a" * 64,
            raw_label="not-a-virus:AdWare.Win32.Test",
            category="benign",
            is_malware=0,
            is_ransomware=0,
            api_sequence=["GetSystemDirectoryA", "LocalAlloc", "CreateFileW", "WriteFile"],
        ),
        APIMDSSample(
            sha256="b" * 64,
            raw_label="Trojan-Ransom.Win32.Test",
            category="ransomware",
            is_malware=1,
            is_ransomware=1,
            api_sequence=["FindFirstFileW", "CreateFileW", "WriteFile", "DeleteFileW", "CryptEncrypt"],
        ),
    ]

    vocab = extract_vocabulary(samples, min_freq=1, max_features=10)
    assert "CreateFileW" in vocab
    assert "WriteFile" in vocab

    X, y, feat_names = build_feature_matrix(samples, vocab=vocab, include_lifecycle=True)

    assert isinstance(X, pd.DataFrame)
    assert len(X) == 2
    assert list(y) == [0, 1]
    assert "seq_length" in feat_names
    assert "crypto_calls" in feat_names
    assert "discovery_to_open_transitions" in feat_names
    assert not X.isna().any().any()

    # Ransomware sample should have crypto and lifecycle transitions
    assert X.loc[1, "crypto_calls"] >= 1.0
    assert X.loc[1, "discovery_to_open_transitions"] >= 1.0
