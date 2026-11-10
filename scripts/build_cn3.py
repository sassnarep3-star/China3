#!/usr/bin/env python3
"""Generate the consolidated CNY->USD dashboard: CSVs + HTML, from cn3_data.py.

Every money figure is recomputed here from the sourced inputs.  If a component is not
published it stays empty in the CSV and renders as a flagged blank, never as zero.
"""
from __future__ import annotations

import csv
import html
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cn3_data as D  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AMOUNTS = list(range(10_000, 400_001, 10_000))

# --- inputs ---------------------------------------------------------------------------------
I = {row["id"]: row["value"] for row in D.INPUTS}
ASK = I["C3-I01"]                 # 6.6903
BID = I["C3-I02"]
MID = I["C3-I03"]
SPREAD = I["C3-I04"]              # 0.210479 %
WIRE_RATE = I["C3-I05"]
WIRE_MIN = I["C3-I06"]
WIRE_MAX = I["C3-I07"]
CABLE = I["C3-I08"]
ATM_CNY_FIXED = 12.0
ATM_CNY_PCT = 0.01
ATM_CNY_CAP = 112.0
ATM_DAILY_CNY = I["C3-I12"]
ATM_ANNUAL_CNY = I["C3-I13"]
CONV = I["C3-I14"]
CASH_TRIP = I["C3-I16"]
RATE_2024 = I["C3-I29"]
RATE_2025 = I["C3-I30"]
TAX_RATE = I["C3-I31"]            # assumption, 24 %
PROHIBITED_FINE = 1.00            # statutory maximum (100 % of amount), C3-S07 arts 39/40/45

SRC = {row["id"]: row for row in D.SOURCES}
METHODS = {row["id"]: row for row in D.METHODS}


def money(x) -> str:
    if x is None or x == "":
        return ""
    return f"{float(x):,.2f}"


