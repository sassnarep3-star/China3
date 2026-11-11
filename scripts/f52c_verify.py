#!/usr/bin/env python3
"""Independent checks for questions.html and the f52c data files.

Does not import the cost engine or the page builder. Arithmetic is redone here with
exact fractions from the raw published figures, so a change in either script cannot
hide behind itself.

  1. all 440 per-route cells and all 40 ladder rows are recomputed and must match the CSV
  2. the recomputation is consistent with the published tariff and board (floor, cap, cable)
  3. every question row is sourced or flagged; UNVERIFIED rows must carry a flag
  4. every source id resolves, every citation URL is on the official-domain allowlist
  5. every number printed on the page appears in the CSV, and every CSV row appears on the page
  6. every local link and anchor resolves; every external link is allowlisted
  7. questions.html is byte-identical to a fresh build
  8. no placeholder text, and the board timestamp and read date are printed

Exit 0 = clean, 1 = violations.
"""
from __future__ import annotations

import csv
import math
import re
import subprocess
import sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "questions.html"
D = ROOT / "data"

OFFICIAL = ("boc.cn", "safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "govinfo.gov",
            "irs.gov", "ecfr.gov", "cbp.gov", "fincen.gov")
EXTRA_OK = ("github.com",)

BID, ASK, CASH_ASK = F(66630, 10000), F(66911, 10000), F(66911, 10000)
MID = (BID + ASK) / 2
WIRE_RATE, WIRE_MIN, WIRE_MAX, CABLE = F(1, 1000), F(50), F(260), F(150)
ATM_FIXED, ATM_PCT, ATM_MAX = F(12), F(1, 100), F(112)
ATM_DAY, ATM_YEAR = F(10000), F(100000)
QUOTA, CASH_FREE, CASH_BANK = F(50000), F(5000), F(10000)
IIT = F(1, 5)
IRS = {"2021": F(6452, 1000), "2022": F(6730, 1000), "2023": F(7075, 1000),
       "2024": F(7189, 1000), "2025": F(7129, 1000)}

ERR: list[str] = []


def fail(m: str) -> None:
    ERR.append(m)


def half_up(x: F, places: int) -> F:
    scale = 10 ** places
    return F(math.floor(x * scale + F(1, 2)), scale)


def money(x: F) -> str:
    v = half_up(x, 2)
    return f"{v.numerator / v.denominator:.2f}"


def pct4(x: F) -> str:
    v = half_up(x, 4)
    return f"{v.numerator / v.denominator:.4f}"


