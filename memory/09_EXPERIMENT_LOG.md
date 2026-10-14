# 09 — Experiment log (append at the bottom)

Every metric you quote anywhere must trace to an entry here.

## Entry template
```
## E-### | YYYY-MM-DD | <short title> | Task: T-P?-??
- Run by: <name> / <agent-IDE>
- Git commit: <hash>   Config: configs/<file>.yaml   Seed: 42
- Data: <dataset + version/hash + split description>
- Method: <model, features, selection, calibration, threshold>
- Selection done on: <validation slice dates / folds>   Test set touched: <yes once | no>
- Results (test):  bal.acc=  macro-F1=  precision=  recall=  FPR=  FNR=  PR-AUC=   (95% CI)
- Early-detection (if any): detect@2s/5s/10s/…  median TTD=  FA/hour=
- Artifacts: <paths to csv/plots/models>
- Notes / surprises: <...>
```

---

## E-001 | 2026-10-14 | Baseline LR reproduction | Task: T-P1-01
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: MLRan 483-feature RFE released split (Train: 3,905, Test: 975)
- Method: Logistic Regression (solver='liblinear', C=1.0, max_iter=1000)
- Selection done on: paper split   Test set touched: yes (reproduction)
- Results (test): bal.acc=98.18% [97.25%, 98.98%], macro-F1=98.15% [97.23%, 98.97%], precision=97.45%, recall=98.71%, FPR=2.35%, FNR=1.29%, PR-AUC=0.9963
- Confusion Matrix: TN=498, FP=12, FN=6, TP=459 (exact paper match)
- Artifacts: `reports/baseline_repro.md`, `scripts/reproduce_baseline.py`
- Notes: Exact reproduction of paper Table 6 and Fig 12 confusion matrix.

## E-002 | 2026-10-14 | Baseline multi-model reproduction | Task: T-P1-02
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: MLRan 483-feature RFE released split (Train: 3,905, Test: 975)
- Method: Decision Tree (gini, max_depth=15), Random Forest (100 trees, depth 20), Extra Trees (100 trees, depth 20), LightGBM (100 trees, lr=0.1)
- Selection done on: paper split   Test set touched: yes (reproduction)
- Results (test bal.acc [95% CI]):
  - LR: 98.18% [97.25%, 98.98%]
  - LightGBM: 97.48% [96.34%, 98.43%]
  - Extra Trees: 97.18% [96.08%, 98.16%]
  - Random Forest: 97.07% [95.92%, 98.05%]
  - Decision Tree: 94.18% [92.70%, 95.62%]
- Artifacts: `reports/baseline_repro.md`
- Notes: Evaluated with 1,000 bootstrap resamples. Confirms LR and LightGBM as top performers on 483 RFE features.

## E-003 | 2026-10-14 | Leak-free chronological validation split | Task: T-P1-03
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: MLRan Train (3,905 samples), carved chronologically: Train_sub (3,124 samples, earliest 80%) / Val (781 samples, latest 20% up to 2023-03-21)
- Method: Temporal split, test set guarded (TestSnoopingGuardError). Evaluated LR, DT, RF, ET, LightGBM on unseen temporal val slice.
- Selection done on: chronological val slice   Test set touched: no
- Results (val bal.acc [95% CI]):
  - Extra Trees: 98.64% [97.45%, 99.49%], macro-F1=96.57%
  - Random Forest: 98.41% [97.22%, 99.33%], macro-F1=95.83%
  - Logistic Regression: 98.12% [96.76%, 99.10%], macro-F1=94.86%
  - LightGBM: 96.75% [95.03%, 98.05%], macro-F1=91.85%
  - Decision Tree: 87.79% [84.93%, 90.34%], macro-F1=75.22%
- Artifacts: `src/eval/protocol.py`, `tests/test_protocol.py`, `reports/baseline_repro.md`
- Notes: Single decision tree collapses under chronological shift (-6.4% drop). Ensembles and regularized linear models maintain >98% balanced accuracy.

## E-030 | 2026-10-14 | Concept drift by year & Area Under Time (AUT) | Task: T-P3-01
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: MLRan test set (975 samples: 510 goodware, 465 ransomware) split by first_submission_date_year (2021-2024)
- Method: Baseline LR evaluated per year. Trapezoidal integration for AUT over 2021-2024.
- Results:
  - 2021: FPR = 0.00% (0/26), FNR = 1.83% (4/218), BalAcc = 99.08%
  - 2022: FPR = 1.41% (1/71), FNR = 0.00% (0/57), BalAcc = 99.30%
  - 2023: FPR = 2.20% (4/182), FNR = 0.63% (1/158), BalAcc = 98.58%
  - 2024: FPR = 3.03% (7/231), FNR = 3.12% (1/32), BalAcc = 96.92%
  - AUT (Balanced Accuracy): 0.9854 (98.54%)
- Artifacts: `reports/drift.md`, `scripts/drift_and_fp_analysis.py`
- Notes: Monotonic growth of FPR over time confirms temporal concept drift. Confirmed base-rate confounder (A12): 81% of test goodware is from 2023-2024.

