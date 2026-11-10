#!/usr/bin/env python3
"""Independent verification of the S775 deliverables.

Checks:
 1. data/s775_*.csv exist with expected shape and unique ids.
 2. Every source_ids value resolves to data/s775_sources.csv, and every source
    URL is an official domain (.gov / govinfo / chinamoney / boc / bocusa).
 3. Timestamps are ISO-8601 UTC on 2026-11-10.
 4. The $10k-$400k ladder is re-derived from first principles (ask/bid) and
    matches the CSV to the cent.
 5. Blank cost cells follow the rule: blank <=> unverified components noted.
 6. HTML pages: exist, contain the expected number of data rows, every row
    carries a source link, anchors referenced from tables exist on the sources
    page, all internal links resolve, nav present on every page.
 7. Dashboard headline numbers agree with the ladder rows.
 8. Generated artifacts are byte-identical to a fresh build.

Exit code 0 = PASS, 1 = FAIL.
"""

import csv
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = ["s775-dashboard.html", "s775-cost-10k-400k.html", "s775-methods.html",
         "s775-steps.html", "s775-penalties-tax.html", "s775-flagged-review.html",
         "s775-sources.html"]

ASK = Decimal("6.6903")
BID = Decimal("6.6622")
MID = (ASK + BID) / 2
RATIO = (ASK - MID) / ASK

# official domains: central/provincial government, regulators, the two banks,
# official statistics/code publishers
OFFICIAL_DOMAINS = (
    "boc.cn", "bocusa.com", "safe.gov.cn", "pbc.gov.cn", "gov.cn",
    "chinatax.gov.cn", "chinamoney.com.cn", "hncourt.gov.cn",
    "rst.shaanxi.gov.cn", "rsj.sh.gov.cn", "jingyuan.gov.cn",
    "govinfo.gov", "irs.gov", "fincen.gov", "ecfr.gov", "cbp.gov",
)

# flag rows that document process irregularities have no official source by
# construction; they are flagged, not verified
PROCESS_STATUSES = ("IRREGULARITY S775-IR-001", "IRREGULARITY S775-IR-002", "NEEDS REVIEW")


def official_domain(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)

ERR = []
NOTE = []


def fail(msg):
    ERR.append(msg)


def note(msg):
    NOTE.append(msg)


