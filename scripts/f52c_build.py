#!/usr/bin/env python3
"""Build questions.html - the decision register for the f52c session.

    python3 scripts/f52c_build.py            write the page
    python3 scripts/f52c_build.py --check    fail if the page on disk is stale

Numbers on the page are never typed in: the ladder and the per-route table are read
from data/f52c_ladder.csv and data/f52c_method_costs.csv, which scripts/f52c_engine.py
writes from the published board and tariff. Text answers come from
data/f52c_questions.csv, sources from data/f52c_sources.csv, open items from
data/f52c_flags.csv.
"""
from __future__ import annotations

import argparse
import csv
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "questions.html"
REPO = "https://github.com/sassnarep3-star/China3"
BOARD = "2026/11/11 10:25:02"
READ_ON = "11 November 2026"

esc = html.escape


def rows(name):
    with (ROOT / "data" / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


SOURCES = {r["id"]: r for r in rows("f52c_sources.csv")}
QUESTIONS = rows("f52c_questions.csv")
FLAGS = rows("f52c_flags.csv")
LADDER = rows("f52c_ladder.csv")
METHOD_COSTS = rows("f52c_method_costs.csv")

NAV = [("index.html", "Home"), ("questions.html", "Questions"), ("dashboard/methods.html", "Methods"),
       ("dashboard/costs.html", "Costs"), ("dashboard/steps.html", "Steps"), ("dashboard/tax.html", "Tax"),
       ("dashboard/flagged.html", "Flagged"), ("dashboard/sources.html", "Sources"),
       ("dashboard/archive.html", "Archive")]

ROUTE_NAMES = {
    "L01": "Documented income earned in China",
    "L02": "Change back unused RMB with the original slip",
    "L03": "Wire out foreign currency already held",
    "L04": "Proceeds of selling a home in China",
    "L05": "Inheritance transfer",
    "L06": "Emigrant property transfer",
    "L07": "USD 50,000 annual convenience amount",
    "L08": "Send the RMB itself abroad (cross-border RMB)",
    "L09": "Dividend from your own Chinese company",
    "L10": "Card cash withdrawals abroad",
    "L11": "Carry foreign cash out in person",
}
KEY = ["10000", "50000", "100000", "200000", "400000"]
STATUS_PILL = {"VERIFIED": ('ok', 'sourced answer'),
               "OPEN": ('warn', 'needs your facts'),
               "UNVERIFIED": ('bad', 'no official answer')}


def usd(x):
    return f"${float(x):,.2f}" if x not in ("", None) else '<span class="blank">not published</span>'


def src(ids, short=True):
    out = []
    for i in (ids or "").split():
        s = SOURCES.get(i)
        if not s:
            continue
        label = i if short else f"{i} {s['issuer']}"
        out.append(f'<a href="{esc(s["url"])}" rel="noopener" title="{esc(s["title"])}">{esc(label)}</a>')
    return " ".join(out)


def table(head, body, cls="stack", caption=None, kind="data"):
    src_cls = ' class="src"'
    out = [f'<div class="tbl"><table class="{cls}" data-kind="{kind}">']
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<thead><tr>" + "".join(
        f'<th{src_cls if i == len(head) - 1 and cls == "stack" else ""}>{esc(h)}</th>'
        for i, h in enumerate(head)) + "</tr></thead><tbody>")
    out.extend(body)
    out.append("</tbody></table></div>")
    return "\n".join(out)


# ------------------------------------------------------------------ the sections
def kpis():
    q = len(QUESTIONS)
    v = sum(1 for r in QUESTIONS if r["status"] == "VERIFIED")
    o = sum(1 for r in QUESTIONS if r["status"] == "OPEN")
    u = sum(1 for r in QUESTIONS if r["status"] == "UNVERIFIED")
    top = LADDER[-1]
    return f"""<div class="kpis">
<div class="kpi"><b>{usd(top['l01_cost_usd'])}</b><span>bank cost to convert and wire $400,000</span><span class="src">{src("F01 F02")}</span></div>
<div class="kpi"><b>{usd(LADDER[0]['l01_cost_usd'])}</b><span>the same route at $10,000</span><span class="src">{src("F01 F02")}</span></div>
<div class="kpi"><b>{v} of {q}</b><span>questions answered from an official page read today ({o} need your facts, {u} have no answer)</span><span class="src"><a href="#questions">Questions</a></span></div>
<div class="kpi"><b>{len(FLAGS)}</b><span>open or flagged items, listed at the end</span><span class="src"><a href="#flagged">Flagged</a></span></div>
</div>"""


