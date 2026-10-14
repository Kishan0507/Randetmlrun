# Early-detection evaluation protocol (T-P4-01)

**Author:** Kishan (dkkishangowda@gmail.com)  
**Date:** 2026-10-14  
**Status:** ACCEPTED as D-004 (Track A). Scale claims from 20 MLRan Cuckoo reports are prototypes only. Primary time-series data is RanSMAP (D-002).

This document defines metrics, labelling, splits, and edge cases for Phase 4. Implementation lives in `src/` (T-P4-02 onward). Do not execute malware; windows are derived from released logs only.

---

## 1. Goal

Measure **how soon** a detector can raise a ransomware alert during an execution, not only whether the full-run feature vector is ransomware. Report speed and cost together: detection rate at time *t*, time-to-detection (TTD), files/bytes touched before alert, and false alarms per hour of goodware.

## 2. Unit of analysis

| Object | Definition |
|---|---|
| Execution | One RanSMAP folder `<app>-<timestamp>` (or one Cuckoo report). Identified by `(family_or_app, timestamp)`. |
| Window | Fixed-length slice of the execution time series. Default: length *W* = 2 s, stride *S* = 1 s (T-P4-02 may retune *W*, *S* on **train executions only**). |
| Prefix | All events with timestamp ≤ *t* from the start of the execution (used for MLRan JSON prototype T-P4-05). |

A row in the window table is one window of one execution. Labels never leak across windows of the same execution into both train and test.

## 3. Window labels (RanSMAP)

RanSMAP has no explicit “encryption start” marker. Use **entropy of ATA writes** as the operational proxy (D-002: entropy is the encryption-related field).

Let \( e_i \) be mean write-entropy in window *i* of a ransomware execution. Let \( \tau_e \) be a threshold fit on **training ransomware executions only** (e.g. 95th percentile of idle/benign-app write entropy, or a documented alternative in T-P4-02).

| Label | Rule |
|---|---|
| `benign` | Execution is a benign app (AESCrypt is treated as **benign crypto**, not ransomware). |
| `pre-encryption` | Ransomware execution, and no window up to and including *i* has \( e_i \ge \tau_e \). |
| `encryption` | Ransomware execution, and some window \( j \le i \) has \( e_j \ge \tau_e \). |

Positive class for the **early-warning** detector: `pre-encryption` ∪ `encryption` (any ransomware window). A secondary head may distinguish pre vs during encryption for analysis, not for the primary TTD number.

If entropy never crosses \( \tau_e \), the whole ransomware execution is still positive (all windows `pre-encryption`); TTD uses the streaming rule, not entropy.

## 4. Streaming decision rule (alerts)

A window classifier outputs \( p_t \in [0,1] \) = P(ransomware | window *t*).

An **alert** fires at the first *t* where a smoothing rule exceeds an operating threshold \( \theta \) chosen on validation executions under an FPR / FA-per-hour budget (same spirit as T-P2-02; default FPR budget 1% of goodware windows, or FA/hour ≤ a documented cap).

Candidate rules (compare in T-P4-04; pick on validation):

1. **Raw:** \( p_t \ge \theta \)
2. **EWMA:** \( s_t = \alpha p_t + (1-\alpha) s_{t-1} \), \( s_t \ge \theta \) (default \( \alpha = 0.3 \) from `configs/default.yaml`)
3. **k-of-n:** at least *k* of the last *n* windows have \( p \ge \theta \) (defaults *k*, *n* from config)

Alert time \( T_{\text{alert}} \) is the **right edge** of the first triggering window, in seconds from execution start. If no alert by \( T_{\max} \) (end of the recorded execution, typically 120 s for RanSMAP-style runs), the event is **censored**.

## 5. Metrics

All formulas use executions as the grouping unit unless noted. Thresholds, *W*, *S*, \( \alpha \), *k*, *n* are frozen before touching test executions.

### 5.1 Time-to-detection (TTD)

For ransomware execution *i*:

