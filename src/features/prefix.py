"""Prefix-based feature extractor and evaluation on Cuckoo JSON reports (T-P4-05).

Prototypes early dynamic detection by truncating execution logs at t seconds
and re-extracting dynamic behavioral features (API call frequencies, categories,
process activities, and inter-call timing).

NOTE: Full Cuckoo JSON reports are available only for sample runs in the public
MLRan repository. This prototype validates the end-to-end prefix extraction logic.
Full scale across all 4,880 samples would require Track B (re-execution in a sandbox)
or release of upstream raw logs (documented in reports/early_detection.md).
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class PrefixFeatures:
    """Extracted behavioral features from a time-truncated Cuckoo execution."""

    sample_id: str
    cutoff_sec: float
    total_calls: int
    n_unique_apis: int
    call_rate: float  # calls per second
    api_counts: Dict[str, int]
    category_counts: Dict[str, int]
    signatures_triggered: List[str]
    features_vector: Dict[str, float]


def get_execution_start_time(report: Dict[str, Any]) -> float:
    """Determine the earliest execution start timestamp in the Cuckoo report."""
    times = []

    # Check processes first_seen or start times
    processes = report.get("behavior", {}).get("processes", [])
    for p in processes:
        if "first_seen" in p and p["first_seen"]:
            times.append(float(p["first_seen"]))
        for c in p.get("calls", []):
            if "time" in c and c["time"]:
                times.append(float(c["time"]))

    if not times:
        # Fallback to info section
        info = report.get("info", {})
        if "started" in info:
            times.append(float(info["started"]))

    return min(times) if times else 0.0


def truncate_cuckoo_report(
    report: Dict[str, Any],
    cutoff_sec: float,
) -> Dict[str, Any]:
    """Create a truncated copy of a Cuckoo JSON report up to cutoff_sec seconds.

    Filters calls, process activities, and summary statistics to only include
    events that occurred before t0 + cutoff_sec.

    Args:
        report: Original Cuckoo report dictionary
        cutoff_sec: Time cutoff from execution start in seconds

    Returns:
        New truncated report dictionary
    """
    t0 = get_execution_start_time(report)
    t_max = t0 + cutoff_sec

    truncated = copy.deepcopy(report)
    behavior = truncated.get("behavior", {})

    filtered_processes = []
    for proc in behavior.get("processes", []):
        calls = proc.get("calls", [])
        # Filter calls by relative time
        kept_calls = [c for c in calls if float(c.get("time", 0.0)) <= t_max]
        proc_copy = dict(proc)
        proc_copy["calls"] = kept_calls
        filtered_processes.append(proc_copy)

    behavior["processes"] = filtered_processes

    # Also update summary API stats if present
    api_stats = {}
    for proc in filtered_processes:
        for c in proc.get("calls", []):
            api_name = c.get("api", "unknown")
            api_stats[api_name] = api_stats.get(api_name, 0) + 1
    behavior["apistats"] = api_stats

    return truncated


def extract_prefix_features(
    report: Dict[str, Any],
    cutoff_sec: float,
    sample_id: str = "unknown",
) -> PrefixFeatures:
    """Extract quantitative behavioral features from a prefix of a Cuckoo report.

    Args:
        report: Original Cuckoo report dictionary
        cutoff_sec: Cutoff threshold in seconds
        sample_id: Sample identifier

    Returns:
        PrefixFeatures container
    """
    t0 = get_execution_start_time(report)
    t_max = t0 + cutoff_sec

    processes = report.get("behavior", {}).get("processes", [])
    all_calls = []
    api_counts: Dict[str, int] = {}
    cat_counts: Dict[str, int] = {}

    for proc in processes:
        for c in proc.get("calls", []):
            call_time = float(c.get("time", 0.0))
            if call_time <= t_max:
                all_calls.append(c)
                api = c.get("api", "unknown")
                cat = c.get("category", "unknown")
                api_counts[api] = api_counts.get(api, 0) + 1
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

    total_calls = len(all_calls)
    n_unique_apis = len(api_counts)
    call_rate = total_calls / cutoff_sec if cutoff_sec > 0 else 0.0

    # Build flat numerical feature vector
    feat_vec: Dict[str, float] = {
        "prefix_cutoff_sec": float(cutoff_sec),
        "total_calls": float(total_calls),
        "unique_apis": float(n_unique_apis),
        "call_rate": float(call_rate),
    }

    # Add API frequencies
    for api, cnt in api_counts.items():
        feat_vec[f"API:{api}"] = float(cnt)

    # Add Category frequencies
    for cat, cnt in cat_counts.items():
        feat_vec[f"CATEGORY:{cat}"] = float(cnt)

    # Signatures
    signatures = [
        sig.get("name", "")
        for sig in report.get("signatures", [])
        if sig.get("name")
    ]

    return PrefixFeatures(
        sample_id=sample_id,
        cutoff_sec=cutoff_sec,
        total_calls=total_calls,
        n_unique_apis=n_unique_apis,
        call_rate=call_rate,
        api_counts=api_counts,
        category_counts=cat_counts,
        signatures_triggered=signatures,
        features_vector=feat_vec,
    )


def evaluate_prefix_progression(
    reports_dir: str | Path = "data/raw/cuckoo_samples",
    cutoffs: Tuple[float, ...] = (2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0),
) -> pd.DataFrame:
    """Evaluate how behavioral feature volume evolves over prefix cutoffs.

    Args:
        reports_dir: Directory containing sample Cuckoo JSON files
        cutoffs: List of prefix durations in seconds

    Returns:
        DataFrame summarizing feature growth across prefix cutoffs
    """
    reports_path = Path(reports_dir)
    json_files = sorted(reports_path.glob("*.json"))

    if not json_files:
        raise FileNotFoundError(f"No Cuckoo JSON reports found in {reports_dir}")

    records = []
    for jf in json_files:
        sample_id = jf.stem
        try:
            with open(jf, "r", encoding="utf-8") as f:
                rep = json.load(f)
        except Exception as e:
            continue

        for cutoff in cutoffs:
            p_feat = extract_prefix_features(rep, cutoff_sec=cutoff, sample_id=sample_id)
            records.append({
                "sample_id": sample_id,
                "cutoff_sec": cutoff,
                "total_calls": p_feat.total_calls,
                "unique_apis": p_feat.n_unique_apis,
                "call_rate": p_feat.call_rate,
                "has_memory_alloc": 1 if "API:NtAllocateVirtualMemory" in p_feat.features_vector else 0,
                "has_protect_memory": 1 if "API:NtProtectVirtualMemory" in p_feat.features_vector else 0,
                "has_file_ops": 1 if any("File" in k for k in p_feat.features_vector) else 0,
            })

    return pd.DataFrame(records)
