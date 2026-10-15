"""Streaming decision rules and early detection evaluation (T-P4-04).

Evaluates time-to-detection (TTD), Detect@t curves, false alarm rates (FA/hour),
and data written before alert per D-004 (docs/early_detection_protocol.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.data.ransmap import Execution


@dataclass
class ExecutionAlert:
    """Alert summary for a single execution."""

    execution_id: str
    family: str
    is_ransomware: bool
    duration_sec: float
    alerted: bool
    alert_time_sec: Optional[float]
    ttd: float  # alert_time if alerted, else duration_sec (censored)
    is_censored: bool
    bytes_before_alert: Optional[int] = None
    lbas_before_alert: Optional[int] = None


@dataclass
class StreamingEvaluationResult:
    """Comprehensive early-detection evaluation across a collection of executions."""

    rule_name: str
    threshold: float
    # TTD metrics
    n_ransomware: int
    n_detected: int
    detection_rate: float
    censored_count: int
    median_ttd_detected: Optional[float]
    mean_ttd_detected: Optional[float]
    min_ttd: Optional[float]
    max_ttd: Optional[float]
    # Detect@t curve
    detect_at_t: Dict[int, float]  # t_sec -> detection fraction
    # Goodware metrics
    n_benign: int
    benign_alerts: int
    benign_duration_hours: float
    fa_per_hour: float  # False alarms per hour of goodware
    execution_fpr: float
    # Damage metrics
    mean_bytes_before_alert: Optional[float]
    mean_lbas_before_alert: Optional[float]
    # Individual execution alerts
    alerts: List[ExecutionAlert]

    def summary_table(self) -> pd.DataFrame:
        """Formatted DataFrame of early detection metrics."""
        rows = [
            ("Rule", self.rule_name),
            ("Threshold", f"{self.threshold:.3f}"),
            ("Ransomware Executions", f"{self.n_ransomware}"),
            ("Detected Executions", f"{self.n_detected} ({self.detection_rate*100:.1f}%)"),
            ("Censored (Undetected)", f"{self.censored_count}"),
            ("Median TTD (Detected)", f"{self.median_ttd_detected:.2f} s" if self.median_ttd_detected is not None else "N/A"),
            ("Min TTD", f"{self.min_ttd:.2f} s" if self.min_ttd is not None else "N/A"),
            ("Max TTD (Detected)", f"{self.max_ttd:.2f} s" if self.max_ttd is not None else "N/A"),
            ("Benign Executions", f"{self.n_benign}"),
            ("Benign Duration", f"{self.benign_duration_hours*3600:.1f} s ({self.benign_duration_hours:.3f} h)"),
            ("False Alarms (Benign)", f"{self.benign_alerts}"),
            ("FA / Hour", f"{self.fa_per_hour:.2f}"),
            ("Execution FPR", f"{self.execution_fpr*100:.2f}%"),
        ]
        for t in sorted(self.detect_at_t.keys()):
            rows.append((f"Detect@{t}s", f"{self.detect_at_t[t]*100:.1f}%"))

        if self.mean_bytes_before_alert is not None:
            mb = self.mean_bytes_before_alert / (1024 * 1024)
            rows.append(("Mean Bytes Before Alert", f"{mb:.2f} MB"))
        if self.mean_lbas_before_alert is not None:
            rows.append(("Mean LBAs Before Alert", f"{self.mean_lbas_before_alert:.0f}"))

        return pd.DataFrame(rows, columns=["Metric", "Value"])


def apply_streaming_rule(
    window_probs: np.ndarray,
    rule: str = "ewma",
    threshold: float = 0.5,
    alpha: float = 0.3,
    k: int = 2,
    n: int = 3,
) -> np.ndarray:
    """Apply a streaming decision rule to a sequence of window probabilities.

    Args:
        window_probs: 1D array of probabilities p_t in [0, 1] ordered by time
        rule: 'raw', 'ewma', or 'k_of_n'
        threshold: Decision threshold theta
        alpha: Smoothing parameter for EWMA (default: 0.3)
        k: Minimum windows meeting threshold in k-of-n rule
        n: Window history length in k-of-n rule

    Returns:
        Boolean 1D array of alerts per window (True if alert triggered at window t)
    """
    n_windows = len(window_probs)
    if n_windows == 0:
        return np.array([], dtype=bool)

    if rule == "raw":
        return window_probs >= threshold

    elif rule == "ewma":
        scores = np.zeros(n_windows, dtype=np.float64)
        s = 0.0
        for i in range(n_windows):
            s = alpha * window_probs[i] + (1.0 - alpha) * s
            scores[i] = s
        return scores >= threshold

    elif rule == "k_of_n":
        raw_hits = (window_probs >= threshold).astype(int)
        alerts = np.zeros(n_windows, dtype=bool)
        for i in range(n_windows):
            start_idx = max(0, i - n + 1)
            count = np.sum(raw_hits[start_idx : i + 1])
            if count >= k:
                alerts[i] = True
        return alerts

    else:
        raise ValueError(f"Unknown streaming rule: '{rule}'. Must be 'raw', 'ewma', or 'k_of_n'.")


def evaluate_execution_stream(
    execution: Execution,
    window_probs: np.ndarray,
    window_times: np.ndarray,
    rule: str = "ewma",
    threshold: float = 0.5,
    alpha: float = 0.3,
    k: int = 2,
    n: int = 3,
) -> ExecutionAlert:
    """Evaluate streaming alert on a single execution.

    Args:
        execution: Execution object
        window_probs: 1D array of window probabilities
        window_times: (n_windows, 2) array of [start_sec, end_sec] relative times
        rule: Smoothing rule name
        threshold: Operating threshold
        alpha, k, n: Rule parameters

    Returns:
        ExecutionAlert object with TTD and damage accounting
    """
    df = execution.ata_write
    duration = float(df["rel_time"].max()) if df is not None and len(df) > 0 else 0.0

    if len(window_probs) == 0:
        return ExecutionAlert(
            execution_id=execution.execution_id,
            family=execution.family,
            is_ransomware=execution.is_ransomware,
            duration_sec=duration,
            alerted=False,
            alert_time_sec=None,
            ttd=duration,
            is_censored=execution.is_ransomware,
            bytes_before_alert=0,
            lbas_before_alert=0,
        )

    alerts = apply_streaming_rule(
        window_probs, rule=rule, threshold=threshold, alpha=alpha, k=k, n=n
    )

    alert_idx = np.where(alerts)[0]
    if len(alert_idx) > 0:
        first_alert = alert_idx[0]
        # Alert time is the right edge of the triggering window (D-004 §4)
        alert_time = float(window_times[first_alert, 1])
        alerted = True
        ttd = alert_time
        is_censored = False
    else:
        alert_time = None
        alerted = False
        ttd = duration
        is_censored = execution.is_ransomware

    # Compute damage before alert
    bytes_before = None
    lbas_before = None
    if df is not None and len(df) > 0:
        cutoff = alert_time if alerted else duration
        prior_writes = df[df["rel_time"] <= cutoff]
        bytes_before = int(prior_writes["size"].sum())
        lbas_before = int(prior_writes["lba"].nunique())

    return ExecutionAlert(
        execution_id=execution.execution_id,
        family=execution.family,
        is_ransomware=execution.is_ransomware,
        duration_sec=duration,
        alerted=alerted,
        alert_time_sec=alert_time,
        ttd=ttd,
        is_censored=is_censored,
        bytes_before_alert=bytes_before,
        lbas_before_alert=lbas_before,
    )


def evaluate_streaming_system(
    executions: List[Execution],
    execution_probs: Dict[str, Tuple[np.ndarray, np.ndarray]],
    rule: str = "ewma",
    threshold: float = 0.5,
    checkpoints: Tuple[int, ...] = (2, 5, 10, 20, 30, 60, 120),
    alpha: float = 0.3,
    k: int = 2,
    n: int = 3,
) -> StreamingEvaluationResult:
    """Evaluate streaming detector across all executions.

    Args:
        executions: List of Execution objects
        execution_probs: Mapping execution_id -> (window_probs, window_times)
        rule: Decision rule ('raw', 'ewma', 'k_of_n')
        threshold: Decision threshold
        checkpoints: Timestamps for Detect@t evaluation
        alpha, k, n: Rule parameters

    Returns:
        StreamingEvaluationResult with complete metrics per D-004
    """
    alerts = []
    for ex in executions:
        if ex.execution_id not in execution_probs:
            continue
        probs, times = execution_probs[ex.execution_id]
        alert = evaluate_execution_stream(
            ex, probs, times, rule=rule, threshold=threshold, alpha=alpha, k=k, n=n
        )
        alerts.append(alert)

    ransomware_alerts = [a for a in alerts if a.is_ransomware]
    benign_alerts = [a for a in alerts if not a.is_ransomware]

    n_ran = len(ransomware_alerts)
    detected_ran = [a for a in ransomware_alerts if a.alerted]
    n_detected = len(detected_ran)
    det_rate = (n_detected / n_ran) if n_ran > 0 else 0.0
    censored = n_ran - n_detected

    if detected_ran:
        detected_ttds = [a.alert_time_sec for a in detected_ran if a.alert_time_sec is not None]
        median_ttd = float(np.median(detected_ttds))
        mean_ttd = float(np.mean(detected_ttds))
        min_ttd = float(np.min(detected_ttds))
        max_ttd = float(np.max(detected_ttds))
        bytes_list = [a.bytes_before_alert for a in detected_ran if a.bytes_before_alert is not None]
        mean_bytes = float(np.mean(bytes_list)) if bytes_list else None
        lbas_list = [a.lbas_before_alert for a in detected_ran if a.lbas_before_alert is not None]
        mean_lbas = float(np.mean(lbas_list)) if lbas_list else None
    else:
        median_ttd = None
        mean_ttd = None
        min_ttd = None
        max_ttd = None
        mean_bytes = None
        mean_lbas = None

    # Detect@t
    detect_at_t = {}
    for t in checkpoints:
        if n_ran > 0:
            count = sum(1 for a in ransomware_alerts if a.alerted and a.alert_time_sec is not None and a.alert_time_sec <= t)
            detect_at_t[t] = count / n_ran
        else:
            detect_at_t[t] = 0.0

    # Goodware false alarm accounting
    n_benign = len(benign_alerts)
    benign_fired = sum(1 for a in benign_alerts if a.alerted)
    total_benign_seconds = sum(a.duration_sec for a in benign_alerts)
    total_benign_hours = total_benign_seconds / 3600.0 if total_benign_seconds > 0 else 0.0

    fa_per_hour = (benign_fired / total_benign_hours) if total_benign_hours > 0 else 0.0
    exec_fpr = (benign_fired / n_benign) if n_benign > 0 else 0.0

    return StreamingEvaluationResult(
        rule_name=rule,
        threshold=threshold,
        n_ransomware=n_ran,
        n_detected=n_detected,
        detection_rate=det_rate,
        censored_count=censored,
        median_ttd_detected=median_ttd,
        mean_ttd_detected=mean_ttd,
        min_ttd=min_ttd,
        max_ttd=max_ttd,
        detect_at_t=detect_at_t,
        n_benign=n_benign,
        benign_alerts=benign_fired,
        benign_duration_hours=total_benign_hours,
        fa_per_hour=fa_per_hour,
        execution_fpr=exec_fpr,
        mean_bytes_before_alert=mean_bytes,
        mean_lbas_before_alert=mean_lbas,
        alerts=alerts,
    )
