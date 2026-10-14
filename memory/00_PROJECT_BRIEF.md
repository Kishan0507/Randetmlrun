# 00 — Project brief

## One sentence
Paper (MLRan): *Can machine learning detect ransomware from its behaviour?*
Our project: *Can we make that detection **earlier**, **more accurate on recent software**, **harder to evade**, and **easy to use**?*

## Final deliverable
A working ransomware-detection system with:
1. Improved ML models trained on MLRan (and RanSMAP time-series for early detection).
2. **Early detection**: a risk score that evolves over time and fires before most files are encrypted.
3. A **dashboard** that shows: verdict, confidence, top reasons (SHAP), risk-over-time chart, alert history.
4. A reproducible evaluation report: baseline vs our improvements, with leak-free temporal protocol.

Example output: `Program → observe behaviour → ML model → 95% ransomware → ALERT` with reasons such as "mass file modifications", "suspicious memory allocation (RWX)", "registry tampering".

## Base work we build on
- MLRan dataset + code: https://github.com/faithfulco/mlran (MIT licence, attribute the authors).
- RanSMAP dataset (storage + memory access time series): https://github.com/manabu-hirano/RanSMAP
- Paper: Onwuegbuche et al., "MLRan: A behavioural dataset for ransomware analysis and detection", J. Netw. Comput. Appl. 250 (2026) 104475.

## Scope
**In:** Windows ransomware, binary detection (primary), type and family classification (secondary), early detection, drift analysis, feature-space adversarial testing, explainability, dashboard.
**Out (unless added by a decision):** writing or improving real malware, Linux/macOS/Android, kernel-level drivers, production deployment.

## Two data tracks (see 05_DECISIONS D-001)
- **Track A — data-only (default, no malware execution):** released MLRan 483-feature CSVs + metadata + 20 sample Cuckoo JSONs + RanSMAP.
- **Track B — optional, needs supervisor approval and an isolated lab VM:** re-run samples (by hash) in a Windows 10/11 sandbox to get raw logs (API sequences, timing, flows) and fresh goodware.

## Team
See `07_CONTRIBUTIONS.md` for names, IDEs and areas. Fill it at kickoff.

## Success criteria (measured on the temporal hold-out, never on a random split)
| # | Criterion | Target |
|---|---|---|
| S1 | Reproduce paper baseline on released data | balanced acc within ±0.5 pt of 98.2 (LR, 483 feats) |
| S2 | Leak-free re-evaluation reported honestly | number reported with chronological validation, no test-set selection |
| S3 | False positives on 2023–24 goodware reduced | FPR on 2023–24 goodware lower than baseline by a measured margin |
| S4 | Family classification improved | balanced accuracy and macro-F1 above baseline (47.07% bal. acc.) |
| S5 | Early detection | detect ≥ 90% of ransomware runs using only the first N seconds / first K% of activity; report N and files-lost-before-alert |
| S6 | Adversarial robustness measured | evasion-rate curve vs perturbation budget, before/after hardening |
| S7 | Dashboard works end-to-end | upload/replay → verdict + reasons + timeline in < 5 s per sample |
| S8 | Everything reproducible | `make reproduce` (or documented commands) regenerates all tables |
