#!/usr/bin/env python3
"""c348 cost engine - an independently re-derivable model of what it costs to turn RMB into USD.

Every number this script emits is either
  * read from data/c348_inputs.csv, each row of which names an official source, or
  * arithmetic on such numbers, stated in the `formula` column, or
  * left BLANK because no official source read in this pass publishes it, in which case the
    row names a flag in data/c348_flags.csv.

The engine never substitutes zero for an unknown. `scripts/verify_c348.py` recomputes every
cell from the same inputs with exact fractions and does not import this module.

    python3 scripts/c348_engine.py            write data/c348_costs.csv and data/c348_tax.csv
"""
import csv
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CENT = D("0.01")

AMOUNTS = [D(10000) * i for i in range(1, 40)]          # USD 10,000 .. 390,000
AMOUNTS.append(D(400000))                              # and 400,000
YEARS = ["2021", "2022", "2023", "2024", "2025"]


def inp():
    with (DATA / "c348_inputs.csv").open(encoding="utf-8", newline="") as fh:
        return {r["id"]: r for r in csv.DictReader(fh)}


I = inp()


def val(key):
    return D(I[key]["value"])


ASK, BID, MID = val("I02"), val("I01"), val("I04")
WIRE_PCT, WIRE_MIN, WIRE_MAX, CABLE = val("I05"), val("I06"), val("I07"), val("I08")


def q(x):
    return None if x is None else x.quantize(CENT, rounding=ROUND_HALF_UP)


def wire_cny(usd):
    """BOC personal e-banking cross-border wire tariff, in CNY (C02)."""
    return min(WIRE_MAX, max(WIRE_MIN, usd * ASK * WIRE_PCT)) + CABLE


def wire_usd(usd):
    return wire_cny(usd) / ASK


def all_in_cny(usd):
    """The exact CNY the bank debits: the USD purchase at the board selling rate plus the wire."""
    return usd * ASK + wire_cny(usd)


def spread(usd):
    """What the customer pays by trading at the bank's selling rate instead of the mid.

    This is the Bank of China's own buying/selling spread, half of it, applied to the amount.
    It is measured, not assumed: (ask - mid) / ask * usd, computed on today's board.
    """
    return usd * (ASK - MID) / ASK


METHODS = None


def methods():
    global METHODS
    if METHODS is None:
        with (DATA / "c348_methods.csv").open(encoding="utf-8", newline="") as fh:
            METHODS = list(csv.DictReader(fh))
    return METHODS


COST_HEADER = ["method_id", "model", "amount_usd", "units", "units_label", "calendar_years",
               "spread_usd", "wire_fee_usd", "receiving_fee_usd", "usage_fee_usd", "prc_tax_usd",
               "known_cost_usd", "known_cost_pct", "cny_debited", "blank_components", "formula",
               "flag_ids", "source_ids"]


def base(m):
    return dict(method_id=m["id"], model=m["model"], units=None, units_label="", calendar_years=None,
                spread_usd=None, wire_fee_usd=None, receiving_fee_usd=None, usage_fee_usd=None,
                prc_tax_usd=None, known_cost_usd=None, known_cost_pct=None, cny_debited=None,
                blank_components="", formula="", flag_ids="", source_ids=m["source_ids"])


APPLICABLE = {
    # which components genuinely apply to each model; anything applicable but None is a BLANK, anything
    # not applicable is stated as such in the formula text and is not counted as a blank.
    "one_wire": ["spread", "wire", "receiving"],
    "wire_only": ["wire", "receiving"],
    "rmb_out": ["spread", "wire", "receiving"],
    "quota_split": ["spread", "wire", "receiving"],
    "atm": ["spread", "usage", "receiving"],
    "cash": ["spread"],
    "approval_wire": ["spread", "wire", "receiving"],
    "none": [],
}
KEYS = {"spread": "spread_usd", "wire": "wire_fee_usd", "receiving": "receiving_fee_usd",
        "usage": "usage_fee_usd", "prc_tax": "prc_tax_usd"}
