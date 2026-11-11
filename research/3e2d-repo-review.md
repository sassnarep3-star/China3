# 3E2D repository review (main @ b677a91)

Session `arena/3e2dbf57-china3`. No sibling-owned file edited.

## Scope

Read COORDINATION.md (2,397 lines), scanned all remote branches + 17 open PRs,
audited canonical data/formulas/source links line by line.

## Findings

1. **Canonical engine sound.** `scripts/e347_costs.py` formulas re-derived:
   spread = usd×(ask−mid)/ask; wire = min(260, max(50, usd×ask/1000)) + 150 CNY.
   Old-board spot check ($10k convert+wire $53.36 at 6.6606/6.6886) recomputes
   exactly. No arithmetic error found.
2. **Source register sound.** `data/e347_sources.csv` S01–S41: 20 load-bearing
   pages re-fetched live (T01–T07, T09, T12, T13, T17, T19, T20, T25–T30, T32,
   T35) — all reachable, figures match. Remainder carried as excerpt (F11).
3. **Ladder sound.** `data/e347_costs.csv`: 40 increments × priced methods;
   blanks (L12/L13) correctly blank, never zero. 3E2D re-prices at the 20:50
   board (M01 $53.37/$898.75) — difference is board movement only.
4. **Irregularities confirmed** (see `3e2d-flagged.html`):
   - 3E2D-IR-01: older layers misstate personal s.988 gain as ordinary
     (DF25-IR-01). Corrected treatment on `3e2d-tax.html` (T31).
   - 3E2D-IR-02: IRS 2025 average 7.129 vs Fed 7.1875 (DF25-IR-03).
   - 3E2D-IR-03: stale `dashboard/archive.html` risk (DF25-IR-04); 3E2D-REQ-01.
5. **Open PRs** (#84, #78, #72, #67, #66, #61, #59, #58, #57, #50, #34, #32,
   #25, #18, #15, #8, #6) are parallel editions; `main` already contains later
   merged work. This session merges none of them.
6. **b579 claim respected.** `origin/arena/b579901a-china3` claims shared files
   (`scripts/e347_build.py`, `scripts/e347_data.py`, `index.html`,
   `dashboard/*.html`). 3E2D touches none of them; requests logged as
   3E2D-REQ-01/REQ-02 in COORDINATION.md.

## Verdict

Canonical dashboard figures verified; 3E2D layer adds a fresh 20:50-board
repricing + corrected s.988 treatment without disturbing shared files.
