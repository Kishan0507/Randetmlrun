"""Flow-level network feature extractor from Cuckoo JSON reports (T-P6-01, T-P6-02).

Extracts flow-level, behavioral, and statistical network features from the Cuckoo
network trace section (DNS, TCP, UDP, HTTP, TLS, hosts, dead hosts).
"""

from __future__ import annotations

import collections
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


@dataclass
class NetworkFeatures:
    """Extracted flow-level network behavioral features."""

    sample_id: str
    dns_query_count: int
    distinct_domains: int
    distinct_hosts: int
    distinct_ports: int
    total_bytes_sent: float
    tls_ratio: float
    conn_burst_rate: float
    failed_conn_ratio: float
    mean_domain_entropy: float
    dga_domain_count: int
    suspicious_ports_count: int
    broadcast_ratio: float
    features_vector: Dict[str, float] = field(default_factory=dict)


def compute_shannon_entropy(text: str) -> float:
    """Compute Shannon entropy of a string."""
    if not text:
        return 0.0
    length = len(text)
    counts = collections.Counter(text)
    ent = 0.0
    for count in counts.values():
        p = count / length
        ent -= p * math.log2(p)
    return float(ent)


def is_dga_like(domain: str) -> bool:
    """Heuristic test for algorithmic domain generation (DGA)."""
    if not domain:
        return False
    # Strip TLD
    parts = domain.split(".")
    base = parts[0] if parts else domain
    if len(base) > 16:
        return True
    # Consonant-vowel ratio
    vowels = set("aeiou")
    consonants = set("bcdfghjklmnpqrstvwxyz")
    v_count = sum(1 for c in base.lower() if c in vowels)
    c_count = sum(1 for c in base.lower() if c in consonants)
    if c_count > 0 and v_count == 0 and len(base) >= 6:
        return True
    if len(base) >= 8 and (c_count / (v_count + c_count + 1e-6)) > 0.8:
        return True
    return False


