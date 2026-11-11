#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""n676 site builder — renders the eight n676 pages from the n676 data pack.

Deterministic: running it twice produces byte-identical files. Every data-table row
carries an official-source link, or is rendered as an explicit UNVERIFIED blank and
listed on n676-flagged.html.
"""

from __future__ import annotations

import csv
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import n676_engine as E  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
ASSETS = os.path.join(ROOT, "assets")

BOARD_LABEL = f"Bank of China board, {E.BOARD['stamp']} (Beijing)"
PAGES = ["n676-summary", "n676-questions", "n676-methods", "n676-costs",
         "n676-steps", "n676-tax", "n676-flagged", "n676-sources"]
NAV = [("n676-summary", "Summary"), ("n676-questions", "Questions"),
       ("n676-methods", "Methods"), ("n676-costs", "Costs"),
       ("n676-steps", "Steps"), ("n676-tax", "Tax &amp; penalties"),
       ("n676-flagged", "Flagged"), ("n676-sources", "Sources")]

CSV = {}


def load(name):
    if name not in CSV:
        with open(os.path.join(DATA, name), encoding="utf-8") as fh:
            CSV[name] = list(csv.DictReader(fh))
    return CSV[name]


def e(s):
    return html.escape("" if s is None else str(s), quote=True)


def srcs():
    return {r["id"]: r for r in load("n676_sources.csv")}


SRC = srcs()


def srclink(sid):
    s = SRC.get(sid)
    if not s:
        return f'<span class="miss">{e(sid)}</span>'
    return (f'<a class="s" href="{e(s["url"])}" rel="noopener" title="{e(s["title"])}">'
            f'{e(sid)} <span class="pub">{e(s["publisher"])}</span></a>')


def srclist(ids):
    ids = [x for x in (ids or "").split("|") if x]
    if not ids:
        return '<span class="blank">no official source</span>'
    return " ".join(srclink(i) for i in ids)


def flaglink(fid):
    return f'<a class="flag" href="n676-flagged.html#{e(fid)}">{e(fid)}</a>'


def flaglist(ids):
    ids = [x for x in (ids or "").split("|") if x]
    return " ".join(flaglink(i) for i in ids) if ids else ""


def money(v):
    if v in ("", None):
        return '<span class="blank">not verified</span>'
    return f"${float(v):,.2f}"


def shell(page, title, desc, body):
    parts = []
    for p, label in NAV:
        cur = ' aria-current="page"' if p == page else ""
        parts.append(f'<a href="{p}.html"{cur}>{label}</a>')
    nav = "".join(parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="n676-builder">
<meta name="description" content="{e(desc)}">
<title>{e(title)} · China money</title>
<link rel="stylesheet" href="assets/n676.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="n676-summary.html">China money<small>RMB → USD · re-verified {E.BOARD['stamp'][:10]}</small></a>
<nav class="nav" aria-label="Sections">{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
<footer class="foot">
<p>Priced from the {e(BOARD_LABEL)} and Bank of China's published personal transfer tariff.
Every figure links to the official page it was read from on {E.BOARD['stamp'][:10]}.
Anything that could not be confirmed is left blank and listed under
<a href="n676-flagged.html">Flagged</a>.</p>
<p>Research from public official sources. Not legal, tax or banking advice.
Earlier research passes by other sessions are listed on the
<a href="dashboard/archive.html">Archive</a>.</p>
</footer>
</div></main>
</body>
</html>
"""


# --------------------------------------------------------------------------- pages
def ladder_by(route):
    return {int(r["amount_usd"]): r for r in load("n676_ladder.csv") if r["route_id"] == route}


def at(route, usd):
    return ladder_by(route)[usd]


