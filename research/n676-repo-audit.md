# n676 — repository audit, 2026-11-11

Audited at commit `d9763dca` (`main`, PR #49 merged 2026-11-11T02:37Z) on branch
`arena/676d2a67-china3`, before any content was written in this session.

Every number below was measured on the tree with the command shown. Nothing is inherited.

## 1. What the repository is

```
$ find . -name '*.html' -not -path './.git/*' | wc -l
98                     (82 at the repository root)
$ ls data/*.csv | wc -l
85
$ ls scripts/verify_*.py scripts/validate_data.py scripts/check_links.py | wc -l
15
$ ls .github/workflows | wc -l
17
$ du -sh --exclude=.git .
8.2M
$ wc -l COORDINATION.md
1406
```

This is a research repository, not an application. It has accumulated **at least twenty**
concurrent agent sessions since 2026-11-07, each of which produced its own namespaced layer
(`a513-*`, `c3x-*`, `c5bf-*`, `d646-*`, `deep-*`, `e347`/`dashboard/`, `m5f19-*`, `s436_*`,
`s775-*`, `schedule-*`, `76e-*`, `docs/`, …), its own validator and its own CI workflow. GitHub
Pages serves `main` at the repository root (`gh api repos/.../pages` → `status: "built"`,
`source: {branch: "main", path: "/"}`).

| # | Finding | Severity | Action taken here |
|---|---|---|---|
| A1 | 98 HTML files at 82 root paths, 85 CSVs, 15 validators, 17 workflows. A reader cannot tell which layer is current. | High — usability | The n676 layer is self-contained and links to the shared `dashboard/archive.html` for everything else. It does not delete or rewrite any sibling file. |
| A2 | Nine different headline totals for the same two transfers are live simultaneously. | High | Measured and published as N676-F02 with the per-figure file counts. |
| A3 | `data/cost_steps.csv` and `data/d646_methods.csv` still instruct a two-year staged emigrant remittance cancelled in 2014. | High — substantive | Measured and published as N676-F01. Sibling-owned, so not edited; correction request logged on the board. |
| A4 | No `LICENSE`. | Medium — legal | **Flagged, not fixed.** Choosing a licence is the owner's decision. Recorded here for the third time (earlier audits A3). |
| A5 | BOC's "Middle Rate" column is not the mid-point of its own buying and selling rates, and several layers call it a fair value. | Medium | Published as N676-F03. The n676 pages compute their own mid-point and say so. |
| A6 | The USD 50,000 figure is used for two unrelated rules — the individual convenience amount and the institutional profit-remittance document threshold. | Medium | Published as N676-F05. The n676 methods table separates them (M03 vs M09). |
| A7 | 汇发〔2014〕2号 is published on a branch site marked （已修改）, and the page does not certify that its amendment list is exhaustive. | Medium | Published as N676-F04. Section 6 — the part relied on — is not among the amended items. |
| A8 | `COORDINATION.md` was committed to `main` with literal merge-conflict markers in an earlier session and no validator checked for them. | Medium | The n676 verifier scans every n676 file **and** `COORDINATION.md` for `<<<<<<<`, `=======` and `>>>>>>>`. A repo-wide gate over `*.md` is logged as a request. |
| A9 | 17 workflows run on `branches: ["**"]`, so several sibling verifiers execute on every pull request and some fail on branches whose declared scope they do not know about. | Medium — CI noise | The n676 workflow is namespaced to paths this session owns. One sibling verifier (`verify_m5f19_site.py` check J) was already made claim-aware by an earlier session and passes here. |
| A10 | Three load-bearing pages were not re-opened this pass (the 2020 guidelines PDF, 财税〔2008〕132号, the CBP cash page). | Medium | Recorded with `fetched_today = no` in the register and left **blank** on the pages. No claim rests on them. |

## 2. Baseline check — what passed before this session wrote anything

Run on `d9763dca`, unmodified:

| Check | Result |
|---|---|
| `scripts/e347_verify.py` | PASS — 440 cost rows over 11 routes recomputed exactly; 8 pages, 659 table rows sourced, 380 blank values flagged, 2139 links resolved |
| `scripts/verify_m5f19_site.py` | PASS — 10 checks, 0 failures |
| `scripts/verify_76e.py` | PASS — 40 ladder rows recomputed |
| `scripts/verify_dashboard.py` | PASS — 17 verification records, 40-row ladder re-derived |
| `scripts/verify_final_integration.py` | PASS — 640 cost rows, 16 methods, 65 steps |
| `scripts/verify_cost_tables.py` | PASS — 800 ladder rows, 39 sources |
| `scripts/validate_data.py` | OK — 27 sources, 22 channels, 25 tax items, 15 penalties, 19 flagged |
| `scripts/check_links.py` | OK — 9 pages, 27 external URLs, all internal links resolve |

The baseline is green. Nothing in this session's work depends on fixing a sibling layer first.

## 3. What this session added, and what it deliberately did not touch

Added, entirely inside the `n676` namespace:

```
data/n676_{sources,questions,methods,steps,flags,ladder}.csv
scripts/n676_{engine,data,build,verify}.py
n676-{summary,questions,methods,costs,steps,tax,flagged,sources}.html
assets/n676.css
.github/workflows/n676-verify.yml
research/n676-{verification,repo-audit}.md
```

Appended (append-only, shared by design): `COORDINATION.md`.

Not touched: `index.html`, `dashboard/**`, `legacy-index.html`, `README.md`,
`EXECUTIVE_SUMMARY.md`, `docs/**`, `scripts/e347_*`, and every other session's files.
`scripts/n676_verify.py` check K enforces this on every run by diffing against the merge base with
`origin/main` and failing on any pre-existing file outside the namespace.

## 4. Correction requests logged rather than made

Two requests go to the shared-file owner and to sibling owners. Neither was actioned here because
the board reserves shared outputs to the final integration session.

1. **Nav entry.** One link on the shared landing page to `n676-summary.html`, labelled
   *"Decision brief, 11 Nov 2026"*. Until then the layer is reachable by direct URL and appears on
   the regenerated `dashboard/archive.html`, which discovers root pages automatically.
2. **Superseded banners.** `data/cost_steps.csv` M03 steps 5-7 and `data/d646_methods.csv` M05
   should be corrected or marked superseded against 汇发〔2014〕2号 §6.
3. **A repo-wide conflict-marker gate.** `grep -E '^(<<<<<<<|=======$|>>>>>>>)' **/*.md` in CI.
   `main` carried literal markers for about an hour in an earlier session and nothing caught it.

## 5. Limits of this audit

- It is a structural and figure-level audit. It does not certify every row of all 85 CSVs; it
  measured the specific claims that this session's pages depend on, plus the ones that contradict
  a source re-read today.
- External URL reachability was checked by fetching 19 pages directly. `scripts/check_links.py`
  skips HTTP checks in this sandbox (offline build path).
- The cost model is Bank of China's published board and published personal tariff. It is not a
  quote from the reader's bank, and intermediary charges are unknown to everyone.