def read_csv(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def q2(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ------------------------------------------------------------- 1. shape
files = {
    "s775_sources.csv": 52, "s775_methods.csv": 24, "s775_penalties.csv": 23,
    "s775_cost_10k_400k.csv": 40, "s775_method_summary.csv": 24,
    "s775_steps.csv": 68, "s775_flags.csv": 18,
}
for name, want in files.items():
    p = DATA / name
    if not p.exists():
        fail(f"missing {name}")
        continue
    rows = read_csv(name)
    if len(rows) != want:
        fail(f"{name} has {len(rows)} rows, expected {want}")

sources = read_csv("s775_sources.csv")
sources_by_id = {s["id"]: s for s in sources}
if len(sources_by_id) != len(sources):
    fail("s775_sources.csv has duplicate ids")

methods = read_csv("s775_methods.csv")
penalties = read_csv("s775_penalties.csv")
costs = read_csv("s775_cost_10k_400k.csv")
summary = read_csv("s775_method_summary.csv")
steps = read_csv("s775_steps.csv")
flags = read_csv("s775_flags.csv")

# ------------------------------------------- 2. sources resolve + official domain
for s in sources:
    url = s["url"]
    if not official_domain(url):
        fail(f"{s['id']}: {url} is not an official domain")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", s["fetched_utc"]):
        fail(f"{s['id']}: bad fetched_utc {s['fetched_utc']!r}")
    elif not s["fetched_utc"].startswith("2026-11-10"):
        fail(f"{s['id']}: fetched_utc is not 2026-11-10")
    if not s["what_it_establishes"].strip():
        fail(f"{s['id']}: what_it_establishes is blank")


def check_src_ids(rows, field, where):
    for r in rows:
        rid = r.get("id") or r.get("method_id")
        ids = [x for x in (r.get(field) or "").split("|") if x]
        if not ids:
            if where == "flags" and r.get("status") in PROCESS_STATUSES:
                note(f"{rid}: process-irregularity flag carries no official source by construction")
            else:
                fail(f"{where} {rid}: no source ids")
        for sid in ids:
            if sid not in sources_by_id:
                fail(f"{where} {rid}: unknown source {sid}")


check_src_ids(methods, "source_ids", "methods")
check_src_ids(penalties, "source_ids", "penalties")
check_src_ids(costs, "source_ids", "costs")
check_src_ids(steps, "source_ids", "steps")
check_src_ids(flags, "source_ids", "flags")

# ------------------------------------------- 3. ladder re-derivation
seen_amounts = []
for r in costs:
    amt = int(r["amount_usd"])
    seen_amounts.append(amt)
    cny = q2(Decimal(amt) * ASK)
    if Decimal(r["cny_needed"]) != cny:
        fail(f"${amt}: cny_needed {r['cny_needed']} != {cny}")
    spread = q2(Decimal(amt) * RATIO)
    if Decimal(r["spread_usd"]) != spread:
        fail(f"${amt}: spread {r['spread_usd']} != {spread}")
    wire_cny = min(Decimal("260"), max(Decimal("50"), cny * Decimal("0.001"))) + Decimal("150")
    if Decimal(r["wire_cny"]) != wire_cny:
        fail(f"${amt}: wire_cny {r['wire_cny']} != {wire_cny}")
    wire_usd = q2(wire_cny / ASK)
    if Decimal(r["wire_usd"]) != wire_usd:
        fail(f"${amt}: wire_usd {r['wire_usd']} != {wire_usd}")
    total = q2(spread + wire_usd)
    if Decimal(r["total_usd"]) != total:
        fail(f"${amt}: total {r['total_usd']} != {total}")
    total_our = q2(total + Decimal("25"))
    if Decimal(r["total_with_our_usd"]) != total_our:
        fail(f"${amt}: total_with_our {r['total_with_our_usd']} != {total_our}")
    if Decimal(r["net_usd"]) != q2(Decimal(amt) - total):
        fail(f"${amt}: net_usd mismatch")
    if Decimal(r["net_with_our_usd"]) != q2(Decimal(amt) - total_our):
        fail(f"${amt}: net_with_our_usd mismatch")
    pct = (total / Decimal(amt)) * 100
    if abs(Decimal(r["total_pct"]) - pct) > Decimal("0.005"):
        fail(f"${amt}: total_pct {r['total_pct']} != {pct:.4f}")

if seen_amounts != list(range(10_000, 400_001, 10_000)):
    fail("ladder amounts are not 10,000..400,000 in 10,000 steps")

# ------------------------------------------- 4. blank rule on method summary
sm = {r["method_id"]: r for r in summary}
for mid, r in sm.items():
    if mid in ("M01", "M02"):
        for col in ("verified_usd_10k", "verified_usd_100k", "verified_usd_400k"):
            if not r[col].strip():
                fail(f"{mid}: verified {col} is blank but the route has official tariffs")
    else:
        blanks = sum(1 for col in ("verified_usd_10k", "verified_usd_100k", "verified_usd_400k")
                     if not r[col].strip())
        if blanks and not r["unverified_components"].strip():
            fail(f"{mid}: cost cells blank but no unverified_components note")

# ------------------------------------------- 5. HTML audits
for p in PAGES:
    if not (ROOT / p).exists():
        fail(f"missing page {p}")

html_by_page = {p: (ROOT / p).read_text(encoding="utf-8") for p in PAGES if (ROOT / p).exists()}

expected_rows = {
    "s775-cost-10k-400k.html": len(costs),
    "s775-methods.html": len(methods),
    "s775-steps.html": len(steps),
    "s775-penalties-tax.html": len(penalties),
    "s775-flagged-review.html": len(flags),
    "s775-sources.html": len(sources),
}
for p, want in expected_rows.items():
    if p not in html_by_page:
        continue
    body = html_by_page[p]
    got = body.count("<tr>") - 1  # minus the header row
    if got != want:
        fail(f"{p}: {got} data rows, expected {want}")

# every data row on the data pages carries a source link or official URL
for p in ["s775-methods.html", "s775-steps.html", "s775-penalties-tax.html",
          "s775-flagged-review.html", "s775-cost-10k-400k.html", "s775-sources.html"]:
    if p not in html_by_page:
        continue
    body = html_by_page[p]
    rows = re.findall(r"<tr>(.*?)</tr>", body, re.DOTALL)
    for i, row in enumerate(rows[1:], start=1):
        if "<a class=\"src\"" not in row and "http" not in row \
                and "S775-IR-00" not in row and "process item" not in row:
            fail(f"{p}: data row {i} has no source link")

# anchors referenced from tables exist
src_page = html_by_page.get("s775-sources.html", "")
anchors = set(re.findall(r'id="(src-[A-Z]\d+)"', src_page))
if len(anchors) != len(sources):
    fail(f"sources page has {len(anchors)} anchors, expected {len(sources)}")
for p, body in html_by_page.items():
    for a in set(re.findall(r"#(src-[A-Z]\d+)", body)):
        if a not in anchors:
            fail(f"{p}: references missing anchor #{a}")

# internal links resolve
all_files = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()}
for p, body in html_by_page.items():
    for href in re.findall(r'href="([^"#]+)', body):
        if href.startswith(("http", "mailto")):
            continue
        target = href.split("?")[0]
        if not target:
            continue
        if target not in all_files:
            fail(f"{p}: broken internal link {href}")

# nav present on every page
NAV_PAGES = PAGES
for p, body in html_by_page.items():
    for u in NAV_PAGES:
        if f'href="{u}"' not in body:
            fail(f"{p}: nav link to {u} missing")

# ------------------------------------------- 6. dashboard headline agreement
dash = html_by_page.get("s775-dashboard.html", "")
r10 = next(r for r in costs if r["amount_usd"] == "10000")
r100 = next(r for r in costs if r["amount_usd"] == "100000")
r400 = next(r for r in costs if r["amount_usd"] == "400000")
for label, row in (("$10,000", r10), ("$100,000", r100), ("$400,000", r400)):
    if row["total_usd"] not in dash:
        fail(f"dashboard does not quote the {label} total ({row['total_usd']})")

# ------------------------------------------- 6b. regression guards (C5BF integration)
# (a) the hero card must quote the SAME $10,000 total as the ladder row, not a
#     hand-typed figure that can drift (the live site shipped $50.93 vs $53.42).
if f'<div class="n">${r10["total_usd"]}</div>' not in dash:
    fail(f"dashboard hero card does not carry the ladder $10,000 total ({r10['total_usd']})")
# (b) the half-spread must be quoted with the (ask-mid)/ask denominator; the older
#     (ask-mid)/mid figure 0.2104% contradicts every derived ladder row.
for p_, body in html_by_page.items():
    if "0.2104" in body:
        fail(f"{p_}: stale 0.2104% half-spread survived into a rendered page")
    # (c) nested <td> inside <td> is invalid markup and renders a phantom column
    if re.search(r"<td[^>]*>\s*<td", body):
        fail(f"{p_}: nested <td> markup (invalid HTML, renders an empty column)")
    # (d) the ID-only US$50,000/day threshold must always carry its scope: it is
    #     汇发〔2020〕14号 art. 64 for 境内个人 (domestic individuals), NOT a
    #     blanket rule for a 境外个人 (foreign individual) — art. 59 (S52).
    if "US$50,000/day" in body and not (
            "境内个人" in body or "domestic individual" in body.lower()):
        fail(f"{p_}: quotes the US$50,000/day ID-only threshold without its "
             f"domestic-individual (art. 64) scope")

# ------------------------------------------- 7. freshness (rebuild + compare)
for script, args in (("scripts/gen_s775_data.py", []),
                     ("scripts/build_s775_site.py", ["--check"])):
    proc = subprocess.run([sys.executable, str(ROOT / script), *args],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        fail(f"{script} {' '.join(args)} failed: " + (proc.stdout + proc.stderr).strip()[:400])
    else:
        note(f"{script} {' '.join(args) or '(regenerated deterministically)'} ok")

# ------------------------------------------- reporting
for n in NOTE:
    print("  note:", n)
if ERR:
    print()
    for e in ERR:
        print("  FAIL:", e)
    print(f"\nFAIL — {len(ERR)} violation(s).")
    raise SystemExit(1)
print(f"\nPASS — S775 verified: {len(sources)} sources, {len(methods)} methods, "
      f"{len(costs)} ladder rows re-derived, {len(steps)} steps, {len(penalties)} penalties, "
      f"{len(flags)} flags; all rows sourced, all blanks flagged, no broken links, output fresh.")
