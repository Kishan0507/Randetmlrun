"""Ransom-note and extension-change behavioral detector (T-P10-04).

Extracts high-precision, low-cost features by detecting:
1. Ransom note filename patterns (e.g. 'how_to_decrypt.html', 'readme_for_decrypt.txt').
2. Threat ransom terminology in dropped files and extracted strings (e.g. 'tor browser', 'bitcoin', 'private key').
3. Ransomware file extensions and double extension anomalies (e.g. '.locked', '.wncry', 'doc.pdf.encrypted').
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Regex patterns for ransom note file names
RANSOM_NOTE_PATTERNS = [
    re.compile(r".*how_to_decrypt.*", re.IGNORECASE),
    re.compile(r".*how_to_recover.*", re.IGNORECASE),
    re.compile(r".*readme.*decrypt.*", re.IGNORECASE),
    re.compile(r".*restore_files.*", re.IGNORECASE),
    re.compile(r".*decrypt_notes?.*", re.IGNORECASE),
    re.compile(r".*your_files_are_encrypted.*", re.IGNORECASE),
    re.compile(r".*files_encrypted.*", re.IGNORECASE),
    re.compile(r".*help_recover.*", re.IGNORECASE),
    re.compile(r".*!readme!.*", re.IGNORECASE),
    re.compile(r".*read_me_first.*", re.IGNORECASE),
]

# Keywords found in ransom note contents
RANSOM_KEYWORDS = [
    re.compile(r"\b(decrypt(or|ion)?)\b", re.IGNORECASE),
    re.compile(r"\b(bitcoin|btc|monero|xmr)\b", re.IGNORECASE),
    re.compile(r"\b(private key)\b", re.IGNORECASE),
    re.compile(r"\b(tor browser|\.onion)\b", re.IGNORECASE),
    re.compile(r"\b(files (have been|are) encrypted)\b", re.IGNORECASE),
    re.compile(r"\b(ransom)\b", re.IGNORECASE),
    re.compile(r"\b(pay(ment)? within \d+ (hours|days))\b", re.IGNORECASE),
]

# Known ransomware extensions
KNOWN_RANSOM_EXTENSIONS: Set[str] = {
    ".locked",
    ".crypto",
    ".wncry",
    ".lockbit",
    ".conti",
    ".darkside",
    ".revil",
    ".crypt",
    ".enc",
    ".ryuk",
    ".badrabbit",
    ".cerber",
    ".thor",
    ".zepto",
    ".locky",
}


@dataclass
class RansomNoteFeatures:
    """Extracted ransom-note and extension-change features."""

    sample_id: str
    ransom_note_count: int
    ransom_keyword_hits: int
    suspicious_extension_count: int
    double_extension_count: int
    ransom_note_detected: bool
    features_vector: Dict[str, float] = field(default_factory=dict)


def is_ransom_note_name(filename: str) -> bool:
    """Check if filename matches known ransom note conventions."""
    if not filename:
        return False
    base = Path(filename).name
    return any(p.search(base) is not None for p in RANSOM_NOTE_PATTERNS)


def has_double_extension(filename: str) -> bool:
    """Check if filename has double extensions (e.g. .docx.locked, .pdf.crypto)."""
    p = Path(filename)
    stem_suffix = Path(p.stem).suffix
    return bool(stem_suffix and p.suffix)


def extract_ransom_note_features(
    report: Dict[str, Any],
    sample_id: str = "sample",
) -> RansomNoteFeatures:
    """Extract ransom note and extension change features from Cuckoo JSON report."""
    note_count = 0
    keyword_hits = 0
    suspicious_ext_count = 0
    double_ext_count = 0

    # 1. Check dropped files
    dropped = report.get("dropped", [])
    if isinstance(dropped, list):
        for f in dropped:
            if isinstance(f, dict):
                name = str(f.get("name", ""))
                if is_ransom_note_name(name):
                    note_count += 1
                ext = Path(name).suffix.lower()
                if ext in KNOWN_RANSOM_EXTENSIONS:
                    suspicious_ext_count += 1
                if has_double_extension(name):
                    double_ext_count += 1

    # 2. Check files created / written in behavior
    behavior = report.get("behavior", {})
    summary = behavior.get("summary", {})
    files_touched = summary.get("write_files", []) + summary.get("delete_files", [])
    if isinstance(files_touched, list):
        for fpath in files_touched:
            path_str = str(fpath)
            if is_ransom_note_name(path_str):
                note_count += 1
            ext = Path(path_str).suffix.lower()
            if ext in KNOWN_RANSOM_EXTENSIONS:
                suspicious_ext_count += 1
            # Check for double extensions (e.g. .docx.locked, .pdf.wncry)
            stem = Path(path_str).stem
            if Path(stem).suffix:
                double_ext_count += 1

    # 3. Check strings in report
    strings_list = report.get("strings", [])
    if isinstance(strings_list, list):
        # Scan up to 500 strings for performance
        text_corpus = " ".join(str(s) for s in strings_list[:500])
        for kw_regex in RANSOM_KEYWORDS:
            matches = kw_regex.findall(text_corpus)
            keyword_hits += len(matches)

    # 4. Check API call arguments for rename / write of ransom notes
    for proc in behavior.get("processes", []):
        for c in proc.get("calls", []):
            args = c.get("arguments", {})
            if isinstance(args, dict):
                for val in args.values():
                    v_str = str(val)
                    if is_ransom_note_name(v_str):
                        note_count += 1
                    ext = Path(v_str).suffix.lower()
                    if ext in KNOWN_RANSOM_EXTENSIONS:
                        suspicious_ext_count += 1

    ransom_detected = (note_count > 0 or (keyword_hits >= 2 and suspicious_ext_count > 0))

    f_vec: Dict[str, float] = {
        "ransom_note_count": float(note_count),
        "ransom_keyword_hits": float(keyword_hits),
        "ransom_suspicious_ext_count": float(suspicious_ext_count),
        "ransom_double_ext_count": float(double_ext_count),
        "ransom_note_detected": 1.0 if ransom_detected else 0.0,
    }

    return RansomNoteFeatures(
        sample_id=sample_id,
        ransom_note_count=note_count,
        ransom_keyword_hits=keyword_hits,
        suspicious_extension_count=suspicious_ext_count,
        double_extension_count=double_ext_count,
        ransom_note_detected=ransom_detected,
        features_vector=f_vec,
    )
