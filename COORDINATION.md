# Coordination Board — China3 (money-out-of-China research)

Branch: `arena/f43e42c8-china3`
Remote: https://github.com/sassnarep3-star/China3.git
Session ID conventions: `<owner>-<task-id>`, e.g. `arena-f43e42c8-china3-T1`.

## Legend
- Status: `unclaimed` | `in progress` | `done` | `needs review`
- `needs review` = item is published on the Flagged for Review page and does not block anything.
- Before starting a task: claim it here (write session ID + file scope), commit and push immediately.
- Never start a task another session has claimed. If a claim is >60 min old with no commits, any session may take over (note the handoff in the log).
- Make small, frequent commits; run `git pull --rebase` before every push.
- If a task requires changing a file owned by another session, log the request here instead of editing it.
- Shared outputs (table data, index, navigation) are changed only by the final integration session once all other tasks are done.

## Tasks

| ID | Task | File scope | Status | Owner | Sources verified | Notes |
|----|------|------------|--------|-------|------------------|-------|
| T1 | Research CNY→USD conversion methods: list all ways, pros/cons, tax-penalty breakdown, official sources | `research/` | done | arena-f43e42c8-china3 | safe.gov.cn (x2), irs.gov (x5: Pub 54, Rev. Proc. 2024-40, Form 8938/FBAR comparison, FBAR practice unit), ecfr.gov (31 CFR 1010.821), Cornell LII (IRC 988), fincen.gov/bsaefiling.fincen.gov; secondary: hsbc.com.cn, sc.com, ecovis.com | research/cny-usd-conversion-research.md |
| T2 | Executive summary (important details) | `docs/executive-summary.md` | done | arena-f43e42c8-china3 | All figures tied to official sources listed in T1 | docs/executive-summary.md |
| T3 | Site creation: landing page + subpages by category, table format, analysis & findings | root HTML files | done | arena-f43e42c8-china3 | All internal links verified; every table row carries a source link or is flagged | index.html, style.css, methods.html, china-rules.html, us-tax.html, penalties.html, flagged-review.html |
| T4 | Verification: line-by-line check of every table row vs official source; blank + flag unverified | root HTML + research/ | done | arena-f43e42c8-china3 | All source links fetched and confirmed reachable during research; unverified items intentionally blank + listed on Flagged for Review page | root HTML + research/ |
| T5 | Flagged for Review page (irregularities + unverified items with source links) | flagged-review.html | done | arena-f43e42c8-china3 | 9 items listed, each blank-unverified with suggested official source | flagged-review.html |
| T6 | GitHub Pages: confirm build, no broken links, publish live | GitHub Pages settings | in progress | arena-f43e42c8-china3 | | Depends on T3–T5 |
| T7 | Pull request from integration branch to main + merge; record PR link & merge result here | GitHub | unclaimed | | | Depends on T6 |

## Log

- 2026-11-07: Session `arena-f43e42c8-china3` created branch work on `arena/f43e42c8-china3`. Repo initially contained only README.md (`# China3`). Claimed T1 (in progress). T2–T7 unclaimed.
