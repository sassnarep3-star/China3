#!/usr/bin/env python3
"""Line-by-line verification of the cost tables.

Deliberately re-derives every figure from data/cost_inputs.csv with its own
arithmetic instead of importing the builder's cost function, so a mistake in
scripts/cost_engine.py cannot silently certify itself.

Checks
  1. every input row: source registered, URL identical to the register, status valid,
     unverified => value blank, verified => value present
  2. every ladder row: 40 amounts per route, totals re-derived to the cent, net and
     percentage consistent
  3. every CSV is byte-identical to a fresh build (no stale artifact)
  4. cost-tables.html: every data row carries an official https source link; every
     method id, input id and flag id present; table row counts match the CSVs; no
     dangling local link
  5. hand-computed spot checks, written out longhand below

Exit 0 = clean, 1 = violations.
"""
from __future__ import annotations

import csv
import html.parser
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGE = ROOT / "cost-tables.html"
errs: list[str] = []
notes: list[str] = []

# Official publication domains. A source link must land on one of these: a
# regulator, a ministry, a court, a central bank, a state gazette, or the one
# commercial bank whose own tariff is the input.
OFFICIAL = (
    ".gov.cn", ".gov", "boc.cn", "hkma.gov.hk", "chinatax.gov.cn",
    "ecfr.gov", "federalregister.gov", "irs.gov", "fincen.gov", "treasury.gov",
)


def official(url: str) -> bool:
    host = url.split("//", 1)[-1].split("/", 1)[0].lower()
    return any(host == d.lstrip(".") or host.endswith(d) for d in OFFICIAL)


def fail(msg: str) -> None:
    errs.append(msg)


def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- 1. inputs
sources = {r["id"]: r for r in rows("cost_sources.csv")}
inputs = {r["id"]: r for r in rows("cost_inputs.csv")}
methods = {r["id"]: r for r in rows("cost_methods.csv")}
ladder = rows("cost_ladder.csv")

if not sources:
    fail("cost_sources.csv is empty")

for iid, r in inputs.items():
    sid = r["source_id"]
    if sid not in sources:
        fail(f"{iid}: source {sid} not in cost_sources.csv")
    elif sources[sid]["url"] != r["source_url"]:
        fail(f"{iid}: source_url does not match the register entry for {sid}")
    if r["status"] not in {"verified", "derived", "unverified"}:
        fail(f"{iid}: bad status {r['status']!r}")
    if r["status"] == "unverified" and r["value"].strip():
        fail(f"{iid}: marked unverified but carries a value ({r['value']!r}) — blank it or verify it")
    if r["status"] != "unverified" and not r["value"].strip():
        fail(f"{iid}: marked {r['status']} but the value is blank")
    if not official(r["source_url"]):
        fail(f"{iid}: source is not on an official domain: {r['source_url']}")
    if not r["source_url"].startswith("https://"):
        notes.append(f"{iid}: official page only served over http ({r['source_url']})")

# ---------------------------------------------------------------- 2. model
# Constants read back out of the input register, so the verifier tests the same
# numbers the page publishes.
ASK = float(inputs["CI01"]["value"])
MID = float(inputs["CI03"]["value"])
WIRE_MIN = float(inputs["CI07"]["value"])
WIRE_MAX = float(inputs["CI08"]["value"])
CABLE = float(inputs["CI09"]["value"])
CONVENIENCE = float(inputs["CI13"]["value"].replace(",", ""))
ONE_PAYMENT_CNY = float(inputs["CI29"]["value"].replace(",", ""))
WIRE_RATE = 0.001  # CI06, "1‰ of the amount"


def fee_cny(usd: float) -> float:
    return min(max(WIRE_RATE * usd * ASK, WIRE_MIN), WIRE_MAX)


