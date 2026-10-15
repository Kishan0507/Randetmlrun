"""Unit tests for API sequence, n-gram, timing, and pattern extraction (T-P5-01, T-P5-02)."""

import json
from pathlib import Path
import numpy as np
import pytest

from src.features.sequence import (
    CallEvent,
    extract_ordered_calls,
    compute_inter_call_delays,
    compute_ngrams,
    compute_category_transitions,
    detect_extension_changes,
    match_ransomware_pipeline_patterns,
    extract_sequence_features,
)


@pytest.fixture
def synthetic_ransomware_report():
    """Synthetic Cuckoo report demonstrating the complete ransomware encryption loop."""
    return {
        "info": {"started": 1000.0, "duration": 10},
        "behavior": {
            "processes": [
                {
                    "process_name": "ransomware.exe",
                    "first_seen": 1000.0,
                    "calls": [
                        # 1. Discovery
                        {"api": "FindFirstFileExW", "category": "file", "time": 1000.1, "tid": 1},
                        {"api": "NtQueryDirectoryFile", "category": "file", "time": 1000.2, "tid": 1},
                        # 2. Open file
                        {"api": "NtOpenFile", "category": "file", "time": 1000.25, "tid": 1},
                        # 3. Read & Write
                        {"api": "NtReadFile", "category": "file", "time": 1000.3, "tid": 1},
                        {"api": "CryptEncrypt", "category": "crypto", "time": 1000.31, "tid": 1},
                        {"api": "NtWriteFile", "category": "file", "time": 1000.32, "tid": 1},
                        # 4. Delete original / rename to .locked
                        {
                            "api": "MoveFileWithProgressW",
                            "category": "file",
                            "time": 1000.4,
                            "tid": 1,
                            "arguments": {"existing_file_name": "data.docx", "new_file_name": "data.docx.locked"},
                        },
                        {"api": "DeleteFileW", "category": "file", "time": 1000.45, "tid": 1},
                    ],
                }
            ]
        },
    }


def test_extract_ordered_calls(synthetic_ransomware_report):
    calls = extract_ordered_calls(synthetic_ransomware_report)
    assert len(calls) == 8
    # Assert strictly ordered by time
    times = [c.time for c in calls]
    assert times == sorted(times)
    assert calls[0].api == "FindFirstFileExW"
    assert calls[-1].api == "DeleteFileW"


def test_compute_inter_call_delays(synthetic_ransomware_report):
    calls = extract_ordered_calls(synthetic_ransomware_report)
    mean_d, std_d, max_d, fast_frac = compute_inter_call_delays(calls)
    assert mean_d > 0.0
    assert max_d > 0.0
    assert 0.0 <= fast_frac <= 1.0


def test_compute_ngrams_and_transitions(synthetic_ransomware_report):
    calls = extract_ordered_calls(synthetic_ransomware_report)
    bigrams, trigrams = compute_ngrams(calls, max_vocab=10)
    assert ("FindFirstFileExW", "NtQueryDirectoryFile") in bigrams
    assert ("NtOpenFile", "NtReadFile", "CryptEncrypt") in trigrams

    cat_trans = compute_category_transitions(calls)
    assert ("file", "crypto") in cat_trans
    assert ("crypto", "file") in cat_trans


def test_ransomware_pipeline_patterns(synthetic_ransomware_report):
    calls = extract_ordered_calls(synthetic_ransomware_report)
    pipe_count, disc_open, open_write, write_del = match_ransomware_pipeline_patterns(calls, window_size=10)
    assert disc_open >= 1  # NtQueryDirectoryFile -> NtOpenFile
    assert open_write >= 1  # NtOpenFile -> NtReadFile
    assert write_del >= 1  # NtWriteFile -> MoveFileWithProgressW / DeleteFileW
    assert pipe_count >= 1  # Full Find -> Open -> Write -> Delete matched in window

    ext_changes = detect_extension_changes(calls)
    assert ext_changes >= 1  # .docx -> .docx.locked


def test_extract_sequence_features_end_to_end(synthetic_ransomware_report):
    seq_feat = extract_sequence_features(synthetic_ransomware_report, sample_id="syn_01")
    assert seq_feat.total_calls == 8
    assert seq_feat.crypto_call_count == 1
    assert seq_feat.pipeline_pattern_count >= 1
    assert "seq_pipeline_matches" in seq_feat.features_vector
    assert seq_feat.features_vector["seq_crypto_calls"] == 1.0
    assert seq_feat.features_vector["seq_ext_changes"] >= 1.0


def test_extract_sequence_features_real_cuckoo_samples():
    samples_dir = Path("data/raw/cuckoo_samples")
    if not samples_dir.exists():
        pytest.skip("No cuckoo samples directory found")

    sample_files = list(samples_dir.glob("*.json"))
    if not sample_files:
        pytest.skip("No cuckoo json files downloaded")

    # Test across first 3 real sample reports
    for s_path in sample_files[:3]:
        with open(s_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        feat = extract_sequence_features(data, sample_id=s_path.stem)
        assert feat.sample_id == s_path.stem
        assert feat.total_calls >= 0
        assert np.isfinite(feat.call_rate)
        assert np.isfinite(feat.inter_call_delay_mean)
        assert isinstance(feat.features_vector, dict)
        for k, v in feat.features_vector.items():
            assert np.isfinite(v), f"Feature {k} must be finite"
