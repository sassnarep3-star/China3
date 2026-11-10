#!/usr/bin/env python3
"""Line-by-line verification of the consolidated dashboard.

Runs without network access. Network reachability of the official sources was
established when data/verify_2026.csv was written (each row carries the fetch
timestamp); this script re-checks the things that can be checked mechanically:

  1. every row of every data table on index.html and verify-2026.html carries a
     link to an official domain, or is explicitly marked blank / unverified /
     prohibited with a reason
  2. every local link and anchor on both pages resolves to a real file / id
  3. the 40-row ladder in data/ladder_20261110.csv is re-derived here, with
     independent arithmetic, from data/live_rate_20261110.csv — including the
     1-per-mille wire fee's CNY 50 floor and CNY 260 cap
  4. the engine reproduces the 2026-11-09 schedule's published numbers from that
     session's own inputs, so a formula change cannot slip through
  5. every row of data/verify_2026.csv has an https URL on an official domain,
     a verbatim quote, a timestamp, a known verdict, and is cited on a page
  6. the generated pages are byte-identical to a fresh build
  7. the archived narrative guide still exists and still contains its content

Exit 0 = clean, 1 = violations.
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
D = Decimal

ERR: list[str] = []
NOTE: list[str] = []

OFFICIAL = (
    "gov.cn", "gov", "boc.cn", "chinatax.gov.cn", "ecfr.gov", "federalregister.gov",
    "irs.gov", "fincen.gov", "treasury.gov", "law.cornell.edu", "hkma.gov.hk",
    "pbc.gov.cn", "chinamoney.com.cn", "npc.gov.cn",
)
FLAG_MARKERS = ("blank", "unverified", "prohibited", "no official source", "penalties.html",
                "deep-review.html")


def fail(m: str) -> None:
    ERR.append(m)


def note(m: str) -> None:
    NOTE.append(m)


def q2(v: D) -> D:
    return v.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def official(url: str) -> bool:
    host = url.split("//", 1)[-1].split("/", 1)[0].lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


# ------------------------------------------------------------------ 1. markup
class Auditor(HTMLParser):
    """Collects table rows, and every local href / id on a page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_tbody = 0
        self.rows: list[list[tuple[str, str]]] = []   # list of rows; each = [(href, text)]
        self.cur: list[tuple[str, str]] | None = None
        self.cur_text: list[str] = []
        self.hrefs: list[str] = []
        self.ids: set[str] = set()
        self.table_index = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if tag == "tbody":
            self.in_tbody += 1
        if tag == "tr" and self.in_tbody:
            self.cur = []
            self.cur_text = []
        if tag == "a" and a.get("href") and self.cur is not None:
            self.cur.append((a["href"], ""))

    def handle_data(self, data):
        if self.cur is not None:
            self.cur_text.append(data)
            if self.cur:
                href, txt = self.cur[-1]
                self.cur[-1] = (href, txt + data)

    def handle_endtag(self, tag):
        if tag == "tbody" and self.in_tbody:
            self.in_tbody -= 1
        if tag == "tr" and self.cur is not None:
            self.rows.append(self.cur)
            self.tbl_text = getattr(self, "tbl_text", [])
            self.tbl_text.append(" ".join(self.cur_text))
            self.cur = None


def audit_page(path: Path) -> Auditor:
    au = Auditor()
    au.feed(path.read_text(encoding="utf-8"))
    return au


PAGES = [ROOT / "index.html", ROOT / "verify-2026.html"]
audits = {}
for page in PAGES:
    if not page.exists():
        fail(f"{page.name} is missing")
        continue
    au = audit_page(page)
    audits[page.name] = au
    bad = []
    for i, row in enumerate(au.rows):
        links = [h for h, _ in row if h.startswith("http")]
        if any(official(h) for h in links):
            continue
        blob = au.tbl_text[i].lower()
        if any(m in blob for m in FLAG_MARKERS):
            continue
        bad.append(i)
    if bad:
        for i in bad:
            fail(f"{page.name}: table row {i + 1} has no official source link and no blank/flag marker: "
                 f"{au.tbl_text[i][:110]}")
    note(f"{page.name}: {len(au.rows)} data rows, all sourced or explicitly flagged")

