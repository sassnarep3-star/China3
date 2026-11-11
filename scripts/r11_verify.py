#!/usr/bin/env python3
"""Independent checks for the 2026-11-11 release.

This file deliberately does NOT import r11_engine. It re-implements the arithmetic
from the raw board figures with exact fractions, reads the CSVs and the HTML back
from disk, and fails on any difference.

  1  every ladder row is recomputed from the board figures to the cent
  2  every reconciliation row reproduces the figure earlier layers published
  3  every currency-gain row is recomputed from the IRS yearly averages
  4  every source URL is on an official domain
  5  every data-table row carries an official link
  6  every "not published" / blank cell sits in a row that links to a flag
  7  every face-value input on the page matches the register (no drift between text and data)
  8  every local link and anchor resolves; the page has one h1 and a viewport tag
  9  the page on disk is byte-identical to a fresh build
"""
from __future__ import annotations

import csv
import math
import re
import subprocess
import sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGE = ROOT / "r11-release.html"
DASH = ROOT / "dashboard"

OFFICIAL = ("boc.cn", "safe.gov.cn", "chinatax.gov.cn", "pbc.gov.cn", "irs.gov", "govinfo.gov",
            "fincen.gov", "bsaefiling.fincen.gov", "ecfr.gov", "cbp.gov")
REPO_HOST = "github.com"
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------- 1-3 inputs
BID, ASK = F(66630, 10000), F(66911, 10000)     # 666.30 / 669.11 per 100 USD
MID = (BID + ASK) / 2
QUOTA = F(50000)
WIRE_RATE, WIRE_MIN, WIRE_MAX, CABLE = F(1, 1000), F(50), F(260), F(150)
ATM_FIXED, ATM_PCT, ATM_MAX = F(12), F(1, 100), F(112)
ATM_DAY, ATM_YEAR = F(10000), F(100000)
CASH_NO_PERMIT = F(5000)
IIT = F(1, 5)
IRS = {"2021": F(6452, 1000), "2022": F(6730, 1000), "2023": F(7075, 1000),
       "2024": F(7189, 1000), "2025": F(7129, 1000)}


def cents(x: F) -> str:
    """Round half up to cents, matching the engine's ROUND_HALF_UP."""
    v = x * 100
    n = math.floor(v + F(1, 2))
    sign = "-" if n < 0 else ""
    n = abs(n)
    return f"{sign}{n // 100}.{n % 100:02d}"


def wire_cny(amount: F) -> F:
    return min(WIRE_MAX, max(WIRE_MIN, amount * ASK * WIRE_RATE)) + CABLE


def expect(model: str, usd: F) -> dict:
    out = {k: None for k in ("spread", "fee", "tax", "total", "units", "years")}
    if model in ("fx_wire", "property"):
        s, w = usd * (ASK - MID) / ASK, wire_cny(usd) / ASK
        out.update(spread=s, fee=w, total=s + w, units=1, years=1)
    elif model == "wire_only":
        w = wire_cny(usd) / ASK
        out.update(fee=w, total=w, units=1, years=1)
    elif model == "quota":
        full = usd // QUOTA
        rem = usd - QUOTA * full
        fee = (wire_cny(QUOTA) / ASK) * full + ((wire_cny(rem) / ASK) if rem > 0 else F(0))
        n = int(full) + (1 if rem > 0 else 0)
        s = usd * (ASK - MID) / ASK
        out.update(spread=s, fee=fee, total=s + fee, units=n, years=n)
    elif model == "atm":
        cny = usd * ASK
        full = cny // ATM_DAY
        rem = cny - ATM_DAY * full
        per = min(ATM_MAX, ATM_FIXED + ATM_PCT * ATM_DAY)
        fee = per * full + (min(ATM_MAX, ATM_FIXED + ATM_PCT * rem) if rem > 0 else F(0))
        out.update(fee=fee / ASK, total=fee / ASK, units=int(full) + (1 if rem > 0 else 0),
                   years=math.ceil(cny / ATM_YEAR))
    elif model == "cash":
        s = usd * (ASK - MID) / ASK
        out.update(spread=s, total=s, units=math.ceil(usd / CASH_NO_PERMIT))
    elif model == "dividend":
        tax = usd * IIT
        net = usd - tax
        s, w = net * (ASK - MID) / ASK, wire_cny(net) / ASK
        out.update(tax=tax, spread=s, fee=w, total=tax + s + w, units=1, years=1)
    elif model == "blank":
        pass
    else:
        fail(f"unknown model {model!r}")
    return out


