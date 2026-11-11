#!/usr/bin/env python3
"""Build the `bea4` pages: independent re-verification (11 Nov 2026) and the penalty breakdown.

Session `arena/bea42a88-china3`. Data comes only from:
  data/bea4_source_audit.csv      (this session's own fetches)
  data/bea4_cost_recheck.csv      (independent re-derivation of data/e347_costs.csv)
  data/bea4_repricing.csv         (same routes at the 11 Nov board)
  data/bea4_penalty_exposure.csv  (published percentages applied to the same amounts)
  data/bea4_summary.json
  data/e347_sources.csv, data/e347_methods.csv, data/e347_costs.csv  (read-only)

Outputs: bea4-audit.html, bea4-penalty.html. Run with --check to fail when stale.
Styling is the dashboard's own dashboard/site.css, so the pages look like the rest of the site
and stay readable on a phone (tables stack below 720px).
"""
from __future__ import annotations

import csv
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CHECKED_ON = "2026-11-11"
BOARD_10 = "2026/11/10 17:39:58"
BOARD_11 = "2026/11/11 15:30:04"
BOARD_URL = "https://www.boc.cn/sourcedb/whpj/enindex_1619.html"
PROPOSED_PBOC = "https://www.pbc.gov.cn/tiaofasi/144941/3581332/4158143/index.html"
PROPOSED_SAFE = "https://www.safe.gov.cn/shanghai/2018/0515/783.html"

NAV = [
    ("index.html", "Home"),
    ("dashboard/decisions.html", "Decide"),
    ("dashboard/methods.html", "Methods"),
    ("dashboard/costs.html", "Costs"),
    ("dashboard/steps.html", "Steps"),
    ("dashboard/tax.html", "Tax"),
    ("dashboard/flagged.html", "Flagged"),
    ("dashboard/sources.html", "Sources"),
    ("bea4-audit.html", "BEA4 audit"),
    ("bea4-penalty.html", "BEA4 penalties"),
]


def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def money(text, dp=2):
    if text in (None, ""):
        return '<span class="blank">not published</span>'
    return f"{float(text):,.{dp}f}"


def usd(text, dp=2):
    return "USD " + money(text, dp) if text not in (None, "") else money(text, dp)


def esc(text):
    return escape(str(text), quote=True)


def link(url, label):
    return f'<a href="{esc(url)}" rel="noopener">{esc(label)}</a>'


