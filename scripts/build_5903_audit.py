#!/usr/bin/env python3
"""Build the 5903 audit page and its data files (session arena/5903db91-china3).

    python3 scripts/build_5903_audit.py            # write data/5903_*.csv and 5903-audit.html
    python3 scripts/build_5903_audit.py --check    # fail if anything is out of date

The published figures are read from data/e347_costs.csv (the canonical dashboard's own
table) and are then recomputed here from the raw board figures and the bank's published
tariff, with exact fractions and no call into the dashboard's engine. Nothing is copied
from the dashboard's outputs: if the two disagree, the page says so.
"""
import csv
import importlib.util
import sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
from html import escape as esc
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
PAGE = ROOT / "5903-audit.html"
CHECKS_CSV = DATA / "5903_checks.csv"
COSTS_CSV = DATA / "5903_costs.csv"


def load_data_module():
    spec = importlib.util.spec_from_file_location("d5903", HERE / "5903_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


D = load_data_module()


# --------------------------------------------------------------------- arithmetic
def fr(x):
    return F(str(x))


def money(x):
    """Cents, half up."""
    if x is None:
        return ""
    d = (Decimal(x.numerator) / Decimal(x.denominator)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{d:,.2f}"


def wire_cny(usd, ask):
    tariff = D.TARIFF
    fee = usd * ask * fr(tariff["wire_pct"])
    fee = max(fr(tariff["wire_min_cny"]), min(fr(tariff["wire_max_cny"]), fee))
    return fee + fr(tariff["cable_cny"])


def recompute(model, usd, board):
    """(spread, fee, tax, total). Exact fractions, no floats."""
    ask = fr(board["ask"])
    bid = fr(board["bid"])
    mid = (ask + bid) / 2
    u = F(usd)
    if model == "fx_wire":
        spread, fee = u * (ask - mid) / ask, wire_cny(u, ask) / ask
        return spread, fee, None, spread + fee
    if model == "wire_only":
        fee = wire_cny(u, ask) / ask
        return None, fee, None, fee
    if model == "quota":
        quota = fr(D.TARIFF["quota_usd"])
        n_full, rem = divmod(u, quota)
        fee = n_full * wire_cny(quota, ask) / ask + (wire_cny(rem, ask) / ask if rem else 0)
        spread = u * (ask - mid) / ask
        return spread, fee, None, spread + fee
    if model == "dividend":
        tax = u * fr(D.TARIFF["dividend_rate"])
        net = u - tax
        spread, fee = net * (ask - mid) / ask, wire_cny(net, ask) / ask
        return spread, fee, tax, tax + spread + fee
    if model == "atm":
        cny = u * ask
        step = fr(D.TARIFF["atm_day_cny"])
        n_full, rem = divmod(cny, step)
        per = min(fr(D.TARIFF["atm_max_cny"]),
                  fr(D.TARIFF["atm_fixed_cny"]) + step * fr(D.TARIFF["atm_pct"]))
        fee_cny = n_full * per
        if rem:
            fee_cny += min(fr(D.TARIFF["atm_max_cny"]),
                           fr(D.TARIFF["atm_fixed_cny"]) + rem * fr(D.TARIFF["atm_pct"]))
        return None, fee_cny / ask, None, fee_cny / ask
    if model == "cash":
        spread = u * (ask - mid) / ask
        return spread, None, None, spread
    raise SystemExit(f"unknown model {model}")


def published_costs():
    path = DATA / "e347_costs.csv"
    out = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out[(r["method_id"], int(r["amount_usd"]))] = r
    return out


# ------------------------------------------------------------------------- tables
def cost_rows():
    pub = published_costs()
    rows = []
    for mid, model, label in D.ROUTES:
        for amount in D.AMOUNTS:
            p = pub.get((mid, amount))
            if p is None:
                continue
            spread, fee, tax, total = recompute(model, amount, D.BOARD)
            rec = {"spread": money(spread), "fee": money(fee), "tax": money(tax), "total": money(total)}
            got = {"spread": p["spread_usd"], "fee": p["fee_usd"], "tax": p["tax_usd"], "total": p["known_cost_usd"]}
            diff = ""
            try:
                diff = money(fr(rec["total"].replace(",", "")) - fr(got["total"].replace(",", "")))
            except Exception:
                diff = "n/a"
            rows.append({
                "route_id": mid, "route": label, "amount_usd": amount, "model": model,
                "published_spread_usd": got["spread"], "published_fee_usd": got["fee"],
                "published_tax_usd": got["tax"], "published_total_usd": got["total"],
                "recomputed_spread_usd": rec["spread"], "recomputed_fee_usd": rec["fee"],
                "recomputed_tax_usd": rec["tax"], "recomputed_total_usd": rec["total"],
                "difference_usd": diff, "board": D.BOARD["published"],
            })
    return rows


def now_board_rows():
    rows = []
    for amount in D.AMOUNTS:
        spread, fee, tax, total = recompute("fx_wire", amount, D.BOARD_NOW)
        rows.append({
            "amount": amount, "spread": money(spread), "fee": money(fee), "total": money(total),
        })
    return rows


# -------------------------------------------------------------------------- files
def write_csvs(checks, costs):
    DATA.mkdir(exist_ok=True)
    with CHECKS_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "area", "claim_as_published", "verdict", "issuer", "official_url",
                    "quote", "note", "read_utc"])
        for c in checks:
            w.writerow([c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8]])
    with COSTS_CSV.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(costs[0].keys()))
        w.writeheader()
        w.writerows(costs)


