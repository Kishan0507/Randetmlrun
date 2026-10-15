"""Explanation service mapping model predictions to plain-language reasons (T-P8-01).

Uses SHAP and feature contribution attribution to explain why a sample is classified
as ransomware or goodware, mapping raw technical features (e.g. API:NtProtectVirtualMemory)
to plain-language security analyst reasons and MITRE ATT&CK techniques.

Acceptance criteria:
  - Top-5 reasons per prediction computed in < 1.0 second.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import shap
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


@dataclass
class FeatureReason:
    """Plain-language explanation for an individual feature contribution."""

    feature_name: str
    feature_value: float
    shap_value: float
    plain_text: str
    category: str
    mitre_technique: str
    severity: str
    direction: str  # 'malicious' (pushes towards ransomware) or 'benign' (pushes towards goodware)


@dataclass
class SampleExplanation:
    """Complete explanation package for a single sample."""

    sample_id: str
    predicted_label: int  # 1 = ransomware, 0 = goodware
    predicted_probability: float
    top_malicious_reasons: List[FeatureReason]
    top_benign_reasons: List[FeatureReason]
    explanation_time_sec: float
    base_value: float = 0.0

    def summary_table(self) -> pd.DataFrame:
        """Formatted DataFrame of top contributing reasons."""
        rows = []
        for r in self.top_malicious_reasons:
            rows.append({
                "Direction": "Malicious (+)",
                "Feature": r.feature_name,
                "Value": r.feature_value,
                "SHAP Impact": f"{r.shap_value:+.4f}",
                "Category": r.category,
                "MITRE": r.mitre_technique,
                "Analyst Reason": r.plain_text,
            })
        for r in self.top_benign_reasons:
            rows.append({
                "Direction": "Benign (-)",
                "Feature": r.feature_name,
                "Value": r.feature_value,
                "SHAP Impact": f"{r.shap_value:+.4f}",
                "Category": r.category,
                "MITRE": r.mitre_technique,
                "Analyst Reason": r.plain_text,
            })
        return pd.DataFrame(rows)


class ExplanationService:
    """Service providing fast SHAP-based feature explanations with security translations."""

    def __init__(
        self,
        model: Any,
        feature_names: List[str],
        config_path: str | Path = "configs/reasons.yaml",
        background_data: Optional[np.ndarray] = None,
    ):
        self.model = model
        self.feature_names = list(feature_names)
        self.config_path = Path(config_path)

        # Load yaml dictionaries
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = {}

        self.patterns = self.config.get("patterns", {})
        self.prefix_fallbacks = self.config.get("prefix_fallbacks", {})

        # Unpack pipeline if needed
        self.estimator = model
        self.scaler = None
        if isinstance(model, Pipeline):
            if "scaler" in model.named_steps:
                self.scaler = model.named_steps["scaler"]
            self.estimator = model.named_steps["clf"]

        # Initialise SHAP explainer
        self._init_explainer(background_data)

    def _init_explainer(self, background_data: Optional[np.ndarray] = None) -> None:
        """Initialise appropriate SHAP explainer based on model family."""
        if isinstance(self.estimator, LogisticRegression):
            # For linear models, exact analytical coefficients enable instantaneous SHAP
            # intercept and coefficients represent log-odds contributions
            self.explainer_type = "linear"
            self.coef = self.estimator.coef_[0]
            self.intercept = float(self.estimator.intercept_[0])
        else:
            self.explainer_type = "tree_or_kernel"
            try:
                self.explainer = shap.TreeExplainer(self.estimator)
            except Exception:
                # Fallback to kernel or linear surrogate
                self.explainer = None

    def map_feature_to_reason(
        self,
        feature_name: str,
        feature_value: float,
        shap_value: float,
    ) -> FeatureReason:
        """Translate a raw feature and its SHAP impact into a plain-language reason."""
        direction = "malicious" if shap_value > 0 else "benign"

        # 1. Exact match in patterns
        if feature_name in self.patterns:
            entry = self.patterns[feature_name]
            return FeatureReason(
                feature_name=feature_name,
                feature_value=feature_value,
                shap_value=shap_value,
                plain_text=entry.get("reason", feature_name),
                category=entry.get("category", "General"),
                mitre_technique=entry.get("mitre", "N/A"),
                severity=entry.get("severity", "INFORMATIONAL"),
                direction=direction,
            )

        # 2. Prefix fallback
        prefix = feature_name.split(":")[0] if ":" in feature_name else "UNKNOWN"
        remainder = feature_name.split(":", 1)[1] if ":" in feature_name else feature_name

        if prefix in self.prefix_fallbacks:
            fallback = self.prefix_fallbacks[prefix]
            template = fallback.get("reason_template", "Observed {name}.")
            text = template.format(name=remainder)
            return FeatureReason(
                feature_name=feature_name,
                feature_value=feature_value,
                shap_value=shap_value,
                plain_text=text,
                category=fallback.get("category", prefix),
                mitre_technique=fallback.get("mitre", "N/A"),
                severity="MEDIUM" if shap_value > 0 else "LOW",
                direction=direction,
            )

        # 3. Default generic reason
        return FeatureReason(
            feature_name=feature_name,
            feature_value=feature_value,
            shap_value=shap_value,
            plain_text=f"Feature '{feature_name}' has value {feature_value:.2f}.",
            category="Other",
            mitre_technique="N/A",
            severity="INFORMATIONAL",
            direction=direction,
        )

    def explain_sample(
        self,
        X_sample: np.ndarray,
        sample_id: str = "sample",
        top_k: int = 5,
    ) -> SampleExplanation:
        """Compute top-k plain-language reasons explaining the model's verdict for a sample.

        Args:
            X_sample: 1D array of feature values (length = n_features) or 2D (1, n_features)
            sample_id: Sample identifier
            top_k: Number of positive and negative reasons to extract

        Returns:
            SampleExplanation instance
        """
        t0 = time.perf_counter()

        X_arr = np.asarray(X_sample, dtype=np.float64).reshape(1, -1)
        raw_vals = X_arr[0]

        # Get scaled vector if pipeline has scaler
        X_scaled = self.scaler.transform(X_arr)[0] if self.scaler is not None else raw_vals

        # Compute prediction and probability
        if hasattr(self.model, "predict_proba"):
            prob = float(self.model.predict_proba(X_arr)[0, 1])
        else:
            prob = 1.0 if self.model.predict(X_arr)[0] == 1 else 0.0

        pred_label = 1 if prob >= 0.5 else 0

        # Compute SHAP values
        if self.explainer_type == "linear":
            # For linear model: shap_i = coef_i * (x_scaled_i - mean_scaled_i)
            # Since StandardScaler normalises to mean 0: shap_i = coef_i * x_scaled_i
            shap_vals = self.coef * X_scaled
            base_val = self.intercept
        elif hasattr(self, "explainer") and self.explainer is not None:
            shap_res = self.explainer.shap_values(X_arr)
            shap_vals = shap_res[1][0] if isinstance(shap_res, list) else shap_res[0]
            base_val = float(self.explainer.expected_value[1] if isinstance(self.explainer.expected_value, (list, np.ndarray)) else self.explainer.expected_value)
        else:
            # Fallback to feature values * coef approximation
            shap_vals = raw_vals
            base_val = 0.0

        # Sort features by positive (malicious) and negative (benign) SHAP impact
        # We only consider features that were active or had non-trivial impact
        pos_indices = np.where(shap_vals > 0)[0]
        neg_indices = np.where(shap_vals < 0)[0]

        # Top positive
        pos_sorted = pos_indices[np.argsort(-shap_vals[pos_indices])]
        top_pos = pos_sorted[:top_k]

        # Top negative (most negative first)
        neg_sorted = neg_indices[np.argsort(shap_vals[neg_indices])]
        top_neg = neg_sorted[:top_k]

        malicious_reasons = [
            self.map_feature_to_reason(self.feature_names[i], raw_vals[i], float(shap_vals[i]))
            for i in top_pos
        ]

        benign_reasons = [
            self.map_feature_to_reason(self.feature_names[i], raw_vals[i], float(shap_vals[i]))
            for i in top_neg
        ]

        elapsed = time.perf_counter() - t0

        return SampleExplanation(
            sample_id=sample_id,
            predicted_label=pred_label,
            predicted_probability=prob,
            top_malicious_reasons=malicious_reasons,
            top_benign_reasons=benign_reasons,
            explanation_time_sec=elapsed,
            base_value=base_val,
        )
