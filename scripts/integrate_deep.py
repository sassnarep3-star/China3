#!/usr/bin/env python3
"""Final-integration edits to the previously published pages.

Additive only: every pre-existing line of content is preserved. This script
replaces the shared navigation, appends the new category grid to the landing
page, appends the full irregularity register to Flagged for Review, appends the
official source register to Sources, and loads the dashboard filter script.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_site as bs  # noqa: E402  (regenerates CSVs + category pages deterministically)

MARKER = "<!-- integration-v2 -->"
NAV = bs.NAV

SECTIONS = [
    ("executive-summary.html", "01 · Executive summary", "The short answer, the ranked recommendation and the full requirement-coverage map."),
    ("china-rules.html", "02 · China rules", "SAFE / PBOC / State Council rules line by line, with official links in every row."),
    ("us-tax.html", "03 · US tax & reporting", "IRS, FinCEN, Treasury and eCFR rules, including 2026 FBAR penalty amounts."),
    ("channels.html", "04 · All channels", "35 conversion methods with eligibility, limits, pros, cons and penalty exposure."),
    ("penalty.html", "05 · Penalty breakdown", "The conversion penalty decomposed into separately verifiable cost layers."),
    ("findings.html", "06 · Analysis", "What the rules mean together, and where the 'conversion tax' premise breaks down."),
    ("review.html", "07 · Flagged for review", "23 irregularities and unverified values, each with a source link."),
    ("sources.html", "08 · Source register", "Every official source used, with verification method."),
]


def nav_html(active):
    items = "".join(
        f'<a class="{"active" if p == active else ""}" href="{p}">{html.escape(t)}</a>'
        for p, t in NAV)
    return f'<header class="topbar"><div class="shell"><a class="brand" href="index.html"><span class="brand-mark">¥</span> China Money Research</a><nav class="nav">{items}</nav></div></header>'


def replace_nav(text, active):
    return re.sub(r'<header class="topbar">.*?</header>', lambda _: nav_html(active), text, count=1, flags=re.S)


def add_script(text):
    if "assets/app.js" in text:
        return text
    return text.replace("</body>", '<script src="assets/app.js"></script></body>')


def integration_block():
    cards = "".join(
        f'<a class="category-link" href="{p}"><article class="card"><span class="pill blue">{tag}</span>'
        f'<h2>{html.escape(tag.split("· ", 1)[-1])}</h2><p>{html.escape(desc)}</p>'
        f'<span class="source">Open category →</span></article></a>'
        for p, tag, desc in SECTIONS)
    return f'''{MARKER}
<section class="section"><div class="section-head"><div><h2 class="section-title">Deep research — subpages by category</h2><p>A second, deeper research pass added in the final integration session. All previous content above is preserved.</p></div></div>
<div class="grid">{cards}</div></section>
<section class="section"><div class="hero-band"><strong>What the integration pass added</strong><p>Official confirmation that a passport-holding U.S. citizen is generally a 境外个人 (foreign individual) whose FX purchase from legitimate, tax-documented RMB income is not limited by the USD 50,000 convenience amount; the current 银发〔2026〕42号 virtual-currency rule that repealed 银发〔2021〕237号; the 2026 FBAR penalty figures ($16,536 / $165,353 or 50% of the balance); Bank of China's published personal wire-fee components; the IRS $200 personal foreign-currency gain rule; Form 3520 gift reporting; and a full decomposition of the "conversion penalty" into tax, documentary, pricing, FX-control, offshore-basis and U.S.-reporting layers. Every new table row links to an official source; unverified values are blank and listed on Flagged for Review.</p></div></section>
'''


def flags_block():
    rows = []
    for r in bs.FLAGS:
        rid, item, why, needed, sid, extra, status = r
        rows.append(
            f'<tr><td><strong>{html.escape(rid)}</strong><br><span class="tag warn">Needs review</span></td>'
            f'<td>{html.escape(item)}</td><td>{html.escape(why)}</td><td>{html.escape(needed)}</td>'
            f'<td class="src">{bs.source_col(sid, extra)}</td></tr>')
    return f'''{MARKER}
<section class="section"><div class="section-head"><div><h2 class="section-title">Flagged for Review — full irregularity register (integration pass)</h2><p>These items are published here with source links and do not block publication. Every unconfirmed value elsewhere on this site is blank and marked UNVERIFIED.</p></div><div class="tools"><label class="filter-label">Filter <input type="search" class="filter" data-filter="flags-table" placeholder="type to filter rows"></label><span class="rowcount" data-count="flags-table">{len(rows)} rows</span></div></div>
<div class="table-wrap"><table class="data" data-table="flags-table"><thead><tr><th>#</th><th>Item</th><th>Why it is flagged</th><th>What would resolve it</th><th>Official source</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>
'''


def sources_block():
    rows = []
    for sid in sorted(bs.SOURCES):
        authority, title, url, method = bs.SOURCES[sid]
        rows.append(
            f'<tr><td><strong>{html.escape(sid)}</strong></td><td>{html.escape(authority)}</td>'
            f'<td>{html.escape(title)}</td>'
            f'<td class="src"><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">Open official page ↗</a></td>'
            f'<td>{html.escape(method)}</td></tr>')
    return f'''{MARKER}
<section class="section"><div class="section-head"><div><h2 class="section-title">Official source register — integration pass ({len(rows)} sources)</h2><p>One row per primary source used in the deep-research tables. All domains are government, regulator, central bank, official court or official bank sources; the single GitHub entry is the repository's own project record.</p></div><div class="tools"><label class="filter-label">Filter <input type="search" class="filter" data-filter="sources-table" placeholder="type to filter rows"></label><span class="rowcount" data-count="sources-table">{len(rows)} rows</span></div></div>
<div class="table-wrap"><table class="data" data-table="sources-table"><thead><tr><th>#</th><th>Authority</th><th>Document</th><th>Official link</th><th>Verification performed</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>
<section class="section"><div class="grid"><article class="card"><h2>Line-by-line verification</h2><ul><li>Every table row on this site carries at least one official-site link in its own row.</li><li>Values that could not be confirmed from an official source are left blank and flagged, never inferred.</li><li><code>scripts/build_site.py</code> regenerates all deep-research tables from <code>data/*.csv</code>; <code>scripts/verify.py</code> audits every row, every source URL, row counts and all local links.</li><li>Chinese-language official documents are paraphrased in English for readability; the linked original controls.</li></ul></article><article class="card"><h2>Machine-readable data</h2><ul><li><code>data/china_rules.csv</code>, <code>data/us_rules.csv</code>, <code>data/channels.csv</code>, <code>data/penalty.csv</code>, <code>data/findings.csv</code>, <code>data/flags.csv</code></li><li><code>data/sources.csv</code> and <code>data/sources.json</code> — the source register</li><li>Research memos are in <code>research/</code>; the task/verification/merge log is in <code>COORDINATION.md</code>.</li></ul></article></div></section>
'''


def main():
    # 1. shared navigation + brand + script on all existing pages
    active_map = {"index.html": "index.html", "routes.html": "index.html",
                  "tax.html": "us-tax.html", "review.html": "review.html",
                  "sources.html": "sources.html"}
    for name, active in active_map.items():
        p = ROOT / name
        t = p.read_text(encoding="utf-8")
        t = replace_nav(t, active)
        t = add_script(t)
        p.write_text(t, encoding="utf-8")

    # 2. additive sections
    for name, block in (("index.html", integration_block()),
                        ("review.html", flags_block()),
                        ("sources.html", sources_block())):
        p = ROOT / name
        t = p.read_text(encoding="utf-8")
        if MARKER in t:
            t = re.sub(re.escape(MARKER) + r".*?(?=</main>)", "", t, count=1, flags=re.S)
        t = t.replace("</main>", block + "</main>")
        p.write_text(t, encoding="utf-8")

    # 3. dashboard filter script
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "app.js").write_text('''/* China Money Research — simple dashboard table filter (no external deps). */
(function () {
  "use strict";
  var inputs = document.querySelectorAll("input.filter");
  Array.prototype.forEach.call(inputs, function (input) {
    var id = input.getAttribute("data-filter");
    var table = document.querySelector('table[data-table="' + id + '"]');
    var count = document.querySelector('[data-count="' + id + '"]');
    if (!table) return;
    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
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
''', encoding="utf-8")

    # 4. additive CSS only (never modifies prior rules)
    css = ROOT / "assets" / "site.css"
    t = css.read_text(encoding="utf-8")
    if "/* integration-v2 */" not in t:
        t += '''
/* integration-v2 — additive styles for deep-research tables */
.tools{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.filter-label{font-size:12px;color:#66758a;display:flex;align-items:center;gap:7px}
input.filter{border:1px solid var(--line);border-radius:9px;padding:8px 11px;font:inherit;font-size:13px;min-width:200px;background:#fff}
input.filter:focus{outline:2px solid #b9c9ed;border-color:#315eff}
.rowcount{font-size:12px;color:#7c899b;white-space:nowrap}
table.data{min-width:1050px}
table.data th{white-space:nowrap}
table.data td{font-size:13px;line-height:1.55}
table.data td:first-child{font-weight:700;color:#233a5c;white-space:nowrap}
table.data tbody tr:hover td{background:#fafcff}
table.data td.src{white-space:nowrap;font-size:12px}
table.data td.src a{display:inline-block;margin:1px 6px 1px 0;padding:3px 8px;border-radius:7px;background:var(--blue-soft);color:#174fbf;text-decoration:none;font-weight:700;font-size:11px}
table.data td.src a:hover{background:#dbe7ff}
table.data td.status{white-space:nowrap}
.tag{display:inline-block;border-radius:999px;padding:3px 9px;font-size:10px;font-weight:800;letter-spacing:.03em;white-space:nowrap}
.tag.ok{background:var(--green-soft);color:var(--green)}
.tag.warn{background:var(--amber-soft);color:var(--amber)}
td.blank{background:#fffaf0;color:#8a6100;font-style:italic}
.section-head .tools{margin-left:auto}
@media(max-width:780px){.section-head .tools{margin-left:0}table.data{min-width:900px}}
'''
        css.write_text(t, encoding="utf-8")

    print("Integrated shared navigation, category grid, flagged register, source register and dashboard script.")


if __name__ == "__main__":
    main()
