# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-14 by Kishan / Antigravity

## Done
- T-P0-01..06: Full Phase 0 complete (environment, data loader, vendored MLRan with SHA256 hashes, RanSMAP layout inspection, and verification of paper audit items A1–A14).
- T-P1-01..05: Full Phase 1 complete (exact baseline LR reproduction TN=498, FP=12, FN=6, TP=459, leak-free temporal protocol with guarded test access, bootstrap CIs).
- T-P3-01..04: Full Phase 3 complete:
  - T-P3-01: Concept drift analysis by year (2021–2024), AUT = 98.54%, FPR grows monotonically 0% -> 3.03% (`reports/drift.md`).
  - T-P3-02: 12 false positives identified and attributed to installer packaging artifacts (`STRING:!this program cannot be run in dos mode.` w=+2.599 in 100% of FPs; dynamic memory allocation, and compression entropy) (`reports/fp_analysis.md`).
  - T-P3-03: Drift mitigation evaluated; cost-weighting goodware (CW=1.5) improves BalAcc to 98.28% and cuts FPR; calibrated thresholding cuts recent FPs by >60%.
  - T-P3-04: Goodware expansion protocol written in `docs/goodware_protocol.md`.

## In progress
- Phase 2: Better models and family classification (T-P2-01, T-P2-02, T-P2-03, T-P2-04, T-P2-05).

## Next step (do this first)
1. T-P2-01: Wider model comparison on same features (LR L1/L2, Linear SVM, RF, Extra Trees, LightGBM, XGBoost) with chronological expanding-window CV.
2. T-P2-02: Probability calibration and operating point selection under FPR budget (FPR <= 1%).
3. T-P2-03: Family classification v2 (hierarchical / class-weighted, beating paper's 47.07% balanced accuracy).

## Open questions for the user / team
- None. Track A only, CPU-only workflow progressing rapidly.

## Gotchas
- The 12 baseline false positives in the test set occur primarily in 2023–2024 because 81% of test goodware is from 2023–2024.
- `STRING:!this program cannot be run in dos mode.` is the #1 cause of false alarms on modern installers; dropping it or weighting goodware heavily mitigates this.
