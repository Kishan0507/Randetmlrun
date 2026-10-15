# 06 — Patch queue (update / patch prompts from the team)

**How to use:** any teammate who wants a change writes a prompt. The agent logs it here **verbatim** (new `P-###`), implements it, verifies, and closes it.
Status: `OPEN` → `IN_PROGRESS` → `DONE` | `REJECTED` | `BLOCKED`. Agents handle OPEN/IN_PROGRESS patches before new plan work.
Quick way to give one: in Cursor/Antigravity type `/new-patch <your request>`.

## Entry template
```
## P-### | <title> | Status: OPEN
- Requested by: <name> on YYYY-MM-DD
- Prompt (verbatim): "<exact words>"
- Interpretation / scope: <what the agent understood; ask if unclear>
- Priority: low | normal | high | blocker
- Related tasks/decisions: T-P?-??, D-???
- Files expected to change: <paths>
- Plan:
  1. ...
- Implementation notes (agent fills): <what was done, files touched>
- Verification: <tests run / metrics / screenshots>
- Closed by: <name + agent/IDE> on YYYY-MM-DD
- Side effects / follow-ups: <...>
```

## Rules
- Never delete a patch. Rejected patches stay with a reason.
- If a patch conflicts with an ACCEPTED decision, the agent stops, quotes the decision, and asks the requester.
- If a patch changes the plan, the agent edits `01_MASTER_PLAN.md`, adds a `D-###`, and notes it in the changelog.
- Prefer the smallest safe change; add or update a test for every fix.

---

## Queue (newest at the bottom)

## P-001 | Investigate and Complete Dropped Tasks Across Master Plan Phases | Status: DONE
- Requested by: Kalyani (Member 3) / User on 2026-10-15
- Prompt (verbatim): "in 01_master_plan.md in some of the phases there are some tasks that are dropped please check why and complete it and if it still causes error keep teh status dropped"
- Interpretation / scope: Investigate why tasks were dropped across all phases in 01_MASTER_PLAN.md. Track B tasks (sandbox/live execution) and blocked tasks (unreleased 6.4M raw dataset) remain DROPPED/BLOCKED with verified rationale. Implement and complete feasible Track A tasks previously dropped by D-009: API sequence representations (T-P5-01), ransomware pattern/rate features (T-P5-02), native sequential time-series modeling on RanSMAP (T-P5-04), network feature design documentation (T-P6-01), and Cuckoo network feature extractor (T-P6-02) with full test suite verification.
- Priority: high
- Related tasks/decisions: T-P3-05, T-P4-06, T-P5-01..04, T-P6-01..03, T-P7-B1..B3, D-001, D-009, D-010
- Files expected to change: `src/features/sequence.py`, `src/features/network.py`, `docs/network_features.md`, `tests/test_sequence.py`, `tests/test_network.py`, `scripts/run_sequence_experiments.py`, `memory/01_MASTER_PLAN.md`, `memory/05_DECISIONS.md`, `memory/06_PATCH_QUEUE.md`, `memory/08_HANDOFF.md`
- Plan:
  1. Download all 20 Cuckoo JSON sample reports from upstream faithfulco/mlran repository.
  2. Implement `src/features/sequence.py` for T-P5-01 (n-grams n=2,3, TF-IDF, transition counts, inter-call delay time gaps) and T-P5-02 (pattern matching for file search -> open -> read/write -> rename/delete sequences and file ops rate).
  3. Implement `src/features/network.py` and `docs/network_features.md` for T-P6-01 & T-P6-02 (flow-level features from Cuckoo network section: DNS queries, distinct hosts, ports, bytes, protocol counts, failed ratio).
  4. Implement `scripts/run_sequence_experiments.py` for T-P5-04 (sequential vs window-stat models on RanSMAP native time series, logging E-051).
  5. Audit Track B tasks (T-P3-05, T-P4-06, T-P5-03, T-P6-03, T-P7-B1, T-P7-B2, T-P7-B3) to confirm they cannot run without an external isolated Windows VM/malware execution, keeping their status DROPPED as requested.
  6. Add unit tests in `tests/test_sequence.py` and `tests/test_network.py`, verify all pass.
  7. Update master plan, decisions, changelog, contributions, and handoff.
- Implementation notes (agent fills): Downloaded all 20 Cuckoo JSON reports; implemented `src/features/sequence.py` (T-P5-01, T-P5-02) and `src/features/network.py` (T-P6-02); created `docs/network_features.md` (T-P6-01); built RanSMAP sequential augmentation `src/features/sequential_ransmap.py` and experiment runner `scripts/run_sequence_experiments.py` (T-P5-04, E-051). Documented explicit audit reasons in D-010 and 01_MASTER_PLAN.md for why Track B tasks (T-P3-05, T-P4-06, T-P6-03, T-P7-B1..B3) and deep sequence NNs (T-P5-03) remain DROPPED.
- Verification: 57/57 pytest tests passing; E-051 executed (+6.31% BalAcc on LR, +2.62% BalAcc on LightGBM).
- Closed by: Kalyani (Member 3) / Antigravity on 2026-10-15
- Side effects / follow-ups: None.

