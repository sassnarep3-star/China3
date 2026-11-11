#!/usr/bin/env python3
"""Build bd1e-decision.html — the decision-readiness page.

    python3 scripts/build_bd1e_site.py            write the page, CSS and CSVs
    python3 scripts/build_bd1e_site.py --check    fail if any generated file is stale

Every figure on the page is computed here from two published inputs:
  * the Bank of China USD board (two dated snapshots), and
  * the Bank of China personal e-banking transfer tariff.
Nothing is typed in by hand; the verifier recomputes the same figures from the
same published inputs and compares them cell by cell.
"""
import argparse
import csv
import html
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "bd1e-decision.html"
CSS = ROOT / "assets" / "bd1e.css"
DATA = ROOT / "data"

# --- published inputs -------------------------------------------------------
# S01 BOC board, RMB per 1 USD. Two dated snapshots, both quoted verbatim in data/bd1e_sources.csv.
BOARDS = {
    "10 Nov": {"bid": D("6.6571"), "ask": D("6.6851"), "pub": "2026/11/10 17:39:58"},
    "11 Nov": {"bid": D("6.6630"), "ask": D("6.6911"), "pub": "2026/11/11 10:25:02"},
}
# S02 BOC personal e-banking cross-border wire tariff.
WIRE_RATE = D("0.001")
WIRE_MIN_CNY = D("50")
WIRE_MAX_CNY = D("260")
CABLE_CNY = D("150")          # non-Hong Kong / Macao / Taiwan
# S12 IIT Law Art. 3(3) and S03 treaty Art. 9(2).
IIT_DIVIDEND = D("0.20")
TREATY_CAP = D("0.10")
# S16 IRS yearly average rates, RMB per USD.
IRS_AVG = {2024: D("7.189"), 2025: D("7.129")}

AMOUNTS = [D(10000) * (i + 1) for i in range(40)]   # $10,000 … $400,000
KEY = [D(10000), D(50000), D(100000), D(200000), D(300000), D(400000)]
TODAY = "11 Nov"
SITE = "10 Nov"
READ_ON = "11 November 2026"

CENT = D("0.01")


def q(x, places=CENT):
    return x.quantize(places, rounding=ROUND_HALF_UP)


def mid(b):
    return (b["bid"] + b["ask"]) / 2


def spread(usd, b):
    """Cost of crossing the bank's spread: the gap between the selling rate and the midpoint
    of the bank's own buying and selling rates, charged on the amount converted."""
    return usd * (b["ask"] - mid(b)) / b["ask"]


def wire_cny(usd, b):
    pct = usd * b["ask"] * WIRE_RATE
    return min(WIRE_MAX_CNY, max(WIRE_MIN_CNY, pct)) + CABLE_CNY


def wire_usd(usd, b):
    return wire_cny(usd, b) / b["ask"]


def l01(usd, b):
    """Convert RMB to USD and wire it out in one wire."""
    s, w = spread(usd, b), wire_usd(usd, b)
    return {"spread": s, "fee": w, "total": s + w, "cny": usd * b["ask"] + wire_cny(usd, b)}


def l03(usd, b):
    """Wire out foreign currency already held in the account: wire fee only."""
    w = wire_usd(usd, b)
    return {"spread": D(0), "fee": w, "total": w, "cny": wire_cny(usd, b)}


def dividend(usd, b, rate):
    tax = usd * rate
    net = usd - tax
    s, w = spread(net, b), wire_usd(net, b)
    return {"tax": tax, "cost_after": s + w, "total": tax + s + w, "net": net}


def fx_gain(usd, b, year):
    return usd - usd * b["ask"] / IRS_AVG[year]


def usd(x):
    return f"${q(x):,.2f}"


def cny(x):
    return f"RMB {q(x):,.2f}"


def pct(x, places=4):
    return f"{q(x * 100, D(1).scaleb(-places))}%"


# --- data -------------------------------------------------------------------
def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


SOURCES = {r["id"]: r for r in read_csv("bd1e_sources.csv")}
QUESTIONS = read_csv("bd1e_questions.csv")
CLOSED = read_csv("bd1e_closed.csv")
FINDINGS = read_csv("bd1e_findings.csv")

