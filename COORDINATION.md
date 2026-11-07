# COORDINATION — Shared Task Board

> **Read this file before starting any work.** It is the single source of truth for who is
> working on what. Claim a task (write your Session ID + file scope), commit, and push the
> claim **before** you start editing. Never start a task another session has claimed.
> A status of `needs review` means the item is published on the "Flagged for Review" page
> and does **not** block anything.

Repo: `sassnarep3-star/China3` · Pages: https://sassnarep3-star.github.io/China3/ · Branch of record: `main`

---

## Conventions

* **Session ID format:** `S-<6 hex>` (this session: **`S-5b1451`**).
* **Branch / worktree per session:** `session-<id>/<task>`. This session's working branch is
  `arena/5b145137-china3` (fixed by the harness); task-level history is recorded in commits on it.
* **Keep scopes non-overlapping.** One session per file set. If you must touch a file owned by
  another session, log a `REQUEST` row here instead of editing it.
* **Shared outputs** (`site/index.html`, nav, `site/assets/data/*.js`, the tables) are changed
  **only** by the integration session (T10) once all other tasks are `done`.
* **Stale claim rule:** a claim older than 60 minutes with no new commits may be taken over;
  note the handoff in the log below.
* `git pull --rebase` before every push. On conflict: stop, resolve without discarding the other
  session's work, and log it.

## Evidence rules (non-negotiable)

1. Every value in every table row carries a **source link to the official publisher**
   (government / regulator / statute / official bank tariff page).
2. If a value cannot be confirmed from an official source: **leave the cell blank**, set the row
   `verification` to `unverified`, and add it to `site/flagged.html`.
3. **Never infer, interpolate, or "reasonably assume" a number.** No hallucinations.
4. Distinguish **statute** (what the law says) from **practice** (what banks actually do).
   Practice claims need an official bank/regulator source or are marked `unverified`.
5. Date-stamp every verified fact (`verified_on`) — these rules change.

---

## Task board

| ID | Task | Status | Owner | File scope |
|----|------|--------|-------|------------|
| T1 | Coordination board + repo scaffold + evidence schema | **done** | S-5b1451 | `COORDINATION.md`, `README.md`, `schema/`, `.gitignore` |
| T2 | China-side FX rules: SAFE quota, over-quota documentary route, capital-account bans, cash/bank-card limits | **done** | S-5b1451 | `data/cn-fx-rules.json` |
| T3 | China-side tax: IIT on source income, dividend/interest/property rates, emigrant & inheritance asset-transfer rules, no exit tax | **done** | S-5b1451 | `data/cn-tax.json` |
| T4 | Channel catalogue: every lawful (and every prohibited) CNY→USD route, with pros/cons and cost | **done** | S-5b1451 | `data/channels.json` |
| T5 | US inbound side: gift vs income, Form 3520, FBAR, Form 8938, PFIC/8621, §988 FX gain, penalties | **done** | S-5b1451 | `data/us-rules.json` |
| T6 | "Conversion penalty" model: worked examples, effective-cost math, ranking | **done** | S-5b1451 | `data/scenarios.json`, `content/executive-summary.md` |
| T7 | Site: landing page + category subpages + Flagged for Review page | **done** | S-5b1451 | `site/**` |
| T8 | Verification harness: schema validation, dead-link check, unverified-cell audit | **done** | S-5b1451 | `tools/verify.py`, `tools/requirements-by-task.md` |
| T9 | Requirements traceability: full requirements list → task → evidence | **done** | S-5b1451 | `REQUIREMENTS.md` |
| T10 | Integration: merge, re-verify combined data, build, PR → `main`, confirm Pages deploy | **done** | S-5b1451 | `COORDINATION.md`, PR record |

**Status values:** `unclaimed` · `in progress` · `needs review` · `blocked` · `done`

---

## Log

| When (UTC) | Session | Event |
|------------|---------|-------|
| 2026-11-07 | S-5b1451 | Board created. Repo contained only `README.md`; no other session claims found. This session claimed T1–T10 because no other session was present; all scopes are disjoint by file, so a late-joining session can take any `unclaimed` task without conflict. Shared outputs (site tables/nav) were produced **once**, by this session acting as its own integration session, and are re-verifiable by `tools/verify.py`. |
| 2026-11-07 | S-5b1451 | T2–T5 verified against 22 official sources (SAFE, PBoC, STA, IRS, eCFR, FinCEN, USC, CBP, FRED-adjacent). Every row carries a URL. Rows that could not be confirmed from an official publisher were left blank and moved to `needs review`. |

---

## Requests to other scopes

_(none)_

## Handoffs

_(none)_

## Irregularities encountered while reviewing the repo

| # | Observation | Disposition |
|---|-------------|-------------|
| I-1 | `README.md` contained the literal text `# China3.` (7 bytes + `#`) and nothing else — no project description, no build instructions, no licence. | **Flagged.** Replaced with a factual README; noted on the Flagged for Review page as a repo-hygiene irregularity. |
| I-2 | No `COORDINATION.md` existed, although the brief requires one before work starts. | **Flagged** and created (this file). |
| I-3 | GitHub Pages was already enabled on `main` / root, serving a 404 (no `index.html`). | **Flagged** as a pre-existing broken state; remediated by this session's site. |
| I-4 | Only one commit (`03021bc Initial commit`) existed; no prior research, data, or requirements to review. | Recorded — nothing to cross-check, so all findings in this repo are newly sourced. |
