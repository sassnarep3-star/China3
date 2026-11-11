#!/usr/bin/env python3
"""3E2D cost engine (session arena/3e2dbf57-china3).

Pure functions over the inputs below. Every input is a published figure read
live on 2026-11-11 (see data/3e2d_sources.csv). Costs that no official or
first-party page publishes are returned as None so they render blank.

Board snapshot (BOC, read 2026-11-11 20:50:05 Beijing):
  USD Buying 665.91, Selling 668.71, Cash Selling 668.71, Middle 671.91 per 100.
The model uses Buying/Selling only; Middle is a reference rate, never used.
"""
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR

RATE = {
    "board_time": "2026/11/11 20:50:05 (Beijing)",
    "bid": D("6.6591"),
    "ask": D("6.6871"),
    "cash_ask": D("6.6871"),
    "boc_middle": D("6.7191"),
    "wire_rate": D("0.001"),
    "wire_min": D("50"),
    "wire_max": D("260"),
    "cable": D("150"),
    "atm_fixed": D("12"),
    "atm_pct": D("0.01"),
    "atm_max": D("112"),
    "atm_day_cap_cny": D("10000"),
    "atm_year_cap_cny": D("100000"),
    "quota_usd": D("50000"),
    "cash_no_permit_usd": D("5000"),
    "cash_bank_permit_usd": D("10000"),
    "iit_flat": D("0.20"),
    "treaty_cap": D("0.10"),
    "bofa_inbound_may": D("15"),
    "irs_avg": {"2021": D("6.452"), "2022": D("6.730"), "2023": D("7.075"),
                "2024": D("7.189"), "2025": D("7.129")},
}

AMOUNTS = [D(x) for x in range(10000, 400001, 10000)]

# id, name, model, sources, flag
METHODS = [
    ("M01", "Documented current-account income (salary/fees) — buy USD + one wire", "fx_wire", "T01|T02|T04", ""),
    ("M02", "Reconvert unused CNY from own FX exchange (24 months) + wire", "fx_wire", "T01|T02|T09", "F02"),
    ("M03", "Already foreign currency — wire only, no conversion", "wire_only", "T02|T08", ""),
    ("M04", "Chinese home-sale proceeds — conversion + wire", "fx_wire", "T01|T02|T15", "F03"),
    ("M05", "Inheritance transfer — conversion + wire", "fx_wire", "T01|T02|T12", ""),
    ("M06", "Emigrant property transfer — conversion + wire", "fx_wire", "T01|T02|T12", ""),
    ("M07", "Annual convenience quota ($50k/yr, ID only) — split wires", "quota", "T01|T02|T05|T06", "F04"),
    ("M08", "Cross-border RMB to own offshore account, convert there", "blank", "T24", "F05"),
    ("M09", "Dividend from own Chinese company — 20% statutory scenario", "dividend", "T01|T02|T25|T27", "F06"),
    ("M09T", "Dividend — 10% treaty-cap scenario (beneficial owner)", "dividend_treaty", "T01|T02|T27", "F06"),
    ("M10", "Overseas ATM withdrawals (UnionPay card)", "atm", "T03|T19", "F07"),
    ("M11", "Carry lawfully purchased FX banknotes abroad", "cash", "T01|T20", ""),
    ("M12", "Wise from-CNY (own account only)", "blank", "T28", "F08"),
    ("M13", "Western Union China (cash pickup only)", "blank", "T29", "F09"),
    ("M14", "Gift / undocumented origin — no verified route", "none", "T04", "F10"),
]

CENT = D("0.01")

def q(x, places=CENT):
    return x.quantize(places, rounding=ROUND_HALF_UP)

def ceil_int(x):
    return int(x.to_integral_value(rounding=ROUND_CEILING))

def mid():
    return (RATE["bid"] + RATE["ask"]) / 2

def spread_usd(usd, ask=None):
    ask = ask or RATE["ask"]
    return usd * (ask - mid()) / ask

