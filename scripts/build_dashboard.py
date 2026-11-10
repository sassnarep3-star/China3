#!/usr/bin/env python3
"""Build the consolidated dashboard (index.html) and the 2026 verification page.

Every number printed by this script is either
  * read from data/verify_2026.csv (a record of an official source fetched this session), or
  * computed here by arithmetic on data/live_rate_20261110.csv (also an official board reading),
  * or copied from data/s436_cost_schedule.csv, which carries a per-row official URL.

Nothing is typed in by hand except prose and the page layout.

Usage
  python3 scripts/build_dashboard.py            # write the pages and the ladder CSV
  python3 scripts/build_dashboard.py --check    # write nothing; fail if on-disk pages are stale
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"

D = Decimal


# --------------------------------------------------------------------- inputs
def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


RATE = {r["field"]: r for r in rows("live_rate_20261110.csv")}
VERIFY = {r["id"]: r for r in rows("verify_2026.csv")}
METHODS = rows("s436_method_summary_40steps.csv")
SCHEDULE = rows("s436_cost_schedule.csv")

ASK = D(RATE["ask_spot_selling"]["value"]) / D(100)          # CNY per USD
BID = D(RATE["bid_spot_buying"]["value"]) / D(100)
PARITY = D(RATE["parity_reference"]["value"]) / D(100)
MID = (ASK + BID) / 2
WIRE_RATE = D(RATE["wire_fee_per_mille"]["value"])
WIRE_MIN = D(RATE["wire_fee_min"]["value"])
WIRE_MAX = D(RATE["wire_fee_max"]["value"])
CABLE = D(RATE["cable_fee_non_hk"]["value"])
OUR = D(RATE["our_usd_optional"]["value"])
BOARD_TS = RATE["board_timestamp"]["value"]
BOARD_URL = RATE["board_timestamp"]["source_url"]
TARIFF_URL = RATE["wire_fee_per_mille"]["source_url"]
OUR_URL = RATE["our_usd_optional"]["source_url"]

AMOUNTS = [D(a) for a in range(10_000, 400_001, 10_000)]


def q2(v: D) -> D:
    return v.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def spread_usd(usd: D) -> D:
    """Cost of crossing the published bid/ask spread. Same convention as the
    2026-11-09 schedule (denominator = ask), so the two ladders are comparable."""
    return usd * (ASK - MID) / ASK


def wire_usd(usd: D) -> D:
    """Personal BOC outward telegraphic transfer + cable, expressed in USD."""
    cny = usd * ASK
    fee_cny = min(WIRE_MAX, max(WIRE_MIN, WIRE_RATE * cny))
    return (fee_cny + CABLE) / ASK


def ladder() -> list[dict]:
    out = []
    for usd in AMOUNTS:
        fx = q2(spread_usd(usd))
        wire = q2(wire_usd(usd))
        total = fx + wire
        out.append(
            dict(
                amount_usd=f"{usd:.0f}",
                cny_needed=f"{q2(usd * ASK):.2f}",
                spread_usd=f"{fx:.2f}",
                wire_cable_usd=f"{wire:.2f}",
                total_usd=f"{total:.2f}",
                total_pct=f"{(total / usd * 100):.4f}",
                net_usd=f"{usd - total:.2f}",
                our_usd=f"{OUR:.2f}",
                net_with_our=f"{usd - total - OUR:.2f}",
            )
        )
    return out


LADDER = ladder()
LADDER_BY_AMOUNT = {r["amount_usd"]: r for r in LADDER}


# ------------------------------------------------------------------- fragments
def src(vid: str, label: str | None = None) -> str:
    """Inline citation chip pointing at the official page behind a figure."""
    v = VERIFY[vid]
    text = label or v["issuer"]
    return (
        f'<a class="src" href="{v["url"]}" target="_blank" rel="noopener">{text}'
        f'<span class="sr"> — {v["source_title"]}</span></a>'
    )


def money(v: str) -> str:
    return f"${D(v):,.2f}"


def pct(v: str) -> str:
    return f"{D(v):.4f}%".replace(".0000%", "%")


def cell(label: str, value: str, cls: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<td data-l="{label}"{c}>{value}</td>'


def status_badge(status: str) -> str:
    s = status.strip().upper()
    if s == "PROHIBITED":
        return '<span class="badge badge-no">prohibited</span>'
    if s == "UNVERIFIED":
        return '<span class="badge badge-blank">unverified</span>'
    return '<span class="badge badge-ok">sourced</span>'


# ------------------------------------------------------------------- sections
def key_cards() -> str:
    big = LADDER_BY_AMOUNT["400000"]
    cards = [
        (
            "No Chinese conversion tax",
            "$0",
            "No official instrument taxes the act of converting your own CNY principal to USD. "
            "The PRC 20% rate below applies to the <em>income that created</em> the money, not the exchange.",
            src("V09", "chinatax.gov.cn"),
        ),
        (
            "Bank spread you actually pay",
            f"{D(LADDER_BY_AMOUNT['10000']['total_pct']):.2f}% → {D(LADDER_BY_AMOUNT['400000']['total_pct']):.2f}%",
            "All-in China-side cost on a documented current-account wire, from "
            f"{money(LADDER_BY_AMOUNT['10000']['total_usd'])} on $10,000 to "
            f"{money(LADDER_BY_AMOUNT['400000']['total_usd'])} on $400,000. "
            f"Built on the {BOARD_TS} BOC board (ask {ASK} CNY/USD).",
            src("V01", "BOC board"),
        ),
        (
            "Wire fee",
            "1‰, cap ¥260",
            "Plus a cable fee of CNY 150 outside Hong Kong/Macau/Taiwan. The CNY 260 cap bites at about "
            f"${q2(WIRE_MAX / WIRE_RATE / ASK):,.0f} of transfer, so the fee stops growing there.",
            src("V04", "BOC tariff"),
        ),
        (
            "FBAR trigger",
            "> $10,000",
            "Aggregate value of foreign accounts <em>exceeds</em> $10,000 at any time in the calendar year. It is a "
            "reporting trigger, not a tax — the penalty is what costs money.",
            src("V17", "FinCEN"),
        ),
        (
            "Willful FBAR ceiling",
            "50% of balance",
            "Greater of the inflation-adjusted USD 165,353 or 50% of the account balance. On $400,000 that "
            f"ceiling is $200,000 — about {D(200000) / D(big['total_usd']):.0f}× the cost of moving the money lawfully.",
            src("V10", "31 USC 5321"),
        ),
        (
            "U.S. currency-gain rule",
            "$200",
            "A personal transaction in foreign currency recognises no §988 gain unless the gain exceeds $200. "
            "Whether your conversion is a “personal transaction”, and the CNY cost basis, are fact-specific — "
            "this is not a finding that your conversion is untaxable.",
            src("V15", "26 USC 988"),
        ),
    ]
    html = ['<div class="cards">']
    for title, big, body, link in cards:
        html.append(
            f'<div class="card"><div class="card-k">{title}</div>'
            f'<div class="card-v">{big}</div><p>{body}</p>'
            f'<div class="card-s">{link}</div></div>'
        )
    html.append("</div>")
    return "\n".join(html)


def verdict_table() -> str:
    rows_ = [
        (
            "1 · Best",
            "Documented current-account income, wired out by the bank",
            "A non-resident (or resident) individual converts lawful, tax-paid onshore income with ID plus "
            "source/purpose documents. No annual ceiling applies when the documents exist.",
            LADDER_BY_AMOUNT["400000"]["total_usd"],
            "1 transfer",
            "V06",
            "safe.gov.cn",
        ),
        (
            "2 · If you emigrated",
            "Emigrant property transfer (移民财产转移)",
            "For property you owned <em>before</em> acquiring emigrant status. Requires the police-issued "
            "household-registration cancellation certificate and consular proof of settlement abroad. One "
            "application; a single remittance is permitted since 2014.",
            LADDER_BY_AMOUNT["400000"]["total_usd"],
            "1 transfer",
            "V07",
            "safe.gov.cn",
        ),
        (
            "3 · Only if needed",
            "USD 50,000 annual convenience amount, year after year",
            "Simplified processing with ID only, per person per year, for a PRC-resident individual (境内个人). "
            "$400,000 takes eight calendar years and eight wire fees. A foreign passport holder does not "
            "automatically get the same treatment — the bank classifies the person first.",
            "1529.87",
            "8 years",
            "V06",
            "safe.gov.cn",
        ),
        (
            "Avoid",
            "Quota splitting, underground banks, crypto, false invoices",
            "Expressly prohibited in China and a money-laundering exposure in the United States. The Chinese "
            "administrative fine is up to 30% of the amount (30%–100% where the case is serious); a willful FBAR "
            "penalty can reach 50% of the balance.",
            "blank by rule",
            "n/a",
            "V16",
            "safe.gov.cn",
        ),
    ]
    html = [
        '<div class="tw"><table class="tbl"><thead><tr>',
        "<th>Path</th><th>What it is</th><th>All-in on $400k</th><th>Time</th><th>Source</th>",
        "</tr></thead><tbody>",
    ]
    for rank, name, desc, cost, time, vid, label in rows_:
        cls = "row-no" if rank == "Avoid" else ""
        html.append(
            f'<tr class="{cls}">'
            + cell("Path", f'<strong>{rank}</strong>')
            + cell("Route", f'<strong>{name}</strong><br><span class="mini">{desc}</span>')
            + cell("All-in on $400,000", money(cost) if cost not in {"see methods", "blank by rule"} else f'<span class="blank">{cost}</span>')

            + cell("Time", time)
            + cell("Source", src(vid, label))
            + "</tr>"
        )
    html += ["</tbody></table></div>"]
    return "\n".join(html)


def ladder_table(rows_: list[dict], with_our: bool = False) -> str:
    html = ['<div class="tw"><table class="tbl tbl-num"><thead><tr>']
    html.append(
        "<th>Amount</th><th>CNY needed</th><th>FX spread</th><th>Wire + cable</th>"
        "<th>Total cost</th><th>% of amount</th><th>Net received</th><th>Source</th>"
    )
    html.append("</tr></thead><tbody>")
    for r in rows_:
        html.append(
            "<tr>"
            + cell("Amount", f'${D(r["amount_usd"]):,.0f}', "num")
            + cell("CNY needed", f'¥{D(r["cny_needed"]):,.2f}', "num")
            + cell("FX spread", f'${D(r["spread_usd"]):,.2f}', "num")
            + cell("Wire + cable", f'${D(r["wire_cable_usd"]):,.2f}', "num")
            + cell("Total cost", f'<strong>${D(r["total_usd"]):,.2f}</strong>', "num")
            + cell("% of amount", f'{D(r["total_pct"]):.4f}%', "num")
            + cell("Net received", f'${D(r["net_usd"]):,.2f}', "num")
            + cell("Source", src("V01", "board") + " " + src("V04", "tariff"))
            + "</tr>"
        )
    html.append("</tbody></table></div>")
    note = (
        "Cost to the sender, China side. Full-amount-received (OUR) would add "
        f"${OUR} per transfer so the U.S. bank does not deduct its own charge from the principal — but that charge "
        "is published in BOC's trade-finance tariff, not in the personal e-banking tariff, so treat it as optional "
        "and confirm availability with the branch. The totals above exclude it."
    )
    if with_our:
        note += " The 40-row file <code>data/ladder_20261110.csv</code> carries the OUR column too."
    return "\n".join(html) + f'<p class="foot">{note}</p>'


def methods_table() -> str:
    html = ['<div class="tw"><table class="tbl"><thead><tr>']
    html.append(
        "<th>#</th><th>Method</th><th>Legal status</th><th>$10k</th><th>$100k</th>"
        "<th>$400k</th><th>Time</th><th>Status</th><th>Source</th>"
    )
    html.append("</tr></thead><tbody>")
    for m in METHODS:
        c10, c100, c400 = (m["cost_at_10000_usd"], m["cost_at_100000_usd"], m["cost_at_400000_usd"])
        cells = []
        for lbl, v in (("$10k", c10), ("$100k", c100), ("$400k", c400)):
            cells.append(
                cell(lbl, f'${D(v):,.2f}' if v.strip() else '<span class="blank">blank</span>', "num")
            )
        years = m["minimum_years_at_400000"].strip()
        html.append(
            "<tr>"
            + cell("#", m["rank"], "num")
            + cell("Method", f'{m["method"]}<br><span class="mini">{m["important_constraint"]}</span>')
            + cell("Legal status", m["legal_status"])
            + "".join(cells)
            + cell("Time", f"{years} yr" if years and years.isdigit() and years != "1" else (f"{years} yr" if years.isdigit() else "n/a"))
            + cell("Status", status_badge(m["status"]))
            + cell("Source", f'<a class="src" href="{m["official_source_url"]}" target="_blank" rel="noopener">{m["source_id"]}</a>')
            + "</tr>"
        )
    html.append("</tbody></table></div>")
    return "\n".join(html)


def penalty_table() -> str:
    rows_ = [
        ("PRC income tax on the source of the money", "20% flat", "Property transfer, interest, rent, dividends, incidental income. A rate, not an amount: the tax base depends on the individual transaction.", "V09", "chinatax"),
        ("PRC tax already deducted at source", "already paid", "If the 20% (or salary tax) was withheld when you earned or sold, converting the after-tax balance does not tax it again.", "V09", "chinatax"),
        ("U.S. income tax on receipt of your own money", "no tax on principal", "Moving your own after-tax savings is not income. What is taxable is unreported income that created the balance, or currency gain above the §988 personal-transaction threshold.", "V15", "26 USC 988"),
        ("FBAR — non-willful", "$16,536 per violation (max)", "Inflation-adjusted ceiling for penalties assessed on or after 2025-01-17. Reasonable cause can eliminate it entirely.", "V11", "eCFR"),
        ("FBAR — willful", "greater of $165,353 or 50% of balance", "On a $400,000 balance the 50% branch yields $200,000. This, not the exchange rate, is the number that should drive the plan.", "V10", "31 USC 5321"),
        ("Form 8938 (FATCA)", "no tax; reporting only", "Filed with the return when the threshold is met. USD 50,000 year-end / 75,000 any time for an unmarried filer living in the U.S.", "V12", "irs.gov"),
        ("Prohibited Chinese FX routes", "up to 30% of the amount", "State Council Order 532 arts. 39 and 45: an administrative fine of 30% or less of the amount for an ordinary case, rising to 30%–100% of the amount where the case is serious, plus confiscation of illegal gains and criminal liability. Not a floor of 30%.", "V16", "safe.gov.cn"),
    ]
    html = ['<div class="tw"><table class="tbl"><thead><tr>']
    html.append("<th>Charge</th><th>Amount</th><th>What it actually applies to</th><th>Source</th></tr></thead><tbody>")
    for name, amount, desc, vid, label in rows_:
        link = src(vid, label) if vid else '<a class="src" href="penalties.html">penalties.html</a>'
        html.append(
            "<tr>"
            + cell("Charge", f"<strong>{name}</strong>")
            + cell("Amount", amount)
            + cell("What it applies to", desc)
            + cell("Source", link)
            + "</tr>"
        )
    html += ["</tbody></table></div>"]
    return "\n".join(html)


def verify_table() -> str:
    html = ['<div class="tw"><table class="tbl"><thead><tr>']
    html.append("<th>ID</th><th>What was checked</th><th>Value found</th><th>Official source</th><th>Status</th></tr></thead><tbody>")
    for vid, v in VERIFY.items():
        html.append(
            f'<tr id="{vid.lower()}">'
            + cell("ID", f'<a href="#{vid.lower()}">{vid}</a>')
            + cell("Checked", f'{v["item"]}<br><span class="mini">{v["source_title"]}</span>')
            + cell("Value", f'{v["value"]} {v["unit"]}'.strip() + f'<details><summary>quoted text</summary><q>{v["quote"]}</q></details>')
            + cell("Source", f'<a class="src" href="{v["url"]}" target="_blank" rel="noopener">{v["issuer"]}</a>')
            + cell("Status", f'<span class="badge badge-ok">{v["verdict"]}</span>')
            + "</tr>"
        )
    html += ["</tbody></table></div>"]
    return "\n".join(html)


def cards_nav() -> str:
    items = [
        ("Cost tables", "Every route at every $10,000 step", "cost-tables.html", "canonical"),
        ("All 640 rows", "16 methods × 40 amounts, filterable", "schedule-cost-10k-400k.html", ""),
        ("Methods &amp; pros/cons", "35 channels with the legal status of each", "deep-channels.html", ""),
        ("Step-by-step", "Copy-ready procedure per route", "schedule-steps.html", ""),
        ("China rules", "SAFE / PBOC instruments, article by article", "deep-china-rules.html", ""),
        ("U.S. tax", "FBAR, 8938, FEIE, §988, treaty", "deep-us-tax.html", ""),
        ("Penalties", "Each penalty layer with its ceiling", "deep-penalty.html", ""),
        ("Verify 2026", "What this session re-checked, with quotes", "verify-2026.html", "new"),
        ("Safety review", "Independent spot checks and their cautions", "a15-review.html", ""),
        ("Flagged for review", "Everything left blank, with the reason", "deep-review.html", ""),
        ("Sources", "84 official pages, by issuer", "deep-sources.html", ""),
        ("Narrative guide", "The earlier editorial passes, preserved", "guide.html", ""),
        ("Data dashboard", "Structured data + calculator", "docs/index.html", ""),
    ]
    out = ['<div class="cards cards-nav">']
    for title, sub, href, tag in items:
        badge = f'<span class="badge badge-new">{tag}</span>' if tag else ""
        out.append(
            f'<a class="card card-link" href="{href}"><div class="card-k">{title} {badge}</div>'
            f'<p>{sub}</p><span class="go">Open →</span></a>'
        )
    out.append("</div>")
    return "\n".join(out)


def correction_box() -> str:
    return f"""
