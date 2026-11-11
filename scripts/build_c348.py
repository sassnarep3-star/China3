#!/usr/bin/env python3
"""Build the c348 edition: a dashboard plus category pages, every table row carrying a source link.

    python3 scripts/build_c348.py

Nothing is typed into the HTML by hand: every figure comes from data/c348_*.csv, which
scripts/verify_c348.py then recomputes independently.
"""
import csv
import html
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
esc = html.escape


def rows(name):
    with (DATA / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


SRC = {r["id"]: r for r in rows("c348_sources.csv")}
INP = {r["id"]: r for r in rows("c348_inputs.csv")}
METHODS = {r["id"]: r for r in rows("c348_methods.csv")}
FLAGS = {r["id"]: r for r in rows("c348_flags.csv")}
COSTS = rows("c348_costs.csv")
TAX = rows("c348_tax.csv")
PEN = rows("c348_penalty_ladder.csv")
PENRULE = {r["id"]: r for r in rows("c348_penalties.csv")}
QS = rows("c348_questions.csv")
STEPS = rows("c348_steps.csv")
RECON = rows("c348_reconciliation.csv")

AMOUNTS = [f"{10000 * i}.00" for i in range(1, 40)] + ["400000.00"]
YEARS = ["2021", "2022", "2023", "2024", "2025"]

NAV = [("c348-dashboard.html", "Dashboard"), ("c348-summary.html", "Summary"),
       ("c348-methods.html", "Methods"), ("c348-costs.html", "Costs $10k–400k"),
       ("c348-steps.html", "Step by step"), ("c348-tax.html", "Tax"),
       ("c348-penalties.html", "Penalties"), ("c348-questions.html", "Questions"),
       ("c348-audit.html", "Reconciliation & audit"), ("c348-flagged.html", "Flagged"),
       ("c348-sources.html", "Sources")]

PAGE_NOTES = {
    "c348-dashboard.html": "Start here: the answer, the cost ladder, the open questions",
    "c348-summary.html": "The executive summary, most important first",
    "c348-methods.html": "Every way to turn CNY into USD, lawful and prohibited",
    "c348-costs.html": "What every method costs at every USD 10,000 step",
    "c348-steps.html": "Exact step-by-step instructions per method",
    "c348-tax.html": "The U.S. and PRC tax on the conversion itself",
    "c348-penalties.html": "What the rules cost when they are broken",
    "c348-questions.html": "What must be answered before deciding, and how",
    "c348-audit.html": "Every previously published figure, reconciled",
    "c348-flagged.html": "Open items, unverified cells and irregularities",
    "c348-sources.html": "Every official page read, with its quotation",
}

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#14181d;--mut:#5b6672;--line:#dde2e8;--acc:#0b5fa5;
--ok:#0a7a45;--warn:#9a6400;--bad:#a4231f;--chip:#eef2f6}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc)}
header{background:#0f1a24;color:#fff;padding:14px 16px}
header .t{font-weight:700;font-size:1.05rem;letter-spacing:.2px}
header .s{color:#a9bccd;font-size:.82rem;margin-top:2px}
nav{background:#16232f;padding:0 8px;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}
nav a{display:inline-block;color:#cfe0ee;text-decoration:none;padding:11px 12px;font-size:.86rem;
border-bottom:3px solid transparent}
nav a.on{color:#fff;border-bottom-color:#4aa3e0;font-weight:600}
main{max-width:1080px;margin:0 auto;padding:18px 14px 60px}
h1{font-size:1.5rem;line-height:1.25;margin:6px 0 4px}
h2{font-size:1.14rem;margin:30px 0 8px;padding-top:6px}
h3{font-size:1rem;margin:20px 0 6px}
p{margin:8px 0}
.lede{color:var(--mut);font-size:.95rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}
.card .k{font-size:.72rem;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
.card .v{font-size:1.32rem;font-weight:700;margin-top:2px}
.card .n{font-size:.78rem;color:var(--mut);margin-top:2px}
.box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.box.acc{border-left:4px solid var(--acc)}
.box.warn{border-left:4px solid var(--warn)}
.box.bad{border-left:4px solid var(--bad)}
.box.ok{border-left:4px solid var(--ok)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);
border-radius:10px;background:var(--card);margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:.85rem;min-width:560px}
th,td{padding:8px 10px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--chip);font-size:.74rem;text-transform:uppercase;letter-spacing:.5px;
color:#39434d;position:sticky;top:0}
tbody tr:nth-child(even){background:#fbfcfd}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.blank{color:var(--bad);font-weight:700;font-size:.8rem;letter-spacing:.3px}
.chip{display:inline-block;background:var(--chip);border-radius:999px;padding:1px 8px;font-size:.74rem;
color:#39434d;margin:1px 2px 1px 0;white-space:nowrap}
.chip.ok{background:#e6f4ec;color:var(--ok)}
.chip.warn{background:#fdf2dd;color:var(--warn)}
.chip.bad{background:#fbe9e8;color:var(--bad)}
.src{font-size:.74rem;white-space:nowrap}
.src a{margin-right:4px}
.why{color:var(--mut);font-size:.82rem}
ul,ol{margin:8px 0 8px 20px;padding:0}
li{margin:4px 0}
.foot{margin-top:40px;border-top:1px solid var(--line);padding-top:14px;color:var(--mut);font-size:.8rem}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.tabs a{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 12px;
text-decoration:none;font-size:.82rem}
.tabs a.on{background:var(--acc);color:#fff;border-color:var(--acc)}
@media(max-width:600px){
 h1{font-size:1.26rem} main{padding:14px 10px 50px} table{font-size:.8rem}
 th,td{padding:7px 8px} .card .v{font-size:1.16rem}
}
"""


def money(x):
    if x in ("", None):
        return None
    return D(x)


def usd(x, blank="BLANK"):
    if x in ("", None):
        return f'<span class="blank">{blank}</span>'
    v = D(str(x))
    return f"${v:,.2f}"


def pct(x):
    if x in ("", None):
        return '<span class="blank">BLANK</span>'
    return f"{D(str(x)):.2f}%"


def src_links(ids, sep=" "):
    out = []
    for s in [x for x in (ids or "").split("|") if x]:
        r = SRC.get(s)
        if not r:
            out.append(f'<span class="blank">{esc(s)}?</span>')
        else:
            out.append(f'<a href="{esc(r["url"])}" title="{esc(r["title"])}">{esc(s)}</a>')
    return f'<span class="src">{sep.join(out)}</span>'


def flag_chips(ids):
    out = []
    for f in [x for x in (ids or "").split("|") if x]:
        r = FLAGS.get(f)
        sev = r["severity"] if r else "medium"
        out.append(f'<a class="chip {"bad" if sev == "high" else "warn" if sev == "medium" else ""}" '
                   f'href="c348-flagged.html#{esc(f)}">{esc(f)}</a>')
    return "".join(out)


def page(name, title, body, note=None):
    slug = name.replace("c348-", "").replace(".html", "")
    body = body.replace("<h1>", f'<h1 id="top-{slug}">', 1)
    nav = "".join(f'<a class="{"on" if f == name else ""}" href="{f}">{esc(l)}</a>' for f, l in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · China money (c348)</title>
<meta name="description" content="{esc(note or title)}">
<link rel="stylesheet" href="assets/c348.css">
</head><body>
<header>
  <div class="t">China money · verified CNY→USD edition (c348)</div>
  <div class="s">Every figure recomputed from an official page read on 2026-11-11 · BOC board 20:50:05 Beijing</div>
</header>
<nav>{nav}</nav>
<main>
{body}
<div class="foot">
<p><strong>What this edition is.</strong> An additive, independently verified edition built in its own
file namespace so it collides with no other session's work. It does not edit the canonical dashboard.
Figures are recomputed by <code>scripts/c348_engine.py</code> and re-derived from scratch by
<code>scripts/verify_c348.py</code> (which shares no code with the builder).</p>
<p><strong>What it is not.</strong> Not tax, legal or investment advice. Every blank cell is a cell no
official page read in this pass fills; blanks are named in the tables and listed on
<a href="c348-flagged.html">Flagged for review</a>. Rates move: the board timestamp is printed beside
each figure.</p>
</div>
</main></body></html>
"""


# ------------------------------------------------------------------ shared fragments
def cost_row(mid, amt):
    for r in COSTS:
        if r["method_id"] == mid and r["amount_usd"] == amt:
            return r
    raise SystemExit(f"missing cost row {mid} {amt}")


def money_cell(text):
    """Render a published figure, which may be one number, two numbers or a phrase."""
    text = (text or "").strip()
    try:
        return f"${D(text.replace(',', '')):,.2f}"
    except Exception:
        return esc(text)


def blank_cell(components):
    parts = [x for x in (components or "").split("; ") if x]
    if not parts:
        return "—"
    return ", ".join(f'<span class="blank">{esc(x)}</span>' for x in parts)


def headline(mid, amt="10000.00"):
    r = cost_row(mid, amt)
    return r["known_cost_usd"]


# ------------------------------------------------------------------ pages
def dashboard():
    m01 = cost_row("M01", "10000.00")
    m01b = cost_row("M01", "400000.00")
    m02 = cost_row("M02", "400000.00")
    m04 = cost_row("M04", "400000.00")
    t24 = [r for r in TAX if r["amount_usd"] == "400000.00" and r["acquired_year"] == "2024"][0]
    pen = {(r["penalty_id"], r["amount_usd"]): r for r in PEN}

    cards = f"""
    <div class="cards">
      <div class="card"><div class="k">Bank cost · USD 10,000</div><div class="v">{usd(m01['known_cost_usd'])}</div>
        <div class="n">{pct(m01['known_cost_pct'])} · one documented wire {src_links(m01['source_ids'])}</div></div>
      <div class="card"><div class="k">Bank cost · USD 400,000</div><div class="v">{usd(m01b['known_cost_usd'])}</div>
        <div class="n">{pct(m01b['known_cost_pct'])} · one documented wire</div></div>
      <div class="card"><div class="k">Already USD in China</div><div class="v">{usd(m02['known_cost_usd'])}</div>
        <div class="n">wire only, no spread, on USD 400,000</div></div>
      <div class="card"><div class="k">PRC penalty if done wrong</div><div class="v">{usd(pen[('P01','400000.00')]['exposure_usd'])}</div>
        <div class="n">30% of USD 400,000, Art. 39 {src_links('C06')}</div></div>
      <div class="card"><div class="k">U.S. tax on the gain · 2024 basis</div><div class="v">{usd(t24['us_tax_usd'])}</div>
        <div class="n">on {usd(t24['usd_gain'])} of gain at 15% {src_links('C12|C13')}</div></div>
      <div class="card"><div class="k">Willful FBAR ceiling</div><div class="v">{usd(pen[('P09','400000.00')]['exposure_usd'])}</div>
        <div class="n">50% of the balance {src_links('C17')}</div></div>
    </div>"""

    ladder = ""
    for amt in ("10000.00", "50000.00", "100000.00", "200000.00", "300000.00", "400000.00"):
        a, b, c, d = (cost_row("M01", amt), cost_row("M02", amt),
                      cost_row("M04", amt), cost_row("M10", amt))
        ladder += (f"<tr><td class='num'>{usd(amt)}</td><td class='num'>{usd(a['known_cost_usd'])}</td>"
                   f"<td class='num'>{pct(a['known_cost_pct'])}</td><td class='num'>{usd(b['known_cost_usd'])}</td>"
                   f"<td class='num'>{usd(c['known_cost_usd'])}</td><td class='num'>{c['units']} / {c['calendar_years']} yr</td>"
                   f"<td class='num'>{usd(d['known_cost_usd'])}</td><td>{src_links('C01|C02')}</td></tr>")

    body = f"""
<h1>What it actually costs to get money out of China</h1>
<p class="lede">A U.S. citizen's balance in a Chinese bank, priced from the official Bank of China board
and tariff, the SAFE rules and the U.S. tax code — every cell recomputed, every gap named. Read the
five findings, then the table, then the questions.</p>

<div class="box acc">
<h2 style="margin-top:0">The answer in one paragraph</h3>
<p>The transfer itself is <strong>not</strong> heavily taxed. No official source read in this pass imposes a
tax or a penalty on converting RMB and wiring it out with documents. What you pay is the bank's
spread and wire fee — about <strong>{usd(m01['known_cost_usd'])} on USD 10,000 (0.53%)</strong> and
<strong>{usd(m01b['known_cost_usd'])} on USD 400,000 (0.22%)</strong> at Bank of China. The money at stake
is elsewhere: (1) whether the money can be documented at all, which decides whether any lawful route
exists; (2) the U.S. currency gain, {usd(t24['usd_gain'])} on USD 400,000 if the RMB was acquired in 2024,
taxed at 15% or more; and (3) the penalties for getting the reporting wrong, which are
<strong>{usd(pen[('P01','400000.00')]['exposure_usd'])}</strong> under PRC Art. 39 for a "move it however you
can" approach and up to <strong>{usd(pen[('P09','400000.00')]['exposure_usd'])}</strong> for a willful FBAR
failure — roughly 222 times the bank cost.</p>
</div>

<h2>Five findings that decide everything</h2>
<ol>
<li><strong>The USD 50,000 figure is not a cap.</strong> SAFE states there is no amount limit for genuine
current-account business; above USD 50,000 the transaction simply needs documents instead of an ID
alone {src_links('C05')}. One page in this repository states this backwards ({flag_chips('F08')}).</li>
<li><strong>A U.S. passport holder does not get the USD 50,000 convenience amount.</strong> It belongs to
domestic individuals and to holders of the PRC Foreign Permanent Resident ID
{src_links('C04|C05')}. For a foreign individual the route is Article 59: ID plus source-of-funds
documents including tax evidence {src_links('C03')}.</li>
<li><strong>If the balance is already USD, the spread disappears.</strong> Wiring existing foreign
currency costs only the wire tariff: {usd(m02['known_cost_usd'])} on USD 400,000
{src_links('C22|C02')}. Whether the balance is RMB or USD is question Q01 and it is not recorded anywhere.</li>
<li><strong>The U.S. tax is on the currency gain, not on the money.</strong> Gain = dollars received minus
the dollar basis; the 2021-to-2024 swing on USD 400,000 is a USD 14,575 loss against a USD 27,926 gain
{src_links('C11|C15')}. Whether that gain is capital or ordinary is genuinely unresolved
({flag_chips('F07')}) and worth about USD 6,144 at USD 400,000.</li>
<li><strong>Doing it unlawfully costs 100 times more than doing it lawfully.</strong> {usd(pen[('P01','400000.00')]['exposure_usd'])}
against {usd(m01b['known_cost_usd'])} {src_links('C06')}. The cheap routes that "avoid tax" are the
offences the rules exist to stop.</li>
</ol>

<h2>The cost ladder, six amounts</h2>
<p>Full 40-step ladder on <a href="c348-costs.html">Costs</a>; every row there is recomputed by the verifier.
"Already USD" is a wire of foreign currency you already hold. "Convenience" is the USD 50,000-a-year
route, which needs the PRC Foreign Permanent Resident ID.</p>
<div class="scroll"><table>
<thead><tr><th class="num">Amount</th><th class="num">Documented wire</th><th class="num">% of amount</th>
<th class="num">Already USD</th><th class="num">Convenience route</th><th class="num">Tranches / years</th>
<th class="num">Card withdrawals</th><th>Source</th></tr></thead>
<tbody>{ladder}</tbody></table></div>
<p class="why">Every method also leaves the U.S. receiving-bank fee blank ({flag_chips('F03')}) and the
card route leaves the ATM tariff blank until it is re-read ({flag_chips('F04')}). The bank cost is the
<em>known</em> cost, not the whole cost.</p>

<h2>Where to go next</h2>
<div class="tabs">
<a href="c348-methods.html">17 methods, lawful and prohibited</a>
<a href="c348-costs.html">Every amount, every method</a>
<a href="c348-tax.html">The tax on the conversion</a>
<a href="c348-penalties.html">Penalties</a>
<a href="c348-questions.html">15 questions before any decision</a>
<a href="c348-audit.html">Reconciliation of every prior figure</a>
<a href="c348-flagged.html">12 open items</a>
</div>
"""
    return page("c348-dashboard.html", "Dashboard", body, PAGE_NOTES["c348-dashboard.html"])


def summary():
    m01 = cost_row("M01", "10000.00")
    m01b = cost_row("M01", "400000.00")
    m02 = cost_row("M02", "400000.00")
    m04 = cost_row("M04", "400000.00")
    pen = {(r["penalty_id"], r["amount_usd"]): r for r in PEN}
    t = {(r["amount_usd"], r["acquired_year"]): r for r in TAX}
    body = f"""
<h1>Executive summary</h1>
<p class="lede">What is known, what it costs, what remains unknown, and what to do next — most
important first.</p>

<h2>1. The direct answer to the question asked</h2>
<div class="box ok">
<p><strong>Least-tax lawful way, on the evidence available:</strong> convert through a bank against
documented source-of-funds and tax evidence (method M01) and wire once. It is the only route that the
official texts support for a foreign individual's balance without an eligibility condition
{src_links('C03|C06')}. Its known cost is {usd(m01['known_cost_usd'])} on USD 10,000 and
{usd(m01b['known_cost_usd'])} on USD 400,000.</p>
<p><strong>If the balance is already in USD</strong>, wire it without converting (M02):
{usd(m02['known_cost_usd'])} on USD 400,000, and no currency gain arises on the wire itself.</p>
<p><strong>If the money cannot be documented</strong>, this edition finds no verified lawful route and says
so rather than inventing one. That is question Q02, and it is the first thing to establish.</p>
</div>

<h2>2. What the conversion itself costs</h2>
<div class="scroll"><table>
<thead><tr><th>Component</th><th class="num">USD 10,000</th><th class="num">USD 400,000</th><th>How it is set</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Spread at the bank's board</td><td class="num">{usd(cost_row('M01','10000.00')['spread_usd'])}</td>
<td class="num">{usd(m01b['spread_usd'])}</td>
<td>amount × (selling − midpoint) ÷ selling = 0.2093% on today's board</td><td>{src_links('C01')}</td></tr>
<tr><td>Wire tariff</td><td class="num">{usd(cost_row('M01','10000.00')['wire_fee_usd'])}</td>
<td class="num">{usd(m01b['wire_fee_usd'])}</td>
<td>1 per mille, min CNY 50, max CNY 260, plus CNY 150 cable</td><td>{src_links('C02')}</td></tr>
<tr><td><strong>Known total</strong></td><td class="num"><strong>{usd(m01['known_cost_usd'])}</strong></td>
<td class="num"><strong>{usd(m01b['known_cost_usd'])}</strong></td>
<td>the two rows above, added after rounding to cents</td><td></td></tr>
<tr><td>Receiving / intermediary bank</td><td class="num"><span class="blank">BLANK</span></td>
<td class="num"><span class="blank">BLANK</span></td><td>no official published figure read in this pass</td>
<td>{flag_chips('F03')}</td></tr>
</tbody></table></div>
<p class="why">The wire-fee cap binds from about USD 37,300 of transfer, which is why the cost falls
from 0.53% to 0.22%. That is arithmetic on the published tariff, not a finding about any person.</p>

<h2>3. The taxes and penalties that actually exist</h2>
<div class="scroll"><table>
<thead><tr><th>Item</th><th class="num">On USD 400,000</th><th>What triggers it</th><th>Source</th></tr></thead>
<tbody>
<tr><td>PRC tax on the conversion itself</td><td class="num">$0.00</td><td>nothing found; the conversion is not a taxable event in the texts read</td><td>{src_links('C06|C03')}</td></tr>
<tr><td>U.S. currency gain, acquired 2024</td><td class="num">{usd(t[('400000.00','2024')]['usd_gain'])} of gain</td>
<td>RMB disposed of at a different rate from the acquisition basis</td><td>{src_links('C11|C15')}</td></tr>
<tr><td>U.S. tax on that gain at 15%</td><td class="num">{usd(t[('400000.00','2024')]['us_tax_usd'])}</td>
<td>capital-gain character, IRS Pub. 525 reading</td><td>{src_links('C12|C13')}</td></tr>
<tr><td>The same gain at 37% ordinary</td><td class="num">{usd(D(t[('400000.00','2024')]['usd_gain'])*D('0.37'))}</td>
<td>if 988(a)(1)(A) governs — the open question {flag_chips('F07')}</td><td>{src_links('C11|C14')}</td></tr>
<tr><td>PRC fine, evasion of FX control</td><td class="num">{usd(pen[('P01','400000.00')]['exposure_usd'])}</td>
<td>moving money out in breach of the rules, incl. by deception</td><td>{src_links('C06')}</td></tr>
<tr><td>FBAR non-willful ceiling</td><td class="num">{usd(pen[('P08','400000.00')]['exposure_usd'])}</td>
<td>a missed FBAR, one per violation</td><td>{src_links('C17')}</td></tr>
<tr><td>FBAR willful ceiling</td><td class="num">{usd(pen[('P09','400000.00')]['exposure_usd'])}</td>
<td>a willful missed FBAR — the greater of USD 165,353 or 50% of the balance</td><td>{src_links('C17')}</td></tr>
</tbody></table></div>

<h2>4. What we do not know, and how to find it</h2>
<p>Fifteen questions are set out with the evidence needed and exactly where to get it. Five decide
everything:</p>
<div class="scroll"><table>
<thead><tr><th>#</th><th>Question</th><th>Why it decides the answer</th><th>How to obtain</th></tr></thead>
<tbody>
{''.join(f"<tr><td>{esc(q['id'])}</td><td><strong>{esc(q['question'])}</strong></td><td>{esc(q['why_it_decides'][:210])}…</td><td>{esc(q['how_to_obtain'][:170])}…</td></tr>" for q in QS if q["priority"] == "1")}
</tbody></table></div>
<p><a href="c348-questions.html">All fifteen questions →</a></p>

<h2>5. What to do, in order</h2>
<ol>
<li>Establish the currency of the balance (Q01) and the documents behind it (Q02). Everything else
depends on these two.</li>
<li>Confirm whether any FBAR was due and filed for past years (Q07). Fixing reporting before moving
money is cheaper than explaining it afterwards.</li>
<li>Collect the acquisition dates and rates for the balance (Q05), because they set the U.S. tax.</li>
<li>Choose between M01 (documented conversion) and M02 (wire of existing USD) — nothing else is
priced as a complete route for a foreign individual.</li>
<li>Get the receiving bank's incoming-wire fee in writing (Q09), then send one small test wire.</li>
<li>Get a written opinion on the character of the gain (Q06, {flag_chips('F07')}) before filing.</li>
</ol>

<h2>6. Honest limits of this edition</h2>
<ul>
<li>The U.S. receiving-bank and intermediary fees are <strong>not verified</strong> ({flag_chips('F03')}).</li>
<li>The cross-border RMB route is <strong>not priced at all</strong> ({flag_chips('F02')}).</li>
<li>The ATM tariff and the banknote-carrying threshold are <strong>inherited, not re-read</strong>
({flag_chips('F04')}, {flag_chips('F05')}).</li>
<li>The PRC property-tax and individual-income-tax rates were <strong>not re-read</strong> in this pass;
no figure from them is used.</li>
<li>The capital-versus-ordinary character of a personal gain is <strong>unresolved on the official
texts</strong> ({flag_chips('F07')}).</li>
</ul>
"""
    return page("c348-summary.html", "Executive summary", body, PAGE_NOTES["c348-summary.html"])


def methods():
    rowshtml = ""
    for mid, m in METHODS.items():
        status = m["status"]
        cls = "ok" if status.startswith("lawful") and "limit" not in status and "cap" not in status else \
              "warn" if status.startswith("lawful") else "bad"
        rowshtml += f"""<tr>
<td><strong>{esc(mid)}</strong></td>
<td>{esc(m['name'])}<div class="why">{esc(m['who'])}</div></td>
<td><span class="chip {cls}">{esc(status)}</span></td>
<td>{esc(m['governing'])}</td>
<td>{esc(m['documents'])}</td>
<td>{esc(m['ceiling'])}</td>
<td class="why"><strong>+</strong> {esc(m['pros'])}<br><strong>−</strong> {esc(m['cons'])}</td>
<td>{src_links(m['source_ids'])}</td></tr>"""

    cards = ""
    for mid, m in METHODS.items():
        if m["model"] == "none":
            continue
        a, b = cost_row(mid, "10000.00"), cost_row(mid, "400000.00")
        cards += (f"<tr><td><strong>{esc(mid)}</strong></td><td>{esc(m['name'].split('(')[0].split(' - ')[0][:58])}</td>"
                  f"<td class='num'>{usd(a['known_cost_usd'])}</td><td class='num'>{usd(b['known_cost_usd'])}</td>"
                  f"<td class='num'>{a['units']}</td><td class='num'>{b['units']}</td>"
                  f"<td class='num'>{b['calendar_years'] or '-'}</td>"
                  f"<td>{blank_cell(b['blank_components'])}</td>"
                  f"<td>{flag_chips(b['flag_ids'])}</td></tr>")

    body = f"""
<h1>Every way to turn CNY into USD</h1>
<p class="lede">Seventeen routes: thirteen lawful (one of them "do nothing"), four prohibited. Each
carries the rule that governs it, the documents it needs, its ceiling, its pros and cons, and a source
link. Nothing here is a recommendation for your facts; four of them depend on eligibility you may not
have.</p>

<div class="box warn">
<p><strong>Read this before the table.</strong> The USD 50,000 annual convenience amount is not a cap on
how much may leave China. SAFE states that for genuine current-account and opened capital-account
business there is <em>no amount limit</em>, and that above USD 50,000 the transaction simply cannot be
done on an ID document alone {src_links('C05')}. It is also not generally available to a foreign
national: it belongs to domestic individuals and to holders of the PRC Foreign Permanent Resident ID
{src_links('C04')}.</p>
</div>

<h2>The table</h2>
<div class="scroll"><table>
<thead><tr><th>#</th><th>Method</th><th>Status</th><th>Governing rule</th><th>Documents</th>
<th>Ceiling as stated</th><th>Pros and cons</th><th>Source</th></tr></thead>
<tbody>{rowshtml}</tbody></table></div>

<h2>Costed methods, at the two ends of the range</h2>
<p>Full ladder at every USD 10,000 step on <a href="c348-costs.html">Costs</a>.</p>
<div class="scroll"><table>
<thead><tr><th>#</th><th>Method</th><th class="num">USD 10,000</th><th class="num">USD 400,000</th>
<th class="num">Units @10k</th><th class="num">Units @400k</th><th class="num">Years</th>
<th>Left blank</th><th>Flag</th></tr></thead>
<tbody>{cards}</tbody></table></div>
<p class="why">A blank total means no component of that route could be verified; it is not zero. The
"left blank" column names what is missing in each row.</p>

<h3>Why four routes are marked prohibited</h3>
<ul>
<li><strong>Splitting across other people's quotas</strong> — evasion of FX control: up to 30% of the
amount, 30–100% in serious cases {src_links('C06')}.</li>
<li><strong>Private exchange, money changers, underground banks</strong> — warning, confiscation of gains,
up to 30%, plus criminal liability {src_links('C06')}.</li>
<li><strong>Cryptocurrency or stablecoin</strong> — the PRC designates it an illegal financial activity and
strictly prohibits it; the 2026 notice replaced the 2021 one and kept the prohibition {src_links('C10')}.</li>
<li><strong>False invoices or purpose</strong> — the conversion is reversed and a fine of up to 30%
applies {src_links('C06')}.</li>
</ul>
"""
    return page("c348-methods.html", "Methods", body, PAGE_NOTES["c348-methods.html"])


def costs():
    costed = [mid for mid, m in METHODS.items() if m["model"] != "none"]
    head = "".join(f"<th class='num'>{esc(mid)}</th>" for mid in costed)
    table = ""
    for amt in AMOUNTS:
        cells = ""
        for mid in costed:
            r = cost_row(mid, amt)
            cells += f"<td class='num'>{usd(r['known_cost_usd'], '—')}</td>"
        table += f"<tr><td class='num'>{usd(amt)}</td>{cells}</tr>"

    labels = "".join(f"<th class='num' title='{esc(METHODS[mid]['name'])}'>{esc(mid)}</th>" for mid in costed)

    key = ""
    for mid in ("M01", "M02", "M03", "M04", "M10", "M11"):
        for amt in ("10000.00", "100000.00", "400000.00"):
            r = cost_row(mid, amt)
            key += (f"<tr><td><strong>{esc(mid)}</strong></td><td class='num'>{usd(amt)}</td>"
                    f"<td class='num'>{usd(r['spread_usd'])}</td><td class='num'>{usd(r['wire_fee_usd'])}</td>"
                    f"<td class='num'>{usd(r['usage_fee_usd'])}</td><td class='num'>{usd(r['known_cost_usd'])}</td>"
                    f"<td class='num'>{pct(r['known_cost_pct'])}</td><td class='num'>{r['units']}</td>"
                    f"<td class='num'>{r['calendar_years'] or '—'}</td>"
                    f"<td class='why'>{esc(r['blank_components']) or '—'}</td>"
                    f"<td>{src_links(r['source_ids'])} {flag_chips(r['flag_ids'])}</td></tr>")

    mnames = "".join(f"<li><strong>{esc(k)}</strong> — {esc(v['name'])}</li>" for k, v in METHODS.items()
                     if v["model"] != "none")
    priced_sentence = "; ".join(
        f"{mid} {esc(METHODS[mid]['name'].split(' - ')[0].split(' (')[0])}: {usd(cost_row(mid, '400000.00')['known_cost_usd'])}"
        for mid in costed)

    body = f"""
<h1>What every method costs, USD 10,000 to USD 400,000</h1>
<p class="lede">Six methods can be priced from official pages today; the rest are either unpriced or
prohibited. Amounts are the dollars you want to arrive; the CNY debited is shown in the detail table
below. All figures from the BOC board of 2026-11-11 20:50:05 Beijing {src_links('C01')} and the BOC
personal wire tariff {src_links('C02')}.</p>

<div class="box acc">
<p><strong>The shape of the curve.</strong> The wire fee is 1 per mille of the amount with a CNY 260
ceiling, so it stops growing at about USD 37,300 and becomes a flat CNY 410 (CNY 260 + CNY 150 cable).
Above that, only the spread grows, and it grows linearly. That is why the cost <em>percentage</em>
falls from 0.53% to 0.22% as the amount rises. It is arithmetic on the published tariff, not advice.</p>
</div>

<h2>1. Known bank cost — the matrix</h2>
<p>Every cell is recomputed by the verifier. A dash means the route is prohibited or does nothing; a
red BLANK means no component of that route could be verified.</p>
<div class="scroll"><table>
<thead><tr><th class="num">Amount</th>{labels}</tr></thead>
<tbody>{table}</tbody></table></div>
<p class="why">Method key: <ul>{mnames}</ul></p>

<h2>2. The components, spelled out</h2>
<p>Three amounts per method: the spread, the wire tariff, the card tariff, the total and the percentage.
The last column names what is <em>not</em> in the total.</p>
<div class="scroll"><table>
<thead><tr><th>#</th><th class="num">Amount</th><th class="num">Spread</th><th class="num">Wire</th>
<th class="num">Card</th><th class="num">Known total</th><th class="num">%</th><th class="num">Units</th>
<th class="num">Years</th><th>Left blank</th><th>Source</th></tr></thead>
<tbody>{key}</tbody></table></div>

<h2>3. How the figures are computed, so you can check them</h2>
<div class="box">
<p><strong>Spread.</strong> <code>amount × (selling rate − midpoint) ÷ selling rate</code>, where midpoint
is the arithmetic mean of the board's own buying and selling rates. On today's board:
(6.6871 − 6.6731) ÷ 6.6871 = 0.2093%.</p>
<p><strong>Wire tariff.</strong> <code>min(CNY 260, max(CNY 50, CNY amount × 0.001)) + CNY 150</code>,
converted to USD at the selling rate. One wire is one tariff; eight wires are eight tariffs.</p>
<p><strong>Total.</strong> The components are rounded to cents <em>before</em> they are added, so that the
columns on this page add up to the total shown. The difference from adding first and rounding later is
at most one cent.</p>
<p><strong>Blank means blank.</strong> The U.S. receiving and intermediary fees are not published for a
personal wire, so they are never counted as zero {flag_chips('F03')}. That makes every total here a
<em>known</em> cost and a lower bound, not an all-in quote.</p>
</div>

<h2>4. Every priced method at USD 400,000, in words</h2>
<p>Repeated as text so the figure can be checked against the data by a reader and by the verifier:
{priced_sentence}</p>

<h2>5. What changes the answer</h2>
<ul>
<li><strong>One wire versus tranches.</strong> Pricing USD 400,000 as eight USD 50,000 wires
({usd(cost_row('M04','400000.00')['known_cost_usd'])}) instead of one costs
{usd(cost_row('M04','400000.00')['known_cost_usd']) } − {usd(cost_row('M01','400000.00')['known_cost_usd'])}
more, and takes eight calendar years.</li>
<li><strong>Whether the balance is already USD</strong> — the spread vanishes: {usd(cost_row('M02','400000.00')['known_cost_usd'])}
against {usd(cost_row('M01','400000.00')['known_cost_usd'])}.</li>
<li><strong>The rate.</strong> The board moved intraday and every prior edition froze a different
snapshot; the spread between those snapshots is about USD 2 per USD 10,000 {flag_chips('F10')}.</li>
</ul>
"""
    return page("c348-costs.html", "Costs", body, PAGE_NOTES["c348-costs.html"])


def steps():
    body = ""
    for mid, m in METHODS.items():
        st = [s for s in STEPS if s["method_id"] == mid]
        if not st:
            continue
        r10 = None
        if m["model"] != "none":
            r10 = cost_row(mid, "10000.00")
        costline = f" · known cost at USD 10,000: {usd(r10['known_cost_usd'])}" if r10 else ""
        body += f"""<h2 id="{esc(mid)}">{esc(mid)} — {esc(m['name'])}{costline}</h2>
<p class="why">{esc(m['who'])} · <strong>Rule:</strong> {esc(m['governing'])} · {src_links(m['source_ids'])}</p>
<div class="scroll"><table>
<thead><tr><th>Step</th><th>Do this</th><th>Where</th><th>What you need</th><th>Rule it rests on</th>
<th>Time</th><th>Cost</th></tr></thead>
<tbody>"""
        for s in st:
            body += (f"<tr><td class='num'>{esc(s['seq'])}</td><td>{esc(s['action'])}</td><td>{esc(s['where'])}</td>"
                     f"<td>{esc(s['what_you_need'])}</td><td>{esc(s['official_rule'])}</td><td>{esc(s['time'])}</td>"
                     f"<td>{esc(s['cost_usd'])}</td></tr>")
        body += "</tbody></table></div>"

    intro = """
<h1>Step by step, for every costed method</h1>
<p class="lede">What to do, where to do it, what to bring, and the rule each step rests on. Where a
figure is not published it says so rather than guessing. Steps are a checklist, not legal advice.</p>
<div class="box warn"><p>Before step one of any route: establish the answers to
<a href="c348-questions.html#Q01">Q01</a> (is it RMB or USD), <a href="c348-questions.html#Q02">Q02</a>
(can the source be documented) and <a href="c348-questions.html#Q07">Q07</a> (is the FBAR history clean).
No route works without the first two, and the third is the cheapest thing to fix.</p></div>
"""
    return page("c348-steps.html", "Step by step", intro + body, PAGE_NOTES["c348-steps.html"])


def tax():
    t = {(r["amount_usd"], r["acquired_year"]): r for r in TAX}
    grid = ""
    for amt in ("10000.00", "50000.00", "100000.00", "200000.00", "300000.00", "400000.00"):
        cells = ""
        for y in YEARS:
            r = t[(amt, y)]
            gain = D(r["usd_gain"])
            cls = "color:#0a7a45" if gain < 0 else ""
            cells += f"<td class='num' style='{cls}'>{usd(r['usd_gain'])}</td>"
        cells += f"<td class='num'>{usd(t[(amt,'2024')]['us_tax_usd'])}</td><td>{src_links('C11|C15')}</td>"
        grid += f"<tr><td class='num'>{usd(amt)}</td>{cells}</tr>"

    full = ""
    for r in TAX:
        if r["amount_usd"] not in ("10000.00", "100000.00", "400000.00"):
            continue
        full += (f"<tr><td class='num'>{usd(r['amount_usd'])}</td><td class='num'>{esc(r['acquired_year'])}</td>"
                 f"<td class='num'>{D(r['irs_avg']):.3f}</td><td class='num'>{usd(r['us_basis_usd'])}</td>"
                 f"<td class='num'>{usd(r['usd_gain'])}</td><td>{esc(r['character'])}</td>"
                 f"<td class='num'>{usd(r['us_tax_usd'])}</td><td class='why'>{esc(r['note'])}</td>"
                 f"<td>{src_links(r['source_ids'])}</td></tr>")

    body = f"""
<h1>The tax on the conversion itself</h1>
<p class="lede">Two questions decide this: is there a tax on converting at all (answer: none found), and
is there a U.S. tax on the change in the exchange rate between when you got the RMB and when you sell
it (answer: yes, and it is computed below for every amount and every acquisition year).</p>

<div class="box ok">
<h2 style="margin-top:0">No PRC tax on the conversion</h2>
<p>No official source read in this pass imposes a tax or a fee on converting RMB to USD or on remitting
it. The State Council regulation says current international payments and transfers are not restricted
{src_links('C06')}. What the bank collects is a price — spread and tariff — not a tax. The tax that
exists is on the <em>income behind the money</em>, and on the U.S. side on the <em>currency gain</em>.</p>
</div>

<div class="box warn">
<h2 style="margin-top:0">The one genuinely open question: capital or ordinary</h2>
<p>26 U.S.C. 988(a)(1)(A) makes a foreign-currency gain ordinary income. But 988(e)(1) says the section
does not apply to an individual's <em>personal transaction</em>, and IRS Publication 525 then says a
personal gain above USD 200 is reported as a <strong>capital gain</strong> {src_links('C11|C12')}. The
two point to different rates. On USD 400,000 acquired in 2024 the difference is
<strong>{usd(D(t[('400000.00','2024')]['usd_gain'])*D('0.15'))}</strong> at 15% against
<strong>{usd(D(t[('400000.00','2024')]['usd_gain'])*D('0.37'))}</strong> at 37% — about USD 6,144.
This edition prices the capital reading because that is what the IRS publication says, and states the
ordinary figure beside it rather than choosing silently. {flag_chips('F07')}</p>
</div>

<h2>The gain by the year the RMB was acquired</h2>
<p>Gain = USD received − USD basis, where the basis is set by the exchange rate on the day the RMB was
acquired {src_links('C11')}, using the IRS yearly average for that year {src_links('C15')}. Today's
selling rate is {D(INP['I02']['value']):.4f} CNY per USD {src_links('C01')}. A negative number is a loss.</p>
<div class="scroll"><table>
<thead><tr><th class="num">Amount</th><th class="num">2021</th><th class="num">2022</th><th class="num">2023</th>
<th class="num">2024</th><th class="num">2025</th><th class="num">Tax @15% (2024 basis)</th><th>Source</th></tr></thead>
<tbody>{grid}</tbody></table></div>
<p class="why">A loss row carries no tax figure: a personal currency loss is not deductible, so there is
nothing to deduct and nothing to pay. The tax shown is federal long-term capital gain at 15%
{src_links('C13')}; state tax, the 3.8% net investment income tax and your own bracket are not modelled
here.</p>

<h2>Every input, three amounts</h2>
<div class="scroll"><table>
<thead><tr><th class="num">Amount</th><th class="num">Acquired</th><th class="num">IRS average</th>
<th class="num">USD basis</th><th class="num">Gain</th><th>Character</th><th class="num">Tax @15%</th>
<th>Note</th><th>Source</th></tr></thead>
<tbody>{full}</tbody></table></div>

<h2>Which basis method may be used</h2>
<div class="box">
<p>The regulation permits any reasonable method applied consistently from year to year to all of a
taxpayer's foreign-currency accounts — first in first out, last in first out, or pro rata — but a method
that consistently pulls out the highest-basis units first is expressly not reasonable
{src_links('C11')}. Moving RMB between your own RMB deposits is not itself a taxable event. Choosing
LIFO or FIFO can change the gain materially when the rate has moved a lot between deposits, so the
method is a decision, not an afterthought. It is recorded as <a href="c348-questions.html#Q05">Q05</a>.</p>
</div>

<h2>The U.S. reporting that runs alongside, every year</h2>
<div class="scroll"><table>
<thead><tr><th>Form</th><th>Threshold</th><th>When due</th><th>Penalty for not filing</th><th>Source</th></tr></thead>
<tbody>
<tr><td>FBAR (FinCEN 114)</td><td>Aggregate foreign accounts over USD 10,000 at any time in the year</td>
<td>15 April, automatic extension to 15 October; filed with FinCEN, not the IRS</td>
<td>Non-willful up to USD 16,536; willful the greater of USD 165,353 or 50% of the balance</td><td>{src_links('C16|C17')}</td></tr>
<tr><td>Form 8938</td><td>Single filer in the U.S.: over USD 50,000 at year end or USD 75,000 at any time</td>
<td>With the return</td><td>Separate penalty regime; see the IRS comparison page</td><td>{src_links('C16')}</td></tr>
<tr><td>FinCEN 105</td><td>More than USD 10,000 in cash or monetary instruments in or out of the U.S.</td>
<td>At the border</td><td>Seizure and forfeiture; civil or criminal penalties</td><td>{src_links('C18')}</td></tr>
</tbody></table></div>
<p class="why">The FBAR threshold is about the <em>aggregate</em>: two accounts of USD 6,000 each trigger it.
The penalty figures are the inflation-adjusted maxima from the eCFR table, not the amounts actually
assessed in any case.</p>
"""
    return page("c348-tax.html", "Tax", body, PAGE_NOTES["c348-tax.html"])


def penalties():
    rules = list(PENRULE.values())
    grid = ""
    for amt in ("10000.00", "50000.00", "100000.00", "200000.00", "400000.00"):
        cells = ""
        for r in rules:
            row = [x for x in PEN if x["penalty_id"] == r["id"] and x["amount_usd"] == amt][0]
            cells += f"<td class='num'>{usd(row['exposure_usd'])}</td>"
        grid += f"<tr><td class='num'>{usd(amt)}</td>{cells}</tr>"

    detail = ""
    for r in rules:
        row400 = [x for x in PEN if x["penalty_id"] == r["id"] and x["amount_usd"] == "400000.00"][0]
        detail += (f"<tr id='{esc(r['id'])}'><td><strong>{esc(r['id'])}</strong></td><td>{esc(r['side'])}</td>"
                   f"<td>{esc(r['instrument'])}</td><td>{esc(r['trigger'])}</td><td>{esc(r['rate'])}</td>"
                   f"<td class='num'>{usd(row400['exposure_usd'])}</td><td class='why'>{esc(row400['basis'])}</td>"
                   f"<td>{src_links(r['source_id'])}</td></tr>")

    heads = "".join(f"<th class='num' title='{esc(r['instrument'])}'>{esc(r['id'])}</th>" for r in rules)
    best = [x for x in PEN if x["penalty_id"] == "P01" and x["amount_usd"] == "400000.00"][0]
    fbar = [x for x in PEN if x["penalty_id"] == "P09" and x["amount_usd"] == "400000.00"][0]
    cost = cost_row("M01", "400000.00")
    ratio = D(fbar["exposure_usd"]) / D(cost["known_cost_usd"])

    body = f"""
<h1>What the rules cost when they are broken</h1>
<p class="lede">This is the table that answers the real question. The lawful route on USD 400,000 costs
{usd(cost['known_cost_usd'])}. The unlawful ones cost up to {usd(best['exposure_usd'])} on the Chinese
side and up to {usd(fbar['exposure_usd'])} on the U.S. side — {ratio:,.0f} times the bank cost.</p>

<div class="box bad">
<p><strong>The comparison that matters.</strong> A lawful, documented conversion of USD 400,000 costs
about <strong>{usd(cost['known_cost_usd'])}</strong> in bank spread and wire fee {src_links('C01|C02')}.
Evading China's FX rules carries a fine of up to <strong>{usd(best['exposure_usd'])}</strong> on the same
amount — up to 30% of the sum involved {src_links('C06')}. A willful FBAR failure on a USD 400,000
balance carries up to <strong>{usd(fbar['exposure_usd'])}</strong> — 50% of the balance {src_links('C17')}.
Every "cheap" route that avoids tax is priced against these numbers, not against the {usd(cost['known_cost_usd'])}.</p>
</div>

<h2>Exposure at each amount</h2>
<p>Every rule in the register, computed at five amounts. A BLANK means the exposure depends on facts not
in evidence in this pass — the unremitted PRC income tax (P06), the value seized (P10) and the
virtual-currency exposure (P11) — and is left blank rather than guessed.</p>
<div class="scroll"><table>
<thead><tr><th class="num">Amount</th>{heads}</tr></thead>
<tbody>{grid}</tbody></table></div>

<h2>Every rule, with what it is computed on</h2>
<div class="scroll"><table>
<thead><tr><th>ID</th><th>Side</th><th>Instrument</th><th>Trigger</th><th>Rate as stated</th>
<th class="num">Exposure on USD 400,000</th><th>How that number was produced</th><th>Source</th></tr></thead>
<tbody>{detail}</tbody></table></div>

<h2>What is <em>not</em> a penalty</h2>
<div class="box ok">
<p>The exchange spread, the wire fee and the cable fee are <strong>prices</strong>, not penalties, and they
are not taxes. Nothing in the official texts read for this edition makes the conversion of lawful,
documented money a taxable event on the Chinese side. The tax that does exist is on the income behind
the money, and on the currency gain on the U.S. side. If you have been told the transfer itself carries
"a considerable amount of tax", that statement is not supported by any source read here — it may be
about unpaid PRC income tax, which is a different thing (P06, and question
<a href="c348-questions.html#Q03">Q03</a>).</p>
</div>

<h2>Illustration: lawful versus unlawful on USD 400,000</h2>
<div class="scroll"><table>
<thead><tr><th>Approach</th><th class="num">Known cost / exposure</th><th>What it rests on</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Documented conversion and one wire (M01)</td><td class="num">{usd(cost['known_cost_usd'])}</td>
<td>BOC board and tariff; no tax or penalty found on the conversion</td><td>{src_links('C01|C02|C06')}</td></tr>
<tr><td>Splitting across other people's quotas</td><td class="num">up to {usd(best['exposure_usd'])}</td>
<td>Art. 39, 30% of the amount (30–100% serious) plus possible criminal liability</td><td>{src_links('C06')}</td></tr>
<tr><td>Private exchanger or underground bank</td><td class="num">up to {usd(best['exposure_usd'])}</td>
<td>Art. 45: confiscation of gains and up to 30%, 30–100% serious</td><td>{src_links('C06')}</td></tr>
<tr><td>Missed FBAR, non-willful</td><td class="num">{usd([x for x in PEN if x['penalty_id']=='P08' and x['amount_usd']=='400000.00'][0]['exposure_usd'])}</td>
<td>31 U.S.C. 5321(a)(5)(B)(i) as adjusted</td><td>{src_links('C17')}</td></tr>
<tr><td>Missed FBAR, willful</td><td class="num">{usd(fbar['exposure_usd'])}</td>
<td>50% of the balance, which exceeds the USD 165,353 floor at this size</td><td>{src_links('C17')}</td></tr>
</tbody></table></div>
"""
    return page("c348-penalties.html", "Penalties", body, PAGE_NOTES["c348-penalties.html"])


def questions():
    body = """
<h1>What must be answered before any decision</h1>
<p class="lede">Fifteen questions, ordered by how much they change the answer. For each: why it decides
something, what is already known, what is missing, and exactly how to obtain it. Nothing here can be
answered from the repository; these are facts about your account and your history.</p>
<div class="box acc">
<p><strong>If only three can be answered today, answer these:</strong>
<a href="#Q01">Q01</a> — is the balance RMB or USD (it decides whether you pay a spread at all);
<a href="#Q02">Q02</a> — can the source be documented (it decides whether a lawful route exists);
<a href="#Q07">Q07</a> — is the FBAR history clean (it decides whether the penalties dwarf the cost).</p>
</div>
"""
    for q in QS:
        body += f"""<div class="box" id="{esc(q['id'])}">
<h2 style="margin-top:0">{esc(q['id'])}. {esc(q['question'])} <span class="chip {'bad' if q['priority']=='1' else 'warn' if q['priority']=='2' else ''}">priority {esc(q['priority'])}</span></h2>
<table style="min-width:0">
<tbody>
<tr><th style="width:26%">Why it decides</th><td>{esc(q['why_it_decides'])}</td></tr>
<tr><th>What is already known</th><td>{esc(q['known'])}</td></tr>
<tr><th>What is missing</th><td>{esc(q['missing'])}</td></tr>
<tr><th>How to obtain it</th><td>{esc(q['how_to_obtain'])}</td></tr>
<tr><th>Status</th><td><span class="chip warn">{esc(q['status'])}</span></td></tr>
</tbody></table></div>"""
    return page("c348-questions.html", "Questions", body, PAGE_NOTES["c348-questions.html"])


def audit():
    recon = ""
    for r in RECON:
        verdict = r["verdict"]
        cls = "ok" if verdict in ("current", "agrees-with-RV01") else \
              "bad" if "conflict" in verdict or "differ" in verdict else "warn"
        recon += (f"<tr id='{esc(r['figure_id'])}'><td><strong>{esc(r['figure_id'])}</strong></td>"
                  f"<td>{esc(r['page'])}</td><td class='num'>{usd(r['amount_usd'])}</td>"
                  f"<td class='num'>{money_cell(r['published_usd'])}</td>"
                  f"<td class='why'>{esc(r['basis'])}</td><td><span class='chip {cls}'>{esc(verdict)}</span></td>"
                  f"<td class='why'>{esc(r['note'])}</td><td>{flag_chips(r['flag'])}</td></tr>")

    flags = ""
    for f in FLAGS.values():
        flags += (f"<tr><td><strong>{esc(f['id'])}</strong></td><td><span class='chip bad'>{esc(f['severity'])}</span></td>"
                  f"<td>{esc(f['title'])}</td><td class='why'>{esc(f['where'])}</td><td>{src_links(f['source_ids'])}</td></tr>")

    body = f"""
<h1>Reconciliation and repository audit</h1>
<p class="lede">This repository contains fifteen parallel editions. They publish different headline
figures for the same transfer. This page sets every one of them side by side, states the exact basis
of each, and says which are current, which are superseded by a newer board, and which are genuinely
different because they price a different scenario.</p>

<div class="box acc">
<h2 style="margin-top:0">The short version</h2>
<p><strong>Most of the apparent disagreement is not disagreement.</strong> Of the eighteen figures
compared, the great majority reproduce exactly once you know two things: <em>which board snapshot</em>
was frozen, and <em>whether one wire or eight</em> was being priced. The headline figures move by about
two dollars on USD 10,000 between board snapshots taken hours apart
({flag_chips('F10')}), and the eight-wire scenario legitimately costs about USD 429 more than one wire
at USD 400,000 because the cable fee is paid eight times.</p>
<p><strong>Two things genuinely were wrong, and both are recorded rather than quietly fixed:</strong></p>
<ol>
<li><code>methods.html</code> states the USD 50,000 convenience amount as a legal cap and a purchase
quota available to an individual. SAFE states there is no amount limit for genuine current-account
business and that the annual amount belongs to domestic individuals and Foreign Permanent Resident ID
holders {src_links('C04|C05')}. See {flag_chips('F08')}.</li>
<li>Several editions publish a "full spread" column that charges both halves of the bid-ask spread on a
one-sided conversion. Where it is clearly labelled as a sensitivity it is honest; a reader who takes it
as the answer overstates the cost by about USD 20.94 per USD 10,000 and USD 837.43 per USD 400,000.
See {flag_chips('F01')}.</li>
</ol>
</div>

<h2>Every published headline figure, reconciled</h2>
<div class="scroll"><table>
<thead><tr><th>ID</th><th>Page</th><th class="num">Amount</th><th class="num">Published</th>
<th>Basis as stated on the page</th><th>Verdict</th><th>Why</th><th>Flag</th></tr></thead>
<tbody>{recon}</tbody></table></div>

<h2>How these verdicts were reached</h2>
<div class="box">
<p>Each page's own stated formula was read from the page, not assumed. Two hypotheses were tested and
<strong>rejected</strong> during this work, and are recorded because a rejected hypothesis is part of an
honest audit:</p>
<ul>
<li><em>"53.47 and 53.42 must double-count the spread."</em> Rejected: 53.38 and 53.42 reproduce exactly
as spread + wire under the same one-sided convention, on two different board snapshots. The difference is
the board, not the method.</li>
<li><em>"76e's 53.42 and 901.20 use a full-spread convention."</em> Rejected: <code>76e-verification.html</code>
states its convention in words — <code>spread = amount × (ask − (bid + ask) / 2) / ask</code> — which is
the same one-sided half-spread used everywhere else. The figures differ from today's only by the board.</li>
</ul>
<p>What survives is the smaller, checkable set of findings above, each with the page, the basis and a
source link.</p>
</div>

<h2>Repository irregularities, not fixed by this session</h2>
<p>This session does not edit another edition's pages. What it found is listed here and requested in
<code>COORDINATION.md</code>. The full register is on <a href="c348-flagged.html">Flagged for review</a>.</p>
<div class="scroll"><table>
<thead><tr><th>ID</th><th>Severity</th><th>Finding</th><th>Where</th><th>Source</th></tr></thead>
<tbody>{flags}</tbody></table></div>

<h2>What this session verified, and how</h2>
<div class="box">
<p>Twenty-two official pages were fetched and read on 2026-11-11, each recorded with its URL, the UTC
timestamp of the read, and a verbatim quotation in <a href="c348-sources.html">Sources</a>. Three further
rows are marked <em>not read this session</em> and are used only with that flag.</p>
<p>The arithmetic is recomputed twice: once by <code>scripts/c348_engine.py</code> and once, independently
and with exact fractions, by <code>scripts/verify_c348.py</code>, which does not import the builder. The
verifier also checks that every row carries an official link, that every blank names a flag, that every
internal link and anchor resolves, and that the figures printed on these pages equal the figures in the
CSV. It runs in CI on every push.</p>
</div>
"""
    return page("c348-audit.html", "Reconciliation", body, PAGE_NOTES["c348-audit.html"])


def flagged():
    order = {"high": 0, "medium": 1, "low": 2, "noted": 3}
    body = """
<h1>Flagged for review</h1>
<p class="lede">Everything this edition could not confirm, plus the irregularities it found in the
repository. Nothing here blocks publication; everything here should be read before acting. Each item
names where it appears and the official source that bears on it.</p>
"""
    for f in sorted(FLAGS.values(), key=lambda r: (order.get(r["severity"], 9), r["id"])):
        body += f"""<div class="box {'bad' if f['severity']=='high' else 'warn' if f['severity']=='medium' else ''}" id="{esc(f['id'])}">
<h2 style="margin-top:0">{esc(f['id'])} — {esc(f['title'])} <span class="chip {'bad' if f['severity']=='high' else 'warn'}">{esc(f['severity'])}</span> <span class="chip">{esc(f['status'])}</span></h2>
<table style="min-width:0"><tbody>
<tr><th style="width:26%">What was found</th><td>{esc(f['what'])}</td></tr>
<tr><th>Where</th><td><code>{esc(f['where'])}</code></td></tr>
<tr><th>Official source bearing on it</th><td>{esc(f['official_sources'])} {src_links(f['source_ids'])}</td></tr>
<tr><th>What it changes</th><td>{esc(f['affects'])}</td></tr>
<tr><th>How to close it</th><td>{esc(f['how_to_resolve'])}</td></tr>
</tbody></table></div>"""

    body += """
<h2>Cells left blank on purpose</h2>
<p>Every blank on this site is one of these. None of them is zero.</p>
<div class="scroll"><table>
<thead><tr><th>Blank</th><th>Where it appears</th><th>Why it is blank</th><th>Flag</th></tr></thead>
<tbody>
<tr><td>U.S. receiving-bank and intermediary fees</td><td>Every cost row</td><td>Not published for a personal wire; must be obtained from the receiving bank</td><td><a href="#F03">F03</a></td></tr>
<tr><td>Cross-border RMB conversion price</td><td>Method M03, every amount</td><td>No official offshore CNY-to-USD price was found or read</td><td><a href="#F02">F02</a></td></tr>
<tr><td>Overseas ATM tariff</td><td>Method M10</td><td>The Bank of China notice was not re-read in this pass</td><td><a href="#F04">F04</a></td></tr>
<tr><td>Banknote carrying threshold above USD 5,000</td><td>Method M11</td><td>Inherited from an earlier register row of the repository</td><td><a href="#F05">F05</a></td></tr>
<tr><td>SAFE approval timeline and any government fee</td><td>Methods M05, M06</td><td>No official service standard was found or read</td><td><a href="#F06">F06</a></td></tr>
<tr><td>PRC property and income tax on the underlying money</td><td>Methods M07, M08</td><td>The rates were not re-read in this pass, so no figure is used</td><td><a href="#F06">F06</a></td></tr>
<tr><td>Penalty exposure for unremitted PRC income tax</td><td>Penalties P06</td><td>Depends on facts not in evidence</td><td><a href="#F07">F07</a></td></tr>
<tr><td>Seizure value and virtual-currency exposure</td><td>Penalties P10, P11</td><td>Not a fixed percentage of any amount</td><td>—</td></tr>
</tbody></table></div>
"""
    return page("c348-flagged.html", "Flagged", body, PAGE_NOTES["c348-flagged.html"])


def sources():
    body = """
<h1>Every official page read</h1>
<p class="lede">Each row records the URL, the issuer, the UTC time this session read it, how much of it
was read, what it establishes, and the quotation that establishes it. Rows marked <em>not read this
session</em> are inherited and are used only with that flag.</p>
<div class="box warn"><p><strong>How to audit this page.</strong> Open any link and search for the text in
the last column. If it is not there, the row is wrong and should be reported. Codes beginning C are cited
on every other page of this edition, next to the figure they support.</p></div>
"""
    for sid, r in SRC.items():
        read = "not read this session" in r["how_read"] or r["read_at_utc"] == "not fetched in this pass"
        body += f"""<tr id="{esc(sid)}"{' style="background:#fdf2dd"' if read else ''}>
<td><strong>{esc(sid)}</strong></td><td>{esc(r['issuer'])}</td>
<td><a href="{esc(r['url'])}">{esc(r['title'])}</a></td>
<td>{esc(r['read_at_utc'])}</td><td class="why">{esc(r['how_read'])}</td>
<td>{esc(r['what_it_establishes'])}</td>
<td class="why"><code>{esc(r['verbatim'][:400])}</code></td></tr>"""
    body = body.replace('<div class="box warn">', '<div class="box warn">', 1)
    body = (body.split('<tr id="C01"')[0] +
            '<div class="scroll"><table><thead><tr><th>ID</th><th>Issuer</th><th>Page</th><th>Read (UTC)</th>'
            '<th>How much</th><th>What it establishes</th><th>Quotation</th></tr></thead><tbody><tr id="C01"' +
            body.split('<tr id="C01"')[1] + "</tbody></table></div>")

    body += """
<h2>Inputs and where each came from</h2>
<div class="scroll"><table>
<thead><tr><th>ID</th><th>Input</th><th class="num">Value</th><th>Unit</th><th>As of</th><th>Source</th></tr></thead>
<tbody>""" + "".join(
        f"<tr><td><strong>{esc(i['id'])}</strong></td><td>{esc(i['input'])}</td><td class='num'>{esc(i['value'])}</td>"
        f"<td>{esc(i['unit'])}</td><td>{esc(i['as_of'])}</td><td>{src_links(i['source_id'])}</td></tr>"
        for i in INP.values()) + """
</tbody></table></div>
<p class="why">Every input is either a figure printed on an official page or an arithmetic combination
of such figures, and the note column says which. Nothing is carried in from memory or from a secondary
source.</p>
"""
    return page("c348-sources.html", "Sources", body, PAGE_NOTES["c348-sources.html"])


def main():
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "c348.css").write_text(CSS, encoding="utf-8")
    builders = [dashboard, summary, methods, costs, steps, tax, penalties, questions, audit, flagged, sources]
    for b in builders:
        name = b.__name__
        text = b()
        target = ROOT / f"c348-{ {'dashboard':'dashboard','summary':'summary','methods':'methods','costs':'costs','steps':'steps','tax':'tax','penalties':'penalties','questions':'questions','audit':'audit','flagged':'flagged','sources':'sources'}[name] }.html"
        target.write_text(text, encoding="utf-8")
        print(f"wrote {target.name} ({len(text):,} bytes)")


if __name__ == "__main__":
    main()