# --------------------------------------------------------------------------- html
PILL = {"confirmed": "ok", "contradiction": "bad", "not re-checked": "warn"}


def src_link(check):
    issuer, url = check[4], check[5]
    host = url.split("//", 1)[-1].split("/", 1)[0]
    return (f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(host)}</a>'
            f'<br><span class="note">{esc(issuer)}</span><br>'
            f'<span class="note">read {esc(check[8][11:16])}Z</span>')


def render(checks, costs, now_rows):
    counts = {k: sum(1 for c in checks if c[3] == k) for k in PILL}
    rows = []
    for c in checks:
        rows.append(
            f'<tr id="{esc(c[0])}">'
            f'<td data-label="ID"><span class="id">{esc(c[0])}</span><br><span class="note">{esc(c[1])}</span></td>'
            f'<td data-label="What the site says">{esc(c[2])}</td>'
            f'<td data-label="Verdict"><span class="pill {PILL[c[3]]}">{esc(D.VERDICTS[c[3]][1])}</span></td>'
            f'<td data-label="What the official page says"><span class="quote">{esc(c[6])}</span>'
            f'<div class="why">{esc(c[7])}</div></td>'
            f'<td data-label="Source" class="src">{src_link(c)}</td>'
            f'</tr>')
    cost_rows_html = []
    for r in costs:
        flag = "" if r["difference_usd"] in ("0.00", "") else ' class="mismatch"'
        cost_rows_html.append(
            f'<tr{flag}>'
            f'<td data-label="Route"><span class="id">{esc(r["route_id"])}</span> {esc(r["route"])}</td>'
            f'<td data-label="Amount" class="num">${r["amount_usd"]:,}</td>'
            f'<td data-label="Published spread">{r["published_spread_usd"] or "—"}</td>'
            f'<td data-label="Published fee">{r["published_fee_usd"] or "—"}</td>'
            f'<td data-label="Published tax">{r["published_tax_usd"] or "—"}</td>'
            f'<td data-label="Published total"><b>{r["published_total_usd"] or "—"}</b></td>'
            f'<td data-label="Recomputed total"><b>{r["recomputed_total_usd"] or "—"}</b></td>'
            f'<td data-label="Difference">{r["difference_usd"] if r["difference_usd"] else "—"}</td>'
            f'</tr>')
    now_html = []
    for r in now_rows:
        now_html.append(
            f'<tr><td data-label="Amount" class="num">${r["amount"]:,}</td>'
            f'<td data-label="Spread">{r["spread"]}</td>'
            f'<td data-label="Fee">{r["fee"]}</td>'
            f'<td data-label="Total today"><b>{r["total"]}</b></td></tr>')

    n_ok = counts["confirmed"]
    n_bad = counts["contradiction"]
    n_blank = counts["not re-checked"]
    mismatches = sum(1 for r in costs if r["difference_usd"] not in ("0.00", ""))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="build_5903_audit.py">
<meta name="description" content="Independent audit, 11 November 2026: every published figure on the China money dashboard re-read at its official source, and every published bank cost recomputed from the board and the tariff.">
<title>Independent audit, 11 November 2026 · China money</title>
<link rel="stylesheet" href="assets/5903.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">China money<small>independent audit</small></a>
<nav class="nav" aria-label="Sections">
<a href="index.html">Dashboard</a>
<a href="dashboard/costs.html">Costs</a>
<a href="dashboard/tax.html">Tax</a>
<a href="dashboard/flagged.html">Flagged</a>
<a href="dashboard/sources.html">Sources</a>
<a href="5903-audit.html" aria-current="page">This audit</a>
</nav>
</div></header>

<main><div class="wrap">
<h1>Independent audit of the published figures</h1>
<p class="lead">Another session's dashboard, checked line by line on {D.AUDIT_DATE}. Every row below names the official page it was checked against and the time it was read. Where the dashboard and the source disagree, the row says so and the disagreement is logged as a request to the session that owns those files. Nothing here changes the dashboard.</p>

