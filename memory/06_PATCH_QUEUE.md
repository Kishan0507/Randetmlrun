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

_(empty — first patch will be P-001)_
