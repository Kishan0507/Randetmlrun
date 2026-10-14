# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-14 by Kishan / Antigravity

## Done
- T-P0-01: Environment verified (pip freeze, torch removed, pytest passing), requirements.txt pinned.
- T-P0-02: RanSMAP upstream layout inspected, ~32 GB size noted, structure and loader decision recorded in D-002.
- T-P0-03: MLRan upstream checked, full 6.4M dataset confirmed not public, recorded in D-003.
- T-P0-04: MLRan 483-feature RFE subset and metadata vendored to data/raw/mlran/, SHA256 hashes verified in data/README.md.
- T-P0-06: Data loader module `src/data/load_mlran.py` implemented and verified with unit tests `tests/test_load_mlran.py` (3,905 train / 975 test rows, 483 features, exact class counts matching paper).
- T-P0-05: Verified and confirmed paper audit items A1–A14 via automated script `scripts/verify_audit.py`, updated `memory/03_PAPER_AUDIT.md`. Phase 0 complete!

## In progress
- T-P1-01..05: Baseline reproduction (LR, Decision Tree, RF, Extra Trees, LightGBM) and leak-free protocol implementation.

## Next step (do this first)
1. T-P1-01: Reproduce paper baseline result (LR on released 483-feature split, target confusion matrix 498/12/6/459, bal acc 98.18%).
2. T-P1-02: Reproduce Table 6 models (DT, RF, Extra Trees, LightGBM).
3. T-P1-03: Build `src/eval/protocol.py` (chronological validation slice, guard against test snooping).
4. T-P1-05: Build `src/eval/metrics.py` (bal acc, macro-F1, precision, recall, FPR, FNR, PR-AUC, 1000 bootstrap resamples CI).

## Open questions for the user / team
- None. Track A only, CPU-only workflow.

## Gotchas
- The paper chooses RFE feature count via test-set balanced accuracy (A1 audit item); our leak-free protocol must use a chronological validation slice carved from train.
- 81% of test goodware is from 2023–2024, causing the false positive clustering observed in the paper (A12).
- Top SHAP feature `STRING:!this program cannot be run in dos mode.` reflects installer wrapper vs raw malware format (A13/A14).
