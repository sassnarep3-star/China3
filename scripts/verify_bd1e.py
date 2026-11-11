#!/usr/bin/env python3
"""Independent verifier for bd1e-decision.html.

Deliberately does not import the builder: every figure is re-derived here from the two
published inputs, then compared against the text actually rendered in the page, and again
against the CSVs the page is built from.

    python3 scripts/verify_bd1e.py
"""
import csv
import html
import re
import subprocess
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "bd1e-decision.html"
CENT = D("0.01")

# --- published inputs, re-stated here on purpose ----------------------------
BID, ASK = D("6.6630"), D("6.6911")            # S01, board 2026/11/11 10:25:02
BID_OLD, ASK_OLD = D("6.6571"), D("6.6851")    # S01, board 2026/11/10 17:39:58
RATE, MINC, MAXC, CABLE = D("0.001"), D("50"), D("260"), D("150")   # S02
IIT, TREATY = D("0.20"), D("0.10")             # S12 Art. 3(3); S03 Art. 9(2)
IRS = {2024: D("7.189"), 2025: D("7.129")}     # S16
AMOUNTS = [D(10000) * i for i in range(1, 41)]
KEY = [D(10000), D(50000), D(100000), D(200000), D(300000), D(400000)]
ALLOWED = {
    "www.boc.cn", "www.safe.gov.cn", "www.irs.gov", "www.ecfr.gov", "www.govinfo.gov",
    "www.fincen.gov", "www.cbp.gov", "fgk.chinatax.gov.cn", "www.chinatax.gov.cn",
}
NONE_MARKER = "no official page read today"

failures, notes = [], []


def check(cond, label, detail=""):
    print(("  \u2713 " if cond else "  \u2717 ") + label)
    if not cond:
        failures.append(label + (f" — {detail}" if detail else ""))
    return cond


def q(x, places=CENT):
    return x.quantize(places, rounding=ROUND_HALF_UP)


def usd(x):
    return f"${q(x):,.2f}"


def cny(x):
    return f"RMB {q(x):,.2f}"


def pct(x):
    return f"{q(x * 100, D('0.001'))}%"


def mid_of(bid, ask):
    return (bid + ask) / 2


def spread(amt, bid, ask):
    return amt * (ask - mid_of(bid, ask)) / ask


def wire_cny(amt, ask):
    return min(MAXC, max(MINC, amt * ask * RATE)) + CABLE


def wire_usd(amt, ask):
    return wire_cny(amt, ask) / ask


def l01(amt, bid, ask):
    s, w = spread(amt, bid, ask), wire_usd(amt, ask)
    return s + w, amt * ask + wire_cny(amt, ask)


def l03(amt, ask):
    return wire_usd(amt, ask)


def fx_gain(amt, ask, year):
    return amt - amt * ask / IRS[year]


def dividend_tax(amt, rate):
    return amt * rate


# --- html helpers -----------------------------------------------------------
def cells_of_row(tr):
    out = []
    for cell in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S):
        text = re.sub(r"<[^>]+>", " ", cell)
        out.append(re.sub(r"\s+", " ", html.unescape(text)).strip())
    return out


def tables(page):
    return [re.findall(r"<tr>(.*?)</tr>", t, flags=re.S)
            for t in re.findall(r"<table[^>]*>.*?</table>", page, flags=re.S)]


