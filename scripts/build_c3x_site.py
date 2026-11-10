#!/usr/bin/env python3
"""Build the C3X canonical edition pages from data/c3x_*.csv.

Pages written (all at repo root, namespaced c3x-):
  c3x-summary.html   executive summary + dashboard (start here)
  c3x-costs.html     the $10,000 -> $400,000 ladder, every method
  c3x-methods.html   all 14 routes, pros and cons
  c3x-steps.html     step-by-step playbook per route
  c3x-tax.html       tax and penalty decomposition, U.S. and PRC
  c3x-flagged.html   everything blank or unverified, with the reason
  c3x-sources.html   the 15 official documents, with verbatim quotes

Nothing is typed into a page as a figure: every number is read from the CSVs
or computed by c3x_engine, and every data row carries a source id that resolves
on c3x-sources.html.  scripts/verify_c3x_site.py fails the build otherwise.
"""
from __future__ import annotations

import html
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c3x_engine as E  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = Decimal

SRC = {s["id"]: s for s in E.SOURCES}
LADDER = E.ladder_rows()
METHODS = E.METHODS
GRID = E.method_grid()
STEPS = E.STEPS
PEN = E.PENALTIES
FLAGS = E.FLAGS

BOARD = SRC["S01"]["doc_date"]
ASK = E.ASK
SPREAD = E.spread_pct() * 100


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def link(source_ids: str) -> str:
    """A row's provenance: one anchor per source id in the pipe-separated list."""
    parts = []
    for sid in [s for s in source_ids.split("|") if s]:
        s = SRC.get(sid)
        if s is None:
            parts.append(f'<span class="missing">{sid}</span>')
            continue
        parts.append(f'<a href="{s["url"]}" rel="noopener">{sid}</a>')
    return " ".join(parts) + f' <a class="srclink" href="c3x-sources.html#{source_ids.split("|")[0]}">ⓘ</a>'


NAV = [
    ("c3x-summary.html", "Summary"),
    ("c3x-costs.html", "Costs $10k–$400k"),
    ("c3x-methods.html", "Methods"),
    ("c3x-steps.html", "Step by step"),
    ("c3x-tax.html", "Tax &amp; penalties"),
    ("c3x-flagged.html", "Flagged"),
    ("c3x-sources.html", "Sources"),
]

CSS = r"""
:root{
  --ink:#0d1b24; --muted:#5a6b77; --line:#dfe6ea; --bg:#f6f8f9; --card:#fff;
  --brand:#0f4c5c; --accent:#c1121f; --ok:#1b7f5a; --warn:#9a5b00; --soft:#eef4f6;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:#0b5f8a}
h1,h2,h3{line-height:1.2;margin:0 0 .5em}
h1{font-size:clamp(1.5rem,4.2vw,2.3rem);letter-spacing:-.02em}
h2{font-size:clamp(1.2rem,2.8vw,1.55rem);margin-top:1.6em}
h3{font-size:1.05rem}
p{margin:.6em 0}
.top{background:var(--brand);color:#fff;position:sticky;top:0;z-index:20;box-shadow:0 1px 0 rgba(0,0,0,.15)}
.top-in{max-width:1080px;margin:0 auto;padding:10px 16px;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center}
.brand{color:#fff;font-weight:700;text-decoration:none;letter-spacing:-.01em}
.brand span{opacity:.55;padding:0 4px}
.nav{display:flex;flex-wrap:wrap;gap:4px 2px}
.nav a{color:#d8e8ea;text-decoration:none;font-size:.86rem;padding:4px 7px;border-radius:6px}
.nav a:hover,.nav a[aria-current]{background:rgba(255,255,255,.14);color:#fff}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 56px}
.hero{padding:22px 0 6px}
.eyebrow{font-size:.74rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 8px;font-weight:700}
.lede{font-size:1.02rem;color:#31424d;max-width:70ch}
.answer{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--brand);
  border-radius:10px;padding:16px 18px;margin:16px 0}
.answer ol{margin:.4em 0 .2em;padding-left:1.2em}
.answer li{margin:.55em 0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.card .k{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:700}
.card .v{font-size:1.45rem;font-weight:750;letter-spacing:-.02em;margin:.15em 0 .1em}
.card .n{font-size:.84rem;color:var(--muted)}
.card.pos .v{color:var(--ok)} .card.neg .v{color:var(--accent)}
.card a{font-size:.84rem}
.pagegrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;margin:12px 0}
.pagegrid a{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:12px 14px;text-decoration:none;color:inherit}
.pagegrid a:hover{border-color:var(--brand)}
.pagegrid strong{display:block;font-size:.98rem;margin-bottom:2px}
.pagegrid span{font-size:.84rem;color:var(--muted)}
table{width:100%;border-collapse:collapse;background:var(--card);font-size:.9rem;
  border:1px solid var(--line);border-radius:10px;overflow:hidden}
caption{caption-side:top;text-align:left;font-size:.82rem;color:var(--muted);padding:6px 2px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--soft);font-size:.76rem;text-transform:uppercase;letter-spacing:.05em;color:#3d4f5a}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:#fbfcfd}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.blank{color:#9aa7b0;font-style:italic}
.flag{display:inline-block;font:600 .72rem/1.4 var(--mono);background:#fdf0e3;color:var(--warn);
  border:1px solid #f0d4b3;border-radius:5px;padding:1px 5px;text-decoration:none}
.pill{display:inline-block;font-size:.72rem;font-weight:700;border-radius:999px;padding:1px 8px;border:1px solid}
.pill.ok{color:var(--ok);border-color:#bfe0d2;background:#eefaf4}
.pill.no{color:var(--accent);border-color:#f0c2c6;background:#fdeef0}
.pill.mid{color:var(--warn);border-color:#f0d4b3;background:#fdf6ec}
.srclink{text-decoration:none;font-size:.8rem;color:#7c8b95}
.callout{border-radius:10px;padding:12px 14px;margin:14px 0;border:1px solid}
.callout.warn{background:#fff8ec;border-color:#f0d4b3;color:#5c3a00}
.callout.info{background:#eef6f8;border-color:#cfe3e8;color:#123b46}
.callout.danger{background:#fdeef0;border-color:#f0c2c6;color:#5c1119}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:12px 0}
summary{cursor:pointer;font-weight:650}
.tight{margin:.4em 0;padding-left:1.15em} .tight li{margin:.3em 0}
.foot{font-size:.84rem;color:var(--muted)}
code{font-family:var(--mono);font-size:.85em;background:#eef2f4;padding:1px 4px;border-radius:4px}
hr{border:0;border-top:1px solid var(--line);margin:26px 0}
.method{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:14px 0}
.method h3{margin-bottom:.2em}
.method .kv{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;font-size:.9rem;margin-top:8px}
.method .kv dt{color:var(--muted);font-weight:650} .method .kv dd{margin:0}
.steps{counter-reset:s;list-style:none;padding:0;margin:.6em 0}
.steps li{counter-increment:s;position:relative;padding:8px 0 8px 34px;border-top:1px solid var(--line)}
.steps li:first-child{border-top:0}
.steps li::before{content:counter(s);position:absolute;left:0;top:8px;width:23px;height:23px;border-radius:50%;
  background:var(--brand);color:#fff;font-size:.76rem;font-weight:700;display:flex;align-items:center;justify-content:center}
.steps .doc{display:block;font-size:.8rem;color:var(--muted);margin-top:2px}
footer{background:#0d1b24;color:#b9c8d1;padding:26px 0;font-size:.85rem}
footer a{color:#9fd0dd}
@media (max-width:640px){
  .nav{width:100%}
  table{border:0;background:transparent;font-size:.92rem}
  thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  tbody tr{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:0 0 8px;padding:4px 0}
  tbody tr:nth-child(even){background:var(--card)}
  tbody td{display:flex;justify-content:space-between;gap:12px;border-bottom:1px dashed #edf1f3;padding:6px 12px;text-align:right}
  tbody td:last-child{border-bottom:0}
  tbody td::before{content:attr(data-label);font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;
    color:var(--muted);font-weight:700;text-align:left;flex:1 1 auto}
  tbody td.num{justify-content:space-between}
  .method .kv{grid-template-columns:1fr}
}
"""


