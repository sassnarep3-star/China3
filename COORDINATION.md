# Coordination Board — China3 (money-out-of-China research)

Branch: `arena/f43e42c8-china3` (current session); `main` contains prior session work merged via PR #1 and PR #3.
Remote: https://github.com/sassnarep3-star/China3.git
Live site: https://sassnarep3-star.github.io/China3/ (GitHub Pages, deployed via Actions run #42411677212)
Session ID conventions: `<owner>-<task-id>`, e.g. `arena-f43e42c8-china3-T1`.

## Sessions involved

- `arena/dd766f7b-china3` (prior session): repository review, official-source research, executive brief dashboard (`index.html`, `routes.html`, `tax.html`, `review.html`, `sources.html`, `assets/site.css`), verification log, findings/irregularities, GitHub Pages workflow (`.github/workflows/pages.yml`), PR #1 + PR #3 merged to main, Pages deployment verified.
- `arena-f43e42c8-china3` (current session): CNY→USD conversion-methods research (`research/cny-usd-conversion-research.md`), executive summary (`docs/executive-summary.md`), dashboard subpages (`methods.html`, `china-rules.html`, `us-tax.html`, `penalties.html`, `flagged-review.html`, `style.css`), unified landing page (`index.html` integrating both sessions), PR #2 (this branch → main), Pages re-deployment verification.

## Legend
- Status: `unclaimed` | `in progress` | `done` | `needs review`
- `needs review` = item is published on the Flagged for Review page and does not block anything.
- Before starting a task: claim it here (write session ID + file scope), commit and push immediately.
- Never start a task another session has claimed. If a claim is >60 min old with no commits, any session may take over (note the handoff in the log).
- Make small, frequent commits; run `git pull --rebase` before every push.
- If a task requires changing a file owned by another session, log the request here instead of editing it.
- Shared outputs (table data, index, navigation) are changed only by the final integration session once all other tasks are done.

## Tasks (unified, both sessions)

| ID | Task | File scope | Status | Owner | Sources verified | Notes |
|----|------|------------|--------|-------|------------------|-------|
| P1 | Inspect repository and document project findings | `README.md`, `COORDINATION.md` | done | arena/dd766f7b-china3 | | Merged to main in PR #1 |
| P2 | Build official-source-backed China-to-US funds transfer dashboard | `index.html`, `routes.html`, `tax.html`, `review.html`, `sources.html`, `assets/site.css` | done | arena/dd766f7b-china3 | SAFE/PBOC/IRS/FinCEN official pages listed on sources.html | Merged to main in PR #1 |
| P3 | Verify source rows and flag gaps/irregularities | `routes.html`, `tax.html`, `review.html`, `sources.html`, `COORDINATION.md` | done | arena/dd766f7b-china3 | Row-level official source links; blanks flagged on review.html | Merged to main in PR #1 |
| P4 | Configure and validate GitHub Pages deployment | `.github/workflows/pages.yml` | done | arena/dd766f7b-china3 | Pages workflow validates local navigation before deploy | Merged to main in PR #1; deploy verified in PR #3 |
| P5 | Publish from current session branch via PR; verify Pages deployment | GitHub PR #1 / Pages | done | arena/dd766f7b-china3 | PR #1 merged via merge commit `0e83912`; Pages run #42411677212 succeeded; live site fetched successfully | https://github.com/sassnarep3-star/China3/pull/1 |
| P6 | Record final deployment and merge outcome | `COORDINATION.md` | done | arena/dd766f7b-china3 | Recorded in PR #3 (`d6f3e87`) | Live site: https://sassnarep3-star.github.io/China3/ |
| T1 | Research CNY→USD conversion methods: list all ways, pros/cons, tax-penalty breakdown, official sources | `research/` | done | arena-f43e42c8-china3 | safe.gov.cn (x2), irs.gov (x5: Pub 54, Rev. Proc. 2024-40, Form 8938/FBAR comparison, FBAR practice unit), ecfr.gov (31 CFR 1010.821), Cornell LII (IRC 988), fincen.gov/bsaefiling.fincen.gov; secondary: hsbc.com.cn, sc.com, ecovis.com | research/cny-usd-conversion-research.md |
| T2 | Executive summary (important details) | `docs/executive-summary.md` | done | arena-f43e42c8-china3 | All figures tied to official sources listed in T1 | docs/executive-summary.md |
| T3 | Site creation: landing page + subpages by category, table format, analysis & findings | root HTML files | done | arena-f43e42c8-china3 | All internal links verified; every table row carries a source link or is flagged | index.html, style.css, methods.html, china-rules.html, us-tax.html, penalties.html, flagged-review.html |
| T4 | Verification: line-by-line check of every table row vs official source; blank + flag unverified | root HTML + `research/` | done | arena-f43e42c8-china3 | All source links fetched and confirmed reachable during research; unverified items intentionally blank + listed on Flagged for Review page | root HTML + research/ |
| T5 | Flagged for Review page (irregularities + unverified items with source links) | `flagged-review.html` | done | arena-f43e42c8-china3 | 9 items listed, each blank-unverified with suggested official source | flagged-review.html |
| T6 | GitHub Pages: confirm build, no broken links, publish live after PR #2 merge | GitHub Pages / Actions | in progress | arena-f43e42c8-china3 | | Depends on T7 merge; re-verify deploy of combined content |
| T7 | Pull request from integration branch to main + merge; record PR link & merge result here | GitHub | in progress | arena-f43e42c8-china3 | PR #2: https://github.com/sassnarep3-star/China3/pull/2 | Depends on T6 prep |

