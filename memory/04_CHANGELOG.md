# 04 — Changelog (newest on top, append at the TOP)

## Entry template
```
## C-### | YYYY-MM-DD | <Task/Patch IDs>
- Contributor (human): <name>
- Agent / IDE: <Cursor | Antigravity | none> (<model if known>)
- What changed: <1–5 bullets, files touched>
- Why: <reason / plan reference>
- Verification: <tests run, metrics, screenshots>
- Plan impact: <none | tasks added/changed>
- Follow-ups: <what the next person should do>
```

## C-010 | 2026-10-15 | T-P9-01, T-P9-02, T-P9-03, T-P9-04
- Contributor (human): Kalyani (Member 3)
- Agent / IDE: Antigravity
- What changed:
  - T-P9-01: Master experiment tables and reproducibility script (`scripts/reproduce_all.py`, `reports/final_tables.md`) with 16 experiments traced across all phases (E-001 through E-071).
  - T-P9-02: Comprehensive ablation study (`reports/ablations.md`) with systematic on/off evaluation of calibration, drift mitigation, streaming rules, two-stage architecture, and adversarial hardening — including honest negative results (FPR/recall trade-offs).
  - T-P9-03: Limitations and threats to validity (`reports/limitations.md`) covering Track A vs Track B scope, source bifurcation (A14), small RanSMAP families, VT first-submission proxy, RFE test snooping (A1), sandbox realism, adversarial feature-space caveats, and 10 summary threats with severity ratings.
  - T-P9-04: Comprehensive final project report (`reports/final_report.md`) synthesising all 9 phases, contributor credits, key performance numbers, improvements over MLRan paper (10 dimensions), reproducibility guide, repository structure, and complete experiment index.
- Why: Complete Phase 9 deliverables (Final Evaluation Report & Write-up). All Track A work is now finished.
- Verification: All 4 artifacts written and cross-referenced; master plan T-P9-01..04 marked DONE; test suite integrity maintained.
- Plan impact: T-P9-01 through T-P9-04 marked DONE. Phase 9 is 100% complete! All Track A phases (0, 1, 2, 3, 4, 7, 8, 9) are now DONE.
- Follow-ups: Only Phase 10 backlog items remain (optional extras). Project is feature-complete for Track A.

---

## C-009 | 2026-10-15 | T-P8-01, T-P8-02, T-P8-03, T-P8-04, T-P8-05, T-P8-06
- Contributor (human): Kalyani (Member 3)
- Agent / IDE: Antigravity
- What changed:
  - T-P8-01: Built explanation service (`src/explain/reasons.py`, `configs/reasons.yaml`) computing analytical linear SHAP attributions in ~0.015s (< 1.0s acceptance criteria); maps raw 483 technical features to plain-language reasons, categories, and MITRE ATT&CK techniques with automatic prefix fallbacks.
  - T-P8-02: Created production inference engine and FastAPI prediction service (`src/app/api.py`); supports calibrated probabilities, top-5 reasons, and standard version string (`v2.1.0`) in every response.
  - T-P8-03: Built Live Sample Inspector in Streamlit (`dashboard/app.py`) with sample selection from guarded MLRan test set or custom CSV upload, visual threat verdict banner, confidence gauge, Plotly SHAP horizontal bar chart, and 3 nearest training neighbors using cosine similarity.
  - T-P8-04: Built Streaming Execution Replay mode in `dashboard/app.py` replaying real RanSMAP I/O telemetry with interactive time scrubber, real-time risk score curves, alert markers, and disk bytes / LBAs written counters.
  - T-P8-05: Built SQLite threat alert database (`src/app/alert_db.py`, `data/processed/alerts.db`) for alert logging, status workflows (QUARANTINED, DISMISSED, INVESTIGATING), CSV export, and an interactive Model Card page.
  - T-P8-06: Conducted usability evaluation across 3 reviewers, documented findings and fixes in `reports/usability.md`.
  - Added unit test suites (`tests/test_explain_and_api.py`, `tests/test_dashboard.py`); all 39 tests across the repository pass green.
- Why: Complete Phase 8 deliverables (Explainability & Interactive Dashboard).
- Verification: 39/39 pytest tests passing; dashboard tested and imported without error; SQLite persistence verified.
- Plan impact: T-P8-01 through T-P8-06 marked DONE. Phase 8 is 100% complete!
- Follow-ups: Proceed to Phase 7 (Adversarial Robustness) or Phase 9 (Final Evaluation Report & Artifacts).

---

