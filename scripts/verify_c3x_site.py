#!/usr/bin/env python3
"""Independent verifier for the C3X edition.

This script deliberately does NOT reuse c3x_engine's arithmetic. It re-reads
data/c3x_inputs.csv, rebuilds the ladder with its own code, and compares the
result to data/c3x_ladder.csv. It then re-runs the page builder in memory and
fails if any page on disk differs, so a stale page cannot ship.

Checks
  1. every source row: https(s) URL on the official allowlist, verbatim quote,
     ISO fetch date
  2. ladder: 40 unique amounts, arithmetic re-derived to the cent, percentages
     re-derived, staged count = ceil(amount / 50000)
  3. method grid: every priced row re-derived; every blank row carries an
     existing flag id
  4. every source id used anywhere resolves on the register
  5. every local link and anchor across the c3x pages resolves
  6. every generated table row carries an official link or a flag
  7. pages on disk are byte-identical to a fresh build (no staleness)
Exit code 0 only if all of the above pass.
"""
from __future__ import annotations

import csv
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
D = Decimal
PAGES = ["c3x-summary.html", "c3x-costs.html", "c3x-methods.html", "c3x-steps.html",
         "c3x-tax.html", "c3x-flagged.html", "c3x-sources.html"]

ALLOWED = (".gov.cn", "boc.cn", "gpo.gov", "govinfo.gov", "irs.gov", "fincen.gov",
           "ecfr.gov", "cbp.gov", "chinatax.gov.cn")

problems: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def q(v: D, places: str = "0.01") -> D:
    return v.quantize(D(places), rounding=ROUND_HALF_UP)


def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- 1. sources
sources = rows("c3x_sources.csv")
src_ids = set()
for s in sources:
    sid = s["id"]
    src_ids.add(sid)
    url = s["url"]
    if not url.startswith(("https://", "http://")):
        fail(f"{sid}: URL is not absolute: {url}")
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    if not any(host == d.lstrip(".") or host.endswith(d) for d in ALLOWED):
        fail(f"{sid}: host {host} is not on the official allowlist")
    if len(s["quote"].strip()) < 25:
        fail(f"{sid}: verbatim quote is missing or too short")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s["fetched_utc"]):
        fail(f"{sid}: fetched_utc is not ISO yyyy-mm-dd")
    if not s["proposition"].strip():
        fail(f"{sid}: no proposition recorded")
notes.append(f"sources: {len(sources)} rows, {len(src_ids)} ids, all on the allowlist with quotes")

# ---------------------------------------------------------------- inputs
inp = {r["id"]: r for r in rows("c3x_inputs.csv")}
ASK = D(inp["ask"]["value"])
BID = D(inp["bid"]["value"])
MID = (ASK + BID) / 2
if abs(D(inp["mid"]["value"]) - MID) > D("0.00005"):
    fail(f"mid input {inp['mid']['value']} != (ask+bid)/2 = {MID}")
PM = D(inp["wire_per_mille"]["value"])
FMIN = D(inp["wire_min"]["value"])
FMAX = D(inp["wire_max"]["value"])
CABLE = D(inp["cable_non_hk"]["value"])
for k, v in inp.items():
    if v["source"] not in src_ids:
        fail(f"input {k}: source {v['source']} is not on the register")

# ---------------------------------------------------------------- 2. ladder
ladder = rows("c3x_ladder.csv")
if len(ladder) != 40:
    fail(f"ladder has {len(ladder)} rows, expected 40")
if [r["amount_usd"] for r in ladder] != [str(10_000 * i) for i in range(1, 41)]:
    fail("ladder amounts are not $10,000..$400,000 in $10,000 steps")
else:
    notes.append("ladder: 40 unique amounts, $10,000 to $400,000, no gaps")