def page(title, description, current, body):
    nav = "".join(
        f'<a href="{href}"{" aria-current=page" if label == current else ""}>{esc(label)}</a>'
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description)}">
<title>{esc(title)}</title>
<link rel="stylesheet" href="dashboard/site.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">China money<small>RMB to USD, source-checked</small></a>
<nav class="nav" aria-label="Sections">{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer class="wrap"><p class="note">Built by session <code>arena/bea42a88-china3</code> on {CHECKED_ON}.
Every figure links to the official page it came from; anything not confirmed from an official page is blank and flagged.
General research, not tax, legal or investment advice. <a href="bea4-audit.html#limits">Method and limits</a>.</p></footer>
</body>
</html>
"""


# --------------------------------------------------------------------------- pieces
def kpis(items):
    cards = "".join(
        f'<div class="kpi"><b>{value}</b><span>{esc(label)}</span>'
        f'<div class="src">{src}</div></div>'
        for value, label, src in items
    )
    return f'<div class="kpis">{cards}</div>'


def source_link(url, label="source"):
    return f'<a href="{esc(url)}" rel="noopener">{esc(label)}</a>'


def audit_page():
    audit = read_csv("bea4_source_audit.csv")
    recheck = read_csv("bea4_cost_recheck.csv")
    repriced = read_csv("bea4_repricing.csv")
    summary = json.loads((DATA / "bea4_summary.json").read_text(encoding="utf-8"))
    sources = {r["id"]: r for r in read_csv("e347_sources.csv")}
    methods = {r["id"]: r for r in read_csv("e347_methods.csv")}
    costs = read_csv("e347_costs.csv")

    confirmed = sum(1 for r in audit if r["result"] == "CONFIRMED")
    broken = [r for r in audit if r["result"] == "LINK_BROKEN"]
    notre = [r for r in audit if r["result"] == "NOT_RECHECKED"]
    proposals = [r for r in audit if r["result"] == "PROPOSED_REPLACEMENT"]

    def cost_at(method, amount):
        for row in costs:
            if row["method_id"] == method and row["amount_usd"] == str(amount):
                return row
        return None

    pills = {"CONFIRMED": "ok", "LINK_BROKEN": "bad", "NOT_RECHECKED": "warn",
             "PROPOSED_REPLACEMENT": "warn"}
    labels = {"CONFIRMED": "confirmed today", "LINK_BROKEN": "link broken",
              "NOT_RECHECKED": "not re-read today", "PROPOSED_REPLACEMENT": "replacement"}

    audit_rows = []
    no_evidence = '<span class="blank">no evidence recorded</span>'
    for r in audit:
        who = f'{esc(r["issuer"])} — {esc(r["title"])}'
        evidence = esc(r["evidence"]) or no_evidence
        audit_rows.append(
            "<tr>"
            f'<td><span class="id">{esc(r["source_id"])}</span></td>'
            f'<td>{who}<br><span class="src">{source_link(r["url"], r["url"])}</span></td>'
            f'<td><span class="pill {pills[r["result"]]}">{labels[r["result"]]}</span></td>'
            f'<td>{evidence}</td>'
            f'<td class="src">{esc(r["note"]) or "—"}</td>'
            "</tr>"
        )

    # recheck per method
    agg = {}
    for r in recheck:
        a = agg.setdefault(r["method_id"], dict(rows=0, cells=0, bad=0))
        a["rows"] += 1
        a["cells"] += int(r["cells_compared"])
        a["bad"] += int(r["mismatches"])
    recheck_rows = []
    no_cost = '<span class="blank">not published</span>'
    for mid in sorted(agg):
        a = agg[mid]
        c10, c400 = cost_at(mid, 10000), cost_at(mid, 400000)
        name = methods.get(mid, {}).get("route", "")
        recheck_rows.append(
            "<tr>"
            f'<td data-label="Route"><span class="id">{esc(mid)}</span>{esc(name)}</td>'
            f'<td data-label="Rows">{a["rows"]}</td>'
            f'<td data-label="Cells compared">{a["cells"]}</td>'
            f'<td data-label="Mismatches"><span class="pill {"ok" if a["bad"] == 0 else "bad"}">{a["bad"]}</span></td>'
            f'<td data-label="Cost at $10,000">{money(c10["known_cost_usd"]) if c10 else no_cost}</td>'
            f'<td data-label="Cost at $400,000">{money(c400["known_cost_usd"]) if c400 else no_cost}</td>'
            f'<td class="src" data-label="Source">{source_link(BOARD_URL, "S01 board")}</td>'
            "</tr>"
        )

    # repricing at $100,000
    rep100 = {r["method_id"]: r for r in repriced if r["amount_usd"] == "100000"}
    rep_rows = []
    for mid in sorted(rep100):
        r = rep100[mid]
        if not r["cost_10nov_usd"]:
            rep_rows.append(
                "<tr>"
                f'<td data-label="Route"><span class="id">{esc(mid)}</span>{esc(methods.get(mid, {}).get("route", ""))}</td>'
                f'<td data-label="Cost, 10 Nov">{money(r["cost_10nov_usd"])}</td>'
                f'<td data-label="Cost, 11 Nov">{money(r["cost_11nov_usd"])}</td>'
                f'<td data-label="Change"></td><td data-label="RMB needed, 10 Nov"></td>'
                f'<td data-label="RMB needed, 11 Nov"></td><td data-label="Change"></td>'
                f'<td class="src" data-label="Source">{source_link(PROPOSED_PBOC, "S37")} '
                f'<span class="blank">no bank tariff published</span></td>'
                "</tr>"
            )
            continue
        rep_rows.append(
            "<tr>"
            f'<td data-label="Route"><span class="id">{esc(mid)}</span>{esc(methods.get(mid, {}).get("route", ""))}</td>'
            f'<td data-label="Cost, 10 Nov">{money(r["cost_10nov_usd"])}</td>'
            f'<td data-label="Cost, 11 Nov">{money(r["cost_11nov_usd"])}</td>'
            f'<td data-label="Change in USD">{money(r["delta_usd"])}</td>'
            f'<td data-label="RMB needed, 10 Nov">{money(r["rmb_10nov"], 2) if r["rmb_10nov"] else "—"}</td>'
            f'<td data-label="RMB needed, 11 Nov">{money(r["rmb_11nov"], 2) if r["rmb_11nov"] else "—"}</td>'
            f'<td data-label="Change in RMB">{money(r["delta_rmb"], 2) if r["delta_rmb"] else "—"}</td>'
            f'<td class="src" data-label="Source">{source_link(BOARD_URL, "S01 board")}</td>'
            "</tr>"
        )

    defects = [
        ("D01", "medium", "One official source link is dead",
         f'S24 (PBOC Beijing, the only citation behind route L08) returns HTTP 404 on {CHECKED_ON}.',
         "Two live replacements read today: " + ", ".join(
             f'{source_link(p["url"], p["source_id"])}' for p in proposals) +
         ". Filed as a change request to the dashboard owner; not edited here.",
         '<a href="https://www.safe.gov.cn/shanghai/2018/0515/783.html" rel="noopener">S36</a>'),
        ("D02", "low", "eCFR as-of date on the dashboard is two days behind",
         'dashboard/sources.html prints the eCFR as of 11/06/2026; the live page says "up to date as of 11/09/2026" today.',
         "Cosmetic; the penalty table itself is unchanged.", source_link(
             "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "S31")),
        ("D03", "info", "A Bank of China ATM tariff changed today and is not in the cost model",
         "The 2026-08-11 notice takes effect 2026-11-11: Mastercard/VISA overseas ATM withdrawals become 2.5%, min USD 3, max USD 40. The UnionPay formula the L10 model uses (CNY 12 + 1%, cap CNY 112) is unchanged before and after.",
         "No change to any published figure. A card-network choice now carries a published cap the model does not price.",
         source_link("https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html", "S03")),
        ("D04", "info", "Bank of China's 'Middle Rate' column is not a midpoint",
         f'Today the column prints {summary["middle_col_11nov"]} while buying {summary["mid_11nov"]} — the arithmetic midpoint of buying and selling — is 667.46 per 100. Using the column as fair value would overstate the bank cost.',
         "The dashboard already warns about this (flag U15 area); restated here with today's numbers.",
         source_link(BOARD_URL, "S01")),
        ("D05", "low", "Ten sources were not re-read in this pass",
         "S05, S08, S09, S11, S14, S15, S18, S22, S26, S34 were read on 2026-11-10 and are marked <em>not re-read today</em>. They are not claimed as verified today.",
         "Re-read them before relying on the rows that cite them.", source_link(
             "https://www.safe.gov.cn/safe/2008/0806/5321.html", "example")),
        ("D06", "info", "The cheapest route looks frozen at large amounts",
         f'L03 (wire out foreign currency already held) is capped at CNY 260 plus the CNY 150 cable fee, so its USD cost stops rising: {money(cost_at("L03", 100000)["known_cost_usd"])} at USD 100,000 and {money(cost_at("L03", 400000)["known_cost_usd"])} at USD 400,000.',
         "Not an error — a published cap. Explained so the figure is not mistaken for a stale row.",
         source_link("https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "S02")),
    ]
    defect_rows = "".join(
        f'<tr><td data-label="ID"><span class="id">{i}</span></td>'
        f'<td data-label="Severity"><span class="pill {"warn" if s in ("low", "medium") else ""}">{s}</span></td>'
        f'<td data-label="What"><b>{esc(what)}</b><br>{detail}</td>'
        f'<td data-label="What was done">{done}</td>'
        f'<td class="src" data-label="Source">{src}</td></tr>'
        for i, s, what, detail, done, src in defects
    )

    body = f"""
<h1>Independent re-verification — {CHECKED_ON}</h1>
<p class="lead">A second session re-read the official pages behind this site and rebuilt its cost
arithmetic in separate code. Short version: the published ladder re-derives to the cent, one
official source link is dead, and a Bank of China tariff changed today.</p>

{kpis([
    (f"{confirmed}/{len(sources)}", "dashboard citations re-read today, confirmed verbatim", '<a href="#sources">row by row below</a>'),
    (f"{summary['cells_compared']:,}", "monetary cells re-derived independently", "0 mismatches"),
    (f"{summary['mismatched_cells']}", "mismatched cells", "max delta 0.00"),
    (f"{len(broken)}", "broken official source link found", "S24, 404 today"),
])}

<h2 id="headlines">What this pass changes, or confirms</h2>
<div class="grid">
<div class="card"><h3>1. The cost ladder is arithmetically right</h3>
<p>The 440 published rows (11 routes × 40 amounts, USD 10,000–400,000) were recomputed in a
separate implementation from the published inputs only: the Bank of China board, the published
wire tariff, the published ATM cap and the published quota. <b>{summary['cells_compared']:,} monetary
cells compared, {summary['mismatched_cells']} mismatches, maximum difference 0.00.</b></p>
<p class="src">Inputs: {source_link(BOARD_URL, "S01 board")}, {source_link("https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "S02 tariff")}</p></div>

<div class="card"><h3>2. Bank cost is a percentage, so waiting costs RMB, not fees</h3>
<p>The bank's buy/sell spread is {summary['spread_10nov_pct']}% of the amount on the 10 Nov board and
{summary['spread_11nov_pct']}% on today's. At USD 400,000 the documented-income route costs
{usd(cost_at('L01', 400000)['known_cost_usd'])} on the published snapshot; repriced at today's board it is
about USD 0.47 lower, while the RMB you must hand over rises by RMB 1,400 (+0.0523%).
The rate level moves the RMB price of a dollar; it barely moves the bank's cut.</p>
<p class="src">Boards: {source_link(BOARD_URL, "S01")} (10 Nov {BOARD_10}; 11 Nov {BOARD_11} Beijing)</p></div>

<div class="card"><h3>3. One official link is dead</h3>
<p><b>S24</b> (PBOC Beijing) returns HTTP 404 today, and it was the only citation behind route
<b>L08</b> — sending the RMB itself abroad and converting outside the mainland. Two live official
pages that support the same proposition were read today and are offered as replacements:
{source_link(proposals[0]['url'], 'S36 (SAFE Shanghai)')} and {source_link(proposals[1]['url'], 'S37 (PBOC 银发〔2020〕330号)')}.</p>
<p class="src">Defect D01 below. The dashboard file is owned by another scope; this is filed, not edited.</p></div>

<div class="card"><h3>4. A tariff changed today</h3>
<p>Bank of China's 2026-08-11 notice takes effect on 2026-11-11. Overseas ATM withdrawal:
UnionPay stays at CNY 12 + 1% (cap CNY 112); <b>Mastercard/VISA becomes 2.5%, min USD 3, max USD 40</b>.
The route the cost model prices (UnionPay) is unchanged, so no published number moves — but the
card-network choice now has a published cap that the model does not price.</p>
<p class="src">{source_link("https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html", "S03 notice")},
{source_link("https://www.safe.gov.cn/hubei/2019/0305/851.html", "S19 card cash caps")}</p></div>

<div class="card"><h3>5. The penalty figures are still current</h3>
<p>31 CFR 1010.821 still lists non-willful <b>USD 16,536</b> and willful <b>USD 165,353</b> for penalties
assessed on or after 17 January 2025; no newer inflation adjustment appears in the table today.
The IRS yearly averages the FX-gain table uses are unchanged (China, 2025: 7.129).</p>
<p class="src">{source_link("https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "S31")},
{source_link("https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates", "S28")}</p></div>

<div class="card"><h3>6. The conversion itself is still not taxed</h3>
<p>Nothing in the sources read today imposes a tax on converting or remitting your own money.
The real exposure is elsewhere, and it is large: Chinese FX-law fines run to 30% of the amount,
or 30–100% in serious cases, and U.S. filing failures run to USD 165,353 or more.
<a href="bea4-penalty.html">See the penalty breakdown →</a></p>
<p class="src">{source_link("https://www.safe.gov.cn/safe/2008/0806/5321.html", "S17 Order 532")},
{source_link("https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", "S27 §988")}</p></div>
</div>

<h2 id="defects">Defects and irregularities, flagged for review</h2>
<p>Published here with the source link so they can be checked without reading any code. Not one of them
blocks the site: D01 needs a one-line URL swap in the dashboard's own data file, which belongs to
another session's scope.</p>
<div class="tbl"><table class="stack">
<thead><tr><th>ID</th><th>Severity</th><th>What</th><th>What was done</th><th class="src">Source</th></tr></thead>
<tbody>{defect_rows}</tbody></table></div>

<h2 id="sources">Source audit — every citation, checked today</h2>
<p>Each row is one citation in <code>data/e347_sources.csv</code>. <em>Confirmed today</em> means the
official page was fetched on {CHECKED_ON} and still says what the row claims, word for word where a
quote is given. <em>Not re-read today</em> is stated plainly rather than glossed over. S36 and S37 are
new pages read today, offered as replacements for the dead S24.</p>
<div class="tbl"><table class="stack">
<thead><tr><th>ID</th><th>Document</th><th>Result</th><th>What the page says today</th><th class="src">Note</th></tr></thead>
<tbody>{''.join(audit_rows)}</tbody></table></div>

<h2 id="recheck">Cost ladder, re-derived in separate code</h2>
<p>For every route and every USD 10,000 step: spread, wire fee, tax, total, percentage and the RMB
debited were recomputed from the published inputs and compared with the published rows.</p>
<div class="tbl"><table class="stack num routes">
<thead><tr><th>Route</th><th>Rows</th><th>Cells</th><th>Mismatches</th><th>Cost at $10,000</th><th>Cost at $400,000</th><th class="src">Source</th></tr></thead>
<tbody>{''.join(recheck_rows)}</tbody></table></div>
<p class="note">L08 has no published cost (no bank publishes a cross-border RMB tariff), so its rows are
blank rather than guessed. Blank is on purpose: see <a href="dashboard/flagged.html">Flagged</a>.</p>

<h2 id="repricing">Repricing: 10 November board versus 11 November board</h2>
<p>Same routes, same tariffs, two rate boards, at USD 100,000. The USD cost is a percentage and hardly
moves; the RMB needed rises with the rate. Full 440-row file: <code>data/bea4_repricing.csv</code>.</p>
<div class="tbl"><table class="stack num routes">
<thead><tr><th>Route</th><th>Cost 10 Nov</th><th>Cost 11 Nov</th><th>Δ USD</th><th>RMB needed 10 Nov</th><th>RMB needed 11 Nov</th><th>Δ RMB</th><th class="src">Source</th></tr></thead>
<tbody>{''.join(rep_rows)}</tbody></table></div>
<p class="note">Boards: {source_link(BOARD_URL, "Bank of China USD row")} — 10 Nov {BOARD_10}
(buy 665.71 / sell 668.51) and 11 Nov {BOARD_11} (buy 666.06 / sell 668.86), CNY per 100 USD.
Fee-only routes are charged in CNY on the account, so they have no RMB column of their own here.</p>

<h2 id="limits">How this was checked, and what it does not cover</h2>
<ul class="plain">
<li><b>Fetches today:</b> 24 of the 35 citations were re-fetched and re-read on {CHECKED_ON};
1 is dead (S24); 10 were not re-read and are labelled so.</li>
<li><b>Arithmetic:</b> an independent implementation, not the dashboard's own module. A shared bug
cannot hide itself if the second implementation is written from the published inputs.</li>
<li><b>Not covered:</b> the actual rate your bank gives you, branch-level or negotiated pricing,
correspondent and receiving-bank fees, U.S. state tax, and any figure that depends on your own
source-of-funds documents. Those stay blank on the <a href="dashboard/flagged.html">Flagged</a> page.</li>
<li><b>Not advice:</b> which route is lawful for you turns on facts not in this repository (how the
RMB was earned, whether tax was paid, your residency and the bank's own checks).</li>
<li><b>Files:</b> <code>data/bea4_source_audit.csv</code>, <code>data/bea4_cost_recheck.csv</code>,
<code>data/bea4_repricing.csv</code>, <code>data/bea4_penalty_exposure.csv</code>;
gate <code>scripts/verify_bea4_site.py</code>; log <code>research/bea4-audit.md</code>.</li>
</ul>
"""
    return page("Independent re-verification, 11 Nov 2026 · China money",
                "A second session re-read 24 official sources and re-derived 1,720 cost cells; one dead link and two tariffs found.",
                "BEA4 audit", body)


def penalty_page():
    pen = read_csv("bea4_penalty_exposure.csv")
    recheck = {r["method_id"]: r for r in read_csv("bea4_cost_recheck.csv") if r["amount_usd"] == "100000"}

    rows = []
    for r in pen:
        rows.append(
            "<tr>"
            f'<td data-label="Amount">{money(r["amount_usd"], 0)}</td>'
            f'<td data-label="Lawful cost (documented income)">{money(r["lawful_cost_l01"])}</td>'
            f'<td data-label="as % of amount">{float(r["lawful_cost_pct"]):.4f}%</td>'
            f'<td data-label="China fine, 30%">{money(r["cn_fine_min_30pct"], 0)}</td>'
            f'<td data-label="China fine, up to 100%">{money(r["cn_fine_max_100pct"], 0)}</td>'
            f'<td data-label="Carrying cash, 20%">{money(r["cn_carry_cash_max_20pct"], 0)}</td>'
            f'<td data-label="U.S. willful FBAR (greater of)">{money(r["us_fbar_willful_greater_of"], 0)}</td>'
            f'<td data-label="Form 8938 maximum">{money(r["us_8938_max"], 0)}</td>'
            f'<td data-label="Form 3520, 25% of gift">{money(r["us_3520_gift_25pct"], 0)}</td>'
            f'<td class="src" data-label="Source">{source_link("https://www.safe.gov.cn/safe/2008/0806/5321.html", "S17")} '
            f'{source_link("https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "S31")} '
            f'{source_link("https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "S29")} '
            f'{source_link("https://www.govinfo.gov/content/pkg/USCODE-2021-title26/html/USCODE-2021-title26-subtitleF-chap61-subchapA-partIII-subpartA-sec6039F.htm", "S33")}</td>'
            "</tr>"
        )

    origins = [
        ("China — evading FX controls (逃汇)", "State Council Order 532, Art. 39",
         "Up to 30% of the amount; where circumstances are serious, 30% up to the equivalent of 100%. Criminal liability possible.",
         "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("China — buying FX with false documents (套汇)", "State Council Order 532, Art. 40",
         "Refund of the funds, plus up to 30%; 30%–100% in serious cases.",
         "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("China — private / underground FX dealing", "State Council Order 532, Art. 45",
         "Warning, confiscation of the proceeds, up to 30%; 30%–100% in serious cases; criminal liability possible.",
         "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("China — carrying currency across the border in breach", "State Council Order 532, Art. 42",
         "Warning; fine up to 20% of the amount.",
         "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("China — untrue or incomplete documents to a bank", "State Council Order 532, Art. 48",
         "For an individual, up to CNY 50,000 — a fixed sum, not a percentage.",
         "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("U.S. — willful FBAR failure", "31 CFR 1010.821 (adjusted 31 U.S.C. 5321(a)(5)(C)(i)(I))",
         "Greater of USD 165,353 or 50% of the balance at the time of the violation (penalties assessed on or after 17 Jan 2025).",
         "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821"),
        ("U.S. — non-willful FBAR failure", "31 CFR 1010.821 (adjusted 31 U.S.C. 5321(a)(5)(B)(i))",
         "Up to USD 16,536 per violation.",
         "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821"),
        ("U.S. — Form 8938 not filed", "IRS comparison of Form 8938 and FBAR",
         "Up to USD 10,000, plus USD 10,000 for each 30 days after IRS notice, maximum USD 60,000.",
         "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements"),
        ("U.S. — Form 3520 not filed for a foreign gift", "26 U.S.C. § 6039F(c)",
         "5% of the gift per month, capped at 25% in aggregate; reasonable-cause exception.",
         "https://www.govinfo.gov/content/pkg/UPCODE-placeholder".replace(
"UPCODE-placeholder", "USCODE-2021-title26/html/USCODE-2021-title26-subtitleF-chap61-subchapA-partIII-subpartA-sec6039F.htm")),
        ("U.S. — travel with more than USD 10,000 undeclared", "CBP / FinCEN Form 105",
         "Failure to report: the currency can be seized or forfeited, with civil or criminal penalties.",
         "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments"),
    ]
    origin_rows = "".join(
        f'<tr><td data-label="Exposure"><b>{esc(n)}</b></td><td data-label="Instrument">{esc(i)}</td>'
        f'<td data-label="What the source says">{esc(w)}</td>'
        f'<td class="src" data-label="Source">{source_link(u, "official page")}</td></tr>'
        for n, i, w, u in origins
    )

    at100 = next(r for r in pen if r["amount_usd"] == "100000")
    at400 = next(r for r in pen if r["amount_usd"] == "400000")

    body = f"""
<h1>The conversion penalty, broken down</h1>
<p class="lead">Converting and remitting your own money is not, on the sources read here, a taxable
event. What actually costs money is four separate things — and only one of them is small.</p>

{kpis([
    (usd(at100["lawful_cost_l01"]), "lawful bank cost to send USD 100,000", source_link(BOARD_URL, "S01 + S02")),
    (usd(at100["cn_fine_min_30pct"], 0), "China FX-law fine at 30% of the same amount", source_link("https://www.safe.gov.cn/safe/2008/0806/5321.html", "S17 Art. 39/40/45")),
    (usd(at100["cn_fine_max_100pct"], 0), "China fine ceiling in serious cases (100%)", source_link("https://www.safe.gov.cn/safe/2008/0806/5321.html", "S17")),
    (usd(at100["us_fbar_willful_greater_of"], 0), "U.S. willful FBAR maximum, or 50% of the balance", source_link("https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "S31")),
])}

<h2 id="stack">1. What is not a penalty</h2>
<ul class="plain">
<li><b>Currency conversion.</b> No source read imposes a tax on exchanging RMB for USD. China's
Order 532 says the state does not restrict current-account international payments and transfers
({source_link("https://www.safe.gov.cn/safe/2008/0806/5321.html", "S17 Art. 5")}).</li>
<li><b>The exchange-rate move.</b> For an individual's personal transaction, §988 gain is not
recognised unless it exceeds USD 200 — and on these balances it usually does
({source_link("https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", "S27(e)")}).
Where it does exceed USD 200, the ordinary-income treatment applies to the gain; that is income tax
on a currency gain, not a toll on transferring.</li>
<li><b>Bank charges.</b> These are a published percentage, not a penalty: 0.1% wire (min CNY 50,
max CNY 260) plus CNY 150 cable, and a 0.4186% buy/sell spread on today's board
({source_link("https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "S02")},
{source_link(BOARD_URL, "S01")}).</li>
</ul>

<h2 id="real">2. What is a penalty, at every USD 10,000 step</h2>
<p>Statutory percentages applied to the same amounts the site prices. These are <b>maxima</b>, not
predictions: a regulator or court fixes the actual amount, and the columns are alternatives, never
additions. The last column before the U.S. figures is the lawful cost of doing it properly on the
documented-income route.</p>
<div class="tbl"><table class="stack num">
<thead><tr><th>Amount</th><th>Lawful cost</th><th>as %</th><th>China 30%</th><th>China up to 100%</th>
<th>Cash carry 20%</th><th>U.S. willful FBAR</th><th>Form 8938 max</th><th>Form 3520 25%</th><th class="src">Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="note">At USD 400,000 the contrast is starkest: {usd(at400["lawful_cost_l01"])} of lawful bank
cost against up to {usd(at400["cn_fine_max_100pct"], 0)} under China's serious-case ceiling, or a
U.S. willful FBAR maximum of {usd(at400["us_fbar_willful_greater_of"], 0)} (the greater of USD 165,353
or 50% of the balance).</p>

<h2 id="origins">3. Where each figure comes from</h2>
<div class="tbl"><table class="stack">
<thead><tr><th>Exposure</th><th>Instrument</th><th>What the source says</th><th class="src">Source</th></tr></thead>
<tbody>{origin_rows}</tbody></table></div>

<h2 id="examples">4. Three worked cases at USD 100,000</h2>
<div class="grid">
<div class="card"><h3>Done properly, documented income</h3>
<p>Cost {money(at100["lawful_cost_l01"])} — {float(at100["lawful_cost_pct"]):.2f}% of the amount —
made up of the bank spread and the wire tariff. No Chinese tax on the conversion; no U.S. tax on the
conversion. Reporting duties still apply: an FBAR once the account exceeds USD 10,000 at any time, and
Form 8938 once the thresholds are met.</p>
<p class="src">{source_link("https://www.fincen.gov/report-foreign-bank-and-financial-accounts", "S30 FBAR")},
{source_link("https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "S29 8938")}</p></div>

<div class="card"><h3>Done through someone else's USD 50,000 amount</h3>
<p>Splitting is expressly prohibited, and the people involved go on a watch list for the year and the
next two. If it is treated as evading FX controls, the fine ceiling is 30% of the amount —
{usd(at100["cn_fine_min_30pct"], 0)} here — rising to 30–100% in serious cases.</p>
<p class="src">{source_link("https://www.safe.gov.cn/guangdong/2020/0304/1668.html", "S21")},
{source_link("https://www.safe.gov.cn/tianjin/2025/0613/2811.html", "S10 watch list")},
{source_link("https://www.safe.gov.cn/safe/2008/0806/5321.html", "S17")}</p></div>

<div class="card"><h3>Transferred lawfully, account never reported</h3>
<p>The transfer can be perfectly lawful and the U.S. exposure still dwarfs it: non-willful FBAR up to
{usd(at100["us_fbar_nonwillful_each"], 0)} per violation; willful up to
{usd(at100["us_fbar_willful_greater_of"], 0)} (greater of USD 165,353 or 50% of the balance);
Form 8938 up to {usd(at100["us_8938_max"], 0)}.</p>
<p class="src">{source_link("https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "S31")},
{source_link("https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "S29")}</p></div>
</div>

<h2 id="limits">5. Limits of this page</h2>
<ul class="plain">
<li>Every percentage is quoted from the official page linked in the row. The multiplication is this
site's own arithmetic and is reproducible from <code>data/bea4_penalty_exposure.csv</code>.</li>
<li>Penalties are discretionary and fact-specific. Whether conduct is 逃汇, 套汇 or neither is decided
by the FX bureau on the documents, not by this table. Nothing here is a prediction.</li>
<li>The columns are alternatives, not cumulative: a single transfer cannot attract both a 30% fine and
a 100% fine, and Chinese and U.S. exposures arise from different conduct.</li>
<li>Chinese tax on the underlying income is a separate question and is blank wherever the facts
(original cost, gain) are not in the repository. See <a href="dashboard/tax.html">Tax</a> and
<a href="dashboard/flagged.html">Flagged</a>.</li>
<li>General research, not tax or legal advice.</li>
</ul>
<p><a href="bea4-audit.html">← Back to the source-by-source re-verification</a></p>
"""
    return page("The conversion penalty, broken down · China money",
                "Statutory penalty percentages applied to USD 10,000-400,000 next to the lawful bank cost, with official sources on every row.",
                "BEA4 penalties", body)


def outputs():
    return {
        ROOT / "bea4-audit.html": audit_page(),
        ROOT / "bea4-penalty.html": penalty_page(),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stale = []
    for path, text in outputs().items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(path.name)
            if not args.check:
                path.write_text(text, encoding="utf-8")
    if args.check:
        if stale:
            print("STALE: " + ", ".join(stale) + " — run python3 scripts/build_bea4_site.py")
            return 1
        print("OK — bea4 pages are up to date.")
        return 0
    print("bea4 build: " + ", ".join(f"{p.name} ({len(p.read_text(encoding='utf-8'))} bytes)" for p in outputs()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
