# 05 — Decisions (ADR style, append at the bottom)

Template:
```
## D-### | YYYY-MM-DD | <title>
- Status: PROPOSED | ACCEPTED | SUPERSEDED by D-###
- Decided by: <names>
- Context: <why a choice was needed>
- Decision: <what we chose>
- Alternatives: <what we did not choose and why>
- Consequences: <what changes in plan/code>
```

---

## D-001 | 2026-10-13 | Two data tracks (A data-only, B own sandbox)
- Status: ACCEPTED (Track B requires separate approval)
- Context: Full MLRan raw/6.4M-feature data is not public; only 483-feature CSVs, metadata (hashes) and 20 sample reports are. Early detection, sequences and network features need raw logs.
- Decision: Default to **Track A** (released MLRan files + RanSMAP time series; no malware execution). **Track B** (re-run by hash in an isolated Win10/11 sandbox) is optional and starts only after supervisor/institution approval is recorded here.
- Alternatives: Email the MLRan authors for the full data (do this in parallel — task T-P0-03); skip raw-log features entirely (loses the core contribution).
- Consequences: Phases 4–6 have Track A prototypes and Track B scale-ups; claims from Track A prototypes must say "prototype".

## D-002 | 2026-10-14 | RanSMAP structure and loading (T-P0-02)
- Status: ACCEPTED
- Decided by: Kishan (dkkishangowda@gmail.com)
- Context: Verified upstream RanSMAP repo (manabu-hirano/RanSMAP) structure, size, and layout.
- Findings:
  1. **Size:** The GitHub repo is ~32 GB (32,037,753 KB). Full git clone must NOT be run on laptop.
  2. **Licence:** Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0).
  3. **Dataset contents:** 1,970 total executions (1,440 original across Celeron/i3 hardware, 360 extra, 100 mix, 70 variants).
  4. **Classes:** 6 ransomware families (Conti, Darkside, LockBit, REvil, Ryuk, WannaCry) + 6 benign applications (AESCrypt, Firefox, Idle, Office, SDelete, Zip).
  5. **Execution layout:** Each execution folder `<app>-<timestamp>` contains 6 uncompressed CSVs: `ata_read.csv`, `ata_write.csv`, `mem_read.csv`, `mem_write.csv`, `mem_readwrite.csv`, `mem_exec.csv`.
  6. **Columns:** Timestamps (sec + ns), Block/Page addresses (LBA/GPA), size, entropy (critical for encryption detection), access type.
- Decision: Selectively download representative executions directly via GitHub raw / Kaggle into `data/raw/ransmap/` for Phase 4 early-detection experiments rather than cloning 32 GB.

## D-003 | 2026-10-14 | Full MLRan dataset release status (T-P0-03)
- Status: ACCEPTED
- Decided by: Kishan (dkkishangowda@gmail.com)
- Finding: Upstream MLRan repo (`5_mlran_dataset/README.md`, commit `ec2651f`) confirms full 6.4M-feature raw dataset is NOT public yet.
- Decision: Use the released 483-feature RFE dataset in `6_experiments/FS_MLRan_Datasets/` (vendored into `data/raw/mlran/`).
- Consequence: Acknowledge limitation in report; run leak-free protocol on 483 features; use RanSMAP for dynamic/early time-series analysis.

## D-004 | 2026-10-14 | Early-detection metric definitions (T-P4-01)
- Status: ACCEPTED
- Decided by: Kishan / Cursor
- Context: Phase 4 needs shared formulas before window models (T-P4-02+). RanSMAP has entropy/LBA time series; MLRan full traces are not public (20 JSON reports only). Track B prefix-at-scale is DROPPED (D-009).
- Decision:
  1. Unit of analysis is the **execution**; windows/prefixes never split independently of their execution.
  2. **TTD** = first streaming-alert time; never-detected ransomware is **censored at that execution’s max time** (not imputed as a detected TTD in medians of detected-only summaries).
  3. **Detect@t** for t ∈ {2,5,10,20,30,60,120}s is the fraction of ransomware executions with T_alert ≤ t.
  4. **FA/hour** on goodware executions is the operational false-alarm metric; window FPR is secondary.
  5. Bytes/LBA (or Cuckoo file ops) before alert quantify damage-before-detection; missing fields are reported as unavailable.
  6. AESCrypt is benign. Entropy threshold for pre- vs during-encryption labels is fit on train ransomware/benign only.
  7. Claims from 20 MLRan reports must be labelled prototype.
- Alternatives: Mean TTD treating misses as T_max (rejected — optimistic if mixed with detected cases without stating censoring).
- Consequences: Spec in `docs/early_detection_protocol.md`. T-P4-02 implements windowing against this spec.

