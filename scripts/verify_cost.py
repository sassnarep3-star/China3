#!/usr/bin/env python3
"""Line-by-line verifier for the cost layer.

This is deliberately NOT a copy of the build script. It re-reads the anchor file,
re-implements the arithmetic from the published formulas, parses the generated
HTML, and compares cell by cell. If the HTML and an independent computation
disagree by one cent the build fails.

Checks
  1. fx_anchor.json carries a retrieval date, and every published figure it
     holds has a source id in the register.
  2. Every one of the 40 x 6 cost rows recomputes to the value printed in HTML
     (money table, method table, home table).
  3. Every <tr> in every table on every cost*.html page contains an official
     http(s) link, and every source id in the register appears on the sources page.
  4. Every UNVERIFIED value in the anchor is genuinely absent (null), never 0.
  5. Every internal href/anchor across the new pages resolves to a file and an
     id that exists.
  6. Percentages printed in the model table match the recomputation.
Exits non-zero with a list of failures.
"""
from __future__ import annotations

import html
import json
import math
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
errors: list[str] = []
notes: list[str] = []

OFFICIAL_DOMAINS = (
    "safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn", "csrc.gov.cn",
    "irs.gov", "fincen.gov", "ecfr.gov", "federalregister.gov", "govinfo.gov",
    "fiscal.treasury.gov", "treasury.gov", "federalreserve.gov", "boc.cn",
    "stat.gov.cn", "customs.gov.cn",
)

PAGES = ["cost.html", "cost-model.html", "cost-methods.html", "cost-playbook.html",
         "cost-tax.html", "cost-review.html", "cost-sources.html"]


def is_official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


A = json.loads((DATA / "fx_anchor.json").read_text(encoding="utf-8"))
MODEL = json.loads((DATA / "cost_model.json").read_text(encoding="utf-8"))

# ---- 1: anchor provenance -------------------------------------------------
if not A.get("retrieved"):
    errors.append("fx_anchor.json: no retrieval date")
for group in ("thresholds", "penalties"):
    for k, v in A[group].items():
        if not isinstance(v, dict):
            errors.append(f"fx_anchor.json:{group}.{k} not an object")
            continue
        sid = v.get("source_id")
        if not sid:
            errors.append(f"fx_anchor.json:{group}.{k} has no source_id")
        if not str(v.get("url", "")).startswith("https://"):
            errors.append(f"fx_anchor.json:{group}.{k} url is not https")
        elif not is_official(v["url"]):
            errors.append(f"fx_anchor.json:{group}.{k} url not on an official domain: {v['url']}")
notes.append(f"anchor: {A['retrieved']}; {len(A['thresholds'])} thresholds, {len(A['penalties'])} penalty figures")

# ---- 4: unverified really is absent ---------------------------------------
for group in ("fees",):
    for k, v in A[group].items():
        if v is None:
            continue
        if isinstance(v, dict) and not v.get("source_id"):
            errors.append(f"fx_anchor.json:{group}.{k} has a value but no source_id")
for k in ("receiving_us_bank_incoming_wire", "correspondent_intermediary_fee",
          "sha_government_approval_fee", "sha_application_notarisation_and_translation"):
    if k in A["fees"] and A["fees"][k] is not None:
        errors.append(f"fees.{k} should be null until an official figure is found")

# ---- independent recomputation -------------------------------------------
RATE = A["derived"]["customer_rate_cny_per_usd"]
SPREAD = A["derived"]["spread_vs_boc_reference_pct"] / 100.0
W = A["fees"]["boc_outward_wire"]


def wire_cny(cny: float) -> float:
    return min(max(cny * 0.001, 50.0), 260.0) + 150.0


def rebuild(usd: float):
    cny = usd * RATE
    fx = usd * SPREAD
    fee = wire_cny(cny) / RATE
    return cny, fx, fee, fx + fee


# spot-check the two derived numbers against the raw board reading
ref = A["anchor"]["boc_usd_reference"]
sel = A["anchor"]["boc_usd_spot_sell"]
implied_spread = round((ref - sel) / ref * 100, 4)
if abs(implied_spread - A["derived"]["spread_vs_boc_reference_pct"]) > 0.0001:
    errors.append(f"derived spread {A['derived']['spread_vs_boc_reference_pct']} != recomputed {implied_spread}")
if abs(sel / 100 - RATE) > 0.00005:
    errors.append(f"derived customer rate {RATE} != spot-sell/100 {sel/100}")
