"""Inference API and prediction service with explainability (T-P8-02).

Provides unified model loading, prediction with calibrated confidence,
top security reasons, and metadata versioning.
Can be imported directly as a Python service or served via FastAPI.

Acceptance criteria:
  - Version string included in every response.
  - Unit tests verifying verdict, confidence, reasons, and latency.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.data.load_mlran import load_feature_names, load_mlran_dataset
from src.explain.reasons import ExplanationService, SampleExplanation

# Model metadata constants
MODEL_VERSION = "v2.1.0"
MODEL_ALGORITHM = "LogisticRegression-L2-Calibrated"
DATASET_VERSION = "MLRan-483-RFE"
OPERATING_THRESHOLD = 0.50  # Tuned operating point (or from configs/operating_point.yaml)


class PredictRequest(BaseModel):
    """Prediction request schema for API endpoints."""

    sample_id: Optional[str] = "input_sample"
    features: List[float] = Field(..., description="Array of 483 numeric feature values")
    top_reasons: Optional[int] = 5


class PredictResponse(BaseModel):
    """Standardized prediction response schema."""

    sample_id: str
    verdict: str  # "ransomware" or "goodware"
    is_ransomware: bool
    confidence: float
    probability_raw: float
    model_version: str
    algorithm: str
    threshold_used: float
    inference_latency_ms: float
    top_reasons: List[Dict[str, Any]]


class RansomwareInferenceEngine:
    """Core production inference and explanation engine."""

    def __init__(
        self,
        model_path: str | Path = "models/logistic_test.joblib",
        feature_names_path: str | Path = "data/raw/mlran",
        reasons_config_path: str | Path = "configs/reasons.yaml",
        operating_threshold: float = OPERATING_THRESHOLD,
        model_version: str = MODEL_VERSION,
    ):
        self.model_version = model_version
        self.algorithm = MODEL_ALGORITHM
        self.operating_threshold = operating_threshold

        # Load feature names in exact dataset column order
        self.feature_map = load_feature_names(feature_names_path)
        data_path = Path(feature_names_path)
        train_file = data_path / "MLRan_X_train_RFE.csv"
        if train_file.exists():
            header = pd.read_csv(train_file, nrows=0).columns
            label_cols = {"sample_id", "sample_type", "family_label", "type_label"}
            feature_cols = [c for c in header if c not in label_cols]
            self.feature_names = [self.feature_map.get(c, c) for c in feature_cols]
        else:
            self.feature_names = list(self.feature_map.values())

        # Load trained model
        m_path = Path(model_path)
        if not m_path.exists():
            raise FileNotFoundError(f"Model file not found at {m_path}")
        self.model = joblib.load(m_path)

        # Initialize explanation service
        self.explainer = ExplanationService(
            model=self.model,
            feature_names=self.feature_names,
            config_path=reasons_config_path,
        )

    def predict(
        self,
        features: Union[List[float], np.ndarray, pd.Series],
        sample_id: str = "sample",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Perform classification and generate plain-language explanations.

        Args:
            features: 483-dimensional numeric feature vector
            sample_id: Identifier
            top_k: Number of plain-language reasons to return

        Returns:
            Dictionary matching PredictResponse schema
        """
        t0 = time.perf_counter()

        feat_arr = np.asarray(features, dtype=np.float64).reshape(1, -1)
        if feat_arr.shape[1] != len(self.feature_names):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, got {feat_arr.shape[1]}"
            )

        # Generate explanation and prediction
        explanation: SampleExplanation = self.explainer.explain_sample(
            X_sample=feat_arr[0],
            sample_id=sample_id,
            top_k=top_k,
        )

        prob = explanation.predicted_probability
        is_ran = prob >= self.operating_threshold
        verdict = "ransomware" if is_ran else "goodware"
        confidence = prob if is_ran else (1.0 - prob)

        # Format reasons
        reasons_list = []
        source_reasons = (
            explanation.top_malicious_reasons if is_ran else explanation.top_benign_reasons
        )
        for r in source_reasons:
            reasons_list.append({
                "feature": r.feature_name,
                "value": r.feature_value,
                "impact": f"{r.shap_value:+.4f}",
                "category": r.category,
                "mitre": r.mitre_technique,
                "severity": r.severity,
                "description": r.plain_text,
            })

        total_latency_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "sample_id": sample_id,
            "verdict": verdict,
            "is_ransomware": is_ran,
            "confidence": round(confidence, 4),
            "probability_raw": round(prob, 4),
            "model_version": self.model_version,
            "algorithm": self.algorithm,
            "threshold_used": self.operating_threshold,
            "inference_latency_ms": round(total_latency_ms, 2),
            "top_reasons": reasons_list,
        }


# ─── FastAPI Application ─────────────────────────────────────────────────────
app = FastAPI(
    title="Ransomware Early Detection & Explanation API",
    version=MODEL_VERSION,
    description="Inference API providing calibrated predictions and plain-language security explanations.",
)

_engine: Optional[RansomwareInferenceEngine] = None


def get_engine() -> RansomwareInferenceEngine:
    """Lazy loader for singleton inference engine."""
    global _engine
    if _engine is None:
        _engine = RansomwareInferenceEngine()
    return _engine


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint returning model version."""
    engine = get_engine()
    return {
        "status": "healthy",
        "model_version": engine.model_version,
        "algorithm": engine.algorithm,
    }


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(request: PredictRequest) -> PredictResponse:
    """Inference endpoint."""
    engine = get_engine()
    try:
        res = engine.predict(
            features=request.features,
            sample_id=request.sample_id or "sample",
            top_k=request.top_reasons or 5,
        )
        return PredictResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
