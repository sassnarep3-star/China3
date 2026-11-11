#!/usr/bin/env python3
"""Build the f52 layer: data/f52_*.csv + f52-*.html from scripts/f52_data.py.

Run: python3 scripts/build_f52_site.py
All money math uses Decimal; unverified values stay blank (None -> "").
"""
import csv, html, os, sys
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f52_data import (RATE, AMOUNTS, SOURCES, SRC, METHODS, PROHIBITED,
                      DECISIONS_SETTLED, PENALTY_LAYERS, STEPS, FLAGS,
                      IRREGULARITIES, SNAPSHOT_DATE)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENT = D("0.01")

def q(x):
    return None if x is None else x.quantize(CENT, rounding=ROUND_HALF_UP)

def money(x):
    return "" if x is None else f"${q(x):,.2f}"

def num(x):
    return "" if x is None else f"{q(x):,.2f}"

BLANK = '<span class="blank">unverified</span>'
BLANKD = '<span class="blank">—</span>'

def mid():
    return (RATE["bid"] + RATE["ask"]) / 2

def spread(t, ask=None):
    ask = ask or RATE["ask"]
    return t * (ask - mid()) / ask

def wire_cny(t):
    pct = t * RATE["ask"] * RATE["wire_rate"]
    return min(RATE["wire_max"], max(RATE["wire_min"], pct)) + RATE["cable"]

def wire_usd(t):
    return wire_cny(t) / RATE["ask"]

def ceil_int(x):
    return int(x.to_integral_value(rounding=ROUND_CEILING))

def ladder_row(series_id, model, t):
    r = dict(series=series_id, amount=t, spread=None, fee=None, tax=None,
             known=None, units=None, units_label="", years=None)
    if model == "fx_wire":
        r.update(spread=spread(t), fee=wire_usd(t), units=1, units_label="wire", years=1)
    elif model == "wire_only":
        r.update(fee=wire_usd(t), units=1, units_label="wire", years=1)
    elif model == "quota":
        cap = RATE["quota_usd"]
        full = int((t / cap).to_integral_value(rounding=ROUND_FLOOR))
        rem = t - cap * full
        fees = wire_usd(cap) * full + (wire_usd(rem) if rem > 0 else D(0))
        n = full + (1 if rem > 0 else 0)
        r.update(spread=spread(t), fee=fees, units=n, units_label="wires (1/year)", years=n)
    elif model == "atm":
        cny = t * RATE["ask"]; day = RATE["atm_day_cap_cny"]
        full = int((cny / day).to_integral_value(rounding=ROUND_FLOOR))
        rem = cny - day * full
        fee_cny = min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * day) * full
        if rem > 0:
            fee_cny += min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * rem)
        n = full + (1 if rem > 0 else 0)
        r.update(fee=fee_cny / RATE["ask"], units=n, units_label="withdrawals",
                 years=ceil_int(cny / RATE["atm_year_cap_cny"]))
    elif model == "cash":
        r.update(spread=spread(t, RATE["cash_ask"]), units=ceil_int(t / RATE["cash_no_permit_usd"]),
                 units_label="trips at USD 5,000", years=None)
    elif model in ("dividend20", "dividend10"):
        rate = RATE["iit_dividend"] if model == "dividend20" else RATE["treaty_dividend"]
        tax = t * rate; net = t - tax
        r.update(tax=tax, spread=spread(net), fee=wire_usd(net), units=1,
                 units_label="wire", years=1)
    # blank: everything stays None
    parts = [v for v in (r["spread"], r["fee"], r["tax"]) if v is not None]
    if parts:
        r["known"] = sum(parts)
    return r

SERIES = []  # (series_id, method_id, model, label)
for m in METHODS:
    if m["id"] == "F09":
        SERIES.append(("F09S", "F09", "dividend20", "Dividend — statutory 20% tax"))
        SERIES.append(("F09T", "F09", "dividend10", "Dividend — treaty 10% ceiling (if eligible)"))
    else:
        SERIES.append((m["id"], m["id"], m["model"], m["name"]))

def fx_gain(t, year):
    return t - t * RATE["ask"] / RATE["irs_avg"][year]

