"""Phase 2: model comparison, calibration, family v2, unknown rejection, efficiency.

Tasks: T-P2-01, T-P2-02, T-P2-03, T-P2-04, T-P2-05
Outputs: reports/model_comparison.md, reports/reliability_curve.png,
         reports/family_recall.csv, configs/operating_point.yaml
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
import yaml
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

from src.data.load_mlran import load_mlran_dataset
from src.eval.metrics import compute_metrics
from src.eval.protocol import ChronologicalExpandingKFold, make_leak_free_split
from src.models.calibrate import (
    CalibratedModelWrapper,
    evaluate_calibration,
    find_operating_threshold,
    save_reliability_curve,
)
from src.models.family import (
    OTHER_LABEL,
    UNKNOWN_LABEL,
    choose_unknown_threshold,
    family_name_map,
    fit_ovr_family_model,
    hierarchical_predict,
    merge_rare_families,
    per_family_recall,
    unknown_flags,
)


SEED = 42
BOOTSTRAP = 1000
MIN_FAMILY_SAMPLES = 10
KNOWN_KEEP_RATE = 0.95
FPR_BUDGET = 0.01


def candidate_models() -> dict:
    return {
        "Logistic Regression (L2, liblinear)": LogisticRegression(
            C=1.0, solver="liblinear", random_state=SEED, max_iter=1000
        ),
        "Logistic Regression (L1, liblinear)": LogisticRegression(
            C=1.0, penalty="l1", solver="liblinear", random_state=SEED, max_iter=1000
        ),
        "Logistic Regression (elastic-net)": LogisticRegression(
            C=1.0,
            penalty="elasticnet",
            solver="saga",
            l1_ratio=0.5,
            random_state=SEED,
            max_iter=4000,
        ),
        "Linear SVM (LinearSVC)": LinearSVC(C=1.0, random_state=SEED, dual="auto", max_iter=4000),
        "Decision Tree (max_depth=15)": DecisionTreeClassifier(
            criterion="gini", max_depth=15, random_state=SEED
        ),
        "Random Forest (n=100, depth=20)": RandomForestClassifier(
            n_estimators=100, max_depth=20, random_state=SEED, n_jobs=-1
        ),
        "Extra Trees (n=100, depth=20)": ExtraTreesClassifier(
            n_estimators=100, max_depth=20, random_state=SEED, n_jobs=-1
        ),
        "LightGBM (n=100, lr=0.1)": lgb.LGBMClassifier(
            n_estimators=100, learning_rate=0.1, random_state=SEED, verbose=-1, n_jobs=-1
        ),
        "XGBoost (n=100, lr=0.1)": xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=SEED,
            n_jobs=-1,
            eval_metric="logloss",
        ),
        "MLP (64 hidden, sklearn)": MLPClassifier(
            hidden_layer_sizes=(64,),
            max_iter=300,
            random_state=SEED,
            early_stopping=True,
            validation_fraction=0.1,
        ),
    }


def scores_from_model(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        return model.decision_function(X)
    return None


def run_model_comparison():
    print("Loading MLRan dataset...")
    ds = load_mlran_dataset(rename_features=False)
    split = make_leak_free_split(ds, val_fraction=0.20)
    models = candidate_models()

    # -------------------------------------------------------------
    # 1. T-P2-01: Wider Model Comparison (selection on expanding CV)
    # -------------------------------------------------------------
    print("\n--- T-P2-01: Wider Model Comparison (expanding-window CV on train) ---")
    cv = ChronologicalExpandingKFold(n_splits=3)
    dates_train = ds.meta_train["first_submission_date_converted"].to_numpy()

    cv_scores = {}
    for name, proto in models.items():
        fold_scores = []
        for train_idx, val_idx in cv.split(ds.X_train, dates_train):
            est = clone(proto)
            X_tr, y_tr = ds.X_train.iloc[train_idx], ds.y_train_binary.iloc[train_idx]
            X_va, y_va = ds.X_train.iloc[val_idx], ds.y_train_binary.iloc[val_idx]
            est.fit(X_tr, y_tr)
            fold_scores.append(balanced_accuracy_score(y_va, est.predict(X_va)))
        cv_scores[name] = float(np.mean(fold_scores))
        print(f"Expanding CV: {name:42s} | BalAcc: {cv_scores[name]*100:.2f}%")

    best_name = max(cv_scores, key=cv_scores.get)
    print(f"Selected by CV (not test): {best_name} ({cv_scores[best_name]*100:.2f}%)")

    print("\nUnlocking test set once for the comparison table + efficiency (T-P2-05)...")
    split.unlock_test_set()

    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    model_records = []
    fitted = {}

    for name, proto in models.items():
        est = clone(proto)
        t0 = time.perf_counter()
        est.fit(ds.X_train, ds.y_train_binary)
        train_time = time.perf_counter() - t0
        fitted[name] = est

        t0 = time.perf_counter()
        test_preds = est.predict(split.X_test)
        lat_per_sample = ((time.perf_counter() - t0) / len(split.X_test)) * 1000.0

        safe = "".join(ch if ch.isalnum() else "_" for ch in name.lower())[:40]
        model_file = models_dir / f"{safe}.joblib"
        joblib.dump(est, model_file)
        model_size_kb = os.path.getsize(model_file) / 1024.0

        y_score = scores_from_model(est, split.X_test)
        m = compute_metrics(
            split.y_test, test_preds, y_score, bootstrap_resamples=BOOTSTRAP, seed=SEED
        )
        bal_ci = m.ci_95["balanced_accuracy"] if m.ci_95 else (0, 0)
        f1_ci = m.ci_95["macro_f1"] if m.ci_95 else (0, 0)
        model_records.append(
            {
                "Model": name,
                "CV BalAcc": f"{cv_scores[name]*100:.2f}%",
                "Test BalAcc (95% CI)": f"{m.balanced_accuracy*100:.2f}% [{bal_ci[0]*100:.2f}%, {bal_ci[1]*100:.2f}%]",
                "Macro-F1 (95% CI)": f"{m.macro_f1*100:.2f}% [{f1_ci[0]*100:.2f}%, {f1_ci[1]*100:.2f}%]",
                "FPR": f"{m.fpr*100:.2f}%",
                "FNR": f"{m.fnr*100:.2f}%",
                "Train Time (s)": round(train_time, 2),
                "Latency (ms/samp)": round(lat_per_sample, 3),
                "Size (KB)": round(model_size_kb, 1),
                "_cv": cv_scores[name],
                "_test_bal": m.balanced_accuracy,
                "_lat": lat_per_sample,
                "_size": model_size_kb,
            }
        )
        print(f"Test: {name:42s} | BalAcc {m.balanced_accuracy*100:.2f}%")

    df_models = pd.DataFrame(model_records)
    best_row = df_models.loc[df_models["_cv"].idxmax()]

    # -------------------------------------------------------------
    # 2. T-P2-02: Calibration + FPR-budget operating point (val only)
    # -------------------------------------------------------------
    print("\n--- T-P2-02: Probability Calibration & Operating Point ---")
    base_lr = LogisticRegression(C=1.0, solver="liblinear", random_state=SEED, max_iter=1000)
    base_lr.fit(split.X_train_sub, split.y_train_sub)

    cal_wrapper = CalibratedModelWrapper(base_lr, method="sigmoid")
    cal_wrapper.fit_calibration(split.X_val, split.y_val)
    cal_val_probs = cal_wrapper.predict_proba(split.X_val)[:, 1]
    op_val = find_operating_threshold(split.y_val, cal_val_probs, fpr_budget=FPR_BUDGET)

    raw_test_probs = base_lr.predict_proba(split.X_test)[:, 1]
    cal_test_probs = cal_wrapper.predict_proba(split.X_test)[:, 1]
    raw_calib_stats = evaluate_calibration(split.y_test, raw_test_probs)
    cal_calib_stats = evaluate_calibration(split.y_test, cal_test_probs)

    m_default = compute_metrics(
        split.y_test, (raw_test_probs >= 0.5).astype(int), raw_test_probs, bootstrap_resamples=0
    )
    m_budget = compute_metrics(
        split.y_test,
        (cal_test_probs >= op_val.threshold).astype(int),
        cal_test_probs,
        bootstrap_resamples=0,
    )
    n_neg = int((split.y_test == 0).sum())

    reliability_path = Path("reports/reliability_curve.png")
    save_reliability_curve(
        split.y_test,
        {"Uncalibrated": raw_test_probs, "Platt (val-fit)": cal_test_probs},
        reliability_path,
    )

    op_cfg = {
        "method": "sigmoid",
        "fpr_budget": FPR_BUDGET,
        "threshold": float(op_val.threshold),
        "selected_on": "chronological validation slice (calibrated probs)",
        "val_empirical_fpr": float(op_val.empirical_fpr),
        "val_empirical_recall": float(op_val.empirical_recall),
        "base_model": "LogisticRegression(C=1.0, solver=liblinear)",
        "seed": SEED,
    }
    Path("configs/operating_point.yaml").write_text(
        yaml.safe_dump(op_cfg, sort_keys=False), encoding="utf-8"
    )

    calib_summary = pd.DataFrame(
        [
            {
                "Configuration": "Uncalibrated (t=0.50)",
                "Threshold": "0.50",
                "Brier": f"{raw_calib_stats['brier_score']:.4f}",
                "ECE": f"{raw_calib_stats['ece']:.4f}",
                "Test FPR": f"{m_default.fpr*100:.2f}% ({m_default.fp}/{n_neg})",
                "Test Recall": f"{m_default.recall*100:.2f}%",
                "Test BalAcc": f"{m_default.balanced_accuracy*100:.2f}%",
            },
            {
                "Configuration": f"Platt + FPR<={FPR_BUDGET:.0%} (val-tuned t)",
                "Threshold": f"{op_val.threshold:.3f}",
                "Brier": f"{cal_calib_stats['brier_score']:.4f}",
                "ECE": f"{cal_calib_stats['ece']:.4f}",
                "Test FPR": f"{m_budget.fpr*100:.2f}% ({m_budget.fp}/{n_neg})",
                "Test Recall": f"{m_budget.recall*100:.2f}%",
                "Test BalAcc": f"{m_budget.balanced_accuracy*100:.2f}%",
            },
        ]
    )

    # -------------------------------------------------------------
    # 3. T-P2-03: Family classification v2
    # -------------------------------------------------------------
    print("\n--- T-P2-03: Family Classification v2 ---")
    y_tr_fam, y_te_fam, rare = merge_rare_families(
        ds.y_train_family, ds.y_test_family, min_samples=MIN_FAMILY_SAMPLES
    )
    n_before = ds.y_train_family.nunique()
    n_after = y_tr_fam.nunique()
    print(f"Merged {len(rare)} rare families (<{MIN_FAMILY_SAMPLES} train samples): {n_before} → {n_after} classes")

    names = family_name_map(pd.concat([ds.meta_train, ds.meta_test]))
    names[OTHER_LABEL] = "other"

    def _fam_metrics(y_true, y_pred):
        return (
            float(balanced_accuracy_score(y_true, y_pred)),
            float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        )

    clf_flat = LogisticRegression(max_iter=1000, random_state=SEED)
    clf_flat.fit(ds.X_train, ds.y_train_family)
    pred_flat = clf_flat.predict(split.X_test)
    bal_flat, f1_flat = _fam_metrics(ds.y_test_family, pred_flat)

    clf_bal = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=SEED)
    clf_bal.fit(ds.X_train, ds.y_train_family)
    pred_bal = clf_bal.predict(split.X_test)
    bal_bal, f1_bal = _fam_metrics(ds.y_test_family, pred_bal)

    clf_bin = LogisticRegression(C=1.0, solver="liblinear", random_state=SEED, max_iter=1000)
    clf_bin.fit(ds.X_train, ds.y_train_binary)
    pred_bin = clf_bin.predict(split.X_test)
    ran_train_mask = ds.y_train_binary == 1
    clf_fam = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=SEED)
    clf_fam.fit(ds.X_train[ran_train_mask], ds.y_train_family[ran_train_mask])
    pred_hier = hierarchical_predict(pred_bin, clf_fam.predict(split.X_test))
    bal_hier, f1_hier = _fam_metrics(ds.y_test_family, pred_hier)

    clf_lgb_fam = lgb.LGBMClassifier(
        n_estimators=100,
        class_weight="balanced",
        learning_rate=0.05,
        random_state=SEED,
        verbose=-1,
        n_jobs=-1,
    )
    clf_lgb_fam.fit(ds.X_train, ds.y_train_family)
    pred_lgb = clf_lgb_fam.predict(split.X_test)
    bal_lgb, f1_lgb = _fam_metrics(ds.y_test_family, pred_lgb)

    clf_merged = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=SEED)
    clf_merged.fit(ds.X_train, y_tr_fam)
    pred_merged = clf_merged.predict(split.X_test)
    bal_merged, f1_merged = _fam_metrics(y_te_fam, pred_merged)

    paper_bal = 47.07
    df_family = pd.DataFrame(
        [
            {
                "Method": "Paper Baseline (Flat LR, 65-class)",
                "Balanced Accuracy": f"{bal_flat*100:.2f}%",
                "Macro-F1": f"{f1_flat*100:.2f}%",
                "Vs. Paper": f"{bal_flat*100 - paper_bal:+.2f} pt",
            },
            {
                "Method": "Balanced LR (v2, 65-class)",
                "Balanced Accuracy": f"{bal_bal*100:.2f}%",
                "Macro-F1": f"{f1_bal*100:.2f}%",
                "Vs. Paper": f"{bal_bal*100 - paper_bal:+.2f} pt",
            },
            {
                "Method": "Hierarchical Balanced LR (binary→family)",
                "Balanced Accuracy": f"{bal_hier*100:.2f}%",
                "Macro-F1": f"{f1_hier*100:.2f}%",
                "Vs. Paper": f"{bal_hier*100 - paper_bal:+.2f} pt",
            },
            {
                "Method": "Balanced LightGBM (65-class)",
                "Balanced Accuracy": f"{bal_lgb*100:.2f}%",
                "Macro-F1": f"{f1_lgb*100:.2f}%",
                "Vs. Paper": f"{bal_lgb*100 - paper_bal:+.2f} pt",
            },
            {
                "Method": f"Balanced LR + rare-merge (N<{MIN_FAMILY_SAMPLES} → Other)",
                "Balanced Accuracy": f"{bal_merged*100:.2f}%",
                "Macro-F1": f"{f1_merged*100:.2f}%",
                "Vs. Paper": "not comparable (fewer classes)",
            },
        ]
    )

    best_fam_pred = pred_bal
    fam_recall = per_family_recall(ds.y_test_family, best_fam_pred, name_map=names, min_support=1)
    fam_recall = fam_recall.sort_values(["support", "recall"], ascending=[False, False])
    fam_recall.to_csv("reports/family_recall.csv", index=False)
    fam_recall_md = fam_recall.head(25).assign(recall=lambda d: (d["recall"] * 100).round(1).astype(str) + "%")
    fam_recall_md = fam_recall_md.rename(columns={"family_id": "ID", "family": "Family", "support": "N", "recall": "Recall"})

    # -------------------------------------------------------------
    # 4. T-P2-04: Unknown-family rejection + LOFO binary catch
    # -------------------------------------------------------------
    print("\n--- T-P2-04: Unknown-family rejection + LOFO ---")
    ovr = fit_ovr_family_model(split.X_train_sub, ds.y_train_family.loc[split.X_train_sub.index])
    _, val_max = unknown_flags(ovr, split.X_val, confidence_threshold=0.0)
    tau = choose_unknown_threshold(val_max, target_known_keep_rate=KNOWN_KEEP_RATE)
    pred_unk, test_max = unknown_flags(ovr, split.X_test, confidence_threshold=tau)
    known_flagged = float((pred_unk == UNKNOWN_LABEL).mean())
    print(f"Unknown threshold tau={tau:.4f} (val {KNOWN_KEEP_RATE:.0%} keep); test unknown rate={known_flagged*100:.2f}%")

    meta_all = pd.concat([ds.meta_train, ds.meta_test])
    X_all = pd.concat([ds.X_train, ds.X_test])
    y_bin_all = pd.concat([ds.y_train_binary, ds.y_test_binary])
    y_fam_all = pd.concat([ds.y_train_family, ds.y_test_family])
    top5 = y_fam_all[y_fam_all > 0].value_counts().head(5).index

    lofo_records = []
    for fam in top5:
        fam_name = names.get(int(fam), str(fam))
        train_mask = y_fam_all != fam
        test_mask = y_fam_all == fam

        clf_lofo = LogisticRegression(C=1.0, solver="liblinear", random_state=SEED, max_iter=1000)
        clf_lofo.fit(X_all[train_mask], y_bin_all[train_mask])
        det_rate = float((clf_lofo.predict(X_all[test_mask]) == 1).mean())

        ovr_lofo = fit_ovr_family_model(X_all[train_mask], y_fam_all[train_mask])
        _, held_max = unknown_flags(ovr_lofo, X_all[test_mask], confidence_threshold=0.0)
        unk_rate = float((held_max < tau).mean())

        lofo_records.append(
            {
                "Held-Out Family": fam_name,
                "Family ID": int(fam),
                "Samples": int(test_mask.sum()),
                "Caught as ransomware (binary)": f"{det_rate * 100:.2f}%",
                "Flagged unknown (OVR max-prob < tau)": f"{unk_rate * 100:.2f}%",
            }
        )
        print(f"LOFO {fam_name}: ransomware {det_rate*100:.1f}% | unknown {unk_rate*100:.1f}%")

    df_lofo = pd.DataFrame(lofo_records)
    avg_det = float(np.mean([float(r["Caught as ransomware (binary)"].rstrip("%")) for r in lofo_records]))
    avg_unk = float(np.mean([float(r["Flagged unknown (OVR max-prob < tau)"].rstrip("%")) for r in lofo_records]))

    display_models = df_models.drop(columns=[c for c in df_models.columns if c.startswith("_")])

    report_content = f"""# Model Comparison, Calibration, and Family Classification Report

