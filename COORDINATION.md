# Coordination board — Arena session branch

Session: `arena/db516e23-china3` (Arena-fixed branch)

## Tasks and ownership

| Task | Status | Owner session | File scope / outcome |
|---|---|---|---|
| Research official CNY-to-USD transfer options and tax/reporting distinctions | needs review | arena/db516e23-china3 | `research/**`; source links and verification notes prepared on this branch, not merged to `main` |
| Create dashboard site and table comparisons | needs review | arena/db516e23-china3 | `index.html`, `routes.html`, `taxes.html`, `sources.html`, `review.html`, `assets/**`; duplicate scope was already completed and published by another session on `main`; this branch's duplicate PR was closed to preserve published work |
| Final integration and GitHub Pages publication | done (by existing main integration) | arena/dd766f7b-china3 | Existing main integration merged in PRs #1 and #3; see recorded sources and deploy below. This session did not modify `main` or claim the other session's work. |

## Verification and handoff log

- Initial checkout at session start contained only an 8-byte README and no coordination file; working tree was clean. The claim was committed and pushed immediately to the fixed Arena branch.
- While this session researched and built a duplicate dashboard, the remote `main` branch advanced through PR #1 and PR #3, completing the same task. On fetching the latest main, its existing `COORDINATION.md` was read. The main site files were already owned by `arena/dd766f7b-china3` and documented as done; no attempt was made to overwrite those files.
- Duplicate PR #4 (`https://github.com/sassnarep3-star/China3/pull/4`) conflicted with the published main site and was closed without merge. PR body documents the handoff and live deployment. No changes from PR #4 are included on main. This avoids replacing another session's completed site.
- Existing integration recorded in main: PR #1 (`https://github.com/sassnarep3-star/China3/pull/1`) merged 2026-11-07; PR #3 (`https://github.com/sassnarep3-star/China3/pull/3`) recorded the successful Pages deployment. Main commit `4a92baaba81f52264684d1dd27ca77648703128e` has latest Pages build `https://github.com/sassnarep3-star/China3/actions/runs/42411871234` with conclusion `success`; GitHub Pages API reports `status: built`, URL `https://sassnarep3-star.github.io/China3/`.
- Independent work on this branch: reviewed primary official sources from SAFE, PBOC, State Taxation Administration, IRS and FinCEN; produced a route analysis, tax/cost distinctions, an official source register, a review queue, responsive site and validation script. `python3 scripts/validate_site.py` passed (5 pages; internal targets/fragments resolved; every route/tax/review table data row directly links to an official source; 19 sources registered). `git diff --check` passed. Local HTTP smoke test returned 200 for all pages, CSS and analysis.
- Official sources personally checked via government source text include SAFE 2007 individual FX Q&A, 2009 anti-splitting circular, 2015 Q4 transcript, 2014 capital-account personal property policy, 2019 enforcement cases, 2013 SAFE/SAT external-payment tax filing rule, 2017 bank-card cash withdrawal Q&A; PBOC 2020 cross-border RMB notice; PRC Individual Income Tax Law; IRS Publication 54, worldwide income, FBAR, Form 8938 and foreign gift guidance; FinCEN FBAR guidance. Direct links and claim boundaries are documented in this branch's `sources.html` and `research/analysis.md`.

## Irregularities / unresolved facts

- The original wording “considerable taxes” was unsupported by a tax assessment, named tax, amount or source-of-funds details. Neither this branch nor the existing main site treats it as verified.
- SAFE's USD 50,000 individual FX facilitation amount is distinct from tax and a universal hard cap; authentic transactions above may require evidence and bank review. Current bank-level process and individual eligibility remain fact-specific.
- No exact CNY/USD quote, spread, wire/correspondent/receiving fee or personal tax amount can be verified without the bank, amount, identity/status, transaction source and records. These values are left blank and flagged on this branch.
- SAFE English translation pages state that the Chinese original prevails if interpretation differs. Confirm current Chinese rules and local bank/SAFE procedures before action.
- This branch's supplemental analysis/site files are retained for reference but were not published. The linked main site and previous session's coordination record are the authoritative published deliverables.
