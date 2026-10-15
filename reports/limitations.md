# Limitations & Threats to Validity (T-P9-03)

**Task:** T-P9-03  
**Author:** Kalyani (Member 3)  
**Reviewed by:** Kishan (project lead), Karthikey  
**Date:** 2026-10-15  

---

## 1. Track A vs Track B Scope Boundary

This project operates exclusively under **Track A** (data-only; no live malware execution), as decided in D-001 and confirmed in D-009.

| Aspect | Track A (This Work) | Track B (Not Performed) |
|---|---|---|
| **Data Sources** | MLRan 483 RFE features (released), RanSMAP ATA writes, 20 sample Cuckoo JSONs | Full 6.4M MLRan features, re-execution of samples on Win10/11 sandbox |
| **Feature Extraction** | Pre-extracted static + behavioral features; cannot modify extraction pipeline | Custom feature engineering from raw Cuckoo reports at scale |
| **OS Coverage** | Win7 sandbox environment (MLRan original); Celeron/i3 hardware (RanSMAP) | Win10/11 with modern Defender state, modern hardware |
| **Scale of Early Detection** | 14 RanSMAP executions (6 ransomware families + 6 benign classes) | Hundreds of executions across dozens of families |
| **Prefix Evaluation** | 20 sample Cuckoo reports (prototype only) | Full MLRan corpus truncated at t seconds |

**Impact:** All early-detection claims (TTD, Detect@t, FA/hour) are demonstrated on a small number of executions and should be considered **proof-of-concept** rather than production-grade benchmarks. The prefix evaluation (T-P4-05) explicitly labels itself as prototype (per D-004 §7). Generalisation to unseen families and modern OS environments requires Track B execution.

---

## 2. Dataset Representativeness & Source Bias

### 2.1 Complete Source Bifurcation (Paper Audit A14)

The MLRan dataset exhibits **100% source bifurcation**: all goodware originates from Software Informer, while all ransomware comes from malware repositories (VirusTotal, MalwareBazaar, MOTIF). This creates a confound — the model may partially learn to distinguish "Software Informer packaging style" from "malware repository packaging style" rather than purely distinguishing ransomware from benign behaviour.

**Evidence:** The top false-positive driver `STRING:!this program cannot be run in dos mode.` (w = +2.599) fires on 12/12 false positives and correlates with installer stub packaging formats common in modern goodware (see `reports/fp_analysis.md`). The feature reflects a dataset artefact rather than a true ransomware signal.

**Mitigation attempted:** Goodware expansion protocol (`docs/goodware_protocol.md`) specifies multi-source diversification (winget, Chocolatey, enterprise tools, portable apps) for future Track B work. Cost-sensitive weighting (CW=1.5) partially compensates within Track A.

### 2.2 Temporal Skew (Paper Audit A12)

81.0% (413/510) of test goodware originates from 2023–2024, while ransomware is more temporally distributed. This creates a base-rate confounder: the 11/12 false positives concentrated in 2023–2024 software may partially reflect temporal distribution shift rather than an inherent model weakness.

**Mitigation attempted:** Concept drift analysis (T-P3-01, AUT = 98.54%) quantifies the monotonic FPR growth. Calibrated threshold tuning at θ = 0.90 achieves < 1% FPR at the cost of 6% recall drop (see ablation in `reports/ablations.md`).

### 2.3 Class Imbalance in Family Classification

The 65-class family task has extreme long-tail imbalance: the largest family (pajetbin) has 134 test samples while 22 families have ≤ 3 samples each. Balanced accuracy of 51.53% (v2) reflects this — rare families remain difficult to identify precisely. Macro-F1 actually drops slightly (35.96% → 33.64%) because class weighting disperses false positives across rare families.

---

## 3. RanSMAP Data Limitations

### 3.1 Small Family Coverage

RanSMAP contains only **6 ransomware families** (Conti, Darkside, LockBit, REvil, Ryuk, WannaCry) and **6 benign applications** (AESCrypt, Firefox, Idle, Office, SDelete, Zip). This is a narrow slice of the ransomware ecosystem:

