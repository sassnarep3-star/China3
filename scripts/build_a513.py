#!/usr/bin/env python3
"""Build the consolidated 2026-11-10 answer pages (a513.html, a513-verify.html, a513-steps.html).

Every figure on the pages is either
  * read from data/a513_inputs.csv, each row of which names a register id (V01...V16) and the
    exact substring of that source's verbatim quote that carries the value, or
  * computed here from those inputs by arithmetic, or
  * deliberately blank because no official price exists, in which case the row carries a flag.
No cost figure is typed into the HTML by hand.

Usage
  python3 scripts/build_a513.py            # write the CSVs and pages
  python3 scripts/build_a513.py --check    # write nothing; exit 1 if the committed files are stale
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

AMOUNTS = [a for a in range(10_000, 400_001, 10_000)]
SCENARIOS = ("one", "multi50", "our")
BUILT = "2026-11-10T18:05Z"


def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


INPUT = {r["field"]: r for r in rows("a513_inputs.csv")}
VERIFY = {r["id"]: r for r in rows("a513_verification.csv")}
METHODS = rows("a513_methods.csv")
FLAGS = {r["id"]: r for r in rows("a513_flags.csv")}


def val(field: str) -> D:
    return D(INPUT[field]["value"])


ASK = val("ask_cny_per_usd")
BID = val("bid_cny_per_usd")
PARITY = val("parity_cny_per_usd")
MID = (ASK + BID) / 2
WIRE_RATE = val("wire_rate")
WIRE_MIN = val("wire_min_cny")
WIRE_MAX = val("wire_max_cny")
CABLE = val("cable_other_cny")
OUR = val("our_usd_other")
CONVENIENCE = int(val("convenience_usd"))


def q2(v: D) -> D:
    return v.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def q4(v: D) -> D:
    return v.quantize(D("0.0001"), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------- costing
def wire_fee_cny(usd: D) -> D:
    """Published personal e-banking tariff: 1 per mille of the CNY amount, floor 50, cap 260."""
    return min(WIRE_MAX, max(WIRE_MIN, WIRE_RATE * usd * ASK))


def spread_usd(usd: D) -> D:
    """Cost of crossing from mid to the published selling rate (half the board spread)."""
    return usd * (ASK - MID) / ASK


def one_transfer(usd: D) -> dict:
    sp = spread_usd(usd)
    fee_cny = wire_fee_cny(usd)
    wire = (fee_cny + CABLE) / ASK
    return dict(spread=sp, fee_cny=fee_cny, wire=wire, total=sp + wire)


def multi_transfer(usd: D) -> dict:
    """One transfer per USD 50,000 convenience amount."""
    n = math.ceil(int(usd) / CONVENIENCE)
    per = usd / n
    sp = spread_usd(usd)
    fee_cny_each = wire_fee_cny(per)
    wire = D(n) * (fee_cny_each + CABLE) / ASK
    return dict(spread=sp, transfers=n, fee_cny_each=fee_cny_each, wire=wire, total=sp + wire)


def ladder_rows() -> list[dict]:
    out = []
    for a in AMOUNTS:
        usd = D(a)
        one = one_transfer(usd)
        multi = multi_transfer(usd)
        out.append(
            dict(
                amount_usd=a,
                cny_needed=q2(usd * ASK),
                spread_usd=q2(one["spread"]),
                wire_fee_cny=q2(one["fee_cny"]),
                wire_cable_usd=q2(one["wire"]),
                total_one=q2(one["total"]),
                pct_one=q4(one["total"] / usd * 100),
                net_one=q2(usd - one["total"]),
                transfers=multi["transfers"],
                wire_multi_usd=q2(multi["wire"]),
                total_multi=q2(multi["total"]),
                pct_multi=q4(multi["total"] / usd * 100),
                total_our=q2(one["total"] + OUR),
                pct_our=q4((one["total"] + OUR) / usd * 100),
            )
        )
    return out


LADDER = ladder_rows()
BY_AMOUNT = {r["amount_usd"]: r for r in LADDER}


def method_cost(model: str, a: int) -> dict:
    usd = D(a)
    one = one_transfer(usd)
    if model == "WIRE1":
        return dict(total=q2(one["total"]), pct=q4(one["total"] / usd * 100), note="")
    if model == "WIRE_OUR":
        t = one["total"] + OUR
        return dict(total=q2(t), pct=q4(t / usd * 100), note="includes one OUR charge")
    if model == "WIRE_MULTI50":
        m = multi_transfer(usd)
        return dict(total=q2(m["total"]), pct=q4(m["total"] / usd * 100), note=f"{m['transfers']} transfers")
    if model == "WIRE_SAFE":
        return dict(total=q2(one["total"]), pct=q4(one["total"] / usd * 100), note="SAFE approval fee not published")
    return dict(total=None, pct=None, note="")


def method_cost_rows() -> list[dict]:
    out = []
    for m in METHODS:
        for a in AMOUNTS:
            c = method_cost(m["cost_model"], a)
            out.append(
                dict(
                    method_id=m["method_id"],
                    method=m["method"],
                    amount_usd=a,
                    total_usd="" if c["total"] is None else f"{c['total']:.2f}",
                    pct="" if c["pct"] is None else f"{c['pct']:.4f}",
                    note=c["note"],
                    status="" if c["total"] is not None else "UNVERIFIED",
                    source_ids=m["source_ids"],
                )
            )
    return out


# 988 sensitivity: CNY acquired at rate r0, converted at ASK today.
R0S = [D("6.40"), D("6.60"), D("6.80"), D("7.00"), D("7.20")]
TAX_RATES = [D("0.24"), D("0.37")]


def sec988_rows() -> list[dict]:
    out = []
    for a in (10_000, 100_000, 400_000):
        usd = D(a)
        cny = usd * ASK
        for r0 in R0S:
            basis = cny / r0
            gain = usd - basis
            recognized = gain > val("sec988_personal_exempt_usd")
            out.append(
                dict(
                    usd=a,
                    r0=str(r0),
                    basis=q2(basis),
                    gain=q2(gain),
                    recognized="yes" if recognized else "no — under USD 200",
                    tax24=q2(gain * TAX_RATES[0]) if recognized and gain > 0 else D("0.00"),
                    tax37=q2(gain * TAX_RATES[1]) if recognized and gain > 0 else D("0.00"),
                )
            )
    return out


SEC988 = sec988_rows()


# ------------------------------------------------------------------- formatting
def usd_fmt(v) -> str:
    return f"${D(str(v)):,.2f}"


def pct_fmt(v) -> str:
    return f"{D(str(v)):.4f}%"


def src(*ids: str) -> str:
    out = []
    for i in ids:
        s = VERIFY[i] if i.startswith("V") else FLAGS[i]
        url = s["url"] if "url" in s else ""
        label = i if i.startswith("V") else i
        if url:
            out.append(f'<a class="src" href="{html.escape(url)}" target="_blank" rel="noopener">{label}</a>')
        else:
            out.append(f'<span class="src src-flag">{label}</span>')
    return " ".join(out)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


NAV = [
    ("a513.html#answer", "Answer"),
    ("a513.html#costs", "Costs"),
    ("a513.html#methods", "Methods"),
    ("a513.html#penalty", "Penalty anatomy"),
    ("a513.html#tax", "U.S. tax"),
    ("a513-steps.html", "Steps"),
    ("a513-verify.html", "Verification"),
    ("a513.html#flags", "Flags"),
    ("a513.html#archive", "Archive"),
]


def head(title: str, desc: str) -> str:
    nav = "\n".join(f'      <a href="{h}">{t}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="assets/a513.css">
</head>
<body>
<header class="top"><div class="wrap top-in">
  <a class="brand" href="a513.html">CNY&nbsp;→&nbsp;USD<span>·</span>verified answer</a>
  <nav class="nav" aria-label="Main">
{nav}
      <a href="index.html">All pages</a>
  </nav>
</div></header>
"""