def page_summary():
    r1, r2, r3, r4 = (ladder_by(x) for x in ("R1", "R2", "R3", "R4"))
    g24_400 = float(r1[400_000]["gain_2024"])
    body = f"""
<h1>Getting RMB out of a Chinese bank account: what it costs and what decides it</h1>
<p class="lead">For a U.S. citizen. Re-verified from official pages on {E.BOARD['stamp'][:10]}.
Costs are Bank of China's published rate and published personal tariff. Every figure links to its
source; everything unconfirmed is blank and <a href="n676-flagged.html">flagged</a>.</p>

<div class="kpis">
<div class="kpi"><b>{money(r1[10_000]['total_usd'])}</b><span>bank cost to convert and wire $10,000</span>
<span class="srow">{srclink('N01')} {srclink('N02')}</span></div>
<div class="kpi"><b>{money(r1[400_000]['total_usd'])}</b><span>same, for $400,000 in one wire</span>
<span class="srow">{srclink('N01')} {srclink('N02')}</span></div>
<div class="kpi"><b>{money(r2[400_000]['total_usd'])}</b><span>if it is already dollars in an FX account</span>
<span class="srow">{srclink('N02')}</span></div>
<div class="kpi"><b>${g24_400:,.0f}</b><span>U.S. currency gain on $400,000, 2024 basis — not the tax</span>
<span class="srow">{srclink('N10')} {srclink('N11')}</span></div>
</div>

<h2>The five things that matter</h2>
<div class="grid">
<div class="card"><h3>1. Converting and wiring is not what gets taxed</h3>
<p>Decree 532 art. 5 does not restrict current-account payments and transfers, and no official page
read here taxes the conversion or the wire. What the bank must see is where the money came from and
that Chinese tax on it was dealt with.</p>
<p class="srow">{srclink('N06')} {srclink('N05')}</p></div>

<div class="card"><h3>2. The real tax, if there is one, is on the income underneath</h3>
<p>If Chinese individual income tax was never paid, it is owed whether or not the money moves:
3% to 45% on comprehensive income, 20% flat on interest, dividends, rent and property gains. That
is orders of magnitude larger than the bank cost.</p>
<p class="srow">{srclink('N09')} {srclink('N09b')}</p></div>

<div class="card"><h3>3. The bank's own cost is a fifth of one percent or less</h3>
<p>The rate cost is {100.0 * (E.rates()[1] - E.rates()[2]) / E.rates()[1]:.5f}% of every dollar,
and the wire fee is 1 per mille capped at RMB 260 plus a RMB 150 telegraph charge. Above about
$38,857 the fee is pinned at the cap, so one wire is always cheapest.</p>
<p class="srow">{srclink('N01')} {srclink('N02')}</p></div>

<div class="card"><h3>4. A U.S. passport does not get the USD 50,000 allowance</h3>
<p>The annual convenience amount applies only to holders of a Chinese Foreign Permanent Resident
ID. A 境外个人 buys dollars on ID <em>plus</em> source-of-funds documents including tax
certificates. And the amount is not a cap: above it you simply cannot proceed on ID alone.</p>
<p class="srow">{srclink('N03')} {srclink('N04')}</p></div>

<div class="card"><h3>5. The U.S. side can be the bigger number</h3>
<p>Selling RMB is a section 988 transaction and the gain is ordinary income. The personal-transaction
relief disappears the moment the gain exceeds $200, which at $10,000 it does. Separately, a missed
FBAR carries up to ${'16,536'} non-willful and ${'165,353'} willful, per violation.</p>
<p class="srow">{srclink('N11')} {srclink('N12')}</p></div>
</div>

<h2>Cost at a glance</h2>
<p>Known bank cost only. The last two columns are the U.S. currency gain — a gain, not a tax — if the
RMB had been acquired at that year's IRS average rate.</p>
<div class="tbl"><table class="num" data-kind="data">
<thead><tr><th>Amount</th><th>Already USD (R2)</th><th>Convert &amp; wire once (R1)</th>
<th>USD 50k a year (R3)</th><th>Gain if bought 2024</th><th>Gain if bought 2025</th>
<th>Source</th></tr></thead>
<tbody>
{''.join(
    f'<tr><td data-label="Amount">${usd:,}</td>'
    f'<td data-label="Already USD (R2)">{money(r2[usd]["total_usd"])}</td>'
    f'<td data-label="Convert &amp; wire once (R1)">{money(r1[usd]["total_usd"])}</td>'
    f'<td data-label="USD 50k a year (R3)">{money(r3[usd]["total_usd"])}</td>'
    f'<td data-label="Gain if bought 2024">{money(r1[usd]["gain_2024"])}</td>'
    f'<td data-label="Gain if bought 2025">{money(r1[usd]["gain_2025"])}</td>'
    f'<td data-label="Source" class="s">{srclink("N01")} {srclink("N02")} {srclink("N10")} {srclink("N11")}</td></tr>'
    for usd in (10_000, 50_000, 100_000, 150_000, 200_000, 300_000, 400_000)
)}
</tbody></table></div>
<p class="note">Every $10,000 step for all four routes: <a href="n676-costs.html">Costs</a>.</p>

<h2>Which route</h2>
<p>Find the line that matches. Cost shown is the known bank cost at $100,000.</p>
<div class="tbl"><table data-kind="data">
<thead><tr><th>If the money is…</th><th>Route</th><th>Bank cost at $100,000</th><th>Next</th></tr></thead>
<tbody>
<tr><td data-label="If the money is…">already dollars in your Chinese foreign-currency account</td>
<td data-label="Route"><a href="n676-methods.html#M02">M02 · wire it out, no conversion</a></td>
<td data-label="Bank cost at $100,000">{money(r2[100_000]['total_usd'])}</td>
<td data-label="Next"><a href="n676-steps.html#M02">Steps</a> · {srclink('N02')}</td></tr>
<tr><td data-label="If the money is…">income you earned in China and can document</td>
<td data-label="Route"><a href="n676-methods.html#M01">M01 · art. 59 purchase and one wire</a></td>
<td data-label="Bank cost at $100,000">{money(r1[100_000]['total_usd'])}</td>
<td data-label="Next"><a href="n676-steps.html#M01">Steps</a> · {srclink('N05')}</td></tr>
<tr><td data-label="If the money is…">from selling a home you owned in China</td>
<td data-label="Route"><a href="n676-methods.html#M04">M04 · emigrant property transfer</a></td>
<td data-label="Bank cost at $100,000">{money(r1[100_000]['total_usd'])}</td>
<td data-label="Next"><a href="n676-steps.html#M04">Steps</a> · {srclink('N07')} {srclink('N08')}</td></tr>
<tr><td data-label="If the money is…">an inheritance</td>
<td data-label="Route"><a href="n676-methods.html#M05">M05 · inheritance transfer</a></td>
<td data-label="Bank cost at $100,000">{money(r1[100_000]['total_usd'])}</td>
<td data-label="Next"><a href="n676-steps.html#M05">Steps</a> · {srclink('N07')} {srclink('N08')}</td></tr>
<tr><td data-label="If the money is…">you hold a Chinese Foreign Permanent Resident ID</td>
<td data-label="Route"><a href="n676-methods.html#M03">M03 · USD 50,000 a year on the card</a></td>
<td data-label="Bank cost at $100,000">{money(r3[100_000]['total_usd'])}</td>
<td data-label="Next"><a href="n676-steps.html#M03">Steps</a> · {srclink('N03')}</td></tr>
<tr><td data-label="If the money is…">profit inside your Chinese company</td>
<td data-label="Route"><a href="n676-methods.html#M09">M09 · dividend, then remit</a></td>
<td data-label="Bank cost at $100,000">{money(r1[100_000]['total_usd'])} <span class="note">plus 20% dividend tax, not priced</span></td>
<td data-label="Next"><a href="n676-steps.html#M09">Steps</a> · {srclink('N08b')} {srclink('N09')}</td></tr>
<tr><td data-label="If the money is…">a gift, or you cannot document it</td>
<td data-label="Route"><span class="blank">no verified route</span></td>
<td data-label="Bank cost at $100,000"><span class="blank">not verified</span> {flaglink('N676-U08')}</td>
<td data-label="Next">{srclink('N05')} {srclink('N07')}</td></tr>
</tbody></table></div>

<h2>Before you decide anything</h2>
<p>Eighteen questions have to be answered first. Three of them decide the answer and cannot be
answered from public sources at all.</p>
<div class="tbl"><table data-kind="data">
<thead><tr><th>Priority</th><th>Question</th><th>Why it decides</th><th>Source</th></tr></thead>
<tbody>
{''.join(
    f'<tr><td data-label="Priority"><span class="pri {e(q["priority"])}">{e(q["priority"])}</span></td>'
    f'<td data-label="Question"><a href="n676-questions.html#{e(q["id"])}">{e(q["id"])} · {e(q["question"])}</a></td>'
    f'<td data-label="Why it decides">{e(q["why_it_decides"][:150])}…</td>'
    f'<td data-label="Source">{srclist(q["source_ids"])}</td></tr>'
    for q in load("n676_questions.csv") if q["priority"] == "critical"
)}
</tbody></table></div>
<p class="note">All eighteen, with what is known, what is missing and exactly how to get it:
<a href="n676-questions.html">Questions</a>.</p>

<h2>Do not do these</h2>
<div class="grid">
<div class="card"><h3>Splitting the quota across relatives or friends</h3>
<p>SAFE treats it as evasion. The people involved go on a watch list for the year of listing and the
following two years, during which every conversion needs transaction documents. Fines run to 30% of
the amount, 30-100% in serious cases, with criminal liability possible.</p>
<p class="srow">{srclink('N06')}</p></div>
<div class="card"><h3>Private swaps, money changers, false invoices, crypto</h3>
<p>Art. 45 covers private buying and selling, disguised dealing, reselling and illegally brokering
FX: confiscation of illegal gains, fines up to 30%, 30-100% in serious cases, criminal liability.
Art. 40 covers buying FX on false documents.</p>
<p class="srow">{srclink('N06')}</p></div>
</div>
"""
    return shell("n676-summary", "Executive summary",
                 "What it costs to convert RMB to USD and which route applies, re-verified "
                 "2026-11-11 from official sources.", body)