- Missing: modern strains (BlackCat/ALPHV, Hive, Royal, Play, Akira, Rhysida) that emerged post-2022.
- Missing: ransomware targeting non-Windows systems or using novel encryption strategies.
- Missing: diverse benign workloads (database servers, backup software, video encoding, developer IDEs) that may generate high-entropy I/O patterns similar to ransomware.

**Impact on streaming results:** The 100% catch rate and 0.00 FA/hour (EWMA Conservative) may not generalise to unseen families or diverse benign workloads. The AESCrypt false-alarm issue (resolved by the two-stage architecture) hints that other benign encryption tools could pose similar challenges.

### 3.2 Hardware-Specific I/O Patterns

RanSMAP executions were captured on specific hardware (Celeron/i3 with standard ATA drives). Modern NVMe SSDs, RAID arrays, and virtualised storage exhibit different I/O latency profiles, burst characteristics, and LBA locality patterns. Features like `lba_sequential_frac` and `burst_count` may behave differently on production hardware.

### 3.3 Short Execution Durations

RanSMAP executions are typically 120 seconds. Some ransomware (notably those with delayed execution, anti-analysis sleep loops, or multi-stage payloads) may not exhibit encryption behaviour within this window. Our streaming TTD metrics assume encryption begins within the observation period.

---

## 4. VirusTotal First-Submission Date as Temporal Proxy

The temporal split protocol (D-007) uses VirusTotal first-submission date as a proxy for "when the sample appeared in the wild." This proxy has known weaknesses:

| Issue | Description | Severity |
|---|---|---|
| **Late submission** | A sample may circulate for months/years before anyone submits it to VT | Medium — biases temporal ordering |
| **Bulk uploads** | Researchers or AV vendors may bulk-submit historical samples, creating artificial date clustering | Medium |
| **Resubmission** | Slightly modified variants may get new submission dates despite being functionally identical | Low |
| **Missing dates** | Some samples may lack VT metadata entirely | Low (MLRan metadata is relatively complete) |

**Impact:** The chronological train/test split may not perfectly reflect real-world deployment order. However, this is the best available proxy without operational deployment logs, and the paper itself uses the same approach.

---

## 5. Feature Space Limitations

### 5.1 RFE Selection on Test Set (Paper Audit A1)

The paper's RFE feature selection (Algorithm 2, line 17) evaluates candidate feature subsets using test-set balanced accuracy. This is a form of test-set snooping. While we reproduced the paper's exact 483-feature set for comparability, the selected features may be optimistically tuned to the specific test distribution.

**Mitigation:** T-P1-04 (re-running RFE within training only) is BLOCKED because the full 24,162 MI-filtered features are not publicly released. This remains an open limitation.

### 5.2 Binary Feature Representation

The 483 RFE features are binary (presence/absence). This loses count and frequency information — e.g., a sample calling `NtAllocateVirtualMemory` once is indistinguishable from one calling it 10,000 times. Frequency, sequence, and timing information would strengthen discrimination but requires the full 6.4M feature set or raw Cuckoo reports.

### 5.3 Static + Dynamic Feature Entanglement

The MLRan feature set combines static PE metadata (strings, sections, imports) with dynamic behaviour (API calls, signatures). Static features are easier for attackers to manipulate (see adversarial analysis in `reports/adversarial_robustness.md`). The adversarial threat model (D-006) documents the asymmetric capability, but Track A cannot separate the contribution of each group without raw feature engineering.

---

## 6. Sandbox Realism

### 6.1 Sandbox Evasion (Paper Audit A14, `reports/execution_failures.md`)

The MLRan paper reports significant execution failures/dropouts per source (e.g., MOTIF 443→426, MarauderMap 621→575, curated 785→777, Software Informer 2696→2550). Samples that evade or crash in the sandbox are excluded from the dataset, creating survivorship bias — the model is trained and tested only on samples that _successfully executed_ in Cuckoo. Evasive malware is systematically absent.

**Impact:** Reported detection rates (98.18% BalAcc) are upper bounds on real-world performance against evasion-aware adversaries.

### 6.2 Win7 Environment

MLRan's Cuckoo sandbox runs Windows 7. Modern ransomware targets Windows 10/11 with different API surfaces (e.g., newer NTAPI calls, WSL, PowerShell 7, .NET 6+, AMSI hooks). Features extracted from Win7 execution may miss behaviour that only manifests on modern OS versions.