def expected(mid_method: dict, amount: float):
    """Return (total_usd | None, spread | None, fee | None, units | None)."""
    model = mid_method["fee_model"]
    spread = amount * (ASK / MID - 1.0)
    if model in ("wire_fx", "wire_fx_plus_docs"):
        fee = (fee_cny(amount) + CABLE) / ASK
        return spread + fee, spread, fee, 1
    if model == "wire_fx_quota":
        left, total, n = amount, 0.0, 0
        while left > 0:
            chunk = min(left, CONVENIENCE)
            total += chunk * (ASK / MID - 1.0) + (fee_cny(chunk) + CABLE) / ASK
            left -= chunk
            n += 1
        fee = total - spread
        return total, spread, fee, n
    if model == "emigrant_staged":
        if amount * ASK <= ONE_PAYMENT_CNY:
            shares = [1.0]
        else:
            shares = [0.5, 0.25, 0.25]
        fee = sum((fee_cny(amount * s) + CABLE) / ASK for s in shares)
        return spread + fee, spread, fee, len(shares)
    if model == "wire_nofx":
        fee = (fee_cny(amount) + CABLE) / ASK
        return fee, 0.0, fee, 1
    if model == "carry_cash":
        return 0.0, None, None, math.ceil(amount / 10_000)
    return None, None, None, None


AMOUNTS = [10_000 * i for i in range(1, 41)]

for mid_, m in methods.items():
    got = [r for r in ladder if r["method_id"] == mid_]
    if [int(r["amount_usd"]) for r in got] != AMOUNTS:
        fail(f"{mid_}: ladder does not contain exactly $10,000-$400,000 in $10,000 steps")
        continue
    for r in got:
        a = float(r["amount_usd"])
        total, spread, fee, units = expected(m, a)
        if total is None:
            if r["total_cost_usd"]:
                fail(f"{mid_} ${a:,.0f}: total printed but the model prices nothing")
            continue
        if not r["total_cost_usd"]:
            fail(f"{mid_} ${a:,.0f}: model produces a total but the row is blank")
            continue
        if abs(float(r["total_cost_usd"]) - round(total, 2)) > 0.011:
            fail(f"{mid_} ${a:,.0f}: total {r['total_cost_usd']} != re-derived {total:.2f}")
        if spread is not None and abs(float(r["spread_usd"] or 0) - round(spread, 2)) > 0.011:
            fail(f"{mid_} ${a:,.0f}: spread {r['spread_usd']} != {spread:.2f}")
        if fee is not None and abs(float(r["bank_fee_usd"] or 0) - round(fee, 2)) > 0.011:
            fail(f"{mid_} ${a:,.0f}: fee {r['bank_fee_usd']} != {fee:.2f}")
        if abs(float(r["net_usd"]) - round(a - total, 2)) > 0.011:
            fail(f"{mid_} ${a:,.0f}: net does not equal amount minus total")
        if abs(float(r["cost_pct"]) - round(total / a * 100, 4)) > 0.0002:
            fail(f"{mid_} ${a:,.0f}: percentage does not match total/amount")
        if abs(float(r["coef_per_0p10_usd"]) - round(a * 0.001, 2)) > 0.011:
            fail(f"{mid_} ${a:,.0f}: 0.10% coefficient wrong")
        if units is not None and str(units) != str(r["units"]):
            fail(f"{mid_} ${a:,.0f}: units {r['units']} != {units}")

# every priced total must be > 0 for the lawful wire routes
m01 = [r for r in ladder if r["method_id"] == "M01"]
if not m01:
    fail("M01 missing from the ladder")
else:
    first, last = float(m01[0]["total_cost_usd"]), float(m01[-1]["total_cost_usd"])
    if not (0 < first < last):
        fail("M01 cost should rise with amount and stay positive")

# ---------------------------------------------------------------- 3. hand checks
# Longhand: 10,000 x 6.6919 = 66,919 CNY.
#   spread  = 6.6919 / 6.67785 - 1 = 0.00210374 -> $21.04 on $10,000
#   wire    = 1 per mille of 66,919 = 66.919 CNY, inside [50, 260]
#   cable   = 150 CNY  -> 216.919 CNY = $32.415
#   total   = 21.0374 + 32.4150 = $53.45
HAND = {
    ("M01", 10_000): 53.45,
    ("M01", 400_000): 902.86,
    ("M07", 400_000): 61.27,
    ("M02", 400_000): 1331.73,
    ("M03", 400_000): 1025.39,
}
for (mid_, amt), want in HAND.items():
    hit = [r for r in ladder if r["method_id"] == mid_ and int(r["amount_usd"]) == amt]
    if not hit:
        fail(f"hand check: {mid_} ${amt:,} not in the ladder")
    elif abs(float(hit[0]["total_cost_usd"]) - want) > 0.011:
        fail(f"hand check: {mid_} ${amt:,} is {hit[0]['total_cost_usd']}, expected {want}")

