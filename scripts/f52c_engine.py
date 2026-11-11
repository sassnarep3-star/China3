#!/usr/bin/env python3
"""Independent cost engine for the f52c decision page (11 Nov 2026 board).

Written from the published inputs only, without importing any earlier session's
engine, so the two implementations can be compared cell by cell.

Inputs, all read from official pages on 2026-11-11 (data/f52c_sources.csv):
  F01 Bank of China exchange-rate board, USD row, published 2026/11/11 10:25:02
      buying 666.30, cash buying 666.30, selling 669.11, cash selling 669.11
  F02 Bank of China personal e-banking transfer tariff: cross-border wire 1 per
      mille, minimum RMB 50, maximum RMB 260, plus RMB 150 cable for
      non-HK/Macau/Taiwan (in force since 2014-11-01)
  F03 Bank of China ATM notice effective 2026-11-11: UnionPay overseas cash
      withdrawal RMB 12 + 1 % per withdrawal, capped at RMB 112
  F06 SAFE Ningxia: the USD 50,000 is an annual convenience amount, not a limit
  F12 SAFE card notice 汇发〔2017〕29号: RMB 100,000 per calendar year, and
      RMB 10,000 per card per day
  F14 SAFE Hebei: USD 5,000 free, USD 5,000-10,000 needs a bank permit,
      above USD 10,000 needs a SAFE permit and is in principle not allowed
  F17 IIT Law: 20 % flat on dividends, interest, rent and property gains
  F18 IRS yearly average rates: 2024 = 7.189, 2025 = 7.129 CNY per USD

Arithmetic convention (stated on the page):
  * converting RMB into USD happens at the bank's SELLING rate for USD;
  * "fair value" is the midpoint of the board's own buying and selling rates,
    computed here as (bid + ask) / 2 - NOT the board's "Middle Rate" column,
    which is not that midpoint (671.91 vs 667.705 on this board);
  * the conversion cost is the USD the midpoint would have bought minus the USD
    actually received:  usd * (ask - mid) / ask;
  * the wire fee is charged in RMB on the RMB amount, then converted at the
    same selling rate;
  * everything is rounded half-up to the cent at the end, not in the middle.

Unknown costs are None and print blank. Nothing is inferred.
"""
from __future__ import annotations

import csv
from decimal import Decimal as D, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CENT = D("0.01")

# ---------------------------------------------------------------- published inputs
BOARD = {
    "pub_time": "2026/11/11 10:25:02",
    "bid": D("6.6630"),
    "ask": D("6.6911"),
    "cash_bid": D("6.6630"),
    "cash_ask": D("6.6911"),
    "boc_middle_column": D("6.7191"),
}
WIRE = {"rate": D("0.001"), "min_cny": D("50"), "max_cny": D("260"), "cable_cny": D("150")}
ATM = {"fixed_cny": D("12"), "pct": D("0.01"), "max_cny": D("112"),
       "day_cap_cny": D("10000"), "year_cap_cny": D("100000")}
QUOTA_USD = D("50000")
CASH = {"no_permit_usd": D("5000"), "bank_permit_usd": D("10000")}
IIT_FLAT = D("0.20")
IRS_AVG = {"2021": D("6.452"), "2022": D("6.730"), "2023": D("7.075"),
           "2024": D("7.189"), "2025": D("7.129")}

AMOUNTS = [D(10000) * i for i in range(1, 41)]  # USD 10,000 to 400,000, step 10,000
KEY_AMOUNTS = [D(10000), D(50000), D(100000), D(200000), D(400000)]

# The eleven lawful routes, same identifiers the dashboard uses.
# model: how the known part of the cost is built. "blank" = no verified figure.
METHODS = [
    ("L01", "fx_wire", "Documented income earned in China"),
    ("L02", "fx_wire", "Change back unused RMB with the original exchange slip"),
    ("L03", "wire_only", "Wire out foreign currency already in a foreign-currency account"),
    ("L04", "fx_wire", "Proceeds from selling a home you owned in China"),
    ("L05", "fx_wire", "Inheritance transfer"),
    ("L06", "fx_wire", "Emigrant property transfer"),
    ("L07", "quota", "Annual USD 50,000 convenience amount (Foreign Permanent Resident ID)"),
    ("L08", "blank", "Send the RMB itself abroad as cross-border RMB"),
    ("L09", "dividend", "Dividend from your own Chinese company"),
    ("L10", "atm", "Cash withdrawals abroad with a mainland UnionPay debit card"),
    ("L11", "cash", "Carry foreign-currency cash out in person"),
]


def cents(x: D) -> D:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def mid() -> D:
    return (BOARD["bid"] + BOARD["ask"]) / 2


def spread_usd(usd: D, ask: D | None = None) -> D:
    ask = ask if ask is not None else BOARD["ask"]
    return usd * (ask - mid()) / ask


def wire_cny(usd: D) -> D:
    pct = usd * BOARD["ask"] * WIRE["rate"]
    return min(WIRE["max_cny"], max(WIRE["min_cny"], pct)) + WIRE["cable_cny"]


def wire_usd(usd: D) -> D:
    return wire_cny(usd) / BOARD["ask"]


