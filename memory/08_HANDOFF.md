# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-15 by Kalyani (Member 3) / Antigravity

## Done
- **Phase 0 (100% complete)**: Environment, data loader, vendored MLRan with SHA256 hashes, RanSMAP layout inspection, verified all 14 paper audit items A1–A14.
- **Phase 1 (100% complete)**: Exact baseline LR reproduction (TN=498, FP=12, FN=6, TP=459), leak-free temporal protocol with guarded test access, bootstrap CIs. T-P1-04 acknowledged as BLOCKED (unreleased 24k intermediate MI features).
- **Phase 2 (100% complete)**: Wider model comparison across 8 algorithms with expanding-window chronological CV (L2 LR selected: 96.33% CV, 98.18% Test BalAcc). Platt scaling calibration (ECE 0.0142). Family classification v2 (51.53% BalAcc). Zero-day LOFO catch rate (97.95%). Efficiency study (LR: 0.014 ms, 9.2 KB).
- **Phase 3 (100% complete)**: Concept drift (AUT = 98.54%), 12 FP root-cause attribution, drift mitigation (CW=1.5 → 98.28% BalAcc), goodware expansion protocol. T-P3-05 remains DROPPED (Track B sandbox execution prohibited in-repo per AGENTS.md §4).
- **Phase 4 (100% complete)**: RanSMAP windowing (1,546 windows, 21 features), window classifiers (RF BalAcc 85.28%), streaming EWMA (100% catch, 0.00 FA/hr, 21s TTD), prefix prototype on 20 sample reports, two-stage architecture (D-005: 18s TTD, 0% AESCrypt FPR). T-P4-06 remains DROPPED (Track B scale reports unreleased upstream).
- **Phase 5 (Track A 100% complete)**: API sequence n-grams ($n=2,3$), transition matrix, time-delay statistics, ransomware lifecycle pattern extractor (`src/features/sequence.py`), RanSMAP sequential trajectory augmentation (`src/features/sequential_ransmap.py`, E-051: +6.31% BalAcc on LR, +2.62% on LightGBM). T-P5-03 remains DROPPED (PyTorch excluded per D-009 CPU-only constraint; scale raw data unreleased).
- **Phase 6 (Track A 100% complete)**: Flow-level network behavioral specification (`docs/network_features.md`) covering 12 metrics (DNS, distinct hosts/ports, TLS ratio, burst rate, failed connection ratio, domain entropy, DGA detection) and network extractor (`src/features/network.py`) verified across all 20 Cuckoo reports. T-P6-03 remains DROPPED (unreleased full network PCAPs).
- **Phase 7 (100% complete)**: Threat model (D-006), 4 adversarial attacks benchmarked (E-070), adversarial training hardening (E-071: +42.4% defense gain), execution failure analysis. Track B tasks (T-P7-B1..B3) retain DROPPED status (prohibited in-repo).
- **Phase 8 (100% complete)**: SHAP explanation service (<0.02s), FastAPI inference engine (v2.1.0), 4-tab Streamlit dashboard (Live Inspector, Execution Replay, Alert DB, Model Card), usability evaluation.
- **Phase 9 (100% complete)**: Master experiment tables (`reports/final_tables.md`), ablation study (`reports/ablations.md`), limitations & threats to validity (`reports/limitations.md`), final comprehensive report (`reports/final_report.md`).
- **Phase 10 (100% complete — Advanced Extensions & Production Readiness)**:
  - T-P10-01: Stacking ensemble classifier (`src/models/ensemble.py`) combining LR, LightGBM, and Random Forest via out-of-fold meta-learner to maximize drift robustness.
  - T-P10-02: Human-in-the-loop active learning loop (`src/models/active_learning.py`) with uncertainty sampling and validation-gated candidate retraining.
  - T-P10-03: Entropy and canary tripwire feature extraction (`src/features/honeyfile.py`) detecting sub-second decoy touches and write entropy.
  - T-P10-04: Explicit ransom note and extension change detector (`src/features/ransom_note.py`) matching note filenames, extortion keywords, and double extensions.
  - T-P10-05: ONNX runtime export & benchmarking engine (`src/models/onnx_export.py`); verified sub-millisecond single-sample CPU latency, low memory footprint, and numerical parity (<1e-3).
  - T-P10-06: Modern dataset extension specification (`docs/mlran_ext_dataset_spec.md`) and metadata manifest schema (`data/processed/mlran_ext_metadata_schema.json`) for community release.
  - T-P10-07: Cross-dataset generalisation study (`src/eval/cross_dataset.py`, `reports/cross_dataset.md`) validating 100% conceptual alignment on major ransomware families and confirming Two-Stage architecture as the universal cross-dataset bridge.
- **Test Suite**: **69/69 passing green** via `pytest`.

## In progress
- Nothing. Entire master plan across Phases 0 through 10 is 100% complete and fully verified.

## Next step (do this first)
- Repository is completely finished, documented, benchmarked, and ready for review/demonstration!
- To launch the interactive dashboard: run `.\.venv\Scripts\streamlit run dashboard/app.py`.
- To run full test suite: `.\.venv\Scripts\python.exe -m pytest -v`.

## Open questions for the user / team
- None.

## Gotchas
- SQLite database auto-creates at `data/processed/alerts.db`.
- All experiment IDs trace directly to `memory/09_EXPERIMENT_LOG.md`.
