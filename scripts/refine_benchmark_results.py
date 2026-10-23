"""Refine and complete cross-dataset benchmark results.

1. Reruns MLRan with binary sample_type (Goodware=0, Ransomware=1) across all standard models.
2. Runs Logistic Regression (L2, lbfgs) on ransom.csv and ransomset-multiclass-dataset.csv.
3. Updates datasets/benchmark_results.json with 100% complete metrics (no ERR).
"""

from __future__ import annotations

import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
)
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import LinearSVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    accuracy_score,
)

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
BENCHMARK_JSON = DATASETS_DIR / "benchmark_results.json"
SEED = 42
np.random.seed(SEED)


def evaluate_model(model, X_test, y_test, is_binary: bool) -> dict:
    t0 = time.perf_counter()
    y_pred = model.predict(X_test)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    avg = "binary" if is_binary else "macro"

    results = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average=avg, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average=avg, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, average=avg, zero_division=0)),
        "latency_ms": round(latency_ms, 3),
        "latency_per_sample_ms": round(latency_ms / len(X_test), 4),
    }

    if is_binary:
        cm = confusion_matrix(y_test, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            results["confusion_matrix"] = {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)}
            results["fpr"] = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
            results["fnr"] = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    else:
        results["fpr"] = None
        results["fnr"] = None

    return results


def rerun_mlran_binary():
    print("[1/3] Rerunning MLRan with clean binary ground truth (sample_type 0/1)...")
    X_train = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "mlran" / "MLRan_X_train_RFE.csv")
    X_test = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "mlran" / "MLRan_X_test_RFE.csv")

    meta_cols = ["sample_id", "sample_type", "family_label", "type_label"]
    feat_cols = [c for c in X_train.columns if c not in meta_cols][:483]

    X_tr = X_train[feat_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values
    X_te = X_test[feat_cols].apply(pd.to_numeric, errors="coerce").fillna(0).values
    y_tr = X_train["sample_type"].astype(int).values
    y_te = X_test["sample_type"].astype(int).values

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    models = {
        "Logistic Regression (L2)": (LogisticRegression(solver="lbfgs", C=1.0, max_iter=1000, random_state=SEED), True),
        "Random Forest": (RandomForestClassifier(n_estimators=100, max_depth=20, random_state=SEED, n_jobs=-1), False),
        "Extra Trees": (ExtraTreesClassifier(n_estimators=100, max_depth=20, random_state=SEED, n_jobs=-1), False),
        "Decision Tree": (DecisionTreeClassifier(max_depth=15, random_state=SEED), False),
        "Linear SVM": (LinearSVC(max_iter=2000, random_state=SEED, dual="auto"), True),
        "MLP (64-Hidden)": (MLPClassifier(hidden_layer_sizes=(64,), max_iter=500, random_state=SEED), True),
        "Gradient Boosting": (GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=SEED), False),
    }

    mlran_results = {}
    for name, (clf, scale) in models.items():
        t0 = time.perf_counter()
        X_train_use = X_tr_s if scale else X_tr
        X_test_use = X_te_s if scale else X_te
        clf.fit(X_train_use, y_tr)
        t_fit = time.perf_counter() - t0
        metrics = evaluate_model(clf, X_test_use, y_te, is_binary=True)
        metrics["train_time_sec"] = round(t_fit, 3)
        metrics["status"] = "OK"
        mlran_results[name] = metrics
        print(f"   MLRan -> {name}: BalAcc={metrics['balanced_accuracy']*100:.2f}% (train {t_fit:.2f}s)")

    return {
        "dataset": "MLRan (Project Baseline)",
        "description": "MLRan RFE 483 Behavioral Features (4,880 samples)",
        "task": "Binary (Ransomware vs Goodware)",
        "n_samples": len(y_tr) + len(y_te),
        "n_features": X_tr.shape[1],
        "n_train": len(X_tr),
        "n_test": len(X_te),
        "class_names": ["Goodware", "Ransomware"],
        "n_classes": 2,
        "is_binary": True,
        "models": mlran_results,
    }


