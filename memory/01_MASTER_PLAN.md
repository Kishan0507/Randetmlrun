# 01 — Master plan

Status values: `TODO` · `IN_PROGRESS` · `DONE` · `BLOCKED` · `DROPPED`
Track: **A** = data-only (default). **B** = needs our own sandbox + approval (optional).
Update the Status column every session. Add new tasks at the end of a phase with the next free ID. Do not renumber.

Order of work (updated D-009): P0 → P1 → P3 → P2 → P4 → P8 → P9. T-P7-01/02 optional last. Phases 5, 6 and all Track B: DROPPED.

---
## Phase 0 — Setup, audit, data access
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P0-01 | Create repo skeleton, `requirements.txt` (pinned), `configs/default.yaml`, `Makefile`, pre-commit (ruff), CI that runs pytest | A | — | repo skeleton | `pip install -r requirements.txt && pytest` passes on a clean machine | DONE | Kishan |
| T-P0-02 | Clone/inspect RanSMAP; record file layout, label scheme, feature columns, sampling interval, licence in `05_DECISIONS.md` | A | T-P0-01 | decision D-002 | Document states: how to load one execution, what a row is, how ransomware vs goodware is labelled | DONE | Kishan |
| T-P0-03 | Re-check upstream MLRan repo: is the full 6.4M-feature dataset released now? Record result | A | — | decision D-003 | Yes/No + link/date noted; if yes, plan T-P1-01 to use full data | DONE | Kishan |
| T-P0-04 | Vendor MLRan released files into `data/raw/mlran/` (do not edit), write `data/README.md` with SHA256 of each file and source URL/commit | A | T-P0-01 | `data/raw/mlran/*` | Files present, hashes recorded, licence note (MIT, attribute authors) | DONE | Kishan |
| T-P0-05 | Verify the audit items in `03_PAPER_AUDIT.md` that can be checked from data (A1–A8) and mark each `CONFIRMED` / `NOT CONFIRMED` / `UNCLEAR` | A | T-P0-04 | updated audit file | Every checkable item has a status + evidence (code/notebook path) | TODO | |
| T-P0-06 | Data loader module `src/data/load_mlran.py`: load X/y, join metadata, map feature index → name, parse first-submission date, return train/test using the paper's sample-id files | A | T-P0-04 | module + tests | 3,905 train / 975 test rows; class counts match paper; unit tests green | DONE | Kishan |

## Phase 1 — Reproduce baseline and make evaluation leak-free
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P1-01 | Reproduce paper result: LR (liblinear, C grid), on released 483-feature split. Reproduce confusion matrix 498/12/6/459 | A | T-P0-06 | `reports/baseline_repro.md`, E-001 | balanced acc within ±0.5 pt of 98.15/98.18; if not, document why | TODO | |
| T-P1-02 | Reproduce the other models (Decision Tree, RF, Extra Trees, LightGBM) with the paper's grid (Table 9) | A | T-P1-01 | E-002 | Numbers vs Table 6 in a side-by-side table | TODO | |
| T-P1-03 | Leak-free protocol: carve a chronological **validation** slice from the last 20% of the training period; choose model/threshold/hyper-params there; test set touched once | A | T-P1-01 | `src/eval/protocol.py`, E-003 | Code path makes test-set access impossible before "final" call (assert/guard); documented in decisions | TODO | |
| T-P1-04 | Re-run RFE feature-count choice **inside training only** (the paper picks 2% using test balanced accuracy — see audit A1). Needs the 24,162 MI-filtered features; if unavailable, document and mark limitation | A | T-P0-03 | E-004 | If data unavailable: marked `BLOCKED` with reason; else honest number reported | TODO | |
| T-P1-05 | Add full metric suite: bal. acc, macro-F1, precision, recall, FPR, FNR, PR-AUC, confusion matrix, 95% bootstrap CI | A | T-P1-03 | `src/eval/metrics.py` | Unit tests on toy data; CI via 1,000 bootstrap resamples | TODO | |