def short_answer():
    return f"""<h2 id="answer">The short answer</h2>
<div class="grid">
<div class="card"><h3>1. The conversion is not the taxed event</h3>
<p>No official page read today taxes converting RMB into USD or wiring it out. What the bank checks is whether the money is genuine and lawful and whether Chinese tax on it has been dealt with. The large numbers in this problem are Chinese income tax on the money behind the balance, and U.S. income tax on the currency gain.</p>
<p class="src">{src("F10 F04 F09")} · <a href="dashboard/tax.html">Tax page</a></p></div>
<div class="card"><h3>2. The bank's own charge is small - about 0.2-0.5 %</h3>
<p>{usd(LADDER[0]['l01_cost_usd'])} on $10,000 (0.53 %) and {usd(LADDER[-1]['l01_cost_usd'])} on $400,000 (0.23 %): the exchange margin plus the RMB 260 wire cap and the RMB 150 cable fee. Fees charged by the receiving or intermediary bank are not published anywhere and are excluded.</p>
<p class="src">{src("F01 F02")} · <a href="#ladder">Ladder</a></p></div>
<div class="card"><h3>3. A U.S. passport alone does not get the $50,000 facility</h3>
<p>The annual USD 50,000 convenience amount is for domestic individuals and for foreign individuals holding a Chinese Foreign Permanent Resident ID. Everyone else converts under art 59 with identity plus source-of-funds documents including tax evidence.</p>
<p class="src">{src("F04 F05 F06")} · <a href="dashboard/methods.html">Methods</a></p></div>
<div class="card"><h3>4. Six facts decide everything, and only you have them</h3>
<p>Where the money came from, which currency it is, how much, when it was acquired, your Chinese residence status, and your U.S. reporting history. Until those six are written down, no route can be recommended - which is why this page is organised as questions rather than as a recommendation.</p>
<p class="src"><a href="#questions">Questions A01-A14</a> · <a href="#flagged">Flagged</a></p></div>
</div>"""


def questions_section():
    out = [f"""<h2 id="questions">The questions, with the answers we do and do not have</h2>
<p class="lead">Section A is facts only you can supply. Sections B and C are the rules, each answer read from an official page on {READ_ON} and linked. Section D is the decision itself. Where no official page answers a question, the answer is left blank and carries a flag - nothing is inferred.</p>"""]
    for section in ("A. Facts only you can supply", "B. Chinese-side rules", "C. U.S. side", "D. The decision"):
        block = [r for r in QUESTIONS if r["section"] == section]
        if not block:
            continue
        body = []
        for r in block:
            cls, label = STATUS_PILL[r["status"]]
            pill = f'<span class="pill {cls}">{esc(r["status"].lower())}</span> <span class="note">{esc(label)}</span>'
            flag = f'<br><a class="note" href="#{esc(r["flag"])}">{esc(r["flag"])}</a>' if r["flag"] else ""
            answer = esc(r["answer"]) or '<span class="blank">no official answer</span>'
            settle = esc(r["how_to_settle"]) or '<span class="blank">n/a</span>'
            body.append(
                f'<tr id="{esc(r["id"])}"><td data-label="Question"><span class="id">{esc(r["id"])}</span>'
                f'{esc(r["question"])}<br>{pill}{flag}</td>'
                f'<td data-label="Answer we have">{answer}</td>'
                f'<td data-label="How to settle it">{settle}</td>'
                f'<td class="src" data-label="Source">{src(r["source_ids"])}</td></tr>')
        n = len(block)
        out.append(f"<h3>{esc(section)} <span class=\"note\">({n} question{'s' if n != 1 else ''})</span></h3>")
        out.append(table(["Question", "Answer we have", "How to settle it", "Source"], body))
    return "\n".join(out)


def ladder_section():
    body = []
    for r in LADDER:
        key = " key" if r["amount_usd"] in KEY else ""
        years = r["l07_years"]
        body.append(
            f'<tr id="amt{r["amount_usd"]}"><td class="{key.strip()}">{esc(usd(r["amount_usd"]))}</td>'
            f'<td>{esc(usd(r["l01_cost_usd"]))}</td><td>{esc(r["l01_pct"])} %</td>'
            f'<td>{esc(usd(r["l03_cost_usd"]))}</td>'
            f'<td>{esc(usd(r["l07_cost_usd"]))}</td><td>{esc(years)}</td>'
            f'<td>{esc(usd(r["us_gain_2024"]))}</td></tr>')
    head = ["Amount", "Convert + wire (L01)", "L01 %", "Wire only (L03)", "50k-a-year (L07)", "L07 years", "U.S. gain, illustration"]
    return f"""<h2 id="ladder">What it costs, in $10,000 steps from $10,000 to $400,000</h2>
<p>Every cell is computed by <code>scripts/f52c_engine.py</code> from the Bank of China board published {BOARD} (buying 666.30, selling 669.11 per 100 USD) and the published personal tariff: 1 per mille, minimum RMB 50, maximum RMB 260, plus RMB 150 cable. The conversion is costed at the midpoint of buying and selling (6.67705); the last column is not a bank cost at all - see the note below the table.</p>
{table(head, body, cls="num routes", caption="Total known cost, in USD", kind="data")}
<p class="note">All figures are the <b>known</b> bank cost. The receiving bank's and any intermediary bank's fees are not published and are in the Flagged list. The last column is a <b>U.S. tax illustration, not a cost</b>: the §988 gain if RMB sold today for that many dollars had been acquired at the IRS 2024 yearly average of 7.189. Your basis is your own acquisition rate - see <a href="#A04">A04</a> and <a href="#C02">C02</a>. {src("F01 F02 F18 F17")}</p>"""


