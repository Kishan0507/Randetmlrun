---
description: End a work session (update all memory files and commit)
---

Run the **Session END protocol** from `AGENTS.md`:
1. New top entry in `memory/04_CHANGELOG.md`.
2. Update task status in `memory/01_MASTER_PLAN.md`.
3. Update the patch entry in `memory/06_PATCH_QUEUE.md` (if any).
4. Update `memory/07_CONTRIBUTIONS.md`.
5. Log metrics in `memory/09_EXPERIMENT_LOG.md` (if any).
6. Overwrite `memory/08_HANDOFF.md`.
7. Commit: `[TASK-ID] type: summary` + `Contributed-by: <Name>`.
Then print a 5-line summary for the user.
