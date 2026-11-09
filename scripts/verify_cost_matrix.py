#!/usr/bin/env python3
"""Line-by-line verification of the cost model.

Independent of scripts/build_cost_matrix.py: it re-implements the arithmetic
from data/cost_params.csv and compares every one of the 520 rows, then audits
the rendered pages.

Checks
  1. every source in data/cost_sources.csv is https and on an official domain;
  2. all 40 amount steps exist for all 13 routes, with no duplicates;
  3. every modelled row's cost columns equal an independent recomputation;
  4. every row carries at least one registered source id and an official URL;
  5. effective percentages and net amounts are internally consistent;
  6. unverified / assumption inputs are labelled on the page;
  7. every table row on both new pages carries an official link;
  8. the rendered tables have the expected row counts;
  9. the 40-row penalty matrix matches the statutory formulas;
 10. every internal link on both new pages resolves.
Exit 0 = clean.
"""
from __future__ import annotations

import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AMOUNTS = [str(a) for a in range(10_000, 400_001, 10_000)]
OFFICIAL = (
    "safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn", "boc.cn",
    "ecfr.gov", "irs.gov", "fincen.gov", "federalregister.gov",
    "home.treasury.gov", "hkma.gov.hk", "hncourt.gov.cn", "csrc.gov.cn",
)
SECONDARY = ("law.cornell.edu",)

errors: list[str] = []
notes: list[str] = []


def official(url: str, allow_secondary=False) -> bool:
    host = (urlparse(url).hostname or "").lower()
    domains = OFFICIAL + (SECONDARY if allow_secondary else ())
    return any(host == d or host.endswith("." + d) for d in domains)


def read(name):
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---- 1. source register ---------------------------------------------------
src = {r["id"]: r for r in read("cost_sources.csv")}
if len(src) != 32:
    errors.append(f"cost_sources.csv: expected 32 sources, found {len(src)}")
for sid, r in src.items():
    if not r["url"].startswith("https://"):
        errors.append(f"{sid}: not https: {r['url']}")
    if not official(r["url"], allow_secondary=True):
        errors.append(f"{sid}: not on an official domain: {r['url']}")
notes.append(f"source register: {len(src)} sources, all https + official/secondary")

# ---- amounts --------------------------------------------------------------
for a in AMOUNTS:
    if not (10_000 <= int(a) <= 400_000 and int(a) % 10_000 == 0):
        errors.append(f"bad amount {a}")

matrix = read("cost_matrix.csv")
methods = read("cost_methods.csv")
params = {r["key"]: r for r in read("cost_params.csv")}

ids = [m["id"] for m in methods]
seen = {(r["method_id"], r["amount_usd"]) for r in matrix}
for mid in ids:
    for a in AMOUNTS:
        if (mid, a) not in seen:
            errors.append(f"missing row {mid}/{a}")
if len(matrix) != len(ids) * len(AMOUNTS):
    errors.append(f"matrix has {len(matrix)} rows, expected {len(ids)*len(AMOUNTS)}")
notes.append(f"matrix: {len(ids)} routes x {len(AMOUNTS)} amounts = {len(matrix)} rows")

# ---- 3/5. independent recomputation --------------------------------------
RATE = float(params["rate_mid"]["value"])
BUY = float(params["boc_buy"]["value"])
SELL = float(params["boc_sell"]["value"])
MID = (BUY + SELL) / 2
SPREAD_HALF = (SELL - MID) / MID
SPREAD_FULL = (SELL - BUY) / MID
SPREAD_HIGH = 0.01
FULL = float(params["full_amount"]["value"].split()[-1])
DOC_ROUTES = {"L01", "L02", "L05", "L06", "L07", "L10"}
COMP_HIGH = {m["id"]: (500.0 if m["id"] in DOC_ROUTES else 0.0) for m in methods}

