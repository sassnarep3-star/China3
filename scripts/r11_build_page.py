#!/usr/bin/env python3
"""Build r11-release.html: the 2026-11-11 release page.

One page, one purpose: answer "how much does each lawful way out of the account
actually cost" at every $10,000 increment from $10,000 to $400,000, at the rate read
live on 2026-11-11, and show what is missing from each number.

Every row links to the official page the input came from. A cell with no published
value is printed as "not published" and links to the flag that explains why.

    python3 scripts/r11_build_page.py            write the page
    python3 scripts/r11_build_page.py --check    fail if the page on disk is stale
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r11_engine as e  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "r11-release.html"
DASH = "dashboard"
esc = html.escape

PRICED = [c for c in e.CHANNELS if c["model"] not in ("none", "blank")]
NAMED = {c["id"]: c["name"] for c in e.CHANNELS}


def src(ids, short=True):
    out = []
    for i in ids:
        s = e.SRC[i]
        label = f"{i} {s[1].split()[0] if short else s[1]}"
        out.append(f'<a href="{esc(s[3])}" rel="noopener" title="{esc(s[2])}">{esc(label)}</a>')
    return " ".join(out)


def money(x):
    return "—" if x is None else e.usd(x)


def flagref(cid):
    f = e.CHANNEL[cid]["flags"]
    return " " + " ".join(f'<a href="{DASH}/flagged.html#{i}">{i}</a>' for i in f) if f else ""


def kpi(label, value, note, ids):
    tail = '<span class="note">' + note + "</span>" if note else ""
    return (f'<div class="kpi"><b>{value}</b><span>{label}</span>'
            f'<span class="src">{src(ids, short=False)}</span>{tail}</div>')


# ------------------------------------------------------------------ section 1: ladder
def ladder_table(cid):
    c = e.CHANNEL[cid]
    rows = []
    for a in e.AMOUNTS:
        r = e.channel_row(c["model"], a)
        spread = "n/a" if r["spread"] is None else e.usd(r["spread"])
        fee = ('<span class="blank">not published</span>' + flagref(cid)) if r["fee"] is None else e.usd(r["fee"])
        tax = e.usd(r["tax"]) if r["tax"] is not None else ("n/a" if c["model"] != "dividend" else "not published")
        total = ('<span class="blank">not published</span>' + flagref(cid)) if r["total"] is None else f'<b>{e.usd(r["total"])}</b>'
        rows.append((None, [
            f'${int(a):,}',
            spread,
            fee,
            tax,
            total,
            "n/a" if r["total"] is None else e.pct(r["total"] / a * 100),
            "n/a" if r["units"] is None else f'{r["units"]}',
            "n/a" if r["calendar_years"] is None else f'{r["calendar_years"]}',
            src(c["src"]),
        ]))
    head = ["Amount", "Spread (mid → ask)", "Wire / card fee", "Chinese tax", "Published cost",
            "% of amount", "Units", "Calendar years", "Source"]
    tail = ""
    if c["model"] == "property":
        r = e.channel_row("property", D(400000))
        tail = (f'<p class="note">What if the original 2004 staging still applied? Three wires '
                f'(half, a quarter, a quarter) would cost <b>{e.usd(r["staged"])}</b> at $400,000 instead of '
                f'{e.usd(r["total"])}. 汇发〔2014〕2号 Art. 6(2) cancelled the staging, so the column above is the '
                f'route that exists. {src(["S08", "S09"])}</p>')
    return render_table(head, rows, cls="num") + tail


def render_table(head, rows, cls="stack", caption=None, kind="data"):
    head_html = "".join(f'<th scope="col">{h}</th>' for h in head)
    body = []
    for rid, cells in rows:
        idattr = f' id="{rid}"' if rid else ""
        body.append(f"<tr{idattr}>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return (f'<div class="tbl"><table class="{cls}" data-kind="{kind}">{cap}'
            f'<thead><tr>{head_html}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')


# ------------------------------------------------------------- section 2: at a glance
def glance_rows():
    rows = []
    for cid in ("L03", "L01", "L02", "L07", "L11", "L10", "L09", "L08", "L06", "L05", "L04"):
        c = e.CHANNEL[cid]
        r10, r100, r400 = (e.channel_row(c["model"], a) for a in (D(10000), D(100000), D(400000)))
        partial = '<span class="pill warn">partial</span>' if c["model"] in ("atm", "cash") else (
            '<span class="blank">not published</span> ' + flagref(cid) if r400["total"] is None else
            '<span class="pill ok">published</span>')
        years = "n/a" if r400["calendar_years"] is None else (
            "1 year" if r400["calendar_years"] == 1 else f'{r400["calendar_years"]} years')
        rows.append((f"row-{cid}", [
            f'<span class="id">{cid}</span>{esc(c["name"])}',
            money(r10["total"]),
            money(r100["total"]),
            money(r400["total"]),
            years,
            partial,
            src(c["src"]),
        ]))
    return rows


# --------------------------------------------------------------- section 3: US side
def us_side_rows():
    rows = []
    for a in e.AMOUNTS:
        g = {y: e.fx_gain(a, y) for y in ("2023", "2024", "2025")}
        rows.append((None, [
            f'${int(a):,}',
            f'{e.usd(g["2023"])}',
            f'<b>{e.usd(g["2024"])}</b>',
            f'{e.usd(g["2025"])}',
            e.usd(e.q(g["2024"] * D("0.24"))),
            e.usd(e.q(g["2024"] * D("0.37"))),
            src(["S25", "S26"]),
        ]))
    return rows


# ------------------------------------------------------------ section 4: scenarios
def scenario_rows():
    rows = []
    for line in (e.DATA / "r11_reconciliation.csv").read_text(encoding="utf-8").splitlines()[1:]:
        import csv
        rows_raw = list(csv.DictReader((e.DATA / "r11_reconciliation.csv").open(encoding="utf-8")))
        break
    for r in rows_raw:
        pill = '<span class="pill ok">current</span>' if r["is_current"] == "yes" else '<span class="pill">historical</span>'
        rows.append((None, [
            f'<span class="id">{r["scenario"]}</span>{esc(r["board_time"])}',
            r["bid"], r["ask"],
            e.usd(D(r["spread_10k_usd"])), e.usd(D(r["cost_10k_usd"])),
            e.usd(D(r["cost_400k_usd"])),
            pill,
            esc(r["note"]) + " " + src(["S01"]),
        ]))
    return rows


# ------------------------------------------------------------------ section 5: steps
STEPS = {
    "L01": [
        ("Ask the branch, in writing, which subject category the account carries (账户主体类别) and which ID it was opened under.", ["S17"]),
        ("Assemble the source-of-funds file: employment contract, payslips, and the bank statements showing each deposit.", ["S04"]),
        ("Get tax evidence from the tax office: a 完税证明, an exemption certificate, or the filing form. Savings interest accrued after 2008-10-09 is exempt, so say so if part of the balance is interest.", ["S19", "S21"]),
        ("If a single payment exceeds USD 50,000 in a listed category, file the 对外支付税务备案 form at the tax office first; it is a filing, not a charge.", ["S18"]),
        ("Take passport, source file and tax evidence to the bank and convert at the day's selling rate. Ask for the rate to be printed on the voucher.", ["S04", "S01"]),
        ("Instruct the wire to your own US account and choose the charge code (OUR/SHA/BEN) deliberately.", ["S02"]),
        ("File the FBAR by 15 April of the following year (automatic extension to 15 October) and Form 8938 with the return if the thresholds are met, and report the §988 gain.", ["S27", "S29", "S25"]),
    ],
    "L02": [
        ("Find the original 兑换水单 from when you changed foreign currency into RMB. Check it is dated within 24 months.", ["S11"]),
        ("Take passport and slip to the bank and change back up to the unused amount on the slip.", ["S11"]),
        ("Convert at the day's selling rate and wire to your own account.", ["S01", "S02"]),
        ("Without a slip, only the equivalent of USD 500 a day can be changed back on ID alone.", ["S11"]),
    ],
    "L03": [
        ("Identify the foreign-currency sub-account on the statement. This route needs no conversion.", ["S07"]),
        ("Ask the branch to remit from that FX account to your US account. Art. 65(1) requires only valid ID for a foreign individual.", ["S07"]),
        ("Pay the wire tariff only: 0.1%, min RMB 50, max RMB 260, plus RMB 150 cable.", ["S02"]),
        ("Record the receiving-bank and correspondent fees, which no official page publishes and this release leaves blank.", ["S02"]),
    ],
    "L04": [
        ("Complete the title transfer and pay the taxes of the sale. The bank will cap the remittance at the sale price less those taxes.", ["S24"]),
        ("Collect the registered sale contract, the registration proof and the tax certificate.", ["S24"]),
        ("Take them to the bank with your passport and convert at the selling rate.", ["S01"]),
        ("Wire to your own account and keep the tax certificate for the U.S. foreign tax credit record.", ["S02", "S25"]),
    ],
    "L05": [
        ("Apply to the SAFE branch where the deceased's household registration was (not where you live).", ["S08", "S10"]),
        ("Submit the written application, the application form, identity and settlement proof, notarised inheritance and property documents, and the tax certificate from the property's tax office.", ["S08"]),
        ("After approval, take the approval letter and 核准件 to the designated bank.", ["S08"]),
        ("Remit once or in instalments within the approved amount; the payout must go to an account in your own name abroad.", ["S09", "S08"]),
        ("In the US, report the bequest on Form 3520 if the aggregate exceeds USD 100,000.", ["S31"]),
    ],
    "L06": [
        ("Obtain the hukou cancellation certificate from the police station that held your registration.", ["S08"]),
        ("Have the Chinese embassy or consulate certify your settlement abroad.", ["S08"]),
        ("Apply to the SAFE branch at your former hukou for one approval covering everything you will move.", ["S08", "S10"]),
        ("Take the approval and 核准件 to the bank and remit once or in instalments.", ["S09"]),
        ("Keep every tax certificate; unpaid Chinese tax on the property or income has to be settled first.", ["S08"]),
    ],
    "L07": [
        ("Confirm you hold the PRC Foreign Permanent Resident ID card rather than a visa or residence permit.", ["S05"]),
        ("Convert up to USD 50,000 equivalent per calendar year on the card alone.", ["S06", "S05"]),
        ("Wire each tranche; the wire tariff is paid once per tranche.", ["S02"]),
        ("Above the annual amount, switch to L01 for the documented remainder.", ["S04"]),
    ],
    "L08": [
        ("Ask the bank whether it offers personal cross-border RMB remittance and what documents it wants.", ["S15"]),
        ("Send the RMB to your own account outside the mainland.", ["S15"]),
        ("Convert at the receiving bank. Its rate and fee are not published anywhere official, so every cost cell here is blank.", ["S15"]),
    ],
    "L09": [
        ("Pass a profit-distribution resolution and complete the books for the dividend.", ["S09"]),
        ("Pay the 20% individual income tax on the dividend, then get the tax evidence.", ["S20"]),
        ("For a payment above USD 50,000, file the 对外支付税务备案 form.", ["S18"]),
        ("Take the resolution, accounts and tax evidence to the bank and remit the net amount.", ["S09"]),
    ],
    "L10": [
        ("Confirm the card is a mainland UnionPay debit card on the RMB account.", ["S13"]),
        ("Withdraw abroad within RMB 10,000 per card per day and RMB 100,000 per person per calendar year.", ["S13"]),
        ("Expect Bank of China's own fee: RMB 12 + 1% per withdrawal, capped at RMB 112.", ["S03"]),
        ("Budget for the UnionPay conversion rate and the foreign ATM's own fee, both blank here.", ["S03"]),
        ("Report the cash on FinCEN Form 105 when entering the US with more than USD 10,000.", ["S33"]),
    ],
    "L11": [
        ("Buy the foreign currency lawfully first through L01, L02 or L07. Cash is a delivery method, not a route.", ["S04", "S14"]),
        ("Up to USD 5,000 equivalent: customs releases it on inspection.", ["S14"]),
        ("USD 5,000 to 10,000: obtain the 携带外汇出境许可证 from the bank.", ["S14"]),
        ("Above USD 10,000: a SAFE permit is required and is in principle not granted.", ["S14"]),
        ("Report on FinCEN Form 105 when entering the US with more than USD 10,000.", ["S33"]),
    ],
}


def steps_html():
    parts = []
    for cid, items in STEPS.items():
        li = "".join(
            f'<li>{esc(text)} <span class="src">{src(ids)}</span></li>' for text, ids in items)
        parts.append(
            f'<details{" open" if cid == "L01" else ""}><summary>{cid} · {esc(NAMED[cid])}'
            f'<span>{len(items)} steps</span></summary><ol class="plain">{li}</ol></details>')
    return "".join(parts)


# ------------------------------------------------------- section 7: registers
def questions_html():
    import csv as _csv
    with (e.DATA / "r11_questions.csv").open(encoding="utf-8", newline="") as fh:
        qs = list(_csv.DictReader(fh))
    prio = {"high": "bad", "medium": "warn", "low": ""}
    gates, order = {}, []
    for r in qs:
        gates.setdefault(r["gate"], []).append(r)
        if r["gate"] not in order:
            order.append(r["gate"])
    blocks = []
    for g in order:
        rows = [(None, [f'<span class="id">{r["id"]}</span>{esc(r["question"])}<br>'
                        f'<span class="pill {prio[r["priority"]]}">{r["priority"]}</span>',
                        esc(r["known"]), esc(r["unknown"]), esc(r["how_to_discover"]),
                        src(r["source_ids"].split("|"))]) for r in gates[g]]
        blocks.append(f'<h3 id="gate-{esc(g.split()[1])}">{esc(g)}</h3>'
                      + render_table(["Question", "What we know (sourced)", "What we do not know",
                                      "How to discover it", "Source"], rows))
    return "".join(blocks)


def flags_html():
    import csv as _csv
    with (e.DATA / "r11_flags.csv").open(encoding="utf-8", newline="") as fh:
        fs = list(_csv.DictReader(fh))
    prio = {"high": "bad", "medium": "warn", "low": ""}
    rows = [(None, [f'<span class="id">{r["id"]}</span>{esc(r["item"])}<br>'
                    f'<span class="pill {prio[r["severity"]]}">{r["severity"]}</span>',
                    esc(r["why"]), esc(r["what_would_settle_it"]), src(r["source_ids"].split("|"))])
            for r in fs]
    return render_table(["Item", "Why it is blank or uncertain", "What would settle it", "Source"], rows)


def review_html():
    import csv as _csv
    with (e.DATA / "r11_repo_review.csv").open(encoding="utf-8", newline="") as fh:
        rs = list(_csv.DictReader(fh))
    prio = {"high": "bad", "medium": "warn", "low": ""}
    rows = [(None, [f'<span class="id">{r["id"]}</span>{esc(r["where"])}<br>'
                    f'<span class="pill {prio[r["severity"]]}">{r["severity"]}</span>',
                    esc(r["finding"]), esc(r["evidence"]), esc(r["action"]),
                    f'<a href="https://github.com/sassnarep3-star/China3" rel="noopener">repository</a>'])
            for r in rs]
    return render_table(["Where", "Finding", "Evidence", "Action taken or recommended", "Link"], rows, kind="repo")


# ------------------------------------------------------------------------- page
def page():
    l01_10 = e.channel_row("fx_wire", D(10000))
    l01_400 = e.channel_row("fx_wire", D(400000))
    l03_400 = e.channel_row("wire_only", D(400000))
    l09_400 = e.channel_row("dividend", D(400000))
    l10_400 = e.channel_row("atm", D(400000))
    g24 = e.fx_gain(D(400000), "2024")
    g24p = g24 / D(400000) * 100
    n_high = sum(1 for f in e.FLAGS if f[1] == "high")

    nav = "".join([
        '<a href="index.html">Home</a>',
        '<a href="dashboard/methods.html">Methods</a>',
        '<a href="dashboard/costs.html">Costs</a>',
        '<a href="dashboard/questions.html">Questions</a>',
        '<a href="dashboard/steps.html">Steps</a>',
        '<a href="dashboard/tax.html">Tax</a>',
        '<a href="dashboard/flagged.html">Flagged</a>',
        '<a href="dashboard/sources.html">Sources</a>',
        '<a href="r11-release.html" aria-current="page">Release 2026-11-11</a>',
        '<a href="dashboard/archive.html">Archive</a>',
    ])

    ladder_sections = "".join(
        f'<h3 id="cost-{c["id"]}">{c["id"]} · {esc(c["name"])}</h3>'
        f'<p class="note">{esc(c["published"])} Not in this figure: {esc(c["blank"] or "nothing identified")} '
        f'{flagref(c["id"])}</p>{ladder_table(c["id"])}'
        for c in PRICED)

    body = f"""
