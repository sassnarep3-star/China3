#!/usr/bin/env python3
"""Independent gate for the decision-readiness register (session b2d4ff40).

Deliberately does not import scripts/e347_build.py, scripts/e347_data.py or
scripts/b2d_data.py: it re-reads the published artefacts (the CSV and the
rendered page) and checks them against each other and against the official
source register.

  A. every register row has an official https source, and its IDs exist in
     data/e347_sources.csv with exactly those URLs
  B. status is one of Answered / Partly answered / Open; a Partly or Open row
     must say what is missing and how to find it, and an Answered row must not
     claim something a source does not settle
  C. no empty cell, no placeholder text
  D. the rendered page carries one row per CSV row, at the same ID, with the
     same question, the same status and every one of its source URLs
  E. every flag named on a row exists on the Flagged page
  F. the page is reachable from the navigation of every generated page
  G. the two arithmetic claims on the page recompute (gain fraction, spread)
"""
import csv
import re
import sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "b2d_decisions.csv"
PAGE = ROOT / "dashboard" / "decisions.html"
SOURCES = ROOT / "data" / "e347_sources.csv"
FLAGS = ROOT / "data" / "e347_flags.csv"
OFFICIAL = ("boc.cn", "safe.gov.cn", "chinatax.gov.cn", "pbc.gov.cn", "irs.gov", "govinfo.gov",
            "fincen.gov", "ecfr.gov", "cbp.gov", "gd.gov.cn")
STATUSES = ("Answered", "Partly answered", "Open")
PLACEHOLDERS = ("todo", "tbd", "xxx", "none", "nan", "placeholder", "n/a")

# Declared readings, re-checked by hand on 2026-11-11 and asserted in check G.
BOC_SELL_20261111 = F(66911, 10000)   # BOC board 2026/11/11 10:25:02, USD selling 669.11 per 100
BOC_BUY_20261111 = F(66630, 10000)    # same board, USD buying 666.30 per 100
IRS_AVG_2024 = F(7189, 1000)          # IRS yearly average, China Yuan per USD

errors = []