## Phase 2 — Better models (binary, type, family)
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P2-01 | Wider model comparison on same features: LR (L1/L2/elastic), linear SVM, RF, ExtraTrees, LightGBM, XGBoost, CatBoost (optional), small MLP. Wider tuning grid, chronological CV (expanding window) | A | T-P1-03 | E-010.. | Table with metrics + train/predict time; best model chosen by validation, not test | TODO | |
| T-P2-02 | Probability calibration (Platt/isotonic) and operating-point selection under an FPR budget (e.g. FPR ≤ 1%) | A | T-P2-01 | `src/models/calibrate.py` | Reliability curve; chosen threshold stored in config | TODO | |
| T-P2-03 | Family classification v2: class-weighting, hierarchical (binary → type → family), macro-F1 objective, merge/ignore families with < N samples (documented), report per-family recall | A | T-P2-01 | E-020.. | Balanced acc and macro-F1 beat paper's 47.07% bal. acc.; per-family table | TODO | |
| T-P2-04 | "Unknown family" rejection: confidence threshold / one-vs-rest so unseen families are flagged instead of mislabelled | A | T-P2-03 | E-025 | Leave-one-family-out test: report how often an unseen family is still caught as ransomware | TODO | |
| T-P2-05 | Efficiency study: inference latency and model size per model (the paper only reports training time) | A | T-P2-01 | table | ms/sample and MB for each model | TODO | |

## Phase 3 — Concept drift and false positives
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P3-01 | Per-year performance and **AUT** (area under time) for the baseline; plot FPR/FNR by first-submission year | A | T-P1-05 | `reports/drift.md` | Plot + table; confirms/denies that 2023–24 goodware drives FPs (11 of 12 in paper) | TODO | |
| T-P3-02 | Error analysis of the 12 baseline false positives: which features fire (SHAP/LIME), which goodware (names in metadata), common cause (e.g. packer entropy, DOS-stub string, registry reads) | A | T-P1-01 | `reports/fp_analysis.md` | Each FP has top-5 features + hypothesis | TODO | |
| T-P3-03 | Drift mitigation experiments: (a) sliding-window retraining, (b) recency sample weights, (c) cost-sensitive loss on goodware, (d) periodic recalibration, (e) drift detector (e.g. ADWIN/PSI on feature distribution) | A | T-P3-01 | E-030.. | Table: FPR on 2023–24 goodware and overall bal. acc. for each strategy | TODO | |
| T-P3-04 | Write **goodware expansion protocol** `docs/goodware_protocol.md`: sources (Microsoft Store/winget, Chocolatey, enterprise/office tools, installers of 2023–25, portable apps), VirusTotal 0-detection rule, category quotas, dedupe, metadata schema | A | — | doc | Doc reviewed by team; ready for Track B execution | TODO | |
| T-P3-05 | **(Track B)** Collect and run new goodware in the sandbox; add as `MLRan-ext` with the same feature extractor | B | T-P3-04, T-P7-B1 | new feature rows | ≥ 500 new goodware, ≥ 5 sources, all VT-clean; FPR re-measured | DROPPED (D-009) | |

## Phase 4 — Early detection (core contribution)
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P4-01 | Define early-detection protocol in `docs/early_detection_protocol.md`: time-to-detection (TTD), detection rate @ t seconds (t = 2,5,10,20,30,60,120), files/bytes affected before alert, false alarms per hour of goodware | A | — | doc + decision D-004 | Metrics defined with formulas and edge cases (never detected = censored at max time) | TODO | |
| T-P4-02 | Load RanSMAP executions as windowed time series (fixed window, stride); label windows pre-encryption / encryption / benign | A | T-P0-02 | `src/data/ransmap.py`, tests | One execution → list of windows; labelling rule documented; no leakage across executions in train/test (group split by execution and by family) | TODO | |
| T-P4-03 | Window classifier baseline (LightGBM/LR on window statistics) → per-window ransomware probability | A | T-P4-02 | E-040 | Window-level metrics; family-held-out split reported | TODO | |
| T-P4-04 | Streaming decision rule: smoothing (EWMA / k-of-n windows) + threshold → alert time; compare rules | A | T-P4-03, T-P2-02 | E-041 | TTD distribution, detection@t, false alarms per hour | TODO | |
| T-P4-05 | Prefix evaluation on MLRan: using the 20 sample Cuckoo JSONs, truncate API/call logs at t seconds and re-extract the 9 feature groups; prototype only (too few for conclusions) | A | T-P0-04 | `src/features/prefix.py`, E-042 | Works end-to-end on 20 reports; documents what needs Track B for scale | TODO | |
| T-P4-06 | **(Track B)** Prefix evaluation at scale: truncate full Cuckoo reports at t seconds for all runs; train on prefixes; detection rate vs t curve | B | T-P7-B2 | E-043 | Curve for t ∈ {2,5,10,20,30,60,120}s; claim "detects X% within N s" | DROPPED (D-009) | |
| T-P4-07 | Combine: early-warning score from windows (RanSMAP-style) + full-report classifier (MLRan-style) as a two-stage system (fast early alert, slower confirmation) | A | T-P4-04 | design note D-005 + E-044 | Ablation: early only vs confirm only vs both | TODO | |

