#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""n676 cost engine — re-derives the USD 10,000 -> 400,000 ladder from first principles.

Every constant in INPUTS below was read off an official page on 2026-11-11 and is
recorded, with its verbatim quote, in data/n676_sources.csv. Nothing in this file is
inherited from an earlier session's CSV; the engine computes the ladder and the
verifier re-derives it independently from the same two inputs.

Arithmetic convention (stated on every page it appears on):

  own_mid   = (buying + selling) / 2          a mid-point we calculate ourselves.
                                                BOC's own "Middle Rate" column is a
                                                different number and is NOT used here.
  spread    = USD * (selling - own_mid) / selling      the cost of the bank's rate
  wire_cny  = clamp(0.001 * CNY_sent, 50, 260) + 150   1 per mille, floor RMB 50,
                                                       ceiling RMB 260, plus the RMB
                                                       150 telegraph charge for a
                                                       destination outside HK/Macau/TW
  CNY_sent  = USD * selling                   you pay the bank's SELLING rate to buy
                                              dollars, so the fee base is the RMB you
                                              actually hand over
  wire_usd  = wire_cny / selling
  total     = round(spread, 2) + round(wire_usd, 2)   components rounded once, then
                                                      added, so the published parts
                                                      always sum to the published total

  gain988   = USD * (1 - selling / basis)     the U.S. currency gain on the RMB if it
                                              had been acquired at that year's IRS
                                              yearly average rate. A gain, not a tax.
"""

from __future__ import annotations

import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# --------------------------------------------------------------------------- inputs
# Verbatim from https://www.boc.cn/sourcedb/whpj/enindex_1619.html, USD row,
# published 2026-11-11 10:25:02 (Beijing). Board quotes are RMB per 100 USD.
BOARD = {
    "stamp": "2026-11-11 10:25:02",
    "buying_cents": 666.30,     # 现汇买入价 / Buying Rate
    "selling_cents": 669.11,    # 现汇卖出价 / Selling Rate
    "middle_cents": 671.91,     # BOC's own "Middle Rate" column — recorded, not used
    "url": "https://www.boc.cn/sourcedb/whpj/enindex_1619.html",
    "source_id": "N01",
}

# Verbatim from https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html
# 跨境汇款（电汇）: 每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；
#                   另收电讯费，港澳台地区人民币80元/笔，非港澳台地区人民币150元/笔
TARIFF = {
    "rate": 0.001,
    "floor_cny": 50.0,
    "ceiling_cny": 260.0,
    "telegraph_cny_non_hkmo": 150.0,
    "telegraph_cny_hkmo": 80.0,
    "url": "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
    "source_id": "N02",
}

# Verbatim from https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates
# China | Yuan | 2025: 7.129 | 2024: 7.189 | 2023: 7.075 | 2022: 6.730 | 2021: 6.452
IRS_AVERAGES = {
    2025: 7.129,
    2024: 7.189,
    2023: 7.075,
    "url": "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates",
    "source_id": "N10",
}

# 26 U.S.C. 988(e)(2): no gain is recognised on a personal-transaction disposition of
# nonfunctional currency unless the gain would otherwise exceed $200.
SEC988_PERSONAL_DE_MINIMIS = 200.0
SEC988_URL = ("https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/"
              "USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm")
SEC988_SOURCE_ID = "N11"

STEP = 10_000
AMOUNTS = list(range(STEP, 400_000 + 1, STEP))
CONVENIENCE_USD = 50_000          # 汇发〔2020〕14号 art. 55 annual convenience amount


def rates():
    bid = BOARD["buying_cents"] / 100.0
    ask = BOARD["selling_cents"] / 100.0
    return bid, ask, (bid + ask) / 2.0


def spread_usd(usd: float, ask: float, own_mid: float) -> float:
    """What the bank's selling rate costs against our own mid-point, in USD."""
    return usd * (ask - own_mid) / ask


def wire_fee_cny(usd: float, ask: float, hkmo: bool = False) -> float:
    cny = usd * ask
    pct = cny * TARIFF["rate"]
    pct = max(TARIFF["floor_cny"], min(TARIFF["ceiling_cny"], pct))
    return pct + (TARIFF["telegraph_cny_hkmo"] if hkmo else TARIFF["telegraph_cny_non_hkmo"])


def gain988(usd: float, ask: float, basis: float) -> float:
    """U.S. currency gain if the RMB had been acquired at `basis` RMB/USD."""
    return usd * (1.0 - ask / basis)


