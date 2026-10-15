"""Unit tests for Cuckoo report prefix truncation and feature extraction (T-P4-05)."""

from pathlib import Path
import numpy as np
import pytest

from src.features.prefix import (
    truncate_cuckoo_report,
    extract_prefix_features,
    evaluate_prefix_progression,
    get_execution_start_time,
)


@pytest.fixture
def sample_cuckoo_report():
    return {
        "info": {"started": 100.0, "duration": 60},
        "behavior": {
            "processes": [
                {
                    "process_name": "sample.exe",
                    "first_seen": 100.0,
                    "calls": [
                        {"api": "NtAllocateVirtualMemory", "category": "memory", "time": 101.5},
                        {"api": "NtProtectVirtualMemory", "category": "memory", "time": 104.0},
                        {"api": "NtWriteFile", "category": "filesystem", "time": 115.0},
                        {"api": "NtClose", "category": "filesystem", "time": 140.0},
                    ],
                }
            ],
            "apistats": {},
        },
        "signatures": [{"name": "creates_suspicious_memory"}],
    }


def test_get_execution_start_time(sample_cuckoo_report):
    t0 = get_execution_start_time(sample_cuckoo_report)
    assert t0 == 100.0


def test_truncate_cuckoo_report(sample_cuckoo_report):
    # Cutoff at 5.0 seconds from t0=100.0 -> max_time = 105.0
    truncated = truncate_cuckoo_report(sample_cuckoo_report, cutoff_sec=5.0)
    calls = truncated["behavior"]["processes"][0]["calls"]
    # Only calls at 101.5 and 104.0 should remain (2 calls)
    assert len(calls) == 2
    assert {c["api"] for c in calls} == {"NtAllocateVirtualMemory", "NtProtectVirtualMemory"}
    assert truncated["behavior"]["apistats"]["NtAllocateVirtualMemory"] == 1
    assert truncated["behavior"]["apistats"]["NtProtectVirtualMemory"] == 1


def test_extract_prefix_features(sample_cuckoo_report):
    p_feat = extract_prefix_features(sample_cuckoo_report, cutoff_sec=10.0, sample_id="test_01")
    assert p_feat.sample_id == "test_01"
    assert p_feat.cutoff_sec == 10.0
    # Calls before 110.0: 101.5, 104.0 (2 calls)
    assert p_feat.total_calls == 2
    assert p_feat.n_unique_apis == 2
    assert p_feat.call_rate == pytest.approx(0.2)
    assert "API:NtAllocateVirtualMemory" in p_feat.features_vector
    assert "CATEGORY:memory" in p_feat.features_vector
    assert "API:NtWriteFile" not in p_feat.features_vector  # happened at 115.0


def test_evaluate_prefix_progression_real_data():
    samples_dir = Path("data/raw/cuckoo_samples")
    if not samples_dir.exists() or not list(samples_dir.glob("*.json")):
        pytest.skip("No real sample Cuckoo JSONs downloaded")

    df = evaluate_prefix_progression(samples_dir, cutoffs=(2.0, 5.0, 10.0, 30.0))
    assert len(df) > 0
    assert "cutoff_sec" in df.columns
    assert "total_calls" in df.columns
    # Check that calls are non-decreasing with cutoff for each sample
    for sid, group in df.groupby("sample_id"):
        calls = group.sort_values("cutoff_sec")["total_calls"].values
        assert (np.diff(calls) >= 0).all()
