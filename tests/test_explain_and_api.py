"""Unit tests for Explanation Service (T-P8-01) and Inference API (T-P8-02)."""

import time
from pathlib import Path
import numpy as np
import pytest

from src.data.load_mlran import load_mlran_dataset
from src.explain.reasons import ExplanationService, SampleExplanation
from src.app.api import RansomwareInferenceEngine, app, MODEL_VERSION


@pytest.fixture(scope="module")
def mlran_data():
    return load_mlran_dataset()


@pytest.fixture(scope="module")
def inference_engine():
    return RansomwareInferenceEngine()


def test_explanation_service_speed_and_reasons(mlran_data, inference_engine):
    # Get a ransomware test sample
    X_sample = mlran_data.X_test.iloc[0].values

    t0 = time.perf_counter()
    explanation = inference_engine.explainer.explain_sample(
        X_sample=X_sample, sample_id="test_sample_0", top_k=5
    )
    elapsed = time.perf_counter() - t0

    # Acceptance criteria: Top-5 reasons computed in < 1.0 second
    assert elapsed < 1.0, f"Explanation took {elapsed:.3f}s, expected < 1.0s"
    assert explanation.explanation_time_sec < 1.0

    # Verify reasons have plain text descriptions and valid directions
    assert len(explanation.top_malicious_reasons) > 0 or len(explanation.top_benign_reasons) > 0
    all_reasons = explanation.top_malicious_reasons + explanation.top_benign_reasons
    for r in all_reasons:
        assert isinstance(r.plain_text, str) and len(r.plain_text) > 0
        assert r.direction in {"malicious", "benign"}
        assert isinstance(r.category, str)


def test_inference_engine_predict_response_structure(mlran_data, inference_engine):
    sample = mlran_data.X_test.iloc[0].values
    res = inference_engine.predict(sample, sample_id="sample_01", top_k=5)

    # Acceptance criteria: Version string in every response
    assert "model_version" in res
    assert res["model_version"] == MODEL_VERSION

    # Check required fields
    assert res["sample_id"] == "sample_01"
    assert res["verdict"] in {"ransomware", "goodware"}
    assert isinstance(res["is_ransomware"], bool)
    assert 0.0 <= res["confidence"] <= 1.0
    assert 0.0 <= res["probability_raw"] <= 1.0
    assert "inference_latency_ms" in res
    assert isinstance(res["top_reasons"], list)

    for reason in res["top_reasons"]:
        assert "feature" in reason
        assert "impact" in reason
        assert "category" in reason
        assert "description" in reason


def test_fastapi_endpoints():
    from src.app.api import health_check, predict_endpoint, PredictRequest

    # 1. Health check endpoint
    data_health = health_check()
    assert data_health["status"] == "healthy"
    assert data_health["model_version"] == MODEL_VERSION

    # 2. Predict endpoint with dummy 483 feature vector
    dummy_features = [0.0] * 483
    dummy_features[5] = 1.0  # activate some feature
    req = PredictRequest(
        sample_id="api_test_01",
        features=dummy_features,
        top_reasons=3,
    )

    data_predict = predict_endpoint(req)
    assert data_predict.model_version == MODEL_VERSION
    assert data_predict.sample_id == "api_test_01"
    assert data_predict.verdict in {"ransomware", "goodware"}
    assert len(data_predict.top_reasons) <= 3
