# MLRan-ext: Modernized Dataset Specification & Metadata Manifest (T-P10-06)

## 1. Overview & Research Motivation

The original MLRan benchmark (JNCA 2026) was collected predominantly on Windows 7 sandboxes with historical goodware spanning 2012–2021. As demonstrated in Phase 3 drift analysis (`reports/drift.md`), **11 out of 12 baseline false positives occur exclusively on modern 2023–2024 benign desktop software**. This is driven by new goodware behaviors:
- Aggressive UPX/Themida packing and protector stubs (elevated entropy).
- Auto-updaters utilizing scheduled tasks and background service injection.
- Modern telemetry and registry tracking.

To mitigate this drift while adhering strictly to academic safety guidelines ([AGENTS.md §4](file:///c:/Users/prabh/OneDrive/Desktop/Randetmlrun/AGENTS.md)), we specify **`MLRan-ext`** as a **metadata-only community dataset contribution**. It provides verified hashes, provenance, VirusTotal telemetry, and behavioral feature vectors without distributing hazardous raw binaries.

---

## 2. Dataset Architecture & Inclusion Criteria

### 2.1 Goodware Expansion Quotas
`MLRan-ext` expands the benign evaluation baseline with **1,000 verified modern Windows 10/11 applications** across five operational categories:

| Category | Target Quota | Key Software Packages | Behavioral Rationale |
|---|---|---|---|
| **Office & Productivity** | 250 samples | LibreOffice, Notion, Obsidian, Foxit Reader, SumatraPDF | Heavy document read/write and temporary file creation |
| **Developer Tools** | 250 samples | VS Code, Git, Python runtimes, Node.js, CMake, Go | High process spawning, compiler I/O, script execution |
| **Utilities & Compression** | 200 samples | 7-Zip, PeaZip, WinRAR, PowerToys, BleachBit | High-entropy bulk compression (potential false-kill trap) |
| **Enterprise & Communication** | 150 samples | Slack, Zoom, Teams, AnyDesk, FileZilla | Network telemetry, auto-updates, background services |
| **Cryptographic Tools** | 150 samples | VeraCrypt, GnuPG, KeePassXC, AxCrypt, AESCrypt | Legitimate full-disk and file encryption operations |

### 2.2 Safety & Verification Rules (Non-Negotiable)
1. **VirusTotal Strict Zero-Detection Rule**: A candidate binary is accepted only if `vt_positives == 0` across $\ge 60$ AV engines with a minimum observation window of 30 days.
2. **Authenticode Signature Verification**: Preference given to binaries signed with valid, non-revoked Microsoft or reputable CA digital certificates.
3. **No Live Binaries in Repository**: Only SHA-256 hashes, provenance URLs, and extracted behavioral feature vectors are shared (`data/processed/`).

---

## 3. Metadata Manifest Schema

Each entry in `MLRan-ext` adheres to the formal JSON schema in `data/processed/mlran_ext_metadata_schema.json`:

```json
{
  "sample_id": "goodware_ext_001",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "file_name": "7z2408-x64.exe",
  "category": "utilities_compression",
  "source_repository": "winget",
  "publisher": "Igor Pavlov",
  "os_platform": "Windows 11 23H2",
  "vt_detection_count": 0,
  "vt_total_engines": 72,
  "vt_first_submission": "2024-08-11T14:22:00Z",
  "file_size_bytes": 1618944,
  "static_entropy": 7.91,
  "is_ransomware": 0,
  "provenance_url": "https://www.7-zip.org/a/7z2408-x64.exe"
}
```

---

## 4. Community Release & Reproducibility Impact

Releasing `MLRan-ext` metadata allows researchers to:
1. Re-evaluate their ransomware detectors on zero-day benign applications without executing unvetted code.
2. Benchmark concept drift mitigation algorithms (e.g. cost-sensitive class weights, sliding-window retraining).
3. Validate endpoint false-positive suppression on modern developer and encryption tools.
