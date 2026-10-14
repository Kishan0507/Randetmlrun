# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-14 by Kishan / Antigravity

## Done
- T-P0-01: Environment verified (pip freeze, torch removed, pytest passing), requirements.txt pinned.
- T-P0-02: RanSMAP upstream layout inspected, ~32 GB size noted, structure and loader decision recorded in D-002.
- T-P0-03: MLRan upstream checked, full 6.4M dataset confirmed not public, recorded in D-003.
- T-P0-04: MLRan 483-feature RFE subset and metadata vendored to data/raw/mlran/, SHA256 hashes verified in data/README.md.
- T-P0-06: Data loader module `src/data/load_mlran.py` implemented and verified with unit tests `tests/test_load_mlran.py` (3,905 train / 975 test rows, 483 features, exact class counts matching paper).

## In progress
- T-P0-05: Verify paper audit items A1–A14 against data, record status and evidence in `memory/03_PAPER_AUDIT.md`.

## Next step (do this first)
1. T-P0-05: Run systematic verification script for paper audit items A1–A14, update `memory/03_PAPER_AUDIT.md`.
2. T-P1-01..05: Baseline reproduction (LR, Decision Tree, RF, Extra Trees, LightGBM) and leak-free protocol implementation.
3. T-P3-01..03: Drift by year and FP analysis.

## Open questions for the user / team
- None. Track A only, CPU-only workflow.

## Gotchas
- The 483 features in MLRan are all binary indicators {0, 1}.
- Feature columns are mapped via `load_feature_names()` or `load_mlran_dataset(rename_features=True)`.
- Temporal split is already encoded in the sample_id train/test split (train <= 2023-03-21, test >= 2021-10-29).