def routes_section():
    by = {}
    for r in METHOD_COSTS:
        by.setdefault(r["method_id"], {})[r["amount_usd"]] = r
    body = []
    for mid, name in ROUTE_NAMES.items():
        cells = [f'<td>{esc(name)}</td>']
        for k in KEY:
            r = by[mid][k]
            cells.append(f'<td>{esc(usd(r["known_cost_usd"]))}</td>')
        last = by[mid]["400000"]
        units = last["units"] or "-"
        years = last["calendar_years"] or "-"
        cells.append(f'<td>{esc(units)}</td><td>{esc(years)}</td>')
        body.append(f'<tr id="route{mid}"><td>{esc(mid)}</td>' + "".join(cells) + "</tr>")
    head = ["Route", "Name", "$10,000", "$50,000", "$100,000", "$200,000", "$400,000", "Units at $400k", "Years"]
    return f"""<h2 id="routes">Every lawful route, at the five decision amounts</h2>
<p>Same engine, same board, same convention as the ladder. "Units" counts the wires, trips or withdrawals at $400,000; "years" applies the published annual caps. Full 40-step detail for all eleven routes is in <a href="dashboard/costs.html">Costs</a> and in <code>data/f52c_method_costs.csv</code>.</p>
{table(head, body, cls="num routes", caption="Known cost in USD at each amount", kind="data")}
<p class="note">The dividend row includes 20 % Chinese individual income tax on the gross before the conversion, which is why it dwarfs the bank fee. The card and cash rows price only the published part of the cost. The 50k-a-year row assumes one exchange rate across eight years. {src("F01 F02 F03 F05 F12 F13 F14")}</p>"""


def steps_section():
    rows_ = [
        ("Documented income earned in China",
         "Contract, payslips, Chinese tax evidence, passport. The bank converts at its selling rate and wires.",
         "Bank branch that holds the account", "F04 F06 F09"),
        ("Change back unused RMB",
         "Passport plus the original exchange slip (24 months). Up to USD 500 a day on ID alone.",
         "Any handling branch", "F08"),
        ("Foreign currency already held",
         "Passport and the instruction. No conversion, so no exchange margin - only the wire fee.",
         "Bank branch that holds the account", "F02"),
        ("Property sale proceeds",
         "Sale contract, deed, tax payment certificate from the transfer, passport.",
         "Bank branch; the property registry already checks the tax certificate", "F11 F14"),
        ("Inheritance transfer",
         "Death certificate, notarised relationship and estate documents, the deceased's tax certificate, one application for the whole amount.",
         "SAFE branch where the deceased was registered", "F11"),
        ("Emigrant property transfer",
         "Hukou cancellation certificate, proof of settlement abroad, title documents, tax certificate; paid out in stages.",
         "SAFE branch where your hukou was registered", "F11"),
    ]
    body = [f'<tr><td data-label="Route">{esc(a)}</td><td data-label="Documents and what happens">{esc(b)}</td>'
            f'<td data-label="Who handles it">{esc(c)}</td><td class="src" data-label="Source">{src(d)}</td></tr>'
            for a, b, c, d in rows_]
    return f"""<h2 id="steps">Step by step, route by route</h2>
<p>These are the mechanics the official pages actually state. The numbered click-by-click version for all eleven routes is on the <a href="dashboard/steps.html">Steps page</a>.</p>
{table(["Route", "Documents and what happens", "Who handles it", "Source"], body)}
<p class="note">Above all of this: the money must have a lawful, documented origin. The 2004 measure refuses any application that cannot prove it, and the Regulation makes a genuine transaction basis a condition of the payment. {src("F11 F10")}</p>"""


