# Early Ransomware Detection (ML + explainable dashboard)

Team project built on the MLRan dataset (Onwuegbuche et al., JNCA 250 (2026) 104475; https://github.com/faithfulco/mlran, MIT) and RanSMAP (https://github.com/manabu-hirano/RanSMAP).

**Idea:** the MLRan paper shows ML can detect ransomware from behaviour. We make that detection earlier, more accurate on recent software, harder to evade, and usable through a dashboard.

## For humans
1. `git clone` this repo, create a branch `feat/<yourname>/<task-id>`.
2. Open the folder in Cursor or Antigravity.
3. Run `/start-session`, tell the agent your name.
4. Give work as a task ID from `memory/01_MASTER_PLAN.md` or as a patch (`/new-patch ...`).
5. Run `/end-session` before you stop. Commit and push.

## For AI agents
Read `AGENTS.md` first. All project memory lives in `memory/`.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

## Safety
No malware, no evasion payloads, no binaries in this repo. Adversarial work is feature-space only. See `AGENTS.md` section 4.

## Credits
Upstream: MLRan authors (F. C. Onwuegbuche, S. O. Adelodun, A. D. Jurcut, L. Pasquale) and RanSMAP authors (M. Hirano, R. Kobayashi). Our team: see `memory/07_CONTRIBUTIONS.md`.