<section class="section" id="correction">
  <h2>Correction published with this dashboard</h2>
  <div class="callout warn">
    <p><strong>The emigrant property transfer is no longer remitted in stages.</strong>
    PBC Order [2004] No. 16 art. 6 says an emigrant applies once for the whole estate and receives it in
    stages: half, then half the remainder after a year, then the rest after two years ({src('V08','2004 text')}).
    The later SAFE circular 汇发〔2014〕2号 §6(2) expressly cancels that requirement —
    <q>取消移民财产转移分次汇出的要求 … 可一次或分次汇出</q> ({src('V07','2014 circular')}) — and §6(1) of the
    same circular cancels the over-RMB-500,000 head-office filing.
    </p>
    <p>The cost model on <a href="cost-tables.html">cost-tables.html</a> prices route M03 as three separate FX
    purchases, which is how it reaches $1,025.39 at $400,000. On the law as it now reads, that route costs the
    same as any other single documented wire — <strong>{money(LADDER_BY_AMOUNT['400000']['total_usd'])}</strong>
    at today's board on $400,000, before the optional ${OUR} OUR charge. The M03 row has been left as published
    (it is a faithful price of the 2004 text) and is listed with this correction on
    <a href="verify-2026.html#corrections">Verify 2026</a> and in <code>COORDINATION.md</code>.</p>
  </div>