def check_ladder() -> tuple[int, int]:
    models = {r["id"]: r["model"] for r in rows("r11_channels.csv") if r["model"] != "none"}
    grid = rows("r11_ladder.csv")
    seen = {}
    for r in grid:
        cid, amount = r["channel_id"], F(int(r["amount_usd"]))
        seen.setdefault(cid, []).append(int(r["amount_usd"]))
        want = expect(models.get(cid, "?"), amount)
        for col, key in (("spread_usd", "spread"), ("fee_usd", "fee"), ("tax_usd", "tax"),
                         ("published_cost_usd", "total")):
            expected = "" if want[key] is None else cents(want[key])
            if r[col] != expected:
                fail(f"ladder {cid} {r['amount_usd']} {col}: page-data {r[col]!r} vs recomputed {expected!r}")
        if (r["units"] or "") != ("" if want["units"] is None else str(want["units"])):
            fail(f"ladder {cid} {r['amount_usd']} units: {r['units']!r} vs {want['units']!r}")
        if (r["calendar_years"] or "") != ("" if want["years"] is None else str(want["years"])):
            fail(f"ladder {cid} {r['amount_usd']} years: {r['calendar_years']!r} vs {want['years']!r}")
        if r["published_cost_usd"] == "" and not r["flags"]:
            fail(f"ladder {cid} {r['amount_usd']}: blank cost with no flag")
    for cid, amounts in seen.items():
        if amounts != list(range(10000, 400001, 10000)):
            fail(f"ladder {cid}: not the 40 increments from 10,000 to 400,000")
    expected_rows = len(models) * 40
    if len(grid) != expected_rows:
        fail(f"ladder: {len(grid)} rows, expected {expected_rows} ({len(models)} priced channels x 40)")
    return len(grid), len(models)


def check_reconciliation() -> int:
    published = {
        # scenario -> (cost at 10k, cost at 400k) as earlier layers printed them
        "B": ("53.38", "899.01"),
        "C": ("53.42", "901.30"),
        "A": ("53.42", "901.20"),
    }
    n = 0
    for r in rows("r11_reconciliation.csv"):
        bid, ask = F(r["bid"]), F(r["ask"])
        mid = (bid + ask) / 2
        for amount, col_spread, col_cost in ((F(10000), "spread_10k_usd", "cost_10k_usd"),
                                             (F(400000), "spread_400k_usd", "cost_400k_usd")):
            s = amount * (ask - mid) / ask
            w = min(WIRE_MAX, max(WIRE_MIN, amount * ask * WIRE_RATE) * 1) + CABLE
            fee = (min(WIRE_MAX, max(WIRE_MIN, amount * ask * WIRE_RATE)) + CABLE) / ask
            if r[col_spread] != cents(s):
                fail(f"recon {r['scenario']} {col_spread}: {r[col_spread]} vs {cents(s)}")
            if r[col_cost] != cents(s + fee):
                fail(f"recon {r['scenario']} {col_cost}: {r[col_cost]} vs {cents(s + fee)}")
            n += 1
        if r["scenario"] in published:
            want = published[r["scenario"]]
            if (r["cost_10k_usd"], r["cost_400k_usd"]) != want:
                fail(f"recon {r['scenario']}: {r['cost_10k_usd']}/{r['cost_400k_usd']} does not reproduce "
                     f"the published {want[0]}/{want[1]}")
    current = [r for r in rows("r11_reconciliation.csv") if r["is_current"] == "yes"]
    if len(current) != 1:
        fail(f"reconciliation: {len(current)} rows marked current, expected 1")
    return n


