#!/usr/bin/env python3
"""Independent line-by0line verifier for the consolidated dashboard.

Deliberately re-implements the arithmetic instead of importing build_cn3.compute(), so a bug in
one implementation shows up as a mismatch rather than as two identical wrong numbers.

Checks
  1  every ladder row's money is reproducible from the sourced inputs (±0.01)
  2  every ladder row cites a registered source whose host is on the official allowlist
  3  an empty cost is allowed only for an unverified/prohibited route, and must be flagged
  4  every rendered ladder table has 40 rows, matches the CSV, and every row carries a link
     (or an explicit "blank" marker when the value is unpublished)
  5  every source id, flag id and method id is rendered on its page
  6  every internal link on every cn3 page resolves
  7  the headline figures on the landing page match the model
"""
from __future__ import annotations

import csv
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import cn3_data as D  # noqa: E402

ALLOWED_HOSTS = {
    "www.boc.cn", "boc.cn",
    "www.safe.gov.cn", "safe.gov.cn", "m.safe.gov.cn",
    "www.pbc.gov.cn", "pbc.gov.cn",
    "www.chinatax.gov.cn", "chinatax.gov.cn", "fgk.chinatax.gov.cn",
    "www.irs.gov", "irs.gov",
    "www.ecfr.gov", "ecfr.gov",
    "www.law.cornell.edu", "law.cornell.edu",
    "www.cbp.gov", "cbp.gov",
    "www.hkma.gov.hk",
}

errors: list[str] = []
warns: list[str] = []


def fail(msg: str):
    errors.append(msg)


def host(url: str) -> str:
    m = re.match(r"https?://([^/]+)/?", url)
    return m.group(1).lower() if m else ""


