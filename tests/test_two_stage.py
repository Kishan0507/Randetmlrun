"""Unit tests for TwoStageDetector and ablation study (T-P4-07)."""

import numpy as np
import pytest

from src.models.two_stage import (
    TwoStageDetector,
    run_two_stage_ablation,
)


def test_two_stage_detector_ransomware_confirmed():
    detector = TwoStageDetector(early_threshold=0.5, early_alpha=0.3, confirm_threshold=0.5)

    window_probs = np.array([0.1, 0.2, 0.8, 0.9, 0.95])
    window_times = np.array([[0, 2], [1, 3], [2, 4], [3, 5], [4, 6]])
    confirm_prob = 0.95

    verdict = detector.evaluate_execution(
        execution_id="Ran-01",
        window_probs=window_probs,
        window_times=window_times,
        confirm_prob=confirm_prob,
        is_ransomware=True,
    )

    assert verdict.early_alert is True
    assert verdict.confirmation_alert is True
    assert verdict.final_verdict == "ransomware"
    assert verdict.files_protected is True
    assert verdict.effective_ttd <= 6.0


def test_two_stage_detector_benign_crypto_dismissed():
    detector = TwoStageDetector(early_threshold=0.5, early_alpha=0.3, confirm_threshold=0.5)

    # Benign crypto has high write entropy -> early alert fires
    window_probs = np.array([0.7, 0.8, 0.9, 0.9])
    window_times = np.array([[0, 2], [1, 3], [2, 4], [3, 5]])
    # But Stage 2 full analysis sees benign software informers / no ransom note / clean PE -> 0.05
    confirm_prob = 0.05

    verdict = detector.evaluate_execution(
        execution_id="AESCrypt-01",
        window_probs=window_probs,
        window_times=window_times,
        confirm_prob=confirm_prob,
        is_ransomware=False,
    )

    assert verdict.early_alert is True
    assert verdict.confirmation_alert is False
    assert verdict.final_verdict == "benign_crypto_dismissed"
    assert verdict.files_protected is False


def test_run_two_stage_ablation():
    times = np.array([[i, i + 2.0] for i in range(5)])

    ran_data = [
        (np.array([0.2, 0.4, 0.9, 0.95, 0.99]), times, 0.98),
        (np.array([0.1, 0.3, 0.85, 0.9, 0.95]), times, 0.92),
    ]
    crypto_data = [
        (np.array([0.6, 0.7, 0.8, 0.85, 0.8]), times, 0.08),  # AESCrypt
    ]
    std_data = [
        (np.array([0.05, 0.02, 0.01, 0.05, 0.02]), times, 0.01),  # Firefox
    ]

    df_ablation = run_two_stage_ablation(ran_data, crypto_data, std_data)
    assert len(df_ablation) == 3
    assert set(df_ablation["Architecture"]) == {
        "Stage 1 Only (Early Streaming)",
        "Stage 2 Only (Full Post-Execution)",
        "Two-Stage Combined (Early + Confirm)",
    }
