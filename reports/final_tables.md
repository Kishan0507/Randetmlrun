# Master Experiment Results & Reproducibility Tables (T-P9-01)

**Project:** Early Ransomware Detection with Machine Learning + Explainable Dashboard  
**Dataset Reference:** MLRan (JNCA 2026) & RanSMAP (CC BY-ND 4.0)  
**Date:** 2026-10-15  
**Reproducibility Command:** `python scripts/reproduce_all.py`  
**Test Suite Verification:** `pytest -v` (45/45 tests passing green)  

---

## 1. Traceability Matrix: Experiments to Deliverables

| Experiment ID | Task ID | Phase | Component / Technique | Primary Metric | Output Artifact |
|---|---|---|---|---|---|
| **E-001** | T-P1-01, T-P1-02 | Phase 1 | Exact Baseline Reproduction (LR L2) | BalAcc: **98.18%** (TN:498, FP:12, FN:6, TP:459) | `reports/baseline_repro.md` |
| **E-002** | T-P1-03, T-P1-04 | Phase 1 | Leak-Free Temporal Protocol & Bootstrap CIs | 95% CI BalAcc: **[97.25%, 98.98%]** | `src/eval/protocol.py` |
| **E-010** | T-P2-01, T-P2-05 | Phase 2 | Multi-Model Benchmark (8 Models) & Efficiency | LR L2: **98.18%** BalAcc, **0.014 ms/sample**, **9.2 KB** | `reports/model_comparison.md` |
| **E-020** | T-P2-03 | Phase 2 | Family Classification v2 (Class-Weighted LR) | BalAcc: **51.53%** (+4.46% over paper's 47.07%) | `reports/family_recall.csv` |
| **E-021** | T-P2-02 | Phase 2 | Probability Calibration (Platt Scaling) & Budget | ECE: **0.0142**, Operating Point under 1% FPR budget | `configs/operating_point.yaml` |
| **E-025** | T-P2-04 | Phase 2 | Unknown Zero-Day Family Generalisation (LOFO) | Zero-Day Ransomware Catch Rate: **97.95%** | `reports/model_comparison.md` |
| **E-031** | T-P3-01, T-P3-02 | Phase 3 | Temporal Concept Drift & 12 FP Attribution | AUT: **98.54%**; 100% FPs attributed to MS-DOS stub | `reports/drift.md`, `reports/fp_analysis.md` |
| **E-032** | T-P3-03 | Phase 3 | Drift Mitigation (Cost-Weighting Goodware CW=1.5)| Recent 2023-24 FPs cut by **>60%**; BalAcc: **98.28%** | `reports/drift.md` |
| **E-040** | T-P4-03 | Phase 4 | RanSMAP Window Classifiers (Grouped 5-Fold CV) | LightGBM BalAcc: **84.96%**, RF BalAcc: **85.28%** | `reports/early_detection.md` |
| **E-041** | T-P4-04 | Phase 4 | Streaming Decision Rules (EWMA vs k-of-n) | EWMA Conservative: **100% caught**, **21.0s TTD**, **0.00 FA/hr**| `reports/early_detection.md` |
| **E-042** | T-P4-05 | Phase 4 | Dynamic Prefix Truncation Prototype (Cuckoo) | Verified monotonic call progression at t=2,5,10,20s | `src/features/prefix.py` |
| **E-044** | T-P4-07 | Phase 4 | Two-Stage Detection Architecture (D-005) | 100% catch rate at 18s TTD; **0% false alarms on AESCrypt** | `src/models/two_stage.py` |
| **E-070** | T-P7-02 | Phase 7 | Adversarial Evasion Benchmarking (4 Attacks) | Random: 3.4% evasion; Mimicry: 34.0%; Gradient: 100% | `reports/adversarial_robustness.md` |
| **E-071** | T-P7-03 | Phase 7 | Adversarial Training Hardening | Evasion drops from 96.3% to 54.0% at budget 5 (+42.4% defense)| `reports/adversarial_robustness.md` |

---

## 2. Table 1: Binary Classification Performance Comparison

Evaluated on the **guarded chronological test set** (975 samples: 510 goodware, 465 ransomware) split by VirusTotal first-submission date (earliest 80% train / latest 20% test):

| Algorithm | Temporal CV BalAcc | Test Balanced Accuracy [95% CI] | Macro-F1 | Precision (Ran) | Recall (Ran) | FPR (Goodware) | Latency | Model Footprint |
|---|---|---|---|---|---|---|---|---|
| **Logistic Regression (L2)** | **96.33%** | **98.18% [97.25%, 98.98%]** | **0.9818** | **97.45%** | **98.71%** | **2.35%** | **0.014 ms** | **9.2 KB** |
| **LightGBM** | 94.82% | 97.48% [96.34%, 98.43%] | 0.9749 | 97.00% | 97.85% | 2.75% | 0.016 ms | 362.7 KB |
| **Random Forest** | 95.81% | 97.07% [95.92%, 98.05%] | 0.9708 | 96.17% | 97.85% | 3.53% | 0.033 ms | 2,008 KB |
| **Extra Trees** | 95.81% | 97.18% [96.08%, 98.16%] | 0.9719 | 96.38% | 97.85% | 3.33% | 0.033 ms | 2,589 KB |
| **Linear SVM** | 96.20% | 97.10% [95.99%, 98.14%] | 0.9710 | 96.17% | 98.06% | 3.53% | 0.007 ms | 9.1 KB |
| **XGBoost** | 93.29% | 96.99% [95.89%, 98.00%] | 0.9699 | 96.37% | 97.42% | 3.73% | 0.110 ms | 193.3 KB |
| **Decision Tree** | 91.29% | 94.18% [92.70%, 95.62%] | 0.9419 | 93.42% | 94.84% | 6.08% | 0.007 ms | 17.6 KB |

---

## 3. Table 2: Early Detection & Streaming Performance (RanSMAP)

Evaluated across **1,546 sliding windows** from 14 real executions (Conti, LockBit, AESCrypt, Firefox, Office):

| Strategy | Rule Parameters | Ransomware Catch Rate | Median Time-to-Detection (TTD) | Detect@20s | False Alarms / Hour | Goodware Execution FPR | Mean Disk Data Written Before Alert |
|---|---|---|---|---|---|---|---|
| **Raw Window Voting** | $	heta = 0.50$ | 100% (5/5) | 16.0 s | 100.0% | 16.84 FA/hr | 66.7% | 12.97 MB |
| **EWMA Smoothing** | $lpha = 0.3, 	heta = 0.50$ | 100% (5/5) | **18.0 s** | 80.0% | **2.81 FA/hr** | 11.1% | 28.93 MB |
| **EWMA Conservative** | $lpha = 0.2, 	heta = 0.70$ | 100% (5/5) | **21.0 s** | 20.0% | **0.00 FA/hr** | **0.0%** | 55.75 MB |
| **$k$-of-$n$ Window Consensus** | $k=2, n=3, 	heta=0.50$ | 100% (5/5) | 17.0 s | 80.0% | 11.23 FA/hr | 44.4% | 24.76 MB |
| **Two-Stage Architecture (D-005)** | Stage 1 EWMA + Stage 2 Confirm | **100% (5/5)** | **18.0 s** | 80.0% | **0.00 FA/hr** | **0.0% (AESCrypt: 0%)** | 28.93 MB |

---

## 4. Table 3: Adversarial Evasion Resilience & Hardening

Tested on **465 ransomware test samples** under feature perturbation budgets $B \in [1, 30]$:

| Perturbation Budget ($B$) | Random Bit-Flips | Benign Padding (Mimicry) | Malicious Feature Suppression | Gradient-Guided Greedy (Baseline) | Gradient-Guided (Adversarially Hardened) | Hardening Defense Gain |
|---|---|---|---|---|---|---|
| **Budget = 1** | 1.3% | 1.9% | 9.0% | 9.2% | 8.2% | **+1.1%** |
| **Budget = 2** | 1.5% | 5.4% | 14.0% | 30.8% | 16.6% | **+14.2%** |
| **Budget = 5** | 1.9% | 11.0% | 23.2% | 96.3% | 54.0% | **+42.4%** |
| **Budget = 10** | 3.4% | 34.0% | 38.7% | 100.0% | 92.5% | **+7.5%** |
| **Budget = 20** | 5.2% | 83.0% | 73.3% | 100.0% | 100.0% | +0.0% |
| **Budget = 30** | 7.5% | 97.2% | 87.7% | 100.0% | 100.0% | +0.0% |

---

## 5. Table 4: Family Classification v2 & Novel Zero-Day Rejection

| Task | Configuration | Balanced Accuracy | Macro-F1 | Novel Family Catch Rate (LOFO) |
|---|---|---|---|---|
| **65-Class Family Classification** | Paper Flat LR Baseline | 47.07% | 35.96% | N/A |
| **65-Class Family Classification** | **Balanced Logistic Regression (v2)** | **51.53% (+4.46%)** | 33.64% | N/A |
| **65-Class Family Classification** | Hierarchical (Binary -> Family) | 49.46% (+2.39%) | 32.19% | N/A |
| **Novel Zero-Day Family Rejection** | Top-5 Family Leave-One-Family-Out | N/A | N/A | **97.95%** (pajetbin: 100%, cryptolocker: 100%, reveton: 95.5%, locker: 94.3%, virlock: 100%) |

---
*Compiled for Task T-P9-01 (Kalyani / Antigravity).*
