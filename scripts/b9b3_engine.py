#!/usr/bin/env python3
"""Recompute the B9B3 cost matrix from exact official inputs.

Inputs are the Bank of China USD board read on 2026-11-11 at 10:40:02 and the
Bank of China personal cross-border wire tariff.  All arithmetic uses Fraction;
display strings are rounded half-up only at the final CSV boundary.

    python3 scripts/b9b3_engine.py       write data/b9b3_method_costs.csv
                                        and data/b9b3_ladder.csv

The site builder imports cost_outputs() so the published CSVs and HTML cannot
drift apart.  The independent verifier deliberately does NOT import this file.
"""
from __future__ import annotations

import csv
import io
import sys
from decimal import Decimal, ROUND_HALF_UP, getcontext
from fractions import Fraction as F
from pathlib import Path

getcontext().prec = 60
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# BOC board 2026/11/11 10:40:02, CNY per 100 USD: buying 666.31, selling 669.12.
BID = F(66631, 10000)
ASK = F(66912, 10000)
MID = (BID + ASK) / 2
SPREAD_HALF = ASK - MID
BOARD_MIDDLE = F(67191, 10000)  # displayed "Middle Rate"; not the bid/ask midpoint

FEE_RATE = F(1, 1000)
FEE_MIN = F(50)
FEE_MAX = F(260)
CABLE = F(150)  # outside Hong Kong / Macao / Taiwan
QUOTA = 50000
AMOUNTS = list(range(10000, 400001, 10000))

