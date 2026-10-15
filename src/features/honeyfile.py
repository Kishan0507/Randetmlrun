"""Entropy and honeyfile / canary tripwire feature extraction (T-P10-03).

Detects ransomware interactions with decoy files placed in critical directories:
1. Canary path matching: detects accesses to predefined decoy files (e.g. Desktop, Documents,
   root C:\\, $Recycle.Bin) matching canary patterns (*canary*, *decoy*, *honey*).
2. Canary write entropy: flags high-entropy modifications to decoy documents.
3. Canary tamper/delete: catches attempts to delete or rename decoy files.
4. Early tripwire signal: provides sub-second early alerts prior to mass user-file encryption.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# Typical decoy / honeyfile naming patterns deployed by endpoint agents
CANARY_PATTERNS = [
    re.compile(r".*canary.*", re.IGNORECASE),
    re.compile(r".*decoy.*", re.IGNORECASE),
    re.compile(r".*honey.*", re.IGNORECASE),
    re.compile(r".*\$recycle\.bin.*", re.IGNORECASE),
    re.compile(r".*000_a_test.*", re.IGNORECASE),  # Alphabetical tripwire (first file in directory)
    re.compile(r".*zzz_decoy.*", re.IGNORECASE),   # Alphabetical tripwire (last file in directory)
]

FILE_ACCESS_APIS: Set[str] = {
    "CreateFileW",
    "CreateFileA",
    "NtCreateFile",
    "NtOpenFile",
}

FILE_WRITE_APIS: Set[str] = {
    "WriteFile",
    "NtWriteFile",
}

FILE_DELETE_APIS: Set[str] = {
    "DeleteFileW",
    "DeleteFileA",
    "NtDeleteFile",
    "MoveFileWithProgressW",
    "MoveFileExW",
    "SetFileInformationByHandle",
}


@dataclass
class HoneyfileFeatures:
    """Extracted honeyfile / canary tripwire features."""

    sample_id: str
    canary_access_count: int
    canary_write_count: int
    canary_delete_count: int
    tripwire_triggered: bool
    time_to_first_trip: float
    max_canary_entropy: float
    features_vector: Dict[str, float] = field(default_factory=dict)


def is_canary_path(filepath: str) -> bool:
    """Check if a file path matches decoy / honeyfile tripwire patterns."""
    if not filepath:
        return False
    path_str = str(filepath).lower()
    return any(p.search(path_str) is not None for p in CANARY_PATTERNS)


def extract_honeyfile_features(
    calls: List[Dict[str, Any]],
    sample_id: str = "sample",
) -> HoneyfileFeatures:
    """Extract honeyfile tripwire features from an execution API call stream.

    Args:
        calls: List of Cuckoo API call dictionaries with 'api', 'arguments', and 'time'.
        sample_id: Execution or sample identifier.

    Returns:
        HoneyfileFeatures dataclass and numeric features dictionary.
    """
    canary_accesses = 0
    canary_writes = 0
    canary_deletes = 0
    tripwire_triggered = False
    first_trip_time = -1.0
    max_entropy = 0.0

    t0 = float(calls[0].get("time", 0.0)) if calls else 0.0

    for c in calls:
        api = c.get("api", "")
        args = c.get("arguments", {})
        if not isinstance(args, dict):
            continue

        raw_time = c.get("time", 0.0)
        try:
            call_time = float(raw_time) - t0
        except (ValueError, TypeError):
            call_time = 0.0

        # Extract file paths from arguments
        paths_in_call = []
        for k in ["filepath", "file_name", "existing_file_name", "new_file_name", "path"]:
            if k in args and args[k]:
                paths_in_call.append(str(args[k]))

        matched_canaries = [p for p in paths_in_call if is_canary_path(p)]

        if matched_canaries:
            if not tripwire_triggered:
                tripwire_triggered = True
                first_trip_time = max(call_time, 0.0)

            if api in FILE_ACCESS_APIS:
                canary_accesses += 1
            elif api in FILE_WRITE_APIS:
                canary_writes += 1
                # If buffer entropy or size is reported
                ent = args.get("entropy", 0.95)  # default tripwire write assumption
                if isinstance(ent, (int, float)):
                    max_entropy = max(max_entropy, float(ent))
            elif api in FILE_DELETE_APIS:
                canary_deletes += 1

    f_vec: Dict[str, float] = {
        "honey_canary_accesses": float(canary_accesses),
        "honey_canary_writes": float(canary_writes),
        "honey_canary_deletes": float(canary_deletes),
        "honey_tripwire_triggered": 1.0 if tripwire_triggered else 0.0,
        "honey_time_to_trip": float(first_trip_time) if tripwire_triggered else 999.0,
        "honey_max_canary_entropy": float(max_entropy),
    }

    return HoneyfileFeatures(
        sample_id=sample_id,
        canary_access_count=canary_accesses,
        canary_write_count=canary_writes,
        canary_delete_count=canary_deletes,
        tripwire_triggered=tripwire_triggered,
        time_to_first_trip=first_trip_time,
        max_canary_entropy=max_entropy,
        features_vector=f_vec,
    )