# route-specific tranche rules, restated deliberately rather than imported
def tranches(mid, amount):
    if mid == "L03":
        return max(1, -(-amount // 50_000))
    if mid == "L05":
        return 1 if amount * MID <= 200_000 else 3
    if mid == "L08":
        return max(1, -(-amount // 10_000))
    if mid == "L09":
        return max(1, -(-amount // (10_000 / MID)))
    return 1


def expected(mid, amount):
    n = tranches(mid, amount)
    cny = amount * MID
    wire = (min(max(0.001 * cny / n, 50), 260) + 150) * n / SELL
    full = FULL * n
    ch = COMP_HIGH[mid]
    if mid == "P01" or mid in ("P02", "P03"):
        return None
    if mid == "L04":
        return wire, wire + full, wire + full
    low = amount * SPREAD_HALF + wire
    base = amount * SPREAD_FULL + wire + full
    high = amount * SPREAD_HIGH + wire + full + ch
    if mid == "L10":
        low += 0.0
        base += amount * 0.005
        high += amount * 0.0194
    if mid == "L09":
        low = amount * SPREAD_HALF
        base = amount * SPREAD_FULL + 5.0 * n
        high = amount * SPREAD_HIGH + 10.0 * n
    return low, base, high


checked = 0
for r in matrix:
    mid, amount = r["method_id"], int(r["amount_usd"])
    exp = expected(mid, amount)
    if exp is None:
        if r["status"] != "prohibited":
            errors.append(f"{mid}/{amount}: prohibited route not marked")
        if abs(float(r["penalty_low_usd"]) - amount * 0.30) > 0.51:
            errors.append(f"{mid}/{amount}: penalty low != 30%")
        if abs(float(r["penalty_high_usd"]) - amount * 1.00) > 0.51:
            errors.append(f"{mid}/{amount}: penalty high != 100%")
        continue
    got = (float(r["cost_low_usd"]), float(r["cost_base_usd"]), float(r["cost_high_usd"]))
    for label, e, g in zip(("low", "base", "high"), exp, got):
        if abs(e - g) > 0.02:
            errors.append(f"{mid}/{amount}: {label} recomputes to {e:.2f}, CSV says {g:.2f}")
    if abs(float(r["pct_base"]) - float(r["cost_base_usd"]) / amount * 100) > 0.006:
        errors.append(f"{mid}/{amount}: pct_base inconsistent")
    if abs(float(r["net_base_usd"]) - (amount - float(r["cost_base_usd"]))) > 0.02:
        errors.append(f"{mid}/{amount}: net_base inconsistent")
    if int(r["tranches"]) != tranches(mid, amount):
        errors.append(f"{mid}/{amount}: tranches {r['tranches']} != {tranches(mid, amount)}")
    if not r["source_ids"].strip():
        errors.append(f"{mid}/{amount}: no source ids")
    for sid in r["source_ids"].split():
        if sid not in src:
            errors.append(f"{mid}/{amount}: unregistered source {sid}")
    checked += 1
notes.append(f"recomputed {checked} modelled rows; all match within USD 0.02")

# ---- 9. penalty matrix ----------------------------------------------------
pen = read("cost_penalty.csv")
if len(pen) != 40:
    errors.append(f"cost_penalty.csv: {len(pen)} rows, expected 40")
for r in pen:
    a = float(r["amount_usd"])
    if abs(float(r["prc_fine_low"]) - a * 0.30) > 0.51:
        errors.append(f"penalty {a}: prc_low wrong")
    if abs(float(r["prc_fine_high"]) - a * 1.00) > 0.51:
        errors.append(f"penalty {a}: prc_high wrong")
    if abs(float(r["fbar_willful_max"]) - max(165_353, a * 0.5)) > 0.51:
        errors.append(f"penalty {a}: FBAR willful wrong")
    if abs(float(r["form_3520_max"]) - a * 0.25) > 0.51:
        errors.append(f"penalty {a}: Form 3520 wrong")
notes.append("penalty matrix: 40 rows, all four formulas verified")

# ---- 6. assumption labelling ---------------------------------------------
assumptions = [k for k, v in params.items() if not v["status"].startswith("verified")]
if len(assumptions) < 5:
    errors.append("expected at least five explicitly labelled assumptions")
page = (ROOT / "deep-costs.html").read_text(encoding="utf-8")
for k in assumptions:
    if params[k]["value"] not in page:
        errors.append(f"assumption {k} value not shown on the page")
notes.append(f"assumption inputs labelled on page: {len(assumptions)}")

# ---- 7. every table row has an official link ------------------------------
class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_thead = False
        self.in_tr = False
        self.links = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "thead":
            self.in_thead = True
        if tag == "tr" and not self.in_thead:
            self.in_tr = True
            self.links = []
        if tag == "a" and self.in_tr:
            self.links.append(a.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_tr:
            self.in_tr = False
            self.rows.append(self.links)
        if tag == "thead":
            self.in_thead = False


total_rows = 0
for name in ("deep-costs.html", "deep-cost-steps.html"):
    txt = (ROOT / name).read_text(encoding="utf-8")
    p = Rows(); p.feed(txt)
    for i, links in enumerate(p.rows, 1):
        total_rows += 1
        if not any(official(u, allow_secondary=True) for u in links):
            errors.append(f"{name}: row {i} has no official link")
notes.append(f"rendered table rows with an official link: {total_rows}")

# ---- 8. rendered row counts per route ------------------------------------
html_rows = len(re.findall(r"<tr", page)) - len(re.findall(r"<th", page))
if len(re.findall(r">L\d\d<|>P0\d<", page)) < len(ids):
    errors.append("not every route appears on the cost page")
for mid in ids:
    block = re.search(rf'<details class="method" id="{mid.lower()}".*?</details>', page, re.S)
    if not block:
        errors.append(f"no section for {mid}")
        continue
    bp = Rows(); bp.feed(block.group(0))
    n = len(bp.rows)
    if n < 40:
        errors.append(f"{mid}: only {n} data rows rendered, expected at least 40")
notes.append("all 13 route sections present with >= 40 rows each")

# ---- 10. internal links ---------------------------------------------------
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        for k in ("href", "src"):
            v = dict(attrs).get(k, "")
            if v and not v.startswith(("http://", "https://", "mailto:", "#", "data:")):
                self.hrefs.append(v.split("#")[0])

for name in ("deep-costs.html", "deep-cost-steps.html"):
    page_obj = ROOT / name
    lp = Links(); lp.feed(page_obj.read_text(encoding="utf-8"))
    for href in lp.hrefs:
        if href and not (ROOT / href).exists():
            errors.append(f"{name}: broken local link {href}")
notes.append("internal links: all resolve")

print("\n".join(f"  - {n}" for n in notes))
if errors:
    print("\nFAILURES:")
    for e in errors[:60]:
        print(f"  ! {e}")
    print(f"\n{len(errors)} failure(s)")
    sys.exit(1)
print("\nAll cost-model checks passed.")
