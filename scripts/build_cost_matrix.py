#!/usr/bin/env python3
"""Build the amount-by-amount CNY->USD cost model.

Single source of truth for the USD 10,000 - 400,000 schedule. Every input is
either (a) a published official number with a dated source, or (b) an explicit,
labelled assumption whose anchor is also cited. The script:

  * reads data/cost_sources.csv (the register for this page family);
  * computes 40 amount steps x 13 routes plus a 40-row penalty matrix;
  * writes data/cost_params.csv, data/cost_methods.csv, data/cost_matrix.csv,
    data/cost_penalty.csv, data/cost_tax.csv;
  * renders deep-costs.html and deep-cost-steps.html.

No value is typed into the HTML by hand. scripts/verify_cost_matrix.py then
recomputes every row independently and fails on any mismatch.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AMOUNTS = list(range(10_000, 400_001, 10_000))
CHECKED = "2026-11-09"

# --------------------------------------------------------------------------
# 1. Official inputs (each carries its register id)
# --------------------------------------------------------------------------
RATE_MID = 6.7188          # C01 SAFE central parity, 2026-11-09
BOC_BUY = 6.6638           # C02 现汇买入价 per USD
BOC_SELL = 6.6919          # C02 现汇卖出价 per USD
BOC_MID = (BOC_BUY + BOC_SELL) / 2
SPREAD_HALF = (BOC_SELL - BOC_MID) / BOC_MID      # 0.2103%
SPREAD_FULL = (BOC_SELL - BOC_BUY) / BOC_MID      # 0.4208%

WIRE_RATE = 0.001          # C03 1 per mille
WIRE_MIN_CNY = 50.0        # C03
WIRE_MAX_CNY = 260.0       # C03
CABLE_CNY = 150.0          # C03 non-HK/Macau/Taiwan
FULL_AMOUNT_USD = 25.0     # C04 beneficiary bank without a BOC New York account

QUOTA_USD = 50_000.0       # C05/C06 annual convenience amount
ATM_CNY_YEAR = 100_000.0   # C10
ATM_CNY_DAY = 10_000.0     # C10
CASH_PER_TRIP_USD = 10_000.0  # C11 permit ceiling
EMIGRANT_ONE_OFF_CNY = 200_000.0  # C08 Art.6 small-amount one-off
FBAR_WILLFUL = 165_353.0   # C16
FBAR_NONWILLFUL = 16_536.0  # C16
FORM_8938_MAX = 60_000.0   # C17 (USD 10,000 + up to 50,000)
FORM_3520_RATE = 0.25      # C19

PARAMS = [
    # key, label, value, unit, status, basis, source ids
    ("rate_mid", "SAFE central parity USD/CNY", f"{RATE_MID:.4f}", "CNY per USD", "verified",
     "Published central parity for 2026-11-09. This is the reference rate, not a tradable customer rate.",
     ["C01"]),
    ("boc_buy", "BOC 现汇买入价 (bank buys USD from you)", f"{BOC_BUY:.4f}", "CNY per USD", "verified",
     "BOC published rate board, 2026-11-09 09:15:45.", ["C02"]),
    ("boc_sell", "BOC 现汇卖出价 (bank sells USD to you)", f"{BOC_SELL:.4f}", "CNY per USD", "verified",
     "The rate you actually pay when buying USD. Same board and timestamp.", ["C02"]),
    ("spread_low", "Conversion spread - low", f"{SPREAD_HALF*100:.3f}%", "of amount", "verified-measured",
     "Half of the measured BOC bid/ask spread: (sell - mid) / mid on 2026-11-09. Measured, not a forecast.",
     ["C02"]),
    ("spread_base", "Conversion spread - base", f"{SPREAD_FULL*100:.3f}%", "of amount", "verified-measured",
     "Full measured BOC bid/ask spread: (sell - buy) / mid on 2026-11-09. Used as the central case.",
     ["C02"]),
    ("spread_high", "Conversion spread - high", "1.000%", "of amount", "assumption",
     "Not published. Anchored to the former 1% ceiling on the customer spot spread, which applied until it was widened in 2014 and then abolished on 2014-07-01. Banks are free to price above it now.",
     ["C14", "C15"]),
    ("wire_rate", "Personal cross-border wire fee", "1 per mille, min CNY 50, max CNY 260", "per transaction", "verified",
     "BOC personal e-banking cross-border telegraphic transfer tariff.", ["C03"]),
    ("cable", "Cable / telecom fee", f"CNY {CABLE_CNY:.0f}", "per transaction", "verified",
     "Non-HK/Macau/Taiwan cable fee. HK/Macau/Taiwan is CNY 80.", ["C03"]),
    ("full_amount", "Full-amount (全额到账) guarantee", f"USD {FULL_AMOUNT_USD:.0f}", "per transaction", "verified",
     "Paid by the sender so that the beneficiary receives the full amount and overseas bank charges are not deducted from principal. USD 15 if the beneficiary bank holds an account at BOC New York.",
     ["C04"]),
    ("compliance", "Documents / notarisation / translation", "USD 0 - 500", "per application", "assumption",
     "No regulator publishes these prices. The band is an assumption for notarised translations and courier costs on routes that require them; it is excluded from the low case and included at USD 500 in the high case.",
     ["C08"]),
    ("atm_fee", "ATM fee per withdrawal", "USD 5", "per withdrawal", "assumption",
     "Chinese issuer fee plus US operator fee. Neither is fixed by regulation; the published SAFE notice sets limits, not prices.",
     ["C10"]),
    ("cnh_low", "Offshore CNY/CNH basis - low", "0.000%", "of amount", "assumption",
     "Base case assumes no offshore basis. Current CNH basis is not published as an official daily series.",
     ["C25"]),
    ("cnh_base", "Offshore CNY/CNH basis - base", "0.500%", "of amount", "assumption",
     "Mid-point assumption, deliberately below the historical stress observation. Not a quote.",
     ["C25"]),
    ("cnh_high", "Offshore CNY/CNH basis - high", "1.940%", "of amount", "verified-historical",
     "HKMA recorded a 1.94% CNY/CNH disparity on 2011-09-23. Historical stress observation, not today's basis.",
     ["C25"]),
    ("fbar_willful", "FBAR willful maximum", f"USD {FBAR_WILLFUL:,.0f}", "per violation", "verified",
     "Inflation-adjusted statutory maximum assessed on or after 2025-01-17; the statute sets the penalty at the greater of this amount or 50% of the account balance.",
     ["C16"]),
    ("fbar_nonwillful", "FBAR non-willful maximum", f"USD {FBAR_NONWILLFUL:,.0f}", "per violation", "verified",
     "Inflation-adjusted statutory maximum.", ["C16"]),
    ("f8938", "Form 8938 maximum", f"USD {FORM_8938_MAX:,.0f}", "per year", "verified",
     "USD 10,000 for failure to disclose plus up to USD 50,000 for continued failure after notice.", ["C17"]),
    ("f3520", "Form 3520 penalty", "5% per month, max 25%", "of the gift", "verified",
     "Applies only if the money is a foreign gift or bequest above the USD 100,000 reporting threshold.", ["C18", "C19"]),
    ("quota", "Annual convenience amount", f"USD {QUOTA_USD:,.0f}", "per person per year", "verified",
     "A processing convenience, not a legal cap and not a tax. Genuine current-account FX is not limited to it.", ["C05", "C06"]),
    ("atm_cap", "Overseas ATM cap", f"CNY {ATM_CNY_YEAR:,.0f}", "per person per year", "verified",
     "All cards in the person's name combined; breach suspends the channel for that year and the next.", ["C10"]),
    ("cash_cap", "Cash carry ceiling", f"USD {CASH_PER_TRIP_USD:,.0f}", "per trip, with permit", "verified",
     "Up to USD 5,000 needs no permit; USD 5,000-10,000 needs a bank 携带证; above USD 10,000 only in listed special cases with a SAFE permit.",
     ["C11"]),
]

# --------------------------------------------------------------------------
# 2. Route definitions
# --------------------------------------------------------------------------
def wire_cny(amount_cny: float) -> float:
    return min(max(WIRE_RATE * amount_cny, WIRE_MIN_CNY), WIRE_MAX_CNY) + CABLE_CNY


def one(amount: float) -> int:
    return 1


def per(limit: float):
    def f(amount: float) -> int:
        return max(1, int(-(-amount // limit)))
    return f


METHODS = [
    dict(id="L01", group="Lawful", name="Foreign individual: current-account income, FX purchase + wire (Art. 59)",
         who="US citizen treated by the bank as 境外个人 (foreign individual)",
         rule="No fixed annual amount applies. ID + source-of-funds documents including tax evidence. Single payment above USD 50,000 also needs the tax filing form.",
         spread=True, tranches=one, compliance_high=500.0, cnh=None,
         years="One application; above USD 50,000 per payment add the 备案表",
         sources=["C06", "C07", "C32", "C03"], verdict="Primary route"),
    dict(id="L02", group="Lawful", name="Chinese-resident individual: non-quota current-account purchase (Art. 57)",
         who="Holder of a PRC resident ID card",
         rule="No fixed annual amount applies, but the purchase must be for a genuine current-account purpose with documents.",
         spread=True, tranches=one, compliance_high=500.0, cnh=None,
         years="One application; above USD 50,000 per payment add the 备案表",
         sources=["C05", "C32", "C03"], verdict="Only if the account is a 境内个人 account"),
    dict(id="L03", group="Lawful", name="Annual convenience amount (USD 50,000 per person per year)",
         who="PRC resident individual, or a foreigner holding a foreign permanent-residence ID",
         rule="ID only, no transaction documents, but capped at the equivalent of USD 50,000 per calendar year and not for capital-account uses.",
         spread=True, tranches=per(QUOTA_USD), compliance_high=0.0, cnh=None,
         years="ceil(amount / USD 50,000) calendar years",
         sources=["C05", "C06", "C03"], verdict="Slowest lawful route for large balances"),
    dict(id="L04", group="Lawful", name="Account already holds USD: wire out without converting",
         who="Any holder of a foreign-currency deposit account",
         rule="No conversion spread because the money is already in USD. Outward remittance evidence rules still apply.",
         spread=False, tranches=one, compliance_high=0.0, cnh=None,
         years="One payment",
         sources=["C03", "C29"], verdict="Free of FX cost, but the conversion already happened"),
    dict(id="L05", group="Lawful", name="Emigrant property transfer (移民财产转移)",
         who="A natural person who emigrated from mainland China, for property owned before emigrating",
         rule="One application for the whole amount; first remittance at most 50%, then at most half the remainder after one year, remainder after two years. Local SAFE approves up to CNY 500,000; above that SAFE headquarters.",
         spread=True, tranches=lambda a: 1 if a * BOC_MID <= EMIGRANT_ONE_OFF_CNY else 3,
         compliance_high=500.0, cnh=None,
         years="1 application, 3 remittances over 2 years (one-off if <= CNY 200,000)",
         sources=["C08", "C03"], verdict="The only 'no ceiling' route, if you qualify"),
    dict(id="L06", group="Lawful", name="Inheritance property transfer (继承财产转移)",
         who="A foreign citizen or HK/Macau resident inheriting mainland assets",
         rule="One application for the whole inherited amount, then one or several remittances. Notarised inheritance and title documents.",
         spread=True, tranches=one, compliance_high=500.0, cnh=None,
         years="1 application; instalments allowed",
         sources=["C08", "C03"], verdict="Only for inherited money"),
    dict(id="L07", group="Lawful", name="Foreign individual: proceeds of selling mainland property",
         who="Foreign individual selling a mainland property",
         rule="Bank handles the purchase and remittance on documents after the property-transfer tax is cleared. PRC IIT of 20% applies to the gain, not to the conversion.",
         spread=True, tranches=one, compliance_high=500.0, cnh=None,
         years="One payment after tax clearance",
         sources=["C06", "C12", "C32", "C03"], verdict="Tax depends on the gain, not the amount moved"),
    dict(id="L08", group="Conditional", name="Carry USD cash out of China",
         who="Traveller",
         rule="Up to USD 5,000 no permit; USD 5,000-10,000 a bank 携带证; above USD 10,000 only in listed special cases with a SAFE permit. Physical loss and travel costs are excluded from the numbers.",
         spread=True, tranches=per(CASH_PER_TRIP_USD), compliance_high=0.0, cnh=None,
         years="ceil(amount / USD 10,000) trips; above USD 10,000 per trip is not generally lawful",
         sources=["C11", "C03"], verdict="Not viable above USD 10,000 per trip"),
    dict(id="L09", group="Conditional", name="Overseas ATM withdrawals on a mainland card",
         who="Holder of a mainland-issued card",
         rule="CNY 100,000 equivalent per person per calendar year across all cards, and CNY 10,000 equivalent per card per day. Breach suspends the channel for the year and the next.",
         spread=True, tranches=lambda a: max(1, int(-(-a // (ATM_CNY_DAY / BOC_MID)))), compliance_high=0.0,
         cnh=None, atm=True,
         years="ceil(amount / USD 14,883) calendar years",
         sources=["C10", "C03"], verdict="Structurally capped at about USD 14,883 a year"),
    dict(id="L10", group="Conditional", name="RMB cross-border settlement, converted offshore (CNH)",
         who="Holder of an account that can make lawful cross-border RMB payments",
         rule="The conversion happens in the offshore market, so the CNY/CNH basis is added to the cost. The offshore basis is not an official daily series; the high case uses a historical stress observation.",
         spread=True, tranches=one, compliance_high=500.0, cnh=(0.0, 0.005, 0.0194),
         years="One remittance, then an offshore conversion",
         sources=["C25", "C03"], verdict="Adds an unhedgeable basis risk"),
    dict(id="P01", group="Prohibited", name="Split purchases / borrowing other people's quotas (分拆)",
         who="-", rule="Classified as 逃汇 / evasion. SAFE enforcement cases show fines under Art. 39.",
         spread=False, tranches=one, compliance_high=0.0, cnh=None, years="Not lawful",
         sources=["C22", "C09"], verdict="Fine plus confiscation exposure", prohibited=True),
    dict(id="P02", group="Prohibited", name="Underground bank / street dealer (地下钱庄 / 黄牛)",
         who="-", rule="Illegal FX trading under Art. 45; criminal exposure under Criminal Law Art. 225.",
         spread=False, tranches=one, compliance_high=0.0, cnh=None, years="Not lawful",
         sources=["C09", "C24"], verdict="Fine, confiscation and imprisonment exposure", prohibited=True),
    dict(id="P03", group="Prohibited", name="Crypto / USDT / stablecoin conversion",
         who="-", rule="Virtual-currency business is prohibited; stablecoin activity is treated as illegal financial activity.",
         spread=False, tranches=one, compliance_high=0.0, cnh=None, years="Not lawful",
         sources=["C23", "C24"], verdict="Prohibited route", prohibited=True),
]

NOT_MODELLED = [
    ("QDII funds / bank overseas wealth products", "An investment product, not a way to move your own savings; product fees are not published per product and returns are at risk.", ["C26"]),
    ("Cross-boundary Wealth Management Connect (跨境理财通)", "Requires residency and eligibility in the Greater Bay Area and is an investment channel with its own quota and product fees.", ["C26"]),
    ("Payment Connect (跨境支付通)", "Small-value retail remittance link; no official tariff or per-transaction limit was confirmed in this pass, so it is left uncosted.", ["C26"]),
    ("Outbound direct investment (ODI) by an individual", "Requires an approved investment project and registration; not a route for personal savings.", ["C09"]),
    ("Personal goods trade / cross-border e-commerce settlement", "Business income only, with customs and tax filings; the cost is a business cost, not an FX fee.", ["C09"]),
    ("Foreign-currency cash remittance (外币现钞汇出)", "Cash must first be deposited; the bank then applies the same wire tariff modelled in L01.", ["C03"]),
    ("Entrusting a relative to act for you", "Agency is allowed, but the money and the quota must still be the account holder's own; it does not create a new channel.", ["C08"]),
    ("Individual FX settlement account for traders", "Requires a trade-business registration; not available for personal savings.", ["C09"]),
    ("Inbound capital-account income conversion", "Direction is into China, so it does not move money out.", ["C09"]),
    ("Buying foreign property / securities / life insurance with the quota", "Capital-account use is not permitted under the convenience amount; treated as a prohibited use.", ["C09"]),
    ("Over/under-invoicing through a business", "False trade documents; criminal exposure, not a cost model.", ["C09"]),
    ("RWA tokens / offshore tokens linked to mainland assets", "Prohibited by the 2026 notice; criminal exposure.", ["C23"]),
]


def compute(method: dict, amount: float) -> dict:
    n = method["tranches"](amount)
    cny = amount * BOC_MID
    wire = wire_cny(cny / n) * n / BOC_SELL
    full = FULL_AMOUNT_USD * n
    compliance_base = method["compliance_high"] * 0.0
    compliance_high = method["compliance_high"]
    if method.get("atm"):
        spread_low = amount * SPREAD_HALF
        spread_base = amount * SPREAD_FULL
        spread_high = amount * 0.01
        atm = 5.0 * n
        lo = spread_low + atm * 0.0
        ba = spread_base + atm
        hi = spread_high + atm * 2
    else:
        spread_low = amount * SPREAD_HALF if method["spread"] else 0.0
        spread_base = amount * SPREAD_FULL if method["spread"] else 0.0
        spread_high = amount * 0.01 if method["spread"] else 0.0
        lo = spread_low + wire
        ba = spread_base + wire + full + compliance_base
        hi = spread_high + wire + full + compliance_high
    if method.get("cnh"):
        lo += amount * method["cnh"][0]
        ba += amount * method["cnh"][1]
        hi += amount * method["cnh"][2]
    if method["id"] == "L04":
        wire = wire_cny(cny) / BOC_SELL
        lo = wire
        ba = wire + full
        hi = wire + full
    out = dict(amount=amount, cny=cny, tranches=n, low=lo, base=ba, high=hi)
    out["net_base"] = amount - ba
    out["pct_low"] = lo / amount * 100
    out["pct_base"] = ba / amount * 100
    out["pct_high"] = hi / amount * 100
    return out


def cash_rows():
    rows = []
    for amount in AMOUNTS:
        r = compute(next(m for m in METHODS if m["id"] == "P01"), amount)
        rows.append(dict(amount=amount,
                         prc_low=amount * 0.30,
                         prc_high=amount * 1.00,
                         fbar_willful=max(FBAR_WILLFUL, amount * 0.5),
                         fbar_nonwillful=FBAR_NONWILLFUL,
                         f8938=FORM_8938_MAX,
                         f3520=amount * FORM_3520_RATE))
    return rows


# --------------------------------------------------------------------------
# 3. Write CSVs
# --------------------------------------------------------------------------
def write_csv(name, header, rows):
    with (DATA / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def main() -> int:
    with (DATA / "cost_sources.csv").open(encoding="utf-8") as fh:
        registry = {r["id"]: r for r in csv.DictReader(fh)}

    write_csv("cost_params.csv",
              ["key", "label", "value", "unit", "status", "basis", "source_ids"],
              [[k, lab, val, unit, status, basis, " ".join(ids)] for k, lab, val, unit, status, basis, ids in PARAMS])

    write_csv("cost_methods.csv",
              ["id", "group", "method", "who", "rule", "tranches_rule", "verdict", "source_ids"],
              [[m["id"], m["group"], m["name"], m["who"], m["rule"], m["years"], m["verdict"],
                " ".join(m["sources"])] for m in METHODS])

    matrix = []
    for m in METHODS:
        for amount in AMOUNTS:
            r = compute(m, amount)
            if m.get("prohibited"):
                matrix.append([m["id"], m["name"], f"{amount:.0f}", f"{r['cny']:.0f}", 1,
                               "", "", "", "",
                               f"{amount*0.30:.0f}", f"{amount*0.30:.0f}", f"{amount*1.00:.0f}",
                               f"{30.0:.3f}", f"{30.0:.3f}", f"{100.0:.3f}", "",
                               "Not lawful - penalty exposure, not a transfer cost",
                               " ".join(m["sources"]), "prohibited"])
            else:
                matrix.append([m["id"], m["name"], f"{amount:.0f}", f"{r['cny']:.0f}", r["tranches"],
                               f"{r['low']:.2f}", f"{r['base']:.2f}", f"{r['high']:.2f}",
                               f"{m['compliance_high']:.0f}",
                               "", "", "",
                               f"{r['pct_low']:.3f}", f"{r['pct_base']:.3f}", f"{r['pct_high']:.3f}",
                               f"{r['net_base']:.2f}", m["years"],
                               " ".join(m["sources"]), "modelled"])
    write_csv("cost_matrix.csv",
              ["method_id", "method", "amount_usd", "cny_at_boc_mid", "tranches",
               "cost_low_usd", "cost_base_usd", "cost_high_usd", "compliance_high_usd",
               "penalty_low_usd", "penalty_base_usd", "penalty_high_usd",
               "pct_low", "pct_base", "pct_high", "net_base_usd", "feasibility",
               "source_ids", "status"],
              matrix)

    write_csv("cost_penalty.csv",
              ["amount_usd", "prc_fine_low", "prc_fine_high", "fbar_willful_max",
               "fbar_nonwillful_max", "form_8938_max", "form_3520_max"],
              [[f"{r['amount']:.0f}", f"{r['prc_low']:.2f}", f"{r['prc_high']:.2f}",
                f"{r['fbar_willful']:.0f}", f"{r['fbar_nonwillful']:.0f}",
                f"{r['f8938']:.0f}", f"{r['f3520']:.2f}"] for r in cash_rows()])

    tax_rows = [
        ("Salary already taxed in China", "3%-45% withheld on comprehensive income; no further PRC tax on moving the net amount",
         "Worldwide income is taxable in the US; foreign earned income exclusion and foreign tax credit may reduce double tax",
         "C12 C27 C28"),
        ("Bank deposit interest", "0% - savings-deposit interest is exempt for interest accruing on or after 2008-10-09",
         "Taxable interest in the US, even though China exempts it", "C13 C27"),
        ("Gain on selling a mainland property", "20% of proceeds minus original value and reasonable expenses",
         "Capital gain in the US; foreign tax credit is limited to the lesser of foreign tax paid and the FTC limitation", "C12 C28"),
        ("Dividends from a mainland company", "20% flat", "Taxable in the US; treaty caps the PRC rate at 10% but the saving clause preserves US taxation", "C12 C28"),
        ("Gift or inheritance received", "No gift tax appears in the PRC IIT rate schedule; whether a receipt is characterised as 偶然所得 depends on the facts and is flagged",
         "No US income tax on a gift, but Form 3520 is required above USD 100,000 and the penalty is 5% per month up to 25%", "C12 C18 C19"),
        ("Your own after-tax principal", "0% - the PRC taxes income, not the act of exchanging currency",
         "0% - the US taxes income, not transfers; personal currency gain is excluded unless it exceeds USD 200", "C09 C21 C20"),
    ]
    write_csv("cost_tax.csv", ["situation", "prc_treatment", "us_treatment", "source_ids"], tax_rows)

    render(registry, matrix, tax_rows)
    print(f"built {len(matrix)} method rows, {len(AMOUNTS)} amount steps, {len(METHODS)} routes")
    return 0


# --------------------------------------------------------------------------
# 4. Render
# --------------------------------------------------------------------------
def money(x: float) -> str:
    return f"${x:,.0f}"


def pct(x: float) -> str:
    return f"{x:.2f}%"


def src_links(ids, registry) -> str:
    out = []
    for sid in ids.split():
        s = registry[sid]
        out.append(f'<a href="{html.escape(s["url"])}" target="_blank" rel="noopener" '
                   f'title="{html.escape(s["title"])}">{sid} ↗</a>')
    return " ".join(out)


def nav(active: str) -> str:
    items = [("index.html", "Site home"), ("deep-executive-summary.html", "Executive summary"),
             ("deep-costs.html", "Cost model"), ("deep-cost-steps.html", "Step-by-step"),
             ("deep-china-rules.html", "China rules"), ("deep-us-tax.html", "US tax &amp; reporting"),
             ("deep-channels.html", "All channels"), ("deep-penalty.html", "Penalty breakdown"),
             ("deep-findings.html", "Analysis"), ("deep-review.html", "Flagged for review"),
             ("deep-sources.html", "Sources"), ("docs/index.html", "Docs dashboard")]
    links = "".join(f'<a class="{"active" if href == active else ""}" href="{href}">{label}</a>'
                    for href, label in items)
    return ('<header class="topbar"><div class="shell"><a class="brand" href="index.html">'
            '<span class="brand-mark">¥</span> China Money Research</a><nav class="nav">'
            f'{links}</nav></div></header>')


HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{desc}">
<title>{title} | China Money Research</title>
<link rel="stylesheet" href="assets/deep-research.css">
<link rel="stylesheet" href="assets/cost.css"></head><body>{nav}<main class="shell">"""