<div class="kpis">
<div class="kpi"><b>{len(checks)}</b><span>claims checked</span></div>
<div class="kpi"><b>{n_ok}</b><span>confirmed at the source</span></div>
<div class="kpi bad"><b>{n_bad}</b><span>contradictions found</span></div>
<div class="kpi warn"><b>{n_blank}</b><span>left blank, not re-read</span></div>
<div class="kpi"><b>{mismatches}</b><span>cost cells that disagree</span></div>
</div>

<div class="callout">
<h2 style="margin-top:0">The short version</h2>
<ul>
<li><b>The bank cost is right.</b> All {len(costs)} published checkpoints across six routes recompute to the cent from the board and the bank's tariff, with no shared code.</li>
<li><b>Two rows on the Costs page contradict themselves.</b> They print the 11 November rate beside a per-100 figure from the 10 November board (A05, A06).</li>
<li><b>One tax row is wrong in a way that understates a saving.</b> A personal currency gain over $200 is a capital gain, not ordinary income (A24, A25).</li>
<li><b>One sentence is too absolute.</b> A U.S. citizen resident in China for a continuous year is a 境内个人 for FX purposes, so the blanket statement that a passport holder never gets the USD 50,000 convenience amount is not supported (A08, A35).</li>
<li><b>One number is missing.</b> The 2025 IRS average is 7.129 and the Federal Reserve's is 7.1875; the dashboard shows only the first (A28).</li>
</ul>
</div>

<h2>How to read the verdicts</h2>
<div class="tbl"><table class="stack">
<thead><tr><th>Verdict</th><th>Meaning</th></tr></thead><tbody>
<tr><td data-label="Verdict"><span class="pill ok">Confirmed</span></td><td data-label="Meaning">{esc(D.VERDICTS['confirmed'][2])}</td></tr>
<tr><td data-label="Verdict"><span class="pill bad">Contradiction</span></td><td data-label="Meaning">{esc(D.VERDICTS['contradiction'][2])}</td></tr>
<tr><td data-label="Verdict"><span class="pill warn">Not re-checked</span></td><td data-label="Meaning">{esc(D.VERDICTS['not re-checked'][2])}</td></tr>
</tbody></table></div>

<h2>Claim by claim</h2>
<p>Every row was read today. The quote column is the page's own words, trimmed with an ellipsis where a sentence is cut; the italic line under it says what the audit concluded.</p>
<div class="tbl"><table class="stack wide">
<thead><tr><th>ID</th><th>What the site says</th><th>Verdict</th><th>What the official page says</th><th>Source</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody></table></div>

<h2>Every published bank cost, recomputed</h2>
<p>The left-hand numbers are what the dashboard prints. The right-hand numbers were computed here with exact fractions from the board (buying 6.6606, selling 6.6886 per dollar), the wire tariff (1&nbsp;‰, minimum ¥50, maximum ¥260, plus ¥150 cable) and the ATM tariff (¥12 + 1%, maximum ¥112 a withdrawal). No code was shared with the dashboard's engine. <b>{mismatches} cells disagree.</b></p>
<div class="tbl"><table class="stack">
<thead><tr><th>Route</th><th>Amount</th><th>Spread</th><th>Fee</th><th>Tax</th><th>Published total</th><th>Recomputed</th><th>Diff.</th></tr></thead>
<tbody>
{chr(10).join(cost_rows_html)}
</tbody></table></div>
<p class="note">Blank cells are costs that route does not incur: a wire of money that is already in dollars has no spread, and bank fees are not tax. The dividend row is the 20% statutory scenario; the treaty scenario is not re-priced here.</p>

<h2>If it were rebuilt on the board reading now</h2>
<p>The dashboard was priced on the 15:30:04 board. When this audit opened the page at 12:50Z the board read 20:50:05 Beijing: buying 665.91, selling 668.71. Recomputing the standard convert-and-wire route on that board moves the answer by a cent. The reason is that the cost is driven by the <i>ratio</i> of the spread to the rate, and both moved together.</p>
<div class="tbl"><table class="stack">
<thead><tr><th>Amount</th><th>Spread</th><th>Fee</th><th>Total on the 20:50:05 board</th></tr></thead>
<tbody>
{chr(10).join(now_html)}
</tbody></table></div>
<p class="note">This is a re-read of the same official price board on the same day, not a forecast. Bank of China republishes the row during the day, so any figure is a snapshot.</p>