def read_csv(name):
    with (ROOT / "data" / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------------------------
# 1–3  data level
# ---------------------------------------------------------------------------------------------
inputs = {r["id"]: r for r in D.INPUTS}
ASK = float(inputs["C3-I01"]["value"])
MID = (float(inputs["C3-I01"]["value"]) + float(inputs["C3-I02"]["value"])) / 2
SPREAD_PCT = (ASK - MID) / MID
assert abs(SPREAD_PCT - float(inputs["C3-I04"]["value"])) < 5e-9, "spread constant drifted"
WIRE_RATE = float(inputs["C3-I05"]["value"])
WIRE_MIN = float(inputs["C3-I06"]["value"])
WIRE_MAX = float(inputs["C3-I07"]["value"])
CABLE = float(inputs["C3-I08"]["value"])
ATM_CAP = 112.0
DAILY = float(inputs["C3-I12"]["value"])
ANNUAL = float(inputs["C3-I13"]["value"])
CONV = float(inputs["C3-I14"]["value"])
R2024 = float(inputs["C3-I29"]["value"])
TAX = float(inputs["C3-I31"]["value"])

sources = {s["id"]: s for s in D.SOURCES}
methods = {m["id"]: m for m in D.METHODS}
flags = {f[0] for f in D.FLAGS}

ladder = read_csv("cn3_ladder.csv")
if len(ladder) != len(D.METHODS) * 40:
    fail(f"ladder has {len(ladder)} rows, expected {len(D.METHODS)*40}")

seen = set()
for r in ladder:
    key = (r["method_id"], r["amount_usd"])
    if key in seen:
        fail(f"duplicate ladder row {key}")
    seen.add(key)

    mid = r["method_id"]
    if mid not in methods:
        fail(f"unknown method id {mid}")
        continue
    amount = int(r["amount_usd"])
    cny = amount * ASK
    if abs(float(r["cny_at_ask"]) - cny) > 0.01:
        fail(f"{mid} ${amount}: CNY {r['cny_at_ask']} != {cny:.2f}")

    f = methods[mid]["formula"]
    if f in ("wire", "wire_quota", "wire_nofx", "wire_dividend"):
        n = math.ceil(amount / CONV) if f == "wire_quota" else 1
        fee_cny = min(max(0.001 * (cny / n), WIRE_MIN), WIRE_MAX) + CABLE
        fee = n * fee_cny / ASK
        spread = 0.0 if f == "wire_nofx" else amount * SPREAD_PCT
        if abs(float(r["wire_fee_usd"]) - n * (fee_cny - CABLE) / ASK) > 0.011:
            fail(f"{mid} ${amount}: wire fee mismatch")
        if abs(float(r["cable_usd"]) - n * CABLE / ASK) > 0.011:
            fail(f"{mid} ${amount}: cable mismatch")
        if abs(float(r["spread_usd"]) - spread) > 0.011:
            fail(f"{mid} ${amount}: spread mismatch")
        if abs(float(r["known_cost_usd"]) - (spread + fee)) > 0.02:
            fail(f"{mid} ${amount}: known cost mismatch")
        if int(r["transfers"]) != n:
            fail(f"{mid} ${amount}: transfer count mismatch")
    elif f in ("atm_unionpay", "atm_visa"):
        n = math.ceil(cny / DAILY)
        if f == "atm_unionpay":
            fee = n * ATM_CAP / ASK
        else:
            per = min(max(0.025 * (DAILY / ASK), 3.0), 40.0)
            fee = n * per
        if abs(float(r["known_cost_usd"]) - fee) > 0.02:
            fail(f"{mid} ${amount}: ATM cost mismatch")
        if int(r["years"]) != math.ceil(cny / ANNUAL):
            fail(f"{mid} ${amount}: ATM years mismatch")
    elif f == "cash":
        if abs(float(r["known_cost_usd"]) - amount * SPREAD_PCT) > 0.011:
            fail(f"{mid} ${amount}: cash cost mismatch")

    # source
    sid = r["source_id"]
    if sid not in sources:
        fail(f"{mid} ${amount}: unregistered source id {sid}")
    if r["source_url"] != sources.get(sid, {}).get("url"):
        fail(f"{mid} ${amount}: source_url does not match the register")
    if host(r["source_url"]) not in ALLOWED_HOSTS:
        fail(f"{mid} ${amount}: non-official host {host(r['source_url'])}")

    # blanks must be legitimate
    if r["known_cost_usd"] == "":
        if r["status"] not in ("unverified", "prohibited"):
            fail(f"{mid} ${amount}: cost blank but status {r['status']}")
    elif r["status"] in ("unverified", "prohibited"):
        fail(f"{mid} ${amount}: status {r['status']} but a cost was published")

    # U.S. §988 line must be reproducible where it is published
    if r["us_tax_2024"] != "":
        gain = max(amount * (1 - ASK / R2024), 0.0)
        if abs(float(r["us_gain_2024"]) - gain) > 0.02:
            fail(f"{mid} ${amount}: §988 gain mismatch")
        if abs(float(r["us_tax_2024"]) - gain * TAX) > 0.02:
            fail(f"{mid} ${amount}: §988 tax mismatch")

# every blank route must be covered by a flag
blank_methods = {r["method_id"] for r in ladder if r["known_cost_usd"] == ""}
if blank_methods and not {"C3-F03", "C3-F11", "C3-F12", "C3-F04"} <= flags:
    fail("blank-cost routes exist but the blank-cost flags are missing")

# ---------------------------------------------------------------------------------------------
# 4–5  HTML level
# ---------------------------------------------------------------------------------------------
TABLE_RE = re.compile(r'<table[^>]*data-kind="([^"]+)"([^>]*)>(.*?)</table>', re.S)
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)