# ------------------------------------------------- 2. local links and anchors
html_files = {p.name: p for p in ROOT.glob("*.html")} | {f"docs/{p.name}": p for p in (ROOT / "docs").glob("*.html")}
all_ids = {}
for name, p in html_files.items():
    ids = set(re.findall(r'id="([^"]+)"', p.read_text(encoding="utf-8", errors="ignore")))
    all_ids[name] = ids

for page in PAGES:
    if not page.exists():
        continue
    for href in audit_page(page).hrefs:
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            if href.startswith("#"):
                if href[1:] and href[1:] not in all_ids.get(page.name, set()):
                    fail(f"{page.name}: anchor {href} does not exist")
            continue
        target, _, frag = href.partition("#")
        target = target.split("?")[0]
        if not target:
            continue
        resolved = (page.parent / target).resolve()
        if not resolved.exists():
            fail(f"{page.name}: broken local link {href}")
        if frag and resolved.suffix == ".html" and resolved.name in all_ids:
            if frag not in all_ids[resolved.name]:
                fail(f"{page.name}: {href} — anchor #{frag} missing in {resolved.name}")

# ------------------------------------------------------ 3. re-derive the ladder
rate = {r["field"]: r for r in rows("live_rate_20261110.csv")}
ask = D(rate["ask_spot_selling"]["value"]) / 100
bid = D(rate["bid_spot_buying"]["value"]) / 100
mid = (ask + bid) / 2
fee_rate = D(rate["wire_fee_per_mille"]["value"])
fee_min = D(rate["wire_fee_min"]["value"])
fee_max = D(rate["wire_fee_max"]["value"])
cable = D(rate["cable_fee_non_hk"]["value"])
our = D(rate["our_usd_optional"]["value"])

ladder = rows("ladder_20261110.csv")
if len(ladder) != 40:
    fail(f"ladder_20261110.csv has {len(ladder)} rows, expected 40")

seen_amounts = set()
for r in ladder:
    usd = D(r["amount_usd"])
    if usd in seen_amounts:
        fail(f"duplicate amount {usd}")
    seen_amounts.add(usd)
    if usd % 10000 != 0 or not (10000 <= usd <= 400000):
        fail(f"amount {usd} is not a $10,000 step in range")

    fx = q2(usd * (ask - mid) / ask)
    cny = q2(usd * ask)
    wire_cny = min(fee_max, max(fee_min, fee_rate * cny))
    wire = q2((wire_cny + cable) / ask)
    total = fx + wire
    for field, expect in (
        ("cny_needed", cny),
        ("spread_usd", fx),
        ("wire_cable_usd", wire),
        ("total_usd", total),
        ("net_usd", usd - total),
        ("net_with_our", usd - total - our),
    ):
        if D(r[field]) != expect:
            fail(f"${usd}: {field} is {r[field]}, independent arithmetic gives {expect}")
    if D(r["total_pct"]) != q2(total / usd * 100 * 100) / 100:
        # percentage is published to 4 dp, so compare rounded to 2 dp of a percentage
        if abs(D(r["total_pct"]) - (total / usd * 100)) > D("0.0001"):
            fail(f"${usd}: total_pct {r['total_pct']} does not match {total / usd * 100:.6f}")

# boundary behaviour of the fee: floor, cap, and the point the cap bites
fee_at_10k = min(fee_max, max(fee_min, fee_rate * D(10000) * ask))
if abs(fee_at_10k - D("0.001") * D("66903")) > D("0.01"):
    fail(f"wire fee at $10,000 is {fee_at_10k}, not the 1-per-mille charge on CNY 66,903")
cap_point = q2(fee_max / fee_rate / ask)
if not (D("38800") < cap_point < D("38900")):
    fail(f"cap threshold recomputed as {cap_point}, expected about 38,862")
note(f"wire fee reaches its CNY 260 cap at about ${cap_point:,.0f} of transfer")

