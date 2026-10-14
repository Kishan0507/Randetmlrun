# 05 — Decisions (ADR style, append at the bottom)

Template:
```
## D-### | YYYY-MM-DD | <title>
- Status: PROPOSED | ACCEPTED | SUPERSEDED by D-###
- Decided by: <names>
- Context: <why a choice was needed>
- Decision: <what we chose>
- Alternatives: <what we did not choose and why>
- Consequences: <what changes in plan/code>
```

---

## D-001 | 2026-10-13 | Two data tracks (A data-only, B own sandbox)
- Status: ACCEPTED (Track B requires separate approval)
- Context: Full MLRan raw/6.4M-feature data is not public; only 483-feature CSVs, metadata (hashes) and 20 sample reports are. Early detection, sequences and network features need raw logs.
- Decision: Default to **Track A** (released MLRan files + RanSMAP time series; no malware execution). **Track B** (re-run by hash in an isolated Win10/11 sandbox) is optional and starts only after supervisor/institution approval is recorded here.
- Alternatives: Email the MLRan authors for the full data (do this in parallel — task T-P0-03); skip raw-log features entirely (loses the core contribution).
- Consequences: Phases 4–6 have Track A prototypes and Track B scale-ups; claims from Track A prototypes must say "prototype".

## D-002 | 2026-10-14 | RanSMAP structure and loading (T-P0-02)
- Status: ACCEPTED
- Decided by: Kishan (dkkishangowda@gmail.com)
- Context: Verified upstream RanSMAP repo (manabu-hirano/RanSMAP) structure, size, and layout.
- Findings:
  1. **Size:** The GitHub repo is ~32 GB (32,037,753 KB). Full git clone must NOT be run on laptop.
  2. **Licence:** Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0).
  3. **Dataset contents:** 1,970 total executions (1,440 original across Celeron/i3 hardware, 360 extra, 100 mix, 70 variants).
  4. **Classes:** 6 ransomware families (Conti, Darkside, LockBit, REvil, Ryuk, WannaCry) + 6 benign applications (AESCrypt, Firefox, Idle, Office, SDelete, Zip).
  5. **Execution layout:** Each execution folder `<app>-<timestamp>` contains 6 uncompressed CSVs: `ata_read.csv`, `ata_write.csv`, `mem_read.csv`, `mem_write.csv`, `mem_readwrite.csv`, `mem_exec.csv`.
  6. **Columns:** Timestamps (sec + ns), Block/Page addresses (LBA/GPA), size, entropy (critical for encryption detection), access type.
- Decision: Selectively download representative executions directly via GitHub raw / Kaggle into `data/raw/ransmap/` for Phase 4 early-detection experiments rather than cloning 32 GB.

## D-003 | 2026-10-14 | Full MLRan dataset release status (T-P0-03)
- Status: ACCEPTED
- Decided by: Kishan (dkkishangowda@gmail.com)
- Finding: Upstream MLRan repo (`5_mlran_dataset/README.md`, commit `ec2651f`) confirms full 6.4M-feature raw dataset is NOT public yet.
- Decision: Use the released 483-feature RFE dataset in `6_experiments/FS_MLRan_Datasets/` (vendored into `data/raw/mlran/`).
- Consequence: Acknowledge limitation in report; run leak-free protocol on 483 features; use RanSMAP for dynamic/early time-series analysis.

## D-004 | pending | Early-detection metric definitions (fill in T-P4-01)
- Status: PROPOSED

## D-005 | pending | Two-stage design (early alert + confirmation) (fill in T-P4-07)
- Status: PROPOSED

## D-006 | pending | Adversarial threat model (fill in T-P7-01)
- Status: PROPOSED

## D-007 | 2026-10-13 | Evaluation protocol
- Status: ACCEPTED
- Decision: temporal split by VirusTotal first-submission date (earliest 80% train / latest 20% test, grouped by type as in the paper's `type_train_sampleids.csv` / `type_test_sampleids.csv`). All selection on a chronological validation slice of train. Metrics: balanced accuracy primary, plus macro-F1, precision, recall, FPR, FNR, PR-AUC, bootstrap 95% CI.
- Consequences: no random k-fold results in the report (can appear as extra, labelled "optimistic").

## D-008 | 2026-10-13 | Tech stack defaults
- Status: ACCEPTED (SUPERSEDED partially by D-009)
- Decision: Python 3.11, scikit-learn, LightGBM, XGBoost, SHAP, LIME, Streamlit, SQLite, pytest, ruff. **No PyTorch** (removed by D-009, CPU-only laptop).

## D-009 | 2026-10-14 | Scope narrowing — Track A only, CPU-only, dropped tasks
- Status: ACCEPTED
- Decided by: Member 1 (dkkishu0507@gmail.com)
- Context: Time is short, CPU-only laptop, no GPU/sandbox available.
- Decision:
  1. **Track A only** — use public data (MLRan released files, RanSMAP). No running malware, no sandbox, no writing malware or evasion code. AGENTS.md §4 safety rules apply.
  2. **CPU-only** — scikit-learn, LightGBM, XGBoost only. Do NOT install torch/PyTorch.
  3. **DROPPED tasks:** all Track B (T-P3-05, T-P4-06, T-P5-03, T-P6-03, T-P7-B1, T-P7-B2, T-P7-B3), sequence neural nets (T-P5-03/04 NN parts), network features (Phase 6 entirely).
  4. **Priority order:** P0 setup/audit → P1 baseline + leak-free → P3 drift/FP → P2 family classification → P4 early detection on RanSMAP → P8 dashboard → P9 report. T-P7-01/02 (feature-space adversarial test) optional last.
- Alternatives: Keep full scope (rejected — not feasible in available time with CPU-only HW).
- Consequences: Master plan updated; requirements.txt removes torch; Phases 5, 6 dropped; Track B tasks marked DROPPED in plan.