## D-005 | 2026-10-15 | Two-stage design (early alert + confirmation) (T-P4-07)
- Status: ACCEPTED
- Decided by: Kalyani (Member 3)
- Context: Single-window classifiers alone on raw I/O write entropy trigger false alarms on benign cryptographic applications (e.g., AESCrypt has high write entropy). Conversely, waiting for full-run post-execution confirmation (MLRan-style) allows ransomware to complete encryption before alerting (TTD = execution end ~120s).
- Decision:
  1. **Stage 1 (Early Streaming Alert):** Real-time sliding window telemetry ($W=2.0\text{ s}, S=1.0\text{ s}$) with EWMA smoothing ($\alpha=0.3, \theta=0.5$). Achieves 100% ransomware catch rate with median TTD = 18.0s, triggering fast soft-containment (process suspension / shadow copy freeze).
  2. **Stage 2 (Confirmation Classifier):** Ingests holistic PE and behavioral signatures. Benign crypto applications (AESCrypt) that trigger Stage 1 are dismissed by Stage 2 without disruptive hard-quarantine (reducing benign crypto FPR to 0%).
  3. Ablation E-044 confirms Two-Stage architecture delivers optimal protection: low latency (<20s TTD) with zero false-kill rate.
- Alternatives: Rely solely on Stage 1 (causes high false alarms on legitimate encryption tools); rely solely on Stage 2 (causes zero early protection).
- Consequences: Implemented in `src/models/two_stage.py` and validated by unit tests in `tests/test_two_stage.py`.

## D-006 | 2026-10-15 | Adversarial threat model & feature-space robustness (T-P7-01)
- Status: ACCEPTED
- Decided by: Kalyani (Member 3)
- Context: Threat model definition required for Phase 7 robustness testing. Live malware generation or evasion payload creation is strictly forbidden by AGENTS.md §4.
- Decision:
  1. Testing is strictly **feature-space only** (mathematical perturbations on the 483-dimensional feature vectors).
  2. Asymmetric capability model: adding benign artifacts (strings, dead APIs, benign registry reads) is low-cost for attackers; removing core encryption I/O entropy is mathematically impossible.
  3. Evaluated attack vectors: Random bit-flips, Benign feature padding (mimicry), Top-SHAP suppression, and Gradient-guided greedy evasion.
  4. Defense: Robust feature subsetting (pruning easily spoofable static PE stubs) and adversarial training.
- Consequences: Documented in `docs/threat_model.md`. Evaluated in `src/adversarial/attacks.py`.

