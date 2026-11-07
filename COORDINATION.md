# Coordination

Shared task board for parallel sessions. Update this board before starting work and after completing each task. Do not edit another session's claimed files.

## Session rules

- Session ID for this run: `arena-2f120d4f-china3`.
- This session is restricted by the workspace to branch `arena/2f120d4f-china3`; it performs claimed tasks sequentially and does not create additional branches. Other sessions should preserve non-overlapping file scopes and follow the handoff rules below.
- `needs review` means published on the site's **Flagged for Review** page and does not block integration.
- A claim older than 60 minutes with no commits may be taken over; record the handoff here.
- Run `git pull --rebase` before every push. Resolve conflicts without discarding another session's work and log the resolution.

## Tasks

| ID | Task | Status | Owning session | Exclusive file scope |
|---|---|---|---|---|
| R1 | Research Chinese FX conversion/remittance routes, controls, documentation, and costs from official sources | done | arena-2f120d4f-china3 | `research/china-routes.md` |
| R2 | Research U.S. citizen tax and reporting obligations from official sources | in progress | arena-2f120d4f-china3 | `research/us-tax-reporting.md` |
| R3 | Build cost taxonomy, comparison methodology, executive-summary evidence, and risk flags | unclaimed | — | `research/methodology.md` |
| I1 | Final integration: verify combined rows, create site/data/navigation, test links/build, PR, merge, and Pages deployment | unclaimed | — | `index.html`, `assets/**`, `pages/**`, `data/**`, `.github/**`, `README.md`, `404.html` |

## Change requests

None.

## Completion and verification log

| Time (UTC) | Session | Task | Sources / verification performed | Irregularities / handoffs |
|---|---|---|---|---|
| 2026-11-07 | arena-2f120d4f-china3 | R1 claim | Initial repository contained only `README.md`; created coordination board and claimed R1. | Repository has no existing implementation or research to audit. |
| 2026-11-07 | arena-2f120d4f-china3 | R1 done; R2 claim | Directly opened and checked controlling SAFE/PBOC/SAT/Customs/BOC pages and PDFs; wrote 25 route/alternative rows, 6 rejected/unconfirmed route rows, 7 cost rows, and evidence/open-issue lists in `research/china-routes.md`. Every factual table row carries an official source link. | Live quotes, user-specific eligibility, named nonbank corridors and personalized tax totals remain blank/flagged. R1 complete; R2 claimed sequentially by the same session. |

## Pull request and deployment

Not started. Integration may begin only after R1–R3 are complete.