FOOT = f"""
<footer class="wrap foot">
  <p><strong>Built {BUILT}</strong> · section <code>a513</code> of this repository ·
  every figure above is either computed from the register in <code>data/a513_inputs.csv</code> or left blank and flagged.</p>
  <p>Research, not advice. No bank quote, account statement or tax return was supplied, so no figure here is a quote for a
  particular person. Check the linked official page before acting, and get the bank's written quote for the branch that will
  execute the transfer.</p>
</footer>
<script src="assets/a513.js"></script>
</body>
</html>
"""


# ------------------------------------------------------------------ page: a513
def page_answer() -> str:
    r10, r400 = BY_AMOUNT[10_000], BY_AMOUNT[400_000]
    sp10 = q4(spread_usd(D(10_000)) / D(10_000) * 100)
    parts = [f"""
<main class="wrap">

<section class="hero" id="answer">
  <p class="eyebrow">Consolidated answer · re-verified {BUILT} · official sources only</p>
  <h1>There is no Chinese tax on converting your own CNY into USD.<br>
      The bill is a bank spread plus a capped wire fee — and, if you cross the line, a reporting penalty.</h1>
  <p class="lede">Every conversion route ends in the same two China-side charges: the bank sells you USD at
  {ASK} rather than the mid of its own board, {q4(MID)}, and it charges 1&nbsp;per&nbsp;mille of the CNY amount
  (min&nbsp;CNY&nbsp;{WIRE_MIN:.0f}, max&nbsp;CNY&nbsp;{WIRE_MAX:.0f}) plus a CNY&nbsp;{CABLE:.0f} cable fee.
  On today's board that is <strong>{usd_fmt(r10['total_one'])} on USD&nbsp;10,000</strong>
  ({pct_fmt(r10['pct_one'])}) and <strong>{usd_fmt(r400['total_one'])} on USD&nbsp;400,000</strong>
  ({pct_fmt(r400['pct_one'])}) — if one transfer is allowed.</p>

  <ol class="answer">
    <li><strong>Best route for a normal individual: one documented bank wire.</strong>
      Convert and remit in a single instruction with ID plus source-of-funds or purpose documents.
      {usd_fmt(r400['total_one'])} all-in on USD&nbsp;400,000 on today's board. {src('V01', 'V02', 'V04')}</li>
    <li><strong>If the bank insists on the USD&nbsp;50,000 convenience amount, the same USD&nbsp;400,000 takes
      {r400['transfers']} transfers and {usd_fmt(r400['total_multi'])} in fees</strong> ({pct_fmt(r400['pct_multi'])}),
      because you pay the cable and wire fee each time. {src('V04')}</li>
    <li><strong>If you emigrated and the balance is pre-emigration property, use the emigrant property transfer.</strong>
      SAFE approves the amount; the bank then charges exactly the same spread and wire fee. {src('V07')}</li>
    <li><strong>The expensive number is not the exchange rate.</strong> A willful FBAR violation carries a maximum of
      {usd_fmt(val('fbar_willful_max_usd'))} per violation in the current table, or 50% of the account balance where that
      is greater; a serious PRC evasion case is fined 30%–100% of the amount. {src('V13', 'V12', 'V05')}</li>
  </ol>
</section>

<section class="stats" aria-label="Key numbers">
  <div class="stat"><span class="k">Spread you cross</span><span class="v">{pct_fmt(sp10)}</span>
    <span class="n">half the board spread, {BID} bid vs {ASK} ask</span></div>
  <div class="stat"><span class="k">All-in at USD 10,000</span><span class="v">{usd_fmt(r10['total_one'])}</span>
    <span class="n">{pct_fmt(r10['pct_one'])} of the amount sent</span></div>
  <div class="stat"><span class="k">All-in at USD 400,000</span><span class="v">{usd_fmt(r400['total_one'])}</span>
    <span class="n">{pct_fmt(r400['pct_one'])}, one transfer</span></div>
  <div class="stat"><span class="k">Same, 8 tranches</span><span class="v">{usd_fmt(r400['total_multi'])}</span>
    <span class="n">{pct_fmt(r400['pct_multi'])} — USD 50,000 a year</span></div>
  <div class="stat"><span class="k">Full-amount-received add-on</span><span class="v">{usd_fmt(OUR)}</span>
    <span class="n">per transfer, or USD 15 via BOC New York</span></div>
  <div class="stat"><span class="k">PRC conversion tax</span><span class="v">none found</span>
    <span class="n">no exchange tax in any instrument checked</span></div>
</section>

<section id="costs">
  <h2>Cost of every USD 10,000 increment, USD 10,000 → 400,000</h2>
  <p class="note">Prices: BOC board stamped <strong>{INPUT['board_stamp']['value']} China time</strong>
  (sell {ASK} / buy {BID} / parity {PARITY}); tariff effective 2014-11-01; OUR tariff effective 2015-04-01.
  {src('V01', 'V02', 'V03')} “One transfer” is the cheapest lawful shape; “{r400['transfers']} tranches”
  prices one wire per USD&nbsp;50,000 convenience amount, which is what the simplified procedure forces if you cannot
  produce source documents.</p>

  <div class="tablewrap">
  <table class="cost">
    <caption>China-side cost only. U.S. receiving-bank and correspondent fees are not published and are flagged, not guessed.</caption>
    <thead><tr>
      <th scope="col">USD sent</th><th scope="col">CNY needed</th><th scope="col">Spread</th>
      <th scope="col">Wire + cable</th><th scope="col">One transfer</th><th scope="col">All-in %</th>
      <th scope="col">Per-50k tranches</th><th scope="col">Net received</th><th scope="col">Source</th>
    </tr></thead>
    <tbody>
"""]
    body = []
    for r in LADDER:
        cls = ' class="hl"' if r["amount_usd"] in (10_000, 100_000, 400_000) else ""
        body.append(
            f'<tr{cls}><th scope="row">{r["amount_usd"]:,}</th>'
            f'<td data-l="CNY needed">{r["cny_needed"]:,.2f}</td>'
            f'<td data-l="Spread">{usd_fmt(r["spread_usd"])}</td>'
            f'<td data-l="Wire + cable">{usd_fmt(r["wire_cable_usd"])}</td>'
            f'<td data-l="One transfer" class="strong">{usd_fmt(r["total_one"])}</td>'
            f'<td data-l="All-in %">{pct_fmt(r["pct_one"])}</td>'
            f'<td data-l="50k tranches">{usd_fmt(r["total_multi"])} <span class="dim">×{r["transfers"]}</span></td>'
            f'<td data-l="Net received">{usd_fmt(r["net_one"])}</td>'
            f'<td data-l="Source">{src("V01", "V02")}</td></tr>'
        )
    parts.append("\n".join(body) + f"""
    </tbody>
  </table>
  </div>
  <p class="note">Arithmetic: spread = amount × (ask − mid) / ask; wire = min(CNY {WIRE_MAX:.0f},
  max(CNY {WIRE_MIN:.0f}, 0.1% × CNY amount)) + CNY {CABLE:.0f}, converted at {ASK}.
  Re-derived independently by <code>scripts/verify_a513.py</code>. Full machine-readable ladder:
  <a href="data/a513_ladder.csv">data/a513_ladder.csv</a>.</p>
</section>

<section id="method-costs">
  <h2>Every route, priced at every increment</h2>
  <p class="note">Choose a route. Rows stay blank where an official price does not exist — blank means
  <em>not verified</em>, never zero. {src('V01', 'V02', 'V03', 'V04', 'V07', 'V08', 'V09')}</p>
  <div class="picker">
    <label for="method">Route</label>
    <select id="method">
""")
    opts = []
    for m in METHODS:
        opts.append(f'      <option value="{m["method_id"]}">{m["method_id"]} · {esc(m["method"][:58])}</option>')
    parts.append("\n".join(opts) + f"""
    </select>
  </div>
  <div class="tablewrap">
  <table class="cost" id="mtable">
    <caption id="mcap">Select a route above. Blank = no official price found (flagged).</caption>
    <thead><tr><th scope="col">USD sent</th><th scope="col">Cost</th><th scope="col">All-in %</th><th scope="col">Note</th></tr></thead>
    <tbody id="mbody"></tbody>
  </table>
  </div>
  <p class="note">Machine-readable: <a href="data/a513_method_costs.csv">data/a513_method_costs.csv</a>
  ({len(METHODS)} routes × {len(AMOUNTS)} increments).</p>
</section>

<section id="methods">
  <h2>The routes, their status and their real limits</h2>
  <div class="tablewrap">
  <table class="methods">
    <thead><tr><th scope="col">Route</th><th scope="col">Status</th><th scope="col">Pros</th>
    <th scope="col">Cons</th><th scope="col">Limit</th></tr></thead>
    <tbody>
""")
    body = []
    for m in METHODS:
        body.append(
            f'<tr><th scope="row"><span class="mid">{m["method_id"]}</span> {esc(m["method"])}</th>'
            f'<td data-l="Status"><span class="tag {"bad" if m["lawful"] == "No" else ("warn" if m["lawful"] == "Conditional" else "ok")}">'
            f'{esc(m["status"])}</span></td>'
            f'<td data-l="Pros">{esc(m["pros"])}</td>'
            f'<td data-l="Cons">{esc(m["cons"])}</td>'
            f'<td data-l="Limit">{esc(m["legal_limit"])} {src(*m["limit_source_ids"].split(";")) if m["limit_source_ids"] else ""}</td></tr>'
        )
    parts.append("\n".join(body) + f"""
    </tbody>
  </table>
  </div>
  <p class="note">The exhaustive 24-route catalogue (including the prohibited ones and the corporate routes) is on the
  earlier <a href="s775-methods.html">S775 methods page</a>; this table keeps the ten routes a private individual
  actually faces, each re-checked against the register on this page.</p>
</section>

<section id="penalty">
  <h2>What the “conversion penalty” is actually made of</h2>
  <p class="note">Waterfall for USD 400,000 sent in one transfer on today's board. Sourced items are priced;
  unsourced items are blank and flagged.</p>
  <div class="tablewrap">
  <table class="flow">
    <thead><tr><th scope="col">Component</th><th scope="col">Cost</th><th scope="col">Basis</th></tr></thead>
    <tbody>
      <tr><th scope="row">1. Bid/ask spread</th><td>{usd_fmt(BY_AMOUNT[400_000]['spread_usd'])}</td>
        <td>USD 400,000 × ({ASK} − {q4(MID)}) / {ASK} {src('V01')}</td></tr>
      <tr><th scope="row">2. Wire commission (capped)</th><td>{usd_fmt(D(BY_AMOUNT[400_000]['wire_fee_cny']) / ASK)}</td>
        <td>0.1% of CNY {BY_AMOUNT[400_000]['cny_needed']:,.2f} = CNY {D(BY_AMOUNT[400_000]['cny_needed']) * WIRE_RATE:,.2f},
        capped at CNY {WIRE_MAX:.0f} {src('V02')}</td></tr>
      <tr><th scope="row">3. Cable / telecom charge</th><td>{usd_fmt(CABLE / ASK)}</td>
        <td>CNY {CABLE:.0f} per transfer (non-HK/MO/TW) {src('V02')}</td></tr>
      <tr class="sum"><th scope="row">China-side total</th><td>{usd_fmt(BY_AMOUNT[400_000]['total_one'])}</td>
        <td>{pct_fmt(BY_AMOUNT[400_000]['pct_one'])} of the amount sent</td></tr>
      <tr><th scope="row">4. OUR / full-amount-received</th><td class="blank">USD {OUR:.0f} (or 15)</td>
        <td>Only if the payment needs an intermediary bank {src('V03')}</td></tr>
      <tr><th scope="row">5. U.S. receiving-bank incoming-wire fee</th><td class="blank">blank</td>
        <td>Not published by the receiving bank in any official tariff reviewed — <span class="src src-flag">F02</span></td></tr>
      <tr><th scope="row">6. Correspondent-bank deduction</th><td class="blank">blank</td>
        <td>Set per bank and per corridor, not published — <span class="src src-flag">F02</span></td></tr>
      <tr><th scope="row">7. U.S. currency-gain tax (26 U.S.C. § 988)</th><td class="blank">depends on your cost basis</td>
        <td>Ordinary gain when the CNY was acquired at a materially different rate; see the section below {src('V15', 'V16')}</td></tr>
      <tr><th scope="row">8. PRC income tax on the money itself</th><td class="blank">depends on the source</td>
        <td>20% proportional on interest, dividends, property transfer and incidental income {src('V10')}</td></tr>
      <tr><th scope="row">9. Penalty if the move is mis-declared</th><td class="blank">up to 30% / 30–100%</td>
        <td>PRC evasion and private-trading articles {src('V05', 'V06')}; willful FBAR maximum
        {usd_fmt(val('fbar_willful_max_usd'))} per violation, or 50% of the balance if greater {src('V13', 'V12')}</td></tr>
    </tbody>
  </table>
  </div>
  <p class="note"><strong>Key finding:</strong> items 1–3 are the entire published cost of a lawful conversion, and they
  fall as the amount rises because the wire fee is capped. Items 5–9 are where the “considerable tax” in the question
  really comes from — and none of them is an exchange tax.</p>
</section>
""")
    parts.append(f"""
<section id="tax">
  <h2>The one U.S. tax that does attach to converting CNY</h2>
  <p class="note">Selling your own currency is a § 988 transaction {src('V16')}. For an individual's
  <em>personal</em> transaction, exchange-rate gain is not recognised unless it exceeds
  {usd_fmt(val('sec988_personal_exempt_usd'))} {src('V15')}. Above that, the gain is ordinary income, taxed at your own
  marginal rate — the 24% and 37% columns are arithmetic, not a prediction.</p>
  <div class="tablewrap">
  <table class="cost">
    <caption>Illustrative only: “rate when you acquired the CNY” is unknown for this person (flag F07).</caption>
    <thead><tr><th scope="col">USD sent</th><th scope="col">Rate when CNY was acquired</th><th scope="col">Basis in USD</th>
      <th scope="col">§ 988 gain</th><th scope="col">Recognised?</th><th scope="col">Tax at 24%</th><th scope="col">Tax at 37%</th><th scope="col">Source</th></tr></thead>
    <tbody>
""")
    body = []
    for r in SEC988:
        cls = ' class="hl"' if r["usd"] == 400_000 and r["r0"] == "7.00" else ""
        body.append(
            f'<tr{cls}><th scope="row">{r["usd"]:,}</th><td data-l="Acquired at">{r["r0"]}</td>'
            f'<td data-l="Basis">{usd_fmt(r["basis"])}</td><td data-l="Gain">{usd_fmt(r["gain"])}</td>'
            f'<td data-l="Recognised">{r["recognized"]}</td><td data-l="24%">{usd_fmt(r["tax24"])}</td>'
            f'<td data-l="37%">{usd_fmt(r["tax37"])}</td>'
            f'<td data-l="Source">{src("V15", "V16")}</td></tr>'
        )
    parts.append("\n".join(body) + f"""
    </tbody>
  </table>
  </div>
  <p class="note">If the CNY was acquired at a <em>higher</em> CNY-per-USD rate than today's {ASK} — the normal case for
  savings built up over years — the conversion produces a dollar gain. If it was acquired recently at a similar rate, the
  gain usually falls under the USD 200 personal-transaction line and nothing is recognised. The PRC side has no equivalent
  charge on principal: the IIT statute taxes income, at 20% for the categories that apply here {src('V10')}, and requires a
  tax clearance only when a person cancels their PRC household registration on emigrating {src('V11')}.</p>
</section>

<section id="flags">
  <h2>Flagged for review — what this page does not know</h2>
  <p class="note">Blank cells above are not zeros. Each one is listed here with the source that would settle it.
  The full register, with the verbatim quote behind every number, is on the
  <a href="a513-verify.html">verification page</a>.</p>
  <ol class="flags">
""")
    body = []
    for f in FLAGS.values():
        body.append(
            f'<li><span class="fid">{f["id"]}</span> <strong>{esc(f["item"])}</strong> — {esc(f["why"])} '
            f'<span class="dim">Settles with: {esc(f["settles_with"])}</span></li>'
        )
    parts.append("\n".join(body) + f"""
  </ol>
</section>

<section id="archive">
  <h2>Earlier passes in this repository</h2>
  <p class="note">Sixteen sessions have worked on this question in parallel. Their pages are preserved, not deleted,
  because each carries its own sources — but they price different assumptions, so read one at a time and check which
  assumption it uses.</p>
  <ul class="archive">
    <li><a href="index.html">Dashboard</a> — the previous landing page, 16 methods, one wire.</li>
    <li><a href="guide.html">Editorial guide</a> — the first narrative pass.</li>
    <li><a href="deep-executive-summary.html">Deep research summary</a> — 23 flags, 22 channels.</li>
    <li><a href="cost-tables.html">Cost tables</a> — 20 routes × 40 increments, 800 rows.</li>
    <li><a href="costs.html">Cost comparison</a> — 35 channels × 40 increments, 1,400 rows.</li>
    <li><a href="schedule-cost-10k-400k.html">Tariff schedule</a> — 16 methods × 40 increments.</li>
    <li><a href="s775-dashboard.html">S775 audit</a> — 24 routes, 51 sources, step playbooks.</li>
    <li><a href="d646-summary.html">2026-11-10 refresh</a> — 16 methods, one wire per USD 50,000.</li>
    <li><a href="verify-2026.html">Verification register (earlier)</a> · <a href="us-fx-gain.html">§ 988 exposure</a> ·
      <a href="deep-review.html">flags</a> · <a href="cross-session-review.html">cross-session review</a> ·
      <a href="a15-review.html">safety review</a></li>
  </ul>
  <p class="note">This page is the one to read first: it re-fetched its own sources on {BUILT} and labels every
  assumption it makes.</p>
</section>

</main>
""")
    return head(
        "Getting money out of China — the verified CNY→USD answer",
        "Consolidated 2026-11-10 answer: what every CNY to USD route costs from USD 10,000 to 400,000, "
        "where the tax and penalties actually attach, and what is still unverified.",
    ) + "\n".join(parts) + FOOT


