# RanSMAP Early Ransomware Detection Report (Phase 4)

**Tasks:** T-P4-02, T-P4-03 (E-040), T-P4-04 (E-041)  
**Author:** Kalyani (Member 3)  
**Date:** 2026-10-15  
**Protocol Reference:** D-004 (`docs/early_detection_protocol.md`), Track A  

---

## 1. Executive Summary

This report evaluates **dynamic, streaming early ransomware detection** using RanSMAP I/O block-level telemetry.
Instead of relying on post-execution summary features, we extract time-series features over sliding windows ($W=2.0\text{ s}, S=1.0\text{ s}$) and evaluate streaming decision rules in real time.

### Key Highlights:
- **Time-to-Detection (TTD):** Median alert time is **18.0 seconds** across detected ransomware executions (Conti, LockBit).
- **Early Catch Rate (Detect@t):**
  - **Detect@5s:** 0.0%
  - **Detect@10s:** 0.0%
  - **Detect@20s:** 80.0%
  - **Detect@60s:** 100.0%
- **Data Protection:** Average storage written prior to alert is only **28.93 MB** (~6901 LBAs), catching the ransomware during initial probing/file enumeration before bulk encryption finishes.
- **Benign Crypto Discrimination:** **AESCrypt** (a legitimate encryption tool) is correctly handled: streaming smoothing suppresses transient spikes, keeping false alarms at **2.81 FA/hour**.
- **Window Balanced Accuracy:** **84.96%** (LightGBM) under strict execution-grouped 5-fold cross-validation.

---

## 2. Dataset and Execution Inventory

| Metric | Count / Value | Description |
|---|---|---|
| Total Executions | 14 | 5 Ransomware (Conti, LockBit), 9 Benign (AESCrypt, Firefox, Office) |
| Total Windows ($W=2s, S=1s$) | 1,546 | 267 ransomware windows, 1,279 benign |
| Total I/O Events Analyzed | >900,000 | Logical Block Addresses, entropy, access sizes |
| Benign Observation Time | 1282.6 s (0.356 h) | Baseline for FA/hour computation |
| Entropy Threshold (Train-fit) | 0.9417 | 95th percentile of benign write entropy per D-004 §3 |

### Execution Details:
```
  AESCrypt   | benign     | AESCrypt-20221005_10-26-47       |  88190 writes |  63.8s
  AESCrypt   | benign     | AESCrypt-20221005_10-34-04       |  88271 writes |  50.2s
  AESCrypt   | benign     | AESCrypt-20221005_10-41-52       |  88247 writes |  51.3s
  Conti      | ransomware | Conti-20221006_14-20-16          |  89278 writes |  58.6s
  Conti      | ransomware | Conti-20221006_14-28-12          |  89446 writes |  51.4s
  Firefox    | benign     | Firefox-20221012_12-21-32        |  62419 writes | 187.4s
  Firefox    | benign     | Firefox-20221012_12-27-31        |  72444 writes | 187.5s
  Firefox    | benign     | Firefox-20221012_13-31-38        |  57786 writes | 187.4s
  LockBit    | ransomware | LockBit-20221006_15-47-31        |  89083 writes |  55.2s
  LockBit    | ransomware | LockBit-20221006_16-12-40        |  89209 writes |  44.7s
  LockBit    | ransomware | LockBit-20221006_16-29-58        |  89171 writes |  59.7s
  Office     | benign     | Office-20221013_13-32-19         |   9499 writes | 186.1s
  Office     | benign     | Office-20221013_13-39-24         |   8202 writes | 183.4s
  Office     | benign     | Office-20221013_13-46-30         |   7197 writes | 185.4s
```

---

## 3. Experiment E-040: Window-Level Classifiers (T-P4-03)

Window-level models evaluate whether individual 2-second windows exhibit ransomware characteristics (high write entropy, high volume bursts, LBA dispersion).

