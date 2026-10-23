# 📁 Project Datasets & Feature Catalog

This directory catalogs all datasets, schemas, and telemetry formats used in the **Early Ransomware Detection with Machine Learning & Explainable Dashboard** project.

---

## 1. Overview of Datasets

| Dataset Identifier | Domain | Samples / Scope | Feature Count | Storage Path | Format |
|---|---|---|---|---|---|
| **MLRan RFE Features** | Dynamic Sandbox Behavioral Profiling | 4,880 Executions (3,905 Train / 975 Test) | 483 behavioral attributes | `data/raw/mlran/` | CSV & JSON |
| **MLRan Metadata** | Telemetry, Hashes & Chronology | 4,880 Executions | VirusTotal submission date, SHA256, Family | `data/raw/mlran/` | CSV |
| **RanSMAP Stream Telemetry** | Low-Level Disk I/O & Memory Traces | 12 Families (6 Ransomware, 6 Benign) | Continuous block address, entropy, access size | `data/raw/ransmap/` | CSV time series |
| **Incident Alerts DB** | Real-time Incident Audit Log | Persistent detections & analyst triages | Verdict, confidence, SHAP reasons, MITRE tags | `data/processed/alerts.db` | SQLite 3 |
| **MLRan-Ext Schema** | Community Extension Metadata Standard | Standardized community contribution format | 14 core validation fields | `data/processed/mlran_ext_metadata_schema.json` | JSON Schema |

---

## 2. MLRan Behavioral Dataset (`data/raw/mlran/`)

Derived from Cuckoo Sandbox behavioral analysis across 6.4 million raw execution features, filtered using **Recursive Feature Elimination (RFE)** with strict chronological separation (earliest 80% train, latest 20% test).

### File Manifest & Integrity Checksums

| File Name | Rows | Columns | SHA256 Checksum | Purpose |
|---|---|---|---|---|
| `MLRan_X_train_RFE.csv` | 3,905 | 483 | `AAF75D5754AAC247B93E2A7D0BAA449CCB3EACC08117F50DFA0FB422AFF3DB1F` | Training feature vectors (80% earliest by date) |
| `MLRan_X_test_RFE.csv` | 975 | 483 | `792E7BEA9CCFE8BB056A05BC4751EBF18311C55E548D1B80910214C052EE8E16` | Guarded test feature vectors (20% latest holdout) |
| `MLRan_labels.csv` | 4,880 | 2 | `1E00F2E11E02A34859E8863808422933988C151E8C821A88247798B051227E4F` | Binary labels (`0 = Goodware`, `1 = Ransomware`) |
| `RFE_selected_feature_names_dic.json` | N/A | 483 keys | `2990CF09143C3B8A40D2C6EDC0F794D79B736B06657BB0D5A7F99B7359A1195A` | Mapping from feature column index to human-readable API/string name |
| `mlran_dataset_metadata.csv` | 4,880 | 18 | `0E275F49C2995CC31181D43B7F30E266BE8ECB7E4BF45DCC8BF6CC4CA7637A5A` | VirusTotal first submission date, SHA256, family label |
| `goodware_samples_description.csv` | 2,544 | 4 | `C75D0F56BD490D2FC1E48895A8FA73D9A60802F17D1620D3F08A604D99A0541D` | Description of benign applications (utilities, dev tools, games, office) |
| `ransomware_samples_families_description.csv` | 66 | 3 | `8B79C2FB890843A3FA6D18C8B2957D763ABDCB9D8F76D9FB292734144F0609B0` | Taxonomy of 66 ransomware families represented in the corpus |
| `type_train_sampleids.csv` | 3,905 | 2 | `C897BF35FABC0F16C15FA61A60E55BFA42D7B9D0075D62893FA226F9A80C7120` | Sample identifiers belonging to chronological training split |
| `type_test_sampleids.csv` | 975 | 2 | `7250D3EF5E495DB85E3668412FA16FBADA9EC8ACD4ACA6FA395F774A9344FF50` | Sample identifiers belonging to chronological test split |

### Feature Category Breakdown (483 RFE Variables)

1. **Filesystem & I/O Calls (38%)**: `NtCreateFile`, `NtWriteFile`, `NtDeleteFile`, `SetFileAttributesW`, directory traversal.
2. **Process & Thread Operations (24%)**: `CreateProcessInternalW`, `OpenProcess`, `VirtualAllocEx`, `WriteProcessMemory` (injection indicators).
3. **Registry Persistence & Evasion (21%)**: `RegSetValueExW`, `RegCreateKeyExW`, `RegDeleteValueW` (disabling defenses, autoruns).
4. **String Signatures & PE Header Indicators (17%)**: PE section entropy, compilation artifact strings (e.g. `!this program cannot be run in dos mode`), ransomware extortion keywords.

---

## 3. RanSMAP Telemetry Dataset Specification

RanSMAP captures fine-grained hardware execution metrics via ATA storage commands and memory traces during live execution inside a Celeron/DDR4 testbed.

- **Families Captured**:
  - *Ransomware*: Conti, Darkside, LockBit, REvil, Ryuk, WannaCry
  - *Benign Applications*: AESCrypt, Firefox, Idle, Office, SDelete, Zip
- **Data Channels**:
  - `ata_write.csv`: Timestamp (s + ns), Logical Block Address (LBA), transfer size (bytes), Shannon entropy (0.0 to 1.0), access flag.
  - `mem_write.csv`: Page address, dirty byte ratios, burst access patterns.
- **Windowing Parameters**: Window size $W = 2.0\text{ s}$, stride $S = 1.0\text{ s}$.
- **Download Automation**: Use `python scripts/download_ransmap.py` to stream executions directly from upstream.

---

## 4. Verification and Integrity Assurance

To re-verify the integrity and dimensions of all dataset files across the repository:
```bash
python scripts/organize_datasets.py
```
This utility automatically reads all raw files, confirms SHA256 hashes against published references, and outputs an updated JSON manifest to `datasets/dataset_manifest.json`.
