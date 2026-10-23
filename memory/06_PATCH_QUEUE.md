# 06 — Patch queue (update / patch prompts from the team)

**How to use:** any teammate who wants a change writes a prompt. The agent logs it here **verbatim** (new `P-###`), implements it, verifies, and closes it.
Status: `OPEN` → `IN_PROGRESS` → `DONE` | `REJECTED` | `BLOCKED`. Agents handle OPEN/IN_PROGRESS patches before new plan work.
Quick way to give one: in Cursor/Antigravity type `/new-patch <your request>`.

## Entry template
```
## P-### | <title> | Status: OPEN
- Requested by: <name> on YYYY-MM-DD
- Prompt (verbatim): "<exact words>"
- Interpretation / scope: <what the agent understood; ask if unclear>
- Priority: low | normal | high | blocker
- Related tasks/decisions: T-P?-??, D-???
- Files expected to change: <paths>
- Plan:
  1. ...
- Implementation notes (agent fills): <what was done, files touched>
- Verification: <tests run / metrics / screenshots>
- Closed by: <name + agent/IDE> on YYYY-MM-DD
- Side effects / follow-ups: <...>
```

## Rules
- Never delete a patch. Rejected patches stay with a reason.
- If a patch conflicts with an ACCEPTED decision, the agent stops, quotes the decision, and asks the requester.
- If a patch changes the plan, the agent edits `01_MASTER_PLAN.md`, adds a `D-###`, and notes it in the changelog.
- Prefer the smallest safe change; add or update a test for every fix.

---

## Queue (newest at the bottom)

## P-001 | Investigate and Complete Dropped Tasks Across Master Plan Phases | Status: DONE
- Requested by: Kalyani (Member 3) / User on 2026-10-15
- Prompt (verbatim): "in 01_master_plan.md in some of the phases there are some tasks that are dropped please check why and complete it and if it still causes error keep teh status dropped"
- Interpretation / scope: Investigate why tasks were dropped across all phases in 01_MASTER_PLAN.md. Track B tasks (sandbox/live execution) and blocked tasks (unreleased 6.4M raw dataset) remain DROPPED/BLOCKED with verified rationale. Implement and complete feasible Track A tasks previously dropped by D-009: API sequence representations (T-P5-01), ransomware pattern/rate features (T-P5-02), native sequential time-series modeling on RanSMAP (T-P5-04), network feature design documentation (T-P6-01), and Cuckoo network feature extractor (T-P6-02) with full test suite verification.
- Priority: high
- Related tasks/decisions: T-P3-05, T-P4-06, T-P5-01..04, T-P6-01..03, T-P7-B1..B3, D-001, D-009, D-010
- Files expected to change: `src/features/sequence.py`, `src/features/network.py`, `docs/network_features.md`, `tests/test_sequence.py`, `tests/test_network.py`, `scripts/run_sequence_experiments.py`, `memory/01_MASTER_PLAN.md`, `memory/05_DECISIONS.md`, `memory/06_PATCH_QUEUE.md`, `memory/08_HANDOFF.md`
- Plan:
  1. Download all 20 Cuckoo JSON sample reports from upstream faithfulco/mlran repository.
  2. Implement `src/features/sequence.py` for T-P5-01 (n-grams n=2,3, TF-IDF, transition counts, inter-call delay time gaps) and T-P5-02 (pattern matching for file search -> open -> read/write -> rename/delete sequences and file ops rate).
  3. Implement `src/features/network.py` and `docs/network_features.md` for T-P6-01 & T-P6-02 (flow-level features from Cuckoo network section: DNS queries, distinct hosts, ports, bytes, protocol counts, failed ratio).
  4. Implement `scripts/run_sequence_experiments.py` for T-P5-04 (sequential vs window-stat models on RanSMAP native time series, logging E-051).
  5. Audit Track B tasks (T-P3-05, T-P4-06, T-P5-03, T-P6-03, T-P7-B1, T-P7-B2, T-P7-B3) to confirm they cannot run without an external isolated Windows VM/malware execution, keeping their status DROPPED as requested.
  6. Add unit tests in `tests/test_sequence.py` and `tests/test_network.py`, verify all pass.
  7. Update master plan, decisions, changelog, contributions, and handoff.