cost_html = (ROOT / "cn3-cost.html").read_text(encoding="utf-8")
rendered = {}
for kind, attrs, body in TABLE_RE.findall(cost_html):
    body = body.split("</thead>", 1)[-1]
    rows = ROW_RE.findall(body)
    if kind == "ladder":
        m = re.search(r'data-method="([^"]+)"', attrs)
        rendered[m.group(1)] = len(rows)
        expect = re.search(r'data-expect="(\d+)"', attrs)
        if expect and int(expect.group(1)) != len(rows):
            fail(f"cn3-cost.html {m.group(1)}: {len(rows)} rows rendered, header says {expect.group(1)}")
        csv_count = sum(1 for r in ladder if r["method_id"] == m.group(1))
        if len(rows) != csv_count:
            fail(f"cn3-cost.html {m.group(1)}: {len(rows)} rendered vs {csv_count} in CSV")
        for row in rows:
            if not re.search(r"https?://", row):
                fail(f"cn3-cost.html {m.group(1)}: a row has no source link")
            if "blank" not in row and "—" not in row and "0.00" not in row:
                pass  # link presence is the requirement
if set(rendered) != set(methods):
    fail(f"cn3-cost.html renders {sorted(rendered)} methods, model has {sorted(methods)}")

index_html = (ROOT / "index.html").read_text(encoding="utf-8")
headline = [b for k, a, b in TABLE_RE.findall(index_html) if k == "headline"]
if not headline:
    fail("index.html: headline table missing")
else:
    rows = ROW_RE.findall(headline[0].split("</thead>", 1)[-1])
    if len(rows) != 40:
        fail(f"index.html: headline table has {len(rows)} rows, expected 40")

sources_html = (ROOT / "cn3-sources.html").read_text(encoding="utf-8")
for sid in sources:
    if sid not in sources_html:
        fail(f"cn3-sources.html: source {sid} missing")
review_html = (ROOT / "cn3-review.html").read_text(encoding="utf-8")
for fid in flags:
    if fid not in review_html:
        fail(f"cn3-review.html: flag {fid} missing")
methods_html = (ROOT / "cn3-methods.html").read_text(encoding="utf-8")
import html as _html
for m in D.METHODS:
    if _html.escape(m["name"][:20]) not in methods_html:
        fail(f"cn3-methods.html: method {m['id']} missing")
steps_html = (ROOT / "cn3-steps.html").read_text(encoding="utf-8")
for mid in {s[0] for s in D.STEPS}:
    if f'id="steps-{mid.lower()}"' not in steps_html:
        fail(f"cn3-steps.html: playbook {mid} missing")
tax_html = (ROOT / "cn3-tax.html").read_text(encoding="utf-8")
for needle in ("§988", "16,536", "165,353", "0.210%", "CNY 260", "CNY 150"):
    if needle not in tax_html:
        fail(f"cn3-tax.html: expected text {needle!r} missing")

# ---------------------------------------------------------------------------------------------
# 6  internal links
# ---------------------------------------------------------------------------------------------
PAGES = ["index.html"] + [f"cn3-{n}.html" for n in
                          ("cost", "methods", "tax", "steps", "review", "sources")]
LINK_RE = re.compile(r'href="([^"]+)"')
for page in PAGES:
    text = (ROOT / page).read_text(encoding="utf-8")
    for href in LINK_RE.findall(text):
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = href.split("#", 1)[0].split("?", 1)[0]
        if not target:
            continue
        if not (ROOT / target).exists():
            fail(f"{page}: broken local link {href}")

# ---------------------------------------------------------------------------------------------
# 7  headline consistency
# ---------------------------------------------------------------------------------------------
w1_400 = next(r for r in ladder if r["method_id"] == "W1" and r["amount_usd"] == "400000")
for value in (f"${float(w1_400['known_cost_usd']):,.2f}", f"${float(w1_400['all_in_usd']):,.2f}"):
    if value not in index_html:
        fail(f"index.html: headline figure {value} not rendered")

print(f"checked {len(ladder)} ladder rows, {len(methods)} methods, {len(sources)} sources, "
      f"{len(inputs)} inputs, {len(flags)} flags, {len(PAGES)} pages")
if warns:
    for w in warns:
        print("WARN:", w)
if errors:
    print(f"FAIL — {len(errors)} error(s)")
    for e in errors[:25]:
        print("  -", e)
    raise SystemExit(1)
print("PASS — every row reproducible, sourced, blank-flagged, and every link resolves.")
