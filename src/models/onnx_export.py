"""ONNX export and endpoint-agent footprint measurement (T-P10-05).

Exports trained ransomware classifiers to the open ONNX standard and benchmarks
endpoint deployment metrics: model file size, session memory, and sub-millisecond CPU latency.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import onnx
import onnxruntime as rt
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression


@dataclass
class ONNXBenchmarkReport:
    """Benchmark results for ONNX model on endpoint."""

    model_path: str
    file_size_kb: float
    n_features: int
    mean_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_absolute_diff: float
    parity_verified: bool


def export_model_to_onnx(
    model: BaseEstimator,
    n_features: int,
    output_path: str | Path = "models/ransomware_detector.onnx",
    initial_type_name: str = "float_input",
) -> Path:
    """Convert a scikit-learn model to ONNX format and save to disk.

    Args:
        model: Trained scikit-learn estimator.
        n_features: Number of input features.
        output_path: Target path for the .onnx file.
        initial_type_name: Tensor input name.

    Returns:
        Path to the saved ONNX model.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    initial_type = [(initial_type_name, FloatTensorType([None, n_features]))]
    # Set target_opset to ensure wide runtime compatibility
    onnx_model = convert_sklearn(model, initial_types=initial_type, target_opset=14)

    with open(out_file, "wb") as f:
        f.write(onnx_model.SerializeToString())

    return out_file


class ONNXInferenceEngine:
    """Lightweight ONNX Runtime inference wrapper for endpoint deployment."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {self.model_path}")

        # Optimize for single-thread / low-overhead endpoint inference
        opts = rt.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        opts.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = rt.InferenceSession(str(self.model_path), sess_options=opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Run ONNX inference and return class probabilities."""
        X_arr = np.asarray(X, dtype=np.float32)
        raw_outputs = self.session.run(self.output_names, {self.input_name: X_arr})

        # skl2onnx outputs: index 0 is labels, index 1 is list of probability dicts or array
        prob_output = raw_outputs[1]
        if isinstance(prob_output, list) and isinstance(prob_output[0], dict):
            # Extract probability for class 1
            p1 = np.array([row.get(1, 0.0) for row in prob_output], dtype=np.float32)
            p0 = 1.0 - p1
            return np.column_stack([p0, p1])
        elif isinstance(prob_output, np.ndarray):
            return prob_output
        else:
            raise ValueError(f"Unexpected ONNX probability output format: {type(prob_output)}")

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Run binary prediction."""
        probs = self.predict_proba(X)[:, 1]
        return (probs >= threshold).astype(np.int64)


def benchmark_onnx_footprint(
    sklearn_model: BaseEstimator,
    onnx_path: str | Path,
    X_sample: np.ndarray,
    n_runs: int = 100,
) -> ONNXBenchmarkReport:
    """Measure file size, output numerical parity, and per-sample latency of ONNX model."""
    onnx_file = Path(onnx_path)
    file_size_kb = onnx_file.stat().st_size / 1024.0

    engine = ONNXInferenceEngine(onnx_file)
    n_features = X_sample.shape[1]

    # Verify parity against scikit-learn
    sk_probs = sklearn_model.predict_proba(X_sample)[:, 1]
    onnx_probs = engine.predict_proba(X_sample)[:, 1]
    diff = float(np.max(np.abs(sk_probs - onnx_probs)))
    parity = diff < 1e-3

    # Benchmark single-sample latency
    latencies = []
    single_x = X_sample[:1].astype(np.float32)
    # Warmup
    for _ in range(10):
        engine.predict_proba(single_x)

    for _ in range(n_runs):
        t0 = time.perf_counter()
        engine.predict_proba(single_x)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms

    return ONNXBenchmarkReport(
        model_path=str(onnx_file),
        file_size_kb=round(file_size_kb, 2),
        n_features=n_features,
        mean_latency_ms=round(float(np.mean(latencies)), 4),
        p95_latency_ms=round(float(np.percentile(latencies, 95)), 4),
        p99_latency_ms=round(float(np.percentile(latencies, 99)), 4),
        max_absolute_diff=round(diff, 6),
        parity_verified=parity,
    )