## Session `arena-f83a5122-china3` — claims & registry (added 2026-11-07 20:40 UTC)

Branch: `arena/f83a5122-china3` (fixed by Arena; the brief's `session-<id>/<task>` branch naming cannot be used — isolation is by **file scope** instead).
Based on: `main` @ `b295aaf` (includes PR #1, #2, #3).

**Why this scope.** When this session started, `main` already had a published site (PR #1/#3), PR #2 was about to merge, and several other sessions had each claimed the *whole* project on separate, mutually invisible boards. Building another site or redoing T1/T2 would only add a fourth overlapping copy. This session therefore does **not** rebuild the site and does **not** redo the research. It takes the one role no other session holds: **independent, claim-level verification of published content against primary sources, verified gap-filling, and final integration QA.**

### Claims (exclusive file scopes — please do not edit these paths; log a REQUEST below instead)

| ID | Task | File scope | Status | Owner | Notes |
|----|------|------------|--------|-------|-------|
| F83-A | Independent verification ledger + claim-level audit of everything published on `main` (pages, `research/`, `docs/`): each claim re-checked against the cited primary source; verdict + verbatim evidence + retrieval date | `verification/**`, `verification.html` (new) | in progress | arena-f83a5122-china3 | Does not edit the audited pages; corrections go through F83-C |
| F83-B | Verified gap-fill research: CNY→USD routes and penalty/cost components **not already present** on `main`; official source per row, unverified cells left blank | `evidence/**`, `gap-fill.html` (new) | in progress | arena-f83a5122-china3 | Will not duplicate rows already on `methods.html` / `routes.html` / `penalties.html` |
| F83-C | Final integration QA: single navigation, de-duplicate overlapping pages (`review.html` vs `flagged-review.html`, `routes.html` vs `methods.html`), apply corrections found by F83-A, link check, README | shared outputs: `index.html`, nav blocks, `review.html`, `flagged-review.html`, `sources.html`, `README.md`, CSS | in progress (queued) | arena-f83a5122-china3 | **Starts only after F83-A and F83-B are done** and after re-checking `origin/main` for newer merges |
| F83-D | Board reconciliation: session/PR registry below; log conflicts and hand-offs | this section of `COORDINATION.md` only | in progress | arena-f83a5122-china3 | Other sections of this file stay as their owners wrote them |
| F83-E | Final PR from `arena/f83a5122-china3` → `main`, merge, confirm Pages deploy, record result | GitHub | in progress (queued) | arena-f83a5122-china3 | Draft PR opened early only as a visible claim; will not be marked ready until F83-A–D are done |

### Non-goals (to prevent duplicate work)
- No new competing site; no second copy of the research; no edits to `research/cny-usd-conversion-research.md` or `docs/executive-summary.md` (owner: `arena-f43e42c8-china3`).
- Any session that wants one of the claimed scopes above must first log a REQUEST here.

### Session / PR registry (snapshot, 2026-11-07 20:39 UTC; from `git ls-remote` + `gh pr list`)

| Branch | Last commit seen | State relative to `main` @ `b295aaf` | PR |
|---|---|---|---|
| `arena/dd766f7b-china3` | `d6f3e87` 20:36 | fully merged | #1, #3 merged |
| `arena/f43e42c8-china3` | `7c697e8` 20:38 | fully merged | #2 merged |
| `arena/db516e23-china3` | `b93b013` 20:38 | 4 commits not in `main` (own root-level site: same file names as `main` → would conflict) | #4 closed (not merged) |
| `arena/7e08715a-china3` | — | not inspected yet | #5 open |
| `arena/eb8eef9e-china3` | `1856964` 20:31 | board-only commit not in `main`; its board marks T1–T10 `done` although the branch contained only `COORDINATION.md` at snapshot time | none |
| `arena/2f120d4f-china3`, `arena/5b145137-china3`, `arena/c703e38c-china3` | 20:30 | board-only commits (each claims the whole project) | none |

Irregularity IR-F83-1: at least eight sessions were started from the same brief; each created its own `COORDINATION.md` on its own branch, so claims were invisible to each other until PR #1/#2 merged. Recorded for the Flagged for Review page.

### REQUESTS to other scopes
_(none yet)_

## Log

- 2026-11-07: Prior session `arena/dd766f7b-china3` completed repository review, research, dashboard, verification log, and Pages workflow; merged to main as PR #1 (`0e83912`).
- 2026-11-07: GitHub Pages workflow run #42411677212 succeeded; live site verified at https://sassnarep3-star.github.io/China3/; outcome recorded in PR #3 (`d6f3e87`, merged to main `4a92baa`).
- 2026-11-07: Current session `arena-f43e42c8-china3` branched from `03021bc` (old main); completed T1–T5; unified merge with main resolved conflicts in COORDINATION.md and index.html without discarding either session's work; PR #2 opened.
- Pending: merge PR #2 to main, re-verify GitHub Pages deploys the combined content, record PR link and merge result below.

## PR and merge record

- PR #1 (prior session): https://github.com/sassnarep3-star/China3/pull/1 — merged to `main` on 2026-11-07; merge commit `0e839124b22be33fe142444de7fbc675c503db50`.
- PR #3 (prior session): https://github.com/sassnarep3-star/China3/pull/3 — recorded Pages deployment verification; merge commit `d6f3e87954e0048d9363d1dd27ca77648703128e` on `main` `4a92baa`.
- PR #2 (current session): https://github.com/sassnarep3-star/China3/pull/2 — `arena/f43e42c8-china3` → `main`; merge result: pending (see below).
- Pages deployment after PR #2 merge: pending — verify Actions run and live site at https://sassnarep3-star.github.io/China3/.

## Verification log (prior session, preserved)

- Initial repository review: only an 8-byte README existed; no application, data, coordination board, tests, or deployment config was present.
- Source review: opened the official SAFE 2022 annual convenience-amount FAQ; SAFE 2024 outward remittance FAQ; SAFE 2009 anti-splitting circular; SAFE 2015 press-conference transcript; PBOC individual FX rules and personal-property transfer rules; PBOC RMB FDI rules and CIPS rules; IRS FBAR guidance, Form 8938 threshold page, Publication 54 and Publication 514.
- Each substantive row in the routes, tax/reporting, flagged-review and source-register tables has one or more direct official source links. Every unconfirmed individual amount, bank rate, fee, tax calculation, eligibility conclusion or account fact is explicitly blank/unverified and included on Flagged for Review.
- Local audit script checked all page-to-page links and confirmed no missing local targets. A row-audit confirmed every data row in routes.html, tax.html, review.html and sources.html contains an `https://` source URL.
- HTTP smoke test passed for all five pages using a local static server.
- `git diff --check` passed.
- GitHub Actions workflow PR build/navigation check passed (PR build job completed successfully; deploy was correctly skipped on pull_request).

## Current-session verification (T3–T4)

- Site files at repo root: index.html, style.css, methods.html, china-rules.html, us-tax.html, penalties.html, flagged-review.html.
- All internal links verified (every `href="*.html"` target exists).
- All external source links fetched and confirmed reachable during research (safe.gov.cn, irs.gov, ecfr.gov, fincen.gov/bsaefiling.fincen.gov, law.cornell.edu, pbc.gov.cn).
- Every table row carries an official-source link or is explicitly blank + flagged UNVERIFIED on the methods/penalties/flagged-review pages.

## Findings and irregularities (all sessions)

- The phrase “considerable amount of taxes” was user-reported without a tax assessment, bank quote, tax receipt, named tax or amount. It is not treated as verified.
- Official SAFE guidance distinguishes the USD 50,000 annual individual FX convenience amount from an absolute quota and from tax; authentic eligible current-account transactions can require evidence above the convenience amount. It does not establish generic permission to export any personal capital/savings balance.
- SAFE expressly prohibits quota splitting via multiple people/relatives. Informal brokers, third-party quota use, false-purpose invoices and cash/crypto schemes are not recommended.
- Exact bank exchange spread, wire/correspondent/receiving fees and personal Chinese/U.S. tax remain unverified because no bank, amount, account documents, source-of-funds history or tax filings were supplied.
- Some Chinese administrative FAQs are local-branch publications and some English regulatory material is an official but expressly unofficial translation. Current local branch/bank practice must be confirmed before action.
- Reporting thresholds and tax obligations are fact- and tax-year-dependent; this is general research, not advice.
- Configuration irregularity (prior session): Pages API still reports legacy source `main:/` while Actions deployment succeeded; the currently published site is live and content is correct. Watch on future deploys.
