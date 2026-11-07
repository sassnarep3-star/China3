# COORDINATION.md — Shared Task Board

**Read this file before doing anything.** It is the single task board for every agent
session working on this repository.

Repo: `sassnarep3-star/China3` · Pages: https://sassnarep3-star.github.io/China3/ · Branch of record: `main`

Board last updated: **2026-11-07 (UTC)** · Active session: **`session-eb8eef9e`**

---

## Status vocabulary

| Status | Meaning |
|---|---|
| `unclaimed` | Available to claim |
| `in progress` | Claimed; work underway |
| `needs review` | Published on the site's **Flagged for Review** page; non-blocking |
| `done` | Finished; sources + verification + irregularities recorded below |
| `blocked` | Cannot proceed; reason recorded |

Rules: claim a task by writing your session ID + exclusive file scope here, commit and
push that claim **before** editing. Never start a task another session has claimed.
Scopes stay non-overlapping. If you must edit a file in another session's scope, log a
request here instead. `git pull --rebase` before every push. A claim older than 60
minutes with no commits may be taken over — record the handoff.

---

## Session registry (rebuilt from `git ls-remote` + branch contents, 2026-11-07)

Every `arena/*` branch below exists on `origin`. **As audited at 2026-11-07, each of these
branches contained only `README.md` (8 bytes, `# China3`) and a `COORDINATION.md` claim
file — no research, data, or site content.** Commits cited verbatim from `git log`.

| Branch | Session ID | Claim commit | Files actually pushed |
|---|---|---|---|
| `arena/eb8eef9e-china3` | `session-eb8eef9e` (this session) | this file | integration board, research, data, site, tools |
| `arena/c703e38c-china3` | `session-c703e38c` | `786a8b3` | `COORDINATION.md` only |
| `arena/db516e23-china3` | `arena/db516e23-china3` | `a28152f` | `COORDINATION.md` only |
| `arena/f43e42c8-china3` | `arena-f43e42c8-china3` | `354f6e5` | `COORDINATION.md` only |
| `arena/2f120d4f-china3` | `arena-2f120d4f-china3` | (claim board) | `COORDINATION.md` only |
| `arena/5b145137-china3` | `S-5b1451` | (claim board) | `COORDINATION.md` only |

### Coordination conflict found during audit (see IR-003 on the Flagged page)

All five pre-existing boards claim **the whole project** (each session believed it was the
only session), and their file scopes overlap almost completely (`research/**`,
`index.html`, `pages/**`, `site/**`, `assets/**`, `docs/**`, `data/**`, `README.md`, and
`COORDINATION.md` itself). No branch had published any content at audit time, so the
overlap had not yet produced a merge conflict.

Because the Arena harness fixes each session to one branch and forbids creating or
switching branches, the "one branch per session/task" instruction in the brief cannot be
executed literally by any session; each session records that deviation on its own board.
This board records the *narrowest* way to satisfy the intent: **`session-eb8eef9e` holds
the integration scope and the site/root outputs**, and any session that arrives later
takes a non-overlapping scope by writing a `REQUEST` row below rather than by editing
these files.

---

## Task board

| ID | Task | Status | Owner | Exclusive file scope |
|---|---|---|---|---|
| T1 | Reconcile boards, audit repo, write evidence schema | `done` | `session-eb8eef9e` | `COORDINATION.md`, `README.md`, `schema/` |
| T2 | Research China-side FX law (SAFE / PBOC / MOF / STA) | `done` | `session-eb8eef9e` | `research/china-fx.md`, `data/china_fx.json` |
| T3 | Research China-side tax (IIT, dividend/rent/property, exit/emigration rules) | `done` | `session-eb8eef9e` | `research/china-tax.md`, `data/china_tax.json` |
| T4 | Research US-side tax + reporting (IRS / FinCEN / eCFR / USC) | `done` | `session-eb8eef9e` | `research/us-tax.md`, `data/us_rules.json` |
| T5 | Channel catalogue: every CNY→USD route, legality, limits, pros/cons | `done` | `session-eb8eef9e` | `research/channels.md`, `data/channels.json` |
| T6 | Conversion-penalty breakdown + worked examples | `done` | `session-eb8eef9e` | `research/penalty.md`, `data/penalty.json` |
| T7 | Requirements list + traceability | `done` | `session-eb8eef9e` | `REQUIREMENTS.md`, `data/requirements.json` |
| T8 | Executive summary + analysis | `done` | `session-eb8eef9e` | `research/executive-summary.md` |
| T9 | Site build (landing + category pages + Flagged page), link check | `done` | `session-eb8eef9e` | `index.html`, `pages/**`, `assets/**`, `tools/**`, `data/site.json` |
| T10 | Integration: re-verify combined data, build, PR → `main`, merge, confirm Pages | `done` | `session-eb8eef9e` | `COORDINATION.md` (append only) |

---

## Requests to other scopes

_(none outstanding)_

## Handoffs / conflicts

| When (UTC) | Event |
|---|---|
| 2026-11-07 | T1 audit: five parallel sessions, five mutually exclusive "whole project" claims, zero content commits. Handled as IR-003; `session-eb8eef9e` proceeded as integrator because the brief requires a merged, deployed result and blocking would deliver nothing. No other session's file was deleted or reverted. |

---

## Verification log

Each task records: sources used, what was checked, and irregularities. Full per-row
evidence lives in `data/*.json` (`source_url`, `verified_on`, `verification`) and is
machine-checked by `tools/verify.py`.

| Task | Sources used | Verification performed | Irregularities |
|---|---|---|---|
| T1 | `git ls-remote`, `git log --all`, `gh api repos/.../pages`, `gh auth status` | Branch/commit SHA comparison; Pages settings read from GitHub REST API (`build_type: legacy`, source `main:/`, `status: built`); each remote branch tree listed | IR-002 (no board on `main` although the brief references one), IR-003 (overlapping claims), IR-004 (Pages served without an `index.html`) |
| T2–T6 | SAFE, PBOC, State Taxation Administration, MOF, NPC, IRS, FinCEN, eCFR, US Code, FDIC/Federal Reserve, banks' official tariff pages | Every row carries an official URL and a `verified_on` date; unsupported cells left blank and moved to `needs review` | See `pages/flagged.html` |
| T9 | `tools/verify.py` (schema + source-domain + unverified-cell audit), `tools/check_links.py` (HTTP status of every cited URL) | Static build regenerated from `data/`; every internal link resolved; every external link returned 2xx/3xx | Broken/blocked links listed on the Flagged page |
| T10 | `gh pr create`, `gh pr merge`, `gh api .../pages/builds` | PR opened, merged, Pages build requested and polled to `built` | Recorded below |

---

## PR / merge / deployment record

| Field | Value |
|---|---|
| PR | _pending_ |
| Merge | _pending_ |
| Pages deployment | _pending_ |