LABEL = {"spread": "spread", "wire": "wire tariff", "receiving": "receiving-bank fee",
         "usage": "card/ATM tariff", "prc_tax": "PRC tax"}
FLAGFORD = {"rmb_out": {"spread": "F02", "wire": "F02"}, "atm": {"usage": "F04"},
            "approval_wire": {"receiving": "F03"}}


def finish(r, amount):
    """Total = the sum of the KNOWN applicable components; any applicable one that is None is named."""
    blank, total, known = [], D(0), 0
    for name in APPLICABLE[r["model"]]:
        v = r[KEYS[name]]
        if v is None:
            blank.append(LABEL[name])
        else:
            total += v
            known += 1
    # If nothing applicable is known, the total is BLANK - never zero by assumption. The one
    # exception is the model that performs no conversion, where zero is the defined answer.
    r["known_cost_usd"] = q(total) if (known or r["model"] == "none") else None
    r["blank_components"] = "; ".join(blank)
    flags = set(f for f in r["flag_ids"].split("|") if f)
    for name in blank:
        f = FLAGFORD.get(r["model"], {}).get(name, "F03")
        flags.add(f)
    r["flag_ids"] = "|".join(sorted(flags))
    if amount and r["known_cost_usd"] is not None:
        r["known_cost_pct"] = q(D(100) * r["known_cost_usd"] / amount)
    return r