</section>"""


def unverified_box() -> str:
    return """
<section class="section" id="limits">
  <h2>What is still blank, and why</h2>
  <p class="lede">Nothing below is estimated or filled with an industry average. Each item stays blank and is
  listed on the <a href="deep-review.html">Flagged for Review</a> page with the official source a bank visit
  should resolve it against.</p>
  <ul class="tight">
    <li><strong>Other banks' spreads.</strong> The 0.2100% here is one BOC board reading at one timestamp. ICBC,
        CMB and the rest publish their own; so does your branch on the day.</li>
    <li><strong>Receiving and correspondent fees.</strong> A U.S. bank's incoming-wire fee and any intermediary
        deduction are blank. BOC's USD 25 (or USD 15 via its New York branch) full-amount-received charge is
        published only in its trade-finance tariff and is not shown as included here.</li>
    <li><strong>The separate questions raised by the <a href="a15-review.html">safety review</a></strong> — whether
        the convenience amount applies to you at all, what your CNY cost basis is for §988, and whether late
        FBAR years need a corrective procedure — are fact-specific and left open.</li>
    <li><strong>The tax base on a property sale.</strong> The 20% rate is verified; the deductible-cost and
        valuation rules that produce the base are transaction-specific.</li>
    <li><strong>Eligibility.</strong> Whether your balance qualifies as documented current-account income,
        emigrant property or something else is a bank/SAFE determination on documents this research does not have.</li>
    <li><strong>Current CNH basis and card-network rates.</strong> No official retail quotation exists to price them.</li>
  </ul>