def r2(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def pct(x) -> str:
    if x is None:
        return ""
    return f"{x*100:.3f}%"


def wire_fee_cny(cny_amount: float) -> float:
    return min(max(WIRE_RATE * cny_amount, WIRE_MIN), WIRE_MAX)


def us_gain(amount: float, basis_rate: float) -> float:
    """IRC 988 gain on disposing of CNY acquired at `basis_rate` (CNY per USD)."""
    gain = amount * (1 - ASK / basis_rate)
    return max(gain, 0.0)


def compute(mid: str, amount: int) -> dict:
    m = METHODS[mid]
    f = m["formula"]
    cny = amount * ASK
    row = dict(
        method_id=mid, amount_usd=amount, cny_at_ask=r2(cny),
        spread_usd="", wire_fee_usd="", cable_usd="",
        transfers="", years="", known_cost_usd="", cost_pct="",
        net_usd="", us_gain_2024="", us_tax_2024="", route_tax_usd="",
        all_in_usd="", status="", note="", source_id="",
        source_url="",
    )
    src = m["sources"][0]
    row["source_id"] = src
    row["source_url"] = SRC[src]["url"]

    if f in ("wire", "wire_quota", "wire_nofx", "wire_dividend"):
        spread = 0.0 if f == "wire_nofx" else amount * SPREAD
        n = max(1, math.ceil(amount / CONV)) if f == "wire_quota" else 1
        per_cny = cny / n
        fee_usd = n * (wire_fee_cny(per_cny) + CABLE) / ASK
        known = spread + fee_usd
        row.update(
            spread_usd=r2(spread), wire_fee_usd=r2(n * wire_fee_cny(per_cny) / ASK),
            cable_usd=r2(n * CABLE / ASK), transfers=n, years=n,
            known_cost_usd=r2(known), cost_pct=pct(known / amount),
            net_usd=r2(amount - known), status="calculated",
            note=("No CNY conversion spread: the balance is already in USD." if f == "wire_nofx"
                  else ("Eight calendar years at USD 50,000 a year." if n > 1 else "")),
        )
        if f == "wire_dividend":
            row["route_tax_usd"] = r2(amount * I["C3-I19"])
            row["note"] = "PRC dividend IIT at 20% of the dividend, before any treaty relief (flagged)."

    elif f in ("atm_unionpay", "atm_visa"):
        n = math.ceil(cny / ATM_DAILY_CNY)
        if f == "atm_unionpay":
            per = min(ATM_CNY_CAP, ATM_CNY_FIXED + ATM_CNY_PCT * ATM_DAILY_CNY)
            fee_usd = n * per / ASK
        else:
            cash_per = ATM_DAILY_CNY / ASK
            per = min(max(0.025 * cash_per, 3.0), 40.0)
            fee_usd = n * per
        years = math.ceil(cny / ATM_ANNUAL_CNY)
        known = fee_usd
        row.update(
            wire_fee_usd=r2(fee_usd), transfers=n, years=years,
            known_cost_usd=r2(known), cost_pct=pct(known / amount),
            net_usd=r2(amount - known), status="partial",
            note=f"{n} withdrawals at the RMB 10,000 daily ceiling; card-network spread not published.",
        )

    elif f == "cash":
        n = math.ceil(amount / CASH_TRIP)
        known = amount * SPREAD
        row.update(
            spread_usd=r2(known), transfers=n, years=n,
            known_cost_usd=r2(known), cost_pct=pct(known / amount),
            net_usd=r2(amount - known), status="partial",
            note=f"{n} trip(s) at the USD 10,000 permit ceiling; travel and risk not priced.",
        )

    elif f == "prohibited":
        row.update(status="prohibited", note=f"Statutory fine exposure up to {int(PROHIBITED_FINE*100)}% of the amount; funds may also be confiscated.")

    elif f == "none":
        row.update(status="no_conversion", known_cost_usd=r2(0), cost_pct="0.000%",
                   net_usd=r2(0), transfers=0, note="Delivers no USD.")

    elif f == "unverified":
        row.update(status="unverified", note="No official price for this route; left blank.")

    # U.S. §988 gain, on routes that dispose of CNY
    if f not in ("wire_nofx", "none", "unverified", "prohibited"):
        g = us_gain(amount, RATE_2024)
        row["us_gain_2024"] = r2(g)
        row["us_tax_2024"] = r2(g * TAX_RATE)
    if row["known_cost_usd"] != "":
        row["all_in_usd"] = r2(float(row["known_cost_usd"])
                               + (float(row["us_tax_2024"]) if row["us_tax_2024"] != "" else 0.0)
                               + (float(row["route_tax_usd"]) if row["route_tax_usd"] != "" else 0.0))
    return row


def build_ladder():
    rows = []
    for mid, m in METHODS.items():
        for amount in AMOUNTS:
            rows.append(compute(mid, amount))
    return rows


# ---------------------------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------------------------
def write_csv(path: Path, fields: list[str], rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_data(ladder):
    DATA.mkdir(exist_ok=True)
    write_csv(DATA / "cn3_sources.csv",
              ["id", "short", "title", "issuer", "url", "status", "excerpt", "supports"],
              D.SOURCES)
    write_csv(DATA / "cn3_inputs.csv",
              ["id", "name", "value", "unit", "source", "status", "note"],
              [dict(r, value="" if r["value"] is None else r["value"]) for r in D.INPUTS])
    write_csv(DATA / "cn3_methods.csv",
              ["id", "rank", "family", "name", "legality", "formula", "transfers", "years",
               "pros", "cons", "requires", "sources", "verdict"],
              [dict(r, sources="|".join(r["sources"])) for r in D.METHODS])
    write_csv(DATA / "cn3_ladder.csv",
              ["method_id", "amount_usd", "cny_at_ask", "spread_usd", "wire_fee_usd", "cable_usd",
               "transfers", "years", "known_cost_usd", "cost_pct", "net_usd",
               "us_gain_2024", "us_tax_2024", "route_tax_usd", "all_in_usd", "status",
               "note", "source_id", "source_url"], ladder)
    write_csv(DATA / "cn3_steps.csv",
              ["method_id", "step", "action", "detail", "document", "source_id"],
              [dict(method_id=a, step=b, action=c, detail=d, document=e, source_id=f)
               for a, b, c, d, e, f in D.STEPS])
    write_csv(DATA / "cn3_flags.csv",
              ["id", "title", "severity", "issue", "handling", "source_id"],
              [dict(id=a, title=b, severity=c, issue=d, handling=e, source_id=f)
               for a, b, c, d, e, f in D.FLAGS])


# ---------------------------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------------------------
E = html.escape

NAV = [
    ("index.html", "Dashboard"),
    ("cn3-cost.html", "Costs $10k–$400k"),
    ("cn3-methods.html", "Methods"),
    ("cn3-tax.html", "Tax & penalties"),
    ("cn3-steps.html", "Step by step"),
    ("cn3-review.html", "Flagged for review"),
    ("cn3-sources.html", "Sources"),
]

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="assets/cn3.css">
</head>
<body>
<header class="top">
  <div class="brand"><span class="mk">C3</span><span>China → U.S. money guide</span></div>
  <nav class="nav">{nav}</nav>
</header>
<main>
"""

TAIL = """</main>
<footer>
  <p><strong>Research, not advice.</strong> Figures are recomputed from the official pages listed in the
  <a href="cn3-sources.html">source register</a>. Blanks mean “no official source publishes this”, not zero.
  Tax treatment depends on facts this page does not have; confirm with a qualified cross-border tax adviser.</p>
  <p>Snapshot: Bank of China board 2026-11-10 07:32:39 · model build <span id="build"></span> ·
  <a href="cn3-review.html">Flagged for review</a> · <a href="cn3-sources.html">Sources</a></p>
</footer>
<script>document.getElementById('build').textContent=document.lastModified;</script>
</body>
</html>
"""


def nav_html(active: str) -> str:
    out = []
    for href, label in NAV:
        cls = ' class="on"' if href == active else ""
        out.append(f'<a href="{href}"{cls}>{label}</a>')
    return "".join(out)


def page(path: str, title: str, desc: str, body: str):
    (ROOT / path).write_text(
        HEAD.format(title=E(title), desc=E(desc), nav=nav_html(path)) + body + TAIL,
        encoding="utf-8")


def src_link(sid: str, label: str | None = None) -> str:
    s = SRC[sid]
    return f'<a href="{s["url"]}" target="_blank" rel="noopener">{E(label or s["short"])}</a>'


def badge(status: str) -> str:
    txt = {"calculated": "calculated", "partial": "partial", "unverified": "unverified",
           "prohibited": "prohibited", "no_conversion": "no conversion"}.get(status, status)
    return f'<span class="b {status}">{E(txt)}</span>'


def table(headers, rows, cls="", caption="", attrs=""):
    h = "".join(f"<th>{c}</th>" for c in headers)
    body = []
    for r in rows:
        cells = []
        for i, c in enumerate(r):
            lab = E(str(headers[i]))
            cells.append(f'<td data-label="{lab}">{c}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return (f'<div class="scroll"><table class="{cls}" {attrs}>{cap}<thead><tr>{h}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


# --- index ----------------------------------------------------------------------------------
def rows_at(amount: int, mids=("W1", "W2", "W7", "A1", "A2", "C1", "W8")):
    return [compute(m, amount) for m in mids]


def index_page(ladder):
    w1_400 = compute("W1", 400_000)
    w1_10 = compute("W1", 10_000)
    w1_100 = compute("W1", 100_000)

    headline_rows = []
    for amount in AMOUNTS:
        r = compute("W1", amount)
        headline_rows.append([
            f"${amount:,.0f}",
            f"${r['known_cost_usd']:,.2f}",
            f"{r['cost_pct']}",
            f"${r['us_tax_2024']:,.2f}",
            f"${r['all_in_usd']:,.2f}",
            f"{(float(r['all_in_usd'])/amount)*100:.2f}%",
        ])

    summary_rows = []
    for amount in (10_000, 100_000, 200_000, 400_000):
        for mid in ("W1", "W2", "W7", "A1", "A2", "C1", "W8", "X1"):
            r = compute(mid, amount)
            m = METHODS[mid]
            if r["known_cost_usd"] == "":
                cost = '<span class="blank">blank — no official price</span>'
            else:
                cost = f"${r['known_cost_usd']:,.0f}"
            summary_rows.append([
                f"${amount:,.0f}", E(m["name"].split("(")[0].strip()),
                cost, f"${r['us_tax_2024']:,.0f}" if r["us_tax_2024"] != "" else "—",
                str(r["years"]) if r["years"] not in ("", None) else "—",
                badge(r["status"]),
                src_link(m["sources"][0]),
            ])

    body = f"""
<section class="hero">
  <h1>What it actually costs to get your money out of China</h1>
  <p class="lede">A U.S. citizen with CNY in a mainland bank account. Every method priced from
  $10,000 to $400,000 in $10,000 steps, every number traced to an official page, every unknown
  left blank and flagged.</p>
  <div class="answer">
    <strong>The short answer.</strong> No official source imposes a Chinese tax on converting your own
    savings; the PRC income-tax law taxes income, not the exchange. What you pay in China is a bank
    spread of <strong>0.21%</strong>, a wire fee capped at <strong>CNY 260</strong>, and a
    <strong>CNY 150</strong> cable fee. The large number is on the U.S. side: if you acquired the CNY at
    the 2024 average rate, converting produces an IRC §988 currency gain of about
    <strong>6.94% of the dollars you receive</strong>, taxed as ordinary income — roughly
    <strong>1.67% of the amount</strong> at a 24% marginal rate. That is the “considerable tax”,
    and no bank, ATM or Hong Kong rail avoids it.
  </div>
</section>

<section class="kpis">
  <div class="kpi"><span class="k">$10,000</span><span class="v">${w1_10['known_cost_usd']:,.2f}</span>
    <span class="s">bank cost ({w1_10['cost_pct']}) + ${w1_10['us_tax_2024']:,.2f} U.S. tax*</span></div>
  <div class="kpi"><span class="k">$100,000</span><span class="v">${w1_100['known_cost_usd']:,.2f}</span>
    <span class="s">bank cost ({w1_100['cost_pct']}) + ${w1_100['us_tax_2024']:,.2f} U.S. tax*</span></div>
  <div class="kpi"><span class="k">$400,000</span><span class="v">${w1_400['known_cost_usd']:,.2f}</span>
    <span class="s">bank cost ({w1_400['cost_pct']}) + ${w1_400['us_tax_2024']:,.2f} U.S. tax*</span></div>
  <div class="kpi"><span class="k">All-in, $400,000</span><span class="v">${w1_400['all_in_usd']:,.2f}</span>
    <span class="s">{(float(w1_400['all_in_usd'])/400000)*100:.2f}% of the amount</span></div>
</section>
<div class="split"><span><strong>Where the 1.89% goes at $400,000:</strong> 0.23% to the Chinese bank,
1.66% to the IRS under §988, 0% to any PRC conversion tax.</span></div>
<p class="tiny">* U.S. §988 gain at the 2024 IRS yearly average (7.189 CNY/USD) taxed at an assumed 24% federal
marginal rate. Both assumptions are yours to change — see <a href="cn3-tax.html">Tax &amp; penalties</a>.
Every row below links to the official source for its inputs.</p>

<section>
  <h2>Cost to move $10,000 → $400,000 through a documented bank wire</h2>
  <p>The recommended route when the money is traceable: one conversion at the bank's ask, one wire,
  one cable fee. “All-in” adds the U.S. §988 tax line so you see the real number.</p>
  {table(["Amount", "Bank cost", "Cost %", "U.S. §988 tax*", "All-in", "All-in %"], headline_rows, "tight",
         "Bank cost = 0.210% spread + wire fee (0.1%, min CNY 50, max CNY 260) + CNY 150 cable, at the 2026-11-10 BOC board.",
         'data-kind="headline" data-expect="40"')}
  <p class="tiny">Source: {src_link('C3-S01')} (board), {src_link('C3-S02')} (tariff), {src_link('C3-S09')} (IRS rates), {src_link('C3-S10')} (§988).</p>
</section>

<section>
  <h2>Every method at a glance</h2>
  <p>Same four amounts, every route. A blank means no official source publishes a price — it is not zero.</p>
  {table(["Amount", "Method", "Known bank cost", "U.S. tax*", "Years", "Status", "Source"], summary_rows,
         attrs='data-kind="summary" data-expect="32"')}
</section>

<section class="cards">
  <a class="card" href="cn3-cost.html"><h3>Costs, $10k–$400k</h3>
    <p>All 40 increments for every method, each row with its source and its blanks.</p></a>
  <a class="card" href="cn3-methods.html"><h3>Methods &amp; pros/cons</h3>
    <p>17 routes: lawful, conditional, capped and prohibited — and why.</p></a>
  <a class="card" href="cn3-tax.html"><h3>Tax &amp; penalty breakdown</h3>
    <p>The conversion “penalty” decomposed: spread, fees, §988, reporting, fines.</p></a>
  <a class="card" href="cn3-steps.html"><h3>Step by step</h3>
    <p>Exactly what to do, in order, for each usable route.</p></a>
  <a class="card" href="cn3-review.html"><h3>Flagged for review</h3>
    <p>{len(D.FLAGS)} items: every blank, every assumption, every correction to earlier pages.</p></a>
  <a class="card" href="cn3-sources.html"><h3>Source register</h3>
    <p>Official pages with the exact text each figure came from.</p></a>
</section>

<section>
  <h2>Do this first — four facts decide everything</h2>
  <ol class="facts">
    <li><strong>Whose money is it, and where did it come from?</strong> Salary, inheritance, property sale,
    company dividend, or untraceable savings. This single answer selects the route.</li>
    <li><strong>Are you 境内个人 or 境外个人?</strong> A Chinese citizen, or a foreigner who has resided in
    China continuously for one year, is 境内个人. That decides whether the USD 50,000 convenience amount
    even applies to you.</li>
    <li><strong>When did you acquire the CNY, and at what rate?</strong> That sets your U.S. §988 basis and
    therefore the only large tax number in this whole exercise.</li>
    <li><strong>What has already been filed?</strong> FBAR and Form 8938 are information returns with
    penalties that dwarf the conversion cost.</li>
  </ol>
  <p class="tiny">Only the last two are about tax. Neither is a Chinese charge.</p>
</section>

<section class="alert">
  <h2>What not to do</h2>
  <p>Splitting money through relatives' quotas, underground banks, and stablecoin conversions are all
  prohibited, and each carries a statutory fine of up to 30% — 30% to 100% if serious — before any
  criminal exposure. See <a href="cn3-methods.html#prohibited">the prohibited routes</a>.</p>
</section>

<section>
  <h2>Every other page in this repository</h2>
  <p>Earlier sessions built separate dashboards on the same question. Nothing has been deleted; this
  page is the consolidated view and the older layers remain for cross-checking.</p>
  <div class="archive">
    <div><h4>Cost models</h4>
      <a href="cn3-cost.html">Consolidated (this page’s model)</a>
      <a href="cost-tables.html">Cost tables (parallel session)</a>
      <a href="costs.html">Cost grid</a>
      <a href="schedule-cost-10k-400k.html">Official-source schedule</a>
      <a href="schedule-dashboard.html">Schedule dashboard</a>
      <a href="docs/index.html">Data dashboard &amp; calculator</a></div>
    <div><h4>Research</h4>
      <a href="methods.html">Methods (prior)</a>
      <a href="routes.html">Transfer routes (prior)</a>
      <a href="china-rules.html">China FX rules</a>
      <a href="deep-china-rules.html">Deep: China rules</a>
      <a href="us-tax.html">U.S. tax &amp; reporting</a>
      <a href="deep-us-tax.html">Deep: U.S. tax</a></div>
    <div><h4>Tax &amp; penalties</h4>
      <a href="cn3-tax.html">Consolidated tax &amp; penalties</a>
      <a href="penalties.html">Penalty breakdown</a>
      <a href="deep-penalty.html">Deep: penalties</a>
      <a href="tax.html">Tax &amp; reporting (prior)</a>
      <a href="cross-session-review.html">Cross-check &amp; U.S. FX-gain tax</a></div>
    <div><h4>Verification</h4>
      <a href="cn3-review.html">Flagged for review (consolidated)</a>
      <a href="a15-review.html">Independent safety review (2026-11-10)</a>
      <a href="flagged-review.html">Flagged (prior)</a>
      <a href="review.html">Review (prior)</a>
      <a href="schedule-flagged-review.html">Schedule flags</a>
      <a href="cost-review.html">Cost verification flags</a>
      <a href="deep-review.html">Deep review</a></div>
    <div><h4>Sources &amp; method</h4>
      <a href="cn3-sources.html">Source register (consolidated)</a>
      <a href="sources.html">Source register (prior)</a>
      <a href="deep-sources.html">Deep sources</a>
      <a href="schedule-sources.html">Schedule sources</a>
      <a href="docs/methodology.html">Methodology</a>
      <a href="VERIFICATION.md">Verification log</a></div>
    <div><h4>Summaries</h4>
      <a href="EXECUTIVE_SUMMARY.md">Executive summary</a>
      <a href="deep-executive-summary.html">Deep executive summary</a>
      <a href="research/s436-executive-summary.md">Schedule executive summary</a>
      <a href="README.md">README</a>
      <a href="COORDINATION.md">Coordination board</a></div>
  </div>
</section>
"""
    page("index.html", "China → U.S. money guide — CNY to USD costs, methods and taxes",
         "Verified costs of converting CNY to USD from $10,000 to $400,000, every method, with official source links.",
         body)


# --- cost page -------------------------------------------------------------------------------
def cost_page(ladder):
    by_method = {}
    for r in ladder:
        by_method.setdefault(r["method_id"], []).append(r)

    blocks = []
    for mid, m in METHODS.items():
        rows = by_method[mid]
        trs = []
        for r in rows:
            trs.append([
                f"${r['amount_usd']:,.0f}",
                money(r["cny_at_ask"]),
                money(r["spread_usd"]) or '<span class="blank">—</span>',
                money(r["wire_fee_usd"]) or '<span class="blank">blank</span>',
                money(r["cable_usd"]) or '<span class="blank">—</span>',
                money(r["known_cost_usd"]) or '<span class="blank">blank</span>',
                r["cost_pct"] or '<span class="blank">blank</span>',
                money(r["net_usd"]) or '<span class="blank">—</span>',
                str(r["years"]) if r["years"] != "" else "—",
                money(r["us_tax_2024"]) or "—",
                money(r["all_in_usd"]) or '<span class="blank">blank</span>',
                src_link(r["source_id"]),
            ])
        note = f'<p class="tiny">{E(m["cons"])}</p>' if mid in ("X1", "X2", "X3") else ""
        blocks.append(f"""
<details {"open" if mid in ("W1", "W7") else ""} id="{mid.lower()}">
  <summary><strong>{E(m['name'])}</strong> <span class="tag">{E(m['family'])}</span> {badge(rows[0]['status'])}</summary>
  <p class="tiny"><strong>Legality:</strong> {E(m['legality'])}. <strong>Verdict:</strong> {E(m['verdict'])}</p>
  {note}
  {table(["Amount", "CNY at ask", "FX spread", "Wire/ATM fee", "Cable", "Known cost", "Cost %", "Net USD", "Years", "U.S. tax*", "All-in", "Source"], trs,
       attrs=f'data-kind="ladder" data-method="{mid}" data-expect="40"')}
</details>""")

    body = f"""
<section class="hero small">
  <h1>Costs from $10,000 to $400,000, every method</h1>
  <p class="lede">40 increments × 17 methods. Each row is recomputed from the inputs below; each row
  links to the official page behind its inputs. Blanks are published, not filled.</p>
</section>

<section class="inputs">
  <h2>The inputs every number is built from</h2>
  {table(["Input", "Value", "Status", "Source"],
         [[E(i['name']), E(str(i['value'])) if i['value'] not in (None, '') else '<span class="blank">blank</span>',
           badge(i['status'] if i['status'] != 'assumption' else 'partial'), src_link(i['source']) if i['source'] else '—']
          for i in D.INPUTS])}
</section>

<section class="formula">
  <h2>How each column is computed</h2>
  <ul>
    <li><strong>CNY at ask</strong> = amount × 6.6903 (the bank sells USD to you at 现汇卖出价, not the mid).</li>
    <li><strong>FX spread</strong> = amount × 0.210447%, where 0.210447% = (6.6903 − 6.67625) ÷ 6.67625.</li>
    <li><strong>Wire fee</strong> = 0.1% of the CNY amount, minimum CNY 50, maximum CNY 260 per transfer, converted at 6.6903.</li>
    <li><strong>Cable</strong> = CNY 150 per transfer to a non-HK/Macau/Taiwan destination.</li>
    <li><strong>Known cost</strong> = spread + wire/ATM fee + cable. It excludes every blank input.</li>
    <li><strong>U.S. tax*</strong> = 24% × amount × (1 − 6.6903 ÷ 7.189). The 7.189 is the IRS 2024 yearly average; the 24% is an assumption.</li>
    <li><strong>All-in</strong> = known cost + U.S. tax*. It does not include your receiving bank's fee, which is blank.</li>
  </ul>
</section>

<section>
  <h2>Per-method ladder</h2>
  {''.join(blocks)}
</section>

<section>
  <h2>What is deliberately missing from every total</h2>
  <p>Your U.S. bank's incoming-wire fee, any correspondent-bank deduction, the card-network FX spread,
  travel, and PRC tax on the underlying income. Each is either unpublished or fact-dependent; all are
  listed on <a href="cn3-review.html">Flagged for review</a>. Adding them can only raise the totals shown here.</p>
</section>
"""
    page("cn3-cost.html", "CNY → USD costs from $10,000 to $400,000 — every method",
         "Forty $10,000 increments priced for every documented CNY-to-USD route, with official source links.",
         body)


# --- methods ---------------------------------------------------------------------------------
def methods_page():
    rows = []
    for m in D.METHODS:
        rows.append([
            str(m["rank"]), f"<strong>{E(m['name'])}</strong><br><span class=\"tiny\">{E(m['family'])}</span>",
            E(m["legality"]), E(m["pros"]), E(m["cons"]), E(m["requires"]),
            " ".join(src_link(s) for s in m["sources"][:2]),
        ])

    prohibited = [m for m in D.METHODS if m["family"] == "Prohibited"]
    prows = [[E(m["name"]), E(m["legality"]), E(m["cons"]),
              " ".join(src_link(s) for s in m["sources"])] for m in prohibited]

    body = f"""
<section class="hero small">
  <h1>Every way to turn CNY into USD</h1>
  <p class="lede">Seventeen routes, ranked from cheapest-and-cleanest to prohibited. Legality and
  availability come first: a cheap illegal route is not a route.</p>
</section>

<section>
  {table(["#", "Method", "Legality", "Pros", "Cons", "What it requires", "Source"], rows, "methods")}
</section>

<section id="prohibited">
  <h2>Prohibited routes</h2>
  <p>These appear in the table so they can be priced for what they are: a statutory fine, not a fee.</p>
  {table(["Method", "Legality", "Consequence", "Source"], prows)}
  <p class="tiny">Fines under the FX Regulations: art. 39 (逃汇) up to 30% of the amount, 30%–100% if serious;
  art. 40 (非法套汇) the same, with the funds returned; art. 45 (private FX dealing) up to 30%, 30%–100% if serious,
  plus confiscation. {src_link('C3-S07')}</p>
</section>

<section>
  <h2>Why the ranking looks like this</h2>
  <ol>
    <li><strong>Cost is dominated by one line — the spread — and it is the same on every bank-conversion route.</strong>
    A different bank may beat 0.21%, but no lawful route removes it.</li>
    <li><strong>The wire fee is capped.</strong> Above roughly USD 38,900 the marginal fee is zero, so splitting a
    large transfer into several wires only adds cable fees. The one exception is the resident convenience
    amount, which forces one wire per calendar year.</li>
    <li><strong>Card and cash routes are capped by regulation, not by price.</strong> RMB 100,000 a year by ATM and
    USD 10,000 a trip by hand make them irrelevant at USD 400,000, whatever they cost per dollar.</li>
    <li><strong>Documentation, not price, decides whether a route exists for you.</strong> W1 is cheapest; it only
    works if the bank accepts where the money came from.</li>
  </ol>
</section>
"""
    page("cn3-methods.html", "CNY → USD methods: pros, cons, legality and requirements",
         "Seventeen documented ways to convert Chinese yuan to U.S. dollars, with legality, pros, cons and official sources.",
         body)


# --- tax page --------------------------------------------------------------------------------
def tax_page():
    conv_rows = []
    for amount in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000):
        g24 = amount * (1 - ASK / RATE_2024)
        g25 = amount * (1 - ASK / RATE_2025)
        conv_rows.append([
            f"${amount:,.0f}",
            f"${g24:,.0f}", f"${g24*0.24:,.0f}", f"${g24*0.32:,.0f}", f"${g24*0.37:,.0f}",
            f"${g25:,.0f}", f"${g25*0.24:,.0f}",
            "$0",
        ])

    body = f"""
<section class="hero small">
  <h1>The “conversion penalty”, line by line</h1>
  <p class="lede">People describe a “considerable tax” on getting money out of China. Decomposed against
  official sources, the Chinese side is a bank spread and a capped fee. The large number is a U.S. income
  tax on the currency gain — and it is avoidable only by basis and timing, not by choosing another rail.</p>
</section>

<section>
  <h2>Where the money actually goes</h2>
  {table(["Line", "Size", "Charged by", "Official source", "Notes"],
    [["Bank FX spread (one way)", "0.210% of the amount", "Bank of China",
      src_link('C3-S01'), "Difference between the mid and the ask you pay. One board reading, 2026-11-10."],
     ["Wire fee", "0.1%, min CNY 50, max CNY 260 per transfer", "Bank of China",
      src_link('C3-S02'), "Above ≈ USD 38,900 the cap binds and the fee stops growing."],
     ["Cable / telecom fee", "CNY 150 per transfer (CNY 80 to HK/Macau/Taiwan)", "Bank of China",
      src_link('C3-S02'), "Charged per wire, so it is the only reason not to split a large transfer."],
     ["Correspondent bank deduction", '<span class="blank">blank</span>', "Intermediary bank",
      src_link('C3-S02'), "Passed through at actual cost; no amount published."],
     ["U.S. receiving-bank fee", '<span class="blank">blank</span>', "Your U.S. bank",
      "—", "Varies by bank and tier; read your own schedule."],
     ["<strong>PRC tax on converting savings</strong>", "<strong>none found</strong>", "—",
      src_link('C3-S08'), "PRC IIT attaches to income, not to the exchange. No provision taxes the conversion."],
     ["PRC tax on the income that created the balance", "3–45% salary; 20% interest, dividends, rent, property gain",
      "State Taxation Administration", src_link('C3-S08'), "Already due when earned, not because you convert."],
     ["<strong>U.S. IRC §988 gain</strong>", "<strong>≈6.94% of the USD received</strong> (2024 basis)",
      "IRS", src_link('C3-S10'), "Ordinary income. A personal transaction with USD 200 or less of gain is untaxed; above USD 200 the whole gain is taxed."],
     ["FBAR penalty if missed", "USD 16,536 non-willful; USD 165,353 willful per violation", "FinCEN",
      src_link('C3-S11'), "Information return: no tax, large penalty."],
     ["Form 8938 penalty if missed", "USD 10,000 + 10,000 per 30 days, max 60,000", "IRS",
      src_link('C3-S12'), "Separate from the FBAR, same accounts."],
     ["SAFE fine if you use a prohibited route", "≤30%; 30%–100% if serious, of the amount", "SAFE",
      src_link('C3-S07'), "Arts. 39, 40, 45. Before criminal exposure."],
    ])}
</section>

<section>
  <h2>The one real tax: IRC §988</h2>
  <p>The statute is short and does not care how you move the money. Disposing of foreign currency in a
  personal transaction, “no gain shall be recognized … The preceding sentence shall not apply if the gain
  which would otherwise be recognized on the transaction exceeds $200.” Above USD 200 of gain, the whole
  gain is ordinary income — not just the excess. {src_link('C3-S10')}</p>
  <p>Gain = amount received × (1 − today's rate ÷ your acquisition rate). With the 2026-11-10 ask of 6.6903
  and the IRS 2024 yearly average of 7.189, that is 6.94% of everything you convert.</p>
  {table(["Amount converted", "Gain @ 2024 avg (7.189)", "Tax @24%", "Tax @32%", "Tax @37%",
          "Gain @ 2025 avg (7.129)", "Tax @24%", "PRC tax on the conversion"], conv_rows)}
  <p class="tiny">Acquisition rates: {src_link('C3-S09')}. The 24/32/37% columns are arithmetic on your own
  marginal rate, not published brackets for 2026. If your CNY was acquired at today's rate, the gain is zero;
  if it was acquired when the yuan was stronger, your gain is larger.</p>
</section>

<section>
  <h2>Ranking the routes by tax, not by fee</h2>
  <p>Every lawful route that disposes of CNY carries the same §988 gain, because the tax follows the
  currency and not the rail. What differs is the PRC tax attached to the underlying item, and the fine
  attached to a prohibited one.</p>
  {table(["Route", "PRC tax on the conversion", "PRC tax on the income", "U.S. §988", "Fine exposure", "Least-tax verdict"],
    [["W1 documented bank wire", "none found", "already paid when earned", "yes", "none", "<strong>Lowest. This is the route to use.</strong>"],
     ["W2 USD 50,000 convenience amount", "none found", "already paid when earned", "yes", "none", "Same tax, slower."],
     ["W3 emigrant / W4 inheritance", "none found", "tax clearance required", "yes", "none", "Same tax, more documents."],
     ["W7 wire out existing USD", "none — no conversion", "already paid when earned", "<strong>none — no CNY disposed</strong>", "none", "<strong>Lowest of all, if you hold USD already.</strong>"],
     ["W5 property-sale proceeds", "none found", "<strong>20% of the gain</strong>", "yes", "none", "Cheap conversion, expensive income tax."],
     ["W8 company dividend", "none found", "<strong>20% of the dividend</strong> (treaty may reduce)", "yes", "none", "Expensive unless the treaty applies."],
     ["A1 / A2 / C1 ATM and cash", "none found", "already paid when earned", "yes", "none (if within limits)", "Same tax as W1, higher fees."],
     ["X1 / X2 / X3 prohibited", "none found", "already paid when earned", "yes", "≤30%, 30%–100% if serious", "The most expensive possible choice."]],
    caption="PRC rates from the Individual Income Tax Law; §988 from the U.S. Code; fines from the FX Regulations.")}
  <p class="tiny">Sources: {src_link('C3-S08')} · {src_link('C3-S10')} · {src_link('C3-S07')} · {src_link('C3-S09')}</p>
</section>

<section>
  <h2>What actually reduces the U.S. tax</h2>
  <ol>
    <li><strong>Get the basis right.</strong> Your basis is the USD value of the CNY on the day you acquired it.
    If part of the balance was acquired at a weaker yuan, that part carries a smaller gain. Sort the balance by
    acquisition date and rate before converting anything.</li>
    <li><strong>Spread the conversion across tax years.</strong> The gain is ordinary income; keeping it inside a
    lower bracket in each year is the only lever the statute leaves you. Converting USD 400,000 at once can push
    you into the top bracket.</li>
    <li><strong>Do not expect a loss to help.</strong> The quoted text exempts gain; it does not give a deduction
    for a personal loss. Treat a loss as non-deductible until an adviser says otherwise (flag C3-F15).</li>
    <li><strong>Treat the reporting returns as the real penalty risk.</strong> FBAR at USD 10,000 aggregate and
    Form 8938 at USD 50,000/75,000 are information returns. Missing them costs more than the conversion does.</li>
    <li><strong>Check whether the money is a gift or a bequest.</strong> A genuine gift from a foreign person above
    USD 100,000 is reported on Form 3520; that is a different analysis from selling your own currency.</li>
  </ol>
  <p class="tiny">What does <em>not</em> reduce the tax: using a different bank, an ATM, cash, Hong Kong, a
  fintech, or a relative. §988 follows the currency, not the rail. Prohibited routes add a fine on top.</p>
</section>

<section class="alert">
  <h2>If you have never filed an FBAR for this account</h2>
  <p>The exposure is the penalty table above, not the conversion cost. Prior-year non-filing is a separate
  question from how to move the money now, and it should be resolved with a tax adviser before you convert,
  because the transfer itself creates the record.</p>
</section>
"""
    page("cn3-tax.html", "CNY → USD tax and penalty breakdown — spread, §988, FBAR, SAFE fines",
         "Decomposition of the conversion 'penalty': bank spread, wire fees, IRC 988 currency gain, FBAR and Form 8938 penalties, SAFE fines.",
         body)


# --- steps -----------------------------------------------------------------------------------
def steps_page():
    groups = {}
    for mid, step, action, detail, document, sid in D.STEPS:
        groups.setdefault(mid, []).append((step, action, detail, document, sid))

    out = []
    for mid in sorted(groups, key=lambda m: METHODS[m]["rank"]):
        steps = groups[mid]
        m = METHODS[mid]
        trs = [[str(s), f"<strong>{E(a)}</strong>", E(d), E(doc), src_link(sid)]
               for s, a, d, doc, sid in steps]
        out.append(f"""
<section id="steps-{mid.lower()}">
  <h2>{E(m['name'])}</h2>
  <p class="tiny">{E(m['legality'])} · {E(m['verdict'])}</p>
  {table(["#", "Action", "What to do", "Keep this document", "Source"], trs)}
</section>""")

    body = f"""
<section class="hero small">
  <h1>Exactly what to do, in order</h1>
  <p class="lede">Each playbook is the shortest lawful sequence for that route. The order matters:
  confirm classification and documents <em>before</em> converting, because a conversion is hard to undo.</p>
</section>
{''.join(out)}
<section>
  <h2>The order never changes</h2>
  <ol>
    <li>Classify the money and yourself at the bank, in writing.</li>
    <li>Get the document list and the tax-recordal answer.</li>
    <li>Get the all-in quote with a timestamp.</li>
    <li>Convert and remit in one instruction.</li>
    <li>Keep the conversion advice — it is your §988 evidence.</li>
    <li>File the U.S. information returns on time.</li>
  </ol>
</section>
"""
    page("cn3-steps.html", "Step-by-step: how to convert CNY to USD lawfully",
         "Ordered playbooks for each lawful CNY-to-USD route, with the documents to keep and the official source for each step.",
         body)


# --- review ----------------------------------------------------------------------------------
def review_page():
    sev = {"high": "High", "medium": "Medium", "low": "Low"}
    rows = [[E(fid), f"<strong>{E(title)}</strong>", sev[s], E(issue), E(handling),
             src_link(sid) if sid != "—" else "—"] for fid, title, s, issue, handling, sid in D.FLAGS]
    counts = {k: sum(1 for f in D.FLAGS if f[2] == k) for k in ("high", "medium", "low")}

    body = f"""
<section class="hero small">
  <h1>Flagged for review</h1>
  <p class="lede">{len(D.FLAGS)} items: {counts['high']} high, {counts['medium']} medium,
  {counts['low']} low. Every blank value in this dashboard appears here with what is missing and what would
  close it. Nothing on this page blocks the rest of the analysis.</p>
</section>

<section>
  <h2>Corrections to earlier layers</h2>
  <p>Two figures published by earlier sessions in this repository were wrong against the primary text.
  Both are corrected in the consolidated model and recorded here rather than silently changed.</p>
  {table(["Item", "What earlier pages said", "What the official text says", "Source"],
    [["Emigrant-property staging", "A payout above RMB 200,000 is staged over two years (PBC [2004] No. 16 art. 6).",
      "Huifa [2014] No. 2 art. 6(2): 取消移民财产转移分次汇出的要求 — the staged-payout requirement was repealed, and art. 6(1) removed the > RMB 500,000 head-office filing.",
      src_link('C3-S05')],
     ["BOC tariff date", "Tariff effective 2024-11-01.",
      "The page states 收费标准2014年11月1日起 — effective 2014-11-01.", src_link('C3-S02')]]) }
</section>

<section>
  <h2>All flags</h2>
  {table(["ID", "Item", "Severity", "What is missing or disputed", "How it is handled here", "Source"], rows)}
</section>

<section>
  <h2>Independent safety review</h2>
  <p>A separate session reviewed this repository on 2026-11-10 and published
  <a href="a15-review.html">its own findings</a>. Two of its warnings are answered directly here:</p>
  <ul>
    <li><strong>The $25 “OUR” charge is not added to any total on this site.</strong> It appears only in a
    corporate trade-finance notice, not the personal e-banking tariff, so it is left blank and flagged
    (C3-F03, C3-F04) rather than combined with the personal schedule.</li>
    <li><strong>§988 is quantified, not assumed away.</strong> The gain is shown per row and per bracket on
    <a href="cn3-tax.html">Tax &amp; penalties</a>, with the acquisition-date gap flagged as C3-F02.</li>
  </ul>
</section>

<section>
  <h2>What would close the high-severity items</h2>
  <ul>
    <li>A bank statement showing the account type and the balance history.</li>
    <li>The acquisition dates and rates for the CNY (or the records that establish them).</li>
    <li>A written classification from the branch: 境内个人 or 境外个人, and the document list it will accept.</li>
    <li>Your U.S. bank's incoming-wire fee schedule.</li>
    <li>Confirmation of whether any FBAR or Form 8938 was filed for prior years.</li>
  </ul>
  <p class="tiny">With those five, every high-severity flag closes and the cost estimates collapse to a
  single number per route. Without them, the ranges on this site are the honest answer.</p>
</section>
"""
    page("cn3-review.html", "Flagged for review — blanks, assumptions and corrections",
         "Every unverified value, assumption and correction in the China-to-U.S. money guide, with the official source that would close it.",
         body)


# --- sources ---------------------------------------------------------------------------------
def sources_page():
    rows = []
    for s in D.SOURCES:
        st = s["status"]
        label = "fetched 2026-11-10" if st == "verified-2026-11-10" else "official URL, carried forward"
        cls = "calculated" if st == "verified-2026-11-10" else "partial"
        rows.append([E(s["id"]), f"<strong>{E(s['title'])}</strong><br><span class=\"tiny\">{E(s['issuer'])}</span>",
                     f'<a href="{s["url"]}" target="_blank" rel="noopener">{E(s["url"])}</a>',
                     f'<span class="b {cls}">{E(label)}</span>',
                     f"<q>{E(s['excerpt'])}</q>", E(s["supports"])])

    inputs = [[E(i["id"]), E(i["name"]), E(str(i["value"])) if i["value"] not in (None, "") else '<span class="blank">blank</span>',
               E(i["unit"]), src_link(i["source"]) if i["source"] else "—",
               badge(i["status"] if i["status"] in ("verified", "derived", "partial") else "partial"),
               E(i["note"])] for i in D.INPUTS]

    body = f"""
<section class="hero small">
  <h1>Sources, with the text each number came from</h1>
  <p class="lede">Every figure is tied to one of these pages. The excerpt column is the exact text
  read; the status column says whether this session fetched it on 2026-11-10 or whether it is an official
  URL carried forward from a prior session's register.</p>
</section>

<section>
  <h2>Official sources ({len(D.SOURCES)})</h2>
  {table(["ID", "Page", "URL", "Status", "Text relied on", "What it supports"], rows, "sources")}
</section>

<section>
  <h2>Input register ({len(D.INPUTS)})</h2>
  <p>Every number in the model, its unit, its source and its status. “Derived” means arithmetic on two
  published numbers. A blank row is a value no official page publishes.</p>
  {table(["ID", "Input", "Value", "Unit", "Source", "Status", "Note"], inputs)}
</section>

<section>
  <h2>How to re-check any number on this site</h2>
  <ol>
    <li>Open the source linked from the row.</li>
    <li>Compare the excerpt here with the page.</li>
    <li>Recompute: spread = amount × 0.210447%; wire = min(max(0.1% × CNY, 50), 260) + 150, ÷ 6.6903.</li>
    <li>Run <code>python3 scripts/verify_cn3.py</code> — it re-derives all {len(AMOUNTS)*len(METHODS)} rows
    and fails if any row, link, blank or arithmetic step disagrees.</li>
  </ol>
</section>
"""
    page("cn3-sources.html", "Official sources behind every CNY → USD figure",
         "Register of official Chinese and U.S. sources with the exact text relied on for each figure.",
         body)


def main():
    ladder = build_ladder()
    write_data(ladder)
    index_page(ladder)
    cost_page(ladder)
    methods_page()
    tax_page()
    steps_page()
    review_page()
    sources_page()
    print(f"built {len(ladder)} ladder rows, {len(D.SOURCES)} sources, {len(D.INPUTS)} inputs, "
          f"{len(METHODS)} methods, {len(D.STEPS)} steps, {len(D.FLAGS)} flags")


if __name__ == "__main__":
    main()