<h1>What it costs to move the money out, $10,000 to $400,000</h1>
<p class="lead">Read live from official pages on 11 November 2026. Every figure is the <strong>published</strong> part
of the cost at the Bank of China board published {esc(e.RATE["board_time"])}. Anything no official page publishes is
printed as <em>not published</em> and linked to the flag that says why. Nothing is estimated, inferred or filled in.</p>

<div class="kpis">
{kpi("bank cost to convert + wire $10,000", e.usd(l01_10["total"]), e.pct(l01_10["total"] / D(10000) * 100), ["S01", "S02"])}
{kpi("bank cost to convert + wire $400,000", e.usd(l01_400["total"]), e.pct(l01_400["total"] / D(400000) * 100), ["S01", "S02"])}
{kpi("wire only, no conversion, $400,000", e.usd(l03_400["total"]), "cheapest lawful route", ["S02", "S07"])}
{kpi("US currency gain if bought at the 2024 average", e.usd(g24, False), e.pct(g24p, 1) + " of the dollars received", ["S25", "S26"])}
</div>

<div class="banner"><strong>The number that matters is not the bank fee.</strong> The bank's published cost is
{e.pct(l01_10["total"] / D(10000) * 100)} at $10,000 and falls to {e.pct(l01_400["total"] / D(400000) * 100)} at
$400,000. The U.S. currency gain on the same $400,000 is {e.usd(g24, False)} before tax, and a single missed FBAR
can cost the greater of $165,353 or half the balance. <a href="dashboard/tax.html">Tax page</a> ·
<a href="dashboard/flagged.html#U02">U02</a>.</div>

