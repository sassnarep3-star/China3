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
| T1 | Research CNY→USD conversion methods: list all ways, pros/cons, tax-penalty breakdown, official sources | `research/` | in progress | arena-f43e42c8-china3 | | Primary research task |
| T2 | Executive summary (important details) | `docs/executive-summary.md` | unclaimed | | | |
| T3 | Site creation: landing page + subpages by category, table format, analysis & findings | `site/` | unclaimed | | | |
| T4 | Verification: line-by-line check of every table row vs official source; blank + flag unverified | `site/` + `research/` | unclaimed | | | |
| T5 | Flagged for Review page (irregularities + unverified items with source links) | `site/flagged-for-review.md` | unclaimed | | | Depends on T1–T4 |
| T6 | GitHub Pages: confirm build, no broken links, publish live | GitHub Pages settings | unclaimed | | | Depends on T3–T5 |
| T7 | Pull request from integration branch to main + merge; record PR link & merge result here | GitHub | unclaimed | | | Depends on T6 |

## Log

- 2026-11-07: Session `arena-f43e42c8-china3` created branch work on `arena/f43e42c8-china3`. Repo initially contained only README.md (`# China3`). Claimed T1 (in progress). T2–T7 unclaimed.