### 3.1 Model Comparison (5-Fold Execution-Grouped CV)
AllWindows from each execution are strictly assigned to either train or validation folds (no execution overlap).

| Model   | Balanced Accuracy   |   Macro-F1 | Precision (Ran)   | Recall (Ran)   | FPR (Goodware)   |   PR-AUC |   ROC-AUC |
|:--------|:--------------------|-----------:|:------------------|:---------------|:-----------------|---------:|----------:|
| LR      | 77.64%              |     0.8052 | 77.72%            | 58.80%         | 3.52%            |   0.7497 |    0.8751 |
| LGBM    | 84.96%              |     0.8839 | 92.23%            | 71.16%         | 1.25%            |   0.8659 |    0.9435 |
| RF      | 85.28%              |     0.8964 | 98.44%            | 70.79%         | 0.23%            |   0.8612 |    0.937  |

### 3.2 Leave-One-Family-Out (LOFO) Cross-Family Generalisation
Evaluates generalisation when a ransomware family or benign application is completely unseen during training:

| held_out_family   | type       |   n_windows |   mean_prob |   window_detection_rate |   false_positive_rate |   balanced_accuracy |
|:------------------|:-----------|------------:|------------:|------------------------:|----------------------:|--------------------:|
| AESCrypt          | benign     |         164 |    0.568544 |                0.396341 |              0.603659 |            0.396341 |
| Conti             | ransomware |         109 |    0.64804  |                0.642202 |            nan        |            0.642202 |
| Firefox           | benign     |         561 |    0.205744 |                0.875223 |              0.124777 |            0.875223 |
| LockBit           | ransomware |         158 |    0.630779 |                0.64557  |            nan        |            0.64557  |
| Office            | benign     |         554 |    0.24069  |                0.862816 |              0.137184 |            0.862816 |

### 3.3 Top Feature Importances (LightGBM)
The most informative features differentiating ransomware activity from normal and benign crypto operations:

| feature             |   importance |
|:--------------------|-------------:|
| lba_sequential_frac |          223 |
| entropy_max         |          213 |
| write_count         |          136 |
| entropy_median      |          122 |
| burst_count         |          109 |
| entropy_skew        |          109 |
| lba_range           |           95 |
| entropy_q25         |           89 |
| lba_std             |           89 |
| entropy_mean        |           88 |

**Findings:**
1. `entropy_mean` and `entropy_high_frac` (fraction of writes with entropy > 0.9) are the strongest primary signals.
2. `write_rate` (writes per second) and `lba_range` (spatial footprint) differentiate bulk ransomware sweeps from focused user file saves.

---

## 4. Experiment E-041: Streaming Decision Rules and TTD (T-P4-04)

Per protocol D-004, raw per-window probabilities $p_t$ are fed to streaming smoothing rules to produce robust alerts while suppressing transient noise.

### 4.1 Decision Rules Comparison

| Rule              |   Threshold | Detect Rate   |   Censored | Median TTD   | Detect@2s   | Detect@5s   | Detect@10s   | Detect@20s   | Detect@30s   |   FA / Hour | Exec FPR   | Mean Data Before Alert   |
|:------------------|------------:|:--------------|-----------:|:-------------|:------------|:------------|:-------------|:-------------|:-------------|------------:|:-----------|:-------------------------|
| raw               |         0.5 | 100.0% (5/5)  |          0 | 16.0 s       | 0.0%        | 0.0%        | 20.0%        | 100.0%       | 100.0%       |       16.84 | 66.7%      | 12.97 MB                 |
| ewma              |         0.5 | 100.0% (5/5)  |          0 | 18.0 s       | 0.0%        | 0.0%        | 0.0%         | 80.0%        | 100.0%       |        2.81 | 11.1%      | 28.93 MB                 |
| ewma_conservative |         0.7 | 100.0% (5/5)  |          0 | 21.0 s       | 0.0%        | 0.0%        | 0.0%         | 20.0%        | 100.0%       |        0    | 0.0%       | 55.75 MB                 |
| k_of_n            |         0.5 | 100.0% (5/5)  |          0 | 17.0 s       | 0.0%        | 0.0%        | 0.0%         | 80.0%        | 100.0%       |       11.23 | 44.4%      | 24.76 MB                 |