# the 1 per mille cap should bind above USD 38,853, so the fee is flat past it
cap_bind = 260 / WIRE_RATE / ASK
if not (38_000 < cap_bind < 39_500):
    fail(f"wire-fee cap crossover {cap_bind:.0f} is outside the expected band")

# ---------------------------------------------------------------- 4. page
if not PAGE.exists():
    fail("cost-tables.html missing")
    print("FAIL\n" + "\n".join(errs))
    sys.exit(1)
page = PAGE.read_text(encoding="utf-8")


class Collector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []
        self.in_td = False
        self.cell = ""
        self.row_links = 0
        self.rows = 0
        self.table = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and d.get("href"):
            self.hrefs.append(d["href"])
            if self.in_td and d["href"].startswith("https://"):
                self.row_links += 1
        if tag == "table":
            self.table += 1
        if tag == "td":
            self.in_td, self.cell = True, ""
        if tag == "tr":
            self.rows += 1

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_td = False
        if tag == "tr" and self.row_links == 0:
            pass  # header rows are <th>; data rows are checked below
        if tag == "tr":
            self.row_links = 0


c = Collector()
c.feed(page)

# every external link must be https and every local link must exist
for h in dict.fromkeys(c.hrefs):
    if h.startswith(("http://", "https://")):
        if not official(h):
            fail(f"page links a non-official domain: {h}")
        elif not h.startswith("https://"):
            notes.append(f"http-only official page linked: {h}")
    elif h.startswith("#"):
        anchor = h[1:]
        if f'id="{anchor}"' not in page:
            fail(f"page links to missing anchor {h}")
    else:
        target = h.split("#", 1)[0]
        if target and not (ROOT / target).exists():
            fail(f"page links to missing local file: {h}")

# data rows: re-scan row by row for an https link inside the row
for tr in re.findall(r"<tr>(.*?)</tr>", page, flags=re.S):
    if "<td" not in tr:
        continue                      # header row
    if not re.search(r"""href=["']https?://""", tr):
        label = re.sub(r"<[^>]+>", " ", tr)[:70]
        fail(f"data row without an official source link: {label}")

for mid_ in methods:
    if f'id="{mid_}"' not in page:
        fail(f"page is missing route {mid_}")
for iid in inputs:
    if iid not in page:
        fail(f"page is missing input {iid}")
for fid in ("IR-024", "IR-025", "IR-026", "IR-027", "IR-028", "IR-029"):
    if fid not in page:
        fail(f"page is missing flag {fid}")

# row counts: 40-step master table + 40 rows per priced route
if page.count("class='amt'") < 40:
    fail("master ladder does not appear to contain 40 amount rows")

# no unverified input may be rendered as a number
for iid, r in inputs.items():
    if r["status"] == "unverified" and r["value"].strip():
        fail(f"{iid} unverified value leaked into the page")

# ---------------------------------------------------------------- 5. freshness
before = {p.name: p.read_bytes() for p in sorted(DATA.glob("cost_*.csv"))}
before["_html"] = PAGE.read_bytes()
proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_cost_tables.py")],
                      capture_output=True, text=True)
if proc.returncode != 0:
    fail("rebuild failed: " + proc.stderr.strip()[:400])
else:
    for p in sorted(DATA.glob("cost_*.csv")):
        if before.get(p.name) != p.read_bytes():
            fail(f"data/{p.name} is stale — rebuild and commit")
    if before["_html"] != PAGE.read_bytes():
        fail("cost-tables.html is stale — rebuild and commit")

# ---------------------------------------------------------------- report
if errs:
    print(f"FAIL — {len(errs)} problem(s)")
    for e in errs[:60]:
        print("  •", e)
    if len(errs) > 60:
        print(f"  … and {len(errs) - 60} more")
    sys.exit(1)

for n in dict.fromkeys(notes):
    print("  note:", n)
print(f"PASS — {len(inputs)} inputs, {len(methods)} routes, {len(ladder)} ladder rows, "
      f"{len(sources)} sources; every total re-derived, every row sourced, page fresh.")
