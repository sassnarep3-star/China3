#!/usr/bin/env python3
"""Final-integration edits for the deep-research pass (namespaced, additive).

All deep-research outputs live under distinct filenames so that merging `main`
never overwrites another session's work. This script ONLY appends small linking
sections to shared files, writes a self-contained stylesheet and dashboard
script, and adds a separate verification workflow. It never edits another
session's CSS, data, scripts or Pages workflow.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_deep_site as bs  # noqa: E402  (regenerates CSVs + deep pages deterministically)

MARKER = "<!-- deep-research-integration-v2 -->"

DEEP_PAGES = [
    ("deep-executive-summary.html", "Executive summary", "Important details, ranked recommendation and requirement coverage"),
    ("deep-china-rules.html", "China rules", "50 SAFE / PBOC / State Council rules, line by line"),
    ("deep-us-tax.html", "US tax & reporting", "28 IRS / FinCEN / Treasury / eCFR rules"),
    ("deep-channels.html", "All channels", "35 conversion methods with pros, cons and penalty exposure"),
    ("deep-penalty.html", "Penalty breakdown", "35 separately verifiable cost and penalty layers"),
    ("deep-findings.html", "Analysis", "22 sourced findings and the deep analysis"),
    ("deep-review.html", "Flagged for Review", "23 irregularities, each with an official source link"),
    ("deep-sources.html", "Official sources", "84 primary sources with verification method"),
]


def links_html():
    items = "".join(
        f'<li style="margin:7px 0"><a href="{p}" style="font-weight:700;text-decoration:none">{html.escape(t)}</a>'
        f' <span style="color:#5b6b82">— {html.escape(d)}</span></li>'
        for p, t, d in DEEP_PAGES)
    return f'''{MARKER}
<section style="max-width:1100px;margin:38px auto;padding:26px;border:1px solid #dfe7f2;border-radius:16px;background:#fff">
  <div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#4067bd;font-weight:800">Deep research · integration session</div>
  <h2 style="font-size:22px;margin:8px 0 6px">Category subpages — verified line by line</h2>
  <p style="color:#53657f;margin:0 0 12px">A second research pass added without altering any earlier page. Every table row links to an official source; unconfirmed values are blank and listed on <a href="deep-review.html">Flagged for Review</a>.</p>
  <ul style="padding-left:20px;margin:0;line-height:1.7">{items}</ul>
  <p style="font-size:12px;color:#7c899b;margin:14px 0 0">Also see the machine-readable data in <code>data/*.csv</code>, the memos in <code>research/</code>, and the shared task/verification log in <code>COORDINATION.md</code>.</p>
</section>
'''


def tiny_notice(target, heading, body):
    return (f'{MARKER}\n<div style="max-width:1100px;margin:22px auto;padding:14px 18px;'
            f'border:1px solid #ead8a6;border-radius:12px;background:#fff8e8;color:#664500">'
            f'<strong>{html.escape(heading)}</strong> {html.escape(body)} '
            f'<a href="{target}">Open the deep-research register →</a></div>\n')


def append_to_html(name, block):
    p = ROOT / name
    t = p.read_text(encoding="utf-8")
    if MARKER in t:
        t = re.sub(re.escape(MARKER) + r".*?(?=</body>)", "", t, count=1, flags=re.S)
    if "</main>" in t:
        t = t.replace("</main>", block + "</main>", 1)
    else:
        t = t.replace("</body>", block + "</body>", 1)
    p.write_text(t, encoding="utf-8")


def append_once(name, block, marker=MARKER):
    p = ROOT / name
    t = p.read_text(encoding="utf-8")
    if marker in t:
        t = t[:t.index(marker)].rstrip() + "\n"
    t = t.rstrip() + "\n\n" + block
    p.write_text(t, encoding="utf-8")


COORD_SECTION = '''<!-- deep-research-integration-v2 -->

## Integration session `session-c703e38c` — deep research pass

Branch: `arena/c703e38c-china3` (fixed by Arena; this branch is also the integration branch).
Board above belongs to other sessions and is preserved verbatim.

### Claim and scope

This session claimed T1–T9 on its own board (kept in the commit history at `786a8b3` /
`05ee625`), then acted as final integration session once the other sessions marked their
tasks `done`. All deep-research outputs use distinct filenames (`deep-*.html`,
`data/*.csv`, `data/deep_sources.json`, `scripts/*_deep.py`, `assets/deep-*.css|js`,
`.github/workflows/deep-research-verify.yml`) so that merging `main` does not overwrite
any other session's files. Shared files were restored to `origin/main`'s exact versions
before merging, then only additive linking sections were appended.

| Task | Status | File scope |
|---|---|---|
| T1 repo audit + coordination board | done | `COORDINATION.md` (append), `README.md` (append) |
| T2 China FX framework research | done | `research/china-framework.md`, `data/china_rules.csv` |
| T3 U.S. tax / reporting research | done | `research/us-tax.md`, `data/us_rules.csv` |
| T4 channels + penalty breakdown | done | `research/channels.md`, `research/penalty-breakdown.md`, `data/channels.csv`, `data/penalty.csv` |
| T5 verified data tables | done | `data/*.csv`, `data/deep_sources.json`, `scripts/build_deep_site.py` |
| T6 dashboard subpages + Flagged for Review | done | `deep-*.html`, `assets/deep-research.css`, `assets/deep-app.js` |
| T7 executive summary + analysis | done | `EXECUTIVE_SUMMARY.md`, `research/analysis.md`, `data/findings.csv` |
| T8 line-by-line re-verification, build, broken links | done | `scripts/verify_deep.py`, `.github/workflows/deep-research-verify.yml` |
| T9 PR → merge → Pages → record | pending | this file |

### Verification log

- Sources: 84 official pages registered in `data/sources.csv` / `data/deep_sources.json` /
  `research/sources.md`; every URL is on an official-domain allowlist enforced by
  `scripts/verify_deep.py`.
- Full text fetched: SAFE Ningxia 2022 Q&A; SAFE Tianjin 2024 individual-FX Q&A; SAFE
  Tianjin 2024 Q&A case (9); gov.cn PBOC Decree [2006] No. 3; SAFE FX Regulation (State
  Council Order 532) full text; PBOC 银发〔2026〕42号; PBOC 银发〔2021〕237号; IRS
  Gifts from foreign person; IRS Form 8938/FBAR comparison; eCFR 31 CFR 1010.821 (all
  chunks); IRS Publication 525.
- `scripts/verify_deep.py` checks: one official source URL per data row; URL registered in
  the source register; UNVERIFIED rows have blank values; generated HTML row counts match
  CSVs; every data row on every deep page has an official link; all 23 flagged ids appear
  on the Flagged for Review page; all 84 source ids appear on the sources page; and no
  broken local links across root and `docs/` HTML pages.
- Other sessions' CI (`scripts/validate_data.py`, `scripts/build_site.py`,
  `scripts/check_links.py`, `.github/workflows/ci.yml`) was run on the merged tree and
  passed; `docs/` was confirmed not stale.
- Local HTTP smoke test: every root HTML page, `docs/*.html`, `assets/deep-research.css`
  and `assets/deep-app.js` returned HTTP 200.

### Irregularities (published with links on `deep-review.html`; non-blocking)

IR-001 single fixed branch instead of `session-<id>/<task>` branches; IR-002 no
COORDINATION.md or prior data at session start; IR-003 Pages legacy source vs Actions
deploy; IR-004 `银发〔2021〕237号` repealed by `银发〔2026〕42号`; IR-005 two versions of
FX Regulation Art. 45; IR-006 two repealed anti-splitting circulars; IR-007 conflicting
official definitions of 境内个人/境外个人; IR-008 2026 FBAR inflation adjustment cancelled;
IR-009 no signed U.S.–mainland China FATCA IGA found; IR-010 eCFR authoritative but
unofficial; IR-011 no official "conversion tax" found; IR-012 current bank spread /
correspondent fees / CNY-CNH basis unverifiable (left blank); IR-013 add/add conflict and
rebase-flattening conflict resolved by abort without discarding work; IR-014 no case
facts; IR-015 current USD/CNY central parity unverified; IR-016 English paraphrases of
Chinese originals; IR-017 Wealth Connect / QDII eligibility unknown; IR-018 no manual
input vs conditional conclusions; IR-019 gift/inheritance character unknown; IR-020 2024
BOC fee promotion expired; IR-021 2004 property-transfer rules not exhaustively
re-checked; IR-022 CNY/CNH spread figures are historical; IR-023 several sources are
provincial SAFE branch Q&As.

### Merge / handoff log

- `origin/main` advanced from `4a92baa` to `3f62eeb` while this session was researching
  (PR #2, #5, #7 from other sessions). `git merge origin/main` was run on this branch;
  shared files were first restored to `origin/main`'s exact content, so the merge had
  **zero conflicts** and no other session's work was discarded.
- Two earlier conflicts: (a) `add/add` on `COORDINATION.md` with `arena/dd766f7b-china3`,
  resolved by preserving that board verbatim in this branch's earlier commit; (b)
  `git pull --rebase` attempted to flatten the resulting merge commit and re-conflicted —
  stopped, verified remote tip equalled local tip, `git rebase --abort`, no work lost.

### PR / merge / deployment record (filled by T9)

- PR link: _pending_
- Merge result: _pending_
- GitHub Pages deployment: _pending_
'''

README_SECTION = '''---

## Deep research pass (integration session `session-c703e38c`)

A second, deeper research pass was integrated without altering any earlier page. All
deep-research outputs use distinct filenames so that merging `main` never overwrites
another session's files.

| Page | Contents |
|---|---|
| `deep-executive-summary.html` | Executive summary, ranked recommendation, requirement coverage |
| `deep-china-rules.html` | 50 China-side FX/tax rules, one official link per row |
| `deep-us-tax.html` | 28 IRS / FinCEN / Treasury / eCFR rules, one official link per row |
| `deep-channels.html` | 35 conversion channels with pros, cons, limits, penalty exposure |
| `deep-penalty.html` | Conversion penalty decomposed into 35 verifiable cost layers |
| `deep-findings.html` | 22 sourced findings and analysis |
| `deep-review.html` | Clearly labelled **Flagged for Review** register (23 items, each with a source link) |
| `deep-sources.html` | 84 official sources with verification method |

Machine-readable data: `data/china_rules.csv`, `data/us_rules.csv`, `data/channels.csv`,
`data/penalty.csv`, `data/findings.csv`, `data/flags.csv`, `data/sources.csv`,
`data/deep_sources.json`. Research memos: `research/*.md`. Full executive summary:
`EXECUTIVE_SUMMARY.md`.

Build and verify locally:

```sh
python3 scripts/build_deep_site.py && python3 scripts/integrate_deep.py && python3 scripts/verify_deep.py
python3 -m http.server 8000 --bind 0.0.0.0
```

Headline findings: a passport-holding U.S. citizen is generally a 境外个人 whose FX
purchase from legitimate, tax-documented RMB income is not limited by the USD 50,000
convenience amount (but the 2008 State Council regulation defines 境内个人 differently —
see IR-007); no official source establishes a general tax on converting personal CNY
principal; the largest single monetary risk is a willful FBAR penalty of up to 50% of the
account balance; and `银发〔2026〕42号` repealed `银发〔2021〕237号`.
'''

WORKFLOW = '''name: Verify deep-research dashboard

on:
  push:
    branches: ["**"]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  deep-research:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Line-by-line verification of deep-research tables and links
        run: python3 scripts/verify_deep.py
      - name: Confirm deep-research pages are present and non-empty
        run: |
          for f in deep-executive-summary.html deep-china-rules.html deep-us-tax.html \
                   deep-channels.html deep-penalty.html deep-findings.html \
                   deep-review.html deep-sources.html assets/deep-research.css assets/deep-app.js; do
            test -s "$f" || { echo "missing or empty: $f"; exit 1; }
          done
'''

ADDITIVE_CSS = '''
/* deep-research-integration-v2 — additive styles only */
.tools{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.filter-label{font-size:12px;color:#66758a;display:flex;align-items:center;gap:7px}
input.filter{border:1px solid var(--line,#e2e8f0);border-radius:9px;padding:8px 11px;font:inherit;font-size:13px;min-width:200px;background:#fff}
input.filter:focus{outline:2px solid #b9c9ed;border-color:#315eff}
.rowcount{font-size:12px;color:#7c899b;white-space:nowrap}
table.data{min-width:1050px}
table.data th{white-space:nowrap}
table.data td{font-size:13px;line-height:1.55}
table.data td:first-child{font-weight:700;color:#233a5c;white-space:nowrap}
table.data tbody tr:hover td{background:#fafcff}
table.data td.src{white-space:nowrap;font-size:12px}
table.data td.src a{display:inline-block;margin:1px 6px 1px 0;padding:3px 8px;border-radius:7px;background:#edf3ff;color:#174fbf;text-decoration:none;font-weight:700;font-size:11px}
table.data td.src a:hover{background:#dbe7ff}
table.data td.status{white-space:nowrap}
.tag{display:inline-block;border-radius:999px;padding:3px 9px;font-size:10px;font-weight:800;letter-spacing:.03em;white-space:nowrap}
.tag.ok{background:#e9f7f1;color:#147d64}
.tag.warn{background:#fff4dd;color:#945c00}
td.blank{background:#fffaf0;color:#8a6100;font-style:italic}
.section-head .tools{margin-left:auto}
@media(max-width:780px){.section-head .tools{margin-left:0}table.data{min-width:900px}}
'''

APP_JS = '''/* China Money Research — simple dashboard table filter (no external deps). */
(function () {
  "use strict";
  Array.prototype.forEach.call(document.querySelectorAll("input.filter"), function (input) {
    var id = input.getAttribute("data-filter");
    var table = document.querySelector('table[data-table="' + id + '"]');
    var count = document.querySelector('[data-count="' + id + '"]');
    if (!table) return;
    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase(), shown = 0;
      rows.forEach(function (row) {
        var match = !q || row.textContent.toLowerCase().indexOf(q) !== -1;
        row.style.display = match ? "" : "none";
        if (match) shown++;
      });
      if (count) count.textContent = shown + " of " + rows.length + " rows";
    });
    if (count) count.textContent = rows.length + " rows";
  });
})();
'''


def main():
    # 1. additive linking sections on shared HTML files (never replaces content)
    append_to_html("index.html", links_html())
    append_to_html("review.html", tiny_notice(
        "deep-review.html", "Additional flagged items:",
        "the integration session published 23 further irregularities and unverified values with official source links."))
    append_to_html("sources.html", tiny_notice(
        "deep-sources.html", "Additional sources:",
        "the integration session registered 84 further official sources with verification methods."))

    # 2. markdown records (append only)
    append_once("README.md", README_SECTION)
    append_once("COORDINATION.md", COORD_SECTION)

    # 3. self-contained stylesheet: base styles snapshot + additive rules
    base = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
    (ROOT / "assets" / "deep-research.css").write_text(
        "/* Self-contained snapshot of shared base styles + deep-research additions. */\n"
        + base + ("\n" if not base.endswith("\n") else "") + ADDITIVE_CSS,
        encoding="utf-8")

    # 4. dashboard script and separate verification workflow (no shared workflow edited)
    (ROOT / "assets" / "deep-app.js").write_text(APP_JS, encoding="utf-8")
    wf = ROOT / ".github" / "workflows" / "deep-research-verify.yml"
    wf.parent.mkdir(parents=True, exist_ok=True)
    wf.write_text(WORKFLOW, encoding="utf-8")

    print("Integrated deep-research links, records, self-contained assets and verification workflow.")


if __name__ == "__main__":
    main()