## Phase 5 — Order and timing (sequence models) — DROPPED (D-009)
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P5-01 | API sequence representation: n-grams (n=2,3), TF-IDF, ordered-transition counts, time-gap features (inter-call delay) from Cuckoo `behavior.processes[].calls[]` | A (20 reports) / B (scale) | T-P4-05 | `src/features/sequence.py` | Unit test on a sample report; feature spec in docs | DROPPED (D-009) | |
| T-P5-02 | Pattern features for "find files → open → read/write → rename/delete" (FindFirstFile/NtQueryDirectoryFile → NtCreateFile → NtWriteFile → MoveFile/DeleteFile), rate features (file ops per second, extension changes) | A / B | T-P5-01 | feature set | Documented, explained with examples | DROPPED (D-009) | |
| T-P5-03 | Models: n-gram + LR/LightGBM; 1D-CNN; GRU; small Transformer. Compare with presence-only baseline | B (needs scale) | T-P5-01, T-P7-B2 | E-050.. | Table; claim only if gain > bootstrap CI | DROPPED (D-009) | |
| T-P5-04 | If Track B is not approved: do the same on RanSMAP time series (order/timing there is native) | A | T-P4-03 | E-051 | Sequence model vs window-stat model on RanSMAP | DROPPED (D-009) | |

## Phase 6 — Network features (paper dropped all of them) — DROPPED (D-009)
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P6-01 | Design flow-level features from Cuckoo network section: #DNS queries, #distinct hosts, #distinct ports, bytes in/out, TLS vs plain, connection burst rate, newly-seen-domain ratio, TLD entropy, failed-connection ratio | A (design) | — | `docs/network_features.md` | Each feature defined, with extraction source field | DROPPED (D-009) | |
| T-P6-02 | Implement extractor, test on 20 sample reports | A | T-P6-01 | `src/features/network.py` | Tests pass | DROPPED (D-009) | |
| T-P6-03 | **(Track B)** Re-evaluate: add network group to the feature set, re-run feature selection, check if any group survives | B | T-P6-02, T-P7-B2 | E-060 | Report survival count vs paper's 0/483 | DROPPED (D-009) | |

## Phase 7 — Robustness (feature-space only) and modern-OS validity
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P7-01 | Threat model doc `docs/threat_model.md`: attacker capabilities (can ADD benign-looking API calls/strings/registry reads cheaply; cannot REMOVE core encryption behaviour), budgets, what is out of scope | A | — | doc + D-006 | Reviewed by team | TODO | |
| T-P7-02 | Perturbation attacks on feature vectors: (a) random bit-flips, (b) benign-feature padding (add features common in goodware), (c) remove top-k SHAP ransomware features, (d) gradient-guided greedy attack on LR / surrogate | A | T-P7-01, T-P2-01 | `src/adversarial/attacks.py`, E-070 | Evasion rate vs budget curve for each model | TODO | |
| T-P7-03 | Hardening: adversarial training, feature-group dropout, monotonic constraints (LightGBM), robust feature subset (drop features attacker can add freely) | A | T-P7-02 | E-071 | Evasion rate curve before vs after; clean-accuracy cost reported | TODO | |
| T-P7-04 | Report **execution failure / evasion rate** per source (the paper reports counts that drop out: e.g. MOTIF 443→426, MarauderMap 621→575, curated 785→777, Software Informer 2696→2550) | A | T-P0-05 | `reports/execution_failures.md` | Table of dropouts per source with fractions and discussion of sandbox evasion | TODO | |
| T-P7-B1 | **(Track B)** Build isolated Windows 10/11 sandbox (e.g. CAPEv2 or Cuckoo-based) with Defender state recorded, no real network, snapshots, human-activity simulation, 120 s timeout + longer timeout subset | B | approval (D-001) | `docs/sandbox_setup.md` | Written runbook; supervisor sign-off recorded | DROPPED (D-009) | |
| T-P7-B2 | **(Track B)** Re-run a stratified subset (by hash from metadata CSV) on Win10/11; keep raw reports locally, share only derived features | B | T-P7-B1 | `MLRan-Win10` features | ≥ 500 ransomware (≥ 20 families) + ≥ 500 goodware; failure rate logged | DROPPED (D-009) | |
| T-P7-B3 | **(Track B)** Cross-OS check: train on Win7 features, test on Win10/11 features and vice versa | B | T-P7-B2 | E-072 | Degradation table | DROPPED (D-009) | |

