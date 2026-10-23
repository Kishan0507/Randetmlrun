# 08 — Handoff (OVERWRITE every session)

Last updated: 2026-10-23 by Kishan (Member 1, Project Lead) / Antigravity

## Done
- **Cross-Dataset ML Benchmark (Patch P-005)**:
  - Ingested and profiled all datasets in `datasets/`:
    1. `Ransomware.csv`: 138,047 samples x 54 PE header features (Binary: Legitimate vs Ransomware)
    2. `data_file.csv`: 62,485 samples x 15 PE & Bitcoin features (Binary: Benign vs Ransomware)
    3. `ransom.csv`: 21,752 samples x 73 PE features (Multi-class: 27 malware families)
    4. `ransomset-multiclass-dataset.csv`: 19,234 samples x 239 API call features (Multi-class: 7 families)
    5. `MLRan Baseline`: 4,880 samples x 483 behavioral RFE features (Binary: Goodware vs Ransomware)
  - Evaluated **>246,400 samples** across 7 standard ML models: Logistic Regression (L2, lbfgs), Random Forest, Extra Trees, Decision Tree, Linear SVM, MLP (64-Hidden), and Gradient Boosting using standard parameters and 80/20 stratified splits (seed=42).
  - Saved 100% complete benchmark metrics (Balanced Accuracy, Precision, Recall, Macro F1, FPR, FNR, Latency per sample, Train Time, Confusion Matrices) to `datasets/benchmark_results.json`.
  - Added dedicated navigation section in `dashboard/app.py`: `"🌐 Cross-Dataset Benchmark & Model Comparison"` with 4 interactive sub-tabs:
    1. Multi-Model Comparison & Heatmap matrix across metrics (BalAcc, F1, Recall, Precision, Latency, Train Time) and grouped Plotly bar charts.
    2. Dataset Deep-Dive with multi-dimensional radar chart, Pareto latency vs accuracy curve, full metrics table, and confusion matrix explorer.
    3. Feature Paradigms & Architectural Insights contrasting static PE headers, dynamic API counts, Bitcoin indicators, and behavioral RFE vectors.
    4. Benchmark Artifacts & Data Export with download buttons for JSON and CSV.
- **Previous Patches (P-001 through P-004)**:
  - Fixed Windows LightGBM C-library access violation via Random Forest window pipeline.
  - Added frontend dataset ingestion and batch evaluator in Tab 6 and Tab 1.
  - Added Model Variations & Parameter Analytics (Tab 5) and standalone `dashboard/analytics.html`.
  - Completed APIMDS external dataset transferability study (E-080).

## In progress
- Nothing. All tasks and patches (P-001 through P-005) are complete and verified.

## Next step (do this first)
- Open Streamlit dashboard: `http://localhost:8501`
- Select `"🌐 Cross-Dataset Benchmark & Model Comparison"` from the sidebar navigation to view:
  - Cross-dataset heatmaps comparing all 7 models across the 5 datasets.
  - Interactive metric selector (Balanced Accuracy, F1, Recall, Precision, Latency, Train Time).
  - Dataset deep-dive with radar charts, Pareto frontiers, and confusion matrices.
  - Downloadable benchmark artifacts (`benchmark_results.json` and `benchmark_leaderboard.csv`).

## Open questions for the user / team
- None. All requested datasets have been analyzed with standard parameters, compared across models, and displayed in the dashboard.

## Gotchas
- When performing multi-class classification on datasets with 7 to 27 classes (`ransom.csv`, `ransomset-multiclass`), `LogisticRegression` uses `solver="lbfgs"` to support multinomial cross-entropy loss without throwing `liblinear` errors.
- In `MLRan Baseline`, binary ground truth uses `sample_type` (0=Goodware, 1=Ransomware), achieving the project's champion 98.17% MLP / 97.77% LR balanced accuracy.
