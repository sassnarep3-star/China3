#!/usr/bin/env python3
"""C5BF final-integration data: BOC FX-board observation register and an
independently re-derived $10k-$400k cost ladder at the LATEST published board.

Everything here is derived from two things only:
  1. BOC's official FX board page (https://www.boc.cn/sourcedb/whpj/), read twice
     on 2026-11-10 (07:32:39 snapshot already used by the rest of the site, and a
     fresh 17:39:58 snapshot taken during this integration session).
  2. BOC's published personal cross-border wire tariff
     (https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html):
     1 permille, min CNY 50, max CNY 260, plus a CNY 150 cable fee (CNY 80 to
     HK/MO/TW), and the published personal OUR surcharge
     (https://www.boc.cn/pbservice/bi2/201412/t20141231_4404048.html): US$15 per
     wire when the beneficiary bank holds an account at BOC New York, otherwise
     US$25.

No value is inferred. Intermediary-bank and US receiving-bank fees have no
official published schedule and are therefore left BLANK, not zero.

Outputs: data/c5bf_board_observations.csv, data/c5bf_cost_10k_400k_latest.csv,
         data/c5bf_cost_delta.csv
"""
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BOARD_URL = "https://www.boc.cn/sourcedb/whpj/"
TARIFF_URL = "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html"
OUR_URL = "https://www.boc.cn/pbservice/bi2/201412/t20141231_4404048.html"
SAFE64_URL = "https://www.safe.gov.cn/tianjin/2024/0229/2402.html"
SAFE59_URL = "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"

D = Decimal
TWO = D("0.01")


def q2(x):
    return x.quantize(TWO, rounding=ROUND_HALF_UP)


# (obs_id, board stamp as published by BOC (Beijing time), UTC fetch, 100-unit quotes)
OBS = [
    ("OBS-0732", "2026-11-10 07:32:39", "2026-11-10T07:32:39Z", "666.22", "669.03", "671.88",
     "canonical snapshot used by every existing page on this site (repo source id S01)"),
    ("OBS-1739", "2026-11-10 17:39:58", "2026-11-10T09:51:30Z", "665.71", "668.51", "671.67",
     "fresh snapshot taken during final integration (C5BF-T1/T2); BOC republishes the board intraday"),
]

OBS_HEADER = ["obs_id", "board_stamp_beijing", "fetched_utc", "bid_100usd", "ask_100usd",
              "parity_100usd", "bid", "ask", "parity", "half_spread_pct_of_ask",
              "half_spread_pct_of_mid", "full_spread_pct_of_ask", "source_url", "note"]


def derive(bid100, ask100, parity100):
    bid, ask, par = D(bid100) / 100, D(ask100) / 100, D(parity100) / 100
    mid = (ask + bid) / 2
    return {
        "bid": bid, "ask": ask, "parity": par, "mid": mid,
        "hs_ask": (ask - mid) / ask * 100,
        "hs_mid": (ask - mid) / mid * 100,
        "fs_ask": (ask - bid) / ask * 100,
    }


def ladder(rate, our_usd=D("25")):
    """40 rows, $10,000 .. $400,000 in $10,000 steps."""
    rows = []
    for k in range(1, 41):
        amt = D(10000 * k)
        cny = q2(amt * rate["ask"])
        spread = q2(amt * rate["hs_ask"] / 100)
        permille = D("0.001") * cny
        clamped = min(max(permille, D("50")), D("260"))
        wire_cny = q2(clamped + D("150"))
        wire_usd = q2(wire_cny / rate["ask"])
        total = q2(spread + wire_usd)
        total_our = q2(total + our_usd)
        rows.append({
            "amount_usd": int(amt), "cny_needed": cny, "spread_usd": spread,
            "wire_cny": wire_cny, "wire_usd": wire_usd, "total_usd": total,
            "total_with_our_usd": total_our,
            "total_pct": (total / amt * 100).quantize(D("0.01"), rounding=ROUND_HALF_UP),
            "net_usd": q2(amt - total), "net_with_our_usd": q2(amt - total_our),
            # NO official schedule exists for these two -> blank, never zero
            "intermediary_fee_usd": "", "us_receiving_fee_usd": "",
        })
    return rows


def wcsv(name, header, rows):
    with (DATA / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote data/{name} ({len(rows)} rows)")


def main():
    obs_rows, rates = [], {}
    for oid, stamp, fetched, b, a, p, note in OBS:
        r = derive(b, a, p)
        rates[oid] = r
        obs_rows.append([oid, stamp, fetched, b, a, p, r["bid"], r["ask"], r["parity"],
                         r["hs_ask"].quantize(D("0.0001"), rounding=ROUND_HALF_UP),
                         r["hs_mid"].quantize(D("0.0001"), rounding=ROUND_HALF_UP),
                         r["fs_ask"].quantize(D("0.0001"), rounding=ROUND_HALF_UP),
                         BOARD_URL, note])
    wcsv("c5bf_board_observations.csv", OBS_HEADER, obs_rows)

    latest = ladder(rates["OBS-1739"])
    LH = ["amount_usd", "cny_needed", "spread_usd", "wire_cny", "wire_usd", "total_usd",
          "total_with_our_usd", "total_pct", "net_usd", "net_with_our_usd",
          "intermediary_fee_usd", "us_receiving_fee_usd", "board_obs_id", "source_urls"]
    wcsv("c5bf_cost_10k_400k_latest.csv", LH,
         [[r["amount_usd"], r["cny_needed"], r["spread_usd"], r["wire_cny"], r["wire_usd"],
           r["total_usd"], r["total_with_our_usd"], r["total_pct"], r["net_usd"],
           r["net_with_our_usd"], r["intermediary_fee_usd"], r["us_receiving_fee_usd"],
           "OBS-1739", f"{BOARD_URL}|{TARIFF_URL}|{OUR_URL}"] for r in latest])

    canon = ladder(rates["OBS-0732"])
    DH = ["amount_usd", "total_usd_obs0732", "total_usd_obs1739", "delta_usd",
          "delta_pct_of_total", "board_obs_ids", "source_url"]
    drows = []
    for c, l in zip(canon, latest):
        delta = q2(l["total_usd"] - c["total_usd"])
        drows.append([c["amount_usd"], c["total_usd"], l["total_usd"], delta,
                      (delta / c["total_usd"] * 100).quantize(D("0.01"), rounding=ROUND_HALF_UP),
                      "OBS-0732|OBS-1739", BOARD_URL])
    wcsv("c5bf_cost_delta.csv", DH, drows)
    print(f"  half-spread OBS-0732 {rates['OBS-0732']['hs_ask']:.6f}%  "
          f"OBS-1739 {rates['OBS-1739']['hs_ask']:.6f}%")
    print(f"  $10,000 total: {canon[0]['total_usd']} -> {latest[0]['total_usd']}   "
          f"$400,000 total: {canon[-1]['total_usd']} -> {latest[-1]['total_usd']}")


if __name__ == "__main__":
    main()