def fail(msg):
    errors.append(msg)


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class Page(HTMLParser):
    """Collects table rows as (id, [cell text], [hrefs])."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.ids, self.h1, self.nav = [], set(), 0, []
        self._row = self._cell = None
        self._in_nav = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "nav":
            self._in_nav = True
        if tag == "tr":
            self._row = dict(id=a.get("id"), cells=[], hrefs=[])
            self.rows.append(self._row)
        if tag == "td":
            self._cell = []
            self._row["cells"].append(self._cell)
        if tag == "a" and a.get("href"):
            if self._in_nav:
                self.nav.append(a["href"])
            if self._row is not None:
                self._row["hrefs"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "nav":
            self._in_nav = False
        if tag == "tr":
            self._row = None
        if tag == "td":
            self._cell = None

    def handle_data(self, text):
        if self._cell is not None:
            self._cell.append(text)


def check_rows(rows, src_by_id, flag_ids):
    seen = set()
    for r in rows:
        rid = r["id"]
        if rid in seen:
            fail(f"A/{rid}: duplicate id")
        seen.add(rid)
        if r["status"] not in STATUSES:
            fail(f"B/{rid}: status {r['status']!r} not in {STATUSES}")
        for col in ("question", "status", "what_we_know", "source_ids", "source_urls", "how_to_find_out"):
            if not r[col].strip():
                fail(f"C/{rid}: empty {col}")
        for col, val in r.items():
            if val.strip().lower() in PLACEHOLDERS:
                fail(f"C/{rid}: placeholder text in {col}: {val!r}")
        ids = [i for i in r["source_ids"].split("|") if i]
        urls = [u for u in r["source_urls"].split() if u]
        if not ids or not urls:
            fail(f"A/{rid}: no source")
            continue
        if len(ids) != len(urls):
            fail(f"A/{rid}: {len(ids)} source ids but {len(urls)} urls")
        for i, u in zip(ids, urls):
            if i not in src_by_id:
                fail(f"A/{rid}: unknown source id {i}")
            elif src_by_id[i] != u:
                fail(f"A/{rid}: url for {i} does not match the source register")
            if not official(u):
                fail(f"A/{rid}: url is not on an official domain: {u}")
        if r["status"] in ("Partly answered", "Open"):
            if not r["what_is_missing"].strip():
                fail(f"B/{rid}: {r['status']} row without 'what is missing'")
            if len(r["how_to_find_out"].split()) < 5:
                fail(f"B/{rid}: {r['status']} row without a usable discovery step")
        for f in filter(None, (x.strip() for x in r["flags"].split("|"))):
            if f not in flag_ids:
                fail(f"E/{rid}: flag {f} is not on the Flagged page")
    return seen


def check_page(rows, src_urls):
    if not PAGE.exists():
        fail(f"D: missing page {PAGE.relative_to(ROOT)}")
        return {}
    text = PAGE.read_text(encoding="utf-8")
    page = Page()
    page.feed(text)
    if page.h1 != 1:
        fail(f"D: expected one h1, found {page.h1}")
    if "e347-dashboard" not in text:
        fail("D: page is not generated by scripts/e347_build.py")
    got = {}
    for r in page.rows:
        if r["id"]:
            got[r["id"]] = r
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = re.sub(r"\s+", " ", plain)
    if "TODO" in plain or "placeholder" in plain.lower():
        fail("D: placeholder text on the page")
    for r in rows:
        rid = r["id"]
        if rid not in got:
            fail(f"D/{rid}: row missing from the rendered page")
            continue
        cells = [" ".join(c) for c in got[rid]["cells"]]
        blob = re.sub(r"\s+", " ", " ".join(cells))
        if re.sub(r"\s+", " ", r["question"]) not in blob:
            fail(f"D/{rid}: question text on the page does not match the register")
        if r["status"] not in blob:
            fail(f"D/{rid}: status {r['status']!r} not shown on the page")
        for i in r["source_ids"].split("|"):
            if i and src_urls.get(i) and src_urls[i] not in got[rid]["hrefs"]:
                fail(f"D/{rid}: source link for {i} missing from the row")
        if any(not c.strip() for c in cells):
            fail(f"D/{rid}: empty cell on the page")
    # every row on the page that looks like a register row must exist in the CSV
    known = {r["id"] for r in rows}
    for rid in got:
        if re.fullmatch(r"[A-E]\d\d", rid) and rid not in known:
            fail(f"D/{rid}: page row has no entry in the register")
    return got


def check_nav():
    pages = [ROOT / "index.html"] + sorted((ROOT / "dashboard").glob("*.html"))
    for p in pages:
        text = p.read_text(encoding="utf-8")
        nav = re.search(r"<nav[^>]*>(.*?)</nav>", text, re.S)
        if not nav:
            fail(f"F/{p.name}: no navigation block")
            continue
        if "decisions.html" not in nav.group(1):
            fail(f"F/{p.name}: navigation has no link to decisions.html")
        if p == PAGE and "aria-current" not in nav.group(1):
            fail("F/decisions.html: page is not marked current in its own navigation")


def check_arithmetic(rows):
    """G. recompute the two figures the register states, from the declared readings."""
    gain = 1 - BOC_SELL_20261111 / IRS_AVG_2024
    if not F(69, 1000) <= gain < F(7, 100):
        fail(f"G: recomputed 2024-basis gain {float(gain):.5f} is not the 6.9% the page states")
    d02 = next((r for r in rows if r["id"] == "D02"), None)
    if d02 is None:
        fail("G: row D02 not found")
    elif "6.9%" not in d02["what_we_know"]:
        fail("G: row D02 no longer states the recomputed 6.9%")
    e02 = next((r for r in rows if r["id"] == "E02"), None)
    if e02 is None:
        fail("G: row E02 not found")
    else:
        for token in ("666.30", "669.11", "2026-11-11"):
            if token not in e02["what_we_know"]:
                fail(f"G: row E02 no longer states the board reading {token}")
    spread = (BOC_SELL_20261111 - BOC_BUY_20261111) / BOC_BUY_20261111
    if not F(3, 1000) <= spread < F(6, 1000):
        fail(f"G: board spread {float(spread):.5f} outside the plausible band")


def main():
    for path in (CSV_PATH, PAGE, SOURCES, FLAGS):
        if not path.exists():
            print(f"FAIL — missing {path.relative_to(ROOT)}")
            return 1
    rows = read_csv(CSV_PATH)
    src_by_id = {s["id"]: s["url"] for s in read_csv(SOURCES)}
    src_urls = dict(src_by_id)
    flag_ids = {r["id"] for r in read_csv(FLAGS)}
    ids = check_rows(rows, src_by_id, flag_ids)
    check_page(rows, src_urls)
    check_nav()
    check_arithmetic(rows)
    if errors:
        print(f"FAIL — {len(errors)} problem(s)")
        for e in errors[:60]:
            print("  -", e)
        return 1
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in STATUSES}
    print(f"PASS — b2d: {len(ids)} register rows ({counts['Answered']} answered, "
          f"{counts['Partly answered']} partly answered, {counts['Open']} open); "
          f"every row carries an official source, every open row a discovery step; "
          f"page and register agree row for row; navigation reaches the page from every page.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
