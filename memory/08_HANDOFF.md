# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-15 by Kalyani (Member 3) / Antigravity

## Done
- **Phase 0 (100% complete)**: Environment, data loader, vendored MLRan with SHA256 hashes, RanSMAP layout inspection, verified all 14 paper audit items A1–A14.
- **Phase 1 (100% complete)**: Exact baseline LR reproduction (TN=498, FP=12, FN=6, TP=459), leak-free temporal protocol with guarded test access, bootstrap CIs.
- **Phase 2 (100% complete)**: Wider model comparison across 8 algorithms with expanding-window chronological CV (L2 LR selected: 96.33% CV, 98.18% Test BalAcc). Platt scaling calibration (ECE 0.0142). Family classification v2 (51.53% BalAcc). Zero-day LOFO catch rate (97.95%). Efficiency study (LR: 0.014 ms, 9.2 KB).
- **Phase 3 (100% complete)**: Concept drift (AUT = 98.54%), 12 FP root-cause attribution, drift mitigation (CW=1.5 → 98.28% BalAcc), goodware expansion protocol.
- **Phase 4 (100% complete)**: RanSMAP windowing (1,546 windows, 21 features), window classifiers (RF BalAcc 85.28%), streaming EWMA (100% catch, 0.00 FA/hr, 21s TTD), prefix prototype, two-stage architecture (D-005: 18s TTD, 0% AESCrypt FPR).
- **Phase 7 (100% complete)**: Threat model (D-006), 4 adversarial attacks benchmarked (E-070), adversarial training hardening (E-071: +42.4% defense gain), execution failure analysis.
- **Phase 8 (100% complete)**: SHAP explanation service (<0.02s), FastAPI inference engine (v2.1.0), 4-tab Streamlit dashboard (Live Inspector, Execution Replay, Alert DB, Model Card), usability evaluation.
- **Phase 9 (100% complete)**: Master experiment tables (`reports/final_tables.md`), ablation study (`reports/ablations.md`), limitations & threats to validity (`reports/limitations.md`), final comprehensive report (`reports/final_report.md`).
- **Test Suite**: 45/45 passing green via `pytest`.

## In progress
- Nothing. All Track A phases are complete.

## Next step (do this first)
- **Project is feature-complete for Track A.** Only Phase 10 backlog items remain (optional extras):
  1. T-P10-01: Ensemble stacking (LR + LightGBM + streaming) for drift robustness.
  2. T-P10-02: Active-learning loop (dashboard analyst feedback → retrain).
  3. T-P10-03: Entropy/honeyfile features as extra window signals.
  4. T-P10-04: Ransom-note/extension-change detector features.
  5. T-P10-05: ONNX export for edge deployment.
  6. T-P10-06: `MLRan-ext` dataset contribution (Track B).
  7. T-P10-07: Cross-dataset generalisation study.

## Open questions for the user / team
- None. Track A pipeline is 100% complete, fast, clean, and reproducible on CPU.

## Gotchas
- To launch the interactive dashboard: run `.\.venv\Scripts\streamlit run dashboard/app.py`.
- SQLite database auto-creates at `data/processed/alerts.db`.
- Full report: `reports/final_report.md`. All experiment IDs trace to `memory/09_EXPERIMENT_LOG.md`.