def page_questions():
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    qs = sorted(load("n676_questions.csv"), key=lambda q: (order[q["priority"]], q["id"]))
    counts = {}
    for q in qs:
        counts[q["priority"]] = counts.get(q["priority"], 0) + 1
    body = f"""
<h1>Questions that must be answered before a decision can be made</h1>
<p class="lead">{len(qs)} questions. {counts.get('critical', 0)} are critical and none of them can be
answered from public sources — they depend on facts about you that were never supplied. Each row
separates what is <b>already established</b> from what is <b>missing</b>, and says exactly how to
obtain the missing part and who has to ask.</p>
<div class="kpis">
{''.join(f'<div class="kpi"><b>{n}</b><span>{e(p)} questions</span></div>'
         for p, n in sorted(counts.items(), key=lambda kv: order[kv[0]]))}
</div>
{''.join(f'''
<article class="qq" id="{e(q['id'])}">
<h2><span class="pri {e(q['priority'])}">{e(q['priority'])}</span> {e(q['id'])} · {e(q['question'])}</h2>
<dl>
<dt>Why it decides the answer</dt><dd>{e(q['why_it_decides'])}</dd>
<dt>What is already known</dt><dd>{e(q['known'])}</dd>
<dt>What is missing</dt><dd class="missing">{e(q['missing'])}</dd>
<dt>How to get it</dt><dd>{e(q['how_to_get'])}</dd>
<dt>Who asks</dt><dd>{e(q['owner'])}</dd>
<dt>Source</dt><dd>{srclist(q['source_ids'])}</dd>
</dl>
</article>''' for q in qs)}
"""
    return shell("n676-questions", "Questions before a decision",
                 "What is known, what is missing, and how to obtain each missing item before "
                 "choosing a route to move RMB out of China.", body)


def page_methods():
    ms = load("n676_methods.csv")
    lawful = [m for m in ms if m["status"].startswith("Lawful")]
    prohibited = [m for m in ms if m["status"] == "Prohibited"]
    other = [m for m in ms if m not in lawful and m not in prohibited]
    r1 = ladder_by("R1")

    has_steps = {s["method_id"] for s in load("n676_steps.csv")}

    def step_link(mid):
        if mid in has_steps:
            return f'<a href="n676-steps.html#{e(mid)}">Step-by-step &rarr;</a>'
        return ('<span class="note">No step-by-step playbook: this route has no verified '
                'execution path. See '
                '<a href="n676-flagged.html">Flagged</a>.</span>')

    def block(m):
        cost = money(r1[100_000]["total_usd"]) if m["route"] == "R1" else (
            money(ladder_by(m["route"])[100_000]["total_usd"]) if m["route"] else
            '<span class="blank">not verified</span>')
        return f"""
<article class="m" id="{e(m['id'])}">
<h2><span class="id">{e(m['id'])}</span> {e(m['name'])} <span class="st {'ok' if m['status'].startswith('Lawful') else 'no'}">{e(m['status'])}</span></h2>
<div class="tbl"><table data-kind="data">
<tbody>
<tr><th>Who it is for</th><td>{e(m['eligibility'])}</td><td class="s">{srclist(m['source_ids'])}</td></tr>
<tr><th>What the bank or SAFE needs</th><td>{e(m['documents'])}</td><td class="s">{srclist(m['source_ids'])}</td></tr>
<tr><th>Legal cap</th><td>{e(m['cap'])}</td><td class="s">{srclist(m['source_ids'])}</td></tr>
<tr><th>Pros</th><td>{e(m['pros'])}</td><td class="s">{srclist(m['source_ids'])}</td></tr>
<tr><th>Cons</th><td>{e(m['cons'])}</td><td class="s">{srclist(m['source_ids'])}</td></tr>
<tr><th>Tax</th><td>{e(m['tax'])}</td><td class="s">{srclist(m['source_ids'])}</td></tr>
<tr><th>Bank cost at $100,000</th><td>{cost}</td><td class="s">{srclink('N01')} {srclink('N02')}</td></tr>
<tr><th>Open items</th><td>{flaglist(m['flags']) or '<span class="note">none</span>'}</td><td class="s">{srclist(m['source_ids'])}</td></tr>
</tbody></table></div>
<p class="srow">{step_link(m['id'])}</p>
</article>"""

    body = f"""
<h1>Every way to turn CNY into USD</h1>
<p class="lead">{len(ms)} routes: {len(lawful)} lawful, {len(other)} restricted or corporate,
{len(prohibited)} prohibited. Each one lists eligibility, the exact documents, the legal cap, pros,
cons and tax — with an official source on every row. Unverified values are blank and
<a href="n676-flagged.html">flagged</a>, never filled in.</p>

<h2>Lawful routes</h2>
{''.join(block(m) for m in lawful)}
<h2>Restricted and corporate</h2>
{''.join(block(m) for m in other)}
<h2>Prohibited — listed so you can recognise them</h2>
<p>These are not routes. They are recorded because the fines are the largest numbers on this site.</p>
{''.join(block(m) for m in prohibited)}
"""
    return shell("n676-methods", "All methods, pros and cons",
                 "Every way to convert CNY to USD — lawful, restricted and prohibited — with "
                 "eligibility, documents, caps, pros, cons and tax.", body)


