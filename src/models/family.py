"""Family classification helpers (T-P2-03, T-P2-04).

- Merge rare families (< N train samples) into an Other bucket so macro metrics
  are not dominated by singletons.
- Hierarchical binary → family prediction.
- One-vs-rest confidence rejection so low-confidence / unseen families can be
  flagged as unknown instead of being forced into a known label.
"""

from __future__ import annotations

from typing import Dict, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier


GOODWARE_LABEL = 0
OTHER_LABEL = -1
UNKNOWN_LABEL = -2


def merge_rare_families(
    y_train: pd.Series,
    y_other: pd.Series | None = None,
    min_samples: int = 10,
    other_label: int = OTHER_LABEL,
    protect: Sequence[int] = (GOODWARE_LABEL,),
) -> tuple[pd.Series, pd.Series | None, set[int]]:
    """Relabel families with fewer than `min_samples` train rows as Other.

    Goodware (label 0) is never merged. Mapping is fit on train only.
    """
    counts = y_train.value_counts()
    rare = set(int(lab) for lab, n in counts.items() if n < min_samples and int(lab) not in protect)

    def _map(y: pd.Series) -> pd.Series:
        mapped = y.copy()
        mapped = mapped.where(~mapped.isin(rare), other_label)
        return mapped.astype(int)

    y_train_m = _map(y_train)
    y_other_m = _map(y_other) if y_other is not None else None
    return y_train_m, y_other_m, rare


def hierarchical_predict(
    binary_pred: np.ndarray,
    family_pred: np.ndarray,
    goodware_label: int = GOODWARE_LABEL,
) -> np.ndarray:
    """If binary says goodware, emit goodware; else emit the family prediction."""
    binary_pred = np.asarray(binary_pred)
    family_pred = np.asarray(family_pred)
    return np.where(binary_pred == 0, goodware_label, family_pred)


def per_family_recall(
    y_true: np.ndarray | pd.Series,
    y_pred: np.ndarray | pd.Series,
    name_map: Mapping[int, str] | None = None,
    min_support: int = 1,
) -> pd.DataFrame:
    """Recall per true family label (support-aware; skips empty classes)."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    rows = []
    for lab in sorted(set(y_true.tolist())):
        mask = y_true == lab
        support = int(mask.sum())
        if support < min_support:
            continue
        rec = float((y_pred[mask] == lab).mean())
        name = name_map.get(int(lab), str(lab)) if name_map else str(lab)
        rows.append(
            {
                "family_id": int(lab),
                "family": name,
                "support": support,
                "recall": rec,
            }
        )
    return pd.DataFrame(rows)


def family_name_map(meta: pd.DataFrame, id_col: str = "family_label", name_col: str = "ransomware_family") -> Dict[int, str]:
    """Map numeric family_label → ransomware_family string (0 → goodware)."""
    mapping: Dict[int, str] = {}
    if id_col not in meta.columns:
        return mapping
    for fid, grp in meta.groupby(id_col):
        fid_i = int(fid)
        if fid_i == GOODWARE_LABEL:
            mapping[fid_i] = "goodware"
            continue
        if name_col in grp.columns:
            names = grp[name_col].dropna().astype(str)
            mapping[fid_i] = names.iloc[0] if len(names) else str(fid_i)
        else:
            mapping[fid_i] = str(fid_i)
    mapping.setdefault(OTHER_LABEL, "other")
    mapping.setdefault(UNKNOWN_LABEL, "unknown")
    return mapping


def fit_ovr_family_model(
    X: pd.DataFrame | np.ndarray,
    y: pd.Series | np.ndarray,
    random_state: int = 42,
) -> OneVsRestClassifier:
    """One-vs-rest LR used for unknown-family confidence scores."""
    base = LogisticRegression(
        solver="liblinear",
        class_weight="balanced",
        max_iter=1000,
        random_state=random_state,
    )
    clf = OneVsRestClassifier(base, n_jobs=1)
    clf.fit(X, y)
    return clf


def unknown_flags(
    ovr: OneVsRestClassifier,
    X: pd.DataFrame | np.ndarray,
    confidence_threshold: float,
    unknown_label: int = UNKNOWN_LABEL,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (argmax class, max probability). Labels below threshold are unknown.

    Callers should replace argmax with `unknown_label` when max_prob < threshold.
    """
    proba = ovr.predict_proba(X)
    max_prob = proba.max(axis=1)
    argmax_idx = proba.argmax(axis=1)
    classes = np.asarray(ovr.classes_)
    pred = classes[argmax_idx]
    pred = np.where(max_prob >= confidence_threshold, pred, unknown_label)
    return pred, max_prob


def choose_unknown_threshold(
    max_prob_known: np.ndarray,
    target_known_keep_rate: float = 0.95,
) -> float:
    """Threshold so that about `target_known_keep_rate` of in-distribution samples stay labelled.

    Uses the lower quantile of max-prob on known (validation) samples.
    """
    if len(max_prob_known) == 0:
        return 1.0
    q = np.clip(1.0 - target_known_keep_rate, 0.0, 1.0)
    return float(np.quantile(max_prob_known, q))
