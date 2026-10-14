# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-14 by Kishan / Antigravity

## Done
- T-P0-01: Environment verified (pip freeze, torch removed, pytest passing), requirements.txt pinned.
- T-P0-02: RanSMAP upstream layout inspected, ~32 GB size noted, structure and loader decision recorded in D-002.
- T-P0-03: MLRan upstream checked, full 6.4M dataset confirmed not public, recorded in D-003.
- T-P0-04: MLRan 483-feature RFE subset and metadata vendored to data/raw/mlran/, SHA256 hashes verified in data/README.md.
- Git repo initialized with Kishan (dkkishangowda@gmail.com) as contributor.

## In progress
- T-P0-06: MLRan data loader (`src/data/load_mlran.py`) + tests.

## Next step (do this first)
1. T-P0-06: Build `src/data/load_mlran.py` to load X_train, X_test, labels, metadata, map feature indices to names, join first_submission_date, write pytest in `tests/test_load_mlran.py`.
2. T-P0-05: Verify paper audit items A1–A14 against data, record status and evidence in `memory/03_PAPER_AUDIT.md`.
3. T-P1-01..05: Baseline reproduction and leak-free protocol.

## Open questions for the user / team
- None currently blocking. Scope narrowed to Track A only, CPU-only laptop via D-009.

## Gotchas
- The full MLRan 6.4M-feature data is not public; only the 483-feature CSVs are. Feature columns are numeric indices — map via `RFE_selected_feature_names_dic.json`.
- The paper chooses RFE feature count via test-set balanced accuracy (A1 audit item); our leak-free protocol must use a chronological validation slice carved from train.
- RanSMAP repo is 32 GB; do not full-clone, fetch needed runs on-demand via HTTP.