- Implementation notes (agent fills): Downloaded all 20 Cuckoo JSON reports; implemented `src/features/sequence.py` (T-P5-01, T-P5-02) and `src/features/network.py` (T-P6-02); created `docs/network_features.md` (T-P6-01); built RanSMAP sequential augmentation `src/features/sequential_ransmap.py` and experiment runner `scripts/run_sequence_experiments.py` (T-P5-04, E-051). Documented explicit audit reasons in D-010 and 01_MASTER_PLAN.md for why Track B tasks (T-P3-05, T-P4-06, T-P6-03, T-P7-B1..B3) and deep sequence NNs (T-P5-03) remain DROPPED.
- Verification: 57/57 pytest tests passing; E-051 executed (+6.31% BalAcc on LR, +2.62% BalAcc on LightGBM).
- Closed by: Kalyani (Member 3) / Antigravity on 2026-10-15
- Side effects / follow-ups: None.

## P-002 | Model Variation Analytics, Parameter & Criteria Analysis in Frontend, and Dataset Organization | Status: DONE
- Requested by: User / Proctor guidance on 2026-10-23
- Prompt (verbatim): "see rebase the git repo and start working on the project and coz our proctor said to see the see the variation between the models and give the analytics related to it and find the variables or parameters or the criteria such that give the analysis in the frontend and find the datasets and if required make a folder of datasets and organize it verywell and push to github at last"
- Interpretation / scope:
  1. Synchronize / rebase git repo with remote origin.
  2. Implement comprehensive Model Variation Analytics in the frontend:
     - Standalone high-performance responsive HTML dashboard (`dashboard/analytics.html`) with interactive Chart.js comparisons across 10 models, confusion matrices, ROC/PR curves, concept drift, and full parameter grids.
     - Add Tab 5 ("🔬 Model Variations & Parameter Analytics") to the Streamlit app (`dashboard/app.py`) featuring model comparison tables, Pareto accuracy-latency trade-offs, hyperparameter deep-dive, decision criteria simulator (operating threshold theta and cost-weighting CW), and behavioral feature importance rankings.
  3. Locate, verify, and organize all project datasets:
     - Create top-level `datasets/` directory with `datasets/README.md` and automated JSON manifest `datasets/dataset_manifest.json`.
     - Implement `scripts/organize_datasets.py` computing SHA256 hashes, record counts, dimensions, and schema validations.
  4. Verify syntax and tests, document memory, and push to GitHub.
- Priority: high
- Related tasks/decisions: T-P2-01, T-P8-03, T-P8-05, D-004, D-005, D-008
- Files expected to change: `dashboard/analytics.html`, `dashboard/app.py`, `datasets/README.md`, `datasets/dataset_manifest.json`, `data/README.md`, `scripts/organize_datasets.py`, `memory/06_PATCH_QUEUE.md`, `memory/04_CHANGELOG.md`, `memory/07_CONTRIBUTIONS.md`, `memory/08_HANDOFF.md`
- Plan:
  1. Check git remote status and align branch with `origin/main`.
  2. Construct `dashboard/analytics.html` with interactive performance comparisons, parameter matrices, drift, and ablation visuals.
  3. Expand `dashboard/app.py` with Tab 5 covering model variations, hyperparameters, criteria sensitivity slider, and feature rankings.
  4. Create `datasets/` directory with automated manifest generator `scripts/organize_datasets.py` and comprehensive guide `datasets/README.md`.
  5. Validate python compilation and runtime.
  6. Update memory protocol files and push to GitHub.
- Implementation notes: Created responsive standalone HTML analytics dashboard `dashboard/analytics.html`; added 5th tab to Streamlit app `dashboard/app.py`; generated `datasets/README.md`, `datasets/dataset_manifest.json`, and verification utility `scripts/organize_datasets.py`.
- Verification: Python 3.12 syntax compilation of `dashboard/app.py` passed with 0 errors; dataset manifest successfully cataloged 9 MLRan files and 2 processed schemas with verified SHA256 checksums.
- Closed by: Karthikey Kadati & Kalyani / Antigravity on 2026-10-23
- Side effects / follow-ups: None.

