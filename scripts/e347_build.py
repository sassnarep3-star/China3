#!/usr/bin/env python3
"""Build the e347 dashboard: root index.html, dashboard/*.html and data/e347_*.csv.

    python3 scripts/e347_build.py            write everything
    python3 scripts/e347_build.py --check    fail if a generated file on disk is stale
                                             (dashboard/archive.html is exempt: it lists
                                             whatever pages exist, so other sessions can
                                             add pages without breaking this check)
"""
import argparse
import csv
import html
import io
import re
import sys
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e347_data as data  # noqa: E402
import e347_costs as costs  # noqa: E402
import b2d_data as decide  # noqa: E402  (decision-readiness register, session b2d4ff40)
from e347_costs import q  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard"
REPO = "https://github.com/sassnarep3-star/China3"
SRC = {s[0]: s for s in data.SOURCES}
METHOD = {m["id"]: m for m in data.METHODS}
FLAG = {f[0]: f for f in data.FLAGS}
NAV = [("index", "Home"), ("decisions", "Decide"), ("methods", "Methods"), ("costs", "Costs"),
       ("steps", "Steps"), ("tax", "Tax"), ("flagged", "Flagged"), ("sources", "Sources"),
       ("archive", "Archive"),
       # Integration (session arena/f9a30493-china3): honors M5F19-REQ-01 and 76E-REQ-01, two
       # open board link requests. Additive nav entries pointing at root-level verified editions.
       ("m5f19", "M5F19 — independent re-verification &amp; cost reconciliation (10 Nov 2026)"),
       ("76e", "Source re-check, 11 Nov 2026")]
OWN_PAGES = {"index.html"} | {f"dashboard/{k}.html" for k, _ in NAV if k != "index"}
KEY_AMOUNTS = [D(10000), D(50000), D(100000), D(200000), D(400000)]


def short_issuer(issuer):
    for key, label in (("People's Bank", "PBOC"), ("Bank of China", "BOC"), ("SAFE", "SAFE"),
                       ("State Taxation", "STA"), ("Ministry of Finance", "STA"), ("National People", "STA"),
                       ("State Council", "State Council"), ("Internal Revenue", "IRS"),
                       ("Government Publishing", "US Code"), ("FinCEN", "FinCEN"), ("eCFR", "eCFR"),
                       ("Customs", "CBP")):
        if key in issuer:
            return label
    return issuer


esc = html.escape


def usd(x, cents=True):
    if x is None:
        return ""
    v = q(x) if cents else q(x, D(1))
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.2f}" if cents else f"{sign}${abs(v):,.0f}"


def pct(x, places=2):
    return f"{q(x, D(1).scaleb(-places))}%"


class Ctx:
    """Link prefixes: the landing page sits at the root, the rest under dashboard/."""

    def __init__(self, key):
        self.key = key
        self.root = key == "index"
        self.sub = "dashboard/" if self.root else ""
        self.home = "index.html" if self.root else "../index.html"
        self.up = "" if self.root else "../"

    def page(self, k):
        if k == "index":
            return self.home
        if k == "m5f19":
            return f"{self.up}m5f19-dashboard.html"
        if k == "76e":
            return f"{self.up}76e-verification.html"
        return f"{self.sub}{k}.html"

    def src(self, ids, short=True):
        out = []
        for i in ids:
            s = SRC[i]
            if short:
                out.append(f'<a href="{esc(s[3])}" rel="noopener" title="{esc(s[2])}">{i} {esc(short_issuer(s[1]))}</a>')
            else:
                out.append(f'<a href="{esc(s[3])}" rel="noopener">{i}</a>')
        return " ".join(out)

    def flags(self, ids):
        return " ".join(f'<a href="{self.page("flagged")}#{i}">{i}</a>' for i in ids)

    def blank(self, flag):
        return f'<span class="blank">not verified</span> <a href="{self.page("flagged")}#{flag}">{flag}</a>'

    def route(self, mid, text=None):
        return f'<a href="{self.page("methods")}#{mid}">{esc(text or mid)}</a>'