<h2>1. The answer in one table</h2>
<p>Published cost only, at the current board. "Partial" means the published figure leaves out a component that no
official page prices; "not published" means nothing usable could be confirmed, so the cell stays empty.</p>
{render_table(["Route", "$10,000", "$100,000", "$400,000", "Time for $400,000", "Figure status", "Source"], glance_rows(), cls="num routes")}
<p class="note">L04, L05 and L06 have the same published cost as L01 because the bank leg is identical; only the
approval and document burden differs. L09 includes the 20% Chinese tax on the dividend. L10 and L11 are marked partial
because the conversion leg is not published. If you already hold foreign currency in the account, L03 is the only route
that avoids the spread entirely.</p>

<h2>2. Every $10,000 step, every route</h2>
<p>Same arithmetic as above, printed for all 40 increments. The convention is stated once, on
<a href="#method">method</a>: the spread is the gap between the bank's own mid rate and the rate you actually get,
the wire fee is the published tariff, and the percentage is against the USD amount.</p>
{ladder_sections}

<h2 id="us">3. The U.S. side, which no bank channel avoids</h2>
<p>Selling RMB is a currency sale under 26 U.S.C. §988, and the gain is ordinary income. The personal-transaction
relief in §988(e) applies only where the gain is $200 or less, so at these amounts it does not apply. The gain below is
what you would report if the RMB had been acquired at that year's IRS average rate and sold at today's board:
<code>gain = amount − amount × 6.6911 ÷ yearly average</code>.</p>
{render_table(["Amount", "If acquired at 2023 average (7.075)", "If acquired at 2024 average (7.189)",
               "If acquired at 2025 average (7.129)", "Tax at 24% on the 2024 case", "Tax at 37% on the 2024 case", "Source"],
              us_side_rows(), cls="num")}
