#!/usr/bin/env python3
"""Build the G8D8 layer: g8d8-*.html, data/g8d8_*.csv, research/g8d8-executive-summary.md.

    python3 scripts/g8d8_build.py            write everything
    python3 scripts/g8d8_build.py --check    fail if a generated file on disk is stale
"""
import csv
import html
import io
import math
import statistics
import sys
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g8d8_data as d  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = {s[0]: s for s in d.SOURCES}
BANK = {b["id"]: b for b in d.BANKS}
FLAG = {f[0]: f for f in d.FLAGS}
esc = html.escape
NAV = [("summary", "Summary"), ("banks", "Banks"), ("receiving", "U.S. side"), ("channels", "Other channels"),
       ("enforcement", "Enforcement"), ("closures", "Flag closures"), ("flagged", "Flagged for Review"), ("sources", "Sources")]
SHORT = {"Bank of China": "BOC", "Agricultural Bank of China": "ABC", "China Construction Bank": "CCB", "China Merchants Bank": "CMB",
         "Industrial and Commercial Bank of China": "ICBC", "Bank of Communications": "BoCom", "SAFE (Beijing branch page)": "SAFE",
         "Internal Revenue Service": "IRS", "Ministry of Finance (PRC)": "MOF", "State Taxation Administration (Shanghai)": "STA",
         "State Taxation Administration (Guizhou)": "STA", "U.S. Government Publishing Office": "US Code", "JPMorgan Chase": "Chase",
         "Bank of America": "BofA", "Charles Schwab": "Schwab"}
MODE = {"full": "Whole page opened", "excerpt": "Excerpt of the official page", "unreadable": "Opened; value not in the page text"}


def q(x, places="0.01"):
    return D(x).quantize(D(places), rounding=ROUND_HALF_UP)


def usd(x):
    return f"${q(x):,.2f}"


def fee_cny(bank, principal_cny):
    return min(max(principal_cny * bank["rate"], bank["min"]), bank["max"]) + bank["cable"]


YARD = BANK[d.YARDSTICK_BANK]["ask"] / 100


def ladder_row(bank, amount):
    """Cost of buying `amount` USD with RMB and wiring it once. None where an input was not read."""
    r = dict(amount=amount, bank=bank["id"], fee_cny_y=None, fee_usd_y=None, ask=None, mid=None, fee_cny=None, fee_usd=None,
             spread_usd=None, total=None, pct=None)
    if bank["rate"] is None:
        return r
    r["fee_cny_y"] = fee_cny(bank, amount * YARD)
    r["fee_usd_y"] = r["fee_cny_y"] / YARD
    if bank["ask"] is not None:
        ask, bid = bank["ask"] / 100, bank["bid"] / 100
        mid = (ask + bid) / 2
        r.update(ask=ask, mid=mid, fee_cny=fee_cny(bank, amount * ask))
        r["fee_usd"] = r["fee_cny"] / ask
        r["spread_usd"] = amount * (ask - mid) / ask
        r["total"] = q(r["fee_usd"]) + q(r["spread_usd"])  # the two published components add up to the cent
        r["pct"] = r["total"] / amount * 100
    return r


LADDER = {(b["id"], a): ladder_row(b, a) for b in d.BANKS for a in d.AMOUNTS}


def case_ratio(c):
    return D(c[8]) / D(c[7])  # RMB of fine per USD moved


def stats(kind, violation):
    xs = sorted(case_ratio(c) for c in d.CASES if c[3] in kind and c[4] == violation)
    return dict(n=len(xs), lo=xs[0], med=D(str(statistics.median(xs))), hi=xs[-1])


# ----------------------------------------------------------------------------- html helpers
def src(ids):
    out = []
    for i in ids:
        s = SRC[i]
        out.append(f'<a href="{esc(s[4])}" rel="noopener" title="{esc(s[3])}">{i} {esc(SHORT.get(s[1], s[1]))}</a>')
    return " ".join(out)


def flags(ids):
    return " ".join(f'<a class="flag" href="g8d8-flagged.html#{i}">{i}</a>' for i in ids)


def blank(flag):
    return f'<span class="blank">not verified</span> <a class="flag" href="g8d8-flagged.html#{flag}">{flag}</a>'


def table(head, rows, cls="stack", caption=None):
    """rows: (row_id or None, [cells]); the last column is always the official source link."""
    out = [f'<div class="tbl"><table class="{cls}" data-kind="data">']
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead><tbody>")
    for rid, cells in rows:
        tds = "".join(f'<td data-label="{esc(head[i])}"{" class=src" if i == len(cells) - 1 else ""}>{c}</td>' for i, c in enumerate(cells))
        out.append(f'<tr{f" id={rid}" if rid else ""}>{tds}</tr>')
    out.append("</tbody></table></div>")
    return "\n".join(out)