def cartons(usd: D, cap: D) -> tuple[int, D]:
    """number of full tranches of `cap`, and the remainder"""
    n = int(usd // cap)
    return n, usd - cap * n


def cost(model: str, usd: D) -> dict:
    """Known cost of one route at one amount. Every unverified part stays None."""
    ask = BOARD["ask"]
    out = {"method": model, "amount_usd": usd, "spread_usd": None, "fee_usd": None,
           "tax_usd": None, "total_usd": None, "pct": None, "units": None,
           "years": None}

    if model in ("fx_wire", "property"):
        s, w = spread_usd(usd), wire_usd(usd)
        out.update(spread_usd=s, fee_usd=w, total_usd=s + w, units=1, years=1)
    elif model == "wire_only":
        w = wire_usd(usd)
        out.update(fee_usd=w, total_usd=w, units=1, years=1)
    elif model == "quota":
        full, rem = cartons(usd, QUOTA_USD)
        fee = wire_usd(QUOTA_USD) * full + (wire_usd(rem) if rem > 0 else D(0))
        n = full + (1 if rem > 0 else 0)
        s = spread_usd(usd)          # one rate for every tranche: a stated simplification
        out.update(spread_usd=s, fee_usd=fee, total_usd=s + fee, units=n, years=n)
    elif model == "atm":
        cny = usd * ask              # board rate stands in for the unverified card-network rate
        full, rem = cartons(cny, ATM["day_cap_cny"])
        per = lambda amt: min(ATM["max_cny"], ATM["fixed_cny"] + ATM["pct"] * amt)
        fee_cny = per(ATM["day_cap_cny"]) * full + (per(rem) if rem > 0 else D(0))
        f = fee_cny / ask
        out.update(fee_usd=f, total_usd=f, units=full + (1 if rem > 0 else 0),
                   years=int((cny / ATM["year_cap_cny"]).to_integral_value(rounding=ROUND_CEILING)))
    elif model == "cash":
        s = spread_usd(usd, BOARD["cash_ask"])
        out.update(spread_usd=s, total_usd=s,
                   units=int(-(-usd // CASH["no_permit_usd"])),
                   years=int(-(-usd // CASH["bank_permit_usd"])))
    elif model == "dividend":
        tax = usd * IIT_FLAT
        net = usd - tax
        s, w = spread_usd(net), wire_usd(net)
        out.update(tax_usd=tax, spread_usd=s, fee_usd=w, total_usd=tax + s + w,
                   units=1, years=1)
    # "blank": nothing published, everything stays None

    if out["total_usd"] is not None:
        out["total_usd"] = cents(out["total_usd"])
        out["pct"] = (out["total_usd"] / usd * 100).quantize(D("0.0001"), rounding=ROUND_HALF_UP)
        for k in ("spread_usd", "fee_usd", "tax_usd"):
            if out[k] is not None:
                out[k] = cents(out[k])
    return out


def us_gain(usd: D, year: str) -> D:
    """USD gain on selling today RMB that was acquired at that year's IRS average rate."""
    return cents(usd - usd * BOARD["ask"] / IRS_AVG[year])


def write_csvs() -> None:
    data = ROOT / "data"
    # 1. all eleven routes x forty increments
    with (data / "f52c_method_costs.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["method_id", "amount_usd", "spread_usd", "fee_usd", "tax_usd",
                    "known_cost_usd", "known_cost_pct", "units", "calendar_years"])
        for mid_, model, _name in METHODS:
            for a in AMOUNTS:
                r = cost(model, a)
                f = lambda v: "" if v is None else f"{v:.2f}"
                w.writerow([mid_, f"{a:.0f}", f(r["spread_usd"]), f(r["fee_usd"]),
                            f(r["tax_usd"]), f(r["total_usd"]),
                            "" if r["pct"] is None else f"{r['pct']:.4f}",
                            "" if r["units"] is None else r["units"],
                            "" if r["years"] is None else r["years"]])

    # 2. the headline ladder: L01, L03, L07 and the US currency-gain line
    with (data / "f52c_ladder.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["amount_usd", "l01_cost_usd", "l01_pct", "l03_cost_usd",
                    "l07_cost_usd", "l07_years", "us_gain_2024", "us_gain_2025",
                    "us_gain_2024_pct"])
        for a in AMOUNTS:
            l01, l03, l07 = cost("fx_wire", a), cost("wire_only", a), cost("quota", a)
            g24, g25 = us_gain(a, "2024"), us_gain(a, "2025")
            w.writerow([f"{a:.0f}", f"{l01['total_usd']:.2f}", f"{l01['pct']:.4f}",
                        f"{l03['total_usd']:.2f}", f"{l07['total_usd']:.2f}", l07["years"],
                        f"{g24:.2f}", f"{g25:.2f}",
                        f"{(g24 / a * 100).quantize(D('0.0001'), rounding=ROUND_HALF_UP):.4f}"])


if __name__ == "__main__":
    write_csvs()
    for m, model, _n in METHODS:
        r10, r400 = cost(model, D(10000)), cost(model, D(400000))
        fmt = lambda v: "blank" if v is None else f"{v:,.2f}"
        print(f"{m} {model:10s} $10k={fmt(r10['total_usd']):>12s}  $400k={fmt(r400['total_usd']):>12s}  "
              f"years={r400['years']} units={r400['units']}")
    print("\nboard 11 Nov 2026 10:25:02  bid", BOARD["bid"], "ask", BOARD["ask"], "mid", mid())
    for a in (D(10000), D(100000), D(400000)):
        r = cost("fx_wire", a)
        print(f"L01 {a:>7.0f}: spread {r['spread_usd']:>10,.2f} wire {r['fee_usd']:>7,.2f} "
              f"total {r['total_usd']:>10,.2f} ({r['pct']}%)")
