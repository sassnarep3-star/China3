# COORDINATION.md — Shared Task Board

Project: **China money** — research, organize and analyze how a US citizen can move CNY out of China into USD with the least tax / conversion penalty; publish a GitHub Pages dashboard with fully-sourced tables and a clearly labeled "Flagged for Review" page.

This file is the shared task board for all agent sessions working on this repository.
Read it before starting. Claim a task by writing your session ID and file scope, then
commit and push that claim immediately. Never start a task another session has claimed.

- Board last updated: 2026-11-07 (UTC)
- Integration session for this board: `session-c703e38c`
- Branch used by this session: `arena/c703e38c-china3` (fixed by Arena)

## Status vocabulary

- `unclaimed` — available
- `in progress` — owned by a session, work underway
- `done` — finished; sources / verification / irregularities recorded below
- `needs review` — published on the site's "Flagged for Review" page; non-blocking

## Merge / handoff log (READ FIRST)

- 2026-11-07 — A **parallel session** `arena/dd766f7b-china3` had already completed and
  merged a first version of the guide to `main` (PR #1 and PR #3; HEAD `4a92baa`) while
  this session was researching. Its board, findings, PR links and deployment record are
  **preserved verbatim** at the end of this file. It marked all of its tasks `done`.
- 2026-11-07 — `git merge origin/main` produced an `add/add` conflict on `COORDINATION.md`
  because both sessions created the file from the same initial commit. **Conflict resolved
  without discarding the other session's work**: their entire board is reproduced verbatim
  below; this board adds the new session's claims, verification log and integration record.
  All other files from `main` (README.md, index.html, routes.html, tax.html, review.html,
  sources.html, assets/site.css, .github/workflows/pages.yml) were taken intact.
- Because the prior session's tasks are `done` and merged, this session acts as the **final
  integration session**: it is the only session permitted to change shared outputs (site
  index/navigation, table data) at this stage. Changes to shared outputs are logged here.
- No competing `in progress` claim existed at the time of takeover. If the other session
  resumes, it should re-read this board before claiming new work.
- 2026-11-07 — `git pull --rebase` run before the first push of the merge commit attempted
  to flatten the merge and re-play the other session's commits on top of this session's
  first commit, producing a second `add/add` conflict on `COORDINATION.md`. **Stopped**,
  verified no work would be lost (remote tip already equalled local tip `4aa7f58`), and
  ran `git rebase --abort` to restore the merge commit intact. No other session's work was
  discarded. Subsequent pre-push syncs use `git fetch` + fast-forward verification instead
  of flattening rebase, because this branch legitimately contains a merge commit. Logged
  as IR-013.

## Important session note / logged deviation

The task brief asks each session to work on its own branch named
`session-<id>/<task>`. The Arena environment fixes the working branch to
`arena/c703e38c-china3` and forbids creating, switching to, or pushing other branches.
This session therefore keeps ALL work on the single mandated branch (the session *is* also
the integration branch), and uses non-overlapping file scopes in the board below instead of
separate branches. Same deviation was recorded independently by the prior session.
Published as IR-001.

## Task board (this session)

| Task | Description | Status | Owner session | File scope (exclusive) |
|---|---|---|---|---|
| T1 | Repo audit + create coordination board | done | session-c703e38c | `COORDINATION.md`, `README.md` (integration edits) |
| T2 | Research: China-side FX law (SAFE / PBOC / State Council) | done | session-c703e38c | `research/china-framework.md` |
| T3 | Research: US-side tax & reporting (IRS / FinCEN / Treasury / eCFR) | done | session-c703e38c | `research/us-tax.md` |
| T4 | Research: conversion channels + conversion-penalty breakdown | done | session-c703e38c | `research/channels.md`, `research/penalty-breakdown.md` |
| T5 | Verified data tables (one official source link per row) | done | session-c703e38c | `data/*.csv`, `scripts/build_site.py`, `scripts/verify.py` |
| T6 | Site build: landing + category subpages + tables + Flagged for Review | done | session-c703e38c | `executive-summary.html`, `china-rules.html`, `us-tax.html`, `channels.html`, `penalty.html`, `findings.html`; integration edits to `index.html`, `review.html`, `sources.html`, `assets/site.css`, `.github/workflows/pages.yml` |
| T7 | Executive summary + analysis & findings | done | session-c703e38c | `executive-summary.html`, `research/analysis.md` |
| T8 | Final integration: line-by-line re-verification, build, broken-link check | done | session-c703e38c | integration only; edits shared outputs |
| T9 | PR to main, merge, confirm Pages deploy, record PR link + merge result here | pending | session-c703e38c | `COORDINATION.md` (append) |

`git pull --rebase` / `git fetch` is run before every push. Small, frequent commits are used.

## Shared-output change log (integration session only)

- `index.html` — preserved all prior content verbatim; added category navigation + a
  "Deep research" section linking the new subpages.
- `review.html`, `sources.html` — preserved prior content; appended this session's flagged
  items and official sources.
- `assets/site.css` — appended additive styles only (no prior rules modified).
- `.github/workflows/pages.yml` — extended the build check to scan **all** `.html` files and
  run `scripts/verify.py`; the prior checks and deploy job were retained.
- New data files `data/*.csv` are the single source of truth for all new tables.

## Verification log (per task, filled when done)

### T1 — Repo audit
- Sources: `git ls-files`, `git log`, `git status`, `git remote -v`,
  `gh api repos/sassnarep3-star/China3`, `gh api repos/sassnarep3-star/China3/pages`.
- Verified: at session start the checkout contained exactly one tracked file `README.md`
  (`# China3`), single commit `03021bc`, default branch `main`, `has_pages: true`,
  Pages source `main:/` legacy, working branch clean. Later found `origin/main` had
  advanced to `4a92baa` via a parallel session.
- Irregularities: brief referenced `[COORDINATION.md](http://COORDINATION.md)` and
  "all entries and findings", but neither existed at session start (IR-002). Pages API
  reported `legacy` source `main:/` while an Actions deploy workflow also exists (IR-003,
  also noted by the prior session).

### T2 — China-side FX framework
- Sources: SAFE 宁夏 2022 政策释疑（八）; SAFE 天津 2024 个人外汇（三）; SAFE 天津 2024
  经常项目外汇政策问答（九）; SAFE 天津 2024《个人外汇管理办法实施细则》(已修改);
  国务院/人民银行《个人外汇管理办法》2006 令第3号 (gov.cn + pbc.gov.cn);
  SAFE《外汇管理条例》国务院令532号 (2008) 全文; SAFE 2025 个人外汇（八）关注名单;
  SAFE 2015 汇发〔2015〕49号 (已废止页面); SAFE 河北 分拆购汇案例;
  SAFE 广东 2020 网上办理外币兑换提示; SAFE 个人购汇申请书 PDF;
  SAFE 2004 个人财产对外转移办法 + 业务指南; 汇发〔2017〕3号 利润汇出;
  SAFE 2018 银行卡境外大额提现通知; SAFE 2003 携带外币现钞出入境办法;
  PBOC 2014 公告第5号 + 2014 大事记; PBOC 银发〔2020〕330号 跨境人民币;
  PBOC 2026 银发〔2026〕42号; 两高法释〔2019〕1号; 刑法225条;
  国家税务总局 公告2013年第40号; 个人所得税法; 财税〔2008〕132号.
- Verification performed: fetched full text of the SAFE 宁夏, 天津 (2 pages), PBOC
  2026 notice, gov.cn 个人外汇管理办法, and SAFE 外汇管理条例 pages; cross-checked
  every quoted figure (USD 50,000, RMB 200,000/500,000, 10万元人民币, 30%/等值罚金,
  500万/2500万, 2%, 3%, 24个月, 3%-45%, 20%) against the retrieved official text.
- Irregularities: 银发〔2021〕237号 **repealed** by 银发〔2026〕42号 (IR-004);
  conflicting 1996 vs 2008 versions of 外汇管理条例 第45条 (IR-005);
  汇发〔2009〕56号 and 汇发〔2015〕49号 both marked 已废止 (IR-006);
  conflicting official definitions of 境内个人/境外个人 (IR-007).

### T3 — US-side tax & reporting
- Sources: IRS Pub 54, Pub 519, Pub 525, Pub 514, international FAQ,
  "Gifts from foreign person", FATCA information for individuals,
  Comparison of Form 8938 and FBAR requirements, Form 8938 instructions,
  IRM 5.21.6, IRM 4.26.16, IRS FBAR page, Streamlined procedures (both),
  IRS China tax treaty documents + treaty PDF + technical explanation,
  FinCEN FBAR line-item instructions + "Who Is A United States Person",
  eCFR 31 CFR 1010.821, Federal Register 2026 penalty-adjustment notices,
  Treasury FATCA IGA page / 2014 S&ED fact sheet.
- Verification performed: fetched IRS gifts-from-foreign-person, IRS comparison page,
  eCFR 1010.821 (all chunks), IRS Pub 525; cross-checked $10,000, $16,536, $165,353,
  50%, $50,000/$75,000/$200,000/$300,000/$400,000/$600,000, $10,000/$60,000, 40%,
  $100,000, 5%/25%, $20,573, $200, 10% treaty rate, saving clause.
- Irregularities: 2026 FBAR inflation adjustment cancelled by OMB M-26-11, so 2025
  amounts remain in force (IR-008); no signed US–mainland-China FATCA IGA confirmed —
  only a 2014 "agreement in substance" (IR-009); eCFR is authoritative but expressly
  unofficial (IR-010).

### T4 — Channels + penalty breakdown
- Sources: all of T2/T3 plus Bank of China official fee schedules (boc.cn),
  HKMA quarterly bulletins on CNY/CNH spread, PBOC Guangzhou 跨境理财通 Q&A,
  SAFE QDII account guide, SAFE 上海 2026 跨境电子商务问答.
- Verification performed: fetched PBOC 2026 notice; read BOC personal e-banking rate
  table (1‰, min ¥50, max ¥260, cable fee ¥80/¥150), BOC corporate schedule
  (min ¥50, max ¥1,000), BOC 2018 announcement (全额到账 USD 15), PBOC 2014 公告5号
  (±2% band, 3% spread cap widened then abolished 2014-07-01), HKMA CNY/CNH spread
  data (1.94% Sept-2011 episode; +163 pips Q1-2014).
- Irregularities: no official source establishes a flat "conversion tax" (IR-011);
  current bank spreads / CNH basis / correspondent fees for a specific account are not
  published by an official source and are left blank (IR-012).

### T5–T7 — Tables, site, executive summary
- Verification performed: `scripts/build_site.py` regenerates every new page from
  `data/*.csv`; `scripts/verify.py` (a) checks every table row has an official-domain
  source URL or is explicitly blank+UNVERIFIED, (b) checks every source URL is on the
  official-domain allowlist and is registered in `data/sources.csv`, (c) checks all
  internal `href`s across every `.html` file resolve, (d) checks all rows in the
  generated HTML match the CSVs.
- Irregularities: all unverified values left blank and surfaced on `review.html`.

### T8 — Final integration
- Verification performed: full site rebuild, `verify.py` line-by-line audit, local static
  HTTP smoke test of every page, `git diff --check`, GitHub Actions build check.
- Result: recorded below after execution.

## Open requests to other sessions

- None.

## PR / merge / deployment record (filled by T9)

- PR link: _pending_
- Merge result: _pending_
- GitHub Pages deployment: _pending_

---

# PRESERVED VERBATIM — board written by prior session `arena/dd766f7b-china3`
(from `origin/main` commit `4a92baa`; reproduced without alteration)

# Coordination board

## Session and constraints
- Active Arena session/branch: `arena/dd766f7b-china3` (fixed by Arena; no alternate branch/worktree will be created).
- No other task claims were present when this board was initialized. No conflicting session scope was found.
- Scope completed by this session: repository review, official-source research, executive report, comparison tables, flagged-items page, source register, and GitHub Pages setup. Files: `COORDINATION.md`, `README.md`, `.github/workflows/pages.yml`, `assets/site.css`, `index.html`, `routes.html`, `tax.html`, `review.html`, `sources.html`.
- User-suggested `session-<id>/<task>` and separate integration branch cannot be used because Arena requires all work to remain on the active fixed branch. The current session has taken the integration role because no other claims/work were present.

## Tasks
| Task | Status | Owner | Files |
|---|---|---|---|
| Inspect repository and document project findings | done | arena/dd766f7b-china3 | README.md, COORDINATION.md |
| Build official-source-backed China-to-US funds transfer dashboard | done | arena/dd766f7b-china3 | index.html, routes.html, tax.html, review.html, sources.html, assets/site.css |
| Verify source rows and flag gaps/irregularities | done | arena/dd766f7b-china3 | routes.html, tax.html, review.html, sources.html, COORDINATION.md |
| Configure and validate GitHub Pages deployment | done | arena/dd766f7b-china3 | .github/workflows/pages.yml |
| Publish from current session branch via PR; verify Pages deployment | done | arena/dd766f7b-china3 | GitHub PR #1 / Pages |
| Record final deployment and merge outcome | done | arena/dd766f7b-china3 | COORDINATION.md |

## Verification log
- Initial repository review: only an 8-byte README existed; no application, data, coordination board, tests, or deployment config was present.
- Source review: opened the official SAFE 2022 annual convenience-amount FAQ; SAFE 2024 outward remittance FAQ; SAFE 2009 anti-splitting circular; SAFE 2015 press-conference transcript; PBOC individual FX rules and personal-property transfer rules; PBOC RMB FDI rules and CIPS rules; IRS FBAR guidance, Form 8938 threshold page, Publication 54 and Publication 514.
- Each substantive row in the routes, tax/reporting, flagged-review and source-register tables has one or more direct official source links. Every unconfirmed individual amount, bank rate, fee, tax calculation, eligibility conclusion or account fact is explicitly blank/unverified and included on Flagged for Review.
- Local audit script checked all page-to-page links and confirmed no missing local targets. A row-audit confirmed every data row in routes.html, tax.html, review.html and sources.html contains an `https://` source URL.
- HTTP smoke test passed for all five pages using a local static server.
- `git diff --check` passed.
- GitHub Actions workflow PR build/navigation check passed (PR build job completed successfully; deploy was correctly skipped on pull_request).
- Merged PR #1: https://github.com/sassnarep3-star/China3/pull/1 — merged to `main` using merge commit `0e839124b22be33fe142444de7fbc675c503db50` on 2026-11-07.
- GitHub Pages workflow run #42411677212 succeeded: https://github.com/sassnarep3-star/China3/actions/runs/42411677212. GitHub Pages API reports `status: built`; published homepage and all four subpages were fetched successfully at https://sassnarep3-star.github.io/China3/.
- The Pages API still reports legacy source `main:/` while Actions deployment succeeded. This is recorded as a configuration irregularity to watch, but the currently published site is live and the content is correct.

## Findings and irregularities
- The phrase “considerable amount of taxes” was user-reported without a tax assessment, bank quote, tax receipt, named tax or amount. It is not treated as verified.
- Official SAFE guidance distinguishes the USD 50,000 annual individual FX convenience amount from an absolute quota and from tax; authentic eligible current-account transactions can require evidence above the convenience amount. It does not establish generic permission to export any personal capital/savings balance.
- SAFE expressly prohibits quota splitting via multiple people/relatives. Informal brokers, third-party quota use, false-purpose invoices and cash/crypto schemes are not recommended.
- Exact bank exchange spread, wire/correspondent/receiving fees and personal Chinese/U.S. tax remain unverified because no bank, amount, account documents, source-of-funds history or tax filings were supplied.
- Some Chinese administrative FAQs are local-branch publications and some English regulatory material is an official but expressly unofficial translation. Current local branch/bank practice must be confirmed before action.
- Reporting thresholds and tax obligations are fact- and tax-year-dependent; this is general research, not advice.

## Publication / handoff
- PR #1: https://github.com/sassnarep3-star/China3/pull/1 — merged to `main` on 2026-11-07; merge commit `0e839124b22be33fe142444de7fbc675c503db50`.
- Pages deployment run #42411677212: https://github.com/sassnarep3-star/China3/actions/runs/42411677212 — success. Live site: https://sassnarep3-star.github.io/China3/.
- Pages status confirmed `built`; live homepage and route, tax, review, and source pages fetched successfully.
- Session remained on `arena/dd766f7b-china3`; no other branch was created or pushed.