# ------------------------------------------------------------------ CSVs
def write_csvs():
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    def w(name, header, rows):
        with open(os.path.join(ROOT, "data", name), "w", newline="", encoding="utf-8") as f:
            c = csv.writer(f); c.writerow(header); c.writerows(rows)
    w("f52_sources.csv", ["id", "issuer", "title", "url", "how_read", "proposition"],
      [[s[0], s[1], s[2], s[3], s[4], s[5]] for s in SOURCES])
    w("f52_methods.csv", ["id", "status", "model", "name", "fits", "limit", "pros", "cons", "tax", "source_ids", "flag_ids"],
      [[m["id"], m["status"], m["model"], m["name"], m["fits"], m["limit"], m["pros"], m["cons"], m["tax"],
        "|".join(m["src"]), "|".join(m["flags"])] for m in METHODS] +
      [[p["id"], "Prohibited", "none", p["name"], "", p["why"], "", p["penalty"], "", "|".join(p["src"]), "|".join(p.get("flags", []))]
       for p in PROHIBITED])
    w("f52_decisions.csv", ["id", "question", "why_it_decides", "answer_today_blank_if_empty", "status", "how_to_discover", "source_ids"],
      [[d[0], d[1], d[2], d[3], d[4], d[5], "|".join(d[6])] for d in DECISIONS_SETTLED])
    w("f52_penalty.csv", ["layer", "what_it_is", "amount_or_rate_blank_if_empty", "applies_when", "source_ids", "flag_ids"],
      [[p[0], p[1], p[2], p[3], "|".join(p[4]), "|".join(p[5])] for p in PENALTY_LAYERS])
    rows = []
    for sid, mid_, model, label in SERIES:
        m = next(x for x in METHODS if x["id"] == mid_)
        for t in AMOUNTS:
            r = ladder_row(sid, model, t)
            rows.append([sid, mid_, model, f"{t:.0f}", num(r["spread"]), num(r["fee"]), num(r["tax"]),
                         num(r["known"]), "" if r["known"] is None else f"{q(r['known']/t*100)}",
                         "" if r["units"] is None else r["units"], r["units_label"],
                         "" if r["years"] is None else r["years"],
                         "intermediary+receiving fees blank (F52-U04); personal tax blank unless shown",
                         "|".join(m["src"]), " ".join(SRC[s][3] for s in m["src"][:2])])
    w("f52_ladder.csv", ["series", "method_id", "model", "amount_usd", "spread_usd", "fee_usd", "tax_usd",
                         "known_cost_usd", "known_cost_pct", "units", "units_label", "calendar_years",
                         "not_included", "source_ids", "source_urls"], rows)
    w("f52_fxgain.csv", ["amount_usd", "gain_if_acquired_2023_avg", "gain_if_acquired_2024_avg",
                         "gain_if_acquired_2025_avg", "note", "source_ids"],
      [[f"{t:.0f}", num(fx_gain(t, "2023")), num(fx_gain(t, "2024")), num(fx_gain(t, "2025")),
        "Gain only, not tax. Tax = gain x your marginal rate (blank, F52-U15); character conflict F52-U05.",
        "F-S15|F-S18|F-S01"] for t in AMOUNTS])
    w("f52_steps.csv", ["method_id", "step", "action", "source_ids"],
      [[mid_, i + 1, a, "|".join(s)] for mid_, steps in STEPS.items() for i, (a, s) in enumerate(steps)])
    w("f52_flags.csv", ["id", "severity", "item", "why_blank_or_uncertain", "what_would_settle_it", "source_ids"],
      [[f[0], f[1], f[2], f[3], f[4], "|".join(f[5])] for f in FLAGS] +
      [[f[0], "review", f[1], f[2], "See Flagged page.", "|".join(f[3])] if False else
       [ir[0], "review", ir[1], ir[2], "See Flagged page.", "F-S01"] for ir in IRREGULARITIES])

# ------------------------------------------------------------------ HTML
def esc(x):
    return html.escape(str(x), quote=True)

def srclinks(ids):
    out = []
    for i in ids:
        s = SRC[i]
        out.append(f'<a href="{esc(s[3])}" rel="noopener" title="{esc(s[2])}">{esc(i)}</a>')
    return " ".join(out)

def flaglink(fid):
    return f'<a href="f52-flagged.html#{esc(fid)}">{esc(fid)}</a>'

NAV = [("f52-summary.html", "Summary"), ("f52-decisions.html", "Decisions"),
       ("f52-methods.html", "Methods & steps"), ("f52-costs.html", "Costs $10k–$400k"),
       ("f52-flagged.html", "Flagged & sources")]

