"""API sequence representation, n-grams, timing, and behavioral pattern extraction (T-P5-01, T-P5-02).

Extracts sequential behavioral representations from Cuckoo execution reports:
1. Ordered API call streams across all monitored processes.
2. N-grams (n=2, 3), TF-IDF vectors, and ordered Markov transition counts.
3. Inter-call delay timing statistics (burstiness, fast-loop fraction).
4. Ransomware attack lifecycle pattern matching (Find -> Open -> Write -> Delete/Rename).
5. File operation rates and extension change indicators.
"""

from __future__ import annotations

import collections
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


# ─── Ransomware API Pattern Catalog ───────────────────────────────────────────
DISCOVERY_APIS: Set[str] = {
    "FindFirstFileExW",
    "FindFirstFileW",
    "FindNextFileW",
    "NtQueryDirectoryFile",
    "SearchPathW",
    "GetLogicalDriveStringsW",
    "GetVolumePathNamesForVolumeNameW",
    "GetVolumeNameForVolumeMountPointW",
    "GetFileAttributesW",
    "GetFileAttributesExW",
}

OPEN_APIS: Set[str] = {
    "CreateFileW",
    "CreateFileA",
    "NtCreateFile",
    "NtOpenFile",
    "NtOpenDirectoryObject",
}

READ_WRITE_APIS: Set[str] = {
    "WriteFile",
    "NtWriteFile",
    "ReadFile",
    "NtReadFile",
    "SetFilePointer",
    "SetFilePointerEx",
}

TAMPER_DELETE_APIS: Set[str] = {
    "DeleteFileW",
    "DeleteFileA",
    "NtDeleteFile",
    "MoveFileWithProgressW",
    "MoveFileExW",
    "SetFileInformationByHandle",
    "SetFileAttributesW",
    "SetFileTime",
}

CRYPTO_APIS: Set[str] = {
    "CryptAcquireContextA",
    "CryptAcquireContextW",
    "CryptCreateHash",
    "CryptHashData",
    "CryptEncrypt",
    "CryptDecrypt",
    "CryptGenKey",
    "CryptExportKey",
    "CryptDecodeObjectEx",
}


@dataclass
class CallEvent:
    """Normalized API call event with timestamp and arguments."""

    api: str
    category: str
    time: float
    tid: int
    arguments: Dict[str, Any] = field(default_factory=dict)
    process_name: str = ""


@dataclass
class SequenceFeatures:
    """Extracted sequential, timing, and pattern features."""

    sample_id: str
    total_calls: int
    duration_sec: float
    call_rate: float
    file_ops_rate: float
    write_rate: float
    inter_call_delay_mean: float
    inter_call_delay_std: float
    inter_call_delay_max: float
    fast_loop_fraction: float  # calls with delta_t < 1ms
    bigrams: Dict[Tuple[str, str], int]
    trigrams: Dict[Tuple[str, str, str], int]
    category_transitions: Dict[Tuple[str, str], int]
    pipeline_pattern_count: int  # Find -> Open -> Write -> Delete matches
    discovery_to_open_count: int
    open_to_write_count: int
    write_to_delete_count: int
    crypto_call_count: int
    extension_change_count: int
    features_vector: Dict[str, float]


def extract_ordered_calls(report: Dict[str, Any]) -> List[CallEvent]:
    """Extract and chronologically order all API calls from Cuckoo processes."""
    events: List[CallEvent] = []
    processes = report.get("behavior", {}).get("processes", [])

    for proc in processes:
        p_name = proc.get("process_name", "")
        calls = proc.get("calls", [])
        for c in calls:
            api = c.get("api", "unknown")
            cat = c.get("category", "unknown")
            t_raw = c.get("time", 0.0)
            try:
                t_val = float(t_raw) if t_raw is not None else 0.0
            except (ValueError, TypeError):
                t_val = 0.0

            tid = int(c.get("tid", 0) or 0)
            args = c.get("arguments", {})
            if not isinstance(args, dict):
                args = {}

            events.append(
                CallEvent(
                    api=api,
                    category=cat,
                    time=t_val,
                    tid=tid,
                    arguments=args,
                    process_name=p_name,
                )
            )

    # Sort strictly chronologically
    events.sort(key=lambda e: e.time)
    return events


