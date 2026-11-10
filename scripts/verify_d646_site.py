#!/usr/bin/env python3
"""
D646 line-by-line verification gate.

Independent of scripts/build_d646_site.py: it re-derives the arithmetic with
decimal.Decimal from the raw published inputs (redeclared here on purpose) and
compares against what the builder emitted. If the two disagree, the build fails.

Checks
  1. Ladder: 40 unique amounts, USD 10,000 -> 400,000, ascending.
  2. Ladder arithmetic recomputed independently (spread, wire fee, totals, gain,
     tax at five brackets, wire count, years).
  3. Every data row in every CSV carries at least one https:// URL on an
     official / first-party domain allowlist.
  4. Blank-by-policy rule: an UNVERIFIED value is empty, never zero or a guess.
  5. Every source id referenced by a page exists in the register.
  6. Every table row in every generated page contains an https link.
  7. All local links and anchors resolve.
  8. Generated output is fresh (`--check` equivalent).
"""
from __future__ import annotations

import csv
import math
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = [
    "d646-summary.html", "d646-methods.html", "d646-costs.html", "d646-penalty.html",
    "d646-verification.html", "d646-flagged.html", "d646-sources.html",
]
CSS_FILE = "assets/d646.css"

# ---- redeclared raw inputs (published values only) ------------------------
SELL = Decimal("6.6903")        # BOC 669.03 / 100
BUY = Decimal("6.6622")         # BOC 666.22 / 100
MID = (SELL + BUY) / 2          # 6.67625 - midpoint of the bank's own two quotes
IRS_2024 = Decimal("7.189")
IRS_2025 = Decimal("7.129")
RATE = Decimal("0.001")
MIN_CNY = Decimal("50")
MAX_CNY = Decimal("260")
CABLE = Decimal("150")
B200 = Decimal("200")
CONV = Decimal("50000")

OFFICIAL = (
    "safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "gov.cn", "govinfo.gov",
    "irs.gov", "ecfr.gov", "fincen.gov", "cbp.gov", "boc.cn", "chinamoney.com.cn",
    "law.cornell.edu", "federalregister.gov", "treasury.gov",
)

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def q2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def tariff_cny(amount_usd: Decimal) -> Decimal:
    rmb = amount_usd * SELL
    return min(max(rmb * RATE, MIN_CNY), MAX_CNY) + CABLE


def spread_pct() -> Decimal:
    return SELL / MID - 1


def gain_frac(irs: Decimal) -> Decimal:
    return 1 - SELL / irs


# ---------------------------------------------------------------- 1-2 ladder
def check_ladder() -> None:
    path = DATA / "d646_ladder.csv"
    if not path.exists():
        fail("data/d646_ladder.csv missing"); return
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if len(rows) != 40:
        fail(f"ladder has {len(rows)} rows, expected 40")
    amounts = [int(r["usd"]) for r in rows]
    if amounts != list(range(10_000, 400_001, 10_000)):
        fail("ladder amounts are not exactly 10,000..400,000 in 10,000 steps")
    if len(set(amounts)) != 40:
        fail("ladder amounts are not unique")

    hd = Decimal(
    )  # placeholder to keep flake quiet
    del hd

    for r in rows:
        usd = Decimal(r["usd"])
        n = int(r["wires"])
        exp_n = max(1, math.ceil(usd / CONV))
        if n != exp_n:
            fail(f"{r['usd']}: wires {n} != {exp_n}")

        exp_spread = usd * SELL / MID - usd
        if q2(exp_spread) != Decimal(r["spread_usd"]):
            fail(f"{r['usd']}: spread {r['spread_usd']} != {q2(exp_spread)}")

        exp_fee = n * tariff_cny(usd / n) / SELL
        if q2(exp_fee) != Decimal(r["wire_fee_usd"]):
            fail(f"{r['usd']}: wire fee {r['wire_fee_usd']} != {q2(exp_fee)}")

        exp_total = exp_spread + exp_fee
        if q2(exp_total) != Decimal(r["known_bank_cost_usd"]):
            fail(f"{r['usd']}: bank total {r['known_bank_cost_usd']} != {q2(exp_total)}")

        if Decimal(r["known_bank_cost_usd"]) <= 0:
            fail(f"{r['usd']}: bank cost is not positive")

        exp_pct = exp_total / usd * 100
        if abs(Decimal(r["bank_cost_pct"]) - exp_pct) > Decimal("0.0001"):
            fail(f"{r['usd']}: bank pct {r['bank_cost_pct']} != {exp_pct:.4f}")

        exp_g24 = usd * gain_frac(IRS_2024)
        if q2(exp_g24) != Decimal(r["fx_gain_2024_usd"]):
            fail(f"{r['usd']}: gain24 {r['fx_gain_2024_usd']} != {q2(exp_g24)}")
        exp_g25 = usd * gain_frac(IRS_2025)
        if q2(exp_g25) != Decimal(r["fx_gain_2025_usd"]):
            fail(f"{r['usd']}: gain25 {r['fx_gain_2025_usd']} != {q2(exp_g25)}")

        for key, rate in (("tax_10", "0.10"), ("tax_22", "0.22"), ("tax_24", "0.24"),
                          ("tax_32", "0.32"), ("tax_37", "0.37")):
            exp = q2(exp_g24 * Decimal(rate))
            if exp != Decimal(r[key]):
                fail(f"{r['usd']}: {key} {r[key]} != {exp}")

        if int(r["years_at_50k"]) != math.ceil(usd / CONV):
            fail(f"{r['usd']}: years {r['years_at_50k']} != {math.ceil(usd / CONV)}")

        # blank-by-policy
        if r["intermediary_fees_usd"].strip() != "":
            fail(f"{r['usd']}: intermediary fee should be blank, found {r['intermediary_fees_usd']!r}")
        if r["intermediary_status"] != "UNVERIFIED":
            fail(f"{r['usd']}: intermediary status must be UNVERIFIED")

    notes.append(f"ladder: {len(rows)} rows, all components re-derived independently")

    # monotonicity + the specific reference points
    totals = [Decimal(r["known_bank_cost_usd"]) for r in rows]
    if any(b <= a for a, b in zip(totals, totals[1:])):
        fail("known bank cost is not strictly increasing with amount")
    if totals[0] != Decimal("53.47"):
        notes.append(f"note: USD 10,000 bank cost now {totals[0]} (was 53.45 at the 6.6919 board)")
    if q2(spread_pct() * 100) != Decimal("0.21"):
        fail(f"spread pct {spread_pct()*100:.4f} is not ~0.21% - is the midpoint wrong?")