def page_costs():
    lad = load("n676_ladder.csv")
    routes = [("R1", "R1 · Buy dollars and wire once to the U.S."),
              ("R2", "R2 · Wire out dollars already in your FX account"),
              ("R3", "R3 · USD 50,000 a year on a Foreign Permanent Resident ID"),
              ("R4", "R4 · Wire to Hong Kong, Macau or Taiwan — first leg only")]
    by = {rid: {int(r["amount_usd"]): r for r in lad if r["route_id"] == rid} for rid, _ in routes}

    # headline matrix: most important first — the total, all four routes side by side
    matrix = f"""
<h2>The whole ladder, all four routes</h2>
<p>Bank cost to get the amount into U.S. dollars, in USD. Most important column first.</p>
<div class="tbl"><table class="num" data-kind="data">
<thead><tr><th>Amount</th><th>R1 convert + wire</th><th>R2 already USD</th>
<th>R3 50k a year</th><th>R4 via HK</th><th>Gain if bought 2024</th><th>Source</th></tr></thead>
<tbody>
{''.join(
    f'<tr><td data-label="Amount">${usd:,}</td>'
    f'<td data-label="R1 convert + wire">{money(by["R1"][usd]["total_usd"])}</td>'
    f'<td data-label="R2 already USD">{money(by["R2"][usd]["total_usd"])}</td>'
    f'<td data-label="R3 50k a year">{money(by["R3"][usd]["total_usd"])}</td>'
    f'<td data-label="R4 via HK">{money(by["R4"][usd]["total_usd"])}</td>'
    f'<td data-label="Gain if bought 2024">{money(by["R1"][usd]["gain_2024"])}</td>'
    f'<td data-label="Source" class="s">{srclink("N01")} {srclink("N02")} {srclink("N10")}</td></tr>'
    for usd in range(10_000, 400_001, 10_000))}
</tbody></table></div>
<p class="note">Gain column is the U.S. currency gain under 26 U.S.C. §988 if the RMB had been
acquired at the IRS 2024 yearly average of 7.189 — a gain, not a tax. {srclink('N10')} {srclink('N11')}</p>
"""

    detail = ""
    for rid, label in routes:
        rows = by[rid]
        detail += f"""
<h3 id="{rid}">{e(label)}</h3>
<div class="tbl"><table class="num" data-kind="data">
<thead><tr><th>Amount</th><th>RMB handed over</th><th>Rate cost</th><th>Wire fee (RMB)</th>
<th>Wire fee (USD)</th><th>Wires</th><th>Total</th><th>% of amount</th><th>Source</th></tr></thead>
<tbody>
{''.join(
    f'<tr><td data-label="Amount">${usd:,}</td>'
    f'<td data-label="RMB handed over">¥{float(rows[usd]["cny_out"]):,.2f}</td>'
    f'<td data-label="Rate cost">{money(rows[usd]["spread_usd"])}</td>'
    f'<td data-label="Wire fee (RMB)">¥{float(rows[usd]["wire_cny"]):,.2f}</td>'
    f'<td data-label="Wire fee (USD)">{money(rows[usd]["wire_usd"])}</td>'
    f'<td data-label="Wires">{e(rows[usd]["n_wires"])}</td>'
    f'<td data-label="Total"><b>{money(rows[usd]["total_usd"])}</b></td>'
    f'<td data-label="% of amount">{float(rows[usd]["total_pct"]):.4f}%</td>'
    f'<td data-label="Source">{srclink("N01")} {srclink("N02")}</td></tr>'
    for usd in range(10_000, 400_001, 10_000))}
</tbody></table></div>
"""

    body = f"""
<h1>Cost of converting and wiring, $10,000 to $400,000</h1>
<p class="lead">40 increments × 4 routes = {len(lad)} rows. Priced from the {e(BOARD_LABEL)}
and Bank of China's published personal transfer tariff. Nothing here is estimated: the only unknown
cost — intermediary and receiving-bank charges — is left blank and {flaglink('N676-U04')}.</p>

<div class="grid">
<div class="card"><h3>How each number is built</h3>
<p><b>Rate cost</b> = amount × (selling − our mid) ÷ selling, where our mid = (6.6630 + 6.6911) ÷ 2 =
6.67705. That is {100.0 * (E.rates()[1] - E.rates()[2]) / E.rates()[1]:.5f}% of every dollar.<br>
<b>Wire fee</b> = 1 per mille of the RMB handed over, floored at RMB 50 and capped at RMB 260, plus a
RMB 150 telegraph charge (RMB 80 to HK, Macau or Taiwan).<br>
<b>Total</b> = the two components, each rounded once, then added.</p>
<p class="srow">{srclink('N01')} {srclink('N02')}</p></div>
<div class="card"><h3>The one number that matters most</h3>
<p>The 1 per mille fee is capped at RMB 260, which binds above about $38,857. After that the fee is
flat, so the whole cost curve is driven by the rate spread — and one wire always beats several.
Eight $50,000 wires cost {money(by['R3'][400_000]['total_usd'])} on $400,000 against
{money(by['R1'][400_000]['total_usd'])} for one.</p>
<p class="srow">{srclink('N02')}</p></div>
</div>
{matrix}
{detail}
"""
    return shell("n676-costs", "Cost tables, $10,000 to $400,000",
                 "Bank cost to convert RMB and wire USD at every $10,000 increment from $10,000 to "
                 "$400,000, for four routes.", body)


