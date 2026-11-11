# E0F4 — independent line-by-line audit of PR #49

Session `arena/e0f4ee29-china3` (`session-e0f4ee29`), 2026-11-11.
Audited object: open PR [#49](https://github.com/sassnarep3-star/China3/pull/49), branch `arena/76e3e41f-china3`,
head commit `5cf4629245ef033bacd83923b26c4f620e04393a` ("76e: same-day source re-check (11 Nov), recomputed
$10k–$400k ladder, 7 findings, CI scope fix"), created 2026-11-11T02:37:18Z.
Audit output: this file, [`data/e0f4_76e_audit.csv`](../data/e0f4_76e_audit.csv) (38 audit records), and the
mobile page [`e0f4-76e-audit.html`](../e0f4-76e-audit.html). Gate: `python3 scripts/verify_e0f4_audit.py`.

This audit is **read-only** against the PR: no `76e-*` file was created, edited or deleted by this session,
and the PR was not merged (the final-integration role is claimed by `arena/5a59401a-china3` as of
2026-11-11T02:29:59Z). All fetches below were made by this session on 2026-11-11 (UTC) using a
page reader against the official sites; timestamps are approximate to the minute.

## Method

1. **Diff review.** The full 1,454-line diff was read: 12 files (new page, its CSS, builder, verifier, CI
   workflow, 3 data CSVs, research memo, `verify_m5f19_site.py` check J rewrite, `COORDINATION.md`
   conflict-marker resolution, regenerated `dashboard/archive.html`).
2. **Arithmetic, re-derived from first principles** with Python `decimal` (ROUND_HALF_UP), not by importing
   the repo's engines. Convention (as stated in the PR's own memo): `spread = amount × (ask − (bid+ask)/2) / ask`;
   `wire CNY = min(260, max(50, amount × ask × 0.001)) + 150`; `total = spread + wire/ask`;
   `fx_gain = amount × (1 − ask / 7.189)` (IRS 2024 average, China Yuan).
   Boards re-read live during this audit: 2026-11-11T10:25:02 Beijing (bid 666.30 / ask 669.11 per 100) and
   the recorded 2026-11-10T17:39:58 snapshot (bid 665.71 / ask 668.51 per 100).
3. **Sources, re-fetched in full.** All 18 official pages the PR re-checked were fetched again by this session
   and read; the PR's `data/76e_recheck.csv` verdicts were compared against what the pages say today.
4. **HTML/CSV parity** between `76e-verification.html`, `data/76e_costs.csv`, `data/76e_recheck.csv`,
   `data/76e_findings.csv`.
5. **Repository review.** Conflict-marker reconstruction (see A32), Archive generator behaviour (A34),
   check J semantics (A35), internal cross-references (A36, A11), and grep-based confirmation of the F06
   finding across the six live pages named there.
6. **CI.** PR #49 checks listed via `gh pr checks 49` at 2026-11-11T02:38Z: 16/16 green, deploy skipped
   (pull requests do not deploy).

## Result

**PR #49 is safe to merge.** Every figure it publishes reproduces to the cent from the official inputs; all 18 of
its source verdicts were independently re-verified against the live official pages this session; its findings
F01–F07 are verified as factually grounded where checkable; the `COORDINATION.md` conflict-marker resolution
loses no content; its CI is green. The defects found are: one 6-cent typo in a research memo (A36), a mislabeled
Archive entry it does not control (A34), an over-permissive token rule in the CI fix it ships (A35, safe-sided),
and a stale `as-of` string in a file it does not own (A11/F05, already flagged by the PR itself).

## Defects and irregularities (all flagged, none blocking)

| ID | Severity | Where | What it is |
|---|---|---|---|
| A36 | cosmetic | `research/76e-verification.md` | States the 10 Nov board gives "28,037.34"; the CSV, the page and this recomputation all give **28,037.28**. Page itself is correct. |
| A34 | low | `dashboard/archive.html` | The generator's catch-all regex files the newest layer (`76e-verification.html`) and will file this page under "First editorial pages — Earliest pass; partly corrected later." The canned note is false for both. |
| A35 | low | `scripts/verify_m5f19_site.py` (check J) | Claim-aware rewrite is sound; any path-like token in a branch's board block (including a link *request*) counts as "claimed". Over-permissive, safe-sided. |
| A11/F05 | cosmetic | `dashboard/sources.html` | eCFR "up to date as of 11/06/2026" is stale (live: 11/09/2026). PR #49 flags it (F05); it is not its file to fix. |
| A37 | resolved | `main` @ `6750ddb` | Literal merge-conflict markers in `COORDINATION.md` for ~1 hour (PR #46 defect). PR #49 fixes them; no repo validator checks `*.md` for markers — this session ships such a gate in its own CI. |
| A04 note | artifact | `data/e347_costs.csv` | 7 of 400 `known_cost_pct` cells differ at the 4th decimal from this session's `decimal` recomputation (float vs decimal rounding). Monetary cells: 1,320/1,320 match to the cent (1,720 cells including the pct column). |

## What this audit does not do

- It does not merge PR #49, and it did not edit any file in it.
- It does not re-price any route other than L01/L03 (the PR's own limitation, restated).
- It does not verify bank policies not published (receiving U.S. bank fees, intermediary fees — blank everywhere, by design).
- It does not decide which lawful route applies to the user's money; that turns on where the money came from
  (dashboard flag U01), which the brief does not state.
- It is not legal, tax or investment advice. Every number above is traceable to the official pages listed in
  `data/e0f4_76e_audit.csv` (all fetched and read on 2026-11-11) or to the repository files named.