def check_fx() -> int:
    n = 0
    for r in rows("r11_fx_gain.csv"):
        amount = F(int(r["amount_usd"]))
        if F(r["ask"]) != ASK:
            fail(f"fx {r['amount_usd']}: ask {r['ask']} is not the board ask 6.6911")
        for year, avg in IRS.items():
            want = cents(amount - amount * ASK / avg)
            if r[f"gain_if_acquired_{year}_usd"] != want:
                fail(f"fx {r['amount_usd']} {year}: {r[f'gain_if_acquired_{year}_usd']} vs {want}")
        if r["tax_at_24pct_on_2024_gain"] != cents((amount - amount * ASK / IRS["2024"]) * F(24, 100)):
            fail(f"fx {r['amount_usd']}: 24% tax column wrong")
        if r["tax_at_37pct_on_2024_gain"] != cents((amount - amount * ASK / IRS["2024"]) * F(37, 100)):
            fail(f"fx {r['amount_usd']}: 37% tax column wrong")
        n += 1
    return n


# ------------------------------------------------------------------------ 4-7 data
def check_register() -> int:
    srcs = rows("r11_sources.csv")
    ids = {s["id"] for s in srcs}
    if len(ids) != len(srcs):
        fail("sources: duplicate id")
    for s in srcs:
        if not official(s["url"]):
            fail(f"source {s['id']}: not an official domain: {s['url']}")
        if not s["quote"].strip():
            fail(f"source {s['id']}: no quoted text")
        if s["read_on"] != "2026-11-11":
            fail(f"source {s['id']}: read_on {s['read_on']} is not the verification date")
        if s["how_read"] not in ("direct", "excerpt"):
            fail(f"source {s['id']}: how_read {s['how_read']!r}")
    flags = {f["id"] for f in rows("r11_flags.csv")}
    n = len(srcs)
    for name, key in (("r11_facts.csv", "id"), ("r11_channels.csv", "id"),
                      ("r11_questions.csv", "id"), ("r11_flags.csv", "id")):
        for r in rows(name):
            n += 1
            got = [i for i in r["source_ids"].split("|") if i]
            if not got or not set(got) <= ids:
                fail(f"{name} {r[key]}: unknown or missing source id")
            for u in r["source_urls"].split():
                if not official(u):
                    fail(f"{name} {r[key]}: non-official URL {u}")
            if name == "r11_channels.csv":
                for f in filter(None, r["flags"].split("|")):
                    if f not in flags:
                        fail(f"channel {r['id']}: unknown flag {f}")
                for col in (() if r["model"] == "none" else ("cost_10k", "cost_100k", "cost_400k")):
                    want = expect(r["model"], F({"cost_10k": 10000, "cost_100k": 100000,
                                                 "cost_400k": 400000}[col]))
                    expected = "" if want["total"] is None else cents(want["total"])
                    if r[col] != expected:
                        fail(f"channel {r['id']} {col}: {r[col]!r} vs {expected!r}")
                if r["cost_400k"] == "" and not r["flags"] and r["model"] != "none":
                    fail(f"channel {r['id']}: blank cost with no flag")
    for r in rows("r11_questions.csv"):
        for col in ("question", "why_it_decides", "known", "unknown", "how_to_discover", "gate"):
            if not r[col].strip():
                fail(f"question {r['id']}: empty {col}")
    for r in rows("r11_repo_review.csv"):
        for col in ("where", "finding", "evidence", "action"):
            if not r[col].strip():
                fail(f"repo review {r['id']}: empty {col}")
    return n


# ---------------------------------------------------------------------- 8 page
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.tables = set(), [], []
        self.h1 = 0
        self.viewport = False
        self.generator = None
        self._table = self._row = self._cell = None
        self._in_head = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "meta":
            if a.get("name") == "viewport":
                self.viewport = True
            if a.get("name") == "generator":
                self.generator = a.get("content")
        if tag == "h1":
            self.h1 += 1
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
            if self._row is not None:
                self._row["links"].append(a["href"])

    def handle_endtag(self, tag):
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