def render(ctx, title, description, body):
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{ctx.page(k)}"{cur if k == ctx.key else ""}>{label}</a>' for k, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="e347-dashboard">
<meta name="description" content="{esc(description)}">
<title>{esc(title)} · China money</title>
<link rel="stylesheet" href="{ctx.sub}site.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{ctx.home}">China money<small>RMB to USD, source-checked</small></a>
<nav class="nav" aria-label="Sections">{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>Rates and fees: Bank of China board published {esc(data.RATE["board_time"])} and its public personal tariff. Sources were read on {data.SNAPSHOT_DATE}.</p>
<p>General research from public official pages. It is not legal, tax or banking advice and makes no finding about any person's case.</p>
<p><a href="{ctx.page("sources")}">All sources</a> · <a href="{ctx.page("flagged")}">Open items</a> · <a href="{REPO}">Repository</a> · built by <code>scripts/e347_build.py</code></p>
</div></footer>
</body>
</html>
"""


def table(head, rows, cls="stack", caption=None, kind="data"):
    """rows: list of (row_id or None, [cells]). Each cell is HTML; the last column is the source."""
    out = [f'<div class="tbl"><table class="{cls}" data-kind="{kind}">']
    if caption:
        out.append(f"<caption>{caption}</caption>")
    src_cls = ' class="src"'
    out.append("<thead><tr>" + "".join(
        f'<th{src_cls if i == len(head) - 1 else ""}>{h}</th>' for i, h in enumerate(head)) + "</tr></thead><tbody>")
    for rid, cells in rows:
        tds = []
        for i, c in enumerate(cells):
            klass = ' class="src"' if i == len(cells) - 1 else ""
            label = "" if "num" in cls else f' data-label="{esc(re.sub("<[^>]+>", "", head[i]))}"'
            tds.append(f"<td{klass}{label}>{c}</td>")
        rid_attr = f' id="{rid}"' if rid else ""
        out.append(f"<tr{rid_attr}>" + "".join(tds) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def status_pill(status):
    cls = "bad" if status.startswith("Prohibited") else ("ok" if status == "Lawful" else "")
    return f'<span class="pill {cls}">{esc(status)}</span>'


# --------------------------------------------------------------------- cost tables
def cost_sources(m):
    model = m["model"]
    base = {"fx_wire": ["S01", "S02"], "property": ["S01", "S02"], "wire_only": ["S02", "S01"],
            "quota": ["S01", "S02", "S06"], "atm": ["S03", "S19", "S01"], "cash": ["S01", "S20"],
            "dividend": ["S25", "S01", "S02"], "blank": ["S24"]}[model]
    rule = [s for s in m["src"] if s not in base][:1] if model in ("fx_wire", "property", "wire_only") else []
    return base + rule


def cost_table(ctx, m, amounts=None, extra_src=()):
    model = m["model"]
    amounts = amounts or data.AMOUNTS
    s = ctx.src(cost_sources(m) + [x for x in extra_src if x not in cost_sources(m)], short=False)
    rows = []
    for a in amounts:
        r = costs.row(m, a)
        amt = usd(a, False)
        if model == "fx_wire":
            head = ["Amount", "Known bank cost", "% of amount", "Exchange spread", "Wire fee", "RMB debited", "Other banks' fees", "Source"]
            cells = [amt, usd(r["known_cost_usd"]), pct(r["known_cost_pct"]), usd(r["spread_usd"]), usd(r["fee_usd"]),
                     f'¥{q(r["rmb_debited"]):,.2f}', ctx.blank("U04"), s]
        elif model == "property":
            head = ["Amount remitted", "Known bank cost", "% of amount", "Chinese tax on your gain (20%)", "Other banks' fees", "Source"]
            cells = [amt, usd(r["known_cost_usd"]), pct(r["known_cost_pct"]), ctx.blank("U01"), ctx.blank("U04"), s]
        elif model == "wire_only":
            head = ["Amount", "Known bank cost", "% of amount", "Other banks' fees", "Source"]
            cells = [amt, usd(r["known_cost_usd"]), pct(r["known_cost_pct"], 3), ctx.blank("U04"), s]
        elif model == "quota":
            head = ["Amount", "Calendar years", "Known bank cost", "% of amount", "Exchange spread", "Wire fees", "Other banks' fees", "Source"]
            cells = [amt, str(r["calendar_years"]), usd(r["known_cost_usd"]), pct(r["known_cost_pct"]), usd(r["spread_usd"]),
                     usd(r["fee_usd"]), ctx.blank("U04"), s]
        elif model == "atm":
            head = ["Amount", "Calendar years", "Withdrawals", "Bank of China card fee", "% of amount", "Exchange rate and ATM-owner fee", "Source"]
            cells = [amt, str(r["calendar_years"]), str(r["units"]), usd(r["known_cost_usd"]), pct(r["known_cost_pct"]), ctx.blank("U13"), s]
        elif model == "cash":
            head = ["Amount", "Trips at $5,000", "Trips at $10,000 with bank permit", "Exchange spread", "% of amount", "Banknote and travel cost", "Source"]
            cells = [amt, str(r["units"]), str(r["extra"]), usd(r["known_cost_usd"]), pct(r["known_cost_pct"]), ctx.blank("U14"), s]
        elif model == "dividend":
            head = ["Dividend before tax", "Chinese tax (20%)", "Bank cost", "Total known cost", "% of dividend", "You receive", "Source"]
            cells = [amt, usd(r["tax_usd"]), usd(r["spread_usd"] + r["fee_usd"]), usd(r["known_cost_usd"]), pct(r["known_cost_pct"]),
                     usd(r["extra"]), s]
        else:  # blank
            head = ["Amount", "Outbound RMB wire fee", "Offshore conversion cost", "Source"]
            cells = [amt, ctx.blank("U09"), ctx.blank("U09"), s]
        cells[1] = cells[1] if model in ("quota", "atm", "cash", "blank") else f"<b>{cells[1]}</b>"
        rows.append((None, cells))
    return table(head, rows, cls="num")


COST_NOTES = {
    "fx_wire": "One conversion and one wire. Spread is measured against the midpoint of Bank of China's own buying and selling rates.",
    "property": "Same bank cost as a documented-income wire. The Chinese tax on the gain depends on your purchase price and costs, which are not known here.",
    "wire_only": "No conversion, so no spread. The fee is charged in RMB on the RMB value of the wire; the selling rate is used to express it in dollars (the choice of rate changes the result by a few cents below $39,000 and not at all above).",
    "quota": "USD 50,000 is converted and wired each calendar year. Later years are priced at today's rate, so this is a scenario, not a forecast.",
    "atm": "Withdrawals of RMB 10,000 each, the daily cap per card. Counts of withdrawals and years use Bank of China's selling rate as a stand-in for the card network's rate, which was not verified.",
    "cash": "Banknotes bought at the board's cash selling rate, which equals the wire selling rate on this board. The cash must first be bought lawfully under another route.",
    "dividend": "The first column is the dividend declared. Chinese tax of 20% is withheld, and the rest is converted and wired once.",
    "blank": "No official page publishes either cost. The cells stay blank.",
}


def page_costs():
    ctx = Ctx("costs")
    r = data.RATE
    mid = costs.mid()
    inputs = [
        ("Bank sells you USD at", f'{r["ask"]} RMB per dollar', "Selling Rate 668.51 per 100, published " + r["board_time"], ["S01"]),
        ("Bank buys USD at", f'{r["bid"]} RMB per dollar', "Buying Rate 665.71 per 100, same board", ["S01"]),
        ("Midpoint used as the fair value", f"{mid} RMB per dollar", "Halfway between the two rates above. The spread you pay is the selling rate minus this.", ["S01"]),
        ("Exchange spread", pct((r["ask"] - mid) / r["ask"] * 100, 4), "Share of the amount lost to the spread on a one-way conversion", ["S01"]),
        ("Wire fee", "0.1%, min ¥50, max ¥260", "Bank of China personal e-banking cross-border wire", ["S02"]),
        ("Cable charge", "¥150 per wire", "Destinations outside Hong Kong, Macao and Taiwan", ["S02"]),
        ("Overseas ATM, UnionPay card", "¥12 + 1%, max ¥112", "Per withdrawal, Bank of China tariff", ["S03"]),
        ("Overseas ATM limits", "¥10,000 a day per card; ¥100,000 a year per person", "汇发〔2017〕29号", ["S19"]),
        ("Annual convenience amount", "USD 50,000 a year", "For Chinese citizens and Foreign Permanent Resident ID holders", ["S06", "S05"]),
        ("Cash carried out", "USD 5,000 free; up to USD 10,000 with bank permit", "Per trip", ["S20"]),
        ("Chinese tax on dividends", "20%", "Individual Income Tax Law Art. 3", ["S25"]),
    ]
    in_rows = [(None, [esc(a), f"<b>{esc(b)}</b>", esc(c), ctx.src(d)]) for a, b, c, d in inputs]

    comp = []
    for m in data.METHODS:
        if m["model"] == "none":
            continue
        cells = [f'<span class="id">{m["id"]}</span>{esc(m["name"])}']
        for a in KEY_AMOUNTS:
            x = costs.row(m, a)
            cells.append(usd(x["known_cost_usd"]) if x["known_cost_usd"] is not None else ctx.blank("U09"))
        last = costs.row(m, D(400000))
        if m["model"] == "cash":
            time = f'{last["units"]} trips'
        elif last["calendar_years"] is None:
            time = ctx.blank("U09")
        elif last["calendar_years"] == 1:
            time = "1 wire"
        else:
            time = f'{last["calendar_years"]} years'
        cells += [time, ctx.src(cost_sources(m), short=False)]
        comp.append((None, cells))

    parts = [f"""<h1>What each route costs, from $10,000 to $400,000</h1>
<p class="lead">Known bank cost only. Fees charged by other banks in the chain are not published anywhere official, so they are left blank and are not in any total. Tax is on the <a href="tax.html">Tax page</a>.</p>
<div class="kpis">
<div class="kpi"><b>{usd(costs.row(METHOD["L01"], D(10000))["known_cost_usd"])}</b><span>to convert and wire $10,000</span></div>
<div class="kpi"><b>{usd(costs.row(METHOD["L01"], D(100000))["known_cost_usd"])}</b><span>for $100,000</span></div>
<div class="kpi"><b>{usd(costs.row(METHOD["L01"], D(400000))["known_cost_usd"])}</b><span>for $400,000</span></div>
<div class="kpi"><b>{usd(costs.row(METHOD["L03"], D(400000))["known_cost_usd"])}</b><span>if the money is already USD</span></div>
</div>
<h2>All routes side by side</h2>
<p>The bank routes that convert and wire once (L01, L02, L04, L05, L06) cost the same at the bank; what differs is the paperwork. The yearly-quota, ATM and cash routes cost more because the fee repeats, and they take years or dozens of trips.</p>
{table(["Route", "$10,000", "$50,000", "$100,000", "$200,000", "$400,000", "Time for $400,000", "Source"], comp, cls="num routes")}
<p class="note">The dividend row includes the 20% Chinese tax, which is why it is far larger. ATM and cash rows cover only the part that is published (see each table).</p>
<h2>What the numbers are built from</h2>
{table(["Input", "Value", "What it is", "Source"], in_rows)}
<p>Formula for a convert-and-wire route: <code>amount × (selling rate − midpoint) ÷ selling rate</code> for the spread, plus <code>(0.1% of the RMB amount, kept between ¥50 and ¥260, + ¥150) ÷ selling rate</code> for the wire. The percentage part of the wire fee stops growing at about ${q(r["wire_max"] / r["wire_rate"] / r["ask"], D(1)):,}.</p>
<h2>Every $10,000 step, route by route</h2>"""]
    shared = [m for m in data.METHODS if m["model"] == "fx_wire"]
    for m in data.METHODS:
        if m["model"] == "none" or (m["model"] == "fx_wire" and m is not shared[0]):
            continue
        group = shared if m["model"] == "fx_wire" else [m]
        a, b = costs.row(m, D(10000)), costs.row(m, D(400000))
        rng = (f'{usd(a["known_cost_usd"])} to {usd(b["known_cost_usd"])}' if a["known_cost_usd"] is not None else "not published")
        anchors = "".join(f'<a id="{g["id"]}"></a>' for g in group)
        title = " · ".join(f'{g["id"]} {esc(g["name"])}' for g in group) if len(group) == 1 else (
            ", ".join(g["id"] for g in group) + " · Convert and wire once (documented income, change-back, inheritance, emigrant transfer)")
        links = " ".join(f'<a href="steps.html#{g["id"]}">{g["id"]} steps</a>' for g in group)
        parts.append(f"""{anchors}<details{" open" if m["id"] == "L01" else ""}>
<summary>{title}<span>{rng}</span></summary>
<p class="note">{COST_NOTES[m["model"]]} {links}</p>
{cost_table(ctx, m, extra_src=[g["src"][0] for g in group[1:]])}
</details>""")
    return render(ctx, "Costs", "Bank cost of every lawful RMB to USD route in $10,000 steps up to $400,000, with a source on every row.", "\n".join(parts))


# ------------------------------------------------------------------------- methods
def page_methods():
    ctx = Ctx("methods")
    lawful = [m for m in data.METHODS if m["model"] != "none"]
    banned = [m for m in data.METHODS if m["model"] == "none"]
    rows = []
    for m in lawful:
        c = costs.row(m, D(100000))["known_cost_usd"]
        cost = (f'<a href="costs.html#{m["id"]}">{usd(c)}</a>' if c is not None else ctx.blank("U09"))
        fl = f' <span class="note">Open: {ctx.flags(m["flags"])}</span>' if m["flags"] else ""
        rows.append((m["id"], [
            f'<span class="id">{m["id"]}</span>{esc(m["name"])}<br>{status_pill(m["status"])}',
            esc(m["fits"]), esc(m["limit"]), esc(m["pros"]), esc(m["cons"]), esc(m["tax"]) + fl,
            cost + f' · <a href="steps.html#{m["id"]}">steps</a>', ctx.src(m["src"])]))
    brow = [(m["id"], [f'<span class="id">{m["id"]}</span>{esc(m["name"])}<br>{status_pill(m["status"])}',
                       esc(m["cons"]), esc(m["tax"]), ctx.src(m["src"])]) for m in banned]
    lrow = [(None, [f'<span class="id">{i}</span>{esc(label)}',
                    f'<span class="blank">not re-read in this pass</span> <a href="flagged.html#U19">U19</a> · <a href="../{page}">earlier write-up</a>',
                    f'<a href="{esc(url)}" rel="noopener">official page cited earlier</a>']) for i, label, url, page in data.LEGACY_ROUTES]
    body = f"""<h1>Every lawful route, and the ones to avoid</h1>
<p class="lead">Eleven lawful routes and six prohibited ones, each tied to the rule that creates it. Which lawful route is open to you depends on where the money came from and which ID your account is held under.</p>
<div class="banner">A foreign passport holder is a 境外个人 under the SAFE rules. The USD 50,000-a-year amount that Chinese citizens use on ID alone does not apply to buying foreign currency on a passport; only holders of the Foreign Permanent Resident ID get it. A foreigner who has lived in China for a year may be classed differently by the bank: see <a href="flagged.html#U10">U10</a>.</div>
<h2>Lawful routes</h2>
{table(["Route", "Use it when", "Limit", "Advantages", "Drawbacks", "Tax", "Bank cost at $100,000", "Source"], rows)}
<h2>Prohibited: do not use</h2>
<p>These are the shortcuts people are usually offered when a bank asks for documents. Each one is named in an official rule or enforcement notice.</p>
{table(["Route", "Why it is prohibited", "Penalty", "Source"], brow)}
<h2>Also catalogued by earlier passes, not re-read today</h2>
<p>These appear in the older research in this repository with an official page cited. This pass did not re-open those pages, so they are listed without a verdict. Most are not ways to turn a personal RMB balance into dollars.</p>
{table(["Route", "Status here", "Source"], lrow)}
"""
    return render(ctx, "Methods", "Lawful and prohibited ways to convert RMB in a Chinese bank account to US dollars, with pros, cons, limits and sources.", body)


# --------------------------------------------------------------------------- steps
def page_steps():
    ctx = Ctx("steps")
    parts = ["""<h1>Step by step, for each lawful route</h1>
<p class="lead">Each step names the official rule behind it. Banks can ask for more than the rule's minimum, so get the branch's document list in writing before you start.</p>"""]
    parts.append('<p class="note">Jump to: ' + " · ".join(f'<a href="#{m}">{m}</a>' for m in data.STEPS) + "</p>")
    for mid, steps in data.STEPS.items():
        m = METHOD[mid]
        rows = [(f"{mid}-{n}", [f"Step {n}", esc(text), ctx.src(src)]) for n, (text, src) in enumerate(steps, 1)]
        parts.append(f'<h2 id="{mid}">{mid} · {esc(m["name"])}</h2>\n<p class="note">{esc(m["fits"])} '
                     f'<a href="costs.html#{mid}">Cost table</a> · <a href="methods.html#{mid}">Route details</a></p>\n'
                     + table(["Step", "What to do", "Source"], rows))
    return render(ctx, "Steps", "Exact steps for each lawful RMB to USD route, each linked to its official rule.", "\n".join(parts))


# ----------------------------------------------------------------------------- tax
def page_tax():
    ctx = Ctx("tax")
    years = sorted(data.RATE["irs_avg"], reverse=True)
    groups = []
    for t in data.TAX_ROWS:
        if t[1] not in groups:
            groups.append(t[1])
    parts = [f"""<h1>Where the tax and the penalties actually are</h1>
<p class="lead">No official source read in this pass taxes the conversion or the wire. The money at stake sits in four other places: Chinese tax on the income behind the balance, the bank's spread and fee, a U.S. currency gain, and U.S. reporting penalties.</p>
<div class="banner">The brief mentions "a considerable amount of taxes" but names no tax. Nothing below confirms what you were quoted. See <a href="flagged.html#U02">U02</a>.</div>"""]
    for g in groups:
        rows = []
        for tid, grp, item, what, amount, src, flags in data.TAX_ROWS:
            if grp != g:
                continue
            amt = f"<b>{esc(amount)}</b>" if amount else ctx.blank(flags[0])
            fl = f' <span class="note">Open: {ctx.flags(flags)}</span>' if flags else ""
            rows.append((tid, [esc(item), amt, esc(what) + fl, ctx.src(src)]))
        parts.append(f"<h2>{esc(g)}</h2>\n" + table(["Item", "Rate or amount", "What it means", "Source"], rows))

    gain_rows = []
    for a in data.AMOUNTS:
        gain_rows.append((None, [usd(a, False)] + [usd(costs.fx_gain(a, y), False) for y in years] + [ctx.src(["S28", "S27", "S01"], short=False)]))
    g24 = costs.fx_gain(D(400000), "2024")
    parts.append(f"""<h2>U.S. currency gain by the year the RMB was acquired</h2>
<p>If you sell RMB for more dollars than it cost you in dollars, the difference is a gain. The table shows that gain for each amount, taking the IRS yearly average rate as the cost. Your real cost is the rate on the day you received each RMB amount, so treat this as a scale, not your figure. The tax is your own rate times the gain; a negative number is a loss, and whether a loss is usable was not verified.</p>
{table(["Dollars received today"] + [f"Acquired {y} (avg {data.RATE['irs_avg'][y]})" for y in years] + ["Source"], gain_rows, cls="num")}
<p class="note">Example: RMB acquired at the 2024 average and sold today for $400,000 shows a gain of {usd(g24, False)}. Whether the personal-transaction rule (no gain recognised up to $200) applies is a legal judgement: <a href="flagged.html#U05">U05</a>.</p>
<h2>How to read this</h2>
<ul class="plain">
<li><b>If the tax was paid when the money was earned</b>, the remaining cost of the transfer is the bank's: about a quarter to half of one percent.</li>
<li><b>If Chinese tax was never paid</b>, that is the large number, and it is owed whether or not the money moves. The bank will not accept the transfer without tax evidence.</li>
<li><b>On the U.S. side</b>, income belongs on the return for the year it was earned, with credit for Chinese tax paid. The transfer adds a possible currency gain and the reporting forms.</li>
<li><b>The prohibited routes</b> cost far more than any tax here: fines start at up to 30% of the amount.</li>
</ul>""")
    return render(ctx, "Tax", "Chinese and U.S. tax, bank cost, reporting duties and penalties around moving RMB to USD, each with its official source.", "\n".join(parts))


# ------------------------------------------------------------------------- flagged
def read_irregularities():
    path = ROOT / "data" / "e347_irregularities.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def page_flagged():
    ctx = Ctx("flagged")
    sev = {"high": "bad", "medium": "warn", "low": ""}
    rows = [(fid, [f'<span class="id">{fid}</span>{esc(item)}<br><span class="pill {sev[s]}">{s}</span>',
                   esc(why), esc(close), ctx.src(src)]) for fid, s, item, why, close, src in data.FLAGS]
    irr = []
    for r in read_irregularities():
        links = f'<a href="{REPO}/blob/main/{esc(r["evidence_path"])}" rel="noopener">repository file</a>' if r["evidence_path"] else f'<a href="{REPO}/pulls" rel="noopener">repository</a>'
        if r["official_source_id"]:
            links += " " + ctx.src([r["official_source_id"]])
        irr.append((r["id"], [f'<span class="id">{r["id"]}</span>{esc(r["where"])}<br><span class="pill {sev[r["severity"]]}">{r["severity"]}</span>',
                              esc(r["finding"]), esc(r["evidence"]), esc(r["status"]), links]))
    others = [("a058-flagged-review.html", "Independent flags (session A058)"),
              ("a502-review.html", "Independent accuracy audit (session A502)"),
              ("completion-audit.html", "Completion audit (session 4a528a74)"),
              ("c3x-flagged.html", "Flags of the C3X edition"),
              ("a15-review.html", "Integration safety review (session A15)"),
              ("cross-session-review.html", "Cross-session review")]
    orow = [(None, [f'<a href="../{p}">{esc(t)}</a>', "Kept as published by its session; not edited here."])
            for p, t in others if (ROOT / p).exists()]
    body = f"""<h1>Flagged for review</h1>
<p class="lead">Everything this site could not confirm from an official page, every assumption, and every problem found in the repository. Blank cells elsewhere on the site link here. Nothing on this page blocks publication.</p>
<div class="kpis">
<div class="kpi"><b>{len(data.FLAGS)}</b><span>open items in the research</span></div>
<div class="kpi"><b>{sum(1 for f in data.FLAGS if f[1] == "high")}</b><span>of them high: they change which route applies</span></div>
<div class="kpi"><b>{len(irr)}</b><span>findings from the repository review</span></div>
<div class="kpi"><b>{sum(1 for s in data.SOURCES if s[4] == "excerpt")}</b><span>of {len(data.SOURCES)} sources read as excerpts</span></div>
</div>
<h2>Unverified or uncertain</h2>
{table(["Item", "Why it is blank or uncertain", "What would settle it", "Source"], rows)}
<h2>Problems found in the repository</h2>
<p>From a scripted pass over every line of every tracked file plus a manual read of the main files, listed in <code>research/e347-repo-review.md</code>. "Evidence" is what <code>scripts/e347_repo_review.py</code> measured when it was last run.</p>
{table(["Where", "Finding", "Evidence", "Status", "Link"], irr, kind="repo")}
<h2>Review pages from other sessions</h2>
{table(["Page", "Note"], orow, kind="nav")}
"""
    return render(ctx, "Flagged for review", "Unverified values, assumptions and repository problems, each with a source link.", body)


# ------------------------------------------------------------------------- sources
def page_sources():
    ctx = Ctx("sources")
    how = {"direct": '<span class="pill ok">read in full</span>', "excerpt": '<span class="pill warn">excerpt only</span>'}
    rows = [(sid, [f'<span class="id">{sid}</span>{esc(issuer)}', how[h], esc(says),
                   f'<a href="{esc(url)}" rel="noopener">{esc(title)}</a>'])
            for sid, issuer, title, url, h, says in data.SOURCES]
    n_direct = sum(1 for s in data.SOURCES if s[4] == "direct")
    body = f"""<h1>Sources</h1>
<p class="lead">{len(data.SOURCES)} official pages, all read on {data.SNAPSHOT_DATE}. {n_direct} were opened and read in full. {len(data.SOURCES) - n_direct} were confirmed from the page's own text as returned by a search of that address, and are marked so you can open them yourself.</p>
<p>Only government, regulator, central-bank and Bank of China pages are used. No law-firm articles, forums or news sites.</p>
{table(["Issuer", "How it was read", "What it establishes", "Document"], rows)}
"""
    return render(ctx, "Sources", "The official pages every figure on this site was read from.", body)


# ------------------------------------------------------------------------- archive
ARCHIVE_GROUPS = [
    (r"^legacy-index\.html$|^verify-2026\.html$", "Previous landing page", "Long single page; superseded by this dashboard."),
    (r"^c3x-", "C3X edition (session 2c8d441e)", "Independent pass on the same 17:39:58 board; its bank-cost figures match this dashboard."),
    (r"^a513", "A513 answer page (session 5130fbc0)", "Independent pass on the same board; figures match."),
    (r"^e8b7-", "E8B7 edition (session e8b70ef3)", ""),
    (r"^s055-", "S055 edition (session 05552f6e)", ""),
    (r"^c5bf-", "C5BF integration audit (session c5bf9ddc)", "Corrections to the S775 layer and a fresh-board ladder."),
    (r"^s775-", "S775 audit", "Known problems: R01, R04, R10 on the Flagged page. Uses the earlier 6.6903 rate."),
    (r"^d646-", "D646 verification refresh", "Uses the earlier 6.6903 rate and prices $400,000 as eight wires."),
    (r"^schedule-|^final-verification", "S436 schedule", "Uses the earlier 6.6903 rate."),
    (r"^deep-", "Deep research", "Known problem: R05 on the Flagged page (2004 staging rule)."),
    (r"^cost|^cross-session|^us-fx-gain", "Cost model and cross-session review", "Uses the 9 November rates (6.6919 / 6.6924)."),
    (r"review|audit", "Independent reviews", "Other sessions' findings, kept as published."),
    (r"^docs/", "First docs site", "Earliest pass; not updated since."),
    (r".", "First editorial pages", "Earliest pass; partly corrected later."),
]


def discover_pages():
    found = sorted(p.name for p in ROOT.glob("*.html")) + sorted(f"docs/{p.name}" for p in (ROOT / "docs").glob("*.html"))
    return [p for p in found if p not in OWN_PAGES]


def page_archive():
    ctx = Ctx("archive")
    rows = []
    pages = discover_pages()
    for pattern, group, note in ARCHIVE_GROUPS:
        for p in list(pages):
            if re.search(pattern, p):
                pages.remove(p)
                text = (ROOT / p).read_text(encoding="utf-8", errors="replace")
                m = re.search(r"<title>(.*?)</title>", text, re.S)
                title = html.unescape(re.sub(r"\s+", " ", m.group(1)).strip()) if m else p
                rows.append((None, [f'<a href="../{p}">{esc(title[:90])}</a><br><span class="note">{esc(p)}</span>', esc(group), esc(note)]))
    body = f"""<h1>Archive: earlier passes</h1>
<p class="lead">{len(rows)} pages written by earlier and parallel sessions. They are kept unchanged so nothing is lost, but they use older rate snapshots and some contain errors listed on the <a href="flagged.html">Flagged page</a>. Where they disagree with this dashboard, the dashboard is the later reading.</p>
{table(["Page", "Layer", "Note"], rows, kind="nav")}
"""
    return render(ctx, "Archive", "Earlier research pages kept for reference.", body)


# ---------------------------------------------------------------------- decisions
DECISION_PILL = {"Answered": "ok", "Partly answered": "warn", "Open": "bad"}


def page_decisions():
    """Decision-readiness register: question, answer, what is missing, how to find it."""
    ctx = Ctx("decisions")
    n = len(decide.DECISIONS)
    counts = {k: sum(1 for d in decide.DECISIONS if d["status"] == k) for k in DECISION_PILL}
    parts = [f"""<h1>What has to be settled before you decide</h1>
<p class="lead">{n} questions, each marked with whether an official page answers it. {counts["Answered"]} are settled by an official source. {counts["Partly answered"]} depend on a document only you can produce. {counts["Open"]} cannot be settled from any public source — for those, the last two columns say what is missing and how to obtain it.</p>
<div class="banner">No row below states a fact about your account. The <b>What we know</b> column restates the text of the source it links. The <b>How to find out</b> column is procedural advice, not a sourced fact. Nothing here is a recommendation for your case; it is the list of things that decide which recommendation would be safe.</div>
<div class="kpis">
<div class="kpi"><b>{counts["Answered"]}</b><span>settled by an official page</span><span class="src"><a href="{ctx.page("sources")}">Sources</a></span></div>
<div class="kpi"><b>{counts["Partly answered"]}</b><span>rule settled, application needs your documents</span></div>
<div class="kpi"><b>{counts["Open"]}</b><span>cannot be answered from public sources</span><span class="src"><a href="{ctx.page("flagged")}">Flagged</a></span></div>
<div class="kpi"><b>{len(decide.DISCOVERY_PLAN)}</b><span>documents or questions that close them</span></div>
</div>"""]

    for sid, stage, note in decide.STAGES:
        rows = []
        for d in decide.DECISIONS:
            if d["stage"] != sid:
                continue
            fl = f' <span class="note">Open item {ctx.flags(d["flags"])}</span>' if d["flags"] else ""
            rows.append((d["id"], [
                f'<span class="id">{d["id"]}</span>{esc(d["question"])}',
                f'<span class="pill {DECISION_PILL[d["status"]]}">{esc(d["status"])}</span>',
                esc(d["known"]),
                esc(d["missing"]) if d["missing"] else '<span class="note">Nothing - the official page settles it.</span>',
                esc(d["find"]),
                ctx.src(d["src"]) + fl]))
        parts.append(f'<h2 id="stage-{sid}">{sid}. {esc(stage)}</h2>\n<p class="note">{esc(note)}</p>\n'
                     + table(["Question", "Can it be answered?", "What we know", "What is missing", "How to find out", "Source"], rows))

    plan = "".join(f"<li><b>{esc(step)}. {esc(item)}</b> — {esc(settles)} <span class=\"note\">Closes: {esc(rows)}</span></li>"
                   for step, item, settles, rows in decide.DISCOVERY_PLAN)
    asks = "".join(f"<li>{esc(q)}</li>" for q in decide.QUESTIONS_TO_ASK)
    parts.append(f"""<h2 id="how-to-close">How to close the open items</h2>
<p>In this order. Each document is useful on its own, and the first three decide whether the rest matters.</p>
<ol class="plain">{plan}</ol>
<h2 id="ask-the-bank">What to put to the bank in writing</h2>
<p>Ask these at the branch that holds the account, and keep the written answer. A branch cannot bind another branch, and an answer that contradicts the rules above should be checked against the official page it cites.</p>
<ul class="plain">{asks}</ul>
<h2 id="order">The order that follows from the register</h2>
<ol class="plain">
<li><b>Classify the money</b> (A01-A05). Until the origin is known, every route is a guess.</li>
<li><b>Fix the Chinese tax position</b> (C01-C08). The bank will not move money whose tax evidence is missing, and the tax is owed whether or not it moves.</li>
<li><b>Fix the U.S. reporting position</b> (D04-D07). The penalties for a missed report are larger than the bank's fee by orders of magnitude, and they do not depend on which Chinese route you use.</li>
<li><b>Then choose the route</b> (B01-B08) and price it (E01-E06). Route choice changes the bank cost by tenths of a percent; it does not change the Chinese income tax or the U.S. reports.</li>
</ol>
<h2 id="related">Other documents in this repository</h2>
<p>Listed so nothing is lost, not as corroboration: none of these is re-verified by this page. Where they disagree with it, the register above states the date of the reading it relies on.</p>
{table(["Document", "What it is", "Status here", "Link"],
       [(None, [f'<b>{esc(title)}</b><br><span class="note">{esc(what)}</span>', esc(note),
                '<span class="pill">not re-verified</span>',
                f'<a href="{esc(url)}" rel="noopener">open</a>'])
        for title, what, note, url in decide.RELATED_DOCS], kind="repo")}
<p class="note">Anything still open after these steps belongs on the <a href="{ctx.page("flagged")}">Flagged page</a>, not in a decision.</p>
""")
    return render(ctx, "Decide",
                  "The questions, answers and missing information that decide how RMB in a Chinese bank account can become USD, with how to find each missing item.",
                  "\n".join(parts))


# --------------------------------------------------------------------------- index
def page_index():
    ctx = Ctx("index")
    l01 = METHOD["L01"]
    c10, c400 = costs.row(l01, D(10000)), costs.row(l01, D(400000))
    g24 = costs.fx_gain(D(400000), "2024")
    g24p = g24 / D(400000) * 100
    sit = []
    for text, mid, answer in data.SITUATIONS:
        if mid:
            m = METHOD[mid]
            c = costs.row(m, D(100000))["known_cost_usd"]
            sit.append((None, [esc(text), f'{ctx.route(mid, mid + " · " + m["name"])}<br><span class="note">{esc(answer)}</span>',
                               usd(c), f'<a href="{ctx.page("steps")}#{mid}">Steps</a> · ' + ctx.src(m["src"][:2])]))
        else:
            sit.append((None, [esc(text), f'<span class="blank">no verified route</span><br><span class="note">{esc(answer)}</span>',
                               ctx.blank("U07"), ctx.src(["S04"])]))
    glance = []
    for mid in ("L03", "L01", "L07", "L11", "L10", "L09"):
        m = METHOD[mid]
        r10, r100, r400 = (costs.row(m, D(a)) for a in (10000, 100000, 400000))
        time = (f'{r400["units"]} trips' if m["model"] == "cash" else "1 wire" if r400["calendar_years"] == 1 else f'{r400["calendar_years"]} years')
        glance.append((None, [f'<span class="id">{mid}</span>{esc(m["name"])}', usd(r10["known_cost_usd"]), usd(r100["known_cost_usd"]),
                              usd(r400["known_cost_usd"]), time, ctx.src(cost_sources(m), short=False)]))
    high = [f for f in data.FLAGS if f[1] == "high"]
    hrows = [(None, [f'<a href="{ctx.page("flagged")}#{f[0]}">{f[0]}</a> {esc(f[2])}', esc(f[3]), ctx.src(f[5])]) for f in high]
    body = f"""<h1>Getting money out of a Chinese bank account and into US dollars</h1>
<p class="lead">For a U.S. citizen. Every figure links to the official page it was read from on 10 November 2026. Anything that could not be confirmed is left blank and listed under <a href="{ctx.page("flagged")}">Flagged</a>.</p>

<div class="grid">
<div class="card"><h3>1. The conversion itself is not what gets taxed</h3>
<p>No official source read here taxes converting RMB or wiring it out. What the bank asks for is proof that Chinese tax on the money was already dealt with. If it was not, that income tax is the large number: 3% to 45% on wages, 20% on dividends, rent and property gains. Bank-deposit interest is exempt.</p>
<p class="src">{ctx.src(["S17", "S04", "S25", "S26"])} · <a href="{ctx.page("tax")}">Tax page</a></p></div>
<div class="card"><h3>2. The bank's own cost is about half a percent or less</h3>
<p>{usd(c10["known_cost_usd"])} on $10,000 ({pct(c10["known_cost_pct"])}) and {usd(c400["known_cost_usd"])} on $400,000 ({pct(c400["known_cost_pct"])}) at Bank of China's published rate and fee. Fees taken by other banks along the way are not published and are left blank.</p>
<p class="src">{ctx.src(["S01", "S02"])} · <a href="{ctx.page("costs")}">Cost tables</a></p></div>
<div class="card"><h3>3. The U.S. side can cost more than the bank</h3>
<p>Selling RMB is a currency sale under U.S. tax law. RMB acquired at the 2024 average rate would show a gain of about {pct(g24p, 1)} today, or {usd(g24, False)} on $400,000, taxed at your ordinary rate unless the personal-transaction rule applies. Each missed report has its own penalty: up to $16,536 for an FBAR, $10,000 for Form 8938, and 5% of a gift per month for Form 3520.</p>
<p class="src">{ctx.src(["S27", "S28", "S31", "S29", "S33"])} · <a href="{ctx.page("tax")}#T10">Currency gain</a></p></div>
<div class="card"><h3>4. The route depends on where the money came from</h3>
<p>A U.S. passport holder does not get the $50,000 a year that Chinese citizens convert on ID alone. Each lawful route is tied to a kind of money: income earned in China, a home sale, an inheritance, or money you brought in yourself. Borrowing relatives' quotas, private swaps and crypto are prohibited, with fines of up to 30% of the amount and more in serious cases.</p>
<p class="src">{ctx.src(["S05", "S06", "S10", "S21"])} · <a href="{ctx.page("methods")}">All routes</a></p></div>
</div>

<div class="kpis">
<div class="kpi"><b>{usd(c10["known_cost_usd"])}</b><span>bank cost to convert and wire $10,000</span><span class="src">{ctx.src(["S01", "S02"], short=False)}</span></div>
<div class="kpi"><b>{usd(c400["known_cost_usd"])}</b><span>bank cost for $400,000 in one wire</span><span class="src">{ctx.src(["S01", "S02"], short=False)}</span></div>
<div class="kpi"><b>{data.RATE["ask"]}</b><span>RMB per dollar, Bank of China selling rate</span><span class="src">{ctx.src(["S01"], short=False)}</span></div>
<div class="kpi"><b>{len(data.FLAGS)}</b><span>open items, {len(high)} of them high</span><span class="src"><a href="{ctx.page("flagged")}">Flagged</a></span></div>
</div>

<h2>Start with where the money came from</h2>
<p>Find the line that matches. The cost shown is the known bank cost for $100,000.</p>
{table(["Your situation", "Route", "Bank cost at $100,000", "Next"], sit)}

<h2>Cost at a glance</h2>
{table(["Route", "$10,000", "$100,000", "$400,000", "Time for $400,000", "Source"], glance, cls="num routes")}
<p class="note">The dividend row includes 20% Chinese tax. ATM and cash rows cover only the published part of the cost. <a href="{ctx.page("costs")}">Every $10,000 step for every route</a>.</p>

<h2>What is still open</h2>
<p>These three decide the answer and cannot be settled from public sources. The full register - every question, whether an official page answers it, what is missing and how to obtain it - is on the <a href="{ctx.page("decisions")}">Decide page</a>.</p>
{table(["Open item", "Why it matters", "Source"], hrows)}

<h2>Sections</h2>
<div class="links">
<a href="{ctx.page("decisions")}"><b>Decide</b><span>{len(decide.DECISIONS)} questions to settle first, and how to close each one</span></a>
<a href="{ctx.page("methods")}"><b>Methods</b><span>11 lawful routes and 6 to avoid, with pros, cons and limits</span></a>
<a href="{ctx.page("costs")}"><b>Costs</b><span>$10,000 to $400,000 in $10,000 steps, per route</span></a>
<a href="{ctx.page("steps")}"><b>Steps</b><span>What to do, in order, for each route</span></a>
<a href="{ctx.page("tax")}"><b>Tax</b><span>Chinese tax, U.S. tax, reporting forms, penalties</span></a>
<a href="{ctx.page("flagged")}"><b>Flagged for review</b><span>Unverified values and repository problems</span></a>
<a href="{ctx.page("sources")}"><b>Sources</b><span>{len(data.SOURCES)} official pages with what each one says</span></a>
</div>
<p class="note">Earlier research passes are kept in the <a href="{ctx.page("archive")}">Archive</a>.</p>
"""
    return render(ctx, "Getting money out of China", "Source-checked guide to converting RMB in a Chinese bank account to US dollars lawfully: routes, bank cost from $10,000 to $400,000, tax and open questions.", body)


# ----------------------------------------------------------------------------- csv
def csv_text(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def urls(ids):
    return " ".join(SRC[i][3] for i in ids)


def data_files():
    f = {}
    f["e347_sources.csv"] = csv_text(
        ["id", "issuer", "title", "url", "read_on", "how_read", "what_it_establishes"],
        [[s[0], s[1], s[2], s[3], data.SNAPSHOT_DATE, s[4], s[5]] for s in data.SOURCES])
    f["e347_methods.csv"] = csv_text(
        ["id", "status", "route", "use_it_when", "limit", "advantages", "drawbacks", "tax", "cost_model", "source_ids", "source_urls", "flags"],
        [[m["id"], m["status"], m["name"], m["fits"], m["limit"], m["pros"], m["cons"], m["tax"], m["model"],
          "|".join(m["src"]), urls(m["src"]), "|".join(m["flags"])] for m in data.METHODS])
    f["e347_steps.csv"] = csv_text(
        ["method_id", "step", "action", "source_ids", "source_urls"],
        [[mid, n, text, "|".join(src), urls(src)] for mid, steps in data.STEPS.items() for n, (text, src) in enumerate(steps, 1)])
    f["e347_facts.csv"] = csv_text(
        ["id", "group", "item", "rate_or_amount", "meaning", "source_ids", "source_urls", "flags"],
        [[t[0], t[1], t[2], t[4] or "", t[3], "|".join(t[5]), urls(t[5]), "|".join(t[6])] for t in data.TAX_ROWS])
    f["b2d_decisions.csv"] = csv_text(
        ["id", "stage", "question", "status", "what_we_know", "source_ids", "source_urls",
         "what_is_missing", "how_to_find_out", "flags"],
        [[d["id"], d["stage"], d["question"], d["status"], d["known"], "|".join(d["src"]), urls(d["src"]),
          d["missing"], d["find"], "|".join(d["flags"])] for d in decide.DECISIONS])
    f["e347_flags.csv"] = csv_text(
        ["id", "severity", "item", "why", "what_would_settle_it", "source_ids", "source_urls"],
        [[x[0], x[1], x[2], x[3], x[4], "|".join(x[5]), urls(x[5])] for x in data.FLAGS])
    rows = []
    blank_flag = {"fx_wire": "U04", "property": "U01|U04", "wire_only": "U04", "quota": "U04|U15", "atm": "U13|U15",
                  "cash": "U14", "dividend": "U04|U06", "blank": "U09"}
    fmt = lambda v: "" if v is None else str(q(v))
    for r in costs.grid():
        m = METHOD[r["method_id"]]
        rows.append([r["method_id"], int(r["amount_usd"]), r["model"], r["units"] if r["units"] is not None else "", r["units_label"],
                     r["calendar_years"] if r["calendar_years"] is not None else "", fmt(r["spread_usd"]), fmt(r["fee_usd"]),
                     fmt(r["tax_usd"]), fmt(r["known_cost_usd"]),
                     "" if r["known_cost_pct"] is None else str(q(r["known_cost_pct"], D("0.0001"))),
                     fmt(r["rmb_debited"]), blank_flag[r["model"]], "|".join(cost_sources(m)), urls(cost_sources(m))])
    f["e347_costs.csv"] = csv_text(
        ["method_id", "amount_usd", "model", "units", "units_label", "calendar_years", "spread_usd", "fee_usd", "tax_usd",
         "known_cost_usd", "known_cost_pct", "rmb_debited", "not_included_flags", "source_ids", "source_urls"], rows)
    years = sorted(data.RATE["irs_avg"])
    f["e347_fx_gain.csv"] = csv_text(
        ["amount_usd"] + [f"gain_if_acquired_{y}_usd" for y in years] + ["source_urls"],
        [[int(a)] + [str(q(costs.fx_gain(a, y))) for y in years] + [urls(["S28", "S27", "S01"])] for a in data.AMOUNTS])
    return f


def outputs():
    out = {ROOT / "index.html": page_index()}
    for key, fn in (("decisions", page_decisions), ("methods", page_methods), ("costs", page_costs), ("steps", page_steps),
                    ("tax", page_tax), ("flagged", page_flagged), ("sources", page_sources), ("archive", page_archive)):
        out[OUT / f"{key}.html"] = fn()
    for name, text in data_files().items():
        out[ROOT / "data" / name] = text
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stale = []
    for path, text in outputs().items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            if args.check and path.name == "archive.html" and current is not None:
                continue
            stale.append(str(path.relative_to(ROOT)))
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check:
        if stale:
            print("STALE: " + ", ".join(stale) + " — run python3 scripts/e347_build.py")
            return 1
        print("OK — e347 dashboard files are up to date.")
        return 0
    print(f"e347 build: {len(outputs())} files, {len(stale)} changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
