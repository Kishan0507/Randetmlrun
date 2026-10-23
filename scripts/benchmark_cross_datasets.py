"""Cross-Dataset ML Benchmark - Train & evaluate standard ML models on all project datasets.

Trains Logistic Regression, Random Forest, Extra Trees, LightGBM, XGBoost, MLP, Decision Tree,
and Linear SVM on each new dataset using 80/20 stratified split (seed=42), then saves results
to datasets/benchmark_results.json for dashboard consumption.

Datasets:
  1. Ransomware.csv (138K PE header features, binary: legitimate 0/1)
  2. data_file.csv (62K PE features, binary: Benign 0/1)
  3. ransom.csv (21K PE features, multiclass: Family)
  4. ransomset-multiclass-dataset.csv (19K API call features, multiclass: classe)
  5. MLRan (baseline - 483 RFE features, binary)

Task: P-005
Author: Kishan (Member 1)
"""

from __future__ import annotations

import json
import os
import sys
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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
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
SEED = 42
np.random.seed(SEED)

# ──────────────────────────────────────────────────────────────────────────────
# Dataset Loaders
# ──────────────────────────────────────────────────────────────────────────────

def load_ransomware_csv() -> dict:
    """Load Ransomware.csv (pipe-separated PE header features, binary classification)."""
    df = pd.read_csv(DATASETS_DIR / "Ransomware.csv", sep="|")
    # Drop non-numeric columns (Name, md5)
    drop_cols = ["Name", "md5"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns] + ["legitimate"])
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
    y = df["legitimate"].values  # 1=legitimate, 0=malware -> remap: 0=benign, 1=ransomware
    y_binary = 1 - y  # flip so 1=ransomware
    return {
        "name": "Ransomware.csv",
        "description": "PE Header Features (138K samples, 54 features)",
        "task": "Binary (Ransomware vs Legitimate)",
        "X": X.values,
        "y": y_binary,
        "feature_names": list(X.columns),
        "n_samples": len(y),
        "n_features": X.shape[1],
        "class_names": ["Legitimate", "Ransomware"],
    }


def load_data_file_csv() -> dict:
    """Load data_file.csv (PE features, binary classification)."""
    df = pd.read_csv(DATASETS_DIR / "data_file.csv")
    drop_cols = ["FileName", "md5Hash"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns] + ["Benign"])
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
    y = df["Benign"].values  # 1=benign, 0=malware -> remap: 0=benign, 1=ransomware
    y_binary = 1 - y
    return {
        "name": "data_file.csv",
        "description": "PE Features & Bitcoin Indicators (62K samples, 15 features)",
        "task": "Binary (Ransomware vs Benign)",
        "X": X.values,
        "y": y_binary,
        "feature_names": list(X.columns),
        "n_samples": len(y),
        "n_features": X.shape[1],
        "class_names": ["Benign", "Ransomware"],
    }


def load_ransom_csv() -> dict:
    """Load ransom.csv (PE header features, multi-class family classification)."""
    df = pd.read_csv(DATASETS_DIR / "ransom.csv")
    label_col = "Family"
    # Drop hash/id columns
    drop_cols = ["md5", "sha1", "file_extension"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns] + [label_col])
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(df[label_col])
    return {
        "name": "ransom.csv",
        "description": "PE Header Features (21K samples, 73 features, 27 families)",
        "task": "Multi-class (27 Malware Families)",
        "X": X.values,
        "y": y,
        "feature_names": list(X.columns),
        "n_samples": len(y),
        "n_features": X.shape[1],
        "class_names": list(le.classes_),
    }


def load_ransomset_multiclass() -> dict:
    """Load ransomset-multiclass-dataset.csv (API call counts, multi-class)."""
    df = pd.read_csv(DATASETS_DIR / "ransomset-multiclass-dataset.csv")
    label_col = "classe"
    X = df.drop(columns=[label_col])
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
    le = LabelEncoder()
    y = le.fit_transform(df[label_col])
    return {
        "name": "ransomset-multiclass-dataset.csv",
        "description": "API Call Features (19K samples, 239 features, 7 classes)",
        "task": "Multi-class (7 Ransomware Families + Normal)",
        "X": X.values,
        "y": y,
        "feature_names": list(X.columns),
        "n_samples": len(y),
        "n_features": X.shape[1],
        "class_names": list(le.classes_),
    }