## E-031 | 2026-10-14 | Error analysis and attribution of the 12 false positives | Task: T-P3-02
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: The 12 misclassified goodware samples from test set matched against `goodware_samples_description.csv`
- Method: Model feature weight decomposition, prevalence check in train vs test, application title/category inspection
- Results:
  - Applications: PDFCreator (13020), Zoom (13030), Intel BT (13046), McAfee (13056), TeamSpeak (13069), Avast (13093), Garmin Express (13118), VALORANT (13187), CyberGhost (13292), Razer Cortex (13333), MiKTeX (15187), Scapple (15373).
  - Primary driver: `STRING:!this program cannot be run in dos mode.` (w=+2.599) fired in 12/12 (100%) FPs due to installer packaging format shift.
  - Secondary drivers: `API:LdrGetProcedureAddress` (w=+1.71, 11/12), `API:NtAllocateVirtualMemory` (w=+1.34, 8/12), `SIGNATURE:packer_entropy` (w=+1.28, 5/12).
- Artifacts: `reports/fp_analysis.md`

## E-032 | 2026-10-14 | Drift mitigation evaluation | Task: T-P3-03
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: MLRan 483-feature test set; focus on 2023-2024 goodware (413 samples)
- Method: Compared Cost-Sensitive Loss (CW Goodware=1.5 and 2.0), Recency Weighting (lambda=0.05), Sliding Window (>= 2012), Operating Threshold Tuning (0.70, 0.90)
- Results:
  - Baseline (LR): BalAcc=98.18%, Overall FPR=2.35% (12/510), 2023-24 FPR=2.66% (11/413)
  - Cost-Weight (CW=1.5): BalAcc=98.28%, Overall FPR=2.16% (11/510), 2023-24 FPR=2.42% (10/413), FNR=1.29% (6/465)
  - Operating Point (t=0.70): BalAcc=98.03%, Overall FPR=1.57% (8/510), FNR=2.37% (11/465)
  - Operating Point (t=0.90): BalAcc=95.85%, Overall FPR=0.98% (5/510, meets <1% budget), FNR=7.31% (34/465)
- Artifacts: `reports/drift.md`, `scripts/drift_and_fp_analysis.py`

## E-010 | 2026-10-14 | Wider model comparison & efficiency study | Task: T-P2-01, T-P2-05
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: MLRan 483-feature dataset (Train: 3,905, Test: 975)
- Method: Expanding-window temporal CV (3 folds) on train; full fit and test evaluation with bootstrap CIs for 8 models (LR L1/L2, Linear SVM, DT, RF, Extra Trees, LightGBM, XGBoost).
- Results (Expanding CV BalAcc / Test BalAcc [95% CI] / Latency ms/samp / Size KB):
  - LR (L2): CV=96.33% / Test=98.18% [97.25%, 98.98%] / Lat=0.014 ms / 9.2 KB
  - Linear SVM: CV=96.20% / Test=97.10% [95.99%, 98.14%] / Lat=0.007 ms / 9.1 KB
  - LightGBM: CV=94.82% / Test=97.48% [96.34%, 98.43%] / Lat=0.016 ms / 362.7 KB
  - Extra Trees: CV=95.81% / Test=97.18% [96.08%, 98.16%] / Lat=0.033 ms / 2,589 KB
  - Random Forest: CV=95.81% / Test=97.07% [95.92%, 98.05%] / Lat=0.033 ms / 2,008 KB
  - XGBoost: CV=93.29% / Test=96.99% [95.89%, 98.00%] / Lat=0.110 ms / 193.3 KB
  - Decision Tree: CV=91.29% / Test=94.18% [92.70%, 95.62%] / Lat=0.007 ms / 17.6 KB
- Artifacts: `reports/model_comparison.md`, `scripts/model_comparison.py`, `models/*_test.joblib`

## E-020 | 2026-10-14 | Family classification v2 | Task: T-P2-03
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: MLRan 65-class family task (Goodware + 64 ransomware families)
- Method: Compared flat LR baseline, class-weighted Balanced LR, Hierarchical (Binary -> Family), and Balanced LightGBM.
- Results:
  - Paper Flat LR Baseline: BalAcc = 47.07%, Macro-F1 = 35.96% (exact reproduction)
  - Balanced Logistic Regression (v2): BalAcc = **51.53%** (+4.46%), Macro-F1 = 33.64%
  - Hierarchical Balanced LR: BalAcc = 49.46% (+2.39%), Macro-F1 = 32.19%
  - Balanced LightGBM: BalAcc = 47.63% (+0.56%), Macro-F1 = 32.41%
- Artifacts: `reports/model_comparison.md`

## E-025 | 2026-10-14 | Unknown family rejection & LOFO generalization | Task: T-P2-04
- Run by: Kishan / Antigravity
- Git commit: pending   Config: configs/default.yaml   Seed: 42
- Data: MLRan top 5 ransomware families (pajetbin, cryptolocker, reveton, locker, virlock)
- Method: Leave-One-Family-Out (LOFO) evaluation: train on all other data with target family completely omitted, evaluate zero-day detection rate as ransomware.
- Results:
  - pajetbin (134 samples): 100.00% caught
  - cryptolocker (104 samples): 100.00% caught
  - reveton (89 samples): 95.51% caught
  - locker (87 samples): 94.25% caught
  - virlock (81 samples): 100.00% caught
  - Average Novel Family Detection: **97.95%**
- Artifacts: `reports/model_comparison.md`