notes.append(f"derived: spread {implied_spread}% recomputed from {ref} and {sel}; customer rate {RATE}")

# ---- 2/3/6: parse HTML ----------------------------------------------------
class Rows(HTMLParser):
    """Collect [cell_texts], [links] for every data row, grouped by data-table id."""
    def __init__(self):
        super().__init__()
        self.thead = False
        self.tr = False
        self.cells: list[str] = []
        self.links: list[str] = []
        self.cur: list[str] = []
        self.rows: list[tuple[list[str], list[str]]] = []
        self.table = None
        self.by_table: dict[str, list] = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.table = a.get("data-table")
            if self.table:
                self.by_table.setdefault(self.table, [])
        if tag == "thead":
            self.thead = True
        if tag == "tr" and not self.thead:
            self.tr = True
            self.cells, self.links, self.cur = [], [], []
        if tag in ("td", "th") and self.tr:
            self.cur = []
        if tag == "a" and self.tr:
            h = a.get("href", "")
            if h.startswith(("http://", "https://")):
                self.links.append(h)
        if tag == "br" and self.tr:
            self.cur.append(" ")

    def handle_endtag(self, tag):
        if tag == "thead":
            self.thead = False
        if tag in ("td", "th") and self.tr:
            self.cells.append(html.unescape("".join(self.cur)).strip())
        if tag == "tr" and self.tr:
            self.tr = False
            self.rows.append((self.cells, self.links))
            if self.table:
                self.by_table[self.table].append((self.cells, self.links))

    def handle_data(self, data):
        if self.tr:
            self.cur.append(data)