\[
\text{TTD}_i =
\begin{cases}
T_{\text{alert},i} & \text{if an alert occurs before } T_{\max,i} \\
\text{censored at } T_{\max,i} & \text{otherwise}
\end{cases}
\]

Report:

- Median TTD among **detected** executions
- Kaplan–Meier (or simple empirical) survival curve of undetected ransomware vs time
- Mean TTD **only** if every ransomware execution is detected; otherwise do not treat censored cases as \( T_{\max} \) in the mean without saying so

Never-detected ransomware = censored at max observed time of that execution.

### 5.2 Detection rate at *t* seconds

Let \( \mathcal{R} \) be ransomware test executions.

\[
\text{Detect@}t = \frac{1}{|\mathcal{R}|} \sum_{i \in \mathcal{R}} \mathbf{1}[\text{alert on } i \text{ with } T_{\text{alert},i} \le t]
\]

Required checkpoints (config): **t ∈ {2, 5, 10, 20, 30, 60, 120}** seconds. If an execution is shorter than *t*, it contributes to Detect@*t* only if it alerted before its own end; otherwise it counts as not detected at that *t*.

### 5.3 Files / bytes affected before alert

From RanSMAP ATA write rows with timestamp \( < T_{\text{alert}} \) (or \( < T_{\max} \) if censored):

- **Bytes before alert:** sum of write sizes
- **Distinct LBA (or page) count:** proxy for files when file names are absent
- If a field is missing, report “unavailable” rather than imputing

For the 20 MLRan Cuckoo JSONs (T-P4-05), use `behavior.summary` file write/rename counts on calls with `time` ≤ \( T_{\text{alert}} \) when present.

### 5.4 False alarms per hour of goodware

Let \( A_g \) be the number of alerts on goodware executions (count at most one alert per execution unless evaluating a “re-alert” policy, which must be stated). Let \( H_g \) be total goodware execution duration in hours.

\[
\text{FA/hour} = \frac{A_g}{H_g}
\]

Also report window-level FPR (goodware windows scored positive) and execution-level FPR (share of goodware executions with ≥1 alert). Primary operational number is **FA/hour**.

### 5.5 Window-level classification (T-P4-03)

On windows: balanced accuracy, macro-F1, precision, recall, FPR, FNR, PR-AUC, 95% bootstrap CI (same suite as `src/eval/metrics.py`). Group bootstrap by **execution** so windows from one run are not treated as independent for CIs.

## 6. Splits (no leakage)

1. Split by **execution id**, never by window.
2. Stratify / group by **family** (ransomware) and **app** (benign). Prefer a family-held-out fold in addition to a chronological or hardware split if timestamps exist.
3. All threshold and hyperparameter choices use training executions (and a validation group of executions). Test executions are touched once for the reported curve.
4. AESCrypt stays in the benign group (it encrypts files on purpose).

## 7. Prototype vs scale (honesty)

| Source | Role | Claim language |
|---|---|---|
| RanSMAP executions (selectively downloaded; not the 32 GB clone) | Primary Track A early-detection evidence | “On RanSMAP windows…” |
| 20 MLRan Cuckoo JSON reports | Prefix-extractor prototype (T-P4-05) | “Prototype on 20 reports; not a population estimate” |
| Track B full Cuckoo prefixes | DROPPED (D-009) | Do not claim |

## 8. Reporting template

Every Phase 4 experiment log entry must include: Detect@2/5/10/20/30/60/120, median TTD (detected), censoring count, FA/hour, bytes-before-alert summary, split description, seed 42, config path.

## 9. Edge cases

| Case | Handling |
|---|---|
| Empty execution / missing CSVs | Drop execution; log in experiment notes |
| Alert at t=0 (first window) | Allowed; TTD = window end time |
| Multiple alerts | TTD uses first alert; extra alerts ignored unless policy is “every crossing” |
| Goodware that encrypts (AESCrypt, Zip) | Benign; false alarm if alerted |
| Ransomware that never writes | Still positive; TTD from API/memory windows if used; else censored |
| Ties in EWMA | First time \( s_t \ge \theta \) |
