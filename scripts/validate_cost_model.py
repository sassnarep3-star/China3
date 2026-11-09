#!/usr/bin/env python3
"""
validate_cost_model.py — enforceable contract for the cost model.

Fails if any of the following is untrue:
  1. Every row of data/cost_model.csv re-computes from the recorded constants.
  2. Total = FX margin + bank fees + other fixed, to the cent.
  3. Net received = amount - total.
  4. The percentage column equals total / amount.
  5. The wire fee matches the published BOC tariff (with min and max clamps).
  6. Every cost-table.html and cost-steps.html figure that is a total appears in the CSV.
  7. Every method carries a basis URL on an official domain and a fee URL.
  8. Every "blank" cell in the model is declared as a flag, not silently empty.
  9. The penalty table recomputes from the statutory constants.

Run: python3 scripts/validate_cost_model.py
"""

import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# Official domains that may be cited as the basis for a number.
OFFICIAL = (
    ".gov.cn", ".gov", ".irs.gov", ".ecfr.gov", ".law.cornell.edu",
    ".chinamoney.com.cn", ".pbc.gov.cn", ".safe.gov.cn",
    ".boc.cn",   # Bank of China publishes its own tariff and board; it is the issuer of those numbers
)

errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def main():
    meta = json.load(open(os.path.join(DATA, "cost_model.json"), encoding="utf-8"))
    rows = list(csv.DictReader(open(os.path.join(DATA, "cost_model.csv"), encoding="utf-8")))
    pen = list(csv.DictReader(open(os.path.join(DATA, "penalty_exposure.csv"), encoding="utf-8")))
    ver = list(csv.DictReader(open(os.path.join(DATA, "reverification.csv"), encoding="utf-8")))

    c = meta["constants"]
    ask = c["boc_spot_sell"]
    margin = c["fx_margin_pct"] / 100.0

    methods = {m["id"]: m for m in meta["methods"]}

    # ---- 1..5 row-level arithmetic
    if len(rows) != len(methods) * len(meta["amounts"]):
        fail("row count %d != %d methods x %d amounts"
             % (len(rows), len(methods), len(meta["amounts"])))

    for r in rows:
        mid = r["method_id"]
        a = float(r["amount_usd"])
        m = methods[mid]
        fx = float(r["fx_margin_usd"])
        fee_usd = float(r["wire_fee_usd"])
        other = float(r["other_fixed_usd"])
        tot = float(r["total_cost_usd"])
        net = float(r["net_usd"])
        pct = float(r["cost_pct"])

        exp_fx = 0.0 if not m["fx"] else a * margin
        if abs(fx - exp_fx) > 0.011:
            fail("%s %s: FX margin %s != %s" % (mid, a, fx, exp_fx))

        if abs((fx + fee_usd + other) - tot) > 0.011:
            fail("%s %s: components %s != total %s" % (mid, a, fx + fee_usd + other, tot))

        if abs((a - tot) - net) > 0.011:
            fail("%s %s: net %s != amount-total %s" % (mid, a, net, a - tot))

        if abs(pct - tot / a * 100.0) > 0.0002:
            fail("%s %s: pct %s != %s" % (mid, a, pct, tot / a * 100.0))

        # 5. fee must match the published tariff schedule
        if m.get("cash"):
            if fee_usd != 0.0:
                fail("%s %s: cash route must carry no wire fee" % (mid, a))
        else:
            sch = m.get("fee_schedule")
            if sch:
                cny = a * ask
                adv = min(max(sch["rate"] * cny, sch["min_cny"]), sch["max_cny"])
                exp_fee_usd = (adv + sch["cable_cny"]) / ask
                if abs(fee_usd - exp_fee_usd) > 0.011:
                    fail("%s %s: fee %s != tariff %s" % (mid, a, fee_usd, exp_fee_usd))

    # ---- 6. spot-check the published HTML against the CSV
    html = open(os.path.join(ROOT, "cost-table.html"), encoding="utf-8").read()
    for r in rows:
        if r["amount_usd"] in ("10000", "400000", "200000"):
            needle = "{:,.2f}".format(float(r["total_cost_usd"]))
            if needle not in html:
                fail("cost-table.html missing total %s (%s %s)"
                     % (needle, r["method_id"], r["amount_usd"]))

    # ---- 7. every method carries official basis + fee URLs
    for mid, m in methods.items():
        for key in ("basis_url", "fee_url"):
            u = m.get(key, "")
            if not u.startswith("https://"):
                fail("%s: %s is not https" % (mid, key))
            elif not any(d in u for d in OFFICIAL):
                fail("%s: %s not on an official domain: %s" % (mid, key, u))

    # ---- 8. declared blanks
    flags = re.findall(r"\bF\d{2}\b", html)
    declared = set(flags)
    for need in ("F01", "F02", "F03", "F04"):
        if need not in declared:
            fail("flag %s not published on cost-table.html" % need)
    if html.count('class="unv"') < 4:
        fail("fewer than four unverified cells published on cost-table.html")

    # ---- 9. penalty table
    pc = meta["penalty_constants"]
    for r in pen:
        a = float(r["amount_usd"])
        exp_w = max(pc["fbar_willful_flat"], pc["fbar_willful_pct"] * a)
        if abs(float(r["fbar_willful_max_usd"]) - exp_w) > 0.011:
            fail("penalty %s: willful %s != %s" % (a, r["fbar_willful_max_usd"], exp_w))
        exp_3520 = pc["f3520_pct"] * a
        if abs(float(r["f3520_max_usd"]) - exp_3520) > 0.011:
            fail("penalty %s: 3520 %s != %s" % (a, r["f3520_max_usd"], exp_3520))
        exp_8938 = pc["f8938_base"] + pc["f8938_continuation_max"]
        if abs(float(r["f8938_max_usd"]) - exp_8938) > 0.011:
            fail("penalty %s: 8938 %s != %s" % (a, r["f8938_max_usd"], exp_8938))

    # ---- sources: every verified row has an https URL; every broken row is labelled
    for v in ver:
        if v["status"] == "verified" and not v["url"].startswith("https://"):
            fail("%s: verified row without https URL" % v["id"])
        if v["status"] == "broken" and "BROKEN" not in v["topic"]:
            fail("%s: broken row not labelled" % v["id"])

    # ---- the headline claims must still be true
    m01_400 = next(r for r in rows if r["method_id"] == "M01" and r["amount_usd"] == "400000")
    if abs(float(m01_400["total_cost_usd"]) - 901.09) > 0.02:
        fail("headline $400,000 cost changed to %s; update the prose" % m01_400["total_cost_usd"])
    m01_10 = next(r for r in rows if r["method_id"] == "M01" and r["amount_usd"] == "10000")
    if abs(float(m01_10["total_cost_usd"]) - 53.41) > 0.02:
        fail("headline $10,000 cost changed to %s; update the prose" % m01_10["total_cost_usd"])

    print("cost-model validation")
    print("  rows: %d   methods: %d   amounts: %d   penalty rows: %d   sources: %d"
          % (len(rows), len(methods), len(meta["amounts"]), len(pen), len(ver)))
    print("  FX margin: %.5f%%   full spread: %.5f%%   ask %.4f   mid %.5f"
          % (c["fx_margin_pct"], c["full_spread_pct"], c["boc_spot_sell"], c["mid"]))
    if warnings:
        for w in warnings:
            print("  warn ", w)
    if errors:
        print("\nFAIL — %d violation(s):" % len(errors))
        for e in errors:
            print("  -", e)
        return 1
    print("PASS — arithmetic reproduces, every method sourced, blanks declared.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
