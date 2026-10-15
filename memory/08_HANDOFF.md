# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-15 by Kalyani (Member 3) / Antigravity

## Done
- **Phase 0 (100% complete)**: Environment, data loader, vendored MLRan with SHA256 hashes, RanSMAP layout inspection, verified all 14 paper audit items A1–A14.
- **Phase 1 (100% complete)**: Exact baseline LR reproduction (TN=498, FP=12, FN=6, TP=459), leak-free temporal protocol with guarded test access, bootstrap CIs. T-P1-04 acknowledged as BLOCKED (unreleased 24k intermediate MI features).
- **Phase 2 (100% complete)**: Wider model comparison across 8 algorithms with expanding-window chronological CV (L2 LR selected: 96.33% CV, 98.18% Test BalAcc). Platt scaling calibration (ECE 0.0142). Family classification v2 (51.53% BalAcc). Zero-day LOFO catch rate (97.95%). Efficiency study (LR: 0.014 ms, 9.2 KB).
- **Phase 3 (100% complete)**: Concept drift (AUT = 98.54%), 12 FP root-cause attribution, drift mitigation (CW=1.5 → 98.28% BalAcc), goodware expansion protocol. T-P3-05 remains DROPPED (Track B sandbox execution prohibited in-repo per AGENTS.md §4).
- **Phase 4 (100% complete)**: RanSMAP windowing (1,546 windows, 21 features), window classifiers (RF BalAcc 85.28%), streaming EWMA (100% catch, 0.00 FA/hr, 21s TTD), prefix prototype on 20 sample reports, two-stage architecture (D-005: 18s TTD, 0% AESCrypt FPR). T-P4-06 remains DROPPED (Track B scale reports unreleased upstream).
- **Phase 5 (Track A 100% complete — unblocked per P-001 / D-010)**:
  - T-P5-01: API sequence representation: n-grams (n=2,3), TF-IDF, category transitions, inter-call delay statistics, and fast sub-millisecond loop detection (`src/features/sequence.py`).
  - T-P5-02: Ransomware attack lifecycle pattern matching (Find -> Open -> Write -> Delete/Rename), file ops rates, and extension change indicators (`src/features/sequence.py`, `tests/test_sequence.py`).
  - T-P5-04 (E-051): Sequential trajectory modeling on RanSMAP native time series (`src/features/sequential_ransmap.py`, `scripts/run_sequence_experiments.py`); achieves +6.31% BalAcc on LR (83.96%) and +2.62% BalAcc on LightGBM (87.58%) with recall jumping to 77.90% (+6.74%).
  - T-P5-03: Marked DROPPED with reason (PyTorch excluded per D-009 CPU-only constraint; unreleased full raw data; successfully replaced by T-P5-04 on RanSMAP).
- **Phase 6 (Track A 100% complete — unblocked per P-001 / D-010)**:
  - T-P6-01: Flow-level network behavioral design specification (`docs/network_features.md`) covering 12 metrics (DNS query counts, distinct hosts/ports, TLS ratio, burst rate, failed connection ratio, domain entropy, DGA detection) and explaining why the paper dropped the network group (closed testbed network isolation).
  - T-P6-02: Flow-level network extractor (`src/features/network.py`) with unit tests (`tests/test_network.py`) verified across all 20 real downloaded Cuckoo JSON reports.
  - T-P6-03: Marked DROPPED with reason (full 4,880 network PCAPs unreleased upstream; prototype evaluated in `docs/network_features.md`).
- **Phase 7 (100% complete)**: Threat model (D-006), 4 adversarial attacks benchmarked (E-070), adversarial training hardening (E-071: +42.4% defense gain), execution failure analysis. Track B tasks (T-P7-B1..B3) retain DROPPED status (prohibited in-repo).
- **Phase 8 (100% complete)**: SHAP explanation service (<0.02s), FastAPI inference engine (v2.1.0), 4-tab Streamlit dashboard (Live Inspector, Execution Replay, Alert DB, Model Card), usability evaluation.
- **Phase 9 (100% complete)**: Master experiment tables (`reports/final_tables.md`), ablation study (`reports/ablations.md`), limitations & threats to validity (`reports/limitations.md`), final comprehensive report (`reports/final_report.md`).
- **Test Suite**: **57/57 passing green** via `pytest` (up from 45/45).

## In progress
- Nothing. All feasible Track A tasks across all phases (including previously dropped Phase 5 & 6 tasks) are now 100% complete and tested.

## Next step (do this first)
- **Project is feature-complete for all Track A tasks across Phases 0–9.** Only Phase 10 backlog items remain (optional extras):
  1. T-P10-01: Ensemble stacking (LR + LightGBM + streaming) for drift robustness.
  2. T-P10-02: Active-learning loop (dashboard analyst feedback → retrain).
  3. T-P10-03: Entropy/honeyfile features as extra window signals.
  4. T-P10-04: Ransom-note/extension-change detector features.
  5. T-P10-05: ONNX export for edge deployment.
  6. T-P10-06: `MLRan-ext` dataset contribution (Track B).
  7. T-P10-07: Cross-dataset generalisation study.

## Open questions for the user / team
- None. All tasks have clear, documented statuses and verified tests.

## Gotchas
- To run the new sequence experiment: `.\.venv\Scripts\python.exe scripts/run_sequence_experiments.py`.
- To launch the interactive dashboard: `.\.venv\Scripts\streamlit run dashboard/app.py`.
- Full test suite: `.\.venv\Scripts\python.exe -m pytest -v`.
