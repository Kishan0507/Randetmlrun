# AGENTS.md — READ THIS FIRST (Cursor, Antigravity, any AI agent)

Project: **Early Ransomware Detection with ML + Explainable Dashboard**
Built on: MLRan (github.com/faithfulco/mlran, JNCA 250 (2026) 104475, MIT licence) and RanSMAP (github.com/manabu-hirano/RanSMAP).
Goal: make MLRan-style behavioural detection **earlier, more accurate, more recent-software-aware, harder to evade, and usable** (dashboard).

This folder is a **shared brain**. Several humans and several AI agents (Cursor, Antigravity) work on the same repo.
Nobody remembers anything between sessions except what is written in `memory/`. Keep it current.

---

## 1. Session START protocol (mandatory, in this order)
1. Read `memory/08_HANDOFF.md` — what the last person/agent did and what is next.
2. Read `memory/06_PATCH_QUEUE.md` — handle every `OPEN` / `IN_PROGRESS` patch BEFORE new plan work, unless the user says otherwise.
3. Read `memory/01_MASTER_PLAN.md` — find the next `TODO` task (respect `Depends on`).
4. Skim `memory/05_DECISIONS.md` — never silently reverse a past decision.
5. Say to the user in 1–3 lines: which task/patch ID you are starting and who it is credited to. Ask "who am I working for?" if the contributor is unknown.

## 2. Session END protocol (mandatory, never skip)
1. Add an entry at the TOP of `memory/04_CHANGELOG.md` (template inside).
2. Update task status in `memory/01_MASTER_PLAN.md` (`TODO` → `IN_PROGRESS` → `DONE` | `BLOCKED`).
3. If a patch prompt was given: update its entry in `memory/06_PATCH_QUEUE.md` (status, files touched, verification).
4. Add or extend the contributor's line in `memory/07_CONTRIBUTIONS.md`.
5. Log every metric run in `memory/09_EXPERIMENT_LOG.md` (config, seed, data version, numbers).
6. Overwrite `memory/08_HANDOFF.md` (done / in progress / next / open questions / gotchas).
7. Commit with message `[T-P3-02] feat: short summary` and trailer `Contributed-by: <Name>`.

**Code changed but memory not updated = task not finished.**

## 3. Working rules
- **Credit everyone.** Every changelog entry, patch and commit names the contributor (human) and the agent/IDE used. Never delete or rewrite someone else's entries — append only.
- **Patch prompts are first-class.** When the user says "patch / update / fix / change X", first create `P-###` in `06_PATCH_QUEUE.md` with the user's words **verbatim**, then implement, then verify, then close it. Do not just edit code silently.
- One task ID per commit where possible. Branch name: `feat/<member>/<task-id>`. Don't push to `main` directly.
- Never edit `data/raw/`. Derived data goes to `data/processed/` with a version tag.
- Reproducibility: seed = 42, parameters in `configs/*.yaml`, no hard-coded paths, pin versions in `requirements.txt`.
- **Temporal discipline** (the paper's own guideline): split by VirusTotal first-submission date (earliest 80% train / latest 20% test). Feature selection, scaling, resampling, threshold choice and hyper-parameter tuning use **training data only** (use a chronological validation slice carved from train). The test set is touched once per experiment for the final number.
- Report: balanced accuracy, macro-F1, precision, recall, FPR, FNR (and PR-AUC). Accuracy alone is not enough.
- Do not trust paper numbers blindly. See `memory/03_PAPER_AUDIT.md`.
- Unsure? Write the question under "Open questions" in `08_HANDOFF.md` and ask the user. Do not guess silently.
- Keep notebooks thin: logic lives in `src/`, notebooks only call it.

## 4. SAFETY (non-negotiable)
- Do **not** write, modify, obfuscate or "improve" ransomware or evasion malware. Do not commit malware binaries or live samples.
- Adversarial testing is **feature-space only** (perturbing feature vectors / replaying logs). No real evasive payloads.
- Live malware execution (Track B, see plan) is done only by a human, in an isolated VM with no route to real networks, with supervisor approval, outside this repo.
- Share only derived features, metadata and logs (paper guideline C14).

## 5. Known facts about the base data (verified from the MLRan GitHub repo)
- Repo layout: `1_sample_collection_scripts/ 2_collected_samples_metadata/ 3_cuckoo_submission_automation/ 4_cuckoo_parser_scripts/ 5_mlran_dataset/ 6_experiments/`.
- **The full 6.4M-feature MLRan dataset is NOT public yet** (`5_mlran_dataset/README.md` says it will be released after publication). Check upstream again at task T-P0-03.
- What IS public: the 483-feature RFE dataset in `6_experiments/FS_MLRan_Datasets/` (`MLRan_X_train_RFE.csv` 3,905 rows, `MLRan_X_test_RFE.csv` 975 rows, `MLRan_labels.csv`, `RFE_selected_feature_names_dic.json`, metadata CSVs, type train/test sample-id files), plus metadata with SHA256 hashes and first-submission dates, plus 20 sample Cuckoo JSON reports in `4_cuckoo_parser_scripts/json_reports/`.
- Feature columns in the CSVs are numeric indices; names are in `RFE_selected_feature_names_dic.json`.
- Consequence: anything needing raw behaviour (API **sequences**, **timing**, flow-level network, early-detection on MLRan reports) needs either (a) RanSMAP time-series data, (b) the 20 sample reports for prototyping, or (c) Track B (re-running samples in our own sandbox). The plan is split into Track A (data-only, no malware execution) and Track B (optional) for this reason.
- RanSMAP repo structure was **not** verified when this scaffold was made (clone failed). Task T-P0-02 must inspect it and record the findings in `memory/05_DECISIONS.md`.

## 6. Folder map
```
AGENTS.md                      <- this file
.cursor/rules/ .cursor/commands/   <- Cursor pointers + slash commands
.agent/rules/  .agent/workflows/   <- Antigravity pointers + workflows
memory/                        <- THE PROJECT BRAIN (index: memory/README.md)
configs/  data/{raw,processed}/  src/{data,features,models,eval,explain,adversarial,app}/
notebooks/  reports/  tests/  dashboard/  scripts/
```

## 7. Tech defaults
Python 3.11, pandas, numpy, scikit-learn, LightGBM, XGBoost, PyTorch (sequence models), SHAP, LIME, Streamlit (dashboard), pytest, ruff. Change only through a `05_DECISIONS.md` entry.