def wires_needed(usd: float) -> int:
    """How many wires the USD 50,000 convenience amount forces, one per calendar year."""
    return -(-int(usd) // CONVENIENCE_USD)


def row(usd: int, kind: str) -> dict:
    bid, ask, own_mid = rates()
    hkmo = kind == "convert_hkmo"
    if kind == "already_usd":
        # R2: the money is already dollars in a Chinese foreign-currency account.
        # No conversion, so no spread — wire fee only.
        spread, n_wires = 0.0, 1
    elif kind in ("convert_once", "convert_hkmo"):
        spread, n_wires = spread_usd(usd, ask, own_mid), 1
    elif kind == "convenience":
        # R3: holders of a Chinese Foreign Permanent Resident ID only. USD 50,000
        # a year on the card alone, so a large balance is bought and wired year by
        # year — one wire per year, one telegraph charge each.
        spread, n_wires = spread_usd(usd, ask, own_mid), wires_needed(usd)
    else:
        raise ValueError(kind)

    wire_cny = 0.0
    if kind == "already_usd":
        wire_cny = wire_fee_cny(usd, ask)
    else:
        for _ in range(n_wires):
            wire_cny += wire_fee_cny(usd / n_wires, ask, hkmo=hkmo)
    wire_usd = wire_cny / ask

    s_r = round(spread, 2)
    w_r = round(wire_usd, 2)
    total = round(s_r + w_r, 2)
    # R2 never converts RMB, so there is no disposition of nonfunctional currency at
    # the wire and no basis rate we could cite. Left blank and flagged (N676-U04)
    # rather than guessed.
    g = {}
    if kind == "already_usd":
        g = {"gain_2025": "", "gain_2024": "", "gain_2023": "",
             "gain_2024_taxable": "UNVERIFIED — no conversion, so no basis rate we can cite"}
    else:
        g24 = gain988(usd, ask, IRS_AVERAGES[2024])
        g = {"gain_2025": f"{gain988(usd, ask, IRS_AVERAGES[2025]):.2f}",
             "gain_2024": f"{g24:.2f}",
             "gain_2023": f"{gain988(usd, ask, IRS_AVERAGES[2023]):.2f}",
             "gain_2024_taxable": ("over the USD 200 personal-transaction threshold, so recognised as ordinary income"
                                   if g24 > SEC988_PERSONAL_DE_MINIMIS
                                   else "at or below the USD 200 personal-transaction threshold")}
    return {
        "amount_usd": usd,
        "kind": kind,
        "n_wires": n_wires,
        "spread_usd": f"{s_r:.2f}",
        "wire_cny": f"{wire_cny:.2f}",
        "wire_usd": f"{w_r:.2f}",
        "total_usd": f"{total:.2f}",
        "total_pct": f"{100.0 * total / usd:.4f}",
        "cny_out": f"{usd * ask:.2f}",
        **g,
        "sources": f"{TARIFF['source_id']}|{BOARD['source_id']}|{IRS_AVERAGES['source_id']}|{SEC988_SOURCE_ID}",
    }


KINDS = [
    ("convert_once", "R1", "Buy dollars and wire once to the U.S. — documented income, home sale, inheritance, emigrant transfer"),
    ("already_usd", "R2", "Wire out dollars already in your Chinese foreign-currency account — no conversion at all"),
    ("convenience", "R3", "USD 50,000 a year on a Chinese Foreign Permanent Resident ID — one wire per year"),
    ("convert_hkmo", "R4", "Buy dollars and wire to Hong Kong, Macau or Taiwan (RMB 80 telegraph, not RMB 150) — first leg only"),
]


def ladder():
    out = []
    for usd in AMOUNTS:
        for kind, _rid, _label in KINDS:
            r = row(usd, kind)
            r["route_id"] = _rid
            r["route"] = _label
            out.append(r)
    return out


FIELDS = ["amount_usd", "route_id", "route", "kind", "n_wires", "spread_usd", "wire_cny",
          "wire_usd", "total_usd", "total_pct", "cny_out",
          "gain_2025", "gain_2024", "gain_2023", "gain_2024_taxable", "sources"]


def write_ladder() -> str:
    path = os.path.join(DATA, "n676_ladder.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in ladder():
            w.writerow({k: r[k] for k in FIELDS})
    return path


if __name__ == "__main__":
    bid, ask, own_mid = rates()
    print(f"board {BOARD['stamp']}  buying {bid}  selling {ask}  own mid {own_mid:.5f}  "
          f"BOC middle column {BOARD['middle_cents'] / 100.0}")
    print(f"spread share of every dollar: {100.0 * (ask - own_mid) / ask:.5f}%")
    p = write_ladder()
    print(f"wrote {p}: {len(ladder())} rows = {len(AMOUNTS)} increments x {len(KINDS)} routes")
    for usd in (10_000, 100_000, 400_000):
        for kind, rid, _l in KINDS:
            r = row(usd, kind)
            print(f"  ${usd:>7,} {rid}  wires={r['n_wires']}  spread={r['spread_usd']:>8}  "
                  f"wire={r['wire_usd']:>7}  total={r['total_usd']:>8}  ({r['total_pct']}%)  "
                  f"gain24={r['gain_2024']:>9}")
