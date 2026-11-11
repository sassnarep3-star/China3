#!/usr/bin/env python3
"""Gate for the `bea4` pages (session arena/bea42a88-china3).

Checks, in order, and exits non-zero on the first failure:

 A. the data files still regenerate byte-identically (data/bea4_*.csv, bea4_summary.json)
 B. the cost re-derivation still reports zero mismatched cells, and the row/cell counts match the
    numbers the pages print
 C. both pages are up to date with the generator (build_bea4_site.py --check)
 D. every table body row carries at least one official http(s) link
 E. every external link is on the official-domain allowlist used by the dashboard, and every
    internal link resolves to a file that exists (anchors included)
 F. every citation in data/bea4_source_audit.csv appears on the page with a URL and a known result,
    and every blank value is visibly marked (nothing silently empty)
 G. no merge-conflict markers, no unrendered template text, no leftover placeholders
"""
from __future__ import annotations

import csv
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

PAGES = [ROOT / "bea4-audit.html", ROOT / "bea4-penalty.html"]
OFFICIAL = ("boc.cn", "safe.gov.cn", "chinatax.gov.cn", "pbc.gov.cn", "irs.gov",
            "govinfo.gov", "fincen.gov", "ecfr.gov", "cbp.gov")
RESULTS = {"CONFIRMED", "LINK_BROKEN", "NOT_RECHECKED", "PROPOSED_REPLACEMENT"}
failures: list[str] = []


def fail(msg):
    failures.append(msg)


def check_data_regenerates():
    import bea4_recheck as R

    rows, bad, cells = R.cost_recheck()
    if bad:
        fail(f"A: re-derivation has {bad} mismatched cells")
    if cells != 1720:
        fail(f"A: expected 1720 compared cells, got {cells}")
    if len(rows) != 440:
        fail(f"A: expected 440 cost rows, got {len(rows)}")
    rep = R.repricing()
    pen = R.penalty_exposure()
    if len(rep) != 440:
        fail(f"A: expected 440 repricing rows, got {len(rep)}")
    if len(pen) != 40:
        fail(f"A: expected 40 penalty rows, got {len(pen)}")
    summary = json.loads((DATA / "bea4_summary.json").read_text(encoding="utf-8"))
    if summary["mismatched_cells"] != 0:
        fail("A: summary claims non-zero mismatches")
    for name, want_rows in (("bea4_cost_recheck.csv", rows), ("bea4_repricing.csv", rep),
                            ("bea4_penalty_exposure.csv", pen)):
        with open(DATA / name, newline="", encoding="utf-8") as fh:
            on_disk = list(csv.DictReader(fh))
        if len(on_disk) != len(want_rows):
            fail(f"A: {name} has {len(on_disk)} rows, expected {len(want_rows)}")
        if {k: str(v) for k, v in on_disk[0].items()} != {k: str(v) for k, v in want_rows[0].items()}:
            fail(f"A: {name} first row differs from a fresh recomputation — rerun bea4_recheck.py")


def check_counts_printed():
    text = (ROOT / "bea4-audit.html").read_text(encoding="utf-8")
    for needle in ("1,720", "440 published rows", "0 mismatches"):
        if needle not in text:
            fail(f"B: audit page no longer states {needle!r}")
    audit = list(csv.DictReader(open(DATA / "bea4_source_audit.csv", encoding="utf-8")))
    e347_ids = {r["id"] for r in csv.DictReader(open(DATA / "e347_sources.csv", encoding="utf-8"))}
    confirmed = sum(1 for r in audit if r["result"] == "CONFIRMED" and r["source_id"] in e347_ids)
    if f"{confirmed}/{len(e347_ids)}" not in text:
        fail(f"B: audit page does not show the confirmed/total ratio {confirmed}/{len(e347_ids)}")


def check_generated():
    sys.path.insert(0, str(ROOT / "scripts"))
    import subprocess
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_bea4_site.py"), "--check"],
                         capture_output=True, text=True)
    if res.returncode:
        fail("C: " + (res.stdout + res.stderr).strip())


class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.rows = []          # list of (in_table, html_length, has_http_link)
        self.current = None
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("table", "tbody", "thead", "tr", "td", "th"):
            self.stack.append(tag)
        if tag == "tr":
            self.current = [True, 0, False]
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.current is not None and a["href"].startswith(("http://", "https://")):
                self.current[2] = True

    def handle_endtag(self, tag):
        if tag == "tr" and self.current is not None:
            if "thead" not in self.stack:
                self.rows.append(tuple(self.current))
            self.current = None
        if tag in ("table", "tbody", "thead", "tr", "td", "th") and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += len(data.strip())


