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
- Notes: Single decision tree collapses under chronological shift (-6.4% drop). Ensembles and regularized linear models maintain >98% balanced accuracy._
