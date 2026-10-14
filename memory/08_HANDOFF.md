# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-14 by Kishan / Antigravity

## Done
- T-P0-01..06: Full Phase 0 complete (environment, data loader, vendored MLRan with SHA256 hashes, RanSMAP layout inspection, and verification of paper audit items A1–A14).
- T-P1-01: Baseline Logistic Regression reproduced exactly (TN=498, FP=12, FN=6, TP=459, Balanced Accuracy 98.18%, Accuracy 98.15%).
- T-P1-02: Multi-model baseline reproduction (DT, RF, Extra Trees, LightGBM) with 95% bootstrap CIs.
- T-P1-03: Leak-free temporal evaluation protocol (`src/eval/protocol.py`) with guarded test access and expanding-window CV.
- T-P1-05: Comprehensive evaluation metrics module (`src/eval/metrics.py`) with bootstrap CIs.
- Experiments E-001, E-002, E-003 logged in `memory/09_EXPERIMENT_LOG.md` and detailed report in `reports/baseline_repro.md`. Phase 1 complete!

## In progress
- Phase 3: Drift by year and false positive analysis (T-P3-01, T-P3-02, T-P3-03).

## Next step (do this first)
1. T-P3-01: Compute performance and AUT (area under time) per year for baseline LR & LightGBM; plot/tabulate FPR/FNR by first-submission year.
2. T-P3-02: Error analysis of the 12 false positives (which features fire via SHAP/coefficients, which goodware apps, common causes).
3. T-P3-03: Drift mitigation experiments (sliding window, recency weighting, cost-sensitive loss, recalibration).

## Open questions for the user / team
- None. Track A only, CPU-only workflow progressing rapidly.

## Gotchas
- The 12 baseline false positives in the test set occur primarily in 2023–2024 because 81% of test goodware is from 2023–2024.
- Single Decision Trees degrade severely over chronological shifts (-6.4% on validation slice), while Extra Trees and LR remain robust.
