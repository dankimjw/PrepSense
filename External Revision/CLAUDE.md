---

````markdown
# CLAUDE.md · Project “PrepSense”

This file is automatically loaded by all Claude Code instances—**follow it exactly**.

---

## 1 Multi‑Instance Collaboration  (PrepSense / bugfix / testzone)

**At every startup, _git pull_, or _git checkout_:**

```bash
cat WORKTREE_NOTES_*.md   # sync knowledge
````

| Worktree                        | Write notes to               |
| ------------------------------- | ---------------------------- |
| `/PrepSense`                    | `WORKTREE_NOTES_MAIN.md`     |
| `/PrepSense-worktrees/bugfix`   | `WORKTREE_NOTES_BUGFIX.md`   |
| `/PrepSense-worktrees/testzone` | `WORKTREE_NOTES_TESTZONE.md` |

**Remember** – `CLAUDE.md` and all notes are symlink‑shared; update once, propagate everywhere.

---

## 2 Core Engineering Rules (non‑negotiable)

1. **Plan → Test → Code.**
   *Write or extend failing tests first, then code the minimal fix.*

2. **Touch only what the task names.**
   Cross‑file edits? Explain why.

3. **Never invent APIs or behaviour.**
   If unsure, say “I’m not sure” and/or fetch docs via Context7.

4. **No placeholders or TODOs in production code.**

5. **Keep existing behaviour intact** unless explicitly told otherwise.

---

## 3 Workflow Checklist

> Use this loop for every task.

| Step            | Command / Action                                               |
| --------------- | -------------------------------------------------------------- |
| 1 · Plan        | List files/functions to change & tests to add.                 |
| 2 · Write tests | `pytest -k` / `npm test` – confirm they **fail**.              |
| 3 · Implement   | Minimal edits; run linter & type‑checker.                      |
| 4 · Green tests | Re‑run full suite; `./quick_check.sh`.                         |
| 5 · Commit      | One logical change, descriptive message **without AI credit**. |
| 6 · Notes       | Append decisions to your `WORKTREE_NOTES_*.md`.                |
| 7 · /clear      | Reset context before next task.                                |

---

## 4 Git & Commit Policy

* **Never mention “Claude”, “AI”, or any assistant** in commit titles, bodies, or trailers.
* **Only** Daniel Kim appears as author.
* No “Co‑authored‑by” lines.

---

## 5 Safe Commands & Tools

* **Testing**  `pytest`, `jest`, `npm run test:ci`
* **Type/Lint**  `mypy`, `eslint`, `tsc --noEmit`
* **Health**  `./quick_check.sh` (30 s) · `python check_app_health.py` (2 min)
* **GitHub**  `gh issue`, `gh pr`
* **MCP servers** (pre‑configured): `ios-simulator`, `mobile`, `memory`, `Context7`, `Apidog`, `PostgreSQL`.

---

## 6 Dependency & Environment Rules

* Install via `pip install …` or `npm install …` **before** importing.
* Update `requirements.txt` or `package.json` automatically (no manual edits).
* The single source of truth for secrets is `PrepSense/.env`.

---

## 7 Testing Requirements (high‑level)

| Area               | Must test                                                               |
| ------------------ | ----------------------------------------------------------------------- |
| **Backend**        | FastAPI endpoints, DB CRUD, external API wrappers, error paths.         |
| **Frontend**       | React‑Native components (unit), key navigation flows, modal visibility. |
| **E2E (optional)** | critical flows via Detox or MCP simulators.                             |

Detailed examples live in `/docs/testing_guides/*.md`.

---

## 8 Project‑Specific Reminders

* PostgreSQL runs in **GCP Cloud SQL** – never localhost.
* Health endpoint: `GET /api/v1/health`
* Keep data backwards‑compatible; run migrations through CI.

---

## 9 Golden Safety Nets

* **If any command fails → stop, ask.**
* **If any rule conflicts with a direct human instruction → clarify first.**