### 6.3 No Human-Activity Simulation

Many modern ransomware families check for user activity before executing (mouse movement, recent documents, running applications). Bare-metal sandbox execution without realistic human-activity simulation may trigger different (typically more aggressive) ransomware behaviour than would occur on a real user's machine.

---

## 7. Adversarial Robustness Caveats

### 7.1 Feature-Space Only Attacks

Our adversarial evaluation (E-070, E-071) perturbs **feature vectors**, not actual malware binaries. The evasion rates reported (e.g., 96.3% at budget 5 for gradient attack) represent mathematical worst-cases. Converting a feature-space perturbation into a real binary modification is non-trivial and may be infeasible for some features (e.g., removing entropy from an encrypted payload).

### 7.2 No Adaptive Adversary

The gradient-guided greedy attack assumes the adversary has **white-box access** to the model weights. Real-world adversaries typically have black-box access at most. Our reported evasion rates are therefore conservative upper bounds on attacker capability.

### 7.3 Limited Hardening Evaluation

Adversarial training (E-071) improves robustness at budget 5 (+42.4% defense gain) but saturates at budget ≥ 20. More sophisticated defenses (randomised smoothing, ensemble diversity, input detection) were not evaluated due to scope constraints (D-009).

---

## 8. Reproducibility Concerns

| Aspect | Status | Note |
|---|---|---|
| **Random seed** | Fixed (seed=42) | All scikit-learn, LightGBM, XGBoost, numpy operations use this seed |
| **Data versioning** | SHA256 hashes in `data/README.md` | Vendored MLRan files verified against upstream |
| **Dependency pinning** | `requirements.txt` with exact versions | Tested on Python 3.11 |
| **Automated reproduction** | `python scripts/reproduce_all.py` | Regenerates master tables from tracked experiments |
| **Test suite** | 45/45 tests passing (`pytest -v`) | Covers data loading, evaluation, models, explainability, dashboard |
| **RanSMAP availability** | GitHub raw download | 32 GB full clone not needed; selective download via `scripts/download_ransmap.py` |
| **Full 6.4M features** | NOT public | Upstream MLRan repo (`5_mlran_dataset/README.md`) confirms pending release |

---

## 9. Summary of Key Threats to Validity

| Threat | Category | Severity | Mitigation in This Work | Residual Risk |
|---|---|---|---|---|
| Source bifurcation (A14) | Construct validity | **High** | Goodware protocol, cost-weighting, FP attribution | Model partially learns source artefacts |
| Small RanSMAP families | External validity | **High** | LOFO evaluation, two-stage architecture | Claims limited to 6+6 classes |
| VT first-submission proxy | Internal validity | **Medium** | Best available; same as paper | Temporal ordering may be noisy |
| RFE test-set snooping (A1) | Internal validity | **Medium** | Acknowledged; leak-free protocol for all _our_ decisions | Paper's 483 features may be optimistic |
| Sandbox evasion survivorship | External validity | **Medium** | Dropout rates documented | Evasive samples systematically absent |
| Win7 OS only | External validity | **Medium** | Track B designed but not executed | Modern OS behaviour unknown |
| Feature-space adversarial only | Construct validity | **Medium** | Asymmetric threat model (D-006) | Real-world evasion gap unknown |
| Binary features (no counts/timing) | Construct validity | **Low** | RanSMAP time-series supplements | Full feature set not public |

---

## 10. Recommendations for Future Work

1. **Execute Track B:** Re-run samples on Win10/11 with modern hardware, human-activity simulation, and extended timeouts. This is the single most impactful improvement.
2. **Diversify goodware sources:** Implement the goodware expansion protocol (`docs/goodware_protocol.md`) to break source bifurcation.
3. **Re-run RFE within training only** once the full 6.4M feature set is publicly released.
4. **Expand RanSMAP families:** Include modern ransomware (BlackCat, Hive, Royal) and diverse benign workloads (databases, backup tools, media encoders).
5. **Adaptive adversarial evaluation:** Test against query-based black-box attacks and transferability attacks across model architectures.
6. **Longitudinal deployment study:** Evaluate the model on a real network over weeks/months to measure true FPR and TTD in production.

---
*Limitations analysis compiled for Task T-P9-03 (Kalyani / Antigravity).*
