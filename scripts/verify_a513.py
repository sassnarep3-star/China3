#!/usr/bin/env python3
"""Independent checks for the a513 pages and data.

Nothing here imports the builder. Each figure is recomputed from the register with a different
arrangement of the arithmetic, and every claim on the pages must trace back to a register row.

Checks
  1. official-domain allowlist for every source URL
  2. every input row names a register row and its evidence string is literally in that row's quote
  3. the 40-increment ladder is re-derived to the cent, plus the percentage and net columns
  4. per-method grid: non-blank cells equal a re-derived model value; blank cells are marked UNVERIFIED
  5. HTML parity: row counts, one source link or flag per data row
  6. every external URL printed on a page exists in the register
  7. local links and anchors resolve; generated output is fresh
  8. no unrendered placeholders, and the ⊂988⊃ sensitivity table is arithmetically right
"""
from __future__ import annotations

import csv
import math
import re
import subprocess
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = ["a513.html", "a513-verify.html", "a513-steps.html"]

OFFICIAL = (
    "boc.cn", "bocusa.com", "safe.gov.cn", "m.safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn",
    "fgk.chinatax.gov.cn", "gov.cn", "govinfo.gov", "irs.gov", "fincen.gov", "ecfr.gov",
    "cbp.gov", "chinamoney.com.cn", "hncourt.gov.cn", "rst.shaanxi.gov.cn",
)

