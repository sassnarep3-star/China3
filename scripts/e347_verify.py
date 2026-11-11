#!/usr/bin/env python3
"""Independent checks for the e347 dashboard. Does not import the cost engine.

  1. every cost row in data/e347_costs.csv is recomputed from the raw board figures with exact fractions
  2. every row of every data table carries a link to an official domain
  3. every blank marker sits in a row that links to an existing flag
  4. no data cell is empty
  5. every local link and anchor resolves; every external link is on the allowlist
  6. the root index.html is the e347 landing page and every page has the same navigation
  7. every source, method, step, fact and flag row in the CSVs has an official URL
"""
import csv
import math
import re
import sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
PAGES = [ROOT / "index.html"] + [ROOT / "dashboard" / f"{n}.html" for n in
                                 ("decisions", "methods", "costs", "steps", "tax", "flagged", "sources", "archive")]
OFFICIAL = ("boc.cn", "safe.gov.cn", "chinatax.gov.cn", "pbc.gov.cn", "irs.gov", "govinfo.gov",
            "fincen.gov", "ecfr.gov", "cbp.gov", "gd.gov.cn")
REPO_HOST = "github.com"
errors = []


def fail(msg):
    errors.append(msg)


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def rows(name):
    with (ROOT / "data" / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ------------------------------------------------------------------ 1. arithmetic
BID, ASK = F(66571, 10000), F(66851, 10000)   # BOC board 665.71 / 668.51 per 100 USD
MID = (BID + ASK) / 2
IRS = {"2021": F(6452, 1000), "2022": F(6730, 1000), "2023": F(7075, 1000), "2024": F(7189, 1000), "2025": F(7129, 1000)}


def cents(x):
    return f"{math.floor(x * 100 + F(1, 2)) / 100:.2f}"


def wire_cny(usd):
    return min(F(260), max(F(50), usd * ASK / 1000)) + 150


def expect(model, usd):
    """Return (spread, fee, tax, total, units, years) recomputed independently; None where blank."""
    if model in ("fx_wire", "property"):
        s, w = usd * (ASK - MID) / ASK, wire_cny(usd) / ASK
        return s, w, None, s + w, 1, 1
    if model == "wire_only":
        w = wire_cny(usd) / ASK
        return None, w, None, w, 1, 1
    if model == "quota":
        n_full, rem = divmod(usd, 50000)
        fee = n_full * wire_cny(F(50000)) / ASK + (wire_cny(rem) / ASK if rem else 0)
        s = usd * (ASK - MID) / ASK
        n = int(n_full) + (1 if rem else 0)
        return s, fee, None, s + fee, n, n
    if model == "atm":
        cny = usd * ASK
        n_full = cny // 10000
        rem = cny - n_full * 10000
        fee = n_full * min(F(112), 12 + F(10000) / 100) + (min(F(112), 12 + rem / 100) if rem else 0)
        return None, fee / ASK, None, fee / ASK, int(n_full) + (1 if rem else 0), math.ceil(cny / 100000)
    if model == "cash":
        s = usd * (ASK - MID) / ASK
        return s, None, None, s, math.ceil(usd / 5000), None
    if model == "dividend":
        tax = usd / 5
        net = usd - tax
        s, w = net * (ASK - MID) / ASK, wire_cny(net) / ASK
        return s, w, tax, tax + s + w, 1, 1
    return None, None, None, None, None, None


def check_costs():
    grid = rows("e347_costs.csv")
    by_method = {}
    for r in grid:
        by_method.setdefault(r["method_id"], []).append(r)
        usd = F(int(r["amount_usd"]))
        s, w, t, total, units, years = expect(r["model"], usd)
        for col, val in (("spread_usd", s), ("fee_usd", w), ("tax_usd", t), ("known_cost_usd", total)):
            want = "" if val is None else cents(val)
            if r[col] != want:
                fail(f"cost {r['method_id']} {r['amount_usd']} {col}: file {r[col]!r}, recomputed {want!r}")
        if (r["units"] or None) != (str(units) if units is not None else None):
            fail(f"cost {r['method_id']} {r['amount_usd']} units: {r['units']!r} vs {units!r}")
        if (r["calendar_years"] or None) != (str(years) if years is not None else None):
            fail(f"cost {r['method_id']} {r['amount_usd']} years: {r['calendar_years']!r} vs {years!r}")
        if not r["source_urls"] or not all(official(u) for u in r["source_urls"].split()):
            fail(f"cost {r['method_id']} {r['amount_usd']}: missing or non-official source URL")
        if r["known_cost_usd"] == "" and not r["not_included_flags"]:
            fail(f"cost {r['method_id']} {r['amount_usd']}: blank cost without a flag")
    for mid, rs in by_method.items():
        if [int(r["amount_usd"]) for r in rs] != list(range(10000, 400001, 10000)):
            fail(f"cost {mid}: not the 40 increments from 10,000 to 400,000")
    for r in rows("e347_fx_gain.csv"):
        usd = F(int(r["amount_usd"]))
        for y, avg in IRS.items():
            want = cents(usd - usd * ASK / avg) if usd - usd * ASK / avg >= 0 else "-" + cents(-(usd - usd * ASK / avg))
            if r[f"gain_if_acquired_{y}_usd"] != want:
                fail(f"fx gain {r['amount_usd']} {y}: file {r[f'gain_if_acquired_{y}_usd']}, recomputed {want}")
    return len(grid), len(by_method)


# ------------------------------------------------------------------ 2-6. pages
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.tables = set(), [], []
        self.h1 = 0
        self.nav = []
        self.generator = None
        self._table = self._row = self._cell = None
        self._in_nav = self._in_blank = self._in_head = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name") == "generator":
            self.generator = a.get("content")
        if tag == "h1":
            self.h1 += 1
        if tag == "nav":
            self._in_nav = True
        if tag == "table":
            self._table = dict(kind=a.get("data-kind", ""), rows=[])
            self.tables.append(self._table)
        if tag == "thead":
            self._in_head = True
        if tag == "tr" and self._table is not None and not self._in_head:
            self._row = dict(cells=[], links=[], blanks=0)
            self._table["rows"].append(self._row)
        if tag == "td" and self._row is not None:
            self._cell = []
            self._row["cells"].append(self._cell)
        if tag == "span" and "blank" in (a.get("class") or "").split() and self._row is not None:
            self._row["blanks"] += 1
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self._in_nav:
                self.nav.append(a["href"])
            if self._row is not None:
                self._row["links"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "nav":
            self._in_nav = False
        if tag == "thead":
            self._in_head = False
        if tag == "tr":
            self._row = None
        if tag == "td":
            self._cell = None
        if tag == "table":
            self._table = None

    def handle_data(self, text):
        if self._cell is not None:
            self._cell.append(text)


def check_pages():
    parsed = {}
    for p in PAGES:
        if not p.exists():
            fail(f"missing page {p.relative_to(ROOT)}")
            continue
        page = Page()
        page.feed(p.read_text(encoding="utf-8"))
        parsed[p] = page
    flag_ids = parsed[ROOT / "dashboard" / "flagged.html"].ids if (ROOT / "dashboard" / "flagged.html") in parsed else set()
    n_rows = n_links = n_blank = 0
    for p, page in parsed.items():
        rel = p.relative_to(ROOT)
        if page.generator != "e347-dashboard":
            fail(f"{rel}: not an e347 page (generator meta missing). If index.html was overwritten by scripts/build_dashboard.py, "
                 "restore it with python3 scripts/e347_build.py; the legacy landing page is legacy-index.html")
        if page.h1 != 1:
            fail(f"{rel}: expected one h1, found {page.h1}")
        if len(page.nav) != 11:
            fail(f"{rel}: navigation has {len(page.nav)} entries, expected 11")
        for t in page.tables:
            if t["kind"] not in ("data", "repo", "nav"):
                fail(f"{rel}: table without data-kind")
            for r in t["rows"]:
                n_rows += 1
                ext = [l for l in r["links"] if l.startswith("http")]
                local = [l for l in r["links"] if not l.startswith("http")]
                if t["kind"] == "data" and not any(official(l) for l in ext):
                    fail(f"{rel}: data row without an official source link: {''.join(r['cells'][0])[:60]!r}")
                if t["kind"] == "repo" and not ext:
                    fail(f"{rel}: repository row without a link: {''.join(r['cells'][0])[:60]!r}")
                if t["kind"] == "nav" and not local:
                    fail(f"{rel}: navigation row without a local link")
                for c in r["cells"]:
                    if not "".join(c).strip():
                        fail(f"{rel}: empty cell in row {''.join(r['cells'][0])[:60]!r}")
                if r["blanks"]:
                    n_blank += r["blanks"]
                    refs = [l.split("#", 1)[1] for l in local if "flagged.html#" in l]
                    if not refs:
                        fail(f"{rel}: blank value without a flag link in row {''.join(r['cells'][0])[:60]!r}")
                    for ref in refs:
                        if ref not in flag_ids:
                            fail(f"{rel}: flag {ref} does not exist on the Flagged page")
        for href in page.links:
            n_links += 1
            if href.startswith("http"):
                host = (urlparse(href).hostname or "").lower()
                if not official(href) and host != REPO_HOST:
                    fail(f"{rel}: external link outside the allowlist: {href}")
                continue
            if href.startswith(("mailto:", "#")):
                if href.startswith("#") and href[1:] not in page.ids:
                    fail(f"{rel}: anchor {href} not found")
                continue
            target, _, anchor = href.partition("#")
            dest = (p.parent / unquote(target)).resolve()
            if not dest.exists():
                fail(f"{rel}: broken local link {href}")
            elif anchor and dest in parsed and anchor not in parsed[dest].ids:
                fail(f"{rel}: anchor #{anchor} not found in {target}")
    css = ROOT / "dashboard" / "site.css"
    if not css.exists() or css.stat().st_size == 0:
        fail("dashboard/site.css missing")
    return len(parsed), n_rows, n_links, n_blank


# ------------------------------------------------------------------ 7. data files
def check_data():
    src = rows("e347_sources.csv")
    ids = {s["id"] for s in src}
    for s in src:
        if not official(s["url"]):
            fail(f"source {s['id']}: URL is not on an official domain")
        if s["how_read"] not in ("direct", "excerpt") or not s["what_it_establishes"].strip():
            fail(f"source {s['id']}: missing how_read or content")
    n = len(src)
    for name, key in (("e347_methods.csv", "id"), ("e347_steps.csv", "method_id"), ("e347_facts.csv", "id"), ("e347_flags.csv", "id")):
        for r in rows(name):
            n += 1
            got = [i for i in r["source_ids"].split("|") if i]
            if not got or not set(got) <= ids:
                fail(f"{name} {r[key]}: missing or unknown source id")
            if not r["source_urls"] or not all(official(u) for u in r["source_urls"].split()):
                fail(f"{name} {r[key]}: missing or non-official source URL")
    for r in rows("e347_facts.csv"):
        if not r["rate_or_amount"] and not r["flags"]:
            fail(f"e347_facts.csv {r['id']}: blank value without a flag")
    flag_ids = {r["id"] for r in rows("e347_flags.csv")}
    for name in ("e347_methods.csv", "e347_facts.csv"):
        for r in rows(name):
            for f in filter(None, r["flags"].split("|")):
                if f not in flag_ids:
                    fail(f"{name}: unknown flag {f}")
    return n


def main():
    n_cost, n_methods = check_costs()
    n_pages, n_rows, n_links, n_blank = check_pages()
    n_data = check_data()
    if errors:
        print(f"FAIL — {len(errors)} problem(s)")
        for e in errors[:60]:
            print("  -", e)
        return 1
    print(f"PASS — e347: {n_cost} cost rows over {n_methods} routes recomputed exactly; {n_pages} pages, {n_rows} table rows "
          f"sourced, {n_blank} blank values all flagged, {n_links} links resolved, {n_data} data rows with official URLs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
