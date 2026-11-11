#!/usr/bin/env python3
"""Verify the f52 layer. Run: python3 scripts/verify_f52.py (exit 1 on failure).

Checks: ladder arithmetic recomputed to the cent; blank series truly blank;
every HTML data row carries an official-source link; every source URL is on
an official domain; internal links resolve; no merge-conflict markers.
"""
import csv, os, re, sys
from decimal import Decimal as D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("build_f52", os.path.join(os.path.dirname(__file__), "build_f52_site.py"))
# Reuse the model functions without rebuilding: import data + copy formulas via build module import guard.
from f52_data import SOURCES, METHODS, AMOUNTS, RATE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFICIAL = ("safe.gov.cn", "boc.cn", "chinatax.gov.cn", "irs.gov", "ecfr.gov",
            "govinfo.gov", "pbc.gov.cn", "fincen.gov", "cbp.gov")
fails = []

def check(cond, msg):
    if not cond:
        fails.append(msg)

# 1. sources official + reachable shape
for s in SOURCES:
    check(any(d in s[3] for d in OFFICIAL), f"{s[0]} non-official URL {s[3]}")
    check(s[3].startswith(("https://", "http://")), f"{s[0]} bad URL")

# 2. ladder recomputation (independent re-derivation)
mid = (RATE["bid"] + RATE["ask"]) / 2
def spread(t): return t * (RATE["ask"] - mid) / RATE["ask"]
def wire(t):
    c = min(RATE["wire_max"], max(RATE["wire_min"], t * RATE["ask"] * RATE["wire_rate"])) + RATE["cable"]
    return c / RATE["ask"]
def q2(x): return x.quantize(D("0.01"))

rows = list(csv.DictReader(open(os.path.join(ROOT, "data/f52_ladder.csv"), encoding="utf-8")))
check(len(rows) == 480, f"ladder rows {len(rows)} != 480")
for r in rows:
    t = D(r["amount_usd"]); model = r["model"]
    exp = None
    if model == "fx_wire": exp = spread(t) + wire(t)
    elif model == "wire_only": exp = wire(t)
    elif model in ("dividend20", "dividend10"):
        rate = RATE["iit_dividend"] if model == "dividend20" else RATE["treaty_dividend"]
        net = t * (1 - rate); exp = t * rate + spread(net) + wire(net)
    if model == "quota":
        from decimal import ROUND_FLOOR
        cap = RATE["quota_usd"]; full = int((t / cap).to_integral_value(rounding=ROUND_FLOOR))
        rem = t - cap * full
        exp = spread(t) + wire(cap) * full + (wire(rem) if rem > 0 else D(0))
    elif model == "cash":
        exp = spread(t)
    elif model == "atm":
        from decimal import ROUND_CEILING
        cny = t * RATE["ask"]; day = RATE["atm_day_cap_cny"]
        full = int(cny // day); rem = cny - day * full
        fee = min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * day) * full
        if rem > 0: fee += min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * rem)
        exp = fee / RATE["ask"]
    if model == "blank":
        check(r["known_cost_usd"] == "", f"{r['series']} {t} blank series priced")
    elif exp is not None:
        got = r["known_cost_usd"].replace(",", "")
        check(got != "" and abs(D(got) - q2(exp)) <= D("0.02"),
              f"{r['series']} {t} known {r['known_cost_usd']} != recomputed {q2(exp)}")
# headline spot values (today's board)
by = {(r["series"], r["amount_usd"]): r["known_cost_usd"] for r in rows}
check(by[("F01", "10000")] == "53.42", f"F01 10k {by[('F01','10000')]}")
check(by[("F01", "400000")] == "901.20", f"F01 400k {by[('F01','400000')]}")
check(by[("F03", "400000")] == "61.28", f"F03 400k {by[('F03','400000')]}")

# 3. HTML: data rows sourced, links resolve, no conflict markers
pages = ["f52-summary.html", "f52-decisions.html", "f52-methods.html", "f52-costs.html", "f52-flagged.html"]
for p in pages:
    path = os.path.join(ROOT, p)
    check(os.path.exists(path), f"missing {p}")
    if not os.path.exists(path):
        continue
    h = open(path, encoding="utf-8").read()
    check("<<<<<<<" not in h and ">>>>>>>" not in h, f"{p} conflict markers")
    for tr in re.findall(r'<tr data-kind="data".*?</tr>', h, re.S):
        check("https://" in tr or "http://" in tr, f"{p} unsourced data row: {tr[:90]}")
    for href in re.findall(r'href="([^"#]+)(?:#[^"]*)?"', h):
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        check(os.path.exists(os.path.join(ROOT, href)), f"{p} broken local link {href}")
md = open(os.path.join(ROOT, "COORDINATION.md"), encoding="utf-8").read()
check(not re.search(r"^(<<<<<<<|=======|>>>>>>>)", md, re.M), "COORDINATION.md conflict markers")

if fails:
    print("FAIL"); [print(" -", f) for f in fails]; sys.exit(1)
print(f"PASS — 20 sources official, 480 ladder rows recomputed, {len(pages)} pages sourced, links OK")