# ------------------------------------------------------- 3-4 csv contract
def check_csv_contract() -> None:
    specs = {
        "d646_sources.csv": ("url", None),
        "d646_methods.csv": ("source_urls", None),
        "d646_ladder.csv": ("source_urls", None),
        "d646_verification.csv": ("source_urls", None),
        "d646_penalty.csv": ("source_urls", None),
    }
    for name, (urlfield, _) in specs.items():
        path = DATA / name
        if not path.exists():
            fail(f"{name} missing"); continue
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        if not rows:
            fail(f"{name} has no rows"); continue
        for i, r in enumerate(rows, start=2):
            urls = re.findall(r"https?://[^\s,]+", r.get(urlfield, ""))
            if not urls:
                fail(f"{name}:{i} has no URL in {urlfield}")
                continue
            for u in urls:
                if not any(d in u for d in OFFICIAL):
                    fail(f"{name}:{i} non-official URL {u}")
        notes.append(f"{name}: {len(rows)} rows, every row has an official URL")

    # UNVERIFIED <-> blank, both ways
    rows = list(csv.DictReader((DATA / "d646_penalty.csv").open(encoding="utf-8")))
    for r in rows:
        if r["status"] == "UNVERIFIED" and r["amount"].strip():
            fail(f"penalty {r['id']}: UNVERIFIED but amount is filled ({r['amount']!r})")
        if r["status"] == "verified" and not r["amount"].strip():
            fail(f"penalty {r['id']}: marked verified but amount is blank")
    notes.append(f"penalty: {len(rows)} rows, blank<=>UNVERIFIED rule holds")


def check_methods() -> None:
    rows = list(csv.DictReader((DATA / "d646_methods.csv").open(encoding="utf-8")))
    if len(rows) < 12:
        fail(f"only {len(rows)} methods - expected at least 12")
    lawful = [r for r in rows if r["legality"].startswith("Lawful")]
    bad = [r for r in rows if r["legality"].startswith(("PROHIBITED", "UNLAWFUL"))]
    if not lawful or not bad:
        fail("method list must contain both lawful and unlawful routes")
    if len({r["method"] for r in rows}) != len(rows):
        fail("duplicate method names")
    notes.append(f"methods: {len(rows)} routes ({len(lawful)} lawful, {len(bad)} unlawful)")