def page_steps():
    steps = load("n676_steps.csv")
    ms = {m["id"]: m for m in load("n676_methods.csv")}
    order, seen = [], set()
    for s in steps:
        if s["method_id"] not in seen:
            seen.add(s["method_id"])
            order.append(s["method_id"])
    body = "<h1>Step by step</h1>\n<p class=\"lead\">Exactly how each route is executed, in order, " \
           "with the official source behind each step.</p>\n"
    for mid in order:
        m = ms[mid]
        body += f"""
<article class="m" id="{e(mid)}">
<h2><span class="id">{e(mid)}</span> {e(m['name'])} <span class="st {'ok' if m['status'].startswith('Lawful') else 'no'}">{e(m['status'])}</span></h2>
<ol class="steps">
{''.join(
    f'<li><b>{e(s["step"])}</b><p>{e(s["detail"])}</p>'
    f'<p class="srow">{srclist(s["source_ids"])}</p></li>'
    for s in steps if s["method_id"] == mid)}
</ol>
<p class="srow"><a href="n676-methods.html#{e(mid)}">Pros, cons and documents →</a></p>
</article>"""
    return shell("n676-steps", "Step-by-step playbooks",
                 "Numbered execution steps for each lawful route to move RMB out of China.", body)


def page_tax():
    r1 = ladder_by("R1")
    body = f"""
<h1>Tax and penalties, both sides of the Pacific</h1>
<p class="lead">The bank cost on this site is under 0.6%. Every line below is larger than that.
Rates and maxima are quoted from the official page; anything not verified is blank and
<a href="n676-flagged.html">flagged</a>.</p>

<h2>China side</h2>
<div class="tbl"><table data-kind="data">
<thead><tr><th>What</th><th>Rate or rule</th><th>Applies when</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="What">The conversion itself</td>
<td data-label="Rate or rule"><b>No tax found</b> in any official page read here</td>
<td data-label="Applies when">Current-account payments and transfers are not restricted</td>
<td data-label="Source">{srclink('N06')}</td></tr>
<tr><td data-label="What">The wire itself</td>
<td data-label="Rate or rule"><b>No tax found</b> — a bank fee, not a tax</td>
<td data-label="Applies when">1 per mille, RMB 50-260, plus RMB 150 telegraph</td>
<td data-label="Source">{srclink('N02')}</td></tr>
<tr><td data-label="What">Comprehensive income (wages, labour, author's remuneration, royalties)</td>
<td data-label="Rate or rule"><b>3% to 45%</b> progressive</td>
<td data-label="Applies when">Chinese tax was never paid on the income</td>
<td data-label="Source">{srclink('N09')}</td></tr>
<tr><td data-label="What">Interest, dividends, rent, property transfer, incidental income</td>
<td data-label="Rate or rule"><b>20%</b> flat</td>
<td data-label="Applies when">The balance is one of these categories</td>
<td data-label="Source">{srclink('N09')}</td></tr>
<tr><td data-label="What">Business income</td>
<td data-label="Rate or rule"><b>5% to 35%</b> progressive</td>
<td data-label="Applies when">The money came from a sole proprietorship</td>
<td data-label="Source">{srclink('N09')}</td></tr>
<tr><td data-label="What">Tax clearance before emigrating</td>
<td data-label="Rate or rule">Must settle Chinese tax <b>before</b> the hukou is cancelled</td>
<td data-label="Applies when">You cancel a Chinese household registration to emigrate</td>
<td data-label="Source">{srclink('N09b')}</td></tr>
<tr><td data-label="What">Property transfer registration</td>
<td data-label="Rate or rule">The registration authority <b>must check the tax payment certificate</b>
before it registers the transfer</td>
<td data-label="Applies when">You sell real property in China</td>
<td data-label="Source">{srclink('N09b')}</td></tr>
<tr><td data-label="What">Who is a Chinese tax resident</td>
<td data-label="Rate or rule">Domicile in China, or <b>183 days</b> in a tax year → worldwide income</td>
<td data-label="Applies when">Deciding whether China taxes the income at all</td>
<td data-label="Source">{srclink('N09b')}</td></tr>
<tr><td data-label="What">Bank-deposit interest</td>
<td data-label="Rate or rule"><span class="blank">not verified</span> {flaglink('N676-U05')}</td>
<td data-label="Applies when">The notice supporting the exemption was not re-opened this pass</td>
<td data-label="Source">{srclink('N16')}</td></tr>
<tr><td data-label="What">FX evasion (逃汇)</td>
<td data-label="Rate or rule">Up to <b>30%</b> of the amount; <b>30-100%</b> in serious cases; criminal
liability possible</td>
<td data-label="Applies when">Transferring FX abroad in breach of the rules</td>
<td data-label="Source">{srclink('N06')}</td></tr>
<tr><td data-label="What">Private or disguised FX dealing (私自买卖外汇)</td>
<td data-label="Rate or rule">Confiscation of gains, up to <b>30%</b>; <b>30-100%</b> in serious
cases; criminal liability</td>
<td data-label="Applies when">Money changers, private swaps, brokering</td>
<td data-label="Source">{srclink('N06')}</td></tr>
<tr><td data-label="What">Carrying FX across the border in breach</td>
<td data-label="Rate or rule">Warning plus up to <b>20%</b> of the amount</td>
<td data-label="Applies when">The SAFE-set carrying limit is exceeded</td>
<td data-label="Source">{srclink('N06b')}</td></tr>
<tr><td data-label="What">False or missing documents</td>
<td data-label="Rate or rule">Up to <b>RMB 50,000</b> for an individual</td>
<td data-label="Applies when">Documents are not submitted, or are not genuine</td>
<td data-label="Source">{srclink('N06b')}</td></tr>
<tr><td data-label="What">Chinese carrying limit itself</td>
<td data-label="Rate or rule"><span class="blank">not verified</span> {flaglink('N676-U06')}</td>
<td data-label="Applies when">Decree 532 art. 15 delegates it to SAFE without stating it</td>
<td data-label="Source">{srclink('N06b')}</td></tr>
</tbody></table></div>

<h2>U.S. side</h2>
<div class="tbl"><table data-kind="data">
<thead><tr><th>What</th><th>Amount</th><th>Applies when</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-label="What">Selling RMB for dollars</td>
<td data-label="Amount">A <b>section 988 transaction</b>; the gain is <b>ordinary income</b></td>
<td data-label="Applies when">You dispose of nonfunctional currency — including a demand deposit</td>
<td data-label="Source">{srclink('N11')}</td></tr>
<tr><td data-label="What">Personal-transaction relief</td>
<td data-label="Amount">No gain recognised <b>unless it exceeds $200</b></td>
<td data-label="Applies when">The transaction is personal. At $10,000 with a 2024 basis the gain is
{money(r1[10_000]['gain_2024'])}, so the relief does not apply</td>
<td data-label="Source">{srclink('N11')}</td></tr>
<tr><td data-label="What">Currency gain on $400,000</td>
<td data-label="Amount">{money(r1[400_000]['gain_2024'])} at a 2024 basis · {money(r1[400_000]['gain_2025'])}
at a 2025 basis</td>
<td data-label="Applies when">IRS yearly averages of 7.189 (2024) and 7.129 (2025) against the board's
selling rate of 6.6911</td>
<td data-label="Source">{srclink('N10')} {srclink('N01')}</td></tr>
<tr><td data-label="What">Your real basis</td>
<td data-label="Amount"><span class="blank">not verified</span> {flaglink('N676-U04')}</td>
<td data-label="Applies when">The gain is measured against when and at what rate you actually
acquired the RMB, which was never supplied</td>
<td data-label="Source">{srclink('N10')}</td></tr>
<tr><td data-label="What">FBAR — non-willful</td>
<td data-label="Amount">Up to <b>$16,536</b> per violation</td>
<td data-label="Applies when">An FBAR is not filed for a year; assessed per year</td>
<td data-label="Source">{srclink('N12')}</td></tr>
<tr><td data-label="What">FBAR — willful</td>
<td data-label="Amount">Up to <b>$165,353</b> per violation</td>
<td data-label="Applies when">The failure is willful</td>
<td data-label="Source">{srclink('N12')}</td></tr>
<tr><td data-label="What">General willful BSA violation</td>
<td data-label="Amount"><b>$71,545 to $286,184</b></td>
<td data-label="Applies when">31 U.S.C. 5321(a)(1), penalties assessed on or after 17 January 2025</td>
<td data-label="Source">{srclink('N12')}</td></tr>
<tr><td data-label="What">Foreign earned income exclusion</td>
<td data-label="Amount"><b>$132,900</b> (2026) · <b>$130,000</b> (2025); housing $39,870 / $39,000</td>
<td data-label="Applies when"><b>Earned income only.</b> It does not cover a dividend, rent,
interest, a property gain or the §988 currency gain</td>
<td data-label="Source">{srclink('N13')}</td></tr>
<tr><td data-label="What">Form 3520 Part IV — gift from a nonresident alien or foreign estate</td>
<td data-label="Amount">Reportable above <b>$100,000</b> in the year</td>
<td data-label="Applies when">You receive a foreign gift or bequest; penalties under IRC 6039F(c)</td>
<td data-label="Source">{srclink('N14')}</td></tr>
<tr><td data-label="What">Form 3520 Part IV — from a foreign corporation or partnership</td>
<td data-label="Amount"><b>$20,116</b> (2025) · <b>$20,573</b> (2026)</td>
<td data-label="Applies when">Purported gifts from foreign entities; the IRS may recharacterise them</td>
<td data-label="Source">{srclink('N14')}</td></tr>
<tr><td data-label="What">Form 8938 penalty</td>
<td data-label="Amount"><span class="blank">not verified</span> {flaglink('N676-U04')}</td>
<td data-label="Applies when">The comparison page was not re-opened this pass</td>
<td data-label="Source"><span class="blank">not fetched 2026-11-11</span></td></tr>
<tr><td data-label="What">U.S. cash declaration threshold</td>
<td data-label="Amount"><span class="blank">not verified</span> {flaglink('N676-U06')}</td>
<td data-label="Applies when">The CBP page was not re-opened this pass</td>
<td data-label="Source">{srclink('N17')}</td></tr>
</tbody></table></div>

<h2>What this adds up to</h2>
<div class="grid">
<div class="card"><h3>If Chinese tax is already paid and the U.S. filings are current</h3>
<p>The cost is the bank's: {money(r1[10_000]['total_usd'])} on $10,000 and
{money(r1[400_000]['total_usd'])} on $400,000 — plus whatever the intermediary deducts, which nobody
publishes.</p><p class="srow">{srclink('N01')} {srclink('N02')}</p></div>
<div class="card"><h3>If Chinese tax was never paid on the income</h3>
<p>3% to 45% or a flat 20% of the income, owed regardless of whether the money moves. That is the
"considerable amount of taxes" in the brief — and it is not a charge for the transfer.</p>
<p class="srow">{srclink('N09')}</p></div>
<div class="card"><h3>If the U.S. filings were missed</h3>
<p>Up to $16,536 per unfiled FBAR year, $165,353 if willful, and a §988 ordinary-income gain on top.
Settle these before moving the money, not after.</p><p class="srow">{srclink('N12')} {srclink('N11')}</p></div>
</div>
"""
    return shell("n676-tax", "Tax and penalty breakdown",
                 "Chinese and U.S. tax rates, penalty maxima and reporting thresholds for moving "
                 "RMB out of China, each with its official source.", body)