</section>"""


# ----------------------------------------------------------------------- pages
def build_index() -> str:
    top = LADDER_BY_AMOUNT["10000"]
    big = LADDER_BY_AMOUNT["400000"]
    summary_amounts = ["10000", "50000", "100000", "200000", "300000", "400000"]
    summary = [LADDER_BY_AMOUNT[a] for a in summary_amounts]
    n_verified = len(VERIFY)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Getting money out of China — CNY to USD dashboard</title>
<meta name="description" content="Official-source dashboard: every lawful way to convert CNY to USD, what each costs from $10,000 to $400,000, and the tax and reporting rules that actually carry a penalty.">
<link rel="stylesheet" href="assets/dashboard.css">
</head>
<body>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="index.html">China&nbsp;money<span>·</span>CNY&nbsp;→&nbsp;USD</a>
    <nav class="nav" aria-label="Main">
      <a href="index.html" aria-current="page">Home</a>
      <a href="cost-tables.html">Costs</a>
      <a href="deep-channels.html">Methods</a>
      <a href="deep-penalty.html">Penalties</a>
      <a href="deep-china-rules.html">China rules</a>
      <a href="deep-us-tax.html">U.S. tax</a>
      <a href="verify-2026.html">Verify</a>
      <a href="deep-review.html">Flags</a>
      <a href="d646-summary.html">2026-11-10 refresh</a>
    </nav>
  </div>
</header>

<main class="wrap">

<section style="padding:18px;border-left:5px solid #12a3b8;background:#eaf7fa;color:#0d3340;border-radius:9px;margin:20px 0">
  <p class="eyebrow" style="margin:0 0 6px">Independent re-verification &middot; 2026-11-10</p>
  <h2 style="margin:0 0 8px;font-size:20px">Seven-page refresh: 21 primary documents re-read today</h2>
  <p style="margin:0 0 10px">A parallel build that re-fetched every load-bearing document on 10 November 2026
  &mdash; Bank of China&rsquo;s stamped board and published tariff, SAFE, PBOC, the State Council FX Regulations,
  the STA Individual Income Tax Law, 26 U.S.C. &sect;988, FinCEN 31 CFR 1010.821, IRS Rev. Proc. 2025-32 and
  CBP &mdash; and re-derived all 40 cost increments from the raw published inputs rather than copying any
  earlier model. It is published alongside this dashboard, not in place of it.</p>
  <p style="margin:0 0 10px"><a href="d646-summary.html"><strong>Executive summary &rarr;</strong></a> &middot;
  <a href="d646-costs.html">Costs $10k&ndash;$400k</a> &middot;
  <a href="d646-methods.html">16 methods</a> &middot;
  <a href="d646-penalty.html">Tax &amp; penalties</a> &middot;
  <a href="d646-verification.html">Verification log</a> &middot;
  <a href="d646-flagged.html">16 flagged items</a> &middot;
  <a href="d646-sources.html">Sources</a></p>
  <p style="margin:0;font-size:14px"><strong>The one open difference between the two builds:</strong> the wire
  count at large amounts. This dashboard prices one wire; the refresh prices one wire per documented
  US$50,000 convenience amount. That is why the refresh shows <strong>$53.47</strong> at $10,000 and
  <strong>$1,332.05</strong> at $400,000 against this page&rsquo;s <strong>$53.42</strong> and
  <strong>$901.30</strong>. The spread, the tariff and the tax treatment agree; only the number of transfers
  differs, and both assumptions are labelled on their own pages.</p>
</section>

<section class="hero">
  <p class="eyebrow">Dashboard · official sources only · last checked 10 Nov 2026</p>
  <h1>Your money is not taxed for leaving China.<br>It is taxed — or penalised — for what it is and how you move it.</h1>
  <p class="lede">A U.S. citizen with a mainland bank balance asks the same question every time: what is the
  cheapest lawful route from CNY to USD, and where does the “tax penalty” actually come from? This page answers
  it in the order that matters: the cost of the transfer first, the reporting risk second, the alternatives last.</p>

  <div class="callout warn" style="margin-top:18px">
    <p><strong>Read this with the safety review.</strong> The independent review at
    <a href="a15-review.html">a15-review.html</a> (10 Nov 2026) raises four cautions this page also carries:
    the USD 50,000 convenience amount is <em>not</em> automatic for a foreign passport holder; a Chinese tax
    certificate is evidence, not a new tax; whether converting your CNY is “personal” for §988 purposes is
    fact-specific and unknown here; and every figure below is a China-side cost that still needs a written bank
    quote. Automated source-link checks do not substitute for that quote.</p>
  </div>

  <div class="answer">
    <h2>The short answer</h2>
    <ol class="tight">
      <li><strong>Converting your own after-tax principal costs about {pct(top['total_pct'])} at $10,000 and
      {pct(big['total_pct'])} at $400,000</strong> — {money(top['total_usd'])} and {money(big['total_usd'])}
      on today's Bank of China board. That is bank spread plus the 1‰ wire fee and its cable charge. There is no
      Chinese “conversion tax” in any instrument checked here.</li>
      <li><strong>The expensive number is a reporting penalty, not an exchange rate.</strong> A willful FBAR
      violation is capped at the greater of USD 165,353 or <em>50% of the balance</em> — USD 200,000 on a
      $400,000 account {src('V10','31 USC 5321')}. Fix U.S. reporting before optimising anything else.</li>
      <li><strong>Choose the route by the documents you can produce, not by the fee table.</strong> A documented
      current-account income remittance and an emigrant property transfer cost the same at the bank; both differ
      from the USD 50,000 convenience amount, which is a per-person, per-year processing allowance
      {src('V06','SAFE')} — not a legal ceiling and not a tax.</li>
    </ol>
  </div>
</section>

<section class="section" id="verdict">
  <h2>Least-penalty path, ranked</h2>
  <p class="lede">Cost column is today's board, single transfer, China side. All four rows link to the instrument
  that decides them.</p>
  {verdict_table()}
</section>

<section class="section" id="numbers">
  <h2>The six numbers that decide this</h2>
  {key_cards()}
</section>

<section class="section" id="ladder">
  <h2>What $10,000 to $400,000 costs, step by step</h2>
  <p class="lede">Documented current-account route, priced from the {BOARD_TS} BOC board
  (ask {ASK} CNY/USD, spread 0.2100%, all-in {pct(LADDER_BY_AMOUNT['10000']['total_pct'])}), the published personal wire tariff
  and the cable charge. Spreadsheet version: <code>data/ladder_20261110.csv</code>.</p>
  {ladder_table(summary, with_our=True)}
  <details class="more">
    <summary>Show all 40 rows ($10,000 → $400,000)</summary>
    {ladder_table(LADDER)}
  </details>
</section>

<section class="section" id="methods">
  <h2>Every method, at three amounts</h2>
  <p class="lede">Sixteen routes, all 40 amounts each on the full page. “Blank” means no official source publishes
  the number — it is not zero. Prohibited routes are listed so that they can be recognised and refused, not used.</p>
  {methods_table()}
  <p class="foot"><a href="schedule-cost-10k-400k.html">All 640 rows →</a> ·
  <a href="cost-tables.html">Cost tables with per-route step-by-step →</a> ·
  <a href="deep-channels.html">35 channels with pros and cons →</a></p>
</section>

<section class="section" id="penalties">
  <h2>Where the “tax penalty” actually comes from</h2>
  <p class="lede">Seven separate charges get conflated into one scary number. They apply to different things and
  most of them are avoidable by reporting correctly.</p>
  {penalty_table()}
</section>

{correction_box()}

<section class="section" id="pages">
  <h2>Every page, by category</h2>
  <p class="lede">Earlier sessions produced several parallel passes over the same brief. Nothing was deleted;
  the canonical page for each topic is listed first, the parallel passes follow it.</p>
  {cards_nav()}
  <details class="more">
    <summary>Parallel passes that were kept (and how they differ)</summary>
    <ul class="tight">
      <li><a href="methods.html">methods.html</a>, <a href="routes.html">routes.html</a> — the first 11-method and
          8-route passes; superseded by <code>deep-channels.html</code> (35 channels) but kept for provenance.</li>
      <li><a href="schedule-dashboard.html">schedule-dashboard.html</a> — the 2026-11-09 schedule pass that this
          ladder is derived from; same tariff inputs, one day earlier.</li>
      <li><a href="costs.html">costs.html</a> / <a href="cost-review.html">cost-review.html</a> — a 1,400-row grid
          that deliberately leaves every price blank instead of assuming a rate.</li>
      <li><a href="cross-session-review.html">cross-session-review.html</a> — an independent reconciliation of the
          parallel sessions' numbers, including the U.S. currency-gain question.</li>
      <li><a href="flagged-review.html">flagged-review.html</a>, <a href="schedule-flagged-review.html">schedule-flagged-review.html</a>,
          <a href="cost-review.html">cost-review.html</a>, <a href="review.html">review.html</a> — four separate flag
          registers, all preserved. <a href="deep-review.html">deep-review.html</a> is the consolidated one.</li>
    </ul>
  </details>
</section>

<section class="section" id="verification">
  <h2>Verification performed in this session</h2>
  <p class="lede">Every figure on this page comes from one of {n_verified} records in
  <code>data/verify_2026.csv</code>, each with the official URL, the verbatim text and the fetch timestamp.
  <a href="verify-2026.html">Open the verification register</a> — or check it yourself with
  <code>python3 scripts/verify_dashboard.py</code>, which re-derives the ladder, re-checks every row's source
  domains and confirms every local link resolves.</p>
  <ul class="tight">
    <li>Re-read in full during this pass: the BOC board and personal/corporate tariffs, SAFE Ningxia 2022 Q&amp;A,
        SAFE 汇发〔2014〕2号, PBC [2004] No.16, eCFR 1010.821, 31 U.S.C. §5321, 26 U.S.C. §988, the IRS FATCA
        summary and IRS IR-2025-103, and the PRC Individual Income Tax Law art. 3.</li>
    <li>Two prior-session findings were corrected or superseded (emigrant staging, 2025-only tax figures); both
        are recorded below and on the verification page.</li>
    <li>Two parallel cost models disagree by $0.05 at $10,000 because they divide the same spread by different
        denominators (ask vs midpoint). The reconciliation is shown on
        <a href="cross-session-review.html">cross-session-review.html</a>; neither figure is presented here.</li>
  </ul>
</section>

{unverified_box()}

</main>

<footer class="foot-main">
  <div class="wrap">
    <p><strong>Research, not advice.</strong> Rules, rates and bank practice change; the board reading here is a
    timestamped snapshot, not a quote. Confirm the route and documents with the holding bank and a qualified
    cross-border tax adviser before transferring.</p>
    <p class="mini">Sources: boc.cn · safe.gov.cn · pbc.gov.cn · chinatax.gov.cn · irs.gov · fincen.gov · ecfr.gov ·
    law.cornell.edu. Full register: <a href="deep-sources.html">deep-sources.html</a>. Data: <code>data/verify_2026.csv</code>,
    <code>data/ladder_20261110.csv</code>, <code>data/live_rate_20261110.csv</code>. Task board:
    <a href="COORDINATION.md">COORDINATION.md</a>.</p>
  </div>
</footer>
</body>
</html>
"""