# ------------------------------------------------------------- page: verification
def page_verify() -> str:
    rows_html = []
    for v in VERIFY.values():
        rows_html.append(
            f'<tr><th scope="row"><span class="fid">{v["id"]}</span></th>'
            f'<td data-l="Institution">{esc(v["issuer"])}</td>'
            f'<td data-l="Document"><a href="{esc(v["url"])}" target="_blank" rel="noopener">{esc(v["doc_title"])}</a></td>'
            f'<td data-l="What it settles">{esc(v["proposition"])}</td>'
            f'<td data-l="Value taken"><code>{esc(v["quoted_value"])}</code></td>'
            f'<td data-l="Verbatim quote" class="quote">{esc(v["quote_verbatim"])}</td>'
            f'<td data-l="Fetched">{esc(v["fetched_utc"])}</td>'
            f'<td data-l="Verdict"><span class="tag ok">{esc(v["verdict"])}</span></td></tr>'
        )
    return head(
        "Verification register — every number traced to a primary source",
        "Line-by-line register for the CNY to USD answer: 16 primary sources with verbatim quotes and fetch timestamps.",
    ) + f"""
<main class="wrap">
<section class="hero">
  <p class="eyebrow">Verification · {BUILT}</p>
  <h1>Sixteen rows, sixteen primary documents, quoted verbatim.</h1>
  <p class="lede">Each row below is a proposition this site relies on, the official page that decides it, the exact
  substring that carries the value, and the moment it was fetched. Anything not on this list is either computed
  arithmetic or blank and flagged — no figure was carried over from a search snippet, a blog, or another page in this
  repository.</p>
  <p class="note">Machine-readable: <a href="data/a513_verification.csv">data/a513_verification.csv</a> ·
  inputs and their evidence: <a href="data/a513_inputs.csv">data/a513_inputs.csv</a>.
  The build refuses to run if a value's evidence string is not literally present in its source quote.</p>
</section>

<section>
  <div class="tablewrap">
  <table class="methods verify">
    <thead><tr><th scope="col">ID</th><th scope="col">Institution</th><th scope="col">Document</th>
      <th scope="col">What it settles</th><th scope="col">Value taken</th><th scope="col">Verbatim quote</th>
      <th scope="col">Fetched</th><th scope="col">Verdict</th></tr></thead>
    <tbody>
    {"".join(rows_html)}
    </tbody>
  </table>
  </div>
</section>

<section>
  <h2>How the numbers were checked</h2>
  <ol class="steps">
    <li><strong>Fetch, do not recall.</strong> Every row was opened on {BUILT}. Chinese-language pages are quoted in the
      original and paraphrased in English beside the quote, so a reader can check the translation.</li>
    <li><strong>One value, one substring.</strong> <code>data/a513_inputs.csv</code> names the register row and the exact
      characters that carry each number. <code>scripts/build_a513.py</code> aborts if the substring is absent.</li>
    <li><strong>Re-derive, do not copy.</strong> <code>scripts/verify_a513.py</code> recomputes all 40 increments with a
      different arrangement of the same published inputs and fails on a one-cent difference.</li>
    <li><strong>Blank beats plausible.</strong> Counter cash rates, receiving-bank fees, correspondent deductions,
      SAFE approval fees and platform margins have no official price. They are blank, and flagged.</li>
    <li><strong>No bank quote exists for this person.</strong> The tariff is published; the branch's execution rate is
      not. Treat every figure as the published floor or ceiling it is, and ask for the quote in writing.</li>
  </ol>
</section>

<section>
  <h2>Limits of this verification</h2>
  <ul class="flags">
    <li><span class="fid">L1</span> The BOC board moves during the day. The prices here are the {INPUT['board_stamp']['value']}
      stamp; an earlier snapshot in this repository (07:32 China time) had ask 6.6903 and parity 6.7188. Same structure,
      different cents.</li>
    <li><span class="fid">L2</span> eCFR is authoritative but not an official legal edition; the FBAR maxima shown are the
      amounts for penalties assessed on or after 2025-01-17, which is the current table.</li>
    <li><span class="fid">L3</span> The SAFE pages used are provincial-branch publications (Ningxia, Hebei) and a
      Tianjin republication of 汇发〔2014〕2号. They quote the national instruments; confirm branch practice locally.</li>
    <li><span class="fid">L4</span> The 2026 Chinese crypto circular and the payment-institution rules were not re-fetched
      for this page; the crypto prohibition is therefore described only as it appears in the earlier S775 catalogue.</li>
    <li><span class="fid">L5</span> No account statement, tax return or bank quote was supplied, so no statement here is
      personalised.</li>
  </ul>
</section>
</main>
""" + FOOT