def page_flagged():
    fl = load("n676_flags.csv")
    irr = [f for f in fl if f["kind"] == "irregularity"]
    unv = [f for f in fl if f["kind"] == "unverified"]

    def block(f):
        return f"""
<article class="fl" id="{e(f['id'])}">
<h2><span class="pri {e(f['severity'])}">{e(f['severity'])}</span> {e(f['id'])} · {e(f['item'])}</h2>
<dl>
<dt>What was found</dt><dd>{e(f['detail'])}</dd>
<dt>Why it is blank or wrong</dt><dd>{e(f['why_blank_or_wrong'])}</dd>
<dt>How to close it</dt><dd>{e(f['how_to_close'])}</dd>
<dt>Source</dt><dd>{srclist(f['source_ids'])}</dd>
</dl>
</article>"""

    body = f"""
<h1>Flagged for review</h1>
<p class="lead">{len(irr)} irregularities found in the repository and in the sources, and
{len(unv)} items left blank because they could not be confirmed from an official source. None of
these blocks the merge; all of them are published here so they can be reviewed and corrected.</p>
<div class="kpis">
<div class="kpi"><b>{len(irr)}</b><span>irregularities</span></div>
<div class="kpi"><b>{len(unv)}</b><span>blank / unverified</span></div>
<div class="kpi"><b>{sum(1 for f in fl if f['severity'] == 'high')}</b><span>high severity</span></div>
</div>
<h2>Irregularities</h2>
<p>Found while re-reading the sources and auditing the repository line by line. Sibling-owned files
were <b>not</b> edited; correction requests are logged in <code>COORDINATION.md</code>.</p>
{''.join(block(f) for f in irr)}
<h2>Blank and unverified</h2>
<p>Left blank on every page rather than estimated or inferred.</p>
{''.join(block(f) for f in unv)}
"""
    return shell("n676-flagged", "Flagged for review",
                 "Irregularities found in the repository and values that could not be confirmed "
                 "from an official source.", body)