## C-008 | 2026-10-15 | T-P4-02, T-P4-03, T-P4-04, T-P4-05, T-P4-07
- Contributor (human): Kalyani (Member 3)
- Agent / IDE: Antigravity
- What changed:
  - T-P4-02: Built RanSMAP time-series execution loader and windowing engine (`src/data/ransmap.py`, `scripts/download_ransmap.py`); downloads only critical ATA write CSVs (under 5MB/file); extracts 21 temporal/entropy/locality features per 2-second window ($W=2.0\text{s}, S=1.0\text{s}$); enforces leak-free execution and family splits.
  - T-P4-03 (E-040): Built baseline window classifiers (`src/models/window_classifier.py`); evaluated under 5-fold execution-grouped CV (Random Forest BalAcc = 85.28%, LightGBM BalAcc = 84.96%, LR BalAcc = 77.64%) and Leave-One-Family-Out (LOFO) generalisation across Conti, LockBit, AESCrypt, Firefox, Office; ranked top features (`lba_sequential_frac`, `entropy_max`, `write_count`, `entropy_median`, `burst_count`).
  - T-P4-04 (E-041): Implemented and benchmarked streaming decision rules (`src/eval/streaming.py`) including RAW, EWMA ($\alpha=0.3$), EWMA Conservative ($\alpha=0.2, \theta=0.7$), and k-of-n ($k=2, n=3$); demonstrated that EWMA Conservative achieves 100% ransomware catch rate with 0.00 FA/hour and 0.0% execution FPR at median TTD = 21.0s, preventing data loss (saving bulk storage).
  - T-P4-05 (E-042): Downloaded sample Cuckoo JSON reports and built dynamic prefix extractor prototype (`src/features/prefix.py`, `scripts/download_cuckoo_samples.py`); verified monotonic call progression across prefix cutoffs $t \in [2, 5, 10, 20, 30, 60, 120]\text{s}$; documented Track B prerequisites for full scale.
  - T-P4-07 (E-044, D-005): Implemented two-stage detection architecture (`src/models/two_stage.py`) combining fast low-latency streaming alert (<20s TTD) with holistic PE/behavioral confirmation, eliminating false alarms on benign cryptographic applications (AESCrypt FPR reduced from 100% to 0%).
  - Added full test suites (`tests/test_ransmap.py`, `tests/test_early_detection.py`, `tests/test_prefix.py`, `tests/test_two_stage.py`); all 34 tests in the repository pass green.
  - Published comprehensive evaluation report in `reports/early_detection.md`.
- Why: Complete all Track A deliverables for Phase 4 (Early Detection).
- Verification: 34/34 pytest tests passing; `scripts/run_early_detection.py` outputs clean metrics table and markdown report.
- Plan impact: T-P4-02, T-P4-03, T-P4-04, T-P4-05, T-P4-07 marked DONE. Phase 4 is 100% complete!
- Follow-ups: Proceed to Phase 8 (Explainability & Dashboard) or Phase 7 (Feature-space adversarial robustness).

---

## C-007 | 2026-10-15 | T-P2-01, T-P2-02, T-P2-03, T-P2-04, T-P2-05, T-P4-01
- Contributor (human): Karthikey / Kishan
- Agent / IDE: Antigravity
- What changed:
  - T-P2-01: Multi-model comparison on 483 sparse features across 8 architectures (LR L1/L2, LinearSVC, DT, RF, Extra Trees, LightGBM, XGBoost, MLP) using expanding temporal CV. Best regularized model is L2 Logistic Regression (CV 96.33%, Test BalAcc 98.18% [97.25%, 98.98%]).
  - T-P2-02: Calibrated probabilities with Platt scaling on chronological validation slice; implemented operating threshold tuning under 1% FPR budget (`src/models/calibrate.py`, `configs/operating_point.yaml`, `reports/reliability_curve.png`).
  - T-P2-03: Solved extreme class imbalance in family classification using class-weighted Balanced Logistic Regression, beating the paper's 47.07% balanced accuracy by +4.46% (reaching 51.53% BalAcc, `reports/family_recall.csv`).
  - T-P2-04: Implemented unknown family rejection via One-Vs-Rest confidence scoring; evaluated novel zero-day generalization via Leave-One-Family-Out (LOFO) across top 5 families, detecting 97.95% of novel ransomware samples.
  - T-P2-05: Benchmarked model latency and memory footprints (LR delivers 0.014 ms/sample and 9.2 KB footprint).
  - Configured `pytest.ini` with `pythonpath = .` and verified all 17 unit tests pass cleanly in `.venv`.
  - T-P4-01: Confirmed early-detection protocol specification in `docs/early_detection_protocol.md`.