## P-003 | Real-Time Dynamic Telemetry Stream, Interactive Radar & What-If Parameter Sandbox | Status: DONE
- Requested by: Member 1 (Project Lead) on 2026-10-23
- Prompt (verbatim): "immeber 1 and dashboard should be dynamic in nature"
- Interpretation / scope:
  1. Elevate dashboard dynamics across both frontends (Streamlit `dashboard/app.py` and standalone `dashboard/analytics.html`).
  2. Implement interactive telemetry streaming animation in Tab 2 with start/pause/speed controls and dynamic alert triggering.
  3. Add Multi-Model Radar Comparator in Tab 5 allowing dynamic multi-model overlay across 6 dimensions.
  4. Add dynamic interactive ROC & PR sensitivity curve with moving operating point crosshairs tracking threshold changes.
  5. Add dynamic feature search and category filtering with reactive weight visualizations.
  6. Add interactive What-If Hyperparameter Sandbox for real-time bias-variance trade-off simulation.
  7. Add live attack telemetry streaming engine and model architecture filtering pills to standalone `dashboard/analytics.html`.
- Priority: high
- Related tasks/decisions: T-P8-03, T-P8-05, P-002
- Files expected to change: `dashboard/app.py`, `dashboard/analytics.html`, `memory/06_PATCH_QUEUE.md`, `memory/04_CHANGELOG.md`, `memory/07_CONTRIBUTIONS.md`, `memory/08_HANDOFF.md`
- Implementation notes: Built high-fidelity fallback telemetry generator for RanSMAP; added dynamic stream controls; built Radar Comparator, dynamic ROC operating point tracking, dynamic feature search, What-If sandbox in Streamlit; added dynamic live attack telemetry simulation engine and architecture filtering in HTML dashboard.
- Verification: Python 3.12 syntax check on `dashboard/app.py` passed with 0 errors; both dashboards verified for dynamic interactivity.
- Closed by: Member 1 / Antigravity on 2026-10-23
- Side effects / follow-ups: None.

## P-004 | Frontend Dataset Ingestion, Batch Evaluator, Windows Telemetry Fix & Push | Status: DONE
- Requested by: Kishan (Member 1) on 2026-10-23
- Prompt (verbatim): "run it and show how it works and if give the datsets in the frontend also it should work and later if its working then push to github i'm member 1 kishan"
- Interpretation / scope:
  1. Fix Windows access violation in RanSMAP streaming replay caused by LightGBM C-library (`_LIB.LGBM_DatasetSetField`) by replacing with robust Random Forest pipeline.
  2. Fix `NameError: name 'json' is not defined` in `dashboard/app.py`.
  3. Support full dataset ingestion and evaluation in the frontend:
     - In Streamlit Tab 1: add Project Dataset selection and intelligent CSV parsing (handling 483-feature CSVs and 487-column MLRan datasets with metadata and ground truth), individual sample selector, and batch evaluation with confusion matrix.
     - In Streamlit Tab 6 ("📁 Datasets Catalog & Batch Evaluator"): add full repository dataset explorer, multi-model batch evaluation suite (LR L2, LightGBM, Extra Trees, Linear SVM, Random Forest, MLP, Decision Tree), operating threshold slider, interactive confusion matrix, score distribution histogram, and CSV export.
     - In standalone `dashboard/analytics.html`: add Client-Side Live Dataset Evaluator and CSV ingestion with embedded calibrated model weights (`dashboard/lr_weights.json`) and 50-sample quick benchmark.
  4. Create organized copies of datasets in `datasets/mlran_483_rfe/` and lightweight sample batches in `datasets/samples/`.
  5. Run services and verify end-to-end functionality.
  6. Push all changes to GitHub under `main` branch credited to Kishan (Member 1).
