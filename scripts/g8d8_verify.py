#!/usr/bin/env python3
"""Independent checks on the G8D8 layer. Exit code 1 on any failure.

It does not import the build script's arithmetic: costs are recomputed here with exact fractions from the
published CSV inputs, and the pages are re-parsed from disk.
"""
import csv
import os
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(ROOT.glob("g8d8-*.html"))
OFFICIAL = ("boc.cn", "abchina.com", "abchina.com.cn", "ccb.com", "cmbchina.com", "icbc.com.cn", "bankcomm.com", "safe.gov.cn",
            "bankofamerica.com", "chase.com", "wellsfargo.com", "schwab.com", "fidelity.com", "wise.com", "westernunion.com",
            "irs.gov", "mof.gov.cn", "chinatax.gov.cn", "govinfo.gov", "ecfr.gov")
OWN = re.compile(r"^(g8d8-[a-z]+\.html|data/g8d8_[a-z_]+\.csv|research/g8d8-[a-z-]+\.md|scripts/g8d8_[a-z]+\.py|assets/g8d8\.css|"
                 r"\.github/workflows/g8d8-verify\.yml|COORDINATION\.md)$")
fails, notes = [], []


def check(name, ok, detail=""):
    (notes if ok else fails).append(f"{'PASS' if ok else 'FAIL'}  {name}{': ' + detail if detail else ''}")


def rows(name):
    with open(ROOT / "data" / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def cents(x):
    return Decimal(x.numerator) / Decimal(x.denominator) if isinstance(x, F) else Decimal(x)


def r2(x, places="0.01"):
    return cents(x).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in OFFICIAL)


# A. generated files are current
res = subprocess.run([sys.executable, str(ROOT / "scripts" / "g8d8_build.py"), "--check"], capture_output=True, text=True)
check("A generated files match the generator", res.returncode == 0, res.stdout.strip()[-200:])

# B. ladder recomputed from the published tariff and board files
banks = {b["bank"]: b for b in rows("g8d8_banks.csv")}
boards = {b["bank"]: b for b in rows("g8d8_bank_boards.csv")}
ladder = rows("g8d8_bank_ladder.csv")
yard = F(boards["BOC"]["sell_per_100_usd"]) / 100
bad = []
for r in ladder:
    b, bd, a = banks[r["bank"]], boards[r["bank"]], F(r["amount_usd"])
    exp = dict.fromkeys(("fee_cny_at_yardstick", "fee_usd_at_yardstick", "fee_cny_own_rate", "fee_usd_own_rate", "spread_usd", "total_usd", "total_pct"), "")
    if b["fee_rate_per_mille"]:
        rate, lo, hi, cable = F(b["fee_rate_per_mille"]) / 1000, F(b["min_cny"]), F(b["max_cny"]), F(b["cable_cny"])
        fee = lambda p: min(max(p * rate, lo), hi) + cable  # noqa: E731
        fy = fee(a * yard)
        exp["fee_cny_at_yardstick"], exp["fee_usd_at_yardstick"] = str(r2(fy)), str(r2(fy / yard))
        if bd["sell_per_100_usd"]:
            ask, bid = F(bd["sell_per_100_usd"]) / 100, F(bd["buy_per_100_usd"]) / 100
            mid = (ask + bid) / 2
            fo = fee(a * ask)
            fee_usd, spread = r2(fo / ask), r2(a * (ask - mid) / ask)
            total = fee_usd + spread
            exp.update(fee_cny_own_rate=str(r2(fo)), fee_usd_own_rate=str(fee_usd), spread_usd=str(spread), total_usd=str(total),
                       total_pct=str(r2(F(str(total)) / a * 100, "0.0001")))
    for k, v in exp.items():
        if r[k] != v:
            bad.append(f'{r["bank"]} {r["amount_usd"]} {k}: file {r[k]!r} expected {v!r}')
check(f"B {len(ladder)} ladder rows recomputed exactly", not bad and len(ladder) == 6 * 40, "; ".join(bad[:3]))
amounts = sorted({int(r["amount_usd"]) for r in ladder})
check("B amounts are $10,000 to $400,000 in $10,000 steps", amounts == list(range(10000, 400001, 10000)))
check("B a blank cost always carries a flag", all(r["flags"] for r in ladder if not r["total_usd"]))

# C. enforcement cases
cases = rows("g8d8_enforcement.csv")
bad = [c["party"] for c in cases if c["fine_cny_per_usd"] != str(r2(F(c["fine_cny"]) / F(c["amount_usd"]), "0.001"))
       or c["fine_pct_at_yardstick"] != str(r2(F(c["fine_cny"]) / F(c["amount_usd"]) / yard * 100, "0.1"))]
kinds = [c["party_type"] for c in cases]
check("C 40 cases, ratios recomputed", len(cases) == 40 and not bad, ", ".join(bad[:3]))
check("C 25 individuals, 2 overseas individuals, 13 companies", (kinds.count("Individual"), kinds.count("Overseas individual"), kinds.count("Company")) == (25, 2, 13))
check("C every case links to a safe.gov.cn bulletin", all(urlparse(c["bulletin_url"]).hostname.endswith("safe.gov.cn") for c in cases))