# model, status, default method-specific source ids, default method flags
METHOD_SPECS = {
    "B01": ("fx_wire", "conditional", "BS01|BS02|BS06|BS07|BS13|BS18", "B9B3-F01|B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06"),
    "B02": ("fx_wire", "conditional", "BS01|BS02|BS06|BS09|BS10|BS18", "B9B3-F02|B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06"),
    "B03": ("wire_only", "conditional", "BS02|BS05|BS06|BS20", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F07"),
    "B04": ("fx_wire", "conditional", "BS01|BS02|BS11|BS20", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F17"),
    "B05": ("blank", "conditional", "BS01|BS11|BS22", "B9B3-F03|B9B3-F17|B9B3-F11"),
    "B06": ("quota", "conditional", "BS01|BS02|BS06|BS08|BS09", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F16"),
    "B07": ("fx_wire", "conditional", "BS01|BS02|BS17|BS18|BS28", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06|B9B3-F13"),
    "B08": ("fx_wire", "conditional", "BS01|BS02|BS14|BS15|BS16|BS40", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F12|B9B3-F15"),
    "B09": ("fx_wire", "conditional", "BS01|BS02|BS14|BS15|BS16", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F12"),
    "B10": ("fx_wire", "conditional", "BS01|BS02|BS15|BS18|BS28|BS31|BS32", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06|B9B3-F14"),
    "B11": ("blank", "conditional", "BS19|BS26|BS27", "B9B3-F09"),
    "B12": ("atm", "conditional", "BS03|BS21|BS49|BS50", "B9B3-F10"),
    "B13": ("cash", "conditional", "BS01|BS22|BS49", "B9B3-F11"),
    "B14": ("fx_wire", "conditional", "BS01|BS02|BS06", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06"),
    "B15": ("fx_wire", "conditional", "BS01|BS02|BS06|BS13|BS18", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06"),
    "B16": ("fx_wire", "conditional", "BS01|BS02|BS19", "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06|B9B3-F12"),
    "B17": ("blank", "conditional", "BS26|BS27", "B9B3-F09"),
    "B18": ("blank", "unverified", "BS06|BS07|BS40", "B9B3-F18"),
    "B19": ("blank", "prohibited", "BS12|BS19|BS24", "B9B3-F16"),
    "B20": ("blank", "prohibited", "BS19|BS23|BS24", "B9B3-F20"),
    "B21": ("blank", "prohibited", "BS19|BS23|BS25", "B9B3-F20"),
    "B22": ("blank", "prohibited", "BS19|BS22|BS24|BS49", "B9B3-F11|B9B3-F20"),
}

BASE_SOURCES = {
    "fx_wire": "BS01|BS02|BS05|BS06",
    "wire_only": "BS02|BS05|BS06|BS20",
    "quota": "BS01|BS02|BS05|BS06|BS08|BS09",
    "cash": "BS01|BS05|BS22|BS49",
    "atm": "BS03|BS05|BS21|BS49",
    "blank": "BS02|BS05|BS19",
}
GLOBAL_FLAGS = "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06|B9B3-F07|B9B3-F08|B9B3-F19"
LIMITS = {
    "fx_wire": "Published single-wire BOC benchmark at the 2026-11-11 10:40:02 board; eligibility, OUR/intermediary/receiving fees, PRC tax and U.S. section 988 gain are not verified.",
    "wire_only": "No conversion; usable only for a balance already held in foreign currency. OUR/intermediary/receiving fees and U.S. tax are not verified.",
    "quota": "Arithmetic across ceil(amount/50,000) calendar-year wires; only PRC Foreign Permanent Resident ID holders qualify for purchase on ID alone. Taxes and other fees are not verified.",
    "cash": "Cash selling rate equals the spot selling rate on this board; banknote withdrawal fee, travel cost, permits and U.S. declaration consequences are not priced.",
    "atm": "BOC card-fee formula is published but the UnionPay conversion rate, ATM-owner fee, yearly cap and U.S. cash declaration consequences are not priced. No amount is inferred.",
    "blank": "No official personal fee/rate or lawful eligibility for this amount was verified. Every numeric cost cell is deliberately blank.",
}

COST_FIELDS = [
    "method_id", "amount_usd", "status", "model", "cny_needed_at_ask",
    "fx_spread_usd", "bank_wire_and_cable_usd", "known_bank_cost_usd",
    "known_bank_cost_pct", "net_after_known_bank_cost_usd", "wire_count",
    "calendar_years", "our_fee_usd", "intermediary_fee_usd",
    "receiving_fee_usd", "prc_tax_usd", "us_988_gain_usd",
    "all_in_total_usd", "source_ids", "source_urls", "flag_ids", "limitations",
]
LADDER_FIELDS = [
    "amount_usd", "cny_needed_at_ask", "best_cny_to_usd_method_id",
    "best_cny_to_usd_known_cost_usd", "best_cny_to_usd_pct",
    "wire_only_known_cost_usd", "source_ids", "source_urls", "flag_ids", "limitations",
]


def q(frac: F, places: int = 2) -> str:
    """Exact Fraction -> half-up decimal string with a fixed number of places."""
    dec = Decimal(frac.numerator) / Decimal(frac.denominator)
    quantum = Decimal(1).scaleb(-places)
    return str(dec.quantize(quantum, rounding=ROUND_HALF_UP))


def wire_cny(usd: F) -> F:
    return min(FEE_MAX, max(FEE_MIN, usd * ASK * FEE_RATE)) + CABLE


def wire_usd(usd: F) -> F:
    return wire_cny(usd) / ASK


def spread_usd(usd: F) -> F:
    return usd * SPREAD_HALF / ASK


def pct(cost: F, amount: F) -> F:
    return cost / amount * 100


def dedupe(items) -> list[str]:
    out: list[str] = []
    for raw in items:
        for item in str(raw).split("|"):
            if item and item not in out:
                out.append(item)
    return out


def load_source_map() -> dict[str, str]:
    with (DATA / "b9b3_sources.csv").open(encoding="utf-8", newline="") as fh:
        return {r["source_id"]: r["url"] for r in csv.DictReader(fh)}


def load_method_meta() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    src: dict[str, list[str]] = {}
    flg: dict[str, list[str]] = {}
    with (DATA / "b9b3_methods.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            src[r["method_id"]] = dedupe([r["source_ids"]])
            flg[r["method_id"]] = dedupe([r["flag_ids"]])
    return src, flg


def urls_for(ids: list[str], source_map: dict[str, str]) -> str:
    missing = [i for i in ids if i not in source_map]
    if missing:
        raise KeyError(f"unknown source ids: {missing}")
    return "|".join(source_map[i] for i in ids)


def cost_outputs(source_map: dict[str, str] | None = None,
                 method_sources: dict[str, list[str]] | None = None,
                 method_flags: dict[str, list[str]] | None = None) -> dict[str, str]:
    source_map = source_map or load_source_map()
    if method_sources is None or method_flags is None:
        method_sources, method_flags = load_method_meta()
    rows: list[dict[str, str]] = []
    by_key: dict[tuple[str, int], dict[str, str]] = {}

    for method_id, (model, status, default_src, default_flag) in METHOD_SPECS.items():
        method_src = method_sources.get(method_id) or dedupe([default_src])
        method_flg = method_flags.get(method_id) or dedupe([default_flag])
        source_ids = dedupe([*method_src, BASE_SOURCES[model]])
        flag_ids = dedupe([*method_flg, GLOBAL_FLAGS])
        source_urls = urls_for(source_ids, source_map)
        flag_str = "|".join(flag_ids)
        source_str = "|".join(source_ids)
        for amount in AMOUNTS:
            a = F(amount)
            r = {k: "" for k in COST_FIELDS}
            r.update({
                "method_id": method_id,
                "amount_usd": str(amount),
                "status": status,
                "model": model,
                "source_ids": source_str,
                "source_urls": source_urls,
                "flag_ids": flag_str,
                "limitations": LIMITS[model],
            })
            if model in {"fx_wire", "wire_only", "quota", "cash"}:
                r["cny_needed_at_ask"] = q(a * ASK)
            if model == "fx_wire":
                s, w = spread_usd(a), wire_usd(a)
                total = s + w
                r.update({
                    "fx_spread_usd": q(s),
                    "bank_wire_and_cable_usd": q(w),
                    "known_bank_cost_usd": q(total),
                    "known_bank_cost_pct": q(pct(total, a), 4),
                    "net_after_known_bank_cost_usd": q(a - total),
                    "wire_count": "1", "calendar_years": "1",
                })
            elif model == "wire_only":
                w = wire_usd(a)
                r.update({
                    "bank_wire_and_cable_usd": q(w),
                    "known_bank_cost_usd": q(w),
                    "known_bank_cost_pct": q(pct(w, a), 4),
                    "net_after_known_bank_cost_usd": q(a - w),
                    "wire_count": "1", "calendar_years": "1",
                })
            elif model == "quota":
                full, rem = divmod(amount, QUOTA)
                n = full + (1 if rem else 0)
                fee = F(full) * wire_usd(F(QUOTA)) + (wire_usd(F(rem)) if rem else F(0))
                s = spread_usd(a)
                total = s + fee
                r.update({
                    "fx_spread_usd": q(s),
                    "bank_wire_and_cable_usd": q(fee),
                    "known_bank_cost_usd": q(total),
                    "known_bank_cost_pct": q(pct(total, a), 4),
                    "net_after_known_bank_cost_usd": q(a - total),
                    "wire_count": str(n), "calendar_years": str(n),
                })
            elif model == "cash":
                r["fx_spread_usd"] = q(spread_usd(a))
            # atm and blank leave every numeric cost cell blank on purpose.
            rows.append(r)
            by_key[(method_id, amount)] = r

    ladder: list[dict[str, str]] = []
    for amount in AMOUNTS:
        a = F(amount)
        b01 = by_key[("B01", amount)]
        b03 = by_key[("B03", amount)]
        source_ids = dedupe([b01["source_ids"], b03["source_ids"]])
        flag_ids = dedupe([b01["flag_ids"], b03["flag_ids"]])
        ladder.append({
            "amount_usd": str(amount),
            "cny_needed_at_ask": q(a * ASK),
            "best_cny_to_usd_method_id": "B01",
            "best_cny_to_usd_known_cost_usd": b01["known_bank_cost_usd"],
            "best_cny_to_usd_pct": b01["known_bank_cost_pct"],
            "wire_only_known_cost_usd": b03["known_bank_cost_usd"],
            "source_ids": "|".join(source_ids),
            "source_urls": urls_for(source_ids, source_map),
            "flag_ids": "|".join(flag_ids),
            "limitations": "Lowest published single-wire CNY-to-USD bank benchmark (B01); B03 is cheaper only if the balance is already foreign currency. All-in totals are blank.",
        })

    def text(fields: list[str], data: list[dict[str, str]]) -> str:
        buf = io.StringIO(newline="")
        writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(data)
        return buf.getvalue()

    return {
        "data/b9b3_method_costs.csv": text(COST_FIELDS, rows),
        "data/b9b3_ladder.csv": text(LADDER_FIELDS, ladder),
    }


def main() -> int:
    outputs = cost_outputs()
    for rel, text in outputs.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"B9B3 engine: {len(AMOUNTS)} amounts × {len(METHOD_SPECS)} methods = "
          f"{len(AMOUNTS) * len(METHOD_SPECS)} cost rows; {len(AMOUNTS)} ladder rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
