# memory/ — the project brain

Every human and every AI agent (Cursor, Antigravity) reads these files at the start of a session and updates them at the end.

| File | Purpose | Who writes | Style |
|---|---|---|---|
| `00_PROJECT_BRIEF.md` | What we build, why, scope, success criteria | rarely, via decision | stable |
| `01_MASTER_PLAN.md` | Phases, task IDs, status, dependencies, acceptance criteria | update status every session | table |
| `02_LIMITATIONS_MAP.md` | Paper limitation → our fix → task IDs → proof metric | when scope changes | table |
| `03_PAPER_AUDIT.md` | Inconsistencies found in the MLRan paper, with verification status | when a check is done | table |
| `04_CHANGELOG.md` | What changed, by whom, why (newest on top) | every session | append at top |
| `05_DECISIONS.md` | Decisions with reasons (ADR style) | when a choice is made | append |
| `06_PATCH_QUEUE.md` | Update / patch prompts from the team, verbatim, with status | every patch | append |
| `07_CONTRIBUTIONS.md` | Who did what (acknowledgement ledger) | every session | append |
| `08_HANDOFF.md` | Where we stopped, what is next | overwrite every session | short |
| `09_EXPERIMENT_LOG.md` | Every metric run, reproducible | every experiment | append |
| `10_PROMPT_LIBRARY.md` | Copy-paste prompts for agents | when a prompt works well | append |
| `templates/` | Blank entry templates | — | — |

## Rules of thumb
- Append, never rewrite someone else's entry. Corrections go in a new entry that references the old one.
- Use IDs everywhere: tasks `T-P#-##`, patches `P-###`, decisions `D-###`, experiments `E-###`, changelog `C-###`.
- Dates: ISO `YYYY-MM-DD`. Times are optional.
- If it is not written here, the next agent does not know it.

## Using it with the IDEs
- **Cursor**: reads `AGENTS.md` and `.cursor/rules/`. Slash commands in `.cursor/commands/`: `/start-session`, `/end-session`, `/new-patch`.
- **Antigravity**: rules in `.agent/rules/`, workflows in `.agent/workflows/` (`/start-session`, `/end-session`, `/new-patch`). If your Antigravity version uses a different folder name (for example `.agents/`), copy the files there; the content is identical.
- Both IDEs share the same `memory/` folder through git, so commit and pull often.