<p class="note">A negative figure would mean a loss, which may be deductible subject to the rules in §988 and the
capital-loss limits; every row here is a gain because the current board is below all three averages.
Acquisition year and rate are facts only you hold: <a href="dashboard/questions.html#Q08">Q08</a>.
The IRS publishes no official rate: {src(["S26"])}</p>

<h2 id="method">4. How the numbers are built</h2>
<div class="tbl"><table class="stack" data-kind="data">
<thead><tr><th scope="col">Model</th><th scope="col">Formula</th><th scope="col">Why this convention</th><th scope="col">Source</th></tr></thead>
<tbody>
<tr><td><b>M1</b> conversion + wire</td><td class="num">spread = amount × (ask − mid) ÷ ask<br>fee = (0.1% × amount × ask, min 50, max 260) ÷ ask + 150 ÷ ask<br>
total = spread + fee</td><td>The bank buys at its bid and sells at its ask. Measuring against its own mid separates the bank's margin from the wire tariff instead of lumping them together.</td><td>{src(["S01", "S02"])}</td></tr>
<tr><td><b>M2</b> wire only</td><td class="num">total = fee</td><td>No conversion, so there is no spread to measure.</td><td>{src(["S02", "S07"])}</td></tr>
<tr><td><b>M3</b> quota</td><td class="num">spread once, fee per yearly tranche</td><td>The whole amount is converted once and held as USD; each USD 50,000 tranche pays its own wire.</td><td>{src(["S06", "S02"])}</td></tr>
<tr><td><b>M4</b> property transfer</td><td class="num">as M1, one approval</td><td>汇发〔2014〕2号 removed the staged payout. The staged what-if is shown beside the table.</td><td>{src(["S09"])}</td></tr>
<tr><td><b>M5</b> card and cash</td><td class="num">published card fee, or cash spread</td><td>Only the part the bank publishes is printed. The conversion leg is left blank.</td><td>{src(["S03", "S13", "S14"])}</td></tr>
</tbody></table></div>