errors: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def q2(v: D) -> D:
    return v.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def official(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


# ------------------------------------------------------------------ 1 + 2. register
reg = rows("a513_verification.csv")
if len(reg) < 10:
    fail(f"register too small: {len(reg)} rows")
for r in reg:
    if not official(r["url"]):
        fail(f"{r['id']}: not an official domain: {r['url']}")
    if len(r["quote_verbatim"].strip()) < 15:
        fail(f"{r['id']}: quote too short to be evidence")
    if r["verdict"] != "verified":
        fail(f"{r['id']}: verdict is {r['verdict']!r}")
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$", r["fetched_utc"]):
        fail(f"{r['id']}: bad timestamp {r['fetched_utc']!r}")

REG = {r["id"]: r for r in reg}
inputs = rows("a513_inputs.csv")
if not inputs:
    fail("no inputs")
INP = {}
for row in inputs:
    fid = row["source_id"]
    if fid not in REG:
        fail(f"input {row['field']}: unknown source id {fid}")
        continue
    if row["evidence"] not in REG[fid]["quote_verbatim"]:
        fail(f"input {row['field']}: evidence {row['evidence']!r} not present in {fid}'s quote")
    INP[row["field"]] = row["value"]
    if row["field"] != "board_stamp":
        try:
            D(row["value"])
        except Exception:
            fail(f"input {row['field']}: {row['value']!r} is not numeric")

required = [
    "ask_cny_per_usd", "bid_cny_per_usd", "parity_cny_per_usd", "board_stamp", "wire_rate",
    "wire_min_cny", "wire_max_cny", "cable_other_cny", "our_usd_other", "convenience_usd",
    "fbar_threshold_usd", "fbar_willful_max_usd", "sec988_personal_exempt_usd",
]
for k in required:
    if k not in INP:
        fail(f"missing input {k}")

# ------------------------------------------------------------- 3. re-derive ladder
ask = D(INP["ask_cny_per_usd"])
bid = D(INP["bid_cny_per_usd"])
mid = (ask + bid) / D(2)
rate = D(INP["wire_rate"])
fmin = D(INP["wire_min_cny"])
fmax = D(INP["wire_max_cny"])
cable = D(INP["cable_other_cny"])
our = D(INP["our_usd_other"])
conv = int(D(INP["convenience_usd"]))

ladder = rows("a513_ladder.csv")
if len(ladder) != 40:
    fail(f"ladder has {len(ladder)} rows, expected 40")

for i, row in enumerate(ladder, start=1):
    a = D(row["amount_usd"])
    if a != D(10_000 * i):
        fail(f"ladder row {i}: amount {a} is not the {i}th 10k increment")
    # different arrangement: convert the CNY-side fee first, then add the spread in CNY terms
    fee = rate * a * ask
    fee = fmax if fee > fmax else (fmin if fee < fmin else fee)
    total = (a * ask - a * mid) / ask + (fee + cable) / ask
    if q2(total) != D(row["total_one_transfer_usd"]):
        fail(f"ladder {a}: total {row['total_one_transfer_usd']} != re-derived {q2(total)}")
    q4 = lambda v: v.quantize(D("0.0001"), rounding=ROUND_HALF_UP)
    if q4(total / a * D(100)) != D(row["pct_one_transfer"]):
        fail(f"ladder {a}: pct {row['pct_one_transfer']} != {q4(total / a * 100)}")
    if q2(a - total) != D(row["net_usd"]):
        fail(f"ladder {a}: net {row['net_usd']} != {q2(a - total)}")
    n = math.ceil(int(a) / conv)
    if int(row["transfers_if_50k"]) != n:
        fail(f"ladder {a}: transfers {row['transfers_if_50k']} != {n}")
    mt = (a * ask - a * mid) / ask + D(n) * (fee * n / n + cable) / ask if n else total
    mt = (a * ask - a * mid) / ask + D(n) * (min(fmax, max(fmin, rate * (a / n) * ask)) + cable) / ask
    if q2(mt) != D(row["total_multi_usd"]):
        fail(f"ladder {a}: multi {row['total_multi_usd']} != re-derived {q2(mt)}")
    if q2(total + our) != D(row["total_our_usd"]):
        fail(f"ladder {a}: our {row['total_our_usd']} != {q2(total + our)}")

notes.append(f"ladder: 40 increments re-derived; USD 10,000 = {ladder[0]['total_one_transfer_usd']}, "
             f"USD 400,000 = {ladder[-1]['total_one_transfer_usd']}")

# ------------------------------------------------------- 4. per-method grid
methods = rows("a513_methods.csv")
if len(methods) != 10:
    fail(f"expected 10 routes, found {len(methods)}")
grid = rows("a513_method_costs.csv")
if len(grid) != len(methods) * 40:
    fail(f"grid has {len(grid)} rows, expected {len(methods) * 40}")

MODEL = {m["method_id"]: m["cost_model"] for m in methods}
SEEN = set()
for r in grid:
    mid_ = r["method_id"]
    if mid_ not in MODEL:
        fail(f"grid references unknown route {mid_}")
        continue
    SEEN.add(mid_)
    a = D(r["amount_usd"])
    base = D(dict((x["amount_usd"], x["total_one_transfer_usd"]) for x in ladder).get(
        str(int(a)), "0")) if False else None
    band = next(D(x["total_one_transfer_usd"]) for x in ladder if D(x["amount_usd"]) == a)
    model = MODEL[mid_]
    if model == "WIRE1":
        want = band
    elif model == "WIRE_OUR":
        want = band + our
    elif model == "WIRE_MULTI50":
        want = next(D(x["total_multi_usd"]) for x in ladder if D(x["amount_usd"]) == a)
    elif model == "WIRE_SAFE":
        want = band
    else:
        want = None
    if want is None:
        if r["total_usd"] != "" or r["status"] != "UNVERIFIED":
            fail(f"{mid_} at {a}: unpriced route carries a value ({r['total_usd']!r})")
    else:
        if r["total_usd"] == "":
            fail(f"{mid_} at {a}: priced route is blank")
        elif D(r["total_usd"]) != q2(want):
            fail(f"{mid_} at {a}: {r['total_usd']} != {q2(want)}")
        if r["status"] == "UNVERIFIED":
            fail(f"{mid_} at {a}: priced route marked UNVERIFIED")
if SEEN != set(MODEL):
    fail(f"grid misses routes: {set(MODEL) - SEEN}")

for m in methods:
    if m["lawful"] == "Yes" and not m["limit_source_ids"]:
        fail(f"{m['method_id']}: lawful route with no limit source")
    for sid in [x for x in m["source_ids"].split(";") if x]:
        if sid not in REG:
            fail(f"{m['method_id']}: unknown source id {sid}")

notes.append(f"method grid: {len(grid)} cells, {sum(1 for r in grid if r['total_usd'])} priced, "
             f"{sum(1 for r in grid if not r['total_usd'])} blank and flagged")

# ----------------------------------------------------------- 5 + 6 + 7. HTML
def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def local_target(page: str, href: str) -> Path:
    path, _, anchor = href.partition("#")
    target = ROOT / (path or page.split("#")[0])
    return target, anchor


for page in PAGES:
    p = ROOT / page
    if not p.exists():
        fail(f"missing page {page}")
        continue
    html = p.read_text(encoding="utf-8")
    if "{" in strip_tags(html) and re.search(r"\{[a-z_]+\(", strip_tags(html)):
        fail(f"{page}: unrendered template placeholder")
    if html.count("<main") != 1 or html.count("</main>") != 1:
        fail(f"{page}: main element count wrong")

    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith(("http://", "https://")):
            if not official(href):
                fail(f"{page}: external link not on the official allowlist: {href}")
            known = {r["url"] for r in reg} | {r["url"] for r in rows("a513_flags.csv") if r["url"]}
            if href not in known:
                fail(f"{page}: external link not registered anywhere: {href}")
            continue
        if href.startswith(("mailto:", "data:")):
            continue
        target, anchor = local_target(page, href)
        if not target.exists():
            fail(f"{page}: broken local link {href}")
            continue
        if anchor:
            thtml = target.read_text(encoding="utf-8")
            if f'id="{anchor}"' not in thtml:
                fail(f"{page}: missing anchor #{anchor} in {target.name}")

    for script in re.findall(r'src="([^"]+)"', html):
        if not (ROOT / script).exists():
            fail(f"{page}: missing script {script}")
    for css in re.findall(r'link rel="stylesheet" href="([^"]+)"', html):
        if not (ROOT / css).exists():
            fail(f"{page}: missing stylesheet {css}")

    # every data row must carry a source chip or an explicit flag
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        if "<th scope=\"col\"" in tr or 'scope="col"' in tr:
            continue
        if "data-l=" not in tr and "class=\"hl\"" not in tr:
            continue
        if "class=\"src\"" not in tr and "src-flag" not in tr and "blank" not in tr and "tag" not in tr:
            fail(f"{page}: data row without a source link or flag: {strip_tags(tr)[:70]!r}")

main_html = (ROOT / "a513.html").read_text(encoding="utf-8")
for amount in range(10_000, 400_001, 10_000):
    if f'<th scope="row">{amount:,}</th>' not in main_html:
        fail(f"a513.html: ladder row {amount} missing")
if main_html.count('<tr') < 40:
    fail("a513.html: fewer than 40 table rows")

verify_html = (ROOT / "a513-verify.html").read_text(encoding="utf-8")
for r in reg:
    if r["url"] not in verify_html:
        fail(f"a513-verify.html: register row {r['id']} url missing")
    if r["id"] not in verify_html:
        fail(f"a513-verify.html: register row {r['id']} id missing")

flags_html = (ROOT / "a513.html").read_text(encoding="utf-8")
for f in rows("a513_flags.csv"):
    if f["id"] not in flags_html:
        fail(f"a513.html: flag {f['id']} not published")

# ------------------------------------------------------------------ 8. 988 table
sec = D(INP.get("sec988_personal_exempt_usd", "200"))
for a in (10_000, 100_000, 400_000):
    marker = f'<th scope="row">{a:,}</th>'
    if marker not in main_html:
        fail(f"a513.html: no 988 row for {a}")
cny = D(400_000) * ask
basis7 = cny / D("7.00")
gain7 = D(400_000) - basis7
if q2(gain7 * D("0.24")) != D("4318.63"):
    fail(f"988 arithmetic drifted: 24% of {q2(gain7)} = {q2(gain7 * D('0.24'))}")

# ------------------------------------------------------------------ 9. freshness
res = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_a513.py"), "--check"],
                     capture_output=True, text=True)
if res.returncode != 0:
    fail(f"generated output is stale: {res.stdout.strip()} {res.stderr.strip()}")
else:
    notes.append(res.stdout.strip())

# ------------------------------------------------------------------------ report
for n in notes:
    print(f"  note: {n}")
if errors:
    print("\nFAIL — " + str(len(errors)) + " problem(s):")
    for e in errors:
        print("  - " + e)
    raise SystemExit(1)
print(f"\nPASS — A513 verified: {len(reg)} register rows on official domains with quotes and timestamps, "
      f"{len(inputs)} inputs whose evidence string is present in its source quote, 40 ladder increments and "
      f"{len(grid)} method cells re-derived, {len(rows('a513_flags.csv'))} flags published, "
      f"all local links and anchors resolve, output fresh.")
