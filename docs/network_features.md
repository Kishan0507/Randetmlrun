# Network Feature Specification & Flow-Level Behavioral Extraction (T-P6-01)

## 1. Context & Motivation

In the MLRan paper (JNCA 2026), the authors extracted features across 9 behavioral groups (API calls, categories, signatures, directories, registry, dropped files, mutexes, processes, and network). However, **0 out of the 483 final RFE-selected features came from the network group** (Audit A8 & A14 in `memory/03_PAPER_AUDIT.md`).

### Why Did the Paper Drop All Network Features?
1. **Sandbox Network Isolation**: The MLRan Cuckoo sandbox executed malware in an isolated host-only virtual network with fake DNS / Tor gateway simulation (`192.168.56.x`). Ransomware attempting to contact live command-and-control (C2) servers or download public keys failed immediately, generating only standard broadcast/NetBIOS traffic (ports 137, 138) and DNS lookup failures.
2. **Feature Sparsity & High Noise**: Many benign samples ran completely offline or had static telemetry pings to Microsoft servers (`www.msftncsi.com`), causing network presence to have near-zero Mutual Information (MI) with the ransomware label.
3. **Lack of Flow-Level Dynamics**: The paper's parser only extracted raw string occurrences or basic presence flags, rather than flow-level temporal metrics (burstiness, failure ratios, domain entropy, connection rates).

To address this, we design 12 flow-level features that capture both live C2 behaviors and sandbox-evasion / discovery patterns.

---

## 2. Feature Specification Catalog

| Feature Name | Type | Cuckoo Source Field | Mathematical Formula / Extraction Logic | Security Rationale |
|---|---|---|---|---|
| `net_dns_query_count` | Integer | `network.dns[].request` | $N_{\text{DNS}} = \vert \text{network.dns} \vert$ | C2 domain lookup and DGA (Domain Generation Algorithm) probing. |
| `net_distinct_domains` | Integer | `network.domains[].domain` | $N_{\text{domains}} = \vert \text{unique}(\text{network.domains}) \vert$ | Multiple redundant domains contacted indicates C2 fallback or DGA. |
| `net_distinct_hosts` | Integer | `network.hosts[]` | $N_{\text{hosts}} = \vert \text{unique}(\text{network.hosts}) \vert$ | Unique external IP addresses contacted. |
| `net_distinct_ports` | Integer | `network.tcp[].dport`, `network.udp[].dport` | $\vert \text{ports}_{\text{TCP}} \cup \text{ports}_{\text{UDP}} \vert$ | Port scanning or multi-protocol communication (e.g., DNS 53, HTTP 80/8080, HTTPS 443, Tor 9001). |
| `net_total_bytes_sent` | Float | `network.tcp[].offset`, `network.udp[].offset` | $\sum \text{payload\_bytes}$ | Data exfiltration volume prior to encryption. |
| `net_tls_ratio` | Float | `network.tls[]`, `network.http[]` | $\frac{\vert \text{TLS} \vert}{\vert \text{TLS} \vert + \vert \text{HTTP} \vert + \epsilon}$ | Modern ransomware families (e.g., LockBit, BlackCat) use TLS/HTTPS to evade deep packet inspection. |
| `net_conn_burst_rate` | Float | `network.tcp[].time`, `network.udp[].time` | $\max_{\Delta t = 1.0\text{s}} \frac{\text{connections}}{\Delta t}$ | Rapid connection attempts within a 1-second burst window. |
| `net_failed_conn_ratio` | Float | `network.dead_hosts[]`, `network.hosts[]` | $\frac{\vert \text{dead\_hosts} \vert}{\vert \text{hosts} \vert + \vert \text{dead\_hosts} \vert + \epsilon}$ | Unreachable C2 IPs in closed testbeds cause high connection failure rates. |
| `net_tld_entropy` | Float | `network.dns[].request` | $-\sum_{i} p(\text{char}_i) \log_2 p(\text{char}_i)$ on 2nd-level domain strings | DGA-generated domains have significantly higher Shannon entropy than benign corporate domains. |
| `net_dga_domain_count` | Integer | `network.dns[].request` | Count of domains with length $> 16$ or consonant ratio $> 0.65$ | Detects algorithmic pseudorandom domain names. |
| `net_suspicious_ports` | Integer | `network.tcp[].dport`, `network.udp[].dport` | Count of connections to non-standard ports (e.g. 4444, 1337, 8443, 9001) | Direct C2 reverse shells or Tor traffic. |
| `net_broadcast_ratio` | Float | `network.udp[].dst` | Fraction of UDP packets sent to `*.255` broadcast addresses | High broadcast (NetBIOS 137/138) indicates local network reconnaissance without external C2. |

---

## 3. Extraction Edge Cases & Defensive Defaults

1. **Air-gapped / Completely Offline Executions**: Samples with `network: {}` or missing keys return zeroes across all network counts and ratios without throwing exceptions.
2. **Missing `offset` or payload sizes**: In PCAP summaries where payload size is omitted, connection count is used as an activity proxy.
3. **Internal vs External IPs**: Local loopback (`127.0.0.1`), gateway (`192.168.56.1`), and host-only addresses are differentiated from routable public IP addresses.