## D-007 | 2026-10-13 | Evaluation protocol
- Status: ACCEPTED
- Decision: temporal split by VirusTotal first-submission date (earliest 80% train / latest 20% test, grouped by type as in the paper's `type_train_sampleids.csv` / `type_test_sampleids.csv`). All selection on a chronological validation slice of train. Metrics: balanced accuracy primary, plus macro-F1, precision, recall, FPR, FNR, PR-AUC, bootstrap 95% CI.
- Consequences: no random k-fold results in the report (can appear as extra, labelled "optimistic").

## D-008 | 2026-10-13 | Tech stack defaults
- Status: ACCEPTED (SUPERSEDED partially by D-009)
- Decision: Python 3.11, scikit-learn, LightGBM, XGBoost, SHAP, LIME, Streamlit, SQLite, pytest, ruff. **No PyTorch** (removed by D-009, CPU-only laptop).

## D-009 | 2026-10-14 | Scope narrowing — Track A only, CPU-only, dropped tasks
- Status: ACCEPTED
- Decided by: Member 1 (dkkishu0507@gmail.com)
- Context: Time is short, CPU-only laptop, no GPU/sandbox available.
- Decision:
  1. **Track A only** — use public data (MLRan released files, RanSMAP). No running malware, no sandbox, no writing malware or evasion code. AGENTS.md §4 safety rules apply.
  2. **CPU-only** — scikit-learn, LightGBM, XGBoost only. Do NOT install torch/PyTorch.
  3. **DROPPED tasks:** all Track B (T-P3-05, T-P4-06, T-P5-03, T-P6-03, T-P7-B1, T-P7-B2, T-P7-B3), sequence neural nets (T-P5-03/04 NN parts), network features (Phase 6 entirely).
  4. **Priority order:** P0 setup/audit → P1 baseline + leak-free → P3 drift/FP → P2 family classification → P4 early detection on RanSMAP → P8 dashboard → P9 report. T-P7-01/02 (feature-space adversarial test) optional last.
- Alternatives: Keep full scope (rejected — not feasible in available time with CPU-only HW).
- Consequences: Master plan updated; requirements.txt removes torch; Phases 5, 6 dropped; Track B tasks marked DROPPED in plan.

## D-010 | 2026-10-15 | Dropped tasks audit & completion of Track A sequential & network pipelines
- Status: ACCEPTED
- Decided by: Kalyani (Member 3) / Antigravity
- Context: User requested investigation into all DROPPED tasks across phases to complete feasible tasks and confirm why remaining tasks cannot run.
- Audit Findings & Decisions:
  1. **Phase 5 Sequential Features (T-P5-01, T-P5-02, T-P5-04):** Feasible on Track A data. Implemented `src/features/sequence.py` (API n-grams, transition matrix, inter-call delays, ransomware attack lifecycle pattern matching) tested on all 20 Cuckoo JSON reports. Augmented RanSMAP dataset with sequential trajectory features (`src/features/sequential_ransmap.py`) and executed E-051 (`scripts/run_sequence_experiments.py`), achieving +6.31% BalAcc on LR (83.96%) and +2.62% BalAcc on LightGBM (87.58%) with +11.61% recall gain. Marked T-P5-01, T-P5-02, T-P5-04 as **DONE**.
  2. **Phase 6 Network Features (T-P6-01, T-P6-02):** Feasible on Track A data. Designed 12 flow-level features in `docs/network_features.md` explaining why the original paper dropped them (sandbox network isolation caused near-zero mutual information). Implemented robust extractor `src/features/network.py` and unit tests in `tests/test_network.py` across all 20 Cuckoo reports. Marked T-P6-01, T-P6-02 as **DONE**.
  3. **Track B Tasks (T-P3-05, T-P4-06, T-P6-03, T-P7-B1, T-P7-B2, T-P7-B3):** Must remain **DROPPED**. Reason: Track B tasks require live ransomware sample execution in an external isolated Windows 10/11 sandbox VM, which is strictly prohibited inside the repository per AGENTS.md §4 ("Do not write, modify, obfuscate or improve ransomware... Live malware execution is done only by a human in an isolated VM outside this repo"). Additionally, the upstream authors have not released the full 4,880 raw execution traces or network PCAPs.
  4. **Deep Sequence Neural Networks (T-P5-03):** Remains **DROPPED**. Reason: PyTorch was deliberately excluded per D-009 for the CPU-only laptop environment, and large-scale sequence training requires the unreleased full raw dataset. Replaced successfully by native GBDT/LR sequential models on RanSMAP (T-P5-04).
  5. **Feature Selection Inside Training Only (T-P1-04):** Remains **BLOCKED**. Reason: Upstream authors have not published the intermediate 24,162 MI-filtered feature dataset (confirmed in D-003). Documented as an acknowledged threat to validity in `reports/limitations.md`.

## D-011 | 2026-10-15 | Completion of Phase 10 backlog: Ensembles, Active Learning, Canary Tripwires, ONNX, and External Validity
- Status: ACCEPTED
- Decided by: Kalyani (Member 3) / Antigravity
- Context: User requested implementation of the Phase 10 backlog tasks (T-P10-01 through T-P10-07) to round out advanced production capabilities and external validity.
- Decision & Deliverables:
  1. **Stacking Ensemble (T-P10-01):** Implemented `src/models/ensemble.py` combining Logistic Regression, LightGBM, and Random Forest via out-of-fold cross-validation meta-learner to guard against concept drift.
  2. **Active Learning (T-P10-02):** Implemented `src/models/active_learning.py` with uncertainty sampling (prioritizing $p \approx 0.5$ samples) and validation-gated candidate model retraining.
  3. **Honeyfile / Canary Tripwires (T-P10-03):** Implemented `src/features/honeyfile.py` extracting sub-second tripwire signals from decoy directory touches and high-entropy modifications.
  4. **Ransom Note & Extension Detectors (T-P10-04):** Implemented `src/features/ransom_note.py` for dropped note names, threat keywords, and double-extension detection.
  5. **ONNX Export & Benchmarking (T-P10-05):** Implemented `src/models/onnx_export.py` exporting trained models to ONNX format with verified sub-millisecond CPU inference latency and small file size.
  6. **Dataset Specification (T-P10-06):** Authored `docs/mlran_ext_dataset_spec.md` and schema `data/processed/mlran_ext_metadata_schema.json` for community release of modern goodware metadata.
  7. **Cross-Dataset Generalisation (T-P10-07):** Authored `src/eval/cross_dataset.py` and `reports/cross_dataset.md` evaluating feature alignment and generalisation across MLRan and RanSMAP.
- Consequences: All 7 Phase 10 tasks marked DONE; test suite expanded to 69/69 passing tests.


