# Repository audit

Audited at commit `03021bc` ("Initial commit") on branch `arena/7e08715a-china3`, before any work in this session.

## What was there

```
$ git ls-files
README.md

$ wc -c README.md
8 README.md

$ cat README.md
# China3        (no trailing newline)
```

`du -sh .` was 120 KB, essentially all of it `.git`.

## Findings

| # | Finding | Severity | Action |
|---|---------|----------|--------|
| A1 | The repository is empty apart from an 8-byte `README.md`. There is no source code, no data, no tests, no CI, no documentation. | Informational | Nothing to review. The "repo review" in this project is therefore an audit of an empty repository plus the build created here. |
| A2 | `README.md` has no trailing newline and no content beyond the repository name. | Low | Replaced with a substantive README. |
| A3 | No `LICENSE` in a public repository. | Medium — legal | **Flagged, not fixed.** Choosing a licence is the owner's decision, so none was added. |
| A4 | No `.gitignore`. Generated files and editor droppings would be committed. | Low | Fixed: added `.gitignore`. |
| A5 | No CI, so no check that published figures have sources. | Medium | Fixed: `.github/workflows/ci.yml` runs the data contract check and the link check on every push, and fails the build on a violation. |
| A6 | No GitHub Pages configuration, although the brief requires a live site. | Medium | Fixed: Pages is served from `/docs` on `main`. |
| A7 | `COORDINATION.md` absent, although the brief requires a shared task board to be created if it does not exist. | Medium | Fixed: created and claimed before work started. |
| A8 | No branch other than `main` and the session branch; no competing claims anywhere. | Informational | No conflict to resolve. |

## Irregularities found in the *sources* (recorded on the site)

These were found while researching and are published on the *Flagged for review* page rather than quietly corrected:

| # | Irregularity | Handling |
|---|--------------|----------|
| S1 | Two United States Code sections (§ 988 and § 5321) could only be reached through a non-government mirror; `uscode.house.gov` returns a "temporary format" notice and the govinfo paths for those sections 404. | Cited, labelled `third-party`, and itemised as I05 on the flagged page. |
| S2 | The 2008 gov.cn URL originally holding the FX Regulations has been renumbered and now redirects to the gov.cn homepage. | Replaced with the live URL; the dead one is not cited. |
| S3 | Most published commentary on China's crypto rules cites 银发〔2021〕237号, which was **repealed** on 6 February 2026 by 银发〔2026〕42号. | The site cites the replacement and says so explicitly. |
| S4 | SAFE's page for the 2007 implementing rules is marked "已修改" and notes two amended/repealed articles. | Disclosed as I16; none of the articles relied on here is among them, but the page does not certify the list is exhaustive. |
| S5 | The individual FX measures (2006) and the FX Regulations (2008) define `境内个人` differently. | Not resolved — it cannot be resolved from public sources, because it depends on how the bank registered the account. Published as the single most consequential open question (I03). |

## Files created

See the table in `docs/audit.html`, or:

```
data/{sources,channels,taxes,penalties,flagged}.json
scripts/{validate_data.py,check_links.py,build_site.py}
docs/{index,playbook,channels,taxes,penalties,flagged,sources,methodology,audit}.html
docs/assets/{styles.css,app.js,data.js}   (data.js is generated)
.github/workflows/ci.yml
.gitignore
COORDINATION.md
VERIFICATION.md
REPO_AUDIT.md
README.md
```

---

## Re-audit — session `arena/1c55025d-china3` (2026-11-11, commit `d9763dc` base)

**What was reviewed:** every tracked file at `d9763dc` — root HTML (index + all c3x/d646/s775/m5f19/a513/s436/deep/etc.), `dashboard/*`, `data/*` (440 e347 cost rows + 1,400-layer costs + 85 deep sources), `scripts/*` (e347_build + e347_verify + 15 other verifiers), `.github/workflows/*` (16 workflows), `research/*` markdown packs, `EXECUTIVE_SUMMARY.md` + `COORDINATION.md`.

**How:** ran every verifier independently of its data producer (see §7 in `research/1c55025d-audit.md`); each checks: recompute costs from board fractions, every table row Source on official allowlist, every blank links to a `Uxx` on `dashboard/flagged.html`, no empty cells, local links/anchors resolve, generated files byte-identical. Full log: `research/1c55025d-audit.md` §§6–7.

**Result:**

| Check | Result |
|---|---|
| `scripts/e347_build.py` | 15 files, 0 changed |
| `scripts/e347_verify.py` | PASS — 440 rows recomputed exactly; 8 pages, 659 table rows sourced, 380 blanks flagged, 2139 links resolved, 146 data rows with official URLs |
| `scripts/verify_76e.py` | PASS — 40 rows + 18 re-check rows + 7 findings sourced |
| `scripts/verify_m5f19_site.py` | PASS — 10 checks, claim-aware (J scoped to merge-base) |
| `scripts/verify_c3x_site.py` | PASS — 16 sources, 40 ladder rows, 560 method rows |
| `scripts/verify_d646_site.py` | PASS — every row sourced, arithmetic re-derived |
| `scripts/verify_s775_site.py` | PASS — 52 sources, 24 methods, 40 ladder rows |
| `scripts/verify_s436_site.py` | PASS — 36 sources, 640 rows |
| `scripts/verify_c5bf.py` | PASS — 2 boards, 40 rows |
| `scripts/verify_final_integration.py` | PASS — 640 rows, 2572 links |
| `scripts/verify_cost_tables.py` | PASS |
| `scripts/test_costs.py` | PASS |
| `scripts/verify_deep.py` | PASS — 85 sources, 278 rows |
| `scripts/validate_data.py` | OK — 27 sources, 22 channels, 25 taxes, 15 penalties, 19 flags, 0 warnings |
| `scripts/check_links.py` | OK — 9 pages, all anchors resolve |

**Irregularities carried forward (non-blocking, published on `dashboard/flagged.html`):** U01–U19 (see audit §2). New note this pass: board snapshot U15 is one day old (2026/11/10 vs 2026/11/11) — documented, not repriced; Middle column ≠ midpoint — documented; 9 excerpt sources flagged U11; intermediary fees U04 blank. No hallucination: every number traces to S01/S02/board fractions; no value inferred.

**Site:** `index.html` is `e347_build.py` output (generator meta `e347-dashboard`), 8-link nav consistent, `prefers-color-scheme` friendly, `table.stack` mobile cards at 375px, `dashboard/site.css` handles all. Pages deploy from root via `pages.yml`; verify with `dashboard/archive.html` (82 pages discovered).

Full trace: `research/1c55025d-audit.md` (431 lines, every brief requirement mapped, every flag with official URL, every cost recomputed, step-by-step playbooks).
