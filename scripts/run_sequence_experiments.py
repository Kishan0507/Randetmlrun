"""Experiment runner for T-P5-04 (E-051): Sequential vs Static Window Models on RanSMAP.

Compares standard static window models against sequential trajectory models
equipped with lag, acceleration, streak, and Markov transition features.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.data.ransmap import (
    build_windowed_dataset,
    discover_executions,
    fit_entropy_threshold,
)
from src.features.sequential_ransmap import build_sequential_dataset
from src.models.window_classifier import (
    evaluate_family_held_out,
    evaluate_window_cv,
    extract_feature_importances,
    make_window_pipeline,
)


def run_sequence_experiment(seed: int = 42) -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("Running E-051: Sequential vs Static Window Models on RanSMAP (T-P5-04)")
    print("=" * 70)

    data_dir = Path("data/raw/ransmap")
    execs = discover_executions(data_dir)
    print(f"Loaded {len(execs)} RanSMAP executions.")

    threshold = fit_entropy_threshold(execs, percentile=90.0)
    static_dataset = build_windowed_dataset(
        execs,
        window_sec=2.0,
        stride_sec=1.0,
        entropy_threshold=threshold,
    )
    print(f"Static Dataset: {static_dataset.X.shape[0]} windows, {static_dataset.X.shape[1]} features.")

    seq_dataset = build_sequential_dataset(static_dataset)
    print(f"Sequential Dataset: {seq_dataset.X.shape[0]} windows, {seq_dataset.X.shape[1]} features.")

    models = ["lr", "lgbm", "rf"]
    results = []

    for model_name in models:
        # Static
        m_static, _ = evaluate_window_cv(static_dataset, model_type=model_name, n_splits=5, seed=seed)
        # Sequential
        m_seq, _ = evaluate_window_cv(seq_dataset, model_type=model_name, n_splits=5, seed=seed)

        results.append({
            "Model": model_name.upper(),
            "Static BalAcc": f"{m_static.balanced_accuracy * 100:.2f}%",
            "Seq BalAcc": f"{m_seq.balanced_accuracy * 100:.2f}%",
            "BalAcc Diff": f"{(m_seq.balanced_accuracy - m_static.balanced_accuracy) * 100:+.2f}%",
            "Static Macro-F1": f"{m_static.macro_f1:.4f}",
            "Seq Macro-F1": f"{m_seq.macro_f1:.4f}",
            "Static FPR": f"{m_static.fpr * 100:.2f}%",
            "Seq FPR": f"{m_seq.fpr * 100:.2f}%",
            "Static Recall": f"{m_static.recall * 100:.2f}%",
            "Seq Recall": f"{m_seq.recall * 100:.2f}%",
        })

    df_comp = pd.DataFrame(results)
    print("\n--- 5-Fold Execution-Grouped CV Comparison (Static vs Sequential) ---")
    print(df_comp.to_string(index=False))

    # Feature importance on Sequential LightGBM
    pipe_seq = make_window_pipeline("lgbm", seed=seed)
    pipe_seq.fit(seq_dataset.X, seq_dataset.y_binary)
    imp_df = extract_feature_importances(pipe_seq, seq_dataset.feature_names)
    print("\n--- Top 10 Features in Sequential Model (LightGBM) ---")
    print(imp_df.head(10).to_string(index=False))

    # Cross-family generalisation check
    print("\n--- Sequential Leave-One-Family-Out Generalisation (LightGBM) ---")
    lofo_df = evaluate_family_held_out(seq_dataset, model_type="lgbm", seed=seed)
    print(lofo_df.to_string(index=False))

    return df_comp


if __name__ == "__main__":
    run_sequence_experiment()