def run_lr_for_ransom_csv():
    print("[2/3] Running Logistic Regression (L2, lbfgs) on ransom.csv (27 classes)...")
    from sklearn.model_selection import train_test_split
    df = pd.read_csv(DATASETS_DIR / "ransom.csv")
    label_col = "Family"
    drop_cols = ["md5", "sha1", "file_extension"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns] + [label_col])
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0).values
    le = LabelEncoder()
    y = le.fit_transform(df[label_col])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=SEED, stratify=y,
    )
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_te_s = scaler.transform(X_test)

    clf = LogisticRegression(solver="lbfgs", C=1.0, max_iter=1000, random_state=SEED)
    t0 = time.perf_counter()
    clf.fit(X_tr_s, y_train)
    t_fit = time.perf_counter() - t0
    metrics = evaluate_model(clf, X_te_s, y_test, is_binary=False)
    metrics["train_time_sec"] = round(t_fit, 3)
    metrics["status"] = "OK"
    print(f"   ransom.csv -> LR (L2): BalAcc={metrics['balanced_accuracy']*100:.2f}% (train {t_fit:.2f}s)")
    return metrics


def run_lr_for_ransomset():
    print("[3/3] Running Logistic Regression (L2, lbfgs) on ransomset-multiclass (7 classes)...")
    from sklearn.model_selection import train_test_split
    df = pd.read_csv(DATASETS_DIR / "ransomset-multiclass-dataset.csv")
    label_col = "classe"
    X = df.drop(columns=[label_col])
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0).values
    le = LabelEncoder()
    y = le.fit_transform(df[label_col])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=SEED, stratify=y,
    )
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_te_s = scaler.transform(X_test)

    clf = LogisticRegression(solver="lbfgs", C=1.0, max_iter=1000, random_state=SEED)
    t0 = time.perf_counter()
    clf.fit(X_tr_s, y_train)
    t_fit = time.perf_counter() - t0
    metrics = evaluate_model(clf, X_te_s, y_test, is_binary=False)
    metrics["train_time_sec"] = round(t_fit, 3)
    metrics["status"] = "OK"
    print(f"   ransomset -> LR (L2): BalAcc={metrics['balanced_accuracy']*100:.2f}% (train {t_fit:.2f}s)")
    return metrics


def main():
    if not BENCHMARK_JSON.exists():
        print("Error: benchmark_results.json not found!")
        return

    with open(BENCHMARK_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Update MLRan
    mlran_new = rerun_mlran_binary()
    for i, item in enumerate(data):
        if item["dataset"] == "MLRan (Project Baseline)":
            data[i] = mlran_new
            break

    # 2. Update ransom.csv LR
    lr_ransom = run_lr_for_ransom_csv()
    for item in data:
        if item["dataset"] == "ransom.csv":
            item["models"]["Logistic Regression (L2)"] = lr_ransom
            break

    # 3. Update ransomset LR
    lr_ransomset = run_lr_for_ransomset()
    for item in data:
        if item["dataset"] == "ransomset-multiclass-dataset.csv":
            item["models"]["Logistic Regression (L2)"] = lr_ransomset
            break

    # Save
    with open(BENCHMARK_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print("\n[SUCCESS] benchmark_results.json successfully updated with 100% complete metrics!")

    # Print summary
    print("\n" + "=" * 105)
    print("FINAL COMPLETE BENCHMARK TABLE - Balanced Accuracy (%) by Dataset x Model")
    print("=" * 105)
    models = list(data[0]["models"].keys())
    header = f"{'Dataset':<33}" + "".join(f"{m[:12]:>13}" for m in models)
    print(header)
    print("-" * len(header))
    for r in data:
        row = f"{r['dataset']:<33}"
        for m in models:
            if m in r["models"] and r["models"][m].get("status") == "OK":
                row += f"{r['models'][m]['balanced_accuracy']*100:>12.2f}%"
            else:
                row += f"{'ERR':>13}"
        print(row)
    print("=" * 105)


if __name__ == "__main__":
    main()