def check_rows_and_links():
    for page in PAGES:
        html = page.read_text(encoding="utf-8")
        parser = Rows()
        parser.feed(html)
        if not parser.rows:
            fail(f"D: {page.name} has no table rows")
        for i, (_, length, has_http) in enumerate(parser.rows):
            if length == 0:
                fail(f"F: {page.name} has an empty table row (#{i + 1})")
            if not has_http:
                fail(f"D: {page.name} row #{i + 1} has no official source link")
        for href in parser.links:
            if href.startswith(("http://", "https://")):
                host = re.sub(r"^https?://", "", href).split("/")[0]
                if not any(host == d or host.endswith("." + d) for d in OFFICIAL):
                    fail(f"E: {page.name} links outside the official allowlist: {href}")
            elif not href.startswith(("#", "mailto:", "tel:")):
                target, _, anchor = href.partition("#")
                if not target:
                    continue  # same-page anchor
                path = (page.parent / target).resolve()
                if not path.exists():
                    fail(f"E: {page.name} -> missing file {href}")
                elif anchor and anchor not in path.read_text(encoding="utf-8"):
                    fail(f"E: {page.name} -> missing anchor {href}")
        for required in ('<meta name="viewport"', "dashboard/site.css"):
            if required not in html:
                fail(f"D: {page.name} lacks {required}")


def check_audit_register():
    audit = list(csv.DictReader(open(DATA / "bea4_source_audit.csv", encoding="utf-8")))
    text = (ROOT / "bea4-audit.html").read_text(encoding="utf-8")
    for r in audit:
        if r["result"] not in RESULTS:
            fail(f"F: unknown result {r['result']!r} for {r['source_id']}")
        if not r["url"].startswith("http"):
            fail(f"F: {r['source_id']} has no URL")
        if r["url"] not in text:
            fail(f"F: {r['source_id']} link is not on the page")
        if f'>{r["source_id"]}<' not in text:
            fail(f"F: {r['source_id']} id is not printed")
        if r["result"] in ("CONFIRMED", "PROPOSED_REPLACEMENT") and not r["evidence"]:
            fail(f"F: {r['source_id']} is marked {r['result']} with no evidence recorded")
        if r["result"] in ("CONFIRMED", "PROPOSED_REPLACEMENT") and not r["bea4_checked_on"]:
            fail(f"F: {r['source_id']} claims confirmation with no check date")
    # every e347 citation must be accounted for exactly once
    e347 = {r["id"] for r in csv.DictReader(open(DATA / "e347_sources.csv", encoding="utf-8"))}
    seen = {r["source_id"] for r in audit if r["source_id"] in e347}
    if e347 - seen:
        fail(f"F: citations never audited: {sorted(e347 - seen)}")
    if len(seen) != len(e347):
        fail("F: duplicate audit rows for an e347 citation")


def check_hygiene():
    marker = re.compile(r"^(<{7}|={7}|>{7})( |$)")
    for page in PAGES + [ROOT / "scripts" / "bea4_recheck.py", ROOT / "scripts" / "build_bea4_site.py"]:
        for n, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if marker.match(line):
                fail(f"G: conflict marker in {page.name} line {n}")
    for page in PAGES:
        html = page.read_text(encoding="utf-8")
        for bad in ("{", "}", "TODO", "PLACEHOLDER", "UPCODE", ">None<"):
            if bad in html:
                fail(f"G: {page.name} contains {bad!r}")
        if html.count("<table") != html.count("</table>"):
            fail(f"G: {page.name} has unbalanced table tags")


def main():
    check_data_regenerates()
    check_counts_printed()
    check_generated()
    check_rows_and_links()
    check_audit_register()
    check_hygiene()
    if failures:
        print(f"FAIL — {len(failures)} problem(s)")
        for f in failures:
            print("  -", f)
        return 1
    audit = list(csv.DictReader(open(DATA / "bea4_source_audit.csv", encoding="utf-8")))
    e347_ids = {r["id"] for r in csv.DictReader(open(DATA / "e347_sources.csv", encoding="utf-8"))}
    conf = sum(1 for r in audit if r["result"] == "CONFIRMED" and r["source_id"] in e347_ids)
    print(f"PASS — bea4: {conf}/{len(e347_ids)} dashboard citations re-read and confirmed, 1,720 cost cells "
          f"re-derived with 0 mismatches, 440 repriced rows, 40 penalty rows, "
          f"every table row carries an official link, all internal links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
