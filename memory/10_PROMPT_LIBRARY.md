# 10 — Prompt library (copy-paste into Cursor / Antigravity)

Replace `<NAME>` with the human's name. Every prompt assumes the agent has read `AGENTS.md`.

---
## 1. Kickoff prompt (first session, any agent)
```
You are working on the "Early Ransomware Detection with ML + Explainable Dashboard" project.
Read AGENTS.md, then everything in memory/ in numeric order. Then:
1. Summarise the project in 5 lines and list the Track A vs Track B split.
2. Tell me which task from memory/01_MASTER_PLAN.md is next (respect dependencies).
3. I am <NAME>. Credit all work to me in the changelog, ledger and commits.
Do not write code until you have told me the plan for this session and I confirm.
```

## 2. Start-of-session prompt
```
/start-session
I am <NAME>. Today I want to work on <task ID or "whatever is next">.
```

## 3. Work-on-a-task prompt
```
Work on task <T-P?-??> from memory/01_MASTER_PLAN.md for <NAME>.
Follow the acceptance criteria in the plan row exactly. Use the temporal protocol in D-007.
Keep logic in src/, notebooks thin, seed 42, configs in configs/.
When done: run tests, then run the Session END protocol (changelog, plan status, ledger, experiment log, handoff).
```

## 4. Patch / update prompt (the one to use for every change request)
```
/new-patch
Requested by <NAME>: <describe exactly what to change and why>.
Priority: <low|normal|high|blocker>. Affects: <files or tasks if you know>.
```
Agent must: log verbatim as P-###, state interpretation, check conflicts with decisions, implement the smallest safe change, add/adjust tests, verify, close the patch, update memory.

## 5. End-of-session prompt
```
/end-session
Contributor: <NAME>. Summarise what changed in 5 lines at the end.
```

## 6. Review prompt (a second agent/person reviews)
```
Review the last changes in git (git log -5, git diff HEAD~N) against memory/04_CHANGELOG.md.
Check: (a) any test-set leakage (selection, scaling, thresholds fitted on test?), (b) metrics reported honestly with CI,
(c) memory files updated, (d) safety rules in AGENTS.md respected.
Write findings as new patches in memory/06_PATCH_QUEUE.md credited to <REVIEWER NAME>.
```

---
## Phase prompts (give to the agent that owns the phase)

### P0 — setup and audit
```
Do T-P0-01 to T-P0-06 in order. Vendor the MLRan released files into data/raw/mlran/ without modifying them,
record SHA256 in data/README.md, write src/data/load_mlran.py that rebuilds the paper split from type_train_sampleids.csv/type_test_sampleids.csv
(expect 3,905 train / 975 test) and maps numeric feature columns to names via RFE_selected_feature_names_dic.json.
Then verify audit items A1–A14 in memory/03_PAPER_AUDIT.md that can be checked from data and mark each with evidence.
```

### P1 — baseline and leak-free protocol
```
Do T-P1-01 to T-P1-05. Reproduce Logistic Regression and the other 4 models on the 483-feature split and compare to Tables 5/6 and Fig. 12 (498/12/6/459).
Then implement the leak-free protocol: a chronological validation slice inside the training period for ALL selection; the test set is accessed once via a guarded function.
Implement the full metric suite with bootstrap 95% CI. Log E-001..E-004.
```

### P2 — better models
```
Do T-P2-01 to T-P2-05. Compare LR (L1/L2/elastic), linear SVM, RF, ExtraTrees, LightGBM, XGBoost, small MLP using expanding-window chronological CV.
Calibrate probabilities and pick the operating point under an FPR budget on validation only. Build hierarchical family classification and unknown-family rejection.
Report balanced accuracy and macro-F1 for type and family, plus per-family recall. Measure inference latency and model size.
```

### P3 — drift and false positives
```
Do T-P3-01 to T-P3-04. Plot per-year FPR/FNR and compute AUT. Analyse the baseline's 12 false positives with SHAP/LIME and the metadata (goodware names, years, source).
Try: sliding-window retraining, recency weights, cost-sensitive loss, recalibration, and a drift detector. Write docs/goodware_protocol.md for collecting new goodware.
```

### P4 — early detection (core)
```
Do T-P4-01 to T-P4-05, T-P4-07. First write docs/early_detection_protocol.md (TTD, detection@t, files/bytes before alert, false alarms per hour; censoring rules).
Load RanSMAP as windowed series with group splits by execution and by family (no leakage). Train a window classifier, add a streaming rule (EWMA or k-of-n) and compare rules.
Prototype prefix truncation on the 20 sample Cuckoo JSONs. Combine into a two-stage design (fast early alert + slower confirmation) and run the ablation.
```

### P5 — order and timing
```
Do T-P5-01, T-P5-02, T-P5-04 (Track A). Build API n-gram/transition/inter-call-time features and "find→open→read/write→rename/delete" pattern features from Cuckoo call logs (20 samples) and the native time ordering of RanSMAP.
Compare sequence models (1D-CNN, GRU) vs window-statistics baseline on RanSMAP with confidence intervals. Mark scale-up (T-P5-03) as Track B.
```

### P6 — network flow features
```
Do T-P6-01 and T-P6-02. Write docs/network_features.md and src/features/network.py computing aggregate flow-level features (DNS count, distinct hosts/ports, bytes, burst rate, TLD entropy, failed-connection ratio) from Cuckoo's network section. Test on the 20 sample reports.
```

### P7 — robustness (feature-space only)
```
Do T-P7-01 to T-P7-04. Follow AGENTS.md safety rules: NO real malware or evasion payloads. Write docs/threat_model.md, implement feature-space attacks
(random flips, benign padding, top-k SHAP feature removal, greedy gradient-guided on LR/surrogate) and hardening (adversarial training, group dropout, monotonic constraints).
Output evasion-rate vs budget curves before/after hardening and the clean-accuracy cost. Also write reports/execution_failures.md from the paper's per-source dropout counts.
```

### P8 — dashboard
```
Do T-P8-01 to T-P8-06. Build src/explain/reasons.py with a YAML lookup that turns feature names into plain-language reasons; a predict() API returning verdict, confidence, reasons, model_version;
a Streamlit dashboard with verdict card, confidence gauge, SHAP reasons, risk-over-time replay with alert marker and "files affected before alert" counter, SQLite alert history, and a model-card page whose numbers come from reports/.
```

### P9 — final report
```
Do T-P9-01 to T-P9-04. One command regenerates all tables from configs; every number cites an E-### entry; ablations include negative results; limitations cover Track A vs B, small RanSMAP family count,
VirusTotal first-submission as a time proxy, and sandbox realism. Acknowledgements come from memory/07_CONTRIBUTIONS.md.
```

---
## Handy one-liners
- "Show me every OPEN patch and which task it touches."
- "Which tasks are unblocked right now?"
- "Compare the last two entries in 09_EXPERIMENT_LOG.md and tell me what changed."
- "Check the repo for any place the test set is used before the final evaluation call."
- "Update memory/ for what we just did, credit <NAME>."
