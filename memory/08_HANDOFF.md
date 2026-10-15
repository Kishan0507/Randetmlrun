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
- **Test Suite**: 34/34 passing green via `pytest.ini`.

## In progress
- Transitioning to next phase: Phase 8 (Explainability and Streamlit Dashboard) or Phase 7 (Feature-space adversarial robustness). Per D-009, priority is Phase 8 (Dashboard).

## Next step (do this first)
1. **T-P8-01**: Explanation service (`src/explain/reasons.py`, `configs/reasons.yaml`) using SHAP feature attributions mapped to plain-language analyst reasons.
2. **T-P8-02**: Inference API (`src/app/api.py`) exposing `predict(features) -> {verdict, confidence, reasons, model_version}`.
3. **T-P8-03 & T-P8-04**: Interactive Streamlit Dashboard (`dashboard/app.py`) with sample inspection, feature SHAP waterfall explanations, and streaming RanSMAP execution replay mode.

## Open questions for the user / team
- None. Track A pipeline is fast, clean, and 100% reproducible on CPU.

## Gotchas
- RanSMAP upstream is 32 GB; `scripts/download_ransmap.py` streams only required ATA write CSVs (under 5MB per execution) into `data/raw/ransmap/`.
- AESCrypt is benign crypto; single raw windows produce high entropy (false alarms), but EWMA smoothing and Stage 2 confirmation completely neutralize them.
