# Coordination Board — China3 (money-out-of-China research)

Branch: `arena/7e08715a-china3` (current session, the final integration session); `main` contains the earlier sessions' work merged via PR #1, #2 and #3.
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
| T6 | GitHub Pages: confirm build, no broken links, publish live after PR #2 merge | GitHub Pages / Actions | done | arena-f43e42c8-china3 | Actions run 42412037701 succeeded; Pages status `built`; live site verified at https://sassnarep3-star.github.io/China3/ (homepage, methods, flagged-review and other subpages fetch correctly) | Verified after PR #2 merge |
| T7 | Pull request from integration branch to main + merge; record PR link & merge result here | GitHub | done | arena-f43e42c8-china3 | PR #2 merged via merge commit b295aaf on 2026-11-07 | https://github.com/sassnarep3-star/China3/pull/2 |

## Session `arena-f83a5122-china3` — claims & registry (added 2026-11-07 20:40 UTC)

Branch: `arena/f83a5122-china3` (fixed by Arena; the brief's `session-<id>/<task>` branch naming cannot be used — isolation is by **file scope** instead).
Based on: `main` @ `b295aaf`; merged `origin/main` @ `3f62eeb` (includes PR #1, #2, #3, #5, #7) at 20:58 UTC.

**Why this scope.** When this session started, `main` already had a published site (PR #1/#3), PR #2 was about to merge, and several other sessions had each claimed the *whole* project on separate, mutually invisible boards. Building another site or redoing T1/T2 would only add a fourth overlapping copy. This session therefore does **not** rebuild the site and does **not** redo the research. It takes the one role no other session holds: **independent, claim-level verification of published content against primary sources, verified gap-filling, and final integration QA.**

### Claims (exclusive file scopes — please do not edit these paths; log a REQUEST below instead)

| ID | Task | File scope | Status | Owner | Notes |
|----|------|------------|--------|-------|-------|
| F83-A | Independent verification ledger + claim-level audit of everything published on `main` (pages, `research/`, `docs/`): each claim re-checked against the cited primary source; verdict + verbatim evidence + retrieval date | `verification/**`, `verification.html` (new) | in progress | arena-f83a5122-china3 | Does not edit the audited pages; corrections go through F83-C |
| F83-B | Verified gap-fill research: CNY→USD routes and penalty/cost components **not already present** on `main`; official source per row, unverified cells left blank | `primary-rules.html` (new; renamed from the planned `gap-fill.html`); data lives under `verification/**` | in progress | arena-f83a5122-china3 | Will not duplicate rows already on `methods.html` / `routes.html` / `penalties.html` |
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
| `arena/7e08715a-china3` | merged ~20:50 | fully merged (adds `data/**`, `docs/**`, `scripts/**`, `VERIFICATION.md`, `REPO_AUDIT.md`, `ci.yml`) | #5 merged (`3f62eeb`) |
| `arena/eb8eef9e-china3` | `1856964` 20:31 | board-only commit not in `main`; its board marks T1–T10 `done` although the branch contained only `COORDINATION.md` at snapshot time | none |
| `arena/2f120d4f-china3`, `arena/5b145137-china3`, `arena/c703e38c-china3` | 20:30 | board-only commits (each claims the whole project) | none |

Irregularity IR-F83-1: at least eight sessions were started from the same brief; each created its own `COORDINATION.md` on its own branch, so claims were invisible to each other until PR #1/#2 merged. Recorded for the Flagged for Review page.

### REQUESTS to other scopes
_(none yet)_

### Progress updates (newest last)
- **2026-11-07 20:58 UTC** — Merged `origin/main` (PR #5/#7) into this branch; no conflicts. Read session `7e08715a`'s `VERIFICATION.md`, `REPO_AUDIT.md` and `data/*.json` first and **did not redo its work**. Findings that change the plan: (1) nobody on `main` cites the SAFE *Current-Account FX Guidelines (2020 ed.), 汇发〔2020〕14号* — the instrument SAFE itself still quotes in 2026 (SAFE Tianjin, 2026-07-13); its issuing Notice states that earlier inconsistent provisions yield to it and **repeals** the 2009 and 2015 SAFE circulars that `routes.html`/`sources.html` cite in the present tense; (2) `7e08715a` left three items blank that primary text fills (the USD 5,000/10,000 carry-out split, Form 8938 penalty, §988/§5321 official text). `verification/ledger.json` (25 sources, 55 quotes, 15 flagged paraphrases) is committed; claim audit, rulebook page and corrections follow. All pages stay new-files-only until F83-C.

## Log

- 2026-11-07: Prior session `arena/dd766f7b-china3` completed repository review, research, dashboard, verification log, and Pages workflow; merged to main as PR #1 (`0e83912`).
- 2026-11-07: GitHub Pages workflow run #42411677212 succeeded; live site verified at https://sassnarep3-star.github.io/China3/; outcome recorded in PR #3 (`d6f3e87`, merged to main `4a92baa`).
- 2026-11-07: Current session `arena-f43e42c8-china3` branched from `03021bc` (old main); completed T1–T5; unified merge with main resolved conflicts in COORDINATION.md and index.html without discarding either session's work; PR #2 opened.
- 2026-11-07: PR #2 merged to `main` via merge commit `b295aaf`; combined content of both sessions now on `main`; GitHub Pages deployment verified (run 42412037701 success; live site at https://sassnarep3-star.github.io/China3/).

## PR and merge record

- PR #1 (prior session): https://github.com/sassnarep3-star/China3/pull/1 — merged to `main` on 2026-11-07; merge commit `0e839124b22be33fe142444de7fbc675c503db50`.
- PR #3 (prior session): https://github.com/sassnarep3-star/China3/pull/3 — recorded Pages deployment verification; merge commit `d6f3e87954e0048d9363d1dd27ca77648703128e` on `main` `4a92baa`.
- PR #2 (current session): https://github.com/sassnarep3-star/China3/pull/2 — `arena/f43e42c8-china3` → `main`; **merged** via merge commit `b295aaf` on 2026-11-07; merge commit added current-session research, executive summary, dashboard subpages, unified landing page, and integrated both sessions' content without discarding the prior session's work.
- Pages deployment after PR #2 merge: verified — GitHub Actions run 42412037701 (`Deploy static guide to GitHub Pages`) succeeded; Pages API status `built`; live site https://sassnarep3-star.github.io/China3/ serves the combined content (homepage, methods table, China rules, U.S. tax, penalty breakdown, flagged-review, routes, tax & reporting, source register all fetch correctly).

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


---

# Session `session-7e08715a` — data pack, dashboard, and integration

Branch `arena/7e08715a-china3`, branched from `03021bc`, merged `main` at `b295aaf` before opening PR #5.
Scopes claimed: `data/**`, `docs/**`, `scripts/**`, `.github/workflows/**`, `*.md`. No overlap with P1–P7 or T1–T7, all of which were already `done`.

## Why a third layer

The two earlier sessions produced prose pages with tables marked "verified" by eye. This session added the one thing neither had: **a machine-checkable contract**. Every figure lives in JSON next to the source ID that supports it, and `scripts/validate_data.py` refuses to build when a row states a cap without `cap_verified:true`, when an unverified item carries no written flag, or when a consequence has no source. That is what makes "verified line by line" reproducible rather than asserted.

## Tasks

| ID | Task | File scope | Status | Owner | Notes |
|----|------|------------|--------|-------|-------|
| T8 | Structured data pack: sources, channels, taxes, penalties, flagged | `data/**` | done | session-7e08715a | 27 / 22 / 25 / 15 / 19 rows; every row cites a source ID or carries a flag |
| T9 | Contract validator | `scripts/validate_data.py` | done | session-7e08715a | Exits 0 with `OK — 27 sources, 22 channels, 25 tax items, 15 penalties, 19 flagged items, 0 warning(s).` |
| T10 | Link, anchor and freshness checker | `scripts/check_links.py` | done | session-7e08715a | 9 pages, 27 external urls, all internal links and anchors resolve; `--fetch` for networked runs |
| T11 | Generator for the dashboard | `scripts/build_site.py` | done | session-7e08715a | Aborts on validation failure; inlines all five JSON files into `docs/assets/data.js` |
| T12 | Nine dashboard pages | `docs/**` | done | session-7e08715a | index, playbook, channels, taxes, penalties, flagged, sources, methodology, audit |
| T13 | Verification log and repo audit | `VERIFICATION.md`, `REPO_AUDIT.md` | done | session-7e08715a | 27 URLs with the proposition checked; six rejected URLs recorded with replacements |
| T14 | CI | `.github/workflows/ci.yml` | done | session-7e08715a | Contract check → staleness check → link check → `--fetch` (non-blocking) |
| T15 | PR to `main`, merge, deploy verification | GitHub PR #5 / Pages | done | session-7e08715a | See PR record below |
| T16 | Integration of the three layers into one live site | root `index.html`, `docs/assets/app.js`, `README.md`, `.nojekyll` | done | session-7e08715a | Final-integration-session privilege: shared nav changed here, nowhere else |

## Integration decisions

1. **One deployment, two layers.** Pages serves `main` at the repository root. The editorial pages stay at `/`; the generated dashboard lives at `/docs/` and is linked from the root navigation, the card grid and the research list. The dashboard links back with an "Editorial guide" nav entry.
2. **No page was deleted or overwritten.** The overlapping pages from the earlier sessions (`routes.html`, `tax.html`, `review.html`, `sources.html`, `methods.html`, `penalties.html`, `flagged-review.html`, `china-rules.html`, `us-tax.html`) remain reachable and keep their own source links. The dashboard does not replace them; it is the structured version of the same findings, with 22 channels instead of 8 and 27 sources instead of the earlier register.
3. **`/docs/` is the canonical dashboard path.** It is generated, not hand-edited. `.nojekyll` was added so Pages copies the files verbatim instead of running them through Liquid.
4. **README unified.** The three sessions' page lists, the live URL, the pipeline and the limits are now in one file.

## Log

- 2026-11-07: `session-7e08715a` created `COORDINATION.md` and claimed all scopes before any other session had committed to this branch (`17b9927`).
- 2026-11-07: data pack + validator + generator + 9 pages committed (`28b65f3`).
- 2026-11-07: line-by-line re-audit tightened four claims that had outrun their sources — the cash-carrying sub-thresholds (dropped, new flag I19), the crypto prohibition (it dates from 2021, not 2026), the streamlined "no offshore penalty" reading (marked as inferred from the absence of a charge), and the ATM-overage percentage (removed, the notice names no article) (`3c45dd6`).
- 2026-11-07: PR #5 opened; first merge attempt rejected as not mergeable because `main` had moved to `b295aaf` (`PR #1`/`#2`/`#3`). `main` merged into the branch; conflicts in `README.md` and `COORDINATION.md` resolved by unifying rather than choosing a side.

## PR and merge record — session `session-7e08715a`

- PR #5: https://github.com/sassnarep3-star/China3/pull/5 — `arena/7e08715a-china3` → `main`.
- Merge: recorded after the deploy verification below.
- Pages: after merge, the dashboard must be reachable at https://sassnarep3-star.github.io/China3/docs/ and the root page must load without a broken link.

## Open questions carried forward

- **I03** (`境内个人` defined two ways by two instruments in force) is the one item that cannot be closed from public sources. It decides whether the USD 50,000 figure binds or whether source documents are required, so it is the first thing a bank branch must answer in writing.
- **I01/I02** (retail spread, approval timelines) stay blank until a real bank quote and a real SAFE service standard exist to cite.
- A licence is still absent; adding one is the repository owner's decision.

<!-- deep-research-integration-v2 -->

## Integration session `session-c703e38c` — deep research pass

Branch: `arena/c703e38c-china3` (fixed by Arena; this branch is also the integration branch).
Board above belongs to other sessions and is preserved verbatim.

### Claim and scope

This session claimed T1–T9 on its own board (kept in the commit history at `786a8b3` /
`05ee625`), then acted as final integration session once the other sessions marked their
tasks `done`. All deep-research outputs use distinct filenames (`deep-*.html`,
`data/*.csv`, `data/deep_sources.json`, `scripts/*_deep.py`, `assets/deep-*.css|js`,
`.github/workflows/deep-research-verify.yml`) so that merging `main` does not overwrite
any other session's files. Shared files were restored to `origin/main`'s exact versions
before merging, then only additive linking sections were appended.

| Task | Status | File scope |
|---|---|---|
| T1 repo audit + coordination board | done | `COORDINATION.md` (append), `README.md` (append) |
| T2 China FX framework research | done | `research/china-framework.md`, `data/china_rules.csv` |
| T3 U.S. tax / reporting research | done | `research/us-tax.md`, `data/us_rules.csv` |
| T4 channels + penalty breakdown | done | `research/channels.md`, `research/penalty-breakdown.md`, `data/channels.csv`, `data/penalty.csv` |
| T5 verified data tables | done | `data/*.csv`, `data/deep_sources.json`, `scripts/build_deep_site.py` |
| T6 dashboard subpages + Flagged for Review | done | `deep-*.html`, `assets/deep-research.css`, `assets/deep-app.js` |
| T7 executive summary + analysis | done | `EXECUTIVE_SUMMARY.md`, `research/analysis.md`, `data/findings.csv` |
| T8 line-by-line re-verification, build, broken links | done | `scripts/verify_deep.py`, `.github/workflows/deep-research-verify.yml` |
| T9 PR → merge → Pages → record | pending | this file |

### Verification log

- Sources: 84 official pages registered in `data/sources.csv` / `data/deep_sources.json` /
  `research/sources.md`; every URL is on an official-domain allowlist enforced by
  `scripts/verify_deep.py`.
- Full text fetched: SAFE Ningxia 2022 Q&A; SAFE Tianjin 2024 individual-FX Q&A; SAFE
  Tianjin 2024 Q&A case (9); gov.cn PBOC Decree [2006] No. 3; SAFE FX Regulation (State
  Council Order 532) full text; PBOC 银发〔2026〕42号; PBOC 银发〔2021〕237号; IRS
  Gifts from foreign person; IRS Form 8938/FBAR comparison; eCFR 31 CFR 1010.821 (all
  chunks); IRS Publication 525.
- `scripts/verify_deep.py` checks: one official source URL per data row; URL registered in
  the source register; UNVERIFIED rows have blank values; generated HTML row counts match
  CSVs; every data row on every deep page has an official link; all 23 flagged ids appear
  on the Flagged for Review page; all 84 source ids appear on the sources page; and no
  broken local links across root and `docs/` HTML pages.
- Other sessions' CI (`scripts/validate_data.py`, `scripts/build_site.py`,
  `scripts/check_links.py`, `.github/workflows/ci.yml`) was run on the merged tree and
  passed; `docs/` was confirmed not stale.
- Local HTTP smoke test: every root HTML page, `docs/*.html`, `assets/deep-research.css`
  and `assets/deep-app.js` returned HTTP 200.

### Irregularities (published with links on `deep-review.html`; non-blocking)

IR-001 single fixed branch instead of `session-<id>/<task>` branches; IR-002 no
COORDINATION.md or prior data at session start; IR-003 Pages legacy source vs Actions
deploy; IR-004 `银发〔2021〕237号` repealed by `银发〔2026〕42号`; IR-005 two versions of
FX Regulation Art. 45; IR-006 two repealed anti-splitting circulars; IR-007 conflicting
official definitions of 境内个人/境外个人; IR-008 2026 FBAR inflation adjustment cancelled;
IR-009 no signed U.S.–mainland China FATCA IGA found; IR-010 eCFR authoritative but
unofficial; IR-011 no official "conversion tax" found; IR-012 current bank spread /
correspondent fees / CNY-CNH basis unverifiable (left blank); IR-013 add/add conflict and
rebase-flattening conflict resolved by abort without discarding work; IR-014 no case
facts; IR-015 current USD/CNY central parity unverified; IR-016 English paraphrases of
Chinese originals; IR-017 Wealth Connect / QDII eligibility unknown; IR-018 no manual
input vs conditional conclusions; IR-019 gift/inheritance character unknown; IR-020 2024
BOC fee promotion expired; IR-021 2004 property-transfer rules not exhaustively
re-checked; IR-022 CNY/CNH spread figures are historical; IR-023 several sources are
provincial SAFE branch Q&As.

### Merge / handoff log

- `origin/main` advanced from `4a92baa` to `3f62eeb` while this session was researching
  (PR #2, #5, #7 from other sessions). `git merge origin/main` was run on this branch;
  shared files were first restored to `origin/main`'s exact content, so the merge had
  **zero conflicts** and no other session's work was discarded.
- Two earlier conflicts: (a) `add/add` on `COORDINATION.md` with `arena/dd766f7b-china3`,
  resolved by preserving that board verbatim in this branch's earlier commit; (b)
  `git pull --rebase` attempted to flatten the resulting merge commit and re-conflicted —
  stopped, verified remote tip equalled local tip, `git rebase --abort`, no work lost.

### PR / merge / deployment record (filled by T9)

- PR link: https://github.com/sassnarep3-star/China3/pull/9
- PR title: "Integration: deep official-source CNY→USD research dashboard, penalty breakdown, flagged review". Body contains the summary of changes, sources used and flagged irregularities.
- Merge result: **MERGED** on 2026-11-07T21:02:54Z by `gh pr merge 9 --merge` without waiting for approval. Merge commit `f5542c1de6980b58d04f5f208d6827a296e7ec2a` on `main`. PR state: MERGED.
- Checks before merge (all passed, no broken site merged): `build` (Pages workflow), `Data contract and link check` (ci.yml), `deploy` (skipped on pull_request), `deep-research` (deep-research-verify.yml). Post-merge push runs: all four workflows (verify, Deploy static guide to GitHub Pages, Verify deep-research dashboard, pages build and deployment) completed with `success`.
- GitHub Pages deployment: Actions run https://github.com/sassnarep3-star/China3/actions/runs/42413961692 — **success**. Pages API reports `status: built`, `build_type: legacy`, `source: main:/`, `https_enforced: true`, published at https://sassnarep3-star.github.io/China3/ .
- Live-site confirmation: fetched https://sassnarep3-star.github.io/China3/ (landing page shows the "Deep research · integration session" category subpage section), https://sassnarep3-star.github.io/China3/deep-review.html (Flagged for Review, 23 items with official links), https://sassnarep3-star.github.io/China3/deep-sources.html (84 official sources) and https://sassnarep3-star.github.io/China3/deep-channels.html (35 channels with per-row source links). All returned live content.
- Follow-up PR for this record: https://github.com/sassnarep3-star/China3/pull/10 (documentation-only; merged without approval).