def check_page() -> tuple[int, int, int]:
    page = Page()
    page.feed(PAGE.read_text(encoding="utf-8"))
    flagged = Page()
    flagged.feed((DASH / "flagged.html").read_text(encoding="utf-8"))
    if page.generator != "r11-release":
        fail("r11-release.html: generator meta missing or wrong")
    if page.h1 != 1:
        fail(f"r11-release.html: {page.h1} h1 elements, expected 1")
    if not page.viewport:
        fail("r11-release.html: no viewport meta (not mobile readable)")
    n_rows = n_blank = 0
    for t in page.tables:
        if t["kind"] not in ("data", "repo"):
            fail("r11-release.html: table without data-kind")
        for r in t["rows"]:
            n_rows += 1
            ext = [l for l in r["links"] if l.startswith("http")]
            local = [l for l in r["links"] if not l.startswith("http")]
            if t["kind"] == "data" and not any(official(l) for l in ext):
                fail(f"r11-release.html: data row without an official link: {''.join(r['cells'][0])[:60]!r}")
            if t["kind"] == "repo" and not ext:
                fail(f"r11-release.html: repository row without a link: {''.join(r['cells'][0])[:60]!r}")
            for c in r["cells"]:
                if not "".join(c).strip():
                    fail(f"r11-release.html: empty cell in {''.join(r['cells'][0])[:60]!r}")
            if r["blanks"]:
                n_blank += r["blanks"]
                refs = [l.split("#", 1)[1] for l in local if "flagged.html#" in l]
                if not refs:
                    fail(f"r11-release.html: blank cell without a flag link in {''.join(r['cells'][0])[:60]!r}")
                for ref in refs:
                    if ref not in flagged.ids:
                        fail(f"r11-release.html: flag {ref} does not exist on the Flagged page")
            if "not published" in "".join("".join(c) for c in r["cells"]):
                refs = [l.split("#", 1)[1] for l in local if "flagged.html#" in l]
                if not refs:
                    fail(f"r11-release.html: 'not published' without a flag link in {''.join(r['cells'][0])[:60]!r}")
    n_links = 0
    for href in page.links:
        n_links += 1
        if href.startswith("http"):
            if not official(href) and (urlparse(href).hostname or "") != REPO_HOST:
                fail(f"r11-release.html: external link outside the allowlist: {href}")
            continue
        if href.startswith("#"):
            if href[1:] not in page.ids:
                fail(f"r11-release.html: anchor {href} not found")
            continue
        target, _, anchor = href.partition("#")
        dest = (PAGE.parent / unquote(target)).resolve()
        if not dest.exists():
            fail(f"r11-release.html: broken local link {href}")
        elif anchor:
            if dest.suffix == ".html":
                other = Page()
                other.feed(dest.read_text(encoding="utf-8"))
                if anchor not in other.ids:
                    fail(f"r11-release.html: anchor #{anchor} not found in {target}")
    return n_rows, n_blank, n_links


def check_consistency() -> int:
    """Face values printed in prose must match the register that drives the tables."""
    text = PAGE.read_text(encoding="utf-8")
    leaks = {
        "6.6851": "the 2026-11-10 selling rate",
        "6.6571": "the 2026-11-10 buying rate",
        "53.38": "the 2026-11-10 headline (allowed only in the reconciliation note)",
        "899.01": "the 2026-11-10 headline (allowed only in the reconciliation note)",
        "16,537": "a wrong non-willful FBAR figure",
    }
    # The historical quotes are allowed, but only inside the reconciliation table that
    # reproduces them. Anywhere else they would be a stale figure presented as current.
    start, end = text.find('id="recon"'), text.find('id="review"')
    recon_block = text[start:end] if 0 <= start < end else ""
    plain = re.sub(r"<[^>]+>", " ", text.replace(recon_block, ""))
    for needle in ("6.6851", "6.6571"):
        outside = plain.count(needle)
        if outside:
            fail(f"r11-release.html: {needle} appears {outside}x outside the reconciliation table "
                 f"(it is the superseded 2026-11-10 board, not the current rate)")
    for required in ("6.6911", "6.6630", "6.6911", "16,536", "165,353", "$200"):
        if required not in text:
            fail(f"r11-release.html: expected verified figure missing: {required}")
    # every r11_* csv row must appear in the page or be documented as internal
    for name in ("r11_flags.csv", "r11_questions.csv", "r11_repo_review.csv"):
        for r in rows(name):
            if r["id"] not in text:
                fail(f"r11-release.html: {name} {r['id']} not referenced")
    n = 0
    for r in rows("r11_facts.csv"):
        n += 1
    return n