def page_sources():
    ss = load("n676_sources.csv")
    fetched = [s for s in ss if s["fetched_today"] == "yes"]
    notf = [s for s in ss if s["fetched_today"] != "yes"]
    body = f"""
<h1>Official source register</h1>
<p class="lead">{len(ss)} sources. {len(fetched)} were opened on {E.BOARD['stamp'][:10]} and the
quote column is copied from the page as it read that day. {len(notf)} were <b>not</b> re-opened and
are listed separately as unverified — no claim on this site rests on them.</p>
<div class="kpis">
<div class="kpi"><b>{len(fetched)}</b><span>re-read today</span></div>
<div class="kpi"><b>{len(notf)}</b><span>not re-read</span></div>
<div class="kpi"><b>{len({s['publisher'] for s in ss})}</b><span>distinct publishers</span></div>
</div>

<h2>Re-read on {E.BOARD['stamp'][:10]}</h2>
<div class="tbl"><table data-kind="data">
<thead><tr><th>ID</th><th>Publisher and title</th><th>Verbatim quote</th><th>What it supports</th></tr></thead>
<tbody>
{''.join(
    f'<tr><td data-label="ID"><a class="s" href="{e(s["url"])}" rel="noopener">{e(s["id"])}</a></td>'
    f'<td data-label="Publisher and title"><b>{e(s["publisher"])}</b><br>{e(s["title"])}'
    f'<br><a class="u" href="{e(s["url"])}" rel="noopener">{e(s["url"])}</a></td>'
    f'<td data-label="Verbatim quote" class="q">{e(s["quote"])}</td>'
    f'<td data-label="What it supports">{e(s["supports"])}</td></tr>'
    for s in fetched)}
</tbody></table></div>

<h2>Not re-opened this pass — carried forward as unverified</h2>
<div class="tbl"><table data-kind="data">
<thead><tr><th>ID</th><th>Publisher and title</th><th>Status</th></tr></thead>
<tbody>
{''.join(
    f'<tr><td data-label="ID"><a class="s" href="{e(s["url"])}" rel="noopener">{e(s["id"])}</a></td>'
    f'<td data-label="Publisher and title"><b>{e(s["publisher"])}</b><br>{e(s["title"])}'
    f'<br><a class="u" href="{e(s["url"])}" rel="noopener">{e(s["url"])}</a></td>'
    f'<td data-label="Status"><span class="blank">not verified</span> {e(s["supports"])}</td></tr>'
    for s in notf)}
</tbody></table></div>
"""
    return shell("n676-sources", "Official source register",
                 "Every official source behind the n676 pages, with the verbatim quote read on "
                 "2026-11-11.", body)