Generated: 2026-10-14 by Kishan / Cursor
Tasks: T-P2-01, T-P2-02, T-P2-03, T-P2-04, T-P2-05
Experiments: E-010 (models), E-011 (efficiency), E-012 (calibration), E-020 (family v2), E-025 (unknown / LOFO)

---

## 1. Wider Binary Model Comparison (T-P2-01)

Expanding-window chronological CV (3 folds) on **training data only**. The winner is chosen by CV balanced accuracy; the test column is a one-shot report after that choice, not a selection criterion.

**Selected model (CV):** {best_name} (CV BalAcc {best_row['_cv']*100:.2f}%).

{display_models.to_markdown(index=False)}

### Observations
- Best validation model: **{best_name}**.
- Test balanced accuracy for that model: **{best_row['Test BalAcc (95% CI)']}**.
- CatBoost was skipped (not in the pinned stack; D-009 CPU-only sklearn / LightGBM / XGBoost). A small sklearn MLP is included instead of PyTorch.

---

## 2. Efficiency (T-P2-05)

Latency is wall-clock `predict` on the 975-row test set (CPU). Size is joblib dump size.

- Fastest compact model in this run: see the Latency / Size columns above.
- Selected model size: **{best_row['_size']:.1f} KB**, latency **{best_row['_lat']:.3f} ms/sample**.