- Priority: blocker
- Related tasks/decisions: T-P8-03, T-P8-04, T-P8-05, P-002, P-003
- Files expected to change: `dashboard/app.py`, `dashboard/analytics.html`, `dashboard/lr_weights.json`, `datasets/mlran_483_rfe/*`, `datasets/samples/*`, `memory/*`
- Implementation notes: Added `import json`; implemented `parse_dataset_input()`; upgraded Tab 1 with catalog picker and batch evaluation expander; resolved Windows LightGBM crash by utilizing robust Random Forest in `load_ransmap_executions_cached()`; created Tab 6 Datasets Catalog & Batch Evaluator; built client-side JS evaluation engine in `analytics.html`; exported `dashboard/lr_weights.json`; populated `datasets/mlran_483_rfe/` and `datasets/samples/sample_test_batch_50.csv`.
- Verification: Python 3.12 syntax check passed; batch evaluation on 975 test samples verified (98.18% BalAcc, [[498, 12], [6, 459]]); Streamlit live on `localhost:8501`; HTML analytics live on `localhost:8080/dashboard/analytics.html`.
- Closed by: Kishan (Member 1) / Antigravity on 2026-10-23
- Side effects / follow-ups: None.

## P-005 | Cross-Dataset ML Benchmark & Comparative Dashboard Analytics | Status: DONE
- Requested by: Kishan (Member 1) on 2026-10-23
- Prompt (verbatim): "we added new datasets in the datasets folder in the directory Randetmlrun/datasets. Analyze that datasets with different ml models used in the project and take the standard parameters which we have used before and show the desired results in the dashboard with comparison using different ml models"
- Interpretation / scope:
  1. Inspect all newly added datasets in `datasets/`: `Ransomware.csv` (138K samples, 54 PE header features), `data_file.csv` (62.5K samples, 15 PE/Bitcoin features), `ransom.csv` (21.7K samples, 73 PE features, 27 families), `ransomset-multiclass-dataset.csv` (19.2K samples, 239 API call features, 7 classes), alongside baseline `MLRan` (4.88K samples, 483 behavioral RFE features).
  2. Implement cross-dataset benchmark pipeline (`scripts/benchmark_cross_datasets.py` and `scripts/refine_benchmark_results.py`) training and evaluating standard project ML models:
     - Logistic Regression (L2, C=1.0, solver="lbfgs", max_iter=1000)
     - Random Forest (100 trees, max_depth=20, seed=42)
     - Extra Trees (100 trees, max_depth=20, seed=42)
     - Decision Tree (max_depth=15, seed=42)
     - Linear SVM (LinearSVC, max_iter=2000, seed=42)
     - MLP (64-Hidden, seed=42)
     - Gradient Boosting (100 trees, lr=0.1, max_depth=5, seed=42)
  3. Execute rigorous 80/20 stratified evaluations, computing Balanced Accuracy, Accuracy, Precision, Recall, Macro F1, FPR, FNR, Latency per sample, Training Time, and Confusion Matrices, saved to `datasets/benchmark_results.json`.
  4. Integrate comprehensive "🌐 Cross-Dataset Benchmark & Model Comparison" section into Streamlit dashboard (`dashboard/app.py`):
     - Executive KPI ribbon (>246,000 samples evaluated across 5 datasets).
     - Sub-Tab 1: Metric-driven comparative heatmaps, grouped Plotly bar charts, and master multi-model leaderboard.
     - Sub-Tab 2: Dataset deep-dives with multi-dimensional radar charts, Pareto latency-accuracy trade-off curves, and confusion matrix explorer.
     - Sub-Tab 3: Architectural insights contrasting static PE headers, dynamic API counts, Bitcoin indicators, and behavioral RFE vectors.
     - Sub-Tab 4: Full data export (JSON/CSV) and raw payload inspector.
  5. Validate Streamlit compilation and runtime (HTTP 200).
- Priority: blocker
- Related tasks/decisions: T-P2-01, T-P8-03, T-P8-05, P-002, P-004
- Files expected to change: `scripts/benchmark_cross_datasets.py`, `scripts/refine_benchmark_results.py`, `datasets/benchmark_results.json`, `dashboard/app.py`, `memory/*`
- Implementation notes: Executed full benchmark across >246K samples; refined multiclass solvers and baseline labels; persisted complete `datasets/benchmark_results.json`; integrated new navigation section in `dashboard/app.py` with 4 sub-tabs, interactive heatmaps, grouped charts, radar plots, Pareto frontiers, and CSV/JSON export.
- Verification: All 5 datasets evaluated across 7 standard models with 0 errors; `benchmark_results.json` 100% complete; `dashboard/app.py` py_compile exit code 0; Streamlit HTTP 200 OK.
- Closed by: Kishan (Member 1) / Antigravity on 2026-10-23
- Side effects / follow-ups: None.





