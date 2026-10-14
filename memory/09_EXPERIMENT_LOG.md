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

_(no experiments yet — first will be E-001, baseline reproduction, T-P1-01)_