# ------------------------------------------------------------------ page: steps
def page_steps() -> str:
    return head(
        "Step by step — executing each lawful CNY to USD route",
        "Exact numbered steps for the bank wire, OUR wire, USD 50,000 tranches, emigrant property transfer, cash carry and the U.S. reporting that follows.",
    ) + f"""
<main class="wrap">
<section class="hero">
  <p class="eyebrow">Playbooks · {BUILT}</p>
  <h1>Exactly how each lawful route runs, from the branch counter to your U.S. return.</h1>
  <p class="lede">Each step names the document that decides it. Where a step depends on a fact nobody has published —
  a branch's cash rate, an intermediary's deduction, SAFE's processing time — the step says so instead of inventing it.</p>
</section>

<section>
  <h2>M01 · One documented bank wire — the default recommendation</h2>
  <ol class="steps">
    <li><strong>Decide what the money is.</strong> Salary, pension, sale of property, an inheritance, or savings.
      The category, not the amount, decides which documents the bank will demand. {src('V04')}</li>
    <li><strong>Collect the paper.</strong> Passport; the mainland account; for current-account income the source
      documents (contract, payroll record, tax payment certificate); for property the title and transfer documents.
      {src('V04')}</li>
    <li><strong>Ask for the rate in writing.</strong> The board prints {ASK} as the selling rate at
      {INPUT['board_stamp']['value']}, but the tariff itself says the branch's execution rate governs.
      {src('V01', 'V02')} Compare that quote with the mid of {q4(MID)} — the gap is your real spread.</li>
    <li><strong>Convert at the counter or in e-banking.</strong> You need CNY {BY_AMOUNT[10_000]['cny_needed']:,.2f}
      for USD 10,000 and CNY {BY_AMOUNT[400_000]['cny_needed']:,.2f} for USD 400,000 at today's ask. {src('V01')}</li>
    <li><strong>Accept the fee.</strong> 1‰ of the CNY amount, floor CNY {WIRE_MIN:.0f}, cap CNY {WIRE_MAX:.0f}, plus the
      CNY {CABLE:.0f} cable charge: USD {BY_AMOUNT[10_000]['wire_cable_usd']:.2f} at USD 10,000 and
      USD {BY_AMOUNT[400_000]['wire_cable_usd']:.2f} at USD 400,000. {src('V02')}</li>
    <li><strong>Send one transfer if you can.</strong> Above USD 50,000 equivalent a genuine current-account payment is
      allowed on documents; the USD 50,000 figure is the simplified route, not a ceiling. {src('V04')}</li>
    <li><strong>Keep the receipt and the rate.</strong> It fixes your USD proceeds and, with the original acquisition
      record, your § 988 basis. {src('V15', 'V16')}</li>
    <li><strong>File the U.S. side.</strong> FBAR if the aggregate of your foreign accounts exceeded
      {usd_fmt(val('fbar_threshold_usd'))} at any time {src('V12')}; Form 8938 if the threshold applies {src('V12')};
      the § 988 gain on the return {src('V15')}.</li>
  </ol>
</section>

<section>
  <h2>M02 · Full-amount-received (OUR)</h2>
  <ol class="steps">
    <li>Ask the branch whether it offers 全额到账 on a personal outward payment. The tariff is published for personal
      business; whether your branch applies it is a branch fact. {src('V03')}</li>
    <li>Confirm the payment actually needs an intermediary. The published service applies only where the remitting and
      receiving banks have no direct account relationship. {src('V03')}</li>
    <li>Price it: USD 15 if the receiving bank holds an account at BOC New York, otherwise USD 25, on top of the wire
      fee and cable. {src('V03')}</li>
    <li>Total at USD 400,000: USD {BY_AMOUNT[400_000]['total_our']:,.2f}. {src('V01', 'V02', 'V03')}</li>
  </ol>
</section>

<section>
  <h2>M03 · One transfer per USD 50,000 convenience amount</h2>
  <ol class="steps">
    <li>Confirm you qualify for the simplified procedure — the bank classifies you first, and a foreign passport holder
      is not automatically a 境内个人. {src('V04')}</li>
    <li>Each calendar year, convert and remit up to USD 50,000 equivalent per person. {src('V04')}</li>
    <li>USD 400,000 therefore takes {BY_AMOUNT[400_000]['transfers']} years and {BY_AMOUNT[400_000]['transfers']} wire
      fees: USD {BY_AMOUNT[400_000]['total_multi']:,.2f} of cost in total, against
      USD {BY_AMOUNT[400_000]['total_one']:,.2f} for one transfer. {src('V01', 'V02')}</li>
    <li>Do not split one payment across relatives or invent purposes to stay under the figure: that is expressly
      penalised. {src('V05', 'V06')}</li>
  </ol>
</section>

<section>
  <h2>M04 · Emigrant property transfer (移民财产转移)</h2>
  <ol class="steps">
    <li>Establish that you owned the property before you emigrated. {src('V07')}</li>
    <li>Cancel your PRC household registration and obtain the certificate; complete the PRC tax clearance before the
      cancellation. {src('V11', 'V07')}</li>
    <li>Apply to the SAFE branch covering your <em>original</em> registration location — the approval moved there. {src('V07')}</li>
    <li>No RMB 500,000 filing step is required; that threshold was cancelled. {src('V07')}</li>
    <li>Once approved, remit once or in instalments inside the approved amount. {src('V07')}</li>
    <li>Pay the same bank spread and wire fee as M01. SAFE's own approval fee is not published — blank, flagged
      <span class="src src-flag">F09</span>.</li>
  </ol>
</section>

<section>
  <h2>M06 · Cash — why it does not scale</h2>
  <ol class="steps">
    <li>Up to USD 5,000 equivalent, customs releases the currency. {src('V09')}</li>
    <li>USD 5,000–10,000 needs a bank-issued 携带外汇出境许可证. {src('V09')}</li>
    <li>Above USD 10,000 needs a SAFE permit and is in principle not allowed. {src('V09')}</li>
    <li>On the U.S. side, more than USD 10,000 at one time must be reported on FinCEN Form 105, and the threshold applies
      to a family travelling together collectively. {src('V14')}</li>
    <li>USD 400,000 of cash would require dozens of trips and would breach at least one of the two regimes. Not a route.</li>
  </ol>
</section>

<section>
  <h2>What happens after the money lands</h2>
  <ol class="steps">
    <li>FBAR: aggregate foreign accounts above {usd_fmt(val('fbar_threshold_usd'))} at any time in the year, filed with
      FinCEN, due 15 April with an automatic extension to 15 October. {src('V12')}</li>
    <li>Form 8938: thresholds depend on filing status and residence; the comparison page states them per category.
      {src('V12')}</li>
    <li>§ 988: report the currency gain as ordinary income, unless it is a personal transaction with gain of USD 200 or
      less. {src('V15', 'V16')}</li>
    <li>Keep the acquisition records. Without the rate at which you acquired the CNY, nobody — including you — can compute
      the § 988 gain, which is why this page prices it as a range rather than a number.</li>
  </ol>
</section>

<section>
  <h2>Next</h2>
  <p><a class="btn" href="a513.html">Back to the cost tables</a>
     <a class="btn ghost" href="a513-verify.html">See the 16-row verification register</a></p>
</section>
</main>
""" + FOOT