def wire_cny(usd):
    pct = usd * RATE["ask"] * RATE["wire_rate"]
    return min(RATE["wire_max"], max(RATE["wire_min"], pct)) + RATE["cable"]

def wire_usd(usd):
    return wire_cny(usd) / RATE["ask"]

def row(method_id, model, usd):
    r = dict(method_id=method_id, model=model, amount_usd=usd, units=None,
             units_label="", calendar_years=None, spread_usd=None, fee_usd=None,
             tax_usd=None, known_cost_usd=None, known_cost_pct=None,
             rmb_debited=None, extra=None)
    if model in ("fx_wire",):
        s, w = spread_usd(usd), wire_usd(usd)
        r.update(units=1, units_label="wire", calendar_years=1, spread_usd=s, fee_usd=w,
                 known_cost_usd=s + w, rmb_debited=usd * RATE["ask"] + wire_cny(usd))
    elif model == "wire_only":
        w = wire_usd(usd)
        r.update(units=1, units_label="wire", calendar_years=1, fee_usd=w, known_cost_usd=w)
    elif model == "quota":
        cap = RATE["quota_usd"]
        full = int((usd / cap).to_integral_value(rounding=ROUND_FLOOR))
        rem = usd - cap * full
        fees = wire_usd(cap) * full + (wire_usd(rem) if rem > 0 else D(0))
        n = full + (1 if rem > 0 else 0)
        s = spread_usd(usd)
        r.update(units=n, units_label="wires, one a year", calendar_years=n, spread_usd=s,
                 fee_usd=fees, known_cost_usd=s + fees)
    elif model == "atm":
        cny = usd * RATE["ask"]
        day = RATE["atm_day_cap_cny"]
        full = int((cny / day).to_integral_value(rounding=ROUND_FLOOR))
        rem = cny - day * full
        per_full = min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * day)
        fee_cny = per_full * full
        if rem > 0:
            fee_cny += min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * rem)
        n = full + (1 if rem > 0 else 0)
        f = fee_cny / RATE["ask"]
        r.update(units=n, units_label="withdrawals", calendar_years=ceil_int(cny / RATE["atm_year_cap_cny"]),
                 fee_usd=f, known_cost_usd=f)
    elif model == "cash":
        s = spread_usd(usd, RATE["cash_ask"])
        r.update(units=ceil_int(usd / RATE["cash_no_permit_usd"]), units_label="trips at USD 5,000",
                 extra=ceil_int(usd / RATE["cash_bank_permit_usd"]), spread_usd=s, known_cost_usd=s)
    elif model in ("dividend", "dividend_treaty"):
        tax = usd * (RATE["iit_flat"] if model == "dividend" else RATE["treaty_cap"])
        net = usd - tax
        s, w = spread_usd(net), wire_usd(net)
        r.update(units=1, units_label="wire", calendar_years=1, tax_usd=tax, spread_usd=s, fee_usd=w,
                 known_cost_usd=tax + s + w, extra=net - s - w)
    if r["known_cost_usd"] is not None:
        r["known_cost_pct"] = r["known_cost_usd"] / usd * 100
    return r

def grid():
    return [row(mid_, model, a) for (mid_, _n, model, _s, _f) in METHODS if model != "none" for a in AMOUNTS]

def fx_gain(usd, year):
    return usd - usd * RATE["ask"] / RATE["irs_avg"][year]

if __name__ == "__main__":
    for (mid_, _n, model, _s, _f) in METHODS:
        if model == "none":
            continue
        a, b = row(mid_, model, D(10000)), row(mid_, model, D(400000))
        fmt = lambda v: "blank" if v is None else str(q(v))
        print(mid_, model, fmt(a["known_cost_usd"]), fmt(b["known_cost_usd"]), b["calendar_years"], b["units"])
    for y in sorted(RATE["irs_avg"]):
        print(y, q(fx_gain(D(10000), y)), q(fx_gain(D(400000), y)))
