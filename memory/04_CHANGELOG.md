# 04 — Changelog (newest on top, append at the TOP)

## Entry template
```
## C-### | YYYY-MM-DD | <Task/Patch IDs>
- Contributor (human): <name>
- Agent / IDE: <Cursor | Antigravity | none> (<model if known>)
- What changed: <1–5 bullets, files touched>
- Why: <reason / plan reference>
- Verification: <tests run, metrics, screenshots>
- Plan impact: <none | tasks added/changed>
- Follow-ups: <what the next person should do>
```

## C-002 | 2026-10-14 | T-P0-01, T-P0-02, T-P0-03, T-P0-04
- Contributor (human): Kishan (dkkishangowda@gmail.com)
- Agent / IDE: Antigravity
- What changed:
  - Initialized git repo, verified and pinned exact versions in `requirements.txt` (torch excluded).
  - Passed initial smoke test with pytest.
  - Inspected upstream RanSMAP repo: confirmed CC BY-ND 4.0 licence, 1,970 executions across 6 ransomware and 6 benign families, ~32 GB size, documented structure in D-002.
  - Checked upstream MLRan repo: confirmed full 6.4M feature dataset is not public yet, documented in D-003.
  - Vendored MLRan 483-feature RFE subset and metadata in `data/raw/mlran/` and recorded SHA256 hashes in `data/README.md`.
- Why: Environment setup and data access (Phase 0).
- Verification: pytest passed, SHA256 hashes verified, RanSMAP API inspect confirmed.
- Plan impact: T-P0-01..T-P0-04 marked DONE.
- Follow-ups: Proceed to T-P0-06 (MLRan loader) and T-P0-05 (paper audit).

---

## C-001 | 2026-10-13 | scaffold
- Contributor (human): Member 1 (project lead) — replace with real name
- Agent / IDE: Claude (chat) generated this scaffold
- What changed: created `AGENTS.md`, IDE rule files, `memory/` brain (plan, limitations map, paper audit, patch queue, ledgers, prompt library), repo skeleton.
- Why: shared memory for multi-person, multi-agent work (Cursor + Antigravity).
- Verification: files present; MLRan repo layout and released-data facts checked by cloning upstream (RanSMAP clone failed → T-P0-02).
- Plan impact: initial plan created (phases 0–10).
- Follow-ups: fill `07_CONTRIBUTIONS.md` with team names, run T-P0-01.