- Why: Complete Phase 2 deliverables and establish leak-free foundation for early-detection time-series (Phase 4).
- Verification: 17/17 pytest tests pass green; all generated models, YAML configs, and Markdown reports verified.
- Plan impact: T-P2-01 through T-P2-05 and T-P4-01 marked DONE. Phase 2 complete!
- Follow-ups: Proceed with Phase 4 time-series execution loader (T-P4-02 on RanSMAP).

---

## C-006 | 2026-10-14 | T-P3-01, T-P3-02, T-P3-03, T-P3-04
- Contributor (human): Kishan (dkkishangowda@gmail.com)
- Agent / IDE: Antigravity
- What changed:
  - Created and ran `scripts/drift_and_fp_analysis.py` to evaluate temporal concept drift, false positive attribution, and drift mitigation.
  - T-P3-01: Analyzed test set performance by year (2021–2024); calculated Area Under Time (AUT = 98.54%); confirmed monotonic FPR growth from 0.0% (2021) to 3.03% (2024). Generated `reports/drift.md`.
  - T-P3-02: Conducted error analysis of the 12 false positives; matched application titles (Zoom, PDFCreator, Intel BT, VALORANT, CyberGhost, Avast); identified 3 root causes:
    1. Static compilation stub artifact (`STRING:!this program cannot be run in dos mode.`, w=+2.599, present in 12/12 FPs).
    2. Dynamic library resolution and memory allocation (`LdrGetProcedureAddress` in 11/12, `NtAllocateVirtualMemory` in 8/12).
    3. Compression triggering high section entropy (`SIGNATURE:packer_entropy` in 5/12).
    Generated `reports/fp_analysis.md`.
  - T-P3-03: Evaluated 5 drift mitigation strategies (Cost-sensitive loss, recency weighting, sliding window, calibrated thresholding); showed that cost-weighting goodware (CW=1.5) improves balanced accuracy to 98.28% and cuts FPR, while threshold tuning cuts recent FPs by >60%.
  - T-P3-04: Created goodware expansion protocol `docs/goodware_protocol.md` defining multi-source ingestion (winget, choco, enterprise, portable) and VT 0-detection criteria to eliminate source bias.
  - Logged E-030, E-031, E-032 in `memory/09_EXPERIMENT_LOG.md`.
- Why: Concept drift analysis and false positive mitigation (Phase 3).
- Verification: Scripts executed cleanly; detailed Markdown reports generated; master plan updated.
- Plan impact: T-P3-01, T-P3-02, T-P3-03, T-P3-04 marked DONE. Phase 3 complete!
- Follow-ups: Proceed to Phase 2 (T-P2-01..03 model comparison & family classification).

---

## C-005 | 2026-10-14 | T-P1-01, T-P1-02, T-P1-03, T-P1-05
- Contributor (human): Kishan (dkkishangowda@gmail.com)
- Agent / IDE: Antigravity
- What changed:
  - Built evaluation metrics module `src/eval/metrics.py` (bal acc, macro-F1, precision, recall, FPR, FNR, PR-AUC, confusion matrix, 95% bootstrap CI via 1,000 resamples).
  - Built leak-free temporal evaluation protocol `src/eval/protocol.py` with `TestSnoopingGuardError`, chronological validation slice (last 20% of train period), and expanding-window CV.
  - Implemented and ran `scripts/reproduce_baseline.py`:
    - Exactly reproduced paper Table 6 and Fig 12 confusion matrix for Logistic Regression: TN=498, FP=12, FN=6, TP=459, Balanced Accuracy 98.18% [97.25%, 98.98%], Accuracy 98.15%.
    - Evaluated DT, RF, Extra Trees, LightGBM with 95% bootstrap CIs.
    - Evaluated models on leak-free chronological validation slice (E-003): Extra Trees achieved 98.64% [97.45%, 99.49%] BalAcc; Decision Tree suffered severe temporal degradation (87.79% BalAcc, 120 FNs).
  - Generated full baseline reproduction report in `reports/baseline_repro.md`.
  - Logged experiments E-001, E-002, E-003 in `memory/09_EXPERIMENT_LOG.md`.
- Why: Baseline reproduction and leak-free evaluation protocol (Phase 1).
- Verification: 11 unit tests green; exact confusion matrix match (498/12/6/459); full bootstrap CIs computed.
- Plan impact: T-P1-01, T-P1-02, T-P1-03, T-P1-05 marked DONE; T-P1-04 marked BLOCKED by upstream MI-feature non-release. Phase 1 complete!
- Follow-ups: Proceed to Phase 3 (T-P3-01..03 concept drift & false positive analysis).

---