<h2 id="recon">5. Why other pages show a different number</h2>
<p>Four earlier layers published four different headline figures for the same conversion. Each is reproduced below from
its own board reading. The differences are the clock, not the channel: hold the formula fixed and move only the rate,
and each published figure comes back to the cent.</p>
{render_table(["Board reading", "Bid", "Ask", "Spread at $10,000", "Cost at $10,000", "Cost at $400,000", "Status", "Note"],
              scenario_rows(), cls="num")}
<p class="note">Scenario A is this release. B reproduces $53.38 and $899.01 (the 2026-11-10 dashboard). C reproduces
$901.30 (the s775 and fbbd3b22 layers). The remaining published variants ($53.42 at $10,000 and $1,328.33 at
$400,000) differ only in whether the spread is measured against the mid or the ask, and in whether the $400,000 is sent
as one wire or eight. <a href="dashboard/flagged.html">Flagged</a> · <a href="dashboard/costs.html">Cost tables</a></p>

<h2 id="steps">6. Step by step, per route</h2>
<p>Each step links to the official page that requires it. Nothing here is a recommendation: which route you can use
depends on answers you hold, not on this page.</p>
{steps_html()}

<h2 id="questions">7. Every question that has to be answered first</h2>
<p>In the order they block a decision. A later gate cannot repair an earlier one: what the money legally is decides
which document list the bank applies, and the account's identity category decides which half of the rule book applies.
The same register is on <a href="dashboard/questions.html">the Questions page</a>; this is the full copy, with what is
already known from an official page beside each question.</p>
{questions_html()}