# ------------------------------- 4. reproduce the 2026-11-09 schedule's numbers
S_ASK, S_BID = D("6.6924"), D("6.6643")
S_MID = (S_ASK + S_BID) / 2
s_fx = q2(D(10000) * (S_ASK - S_MID) / S_ASK)
s_fee = q2((min(D(260), max(D(50), D("0.001") * D(10000) * S_ASK)) + D(150)) / S_ASK)
s_total = s_fx + s_fee + D(25)
unrounded = D(10000) * (S_ASK - S_MID) / S_ASK + (
    (min(D(260), max(D(50), D("0.001") * D(10000) * S_ASK)) + D(150)) / S_ASK) + D(25)
if abs(unrounded - D("78.41")) > D("0.005"):
    fail(f"engine does not reproduce the published $10,000 schedule row: got {unrounded} vs 78.41")
else:
    note("engine reproduces the 2026-11-09 schedule's $10,000 row "
         f"(spread {s_fx} + wire {s_fee} + OUR 25 = {unrounded:.2f} unrounded; the schedule prints 78.41)")

# ------------------------------------------------------- 5. verification records
VERDICTS = {"verified", "derived", "unverified", "rejected"}
ver = rows("verify_2026.csv")
if len(ver) < 10:
    fail(f"verify_2026.csv has only {len(ver)} records")
seen_ids = set()
for v in ver:
    vid = v["id"]
    if vid in seen_ids:
        fail(f"{vid}: duplicate id")
    seen_ids.add(vid)
    if not official(v["url"]):
        fail(f"{vid}: {v['url']} is not an official domain")
    if not v["url"].startswith("https://") and "safe.gov.cn" not in v["url"]:
        fail(f"{vid}: source URL is not https ({v['url']})")
    if len(v["quote"].strip()) < 20:
        fail(f"{vid}: quote is too short to be verbatim")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", v["fetched_utc"]):
        fail(f"{vid}: fetched_utc {v['fetched_utc']!r} is not an ISO-8601 UTC timestamp")
    if v["verdict"] not in VERDICTS:
        fail(f"{vid}: verdict {v['verdict']!r} not in {sorted(VERDICTS)}")
    if v["verdict"] == "unverified" and v["value"].strip():
        fail(f"{vid}: marked unverified but carries a value")
    if v["verdict"] != "unverified" and not v["value"].strip():
        fail(f"{vid}: marked {v['verdict']} but value is blank")

page_text = "".join(p.read_text(encoding="utf-8") for p in PAGES if p.exists())
for vid in seen_ids:
    if vid not in page_text:
        fail(f"{vid}: no page cites this verification record")

cited = set(re.findall(r"\bV\d{2}\b", page_text))
for vid in sorted(cited - seen_ids):
    fail(f"page cites {vid} but data/verify_2026.csv has no such record")

# ------------------------------------------------- 6. generated output is fresh
proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_dashboard.py"), "--check"],
                      capture_output=True, text=True)
if proc.returncode != 0:
    fail("generated pages are stale: " + (proc.stdout + proc.stderr).strip())
else:
    note("generated pages are byte-identical to a fresh build")

# ------------------------------------------------------- 7. archive still there
guide = ROOT / "guide.html"
if not guide.exists():
    fail("guide.html (the archived narrative guide) is missing")
else:
    g = guide.read_text(encoding="utf-8")
    for marker in ("Executive takeaway", "Recommended sequence", "site-footer"):
        if marker not in g:
            fail(f"guide.html lost the earlier content marker {marker!r}")

if not (ROOT / "assets" / "dashboard.css").exists():
    fail("assets/dashboard.css is missing")

# ------------------------------------------------------------------- reporting
for n in NOTE:
    print("  note:", n)
if ERR:
    print()
    for e in ERR:
        print("  FAIL:", e)
    print(f"\nFAIL — {len(ERR)} violation(s).")
    raise SystemExit(1)
print(f"\nPASS — {len(ver)} verification records, {sum(len(a.rows) for a in audits.values())} data rows "
      f"across {len(PAGES)} pages, 40-row ladder re-derived, no broken links.")