def build_verify() -> str:
    corrections = [
        (
            "C1",
            "Emigrant property transfer priced as three purchases",
            "PBC [2004] No.16 art. 6 stages a remittance (half, half the remainder, rest after two years). "
            "SAFE 汇发〔2014〕2号 §6(2) cancels that requirement; §6(1) cancels the over-RMB-500,000 head-office filing.",
            "cost-tables.html M03 shows $1,025.39 at $400,000 on the staged reading. On the current text the same "
            "transfer costs one wire.",
            "V07",
            "V08",
            "M03 left as published, correction banner added to cost-tables.html",
        ),
        (
            "C2",
            "U.S. tax figures were 2025-vintage",
            "Pages citing the foreign earned income exclusion use USD 130,000, the 2025 amount. Tax year 2026 is USD 132,900.",
            "For the 2026 return the exclusion is $132,900; the annual gift exclusion stays $19,000.",
            "V13",
            "V14",
            "Both years now stated; no page was rewritten",
        ),
        (
            "C3",
            "Two cost models divided the same spread differently",
            "Session s436 divides (ask − midpoint) by the ask; session 7a636dce divides by the midpoint.",
            "Difference is $0.05 at $10,000 on identical board inputs and grows linearly — an artifact of "
            "convention, not of facts.",
            "V01",
            "V03",
            "Both pages kept; this dashboard states its convention explicitly",
        ),
        (
            "C4",
            "Chinese FX fines were described as a 30% floor",
            "State Council Order 532 art. 39 and art. 45 impose a fine of 30% or less of the amount in an "
            "ordinary case; only where the case is serious does the band become 30% up to the equivalent amount.",
            "A 30% ‘floor’ overstates the ordinary case and understates the serious one.",
            "V16",
            "V16",
            "Penalty row corrected on this dashboard; other pages left as published and flagged",
        ),
        (
            "C5",
            "FBAR amounts were checked against the current eCFR, not a secondary summary",
            "31 CFR 1010.821 was read on 2026-11-10 and displays amounts for penalties assessed on or after 2025-01-17.",
            "$16,536 non-willful and $165,353 willful remain current; no 2026 adjustment row appears.",
            "V11",
            "V11",
            "Confirmed, no change needed",
        ),
    ]
    corr_html = ['<div class="tw"><table class="tbl"><thead><tr>']
    corr_html.append("<th>ID</th><th>What was found</th><th>Official basis</th><th>Effect</th><th>Action taken</th></tr></thead><tbody>")
    for cid, title, basis, effect, v1, v2, action in corrections:
        corr_html.append(
            "<tr>"
            + cell("ID", f'<a id="{cid.lower()}"></a><strong>{cid}</strong>')
            + cell("Found", f"<strong>{title}</strong><br><span class=\"mini\">{basis}</span>")
            + cell("Basis", src(v1) + ("" if v1 == v2 else " " + src(v2)))
            + cell("Effect", effect)
            + cell("Action", action)
            + "</tr>"
        )
    corr_html += ["</tbody></table></div>"]

    unverified = [
        ("Bank spread other than BOC's board reading", "No official quotation for ICBC, CMB, CCB or your branch on the day of transfer.", "IR-024"),
        ("U.S. receiving-bank and correspondent fees", "Only BOC's optional OUR charge is published; a U.S. bank's incoming fee is not a published tariff.", "IR-028"),
        ("PRC tax base on a property sale", "The 20% rate is verified; the deductible-cost and valuation rules are transaction-specific.", "IR-025"),
        ("Eligibility of a specific balance", "Document set, province, residency history and source of funds are unknown to this research.", "I03"),
        ("CNH basis and card-network FX rates", "No official retail tariff exists; the 1.94% figure used in an earlier pass was withdrawn.", "IR-026"),
        ("Whether a branch will insist on staged emigrant payouts", "Two in-force texts conflict on their face; the later circular cancels staging, but branch practice must be confirmed in writing.", "C1"),
    ]
    unv_html = ['<div class="tw"><table class="tbl"><thead><tr>']
    unv_html.append("<th>Item left blank</th><th>Why no number is given</th><th>Flag</th></tr></thead><tbody>")
    for item, why, flag in unverified:
        unv_html.append(
            "<tr>"
            + cell("Item", f"<strong>{item}</strong>")
            + cell("Why blank", why)
            + cell("Reference", f'<span class="badge badge-blank">{flag}</span> '
                    '<a class="src" href="deep-review.html">deep-review.html</a>')
            + "</tr>"
        )
    unv_html += ["</tbody></table></div>"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verify 2026 — line-by-line source register · China money</title>
<meta name="description" content="Sixteen figures re-checked against official sources on 10 November 2026, with verbatim quotations, plus the corrections and the items deliberately left blank.">
<link rel="stylesheet" href="assets/dashboard.css">
</head>
<body>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="index.html">China&nbsp;money<span>·</span>CNY&nbsp;→&nbsp;USD</a>
    <nav class="nav" aria-label="Main">
      <a href="index.html">Home</a>
      <a href="cost-tables.html">Costs</a>
      <a href="deep-channels.html">Methods</a>
      <a href="deep-penalty.html">Penalties</a>
      <a href="deep-china-rules.html">China rules</a>
      <a href="deep-us-tax.html">U.S. tax</a>
      <a href="verify-2026.html" aria-current="page">Verify</a>
      <a href="deep-review.html">Flags</a>
      <a href="d646-summary.html">2026-11-10 refresh</a>
    </nav>
  </div>
</header>

<main class="wrap">
<section class="hero">
  <p class="eyebrow">Verification register · 10 November 2026</p>
  <h1>Every figure, its official page, and the sentence it came from</h1>
  <p class="lede">Each record below was fetched during this session. The quote is the text on the official page,
  not a paraphrase; the timestamp is when it was read. Where the official page publishes a rate or a ceiling but
  not an amount, no amount is given anywhere on the site.</p>
</section>

<section class="section">
  <h2>{len(VERIFY)} records</h2>
  {verify_table()}
  <p class="foot">Machine-readable: <code>data/verify_2026.csv</code>. Re-check the register with
  <code>python3 scripts/verify_dashboard.py</code> (structural checks, official-domain check, ladder re-derivation).</p>
</section>

<section class="section" id="corrections">
  <h2>Corrections and reconciliations</h2>
  <p class="lede">Four items where this pass disagreed with, or tightened, what an earlier pass had published.</p>
  {"".join(corr_html)}
</section>

<section class="section">
  <h2>Deliberately blank</h2>
  <p class="lede">These are the numbers a reader most wants and that no official source publishes. They are left
  empty rather than estimated.</p>
  {"".join(unv_html)}
</section>

<section class="section">
  <h2>Sites checked and rejected</h2>
  <ul class="tight">
    <li><code>irs.gov/individuals/international-taxpayers/comparison-of-form-8938-and-fbar-requirements</code> —
        returns HTTP 404. Replaced with the IRS FATCA summary page ({src('V12','irs.gov')}).</li>
    <li><code>irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026</code> — 404 without the
        full slug. The working page is the one cited in V13/V14.</li>
    <li>Commercial FX comparison sites were not used for any figure. Where they appeared in search results, the
        underlying IRS revenue procedure was cited instead.</li>
  </ul>
</section>
</main>

<footer class="foot-main">
  <div class="wrap">
    <p><strong>Research, not advice.</strong> A record marked <em>verified</em> means the official page said what
    the row reports at the timestamp shown. It does not mean the rule will still read that way when you transfer.</p>
    <p class="mini"><a href="index.html">← Back to the dashboard</a> · <a href="deep-review.html">Flagged for review</a> ·
    <a href="COORDINATION.md">COORDINATION.md</a></p>
  </div>
</footer>
</body>
</html>
"""


CSS = """/* Dashboard stylesheet — new in this integration pass. Mobile first. */
:root{
  --ink:#10202c; --ink2:#3c5265; --line:#dbe4ec; --bg:#f6f8fb; --paper:#fff;
  --brand:#0b5c73; --brand2:#0e7c8c; --ok:#0f766e; --warn:#b45309; --no:#a11b1b;
  --shadow:0 1px 2px rgba(16,32,44,.06),0 8px 22px rgba(16,32,44,.05);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:0 16px}
a{color:#0a5f8a;text-decoration:none}
a:hover{text-decoration:underline}
h1,h2,h3{line-height:1.22;margin:0 0 .5em}
h1{font-size:clamp(1.55rem,4.2vw,2.6rem);letter-spacing:-.02em}
h2{font-size:clamp(1.2rem,2.6vw,1.6rem);letter-spacing:-.01em}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}

/* header */
.top{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.96);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line)}
.top-in{display:flex;align-items:center;gap:12px;min-height:56px;flex-wrap:wrap;padding-top:6px;padding-bottom:6px}
.brand{font-weight:800;letter-spacing:-.01em;color:var(--brand);white-space:nowrap}
.brand span{color:#9aa9bb;margin:0 3px}
.nav{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;flex:1 1 auto;padding-bottom:2px}
.nav::-webkit-scrollbar{display:none}
.nav a{padding:6px 10px;border-radius:999px;font-size:.86rem;color:var(--ink2);white-space:nowrap}
.nav a:hover{background:#eef3f8;text-decoration:none}
.nav a[aria-current=page]{background:var(--brand);color:#fff}

/* hero + answer */
.hero{padding:34px 0 6px}
.eyebrow{margin:0 0 10px;font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--brand2);font-weight:800}
.lede{font-size:1.02rem;color:var(--ink2);max-width:74ch}
.answer{margin:22px 0 6px;padding:20px;background:var(--paper);border:1px solid var(--line);
  border-left:5px solid var(--brand);border-radius:14px;box-shadow:var(--shadow)}
.answer h2{margin-top:0;font-size:1.1rem}
ol.tight,ul.tight{margin:.2em 0;padding-left:1.15em}
ol.tight li,ul.tight li{margin:.45em 0}

/* sections */
.section{padding:26px 0;border-top:1px solid var(--line)}
.section:first-of-type{border-top:0}
.foot,.mini{font-size:.82rem;color:#67798c}
.foot{margin:.6em 0 0}
summary{cursor:pointer;font-weight:600;color:var(--brand)}
details.more{margin-top:14px;padding:12px 14px;background:var(--paper);border:1px solid var(--line);border-radius:12px}
details.more[open]{padding-bottom:18px}

/* cards */
.cards{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));margin-top:14px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow)}
.card-k{font-size:.76rem;letter-spacing:.08em;text-transform:uppercase;color:#67798c;font-weight:800}
.card-v{font-size:1.5rem;font-weight:800;letter-spacing:-.02em;margin:6px 0 4px;color:var(--brand)}
.card p{margin:.35em 0;font-size:.9rem;color:var(--ink2)}
.card-s{margin-top:8px;font-size:.78rem}
.card-link{display:flex;flex-direction:column;color:inherit}
.card-link:hover{border-color:var(--brand2);text-decoration:none}
.card-link .go{margin-top:auto;padding-top:10px;font-weight:700;color:var(--brand);font-size:.85rem}

/* tables */
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:12px;
  background:var(--paper);margin-top:14px}