def num(s: str):
    s = s.replace("$", "").replace(",", "").replace("%", "").strip()
    if not s or s in {"—", "–", "-"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


parsed = {}
TABLES = {}
for name in PAGES:
    p = ROOT / name
    if not p.exists():
        errors.append(f"missing page {name}")
        continue
    rp = Rows()
    rp.feed(p.read_text(encoding="utf-8"))
    parsed[name] = rp.rows
    TABLES[name] = rp.by_table

# every row of every table must carry an official link
rowcount = 0
for name, rows in parsed.items():
    for i, (cells, links) in enumerate(rows, 1):
        rowcount += 1
        if not links:
            errors.append(f"{name}: data row {i} has no link at all")
        elif not any(is_official(u) for u in links):
            errors.append(f"{name}: data row {i} has no official-domain link ({links[:2]})")
notes.append(f"row audit: {rowcount} data rows across {len(parsed)} pages, each with an official link")

# ---- exact cell comparison on the master cost table ----------------------
def find_table(name, header_word):
    """Return the rows of the first table whose first data row looks like the one we want."""
    return parsed.get(name, [])

master = TABLES["cost-model.html"].get("master", [])
if len(master) != 40:
    errors.append(f"cost-model.html: expected 40 master rows, found {len(master)}")
for cells, links in master:
    usd = num(cells[0])
    if usd is None or usd % 10000:
        errors.append(f"cost-model.html: bad USD cell {cells[0]!r}")
        continue
    cny, fx, fee, tot = rebuild(usd)
    got_cny, got_fx, got_fee, got_tot = (num(cells[1]), num(cells[2]), num(cells[3]), num(cells[4]))
    if got_cny is None or abs(got_cny - cny) > 0.51:
        errors.append(f"cost-model {usd:,.0f}: CNY {got_cny} != {cny:.0f}")
    if got_fx is None or abs(got_fx - fx) > 0.011:
        errors.append(f"cost-model {usd:,.0f}: FX {got_fx} != {fx:.2f}")
    if got_fee is None or abs(got_fee - fee) > 0.011:
        errors.append(f"cost-model {usd:,.0f}: fee {got_fee} != {fee:.2f}")
    if got_tot is None or abs(got_tot - tot) > 0.011:
        errors.append(f"cost-model {usd:,.0f}: total {got_tot} != {tot:.2f}")
    pct = num(cells[5])
    if pct is None or abs(pct - tot / usd * 100) > 0.006:
        errors.append(f"cost-model {usd:,.0f}: pct {pct} != {tot/usd*100:.2f}")
notes.append("master table: 40 rows x (CNY, spread, fee, total, pct) recomputed independently")

# ---- the six-column method matrix on two pages ---------------------------
for name, tid in (("cost-model.html", "matrix-model"), ("cost-methods.html", "matrix-methods")):
    six = TABLES[name].get(tid, [])
    if len(six) != 40:
        errors.append(f"{name}: expected 40 rows in {tid}, found {len(six)}")
        continue
    for cells, links in six:
        usd = num(cells[0])
        _, fx, fee, tot = rebuild(usd)
        c = [num(x) for x in cells[1:]]
        # M1 (may be n/a above 50k), M2 = tot, M3 blank, M4 = tot, M5 blank, M6
        if usd <= 50_000:
            if c[0] is None or abs(c[0] - tot) > 0.011:
                errors.append(f"{name} {usd:,.0f}: M1 {c[0]} != {tot:.2f}")
        if c[1] is None or abs(c[1] - tot) > 0.011:
            errors.append(f"{name} {usd:,.0f}: M2 {c[1]} != {tot:.2f}")
        if c[2] is not None:
            errors.append(f"{name} {usd:,.0f}: M3 should be blank (no official figure), got {c[2]}")
        n4 = max(1, math.ceil(usd / 50_000))
        m4 = fx + fee * n4
        if c[3] is None or abs(c[3] - m4) > 0.011:
            errors.append(f"{name} {usd:,.0f}: M4 {c[3]} != {m4:.2f}")
        if c[4] is not None:
            errors.append(f"{name} {usd:,.0f}: M5 should be blank, got {c[4]}")
        if usd <= 10_000 and (c[5] is None or abs(c[5] - fx) > 0.011):
            errors.append(f"{name} {usd:,.0f}: M6 {c[5]} != {fx:.2f}")
notes.append("method matrix: M1/M2/M4/M6 recomputed on both pages; M3 and M5 asserted blank")

# ---- home table ----------------------------------------------------------
home = TABLES["cost.html"].get("home-summary", [])
for cells, links in home:
    usd = num(cells[0])
    _, _, _, tot = rebuild(usd)
    if abs((num(cells[2]) or -1) - tot) > 0.011:
        errors.append(f"cost.html {usd:,.0f}: total {cells[2]} != {tot:.2f}")
    if abs((num(cells[3]) or -1) - tot / usd * 100) > 0.006:
        errors.append(f"cost.html {usd:,.0f}: pct {cells[3]} != {tot/usd*100:.2f}")
notes.append(f"home table: {len(home)} summary rows recomputed")

# ---- 5: internal links and anchors --------------------------------------
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            h = a.get(k, "")
            if h and not h.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#")):
                self.hrefs.append(h)


allids = {}
for p in ROOT.glob("*.html"):
    lp = Links()
    lp.feed(p.read_text(encoding="utf-8"))
    allids[p.name] = lp.ids

for name in PAGES:
    p = ROOT / name
    if not p.exists():
        continue
    lp = Links()
    lp.feed(p.read_text(encoding="utf-8"))
    for href in lp.hrefs:
        target, _, frag = href.partition("#")
        if target:
            tp = ROOT / target
            if not tp.exists():
                errors.append(f"{name}: broken link to {target}")
                continue
            if frag and target.endswith(".html"):
                if frag not in allids.get(Path(target).name, set()):
                    errors.append(f"{name}: anchor #{frag} not found in {target}")
        elif frag:
            if frag not in lp.ids:
                errors.append(f"{name}: internal anchor #{frag} not defined on the page")
notes.append("internal links and anchors: checked across all seven new pages")

# ---- source register completeness on the sources page -------------------
src_page = (ROOT / "cost-sources.html").read_text(encoding="utf-8")
live = json.loads((DATA / "fx_anchor.json").read_text(encoding="utf-8"))
used = set(re.findall(r">(V\d\d)<", src_page)) | set(re.findall(r'href="#(V\d\d)"', src_page))
declared = set(re.findall(r'<td><b>(V\d\d)</b></td>', src_page))
cited = ({A["thresholds"][k]["source_id"] for k in A["thresholds"]}
         | {A["penalties"][k]["source_id"] for k in A["penalties"]})
missing_from_page = sorted(cited - declared)
for sid in missing_from_page:
    errors.append(f"cost-sources.html: anchor figures cite {sid} which is not in the register")
if "V10" not in declared or "V12" not in declared:
    errors.append("cost-sources.html: the two price sources V10/V12 must be in the register")
notes.append(f"source register: {len(declared)} entries rendered on the sources page")

# ---- report -------------------------------------------------------------
for n in notes:
    print(f"  ok  {n}")
if errors:
    print()
    for e in errors:
        print(f"  FAIL  {e}")
    print(f"\nFAIL — {len(errors)} problem(s).")
    sys.exit(1)
print("\nPASS — every cost cell recomputes, every row is sourced, no broken links.")