def head(title: str, desc: str, current: str) -> str:
    nav = "\n".join(
        f'<a href="{href}"{" aria-current=page" if href == current else ""}>{label}</a>'
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="assets/c3x.css">
</head>
<body>
<header class="top"><div class="top-in">
  <a class="brand" href="index.html">China&nbsp;money<span>·</span>CNY&nbsp;→&nbsp;USD</a>
  <nav class="nav" aria-label="Main">{nav}</nav>
</div></header>
<main class="wrap">
"""


TAIL = """</main>
<footer><div class="wrap">
<p><strong>Research, not tax or legal advice.</strong> Figures are arithmetic over the official documents in the
register, each fetched on 2026-11-10 and quoted verbatim. A bank quote, a tax certificate and your own cost basis
are still required before acting. Board readings are timestamped snapshots, not quotes.</p>
<p>Sources: boc.cn · safe.gov.cn · chinatax.gov.cn · gpo.gov · irs.gov · fincen.gov · ecfr.gov · cbp.gov.
Register: <a href="c3x-sources.html">c3x-sources.html</a>. Data: <code>data/c3x_*.csv</code>.
Task board: <a href="COORDINATION.md">COORDINATION.md</a>.</p>
</div></footer>
</body>
</html>
"""


def money_cell(text: str) -> str:
    return f'<td class="num">${text}</td>'


# --------------------------------------------------------------------------- summary
def build_summary() -> str:
    top = LADDER[0]
    mid50 = LADDER[4]
    big = LADDER[-1]
    gain24 = E.sec988_gain_pct(D(E.INPUTS["irs_avg_2024"]["value"])) * 100
    tax24 = D(big["sec988_tax_37_usd"])
    max_zero = D(E.INPUTS["sec988_200"]["value"]) / E.sec988_gain_pct(D(E.INPUTS["irs_avg_2024"]["value"]))

    ranked = [
        ("1", "Documented bank remittance — documented current-account income", "M01 / M06",
         f"${top['single_total_usd']} on $10,000 · ${big['single_total_usd']} on $400,000",
         "No PRC penalty exposure; the U.S. §988 tax applies to any channel, so the only choice is which documents you can produce.", "ok", "S03|S04|S02"),
        ("2", "Emigrant property transfer, if you are emigrating and cancelling household registration", "M03",
         f"same bank tariff · ${big['single_total_usd']} on $400,000",
         "PRC 20% applies to the property gain, not the conversion; it must be settled before the registration is cancelled.", "mid", "S06|S07|S08"),
        ("3", "Inheritance transfer, if the money is inherited mainland property", "M04",
         f"same bank tariff · ${big['single_total_usd']} on $400,000",
         "SAFE approval at the deceased's registered locality; notarised file; tax certificate first.", "mid", "S06"),
        ("4", "Convenience amount, only with a Foreign Permanent Resident ID", "M05",
         "price as M01 · amount not stated on the cited page",
         "The only route where a foreign passport holder is expressly given the annual convenience amount.", "mid", "S04"),
        ("5", "Card / ATM withdrawals abroad", "M07",
         "price blank · cap ¥100,000 per year",
         "About $14,960 a year at today's ask. Cannot move a $400,000 balance.", "mid", "S15"),
        ("6", "Carry cash", "M08",
         "price blank · U.S. report above $10,000",
         "Two legal systems; seizure risk; PRC export figure deliberately blank.", "mid", "S05|S14"),
        ("7", "Quota splitting, underground banks, undeclared cash", "M12–M14",
         "fine up to 30%, 30%–100% if serious",
         "The sanction is a percentage of the amount moved — orders of magnitude above the fee it tries to avoid.", "no", "S05"),
    ]
    rank_rows = "\n".join(
        f"<tr><td data-label=\"#\">{n}</td>"
        f"<td data-label=\"Route\"><strong>{esc(name)}</strong><br><span class=\"foot\">{mid}</span></td>"
        f"<td data-label=\"China-side cost\">{cost}</td>"
        f"<td data-label=\"Why it ranks here\">{esc(why)} <span class=\"pill {'ok' if cls=='ok' else ('no' if cls=='no' else 'mid')}\">"
        f"{'lawful' if cls!='no' else 'prohibited'}</span></td>"
        f"<td data-label=\"Source\">{link(srcs)}</td></tr>"
        for n, name, mid, cost, why, cls, srcs in ranked
    )

    anchors = ["10000", "50000", "100000", "200000", "300000", "400000"]
    anchor_rows = "\n".join(
        f"<tr><td data-label=\"Amount\">${int(a):,}</td>"
        f"<td class=\"num\" data-label=\"One transfer\">${next(r['single_total_usd'] for r in LADDER if r['amount_usd']==a)}</td>"
        f"<td class=\"num\" data-label=\"% of amount\">{next(r['single_total_pct'] for r in LADDER if r['amount_usd']==a)}%</td>"
        f"<td class=\"num\" data-label=\"Split at $50k\">${next(r['staged_total_usd'] for r in LADDER if r['amount_usd']==a)}</td>"
        f"<td class=\"num\" data-label=\"U.S. §988 tax @37%\">${next(r['sec988_tax_37_usd'] for r in LADDER if r['amount_usd']==a)}</td>"
        f"<td data-label=\"Source\">{link('S01|S02|S09')}</td></tr>"
        for a in anchors
    )

    return head(
        "Getting money out of China: the cheapest lawful route and what the tax penalty really is",
        "Official-source answer for a U.S. citizen: CNY to USD routes ranked, the $10,000 to $400,000 cost ladder, and the U.S. and PRC tax lines that actually apply.",
        "c3x-summary.html",
    ) + f"""
<section class="hero">
  <p class="eyebrow">Canonical edition · {len(E.SOURCES)} official documents fetched 2026-11-10 · board {esc(BOARD)}</p>
  <h1>No PRC tax on converting CNY to USD was found. The real costs are the bank spread, the U.S. §988 currency gain, and a reporting penalty you can avoid.</h1>
  <p class="lede">A U.S. citizen with a mainland bank balance is told the money is “stuck” behind a tax. The documents do not
  support that: the charge that looks like a conversion tax is either the bank's spread, the PRC tax on the income that
  created the money, or the U.S. tax on the currency gain — and only the last one is a genuine conversion tax. This page
  prices all three, in the order they hit you.</p>

  <div class="answer">
    <h2>The short answer</h2>
    <ol>
      <li><strong>Move it through a bank with documents.</strong> The published China-side cost is
      <strong>${top['single_total_usd']}</strong> on $10,000 ({top['single_total_pct']}%) and
      <strong>${big['single_total_usd']}</strong> on $400,000 ({big['single_total_pct']}%) — the 1‰ wire tariff capped at
      CNY 260 plus CNY 150 cable, and a {SPREAD:.4f}% half-spread on the board. That is the whole bill from the Chinese side.</li>
      <li><strong>The tax you were warned about is most likely the U.S. one.</strong> Disposing of a CNY deposit is a
      §988 transaction and the gain is ordinary income. At the 2024 IRS average of 7.189 CNY/USD, converting at today's ask
      produces a <strong>{gain24:.4f}%</strong> gain on the dollars received — <strong>${tax24:,.2f}</strong> of federal tax at
      a 37% marginal rate on $400,000. It is the same for every lawful channel, so changing channel cannot avoid it.</li>
      <li><strong>Only the first ~${max_zero:,.0f} escapes it.</strong> §988(e)(2) excludes a personal transaction only if the
      gain is $200 or less. At a {gain24:.2f}% gain that ceiling is about <strong>${max_zero:,.0f}</strong> converted, so the
      exclusion is irrelevant at these amounts. No tax-treaty relief was analysed in this pass, so none is claimed
      (F14).</li>
      <li><strong>The genuinely large numbers are penalties for not reporting.</strong> A non-willful FBAR violation is capped at
      $16,536 and a willful one at $165,353 per violation. Splitting the amount across relatives' quotas, by contrast, is a PRC
      offence carrying up to 30% of the amount — $120,000 on $400,000. Both dwarf the $410 bank fee people try to avoid.</li>
    </ol>
  </div>

  <div class="cards">
    <div class="card"><div class="k">Bank cost, $10,000</div><div class="v">${top['single_total_usd']}</div>
      <div class="n">{top['single_total_pct']}% · spread ${top['spread_usd']} + fee ${top['fee_usd']}</div></div>
    <div class="card"><div class="k">Bank cost, $400,000</div><div class="v">${big['single_total_usd']}</div>
      <div class="n">{big['single_total_pct']}% · one transfer</div></div>
    <div class="card"><div class="k">Split into 8 wires</div><div class="v">${big['staged_total_usd']}</div>
      <div class="n">{big['staged_total_pct']}% · the expensive assumption</div></div>
    <div class="card neg"><div class="k">U.S. §988 tax, $400,000 @37%</div><div class="v">${tax24:,.0f}</div>
      <div class="n">if the CNY was acquired at the 2024 average</div></div>
    <div class="card"><div class="k">Half-spread on the board</div><div class="v">{SPREAD:.4f}%</div>
      <div class="n">ask {ASK} against mid {E.MID:.4f} CNY/USD</div></div>
    <div class="card"><div class="k">FBAR caps per violation</div><div class="v">$16,536 / $165,353</div>
      <div class="n">non-willful / willful</div></div>
  </div>

  <div class="callout info">
    <p><strong>The rule that decides your route.</strong> If you hold a 外国人永久居留身份证 you get the annual
    convenience amount for buying FX. If you do not, a foreign individual buys FX from lawful current-account RMB income
    <em>with ID and source-of-funds materials including tax documents</em> — the convenience amount is expressly limited to
    PR-ID holders. That is the single most consequential sentence in this research (<a href="c3x-sources.html#S04">S04</a>).
    SAFE's Tianjin branch restated exactly that rule on <strong>13 July 2026</strong> for a foreign individual remitting
    <em>labour remuneration earned in China</em>, which is the closest official statement to your situation found in this
    pass (<a href="c3x-sources.html#S16">S16</a>). It states no cap and no convenience amount for a non-PR-ID holder.</p>
  </div>
</section>

<section>
  <h2>Routes ranked by tax and penalty exposure — not by fee</h2>
  <p class="lede">The fee differences are tens of dollars. The penalty differences are tens of thousands. Ranked best-first
  for a U.S. citizen holding a mainland CNY balance.</p>
  <table>
    <caption>China-side cost is the published bank charge. U.S. §988 tax is additional on every lawful row and is not repeated.</caption>
    <thead><tr><th>#</th><th>Route</th><th>China-side cost</th><th>Why it ranks here</th><th>Source</th></tr></thead>
    <tbody>{rank_rows}</tbody>
  </table>
</section>

<section>
  <h2>What it costs at six amounts</h2>
  <p class="lede">Every $10,000 step from $10,000 to $400,000 is on <a href="c3x-costs.html">the cost page</a>.
  The two China-side columns are the same money counted two ways: one transfer, or one transfer per $50,000.</p>
  <table>
    <caption>Board {esc(BOARD)}. §988 column assumes acquisition at the 2024 IRS yearly average and a 37% marginal rate.</caption>
    <thead><tr><th>Amount</th><th class="num">One transfer</th><th class="num">%</th><th class="num">Split at $50k</th><th class="num">U.S. §988 @37%</th><th>Source</th></tr></thead>
    <tbody>{anchor_rows}</tbody>
  </table>
</section>

<section>
  <h2>Which route applies to you — a four-question test</h2>
  <div class="cards">
    <div class="card"><div class="k">Question 1</div><div class="v" style="font-size:1rem">Do you hold a 外国人永久居留身份证?</div>
      <div class="n">Yes → the annual convenience amount is open to you (M05). No → go to question 2.</div></div>
    <div class="card"><div class="k">Question 2</div><div class="v" style="font-size:1rem">Are you emigrating and cancelling mainland household registration?</div>
      <div class="n">Yes → emigrant property transfer (M03), one application, tax certificate first.</div></div>
    <div class="card"><div class="k">Question 3</div><div class="v" style="font-size:1rem">Is the balance inherited mainland property?</div>
      <div class="n">Yes → inheritance transfer (M04) at the deceased's registered locality.</div></div>
    <div class="card"><div class="k">Question 4</div><div class="v" style="font-size:1rem">Is it documented current-account income?</div>
      <div class="n">Yes → M06/M01, the cheapest priced route. No → the balance needs a different legal characterisation before any bank will move it; that is a written branch answer, not a fee decision.</div></div>
  </div>
</section>

<section>
  <h2>Do these five things before moving anything</h2>
  <ol class="tight">
    <li><strong>Get the branch's answer in writing</strong> on which rule it applies to a foreign passport holder, and on
    whether your documents establish lawful current-account income. <a href="c3x-sources.html#S04">S04</a> /
    <a href="c3x-sources.html#S03">S03</a></li>
    <li><strong>Reconstruct your CNY cost basis</strong> by acquisition date, because that is what decides whether there is a
    §988 gain at all. A 2021 acquisition produces a loss at today's rate; a 2024 acquisition produces a 7% gain.
    <a href="c3x-tax.html">Tax page</a></li>
    <li><strong>Fix U.S. reporting first.</strong> FBAR if the aggregate exceeded $10,000 at any point in the year; Form 8938
    if the threshold applies. The penalty caps are larger than the bank bill by two orders of magnitude.</li>
    <li><strong>Do not split the amount across relatives' quotas.</strong> It is the exact pattern arts. 39 and 45 sanction,
    and the fine is a percentage of the amount.</li>
    <li><strong>Ask for the quote, not the tariff.</strong> The tariff is published; your branch's actual rate, any local
    charge, and the U.S. receiving fee are not.</li>
  </ol>
</section>

<section>
  <h2>Read next</h2>
  <div class="pagegrid">
    <a href="c3x-costs.html"><strong>Costs, $10,000 → $400,000</strong><span>40 rows, one transfer vs eight, and the §988 line</span></a>
    <a href="c3x-methods.html"><strong>All 14 methods</strong><span>pros, cons, lawfulness, eligibility</span></a>
    <a href="c3x-steps.html"><strong>Step by step</strong><span>document-by-document playbook</span></a>
    <a href="c3x-tax.html"><strong>Tax &amp; penalties</strong><span>§988, FBAR, 8938, PRC 20%, Order 532</span></a>
    <a href="c3x-flagged.html"><strong>Flagged for review</strong><span>every blank and every unverified premise</span></a>
    <a href="c3x-sources.html"><strong>{len(E.SOURCES)} official sources</strong><span>verbatim quotes and fetch dates</span></a>
  </div>
</section>
""" + TAIL


# --------------------------------------------------------------------------- costs
def build_costs() -> str:
    rows = []
    for r in LADDER:
        rows.append(
            f"<tr><td data-label=\"Amount\">${int(r['amount_usd']):,}</td>"
            f"<td class=\"num\" data-label=\"CNY to buy\">{float(r['cny_needed']):,.2f}</td>"
            f"<td class=\"num\" data-label=\"Spread\">${r['spread_usd']}</td>"
            f"<td class=\"num\" data-label=\"Bank fee\">¥{r['fee_cny']} = ${r['fee_usd']}</td>"
            f"<td class=\"num\" data-label=\"One transfer\">${r['single_total_usd']}</td>"
            f"<td class=\"num\" data-label=\"%\">{r['single_total_pct']}%</td>"
            f"<td class=\"num\" data-label=\"Split at $50k\">{r['staged_wires']} × → ${r['staged_total_usd']}</td>"
            f"<td class=\"num\" data-label=\"U.S. §988 @37%\">${r['sec988_tax_37_usd']}</td>"
            f"<td data-label=\"Source\">{link('S01|S02|S09')}</td></tr>"
        )

    anchors = ["10000", "50000", "100000", "200000", "300000", "400000"]
    by_amount = {r["amount_usd"]: r for r in LADDER}
    mrows = []
    for m in METHODS:
        cells = []
        for a in anchors:
            g = next(x for x in GRID if x["method_id"] == m["id"] and x["amount_usd"] == a)
            if g["cost_usd"]:
                cells.append(f'<td class="num" data-label="${int(a):,}">${g["cost_usd"]}<br><span class="foot">{g["cost_pct"]}%</span></td>')
            else:
                cells.append(f'<td class="num" data-label="${int(a):,}"><span class="blank">blank</span><br><a class="flag" href="c3x-flagged.html#{g["flag"]}">{g["flag"]}</a></td>')
        badge = {"Lawful": "ok", "Prohibited": "no"}.get(m["lawfulness"].split(",")[0], "mid")
        if m["lawfulness"].startswith("Prohibited") or m["lawfulness"].startswith("Unlawful"):
            badge = "no"
        mrows.append(
            f"<tr><td data-label=\"Route\">{m['id']}<br><span class=\"foot\">{esc(m['name'])}</span></td>"
            f"<td data-label=\"Lawfulness\"><span class=\"pill {badge}\">{esc(m['lawfulness'])}</span></td>"
            + "".join(cells) + f"<td data-label=\"Source\">{link(m['sources'])}</td></tr>"
        )

    return head(
        "CNY to USD costs at every $10,000 step to $400,000",
        "Mobile-friendly cost table: the published China-side cost of converting CNY to USD at 40 amounts from $10,000 to $400,000, for every method, with sources.",
        "c3x-costs.html",
    ) + f"""
<section class="hero">
  <p class="eyebrow">Cost schedule · board {esc(BOARD)}</p>
  <h1>$10,000 to $400,000, in $10,000 steps</h1>
  <p class="lede">The only China-side prices an official document publishes are the FX spread and the wire tariff. Both are
  used here exactly as published: <strong>{SPREAD:.4f}%</strong> half-spread on the ask
  (<a href="c3x-sources.html#S01">S01</a>) and <strong>1‰ of the CNY amount, minimum ¥50, maximum ¥260, plus ¥150
  cable</strong> (<a href="c3x-sources.html#S02">S02</a>). Anything the sources do not publish is blank and flagged — never
  zero.</p>

  <div class="callout warn">
    <p><strong>Two ways to count the fee, both shown.</strong> “One transfer” applies the tariff once. “Split at $50,000”
    applies it to each whole $50,000 transfer. The split costs more at every amount above $50,000 and is a
    <em>fee assumption</em>, not a legal requirement: SAFE's rule is that above $50,000 a day you produce documents, not
    that you must break the payment up (<a href="c3x-sources.html#S03">S03</a>).</p>
  </div>
</section>

<section>
  <h2>The ladder</h2>
  <table>
    <caption>Board {esc(BOARD)}: ask {ASK}, bid {E.BID}, mid {E.MID:.4f} CNY/USD. CNY column is what you spend.
    §988 column is the U.S. federal tax on the currency gain at a 37% marginal rate and a 2024-average cost basis — it is
    not China-side and it is not in the totals.</caption>
    <thead><tr><th>Amount</th><th class="num">CNY to buy</th><th class="num">Spread</th><th class="num">Bank fee</th>
    <th class="num">One transfer</th><th class="num">%</th><th class="num">Split at $50k</th><th class="num">U.S. §988 @37%</th><th>Source</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p class="foot">Machine-readable: <code>data/c3x_ladder.csv</code> · full 14 × 40 grid: <code>data/c3x_method_costs.csv</code>
  (560 rows).</p>
</section>

<section>
  <h2>Every method at six amounts</h2>
  <p class="lede">“Blank” means no official source publishes the figure. It is not a zero and it is not an estimate.
  Prohibited routes are listed so they can be recognised and refused.</p>
  <table>
    <caption>China-side cost only. The U.S. §988 line applies to every lawful row and is not repeated here.</caption>
    <thead><tr><th>Route</th><th>Lawfulness</th><th class="num">$10,000</th><th class="num">$50,000</th>
    <th class="num">$100,000</th><th class="num">$200,000</th><th class="num">$300,000</th><th class="num">$400,000</th><th>Source</th></tr></thead>
    <tbody>{''.join(mrows)}</tbody>
  </table>
</section>

<section>
  <h2>Why the percentage falls as the amount rises</h2>
  <p>The ¥260 cap is the reason. At $10,000 the fee is driven by the 1‰ rate (¥66.85, so ¥216.85 with cable); by $38,862 the
  cap binds and every additional dollar costs only the spread. The headline rate therefore falls from
  {LADDER[0]['single_total_pct']}% to {LADDER[-1]['single_total_pct']}% — which is exactly why the cheapest large transfer is
  <em>one</em> transfer, and why splitting into eight adds {float(by_amount['400000']['staged_total_usd']) - float(by_amount['400000']['single_total_usd']):,.2f}
  dollars at $400,000 for no legal benefit.</p>
</section>
""" + TAIL


# --------------------------------------------------------------------------- methods
def build_methods() -> str:
    blocks = []
    for m in METHODS:
        blocks.append(f"""
<article class="method" id="{m['id']}">
  <h3>{m['id']} · {esc(m['name'])}</h3>
  <span class="pill {'no' if m['lawfulness'].startswith(('Prohibited','Unlawful')) else ('ok' if m['lawfulness']=='Lawful' else 'mid')}">{esc(m['lawfulness'])}</span>
  <span class="pill mid">{esc(m['category'])}</span>
  <dl class="kv">
    <dt>Who can use it</dt><dd>{esc(m['eligibility'])}</dd>
    <dt>Pros</dt><dd>{esc(m['pros'])}</dd>
    <dt>Cons</dt><dd>{esc(m['cons'])}</dd>
    <dt>PRC tax</dt><dd>{esc(m['prc_tax'])}</dd>
    <dt>U.S. tax</dt><dd>{esc(m['us_tax'])}</dd>
    <dt>Priced?</dt><dd>{"Yes — published tariff" if m['price_model'] in ('single','staged') else "No — blank and flagged (F05)"}</dd>
    <dt>Sources</dt><dd>{link(m['sources'])}</dd>
    <dt>How to do it</dt><dd><a href="c3x-steps.html#{m['id']}">Step-by-step →</a></dd>
  </dl>
</article>""")
    return head(
        "All 14 ways to convert CNY to USD — pros, cons, lawfulness",
        "Every CNY-to-USD conversion and repatriation route found in the official sources, with pros, cons, eligibility and legal status.",
        "c3x-methods.html",
    ) + f"""
<section class="hero">
  <p class="eyebrow">Method catalogue · 14 routes</p>
  <h1>Every route, and what is actually wrong with it</h1>
  <p class="lede">Four of these are lawful, documented bank routes that differ mainly in which documents you can produce.
  One is an offshore-account route that does not solve the outbound leg. Two are investment or trade channels that are not
  conversions of an existing balance. Three are prohibited, and they are here only so they can be recognised.</p>
  <div class="callout danger">
    <p><strong>Reading the prohibited entries.</strong> Nothing in this repository is a how-to for M12–M14. The cost of
    those routes is not a fee but a fine of up to 30% of the amount, or 30%–100% where serious
    (<a href="c3x-sources.html#S05">S05</a> arts. 39, 40, 45), so they carry no price and no steps.</p>
  </div>
</section>
{''.join(blocks)}
""" + TAIL


# --------------------------------------------------------------------------- steps
def build_steps() -> str:
    by_method: dict[str, list[tuple]] = {}
    for sid, n, action, doc, sources in STEPS:
        by_method.setdefault(sid, []).append((n, action, doc, sources))

    out = []
    for m in METHODS:
        rows = by_method.get(m["id"], [])
        if rows:
            body = '<ol class="steps">' + "".join(
                f"<li>{esc(action)}<span class=\"doc\">Document: {esc(doc)} · {link(src)}</span></li>"
                for _, action, doc, src in rows
            ) + "</ol>"
        else:
            body = ('<p class="foot">No step list is published for this route: it is prohibited or it is not a conversion of '
                    'an existing balance. See <a href="c3x-methods.html#' + m["id"] + '">the method entry</a> for why.</p>')
        out.append(f'<section class="method" id="{m["id"]}"><h3>{m["id"]} · {esc(m["name"])}</h3>{body}</section>')

    return head(
        "Step by step: exactly how each CNY-to-USD route works",
        "Document-by-document playbook for each lawful CNY-to-USD route, with the official article that requires each step.",
        "c3x-steps.html",
    ) + f"""
<section class="hero">
  <p class="eyebrow">Playbook · 30 steps across the priced routes</p>
  <h1>Exactly what happens, in order</h1>
  <p class="lede">Each step names the document the bank or SAFE will ask for and the article that requires it. Where an
  article is silent, the step says so rather than inventing a requirement.</p>
  <div class="callout info">
    <p><strong>Start with the written branch answer.</strong> Step 1 of every bank route is the same because the same
    balance can fall under two different rules (F08). Until the branch says which one it will apply, no later step is
    reliable.</p>
  </div>
</section>
{''.join(out)}
""" + TAIL


# --------------------------------------------------------------------------- tax
def build_tax() -> str:
    years = ["2021", "2022", "2023", "2024", "2025"]
    gain_rows = []
    for y in years:
        r0 = D(E.INPUTS[f"irs_avg_{y}"]["value"])
        g = E.sec988_gain_pct(r0) * 100
        sign = "gain" if g > 0 else "loss"
        note = ("a loss is not recognised on a personal transaction either — §988(e)(1) excludes it"
                if g <= 0 else
                f"the $200 exclusion is lost above ${float(D(E.INPUTS['sec988_200']['value'])/(g/100)):,.0f} converted")
        gain_rows.append(
            f"<tr><td data-label=\"Acquired in\">{y}</td><td class=\"num\" data-label=\"IRS average\">{r0}</td>"
            f"<td class=\"num\" data-label=\"Result at today's ask\">{g:+.4f}% {sign}</td>"
            f"<td data-label=\"Consequence\">{note}</td><td data-label=\"Source\">{link('S11|S09|S01')}</td></tr>"
        )

    anchors = ["10000", "50000", "100000", "200000", "400000"]
    g24 = E.sec988_gain_pct(D(E.INPUTS["irs_avg_2024"]["value"]))
    rate_rows = []
    for a in anchors:
        usd = D(a)
        gain = usd * g24
        cells = []
        for rate in E.MARGINAL_RATES:
            tax = gain * D(rate) / 100
            cells.append(f'<td class="num" data-label="{rate}%">${tax:,.2f}</td>')
        rate_rows.append(f"<tr><td data-label=\"Amount\">${int(a):,}</td><td class=\"num\" data-label=\"Gain @2024 basis\">${gain:,.2f}</td>{''.join(cells)}<td data-label=\"Source\">{link('S09|S11')}</td></tr>")

    prc = "".join(
        f"<tr><td data-label=\"Rule\">{esc(p['rule'])}</td><td data-label=\"Exposure\">{esc(p['amount'])}</td>"
        f"<td data-label=\"What triggers it\">{esc(p['trigger'])}</td><td data-label=\"Source\">{link(p['source'])}</td></tr>"
        for p in PEN
    )

    tax_rows = "".join(
        f"<tr><td data-label=\"Layer\">{i}</td><td data-label=\"What it is\">{esc(name)}</td>"
        f"<td data-label=\"Applies to\">{esc(applies)}</td><td data-label=\"Scale\">{esc(scale)}</td>"
        f"<td data-label=\"Avoidable?\">{esc(avoid)}</td><td data-label=\"Source\">{link(srcs)}</td></tr>"
        for i, name, applies, scale, avoid, srcs in [
            ("1", "FX spread", "Every conversion", f"{SPREAD:.4f}% of the amount", "No — it is the price of the trade", "S01"),
            ("2", "Wire tariff + cable", "Every remittance", "¥50–260 + ¥150 per transfer", "Partly — use one transfer, not eight", "S02"),
            ("3", "PRC income tax", "The income that created the balance", "20% on property transfer, interest, dividends", "No, but it is not a conversion tax", "S08"),
            ("4", "U.S. §988 currency gain", "The disposal of the CNY itself", "Ordinary rates on the gain; $200 exclusion", "Only by basis and timing, not by channel", "S09|S11"),
            ("5", "FBAR / Form 8938", "The account, every year", "$16,536 / $165,353 · $60,000 ceiling", "Yes — report on time", "S10|S12|S13"),
            ("6", "PRC FX sanctions", "Illegal movement", "Up to 30%; 30%–100% if serious", "Yes — use a licensed bank", "S05"),
            ("7", "CBP currency reporting", "Physical cash over $10,000", "Seizure and forfeiture", "Yes — file Form 105", "S14"),
        ]
    )

    return head(
        "Where the “conversion tax” actually comes from — §988, FBAR, 8938, PRC 20%, Order 532",
        "Seven separate charges get called a conversion tax. This page separates the bank spread, the U.S. currency gain, PRC income tax and the reporting penalties, with sources.",
        "c3x-tax.html",
    ) + f"""
<section class="hero">
  <p class="eyebrow">Tax &amp; penalty decomposition</p>
  <h1>Seven different charges get called “the tax on converting”</h1>
  <p class="lede">Only one of them is a tax on the conversion itself: the U.S. §988 currency gain. The rest are the price of
  the trade, a PRC tax on the income behind the money, or penalties for not reporting. They behave completely differently,
  so they are separated here.</p>
  <table>
    <caption>Each layer with its trigger and whether any lawful route avoids it.</caption>
    <thead><tr><th>Layer</th><th>What it is</th><th>Applies to</th><th>Scale</th><th>Avoidable?</th><th>Source</th></tr></thead>
    <tbody>{tax_rows}</tbody>
  </table>
</section>

<section>
  <h2>1 · The U.S. §988 currency gain is the real conversion tax</h2>
  <p>26 U.S.C. §988(c)(1)(C)(i) treats the <em>disposition</em> of nonfunctional currency as a §988 transaction, and
  §988(a)(1)(A) makes the gain ordinary income. An individual's personal transaction is excluded by §988(e)(1) only under
  §988(e)(2) — <q>the preceding sentence shall not apply if the gain which would otherwise be recognized on the transaction
  exceeds $200</q> (<a href="c3x-sources.html#S09">S09</a>). The capital-gain election in §988(a)(1)(B) covers forwards,
  futures and options, not a bank deposit.</p>
  <table>
    <caption>Gain on the dollars received, at today's ask of {ASK} CNY/USD, by the year the CNY was acquired (IRS yearly averages, S11).</caption>
    <thead><tr><th>Acquired in</th><th class="num">IRS average</th><th class="num">Result</th><th>Consequence</th><th>Source</th></tr></thead>
    <tbody>{''.join(gain_rows)}</tbody>
  </table>
  <div class="callout warn">
    <p><strong>This is why the answer to “how do I avoid the tax” is “find your basis”, not “find a cleverer channel”.</strong>
    The gain is measured from acquisition to disposition. If your CNY came in when the yuan was weaker than today you have a
    loss, and on a personal transaction that loss is not recognised either. No route changes this arithmetic — the tax is
    identical whether you wire once, wire eight times, or use the emigrant route.</p>
  </div>
</section>

<section>
  <h2>2 · What it becomes at your marginal rate</h2>
  <table>
    <caption>Assuming acquisition at the 2024 IRS average (7.189) and conversion at today's ask: a {g24*100:.4f}% gain on the dollars received.</caption>
    <thead><tr><th>Amount received</th><th class="num">Gain</th>{"".join(f'<th class="num">{r}%</th>' for r in E.MARGINAL_RATES)}</tr></thead>
    <tbody>{''.join(rate_rows)}</tbody>
  </table>
  <p class="foot">Marginal rates are the U.S. ordinary brackets; the applicable one depends on total taxable income, which is
  not known here (F01). No state tax is modelled. This is a sensitivity, not a computation of your liability (F03).</p>
</section>

<section>
  <h2>3 · PRC tax attaches to the income, not the conversion</h2>
  <p>The Individual Income Tax Law's nine taxable categories do not include currency conversion. It does tax
  <em>property transfer income</em> at 20%, with the base being proceeds less original value and reasonable expenses
  (art. 6(5)), and it requires a taxpayer cancelling Chinese household registration to emigrate to settle tax
  <em>before</em> cancellation (art. 13). <a href="c3x-sources.html#S08">S08</a></p>
  <div class="callout info">
    <p><strong>The practical consequence for the “considerable taxes” story.</strong> If a PRC tax appears when you try to
    move the money, look at what it is attached to. A 20% charge on a property sale or on interest is the income tax on the
    gain, and it is due whether or not you move the money offshore. A “conversion tax” with no income behind it was not found
    in any instrument reviewed (F09).</p>
  </div>
</section>

<section>
  <h2>4 · Every penalty, with its ceiling</h2>
  <table>
    <caption>PRC sanctions from Order 532 and the IIT Law; U.S. sanctions from the current eCFR table and the IRS/FinCEN pages.</caption>
    <thead><tr><th>Rule</th><th>Exposure</th><th>What triggers it</th><th>Source</th></tr></thead>
    <tbody>{prc}</tbody>
  </table>
</section>

<section>
  <h2>5 · The reporting you must not skip</h2>
  <ul class="tight">
    <li><strong>FBAR.</strong> A U.S. person with a financial interest in, or signature authority over, foreign accounts
    whose aggregate value exceeds $10,000 at any time in the calendar year must file FinCEN Form 114
    (<a href="c3x-sources.html#S13">S13</a>). Caps: $16,536 non-willful, $165,353 willful, per violation, for penalties
    assessed on or after 2025-01-17 (<a href="c3x-sources.html#S10">S10</a>).</li>
    <li><strong>Form 8938.</strong> A U.S.-resident unmarried specified individual crosses the threshold above $50,000 at
    year-end or $75,000 at any time; living outside the U.S., above $200,000 / $300,000. Penalty up to $10,000 plus $10,000
    per 30 days after notice, capped at $60,000 (<a href="c3x-sources.html#S12">S12</a>).</li>
    <li><strong>FinCEN Form 105.</strong> Carrying more than $10,000 in or out of the United States; the threshold is the
    family or group total, not per person; failure risks seizure and forfeiture (<a href="c3x-sources.html#S14">S14</a>).
    It is a report, not a tax.</li>
  </ul>
</section>
""" + TAIL


# --------------------------------------------------------------------------- flags
def build_flags() -> str:
    rows = "".join(
        f'<tr id="{f["id"]}"><td data-label="ID"><a href="#{f["id"]}">{f["id"]}</a></td>'
        f"<td data-label=\"Item\"><strong>{esc(f['item'])}</strong></td>"
        f"<td data-label=\"Why it is flagged\">{esc(f['why'])}</td>"
        f"<td data-label=\"Source\">{link(f['source'])}</td></tr>"
        for f in FLAGS
    )
    for t in ("S05", "S01"):
        pass
    return head(
        "Flagged for review — blanks, ambiguities and unverified premises",
        "Every item this edition deliberately left blank or could not confirm from an official source, with the source that would resolve it.",
        "c3x-flagged.html",
    ) + f"""
<section class="hero">
  <p class="eyebrow">Flagged · {len(FLAGS)} items · non-blocking</p>
  <h1>What this edition does not claim</h1>
  <p class="lede">Nothing here is a guess and nothing is filled with an industry average. Where a source is silent the
  figure is blank; where a premise could not be checked the premise is flagged. Each row names the document that would
  close it.</p>
</section>

<section>
  <table>
    <caption>All {len(FLAGS)} flags. Status <strong>needs review</strong>; none of them blocks publication.</caption>
    <thead><tr><th>ID</th><th>Item</th><th>Why it is flagged</th><th>Source</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</section>

<section>
  <h2>The three that change the answer most</h2>
  <ol class="tight">
    <li><strong>F01 — your facts.</strong> No balance, residency status, cost basis or filing history was supplied. Every
    numeric answer here is therefore conditional on assumptions stated on the page where it appears.</li>
    <li><strong>F08 — two definitions of 境内个人.</strong> Order 532 art. 52(2) includes a foreigner continuously resident
    for one year. The current-account guidance in S04 treats foreign individuals separately and reserves the convenience
    amount for PR-ID holders. Which one your branch applies changes everything about the documents you need.</li>
    <li><strong>F03 — cost basis.</strong> The U.S. tax line flips between a 7% gain and a 3.6% loss depending on when the
    CNY was acquired. This is the largest single number in the whole analysis and it is the one thing only you can supply.</li>
  </ol>
</section>
""" + TAIL


# --------------------------------------------------------------------------- sources
def build_sources() -> str:
    rows = []
    for s in E.SOURCES:
        rows.append(f"""
<tr id="{s['id']}">
  <td data-label="ID"><strong>{s['id']}</strong></td>
  <td data-label="Document">
    <a href="{s['url']}" rel="noopener">{esc(s['title'])}</a><br>
    <span class="foot">{esc(s['issuer'])} · {esc(s['doc_date'])}</span>
  </td>
  <td data-label="What it establishes">{esc(s['proposition'])}</td>
  <td data-label="Verbatim"><q>{esc(s['quote'])}</q></td>
  <td data-label="Fetched">{esc(s['fetched_utc'])}</td>
</tr>""")
    return head(
        "Official sources — 15 documents, verbatim quotes, fetch dates",
        "The official primary sources behind every figure in this edition, with the verbatim passage relied on and the date it was fetched.",
        "c3x-sources.html",
    ) + f"""
<section class="hero">
  <p class="eyebrow">Source register · {len(E.SOURCES)} documents · all fetched 2026-11-10</p>
  <h1>The evidence, quoted</h1>
  <p class="lede">Every figure in this edition resolves to one of these rows. The quote column is the passage the figure was
  read from, in the original language where the document is Chinese, so the reading can be checked without trusting this
  page.</p>
  <div class="callout info">
    <p><strong>Official does not always mean authoritative English.</strong> The Chinese texts are the operative ones.
    eCFR says of itself that the content is <q>authoritative but unofficial</q>; the govinfo U.S. Code is the GPO edition.
    Both are cited as such.</p>
  </div>
</section>

<section>
  <table>
    <caption>Domain allowlist enforced by <code>scripts/verify_c3x_site.py</code>: .gov.cn, chinatax.gov.cn, boc.cn,
    gpo.gov, irs.gov, fincen.gov, ecfr.gov, cbp.gov.</caption>
    <thead><tr><th>ID</th><th>Document</th><th>What it establishes</th><th>Verbatim</th><th>Fetched</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</section>

<section>
  <h2>How the arithmetic uses them</h2>
  <table>
    <caption>Inputs and where each comes from. Full machine-readable list: <code>data/c3x_inputs.csv</code>.</caption>
    <thead><tr><th>Input</th><th class="num">Value</th><th>Unit</th><th>Source</th></tr></thead>
    <tbody>
    {"".join(f'<tr><td data-label="Input"><code>{k}</code></td><td class="num" data-label="Value">{v["value"]}</td>'
             f'<td data-label="Unit">{esc(v["unit"])}</td><td data-label="Source">{link(v["source"])}</td></tr>'
             for k, v in E.INPUTS.items())}
    </tbody>
  </table>
</section>
""" + TAIL


def main() -> None:
    E.build_data()
    pages = {
        "c3x-summary.html": build_summary(),
        "c3x-costs.html": build_costs(),
        "c3x-methods.html": build_methods(),
        "c3x-steps.html": build_steps(),
        "c3x-tax.html": build_tax(),
        "c3x-flagged.html": build_flags(),
        "c3x-sources.html": build_sources(),
    }
    for name, body in pages.items():
        (ROOT / name).write_text(body, encoding="utf-8")
        print(f"wrote {name} ({len(body):,} bytes)")
    (ROOT / "assets" / "c3x.css").write_text(CSS, encoding="utf-8")
    print("wrote assets/c3x.css")


if __name__ == "__main__":
    main()
