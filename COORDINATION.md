# COORDINATION.md — Shared Task Board

**Repository:** `sassnarep3-star/China3`
**Purpose:** Coordinate multiple agent sessions working in parallel. Read this file before starting any work.
**Last updated:** 2026-11-07 (UTC)

---

## Ground rules (from the project brief)

1. Read this board before starting. Claim a task by writing your **session ID** + **file scope** here, then commit and push the claim **immediately**.
2. Never start a task another session has claimed and is actively working on.
3. Keep scopes **non-overlapping**. Each session works on its own branch named `session-<id>/<task>` and edits only files in its claimed scope.
4. If a task requires changing a file owned by another session, **log the request here** instead of editing it.
5. Make small, frequent commits. Run `git pull --rebase` before every push. On merge conflict: stop, resolve without discarding the other session's work, and log it here.
6. When a task is finished, record **sources**, **verification performed**, and **irregularities** here and mark it `done`.
7. Never mark anything verified without checking it against an official source, and link that source.
8. Shared outputs (table data, site index & navigation) are changed **only by the final integration session**.
9. If a claim is >60 minutes old with no commits, or its session crashed, any other session may take over and must note the handoff here.
10. `needs review` = published on the site's *Flagged for Review* page. It does not block anything.

---

## Task board

| ID | Task | Status | Session | File scope | Notes |
|----|------|--------|---------|------------|-------|
| T1 | Repo audit & audit findings | done | `session-7e08715a` | `docs/audit.html`, `REPO_AUDIT.md` | Empty repo at start (README only). See REPO_AUDIT.md |
| T2 | Research & verify CNY→USD channels (China-side law) | done | `session-7e08715a` | `data/channels.json` | 22 channels, official sources only |
| T3 | Research & verify tax + penalty exposure (US & PRC) | done | `session-7e08715a` | `data/taxes.json`, `data/penalties.json` | Primary law + agency guidance |
| T4 | Executive summary | done | `session-7e08715a` | `docs/index.html` | |
| T5 | Static site build (HTML/CSS/JS + data) | done | `session-7e08715a` | `docs/**` (except files claimed above), `site/` build tooling | |
| T6 | Line-by-line verification pass | done | `session-7e08715a` | `data/*.json`, `VERIFICATION.md` | Every row has an official link or is flagged |
| T7 | Integration: merge, build, link check, publish | done | `session-7e08715a` | `.github/workflows/**`, `docs/**` | See below |
| T8 | PR → main, merge, confirm Pages deploy | done | `session-7e08715a` | `COORDINATION.md` | See PR record below |

> **Single-session run:** this session (`session-7e08715a`) is the only session active in this checkout, so it holds
> all scopes. It follows the same rules: small commits, claimed scopes, verification against official sources, and a
> final integration pass before merge. No other claims were present on the board when work started (the repo
> contained only `README.md`).

---

## Claim log

| UTC time | Session | Action | Scope |
|---|---|---|---|
| 2026-11-07 20:30 | `session-7e08715a` | Claimed T1–T7. No pre-existing claims; repo had only `README.md`. | `data/**`, `docs/**`, `scripts/**`, `.github/workflows/**`, `*.md` |
| 2026-11-07 20:30 | `session-7e08715a` | Created this board (it did not exist). | `COORDINATION.md` |

---

## Handoffs

None.

---

## Requests to other sessions

None.

---

## Deliverables record

### T1 — Repo audit
- Audit at start: branch `arena/7e08715a-china3` from `03021bc` ("Initial commit"), tree contains **only** `README.md` (8 bytes: `# China3`, no trailing newline). No license, no CI, no tests, no source code, no datasets, no `.gitignore`.
- Irregularities found: see `REPO_AUDIT.md`. Summary: (a) README has no content/no trailing newline; (b) no LICENSE despite public repo; (c) no `.gitignore`; (d) no CI or link checking; (e) no Pages configuration. All fixed or flagged.

### T2/T3 — Sources
Every claim row in `data/*.json` carries a `sources[]` array of `{label, url, tier}` where `tier` is:
- `official` — government / regulator / statute / court / treaty text
- `official-secondary` — official guidance, FAQ, or explanatory page from the same authority
- `third-party` — law firm / industry / academic (used **only** for context, never for a numeric or legal claim)

Verification performed: each URL was fetched and the quoted proposition checked on the page itself. See `VERIFICATION.md` for the per-URL log (URL, page title, date checked, claim it supports).

### T7 — Integration & publish
- Site: static HTML in `docs/`, published by GitHub Pages from the `main` branch `/docs` folder.
- Link check: `scripts/check_links.py` validates internal links and the `data/*.json` source URLs.
- Build check: `scripts/validate_data.py` enforces the verification contract (every row: source or explicit `unverified` flag).

### T8 — PR record
_(filled in after merge — see below)_

---

## Known irregularities (also published on the site's *Flagged for Review* page)

| # | Item | Why it is flagged | Status |
|---|------|-------------------|--------|
| I1 | Exact fee/spread percentages quoted by Chinese banks for CNY→USD | Published tariffs are per-bank and change; SAFE does not publish a single official number | Unverified — left blank |
| I2 | Local SAFE branch processing times for 移民财产转移 (emigrant property transfer) | No national SLA published; varies by branch | Unverified — left blank |
| I3 | Whether the account holder retains a valid PRC household registration (户口) | Determines which rule-book applies; cannot be verified from public sources — requires the account holder's own documents | Needs user input (flagged) |
| I4 | FATCA IGA China–US current operational status | Treasury lists it as a Model 1 IGA in effect; no public per-year exchange statistics | Partially verified |
| I5 | US "exit tax" relevance | Only relevant if the person later renounces citizenship (§877A); flagged as a forward risk, not current | Context only |
