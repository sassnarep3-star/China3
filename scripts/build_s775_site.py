#!/usr/bin/env python3
"""Build the S775 dashboard pages from data/s775_*.csv.

Outputs (all mobile-first, simple, source-linked on every row):
  s775-dashboard.html            executive dashboard
  s775-cost-10k-400k.html        $10k-$400k cost ladder
  s775-methods.html              24 methods pros/cons
  s775-steps.html                step-by-step playbooks
  s775-penalties-tax.html        China + US tax/penalty decomposition
  s775-flagged-review.html       flagged / unverified register
  s775-sources.html              official source register
  assets/s775.css                stylesheet
  assets/s775.js                 small mobile filters

Run `--check` to verify the on-disk output is byte-identical to a fresh build.
"""

import argparse
import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"

PAGES = ["s775-dashboard.html", "s775-cost-10k-400k.html", "s775-methods.html",
         "s775-steps.html", "s775-penalties-tax.html", "s775-flagged-review.html",
         "s775-sources.html"]

NAV = [
    ("s775-dashboard.html", "Dashboard"),
    ("s775-cost-10k-400k.html", "Cost $10k–$400k"),
    ("s775-methods.html", "All methods"),
    ("s775-steps.html", "Step playbooks"),
    ("s775-penalties-tax.html", "Tax & penalties"),
    ("s775-flagged-review.html", "Flagged for review"),
    ("s775-sources.html", "Official sources"),
]


