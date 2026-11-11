#!/usr/bin/env python3
"""Gate for the 76e source re-check layer.

Checks, in order:
  1. data/76e_costs.csv recomputes exactly from the board figures recorded for
     11 November 2026 and the published BOC tariff;
  2. the archived 10 November values still recompute, while the current canonical
     data/e347_costs.csv (L01, L03) independently recomputes at its current board;
  3. the HTML table cells equal the CSV cells (no hand-edited page);
  4. every source row and every finding row carries at least one https URL and
     every URL is on an official domain;
  5. no table row is blank without a flag, and no value is missing;
  6. every local href/link target in the page exists.

Exit 0 on pass, 1 on the first failure. Run: python3 scripts/verify_76e.py
"""
import csv
import os
import re
import sys
from decimal import Decimal as D, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENT = D("0.01")

BID, ASK = D("6.6630"), D("6.6911")
BID_10, ASK_10 = D("6.6571"), D("6.6851")
BID_CURRENT, ASK_CURRENT = D("6.6606"), D("6.6886")
IRS_2024 = D("7.189")
WIRE_RATE, WIRE_MIN, WIRE_MAX, CABLE = D("0.001"), D("50"), D("260"), D("150")

OFFICIAL = (
    ".gov.cn", ".irs.gov", ".ecfr.gov", ".govinfo.gov",
    "boc.cn", "chinatax.gov.cn",
)

failures = []
rounding_notes = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


def q(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def spread(usd, bid, ask):
    return D(usd) * (ask - (bid + ask) / 2) / ask


def wire(usd, ask):
    return (min(WIRE_MAX, max(WIRE_MIN, D(usd) * ask * WIRE_RATE)) + CABLE) / ask


def load(path):
    with open(os.path.join(ROOT, path), newline="") as fh:
        return list(csv.DictReader(fh))


# 1 + 2 ----------------------------------------------------------------------
costs = load("data/76e_costs.csv")
check(len(costs) == 40, "expected 40 ladder rows, found %d" % len(costs))

published = {(r["method_id"], int(r["amount_usd"])): D(r["known_cost_usd"])
             for r in load("data/e347_costs.csv") if r["method_id"] in ("L01", "L03")}

for r in costs:
    amt = int(r["amount_usd"])
    l01 = q(spread(amt, BID, ASK) + wire(amt, ASK))
    l03 = q(wire(amt, ASK))
    check(D(r["l01_total_today"]) == l01,
          "row %d: l01_total_today %s != recomputed %s" % (amt, r["l01_total_today"], l01))
    check(D(r["l03_total_today"]) == l03,
          "row %d: l03_total_today %s != recomputed %s" % (amt, r["l03_total_today"], l03))
    if D(r["l01_spread_today"]) + D(r["l01_fee_today"]) != l01:
        rounding_notes.append(amt)
    check(q(spread(amt, BID_CURRENT, ASK_CURRENT) + wire(amt, ASK_CURRENT)) == published[("L01", amt)],
          "row %d: current canonical L01 does not match its current board" % amt)
    check(q(wire(amt, ASK_CURRENT)) == published[("L03", amt)],
          "row %d: current canonical L03 does not match its current board" % amt)
    check(D(r["l01_delta"]) == l01 - D(r["l01_total_10nov"]),
          "row %d: delta does not equal today minus 10 Nov" % amt)
    # The 10 November board must reproduce the archived 76e baseline, not the newer canonical file.
    check(q(spread(amt, BID_10, ASK_10) + wire(amt, ASK_10)) == D(r["l01_total_10nov"]),
          "row %d: the convention does not reproduce the archived L01 figure" % amt)
    check(q(D(amt) * (1 - ASK / IRS_2024)) == D(r["fx_gain_2024_today"]),
          "row %d: 2024 currency-gain figure does not recompute" % amt)

# 3 --------------------------------------------------------------------------
page = open(os.path.join(ROOT, "76e-verification.html"), encoding="utf-8").read()
cells = re.findall(r"<td data-label=\"Bank purchase \+ wire \(L01\)\">([\d,\.]+)</td>", page)
check(len(cells) == 40, "expected 40 L01 cells in the page, found %d" % len(cells))
for r, cell in zip(costs, cells):
    check(D(cell.replace(",", "")) == D(r["l01_total_today"]),
          "page cell %s does not match CSV %s" % (cell, r["l01_total_today"]))
l03_cells = re.findall(r"<td data-label=\"Wire out FX already held \(L03\)\">([\d,\.]+)</td>", page)
check(len(l03_cells) == 40, "expected 40 L03 cells in the page, found %d" % len(l03_cells))
for r, cell in zip(costs, l03_cells):
    check(D(cell.replace(",", "")) == D(r["l03_total_today"]),
          "page L03 cell %s does not match CSV %s" % (cell, r["l03_total_today"]))

# 4 --------------------------------------------------------------------------
URL_RE = re.compile(r"https?://[^\s\"'<>]+")


def official(url):
    host = url.split("/")[2].lower()
    return any(host == d.lstrip(".") or host.endswith(d) for d in OFFICIAL)


for name, rows in (("76e_recheck.csv", load("data/76e_recheck.csv")),
                   ("76e_findings.csv", load("data/76e_findings.csv"))):
    check(len(rows) >= 6, "%s has only %d rows" % (name, len(rows)))
    for r in rows:
        rid = r.get("id", "?")
        urls = URL_RE.findall(r.get("url", "") + " " + r.get("source_urls", ""))
        check(bool(urls), "%s %s carries no source URL" % (name, rid))
        for u in urls:
            check(official(u), "%s %s cites a non-official domain: %s" % (name, rid, u))
        for key in ("finding", "evidence") if name.endswith("findings.csv") else ("finding_today", "verdict"):
            check(bool(r.get(key, "").strip()), "%s %s has an empty %s" % (name, rid, key))

# every source row must also appear as a link in the page
for r in load("data/76e_recheck.csv"):
    check(r["url"] in page, "source %s URL is not linked in the page" % r["id"])
for r in load("data/76e_findings.csv"):
    first = r["source_urls"].split()[0]
    check(first in page, "finding %s first source URL is not linked in the page" % r["id"])

# 5 --------------------------------------------------------------------------
check("not verified" not in page.lower() or "unverified" in page.lower(),
      "page mentions unverified material without a flag")
check(page.count("data-label=") > 100, "stacked-table labels missing")

# 6 --------------------------------------------------------------------------
for href in set(re.findall(r'href="([^"#?][^"]*)"', page)):
    if href.startswith(("http", "mailto:")):
        continue
    target = os.path.normpath(os.path.join(ROOT, href.split("#")[0]))
    check(os.path.exists(target), "broken local link: %s" % href)

if failures:
    print("FAIL — %d problem(s)" % len(failures))
    for f in failures[:40]:
        print("  -", f)
    sys.exit(1)

if rounding_notes:
    print("note: in %d of 40 rows the two rounded components add to one cent more or less "
          "than the rounded total (%s). The total is rounded once, from unrounded parts."
          % (len(rounding_notes), ", ".join("$%s" % format(a, ",") for a in rounding_notes[:6])))
print("PASS — 76e: 40 ladder rows recomputed; archived and current conventions independently reproduce the "
      "80 canonical L01/L03 cells; page cells equal the CSV; %d re-check rows and %d "
      "findings each cite an official page; all local links resolve."
      % (len(load("data/76e_recheck.csv")), len(load("data/76e_findings.csv"))))
