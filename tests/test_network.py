"""Unit tests for flow-level network feature extractor (T-P6-01, T-P6-02)."""

import json
from pathlib import Path
import numpy as np
import pytest

from src.features.network import (
    NetworkFeatures,
    compute_shannon_entropy,
    is_dga_like,
    extract_network_features,
)


@pytest.fixture
def synthetic_network_report():
    """Synthetic Cuckoo report with DNS, UDP, TCP, and dead hosts."""
    return {
        "network": {
            "dns": [
                {"request": "c2server.evilcorp.com", "type": "A"},
                {"request": "xkjqmwzrtpvbfkdlq.ru", "type": "A"},  # DGA domain
            ],
            "domains": [
                {"domain": "c2server.evilcorp.com", "ip": "185.220.101.5"},
                {"domain": "xkjqmwzrtpvbfkdlq.ru", "ip": "185.220.101.6"},
            ],
            "hosts": ["185.220.101.5", "185.220.101.6"],
            "dead_hosts": ["198.51.100.1"],  # 1 dead host
            "tcp": [
                {"dport": 4444, "offset": 1024, "time": 1.2},  # suspicious port
                {"dport": 4444, "offset": 2048, "time": 1.5},
            ],
            "udp": [
                {"dport": 53, "offset": 256, "time": 1.1, "dst": "8.8.8.8"},
                {"dport": 137, "offset": 128, "time": 1.8, "dst": "192.168.56.255"},  # broadcast
            ],
            "tls": [],
            "http": [],
        }
    }


def test_shannon_entropy():
    # Empty string has 0 entropy
    assert compute_shannon_entropy("") == 0.0
    # Repeating string has 0 entropy
    assert compute_shannon_entropy("aaaaaa") == 0.0
    # Diverse string has higher entropy
    ent1 = compute_shannon_entropy("google.com")
    ent2 = compute_shannon_entropy("xkjqmwzrtpvbfkdlq.ru")
    assert ent2 > ent1


def test_is_dga_like():
    assert not is_dga_like("google.com")
    assert not is_dga_like("microsoft.com")
    assert is_dga_like("xkjqmwzrtpvbfkdlq.ru")
    assert is_dga_like("abcdefghijklmnopqrstu.com")


def test_extract_network_features_synthetic(synthetic_network_report):
    feat = extract_network_features(synthetic_network_report, sample_id="syn_net")
    assert feat.sample_id == "syn_net"
    assert feat.dns_query_count == 2
    assert feat.distinct_domains == 2
    assert feat.distinct_hosts == 2
    assert feat.suspicious_ports_count == 2  # port 4444 twice
    assert feat.dga_domain_count >= 1
    assert feat.broadcast_ratio == 0.5  # 1 of 2 UDP is broadcast
    assert feat.failed_conn_ratio == pytest.approx(1.0 / 3.0, abs=1e-3)  # 1 dead / 3 total
    assert feat.conn_burst_rate == 4.0  # all 4 conns within [1.1, 1.8] <= 1.0s window
    assert feat.features_vector["net_total_bytes_sent"] == 1024 + 2048 + 256 + 128


def test_extract_network_features_empty_report():
    empty_report = {}
    feat = extract_network_features(empty_report, sample_id="empty")
    assert feat.sample_id == "empty"
    assert feat.dns_query_count == 0
    assert feat.distinct_hosts == 0
    assert feat.distinct_ports == 0
    assert feat.conn_burst_rate == 0.0
    assert feat.features_vector["net_failed_conn_ratio"] == 0.0


def test_extract_network_features_all_real_samples():
    samples_dir = Path("data/raw/cuckoo_samples")
    if not samples_dir.exists():
        pytest.skip("No cuckoo samples directory found")

    sample_files = list(samples_dir.glob("*.json"))
    if not sample_files:
        pytest.skip("No cuckoo json files downloaded")

    # Test all 20 real downloaded sample reports
    for s_path in sample_files:
        with open(s_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        feat = extract_network_features(data, sample_id=s_path.stem)
        assert feat.sample_id == s_path.stem
        assert feat.dns_query_count >= 0
        assert feat.distinct_ports >= 0
        assert np.isfinite(feat.conn_burst_rate)
        assert np.isfinite(feat.broadcast_ratio)
        for k, v in feat.features_vector.items():
            assert np.isfinite(v), f"Feature {k} must be finite for {s_path.name}"