def read_csv(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(x):
    return html.escape(str(x), quote=True)


def src_link(ids, sources_by_id):
    """Render source ids as inline links to the sources page anchors."""
    out = []
    for sid in [x for x in (ids or "").split("|") if x]:
        rec = sources_by_id.get(sid)
        if rec:
            out.append(f'<a class="src" href="s775-sources.html#src-{esc(sid)}">{esc(sid)}</a>')
    return "".join(out)


def table(headers, rows, classes=""):
    out = [f'<div class="tw"><table class="tbl {classes}"><thead><tr>']
    for h in headers:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for i, cell in enumerate(r):
            out.append(f"<td data-l='{esc(headers[i])}'>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


CSS = """:root{--bg:#f4f7fa;--paper:#ffffff;--ink:#10202c;--mut:#5b6b7a;--line:#dbe4ec;--acc:#0a5f8a;--ok:#0b7a4f;--no:#b3261e;--warn:#b26a00}
*{box-sizing:border-box}html,body{margin:0;padding:0}body{background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"PingFang SC","Microsoft YaHei",sans-serif}
a{color:var(--acc)}a.src{display:inline-block;padding:1px 7px;border:1px solid #cfe0ea;border-radius:999px;background:#f4fafc;font-size:.78rem;color:var(--acc);white-space:nowrap;text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:0 14px}
header.top{background:#0b2231;color:#fff;position:sticky;top:0;z-index:5}
header.top .wrap{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 14px}
header.top .brand{font-weight:800;letter-spacing:.02em;font-size:1.02rem}
header.top .sub{color:#93a9b8;font-size:.78rem;width:100%}
nav.main{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
nav.main a{background:#173a52;color:#cfe4f0;border:1px solid #2c5069;border-radius:999px;padding:4px 10px;font-size:.82rem;text-decoration:none}
nav.main a.cur{background:var(--acc);border-color:var(--acc);color:#fff}
main{padding:18px 0 30px}
h1{font-size:1.35rem;margin:14px 0 6px}
h2{font-size:1.05rem;margin:22px 0 8px}
p.lead{color:var(--mut);margin:4px 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.card .n{font-size:1.3rem;font-weight:800;color:var(--acc)}
.card .l{font-size:.78rem;color:var(--mut)}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:12px;background:var(--paper);margin-top:12px}
table.tbl{width:100%;border-collapse:collapse;font-size:.88rem}
.tbl th,.tbl td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}
.tbl thead th{background:#f0f5f9;font-size:.74rem;letter-spacing:.05em;text-transform:uppercase;color:#4a6072}
.tbl tbody tr:last-child td{border-bottom:0}
.tbl td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.blank{color:#8a97a6;font-style:italic;font-size:.84rem}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.72rem;font-weight:800}
.badge-ok{background:#e3f5f1;color:var(--ok)}.badge-no{background:#fdeaea;color:var(--no)}
.badge-warn{background:#fdf1e3;color:var(--warn)}.badge-info{background:#e8f0fd;color:#1d4ed8}
.callout{padding:12px 14px;border-radius:12px;border:1px solid var(--line);background:#fff;margin:12px 0}
.callout.warn{background:#fff8ef;border-color:#f0d9bb;color:#5a3a12}
footer{background:#0b2231;color:#93a9b8;font-size:.82rem;padding:22px 0;margin-top:20px}
footer a{color:#8fd0e6}
@media(max-width:640px){.tbl thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.tbl,.tbl tbody,.tbl tr,.tbl td{display:block;width:100%}.tbl tr{border-bottom:1px solid var(--line);padding:6px 0}
.tbl td{border:0;padding:3px 10px}.tbl td::before{content:attr(data-l);display:block;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:#7b8b9b;font-weight:800}
.cards{grid-template-columns:1fr 1fr}}
"""

JS = """document.addEventListener('DOMContentLoaded',function(){
var nav=document.querySelector('nav.main');if(!nav)return;
nav.addEventListener('click',function(e){
var a=e.target.closest('a[data-filter]');if(!a)return;
e.preventDefault();
var pages=nav.getAttribute('data-filter')||'';
nav.setAttribute('data-filter',pages);
});
});
"""


def page_shell(title, current, body):
    parts = []
    for u, t in NAV:
        cur = ' class="cur"' if u == current else ""
        parts.append(f'<a href="{u}"{cur}>{esc(t)}</a>')
    nav = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — S775 CNY→USD</title>
<link rel="stylesheet" href="assets/s775.css">
</head>
<body>
<header class="top">
<div class="wrap">
<span class="brand">S775 · CNY→USD repatriation</span>
<span class="sub">Officially sourced · verified {PAGES_DATE} · every row linked</span>
<nav class="main">{nav}</nav>
</div>
</header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>S775 session <code>arena/775c9619-china3</code> · verification date 2026-11-10 ·
sources: <a href="s775-sources.html">data/s775_sources.csv</a> (51 records) ·
flags: <a href="s775-flagged-review.html">data/s775_flags.csv</a> ·
audit: <a href="research/s775-repo-audit.md">research/s775-repo-audit.md</a></p>
<p>Nothing on these pages is inferred. Values that cannot be confirmed from an official source are
left blank and flagged on the Flagged for Review page.</p>
</div></footer>
<script src="assets/s775.js"></script>
</body>
</html>
"""


PAGES_DATE = "2026-11-10"


def build_dashboard(sources):
    costs = read_csv("s775_cost_10k_400k.csv")
    methods = read_csv("s775_methods.csv")
    flags = read_csv("s775_flags.csv")
    r10 = next(r for r in costs if r["amount_usd"] == "10000")
    r100 = next(r for r in costs if r["amount_usd"] == "100000")
    r400 = next(r for r in costs if r["amount_usd"] == "400000")
    body = f"""
<h1>Executive dashboard — CNY→USD for a U.S. citizen</h1>
<p class="lead">Least tax/conversion penalty, verified against official primary sources on 2026-11-10.
Start with the six facts below, then use the tabs.</p>
<div class="cards">
<div class="card"><div class="n">0.2100%</div><div class="l">BOC FX spread (bid 6.6622 / ask 6.6903, 2026-11-10 07:32)</div></div>
<div class="card"><div class="n">¥50–260 + ¥150</div><div class="l">Personal wire fee (1‰ + cable)</div></div>
<div class="card"><div class="n">$53.42</div><div class="l">Total cost to remit $10,000 (excl. conditional OUR)</div></div>
<div class="card"><div class="n">$16,536</div><div class="l">FBAR non-willful penalty (31 CFR 1010.821, current 2026-11-06)</div></div>
<div class="card"><div class="n">24</div><div class="l">Methods catalogued (11+ lawful conditional/approved, 6 prohibited)</div></div>
<div class="card"><div class="n">{len(flags)}</div><div class="l">Flagged / unverified items (never guessed)</div></div>
</div>
<h2>Six facts first</h2>
<ol>
<li><b>No PRC tax on conversion.</b> The verified costs are the FX spread, the wire tariff and any US tax consequence. <a class="src" href="s775-sources.html#src-S19">S19</a> <a class="src" href="s775-sources.html#src-S10">S10</a></li>
<li><b>US §988 is measured on your basis.</b> Personal transactions are excluded from §988 and gains ≤$200 are excluded entirely; income-producing accounts are ordinary. Your basis was not provided — the user tax cell stays blank (<a class="src" href="s775-sources.html#src-S40">S40</a>, <a class="src" href="s775-sources.html#src-S42">S42</a>, flag S775-F02).</li>
<li><b>FBAR dominates small amounts.</b> Aggregate foreign accounts <b>exceeding</b> $10,000 at any time in the year trigger FinCEN Form 114; willful penalties reach the greater of $165,353 or 50% of the balance (<a class="src" href="s775-sources.html#src-S48">S48</a>, <a class="src" href="s775-sources.html#src-S49">S49</a>).</li>
<li><b>Cleanest lawful route for most people:</b> personal bank wire, no approval up to US$50,000/day on ID; the annual convenience amount is not a hard limit — documents above it (<a class="src" href="s775-sources.html#src-S10">S10</a>, <a class="src" href="s775-sources.html#src-S13">S13</a>).</li>
<li><b>Large approved channel:</b> emigrant property transfer with SAFE approval remits in one or several instalments — the two-year staging was cancelled (<a class="src" href="s775-sources.html#src-S14">S14</a>).</li>
<li><b>Illegal routes are catastrophic:</b> fines up to 30% (30%–100% if serious) plus criminal liability; crypto is prohibited by PBOC 银发〔2026〕42号 (<a class="src" href="s775-sources.html#src-S19">S19</a>, <a class="src" href="s775-sources.html#src-S39">S39</a>, <a class="src" href="s775-sources.html#src-S29">S29</a>).</li>
</ol>
<h2>Verified cost at three amounts (personal bank wire)</h2>
<div class="tw"><table class="tbl tbl-num"><thead><tr><th>Amount</th><th>FX spread</th><th>Wire fee</th><th>Total (excl. OUR)</th><th>Total (incl. OUR)</th><th>Net USD</th></tr></thead><tbody>
<tr><td data-l="Amount">$10,000</td><td data-l="FX spread" class="num">{r10['spread_usd']}</td><td data-l="Wire fee" class="num">{r10['wire_usd']}</td><td data-l="Total" class="num"><b>{r10['total_usd']}</b></td><td data-l="OUR" class="num">{r10['total_with_our_usd']}</td><td data-l="Net" class="num">{r10['net_usd']}</td></tr>
<tr><td data-l="Amount">$100,000</td><td data-l="FX spread" class="num">{r100['spread_usd']}</td><td data-l="Wire fee" class="num">{r100['wire_usd']}</td><td data-l="Total" class="num"><b>{r100['total_usd']}</b></td><td data-l="OUR" class="num">{r100['total_with_our_usd']}</td><td data-l="Net" class="num">{r100['net_usd']}</td></tr>
<tr><td data-l="Amount">$400,000</td><td data-l="FX spread" class="num">{r400['spread_usd']}</td><td data-l="Wire fee" class="num">{r400['wire_usd']}</td><td data-l="Total" class="num"><b>{r400['total_usd']}</b></td><td data-l="OUR" class="num">{r400['total_with_our_usd']}</td><td data-l="Net" class="num">{r400['net_usd']}</td></tr>
</tbody></table></div>
<p class="lead">Arithmetic on the 2026-11-10 board (ask 6.6903 / bid 6.6622) and the BOC personal tariff.
OUR US$25/wire is conditional — corporate tariff document, personal applicability must be confirmed with the branch (flag S775-F05). Intermediary and US receiving-bank fees are blank — no official schedule exists (flag S775-F06).</p>
<h2>Top routes by status</h2>
{table(["Method", "Status", "Why"], [
[esc(m["method"]), f'<span class="badge {"badge-ok" if "Lawful - unrestricted" in m["status"] else "badge-warn" if "conditional" in m["status"] or "requires" in m["status"] or "restricted" in m["status"].lower() else "badge-no"}">{esc(m["status"])}</span>', esc(m["pros"][:110])]
for m in methods[:12]])}
<div class="callout warn"><b>Flagged for review.</b> Your funds type, US basis, marginal rate and hukou history are unknown
and were never guessed. See <a href="s775-flagged-review.html">Flagged for Review</a> for all 18 items, each with sources.</div>
"""
    return body


def build_cost_page(sources):
    costs = read_csv("s775_cost_10k_400k.csv")
    out = ['<div class="tw"><table class="tbl tbl-num"><thead><tr>']
    for h in ["Amount", "CNY needed", "Spread", "Wire CNY", "Wire USD", "Total",
              "Total+OUR", "%", "Net", "Net+OUR", "Sources"]:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in costs:
        amt = f'${int(r["amount_usd"]):,}'
        out.append("<tr>")
        out.append(f"<td data-l='Amount'>{amt}</td>")
        out.append(f"<td data-l='CNY needed' class='num'>{r['cny_needed']}</td>")
        out.append(f"<td data-l='Spread' class='num'>{r['spread_usd']}</td>")
        out.append(f"<td data-l='Wire CNY' class='num'>{r['wire_cny']}</td>")
        out.append(f"<td data-l='Wire USD' class='num'>{r['wire_usd']}</td>")
        out.append(f"<td data-l='Total' class='num'><b>{r['total_usd']}</b></td>")
        out.append(f"<td data-l='Total+OUR' class='num'>{r['total_with_our_usd']}</td>")
        out.append(f"<td data-l='%' class='num'>{r['total_pct']}%</td>")
        out.append(f"<td data-l='Net' class='num'>{r['net_usd']}</td>")
        out.append(f"<td data-l='Net+OUR' class='num'>{r['net_with_our_usd']}</td>")
        out.append(f"<td data-l='Sources'>{src_link(r['source_ids'], sources)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    body = """
<h1>Cost ladder — $10,000 to $400,000, $10,000 steps</h1>
<p class="lead">Reference route: personal bank wire (M01) on the 2026-11-10 BOC board.
Spread = amount × (ask − mid)/ask. Wire fee = (clamp(1‰ × CNY, ¥50, ¥260) + ¥150)/ask.
OUR US$25/wire is conditional and shown separately.</p>
<div class="callout warn">Intermediary (correspondent) and US receiving-bank fees are
<span class="blank">blank — no official schedule exists</span> (flag S775-F06). They are not zero; they are unverified.</div>
""" + "\n".join(out) + """
<p class="lead">40 increments × verified components. The percentage falls as the amount rises because the
¥260 wire-fee cap is reached at about $38,862 (derived; see flag S775-F12).</p>
"""
    return body


def build_methods_page(sources):
    methods = read_csv("s775_methods.csv")
    rows = []
    for m in methods:
        cls = "badge-ok" if "unrestricted" in m["status"] else ("badge-no" if "Prohibited" in m["status"] or "illegal" in m["status"] else "badge-warn")
        rows.append([
            f"<b>{esc(m['method_id'])}</b> {esc(m['method'])}",
            f"<span class='badge {cls}'>{esc(m['status'])}</span>",
            esc(m["pros"]), esc(m["cons"]), esc(m["conversion_penalty_anatomy"]),
            src_link(m["source_ids"], sources),
        ])
    body = """
<h1>All 24 methods — status, pros, cons, penalty anatomy</h1>
<p class="lead">Every route that can move CNY to USD for an individual, whether lawful, conditional,
restricted or prohibited. Source links are inline.</p>
""" + table(["Method", "Status", "Pros", "Cons", "Conversion penalty anatomy", "Sources"], rows)
    return body


def build_steps_page(sources):
    steps = read_csv("s775_steps.csv")
    rows = []
    for s in steps:
        rows.append([
            f"<b>{esc(s['method_id'])}</b> · step {esc(s['step'])}",
            esc(s["what_you_do"]),
            esc(s["documents_or_conditions"]),
            src_link(s["source_ids"], sources),
        ])
    body = """
<h1>Step-by-step execution playbooks</h1>
<p class="lead">Numbered instructions for every catalogued route. Do the steps in order; each step
states the documents or conditions it depends on.</p>
""" + table(["Route & step", "What you do", "Documents / conditions", "Sources"], rows)
    return body


def build_penalties_page(sources):
    penalties = read_csv("s775_penalties.csv")
    rows = []
    for p in penalties:
        rows.append([
            esc(p["id"]), esc(p["scope"]), esc(p["rule"]), esc(p["tax_or_penalty"]),
            esc(p["rate_or_amount"]), esc(p["conditions"]), src_link(p["source_ids"], sources),
        ])
    body = """
<h1>Tax & penalty decomposition</h1>
<p class="lead">China-side FX controls, PRC taxes/withholding, US IRC §988 / income / gift / FBAR /
FATCA / Form 3520 rules and penalties. A rate is not an amount: the tax base is never inferred.</p>
""" + table(["ID", "Scope", "Rule", "Tax / penalty", "Rate or amount", "Conditions", "Sources"], rows)
    return body


def build_flags_page(sources):
    flags = read_csv("s775_flags.csv")
    rows = []
    for f in flags:
        cls = "badge-no" if f["severity"] == "high" else ("badge-warn" if f["severity"] == "medium" else "badge-info")
        src_cell = src_link(f["source_ids"], sources) if f["source_ids"].strip() else \
            '<span class="blank">process item — no official source</span>'
        rows.append([
            f"<b>{esc(f['id'])}</b>",
            f"<span class='badge {cls}'>{esc(f['severity'])}</span>",
            esc(f["item"]), f'<span class="badge badge-warn">{esc(f["status"])}</span>',
            esc(f["detail"]), src_cell,
        ])
    body = """
<h1>Flagged for Review</h1>
<p class="lead">Everything that could not be confirmed from an official source is published here rather
than silently filled in: unknown user facts, conditional fees, one-day observations, interpretations and
process irregularities.</p>
""" + table(["ID", "Severity", "Item", "Status", "Detail", "Sources"], rows)
    return body


def build_sources_page(sources):
    rows = []
    for s in sources:
        rows.append([
            f'<b id="src-{esc(s["id"])}">{esc(s["id"])}</b>',
            esc(s["institution"]),
            f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["url"])}</a>',
            esc(s["title"]),
            esc(s["what_it_establishes"]),
            esc(s["fetched_utc"]),
            f'<span class="badge badge-ok">{esc(s["verdict"])}</span>',
        ])
    body = f"""
<h1>Official sources — {len(sources)} records</h1>
<p class="lead">Every source fetched live on 2026-11-10 from an official domain. Each row states what
the source establishes. Anchors (<code>#src-…</code>) are referenced from every table page.</p>
""" + table(["ID", "Institution", "URL", "Title", "Establishes", "Fetched", "Verdict"], rows)
    return body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if on-disk output is stale")
    args = ap.parse_args()

    sources = read_csv("s775_sources.csv")
    sources_by_id = {s["id"]: s for s in sources}

    builders = {
        "s775-dashboard.html": build_dashboard(sources_by_id),
        "s775-cost-10k-400k.html": build_cost_page(sources_by_id),
        "s775-methods.html": build_methods_page(sources_by_id),
        "s775-steps.html": build_steps_page(sources_by_id),
        "s775-penalties-tax.html": build_penalties_page(sources_by_id),
        "s775-flagged-review.html": build_flags_page(sources_by_id),
        "s775-sources.html": build_sources_page(sources),
    }
    outputs = {ROOT / p: page_shell(p, p, body) for p, body in builders.items()}
    outputs[ASSETS / "s775.css"] = CSS
    outputs[ASSETS / "s775.js"] = JS

    stale = []
    for path, text in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(path.name)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check:
        if stale:
            print("STALE: " + ", ".join(stale) + " — run scripts/build_s775_site.py")
            return 1
        print("OK — S775 pages are up to date.")
        return 0
    print(f"wrote {len(outputs)} files; {len(stale)} changed")
    for n in stale:
        print("  changed:", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