## Phase 8 — Explainability and dashboard
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P8-01 | Explanation service: SHAP (global + per-sample), optional LIME; map raw feature names to **plain-language reasons** via a lookup (e.g. `API:NtAllocateVirtualMemory`+`SIGNATURE:allocates_rwx` → "allocates executable memory — common in code injection") | A | T-P2-01 | `src/explain/reasons.py`, `configs/reasons.yaml` | Top-5 reasons per prediction in < 1 s | TODO | |
| T-P8-02 | Inference API (FastAPI or plain Python module): `predict(features) → {verdict, confidence, reasons, model_version}`; save/load model with metadata | A | T-P8-01, T-P2-02 | `src/app/api.py` | Unit tests; version string in every response | TODO | |
| T-P8-03 | Streamlit dashboard v1: pick a sample (test set) or upload feature CSV → verdict card, confidence gauge, top reasons bar chart, similar-sample neighbours | A | T-P8-02 | `dashboard/app.py` | Runs with `streamlit run dashboard/app.py`; screenshot in `reports/` | TODO | |
| T-P8-04 | Dashboard v2: **replay mode** — stream RanSMAP/prefix windows with a moving risk-score line, alert marker, "files affected before alert" counter | A | T-P4-04, T-P8-03 | dashboard page | Replay of ≥ 3 ransomware and ≥ 3 goodware runs; alert time displayed | TODO | |
| T-P8-05 | Dashboard v3: alert history table (SQLite), export report (PDF/CSV), model card page (data, metrics, limits) | A | T-P8-04 | dashboard page | Alerts persist across restarts; model card matches `reports/` numbers | TODO | |
| T-P8-06 | Usability pass: 3 teammates test, collect feedback in `reports/usability.md` | A | T-P8-05 | notes | ≥ 3 findings fixed or logged as patches | TODO | |

## Phase 9 — Evaluation report and write-up
| ID | Task | Track | Depends on | Output | Acceptance criteria | Status | Owner |
|---|---|---|---|---|---|---|---|
| T-P9-01 | Final experiment tables regenerated by one command (`make reproduce`); every number traceable to an `E-###` entry | A | all experiments | `reports/final_tables.md` | Fresh clone reproduces within tolerance | TODO | |
| T-P9-02 | Ablations: each improvement on/off (calibration, drift strategy, sequence features, early two-stage) | A | P2–P7 | `reports/ablations.md` | One table, honest negative results included | TODO | |
| T-P9-03 | Limitations + threats to validity section (Track A vs B, small RanSMAP families, VT-first-submission as time proxy, sandbox realism) | A | — | `reports/limitations.md` | Reviewed by team | TODO | |
| T-P9-04 | Final report + slides + demo script | A | T-P9-01 | `reports/final_report.*` | Every contributor named with their parts | TODO | |

## Phase 10 — Backlog / extras (add anything new here; promote to a phase when scheduled)
| ID | Idea | Why | Status |
|---|---|---|---|
| T-P10-01 | Ensemble / stacking of LR + LightGBM + sequence model | possible accuracy gain with drift robustness | TODO |
| T-P10-02 | Active-learning loop: dashboard lets analyst label an alert, retrain candidate model | handles drift in practice | TODO |
| T-P10-03 | Entropy / honeyfile features (decoy-file touch = strong signal) as extra window features | very early signal | TODO |
| T-P10-04 | Ransom-note and extension-change detectors (strings like "how_to_decrypt") as explicit features | cheap, interpretable | TODO |
| T-P10-05 | Export model to ONNX; measure endpoint-agent footprint | deployment realism | TODO |
| T-P10-06 | Dataset paper-style contribution: `MLRan-ext` (Win10/11 + new goodware) release with metadata only | community value | TODO |
| T-P10-07 | Cross-dataset generalisation: train MLRan → test on other public sets where feature overlap exists | external validity | TODO |

---
## How to add a task
Copy a row, take the next free ID in the phase (`T-P4-08`), fill every column, add a line in `04_CHANGELOG.md` ("plan changed") and a decision in `05_DECISIONS.md` if scope changes.