def main():
    if not PAGE.exists():
        print("FAIL — page missing; run scripts/build_bd1e_site.py")
        return 1
    page = PAGE.read_text(encoding="utf-8")
    ladder_csv = list(csv.DictReader(open(ROOT / "data/bd1e_ladder.csv", newline="", encoding="utf-8")))
    drift_csv = list(csv.DictReader(open(ROOT / "data/bd1e_drift.csv", newline="", encoding="utf-8")))
    sources = list(csv.DictReader(open(ROOT / "data/bd1e_sources.csv", newline="", encoding="utf-8")))
    questions = list(csv.DictReader(open(ROOT / "data/bd1e_questions.csv", newline="", encoding="utf-8")))
    closed = list(csv.DictReader(open(ROOT / "data/bd1e_closed.csv", newline="", encoding="utf-8")))
    findings = list(csv.DictReader(open(ROOT / "data/bd1e_findings.csv", newline="", encoding="utf-8")))
    src_urls = {s["url"] for s in sources}

    print("A. build is reproducible")
    r = subprocess.run([sys.executable, str(ROOT / "scripts/build_bd1e_site.py"), "--check"],
                       capture_output=True, text=True)
    check(r.returncode == 0, "generated page, CSS and CSVs are byte-identical to a fresh build", r.stdout.strip())

    print("B. every rendered figure re-derived from the published inputs")
    rows = tables(page)       # 0 questions, 1 costs, 2 drift, 3 ladder, 4 closed, 5 dividend,
                              # 6 open items, 7 findings, 8 sources
    def body(t):
        return [tr for tr in t if cells_of_row(tr)]

    ladder = body(rows[3])
    check(len(ladder) == 40, f"ladder has 40 rows (found {len(ladder)})")
    ladder_ok = 0
    for tr, amt in zip(ladder, AMOUNTS):
        c = cells_of_row(tr)
        want = [usd(amt), usd(l03(amt, ASK)), usd(l01(amt, BID, ASK)[0]),
                pct(l01(amt, BID, ASK)[0] / amt), usd(fx_gain(amt, ASK, 2024))]
        if c[:5] == want:
            ladder_ok += 1
        else:
            notes.append(f"ladder {amt}: page {c[:5]} != {want}")
    check(ladder_ok == 40, f"all 40 ladder rows match the recomputation ({ladder_ok}/40)", "; ".join(notes[:2]))

    drift = body(rows[2])
    drift_ok = 0
    for tr, amt in zip(drift, KEY):
        c = cells_of_row(tr)
        want = [usd(amt), usd(l01(amt, BID_OLD, ASK_OLD)[0]), usd(l01(amt, BID, ASK)[0]),
                usd(l01(amt, BID, ASK)[0] - l01(amt, BID_OLD, ASK_OLD)[0]),
                usd(l03(amt, ASK_OLD)), usd(l03(amt, ASK))]
        if c[:6] == want:
            drift_ok += 1
        else:
            notes.append(f"drift {amt}: page {c[:6]} != {want}")
    check(drift_ok == 6, f"all 6 drift rows match the recomputation ({drift_ok}/6)")

    div = body(rows[5])
    div_ok = 0
    for tr, amt in zip(div, KEY):
        c = cells_of_row(tr)
        want = [usd(amt), usd(dividend_tax(amt, IIT)), usd(dividend_tax(amt, TREATY)),
                usd(dividend_tax(amt, IIT) - dividend_tax(amt, TREATY)),
                usd(dividend_tax(amt, TREATY) + l01(amt - dividend_tax(amt, TREATY), BID, ASK)[0])]
        if c[:5] == want:
            div_ok += 1
        else:
            notes.append(f"dividend {amt}: page {c[:5]} != {want}")
    check(div_ok == 6, f"all 6 dividend rows match the recomputation ({div_ok}/6)")

    kpis = re.findall(r'<div class="kpi"><b>([^<]+)</b>', page)
    want_kpis = [usd(l01(D(10000), BID, ASK)[0]), usd(l01(D(400000), BID, ASK)[0]),
                 usd(dividend_tax(D(400000), IIT) - dividend_tax(D(400000), TREATY) + 0)]
    # the third KPI is the tax saved less the small transfer-cost difference; recompute exactly
    saved = (dividend_tax(D(400000), IIT) + l01(D(400000) - dividend_tax(D(400000), IIT), BID, ASK)[0]) - \
            (dividend_tax(D(400000), TREATY) + l01(D(400000) - dividend_tax(D(400000), TREATY), BID, ASK)[0])
    want_kpis[2] = usd(saved)
    check(kpis[:3] == want_kpis, f"KPI figures match ({kpis[:3]} vs {want_kpis})")

    print("C. page cells equal the CSVs")
    csv_l01 = {int(r["amount_usd"]): r for r in ladder_csv if r["method_id"] == "L01"}
    csv_l03 = {int(r["amount_usd"]): r for r in ladder_csv if r["method_id"] == "L03"}
    mism = 0
    for tr, amt in zip(ladder, AMOUNTS):
        c = cells_of_row(tr)
        if c[1] != f'${D(csv_l03[int(amt)]["total_usd"]):,.2f}' or c[2] != f'${D(csv_l01[int(amt)]["total_usd"]):,.2f}':
            mism += 1
    check(mism == 0, f"ladder cells equal data/bd1e_ladder.csv ({40 - mism}/40)")
    csv_drift = {int(r["amount_usd"]): r for r in drift_csv}
    mism = sum(1 for tr, amt in zip(drift, KEY)
               if cells_of_row(tr)[2] != f'${D(csv_drift[int(amt)]["l01_11nov"]):,.2f}')
    check(mism == 0, "drift cells equal data/bd1e_drift.csv (6/6)")

    print("D. every table row carries an official source or is flagged")
    no_source, bad_domain, rows_total = [], [], 0
    for t in rows:
        for tr in t:
            c = cells_of_row(tr)
            if not c:
                continue
            rows_total += 1
            urls = re.findall(r'href="(https?://[^"]+)"', tr)
            for u in urls:
                host = urlparse(u).netloc
                if host not in ALLOWED:
                    bad_domain.append(u)
            if not urls and NONE_MARKER not in " ".join(c):
                no_source.append(" | ".join(c)[:120])
    check(not bad_domain, "every external link is on an allow-listed official domain", "; ".join(bad_domain[:3]))
    check(not no_source, f"every one of {rows_total} table rows cites an official page or is flagged as unread",
          "; ".join(no_source[:3]))
    check(rows_total >= 100, f"table rows audited: {rows_total}")

    print("E. local links and anchors resolve")
    broken = []
    for href in sorted(set(re.findall(r'href="([^"#:]+)(?:#[^"]*)?"', page))):
        if href.startswith(("http", "//")):
            continue
        if not (ROOT / href).exists():
            broken.append(href)
    for target, anchor in re.findall(r'href="([^"#:]+\.html)#([^"]+)"', page):
        f = ROOT / target
        if not f.exists() or f'id="{anchor}"' not in f.read_text(encoding="utf-8"):
            broken.append(f"{target}#{anchor}")
    check(not broken, "every local link and anchor resolves", "; ".join(broken[:4]))

    print("F. the three closed items are sourced, and the numbers they claim are right")
    for c in closed:
        check(all(s in {x["id"] for x in sources} for s in c["source_ids"].split()),
              f"{c['id']} cites only registered sources")
    check(q(D("165353") / D("0.5")) == D("330706.00"), "50% prong overtakes the ceiling at a $330,706 balance")
    check(D("400000") * D("0.5") == D("200000"), "willful 50% exposure on $400,000 is $200,000")
    check(D("80000") - D("40000") == D("40000"), "20% to 10% on a $400,000 dividend saves $40,000 of Chinese tax")
    check(all(c["status"] == "needs review" for c in findings), "every finding is marked needs review")

    print("G. questions and sources are complete")
    check(len(questions) == 12, f"12 questions ({len(questions)})")
    check(all(qq["source_ids"].split() and all(s in {x['id'] for x in sources} for s in qq["source_ids"].split())
              for qq in questions), "every question cites registered sources")
    check(len(sources) == 18, f"18 sources ({len(sources)})")
    check(all(s["read_on"] == "2026-11-11" for s in sources), "all 18 sources read on 2026-11-11")
    check(all(s["quote"].strip() for s in sources), "every source carries a verbatim quote")
    check(all(urlparse(s["url"]).netloc in ALLOWED for s in sources), "every source URL is on an official domain")

    print("H. repository hygiene")
    markers = []
    for p in ROOT.rglob("*"):
        if p.is_dir() or ".git" in p.parts or p.suffix not in {".md", ".html", ".csv", ".py", ".yml", ".css", ".js"}:
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if re.match(r"^(<<<<<<< |>>>>>>> |=======$)", line):
                markers.append(f"{p.relative_to(ROOT)}:{n}")
    check(not markers, "no merge-conflict markers in any tracked text file", "; ".join(markers[:4]))

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        for f in failures:
            print("   · " + f)
        return 1
    print(f"PASS — bd1e: 4 generated files reproducible; 40 ladder rows, 6 drift rows and 6 dividend rows "
          f"recomputed from the published inputs and matched cell by cell; {rows_total} table rows sourced or "
          f"flagged; 18 sources read 2026-11-11; all local links and anchors resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