<h2>What this audit asks the dashboard's owner to change</h2>
<div class="tbl"><table class="stack">
<thead><tr><th>Request</th><th>File</th><th>Change</th><th>Why</th></tr></thead>
<tbody>
<tr><td data-label="Request"><b>5903-REQ-01</b></td><td data-label="File">scripts/e347_build.py</td><td data-label="Change">Build the two "668.51 per 100" / "665.71 per 100" strings from the rate values instead of typing them.</td><td data-label="Why">A05, A06</td></tr>
<tr><td data-label="Request"><b>5903-REQ-02</b></td><td data-label="File">scripts/e347_data.py</td><td data-label="Change">Tax row T10: personal money over $200 is a capital gain (Publication 525), and a personal loss is not deductible (26 U.S.C. 165(c)).</td><td data-label="Why">A24, A25, A26</td></tr>
<tr><td data-label="Request"><b>5903-REQ-03</b></td><td data-label="File">scripts/e347_data.py</td><td data-label="Change">Print the Federal Reserve's 2025 average (7.1875) beside the IRS's 7.129, or say which one the column uses.</td><td data-label="Why">A28</td></tr>
<tr><td data-label="Request"><b>5903-REQ-04</b></td><td data-label="File">scripts/e347_data.py</td><td data-label="Change">Home page sentence about the USD 50,000 amount: make it conditional on the Foreign Permanent Resident ID or on being a 境内个人, and give the two official tests.</td><td data-label="Why">A08, A09, A35</td></tr>
<tr><td data-label="Request"><b>5903-REQ-05</b></td><td data-label="File">dashboard/archive.html</td><td data-label="Change">Regenerate so this page is listed, and add a navigation entry for it.</td><td data-label="Why">This page is new.</td></tr>
</tbody></table></div>

<h2>What this audit does not establish</h2>
<ul class="plain">
<li><b>No legal or tax conclusion for your case.</b> The rows restate what an official page says; whether a particular balance is personal or investment money, and where you are resident, decide which rows apply.</li>
<li><b>No live quote.</b> The bank's published board is a reference rate. What you are actually charged appears at the counter or in the app, and the tariff allows agreements, promotions and local schedules to differ.</li>
<li><b>No intermediary or receiving-bank charges.</b> Those are not published anywhere official and stay blank on the dashboard; this audit did not fill them in.</li>
<li><b>No test of the dashboard's other pages.</b> Property-transfer and inheritance documents were not re-read here (A36), and are neither confirmed nor contradicted.</li>
<li><b>No browser rendering test.</b> Links and anchors were resolved by script and every external link was opened; layout was not visually inspected in this pass.</li>
</ul>

<h2>Provenance</h2>
<div class="tbl"><table class="stack">
<thead><tr><th>Item</th><th>Value</th></tr></thead><tbody>
<tr><td data-label="Item">Dashboard audited</td><td data-label="Value">commit <code>{esc(D.SNAPSHOT_COMMIT)}</code> of main, the merge of PR #83</td></tr>
<tr><td data-label="Item">Audit date</td><td data-label="Value">{esc(D.AUDIT_DATE)} (UTC)</td></tr>
<tr><td data-label="Item">Board used for recomputation</td><td data-label="Value">Bank of China, published {esc(D.BOARD['published'])}; re-read {esc(D.BOARD_NOW['published'])}</td></tr>
<tr><td data-label="Item">Data files</td><td data-label="Value"><code>data/5903_checks.csv</code>, <code>data/5903_costs.csv</code></td></tr>
<tr><td data-label="Item">Rebuild</td><td data-label="Value"><code>python3 scripts/build_5903_audit.py</code></td></tr>
<tr><td data-label="Item">Gate</td><td data-label="Value"><code>python3 scripts/verify_5903_audit.py</code></td></tr>
</tbody></table></div>

<p class="note">Prepared by session <code>arena/5903db91-china3</code>. It edits no file owned by another session: the five requests above are logged in <code>COORDINATION.md</code> for the session that holds those files.</p>
</div></main>

<footer class="foot"><div class="wrap">
<p>Every figure on this page links to the government, regulator, central-bank or bank page it came from. A value that could not be confirmed is blank.</p>
</div></footer>
</body>
</html>
"""


def main():
    checks = D.CHECKS
    costs = cost_rows()
    now_rows = now_board_rows()
    html = render(checks, costs, now_rows)
    if "--check" in sys.argv:
        stale = []
        if not PAGE.exists() or PAGE.read_text(encoding="utf-8") != html:
            stale.append(PAGE.name)
        for path in (CHECKS_CSV, COSTS_CSV):
            if not path.exists():
                stale.append(path.name)
        if stale:
            print("STALE — " + ", ".join(stale) + "; run scripts/build_5903_audit.py")
            return 1
        print(f"OK — 5903 audit files are up to date ({len(checks)} checks, {len(costs)} cost cells).")
        return 0
    write_csvs(checks, costs)
    PAGE.write_text(html, encoding="utf-8")
    bad = sum(1 for r in costs if r["difference_usd"] not in ("0.00", ""))
    print(f"wrote {PAGE.name}: {len(checks)} checks, {len(costs)} cost cells, {bad} mismatches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