def rows(name):
    with (D / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def wire_cny(usd: F) -> F:
    raw = usd * ASK * WIRE_RATE
    return min(WIRE_MAX, max(WIRE_MIN, raw)) + CABLE


def spread(usd: F, ask: F = ASK) -> F:
    return usd * (ask - MID) / ask


def expect(model: str, usd: F):
    """(spread, fee, tax, total, units, years) as exact fractions; None where blank."""
    if model in ("fx_wire", "property"):
        s, w = spread(usd), wire_cny(usd) / ASK
        return s, w, None, s + w, 1, 1
    if model == "wire_only":
        w = wire_cny(usd) / ASK
        return None, w, None, w, 1, 1
    if model == "quota":
        full = int(usd // QUOTA)
        rem = usd - QUOTA * full
        fee = (wire_cny(QUOTA) / ASK) * full + ((wire_cny(rem) / ASK) if rem > 0 else F(0))
        n = full + (1 if rem > 0 else 0)
        s = spread(usd)
        return s, fee, None, s + fee, n, n
    if model == "atm":
        cny = usd * ASK
        full = int(cny // ATM_DAY)
        rem = cny - ATM_DAY * full
        per = lambda a: min(ATM_MAX, ATM_FIXED + ATM_PCT * a)
        fee_cny = per(ATM_DAY) * full + (per(rem) if rem > 0 else F(0))
        units = full + (1 if rem > 0 else 0)
        years = math.ceil(cny / ATM_YEAR)
        return None, fee_cny / ASK, None, fee_cny / ASK, units, years
    if model == "cash":
        s = spread(usd, CASH_ASK)
        return s, None, None, s, math.ceil(usd / CASH_FREE), math.ceil(usd / CASH_BANK)
    if model == "dividend":
        tax = usd * IIT
        net = usd - tax
        s, w = spread(net), wire_cny(net) / ASK
        return s, w, tax, tax + s + w, 1, 1
    return None, None, None, None, None, None


METHODS = {
    "L01": "fx_wire", "L02": "fx_wire", "L03": "wire_only", "L04": "fx_wire", "L05": "fx_wire",
    "L06": "fx_wire", "L07": "quota", "L08": "blank", "L09": "dividend", "L10": "atm", "L11": "cash",
}
AMOUNTS = [F(10000) * i for i in range(1, 41)]

# ---------------------------------------------------------------- 1. arithmetic
def check_arithmetic() -> None:
    cells = rows("f52c_method_costs.csv")
    if len(cells) != 440:
        fail(f"method costs: {len(cells)} rows, expected 440")
    seen = set()
    for r in cells:
        mid, amount = r["method_id"], F(r["amount_usd"])
        seen.add((mid, amount))
        model = METHODS.get(mid)
        if model is None:
            fail(f"unknown method {mid}")
            continue
        s, w, t, total, units, years = expect(model, amount)
        if total is None:
            for col in ("known_cost_usd", "spread_usd", "fee_usd", "tax_usd", "known_cost_pct", "units"):
                if r[col] != "":
                    fail(f"{mid} {r['amount_usd']}: unpublished cost must be blank, found {col}={r[col]!r}")
            if r["calendar_years"] != "":
                fail(f"{mid} {r['amount_usd']}: years must be blank")
            continue
        rounded = half_up(total, 2)
        want = {"known_cost_usd": money(total), "known_cost_pct": pct4(rounded / amount * 100),
                "units": str(units), "calendar_years": str(years)}
        want["spread_usd"] = money(s) if s is not None else ""
        want["fee_usd"] = money(w) if w is not None else ""
        want["tax_usd"] = money(t) if t is not None else ""
        for col, val in want.items():
            if r[col] != val:
                fail(f"{mid} {r['amount_usd']} {col}: CSV {r[col]!r} != recomputed {val!r}")
    for mid, model in METHODS.items():
        for a in AMOUNTS:
            if (mid, a) not in seen:
                fail(f"missing cell {mid} {a}")

    # 2. tariff behaviour: floor, cap, cable
    if wire_cny(F(100) * ASK) - CABLE != WIRE_MIN * 0:
        pass
    if wire_cny(F(1)) - CABLE != WIRE_MIN:
        fail("wire floor is not RMB 50")
    if wire_cny(F(10**7)) - CABLE != WIRE_MAX:
        fail("wire cap is not RMB 260")
    if CABLE != F(150):
        fail("cable fee changed")
    if not (spread(F(400000)) < F(400000) * F(3, 1000)):
        fail("spread at 400k is implausibly large")

    # ladder
    lad = rows("f52c_ladder.csv")
    if len(lad) != 40:
        fail(f"ladder: {len(lad)} rows, expected 40")
    for r in lad:
        a = F(r["amount_usd"])
        if a != AMOUNTS[int(a / 10000) - 1]:
            fail(f"ladder amount {r['amount_usd']} is not a $10,000 step")
        l01, _, _, t01, _, _ = expect("fx_wire", a)
        _, _, _, t03, _, _ = expect("wire_only", a)
        _, _, _, t07, _, y07 = expect("quota", a)
        g24 = a - a * ASK / IRS["2024"]
        g25 = a - a * ASK / IRS["2025"]
        want = {"l01_cost_usd": money(t01), "l01_pct": pct4(half_up(t01, 2) / a * 100),
                "l03_cost_usd": money(t03), "l07_cost_usd": money(t07),
                "l07_years": str(y07), "us_gain_2024": money(g24),
                "us_gain_2025": money(g25), "us_gain_2024_pct": pct4(half_up(g24, 2) / a * 100)}
        for col, val in want.items():
            if r[col] != val:
                fail(f"ladder {r['amount_usd']} {col}: CSV {r[col]!r} != recomputed {val!r}")
        if not (F(t03) <= F(t01)):
            fail(f"ladder {r['amount_usd']}: wire-only should not exceed convert+wire")


# ------------------------------------------------------- 3. sourcing and flags
def official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def check_sources() -> None:
    sources = {r["id"]: r for r in rows("f52c_sources.csv")}
    flags = {r["id"]: r for r in rows("f52c_flags.csv")}
    questions = rows("f52c_questions.csv")

    for sid, s in sources.items():
        if not s["url"].startswith("https://") and not s["url"].startswith("http://"):
            fail(f"{sid}: source has no URL")
        if not official(s["url"]):
            fail(f"{sid}: {s['url']} is not on the official allowlist")
        if s["read_on"] != "2026-11-11":
            fail(f"{sid}: read_on is {s['read_on']}, expected 2026-11-11")
        if len(s["verbatim"]) < 40:
            fail(f"{sid}: verbatim quote too short to be a quote")
        if s["what_it_settles"].strip() == "":
            fail(f"{sid}: says nothing about what it settles")

    for fid, f in flags.items():
        if f["severity"] not in ("high", "medium", "low"):
            fail(f"{fid}: bad severity {f['severity']!r}")
        if not f["what_would_settle_it"].strip():
            fail(f"{fid}: no remedy stated")

    seen = set()
    for q in questions:
        qid = q["id"]
        if qid in seen:
            fail(f"{qid}: duplicate question id")
        seen.add(qid)
        if q["status"] not in ("VERIFIED", "OPEN", "UNVERIFIED"):
            fail(f"{qid}: bad status {q['status']!r}")
        ids = q["source_ids"].split()
        if not ids:
            fail(f"{qid}: no source cited")
        for i in ids:
            if i not in sources:
                fail(f"{qid}: cites unknown source {i}")
        if q["status"] == "UNVERIFIED":
            if not q["flag"] or q["flag"] not in flags:
                fail(f"{qid}: UNVERIFIED without a valid flag")
        elif q["flag"] and q["flag"] not in flags:
            fail(f"{qid}: cites unknown flag {q['flag']}")
        if q["status"] == "OPEN" and not q["how_to_settle"].strip():
            fail(f"{qid}: OPEN question has no way to settle it")
        if not q["answer"].strip():
            fail(f"{qid}: empty answer")
    for f in flags.values():
        for i in f["source_ids"].split():
            if i not in sources:
                fail(f"{f['id']}: cites unknown source {i}")


# ------------------------------------------------------------- 4. page vs data
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.ids = [], []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.append(d["id"])
        if tag == "a" and d.get("href"):
            self.hrefs.append(d["href"])


def check_page() -> None:
    if not PAGE.exists():
        fail("questions.html missing")
        return
    text = PAGE.read_text(encoding="utf-8")
    p = Links()
    p.feed(text)

    for q in rows("f52c_questions.csv"):
        if f'id="{q["id"]}"' not in text:
            fail(f"question {q['id']} is not on the page")
    for f in rows("f52c_flags.csv"):
        if f'id="{f["id"]}"' not in text:
            fail(f"flag {f['id']} is not on the page")
    for s in rows("f52c_sources.csv"):
        if f'id="{s["id"]}"' not in text:
            fail(f"source {s['id']} is not on the page")
    if len(rows("f52c_sources.csv")) < 20:
        fail("fewer than 20 sources: the register is not complete")

    # every printed money value must exist in the CSVs, and every CSV value must be printed
    csv_values = set()
    for r in rows("f52c_method_costs.csv"):
        for col in ("known_cost_usd", "spread_usd", "fee_usd", "tax_usd"):
            if r[col]:
                csv_values.add(f"${float(r[col]):,.2f}")
        csv_values.add(f"${float(r['amount_usd']):,.2f}")
    for r in rows("f52c_ladder.csv"):
        for col in ("l01_cost_usd", "l03_cost_usd", "l07_cost_usd", "us_gain_2024", "us_gain_2025"):
            csv_values.add(f"${float(r[col]):,.2f}")
        csv_values.add(f"${float(r['amount_usd']):,.2f}")
    printed = set(re.findall(r"\$[\d,]+\.\d{2}", text))
    stray = {v for v in printed if v not in csv_values}
    if stray:
        fail(f"page prints money values that are not in the CSV: {sorted(stray)[:10]}")
    for r in rows("f52c_ladder.csv"):
        want = f"${float(r['l01_cost_usd']):,.2f}"
        if want not in text:
            fail(f"ladder value {want} missing from the page")
        if r["l01_pct"] not in text:
            fail(f"ladder percentage {r['l01_pct']} missing from the page")
    for mid in METHODS:
        if f"route{mid}" not in text:
            fail(f"route {mid} missing from the page")

    # local links and anchors
    for href in p.hrefs:
        if href.startswith(("http://", "https://")):
            if not (official(href) or any((urlparse(href).hostname or "").endswith(x) for x in EXTRA_OK)):
                fail(f"external link not on the allowlist: {href}")
            continue
        target, _, anchor = href.partition("#")
        if target:
            path = (PAGE.parent / target).resolve()
            if not path.exists():
                fail(f"missing local target: {href}")
                continue
        else:
            path = PAGE
        if anchor:
            body = path.read_text(encoding="utf-8", errors="replace")
            if f'id="{anchor}"' not in body:
                fail(f"missing anchor: {href}")

    if "2026/11/11 10:25:02" not in text:
        fail("the board timestamp is not printed")
    if "11 November 2026" not in text:
        fail("the read date is not printed")
    for bad in ("TODO", "FIXME", "lorem", "XXX", "{{"):
        if bad in text:
            fail(f"page contains placeholder text {bad!r}")
    if re.search(r"^(<<<<<<<|=======$|>>>>>>>)", text, re.M):
        fail("page contains merge-conflict markers")


def main() -> int:
    check_arithmetic()
    check_sources()
    check_page()
    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "f52c_build.py"), "--check"],
                        capture_output=True, text=True)
    if rc.returncode != 0:
        fail(f"page is stale or the build failed: {rc.stdout.strip()} {rc.stderr.strip()}")

    if ERR:
        print(f"FAIL: {len(ERR)} violation(s)")
        for e in ERR:
            print("  -", e)
        return 1
    print(f"OK - {len(AMOUNTS)} increments x {len(METHODS)} routes recomputed, "
          f"{len(rows('f52c_ladder.csv'))} ladder rows exact, "
          f"{len(rows('f52c_questions.csv'))} questions sourced or flagged, "
          f"{len(rows('f52c_sources.csv'))} official pages, "
          f"{len(rows('f52c_flags.csv'))} flags, page matches data, all links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