<h2 id="flags">8. Everything still unverified, with what would settle it</h2>
<p>{len(e.FLAGS)} items are open, {n_high} of them high. A blank cell anywhere in this release links to one of these.</p>
{flags_html()}

<h2 id="review">9. Problems found in this repository, line by line</h2>
<p>The repository now holds fourteen layers of research with colliding figures, colliding flag ids and four different
quotes for the same conversion. Each finding below states what was measured, where, and what this release did about it.
Carried on <a href="dashboard/flagged.html">the Flagged page</a> as the only review register.</p>
{review_html()}

<h2>10. Sources read for this page, on 2026-11-11</h2>
<p>All {len(e.SOURCES)} were opened on 11 November 2026; {sum(1 for s in e.SOURCES if s[4] == "direct")} in full and
{sum(1 for s in e.SOURCES if s[4] != "direct")} as an excerpt. The quotes below are the text that carries each number.</p>
<div class="tbl"><table class="stack" data-kind="data">
<thead><tr><th scope="col">Id</th><th scope="col">Document</th><th scope="col">Text relied on</th><th scope="col">How read</th></tr></thead>
<tbody>
{''.join(f'<tr><td><span class="id">{s[0]}</span>{esc(s[1])}</td>'
         f'<td><a href="{esc(s[3])}" rel="noopener">{esc(s[2])}</a></td>'
         f'<td class="quote">{esc(s[5])}</td>'
         f'<td>{"read in full" if s[4] == "direct" else "excerpt"}</td></tr>' for s in e.SOURCES)}
