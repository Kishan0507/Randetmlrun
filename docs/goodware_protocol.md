# Goodware Expansion Protocol (T-P3-04)

**Author:** Kishan (dkkishangowda@gmail.com)  
**Date:** 2026-10-14  
**Status:** APPROVED (Protocol for mitigating source bias and concept drift)

---

## 1. Motivation and Objective

Audit item **A14** and our empirical false positive analysis (**T-P3-02**) confirmed that the MLRan goodware set suffers from complete source bifurcation:
1. **100% of existing goodware** comes from a single aggregator (`Software Informer`).
2. Training goodware (2006–2018) had only **43.0%** prevalence of standard PE packaging stubs (`STRING:!this program cannot be run in dos mode.`), whereas 100% of the 2023–2024 test false positives (Zoom, PDFCreator, VALORANT, Avast) contained this stub and dynamic injection APIs.
3. To build a robust, production-grade ransomware detector, the benign corpus must be expanded with modern, diverse Windows software.

This protocol defines the collection, curation, deduplication, and feature extraction pipeline for `MLRan-ext`.

---

## 2. Collection Sources and Quotas

To eliminate aggregator bias, software must be drawn equally from 5 distinct distribution channels:

| Source Channel | Tool / Mechanism | Examples | Quota |
|---|---|---|---|
| **Windows Package Manager (`winget`)** | Official Microsoft CDN | Microsoft PowerToys, VS Code, Git, 7-Zip, Notepad++ | 25% |
| **Chocolatey Community Repository** | `choco download` | VLC, Blender, GIMP, FileZilla, LibreOffice | 20% |
| **Enterprise / Office Suites** | Vendor Direct Downloads | Zoom, Slack, Cisco Webex, Teams, Adobe Acrobat Reader | 20% |
| **Portable Apps Repository** | `portableapps.com` | PuTTY, KeePass, Audacity, Inkscape (unwrapped PEs) | 15% |
| **Developer & System Tools** | Sysinternals / GitHub Releases | Process Explorer, Wireshark, Autoruns, curl, Python | 20% |

---

## 3. Strict Verification & Integrity Rules

Every collected sample must satisfy:
1. **VirusTotal Zero-Detection Rule:**
   - Must have 0 detections across all $\ge 70$ VirusTotal security vendors at collection time.
   - Re-verified 30 days after collection to guard against delayed malware classification.
2. **First-Seen Timestamp Validation:**
   - Samples must have VirusTotal `first_submission_date` $\ge$ 2023-01-01 to ensure recentness.
3. **Deduplication:**
   - SHA-256 hash deduplication against existing MLRan samples.
   - Authenticode signature and certificate thumbprint cataloging.

---

## 4. Metadata Schema

Every added sample is recorded in `data/processed/mlran_ext_goodware_metadata.csv` with the following schema:

```csv
sample_id,sha256,sha1,md5,title,developer,version,source_channel,download_url,category,vt_detections,first_submission_date,architecture
```

---

## 5. Feature Extraction Pipeline

1. **Sandboxing Environment:** Isolated Windows 10/11 VM (BitVisor / CAPEv2).
2. **Execution Parameters:** 120-second dynamic trace with simulated human interaction (mouse movement, dialogue confirmation).
3. **Feature Mapping:** Extracted API calls, registry accesses, file operations, and entropy statistics projected directly onto the 483-feature space via `src/data/load_mlran.py`.
