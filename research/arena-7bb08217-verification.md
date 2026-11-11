# Session `arena-7bb08217-china3` — verification log (2026-11-11)

Scope: final quality pass on `arena/7bb08217-china3`, cut from `main` at `f6ae79e` (PR #46 merge), re-based onto `15a7986`
(PR #47, the `m5f19` edition) and finally rebuilt on `1638a47` (PR #48 + PR #49 + PR #51 + PR #52 + PR #53 + PR #54 + PR #60). **No data file, no figure, no source register, no shared file was merged or left modified by this
session.** The one integration task this session performed was **handed back** to the live `5a59` final-integration claim
(see "B3 — handed off, not merged" below).

## B2 — inherited validator/generator suite on the tree as it stood (all re-run 2026-11-11)

All of the following PASS at the merged `main` base this session verified (the suite was run both before the rebase
excursions and is expected to be re-run by CI on the merge; results as observed):

| Gate | Result |
|---|---|
| `scripts/validate_data.py` | OK — 27 sources, 22 channels, 25 tax items, 15 penalties, 19 flagged items, 0 warnings |
| `scripts/check_links.py` | OK — 9 pages, 27 external URLs (offline mode) |
| `scripts/verify_deep.py` | PASS |
| `scripts/verify_cost_tables.py` | PASS — 800 ladder rows |
| `scripts/verify_d646_site.py` / `verify_s436_site.py` / `verify_final_integration.py` | PASS |
| `scripts/verify_dashboard.py` | PASS — generated pages byte-identical |
| `scripts/verify_s775_site.py` / `verify_c3x_site.py` / `verify_a513.py` / `verify_completion.py` / `a502_audit.py` / `verify_c5bf.py` | PASS |
| `scripts/verify_m5f19_site.py` | checks A–I and K PASS; **check J FAILs on this branch if and only if shared files differ from the merge base** — see disposition below |
| `scripts/e347_verify.py` | PASS (440 cost rows recomputed; 658 table rows sourced; 380 blanks flagged) — both before and after this session's (later reverted) generator edit |
| `scripts/test_costs.py` | PASS — 1,400 combinations |
| Repo-wide local-link sweep (this session) | 89 pages, 2,693 `href`/`src` local references — **0 broken** |

## B4 — live-site and official-source checks (fresh, via this session's page-fetch tool)

- **Sandbox egress to `sassnarep3-star.github.io` fails** (`curl` → `000`), matching earlier sessions. Pages evidence:
  GitHub Pages API (`status: built`, `build_type: legacy`, `main:/`), Actions on `main` all `success` at 2026-11-11T02:34Z
  (incl. `Deploy static guide to GitHub Pages` run 42946951994 and `pages-build-deployment` 42946950547), plus independent
  fetches through this session's tool:
- **Live landing page** — serves the e347 dashboard content (headline figures, situation table, per-row official links).
- **Live `dashboard/archive.html`** — 81–82 pages listed; the nine `m5f19-*` pages (and, after PR #49, `76e-verification.html`)
  appear under the catch-all **"First editorial pages"** group with the note "Earliest pass" — reachable, but mislabelled.
- **`m5f19-dashboard.html`** — live and substantive (Article 65 classification; $53.38 / $899.01 headline figures).
- **Official sources re-read fresh on 2026-11-11** (not inherited):
  - IRS — Report of Foreign Bank and Financial Accounts: FBAR (FinCEN Form 114) required when aggregate foreign financial
    accounts exceeded **USD 10,000** at any time in the calendar year; due **15 April**, automatic extension to **15 October**;
    e-filed via FinCEN BSA E-Filing, **not** with the tax return; records kept 5 years. Matches the site's published FBAR rows.
    <https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar>
  - Bank of China — 外汇牌价 (USD), fetched 2026-11-11 10:25:02, per CNY 100: 现汇买入 666.3, 现钞买入 666.3, **现汇卖出 669.11**,
    现钞卖出 669.11, 中行折算价 671.91 (i.e. 6.6630 / 6.6630 / 6.6911 / 6.6911 / 6.7191 per USD).
    This is **not** the snapshot the site's cost tables are tied to (2026-11-10 17:39:58 board: 6.6571 / 6.6851 / 6.6711).
    The published tables are deliberately tied to the recorded board they derive from; the drift is expected and is **not** an
    error in the tables. PR #49 repriced a re-check at today's board ($53.42 / $901.20) and flagged the F03 one-day-old status;
    it likewise did not reprice the dashboard tables.
    <https://www.boc.cn/sourcedb/whpj/>

## B3 — handed off, **not** merged (protocol: a live claim owns the shared files)

This session initially implemented the integration gap it found: PR #47's nine `m5f19-*` pages were unlinked from the landing
page and README and (at deploy time) globbed into the Archive under "First editorial pages"; `scripts/e347_build.py` had no
`^m5f19-` Archive group. The implementation (one additive `ARCHIVE_GROUPS` row, one additive landing-page note honoring
**M5F19-REQ-01**, generator-regenerated `index.html` + `dashboard/archive.html`, one additive README line) was built, rebuilt
and verified locally — and then **discovered to duplicate an overlapping live claim**:

- **`arena/5a59401a-china3` (`5a59`), claim commit `1ffa64e` at 2026-11-11T02:29:59Z** claims the **final-integration role**
  plus `5a59-*`, and explicitly: additive `README.md` / `COORDINATION.md` / **regenerated `dashboard/archive.html`**
  (visible in `arena/76e3e41f`'s claim scan, merged to `main` in PR #49 at 02:37Z). Its branch exists on the remote with no
  commits beyond the claim; it is **inside the 60-minute take-over window**.
- This session's claim (originally authored 02:34Z) was written **without sight of that claim** — it reached `main` only at
  02:37Z (PR #49), after this session had already fetched. 76e and B8720152 both deferred the integration role to `5a59`;
  the conforming course is the same.

Therefore this session:

1. **Reverted** `scripts/e347_build.py`, `index.html`, `dashboard/archive.html`, `README.md` back to `origin/main` (`1638a47`)
   byte-for-byte — nothing of another layer's file is merged or modified by this branch.
2. **Handed the integration to `5a59`** in machine-applicable form: `research/arena-7bb08217-m5f19-reachability.patch`
   (the exact additive changes, `git apply`-able with `--3way`), plus the recipe below.
3. Kept only non-shared deliverables: this log, and board records in `COORDINATION.md` (append-only).

### Handoff recipe (for `5a59` or whoever lands the integration)

1. In `scripts/e347_build.py`, insert before the catch-all `(r".", …)` in `ARCHIVE_GROUPS`:
   `(r"^m5f19-", "M5F19 independent re-verification (session 5f1925df)", "Fresh primary-source re-verification (2026-11-10); Article 65 classification; headline figures match this dashboard."),`
2. Optionally add a `^76e-` group ("76e same-day source re-check") for the same reason — `76e-verification.html` currently
   sits in "First editorial pages".
3. In `page_index()`, add one additive paragraph (no nav change; `scripts/e347_verify.py` requires exactly 8 nav entries):
   `<p class="note"><a href="m5f19-dashboard.html"><b>M5F19 — independent re-verification &amp; cost reconciliation (10 Nov 2026)</b></a> …</p>`
   This honors M5F19-REQ-01 as a landing-page note rather than a 9th nav entry (see the constraint above), and likewise
   satisfies 76E-REQ-01's intent; a true 9th nav entry would require changing `NAV` **and** the nav contract in
   `scripts/e347_verify.py` together.
4. `python3 scripts/e347_build.py` then verify with `python3 scripts/e347_verify.py`; expect "e347 build: N files" with only
   `index.html`, `dashboard/archive.html` changed; confirm one archive row per page.
5. `README.md`: one additive pointer to the M5F19 edition (sentence supplied in the patch).
6. **Never merge by hand.** Two separate regens merged textually (PR #48's then this session's) produced a duplicated
   Archive (m5f19 rows twice, in both groups) within 30 minutes; always re-run the generator after merging main.

## Flagged observations (non-blocking; owners named)

- **RC-16 (open, owner `docs/` pipeline):** 22 anchors in `docs/playbook.html` and `docs/methodology.html` point at
  `docs/sources.html#S01…#S27`; that page renders its list client-side and declares no such ids.
- **Pages double deploy (open):** repository Pages setting is `build_type: legacy` while the Actions workflow also deploys;
  both publish the same tree.
- **Conflict markers on `main`:** repaired by 76e (PR #49); 76e also recommends a `grep -E '^(<<<<<<<|=======$|>>>>>>>)'` CI
  gate over `*.md` — still absent, recommended to the workflow owner.
- **`verify_m5f19_site.py` check J** failed on sibling integration branches by construction (reported by B8720152 on PR #48;
  this session saw the same). **PR #49 rewrote it claim-aware** (additive files, append-only board and regenerated archive
  allowed; other layers' pre-existing files still fail) — the request was actioned correctly. Note: this session's earlier
  copy of the verifier (base `15a7986`) still has the hard-coded version; on this branch, after the revert, checks A–I + K
  pass and J is immaterial because no foreign file differs from the merge base.
- **Today's BOC board has moved** relative to the recorded snapshot (6.6911 vs 6.6851 selling). Expected drift; repricing
  needs a fresh dated board reading and a rebuild; do not edit figures in place.
- **Merge-marker near-miss in this session:** the textual auto-merge of two generator outputs duplicated the Archive rows;
  caught before commit by rebuild + grep. Worth stating plainly because it is exactly the failure mode that put conflict
  markers on `main` earlier today.
- **Sandbox cannot reach the live site or external URLs**; external verification here is via Actions + Pages API + an
  independent page-fetch tool (used above).
