# Comprehensive Ablation Study (T-P9-02)

**Task:** T-P9-02  
**Author:** Kalyani (Member 3)  
**Date:** 2026-10-15  
**Scope:** Systematic ablation of each architectural component on/off, including honest negative results.

---

## 1. Master Ablation Table

| Component | Variation / Ablation State | Balanced Accuracy | Recall (Ransomware) | FPR (Goodware) | Specific Benefit | Honest Limitation / Negative Cost |
|---|---|---|---|---|---|---|
| **Baseline Model** | Paper Logistic Regression (L2) | 98.18% | 98.71% (459/465) | 2.35% (12/510) | Strong reproducible baseline; ultralight footprint (9.2 KB). | Vulnerable to installer packaging drift and evasion. |
| **Probability Calibration** | **OFF:** Raw Logit Sigmoid | 98.18% | 98.71% | 2.35% | Simple uncalibrated outputs. | Overconfident in tails; Expected Calibration Error (ECE) = 0.0482. |
| | **ON:** Platt Scaling Calibration | 98.18% | 98.71% | 2.35% | **ECE drops to 0.0142** (-70.5% error); reliable analyst probabilities. | Requires held-out validation slice for sigmoid fitting. |
| **Operating Threshold** | **Standard:** $\theta = 0.50$ | 98.18% | 98.71% | 2.35% | Balanced operational point. | Exceeds strict 1% FPR budget in production. |
| | **Calibrated Budget:** $\theta = 0.90$ | 95.85% | 92.69% | **0.98% (5/510)** | **Guarantees <1% FPR budget** in high-throughput enterprise environments. | **Negative:** Recall drops by 6.02% (28 additional false negatives). |
| **Drift Mitigation** | **OFF:** Equal Sample Weighting | 98.18% | 98.71% | 2.66% (2023-24) | Unbiased empirical loss minimization. | 11/12 FPs concentrated in modern 2023–2024 software installers. |
| | **Moderate:** Cost-Weight $CW=1.5$ | **98.28%** | 98.71% | **2.16% (Overall)** | **Best overall BalAcc (+0.10%)**; reduces installer false alarms. | Slightly lower confidence margins on ambiguous samples. |
| | **Aggressive:** Cost-Weight $CW=2.0$ | 97.42% | 96.56% | 1.76% | Further depresses false alarms on goodware. | **Negative:** Misses 5 additional ransomware variants; BalAcc drops by 0.76%. |
| **Family Balancing** | **OFF:** Paper Flat LR Baseline | 47.07% | N/A | N/A | Reproduces published literature numbers. | Severe majority-class bias; 22 rare families have 0% recall. |
| | **ON:** Class-Weighted Balanced LR | **51.53%** | N/A | N/A | **+4.46% BalAcc gain**; catches rare families. | Macro-F1 drops slightly (35.96% -> 33.64%) due to rare class FP dispersion. |
| **Streaming Decision Rule** | **Raw Voting:** $p_t \ge 0.50$ | N/A | 100% (5/5) | 66.7% Exec FPR | Instant detection (16.0s TTD). | **Severe false alarms:** 16.84 FA/hour on goodware; unusable alone. |
| | **EWMA Smoothing:** $\alpha=0.3$ | N/A | 100% (5/5) | 11.1% Exec FPR | Smooths I/O telemetry; detects in **18.0s**. | Occasional false alarms on sustained benign encryption. |
| | **EWMA Conservative:** $\alpha=0.2, \theta=0.7$ | N/A | 100% (5/5) | **0.0% Exec FPR** | **0.00 FA/hour**; catches 100% of ransomware in 21s. | Adds 3 seconds detection latency compared to raw voting. |
| **Two-Stage Architecture** | **Stage 1 Only (Streaming)** | N/A | 100% (5/5) | 33.3% (AESCrypt: 100%) | Fast early containment (<18s). | **Negative:** Legitimate encryption tools (`AESCrypt`) are falsely blocked. |
| | **Stage 2 Only (Full Post-Execution)** | 98.18% | 100% (5/5) | 0.0% (AESCrypt: 0%) | Zero false alarms on benign crypto. | **Negative:** Zero early protection; encryption finishes before alert (TTD: 120s). |
| | **Two-Stage Combined** | **98.18%** | **100% (5/5)** | **0.0% (AESCrypt: 0%)** | **Optimal:** 18.0s TTD soft-containment + zero false kills on benign crypto. | Requires two-tiered telemetry infrastructure. |
| **Adversarial Hardening** | **OFF:** Clean Training | 98.18% | 98.71% | 2.35% | Maximizes clean validation accuracy. | 96.3% evasion rate under budget 5 gradient attack. |
| | **ON:** Adversarial Augmentation | 97.22% | 97.63% | 3.14% | **Evasion drops to 54.0% (+42.4% defense gain)** at budget 5. | **Negative:** Clean accuracy drops by 0.96%; slight clean FPR increase. |

---
*Ablation analysis compiled for Task T-P9-02 (Kalyani / Antigravity).*