def row_for(m, amount):
    model = m["model"]
    r = base(m)
    r["amount_usd"] = q(amount)
    if model == "one_wire":
        r.update(units=1, units_label="wire", calendar_years=1, spread_usd=q(spread(amount)),
                 wire_fee_usd=q(wire_usd(amount)), cny_debited=q(all_in_cny(amount)),
                 formula=f"spread = amount x (ask {ASK} - mid {MID}) / ask; wire = min({WIRE_MAX}, max({WIRE_MIN}, amount x ask x {WIRE_PCT})) + {CABLE} CNY, converted at ask",
                 flag_ids="")
        return finish(r, amount)
    if model == "wire_only":
        r.update(units=1, units_label="wire", calendar_years=1, wire_fee_usd=q(wire_usd(amount)),
                 spread_usd=q(D(0)),
                 formula="no conversion: the balance is already USD, so the spread is zero; wire = BOC tariff C02",
                 flag_ids="")
        return finish(r, amount)
    if model == "rmb_out":
        r.update(units=1, units_label="remittance", calendar_years=1, spread_usd=None, wire_fee_usd=None,
                 formula="the offshore CNY-to-USD price and the remittance tariff were not verified in this pass, so every cost cell is blank",
                 blank_components="spread; wire tariff", flag_ids="F02")
        return finish(r, amount)
    if model == "quota_split":
        cap = val("I09")
        full = int(amount // cap)
        rem = amount - cap * full
        units = full + (1 if rem > 0 else 0)
        fees = wire_usd(cap) * full + (wire_usd(rem) if rem > 0 else D(0))
        r.update(units=units, units_label="wires, at most one a calendar year", calendar_years=units,
                 spread_usd=q(spread(amount)), wire_fee_usd=q(fees),
                 cny_debited=q(all_in_cny(amount) + (fees - wire_usd(amount)) * ASK),
                 formula=f"spread on the whole amount; wire tariff charged once per USD {cap} tranche; needs {units} calendar years",
                 flag_ids="")
        return finish(r, amount)
    if model == "atm":
        cny = amount * ASK
        year_cap, day_cap = val("I12"), val("I13")
        withdrawals = int((cny / day_cap).to_integral_value(rounding="ROUND_CEILING"))
        years = int((cny / year_cap).to_integral_value(rounding="ROUND_CEILING"))
        r.update(units=withdrawals, units_label="withdrawals of CNY 10,000 equivalent", calendar_years=years,
                 spread_usd=q(spread(amount)), wire_fee_usd=q(D(0)), cny_debited=None,
                 formula="the card/ATM tariff C19 was NOT re-read this pass, so the fee is blank; the annual ceiling C07 is CNY 100,000",
                 blank_components="card/ATM tariff", flag_ids="F04")
        return finish(r, amount)
    if model == "cash":
        permit_cap = D(5000)          # inherited R15: USD 5,000 without a permit
        trips = int((amount / permit_cap).to_integral_value(rounding="ROUND_CEILING"))
        r.update(units=trips, units_label="trips at USD 5,000", calendar_years=trips,
                 spread_usd=q(spread(amount)), wire_fee_usd=q(D(0)),
                 formula=f"the banknote rate equals the spot rate on today's board ({ASK}); {trips} permitted trips of USD 5,000 because the inherited R15 says USD 5,000 without a permit",
                 flag_ids="F05")
        return finish(r, amount)
    if model == "approval_wire":
        r.update(units=1, units_label="approved transfer", calendar_years=None, spread_usd=q(spread(amount)),
                 wire_fee_usd=q(wire_usd(amount)),
                 formula="the SAFE approval route has no published fee; only the ordinary spread and wire tariff are costed",
                 blank_components="approval timeline and any government fee", flag_ids="F06")
        return finish(r, amount)
    if model == "none":
        r.update(units=0, units_label="no transfer", calendar_years=0, spread_usd=q(D(0)), wire_fee_usd=q(D(0)),
                 formula="no conversion takes place, so no conversion cost arises", flag_ids="")
        return finish(r, amount)
    raise SystemExit(f"unknown model {model}")


def build_costs():
    rows = []
    for m in methods():
        for amount in AMOUNTS:
            rows.append(row_for(m, amount))
    rows.sort(key=lambda r: (r["method_id"], D(str(r["amount_usd"]))))
    with (DATA / "c348_costs.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COST_HEADER)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in COST_HEADER})
    return rows


TAX_HEADER = ["amount_usd", "acquired_year", "irs_avg", "spot_ask", "us_basis_usd", "usd_received",
              "usd_gain", "character", "rate", "us_tax_usd", "exclusion_applies", "note", "source_ids"]


def build_tax():
    """The U.S. currency gain on the RMB sold, by the year the RMB was acquired.

    gain = USD received - USD basis, where basis = (CNY paid / IRS yearly average) and
    USD received = CNY paid / spot. With CNY paid = amount x spot, this is
    amount - amount x spot / irs_average. Negative means a loss.
    """
    rows = []
    for amount in AMOUNTS:
        for y in YEARS:
            irs = val(f"I{26 + YEARS.index(y)}")
            received = amount
            basis = amount * ASK / irs
            gain = received - basis
            character, rate, tax, excl, note, src = "", None, None, "", "", "C11|C12|C13|C15"
            if gain < 0:
                character = "loss"
                note = "a personal-transaction currency loss is not deductible (26 U.S.C. 165(c) as applied to personal expenses); no tax is due and no deduction is claimed here"
                src = "C11"
            elif gain <= val("I19"):
                character = "below the personal-transaction exclusion"
                excl = "yes, if the transaction is a personal transaction"
                tax = q(D(0))
                note = "no gain is recognised up to USD 200 for an individual's personal transaction (988(e)(2))"
            else:
                character = "capital gain (IRS Pub. 525) - or ordinary income if the money is business or investment money (988(a)(1)(A))"
                rate = val("I20")
                tax = q(gain * rate)
                note = "USD 200 exclusion does not apply; tax shown at the 15% long-term capital rate, the rate IRS Topic 409 gives for most single filers in this range"
                src = "C11|C12|C13|C15"
            rows.append(dict(amount_usd=q(amount), acquired_year=y, irs_avg=irs, spot_ask=ASK,
                             us_basis_usd=q(basis), usd_received=q(received), usd_gain=q(gain),
                             character=character, rate=("" if rate is None else rate), us_tax_usd=("" if tax is None else tax),
                             exclusion_applies=excl, note=note, source_ids=src))
    with (DATA / "c348_tax.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=TAX_HEADER)
        w.writeheader()
        w.writerows(rows)
    return rows




PEN_HEADER = ["penalty_id", "side", "instrument", "amount_usd", "exposure_usd", "exposure_pct", "basis", "source_ids"]


def penalty_rows():
    """Turn each penalty rule into a dollar exposure at each amount.

    A percentage rule is computed. A fixed rule is stated as a fixed figure. A rule whose
    exposure depends on facts not in evidence (the tax on the income, the character of the gain)
    takes its figure from the tax ladder where that is computable and is otherwise left BLANK.
    """
    with (DATA / "c348_penalties.csv").open(encoding="utf-8", newline="") as fh:
        rules = list(csv.DictReader(fh))
    tax = {(str(r["amount_usd"]), r["acquired_year"]): r for r in
           csv.DictReader((DATA / "c348_tax.csv").open(encoding="utf-8", newline=""))}
    out = []
    for rule in rules:
        for amount in AMOUNTS:
            model, param = rule["model"], D(str(rule["parameter"]))
            exposure, pct, basis = None, None, ""
            if model == "percent":
                exposure = q(amount * param)
                pct = q(D(100) * param)
                basis = f"amount x {param}"
            elif model == "none":
                exposure, pct, basis = q(D(0)), q(D(0)), "no penalty found for this conduct"
            elif model == "fixed":
                exposure, pct, basis = q(param), q(D(100) * param / amount), "fixed figure, independent of the amount"
            elif model == "greater_of":
                half = amount / 2
                exposure = q(max(param, half))
                pct = q(D(100) * exposure / amount)
                basis = f"greater of USD {param} or 50% of the balance"
            elif model == "tax_from_table":
                # the 2024 acquisition year is the one used to illustrate; the ladder has every year
                row = tax[(f"{q(amount)}", "2024")]
                exposure = D(row["us_tax_usd"]) if row["us_tax_usd"] else None
                pct = q(D(100) * exposure / amount) if exposure is not None else None
                basis = "gain if acquired in 2024 x 15%, from data/c348_tax.csv - the character is disputed (F07)"
            elif model == "unverified":
                basis = "exposure depends on facts not in evidence in this pass - left BLANK"
            out.append(dict(penalty_id=rule["id"], side=rule["side"], instrument=rule["instrument"],
                            amount_usd=q(amount), exposure_usd=("" if exposure is None else exposure),
                            exposure_pct=("" if pct is None else pct), basis=basis,
                            source_ids=rule["source_id"]))
    return out


def build_penalties():
    rows = penalty_rows()
    with (DATA / "c348_penalty_ladder.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PEN_HEADER)
        w.writeheader()
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    costs = build_costs()
    tax = build_tax()
    pens = build_penalties()
    print(f"wrote data/c348_costs.csv  ({len(costs)} rows)")
    print(f"wrote data/c348_tax.csv    ({len(tax)} rows)")
    print(f"wrote data/c348_penalty_ladder.csv ({len(pens)} rows)")
    for mid in ("M01", "M02", "M04", "M10", "M11"):
        sel = [r for r in costs if r["method_id"] == mid and r["amount_usd"] in ("10000", "400000")]
        for r in sel:
            print(f"  {mid}  {r['amount_usd']:>7}  known={r['known_cost_usd']}  pct={r['known_cost_pct']}  "
                  f"units={r['units']} years={r['calendar_years']} blank={r['blank_components'] or '-'}")
    g = [r for r in tax if str(r["amount_usd"]).startswith("10000")]
    print("  USD 10,000 gain by acquisition year:",
          ", ".join(f"{r['acquired_year']}:{r['usd_gain']}" for r in g))
