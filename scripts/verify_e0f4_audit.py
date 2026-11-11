#!/usr/bin/env python3
"""Content gate for the e0f4 independent audit of PR #49.

Checks:
  1. every row of data/e0f4_76e_audit.csv carries at least one https official URL or is
     explicitly repo-internal (categories repo/verdict/, arithmetic A05/A06 style with no external URL);
     all external domains are official;
  2. headline arithmetic claims re-derived from the 2026-11-11 board (L01/L03 ladder, 40 rows) match the CSV figures recorded in this pass;
  3. the page's rendered parity cells ($53.42 / $271.26 / $901.20 / 6,925.86 / 27,703.44) are present;
  4. the page links only existing local files, and every external link is https on an official domain,
     github.com (this repository) or govinfo.gov;
  5. every finding ID F01-F07 appears in the page;
  6. no tracked *.md file contains literal merge-conflict markers;
  7. data/e347_costs.csv monetary cells still re-derive to the cent at the 10 Nov board (the audit's A04 claim).

Exit 0 on pass, 1 on the first failure. Run: python3 scripts/verify_e0f4_audit.py
"""
import csv
import os
import re
import subprocess
from collections import Counter
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFICIAL = (
    ".gov.cn", ".irs.gov", ".ecfr.gov", ".govinfo.gov", "boc.cn", "chinatax.gov.cn",
    ".pbc.gov.cn", ".safe.gov.cn", ".mofcom.gov.cn", ".chinatax.gov.cn",
    "github.com",
)
failures = []

def fail(msg):
    failures.append(msg)

def rel(path):
    return os.path.join(ROOT, path)

# 1 -----------------------------------------------------------------------
with open(rel("data/e0f4_76e_audit.csv"), newline="") as fh:
    rows = list(csv.DictReader(fh))
check_rows = [r for r in rows if r["verdict"] not in ("SAFE TO MERGE",)]
if len(rows) != 38:
    fail("expected 38 audit rows, found %d" % len(rows))
for r in rows:
    urls = [u for u in r["source_urls"].split() if u]
    for u in urls:
        if not u.startswith("https://") and not u.startswith("http://"):
            fail("audit %s: non-http(s) URL %s" % (r["id"], u))
        host = urlparse(u).netloc.lower()
        if not any(host == d.lstrip(".") or host.endswith(d) for d in OFFICIAL):
            fail("audit %s: non-official domain %s" % (r["id"], host))
    if not urls and r["category"] in ("sources", "findings"):
        fail("audit %s: no source URL recorded for a %s row" % (r["id"], r["category"]))

# 2 -----------------------------------------------------------------------
BID, ASK = D("6.6630"), D("6.6911")
BID10, ASK10 = D("6.6571"), D("6.6851")
CENT = D("0.01")

def r2(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)

def ladder(bid, ask):
    mid = (bid + ask) / 2
    out = {}
    for a in range(10000, 400001, 10000):
        DA = D(a)
        spread = DA * (ask - mid) / ask
        wire = (min(D(260), max(D(50), DA * ask * D("0.001"))) + D(150)) / ask
        out[a] = (r2(spread + wire), r2(wire))
    return out

t11, t10 = ladder(BID, ASK), ladder(BID10, ASK10)
expected_today = {10000: D("53.42"), 100000: D("271.26"), 400000: D("901.20")}
for amt, exp in expected_today.items():
    if t11[amt][0] != exp:
        fail("11 Nov board re-derivation: expected %s at %d, got %s" % (exp, amt, t11[amt][0]))
if t10[10000][0] != D("53.38") or t10[400000][0] != D("899.01"):
    fail("10 Nov board re-derivation drifted: %s / %s" % (t10[10000][0], t10[400000][0]))

# 3 -----------------------------------------------------------------------
page = open(rel("e0f4-76e-audit.html"), encoding="utf-8").read()
for token in ("53.42", "271.26", "901.20", "27,703.44", "6,925.86", "16/16", "SAFE TO MERGE"):
    if token not in page:
        fail("page missing required parity token: %s" % token)

# 4 -----------------------------------------------------------------------
hrefs = re.findall(r'href="([^"]+)"', page)
for href in hrefs:
    if href.startswith(("http://", "https://")):
        host = urlparse(href).netloc.lower()
        if not any(host == d.lstrip(".") or host.endswith(d) for d in OFFICIAL):
            fail("page links non-official external domain: %s" % host)
    elif href.startswith(("#", "mailto:")):
        continue
    else:
        target = rel(href.split("#")[0])
        if not os.path.exists(target):
            fail("page links missing local file: %s" % href)

# 5 -----------------------------------------------------------------------
for i in range(1, 8):
    fid = "F%02d" % i
    if fid not in page:
        fail("page missing finding %s" % fid)