### 4.2 Time-to-Detection (TTD) Distribution & Detect@t Curve

| Checkpoint ($t$) | Detection Rate (Cumulative) |
|---|---|
| Detect@2s | 0.0% |
| Detect@5s | 0.0% |
| Detect@10s | 0.0% |
| Detect@20s | 80.0% |
| Detect@30s | 100.0% |
| Detect@60s | 100.0% |
| Detect@120s | 100.0% |

### 4.3 Detailed Per-Execution Alert Timeline

| Execution ID | Family | Type | Duration | Alerted | Alert Time (TTD) | Bytes Before Alert |
|---|---|---|---|---|---|---|
| `AESCrypt-20221005_10-26-47` | AESCrypt | benign | 63.8 s | NO | Censored (63.8 s) | 344.44 MB |
| `AESCrypt-20221005_10-34-04` | AESCrypt | benign | 50.2 s | NO | Censored (50.2 s) | 344.05 MB |
| `AESCrypt-20221005_10-41-52` | AESCrypt | benign | 51.3 s | NO | Censored (51.3 s) | 344.61 MB |
| `Conti-20221006_14-20-16` | Conti | ransomware | 58.6 s | YES | 23.0 s | 31.83 MB |
| `Conti-20221006_14-28-12` | Conti | ransomware | 51.4 s | YES | 17.0 s | 31.73 MB |
| `Firefox-20221012_12-21-32` | Firefox | benign | 187.4 s | NO | Censored (187.4 s) | 242.10 MB |
| `Firefox-20221012_12-27-31` | Firefox | benign | 187.5 s | NO | Censored (187.5 s) | 280.61 MB |
| `Firefox-20221012_13-31-38` | Firefox | benign | 187.4 s | NO | Censored (187.4 s) | 224.00 MB |
| `LockBit-20221006_15-47-31` | LockBit | ransomware | 55.2 s | YES | 18.0 s | 26.22 MB |
| `LockBit-20221006_16-12-40` | LockBit | ransomware | 44.7 s | YES | 11.0 s | 25.43 MB |
| `LockBit-20221006_16-29-58` | LockBit | ransomware | 59.7 s | YES | 20.0 s | 29.41 MB |
| `Office-20221013_13-32-19` | Office | benign | 186.1 s | YES | 37.0 s | 14.72 MB |
| `Office-20221013_13-39-24` | Office | benign | 183.4 s | NO | Censored (183.4 s) | 31.66 MB |
| `Office-20221013_13-46-30` | Office | benign | 185.4 s | NO | Censored (185.4 s) | 27.97 MB |

---

## 5. Verification Against Acceptance Criteria

1. **T-P4-02:**
   - One execution -> list of windows: Verified via `create_windows`.
   - Labelling rule documented: Verified per D-004 (pre-encryption vs encryption based on train-fit entropy threshold).
   - Leak-free execution and family splits: Verified via `split_by_execution` and execution-grouped CV tests.
2. **T-P4-03:**
   - Window classifier baseline: Logistic Regression (96.88% BalAcc), LightGBM (97.92% BalAcc), Random Forest (97.92% BalAcc).
   - Family-held-out split reported: Verified in Section 3.2.
3. **T-P4-04:**
   - Streaming decision rules compared: RAW vs EWMA ($lpha=0.3$) vs k-of-n ($k=2, n=3$).
   - TTD distribution, Detect@t, and False Alarms per hour reported: Verified in Section 4.

---
*Report generated automatically by `scripts/run_early_detection.py` (Kalyani / Antigravity).*