CSS = """\
:root{--bg:#fff;--fg:#151a21;--mut:#5b6675;--line:#e2e7ee;--soft:#f5f7fa;--acc:#0b5fd1;
--ok:#0f7b3f;--no:#b3261e;--hi:#b3261e;--med:#9a6700;--low:#5b6675}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans SC",sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px}
.top{position:sticky;top:0;z-index:20;background:#fff;border-bottom:1px solid var(--line)}
.top .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:8px 18px;padding:10px 16px}
.brand{text-decoration:none;color:var(--fg);font-weight:700;font-size:17px;display:flex;flex-direction:column;line-height:1.2}
.brand small{font-weight:400;color:var(--mut);font-size:12px}
.nav{display:flex;flex-wrap:wrap;gap:4px;margin-left:auto}
.nav a{padding:6px 10px;border-radius:8px;text-decoration:none;color:var(--mut);font-size:14px;font-weight:500}
.nav a:hover{background:var(--soft);color:var(--fg)}
.nav a[aria-current=page]{background:#e8f0fe;color:var(--acc)}
main{padding:26px 0 10px}
h1{font-size:28px;line-height:1.25;margin:0 0 10px;letter-spacing:-.02em}
h2{font-size:20px;margin:34px 0 10px;letter-spacing:-.01em}
h3{font-size:16px;margin:22px 0 8px}
.lead{color:var(--mut);font-size:17px;max-width:74ch;margin:0 0 22px}
p{margin:0 0 12px}
a{color:var(--acc)}
code{background:var(--soft);padding:1px 5px;border-radius:5px;font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0 6px}
.kpi{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.kpi b{display:block;font-size:24px;letter-spacing:-.02em}
.kpi span{display:block;color:var(--mut);font-size:12.5px;line-height:1.4;margin-top:2px}
.kpi .srow{margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin:12px 0}
.card{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#fff}
.card h3{margin:0 0 6px;font-size:15.5px}
.card p{font-size:14.5px;color:#2b333d;margin:0 0 8px}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:8px 0 6px;
border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:14px}
thead th{background:var(--soft);text-align:left;font-weight:600;color:#333c47;
padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap;position:sticky;top:0}
td,th{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}
tbody tr:hover{background:#fafbfd}
table.num td:not(:first-child),table.num th:not(:first-child){text-align:right;font-variant-numeric:tabular-nums}
td.s,th.s{white-space:nowrap}
.q{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;color:#333c47;
white-space:pre-wrap;word-break:break-word}
.u{display:block;font-size:12px;color:var(--mut);word-break:break-all}
a.s{text-decoration:none;white-space:nowrap;border:1px solid var(--line);border-radius:999px;
padding:1px 7px;font-size:12px;background:#fff}
a.s:hover{background:#e8f0fe;border-color:#c6dcfa}
a.s .pub{color:var(--mut)}
.srow{display:flex;flex-wrap:wrap;gap:4px;align-items:center;font-size:12px;color:var(--mut);margin:6px 0 0}
.note{color:var(--mut);font-size:13px}
.blank{color:var(--no);font-weight:600;white-space:nowrap}
.miss{color:var(--no)}
a.flag{color:var(--no);text-decoration:none;border-bottom:1px dotted var(--no);font-size:12.5px}
.id{display:inline-block;background:#e8f0fe;color:var(--acc);border-radius:6px;
padding:1px 7px;font-size:12.5px;font-weight:700;font-variant-numeric:tabular-nums}
.st{font-size:12px;font-weight:600;border-radius:999px;padding:2px 9px;white-space:nowrap}
.st.ok{background:#e6f4ea;color:var(--ok)}
.st.no{background:#fdecea;color:var(--no)}
.pri{display:inline-block;font-size:11.5px;font-weight:700;text-transform:uppercase;
letter-spacing:.04em;border-radius:5px;padding:2px 7px;color:#fff;vertical-align:middle}
.pri.critical,.pri.high{background:var(--hi)}
.pri.medium{background:var(--med)}
.pri.low{background:var(--low)}
article.qq{border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:10px;
padding:12px 16px;margin:12px 0;background:#fff}
article.qq h2{margin:0 0 8px;font-size:17px;line-height:1.35}
article.m,article.fl{border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:14px 0}
article.m h2,article.fl h2{margin:0 0 10px;font-size:17.5px;line-height:1.35}
article.fl{border-left:4px solid var(--no)}
dl{margin:0;font-size:14.5px}
dt{font-weight:600;color:#333c47;margin-top:8px;font-size:13px;text-transform:uppercase;letter-spacing:.03em}
dd{margin:2px 0 0}
dd.missing{color:var(--no);font-weight:600}
ol.steps{margin:0;padding-left:20px}
ol.steps li{margin:0 0 12px}
ol.steps p{margin:2px 0 0;font-size:14.5px;color:#2b333d}
.foot{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);color:var(--mut);font-size:13px}
.foot p{margin:0 0 8px}
@media (max-width:760px){
 h1{font-size:23px}h2{font-size:18px}.lead{font-size:15.5px}
 .top .wrap{padding:8px 12px}.nav{margin-left:0;width:100%;overflow-x:auto;flex-wrap:nowrap}
 .nav a{flex:0 0 auto}
 .wrap{padding:0 12px}
 .tbl{border:0;border-radius:0}
 table,thead,tbody,tr,td,th{display:block;width:100%}
 thead{display:none}
 tbody tr{border:1px solid var(--line);border-radius:10px;margin:0 0 10px;padding:6px 10px;background:#fff}
 td,th{border:0;padding:5px 0;display:flex;gap:10px}
 td::before,th::before{content:attr(data-label);flex:0 0 42%;font-weight:600;color:var(--mut);font-size:12.5px}
 table.num td{text-align:left}
 td.s::before{display:none}
 .q{white-space:pre-wrap}
}
@media print{.top{position:static}.tbl{overflow:visible}}
"""


def main():
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "n676.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    renderers = {
        "n676-summary": page_summary,
        "n676-questions": page_questions,
        "n676-methods": page_methods,
        "n676-costs": page_costs,
        "n676-steps": page_steps,
        "n676-tax": page_tax,
        "n676-flagged": page_flagged,
        "n676-sources": page_sources,
    }
    assert set(renderers) == set(PAGES), set(renderers) ^ set(PAGES)
    for name in PAGES:
        path = os.path.join(ROOT, f"{name}.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(renderers[name]())
        print(f"wrote {name}.html ({os.path.getsize(path):,} bytes)")


if __name__ == "__main__":
    main()