def compute_inter_call_delays(calls: List[CallEvent]) -> Tuple[float, float, float, float]:
    """Compute inter-call delay statistics: mean, std, max, fast_loop_fraction."""
    if len(calls) < 2:
        return 0.0, 0.0, 0.0, 0.0

    times = np.array([c.time for c in calls], dtype=np.float64)
    deltas = np.diff(times)
    # Filter negative deltas if clock skew
    deltas = np.maximum(deltas, 0.0)

    mean_d = float(np.mean(deltas))
    std_d = float(np.std(deltas))
    max_d = float(np.max(deltas))
    fast_frac = float(np.mean(deltas < 0.001))  # sub-millisecond burst loops

    return mean_d, std_d, max_d, fast_frac


def compute_ngrams(
    calls: List[CallEvent],
    max_vocab: int = 50,
) -> Tuple[Dict[Tuple[str, str], int], Dict[Tuple[str, str, str], int]]:
    """Compute frequency counts for API bigrams (n=2) and trigrams (n=3)."""
    bigrams: collections.Counter = collections.Counter()
    trigrams: collections.Counter = collections.Counter()

    apis = [c.api for c in calls]
    for i in range(len(apis) - 1):
        bigrams[(apis[i], apis[i + 1])] += 1
    for i in range(len(apis) - 2):
        trigrams[(apis[i], apis[i + 1], apis[i + 2])] += 1

    return dict(bigrams.most_common(max_vocab)), dict(trigrams.most_common(max_vocab))


def compute_category_transitions(calls: List[CallEvent]) -> Dict[Tuple[str, str], int]:
    """Compute Markov transition counts between high-level behavioral categories."""
    transitions: collections.Counter = collections.Counter()
    cats = [c.category for c in calls]
    for i in range(len(cats) - 1):
        transitions[(cats[i], cats[i + 1])] += 1
    return dict(transitions)


def detect_extension_changes(calls: List[CallEvent]) -> int:
    """Detect file rename or extension manipulation indicating ransomware encryption."""
    count = 0
    suspicious_exts = {".encrypted", ".locked", ".crypto", ".ransom", ".wncry", ".dark", ".conti"}

    for c in calls:
        if c.api in {"MoveFileWithProgressW", "MoveFileExW", "SetFileInformationByHandle"}:
            args_str = str(c.arguments).lower()
            if any(ext in args_str for ext in suspicious_exts):
                count += 1
            # Check for differing source vs target extension
            src = c.arguments.get("existing_file_name", "") or c.arguments.get("src", "")
            dst = c.arguments.get("new_file_name", "") or c.arguments.get("dst", "")
            if src and dst and Path(src).suffix != Path(dst).suffix:
                count += 1
    return count


def match_ransomware_pipeline_patterns(
    calls: List[CallEvent],
    window_size: int = 20,
) -> Tuple[int, int, int, int]:
    """Match ransomware behavioral pattern: Find -> Open -> Write -> Delete.

    Returns:
        (pipeline_full_matches, discovery_to_open, open_to_write, write_to_delete)
    """
    n = len(calls)
    full_pipeline_matches = 0
    discovery_to_open = 0
    open_to_write = 0
    write_to_delete = 0

    apis = [c.api for c in calls]

    # 1. Consecutive or near-neighbor pair transitions
    for i in range(n - 1):
        a1, a2 = apis[i], apis[i + 1]
        if a1 in DISCOVERY_APIS and a2 in OPEN_APIS:
            discovery_to_open += 1
        elif a1 in OPEN_APIS and a2 in READ_WRITE_APIS:
            open_to_write += 1
        elif a1 in READ_WRITE_APIS and a2 in TAMPER_DELETE_APIS:
            write_to_delete += 1

    # 2. Sliding window full lifecycle pipeline match (Find -> Open -> Write -> Delete in same window)
    if n < 4:
        return full_pipeline_matches, discovery_to_open, open_to_write, write_to_delete

    if n <= window_size:
        has_disc = any(a in DISCOVERY_APIS for a in apis)
        has_open = any(a in OPEN_APIS for a in apis)
        has_write = any(a in READ_WRITE_APIS for a in apis)
        has_tamper = any(a in TAMPER_DELETE_APIS for a in apis)
        if has_disc and has_open and has_write and has_tamper:
            full_pipeline_matches += 1
    else:
        for i in range(n - window_size + 1):
            window = apis[i : i + window_size]
            has_disc = any(a in DISCOVERY_APIS for a in window)
            has_open = any(a in OPEN_APIS for a in window)
            has_write = any(a in READ_WRITE_APIS for a in window)
            has_tamper = any(a in TAMPER_DELETE_APIS for a in window)
            if has_disc and has_open and has_write and has_tamper:
                full_pipeline_matches += 1

    return full_pipeline_matches, discovery_to_open, open_to_write, write_to_delete


