#!/usr/bin/env python3
"""
m5f19 cost engine — CNY -> USD repatriation cost model, USD 10,000 .. 400,000.

Every input below was fetched from an official public page on 2026-11-10 by this
session (session-5f1925df). No figure is inherited from another session's model.

VERIFIED INPUTS
---------------
1. Bank of China published FX board (中国银行外汇牌价), reading 2026-11-10 17:39:58.
   Source: https://www.boc.cn/sourcedb/whpj/
   Row 美元 (USD): 现汇买入价 665.71 | 现钞买入价 665.71 | 现汇卖出价 668.51 |
                   现钞卖出价 668.51 | 中行折算价 671.67
   Board unit is "100 units of foreign currency expressed in CNY", so the quoted
   figures are divided by 100 to get CNY per USD.
   The same page carries BOC's own disclaimer that the table is 仅供参考
   ("for reference only") and that the executable rate is the one shown by BOC
   online banking / mobile banking / smart counter / branch counter. Everything
   derived from it here is therefore a MODEL, not a quote.

2. Bank of China personal e-banking transfer tariff
   (中国银行电子银行个人服务转账汇款费率表), charges effective 2014-11-01.
   Source: https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html
   Row 跨境汇款（电汇）: "每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；
   另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。"
   Note 1 on that page: agreements, promotional discounts and local charging
   differences override the published tariff.

CONVENTION (stated, because the repository contains two and they disagree)
--------------------------------------------------------------------------
For a transfer of USD X purchased with CNY at the board ask:

  mid        = (ask + bid) / 2
  CNY spent  = X * ask
  spread cost (CNY, vs a hypothetical zero-spread mid rate) = X * (ask - mid)

That spread is an OPPORTUNITY COST borne in the CNY you spend. It is NOT a second
deduction from the USD you receive: buying USD X at the ask delivers USD X. This
is the double-counting defect flagged by sessions a502 and a058 and it is avoided
here by construction.

Two denominators are reported side by side, never mixed:
  spread_pct_ask = (ask - mid) / ask    <- "as a share of what you actually paid"
  spread_pct_mid = (ask - mid) / mid    <- "as a share of the mid-market price"

Wire fee: the tariff states 1 per mille of the remittance amount with a CNY 50
floor and a CNY 260 ceiling. Both readings (fee computed on the USD amount, or
computed on the CNY amount then converted back at the same ask) are evaluated and
asserted equal, so the convention cannot silently drift.
"""

from __future__ import annotations

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

# --------------------------------------------------------------------------
# Verified inputs (2026-11-10)
# --------------------------------------------------------------------------

FETCHED = "2026-11-10"
BOARD_DATE = "2026-11-10"
BOARD_TIME = "17:39:58"
BOARD_URL = "https://www.boc.cn/sourcedb/whpj/"

# per 100 USD, as published
ASK_PER_100 = Decimal("668.51")   # 现汇卖出价 — BOC sells USD to you at this
BID_PER_100 = Decimal("665.71")   # 现汇买入价 — BOC buys USD from you at this
BOC_CONV_PER_100 = Decimal("671.67")  # 中行折算价

ASK = ASK_PER_100 / 100           # 6.6851 CNY per USD
BID = BID_PER_100 / 100           # 6.6571 CNY per USD
BOC_CONV = BOC_CONV_PER_100 / 100  # 6.7167 CNY per USD
MID = (ASK + BID) / 2

TARIFF_URL = ("https://www.boc.cn/ebanking/service/cs1/200905/"
              "t20090506_990712.html")
FEE_RATE = Decimal("0.001")        # 1‰
FEE_MIN_CNY = Decimal("50")        # 最低收取50元/笔
FEE_MAX_CNY = Decimal("260")       # 最高收取260元/笔
TELECOM_CNY_NON_HMT = Decimal("150")  # 非港澳台地区
TELECOM_CNY_HMT = Decimal("80")       # 港澳台地区

# Increments required by the brief: USD 10,000 up to USD 400,000 in 10,000 steps.
STEP_USD = 10_000
MIN_USD = 10_000
MAX_USD = 400_000

