#!/usr/bin/env python3
"""Validate local links, source register entries, and citations in site tables."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["index.html", "routes.html", "taxes.html", "sources.html", "review.html"]
OFFICIAL_HOSTS = ("safe.gov.cn", "chinatax.gov.cn", "pbc.gov.cn", "irs.gov", "fincen.gov")

class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.table_depth = 0
        self.row_depth = 0
        self.cell_depth = 0
        self.current_row = None
        self.current_row_has_data = False
        self.rows = []
        self.source_items = []
        self.current_source = None
        self.current_source_links = []
        self.source_entry_links = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.current_row is not None:
                self.current_row.append(a["href"])
            if self.current_source is not None:
                self.current_source_links.append(a["href"])
        if tag == "table":
            self.table_depth += 1
        if tag == "tr" and self.table_depth:
            self.row_depth += 1
            self.current_row = []
            self.current_row_has_data = False
        if tag in ("td", "th") and self.current_row is not None:
            if tag == "td":
                self.current_row_has_data = True
            self.cell_depth += 1
        if tag == "article" and a.get("class") == "source-item":
            self.current_source = a.get("id", "")
            self.source_items.append(self.current_source)
            self.current_source_links = []

    def handle_endtag(self, tag):
        if tag == "tr" and self.table_depth:
            if self.current_row is not None and self.current_row_has_data:
                self.rows.append(self.current_row)
            self.current_row = None
            self.current_row_has_data = False
            self.row_depth = max(0, self.row_depth - 1)
        if tag == "table":
            self.table_depth = max(0, self.table_depth - 1)
        if tag in ("td", "th") and self.current_row is not None:
            self.cell_depth = max(0, self.cell_depth - 1)
        if tag == "article" and self.current_source is not None:
            self.source_entry_links[self.current_source] = list(self.current_source_links)
            self.current_source = None
            self.current_source_links = []

def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1

def main():
    missing = [p for p in PAGES if not (ROOT / p).is_file()]
    if missing:
        return fail("missing required pages: " + ", ".join(missing))

    scans = {}
    errors = []
    for page in PAGES:
        parser = Scan()
        parser.feed((ROOT / page).read_text(encoding="utf-8"))
        scans[page] = parser

    # Validate all internal files and fragment IDs in generated pages.
    for page, parser in scans.items():
        for href in parser.links:
            u = urlparse(href)
            if u.scheme or u.netloc or href.startswith("mailto:") or href.startswith("javascript:"):
                if u.scheme in ("http", "https") and u.hostname and not any(
                    u.hostname == host or u.hostname.endswith("." + host) for host in OFFICIAL_HOSTS
                ):
                    errors.append(f"{page}: non-official external link: {href}")
                continue
            target_rel = unquote(u.path) if u.path else page
            target = (ROOT / target_rel).resolve()
            if not target.exists():
                errors.append(f"{page}: missing local target {href}")
                continue
            if u.fragment and target.suffix.lower() == ".html":
                target_page = target.relative_to(ROOT).as_posix()
                target_scan = scans.get(target_page)
                if target_scan is None:
                    p = Scan(); p.feed(target.read_text(encoding="utf-8")); target_scan = p
                if unquote(u.fragment) not in target_scan.ids:
                    errors.append(f"{page}: fragment #{u.fragment} missing in {target_rel}")

    # Every actual body row in route, tax and review tables must link directly to an official source.
    for page in ("routes.html", "taxes.html", "review.html"):
        for number, row_links in enumerate(scans[page].rows, 1):
            official = []
            for href in row_links:
                u = urlparse(href)
                if u.scheme in ("http", "https") and u.hostname and any(
                    u.hostname == host or u.hostname.endswith("." + host) for host in OFFICIAL_HOSTS
                ):
                    official.append(href)
            if not official:
                errors.append(f"{page}: table row {number} has no direct official source link")

    # Sources are expected to be official primary-source hosts and unique IDs.
    ids = scans["sources.html"].source_items
    if len(ids) != 19:
        errors.append(f"sources.html: expected 19 source-register entries, found {len(ids)}")
    if len(ids) != len(set(ids)):
        errors.append("sources.html: duplicate source register IDs")
    for sid in ids:
        if not sid.startswith("S"):
            errors.append(f"sources.html: invalid source entry id {sid!r}")
        links = scans["sources.html"].source_entry_links.get(sid, [])
        official = []
        for href in links:
            u = urlparse(href)
            if u.scheme in ("http", "https") and u.hostname and any(
                u.hostname == host or u.hostname.endswith("." + host) for host in OFFICIAL_HOSTS
            ):
                official.append(href)
        if not official:
            errors.append(f"sources.html: {sid} has no direct official source link")

    # All cited S-numbers must resolve to a source register entry.
    source_ids = set(ids)
    for page, parser in scans.items():
        for href in parser.links:
            u = urlparse(href)
            if u.path == "sources.html" and u.fragment and u.fragment not in source_ids:
                errors.append(f"{page}: citation references unknown {u.fragment}")

    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        return 1
    print(f"OK: {len(PAGES)} required pages; local links/fragments resolve; all comparison/review table rows cite sources; {len(ids)} source entries registered.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