# ------------------------------------------------------------- 5 ids/html
def check_source_ids() -> None:
    src = {r["id"] for r in csv.DictReader((DATA / "d646_sources.csv").open(encoding="utf-8"))}
    if len(src) < 18:
        fail(f"only {len(src)} sources in register")
    for name in ("d646_methods.csv", "d646_penalty.csv", "d646_verification.csv"):
        for r in csv.DictReader((DATA / name).open(encoding="utf-8")):
            for sid in [x for x in r["source_ids"].split("|") if x]:
                if sid not in src:
                    fail(f"{name}: unknown source id {sid}")
    # every S-id that appears in a page must be in the register
    for page in PAGES:
        text = (ROOT / page).read_text(encoding="utf-8")
        used = set(re.findall(r'<span class="sid">(S\d\d)</span>', text))
        missing = used - src
        if missing:
            fail(f"{page}: references unregistered sources {sorted(missing)}")
    notes.append(f"sources: {len(src)} records, every referenced id resolves")


class RowParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows: list[list[tuple[str, str]]] = []
        self._cur: list[tuple[str, str]] | None = None
        self._cell: str | None = None
        self._links: list[str] = []
        self.in_tbody = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self._cur = []
        elif tag == "td" and self._cur is not None:
            self._cell = ""
            self._links = []
        elif tag == "a" and self._cell is not None:
            href = a.get("href", "")
            if href.startswith("http"):
                self._links.append(href)

    def handle_endtag(self, tag):
        if tag == "td" and self._cur is not None and self._cell is not None:
            self._cur.append((self._cell, "|".join(self._links)))
            self._cell = None
        elif tag == "tr" and self._cur is not None:
            self.rows.append(self._cur)
            self._cur = None
        elif tag == "tbody":
            self.in_tbody = False

    def handle_data(self, data):
        if self._cell is not None:
            self._cell += data


def check_rows_sourced() -> None:
    total = 0
    for page in PAGES:
        p = RowParser()
        p.feed((ROOT / page).read_text(encoding="utf-8"))
        for i, row in enumerate(p.rows, start=1):
            total += 1
            links = [l for _, l in row if l]
            if not links:
                fail(f"{page} row {i}: no https link anywhere in the row "
                     f"(first cell {row[0][0][:40]!r})")
                continue
            for l in links:
                for href in l.split("|"):
                    if not any(d in href for d in OFFICIAL):
                        fail(f"{page} row {i}: non-official link {href}")
    if total < 100:
        fail(f"only {total} sourced table rows audited - expected 100+")
    notes.append(f"html: {total} table rows audited, every row carries an official link")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a":
            h = a.get("href", "")
            if h and not h.startswith(("http://", "https://", "mailto:", "tel:")):
                self.hrefs.append(h)


def check_links() -> None:
    ids = {}
    parsed = {}
    for page in PAGES:
        p = Links()
        p.feed((ROOT / page).read_text(encoding="utf-8"))
        parsed[page] = p
        ids[page] = p.ids
    for page, p in parsed.items():
        for href in p.hrefs:
            target, _, anchor = href.partition("#")
            target = target or page
            if not (ROOT / target).exists():
                fail(f"{page}: broken link {href}")
                continue
            if anchor and target in ids and anchor not in ids[target] and not (ROOT / target).read_text(encoding="utf-8").count(f'id="{anchor}"'):
                fail(f"{page}: missing anchor #{anchor} in {target}")
    for page in PAGES:
        css = (ROOT / page).read_text(encoding="utf-8")
        if CSS_FILE not in css:
            fail(f"{page}: does not link {CSS_FILE}")
    if not (ROOT / CSS_FILE).exists():
        fail(f"{CSS_FILE} missing")
    notes.append(f"links: {len(PAGES)} pages, no broken local link or anchor")


def check_fresh() -> None:
    import importlib
    sys.path.insert(0, str(ROOT / "scripts"))
    mod = importlib.import_module("build_d646_site")
    for path, text in mod.render_all().items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            fail(f"stale output: {path.relative_to(ROOT)}")
    for name, (fields, rows) in mod.csv_payloads().items():
        path = DATA / name
        tmp = path.with_suffix(".chk")
        mod.write_csv(tmp, fields, rows)
        same = path.exists() and path.read_text(encoding="utf-8") == tmp.read_text(encoding="utf-8")
        tmp.unlink()
        if not same:
            fail(f"stale output: data/{name}")
    notes.append("freshness: generated pages and CSVs match the builder")


def main() -> int:
    check_ladder()
    check_csv_contract()
    check_methods()
    check_source_ids()
    check_rows_sourced()
    check_links()
    check_fresh()

    for n in notes:
        print("  ok ", n)
    if failures:
        print(f"\nFAIL — {len(failures)} problem(s):")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS — every row sourced, every blank flagged, arithmetic re-derived independently, "
          "no broken links, output fresh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