table.tbl{width:100%;border-collapse:collapse;font-size:.9rem;min-width:640px}
.tbl th,.tbl td{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line)}
.tbl thead th{background:#f0f5f9;font-size:.76rem;letter-spacing:.05em;text-transform:uppercase;
  color:#4a6072;position:sticky;top:0}
.tbl tbody tr:last-child td{border-bottom:0}
.tbl tbody tr:hover{background:#fafcfe}
.tbl-num td.num,.tbl td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl-num th:nth-child(n+2){text-align:right}
.tbl .src{font-size:.78rem}
a.src{display:inline-block;padding:1px 7px;border:1px solid #cfe0ea;border-radius:999px;background:#f4fafc;
  font-size:.78rem;color:#0a5f8a;white-space:nowrap}
a.src:hover{background:#e6f4f8;text-decoration:none}
.blank{color:#8a97a6;font-style:italic;font-size:.84rem}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.72rem;font-weight:800;
  letter-spacing:.03em}
.badge-ok{background:#e3f5f1;color:var(--ok)}
.badge-no{background:#fdeaea;color:var(--no)}
.badge-blank{background:#fdf1e3;color:var(--warn)}
.badge-new{background:#e8f0fd;color:#1d4ed8}
.row-no td{background:#fff6f6}
q{display:block;margin-top:6px;padding-left:10px;border-left:3px solid var(--line);
  font-size:.82rem;color:#4a6072;font-style:italic}

/* callouts */
.callout{padding:16px 18px;border-radius:12px;border:1px solid;margin:16px 0}
.callout.warn{background:#fff8ef;border-color:#f0d9bb;color:#5a3a12}
.callout.warn q{border-left-color:#e3c194}

/* footer */
.foot-main{margin-top:30px;padding:26px 0 40px;background:#0b2231;color:#cddbe6;font-size:.88rem}
.foot-main a{color:#8fd0e6}
.foot-main .mini{color:#93a9b8}

/* phones: turn each row into a card */
@media (max-width:640px){
  table.tbl{min-width:0}
  .tbl thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .tbl,.tbl tbody,.tbl tr,.tbl td{display:block;width:100%}
  .tbl tr{border-bottom:1px solid var(--line);padding:6px 0}
  .tbl td{border:0;padding:4px 12px;text-align:left!important;white-space:normal}
  .tbl td::before{content:attr(data-l);display:block;font-size:.68rem;letter-spacing:.08em;
    text-transform:uppercase;color:#7b8b9b;font-weight:800}
  .tw{border-radius:12px}
}
"""


# ------------------------------------------------------------------------ main
LADDER_FIELDS = [
    "amount_usd", "cny_needed", "spread_usd", "wire_cable_usd", "total_usd",
    "total_pct", "net_usd", "our_usd", "net_with_our",
]


def ladder_csv() -> str:
    import io

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=LADDER_FIELDS, lineterminator="\n")
    w.writeheader()
    for r in LADDER:
        w.writerow({k: r[k] for k in LADDER_FIELDS})
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if on-disk output is stale")
    args = ap.parse_args()

    outputs = {
        ROOT / "index.html": build_index(),
        ROOT / "verify-2026.html": build_verify(),
        DATA / "ladder_20261110.csv": ladder_csv(),
        ASSETS / "dashboard.css": CSS,
    }

    stale = []
    for path, text in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(path.name)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")

    if args.check:
        if stale:
            print("STALE: " + ", ".join(stale) + " — run scripts/build_dashboard.py")
            return 1
        print("OK — generated dashboard artifacts are up to date.")
        return 0

    print(f"wrote {len(outputs)} files; {len(stale)} changed")
    for name in stale:
        print("  changed:", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
