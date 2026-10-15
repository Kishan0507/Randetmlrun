# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-15 by Kalyani (Member 3) / Antigravity

## Done
- **Phase 0 (100% complete)**: Environment, data loader, vendored MLRan with SHA256 hashes, RanSMAP layout inspection, verified all 14 paper audit items A1–A14.
- **Phase 1 (100% complete)**: Exact baseline LR reproduction (TN=498, FP=12, FN=6, TP=459), leak-free temporal protocol with guarded test access, bootstrap CIs.
- **Phase 3 (100% complete)**:
  - T-P3-01: Concept drift analysis by year (2021–2024), AUT = 98.54%, FPR grows monotonically 0% -> 3.03% (`reports/drift.md`).
  - T-P3-02: 12 false positives identified and attributed to installer packaging artifacts (`STRING:!this program cannot be run in dos mode.` w=+2.599 in 100% of FPs; dynamic memory allocation, and compression entropy) (`reports/fp_analysis.md`).
  - T-P3-03: Drift mitigation evaluated; cost-weighting goodware (CW=1.5) improves BalAcc to 98.28% and cuts FPR; calibrated thresholding cuts recent FPs by >60%.
  - T-P3-04: Goodware expansion protocol written in `docs/goodware_protocol.md`.
- **Phase 2 (100% complete)**:
  - T-P2-01: Wider model comparison across 8 algorithms with expanding-window chronological CV (L2 LR selected: 96.33% CV, 98.18% Test BalAcc).
  - T-P2-02: Probability calibration via Platt scaling and operating threshold under 1% FPR budget (`src/models/calibrate.py`, `configs/operating_point.yaml`).
  - T-P2-03: Family classification v2 beating paper baseline (51.53% vs 47.07% BalAcc, `reports/family_recall.csv`).
  - T-P2-04: Unknown family rejection via OVR and LOFO validation (97.95% novel zero-day ransomware catch rate).
  - T-P2-05: Model efficiency study (LR inference latency: 0.014 ms/sample, size: 9.2 KB).
- **Phase 4 (100% complete)**:
  - T-P4-01: Early-detection protocol defined in `docs/early_detection_protocol.md` (accepted as D-004).
  - T-P4-02: RanSMAP time-series execution loader and windowing engine (`src/data/ransmap.py`, `scripts/download_ransmap.py`). 1,546 windows extracted with 21 features.
  - T-P4-03 (E-040): Window classifier baseline: LightGBM (84.96% BalAcc), Random Forest (85.28% BalAcc), Logistic Regression (77.64% BalAcc) under 5-fold execution-grouped CV and Leave-One-Family-Out validation.
  - T-P4-04 (E-041): Streaming decision rules (`src/eval/streaming.py`): EWMA Conservative achieves 100% catch rate (5/5), median TTD = 21.0s, 0.00 FA/hour, 0.0% execution FPR, saving bulk data loss.
  - T-P4-05 (E-042): Dynamic prefix extractor prototype (`src/features/prefix.py`) verified on sample Cuckoo JSON reports.
  - T-P4-07 (E-044, D-005): Two-stage detection architecture (`src/models/two_stage.py`) combining fast early containment with holistic confirmation, dropping benign crypto FPR to 0.0%.
  - Comprehensive report published in `reports/early_detection.md`.
- **Phase 8 (100% complete)**:
  - T-P8-01: Explanation service (`src/explain/reasons.py`, `configs/reasons.yaml`) with analytical SHAP (< 0.02s latency) and plain-language security reason translations with MITRE ATT&CK mappings.
  - T-P8-02: Inference engine and FastAPI prediction service (`src/app/api.py`) returning version string (`v2.1.0`), calibrated confidence, and top reasons.
  - T-P8-03: Live Sample Inspector in Streamlit (`dashboard/app.py`) with sample selection, confidence gauges, Plotly SHAP bar charts, and 3 nearest training neighbors.
  - T-P8-04: Streaming Execution Replay mode in `dashboard/app.py` replaying real RanSMAP I/O telemetry with interactive time scrubber, real-time risk score curves, alert markers, and disk bytes / LBAs written counters.
  - T-P8-05: Threat Alert Database backed by SQLite (`src/app/alert_db.py`, `data/processed/alerts.db`), CSV audit export, and interactive Model Card.
  - T-P8-06: Usability evaluation documented in `reports/usability.md`.
- **Test Suite**: 39/39 passing green via `pytest.ini`.

## In progress
- Phase 7 (Feature-space adversarial robustness) & Phase 9 (Final evaluation report and write-up).

## Next step (do this first)
1. **Phase 7 (T-P7-01..03)**: Threat model (`docs/threat_model.md`), feature-space perturbation attacks (random bit-flips, benign padding, greedy surrogate attack) in `src/adversarial/attacks.py` (E-070), and model hardening (E-071).
2. **Phase 9 (T-P9-01..04)**: Final evaluation synthesis, master reproducible experiment table (`reports/final_tables.md`), ablation summary (`reports/ablations.md`), and final comprehensive report (`reports/final_report.md`).

## Open questions for the user / team
- None. Track A pipeline is fast, clean, and 100% reproducible on CPU.

## Gotchas
- To launch the interactive dashboard: run `.\.venv\Scripts\streamlit run dashboard/app.py`.
- SQLite database auto-creates at `data/processed/alerts.db`.