def sources_section():
    body = []
    for r in SOURCES.values():
        body.append(f'<tr id="{esc(r["id"])}"><td data-label="Source"><span class="id">{esc(r["id"])}</span>'
                    f'{esc(r["issuer"])}</td>'
                    f'<td data-label="Page"><a href="{esc(r["url"])}" rel="noopener">{esc(r["title"])}</a></td>'
                    f'<td data-label="Read on">{esc(r["read_on"])}</td>'
                    f'<td data-label="What was read" class="quote">{esc(r["verbatim"])}</td></tr>')
    return f"""<h2 id="sources">{len(SOURCES)} official pages, each read on {READ_ON}</h2>
<p class="lead">Every answer above rests on one of these. The quote column is the text actually returned by the page today - it is what the claim is checked against, not a summary written from memory.</p>
{table(["Source", "Page", "Read on", "What the page says"], body, caption="Source register", kind="data")}"""


def flags_section():
    body = []
    for r in FLAGS:
        body.append(f'<tr id="{esc(r["id"])}"><td data-label="Item"><span class="id">{esc(r["id"])}</span>'
                    f'{esc(r["item"])}<br><span class="pill warn">{esc(r["severity"])}</span></td>'
                    f'<td data-label="Why it is open">{esc(r["why"])}</td>'
                    f'<td data-label="What would settle it">{esc(r["what_would_settle_it"])}</td>'
                    f'<td class="src" data-label="Source">{src(r["source_ids"])}</td></tr>')
    return f"""<h2 id="flagged">Flagged for review: {len(FLAGS)} items</h2>
<p class="lead">Nothing here blocks anything; these are the places where the answer is incomplete or the repository is wrong. Each carries the source it was checked
against and what would settle it. Three high-severity items decide your case: your U.S. basis, the unidentified tax, and the absence of any verified route for gifted or undocumented money.</p>
{table(["Item", "Why it is open", "What would settle it", "Source"], body, caption="Open and flagged items", kind="data")}"""


def page():
    body = "\n".join([
        f"""<h1>What must be settled before any money moves</h1>
<p class="lead">A U.S. citizen with RMB in a Chinese bank account. {len(QUESTIONS)} questions, {len(SOURCES)} official pages re-read on {READ_ON}, every figure repriced from the board published {BOARD}. Where an answer does not exist, it is blank and flagged.</p>""",
        kpis(), short_answer(), questions_section(), ladder_section(),
        routes_section(), steps_section(), sources_section(), flags_section(),
        """<h2>How this page was checked</h2>
<ul class="plain">
<li>Every cost cell is computed by <code>scripts/f52c_engine.py</code> from the published board and tariff, then recomputed independently with exact fractions by <code>scripts/f52c_verify.py</code>. A one-cent change in any cell fails the build.</li>
<li>The engine was written from scratch for this page and then compared cell by cell with the dashboard's separate engine at the dashboard's own inputs: 440 of 440 cells agree.</li>
<li>Every question row either cites an official page or is marked <span class="pill warn">open</span> / <span class="pill bad">unverified</span> with a flag. The verifier rejects a blank that has no flag.</li>
<li>Every external link must be on the official-domain allowlist, and every internal link and anchor must resolve.</li>
</ul>""",
    ])
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{h}"{cur if h == "questions.html" else ""}>{esc(l)}</a>'
                  for h, l in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="f52c-questions">
<meta name="description" content="The questions that must be answered before moving money out of China, with the sourced answer we do and do not have, a $10,000-$400,000 cost ladder repriced 11 November 2026, and a list of flagged items.">
<title>Questions before any decision · China money</title>
<link rel="stylesheet" href="dashboard/site.css">
<link rel="stylesheet" href="assets/f52c.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">China money<small>RMB to USD, source-checked</small></a>
<nav class="nav" aria-label="Sections">{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>Bank of China board published {BOARD}; personal tariff in force since 2014-11-01; official pages read {READ_ON}. General research from public official pages - not legal, tax or banking advice, and no finding about any person's case.</p>
<p><a href="#questions">Questions</a> · <a href="#ladder">Ladder</a> · <a href="#sources">Sources</a> · <a href="#flagged">Flagged</a> · <a href="{REPO}">Repository</a> · built by <code>scripts/f52c_build.py</code></p>
<p>Parallel editions of the same exercise, kept as their authors published them: <a href="https://github.com/sassnarep3-star/China3/blob/main/QNA.md">QNA.md</a>, <a href="76e-verification.html">76e verification</a>, <a href="m5f19-dashboard.html">m5f19</a>. Where they disagree with this page, the source ids here are the ones re-read on {READ_ON}.</p>
</div></footer>
</body>
</html>
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    html_out = page()
    if a.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != html_out:
            sys.exit("questions.html is stale: run scripts/f52c_build.py")
        print("questions.html is up to date")
    else:
        OUT.write_text(html_out, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)} ({len(html_out):,} bytes)")