def render(key, title, description, body):
    nav = "".join(f'<a href="g8d8-{k}.html"{" aria-current=page" if k == key else ""}>{label}</a>' for k, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="g8d8">
<meta name="description" content="{esc(description)}">
<title>{esc(title)} · China money</title>
<link rel="stylesheet" href="assets/g8d8.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">China money<small>new evidence, 11 November 2026</small></a>
<nav class="nav" aria-label="Sections">{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>Read on {d.FETCH_DATE} (UTC) from each issuer's own site. Rates: Bank of China board published {esc(BANK["BOC"]["stamp"])}.</p>
<p>General research from public pages. It is not legal, tax or banking advice and makes no finding about any person's case.</p>
<p><a href="index.html">Main dashboard</a> · <a href="g8d8-flagged.html">Flagged for Review</a> · <a href="g8d8-sources.html">Sources</a> · built by <code>scripts/g8d8_build.py</code></p>
</div></footer>
</body>
</html>
"""


# ----------------------------------------------------------------------------- pages
def page_banks():
    trows = []
    for b in d.BANKS:
        if b["rate"] is None:
            f = b["flags"][0]
            trows.append((b["id"], [esc(b["name"]), blank(f), blank(f), blank(f), blank(f), esc(SRC[b["tariff_src"]][6]) or "none shown", src([b["tariff_src"]])]))
        else:
            fl = flags([x for x in b["flags"] if x in ("F03",)])
            trows.append((b["id"], [esc(b["name"]), f'{q(b["rate"] * 1000, "0.1")}‰ of the amount', f'¥{b["min"]}', f'¥{b["max"]}', f'¥{b["cable"]}',
                                    (esc(SRC[b["tariff_src"]][6]) or "none shown") + (" " + fl if fl else ""), src([b["tariff_src"]])]))
    brows = []
    for b in d.BANKS:
        if b["ask"] is None:
            s = [b["board_src"]] if b["board_src"] else [b["tariff_src"]]
            brows.append((None, [esc(b["name"]), blank("F05"), blank("F05"), blank("F05"), blank("F05"), "", src(s)]))
        else:
            ask, bid = b["ask"] / 100, b["bid"] / 100
            mid = (ask + bid) / 2
            fl = flags([x for x in b["flags"] if x == "F04"])
            brows.append((None, [esc(b["name"]), f"{ask}", f"{bid}", f"{mid}", f'{q((ask - mid) / ask * 100, "0.0001")}%',
                                 esc(b["stamp"]) + (" " + fl if fl else ""), src([b["board_src"]])]))
    own = [b for b in d.BANKS if b["ask"] is not None]
    lrows = []
    for a in d.AMOUNTS:
        cells = [f"${a:,.0f}"]
        for b in own:
            r = LADDER[(b["id"], a)]
            cells += [usd(r["total"]), f'{q(r["pct"])}%']
        cells.append(src([x for b in own for x in (b["tariff_src"], b["board_src"])]))
        lrows.append((None, cells))
    priced = [b for b in d.BANKS if b["rate"] is not None]
    frows = []
    for a in d.AMOUNTS:
        frows.append((None, [f"${a:,.0f}"] + [usd(LADDER[(b["id"], a)]["fee_usd_y"]) for b in priced] + [src([b["tariff_src"] for b in priced])]))
    pc = [
        ("BOC", "Rate board is published with a time stamp and was readable. Narrowest spread of the two boards read.", "Cable fee of ¥150 is the higher of the two cable levels."),
        ("ABC", "Lowest fee cap (¥200) and the lower cable fee (¥80).", "Rate board could not be read, so the spread is unknown."),
        ("CCB", "Low minimum (¥20) and the lower cable fee (¥80). Online requests accepted at any hour.", "The fee text comes from a 2016 branch page. Rate board not read."),
        ("CMB", "Publishes how each charge option works, including the OUR pre-charge.", "Highest minimum (¥100) and cap (¥1,000). Spread on the board read was slightly wider than Bank of China's."),
    ]
    prows = [(None, [esc(BANK[i]["name"]), esc(p), esc(c), src([BANK[i]["tariff_src"]] + ([BANK[i]["board_src"]] if BANK[i]["board_src"] else []))]) for i, p, c in pc]
    srows = [(None, [str(n), esc(t) + (' See <a href="dashboard/methods.html">Methods</a> and <a href="dashboard/steps.html">Steps</a>.' if n == 1 else ""), src(s)]) for n, t, s, _ in d.BANK_STEPS]
    b400 = {b["id"]: LADDER[(b["id"], D(400000))] for b in d.BANKS}
    fees400 = sorted((b400[b["id"]]["fee_usd_y"], b["name"]) for b in priced)
    body = f"""<h1>Chinese banks compared</h1>
<p class="lead">At $400,000 in one wire, the published wire fee runs from {usd(fees400[0][0])} ({esc(fees400[0][1])}) to {usd(fees400[-1][0])} ({esc(fees400[-1][1])}). The exchange spread is larger: {usd(b400["BOC"]["spread_usd"])} at Bank of China and {usd(b400["CMB"]["spread_usd"])} at China Merchants Bank on the boards read. Ask for a better rate before comparing fees.</p>

<h2>Cost to convert and wire once, at each bank's own board</h2>
<p>Exchange spread (selling rate against the midpoint of buying and selling) plus the wire fee and cable fee. Only the two banks whose boards could be read are priced in full. Fees charged by other banks along the route are not included {flags(["F10"])}.</p>
{table(["Amount"] + [x for b in own for x in (b["id"] + " cost", b["id"] + " %")] + ["Source"], lrows, cls="num")}

<h2>Wire fee and cable fee only, four banks</h2>
<p>Each bank's published tariff applied to the same RMB amount and converted at one yardstick rate ({YARD} RMB per dollar, Bank of China's selling rate) {flags(["F06"])}. The exchange spread at Agricultural Bank and Construction Bank is blank {flags(["F05"])}.</p>
{table(["Amount"] + [b["id"] for b in priced] + ["Source"], frows, cls="num")}

<h2>Tariffs as published</h2>
{table(["Bank", "Fee", "Minimum", "Cap per wire", "Cable fee", "Date on page", "Source"], trows)}

<h2>Rate boards read today (RMB per U.S. dollar)</h2>
{table(["Bank", "Sells dollars at", "Buys dollars at", "Midpoint", "Half-spread", "Stamp on page", "Source"], brows)}

<h2>Advantages and drawbacks</h2>
{table(["Bank", "Advantage", "Drawback", "Source"], prows)}

<h2>Steps</h2>
{table(["Step", "What to do", "Source"], srows)}
"""
    return render("banks", "Chinese banks compared", "Official wire tariffs and rate boards of Chinese banks, with cost in $10,000 steps.", body)


def page_receiving():
    rrows = [(None, [esc(n), esc(fee) if fee else blank(fl[0]), esc(what) + (" " + flags(fl) if fee and fl else ""), esc(note), src(s)]) for n, fee, what, s, fl, note in d.US_RECEIVING]
    crows = [(None, [esc(n), esc(how), esc(cost) + (" " + flags(fl) if fl else ""), src(s)]) for n, how, cost, s, fl in d.CHARGE_OPTIONS]
    erows = []
    for a in (10000, 50000, 100000, 200000, 400000):
        r = LADDER[("BOC", D(a))]
        erows.append((None, [f"${a:,.0f}", usd(r["total"]), "$15.00", usd(r["total"] + 15), f'{q((r["total"] + 15) / a * 100)}%', blank("F10"), src(["G01", "G02", "G14", "G15"])]))
    body = f"""<h1>The U.S. receiving side</h1>
<p class="lead">Bank of America and Chase each publish $15 to receive an international wire. Chase's $0 case covers wires that were sent through Chase itself. Add $15 to the bank cost; what banks along the route deduct is not published.</p>

<h2>Bank cost plus the receiving fee</h2>
<p>Bank of China cost from the <a href="g8d8-banks.html">Banks</a> page, plus $15 at Bank of America or Chase.</p>
{table(["Amount", "Chinese bank cost", "Receiving fee", "Total", "Share of amount", "Deducted along the route", "Source"], erows, cls="num")}

<h2>Fee to receive an international wire</h2>
{table(["Institution", "Fee", "What the page says", "Note", "Source"], rrows)}

<h2>Who pays the fees: the three charge options</h2>
<p>As published by China Merchants Bank. Other banks' wording was not read.</p>
{table(["Option", "How it works", "Effect on cost", "Source"], crows)}
"""
    return render("receiving", "The U.S. receiving side", "Published fees for receiving an international wire in the United States.", body)


def page_channels():
    rows = []
    for c in d.CHANNELS:
        rows.append((c["id"], [f'<strong>{esc(c["name"])}</strong><br><span class="note">{esc(c["status"])}</span>', esc(c["who"]),
                               esc(c["limit"]) if c["limit"] else blank(c["flags"][0]), esc(c["delivery"]), blank(c["flags"][0]),
                               esc(c["pros"]), esc(c["cons"]), src(c["src"])]))
    wrows = []
    for a in d.AMOUNTS:
        cny = a * YARD
        n = (cny / 300000).to_integral_value(rounding=ROUND_CEILING)
        wrows.append((None, [f"${a:,.0f}", f"¥{q(cny, '1'):,.0f}", str(n), blank("F07"), src(["G18", "G02"])]))
    srows = [(None, [esc(next(c["name"] for c in d.CHANNELS if c["id"] == cid)), str(n), esc(t), src(s)]) for cid, n, t, s in d.CHANNEL_STEPS]
    body = f"""<h1>Channels other than a bank wire</h1>
<p class="lead">Two providers publish terms for sending money out of mainland China. Wise sends a foreigner's taxed salary to an account in the same name, up to 300,000 CNY per transfer. Western Union pays out cash abroad through partner banks. Neither price could be read, so every cost cell is blank.</p>

<h2>What each channel offers</h2>
{table(["Channel", "Who can use it", "Limit", "Where the money lands", "Price", "Advantages", "Drawbacks", "Source"], rows)}

<h2>Wise: transfers needed for each amount</h2>
<p>RMB needed at {YARD} RMB per dollar (Bank of China selling rate, used only to size the transfers), divided into transfers of 300,000 CNY. The overall limit, set by after-tax salary, may be lower than the amount.</p>
{table(["Amount", "RMB needed", "Transfers of 300,000 CNY", "Fee and rate", "Source"], wrows, cls="num")}

<h2>Western Union: cost by amount</h2>
<p>No fee and no amount limit are on the provider's page, so no table can be built {flags(["F08"])}.</p>

<h2>Steps</h2>
{table(["Channel", "Step", "What to do", "Source"], srows)}

<h2>Not channels</h2>
<p>Underground banks, private swaps and splitting a transfer across other people's quotas are prohibited. The fines SAFE has published for them are on the <a href="g8d8-enforcement.html">Enforcement</a> page.</p>
"""
    return render("channels", "Channels other than a bank wire", "Wise and Western Union terms for sending money out of mainland China.", body)


def pct_yard(ratio):
    return q(ratio / YARD * 100, "0.1")


def page_enforcement():
    su, ss = stats("IO", "U"), stats("IO", "S")
    srows = [
        (None, ["Individuals who used an underground bank", str(su["n"]), f'¥{q(su["lo"], "0.001")} to ¥{q(su["hi"], "0.001")}', f'¥{q(su["med"], "0.001")}',
                f'{pct_yard(su["lo"])}% to {pct_yard(su["hi"])}%', src(["G10", "G12", "G13"])]),
        (None, ["Individuals who split a transfer across other people's quotas", str(ss["n"]), f'¥{q(ss["lo"], "0.001")} to ¥{q(ss["hi"], "0.001")}', f'¥{q(ss["med"], "0.001")}',
                f'{pct_yard(ss["lo"])}% to {pct_yard(ss["hi"])}%', src(["G11"])]),
    ]
    rows = []
    for c in sorted(d.CASES, key=lambda c: (c[3] == "C", -case_ratio(c))):
        s, n, party, kind, vio, period, deals, amt, fine = c
        r = case_ratio(c)
        what = VIO_SHORT[vio] + (f", {deals} deals" if deals else "")
        rows.append((None, [f'{esc(party)}<br><span class="note">{d.PARTY[kind]} · case {n}</span>', esc(what) + f'<br><span class="note">{esc(period)}</span>',
                            f"${D(amt) * 10000:,.0f}", f"¥{D(fine) * 10000:,.0f}", f'¥{q(r, "0.001")}', f"{pct_yard(r)}%", src([s])]))
    b = LADDER[("BOC", D(400000))]
    body = f"""<h1>What SAFE has fined</h1>
<p class="lead">In four published bulletins, {su["n"]} individuals who bought or sold foreign exchange through an underground bank were fined a median of ¥{q(su["med"], "0.001")} for every dollar moved, about {pct_yard(su["med"])}% at today's rate. The lawful bank cost on $400,000 is {q(b["pct"])}%. Every underground-bank case also went on the central bank's credit record.</p>

<h2>Fine per dollar moved</h2>
<p>The bulletins print the amount in U.S. dollars and the fine in RMB. The percentage converts at {YARD} RMB per dollar as a yardstick {flags(["F15"])}. The legal ceiling for ordinary cases is 30% of the amount.</p>
{table(["Group", "Cases", "Fine per dollar", "Median", "As a share of the amount", "Source"], srows)}

<h2>All {len(d.CASES)} cases</h2>
<p>Individuals first, largest fine per dollar first.</p>
{table(["Party", "What they did", "Amount", "Fine", "Fine per dollar", "Share", "Source"], rows)}
"""
    return render("enforcement", "What SAFE has fined", "Published SAFE enforcement cases: amount, fine and fine per dollar.", body)


VIO_SHORT = {"U": "Underground bank", "S": "Split across other people's quotas", "T": "False trade background"}


def page_closures():
    nv = {k: sum(1 for c in d.CLOSURES if c[2].startswith(k)) for k in ("Closed", "Partly", "Still")}
    rows = []
    for fid, item, verdict, found, s, fl in d.CLOSURES:
        cls = "ok" if verdict.startswith("Closed") else "part" if verdict.startswith("Partly") else "open"
        rows.append((fid, [f'<a href="dashboard/flagged.html#{fid}">{fid}</a> {esc(item)}', f'<span class="pill {cls}">{esc(verdict)}</span>', esc(found),
                           flags(fl) if fl else "nothing", src(s)]))
    body = f"""<h1>Open items on the main dashboard: what was found</h1>
<p class="lead">{len(d.CLOSURES)} open items from the main dashboard's <a href="dashboard/flagged.html">Flagged page</a> were taken to primary texts: {nv["Closed"]} closed, {nv["Partly"]} partly closed, {nv["Still"]} still open. The main dashboard was not edited; each result is a request to its owner.</p>
{table(["Open item", "Verdict", "What was found", "Still blank", "Source"], rows)}

<h2>Requests logged for the main dashboard's owner</h2>
<ul>
<li>Route L09 (dividend): add the treaty cap of 10 percent next to the statutory 20 percent, with the residence condition {flags(["F16", "F11"])}.</li>
<li>Flag U08: cite the Ministry of Finance statement {flags(["F12"])}.</li>
<li>Flag U12: cite the statute for the 50 percent alternative.</li>
<li>Flags U03, U04, U17 and U18: link to this layer's Banks, U.S. side and Other channels pages.</li>
</ul>
"""
    return render("closures", "Open items: what was found", "Attempts to close open items on the main dashboard with primary texts.", body)


def page_flagged():
    order = {"high": 0, "medium": 1, "low": 2}
    rows = [(f[0], [f'<span class="id">{f[0]}</span> {esc(f[2])}', f'<span class="pill {f[1]}">{f[1]}</span>', esc(f[3]), esc(f[4]), src(f[5])])
            for f in sorted(d.FLAGS, key=lambda f: (order[f[1]], f[0]))]
    n = {k: sum(1 for f in d.FLAGS if f[1] == k) for k in order}
    body = f"""<h1>Flagged for Review</h1>
<p class="lead">{len(d.FLAGS)} items from this layer: {n["high"]} high, {n["medium"]} medium, {n["low"]} low. A blank cell anywhere on these pages links to its entry here. Nothing below blocks the rest of the site.</p>
{table(["Item", "Severity", "Why it is flagged", "What would settle it", "Source"], rows)}
<p>The main dashboard keeps its own list on its <a href="dashboard/flagged.html">Flagged page</a>.</p>
"""
    return render("flagged", "Flagged for Review", "Unverified values and irregularities found in this layer.", body)


def page_sources():
    rows = [(s[0], [f'<span class="id">{s[0]}</span> {esc(s[1])}', esc(s[3]) + f'<br><span class="note">{esc(s[2])}</span>', MODE[s[5]], esc(s[6]) or "none shown",
                    f'<span lang="{"zh" if any(ord(ch) > 0x2E80 for ch in s[7]) else "en"}">{esc(s[7])}</span>', f'<a href="{esc(s[4])}" rel="noopener">{esc(s[4].split("/")[2])}</a>'])
            for s in d.SOURCES]
    n = {k: sum(1 for s in d.SOURCES if s[5] == k) for k in MODE}
    body = f"""<h1>Sources</h1>
<p class="lead">{len(d.SOURCES)} pages on the issuers' own sites, all opened on {d.FETCH_DATE} (UTC): {n["full"]} read in full, {n["excerpt"]} read as excerpts, {n["unreadable"]} opened without yielding the value. Quotations are verbatim.</p>
{table(["Issuer", "Page", "How it was read", "Date on page", "What it says", "Link"], rows)}
"""
    return render("sources", "Sources", "Official pages read for this layer, with verbatim quotations.", body)


def page_summary():
    b400 = {b["id"]: LADDER[(b["id"], D(400000))] for b in d.BANKS}
    priced = [b for b in d.BANKS if b["rate"] is not None]
    fees = sorted(b400[b["id"]]["fee_usd_y"] for b in priced)
    su, ss = stats("IO", "U"), stats("IO", "S")
    crow = []
    for fid, item, verdict, found, s, fl in d.CLOSURES:
        cls = "ok" if verdict.startswith("Closed") else "part" if verdict.startswith("Partly") else "open"
        crow.append((None, [f'<a href="g8d8-closures.html#{fid}">{fid}</a> {esc(item)}', f'<span class="pill {cls}">{esc(verdict)}</span>', esc(found.split(". ")[0] + "."), src(s)]))
    qrow = [(None, [esc(a), esc(b), esc(c), src(s)]) for a, b, c, s in d.QUESTIONS]
    glance = []
    for a in (10000, 50000, 100000, 200000, 400000):
        r1, r2 = LADDER[("BOC", D(a))], LADDER[("CMB", D(a))]
        glance.append((None, [f"${a:,.0f}", usd(r1["total"]), usd(r2["total"]), usd(r1["total"] + 15), src(["G01", "G02", "G05", "G06", "G14"])]))
    body = f"""<h1>New evidence: other banks, the U.S. side, other channels, and what SAFE fines</h1>
<p class="lead">Added on 11 November 2026 to the <a href="index.html">main dashboard</a>. Every figure was read today from the issuer's own site and links to it. Values that could not be read are blank and listed under <a href="g8d8-flagged.html">Flagged for Review</a>.</p>

<div class="grid">
<div class="card"><h3>1. The rate matters more than the bank's fee</h3><p class="big">{usd(b400["BOC"]["spread_usd"])}</p><p>exchange spread on $400,000 at Bank of China, against a wire fee of {usd(fees[0])} to {usd(fees[-1])} across four banks. <a href="g8d8-banks.html">Banks</a></p></div>
<div class="card"><h3>2. Add $15 on the U.S. side</h3><p class="big">$15</p><p>to receive an international wire at Bank of America or Chase. Fees taken along the route are not published. <a href="g8d8-receiving.html">U.S. side</a></p></div>
<div class="card"><h3>3. A second lawful channel for taxed salary</h3><p class="big">300,000 CNY</p><p>per transfer through Wise, to your own account abroad, limited to after-tax salary. Its price was not read. <a href="g8d8-channels.html">Other channels</a></p></div>
<div class="card"><h3>4. The prohibited routes cost far more</h3><p class="big">about {pct_yard(su["med"])}%</p><p>median published fine for individuals who used an underground bank, against {q(b400["BOC"]["pct"])}% for a lawful $400,000 bank wire. <a href="g8d8-enforcement.html">Enforcement</a></p></div>
</div>

<h2>Cost at a glance</h2>
<p>Convert and wire once. Full figures for every $10,000 step are on the <a href="g8d8-banks.html">Banks</a> page.</p>
{table(["Amount", "Bank of China", "China Merchants Bank", "Bank of China plus $15 receiving fee", "Source"], glance, cls="num")}

<h2>What this settles on the main dashboard</h2>
{table(["Open item", "Verdict", "Finding", "Source"], crow)}

<h2>Questions this evidence raises</h2>
<p>These add to the main question list; they do not replace it.</p>
{table(["Question", "Why it matters", "How to find out", "Source"], qrow)}

<h2>Sections</h2>
<div class="links">
<a href="g8d8-banks.html"><strong>Banks</strong> Four tariffs, two rate boards, cost in $10,000 steps</a>
<a href="g8d8-receiving.html"><strong>U.S. side</strong> Receiving fees and the three charge options</a>
<a href="g8d8-channels.html"><strong>Other channels</strong> Wise and Western Union: who, limits, steps</a>
<a href="g8d8-enforcement.html"><strong>Enforcement</strong> {len(d.CASES)} SAFE cases with fine per dollar</a>
<a href="g8d8-closures.html"><strong>Flag closures</strong> {len(d.CLOSURES)} open items taken to primary texts</a>
<a href="g8d8-flagged.html"><strong>Flagged for Review</strong> {len(d.FLAGS)} unverified values and irregularities</a>
<a href="g8d8-sources.html"><strong>Sources</strong> {len(d.SOURCES)} official pages with quotations</a>
</div>
"""
    return render("summary", "New evidence, 11 November 2026", "Other banks, the U.S. receiving side, other channels and SAFE enforcement, read on 11 November 2026.", body)


# ----------------------------------------------------------------------------- csv + markdown
def to_csv(head, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(head)
    w.writerows(rows)
    return buf.getvalue()


def urls(ids):
    return " ".join(SRC[i][4] for i in ids)


def n(x, places="0.01"):
    return "" if x is None else str(q(x, places))


def build_csvs():
    out = {}
    out["g8d8_sources.csv"] = to_csv(["id", "issuer", "kind", "title", "url", "read_mode", "date_on_page", "what_it_says", "fetched_utc"],
                                     [list(s) + [d.FETCH_DATE] for s in d.SOURCES])
    out["g8d8_banks.csv"] = to_csv(["bank", "name", "fee_rate_per_mille", "min_cny", "max_cny", "cable_cny", "note", "source_url", "flags"],
                                   [[b["id"], b["name"], n(b["rate"] * 1000, "0.1") if b["rate"] is not None else "", b["min"] or "", b["max"] or "", b["cable"] or "",
                                     b["note"], urls([b["tariff_src"]]), "|".join(b["flags"])] for b in d.BANKS])
    out["g8d8_bank_boards.csv"] = to_csv(["bank", "sell_per_100_usd", "buy_per_100_usd", "stamp_on_page", "source_url", "flags"],
                                         [[b["id"], b["ask"] or "", b["bid"] or "", b["stamp"], urls([b["board_src"]]) if b["board_src"] else "",
                                           "|".join(f for f in b["flags"] if f in ("F04", "F05"))] for b in d.BANKS])
    rows = []
    for b in d.BANKS:
        for a in d.AMOUNTS:
            r = LADDER[(b["id"], a)]
            rows.append([a, b["id"], YARD, n(r["fee_cny_y"]), n(r["fee_usd_y"]), r["ask"] or "", r["mid"] or "", n(r["fee_cny"]), n(r["fee_usd"]),
                         n(r["spread_usd"]), n(r["total"]), n(r["pct"], "0.0001"),
                         urls([b["tariff_src"]] + ([b["board_src"]] if b["board_src"] else [])), "|".join(b["flags"])])
    out["g8d8_bank_ladder.csv"] = to_csv(["amount_usd", "bank", "yardstick_cny_per_usd", "fee_cny_at_yardstick", "fee_usd_at_yardstick", "own_sell_rate", "own_midpoint",
                                          "fee_cny_own_rate", "fee_usd_own_rate", "spread_usd", "total_usd", "total_pct", "source_urls", "flags"], rows)
    out["g8d8_us_receiving.csv"] = to_csv(["institution", "incoming_wire_fee", "what_the_page_says", "note", "source_urls", "flags"],
                                          [[a, fee or "", what, note, urls(s), "|".join(fl)] for a, fee, what, s, fl, note in d.US_RECEIVING])
    out["g8d8_channels.csv"] = to_csv(["id", "channel", "status", "who", "limit", "delivery", "price", "advantages", "drawbacks", "source_urls", "flags"],
                                      [[c["id"], c["name"], c["status"], c["who"], c["limit"] or "", c["delivery"], c["price"] or "", c["pros"], c["cons"], urls(c["src"]),
                                        "|".join(c["flags"])] for c in d.CHANNELS])
    out["g8d8_channel_steps.csv"] = to_csv(["channel", "step", "what_to_do", "source_urls"],
                                           [[c, s, t, urls(x)] for c, s, t, x in d.CHANNEL_STEPS] + [["BANK", s, t, urls(x)] for s, t, x, _ in d.BANK_STEPS])
    out["g8d8_enforcement.csv"] = to_csv(["bulletin_url", "case_no", "party", "party_type", "violation", "period", "deals", "amount_usd", "fine_cny",
                                          "fine_cny_per_usd", "fine_pct_at_yardstick"],
                                         [[SRC[c[0]][4], c[1], c[2], d.PARTY[c[3]], d.VIOLATION[c[4]], c[5], c[6] or "", int(D(c[7]) * 10000), int(D(c[8]) * 10000),
                                           n(case_ratio(c), "0.001"), str(pct_yard(case_ratio(c)))] for c in d.CASES])
    out["g8d8_flag_closures.csv"] = to_csv(["main_dashboard_flag", "item", "verdict", "what_was_found", "source_urls", "still_flagged"],
                                           [[a, b, c, e, urls(s), "|".join(fl)] for a, b, c, e, s, fl in d.CLOSURES])
    out["g8d8_flags.csv"] = to_csv(["id", "severity", "item", "why", "what_would_settle_it", "source_urls"], [list(f[:5]) + [urls(f[5])] for f in d.FLAGS])
    return out


def summary_md():
    b = {x["id"]: LADDER[(x["id"], D(400000))] for x in d.BANKS}
    su, ss = stats("IO", "U"), stats("IO", "S")
    return f"""# New evidence, 11 November 2026 (G8D8)

Generated by `scripts/g8d8_build.py` from `scripts/g8d8_data.py`. Read on {d.FETCH_DATE} (UTC) by {d.SESSION}. Pages: `g8d8-summary.html` and seven subpages.
This adds to the main dashboard (`index.html`, `dashboard/`); it does not replace it and edits none of its files.

## Findings

1. **The exchange rate matters more than the bank's fee.** On $400,000 in one wire the exchange spread is {usd(b["BOC"]["spread_usd"])} at Bank of China and {usd(b["CMB"]["spread_usd"])} at China Merchants Bank. The wire fee is {usd(b["ABC"]["fee_usd_y"])} at Agricultural Bank, {usd(b["CCB"]["fee_usd_y"])} at Construction Bank, {usd(b["BOC"]["fee_usd_y"])} at Bank of China and {usd(b["CMB"]["fee_usd_y"])} at China Merchants Bank. Total: {usd(b["BOC"]["total"])} ({q(b["BOC"]["pct"])}%) at Bank of China, {usd(b["CMB"]["total"])} ({q(b["CMB"]["pct"])}%) at China Merchants Bank.
2. **Add $15 on the U.S. side.** Bank of America and Chase each publish $15 for an incoming international wire. Fees deducted along the route are not published.
3. **A second lawful channel exists for taxed salary.** Wise publishes a service for foreigners with Chinese tax records: up to 300,000 CNY per transfer, only to an account in the same name, limited overall to after-tax salary. Western Union pays out cash abroad through partner banks. Neither price was read.
4. **The prohibited routes cost far more.** In four SAFE bulletins, {su["n"]} individuals who used an underground bank were fined ¥{q(su["lo"], "0.001")} to ¥{q(su["hi"], "0.001")} per dollar moved (median ¥{q(su["med"], "0.001")}, about {pct_yard(su["med"])}% at today's rate). {ss["n"]} individuals who split a transfer across other people's quotas were fined ¥{q(ss["lo"], "0.001")} to ¥{q(ss["hi"], "0.001")} per dollar (about {pct_yard(ss["med"])}%).
5. **Open items on the main dashboard.** Closed: the FBAR willful ceiling (U12) and, as of 2017, Chinese inheritance tax (U08). Partly closed: other banks (U03), receiving fees (U04), the treaty dividend rate (U06: 10 percent cap, subject to treaty residence), home-sale value-added tax (U17) and transfer companies (U18). Still open: the personal-transaction question (U05).

## Still blank

{chr(10).join(f"- **{f[0]}** ({f[1]}) {f[2]}: {f[3]}" for f in d.FLAGS)}

## Files

- Data: `data/g8d8_*.csv` (10 files). Evidence log with verbatim readings: `research/g8d8-evidence-log.md`.
- Checks: `python3 scripts/g8d8_build.py --check` and `python3 scripts/g8d8_verify.py`.
"""


def outputs():
    out = {f"g8d8-{k}.html": fn() for k, fn in (("summary", page_summary), ("banks", page_banks), ("receiving", page_receiving), ("channels", page_channels),
                                                ("enforcement", page_enforcement), ("closures", page_closures), ("flagged", page_flagged), ("sources", page_sources))}
    out.update({f"data/{k}": v for k, v in build_csvs().items()})
    out["research/g8d8-executive-summary.md"] = summary_md()
    return out


def main():
    check = "--check" in sys.argv
    stale = []
    for rel, text in outputs().items():
        p = ROOT / rel
        if check:
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                stale.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
    if check:
        if stale:
            print("STALE:", ", ".join(stale))
            sys.exit(1)
        print(f"g8d8_build --check: {len(outputs())} generated files are current")
    else:
        print(f"g8d8_build: wrote {len(outputs())} files")


if __name__ == "__main__":
    main()
