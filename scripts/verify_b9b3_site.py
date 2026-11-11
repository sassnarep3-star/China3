#!/usr/bin/env python3
"""Independent B9B3 gate: exact arithmetic, provenance, blanks, links, determinism.

Deliberately does NOT import b9b3_engine or build_b9b3_site.  The bank-cost
matrix is recomputed here from the same exact Fractions, and the generated
HTML/CSV files are parsed as data.  Exit 0 = every check passed.
"""
from __future__ import annotations

import csv
import hashlib
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP, getcontext
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

getcontext().prec = 60
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESEARCH = ROOT / "research"
ASSETS = ROOT / "assets"

BID = F(66631, 10000)
ASK = F(66912, 10000)
MID = (BID + ASK) / 2
HALF = ASK - MID
FEE_RATE = F(1, 1000)
FEE_MIN = F(50)
FEE_MAX = F(260)
CABLE = F(150)
QUOTA = 50000
AMOUNTS = list(range(10000, 400001, 10000))

PAGES = [
    "b9b3-dashboard.html", "b9b3-questions.html", "b9b3-methods.html",
    "b9b3-costs.html", "b9b3-steps.html", "b9b3-penalties.html",
    "b9b3-flagged.html", "b9b3-sources.html",
]
CSVS = [
    "data/b9b3_sources.csv", "data/b9b3_questions.csv", "data/b9b3_methods.csv",
    "data/b9b3_penalties.csv", "data/b9b3_ladder.csv", "data/b9b3_method_costs.csv",
    "data/b9b3_steps.csv", "data/b9b3_flags.csv",
]
MDS = [
    "research/b9b3-verification-log.md", "research/b9b3-executive-summary.md",
    "research/b9b3-decision-questions.md", "research/b9b3-methods-and-penalties.md",
    "research/b9b3-repo-audit.md",
]
ASSET_FILES = ["assets/b9b3.css", "assets/b9b3.js"]
GENERATED = PAGES + CSVS + MDS + ASSET_FILES

OFFICIAL_DOMAINS = (
    "boc.cn", "safe.gov.cn", "pbc.gov.cn", "mofcom.gov.cn", "chinatax.gov.cn",
    "irs.gov", "fincen.gov", "ecfr.gov", "govinfo.gov", "cbp.gov", "gov.cn",
)
CONFLICT = re.compile(r"^(<<<<<<<|=======|>>>>>>>)", re.M)
FAILURES: list[str] = []
CHECKS = 0


def fail(msg: str) -> None:
    FAILURES.append(msg)


def ok(label: str) -> None:
    global CHECKS
    CHECKS += 1
    print(f"  ✓ {label}")


