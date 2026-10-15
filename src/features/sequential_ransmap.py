"""Sequential and trajectory feature augmentation for RanSMAP time series (T-P5-04).

Transforms static window feature vectors into sequential trajectory vectors by incorporating:
1. Temporal lag differences (delta entropy, delta write rate, acceleration).
2. Cumulative execution trajectory (cumulative bytes, cumulative high-entropy windows).
3. State transitions (low/mid to high entropy phase transition, high entropy streak length).
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import numpy as np

from src.data.ransmap import WINDOW_FEATURE_NAMES, WindowedDataset


SEQUENTIAL_EXTRA_FEATURE_NAMES = [
    "delta_entropy_mean_lag1",
    "delta_entropy_mean_lag2",
    "accel_entropy_mean",
    "delta_write_rate_lag1",
    "delta_write_bytes_lag1",
    "cum_bytes_written",
    "cum_high_entropy_windows",
    "high_entropy_streak",
    "transition_to_high_entropy",
    "entropy_expanding_mean",
]


def build_sequential_dataset(dataset: WindowedDataset) -> WindowedDataset:
    """Augment a WindowedDataset with sequential, lag, and trajectory features.

    Maintains execution boundaries strictly: lags and cumulative statistics
    reset at the boundary of each execution.

    Args:
        dataset: Input WindowedDataset with static window features.

    Returns:
        New WindowedDataset containing original features plus sequential trajectory features.
    """
    n_windows = dataset.X.shape[0]
    n_extra = len(SEQUENTIAL_EXTRA_FEATURE_NAMES)
    extra_features = np.zeros((n_windows, n_extra), dtype=np.float64)

    # Indices of required static features
    idx_ent_mean = WINDOW_FEATURE_NAMES.index("entropy_mean")
    idx_write_rate = WINDOW_FEATURE_NAMES.index("write_rate")
    idx_write_bytes = WINDOW_FEATURE_NAMES.index("write_bytes_total")

    unique_exec_ids = np.unique(dataset.execution_ids)

    for ex_id in unique_exec_ids:
        mask = (dataset.execution_ids == ex_id)
        indices = np.where(mask)[0]
        # Ensure chronological ordering within execution
        times = dataset.window_times[indices, 0]
        sort_order = np.argsort(times)
        ordered_idx = indices[sort_order]

        ent_means = dataset.X[ordered_idx, idx_ent_mean]
        write_rates = dataset.X[ordered_idx, idx_write_rate]
        write_bytes = dataset.X[ordered_idx, idx_write_bytes]

        cum_bytes = 0.0
        cum_high_ent = 0.0
        current_streak = 0.0
        prev_ent = 0.0
        prev_prev_ent = 0.0
        prev_rate = 0.0
        prev_bytes = 0.0
        ent_history = []

        for step, row_idx in enumerate(ordered_idx):
            ent = ent_means[step]
            rate = write_rates[step]
            b_bytes = write_bytes[step]

            # 1. Lag-1 and Lag-2 differences
            if step == 0:
                delta_ent_1 = 0.0
                delta_ent_2 = 0.0
                accel_ent = 0.0
                delta_rate_1 = 0.0
                delta_bytes_1 = 0.0
            elif step == 1:
                delta_ent_1 = ent - prev_ent
                delta_ent_2 = 0.0
                accel_ent = delta_ent_1
                delta_rate_1 = rate - prev_rate
                delta_bytes_1 = b_bytes - prev_bytes
            else:
                delta_ent_1 = ent - prev_ent
                delta_ent_prev = prev_ent - prev_prev_ent
                delta_ent_2 = ent - prev_prev_ent
                accel_ent = delta_ent_1 - delta_ent_prev
                delta_rate_1 = rate - prev_rate
                delta_bytes_1 = b_bytes - prev_bytes

            # 2. Cumulative statistics
            cum_bytes += b_bytes
            ent_history.append(ent)
            expanding_mean_ent = float(np.mean(ent_history))

            is_high_entropy = (ent >= 0.85)
            if is_high_entropy:
                cum_high_ent += 1.0
                current_streak += 1.0
            else:
                current_streak = 0.0

            # 3. Transition to high entropy
            transition_flag = 1.0 if (step > 0 and prev_ent < 0.70 and ent >= 0.85) else 0.0

            extra_features[row_idx, :] = [
                delta_ent_1,
                delta_ent_2,
                accel_ent,
                delta_rate_1,
                delta_bytes_1,
                cum_bytes,
                cum_high_ent,
                current_streak,
                transition_flag,
                expanding_mean_ent,
            ]

            prev_prev_ent = prev_ent
            prev_ent = ent
            prev_rate = rate
            prev_bytes = b_bytes

    combined_X = np.hstack([dataset.X, extra_features])
    combined_feature_names = list(dataset.feature_names) + list(SEQUENTIAL_EXTRA_FEATURE_NAMES)

    return WindowedDataset(
        X=combined_X,
        y_binary=dataset.y_binary.copy(),
        y_detail=dataset.y_detail.copy(),
        execution_ids=dataset.execution_ids.copy(),
        window_times=dataset.window_times.copy(),
        families=dataset.families.copy(),
        feature_names=combined_feature_names,
    )
