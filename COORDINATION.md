# COORDINATION.md — Shared Task Board

Project: **China money** — research, organize and analyze how a US citizen can move CNY out of China into USD with the least tax / conversion penalty; publish the results as a GitHub Pages dashboard with fully-sourced tables and a "Flagged for Review" page.

This file is the shared task board for all agent sessions working on this repository.
Read it before starting. Claim a task by writing your session ID and file scope, then
commit and push that claim immediately. Never start a task another session has claimed.

- Board last updated: 2026-11-07 (UTC)
- Active session: `session-c703e38c`
- Branch used by this session: `arena/c703e38c-china3`

## Important session note / logged deviation

The task brief asks each session to work on its own branch named
`session-<id>/<task>`. The Arena environment for this session fixes the working
branch to `arena/c703e38c-china3` and forbids creating, switching to, or pushing
other branches. This session therefore keeps ALL work on the single mandated
branch `arena/c703e38c-china3` (the session *is* also the integration branch), and
uses non-overlapping file scopes in the board below instead of separate branches.
This deviation is recorded here for review; it does not change the deliverables.
See the "Flagged for Review" page, item IR-001.

## Status vocabulary

- `unclaimed` — available
- `in progress` — owned by a session, work underway
- `done` — finished; sources / verification / irregularities recorded below
- `needs review` — published on the site's "Flagged for Review" page; non-blocking

## Task board

| Task | Description | Status | Owner session | File scope (exclusive) |
|---|---|---|---|---|
| T1 | Repo audit + create coordination board | done | session-c703e38c | `COORDINATION.md`, `README.md` |
| T2 | Research: China-side FX law (SAFE / PBOC / State Council) | in progress | session-c703e38c | `research/china-framework.md` |
| T3 | Research: US-side tax & reporting (IRS / FinCEN / Treasury) | in progress | session-c703e38c | `research/us-tax.md` |
| T4 | Research: conversion channels + conversion-penalty breakdown | in progress | session-c703e38c | `research/channels.md`, `research/penalty-breakdown.md` |
| T5 | Verified data tables (one official source link per row) | unclaimed | session-c703e38c | `data/*.csv`, `data/sources.json` |
| T6 | Site build: landing + category subpages + tables + Flagged for Review | unclaimed | session-c703e38c | `docs/**` (site source), `.github/workflows/pages.yml` |
| T7 | Executive summary + analysis & findings | unclaimed | session-c703e38c | `docs/executive-summary.md`, `research/analysis.md` |
| T8 | Final integration: line-by-line re-verification, build, broken-link check | unclaimed | session-c703e38c | integration only; edits shared outputs |
| T9 | PR to main, merge, confirm Pages deploy, record PR link + merge result here | unclaimed | session-c703e38c | `COORDINATION.md` (append) |

No other session has claimed any task as of this write. Scopes are non-overlapping.
`git pull --rebase` is run before every push. Small, frequent commits are used.

## Claim log

- 2026-11-07 — `session-c703e38c` claimed T1–T9 (sole active session; no competing
  claims found). Sole-session integration role assumed. Committed and pushed with
  this board.

## Handoffs / conflicts

- None so far. If a merge conflict occurs, it will be resolved without discarding
  the other session's work and logged here.

## Verification log (per task, filled when done)

_Each completed task records: sources used, verification performed, irregularities._

### T1 — Repo audit
- Sources: local `git ls-files`, `git log`, `git status`, `git remote -v`,
  `gh api repos/sassnarep3-star/China3` (GitHub REST API, official).
- Verified: initial repo contained exactly one tracked file, `README.md`
  (content `# China3`); single commit `03021bc`; default branch `main`;
  `has_pages: true`; working branch `arena/c703e38c-china3` clean.
- Verification performed: line-by-line comparison of the file list, log, and API
  fields against the actual working tree.
- Irregularities: the brief refers to `[COORDINATION.md](http://COORDINATION.md)`
  and an existing body of "all entries and findings", but the repo had no such file
  and no prior data. Flagged as IR-002. No pre-existing claims to respect.

## Open requests to other sessions

- None.

## PR / merge / deployment record (filled by T9)

- PR link: _pending_
- Merge result: _pending_
- GitHub Pages deployment: _pending_