</tbody></table></div>

<p class="note">Reproduce every figure on this page with <code>python3 scripts/r11_engine.py &amp;&amp;
python3 scripts/r11_build_page.py</code>, and check it with <code>python3 scripts/r11_verify.py</code>.
General research from public official pages; not legal, tax or banking advice, and no finding about any person's case.</p>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="r11-release">
<meta name="description" content="Published cost of every lawful way to move money out of a Chinese bank account, $10,000 to $400,000 in $10,000 steps, at the Bank of China board read live on 11 November 2026, with every source linked and every gap flagged.">
<title>Release 2026-11-11: $10,000 to $400,000 · China money</title>
<link rel="stylesheet" href="dashboard/site.css">
<style>
.kpi .note{{font-size:.78rem;color:var(--muted);margin-top:4px}}
td.quote{{font-size:.86rem;color:var(--muted);max-width:46ch}}
details ol.plain{{padding:6px 18px 14px 32px}}
details ol.plain li{{margin:.35em 0;font-size:.94rem}}
details .src{{font-size:.8rem;color:var(--muted)}}
</style>
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
<p>Rate: Bank of China board published {esc(e.RATE["board_time"])}, bid 6.6630 / ask 6.6911, read on 2026-11-11.
Wire tariff: 0.1%, RMB 50-260, plus RMB 150 cable.</p>
<p>General research from public official pages. It is not legal, tax or banking advice and makes no finding about
any person's case.</p>
<p><a href="dashboard/sources.html">All sources</a> · <a href="dashboard/flagged.html">Open items</a> ·
<a href="https://github.com/sassnarep3-star/China3">Repository</a> · built by <code>scripts/r11_build_page.py</code></p>
</div></footer>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = page()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else None
        if current != text:
            print("FAIL — r11-release.html is stale; run python3 scripts/r11_build_page.py")
            return 1
        print("OK — r11-release.html is up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
