"""Unit tests for cross-dataset generalisation and alignment (T-P10-07)."""

from pathlib import Path
import pytest

from src.eval.cross_dataset import (
    CrossDatasetReport,
    compute_cross_dataset_alignment,
)


def test_cross_dataset_alignment():
    rep = compute_cross_dataset_alignment()
    assert isinstance(rep, CrossDatasetReport)
    assert rep.mlran_sample_count > 0
    assert rep.ransmap_window_count > 0
    assert len(rep.common_families) > 0
    # Must identify shared families like conti or lockbit
    common_lower = [f.lower() for f in rep.common_families]
    assert any(fam in common_lower for fam in ["conti", "lockbit", "wannacry", "ryuk"])
    assert 0.0 <= rep.behavioral_overlap_score <= 1.0
    assert rep.representation_transferable is True