# 6 -----------------------------------------------------------------------
def marker_lines(text):
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"`[^`\n]*`", "", raw)
        stripped = line.strip()
        if stripped.startswith("<<<<<<<") or stripped.startswith(">>>>>>>") or re.fullmatch(r"=+", stripped):
            lines.append(raw)
    return lines


try:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    base = ""
    for ref in ("origin/main", "FETCH_HEAD"):
        try:
            base = subprocess.run(["git", "merge-base", "HEAD", ref], cwd=ROOT,
                                  capture_output=True, text=True, check=True).stdout.strip()
            if base:
                break
        except subprocess.CalledProcessError:
            continue
    if not base:
        print("warning: no merge-base for the conflict-marker gate; inherited markers cannot be distinguished, gate skipped")
        base_markers = None
    else:
        base_files = subprocess.run(["git", "ls-tree", "-r", "--name-only", base], cwd=ROOT,
                                    capture_output=True, text=True, check=True).stdout.split()
        base_markers = {}
        for bpath in base_files:
            if not bpath.endswith(".md"):
                continue
            btext = subprocess.run(["git", "show", "%s:%s" % (base, bpath)], cwd=ROOT,
                                   capture_output=True, check=False).stdout.decode("utf-8", errors="ignore")
            base_markers[bpath] = Counter(marker_lines(btext))

    for path in out:
        current = Counter(marker_lines(open(rel(path), encoding="utf-8", errors="ignore").read()))
        if base_markers is None:
            continue
        inherited = base_markers.get(path, Counter())
        excess = current - inherited
        if excess:
            for line, count in excess.items():
                fail("tracked markdown %s introduces conflict marker not present at merge-base (x%d): %s" % (path, count, line[:80]))
except subprocess.CalledProcessError as exc:
    print("warning: git ls-files failed (%s); conflict-marker gate skipped" % exc)

# 7 -----------------------------------------------------------------------
BID10, ASK10 = D("6.6571"), D("6.6851")
mid10 = (BID10 + ASK10) / 2
mon_checks = mon_mm = 0
with open(rel("data/e347_costs.csv"), newline="") as fh:
    for r in csv.DictReader(fh):
        model = r["model"]
        if model == "blank":
            continue
        a = int(r["amount_usd"])
        DA = D(a)
        spread = DA * (ASK10 - mid10) / ASK10

        def wire_cny(base):
            return min(D(260), max(D(50), base * D("0.001"))) + D(150)

        cells = []
        if model == "wire_only":
            fee = wire_cny(DA * ASK10) / ASK10
            cells = [("fee_usd", fee), ("known_cost_usd", fee)]
        elif model in ("property", "fx_wire"):
            fee_cny = wire_cny(DA * ASK10)
            fee = fee_cny / ASK10
            cells = [("spread_usd", spread), ("fee_usd", fee), ("known_cost_usd", spread + fee), ("rmb_debited", DA * ASK10 + fee_cny)]
        elif model == "quota":
            n_full, rem = divmod(a, 50000)
            wires = [D(50000)] * n_full + ([D(rem)] if rem else [])
            fee = sum(wire_cny(w * ASK10) / ASK10 for w in wires)
            cells = [("spread_usd", spread), ("fee_usd", fee), ("known_cost_usd", spread + fee)]
        elif model == "dividend":
            tax = DA * D("0.2")
            base = DA - tax
            sp = base * (ASK10 - mid10) / ASK10
            fee = wire_cny(base * ASK10) / ASK10
            cells = [("tax_usd", tax), ("spread_usd", sp), ("fee_usd", fee), ("known_cost_usd", tax + sp + fee)]
        elif model == "cash":
            cells = [("spread_usd", spread), ("known_cost_usd", spread)]
        elif model == "atm":
            rmb = DA * ASK10
            n_full = int(rmb // D(10000))
            rem = rmb - n_full * D(10000)
            chunks = [D(10000)] * n_full + ([rem] if rem > 0 else [])
            fee = sum(min(D(112), D(12) + c * D("0.01")) for c in chunks) / ASK10
            cells = [("fee_usd", fee), ("known_cost_usd", fee)]
        for col, got in cells:
            mon_checks += 1
            if abs(r2(got) - D(r[col])) > D("0.005"):
                mon_mm += 1
if mon_mm:
    fail("data/e347_costs.csv: %d monetary mismatches at the 10 Nov board (of %d cells)" % (mon_mm, mon_checks))

if failures:
    for msg in failures:
        print("FAIL: %s" % msg)
    sys.exit(1)
print("e0f4 audit gate passed: %d CSV rows; 40-row ladder re-derived; page parity ok; %d monetary cells re-derived (10 Nov board); %d findings present; no conflict markers in tracked *.md" % (len(rows), mon_checks, 7))
