"""Download sample Cuckoo JSON reports from faithfulco/mlran for T-P4-05 prefix prototype."""

import json
from pathlib import Path
import urllib.request

SAMPLES = [
    "10002.json",  # 174 KB
    "10007.json",  # 157 KB
    "10011.json",  # 65 KB
    "10015.json",  # 98 KB
    "10022.json",  # 266 KB
    "10013.json",  # 464 KB
    "10025.json",  # 452 KB
    "10026.json",  # 531 KB
]

BASE_URL = "https://raw.githubusercontent.com/faithfulco/mlran/main/4_cuckoo_parser_scripts/json_reports/"
DEST_DIR = Path("data/raw/cuckoo_samples")

def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for sample in SAMPLES:
        dest_path = DEST_DIR / sample
        if dest_path.exists() and dest_path.stat().st_size > 0:
            print(f"[EXISTS] {sample} ({dest_path.stat().st_size:,} bytes)")
            continue
        url = BASE_URL + sample
        print(f"Downloading {sample} from {url}...")
        try:
            urllib.request.urlretrieve(url, dest_path)
            print(f"  OK ({dest_path.stat().st_size:,} bytes)")
        except Exception as e:
            print(f"  FAILED: {e}")

if __name__ == "__main__":
    main()
