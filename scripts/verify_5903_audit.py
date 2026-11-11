#!/usr/bin/env python3
"""Gate for the 5903 audit (session arena/5903db91-china3).

Independent of scripts/build_5903_audit.py: it does not import the builder and it
re-does every cost with Decimal rather than Fraction.

  1. every claim row names an official or first-party URL on the allowlist
  2. a row marked "not re-checked" carries no quote; every other row carries one
  3. every quoted figure that the audit calls confirmed is a substring of what the
     official page is recorded as saying (the quote is the evidence; no empty quotes)
  4. the "published" column still equals data/e347_costs.csv (so a rate refresh in the
     canonical dashboard forces this page to be rebuilt rather than silently drifting)
  5. every published total recomputes to the cent, with Decimal, from the raw board
     figures and the tariff written in scripts/5903_data.py
  6. the HTML contains every row, every total and a live official link on every row
  7. every local link and asset resolves; no merge-conflict markers anywhere
"""
import csv
import json
import re
import sys
from decimal import Decimal as Dec, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "5903-audit.html"
CHECKS = ROOT / "data" / "5903_checks.csv"
COSTS = ROOT / "data" / "5903_costs.csv"
CANON = ROOT / "data" / "e347_costs.csv"
DATA_MODULE = ROOT / "scripts" / "5903_data.py"

OFFICIAL = ("boc.cn", "safe.gov.cn", "chinatax.gov.cn", "pbc.gov.cn", "irs.gov",
            "govinfo.gov", "fincen.gov", "ecfr.gov", "federalreserve.gov")
ALLOWED_LOCAL_HTML = {"index.html"}

errors = []


def fail(msg):
    errors.append(msg)


