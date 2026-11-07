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