def page(title, body):
    nav = "".join(f'<a href="{u}">{esc(t)}</a>' for u, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China money (f52, {SNAPSHOT_DATE})</title>
<link rel="stylesheet" href="assets/f52.css"></head>
<body><header><div class="brand">China money <span>CNY → USD · decision checklist &amp; fresh costs · {SNAPSHOT_DATE}</span></div>
<nav>{nav}<a href="index.html">Main dashboard</a><a href="dashboard/flagged.html">Prior flagged</a></nav></header>
<main>
<p class="notice">Research from official sources read on {SNAPSHOT_DATE} — not legal, tax or banking advice. A blank cell means <b>unverified</b> (see <a href="f52-flagged.html">Flagged</a>); blank is never zero. Bank prices are Bank of China public board/tariff illustrations, not your bank's quote.</p>
{body}
</main><footer>Sources: SAFE · PBOC · Bank of China · State Taxation Administration · IRS · FinCEN/eCFR · U.S. Code. Every data row links its source. Snapshot: BOC board {esc(RATE['board_time'])} (Beijing), USD selling 6.6911 / buying 6.6630 CNY.</footer>
</body></html>"""

def build_pages():
    mid_v = (RATE["bid"] + RATE["ask"]) / 2
    half = (RATE["ask"] - mid_v) / RATE["ask"] * 100
    at = {t: ladder_row("F01", "fx_wire", D(t)) for t in (10000, 100000, 400000)}
    # ---- summary
    glance_rows = ""
    for sid, mid_, model, label in SERIES:
        cells = ""
        for t in (10000, 50000, 100000, 200000, 400000):
            r = ladder_row(sid, model, D(t))
            cells += f'<td data-label="${t:,}">{money(r["known"]) if r["known"] is not None else BLANK}</td>'
        r4 = ladder_row(sid, model, D(400000))
        time = "" if r4["years"] is None else (f'{r4["years"]} yr' if r4["units_label"] != "trips at USD 5,000" else f'{r4["units"]} trips')
        if r4["units_label"] == "trips at USD 5,000":
            time = f'{r4["units"]} trips'
        m = next(x for x in METHODS if x["id"] == mid_)
        glance_rows += (f'<tr data-kind="data"><td data-label="Route"><b>{esc(sid)}</b> {esc(label)}</td>{cells}'
                        f'<td data-label="Time for $400k">{esc(time) if time else BLANK}</td>'
                        f'<td class="src" data-label="Source">{srclinks(m["src"][:3])}</td></tr>')
    route_rows = ""
    for d in [x for x in DECISIONS_SETTLED if x[0] in ("Q06",)]:
        pass
    summary = f"""
<h1>Getting money out of China as a U.S. citizen — executive summary</h1>
<p class="lead">Most important first. Prices use today's Bank of China board ({esc(RATE['board_time'])}, selling <b>6.6911 CNY/USD</b>). Full $10,000-step tables are on the <a href="f52-costs.html">Costs page</a>; the questions that must be answered before choosing are on the <a href="f52-decisions.html">Decisions page</a>.</p>
<div class="cards">
<div class="card"><b>{money(at[10000]['known'])}</b><span>known bank cost to convert + wire $10,000 (documented-income route)</span></div>
<div class="card"><b>{money(at[400000]['known'])}</b><span>same route at $400,000 in one wire (0.23%)</span></div>
<div class="card"><b>{half:.4f}%</b><span>today's BOC conversion spread vs the buy/sell midpoint — the whole 'conversion penalty' at the bank</span></div>
<div class="card"><b>17 questions</b><span>6 answered from official sources, 11 blank until your documents/bank answer them</span></div>
</div>
<h2>The answer in five points</h2>
<ol>
<li><b>Converting and wiring is not taxed.</b> No official source read puts a tax on the conversion or the wire; the State does not restrict recurring international payments and transfers. What the bank must see is a genuine lawful basis plus source/tax documents. {srclinks(['F-S08','F-S04'])}</li>
<li><b>The large number, if real, is tax on the underlying income</b> — wages/comprehensive income at 3%–45%, or 20% on dividends, rent and property gains — owed whether or not the money moves, and only if it was never paid. Bank-deposit interest is not in the nine taxable categories as fetched; its exemption notice was not re-fetched today (flagged via F52-U11 practice: ask the tax office). {srclinks(['F-S07'])}</li>
<li><b>The bank's own cost is about two-tenths of one percent.</b> {money(at[10000]['known'])} on $10,000 and {money(at[400000]['known'])} on $400,000 in one wire at BOC today. Intermediary and U.S. receiving fees are unpublished — blank, so these are lower bounds. {srclinks(['F-S01','F-S02'])} {flaglink('F52-U04')}</li>
<li><b>A U.S. passport does not buy the $50,000 ID-only amount.</b> Only Chinese citizens and Foreign Permanent Resident ID holders do. On a passport, the standard route is documented lawful income (F01); home-sale, inheritance, emigrant-property and change-back routes each fit one kind of money. {srclinks(['F-S05','F-S04','F-S09'])}</li>
<li><b>The U.S. side can exceed the bank cost.</b> Selling RMB is a taxable currency disposition (gain illustrated up to ${fx_gain(D(400000),'2024'):,.0f} on $400,000 if acquired at the 2024 IRS average — gain, not tax), and missed FBAR/Form 8938/Form 3520 filings carry penalties up to $16,536 / $60,000 / 25% respectively. {srclinks(['F-S18','F-S15','F-S12','F-S14','F-S17'])}</li>
</ol>
<h2>Cost at a glance — known bank cost only (today's BOC snapshot)</h2>
<div class="tbl"><table><thead><tr><th>Route</th><th>$10,000</th><th>$50,000</th><th>$100,000</th><th>$200,000</th><th>$400,000</th><th>Time for $400k</th><th>Source</th></tr></thead><tbody>{glance_rows}</tbody></table></div>
<p class="note">F09 rows include real dividend tax (20% statutory / 10% treaty ceiling), which is why they dwarf the fee-only rows. F10 prices only the BOC card fee (conversion rate unpublished). F11 prices only the conversion spread. F08 is blank throughout — blank means unverified, not free. Every $10,000 step: <a href="f52-costs.html">Costs page</a> (data: <code>data/f52_ladder.csv</code>).</p>
<h2>Which route fits which money</h2>
<div class="tbl"><table><thead><tr><th>If the money is…</th><th>Route</th><th>Bank cost at $100k</th><th>Next</th></tr></thead><tbody>
<tr data-kind="data"><td data-label="If the money is">Documented income earned in China</td><td data-label="Route"><a href="f52-methods.html#F01">F01</a></td><td data-label="Bank cost at $100k">{money(ladder_row('F01','fx_wire',D(100000))['known'])}</td><td data-label="Next"><a href="f52-methods.html#F01">Steps</a> · {srclinks(['F-S04'])}</td></tr>
<tr data-kind="data"><td data-label="If the money is">Your own FX changed into RMB &lt;24 months ago (slip kept)</td><td data-label="Route"><a href="f52-methods.html#F02">F02</a></td><td data-label="Bank cost at $100k">{money(ladder_row('F02','fx_wire',D(100000))['known'])}</td><td data-label="Next"><a href="f52-methods.html#F02">Steps</a> · {srclinks(['F-S09'])}</td></tr>
<tr data-kind="data"><td data-label="If the money is">Already USD/FX in the account</td><td data-label="Route"><a href="f52-methods.html#F03">F03</a></td><td data-label="Bank cost at $100k">{money(ladder_row('F03','wire_only',D(100000))['known'])}</td><td data-label="Next"><a href="f52-methods.html#F03">Steps</a> · {srclinks(['F-S02'])}</td></tr>
<tr data-kind="data"><td data-label="If the money is">Home-sale proceeds / inheritance / pre-emigration property</td><td data-label="Route"><a href="f52-methods.html#F04">F04</a> / <a href="f52-methods.html#F05">F05</a> / <a href="f52-methods.html#F06">F06</a></td><td data-label="Bank cost at $100k">{money(ladder_row('F04','fx_wire',D(100000))['known'])} bank part</td><td data-label="Next"><a href="f52-methods.html#F04">Steps</a> · {srclinks(['F-S07'])}</td></tr>
<tr data-kind="data"><td data-label="If the money is">You hold a Chinese ID or Foreign Permanent Resident ID</td><td data-label="Route"><a href="f52-methods.html#F07">F07</a> ($50k/yr)</td><td data-label="Bank cost at $100k">{money(ladder_row('F07','quota',D(100000))['known'])}</td><td data-label="Next"><a href="f52-methods.html#F07">Steps</a> · {srclinks(['F-S05','F-S06'])}</td></tr>
<tr data-kind="data"><td data-label="If the money is">Profit inside your Chinese company</td><td data-label="Route"><a href="f52-methods.html#F09">F09</a> dividend</td><td data-label="Bank cost at $100k">{money(ladder_row('F09S','dividend20',D(100000))['known'])} incl. 20% tax</td><td data-label="Next"><a href="f52-methods.html#F09">Steps</a> · {srclinks(['F-S07','F-S13'])}</td></tr>
<tr data-kind="data"><td data-label="If the money is">A gift, or you cannot document the source</td><td data-label="Route"><span class="blank">no verified route</span></td><td data-label="Bank cost at $100k"><span class="blank">unverified</span></td><td data-label="Next">{flaglink('F52-U07')} · {srclinks(['F-S04'])}</td></tr>
</tbody></table></div>
<p><b>Do not</b> use relatives' quotas, private swaps, false purposes or crypto: fines run to 30% of the amount (30%–100% serious), plus a 2-year-plus watch listing for splitting. <a href="f52-methods.html#prohibited">Prohibited rows X01–X06</a>. {srclinks(['F-S08','F-S20'])}</p>
<h2>Before any decision</h2>
<p>Three blanks decide everything: <a href="f52-decisions.html#Q06">Q06 what created the money</a>, <a href="f52-decisions.html#Q07">Q07 whether its Chinese tax is paid</a>, and <a href="f52-decisions.html#Q10">Q10 what the quoted 'taxes' actually are</a>. The Decisions page gives the exact document or office that settles each one. Nothing on this site recommends a route for your case until those are answered.</p>
"""
    # ---- decisions
    drows = ""
    for d in DECISIONS_SETTLED:
        ans = esc(d[3]) if d[3] else '<span class="blank">blank — unverified</span>'
        drows += (f'<tr data-kind="data" id="{esc(d[0])}"><td data-label="Question"><b>{esc(d[0])}</b> {esc(d[1])}</td>'
                  f'<td data-label="Why it decides">{esc(d[2])}</td><td data-label="Answer today">{ans}</td>'
                  f'<td data-label="Status">{esc(d[4])}</td><td data-label="How to discover it">{esc(d[5])}</td>'
                  f'<td class="src" data-label="Source">{srclinks(d[6])}</td></tr>')
    decisions = f"""
<h1>Decision checklist — questions, answers, and how to discover the rest</h1>
<p class="lead">No route can reasonably be chosen until the <b>blank</b> rows are settled. Settled rows cite the official page that settles them; blank rows give the exact document, office or written quote that would settle them. Work top to bottom: Q06–Q10 first.</p>
<div class="tbl"><table><thead><tr><th>Question</th><th>Why it decides</th><th>Answer today</th><th>Status</th><th>How to discover it</th><th>Source</th></tr></thead><tbody>{drows}</tbody></table></div>
<p class="note">Data: <code>data/f52_decisions.csv</code>. 'Answered from official sources' means the general rule is settled; applying it to your account still needs the documents named in the blank rows.</p>
"""
    # ---- methods + steps + prohibited + penalty summary
    mrows, stepblocks = "", ""
    for m in METHODS:
        fl = " ".join(flaglink(f) for f in m["flags"])
        mrows += (f'<tr data-kind="data" id="{esc(m["id"])}"><td data-label="Route"><b>{esc(m["id"])}</b> {esc(m["name"])}<br><span class="note">{esc(m["status"])}</span></td>'
                  f'<td data-label="Use it when">{esc(m["fits"])}</td><td data-label="Limit">{esc(m["limit"])}</td>'
                  f'<td data-label="Pros">{esc(m["pros"])}</td><td data-label="Cons">{esc(m["cons"])}</td>'
                  f'<td data-label="Tax">{esc(m["tax"])}<br>{fl}</td>'
                  f'<td class="src" data-label="Source">{srclinks(m["src"])}</td></tr>')
        lis = "".join(f'<li>{esc(a)} {srclinks(s)}</li>' for a, s in STEPS[m["id"]])
        stepblocks += f'<h3 id="steps-{esc(m["id"])}">{esc(m["id"])} — step by step</h3><ol>{lis}</ol>'
    prows = ""
    for p in PROHIBITED:
        prows += (f'<tr data-kind="data"><td data-label="Do not use"><b>{esc(p["id"])}</b> {esc(p["name"])}</td>'
                  f'<td data-label="Why prohibited">{esc(p["why"])}</td><td data-label="Penalty">{esc(p["penalty"])}</td>'
                  f'<td class="src" data-label="Source">{srclinks(p["src"])}</td></tr>')
    penrows = ""
    for p in PENALTY_LAYERS:
        amt = esc(p[2]) if p[2] else '<span class="blank">blank — unverified</span>'
        fl = " ".join(flaglink(f) for f in p[5])
        penrows += (f'<tr data-kind="data"><td data-label="Layer"><b>{esc(p[0])}</b></td><td data-label="What it is">{esc(p[1])} {fl}</td>'
                    f'<td data-label="Amount / rate">{amt}</td><td data-label="Applies when">{esc(p[3])}</td>'
                    f'<td class="src" data-label="Source">{srclinks(p[4])}</td></tr>')
    methods = f"""
<h1>Ways to convert CNY to USD — pros, cons, steps, and the penalty breakdown</h1>
<p class="lead">Eleven lawful routes and six prohibited ones. Bank costs below are today's BOC illustration; eligibility always depends on the Decisions page.</p>
<h2>Lawful routes</h2>
<div class="tbl"><table><thead><tr><th>Route</th><th>Use it when</th><th>Limit</th><th>Pros</th><th>Cons</th><th>Tax</th><th>Source</th></tr></thead><tbody>{mrows}</tbody></table></div>
<h2>Step by step — exactly how each route works</h2>
{stepblocks}
<h2 id="prohibited">Prohibited — do not use at any amount</h2>
<div class="tbl"><table><thead><tr><th>Do not use</th><th>Why prohibited</th><th>Penalty</th><th>Source</th></tr></thead><tbody>{prows}</tbody></table></div>
<h2>Conversion penalty, decomposed</h2>
<p>The feared 'conversion penalty' is eight separate layers. Only layers 1–2 are charged by the bank; layer 4 is pre-existing income tax; layers 6–7 are fines for missed filings or prohibited methods. Keep them separate — adding them together double-counts.</p>
<div class="tbl"><table><thead><tr><th>Layer</th><th>What it is</th><th>Amount / rate</th><th>Applies when</th><th>Source</th></tr></thead><tbody>{penrows}</tbody></table></div>
<p class="note">Data: <code>data/f52_methods.csv</code> · <code>data/f52_penalty.csv</code> · <code>data/f52_steps.csv</code>.</p>
"""
    # ---- costs
    inputs = f"""
<h2>What the numbers are built from (all read {SNAPSHOT_DATE})</h2>
<div class="tbl"><table><thead><tr><th>Input</th><th>Value</th><th>What it is</th><th>Source</th></tr></thead><tbody>
<tr data-kind="data"><td data-label="Input">Bank sells you USD at</td><td data-label="Value"><b>6.6911 CNY/USD</b></td><td data-label="What it is">BOC Selling Rate 669.11 per 100, board {esc(RATE['board_time'])}</td><td class="src" data-label="Source">{srclinks(['F-S01'])}</td></tr>
<tr data-kind="data"><td data-label="Input">Bank buys USD at</td><td data-label="Value"><b>6.6630 CNY/USD</b></td><td data-label="What it is">BOC Buying Rate 666.30 per 100, same board</td><td class="src" data-label="Source">{srclinks(['F-S01'])}</td></tr>
<tr data-kind="data"><td data-label="Input">Fair-value midpoint (computed)</td><td data-label="Value"><b>{mid_v} CNY/USD</b></td><td data-label="What it is">Midpoint of the two rates above. Spread cost = amount × (selling − midpoint) ÷ selling = {half:.4f}%. BOC's printed 'Middle Rate' (6.7191) is a different reference figure — {flaglink('F52-U14')}</td><td class="src" data-label="Source">{srclinks(['F-S01'])}</td></tr>
<tr data-kind="data"><td data-label="Input">Wire fee</td><td data-label="Value"><b>1‰ (CNY 50–260) + CNY 150</b></td><td data-label="What it is">BOC personal cross-border wire + cable (non-HK/Macau/Taiwan), since 2014-11-01; local differences possible</td><td class="src" data-label="Source">{srclinks(['F-S02'])}</td></tr>
<tr data-kind="data"><td data-label="Input">Worked example ($100,000, F01)</td><td data-label="Value"><b>{money(at[100000]['known'])}</b></td><td data-label="What it is">Spread {money(at[100000]['spread'])} + wire {money(at[100000]['fee'])}. RMB debited: {100000*float(RATE['ask'])+float(wire_cny(D(100000))):,.2f}. Intermediary/receiving fees excluded (blank)</td><td class="src" data-label="Source">{srclinks(['F-S01','F-S02'])}</td></tr>
</tbody></table></div>"""
    srows = ""
    for sid, mid_, model, label in SERIES:
        cells = ""
        for t in (10000, 50000, 100000, 200000, 400000):
            r = ladder_row(sid, model, D(t))
            cells += f'<td data-label="${t:,}">{money(r["known"]) if r["known"] is not None else BLANK}</td>'
        m = next(x for x in METHODS if x["id"] == mid_)
        srows += f'<tr data-kind="data"><td data-label="Route"><b>{esc(sid)}</b> {esc(label)}</td>{cells}<td class="src" data-label="Source">{srclinks(m["src"][:3])} · <a href="#full-{esc(sid)}">all 40 steps</a></td></tr>'
    full = ""
    for sid, mid_, model, label in SERIES:
        m = next(x for x in METHODS if x["id"] == mid_)
        trs = ""
        for t in AMOUNTS:
            r = ladder_row(sid, model, t)
            pct = "" if r["known"] is None else f'{q(r["known"]/t*100)}%'
            units = "" if r["units"] is None else f'{r["units"]} {esc(r["units_label"])}'
            trs += (f'<tr data-kind="data"><td data-label="Amount (USD)">${t:,.0f}</td>'
                    f'<td data-label="Known cost">{money(r["known"]) if r["known"] is not None else BLANK}</td>'
                    f'<td data-label="Known %">{esc(pct) if pct else BLANKD}</td>'
                    f'<td data-label="Spread">{money(r["spread"])}</td><td data-label="Fee">{money(r["fee"])}</td>'
                    f'<td data-label="Tax in row">{money(r["tax"])}</td>'
                    f'<td data-label="Units / time">{esc(units) if units else BLANK}</td>'
                    f'<td class="src" data-label="Source">{srclinks(m["src"][:2])}</td></tr>')
        full += (f'<details id="full-{esc(sid)}"><summary><b>{esc(sid)}</b> {esc(label)} — every $10,000 step</summary>'
                 f'<div class="tbl"><table><thead><tr><th>Amount</th><th>Known cost</th><th>Known %</th><th>Spread</th><th>Fee</th><th>Tax in row</th><th>Units / time</th><th>Source</th></tr></thead><tbody>{trs}</tbody></table></div></details>')
    grows = ""
    for t in AMOUNTS:
        grows += (f'<tr data-kind="data"><td data-label="Convert (USD)">${t:,.0f}</td>'
                  f'<td data-label="Gain if acquired 2023">{money(fx_gain(t, "2023"))}</td>'
                  f'<td data-label="Gain if acquired 2024">{money(fx_gain(t, "2024"))}</td>'
                  f'<td data-label="Gain if acquired 2025">{money(fx_gain(t, "2025"))}</td>'
                  f'<td data-label="Tax on the gain"><span class="blank">blank — your rate (Q15)</span></td>'
                  f'<td class="src" data-label="Source">{srclinks(["F-S15", "F-S18", "F-S01"])}</td></tr>')
    costs = f"""
<h1>What every method costs — $10,000 to $400,000 in $10,000 steps</h1>
<p class="lead">Most important first: the summary matrix, then every step for every method. 'Known cost' includes only published components; intermediary/receiving fees and personal tax stay blank and are <b>not</b> in any total.</p>
{inputs}
<h2>All routes side by side (known cost)</h2>
<div class="tbl"><table><thead><tr><th>Route</th><th>$10,000</th><th>$50,000</th><th>$100,000</th><th>$200,000</th><th>$400,000</th><th>Source</th></tr></thead><tbody>{srows}</tbody></table></div>
<p class="note">Reading the table: F01/F02/F04/F05/F06 share one bank price — what differs is paperwork and approval, not the wire. F03 is cheapest (no conversion). F07 repeats the wire yearly. F09 includes real tax. F10 is fee-only (rate unpublished). F11 is spread-only. F08 is blank because no official price exists.</p>
<h2>Every $10,000 step, every method</h2>
{full}
<h2>U.S. currency gain on converting (gain only — tax is blank)</h2>
<p>If the RMB was acquired when it was weaker, selling it today realises a §988 gain. Basis illustrations use IRS yearly averages (2023: 7.075, 2024: 7.189, 2025: 7.129 CNY/USD) against today's BOC selling rate. Your actual basis is your acquisition rate (Q09/Q14).</p>
<div class="tbl"><table><thead><tr><th>Convert</th><th>Gain if acquired 2023</th><th>Gain if acquired 2024</th><th>Gain if acquired 2025</th><th>Tax on the gain</th><th>Source</th></tr></thead><tbody>{grows}</tbody></table></div>
<p class="note">Data: <code>data/f52_ladder.csv</code> (480 rows) · <code>data/f52_fxgain.csv</code>. Recompute: <code>python3 scripts/verify_f52.py</code>. Formula disclosure: <code>research/f52-cost-methodology.md</code>.</p>
"""
    # ---- flagged + sources
    frows = ""
    for f in FLAGS:
        frows += (f'<tr data-kind="data" id="{esc(f[0])}"><td data-label="Item"><b>{esc(f[0])}</b> ({esc(f[1])}) {esc(f[2])}</td>'
                  f'<td data-label="Why blank / uncertain">{esc(f[3])}</td><td data-label="What would settle it">{esc(f[4])}</td>'
                  f'<td class="src" data-label="Source">{srclinks(f[5])}</td></tr>')
    irows = ""
    for ir in IRREGULARITIES:
        irows += (f'<tr data-kind="data"><td data-label="Irregularity"><b>{esc(ir[0])}</b> {esc(ir[1])}</td>'
                  f'<td data-label="Disposition">{esc(ir[2])}</td><td class="src" data-label="Source">{srclinks(ir[3])}</td></tr>')
    srcrows = ""
    for s in SOURCES:
        srcrows += (f'<tr data-kind="data"><td data-label="ID"><b>{esc(s[0])}</b></td><td data-label="Issuer">{esc(s[1])}</td>'
                    f'<td data-label="Document"><a href="{esc(s[3])}" rel="noopener">{esc(s[2])}</a></td>'
                    f'<td data-label="Read">{esc(s[4])} on {SNAPSHOT_DATE}</td><td data-label="What it establishes">{esc(s[5])}</td></tr>')
    flagged = f"""
<h1>Flagged for Review — unverified items, irregularities, and every source</h1>
<p class="lead">Nothing here blocks publication. Each blank elsewhere on this site links to one of these entries.</p>
<h2>Unverified or uncertain ({len(FLAGS)} items)</h2>
<div class="tbl"><table><thead><tr><th>Item</th><th>Why blank / uncertain</th><th>What would settle it</th><th>Source</th></tr></thead><tbody>{frows}</tbody></table></div>
<h2>Irregularities ({len(IRREGULARITIES)} items)</h2>
<div class="tbl"><table><thead><tr><th>Irregularity</th><th>Disposition</th><th>Source</th></tr></thead><tbody>{irows}</tbody></table></div>
<h2>Source register — {len(SOURCES)} official pages read on {SNAPSHOT_DATE}</h2>
<p>Only government, regulator, central-bank and Bank of China pages. 'Excerpt' means the official file's own text was returned by a search of that exact URL and the file was not opened in full in this pass — open it yourself before relying on it.</p>
<div class="tbl"><table><thead><tr><th>ID</th><th>Issuer</th><th>Document</th><th>Read</th><th>What it establishes</th></tr></thead><tbody>{srcrows}</tbody></table></div>
<p class="note">Data: <code>data/f52_sources.csv</code> · <code>data/f52_flags.csv</code>. Verification log with verbatim quotes: <code>research/f52-verification.md</code>.</p>
"""
    pages = {"f52-summary.html": ("Executive summary", summary),
             "f52-decisions.html": ("Decision checklist", decisions),
             "f52-methods.html": ("Methods, steps & penalties", methods),
             "f52-costs.html": ("Costs $10k–$400k", costs),
             "f52-flagged.html": ("Flagged for Review & sources", flagged)}
    for name, (title, body) in pages.items():
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(page(title, body))
    print(f"built 5 pages, {len(SERIES)*len(AMOUNTS)} ladder rows")

if __name__ == "__main__":
    write_csvs()
    build_pages()
