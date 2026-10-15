"""Unit tests for ONNX export and endpoint benchmarking (T-P10-05)."""

from pathlib import Path
import numpy as np
import pytest
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression

from src.models.onnx_export import (
    ONNXBenchmarkReport,
    ONNXInferenceEngine,
    benchmark_onnx_footprint,
    export_model_to_onnx,
)


def test_export_and_benchmark_onnx(tmp_path):
    X, y = make_classification(
        n_samples=200,
        n_features=25,
        n_informative=12,
        random_state=42,
    )
    model = LogisticRegression(C=1.0, random_state=42)
    model.fit(X[:150], y[:150])

    onnx_file = tmp_path / "test_model.onnx"
    out_path = export_model_to_onnx(model, n_features=25, output_path=onnx_file)
    assert out_path.exists()
    assert out_path.stat().st_size > 0

    # Test engine
    engine = ONNXInferenceEngine(out_path)
    probs = engine.predict_proba(X[150:])
    preds = engine.predict(X[150:])

    assert probs.shape == (50, 2)
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-4)
    assert len(preds) == 50

    # Benchmark report
    rep = benchmark_onnx_footprint(model, out_path, X[150:], n_runs=20)
    assert rep.parity_verified is True
    assert rep.file_size_kb < 100.0  # highly compact footprint
    assert rep.mean_latency_ms < 10.0  # low latency on CPU
