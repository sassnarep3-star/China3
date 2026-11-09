#!/usr/bin/env python3
"""Line-by-line verification for the deep-research dashboard.

Checks performed:
  1. Every data row has a source_url on an official domain AND registered in sources.csv.
  2. Every source id used by a row resolves to the exact registered URL.
  3. UNVERIFIED rows have a deliberately blank value; VERIFIED rows have a value.
  4. Every generated HTML <tbody><tr> contains at least one official http(s) link.
  5. Generated HTML row counts match the CSV row counts.
  6. EVERY data row in EVERY table on EVERY deep-*.html page has an official link.
  7. Every local href/src in every root and docs/ HTML page resolves (broken-link check).
  8. Every flagged item id appears on the Flagged for Review page.
  9. Every source id in sources.csv appears on the deep sources page.
Exits non-zero on any failure. Other sessions' data/CI are checked by their own scripts.
"""
from __future__ import annotations

import csv
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
errors: list[str] = []
notes: list[str] = []

OFFICIAL_DOMAINS = (
    "safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn", "moj.gov.cn",
    "hncourt.gov.cn", "csrc.gov.cn", "boc.cn", "hkma.gov.hk", "gd.gov.cn",
    "hunan.gov.cn", "zjwy.gov.cn", "hangzhou.pbc.gov.cn", "xining.pbc.gov.cn",
    "guangzhou.pbc.gov.cn", "shanghai.chinatax.gov.cn", "fgk.chinatax.gov.cn",
    "irs.gov", "fincen.gov", "ecfr.gov", "federalregister.gov", "govinfo.gov",
    "home.treasury.gov", "treasury.gov", "taxpayeradvocate.irs.gov", "github.com",
    "boc.cn", "federalreserve.gov", "fiscal.treasury.gov",
)