# Historical board reading used by sessions fbbd3b22 / d6467425 / 775c9619
# (recorded in data/live_rate_20261110.csv). Reproduced here ONLY to prove the
# reconciliation in data/m5f19_reconciliation.csv; never used for m5f19 figures.
LEGACY_ASK = Decimal("6.6903")
LEGACY_BID = Decimal("6.6622")
LEGACY_MID = (LEGACY_ASK + LEGACY_BID) / 2

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    """Round to cents, half-up (the convention banks publish to)."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def fee_usd(amount_usd: Decimal, ask: Decimal = ASK) -> Decimal:
    """BOC cross-border TT fee in USD, from the 1 permille / CNY 50-260 tariff."""
    nominal = amount_usd * FEE_RATE
    floor = FEE_MIN_CNY / ask
    ceiling = FEE_MAX_CNY / ask
    return min(max(nominal, floor), ceiling)


def fee_usd_via_cny(amount_usd: Decimal, ask: Decimal = ASK) -> Decimal:
    """Same fee computed on the CNY leg then converted back — must agree."""
    cny_amount = amount_usd * ask
    nominal_cny = cny_amount * FEE_RATE
    clamped_cny = min(max(nominal_cny, FEE_MIN_CNY), FEE_MAX_CNY)
    return clamped_cny / ask


def telecom_usd(ask: Decimal = ASK, hmt: bool = False) -> Decimal:
    cny = TELECOM_CNY_HMT if hmt else TELECOM_CNY_NON_HMT
    return cny / ask


def leg_cost(amount_usd: Decimal, wires: int, ask: Decimal, bid: Decimal,
             denominator: str) -> dict:
    """Cost of moving `amount_usd` split across `wires` transfers.

    `ask` and `bid` are BOTH passed in. An earlier draft inferred the bid from
    an identity comparison against the module-level ASK constant, which silently
    fell through to the legacy board whenever a freshly constructed Decimal was
    passed. That is why both are explicit parameters now.

    denominator: "ask" -> (ask-mid)/ask ; "mid" -> (ask-mid)/mid
    """
    if denominator not in ("ask", "mid"):
        raise ValueError(f"unknown denominator {denominator!r}")
    if ask <= bid:
        raise ValueError(f"ask {ask} must exceed bid {bid}")
    mid = (ask + bid) / 2
    per_wire = amount_usd / Decimal(wires)

    spread_cny = amount_usd * (ask - mid)
    spread_usd = (spread_cny / ask) if denominator == "ask" else (spread_cny / mid)

    fee_total = fee_usd(per_wire, ask) * wires
    telecom_total = telecom_usd(ask) * wires
    total = spread_usd + fee_total + telecom_total

    return {
        "amount_usd": amount_usd,
        "wires": wires,
        "cny_spent": money(amount_usd * ask),
        "spread_pct": (ask - mid) / ask if denominator == "ask"
                      else (ask - mid) / mid,
        "spread_usd": money(spread_usd),
        "fee_usd": money(fee_total),
        "telecom_usd": money(telecom_total),
        "total_usd": money(total),
        "total_pct": total / amount_usd,
        "denominator": denominator,
    }


def build_ladder():
    """40 increments x {1 wire, 8 wires} x {ask, mid} denominators."""
    rows = []
    amount = MIN_USD
    while amount <= MAX_USD:
        x = Decimal(amount)
        for wires in (1, 8):
            for denom in ("ask", "mid"):
                c = leg_cost(x, wires, ASK, BID, denom)
                rows.append({
                    "amount_usd": amount,
                    "wires": wires,
                    "denominator": denom,
                    "board_date": BOARD_DATE,
                    "board_time": BOARD_TIME,
                    "ask_cny_per_usd": str(ASK),
                    "bid_cny_per_usd": str(BID),
                    "mid_cny_per_usd": str(MID),
                    "cny_spent": str(c["cny_spent"]),
                    "spread_pct": f'{c["spread_pct"] * 100:.6f}',
                    "spread_usd": str(c["spread_usd"]),
                    "fee_usd": str(c["fee_usd"]),
                    "telecom_usd": str(c["telecom_usd"]),
                    "total_usd": str(c["total_usd"]),
                    "total_pct": f'{c["total_pct"] * 100:.6f}',
                })
        amount += STEP_USD
    return rows


def self_checks():
    """Assertions that must hold, or the model is wrong."""
    # 1. Fee convention independence.
    for amount in range(MIN_USD, MAX_USD + 1, STEP_USD):
        x = Decimal(amount)
        a = fee_usd(x)
        b = fee_usd_via_cny(x)
        assert money(a) == money(b), f"fee convention drift at {amount}: {a} vs {b}"

    # 2. The CNY 260 cap binds above ~USD 38,892 at today's ask.
        if amount >= 40_000:
            assert money(a) == money(FEE_MAX_CNY / ASK), f"cap not binding at {amount}"
        if amount == 10_000:
            assert money(a) == Decimal("10.00"), f"fee at 10k should be 10.00, got {a}"

    # 3. Spread is strictly positive and below the full bid/ask spread.
        s = (ASK - MID) / ASK
        assert Decimal("0") < s < (ASK - BID) / ASK

    # 4. Cost is monotonic in amount for a fixed wire count.
    prev = None
    for amount in range(MIN_USD, MAX_USD + 1, STEP_USD):
        c = leg_cost(Decimal(amount), 1, ASK, BID, "ask")["total_usd"]
        if prev is not None:
            assert c > prev, f"non-monotonic at {amount}"
        prev = c

    # 5. Cost per dollar falls with size (the cap bites), for 1 wire.
        p = leg_cost(Decimal(amount), 1, ASK, BID, "ask")["total_pct"]
    small = leg_cost(Decimal(MIN_USD), 1, ASK, BID, "ask")["total_pct"]
    large = leg_cost(Decimal(MAX_USD), 1, ASK, BID, "ask")["total_pct"]
    assert large < small, "all-in percentage should fall with size"

    # 6. Eight wires cost strictly more than one wire at every increment.
    for amount in range(MIN_USD, MAX_USD + 1, STEP_USD):
        one = leg_cost(Decimal(amount), 1, ASK, BID, "ask")["total_usd"]
        eight = leg_cost(Decimal(amount), 8, ASK, BID, "ask")["total_usd"]
        assert eight > one, f"8-wire not costlier at {amount}"

    # 7. Reproduce the two historical published models EXACTLY, to the cent.
    #    fbbd3b22 dashboard: 1 wire, ask denominator, legacy board.
    hist_ask_1 = leg_cost(Decimal(10_000), 1, LEGACY_ASK, LEGACY_BID, "ask")["total_usd"]
    assert hist_ask_1 == Decimal("53.42"), f"legacy 1-wire ask @10k = {hist_ask_1}"
    hist_ask_400 = leg_cost(Decimal(400_000), 1, LEGACY_ASK, LEGACY_BID, "ask")["total_usd"]
    assert hist_ask_400 == Decimal("901.30"), f"legacy 1-wire ask @400k = {hist_ask_400}"
    #    d6467425 refresh: 1 wire, mid denominator (10k) and 8 wires (400k).
    hist_mid_10 = leg_cost(Decimal(10_000), 1, LEGACY_ASK, LEGACY_BID, "mid")["total_usd"]
    assert hist_mid_10 == Decimal("53.47"), f"legacy 1-wire mid @10k = {hist_mid_10}"
    hist_mid_400 = leg_cost(Decimal(400_000), 8, LEGACY_ASK, LEGACY_BID, "mid")["total_usd"]
    assert hist_mid_400 == Decimal("1332.05"), f"legacy 8-wire mid @400k = {hist_mid_400}"


def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    self_checks()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows = build_ladder()
    out = os.path.join(root, "data", "m5f19_ladder.csv")
    write_csv(out, rows, list(rows[0].keys()))

    one_ask = [r for r in rows if r["wires"] == 1 and r["denominator"] == "ask"]
    print(f"OK — {len(rows)} ladder rows written to {out}")
    print(f"board {BOARD_DATE} {BOARD_TIME}  ask {ASK}  bid {BID}  mid {MID}")
    print(f"spread  ask-denom {(ASK-MID)/ASK*100:.6f}%   "
          f"mid-denom {(ASK-MID)/MID*100:.6f}%")
    print(f"fee     CNY {FEE_MAX_CNY} cap = USD {money(FEE_MAX_CNY/ASK)}; "
          f"telecom CNY {TELECOM_CNY_NON_HMT} = USD {money(TELECOM_CNY_NON_HMT/ASK)}")
    for r in (one_ask[0], one_ask[-1]):
        print(f"  USD {r['amount_usd']:>7,}  1 wire  total USD {r['total_usd']:>8}  "
              f"({r['total_pct']}%)  CNY {r['cny_spent']}")
    print("historical models reproduced to the cent: "
          "$53.42 / $901.30 (1 wire, ask-denom) and $53.47 / $1,332.05 (mid-denom, 1/8 wires)")