def extract_network_features(
    report: Dict[str, Any],
    sample_id: str = "sample",
) -> NetworkFeatures:
    """Extract flow-level network features from a Cuckoo JSON report.

    Safely handles empty network sections, missing keys, and air-gapped runs.
    """
    net = report.get("network", {})
    if not isinstance(net, dict):
        net = {}

    dns_entries = net.get("dns", [])
    if not isinstance(dns_entries, list):
        dns_entries = []

    domains_entries = net.get("domains", [])
    if not isinstance(domains_entries, list):
        domains_entries = []

    hosts_entries = net.get("hosts", [])
    if not isinstance(hosts_entries, list):
        hosts_entries = []

    tcp_entries = net.get("tcp", [])
    if not isinstance(tcp_entries, list):
        tcp_entries = []

    udp_entries = net.get("udp", [])
    if not isinstance(udp_entries, list):
        udp_entries = []

    http_entries = net.get("http", [])
    if not isinstance(http_entries, list):
        http_entries = []

    tls_entries = net.get("tls", [])
    if not isinstance(tls_entries, list):
        tls_entries = []

    dead_hosts = net.get("dead_hosts", [])
    if not isinstance(dead_hosts, list):
        dead_hosts = []

    # 1. DNS & Domain metrics
    dns_query_count = len(dns_entries)
    domain_names: Set[str] = set()
    for d in domains_entries:
        if isinstance(d, dict) and "domain" in d:
            domain_names.add(d["domain"])
    for d in dns_entries:
        if isinstance(d, dict) and "request" in d:
            domain_names.add(d["request"])

    distinct_domains = len(domain_names)

    # Domain entropy and DGA detection
    entropies = [compute_shannon_entropy(d) for d in domain_names]
    mean_domain_entropy = float(np.mean(entropies)) if entropies else 0.0
    dga_domain_count = sum(1 for d in domain_names if is_dga_like(d))

    # 2. Host and Port metrics
    distinct_hosts = len(set(hosts_entries))
    ports: Set[int] = set()
    total_bytes = 0.0
    conn_times: List[float] = []
    broadcast_count = 0

    suspicious_ports_catalog = {1337, 31337, 4444, 5555, 6666, 8443, 9001, 9050}
    suspicious_ports_count = 0

    for conn in tcp_entries:
        if isinstance(conn, dict):
            dp = conn.get("dport")
            if dp is not None:
                try:
                    p = int(dp)
                    ports.add(p)
                    if p in suspicious_ports_catalog:
                        suspicious_ports_count += 1
                except (ValueError, TypeError):
                    pass
            offset = conn.get("offset", 0)
            if isinstance(offset, (int, float)):
                total_bytes += float(offset)
            t = conn.get("time")
            if t is not None:
                try:
                    conn_times.append(float(t))
                except (ValueError, TypeError):
                    pass

    for conn in udp_entries:
        if isinstance(conn, dict):
            dp = conn.get("dport")
            if dp is not None:
                try:
                    p = int(dp)
                    ports.add(p)
                    if p in suspicious_ports_catalog:
                        suspicious_ports_count += 1
                except (ValueError, TypeError):
                    pass
            offset = conn.get("offset", 0)
            if isinstance(offset, (int, float)):
                total_bytes += float(offset)
            t = conn.get("time")
            if t is not None:
                try:
                    conn_times.append(float(t))
                except (ValueError, TypeError):
                    pass
            dst = str(conn.get("dst", ""))
            if dst.endswith(".255"):
                broadcast_count += 1

    distinct_ports = len(ports)
    total_udp = len(udp_entries)
    broadcast_ratio = float(broadcast_count / total_udp) if total_udp > 0 else 0.0

    # 3. Protocol ratios & failure rates
    total_proto = len(tls_entries) + len(http_entries)
    tls_ratio = float(len(tls_entries) / total_proto) if total_proto > 0 else 0.0

    total_hosts = distinct_hosts + len(dead_hosts)
    failed_conn_ratio = float(len(dead_hosts) / total_hosts) if total_hosts > 0 else 0.0

    # 4. Burst rate: max connections within a 1.0s window
    conn_burst_rate = 0.0
    if len(conn_times) > 1:
        conn_times.sort()
        # Sliding window 1.0 second
        arr = np.array(conn_times)
        max_burst = 0
        for i in range(len(arr)):
            burst = int(np.sum((arr >= arr[i]) & (arr < arr[i] + 1.0)))
            if burst > max_burst:
                max_burst = burst
        conn_burst_rate = float(max_burst)
    elif len(conn_times) == 1:
        conn_burst_rate = 1.0

    f_vec: Dict[str, float] = {
        "net_dns_query_count": float(dns_query_count),
        "net_distinct_domains": float(distinct_domains),
        "net_distinct_hosts": float(distinct_hosts),
        "net_distinct_ports": float(distinct_ports),
        "net_total_bytes_sent": float(total_bytes),
        "net_tls_ratio": float(tls_ratio),
        "net_conn_burst_rate": float(conn_burst_rate),
        "net_failed_conn_ratio": float(failed_conn_ratio),
        "net_mean_domain_entropy": float(mean_domain_entropy),
        "net_dga_domain_count": float(dga_domain_count),
        "net_suspicious_ports_count": float(suspicious_ports_count),
        "net_broadcast_ratio": float(broadcast_ratio),
    }

    return NetworkFeatures(
        sample_id=sample_id,
        dns_query_count=dns_query_count,
        distinct_domains=distinct_domains,
        distinct_hosts=distinct_hosts,
        distinct_ports=distinct_ports,
        total_bytes_sent=total_bytes,
        tls_ratio=tls_ratio,
        conn_burst_rate=conn_burst_rate,
        failed_conn_ratio=failed_conn_ratio,
        mean_domain_entropy=mean_domain_entropy,
        dga_domain_count=dga_domain_count,
        suspicious_ports_count=suspicious_ports_count,
        broadcast_ratio=broadcast_ratio,
        features_vector=f_vec,
    )
