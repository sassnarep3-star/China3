#!/usr/bin/env python3
"""Cost model for the e347 dashboard. Pure functions over the inputs in e347_data.RATE.

Every input is a published figure (see e347_data.SOURCES S01-S03, S06, S19, S20, S25, S28).
Costs that no official page publishes are returned as None so they render blank.
"""
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR

from e347_data import RATE, AMOUNTS, METHODS

CENT = D("0.01")


def q(x, places=CENT):
    return x.quantize(places, rounding=ROUND_HALF_UP)


def ceil_int(x):
    return int(x.to_integral_value(rounding=ROUND_CEILING))


def mid():
    """Midpoint of BOC's own buying and selling rates (not the BOC 'Middle Rate' column)."""
    return (RATE["bid"] + RATE["ask"]) / 2


def spread_usd(usd, ask=None):
    ask = ask or RATE["ask"]
    return usd * (ask - mid()) / ask


def wire_cny(usd):
    """BOC personal e-banking cross-border wire: 0.1%, min 50, max 260, plus 150 cable (S02)."""
    pct = usd * RATE["ask"] * RATE["wire_rate"]
    return min(RATE["wire_max"], max(RATE["wire_min"], pct)) + RATE["cable"]


def wire_usd(usd):
    return wire_cny(usd) / RATE["ask"]


def row(method, usd):
    """Return the cost row for one method at one amount. Unknown values are None."""
    model = method["model"]
    ask = RATE["ask"]
    r = dict(method_id=method["id"], model=model, amount_usd=usd, units=None, units_label="",
             calendar_years=None, spread_usd=None, fee_usd=None, tax_usd=None,
             known_cost_usd=None, known_cost_pct=None, rmb_debited=None, extra=None)
    if model in ("fx_wire", "property"):
        s, w = spread_usd(usd), wire_usd(usd)
        r.update(units=1, units_label="wire", calendar_years=1, spread_usd=s, fee_usd=w,
                 known_cost_usd=s + w, rmb_debited=usd * ask + wire_cny(usd))
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
        cny = usd * ask  # BOC selling rate used as a stand-in for the unverified UnionPay rate (flag U13)
        day = RATE["atm_day_cap_cny"]
        full = int((cny / day).to_integral_value(rounding=ROUND_FLOOR))
        rem = cny - day * full
        per_full = min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * day)
        fee_cny = per_full * full
        if rem > 0:
            fee_cny += min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * rem)
        n = full + (1 if rem > 0 else 0)
        f = fee_cny / ask
        r.update(units=n, units_label="withdrawals", calendar_years=ceil_int(cny / RATE["atm_year_cap_cny"]),
                 fee_usd=f, known_cost_usd=f)
    elif model == "cash":
        s = spread_usd(usd, RATE["cash_ask"])
        r.update(units=ceil_int(usd / RATE["cash_no_permit_usd"]), units_label="trips at USD 5,000",
                 extra=ceil_int(usd / RATE["cash_bank_permit_usd"]), spread_usd=s, known_cost_usd=s)
    elif model == "dividend":
        tax = usd * RATE["iit_flat"]
        net = usd - tax
        s, w = spread_usd(net), wire_usd(net)
        r.update(units=1, units_label="wire", calendar_years=1, tax_usd=tax, spread_usd=s, fee_usd=w,
                 known_cost_usd=tax + s + w, extra=net - s - w)
    # model "blank" and "none": nothing is published, everything stays None
    if r["known_cost_usd"] is not None:
        r["known_cost_pct"] = r["known_cost_usd"] / usd * 100
    return r


def grid():
    return [row(m, a) for m in METHODS if m["model"] != "none" for a in AMOUNTS]


def fx_gain(usd, year):
    """USD gain if the RMB sold today for `usd` had been acquired at that year's IRS average rate."""
    return usd - usd * RATE["ask"] / RATE["irs_avg"][year]


if __name__ == "__main__":
    for m in METHODS:
        if m["model"] == "none":
            continue
        a, b = row(m, D(10000)), row(m, D(400000))
        fmt = lambda v: "blank" if v is None else str(q(v))
        print(m["id"], m["model"], fmt(a["known_cost_usd"]), fmt(b["known_cost_usd"]), b["calendar_years"], b["units"])
    for y in sorted(RATE["irs_avg"]):
        print(y, q(fx_gain(D(10000), y)), q(fx_gain(D(400000), y)))