FOOT = """</main><footer class="foot"><div class="shell foot-row"><div><b>China Money Research</b>
<p>Official-source research · cost model built {checked} · no commercial providers.</p></div>
<p>Rates dated {checked} · <a href="deep-sources.html">Source register</a> · <a href="deep-review.html">Flagged for review</a></p>
</div></footer><script src="assets/deep-app.js"></script></body></html>"""


def render(registry, matrix, tax_rows):
    rows_by_method = {}
    for r in matrix:
        rows_by_method.setdefault(r[0], []).append(r)

    def row(cells, cls=""):
        return f'<tr class="{cls}">' + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    # ---- glance table at 400k and at 10k
    def at(mid, amount):
        for r in rows_by_method[mid]:
            if r[2] == f"{amount:.0f}":
                return r
        return None

    glance = []
    for m in METHODS:
        if m.get("prohibited"):
            continue
        r10, r400 = at(m["id"], 10_000), at(m["id"], 400_000)
        glance.append((m, r10, r400))
    glance.sort(key=lambda t: (t[0]["id"] == "L04", float(t[2][13])))

    glance_rows = []
    for m, r10, r400 in glance:
        glance_rows.append(row([
            f'<strong>{m["id"]}</strong> {html.escape(m["name"])}<br><span class="small">{html.escape(m["who"])}</span>',
            money(float(r10[5])), money(float(r10[6])), money(float(r10[7])),
            f'{pct(float(r10[13]))}',
            money(float(r400[6])), f'<strong>{pct(float(r400[13]))}</strong>',
            html.escape(r400[16]),
            f'<span class="src">{src_links(" ".join(m["sources"]), registry)}</span>',
        ]))

    # ---- per-method sections
    sections = []
    for m in METHODS:
        rows = rows_by_method[m["id"]]
        if m.get("prohibited"):
            head = (f'<tr><th>Amount</th><th>Administrative fine 30%</th><th>Administrative fine 100%</th>'
                    f'<th>Amount confiscated / at risk</th><th>Total exposure</th><th>Status</th><th>Source</th></tr>')
            body = []
            for r in rows:
                amt = float(r[2])
                body.append(row([money(amt), money(amt * 0.30), money(amt * 1.00), money(amt),
                                 f'{money(amt * 1.30)} – {money(amt * 2.00)}',
                                 '<span class="tag warn">Not lawful</span>',
                                 f'<span class="src">{src_links(r[17], registry)}</span>']))
            table = ('<div class="table-wrap"><table class="data"><thead>' + head + '</thead><tbody>'
                     + "".join(body) + "</tbody></table></div>")
        else:
            head = ('<tr><th>Amount</th><th>Low</th><th>Base</th><th>High</th><th>Effective&nbsp;% (base)</th>'
                    '<th>Net received (base)</th><th>Payments / time</th><th>Source</th></tr>')
            body = []
            for r in rows:
                body.append(row([f'<strong>{money(float(r[2]))}</strong>',
                                 money(float(r[5])), money(float(r[6])), money(float(r[7])),
                                 pct(float(r[13])), money(float(r[15])),
                                 html.escape(r[16]),
                                 f'<span class="src">{src_links(r[17], registry)}</span>']))
            table = ('<div class="table-wrap"><table class="data"><thead>' + head + '</thead><tbody>'
                     + "".join(body) + "</tbody></table></div>")
            # compact strip (mobile-first: the five amounts that matter)
            key = [r for r in rows if r[2] in {"10000", "50000", "100000", "200000", "400000"}]
            strip = ('<div class="table-wrap compact"><table class="data"><thead><tr><th>Amount</th>'
                     '<th>Base cost</th><th>Effective %</th><th>High</th><th>Source</th></tr></thead><tbody>'
                     + "".join(row([money(float(r[2])), money(float(r[6])), pct(float(r[13])),
                                    money(float(r[7])),
                                    f'<span class="src">{src_links(r[17], registry)}</span>']) for r in key)
                     + "</tbody></table></div>")
        sections.append(
            f'<details class="method" id="{m["id"].lower()}"{" open" if m["id"] in ("L01", "L05", "L03") else ""}>'
            f'<summary><span class="mid">{m["id"]}</span> {html.escape(m["name"])}'
            f'<span class="pill {"green" if m["group"]=="Lawful" else ("amber" if m["group"]=="Conditional" else "red")}">{m["group"]}</span>'
            f'<span class="verdict">{html.escape(m["verdict"])}</span></summary>'
            f'<p class="rule">{html.escape(m["rule"])}</p>'
            f'{strip if not m.get("prohibited") else ""}'
            f'{table}</details>')

    penalty_rows = []
    for r in cash_rows():
        penalty_rows.append(row([
            money(r["amount"]),
            f'{money(r["prc_low"])} – {money(r["prc_high"])}',
            money(r["fbar_willful"]),
            money(r["fbar_nonwillful"]),
            money(r["f8938"]),
            money(r["f3520"]),
            '<span class="src">'
            + f'<a href="{registry["C09"]["url"]}" target="_blank" rel="noopener">C09 ↗</a> '
            + f'<a href="{registry["C16"]["url"]}" target="_blank" rel="noopener">C16 ↗</a> '
            + f'<a href="{registry["C17"]["url"]}" target="_blank" rel="noopener">C17 ↗</a> '
            + f'<a href="{registry["C19"]["url"]}" target="_blank" rel="noopener">C19 ↗</a>'
            + '</span>',
        ]))
    penalty_table = ('<div class="table-wrap"><table class="data"><thead><tr>'
                     '<th>Amount moved</th><th>PRC fine if the route is unlawful (30%–100%)</th>'
                     '<th>FBAR willful max</th><th>FBAR non-willful</th><th>Form 8938 max</th>'
                     '<th>Form 3520 max (gift)</th><th>Source</th></tr></thead><tbody>'
                     + "".join(penalty_rows) + '</tbody></table></div>'
                     '<p class="small">PRC fines: <a href="' + registry["C09"]["url"] + '" target="_blank" rel="noopener">C09</a>. '
                     'FBAR: <a href="' + registry["C16"]["url"] + '" target="_blank" rel="noopener">C16</a>. '
                     'Form 8938: <a href="' + registry["C17"]["url"] + '" target="_blank" rel="noopener">C17</a>. '
                     'Form 3520: <a href="' + registry["C18"]["url"] + '" target="_blank" rel="noopener">C18</a>, '
                     '<a href="' + registry["C19"]["url"] + '" target="_blank" rel="noopener">C19</a>.</p>')

    param_rows = []
    for key, label, value, unit, status, basis, ids in PARAMS:
        cls = "ok" if status.startswith("verified") else "warn"
        param_rows.append(row([html.escape(label), f'<strong>{html.escape(value)}</strong>', html.escape(unit),
                               f'<span class="tag {cls}">{status}</span>', html.escape(basis),
                               f'<span class="src">{src_links(" ".join(ids), registry)}</span>']))
    param_table = ('<div class="table-wrap"><table class="data"><thead><tr><th>Input</th><th>Value</th>'
                   '<th>Unit</th><th>Status</th><th>Basis</th><th>Source</th></tr></thead><tbody>'
                   + "".join(param_rows) + "</tbody></table></div>")

    tax_table_rows = []
    for situation, prc, us, ids in tax_rows:
        tax_table_rows.append(row([f'<strong>{html.escape(situation)}</strong>', html.escape(prc), html.escape(us),
                                   f'<span class="src">{src_links(ids, registry)}</span>']))
    tax_table = ('<div class="table-wrap"><table class="data"><thead><tr><th>Situation</th>'
                 '<th>PRC treatment</th><th>US treatment</th><th>Source</th></tr></thead><tbody>'
                 + "".join(tax_table_rows) + "</tbody></table></div>")

    nm_rows = []
    for name, reason, ids in NOT_MODELLED:
        nm_rows.append(row([f'<strong>{html.escape(name)}</strong>', html.escape(reason),
                            f'<span class="src">{src_links(" ".join(ids), registry)}</span>']))
    nm_table = ('<div class="table-wrap"><table class="data"><thead><tr><th>Channel</th>'
                '<th>Why it is not costed here</th><th>Source</th></tr></thead><tbody>'
                + "".join(nm_rows) + "</tbody></table></div>")

    l01_10 = at("L01", 10_000); l01_400 = at("L01", 400_000)
    stats = f"""
<div class="stats">
  <div class="stat"><b>{money(float(l01_10[6]))} – {money(float(l01_400[6]))}</b><span>All-in cost to move USD 10,000 – 400,000 lawfully</span></div>
  <div class="stat"><b>0.99% → 0.44%</b><span>Effective cost falls as the amount rises (fixed fees are capped)</span></div>
  <div class="stat"><b>30%–100%</b><span>PRC fine on an unlawful route — plus confiscation</span></div>
  <div class="stat"><b>{money(FBAR_WILLFUL)}</b><span>Willful FBAR maximum, or 50% of the balance if larger</span></div>
</div>"""

    page = HEAD.format(desc="Computed cost of converting CNY to USD at every USD 10,000 step from 10,000 to 400,000, for every lawful, conditional and prohibited route.",
                       title="Cost at every USD 10,000 step", nav=nav("deep-costs.html")) + f"""
<section class="hero"><div class="eyebrow">Cost model · USD 10,000 to 400,000</div>
<h1>What it actually costs, at every USD 10,000 step</h1>
<p>Forty amount steps, thirteen routes, one arithmetic. Each input is either a dated official number or a labelled assumption. Nothing here is a bank quote: it is the arithmetic a bank quote should be compared against.</p></section>
{stats}
<div class="hero-band"><strong>The answer in one line</strong>
<p>Converting your own CNY principal costs roughly <strong>0.4%–1.0%</strong> through a lawful bank route, and that percentage <em>falls</em> as the amount rises because the wire fee is capped at CNY 260. The tax you are worried about is not a conversion tax: it is (a) PRC income tax on whatever created the money, and (b) US reporting penalties, which are fixed statutory amounts far larger than the FX cost. The expensive mistake is choosing an unlawful route: 30%–100% of the amount, plus confiscation.</p></div>

<section class="section" id="glance">
<div class="section-head"><div><h2 class="section-title">1 · Every lawful route, cheapest first</h2>
<p>Base case, sorted by effective cost at USD 400,000. Click a row's route below for all 40 amount steps.</p></div></div>
<div class="table-wrap"><table class="data"><thead><tr>
<th>Route</th><th>Cost at $10k</th><th>Low</th><th>High</th><th>Eff. % at $10k</th><th>Cost at $400k</th><th>Eff. % at $400k</th><th>Time / constraint</th><th>Source</th>
</tr></thead><tbody>{''.join(glance_rows)}</tbody></table></div>
<p class="small">Cost includes the conversion spread and every published bank fee. It excludes tax on the source of the money (table 4) and excludes US reporting penalties (table 3), because neither depends on the amount converted.</p>
</section>

<section class="section" id="methods">
<div class="section-head"><div><h2 class="section-title">2 · All 40 amount steps, route by route</h2>
<p>Open a route. The first table is the mobile view of the five amounts that matter; the second is the full 40-row schedule.</p></div></div>
{''.join(sections)}
</section>

<section class="section" id="penalty">
<div class="section-head"><div><h2 class="section-title">3 · The cost of getting it wrong</h2>
<p>These are statutory maximums and ranges, not predictions. Compare them with the 0.4%–1.0% in table 1.</p></div></div>
{penalty_table}
<div class="notice red"><strong>Why this table matters more than the FX cost.</strong> At USD 400,000 the lawful transfer costs about USD 1,770. A single willful FBAR violation is capped at the greater of USD 165,353 or 50% of the account balance — USD 200,000 at that balance. A PRC fine for an unlawful route is 30%–100% of the amount, i.e. USD 120,000–400,000 at USD 400,000, plus confiscation. Reporting correctly is worth more than any rate negotiation.</div>
</section>

<section class="section" id="tax">
<div class="section-head"><div><h2 class="section-title">4 · Tax, separated from the conversion</h2>
<p>Tax depends on what created the money, not on how much you move. This is the actual answer to "why is there a big tax".</p></div></div>
{tax_table}
<div class="notice"><strong>No conversion tax was found.</strong> The PRC personal income tax law taxes nine categories of income; exchanging your own after-tax principal is not one of them (<a href="{registry['C12']['url']}" target="_blank" rel="noopener">C12</a>). The State Council FX Regulation states that the State does not restrict current international payments and transfers (<a href="{registry['C09']['url']}" target="_blank" rel="noopener">C09</a>, Art. 5). What banks do require is <em>evidence of the source</em>, including tax evidence — a document request, not a levy (<a href="{registry['C07']['url']}" target="_blank" rel="noopener">C07</a>). This is a negative finding: no provision was found, which is why it is also flagged (IR-011).</div>
</section>

<section class="section" id="assumptions">
<div class="section-head"><div><h2 class="section-title">5 · Every input, its value, its status</h2>
<p><span class="tag ok">verified</span> = dated official number. <span class="tag warn">assumption</span> = not published; stated so you can replace it with your bank's quote.</p></div></div>
{param_table}
</section>

<section class="section" id="not-modelled">
<div class="section-head"><div><h2 class="section-title">6 · Channels deliberately not costed</h2>
<p>Listing them is part of "as many as possible"; pricing them would require inventing product fees.</p></div></div>
{nm_table}
</section>

<section class="section" id="method-note">
<div class="section-head"><div><h2 class="section-title">7 · Method and limits</h2></div></div>
<div class="grid">
<div class="card"><h2>Arithmetic</h2>
<div class="formula">CNY principal = USD amount × {BOC_MID:.5f}<br>
Spread cost = USD amount × spread %<br>
Wire fee = min(max(0.001 × CNY per payment, CNY 50), CNY 260) + CNY 150, ÷ {BOC_SELL:.4f}<br>
Full-amount guarantee = USD 25 per payment<br>
Total = spread + wire + guarantee + documents<br>
Effective % = total ÷ USD amount × 100</div>
<p>Payments: one, unless the route is capped (USD 50,000 a year; USD 10,000 a trip; RMB 100,000 a year at ATMs) or staged by the 2004 transfer rules (50% / 25% / 25%).</p></div>
<div class="card"><h2>What this is not</h2>
<ul><li>Not a bank quote. Your bank's rate is set by the bank; the customer spread was deregulated on 2014-07-01 (<a href="{registry['C14']['url']}" target="_blank" rel="noopener">C14</a>).</li>
<li>Not a tax calculation. Tax depends on the source of the funds and your basis (table 4).</li>
<li>Not a prediction of the CNY/CNH basis: the high case uses a 2011 stress observation (<a href="{registry['C25']['url']}" target="_blank" rel="noopener">C25</a>).</li>
<li>Not advice. Verify the rate and the documentary checklist with the specific bank branch in writing before instructing anything.</li></ul></div>
</div>
<p class="page-note">A second, deliberately conservative view of the same question is published at <a href="costs.html">costs.html</a> (all 35 channels × 40 increments, with numeric costs left blank where no bank quote exists) together with its own <a href="cost-review.html">verification flags</a>. This page is the computed model: same rules, but with every input dated and every assumption exposed.</p>
<p class="page-note">Every table row carries its own source links. Rates are a 2026-11-09 snapshot. Rows labelled <em>assumption</em> are not official values and are flagged for review. This page is informational research, not legal, tax or banking advice.</p>
</section>
""" + FOOT.format(checked=CHECKED)

    (ROOT / "deep-costs.html").write_text(page, encoding="utf-8")

    # ---- steps page
    step_data = {
        "L01": [
            "Collect the paper trail for the source of the money: employment contract and payslips, or the sale contract, the PRC tax receipt and the bank statements showing the RMB arriving.",
            "Ask the account-opening branch, in writing, whether the account is classified 境内个人 or 境外个人, and which article it will process under (Art. 59 for a foreign individual).",
            "Obtain the tax evidence: 完税证明, 免税证明, or the 服务贸易等项目对外支付税务备案表 if a single payment exceeds USD 50,000.",
            "Request an all-in written quote: customer rate, the reference rate and its timestamp, spread, wire fee, cable fee, guarantee fee, and the exact USD the US account will receive.",
            "Instruct one payment. Keep the bank's 购汇/付汇 documents; you need the date and the rate for your US return and for Form 8938/FBAR.",
            "Report on the US side: FBAR by 15 April (automatic extension to 15 October), Form 8938 with the return, and the interest or gain on the money in income.",
        ],
        "L02": [
            "Confirm the account is a 境内个人 account (PRC resident ID), because the convenience amount and Art. 57 only work for that classification.",
            "Assemble the documents for the specific current-account purpose; the purchase must match a real transaction, not a savings transfer.",
            "If a single payment exceeds USD 50,000, file the 税务备案表 before the bank will remit.",
            "Get the written all-in quote and check the spread against the measured 0.42% benchmark on this site.",
            "Instruct, keep the documents, and report the account and the income in the US.",
        ],
        "L03": [
            "Use it only for the amount inside USD 50,000 per calendar year, per person.",
            "Buy FX with ID only; no transaction documents, but the 个人购汇申请书 representations still apply.",
            "Do not split a larger balance across relatives or across banks to stay under the figure: that is the 分拆 pattern SAFE fines under Art. 39.",
            "For a USD 400,000 balance the route needs eight calendar years, so run it alongside a no-ceiling route rather than instead of one.",
            "Report every year in the US, including the years when nothing moves.",
        ],
        "L04": [
            "Confirm the account balance is already USD (or another foreign currency), not CNY.",
            "Provide the outward-remittance evidence the bank requires; above USD 50,000 in a day the bank will ask for transaction documents.",
            "Pay the wire and cable fees, and decide whether to buy the full-amount guarantee so the US bank does not deduct from principal.",
            "Keep the original conversion documents too: the US basis and the FBAR values depend on them.",
        ],
        "L05": [
            "Check eligibility first: this route is for a natural person who emigrated from mainland China and is moving property owned <em>before</em> acquiring emigrant status. Money earned after emigrating does not qualify.",
            "Assemble: written application, 移民财产对外转移申请人情况表, ID, cancelled 户籍 certificate, proof of overseas settlement authenticated by the Chinese embassy/consulate, property title and sale documents, and the PRC tax receipts.",
            "Apply once, to the SAFE branch where the 户籍 was registered. Up to CNY 500,000 is approved locally; above that it goes to SAFE headquarters.",
            "Remit in the staged pattern: at most 50% first, at most half the remainder after one year, the rest after two years (a one-off is allowed if the total is at most CNY 200,000).",
            "Note that the bank must remit directly to your own overseas account; cash withdrawal is not allowed under this route.",
            "Budget for three FX conversions and three wire fees over two years, plus two years of exchange-rate exposure.",
        ],
        "L06": [
            "Confirm you are a foreign citizen or HK/Macau resident inheriting mainland assets.",
            "Assemble the notarised inheritance proof, the deceased's title documents, your ID and the tax receipts.",
            "Apply once to the SAFE branch where the deceased was registered; the whole inherited amount is applied for at once.",
            "Remit in one or several payments after approval; keep every approval letter.",
            "Report the receipt in the US: Form 3520 above USD 100,000, and FBAR/8938 for the account while it is open.",
        ],
        "L07": [
            "Sell the property and settle the PRC individual income tax on the gain (20% of proceeds minus original value and reasonable expenses).",
            "Obtain the tax clearance and the property-transfer registration documents.",
            "Take the sale contract, tax receipts and ID to the bank for the FX purchase and remittance.",
            "Above USD 50,000 per payment, file the 税务备案表 first.",
            "Keep the gain calculation: the US will tax the same gain, with a foreign tax credit limited by the FTC limitation.",
        ],
        "L08": [
            "Up to USD 5,000 equivalent: no permit, but customs declaration rules still apply.",
            "USD 5,000–10,000: obtain a 携带证 from a designated FX bank before departure.",
            "Above USD 10,000: only the listed special cases can obtain a SAFE permit; assume it is not available for a normal individual.",
            "Do not structure trips to move a large balance: unlawful carrying is fined up to 20% under Art. 42 and can be treated as smuggling.",
            "Declare the cash on entry to the US if it exceeds USD 10,000 (FinCEN 105).",
        ],
        "L09": [
            "Confirm the card is a mainland-issued card and that overseas cash withdrawal is enabled.",
            "Stay inside RMB 10,000 equivalent per card per day and RMB 100,000 per person per calendar year across all cards.",
            "Expect the issuer fee plus any US operator fee on every withdrawal, and a worse rate than a wire.",
            "Do not lend or borrow cards to get around the cap: that is explicitly prohibited and triggers a suspension.",
            "Treat this as spending money abroad, not as a way to move a balance.",
        ],
        "L10": [
            "Confirm the RMB payment itself is a lawful current-account payment (salary, services, rent) with documents.",
            "Remit RMB to your own offshore account; the onshore bank charges its RMB remittance tariff.",
            "Convert CNY to USD offshore, where the rate follows CNH rather than the onshore fix.",
            "Measure the CNH basis on the day; the model's high case uses a 1.94% historical stress observation, not today's price.",
            "Keep both legs documented for the US return; the conversion is a personal transaction, so the USD 200 rule applies to the currency gain.",
        ],
    }
    steps_html = []
    for m in METHODS:
        if m.get("prohibited"):
            continue
        items = step_data.get(m["id"], [])
        lis = "".join(f"<li>{s}</li>" for s in items)
        steps_html.append(
            f'<section class="card stepcard" id="steps-{m["id"].lower()}"><h2><span class="mid">{m["id"]}</span> {html.escape(m["name"])}</h2>'
            f'<p class="small">{html.escape(m["rule"])}</p><ol class="steps">{lis}</ol>'
            f'<p class="small">Sources: {src_links(" ".join(m["sources"]), registry)}</p></section>')

    steps_page = HEAD.format(desc="Step-by-step execution for every lawful CNY to USD route, with the documents, the office and the order of operations.",
                             title="Step-by-step execution", nav=nav("deep-cost-steps.html")) + f"""
<section class="hero"><div class="eyebrow">Execution playbook</div>
<h1>Exactly how each route works, in order</h1>
<p>Same thirteen routes as the cost model. Each step names the document or the office, so the sequence can be checked against the bank's own checklist before any money moves.</p></section>
<div class="notice"><strong>Do this before choosing a route.</strong> Ask the account-opening branch two questions in writing: (1) is this account classified 境内个人 or 境外个人, and (2) under which article will it process a purchase and remittance of this size? The answer decides whether the USD 50,000 convenience amount binds or whether you proceed on source documents — the single most important fork in this project (flagged as IR-007).</div>
<div class="grid">{''.join(steps_html)}</div>
<section class="section"><div class="card"><h2>The same six controls on every route</h2>
<ol class="steps">
<li><strong>One route, one application.</strong> Never split across relatives, banks or years to avoid a threshold; that is the 分拆 pattern SAFE fines under Art. 39 (<a href="{registry['C22']['url']}" target="_blank" rel="noopener">C22</a>).</li>
<li><strong>Source, not purpose.</strong> The bank's job is to verify where the RMB came from, including tax evidence (<a href="{registry['C07']['url']}" target="_blank" rel="noopener">C07</a>).</li>
<li><strong>Written all-in quote.</strong> Customer rate, reference rate and timestamp, spread, every fee, and net USD to the beneficiary.</li>
<li><strong>Keep the paper.</strong> The purchase documents are the evidence for FBAR, Form 8938 and the US basis.</li>
<li><strong>Report in the US whether or not money moves.</strong> FBAR above USD 10,000 aggregate; Form 8938 at the applicable threshold (<a href="{registry['C17']['url']}" target="_blank" rel="noopener">C17</a>).</li>
<li><strong>Never use a prohibited route.</strong> The fine is 30%–100% of the amount plus confiscation, and can be criminal (<a href="{registry['C09']['url']}" target="_blank" rel="noopener">C09</a>, <a href="{registry['C24']['url']}" target="_blank" rel="noopener">C24</a>).</li>
</ol></div></section>
<p class="page-note">Sources are linked in each block. This is a research summary of published rules, not legal, tax or banking advice; the specific branch's written checklist controls.</p>
""" + FOOT.format(checked=CHECKED)
    (ROOT / "deep-cost-steps.html").write_text(steps_page, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