def q(frac: F, places: int = 2) -> str:
    dec = Decimal(frac.numerator) / Decimal(frac.denominator)
    return str(dec.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return url.startswith(("http://", "https://")) and any(
        host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS
    )


def rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def ids(value: str) -> list[str]:
    return [x for x in value.split("|") if x]


def wire_cny(usd: F) -> F:
    return min(FEE_MAX, max(FEE_MIN, usd * ASK * FEE_RATE)) + CABLE


def wire_usd(usd: F) -> F:
    return wire_cny(usd) / ASK


def spread_usd(usd: F) -> F:
    return usd * HALF / ASK


def pct(cost: F, amount: F) -> F:
    return cost / amount * 100


def expected_cost(row: dict[str, str]) -> dict[str, str]:
    """Recompute one cost row from exact Fractions, with no engine import."""
    a = F(int(row["amount_usd"]))
    model = row["model"]
    e = {k: "" for k in (
        "cny_needed_at_ask", "fx_spread_usd", "bank_wire_and_cable_usd",
        "known_bank_cost_usd", "known_bank_cost_pct",
        "net_after_known_bank_cost_usd", "wire_count", "calendar_years",
    )}
    if model in {"fx_wire", "wire_only", "quota", "cash"}:
        e["cny_needed_at_ask"] = q(a * ASK)
    if model == "fx_wire":
        s, w = spread_usd(a), wire_usd(a)
        total = s + w
        e.update({
            "fx_spread_usd": q(s), "bank_wire_and_cable_usd": q(w),
            "known_bank_cost_usd": q(total), "known_bank_cost_pct": q(pct(total, a), 4),
            "net_after_known_bank_cost_usd": q(a - total),
            "wire_count": "1", "calendar_years": "1",
        })
    elif model == "wire_only":
        w = wire_usd(a)
        e.update({
            "bank_wire_and_cable_usd": q(w), "known_bank_cost_usd": q(w),
            "known_bank_cost_pct": q(pct(w, a), 4),
            "net_after_known_bank_cost_usd": q(a - w),
            "wire_count": "1", "calendar_years": "1",
        })
    elif model == "quota":
        full, rem = divmod(int(row["amount_usd"]), QUOTA)
        n = full + (1 if rem else 0)
        fee = F(full) * wire_usd(F(QUOTA)) + (wire_usd(F(rem)) if rem else F(0))
        s = spread_usd(a)
        total = s + fee
        e.update({
            "fx_spread_usd": q(s), "bank_wire_and_cable_usd": q(fee),
            "known_bank_cost_usd": q(total), "known_bank_cost_pct": q(pct(total, a), 4),
            "net_after_known_bank_cost_usd": q(a - total),
            "wire_count": str(n), "calendar_years": str(n),
        })
    elif model == "cash":
        e["fx_spread_usd"] = q(spread_usd(a))
    return e


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.rows: list[dict] = []
        self.viewport = False
        self._tbody = 0
        self._row: dict | None = None
        self._cell: dict | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag in {"a", "link", "script", "img"}:
            href = a.get("href") or a.get("src")
            if href:
                self.links.append(href)
        if tag == "tbody":
            self._tbody += 1
        if tag == "tr" and self._tbody:
            self._row = {"cells": [], "links": []}
        if tag == "td" and self._row is not None:
            if self._cell is not None:
                fail("nested <td> in a B9B3 table")
            self._cell = {"text": "", "links": [], "blank": False}
        if tag == "span" and "blank" in (a.get("class") or "").split() and self._cell is not None:
            self._cell["blank"] = True
        if tag == "a" and a.get("href") and self._row is not None:
            href = a["href"]
            self._row["links"].append(href)
            if self._cell is not None:
                self._cell["links"].append(href)

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._cell is not None and self._row is not None:
            self._row["cells"].append(self._cell)
            self._cell = None
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None
        if tag == "tbody" and self._tbody:
            self._tbody -= 1


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def check_exact_costs(source_map: dict[str, str]) -> dict[tuple[str, int], dict[str, str]]:
    print("A. exact-Fraction cost matrix (independent recomputation)")
    costs = rows("data/b9b3_method_costs.csv")
    methods = {m["method_id"]: m for m in rows("data/b9b3_methods.csv")}
    flags = {f["flag_id"] for f in rows("data/b9b3_flags.csv")}
    expected_keys = {(mid, amt) for mid in methods for amt in AMOUNTS}
    got_keys = {(r["method_id"], int(r["amount_usd"])) for r in costs}
    if got_keys != expected_keys or len(costs) != len(expected_keys):
        fail(f"cost matrix keys: expected {len(expected_keys)}, got {len(costs)}")
    by_key: dict[tuple[str, int], dict[str, str]] = {}
    for i, r in enumerate(costs, 1):
        mid, amt = r["method_id"], int(r["amount_usd"])
        by_key[(mid, amt)] = r
        m = methods[mid]
        if r["status"] != m["legal_status"] or r["model"] != m["cost_model"]:
            fail(f"cost row {i}: status/model mismatch for {mid} ${amt:,}")
        e = expected_cost(r)
        for field, want in e.items():
            if r[field] != want:
                fail(f"cost row {i} {mid} ${amt:,} {field}: file {r[field]!r}, recomputed {want!r}")
        for field in ("our_fee_usd", "intermediary_fee_usd", "receiving_fee_usd",
                      "prc_tax_usd", "us_988_gain_usd", "all_in_total_usd"):
            if r[field] != "":
                fail(f"cost row {i}: {field} silently filled with {r[field]!r}")
        if not r["flag_ids"] or not set(ids(r["flag_ids"])) <= flags:
            fail(f"cost row {i}: missing or unknown flags")
        src_ids = ids(r["source_ids"])
        if not src_ids or not set(src_ids) <= set(source_map):
            fail(f"cost row {i}: missing or unknown source ids")
            continue
        want_urls = "|".join(source_map[s] for s in src_ids)
        if r["source_urls"] != want_urls or not all(official(u) for u in r["source_urls"].split("|")):
            fail(f"cost row {i}: source_urls are stale, non-official or out of order")
        if not r["limitations"].strip():
            fail(f"cost row {i}: missing limitation disclosure")
    # Sanity anchors from the 2026-11-11 10:40:02 board.
    if by_key.get(("B01", 10000), {}).get("known_bank_cost_usd") != "53.42":
        fail("B01 $10,000 known cost is not $53.42")
    if by_key.get(("B01", 400000), {}).get("known_bank_cost_usd") != "901.18":
        fail("B01 $400,000 known cost is not $901.18")
    if by_key.get(("B03", 10000), {}).get("known_bank_cost_usd") != "32.42":
        fail("B03 $10,000 wire-only cost is not $32.42")
    ok(f"{len(costs)} cost rows recomputed exactly; 40 increments × {len(methods)} methods")
    return by_key


def check_ladder(by_key: dict[tuple[str, int], dict[str, str]], source_map: dict[str, str]) -> None:
    print("B. 40-row decision ladder")
    ladder = rows("data/b9b3_ladder.csv")
    flags = {f["flag_id"] for f in rows("data/b9b3_flags.csv")}
    if [int(r["amount_usd"]) for r in ladder] != AMOUNTS:
        fail("ladder does not cover $10,000..$400,000 in $10,000 steps")
    for r in ladder:
        amt = int(r["amount_usd"])
        b01, b03 = by_key[("B01", amt)], by_key[("B03", amt)]
        if r["best_cny_to_usd_method_id"] != "B01":
            fail(f"ladder ${amt:,}: unexpected best method {r['best_cny_to_usd_method_id']}")
        for field, want in (
            ("cny_needed_at_ask", q(F(amt) * ASK)),
            ("best_cny_to_usd_known_cost_usd", b01["known_bank_cost_usd"]),
            ("best_cny_to_usd_pct", b01["known_bank_cost_pct"]),
            ("wire_only_known_cost_usd", b03["known_bank_cost_usd"]),
        ):
            if r[field] != want:
                fail(f"ladder ${amt:,} {field}: file {r[field]!r}, expected {want!r}")
        src_ids = ids(r["source_ids"])
        if not src_ids or not set(src_ids) <= set(source_map):
            fail(f"ladder ${amt:,}: unknown source ids")
        elif r["source_urls"] != "|".join(source_map[s] for s in src_ids):
            fail(f"ladder ${amt:,}: stale source_urls")
        if not r["flag_ids"] or not set(ids(r["flag_ids"])) <= flags:
            fail(f"ladder ${amt:,}: missing or unknown flags")
    ok(f"{len(ladder)} ladder rows agree with the independently recomputed cost matrix")


def check_static_csvs(source_map: dict[str, str]) -> None:
    print("C. CSV registers, source links, blanks and discovery steps")
    flag_ids = {f["flag_id"] for f in rows("data/b9b3_flags.csv")}
    method_ids = {m["method_id"] for m in rows("data/b9b3_methods.csv")}
    src_ids = set(source_map)
    for rel in CSVS:
        for i, r in enumerate(rows(rel), 1):
            for key, known in (("source_ids", src_ids), ("flag_ids", flag_ids)):
                if key in r:
                    got = ids(r[key])
                    if key == "source_ids" and (not got or not set(got) <= known):
                        fail(f"{rel} row {i}: bad {key} {r[key]!r}")
                    if key == "flag_ids" and not set(got) <= known:
                        fail(f"{rel} row {i}: bad {key} {r[key]!r}")
            if "source_urls" in r:
                urls = r["source_urls"].split("|") if r["source_urls"] else []
                if not urls or not all(official(u) for u in urls):
                    fail(f"{rel} row {i}: missing/non-official source_urls")
                want = [source_map[s] for s in ids(r.get("source_ids", ""))]
                if urls != want:
                    fail(f"{rel} row {i}: source_urls do not match source_ids in order")
    for qrow in rows("data/b9b3_questions.csv"):
        if qrow["status"] in {"Open", "Partly answered"}:
            if not qrow["how_to_discover"].strip() or not qrow["answer_needed"].strip():
                fail(f"{qrow['question_id']}: open/partial question lacks a discovery step or answer")
    for prow in rows("data/b9b3_penalties.csv"):
        if not prow["rate_or_amount"].strip() and not prow["flag_ids"]:
            fail(f"{prow['penalty_id']}: blank penalty without a flag")
    step_methods = {s["method_id"] for s in rows("data/b9b3_steps.csv")}
    if not method_ids <= step_methods:
        fail(f"methods without step playbooks: {sorted(method_ids - step_methods)}")
    ok(f"{len(CSVS)} CSV registers: all source/flag references resolve; blank penalties flagged; every method has steps")


def check_html() -> None:
    print("D. HTML rows, official links, blank-cell flags, internal links/anchors")
    parsed: dict[str, PageParser] = {}
    for name in PAGES:
        path = ROOT / name
        p = PageParser()
        p.feed(path.read_text(encoding="utf-8"))
        parsed[name] = p
        if not p.viewport:
            fail(f"{name}: missing mobile viewport meta")
        if not p.rows:
            fail(f"{name}: no data table rows parsed")
    flag_page_ids = parsed["b9b3-flagged.html"].ids
    total_rows = 0
    blank_cells = 0
    for name, p in parsed.items():
        for i, row in enumerate(p.rows, 1):
            total_rows += 1
            ext = [h for h in row["links"] if h.startswith(("http://", "https://"))]
            if not any(official(h) for h in ext):
                fail(f"{name} tbody row {i}: no official source URL")
            for h in ext:
                if not official(h):
                    fail(f"{name} tbody row {i}: external link outside the official allowlist: {h}")
            for cell in row["cells"]:
                if not cell["text"].strip() and not cell["links"]:
                    fail(f"{name} tbody row {i}: empty cell")
                if cell["blank"]:
                    blank_cells += 1
                    refs = [h.split("#", 1)[1] for h in cell["links"] if "b9b3-flagged.html#" in h]
                    if not refs:
                        fail(f"{name} tbody row {i}: blank cell has no flag link")
                    for ref in refs:
                        if ref not in flag_page_ids:
                            fail(f"{name} tbody row {i}: flag #{ref} missing on Flagged page")
    # Internal links and anchors, including CSS/JS from link/script tags.
    for name, p in parsed.items():
        page = ROOT / name
        for href in p.links:
            if href.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            if href.startswith("#"):
                anchor = href[1:]
                if anchor and anchor not in p.ids:
                    fail(f"{name}: broken same-page anchor {href}")
                continue
            target, _, anchor = href.partition("#")
            dest = (page.parent / unquote(target)).resolve()
            if not dest.exists():
                fail(f"{name}: broken local link {href}")
                continue
            if anchor and dest.suffix == ".html":
                target_parser = parsed.get(dest.name)
                if target_parser is None:
                    target_parser = PageParser()
                    target_parser.feed(dest.read_text(encoding="utf-8"))
                if anchor not in target_parser.ids:
                    fail(f"{name}: broken anchor {href} (id not found in {dest.name})")
    ok(f"{len(PAGES)} pages, {total_rows} tbody rows all sourced, {blank_cells} blank cells all flag-linked, all local links/anchors resolve")


def check_archive_and_markers() -> None:
    print("E. archive reachability and zero conflict markers")
    archive = (ROOT / "dashboard" / "archive.html").read_text(encoding="utf-8")
    for name in PAGES:
        if f"../{name}" not in archive:
            fail(f"dashboard/archive.html does not link {name}")
    claim_files: list[Path] = [ROOT / "COORDINATION.md", ROOT / "dashboard" / "archive.html"]
    for path in sorted(ROOT.rglob("*b9b3*")):
        if path.is_file() and ".git" not in path.parts:
            claim_files.append(path)
    for path in claim_files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if CONFLICT.search(text):
            fail(f"conflict marker in {path.relative_to(ROOT)}")
    board = (ROOT / "COORDINATION.md").read_text(encoding="utf-8")
    if "arena/9b36086f-china3" not in board or "b9b3" not in board:
        fail("COORDINATION.md does not carry the current branch's b9b3 claim")
    ok(f"all {len(PAGES)} B9B3 pages linked from the archive; {len(claim_files)} claim files have zero conflict markers")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_determinism() -> None:
    print("F. build/check idempotency")
    paths = [ROOT / rel for rel in GENERATED] + [ROOT / "dashboard" / "archive.html"]
    before = {p: sha(p) for p in paths}
    for cmd in (
        ("python3", "scripts/b9b3_engine.py"),
        ("python3", "scripts/build_b9b3_site.py"),
        ("python3", "scripts/e347_build.py"),
    ):
        r = run(*cmd)
        if r.returncode != 0:
            fail(f"{' '.join(cmd)} exited {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}")
            return
    after = {p: sha(p) for p in paths}
    changed = [p.relative_to(ROOT) for p in paths if before[p] != after[p]]
    if changed:
        fail(f"rebuild changed files: {', '.join(map(str, changed))}")
        return
    for cmd in (
        ("python3", "scripts/build_b9b3_site.py", "--check"),
        ("python3", "scripts/e347_build.py", "--check"),
    ):
        r = run(*cmd)
        if r.returncode != 0:
            fail(f"{' '.join(cmd)} failed: {(r.stderr or r.stdout).strip()[-300:]}")
            return
    ok(f"{len(paths)} generated files are byte-identical after rebuild; both --check gates pass")


def main() -> int:
    print("=" * 78)
    print("B9B3 independent verification")
    print("=" * 78)
    missing = [rel for rel in GENERATED + ["dashboard/archive.html"] if not (ROOT / rel).exists()]
    if missing:
        fail("missing generated files: " + ", ".join(missing))
        print("\n".join("  ✗ " + f for f in FAILURES))
        return 1
    sources = rows("data/b9b3_sources.csv")
    source_map = {s["source_id"]: s["url"] for s in sources}
    if len(source_map) != 50 or any(not official(u) for u in source_map.values()):
        fail("source register is not 50 unique official URLs")
    by_key = check_exact_costs(source_map)
    check_ladder(by_key, source_map)
    check_static_csvs(source_map)
    check_html()
    check_archive_and_markers()
    check_determinism()
    print("-" * 78)
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s):")
        for f in FAILURES[:80]:
            print("  ✗ " + f)
        return 1
    print(f"PASS — {CHECKS} checks, 0 failures; 880 exact cost rows, 40 ladder rows, "
          f"{len(PAGES)} source-linked pages, all blanks flagged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
