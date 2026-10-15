# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-15 by Karthikey / Antigravity

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
  - Test suite verified: 17/17 tests passing via `pytest.ini`.
- **Phase 4 (In Progress)**:
  - T-P4-01: Early-detection protocol defined in `docs/early_detection_protocol.md` (accepted as D-004).

## In progress
- Phase 4: Early detection on RanSMAP (T-P4-02 onwards).

## Next step (do this first)
1. T-P4-02: Load RanSMAP executions as windowed time series (`src/data/ransmap.py`, tests).
2. T-P4-03: Window classifier baseline (LR/LightGBM on window statistics).
3. T-P4-04: Streaming decision rules (EWMA, k-of-n) and time-to-detection (TTD) curves.

## Open questions for the user / team
- None. Track A only, CPU-only workflow progressing rapidly.

## Gotchas
- RanSMAP upstream is 32 GB; we selectively download representative executions (Conti, LockBit, WannaCry + AESCrypt, Firefox, Office) to keep local storage lightweight.
- `pytest.ini` now automatically routes imports to root, ensuring clean test discovery.