def load_mlran_baseline() -> dict:
    """Load MLRan 483-feature RFE dataset (project baseline)."""
    X_train = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "mlran" / "MLRan_X_train_RFE.csv")
    X_test = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "mlran" / "MLRan_X_test_RFE.csv")
    labels = pd.read_csv(PROJECT_ROOT / "data" / "raw" / "mlran" / "MLRan_labels.csv")

    meta_cols = ["sample_id", "sample_type", "family_label", "type_label"]
    feat_cols_train = [c for c in X_train.columns if c not in meta_cols][:483]
    feat_cols_test = [c for c in X_test.columns if c not in meta_cols][:483]

    train_ids = X_train["sample_id"].values if "sample_id" in X_train.columns else np.arange(len(X_train))
    test_ids = X_test["sample_id"].values if "sample_id" in X_test.columns else np.arange(len(X_test))

    X_tr = X_train[feat_cols_train].apply(pd.to_numeric, errors="coerce").fillna(0).values
    X_te = X_test[feat_cols_test].apply(pd.to_numeric, errors="coerce").fillna(0).values

    # Merge labels
    y_tr = X_train["sample_type"].astype(int).values if "sample_type" in X_train.columns else labels.set_index("sample_id").loc[train_ids, "sample_type"].astype(int).values
    y_te = X_test["sample_type"].astype(int).values if "sample_type" in X_test.columns else labels.set_index("sample_id").loc[test_ids, "sample_type"].astype(int).values

    X_all = np.vstack([X_tr, X_te])
    y_all = np.concatenate([y_tr, y_te])

    return {
        "name": "MLRan (Project Baseline)",
        "description": "MLRan RFE 483 Behavioral Features (4,880 samples)",
        "task": "Binary (Ransomware vs Goodware)",
        "X": X_all,
        "y": y_all,
        "feature_names": feat_cols_train,
        "n_samples": len(y_all),
        "n_features": X_all.shape[1],
        "class_names": ["Goodware", "Ransomware"],
        # Keep pre-split for baseline comparison
        "X_train": X_tr,
        "X_test": X_te,
        "y_train": y_tr,
        "y_test": y_te,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Model Factory
# ──────────────────────────────────────────────────────────────────────────────

def get_models() -> dict:
    """Standard ML model suite with project-standard hyperparameters."""
    return {
        "Logistic Regression (L2)": LogisticRegression(
            solver="lbfgs", C=1.0, max_iter=1000, random_state=SEED,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100, max_depth=20, random_state=SEED, n_jobs=-1,
        ),
        "Extra Trees": ExtraTreesClassifier(
            n_estimators=100, max_depth=20, random_state=SEED, n_jobs=-1,
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=15, random_state=SEED,
        ),
        "Linear SVM": LinearSVC(
            max_iter=2000, random_state=SEED, dual="auto",
        ),
        "MLP (64-Hidden)": MLPClassifier(
            hidden_layer_sizes=(64,), max_iter=500, random_state=SEED,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.1, max_depth=5, random_state=SEED,
        ),
    }

    # Note: LightGBM and XGBoost added conditionally below


def get_optional_models() -> dict:
    """Try to add LightGBM and XGBoost if available."""
    extra = {}
    try:
        from lightgbm import LGBMClassifier
        extra["LightGBM"] = LGBMClassifier(
            n_estimators=100, learning_rate=0.1, num_leaves=31,
            random_state=SEED, verbose=-1, n_jobs=-1,
        )
    except ImportError:
        pass
    try:
        from xgboost import XGBClassifier
        extra["XGBoost"] = XGBClassifier(
            n_estimators=100, learning_rate=0.1, max_depth=5,
            random_state=SEED, use_label_encoder=False,
            eval_metric="logloss", verbosity=0, n_jobs=-1,
        )
    except ImportError:
        pass
    return extra


# ──────────────────────────────────────────────────────────────────────────────
# Benchmark Runner
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_model(model, X_test, y_test, is_binary: bool) -> dict:
    """Compute standard metrics on test set."""
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


def run_benchmark(dataset_info: dict, models: dict) -> dict:
    """Run all models on one dataset, return results dict."""
    X, y = dataset_info["X"], dataset_info["y"]
    is_binary = len(np.unique(y)) == 2

    # Use pre-split for MLRan if available
    if "X_train" in dataset_info:
        X_train, X_test = dataset_info["X_train"], dataset_info["X_test"]
        y_train, y_test = dataset_info["y_train"], dataset_info["y_test"]
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=SEED, stratify=y,
        )

    # Scale features for linear models
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model_results = {}
    for model_name, model in models.items():
        print(f"    -> {model_name}...", end=" ", flush=True)
        t0 = time.perf_counter()
        try:
            # Use scaled data for linear/neural models
            needs_scaling = any(kw in model_name.lower() for kw in ["logistic", "svm", "mlp", "linear"])
            X_tr = X_train_scaled if needs_scaling else X_train
            X_te = X_test_scaled if needs_scaling else X_test

            model.fit(X_tr, y_train)
            train_time = time.perf_counter() - t0

            metrics = evaluate_model(model, X_te, y_test, is_binary)
            metrics["train_time_sec"] = round(train_time, 3)
            metrics["status"] = "OK"
            model_results[model_name] = metrics
            print(f"BalAcc={metrics['balanced_accuracy']*100:.2f}% ({train_time:.1f}s)")
        except Exception as e:
            model_results[model_name] = {
                "status": "ERROR",
                "error": str(e),
                "balanced_accuracy": 0.0,
            }
            print(f"ERROR: {e}")

    return {
        "dataset": dataset_info["name"],
        "description": dataset_info["description"],
        "task": dataset_info["task"],
        "n_samples": dataset_info["n_samples"],
        "n_features": dataset_info["n_features"],
        "n_train": len(X_train),
        "n_test": len(X_test),
        "class_names": dataset_info["class_names"],
        "n_classes": len(np.unique(y)),
        "is_binary": is_binary,
        "models": model_results,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Cross-Dataset ML Benchmark - Early Ransomware Detection Project")
    print("=" * 70)
    print(f"Seed: {SEED}  |  Models: Standard Suite  |  Split: 80/20 Stratified")
    print()

    # Collect all models
    models = get_models()
    models.update(get_optional_models())
    print(f"Models available ({len(models)}): {', '.join(models.keys())}")
    print()

    # Load datasets
    loaders = [
        ("MLRan (Project Baseline)", load_mlran_baseline),
        ("Ransomware.csv", load_ransomware_csv),
        ("data_file.csv", load_data_file_csv),
        ("ransom.csv", load_ransom_csv),
        ("ransomset-multiclass-dataset.csv", load_ransomset_multiclass),
    ]

    all_results = []
    for ds_name, loader_fn in loaders:
        print(f"\n{'-'*70}")
        print(f"[DS] Dataset: {ds_name}")
        print(f"{'-'*70}")
        try:
            ds_info = loader_fn()
            print(f"   Loaded: {ds_info['n_samples']} samples x {ds_info['n_features']} features  |  Task: {ds_info['task']}")
            print(f"   Classes: {ds_info['class_names']}")
            result = run_benchmark(ds_info, models)
            all_results.append(result)
        except Exception as e:
            print(f"   [FAIL] Failed to load: {e}")
            import traceback
            traceback.print_exc()

    # Save results
    output_path = DATASETS_DIR / "benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n\n[OK] Results saved to {output_path}")

    # Print summary table
    print(f"\n{'='*100}")
    print("SUMMARY TABLE - Balanced Accuracy (%) by Dataset x Model")
    print(f"{'='*100}")
    model_names = list(models.keys())
    header = f"{'Dataset':<35}" + "".join(f"{m[:12]:>14}" for m in model_names)
    print(header)
    print("-" * len(header))
    for r in all_results:
        row = f"{r['dataset']:<35}"
        for m in model_names:
            if m in r["models"] and r["models"][m].get("status") == "OK":
                row += f"{r['models'][m]['balanced_accuracy']*100:>13.2f}%"
            else:
                row += f"{'ERR':>14}"
        print(row)
    print()


if __name__ == "__main__":
    main()