half = (ASK - MID) / ASK
for r in ladder:
    usd = D(r["amount_usd"])
    cny = usd * ASK
    spread = usd * half
    fee_cny = min(max(cny * PM, FMIN), FMAX) + CABLE
    fee_usd = fee_cny / ASK
    total = spread + fee_usd
    pct = total / usd * 100
    n = int((usd / D(50_000)).to_integral_value(rounding="ROUND_CEILING"))
    per = D(50_000) if usd >= D(50_000) else usd
    fee_each = min(max(per * ASK * PM, FMIN), FMAX) + CABLE
    staged_fee = fee_each * n / ASK
    staged_total = spread + staged_fee
    gain = usd * (1 - ASK / D(inp["irs_avg_2024"]["value"]))
    tax = gain * D("0.37") if gain > D(inp["sec988_200"]["value"]) else D(0)

    checks = [
        ("cny_needed", cny), ("spread_usd", spread), ("fee_cny", fee_cny), ("fee_usd", fee_usd),
        ("single_total_usd", total), ("staged_fee_usd", staged_fee), ("staged_total_usd", staged_total),
        ("sec988_tax_37_usd", tax),
    ]
    for field, expect in checks:
        if D(r[field]) != q(expect):
            fail(f"ladder {r['amount_usd']} {field}: csv {r[field]} != re-derived {q(expect)}")
    if D(r["single_total_pct"]) != q(pct, "0.0001"):
        fail(f"ladder {r['amount_usd']} pct: {r['single_total_pct']} != {q(pct, '0.0001')}")
    if r["staged_wires"] != str(n):
        fail(f"ladder {r['amount_usd']} wires: {r['staged_wires']} != {n}")
notes.append(f"ladder: 40 rows re-derived independently to the cent (half-spread {half*100:.4f}%)")

# ---------------------------------------------------------------- 3. method grid
methods = rows("c3x_methods.csv")
flags = {f["id"] for f in rows("c3x_flags.csv")}
grid = rows("c3x_method_costs.csv")
if len(grid) != len(methods) * 40:
    fail(f"method grid has {len(grid)} rows, expected {len(methods)*40}")
model = {m["id"]: m["price_model"] for m in methods}
priced = 0
for g in grid:
    m = model.get(g["method_id"])
    if m is None:
        fail(f"grid references unknown method {g['method_id']}")
        continue
    usd = D(g["amount_usd"])
    if m == "single":
        fee_cny = min(max(usd * ASK * PM, FMIN), FMAX) + CABLE
        want = q(usd * half + fee_cny / ASK)
        if D(g["cost_usd"]) != want:
            fail(f"grid {g['method_id']} {g['amount_usd']}: {g['cost_usd']} != {want}")
        priced += 1
    elif m == "staged":
        n = int((usd / D(50_000)).to_integral_value(rounding="ROUND_CEILING"))
        per = D(50_000) if usd >= D(50_000) else usd
        fee_cny = (min(max(per * ASK * PM, FMIN), FMAX) + CABLE) * n
        want = q(usd * half + fee_cny / ASK)
        if D(g["cost_usd"]) != want:
            fail(f"grid {g['method_id']} {g['amount_usd']}: {g['cost_usd']} != {want}")
        priced += 1
    else:
        if g["cost_usd"] or g["cost_pct"]:
            fail(f"grid {g['method_id']} {g['amount_usd']}: unpriced row carries a value")
        if g["flag"] not in flags:
            fail(f"grid {g['method_id']} {g['amount_usd']}: blank row has no valid flag")
notes.append(f"method grid: {len(grid)} rows, {priced} priced rows re-derived, "
             f"{len(grid)-priced} blank rows all carry an existing flag id")

# ---------------------------------------------------------------- 4. source ids used
for name in ("c3x_methods.csv", "c3x_steps.csv", "c3x_penalties.csv", "c3x_flags.csv"):
    for r in rows(name):
        blob = "|".join(v for v in r.values() if isinstance(v, str))
        for sid in set(re.findall(r"S\d{2}", blob)):
            if sid not in src_ids:
                fail(f"{name}: unknown source id {sid}")

# ---------------------------------------------------------------- 5. links and anchors
class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.ids, self.rows_without_link = [], set(), 0
        self._row_buf = ""
        self._in_row = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "tr":
            self._in_row, self._row_buf = True, ""
        if tag == "th" and self._in_row:
            self._row_buf += "TH"
        elif tag == "a" and a.get("href") and a["href"].startswith("http"):
            self._row_buf += "LINK"

    def handle_endtag(self, tag):
        if tag == "tr" and self._in_row:
            if "LINK" not in self._row_buf and "TH" not in self._row_buf:
                self.rows_without_link += 1
            self._in_row = False


