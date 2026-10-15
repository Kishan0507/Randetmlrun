"""Download representative RanSMAP executions from GitHub for Phase 4.

Downloads ONLY ata_write.csv (primary — has entropy for encryption detection)
and mem_write.csv (secondary — memory write patterns) to keep download size
manageable. Full structure per D-002:

  dataset/original/<cpu>/<ram>/<Family>/<Family-timestamp>/
    ata_read.csv, ata_write.csv, mem_read.csv, mem_write.csv,
    mem_readwrite.csv, mem_exec.csv

We download into data/raw/ransmap/<Family>/<execution-name>/ with only the
two critical CSVs.  This still gives ~40-60 MB per execution.

Columns (no header in raw files):
  col0: timestamp_sec (Unix epoch)
  col1: timestamp_ns
  col2: LBA or GPA (block/page address)
  col3: size (bytes)
  col4: entropy (float 0-1, critical for encryption detection)
  col5: access_type (int)

Usage:
    python scripts/download_ransmap.py [--dest data/raw/ransmap] [--max-per-family 3]
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests

GITHUB_API = "https://api.github.com"
REPO = "manabu-hirano/RanSMAP"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"

# Use one specific hardware config to keep things consistent
HW_PATH = "dataset/original/celeron-gen6/ddr4-2133-16g"

# All 12 families in RanSMAP
FAMILIES: Dict[str, str] = {
    # Ransomware (6 families)
    "Conti": "ransomware",
    "Darkside": "ransomware",
    "LockBit": "ransomware",
    "REvil": "ransomware",
    "Ryuk": "ransomware",
    "WannaCry": "ransomware",
    # Benign (6 apps)
    "AESCrypt": "benign",
    "Firefox": "benign",
    "Idle": "benign",
    "Office": "benign",
    "SDelete": "benign",
    "Zip": "benign",
}

# Download only these CSVs (the ones critical for early detection)
DOWNLOAD_CSVS = ["ata_write.csv"]  # Start with just the primary signal


def get_session() -> requests.Session:
    """Create a requests session with GitHub token if available."""
    session = requests.Session()
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        session.headers["Authorization"] = f"token {token}"
    session.headers["Accept"] = "application/vnd.github.v3+json"
    return session


def list_execution_dirs(session: requests.Session, family: str) -> List[str]:
    """List execution directory names for a family using GitHub API."""
    path = f"{HW_PATH}/{family}"
    url = f"{GITHUB_API}/repos/{REPO}/contents/{path}"
    resp = session.get(url, timeout=30)
    if resp.status_code == 403:
        print(f"  [WARN] Rate limited for {path}; waiting 60s...")
        time.sleep(60)
        resp = session.get(url, timeout=30)
    if resp.status_code != 200:
        print(f"  [WARN] Could not list {path}: HTTP {resp.status_code}")
        return []
    items = resp.json()
    dirs = [item["name"] for item in items if item["type"] == "dir"]
    dirs.sort()
    return dirs


def download_file_streaming(
    session: requests.Session,
    url: str,
    out_path: Path,
    max_bytes: int = 0,
) -> bool:
    """Download a file via streaming. Optionally truncate at max_bytes."""
    try:
        resp = session.get(url, stream=True, timeout=120)
        if resp.status_code != 200:
            return False
        total = 0
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
                total += len(chunk)
                if max_bytes > 0 and total >= max_bytes:
                    break
        resp.close()
        return True
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False


def download_execution(
    session: requests.Session,
    family: str,
    exec_name: str,
    dest_dir: Path,
    max_bytes: int = 0,
) -> bool:
    """Download critical CSVs for a single execution."""
    exec_dir = dest_dir / family / exec_name
    exec_dir.mkdir(parents=True, exist_ok=True)

    all_ok = True
    for csv_file in DOWNLOAD_CSVS:
        out_path = exec_dir / csv_file
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"    {csv_file}: already exists ({out_path.stat().st_size:,} bytes)")
            continue

        url = f"{RAW_BASE}/{HW_PATH}/{family}/{exec_name}/{csv_file}"
        print(f"    Downloading {csv_file}...", end=" ", flush=True)
        ok = download_file_streaming(session, url, out_path, max_bytes=max_bytes)
        if ok:
            size = out_path.stat().st_size
            print(f"OK ({size:,} bytes)")
        else:
            print("FAILED")
            all_ok = False

    return all_ok


def create_manifest(dest_dir: Path) -> None:
    """Write a manifest CSV listing all downloaded executions."""
    manifest_path = dest_dir / "manifest.csv"
    rows = []
    for family_dir in sorted(dest_dir.iterdir()):
        if not family_dir.is_dir() or family_dir.name.startswith("."):
            continue
        family = family_dir.name
        label = FAMILIES.get(family, "unknown")
        for exec_dir in sorted(family_dir.iterdir()):
            if not exec_dir.is_dir():
                continue
            csvs = [f.name for f in exec_dir.iterdir() if f.suffix == ".csv"]
            total_size = sum(
                f.stat().st_size for f in exec_dir.iterdir() if f.suffix == ".csv"
            )
            rows.append({
                "family": family,
                "label": label,
                "execution": exec_dir.name,
                "n_csvs": len(csvs),
                "total_bytes": total_size,
                "path": str(exec_dir.relative_to(dest_dir)),
            })

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "family", "label", "execution", "n_csvs", "total_bytes", "path"
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[INFO] Manifest written to {manifest_path} ({len(rows)} executions)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download representative RanSMAP data")
    parser.add_argument(
        "--dest", default="data/raw/ransmap", help="Destination directory"
    )
    parser.add_argument(
        "--max-per-family",
        type=int,
        default=3,
        help="Max executions to download per family (default: 3)",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=0,
        help="Max bytes per file (0 = full download). Use e.g. 5000000 for ~5MB sample",
    )
    parser.add_argument(
        "--families",
        nargs="*",
        default=None,
        help="Specific families to download (default: all)",
    )
    args = parser.parse_args()

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    session = get_session()
    total_downloaded = 0

    families = args.families or list(FAMILIES.keys())

    for family in families:
        if family not in FAMILIES:
            print(f"[WARN] Unknown family '{family}', skipping")
            continue

        label = FAMILIES[family]
        print(f"\n{'='*60}")
        print(f"Family: {family} ({label})")
        print(f"{'='*60}")

        # Count already-downloaded executions
        family_dir = dest / family
        existing_count = 0
        if family_dir.exists():
            existing_count = sum(
                1
                for d in family_dir.iterdir()
                if d.is_dir() and any(d.glob("*.csv"))
            )

        if existing_count >= args.max_per_family:
            print(f"  Already have {existing_count} executions, skipping")
            total_downloaded += existing_count
            continue

        needed = args.max_per_family - existing_count

        print(f"  Listing executions...")
        exec_dirs = list_execution_dirs(session, family)
        if not exec_dirs:
            print(f"  No executions found!")
            continue

        print(f"  Found {len(exec_dirs)} executions, downloading {needed}")
        downloaded = 0

        for exec_name in exec_dirs:
            if downloaded >= needed:
                break

            print(f"  [{downloaded+1}/{needed}] {exec_name}")
            ok = download_execution(
                session, family, exec_name, dest, max_bytes=args.max_bytes
            )
            if ok:
                downloaded += 1
            time.sleep(0.5)

        total_downloaded += existing_count + downloaded
        print(f"  Total for {family}: {existing_count + downloaded}")

    create_manifest(dest)
    print(f"\n[DONE] Total executions available: {total_downloaded}")


if __name__ == "__main__":
    main()