def is_official(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


def read(name):
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


sources = {r["id"]: r for r in read("sources.csv")}
notes.append(f"source register: {len(sources)} official sources")

# --- 1/2/3: CSV row audit ---------------------------------------------------
table_specs = {
    "china_rules.csv": ("value", "china-table", "deep-china-rules.html"),
    "us_rules.csv": ("value", "us-table", "deep-us-tax.html"),
    "channels.csv": (None, "channels-table", "deep-channels.html"),
    "penalty.csv": ("verified_value", "penalty-table", "deep-penalty.html"),
    "findings.csv": (None, "findings-table", "deep-findings.html"),
    "flags.csv": (None, "flags-table", "deep-review.html"),
}
csv_counts = {}
for fname, (value_col, tid, _) in table_specs.items():
    rows = read(fname)
    csv_counts[tid] = len(rows)
    for r in rows:
        rid, sid, url, status = r["id"], r["source_id"], r["source_url"], r["status"]
        if not url.startswith(("https://", "http://")):
            errors.append(f"{fname}:{rid} missing source_url")
        if not is_official(url):
            errors.append(f"{fname}:{rid} source_url not on official domain: {url}")
        if sid not in sources:
            errors.append(f"{fname}:{rid} source_id {sid} not in sources.csv")
        elif sources[sid]["url"] != url:
            errors.append(f"{fname}:{rid} source_url != registered URL for {sid}")
        for extra in (r.get("extra_source_ids") or "").split():
            if extra not in sources:
                errors.append(f"{fname}:{rid} extra source id {extra} not registered")
        if status not in ("verified", "unverified", "needs review"):
            errors.append(f"{fname}:{rid} bad status {status}")
        if value_col:
            if status == "unverified" and r[value_col].strip() != "":
                errors.append(f"{fname}:{rid} UNVERIFIED but value column is not blank")
            if status == "verified" and r[value_col].strip() == "":
                errors.append(f"{fname}:{rid} VERIFIED but value column is blank")
    notes.append(f"{fname}: {len(rows)} rows audited")

for sid, r in sources.items():
    if not is_official(r["url"]):
        errors.append(f"sources.csv:{sid} URL not official: {r['url']}")

# --- 4/5: generated HTML table rows ----------------------------------------
class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.in_tr = False
        self.current_links: list[str] = []
        self.tables: dict[str, list[list[str]]] = {}
        self.current_table = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.current_table = a.get("data-table")
            if self.current_table:
                self.tables[self.current_table] = []
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.current_links = []
        if tag == "a" and self.in_tr:
            href = a.get("href", "")
            if href:
                self.current_links.append(href)

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_tr:
            self.in_tr = False
            if self.current_table:
                self.tables[self.current_table].append(self.current_links)
        if tag == "tbody":
            self.in_tbody = False


for fname, (_, tid, page_name) in table_specs.items():
    page = ROOT / page_name
    p = TableParser()
    p.feed(page.read_text(encoding="utf-8"))
    rows = p.tables.get(tid, [])
    if len(rows) != csv_counts[tid]:
        errors.append(f"{page.name}: {len(rows)} HTML rows != {csv_counts[tid]} CSV rows")
    for i, links in enumerate(rows, 1):
        if not any(h.startswith(("https://", "http://")) and is_official(h) for h in links):
            errors.append(f"{page.name}: table {tid} row {i} has no official source link")
    notes.append(f"{page.name}: {len(rows)} table rows, each with an official link")

# --- 6: EVERY data row in EVERY table on EVERY deep page -------------------
class AllTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_thead = False
        self.in_tr = False
        self.links: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "thead":
            self.in_thead = True
        if tag == "tr" and not self.in_thead:
            self.in_tr = True
            self.links = []
        if tag == "a" and self.in_tr:
            u = a.get("href", "")
            if u.startswith(("https://", "http://")):
                self.links.append(u)

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_tr:
            self.in_tr = False
            self.rows.append(self.links)
        if tag == "thead":
            self.in_thead = False


deep_pages = sorted(ROOT.glob("deep-*.html"))
all_rows = 0
for page in deep_pages:
    atp = AllTableParser()
    atp.feed(page.read_text(encoding="utf-8"))
    for i, links in enumerate(atp.rows, 1):
        all_rows += 1
        if not any(is_official(u) for u in links):
            errors.append(f"{page.name}: table row {i} has no official source link")
notes.append(f"all-page deep table audit: {len(deep_pages)} pages, {all_rows} data rows checked")

# --- 7: broken internal link check across root AND docs/ html --------------
class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ("href", "src"):
            h = a.get(key, "")
            if h and not h.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                self.hrefs.append(h.split("#", 1)[0])


pages = sorted(ROOT.glob("*.html")) + sorted((ROOT / "docs").glob("*.html"))
for page in pages:
    lp = LinkParser()
    lp.feed(page.read_text(encoding="utf-8"))
    for href in lp.hrefs:
        if href and not (page.parent / href).exists():
            errors.append(f"{page.relative_to(ROOT)}: broken local link -> {href}")
notes.append(f"broken-link check: {len(pages)} root + docs HTML pages scanned")

# --- 8: flagged items published --------------------------------------------
review = (ROOT / "deep-review.html").read_text(encoding="utf-8")
for r in read("flags.csv"):
    if r["id"] not in review:
        errors.append(f"deep-review.html missing flagged item {r['id']}")
notes.append("Flagged for Review page: all flagged item ids present")

# --- 9: source ids published -----------------------------------------------
sources_page = (ROOT / "deep-sources.html").read_text(encoding="utf-8")
missing_src = [sid for sid in sources if sid not in sources_page]
if missing_src:
    errors.append(f"deep-sources.html missing source ids: {', '.join(missing_src)}")
notes.append(f"Sources page: {len(sources) - len(missing_src)}/{len(sources)} source ids present")

# --- report -----------------------------------------------------------------
print("DEEP-RESEARCH VERIFICATION REPORT")
for n in notes:
    print("  ok  " + n)
if errors:
    print(f"\nFAILED with {len(errors)} error(s):")
    for e in errors:
        print("  !!  " + e)
    sys.exit(1)
print("\nPASS — all rows sourced, blanks flagged, no broken local links.")
