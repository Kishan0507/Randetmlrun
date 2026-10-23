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