def extract_sequence_features(
    report: Dict[str, Any],
    sample_id: str = "sample",
) -> SequenceFeatures:
    """Extract full sequence, timing, n-gram, and pattern features from a Cuckoo report."""
    calls = extract_ordered_calls(report)
    total_calls = len(calls)

    if total_calls > 0:
        duration = max(calls[-1].time - calls[0].time, 0.001)
    else:
        duration = 0.001

    call_rate = total_calls / duration

    # File ops and writes count
    file_ops = sum(1 for c in calls if c.category == "file" or c.api in DISCOVERY_APIS | OPEN_APIS | READ_WRITE_APIS | TAMPER_DELETE_APIS)
    write_ops = sum(1 for c in calls if c.api in READ_WRITE_APIS)
    crypto_ops = sum(1 for c in calls if c.api in CRYPTO_APIS or c.category == "crypto")

    file_ops_rate = file_ops / duration
    write_rate = write_ops / duration

    mean_d, std_d, max_d, fast_frac = compute_inter_call_delays(calls)
    bigrams, trigrams = compute_ngrams(calls, max_vocab=30)
    cat_trans = compute_category_transitions(calls)

    pipe_matches, disc_open, open_write, write_del = match_ransomware_pipeline_patterns(calls)
    ext_changes = detect_extension_changes(calls)

    # Flatten into feature dictionary for ML models
    f_vec: Dict[str, float] = {
        "seq_total_calls": float(total_calls),
        "seq_duration_sec": float(duration),
        "seq_call_rate": float(call_rate),
        "seq_file_ops_rate": float(file_ops_rate),
        "seq_write_rate": float(write_rate),
        "seq_inter_delay_mean": float(mean_d),
        "seq_inter_delay_std": float(std_d),
        "seq_inter_delay_max": float(max_d),
        "seq_fast_loop_fraction": float(fast_frac),
        "seq_pipeline_matches": float(pipe_matches),
        "seq_disc_to_open": float(disc_open),
        "seq_open_to_write": float(open_write),
        "seq_write_to_delete": float(write_del),
        "seq_crypto_calls": float(crypto_ops),
        "seq_ext_changes": float(ext_changes),
    }

    # Add top transition signals
    for (c1, c2), count in cat_trans.items():
        f_vec[f"trans_cat_{c1}_to_{c2}"] = float(count)

    for (a1, a2), count in bigrams.items():
        f_vec[f"ngram_bi_{a1}__{a2}"] = float(count)

    return SequenceFeatures(
        sample_id=sample_id,
        total_calls=total_calls,
        duration_sec=duration,
        call_rate=call_rate,
        file_ops_rate=file_ops_rate,
        write_rate=write_rate,
        inter_call_delay_mean=mean_d,
        inter_call_delay_std=std_d,
        inter_call_delay_max=max_d,
        fast_loop_fraction=fast_frac,
        bigrams=bigrams,
        trigrams=trigrams,
        category_transitions=cat_trans,
        pipeline_pattern_count=pipe_matches,
        discovery_to_open_count=disc_open,
        open_to_write_count=open_write,
        write_to_delete_count=write_del,
        crypto_call_count=crypto_ops,
        extension_change_count=ext_changes,
        features_vector=f_vec,
    )