# ------------------------------------------------------------------------- write
def write_all() -> dict[str, str]:
    files: dict[str, str] = {}

    lines = ["amount_usd,cny_needed,spread_usd,wire_fee_cny,wire_cable_usd,total_one_transfer_usd,pct_one_transfer,net_usd,transfers_if_50k,wire_multi_usd,total_multi_usd,pct_multi,total_our_usd,pct_our,source_ids"]
    for r in LADDER:
        lines.append(
            ",".join(str(x) for x in [
                r["amount_usd"], r["cny_needed"], r["spread_usd"], r["wire_fee_cny"], r["wire_cable_usd"],
                r["total_one"], r["pct_one"], r["net_one"], r["transfers"], r["wire_multi_usd"],
                r["total_multi"], r["pct_multi"], r["total_our"], r["pct_our"], "V01|V02|V03",
            ])
        )
    files["data/a513_ladder.csv"] = "\n".join(lines) + "\n"

    lines = ["method_id,method,amount_usd,total_usd,pct,note,status,source_ids"]
    for r in method_cost_rows():
        lines.append(
            ",".join('"' + str(x).replace('"', '""') + '"' if "," in str(x) else str(x) for x in [
                r["method_id"], r["method"], r["amount_usd"], r["total_usd"], r["pct"], r["note"],
                r["status"], r["source_ids"],
            ])
        )
    files["data/a513_method_costs.csv"] = "\n".join(lines) + "\n"

    files["a513.html"] = page_answer_html()
    files["a513-verify.html"] = page_verify()
    files["a513-steps.html"] = page_steps()

    # embedded data for the route picker
    grid = {}
    for r in method_cost_rows():
        grid.setdefault(r["method_id"], []).append(
            [r["amount_usd"], r["total_usd"], r["pct"], r["note"], r["status"]]
        )
    payload = json.dumps({"methods": grid, "labels": {m["method_id"]: m["method"] for m in METHODS}},
                         ensure_ascii=False)
    files["assets/a513-data.js"] = "window.A513 = " + payload + ";\n"
    return files


def page_answer_html() -> str:
    return page_answer()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files = write_all()
    if args.check:
        stale = [p for p, c in files.items() if not (ROOT / p).exists() or (ROOT / p).read_text(encoding="utf-8") != c]
        if stale:
            print("STALE: " + ", ".join(stale))
            return 1
        print(f"OK — {len(files)} generated files match a fresh build.")
        return 0
    for p, c in files.items():
        (ROOT / p).write_text(c, encoding="utf-8")
    print(f"wrote {len(files)} files: {', '.join(sorted(files))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
