#!/usr/bin/env python3
"""Independent re-derivation of the e347 cost ladder, repricing and penalty exposure.

Session `arena/bea42a88-china3` (namespace `bea4`), 2026-11-11.

What this does, and why it is a separate implementation:

1. Recomputes every monetary cell of `data/e347_costs.csv` from the published inputs
   (Bank of China board + published tariff + published caps) using this file's own
   arithmetic — it does NOT import `scripts/e347_costs.py`, so a shared bug cannot
   hide itself.
2. Reprices the same 11 routes at the board read on 2026-11-11 15:30:04 Beijing, so the
   difference between the dashboard snapshot (10 Nov) and today is quantified rather
   than asserted.
3. Applies the published penalty percentages (State Council Order 532 Arts 39/40/42/45/48;
   31 CFR 1010.821; 26 U.S.C. 6039F; IRS Form 8938 comparison page) to the same amounts,
   so the "conversion penalty" can be compared with the lawful bank cost at each step.

Inputs are the three figures the dashboard itself publishes (see data/e347_sources.csv
rows S01, S02, S03 and the caps in S06/S19/S20). Nothing is inferred; where no official
page gives a number the cell stays blank.

Outputs (all deterministic, checked by scripts/verify_bea4_site.py):
  data/bea4_cost_recheck.csv     440 rows, published vs independently recomputed
  data/bea4_repricing.csv        440 rows, 10 Nov board vs 11 Nov board
  data/bea4_penalty_exposure.csv  40 rows, statutory exposure vs lawful cost
  data/bea4_summary.json         counts and headline deltas for the pages
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

CENT = D("0.01")
PCT = D("0.0001")


def q2(x):
    return None if x is None else x.quantize(CENT, rounding=ROUND_HALF_UP)


def q4(x):
    return None if x is None else x.quantize(PCT, rounding=ROUND_HALF_UP)


def ceil_int(x):
    return int(x.to_integral_value(rounding=ROUND_CEILING))


# --------------------------------------------------------------------------- boards
# The dashboard snapshot, copied from scripts/e347_data.py RATE (board 2026/11/10 17:39:58).
BOARD_10NOV = dict(
    time="2026/11/10 17:39:58",
    bid=D("6.6571"), ask=D("6.6851"), cash_ask=D("6.6851"), middle=D("6.7167"),
)
# Read on 2026-11-11 from https://www.boc.cn/sourcedb/whpj/enindex_1619.html
# USD row: Buying 666.06, Cash Buying 666.06, Selling 668.86, Cash Selling 668.86,
# Middle 671.91, Pub Time 2026/11/11 15:30:04.  CNY per 100 USD -> per 1 USD below.
BOARD_11NOV = dict(
    time="2026/11/11 15:30:04",
    bid=D("6.6606"), ask=D("6.6886"), cash_ask=D("6.6886"), middle=D("6.7191"),
)

TARIFF = dict(
    wire_rate=D("0.001"), wire_min=D("50"), wire_max=D("260"), cable=D("150"),
    atm_fixed=D("12"), atm_pct=D("0.01"), atm_max=D("112"),
    atm_day_cap_cny=D("10000"), atm_year_cap_cny=D("100000"),
    quota_usd=D("50000"), cash_no_permit_usd=D("5000"), cash_bank_permit_usd=D("10000"),
    iit_flat=D("0.20"),
)

AMOUNTS = [D(x) for x in range(10000, 400001, 10000)]

MODELS = {
    "L01": "fx_wire", "L02": "fx_wire", "L03": "wire_only", "L04": "property",
    "L05": "fx_wire", "L06": "fx_wire", "L07": "quota", "L08": "blank",
    "L09": "dividend", "L10": "atm", "L11": "cash",
}


def wire_cny(usd, board):
    """BOC personal e-banking cross-border wire tariff (S02), in CNY."""
    pct = usd * board["ask"] * TARIFF["wire_rate"]
    return min(TARIFF["wire_max"], max(TARIFF["wire_min"], pct)) + TARIFF["cable"]


def recompute(method_id, usd, board):
    """Independent implementation of each published cost model."""
    t = TARIFF
    ask = board["ask"]
    mid = (board["bid"] + ask) / 2
    out = dict(spread_usd=None, fee_usd=None, tax_usd=None, total=None, rmb=None,
               units=None, years=None)
    model = MODELS[method_id]
    if model in ("fx_wire", "property"):
        spread = usd * (ask - mid) / ask
        fee = wire_cny(usd, board) / ask
        out.update(spread_usd=spread, fee_usd=fee, total=spread + fee,
                   rmb=usd * ask + wire_cny(usd, board), units=1, years=1)
    elif model == "wire_only":
        fee = wire_cny(usd, board) / ask
        out.update(fee_usd=fee, total=fee, units=1, years=1)
    elif model == "quota":
        full = int((usd / t["quota_usd"]).to_integral_value(rounding=ROUND_FLOOR))
        rem = usd - t["quota_usd"] * full
        fee = (wire_cny(t["quota_usd"], board) / ask) * full
        if rem > 0:
            fee += wire_cny(rem, board) / ask
        n = full + (1 if rem > 0 else 0)
        spread = usd * (ask - mid) / ask
        out.update(spread_usd=spread, fee_usd=fee, total=spread + fee, units=n, years=n)
    elif model == "atm":
        cny = usd * ask
        full = int((cny / t["atm_day_cap_cny"]).to_integral_value(rounding=ROUND_FLOOR))
        rem = cny - t["atm_day_cap_cny"] * full
        per = min(t["atm_max"], t["atm_fixed"] + t["atm_pct"] * t["atm_day_cap_cny"])
        fee_cny = per * full
        if rem > 0:
            fee_cny += min(t["atm_max"], t["atm_fixed"] + t["atm_pct"] * rem)
        n = full + (1 if rem > 0 else 0)
        fee = fee_cny / ask
        out.update(fee_usd=fee, total=fee, units=n,
                   years=ceil_int(cny / t["atm_year_cap_cny"]))
    elif model == "cash":
        cash_mid = (board["bid"] + board["cash_ask"]) / 2
        spread = usd * (board["cash_ask"] - cash_mid) / board["cash_ask"]
        out.update(spread_usd=spread, total=spread,
                   units=ceil_int(usd / t["cash_no_permit_usd"]),
                   years=None)
    elif model == "dividend":
        tax = usd * t["iit_flat"]
        net = usd - tax
        spread = net * (ask - mid) / ask
        fee = wire_cny(net, board) / ask
        out.update(tax_usd=tax, spread_usd=spread, fee_usd=fee,
                   total=tax + spread + fee, units=1, years=1)
    return out


def published_rows():
    with open(DATA / "e347_costs.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def dec(text):
    return D(text) if text not in (None, "") else None


def cost_recheck():
    rows, mismatches_total, cells = [], 0, 0
    for pub in published_rows():
        method, amount = pub["method_id"], D(pub["amount_usd"])
        got = recompute(method, amount, BOARD_10NOV)
        checks = [
            ("spread_usd", dec(pub["spread_usd"]), q2(got["spread_usd"])),
            ("fee_usd", dec(pub["fee_usd"]), q2(got["fee_usd"])),
            ("tax_usd", dec(pub["tax_usd"]), q2(got["tax_usd"])),
            ("known_cost_usd", dec(pub["known_cost_usd"]), q2(got["total"])),
            ("known_cost_pct", dec(pub["known_cost_pct"]),
             None if got["total"] is None else q4(got["total"] / amount * 100)),
            ("rmb_debited", dec(pub["rmb_debited"]), q2(got["rmb"])),
        ]
        bad, worst = 0, D("0")
        for _, want, have in checks:
            if want is None and have is None:
                continue
            cells += 1
            if want is None or have is None or want != have:
                bad += 1
                if want is not None and have is not None:
                    worst = max(worst, abs(want - have))
        mismatches_total += bad
        rows.append(dict(
            method_id=method, amount_usd=int(amount), model=MODELS[method],
            published_spread=pub["spread_usd"], recomputed_spread=str(q2(got["spread_usd"]) or ""),
            published_fee=pub["fee_usd"], recomputed_fee=str(q2(got["fee_usd"]) or ""),
            published_tax=pub["tax_usd"], recomputed_tax=str(q2(got["tax_usd"]) or ""),
            published_total=pub["known_cost_usd"], recomputed_total=str(q2(got["total"]) or ""),
            published_pct=pub["known_cost_pct"], recomputed_pct=str(q4(None if got["total"] is None else got["total"] / amount * 100) or ""),
            published_rmb=pub["rmb_debited"], recomputed_rmb=str(q2(got["rmb"]) or ""),
            cells_compared=sum(1 for _, w, h in checks if not (w is None and h is None)),
            mismatches=bad, max_abs_delta=str(worst),
        ))
    return rows, mismatches_total, cells


def repricing():
    rows = []
    for pub in published_rows():
        method, amount = pub["method_id"], D(pub["amount_usd"])
        old = recompute(method, amount, BOARD_10NOV)
        new = recompute(method, amount, BOARD_11NOV)
        if old["total"] is None or new["total"] is None:
            rows.append(dict(method_id=method, amount_usd=int(amount),
                             cost_10nov_usd="", cost_11nov_usd="", delta_usd="",
                             rmb_10nov="", rmb_11nov="", delta_rmb="", pct_change_cost=""))
            continue
        if old["rmb"] is None or new["rmb"] is None:
            rmb_10 = rmb_11 = d_rmb = ""
        else:
            rmb_10, rmb_11 = str(q2(old["rmb"])), str(q2(new["rmb"]))
            d_rmb = str(q2(new["rmb"] - old["rmb"]))
        rows.append(dict(
            method_id=method, amount_usd=int(amount),
            cost_10nov_usd=str(q2(old["total"])), cost_11nov_usd=str(q2(new["total"])),
            delta_usd=str(q2(new["total"] - old["total"])),
            rmb_10nov=rmb_10, rmb_11nov=rmb_11, delta_rmb=d_rmb,
            pct_change_cost=str(q4((new["total"] - old["total"]) / old["total"] * 100))
            if old["total"] else "",
        ))
    return rows


# --------------------------------------------------------------- penalty exposure
def penalty_exposure():
    """Statutory penalty percentages applied to the same 40 amounts.

    China, State Council Order 532 (S17):
      Art 39 逃汇 / Art 40 套汇 / Art 45 private FX dealing: up to 30% of the amount;
      where the circumstances are serious, 30% up to the equivalent of 100%.
      Art 42 carrying currency across the border in breach: warning, up to 20%.
      Art 48 individual, untrue/incomplete documents: up to RMB 50,000 (fixed).
    U.S.:
      31 CFR 1010.821 (S31) willful FBAR: greater of USD 165,353 or 50% of the balance;
      non-willful FBAR: USD 16,536 per violation.
      Form 8938 (S29): up to USD 10,000, plus USD 10,000 per 30 days after notice, max USD 60,000.
      26 U.S.C. 6039F(c) (S33): 5% of the foreign gift per month, capped at 25%.
    """
    rows = []
    for amount in AMOUNTS:
        lawful = recompute("L01", amount, BOARD_10NOV)["total"]
        rows.append(dict(
            amount_usd=int(amount),
            cn_fine_min_30pct=str(q2(amount * D("0.30"))),
            cn_fine_max_100pct=str(q2(amount * D("1.00"))),
            cn_carry_cash_max_20pct=str(q2(amount * D("0.20"))),
            cn_documents_fixed_cny="50000",
            us_fbar_willful_greater_of=str(q2(max(D("165353"), amount * D("0.50")))),
            us_fbar_nonwillful_each=str(q2(D("16536"))),
            us_8938_max=str(q2(D("60000"))),
            us_3520_gift_25pct=str(q2(amount * D("0.25"))),
            lawful_cost_l01=str(q2(lawful)),
            lawful_cost_pct=str(q4(lawful / amount * 100)),
            ratio_30pct_to_lawful=str((amount * D("0.30") / lawful).quantize(D("1"), rounding=ROUND_HALF_UP)),
            ratio_100pct_to_lawful=str((amount / lawful).quantize(D("1"), rounding=ROUND_HALF_UP)),
        ))
    return rows


def summary(recheck_rows, mismatch_cells, compared_cells, repriced):
    by_method = {}
    for r in repriced:
        if not r["delta_usd"]:
            continue
        mid_ = r["method_id"]
        d = by_method.setdefault(mid_, dict(min_delta=None, max_delta=None, max_pct=D("0"), n=0))
        val = D(r["delta_usd"])
        d["n"] += 1
        d["min_delta"] = val if d["min_delta"] is None else min(d["min_delta"], val)
        d["max_delta"] = val if d["max_delta"] is None else max(d["max_delta"], val)
        if r["pct_change_cost"]:
            d["max_pct"] = max(d["max_pct"], abs(D(r["pct_change_cost"])))
    priced = [r for r in recheck_rows if r["published_total"]]
    return dict(
        generated_for="2026-11-11",
        board_10nov=BOARD_10NOV["time"],
        board_11nov=BOARD_11NOV["time"],
        rows=len(recheck_rows),
        cells_compared=compared_cells,
        mismatched_cells=mismatch_cells,
        methods=sorted({r["method_id"] for r in recheck_rows}),
        amounts=len(AMOUNTS),
        priced_rows=len(priced),
        repriced_rows=len(repriced),
        repricing_by_method={k: {kk: str(vv) for kk, vv in v.items()} for k, v in sorted(by_method.items())},
        spread_10nov_pct=str(q4((BOARD_10NOV["ask"] - BOARD_10NOV["bid"]) / BOARD_10NOV["ask"] * 100)),
        spread_11nov_pct=str(q4((BOARD_11NOV["ask"] - BOARD_11NOV["bid"]) / BOARD_11NOV["ask"] * 100)),
        mid_10nov=str(q4((BOARD_10NOV["bid"] + BOARD_10NOV["ask"]) / 2)),
        mid_11nov=str(q4((BOARD_11NOV["bid"] + BOARD_11NOV["ask"]) / 2)),
        middle_col_10nov=str(BOARD_10NOV["middle"]),
        middle_col_11nov=str(BOARD_11NOV["middle"]),
        wire_cny_at_400k_10nov=str(q2(wire_cny(D("400000"), BOARD_10NOV))),
        wire_cny_at_400k_11nov=str(q2(wire_cny(D("400000"), BOARD_11NOV))),
    )


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    rows, bad, cells = cost_recheck()
    write_csv(DATA / "bea4_cost_recheck.csv", rows)
    rep = repricing()
    write_csv(DATA / "bea4_repricing.csv", rep)
    pen = penalty_exposure()
    write_csv(DATA / "bea4_penalty_exposure.csv", pen)
    s = summary(rows, bad, cells, rep)
    (DATA / "bea4_summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
    print(f"bea4 recheck: {len(rows)} cost rows, {cells} cells compared, {bad} mismatches")
    print(f"bea4 repricing: {len(rep)} rows; {len(pen)} penalty rows")
    print(json.dumps({k: s[k] for k in ("board_10nov", "board_11nov", "spread_10nov_pct",
                                        "spread_11nov_pct", "mid_10nov", "mid_11nov")}, indent=2))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