# D. sources and flags registers
sources = rows("g8d8_sources.csv")
flags = {f["id"] for f in rows("g8d8_flags.csv")}
check(f"D {len(sources)} sources, all on official hosts, ids unique", all(official(s["url"]) for s in sources) and len({s["id"] for s in sources}) == len(sources))
check("D every source has a quotation and a read mode", all(s["what_it_says"] and s["read_mode"] in ("full", "excerpt", "unreadable") for s in sources))
for name in ("g8d8_banks.csv", "g8d8_us_receiving.csv", "g8d8_channels.csv", "g8d8_flag_closures.csv", "g8d8_bank_ladder.csv"):
    used = {x for r in rows(name) for x in (r.get("flags") or r.get("still_flagged") or "").split("|") if x}
    check(f"D flags used in {name} exist", used <= flags, ", ".join(sorted(used - flags)))
for name in ("g8d8_banks.csv", "g8d8_us_receiving.csv", "g8d8_channels.csv", "g8d8_flag_closures.csv", "g8d8_channel_steps.csv", "g8d8_flags.csv"):
    rs = rows(name)
    key = "source_url" if "source_url" in rs[0] else "source_urls"
    check(f"D every row of {name} has an official source link", all(r[key] and all(official(u) for u in r[key].split()) for r in rs))


# E. pages
class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.rows, self.viewport = set(), [], [], False
        self.in_body = self.in_td = False
        self.row = self.cell = None
        self.pending_blank = False
        self.blank_bad = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name") == "viewport" and "width=device-width" in a.get("content", ""):
            self.viewport = True
        if tag == "tbody":
            self.in_body = True
        if tag == "tr" and self.in_body:
            self.row = []
        if tag == "td" and self.row is not None:
            self.cell = []
            self.row.append(self.cell)
        if tag == "span" and "blank" in a.get("class", ""):
            self.pending_blank = True
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
            if self.cell is not None:
                self.cell.append(a["href"])
            if self.pending_blank:
                if not re.match(r"g8d8-flagged\.html#F\d\d$", a["href"]):
                    self.blank_bad += 1
                self.pending_blank = False
        elif self.pending_blank and tag not in ("span",):
            self.blank_bad += 1
            self.pending_blank = False

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_body = False
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = self.cell = None
        if tag == "td":
            self.cell = None


parsed = {}
for p in PAGES:
    pg = Page()
    pg.feed(p.read_text(encoding="utf-8"))
    parsed[p.name] = pg
check("E eight pages exist", len(PAGES) == 8, ", ".join(p.name for p in PAGES))
total_rows = unsourced = 0
for name, pg in parsed.items():
    total_rows += len(pg.rows)
    unsourced += sum(1 for r in pg.rows if not r or not any(official(h) for h in r[-1]))
check(f"E all {total_rows} table rows end in an official source link", unsourced == 0 and total_rows >= 250, f"{unsourced} rows without one")
check("E every page has a mobile viewport", all(pg.viewport for pg in parsed.values()))
check("E every blank cell links to its flag", all(pg.blank_bad == 0 for pg in parsed.values()))
ext = [h for pg in parsed.values() for h in pg.links if h.startswith("http")]
check(f"E all {len(ext)} external links go to official hosts", all(official(h) for h in ext), ", ".join(sorted({h for h in ext if not official(h)})[:3]))
cache, broken, n_int = {}, [], 0
for name, pg in parsed.items():
    for h in pg.links:
        if h.startswith(("http", "mailto:")):
            continue
        n_int += 1
        path, _, frag = h.partition("#")
        target = (ROOT / path) if path else (ROOT / name)
        if not target.exists():
            broken.append(f"{name} -> {h}")
            continue
        if frag and target.suffix == ".html":
            if target not in cache:
                t = Page()
                t.feed(target.read_text(encoding="utf-8", errors="replace"))
                cache[target] = t.ids
            if frag not in cache[target]:
                broken.append(f"{name} -> {h}")
check(f"E all {n_int} internal links and anchors resolve", not broken, "; ".join(broken[:4]))
page_flags = {m for p in PAGES for m in re.findall(r"g8d8-flagged\.html#(F\d\d)", p.read_text(encoding="utf-8"))}
check("E flags referenced on pages exist, and every flag has an anchor", page_flags <= flags and flags <= parsed["g8d8-flagged.html"].ids)
markers = [p.name for p in list(PAGES) + sorted((ROOT / "data").glob("g8d8_*")) + sorted((ROOT / "scripts").glob("g8d8_*.py"))
           if re.search(r"^(<{7}|>{7}|={7})( |$)", p.read_text(encoding="utf-8"), re.M)]
check("E no merge-conflict markers", not markers, ", ".join(markers))

# F. scope: only on this session's own branch, so other sessions' branches are never failed by this check
branch = os.environ.get("GITHUB_HEAD_REF") or subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
if branch == "arena/8d8b8493-china3":
    base = subprocess.run(["git", "merge-base", "origin/main", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if base:
        changed = subprocess.run(["git", "diff", "--name-only", base, "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.split()
        outside = [c for c in changed if not OWN.match(c)]
        check(f"F {len(changed)} changed files are all inside the claimed scope", not outside, ", ".join(outside[:5]))
    else:
        notes.append("SKIP  F scope check: origin/main not available")
else:
    notes.append(f"SKIP  F scope check: not this session's branch ({branch or 'unknown'})")

print("\n".join(notes + fails))
print(f"\ng8d8_verify: {'FAIL' if fails else 'PASS'} ({len(notes)} ok, {len(fails)} failed)")
sys.exit(1 if fails else 0)
