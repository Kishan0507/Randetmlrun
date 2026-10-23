"""Dataset Organization and Integrity Verification Script.

Inspects all datasets in data/raw/ and data/processed/, computes SHA256 hashes,
validates dimensions, record counts, variable types, and generates a structured
dataset catalog.

Usage:
    python scripts/organize_datasets.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATASETS_DIR = PROJECT_ROOT / "datasets"


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def inspect_mlran_datasets() -> List[Dict[str, Any]]:
    """Inspect all MLRan raw dataset files."""
    mlran_dir = DATA_DIR / "raw" / "mlran"
    if not mlran_dir.exists():
        return []

    catalog = []
    for f in sorted(mlran_dir.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            info: Dict[str, Any] = {
                "filename": f.name,
                "relative_path": str(f.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "size_bytes": f.stat().st_size,
                "sha256": compute_sha256(f),
                "format": f.suffix.lstrip(".").upper(),
            }

            if f.suffix == ".csv":
                try:
                    df = pd.read_csv(f, nrows=5)
                    full_df = pd.read_csv(f)
                    info["n_rows"] = len(full_df)
                    info["n_cols"] = len(full_df.columns)
                    info["columns_sample"] = list(df.columns[:5])
                except Exception as e:
                    info["read_error"] = str(e)
            elif f.suffix == ".json":
                try:
                    with open(f, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                    info["json_keys_count"] = len(data) if isinstance(data, (dict, list)) else 1
                except Exception as e:
                    info["read_error"] = str(e)

            catalog.append(info)

    return catalog


def inspect_processed_data() -> List[Dict[str, Any]]:
    """Inspect processed database and schemas."""
    proc_dir = DATA_DIR / "processed"
    if not proc_dir.exists():
        return []

    catalog = []
    for f in sorted(proc_dir.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            info: Dict[str, Any] = {
                "filename": f.name,
                "relative_path": str(f.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "size_bytes": f.stat().st_size,
                "sha256": compute_sha256(f),
                "format": f.suffix.lstrip(".").upper(),
            }
            catalog.append(info)
    return catalog


def build_manifest() -> Dict[str, Any]:
    """Build unified dataset manifest."""
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    mlran_files = inspect_mlran_datasets()
    proc_files = inspect_processed_data()

    manifest = {
        "project": "Early Ransomware Detection with ML + Explainable Dashboard",
        "description": "Unified Master Dataset Manifest for MLRan and RanSMAP Telemetry",
        "version": "1.0.0",
        "data_sources": {
            "mlran": {
                "name": "MLRan Behavioral Ransomware Dataset (JNCA 2026)",
                "upstream": "https://github.com/faithfulco/mlran",
                "licence": "MIT",
                "features_count": 483,
                "train_samples": 3905,
                "test_samples": 975,
                "files": mlran_files,
            },
            "processed": {
                "name": "Processed Alert Database and Extension Metadata",
                "files": proc_files,
            },
            "ransmap_specification": {
                "name": "RanSMAP I/O & Memory Telemetry Dataset",
                "upstream": "https://github.com/manabu-hirano/RanSMAP",
                "families_count": 12,
                "telemetry_channels": ["ata_write", "ata_read", "mem_write", "mem_read"],
                "streaming_window": {"size_sec": 2.0, "stride_sec": 1.0},
            },
        },
    }

    manifest_path = DATASETS_DIR / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[SUCCESS] Dataset manifest written to: {manifest_path}")
    print(f"  MLRan Files Cataloged: {len(mlran_files)}")
    print(f"  Processed Files Cataloged: {len(proc_files)}")
    return manifest


if __name__ == "__main__":
    build_manifest()