---

## 3. Probability Calibration & Operating Point (T-P2-02)

Platt scaling (sigmoid) fit on the chronological validation slice. The FPR ≤ {FPR_BUDGET:.0%} threshold is chosen on **calibrated validation probabilities**, then applied once to test. Stored in `configs/operating_point.yaml` (threshold={op_val.threshold:.4f}; val FPR={op_val.empirical_fpr*100:.2f}%, val recall={op_val.empirical_recall*100:.2f}%).

Reliability curve: `reports/reliability_curve.png`.

{calib_summary.to_markdown(index=False)}

Note: test FPR can exceed the budget even when validation FPR meets it (temporal drift; see Phase 3). The budget is a validation constraint, not a test guarantee.

---

## 4. Family Classification v2 (T-P2-03)

Paper 65-class balanced accuracy is **47.07%**. Rare-family merge uses train counts only (N < {MIN_FAMILY_SAMPLES} → Other; {len(rare)} families merged; {n_before} → {n_after} classes). Merged metrics are **not** comparable to the paper.

{df_family.to_markdown(index=False)}

**Headline (same 65-class space as the paper):** Balanced LR **{bal_bal*100:.2f}%** balanced accuracy ({bal_bal*100 - paper_bal:+.2f} pt vs 47.07%).

Per-family recall for Balanced LR (top 25 by support) is below; full table: `reports/family_recall.csv`.

{fam_recall_md.to_markdown(index=False)}

---

## 5. Unknown family rejection (T-P2-04)

One-vs-rest LR scores; `tau={tau:.4f}` is the validation lower quantile so ~{KNOWN_KEEP_RATE:.0%} of in-distribution val samples keep a family label. Test in-distribution unknown rate: **{known_flagged*100:.2f}%**.

Leave-one-family-out: the held-out family is absent from training. We report (a) binary ransomware catch rate and (b) fraction flagged unknown under the same `tau`.

{df_lofo.to_markdown(index=False)}

- Average binary catch of held-out families: **{avg_det:.2f}%**
- Average unknown-flag rate on held-out families: **{avg_unk:.2f}%**
"""

    out_file = Path("reports/model_comparison.md")
    out_file.write_text(report_content, encoding="utf-8")
    print(f"\nReport written to {out_file.resolve()}")
    return df_models, calib_summary, df_family, df_lofo


if __name__ == "__main__":
    run_model_comparison()