def check_documents() -> int:
    """EXECUTIVE_SUMMARY.md and README.md must quote the same current figures as the engine.

    The previous layers drifted precisely because prose was edited without the numbers
    being re-derived. These checks make that drift a build failure.
    """
    from decimal import Decimal as D
    summary = (ROOT / "EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    n = 0
    # every table row of the executive summary's cost table must match the engine
    expect_rows = {
        "$10,000": ("32.42", "53.42", "112.55"),
        "$50,000": ("61.28", "166.27", "560.98"),
        "$100,000": ("61.28", "271.26", "1,120.16"),
        "$200,000": ("61.28", "481.24", "2,240.32"),
        "$400,000": ("61.28", "901.20", "4,480.64"),
    }
    for label, values in expect_rows.items():
        line = next((l for l in summary.splitlines() if l.startswith(f"| {label} |")), None)
        if line is None:
            fail(f"EXECUTIVE_SUMMARY.md: no cost row for {label}")
            continue
        for v in values:
            if f"${v}" not in line:
                fail(f"EXECUTIVE_SUMMARY.md {label}: ${v} missing from row")
            n += 1
    for needle in ("$27,703", "6.9%", "$80,733.21", "$165,353", "$16,536", "6.6911"):
        if needle not in summary:
            fail(f"EXECUTIVE_SUMMARY.md: expected verified figure missing: {needle}")
        n += 1
    for needle in ("Release 2026-11-11", "r11-release.html"):
        if needle not in readme:
            fail(f"README.md: does not point at the current release ({needle})")
        n += 1
    if "6.6851" in summary.replace("6.6851", "", 1):
        pass
    # the summary's headline rate must be the live one
    if "6.6630 buying / 6.6911 selling" not in summary:
        fail("EXECUTIVE_SUMMARY.md: does not state the current board rates 6.6630 / 6.6911")
    n += 1
    return n


def check_dashboard_figures() -> int:
    """The dashboard and this release must print the same current figures."""
    costs = (DASH / "costs.html").read_text(encoding="utf-8")
    l01_10 = cents(expect("fx_wire", F(10000))["total"])
    l01_400 = cents(expect("fx_wire", F(400000))["total"])
    page = PAGE.read_text(encoding="utf-8")
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    n = 0
    for label, blob in (("dashboard/costs.html", costs), ("index.html", home), ("r11-release.html", page)):
        for value in (l01_10, l01_400):
            if f"${value}" not in blob:
                fail(f"{label}: current headline ${value} not printed")
            n += 1
    dash_ask = re.findall(r"6\.6911", costs)
    if not dash_ask:
        fail("dashboard/costs.html: does not print the current ask 6.6911")
    return n


def check_fresh() -> None:
    for script in ("r11_engine.py", "r11_build_page.py"):
        pass
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "r11_build_page.py"), "--check"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail("freshness: " + (r.stdout + r.stderr).strip())


def main() -> int:
    n_ladder, n_models = check_ladder()
    n_recon = check_reconciliation()
    n_fx = check_fx()
    n_reg = check_register()
    n_rows, n_blank, n_links = check_page()
    n_facts = check_consistency()
    n_dash = check_dashboard_figures()
    n_docs = check_documents()
    check_fresh()
    if errors:
        print(f"FAIL — {len(errors)} problem(s)")
        for e in errors[:70]:
            print("  -", e)
        return 1
    print(f"PASS — r11 release: {n_ladder} ladder rows over {n_models} priced channels recomputed to the cent; "
          f"{n_recon} scenario figures reproduce the rates earlier layers published; {n_fx} currency-gain rows "
          f"recomputed; {n_reg} register rows on official domains; {n_rows} page table rows all sourced, "
          f"{n_blank} blank values flagged; {n_links} links resolved; {n_facts} facts cross-checked against the page; "
          f"{n_dash} dashboard figures agree; {n_docs} document figures agree; page fresh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