SHORT = {
    "BD-S01": "BOC board", "BD-S02": "BOC tariff", "BD-S03": "IRS treaty", "BD-S04": "STA 2019/35",
    "BD-S05": "31 USC 5321", "BD-S06": "31 CFR 1010.821", "BD-S07": "SAFE Hebei", "BD-S08": "SAFE Tianjin",
    "BD-S09": "SAFE Tianjin", "BD-S10": "SAFE Ningxia", "BD-S11": "SAFE Tianjin", "BD-S12": "IIT Law",
    "BD-S13": "STA/SAFE 2013/40", "BD-S14": "FinCEN", "BD-S15": "IRS 8938", "BD-S16": "IRS rates",
    "BD-S17": "SAFE Hebei", "BD-S18": "CBP",
}

esc = html.escape


def src_links(ids):
    out = []
    for i in ids.split():
        s = SOURCES[i]
        out.append(
            f'<a href="{esc(s["url"])}" rel="noopener" title="{esc(s["title"])}">{i} {esc(SHORT[i])}</a>'
        )
    return " ".join(out)


def table(headers, rows, cls="", widths=None):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join(
            f'<td data-label="{esc(headers[i])}">{c}</td>' for i, c in enumerate(r)) + "</tr>")
    col = ""
    if widths:
        col = "<colgroup>" + "".join(f'<col style="width:{w}">' for w in widths) + "</colgroup>"
    return (f'<div class="scroll"><table class="{cls}">{col}<thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


CSS_TEXT = """/* bd1e — decision page. Mobile first. */
:root{
  --bg:#f6f7f9; --card:#fff; --ink:#17202a; --muted:#59636f; --line:#dde3ea;
  --accent:#0b5cab; --accent-soft:#e8f1fa; --warn:#8a4b00; --warn-soft:#fff4e2;
  --ok:#0b6b3a; --ok-soft:#e7f6ee; --radius:14px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif}
a{color:var(--accent)}
a:hover{text-decoration:none}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px}
header.site{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
header.site .wrap{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;padding:10px 16px}
.brand{font-weight:700;text-decoration:none;color:var(--ink);line-height:1.15}
.brand small{display:block;font-weight:400;color:var(--muted);font-size:12px}
nav.nav{display:flex;flex-wrap:wrap;gap:4px}
nav.nav a{font-size:13px;padding:5px 9px;border-radius:999px;text-decoration:none;color:var(--muted)}
nav.nav a[aria-current=page]{background:var(--accent-soft);color:var(--accent);font-weight:600}
nav.nav a:hover{background:#eef1f5;color:var(--ink)}
main{padding:20px 0 48px}
h1{font-size:clamp(26px,5vw,38px);line-height:1.15;margin:8px 0 10px}
h2{font-size:clamp(20px,3.4vw,26px);line-height:1.2;margin:36px 0 8px;scroll-margin-top:70px}
h3{font-size:17px;margin:18px 0 6px}
p{margin:0 0 12px}
.lead{font-size:17px;color:var(--muted);max-width:70ch}
.eyebrow{text-transform:uppercase;letter-spacing:.08em;font-size:12px;color:var(--accent);font-weight:700;margin:0}
.kpis{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:18px 0 6px}
@media(min-width:720px){.kpis{grid-template-columns:repeat(4,1fr)}}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px}
.kpi b{display:block;font-size:22px;line-height:1.15}
.kpi span{display:block;font-size:12.5px;color:var(--muted);margin-top:4px}
.kpi .src{font-size:11.5px;margin-top:6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px;margin:12px 0}
.card.warn{background:var(--warn-soft);border-color:#f0d8b4}
.card.ok{background:var(--ok-soft);border-color:#c7e6d5}
.grid3{display:grid;gap:12px}
@media(min-width:800px){.grid3{grid-template-columns:repeat(3,1fr)}}
.grid3 .card{margin:0}
.tag{display:inline-block;font-size:11.5px;font-weight:700;padding:2px 8px;border-radius:999px;
  background:#eef1f5;color:var(--muted);white-space:nowrap}
.tag.high{background:#fde8e6;color:#9d1f14}
.tag.med{background:var(--warn-soft);color:var(--warn)}
.tag.low{background:#eef1f5;color:#43505e}
.tag.ok{background:var(--ok-soft);color:var(--ok)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;background:var(--card);border:1px solid var(--line);
  border-radius:var(--radius);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:14px}
thead th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);
  padding:10px 12px;border-bottom:1px solid var(--line);background:#fbfcfd;white-space:nowrap}
tbody td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:last-child td{border-bottom:0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.src{font-size:12px;white-space:nowrap}
td.src a{display:inline-block;margin-right:6px;text-decoration:none}
tr.total td{font-weight:700;background:#fbfcfd}
.blank{color:var(--warn);font-weight:600}
.note{font-size:13.5px;color:var(--muted)}
.toc{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:12px 16px;margin:14px 0}
.toc b{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.toc ol{margin:8px 0 0;padding-left:20px;font-size:14px}
.toc li{margin:2px 0}
ol.steps{padding-left:20px;margin:8px 0}
ol.steps li{margin:6px 0}
blockquote{margin:8px 0;padding:10px 14px;border-left:3px solid var(--accent);background:#fbfcfd;
  font-size:14px;color:#2b3540;border-radius:0 8px 8px 0}
blockquote.zh{font-size:14.5px}
footer.site{border-top:1px solid var(--line);background:#fff;padding:20px 0;margin-top:20px}
footer.site p{font-size:13px;color:var(--muted)}
@media(max-width:640px){
  table.stack thead{display:none}
  table.stack,table.stack tbody,table.stack tr,table.stack td{display:block;width:100%}
  table.stack tr{border-bottom:2px solid var(--line);padding:4px 0}
  table.stack td{border:0;padding:6px 12px;display:grid;grid-template-columns:40% 1fr;gap:10px;text-align:left}
  table.stack td::before{content:attr(data-label);font-size:11px;text-transform:uppercase;
    letter-spacing:.05em;color:var(--muted);font-weight:700;padding-top:2px}
  table.stack td.num{text-align:left}
  .scroll{border-radius:var(--radius)}
}
"""


# --- page -------------------------------------------------------------------
def page():
    b_today, b_site = BOARDS[TODAY], BOARDS[SITE]
    l01_10k = l01(D(10000), b_today)
    l01_400k = l01(D(400000), b_today)
    div20_400k = dividend(D(400000), b_today, IIT_DIVIDEND)
    div10_400k = dividend(D(400000), b_today, TREATY_CAP)
    saved = div20_400k["total"] - div10_400k["total"]

    out = []
    A = out.append
    A('<!doctype html><html lang="en"><head><meta charset="utf-8">')
    A('<meta name="viewport" content="width=device-width,initial-scale=1">')
    A('<title>Before you decide · China money</title>')
    A('<meta name="description" content="The questions that must be answered before moving RMB out of China, '
      'what the official sources settle, what is still open, and what the transfer costs at today\'s Bank of China board.">')
    A('<link rel="stylesheet" href="assets/bd1e.css">')
    A('</head><body>')
    A('<header class="site"><div class="wrap">')
    A('<a class="brand" href="index.html">China money<small>RMB to USD, source-checked</small></a>')
    A('<nav class="nav" aria-label="Sections">'
      '<a href="index.html">Home</a>'
      '<a href="dashboard/methods.html">Methods</a>'
      '<a href="dashboard/costs.html">Costs</a>'
      '<a href="dashboard/steps.html">Steps</a>'
      '<a href="dashboard/tax.html">Tax</a>'
      '<a href="dashboard/flagged.html">Flagged</a>'
      '<a href="dashboard/sources.html">Sources</a>'
      '<a href="dashboard/archive.html">Archive</a>'
      '<a href="bd1e-decision.html" aria-current="page">Before you decide</a></nav>')
    A('</div></header><main><div class="wrap">')

    A('<p class="eyebrow">Decision readiness · read on ' + READ_ON + '</p>')
    A('<h1>Before you decide</h1>')
    A('<p class="lead">A U.S. citizen has RMB in a Chinese bank account and has been told that turning it into '
      'dollars means "a considerable amount of taxes". The repo already carries a 36-question register on '
      '<a href="dashboard/decisions.html">Decide</a> and a long-form Q&amp;A in <a href="QNA.md">QNA.md</a>. This page '
      'does not repeat them: it is the short path through the questions that actually change the answer, and it adds '
      '<b>three open items that were closed today</b> — items the register still marks unread — with the money each '
      'one moves, plus the cost ladder recomputed at today\'s board. Every figure and every statement here carries a '
      'link to the official page it was read from on ' + READ_ON + '.</p>')

    A('<div class="kpis">')
    A(f'<div class="kpi"><b>{usd(l01_10k["total"])}</b><span>Bank cost to convert and wire $10,000 at today\'s board</span>'
      f'<span class="src">{src_links("BD-S01 BD-S02")}</span></div>')
    A(f'<div class="kpi"><b>{usd(l01_400k["total"])}</b><span>Same route for $400,000 in one wire</span>'
      f'<span class="src">{src_links("BD-S01 BD-S02")}</span></div>')
    A(f'<div class="kpi"><b>{usd(saved)}</b><span>Chinese dividend tax saved by the treaty cap at $400,000</span>'
      f'<span class="src">{src_links("BD-S03 BD-S04")}</span></div>')
    A(f'<div class="kpi"><b>3</b><span>Open items closed today (U06, U12, U16)</span>'
      f'<span class="src">{src_links("BD-S03 BD-S05 BD-S07")}</span></div>')
    A('</div>')

    A('<div class="card ok"><p style="margin:0"><b>What the sources actually say.</b> No official page read for this '
      'project puts a tax on the conversion or on the wire. The Chinese tax that matters is tax on the income behind '
      'the money, owed whether or not it moves '
      f'({src_links("BD-S12")}). The bank is required to see the tax evidence before it sells the dollars '
      f'({src_links("BD-S08")}). On the U.S. side the risks are the currency gain on the RMB '
      f'({src_links("BD-S16")}) and the reporting forms, whose penalties are larger than the bank\'s fee '
      f'({src_links("BD-S05 BD-S06")}).</p></div>')

    A('<div class="toc"><b>On this page</b><ol>'
      '<li><a href="#questions">The 12 questions, in the order they decide things</a></li>'
      '<li><a href="#costs">What the transfer costs at today\'s board</a></li>'
      '<li><a href="#ladder">Every $10,000 step to $400,000</a></li>'
      '<li><a href="#closed">Three open items closed today</a></li>'
      '<li><a href="#treaty">The dividend route and the treaty cap</a></li>'
      '<li><a href="#open">What is still open</a></li>'
      '<li><a href="#findings">Findings for review</a></li>'
      '<li><a href="#sources">Sources read for this page</a></li>'
      '</ol></div>')

    # ---------------- questions
    A('<h2 id="questions">1. The 12 questions, in the order they decide things</h2>')
    A('<p class="lead">Each question changes which route is lawful or what it costs. "Open" means no public source '
      'can answer it — it depends on your documents. The last column says what the answer unlocks. The full register, '
      'with 36 questions and the discovery plan for each, is on <a href="dashboard/decisions.html">Decide</a>; these '
      'twelve are the ones that move the route or the number.</p>')
    rows = []
    for r in QUESTIONS:
        kind = {"open": "high", "answered": "ok", "part": "med"}.get(
            r["status_kind"].split("—")[0].strip().lower(), "")
        rows.append([
            f'<b>{esc(r["id"])}</b> {esc(r["question"])}',
            esc(r["why_it_decides"]),
            f'<span class="tag {kind}">{esc(r["status"])}</span>',
            esc(r["how_to_get_it"]),
            esc(r["unlocks"]) + '<br>' + src_links(r["source_ids"]),
        ])
    A(table(["Question", "Why it decides the answer", "Status", "How to get the answer", "Unlocks · source"],
            rows, cls="stack", widths=["19%", "26%", "11%", "24%", "20%"]))
    A('<p class="note">Questions Q01, Q02 and Q05 are the three that can change the answer by tens of thousands of '
      'dollars. Q09 to Q11 are the U.S. reporting tests that carry penalties larger than any bank fee here.</p>')

    # ---------------- costs
    A('<h2 id="costs">2. What the transfer costs at today\'s board</h2>')
    A(f'<p>Two routes only, because they are the only two whose costs are published in full: <b>L03</b> wires out '
      f'foreign currency already in the account (wire fee only) and <b>L01</b> buys dollars with documented RMB '
      f'income and wires them (spread plus wire fee). Both are computed with the Bank of China board published '
      f'{b_today["pub"]} (buying {b_today["bid"]}, selling {b_today["ask"]}) and its personal e-banking tariff: '
      f'0.1% of the amount, minimum RMB 50, maximum RMB 260, plus RMB 150 cable for a non-Hong Kong/Macao/Taiwan '
      f'wire ({src_links("BD-S01 BD-S02")}). Intermediary and receiving-bank fees are published nowhere and are '
      f'<span class="blank">not included</span> (site flag U04).</p>')
    rows = []
    for amt in KEY:
        a, b = l01(amt, b_today), l03(amt, b_today)
        rows.append([
            usd(amt), usd(b["total"]), usd(a["total"]), pct(a["total"] / amt, 3),
            cny(a["cny"]), src_links("BD-S01 BD-S02"),
        ])
    A(table(["Amount", "L03 wire only", "L01 convert + wire", "Cost as % of amount", "RMB debited (L01)", "Source"],
            rows, cls="stack", widths=["12%", "15%", "17%", "15%", "24%", "17%"]))
    A('<p class="note">The spread is the gap between the bank\'s selling rate and the midpoint of its own buying '
      'and selling rates, charged on the amount converted. It is larger than the wire fee above about $20,000. '
      'The wire fee stops growing at RMB 260 once the transfer passes roughly USD 38,900, which is why the total '
      'cost falls as a percentage of the amount.</p>')

    # ---------------- drift
    A('<h3>The published tables use an older board. Here is the difference.</h3>')
    A('<p>The site\'s cost tables were built on the 10 November board and were not repriced '
      f'(<a href="dashboard/flagged.html#U15">flag U15</a>). The table below applies the identical formula to both '
      'dated boards so the drift is visible. It is a check, not a new headline: the published ladder stays at '
      f'<a href="dashboard/costs.html">Costs</a>.</p>')
    rows = []
    for amt in KEY:
        a_site, a_now = l01(amt, b_site), l01(amt, b_today)
        rows.append([
            usd(amt), usd(a_site["total"]), usd(a_now["total"]), usd(a_now["total"] - a_site["total"]),
            usd(l03(amt, b_site)["total"]), usd(l03(amt, b_today)["total"]),
            src_links("BD-S01"),
        ])
    A(table(["Amount", "L01 at 10 Nov board", "L01 at 11 Nov board", "Change",
             "L03 at 10 Nov", "L03 at 11 Nov", "Source"],
            rows, cls="stack", widths=["12%", "16%", "16%", "11%", "14%", "14%", "17%"]))
    A(f'<p class="note">Both boards are quoted verbatim in the source table below. A one-day move of this size '
      f'(${q(b_today["ask"] - b_site["ask"]):.4f} per dollar) changes the $400,000 total by '
      f'{usd(l01(D(400000), b_today)["total"] - l01(D(400000), b_site)["total"])}. The ranking of routes does not '
      f'change, and no rate on this page is a forecast.</p>')

    # ---------------- ladder
    A('<h2 id="ladder">3. Every $10,000 step, $10,000 to $400,000, at today\'s board</h2>')
    A('<p>The same two routes at every increment. The last column is the U.S. currency gain if the RMB had been '
      f'acquired at the 2024 IRS yearly average rate of {IRS_AVG[2024]} '
      f'({src_links("BD-S16")}) — it is income, not a tax, and the personal-transaction rule may exclude small '
      f'amounts (<a href="dashboard/flagged.html#U05">U05</a>).</p>')
    rows = []
    for amt in AMOUNTS:
        a, b = l01(amt, b_today), l03(amt, b_today)
        rows.append([
            usd(amt), usd(b["total"]), usd(a["total"]), pct(a["total"] / amt, 3),
            usd(fx_gain(amt, b_today, 2024)), src_links("BD-S01 BD-S02 BD-S16"),
        ])
    A(table(["Amount", "L03 wire only", "L01 convert + wire", "Cost %", "U.S. gain if acquired 2024", "Source"],
            rows, cls="stack", widths=["13%", "15%", "17%", "11%", "27%", "17%"]))
    A('<p class="note">Dividend, cash, ATM, cross-border RMB, inheritance and property routes are priced on '
      '<a href="dashboard/costs.html">Costs</a>. They are not repeated here: several depend on documents and '
      'personal facts that are still open (Q01, Q08), and this page does not publish a competing total.</p>')

    # ---------------- closed
    A('<h2 id="closed">4. Three open items closed today</h2>')
    A('<p class="lead">These were listed on the site as unread or unverified. Each was read in the official text '
      'today. Where the closure changes a number, the change is shown.</p>')
    rows = []
    for c in CLOSED:
        rows.append([
            f'<b>{esc(c["id"])}</b> {esc(c["item"])}',
            esc(c["was"]),
            esc(c["now"]),
            esc(c["effect"]) + '<br>' + src_links(c["source_ids"]),
        ])
    A(table(["Item", "What the site said", "What the official text says", "What changes"],
            rows, cls="stack", widths=["16%", "24%", "32%", "28%"]))

    A('<h3>U06 in the treaty\'s own words</h3>')
    A('<blockquote>“However, such dividends may also be taxed in the Contracting State of which the company paying '
      'the dividends is a resident, and according to the laws of that Contracting State, but if the recipient is '
      'the beneficial owner of the dividends the tax so charged shall not exceed 10 percent of the gross amount of '
      'the dividends.” — Article 9(2), U.S.–China income tax treaty ' + src_links("BD-S03") + '</blockquote>')
    A('<h3>U12 in the statute\'s own words</h3>')
    A('<blockquote>“(C) Willful violations … (i) the maximum penalty under subparagraph (B)(i) shall be increased '
      'to the greater of— (I) $100,000, or (II) 50 percent of the amount determined under subparagraph (D) … (D) … '
      'the balance in the account at the time of the violation.” — 31 U.S.C. § 5321(a)(5) '
      + src_links("BD-S05") + '</blockquote>')
    A('<h3>U16 in the 2024 guidelines as reproduced by SAFE</h3>')
    A('<blockquote>“六、资本项下个人外汇业务管理 6.4 对外财产转移购付汇核准 6.4.3.1 移民财产转移 (1) 书面申请，并附'
      '《个人财产转移业务申请表》… (4) 主管税务部门出具的税务证明原件…” — 汇发〔2024〕12号 § 6.4.3.1, reproduced in '
      'SAFE Hebei\'s service guide, which also records a 20-working-day limit, no fee, and an approval valid 当次 '
      + src_links("BD-S07") + '</blockquote>')

    # ---------------- treaty
    A('<h2 id="treaty">5. The dividend route and the treaty cap</h2>')
    A('<p>This is the only place where the treaty changes a number on this site. Domestic law taxes dividends at a '
      f'flat 20% ({src_links("BD-S12")}); the treaty caps Chinese tax at 10% of the gross amount for a beneficial '
      f'owner who is a U.S. resident ({src_links("BD-S03")}). The relief is not automatic: it is self-assessed under '
      f'SAT Announcement 2019 No. 35 — the information report form goes to the withholding agent, with a U.S. '
      f'residency certificate and beneficial-owner evidence kept on file. Without the form, the payer withholds '
      f'under domestic law ({src_links("BD-S04")}).</p>')
    rows = []
    for amt in KEY:
        d20, d10 = dividend(amt, b_today, IIT_DIVIDEND), dividend(amt, b_today, TREATY_CAP)
        rows.append([
            usd(amt), usd(d20["tax"]), usd(d10["tax"]), usd(d20["tax"] - d10["tax"]),
            usd(d10["total"]), src_links("BD-S03 BD-S04 BD-S12"),
        ])
    A(table(["Dividend amount", "Chinese tax at 20% (domestic)", "Chinese tax at 10% (treaty)",
             "Difference", "Transfer cost after 10% tax", "Source"],
            rows, cls="stack", widths=["14%", "20%", "18%", "13%", "18%", "17%"]))
    A('<p class="note">Chinese tax only. The U.S. tax on the same dividend, and the foreign tax credit that may '
      'offset it, are not modelled here; this table is not a statement about your combined burden '
      '(<a href="#findings">BD-F01</a>). The 10% cap is also not available to a person who is a Chinese resident '
      'under the treaty tie-breaker (Q05).</p>')
    A('<h3>How the relief is actually claimed</h3><ol class="steps">'
      '<li>Obtain a certificate of U.S. residency for the year from the IRS — the document the announcement '
      f'requires ({src_links("BD-S04")}, Art. 7(1)).</li>'
      '<li>Complete the 《非居民纳税人享受协定待遇信息报告表》 and give it to the company or bank that pays the '
      'dividend, before it withholds. If you do not, it withholds 20%.</li>'
      '<li>Keep the ownership documents and the beneficial-owner evidence on file for the statutory retention '
      'period; the tax office can demand them later.</li>'
      '<li>If relief is later found not to have been due, declare and pay the shortfall yourself. Improper use '
      'creates a compliance record and late-payment liability.</li></ol>')

    # ---------------- open
    A('<h2 id="open">6. What is still open</h2>')
    A('<p class="lead">These are unchanged and still block a definite answer. They are listed with the question '
      'that would settle each one on the <a href="dashboard/flagged.html">Flagged for review</a> page.</p>')
    none_marker = '<span class="blank">no official page read today</span>'
    open_items = [
        ("U01", "high", "Where the money came from",
         "Decides the route. Nothing else can be recommended until it is known.", "BD-S08"),
        ("U02", "high", "What the “considerable taxes” actually are",
         "No tax, rate, amount or office was named. No official page read today imposes a tax on the conversion itself.", "BD-S08"),
        ("U05", "med", "Whether the currency gain is a personal transaction",
         "A legal judgement under § 988(e); the USD 200 exclusion may or may not apply.", ""),
        ("U07", "high", "Gifts, or money with no documents",
         "No official rule was found that lets a foreign passport holder convert it. The rule read today requires documented income.", "BD-S08"),
        ("U09", "med", "What the cross-border RMB route (L08) costs",
         "Neither the outbound fee nor the offshore conversion rate is published.", ""),
        ("U13", "med", "The ATM route's exchange rate and foreign-ATM fee",
         "Only the Chinese card fee is published; the UnionPay rate and the foreign ATM's fee are not.", ""),
        ("U17", "low", "Property taxes beyond income tax (VAT, deed tax, land appreciation tax)",
         "Not verified. The tax certificate required on a sale is a separate matter from the property taxes themselves.", ""),
        ("U18", "med", "Whether any transfer company or app can send a personal RMB balance abroad",
         "No official page read confirms one; the rule read today allows only banks to do the conversion for a foreign individual.", "BD-S08"),
        ("U19", "low", "Ten routes catalogued by earlier passes not re-read today",
         "They carry no verdict and no cost on this page.", ""),
    ]
    rows = []
    for i, s, t, w, sid in open_items:
        rows.append([
            f'<a href="dashboard/flagged.html#{i}">{i}</a>',
            f'<span class="tag {"high" if s == "high" else ("med" if s == "med" else "low")}">{s}</span>',
            esc(t), esc(w),
            src_links(sid) if sid else none_marker,
        ])
    A(table(["Item", "Severity", "Unverified point", "Why it still blocks a decision", "Source read today"],
            rows, cls="stack", widths=["8%", "9%", "29%", "33%", "21%"]))
    A('<p class="note">Where the last column says no official page was read today, the item is not restated from an '
      'earlier pass: it stays blank and is carried on <a href="dashboard/flagged.html">Flagged for review</a>, which '
      'holds the full list of 19. U06, U12 and U16 are closed in section 4; U15 is quantified in section 2.</p>')

    # ---------------- findings
    A('<h2 id="findings">7. Findings for review</h2>')
    A('<p class="lead">Problems found in the repository while closing the items above. None of them blocks '
      'publication; all are published for review with their official sources.</p>')
    rows = []
    for f in FINDINGS:
        sev = {"medium": "med"}.get(f["severity"], f["severity"])
        rows.append([
            f'<b>{esc(f["id"])}</b>',
            f'<span class="tag {sev}">{esc(f["severity"])}</span>',
            esc(f["finding"]), esc(f["evidence"]) + '<br>' + src_links(f["source_ids"]),
            esc(f["status"]),
        ])
    A(table(["ID", "Severity", "Finding", "Evidence", "Status"], rows, cls="stack",
            widths=["7%", "9%", "33%", "41%", "10%"]))
    A('<p class="note">BD-F01 and BD-F02 are corrections that belong on the shared Tax page, which this session '
      'does not own. The request is logged on the coordination board as BD1E-REQ-02.</p>')

    # ---------------- sources
    A('<h2 id="sources">8. Sources read for this page</h2>')
    A('<p class="lead">Every row was opened on ' + READ_ON + ' and the quoted sentence was read on the page itself. '
      'Where a page is quoted only in part, the quoted part is what was read.</p>')
    rows = []
    for sid, s in SOURCES.items():
        rows.append([
            f'<b>{esc(sid)}</b>', esc(s["issuer"]),
            f'<a href="{esc(s["url"])}" rel="noopener">{esc(s["title"])}</a>',
            f'<span class="note">{esc(s["quote"])}</span>', esc(s["read_on"]),
        ])
    A(table(["ID", "Issuer", "Page", "What it says (verbatim)", "Read on"], rows, cls="stack",
            widths=["7%", "13%", "25%", "45%", "10%"]))
    A('<p class="note">Two of these were read through the publisher\'s own service guide rather than the instrument '
      'itself: U16 (SAFE Hebei reproduces § 6.4.3.1 of the 2024 guidelines) and the treaty (the IRS PDF of the '
      'signed agreement). Both are official publications of the issuing government.</p>')

    A('</div></main>')
    A('<footer class="site"><div class="wrap">')
    A('<p><b>Method.</b> Figures are recomputed from two published inputs — the Bank of China USD board and its '
      'personal e-banking tariff — by <code>scripts/build_bd1e_site.py</code> and re-derived independently by '
      '<code>scripts/verify_bd1e.py</code>. Undated or unpublished values are left blank, never estimated.</p>')
    A('<p><b>Scope.</b> Research from public official pages, read on ' + READ_ON + '. It is not legal, tax or '
      'banking advice and makes no finding about any person\'s case. Rates move daily; the ones shown are dated.</p>')
    A('<p><a href="index.html">Home</a> · <a href="dashboard/flagged.html">Open items</a> · '
      '<a href="dashboard/sources.html">All sources</a> · <a href="dashboard/decisions.html">Decide register</a> · '
      '<a href="QNA.md">Q&amp;A register</a> · '
      '<a href="REPO_AUDIT.md">Repository audit</a> · '
      '<a href="https://github.com/sassnarep3-star/China3">Repository</a></p>')
    A('</div></footer></body></html>')
    return "\n".join(out)


# --- CSVs -------------------------------------------------------------------
def csv_outputs():
    b_today, b_site = BOARDS[TODAY], BOARDS[SITE]
    ladder = ["method_id,amount_usd,board_pub_time,bid,ask,spread_usd,fee_usd,cny_fee,total_usd,total_pct,rmb_debited,fx_gain_2024,fx_gain_2025,source_ids"]
    for amt in AMOUNTS:
        for mid_, fn in (("L01", l01), ("L03", l03)):
            r = fn(amt, b_today)
            ladder.append(",".join(str(v) for v in [
                mid_, int(amt), b_today["pub"], b_today["bid"], b_today["ask"],
                q(r["spread"]), q(r["fee"]), q(wire_cny(amt, b_today)),
                q(r["total"]), q(r["total"] / amt * 100, D("0.001")), q(r["cny"]),
                q(fx_gain(amt, b_today, 2024)), q(fx_gain(amt, b_today, 2025)),
                "BD-S01|BD-S02|BD-S16"]))
    drift = ["amount_usd,l01_10nov,l01_11nov,l01_change,l03_10nov,l03_11nov,dividend_tax_20pct,dividend_tax_10pct,dividend_saving"]
    for amt in AMOUNTS:
        a_site, a_now = l01(amt, b_site), l01(amt, b_today)
        d20, d10 = dividend(amt, b_today, IIT_DIVIDEND), dividend(amt, b_today, TREATY_CAP)
        drift.append(",".join(str(v) for v in [
            int(amt), q(a_site["total"]), q(a_now["total"]), q(a_now["total"] - a_site["total"]),
            q(l03(amt, b_site)["total"]), q(l03(amt, b_today)["total"]),
            q(d20["tax"]), q(d10["tax"]), q(d20["tax"] - d10["tax"])]))
    return {"bd1e_ladder.csv": "\n".join(ladder) + "\n", "bd1e_drift.csv": "\n".join(drift) + "\n"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if a generated file is stale")
    args = ap.parse_args()
    targets = {PAGE: page(), CSS: CSS_TEXT}
    for name, text in csv_outputs().items():
        targets[DATA / name] = text
    stale = []
    for path, text in targets.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(path.relative_to(ROOT))
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check:
        if stale:
            print("STALE: " + ", ".join(str(s) for s in stale))
            return 1
        print(f"OK — {len(targets)} generated files are byte-identical")
        return 0
    print(f"wrote {len(targets)} files, {len(stale)} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
