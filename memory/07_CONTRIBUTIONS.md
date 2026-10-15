# 07 — Contributions ledger (acknowledgement)

Every contribution — code, data, analysis, writing, review, ideas, testing — is recorded here with the person's name. Append only. The final report's acknowledgement section is generated from this file.

## Team roster (fill at kickoff)
| Member | Email / handle | Main IDE | Focus area | Joined |
|---|---|---|---|---|
| Kishan (project lead) | dkkishangowda@gmail.com | Antigravity / Cursor | All | 2026-10-13 |
| Member 2 (Karthikey) | | Antigravity | Environment, Phase 2, Early detection | 2026-10-14 |
| Kalyani (Member 3) | Member 3 | Antigravity | Phase 4 Early Detection, Two-stage architecture | 2026-10-15 |
| Member 4 | | | | |

## Ledger (newest at the bottom)
| Date | Member | Agent/IDE | Task / Patch IDs | Contribution (one line) | Files / links |
|---|---|---|---|---|---|
| 2026-10-13 | Kishan | Claude chat | scaffold | Project idea, limitations analysis, scaffold request | memory/* |
| 2026-10-14 | Kishan | Antigravity | T-P0-01..04 | Env setup, pinned reqs, git init, MLRan vendoring + hashes, RanSMAP layout inspection | memory/*, requirements.txt, data/* |
| 2026-10-14 | Kishan | Antigravity | T-P0-06 | Data loader `src/data/load_mlran.py`, metadata joining, chronological split, tests | `src/data/load_mlran.py`, `tests/test_load_mlran.py` |
| 2026-10-14 | Kishan | Antigravity | T-P0-05 | Automated audit script `scripts/verify_audit.py`, confirmed all 14 paper audit items A1-A14 | `scripts/verify_audit.py`, `memory/03_PAPER_AUDIT.md` |
| 2026-10-14 | Kishan | Antigravity | T-P1-01..05 | Exact baseline reproduction (LR 498/12/6/459), full metrics with bootstrap CIs, leak-free protocol | `src/eval/*`, `tests/test_*`, `reports/baseline_repro.md` |
| 2026-10-14 | Kishan | Antigravity | T-P3-01..04 | Drift analysis (AUT=98.54%), 12 FP root-cause attribution, drift mitigation experiments, goodware expansion protocol | `scripts/drift_and_fp_analysis.py`, `reports/drift.md`, `reports/fp_analysis.md`, `docs/goodware_protocol.md` |
| 2026-10-15 | Karthikey / Kishan | Antigravity | T-P2-01..05, T-P4-01 | Phase 2 multi-model benchmark, calibration under FPR budget, family v2, pytest configuration & test verification | `src/models/*`, `tests/test_*`, `reports/model_comparison.md`, `configs/*`, `pytest.ini` |
| 2026-10-15 | Kalyani | Antigravity | T-P4-02..05, T-P4-07 | Phase 4 early detection on RanSMAP: window loader, window classifiers (E-040), streaming rules & TTD evaluation (E-041), prefix truncation prototype (E-042), two-stage detector & ablation (E-044, D-005) | `src/data/ransmap.py`, `src/models/window_classifier.py`, `src/eval/streaming.py`, `src/features/prefix.py`, `src/models/two_stage.py`, `reports/early_detection.md`, `tests/test_*.py` |
| 2026-10-15 | Kalyani | Antigravity | T-P8-01..06 | Phase 8 explainability & dashboard: SHAP reason translation service, FastAPI inference engine, 4-tab Streamlit app with RanSMAP execution replay & SQLite threat history, usability audit | `src/explain/reasons.py`, `configs/reasons.yaml`, `src/app/api.py`, `src/app/alert_db.py`, `dashboard/app.py`, `reports/usability.md`, `tests/test_*.py` |

## Summary counts (update at milestones)
| Member | Tasks done | Patches requested | Patches implemented | Reviews | Notes |
|---|---|---|---|---|---|
| | | | | | |

## Credit rules
1. A contribution is credited to the **human** who directed or wrote it; the AI agent/IDE is noted but is not a substitute for the name.
2. Ideas count: a good idea or bug report gets a line even if someone else typed the code.
3. Reviews count: a person who reviews and catches an error gets a line.
4. Commit trailer `Contributed-by: <Name>` must match the ledger name.
5. Upstream credit: MLRan (Onwuegbuche et al.), RanSMAP (Hirano & Kobayashi) are cited in the report and README.