## C-004 | 2026-10-14 | T-P0-05
- Contributor (human): Kishan (dkkishangowda@gmail.com)
- Agent / IDE: Antigravity
- What changed:
  - Created automated verification script `scripts/verify_audit.py` to audit paper claims A1–A14 against the raw MLRan dataset and paper text.
  - Audited and CONFIRMED all 14 items in `memory/03_PAPER_AUDIT.md`:
    - A1: Test set snooping in RFE (Alg 2 line 17 uses test set balanced accuracy).
    - A2: Caption errors (XGBoost named in caption of Table 5/6).
    - A3: Mathematical inconsistency in Table 5 (F1=98.41 reported with P=R=93.85).
    - A4: Abstract cherry-picking class-specific metrics to claim up to 98.9%/98.7%.
    - A5-A6: Table 1 swapped ShieldFS columns and Table 7 vs text STR discrepancy.
    - A7: Date ranges: Goodware (2006-2024), Ransomware (2008-2024).
    - A8: 65 classes = 1 goodware (class 0) + 64 ransomware families (classes 1-64).
    - A9: 2% of 24,162 features = 483 features; notation error |X_train| instead of |F|.
    - A10: Solver discrepancy: saga in Alg 2 vs liblinear/lbfgs in Table 9.
    - A11: Sample and family count mismatches in Fig 6 vs text.
    - A12: 81.0% (413/510) of test goodware are 2023-2024, creating a massive base-rate confounder for the 11/12 false positives.
    - A13: Top SHAP feature `STRING:!this program cannot be run in dos mode.` reflects benign installer wrappers (43% train, 27% test) vs raw ransomware binaries (91% train, 82% test).
    - A14: Complete source bifurcation: 100% of goodware from Software Informer, 100% of ransomware from malware repos.
- Why: Paper verification before citing numbers or building models (T-P0-05).
- Verification: `python scripts/verify_audit.py` runs with exit code 0 and verifies all items.
- Plan impact: T-P0-05 marked DONE. Phase 0 is now 100% complete!
- Follow-ups: Proceed to Phase 1 (T-P1-01 baseline reproduction & leak-free protocol).

---

## C-003 | 2026-10-14 | T-P0-06
- Contributor (human): Kishan (dkkishangowda@gmail.com)
- Agent / IDE: Antigravity
- What changed:
  - Implemented `src/data/load_mlran.py` with `load_feature_names`, `load_mlran_dataset` (returning `MLRanDataset`), and `get_chronological_val_split`.
  - Added unit test suite `tests/test_load_mlran.py` verifying shapes (3,905 train, 975 test, 483 binary features), exact paper class counts (train: 2040/1865, test: 510/465, 65 families, 5 types), feature renaming, and chronological validation split properties.
- Why: Standardized data loader and leak-free split foundation (T-P0-06).
- Verification: `pytest tests/test_load_mlran.py` passed (4/4 tests passed in 3.01s; 5/5 overall passed).
- Plan impact: T-P0-06 marked DONE.
- Follow-ups: T-P0-05 (paper audit verification against data).

---

## C-002 | 2026-10-14 | T-P0-01, T-P0-02, T-P0-03, T-P0-04
- Contributor (human): Kishan (dkkishangowda@gmail.com)
- Agent / IDE: Antigravity
- What changed:
  - Initialized git repo, verified and pinned exact versions in `requirements.txt` (torch excluded).
  - Passed initial smoke test with pytest.
  - Inspected upstream RanSMAP repo: confirmed CC BY-ND 4.0 licence, 1,970 executions across 6 ransomware and 6 benign families, ~32 GB size, documented structure in D-002.
  - Checked upstream MLRan repo: confirmed full 6.4M feature dataset is not public yet, documented in D-003.
  - Vendored MLRan 483-feature RFE subset and metadata in `data/raw/mlran/` and recorded SHA256 hashes in `data/README.md`.
- Why: Environment setup and data access (Phase 0).
- Verification: pytest passed, SHA256 hashes verified, RanSMAP API inspect confirmed.
- Plan impact: T-P0-01..T-P0-04 marked DONE.
- Follow-ups: Proceed to T-P0-06 (MLRan loader) and T-P0-05 (paper audit).

---

## C-001 | 2026-10-13 | scaffold
- Contributor (human): Member 1 (project lead) — replace with real name
- Agent / IDE: Claude (chat) generated this scaffold
- What changed: created `AGENTS.md`, IDE rule files, `memory/` brain (plan, limitations map, paper audit, patch queue, ledgers, prompt library), repo skeleton.
- Why: shared memory for multi-person, multi-agent work (Cursor + Antigravity).
- Verification: files present; MLRan repo layout and released-data facts checked by cloning upstream (RanSMAP clone failed → T-P0-02).
- Plan impact: initial plan created (phases 0–10).
- Follow-ups: fill `07_CONTRIBUTIONS.md` with team names, run T-P0-01.
