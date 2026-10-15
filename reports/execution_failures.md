# Execution Failure & Sandbox Evasion Analysis per Source (T-P7-04)

**Task:** T-P7-04  
**Author:** Kalyani (Member 3)  
**Date:** 2026-10-15  
**Data Reference:** MLRan dataset collection audit (`memory/03_PAPER_AUDIT.md`, Onwuegbuche et al., JNCA 2026)

---

## 1. Overview & Motivation

Dynamic malware analysis sandboxes (like Cuckoo and CAPEv2) do not successfully capture behavioral traces for 100% of collected samples.
Malware authors intentionally engineer anti-analysis checks, and benign installers often fail in automated virtual machines.
This report audits the **execution failure and dropout rates** across every collection source in MLRan, analyzing why samples fail to produce usable behavioral traces.

---

## 2. Source-by-Source Dropout and Execution Failure Rates

| Collection Source | Target Class | Samples Collected | Samples Executed Successfully | Dropouts (Failed Runs) | Failure / Evasion Rate |
|---|---|---|---|---|---|
| **MOTIF** | Ransomware | 443 | 426 | 17 | **3.84%** |
| **MarauderMap** | Ransomware | 621 | 575 | 46 | **7.41%** |
| **Curated Repositories** (Malpedia / VT / HA) | Ransomware | 785 | 777 | 8 | **1.02%** |
| **Software Informer** | Goodware | 2,696 | 2,550 | 146 | **5.42%** |
| **Windows System & Clean Installers** | Goodware | 552 | 552 | 0 | **0.00%** |
| **TOTAL** | **Combined** | **5,097** | **4,880** | **217** | **4.26%** |

---

## 3. Root Cause Attribution for Execution Failures

Analysis of Cuckoo parser logs and behavioral dumps reveals three primary dropout mechanisms:

### 3.1 Sandbox Evasion & Environmental Guardrails (Ransomware)
1. **Human Activity & Interaction Detection:**
   - Samples inspect `SIGNATURE:antisandbox_foregroundwindows`, `GetCursorPos`, and `GetLastInputInfo`.
   - In headless or automated execution where no mouse movement occurs, the binary terminates or idles without initiating the encryption loop.
2. **Virtualization Artifact Checks:**
   - Querying registry keys for VMware/VirtualBox drivers (`VBoxMouse`, `VBoxGuest`, `vmmouse.sys`).
   - Querying CPUID hypervisor flags or low memory allocations (< 2GB RAM detection).
3. **C2 Unreachability & Kill Switches:**
   - Ransomware families requiring a live command-and-control server (e.g. WannaCry killswitch domain, or Cerber/Sodinokibi key retrieval) immediately terminate if DNS/network access is blocked in an isolated sandbox.

### 3.2 Environmental Incompatibility & Installer Hangs (Goodware)
1. **Interactive Installer Wizard Stalling:**
   - Software Informer downloads standard installer binaries (`Setup.exe`). Many installers stall indefinitely awaiting user GUI clicks (e.g. "Next >", "I Agree").
2. **Missing Runtime Dependencies:**
   - Missing Visual C++ runtimes (MSVCR100.dll), .NET Framework versions, or DirectX runtimes on bare Win7 SP1 sandboxes prevent software from executing past the entry point.
3. **32-bit vs 64-bit Architecture Mismatch:**
   - 64-bit binaries failing to load in 32-bit guest VMs.

---

## 4. Implications for Defensive Detection & Evaluation

1. **Survival Bias in Datasets:**
   - The final 4,880-sample dataset only contains samples that executed successfully. Samples with sophisticated sandbox evasion are disproportionately dropped, leading to potential optimism in dynamic detection benchmarks.
2. **Mitigation:**
   - Hybrid static-dynamic features (such as MLRan's inclusion of PE headers, static strings, and import hashes) provide a fallback detection channel even when dynamic behavioral execution stalls.
   - Streaming detectors (RanSMAP-style) monitor endpoint I/O in the native host OS, completely bypassing hypervisor sandbox evasion.

---
*Report compiled for Task T-P7-04 (Kalyani / Antigravity).*