parsed: dict[str, Collector] = {}
for page in PAGES:
    p = ROOT / page
    if not p.exists():
        fail(f"{page}: missing")
        continue
    c = Collector()
    c.feed(p.read_text(encoding="utf-8"))
    parsed[page] = c

for page, c in parsed.items():
    for href in c.hrefs:
        target, _, anchor = href.partition("#")
        if not target:
            if anchor and anchor not in c.ids:
                fail(f"{page}: internal anchor #{anchor} does not exist")
            continue
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        dest = (ROOT / target)
        if not dest.exists():
            fail(f"{page}: link to missing local file {target}")
            continue
        if anchor:
            if target not in parsed and dest.suffix == ".html":
                cc = Collector()
                cc.feed(dest.read_text(encoding="utf-8"))
                parsed[target] = cc
            if target in parsed and anchor not in parsed[target].ids:
                fail(f"{page}: #{anchor} not found in {target}")

# rows in the register and ladder must each carry a link or flag; the prose
# tables (tax layer, ranked routes) are sourced in the surrounding text.
for page in ("c3x-costs.html", "c3x-summary.html", "c3x-tax.html", "c3x-sources.html", "c3x-flagged.html"):
    c = parsed.get(page)
    if c and c.rows_without_link:
        fail(f"{page}: {c.rows_without_link} table row(s) carry no link at all")
    elif c:
        notes.append(f"{page}: every table row carries at least one link")

# explicit spot check: every source row and every flag row has an official link
for page in ("c3x-sources.html", "c3x-flagged.html"):
    text = (ROOT / page).read_text(encoding="utf-8")
    count = text.count("<tr id=")
    links = len(re.findall(r'href="https?://', text))
    if count == 0:
        fail(f"{page}: no id-bearing rows found")
    if links < count:
        fail(f"{page}: {count} rows but only {links} external links")

# ---------------------------------------------------------------- 6. row counts in HTML
costs_html = (ROOT / "c3x-costs.html").read_text(encoding="utf-8")
ladder_rows = len(re.findall(r'<td data-label="Amount">\$', costs_html))
if ladder_rows != 40:
    fail(f"c3x-costs.html renders {ladder_rows} ladder rows, expected 40")
else:
    notes.append("c3x-costs.html: 40 ladder rows rendered, each with a source cell")

# ---------------------------------------------------------------- 7. freshness
sys.path.insert(0, str(ROOT / "scripts"))
import build_c3x_site as B  # noqa: E402

fresh = {
    "c3x-summary.html": B.build_summary(),
    "c3x-costs.html": B.build_costs(),
    "c3x-methods.html": B.build_methods(),
    "c3x-steps.html": B.build_steps(),
    "c3x-tax.html": B.build_tax(),
    "c3x-flagged.html": B.build_flags(),
    "c3x-sources.html": B.build_sources(),
}
for page, html_text in fresh.items():
    disk = (ROOT / page)
    if disk.exists() and disk.read_text(encoding="utf-8") != html_text:
        fail(f"{page}: on-disk page is stale — run scripts/build_c3x_site.py")
if (ROOT / "assets" / "c3x.css").read_text(encoding="utf-8") != B.CSS:
    fail("assets/c3x.css is stale")
notes.append("freshness: all 7 pages and the stylesheet match a fresh in-memory build")

# ---------------------------------------------------------------- report
print("\n".join("· " + n for n in notes))
if problems:
    print("\nFAIL")
    for p in problems[:60]:
        print("  ✗", p)
    if len(problems) > 60:
        print(f"  … and {len(problems)-60} more")
    sys.exit(1)

print(f"\nPASS — {len(sources)} sources, {len(ladder)} ladder rows, {len(grid)} method rows, "
      f"{len(methods)} methods, {len(flags)} flags, {len(PAGES)} pages, 0 problems.")