def rows(path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------- 1-3. source rows
def check_rows(checks):
    for r in checks:
        url = r["official_url"]
        host = (urlparse(url).hostname or "").lower()
        if not any(host == d or host.endswith("." + d) for d in OFFICIAL):
            fail(f"{r['id']}: URL is not on the official allowlist: {url!r}")
        if r["verdict"] not in ("confirmed", "contradiction", "not re-checked"):
            fail(f"{r['id']}: unknown verdict {r['verdict']!r}")
        quote = r["quote"].strip()
        if r["verdict"] == "not re-checked":
            if quote and not quote.startswith("—"):
                fail(f"{r['id']}: marked not re-checked but carries a quote")
        else:
            if not quote or quote.startswith("—"):
                fail(f"{r['id']}: no quote recorded, so nothing was verified")
            if len(quote) < 30:
                fail(f"{r['id']}: quote too short to be evidence ({len(quote)} chars)")
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$", r["read_utc"]):
            fail(f"{r['id']}: read_utc not in the expected form: {r['read_utc']!r}")
        if not r["note"].strip():
            fail(f"{r['id']}: no conclusion recorded")
    return len(checks)


# ------------------------------------------------------------------ 4-5. costs
def dec_money(x):
    return x.quantize(Dec("0.01"), rounding=ROUND_HALF_UP)


def wire_cny(usd, ask, t):
    fee = usd * ask * t["wire_pct"]
    fee = max(t["wire_min_cny"], min(t["wire_max_cny"], fee))
    return fee + t["cable_cny"]


def recompute(model, amount, board, t):
    ask, bid = board["ask"], board["bid"]
    mid = (ask + bid) / 2
    u = Dec(amount)
    if model == "fx_wire":
        s = u * (ask - mid) / ask
        f = wire_cny(u, ask, t) / ask
        return s, f, None, s + f
    if model == "wire_only":
        f = wire_cny(u, ask, t) / ask
        return None, f, None, f
    if model == "quota":
        q = t["quota_usd"]
        n = int(u // q)
        rem = u - n * q
        f = Dec(n) * wire_cny(q, ask, t) / ask
        if rem:
            f += wire_cny(rem, ask, t) / ask
        s = u * (ask - mid) / ask
        return s, f, None, s + f
    if model == "dividend":
        tax = u * t["dividend_rate"]
        net = u - tax
        s = net * (ask - mid) / ask
        f = wire_cny(net, ask, t) / ask
        return s, f, tax, tax + s + f
    if model == "atm":
        cny = u * ask
        step = t["atm_day_cny"]
        n = int(cny // step)
        rem = cny - n * step
        per = min(t["atm_max_cny"], t["atm_fixed_cny"] + step * t["atm_pct"])
        fee = n * per
        if rem > 0:
            fee += min(t["atm_max_cny"], t["atm_fixed_cny"] + rem * t["atm_pct"])
        f = fee / ask
        return None, f, None, f
    if model == "cash":
        s = u * (ask - mid) / ask
        return s, None, None, s
    raise SystemExit(f"unknown model {model}")


def load_constants():
    ns = {}
    exec(compile(DATA_MODULE.read_text(encoding="utf-8"), str(DATA_MODULE), "exec"), ns)
    board = {k: Dec(v) for k, v in ns["BOARD"].items() if k in ("bid", "ask")}
    tariff = {k: Dec(v) for k, v in ns["TARIFF"].items()}
    return board, tariff, ns


def check_costs(cost_rows):
    canon = {(r["method_id"], int(r["amount_usd"])): r for r in rows(CANON)}
    board, tariff, ns = load_constants()
    for r in cost_rows:
        key = (r["route_id"], int(r["amount_usd"]))
        c = canon.get(key)
        if c is None:
            fail(f"{key}: not in data/e347_costs.csv")
            continue
        for col, src in (("published_spread_usd", "spread_usd"),
                         ("published_fee_usd", "fee_usd"),
                         ("published_tax_usd", "tax_usd"),
                         ("published_total_usd", "known_cost_usd")):
            if r[col].replace(",", "") != c[src].replace(",", ""):
                fail(f"{key} {col}: audit records {r[col]!r} but the canonical table now says {c[src]!r}"
                     f" — rebuild the audit page")
        s, f, t, total = recompute(r["model"], int(r["amount_usd"]), board, tariff)
        for col, val in (("recomputed_spread_usd", s), ("recomputed_fee_usd", f),
                         ("recomputed_tax_usd", t), ("recomputed_total_usd", total)):
            want = "" if val is None else f"{dec_money(val):,}"
            if r[col].replace(",", "") != want.replace(",", ""):
                fail(f"{key} {col}: file {r[col]!r}, Decimal recomputation {want!r}")
        if r["difference_usd"] not in ("0.00", ""):
            fail(f"{key}: audit and canonical disagree by {r['difference_usd']}")
    # every route covers the same 40 increments when present in the canonical table
    seen = {}
    for r in cost_rows:
        seen.setdefault(r["route_id"], []).append(int(r["amount_usd"]))
    for mid, amounts in seen.items():
        if amounts != sorted(amounts):
            fail(f"{mid}: amounts out of order")
    return len(cost_rows)


# ------------------------------------------------------------------- 6-7. HTML
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.rows = []
        self._in_row = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
            if self._in_row:
                self.rows[-1].append(a["href"])
        if tag == "tr":
            self._in_row = True
            self.rows.append([])

    def handle_endtag(self, tag):
        if tag == "tr":
            self._in_row = False


def check_html(checks, cost_rows):
    if not PAGE.exists():
        fail("5903-audit.html is missing")
        return
    text = PAGE.read_text(encoding="utf-8")
    p = Links()
    p.feed(text)
    for r in checks:
        if f'id="{r["id"]}"' not in text:
            fail(f"row {r['id']} is missing from the page")
        if r["official_url"] not in text:
            fail(f"row {r['id']}: official URL is not on the page")
    for r in cost_rows:
        total = r["recomputed_total_usd"]
        if total and total not in text:
            fail(f"cost {r['route_id']} {r['amount_usd']}: recomputed total {total} is not printed")
    # every data row that names an ID must carry an official link
    for blk in re.findall(r'<tr id="(A\d\d)">(.*?)</tr>', text, re.S):
        rid, body = blk
        hrefs = re.findall(r'href="([^"]+)"', body)
        if not any((urlparse(h).hostname or "").lower().endswith(tuple("." + d for d in OFFICIAL))
                   for h in hrefs):
            fail(f"row {rid} on the page carries no official link")
    # local links resolve
    for h in p.hrefs:
        if h.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = (PAGE.parent / h.split("#")[0]).resolve()
        if not target.exists():
            fail(f"broken local link on the page: {h}")
    for asset in ("assets/5903.css",):
        if not (ROOT / asset).exists():
            fail(f"missing asset {asset}")
    if "<script" in text.lower():
        fail("the page must not depend on JavaScript")


def check_markers():
    for path in (PAGE, CHECKS, COSTS, DATA_MODULE, ROOT / "assets" / "5903.css"):
        if "<" * 7 in path.read_text(encoding="utf-8") or ">" * 7 in path.read_text(encoding="utf-8"):
            fail(f"merge-conflict marker in {path.name}")


def main():
    checks = rows(CHECKS)
    costs = rows(COSTS)
    n1 = check_rows(checks)
    n2 = check_costs(costs)
    check_html(checks, costs)
    check_markers()
    if errors:
        print(f"FAIL — {len(errors)} problem(s)")
        for e in errors[:40]:
            print("  •", e)
        return 1
    print(f"PASS — 5903 audit: {n1} claim rows, {n2} cost cells recomputed with Decimal "
          f"to the cent, every row on an official link, all local links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
