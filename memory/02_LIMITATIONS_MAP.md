# 02 — Limitations of the MLRan paper → what we do → how we prove it

| # | Limitation in the paper | Our improvement | Tasks | Proof metric |
|---|---|---|---|---|
| L1 | **Delayed detection.** Classifies a full 120 s Cuckoo report; no latency or early-detection evaluation | Early detection: windowed time series (RanSMAP), prefix-truncated reports, streaming alert rule, two-stage system | T-P4-01…07 | detection rate @ t s, time-to-detection, files lost before alert |
| L2 | **Outdated environment** (Windows 7, Cuckoo 2.0.7); modern Windows 10/11 with Defender/ETW may behave differently | Track B: Win10/11 sandbox re-run of a stratified subset; cross-OS train/test; use RanSMAP (Win10) in Track A | T-P7-B1…B3, T-P4-02 | cross-OS degradation table |
| L3 | **Concept drift visible, not addressed.** 11 of 12 false positives are 2023–24 goodware | Drift analysis (AUT, per-year), recency weighting, sliding-window retrain, recalibration, drift detector, new goodware | T-P3-01…05 | FPR on 2023–24 goodware, AUT |
| L4 | **Family classification weak** (≈82% accuracy but ≈47% balanced accuracy) | Hierarchical/class-weighted models, macro-F1 objective, unknown-family rejection | T-P2-03, T-P2-04 | balanced acc., macro-F1, per-family recall |
| L5 | **Network features dropped** (0 of 483 survived; IP/domain presence too granular) | Flow-level aggregate features | T-P6-01…03 | # network features surviving selection; gain in bal. acc. |
| L6 | **Binary presence features ignore order and timing** | Sequence n-grams, transition counts, inter-call timing, sequence NN; pre-encryption phase features | T-P5-01…04 | gain over presence-only baseline (with CI) |
| L7 | **Goodware from a single source** (Software Informer), no enterprise software; narrow tuning grid | Goodware expansion protocol and collection; wider models and grids | T-P3-04, T-P3-05, T-P2-01 | FPR, source-held-out evaluation |
| L8 | **No adversarial testing; no report of sandbox-evasion failures** | Feature-space attacks and hardening; per-source execution-failure report | T-P7-01…04 | evasion rate vs budget; dropout table |
| L9 | **Test-set used to choose feature count** (RFE 2% picked by test balanced accuracy — see audit A1) | Leak-free protocol with chronological validation | T-P1-03, T-P1-04 | honest vs paper number |
| L10 | **Typos / inconsistent numbers** in paper tables | Audit before citing any number | T-P0-05 | audit statuses |
| L11 | **Reproducibility gap:** full 6.4M-feature data not yet public; only the 483-feature set is | Work on released set; re-check upstream; Track B for raw data | T-P0-03, Track B | documented in D-003 |
| L12 | **No usable tool** — research pipeline only | Explainable dashboard with replay + alerts | T-P8-01…06 | usability findings, end-to-end demo |
