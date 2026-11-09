#!/usr/bin/env python3
"""Build cross-session-review.html and data/reference_check_values.csv.

Session: session-5e4816e0 (cross-session reconciliation review, tasks X1-X3).

Inputs (all hand-entered from official pages fetched on 2026-11-09, each row
carries its URL and a verbatim excerpt):
  data/reference_inputs.csv        official reference inputs (R01..R29)
  data/cross_session_findings.csv  discrepancies found in other sessions' work

Outputs (generated, deterministic):
  data/reference_check_values.csv  40 rows, USD 10,000 .. 400,000
  cross-session-review.html        stand-alone, mobile-first page

The check values use ONLY:
  * BOC published board rates (R01, R02)          -> spread vs. bank mid
  * BOC published personal e-banking tariff (R08, R09) -> wire + cable fee
  * SAFE convenience amount (R12)                 -> years if relying on it
  * IRS yearly average CNY rates (R23..R27)       -> illustrative currency gain
Anything else (intermediary fees, receiving fees, the executed rate on a real
account, the tax rate applied to a gain) is left blank and flagged.

Run:  python3 scripts/build_cross_session_review.py          (build)
      python3 scripts/build_cross_session_review.py --check  (build to memory,
                                                    fail if files are stale)
Exit code 0 = OK; 1 = a contract check failed or output is stale.
"""
from __future__ import annotations

import csv
import html
import io
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
INPUTS = DATA / "reference_inputs.csv"
FINDINGS = DATA / "cross_session_findings.csv"
OUT_CSV = DATA / "reference_check_values.csv"
OUT_HTML = ROOT / "cross-session-review.html"

URL_BOARD = "https://www.boc.cn/sourcedb/whpj/"
URL_TARIFF = "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html"
URL_SAFE_QUOTA = "https://www.safe.gov.cn/ningxia/2022/0929/1997.html"
URL_SAFE_DAILY = "https://www.safe.gov.cn/tianjin/2024/0229/2402.html"
URL_IRS_RATES = "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates"
URL_988 = ("https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/"
           "USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm")
URL_CFETS = "https://www.chinamoney.com.cn/chinese/bkccpr/"
URL_FULLAMT = "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html"


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def num(rows: dict, rid: str) -> float:
    return float(rows[rid]["value"].replace(",", ""))


def fee_cny(cny_amount: float) -> float:
    """BOC personal e-banking cross-border wire (R08) + non-HK/MO/TW cable (R09)."""
    commission = min(260.0, max(50.0, 0.001 * cny_amount))
    return commission + 150.0


def money(x: float, places: int = 0) -> str:
    if places:
        return f"${x:,.{places}f}"
    return f"${x:,.0f}"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}" rel="noopener" target="_blank">{esc(label)}</a>'


def build() -> tuple[str, str, list[str]]:
    errors: list[str] = []
    inputs = load(INPUTS)
    findings = load(FINDINGS)
    by_id = {r["id"]: r for r in inputs}

    # ---- contract checks on inputs -------------------------------------
    for r in inputs:
        if not r["source_url"].startswith(("https://", "http://")):
            errors.append(f"{r['id']}: no official source URL")
        if r["status"].startswith("UNVERIFIED"):
            if r["value"].strip():
                errors.append(f"{r['id']}: UNVERIFIED row must have a blank value")
        elif not r["verbatim_excerpt"].strip():
            errors.append(f"{r['id']}: verified row without verbatim excerpt")
    for f in findings:
        if not f["evidence_url"].startswith(("https://", "http://")):
            errors.append(f"{f['id']}: finding without evidence URL")

    buy = num(by_id, "R01") / 100.0      # 6.6638
    sell = num(by_id, "R02") / 100.0     # 6.6919
    parity = num(by_id, "R06")           # 6.7188
    quota = num(by_id, "R12")            # 50,000
    mid = (buy + sell) / 2.0             # 6.67785
    spread_pct = sell / mid - 1.0        # +0.2104 %
    vs_parity = sell / parity - 1.0      # -0.4004 %
    irs = {y: num(by_id, rid) for y, rid in
           (("2025", "R23"), ("2024", "R24"), ("2023", "R25"),
            ("2022", "R26"), ("2021", "R27"))}

    # sanity: published numbers must reproduce what the page says
    if abs(spread_pct - 0.002104) > 0.000001:
        errors.append(f"spread check failed: {spread_pct:.6%}")
    if abs(vs_parity + 0.004004) > 0.000001:
        errors.append(f"parity check failed: {vs_parity:.6%}")

    # ---- 40-row reference check table ----------------------------------
    rows = []
    for k in range(1, 41):
        a = 10000 * k
        cny = a * sell
        spread_usd = a * spread_pct
        single_fee_cny = fee_cny(cny)
        n = math.ceil(a / quota)
        chunks = [quota] * (n - 1) + [a - quota * (n - 1)]
        split_fee_cny = sum(fee_cny(c * sell) for c in chunks)
        single_total = spread_usd + single_fee_cny / sell
        split_total = spread_usd + split_fee_cny / sell
        gain24 = a * (1 - sell / irs["2024"])
        gain25 = a * (1 - sell / irs["2025"])
        rows.append({
            "amount_usd": a,
            "cny_debited_at_boc_sell": round(cny, 2),
            "spread_cost_usd": round(spread_usd, 2),
            "single_wire_fee_cny": round(single_fee_cny, 2),
            "single_wire_known_cost_usd": round(single_total, 2),
            "single_wire_known_cost_pct": round(single_total / a * 100, 4),
            "wires_if_50k_chunks": n,
            "split_wire_fees_cny": round(split_fee_cny, 2),
            "split_known_cost_usd": round(split_total, 2),
            "years_if_only_convenience_amount": n,
            "intermediary_and_receiving_fees_usd": "",
            "fx_gain_if_cny_acquired_at_2024_irs_avg_usd": round(gain24, 2),
            "fx_gain_if_cny_acquired_at_2025_irs_avg_usd": round(gain25, 2),
            "source_urls": f"{URL_BOARD} {URL_TARIFF} {URL_SAFE_QUOTA} {URL_IRS_RATES}",
            "status": ("computed from official published inputs dated 2026-11-09; "
                       "intermediary/receiving fees UNVERIFIED (blank); not a bank quote"),
        })

    # arithmetic spot checks against hand-calculated values
    r10 = rows[0]
    if abs(r10["spread_cost_usd"] - 21.04) > 0.01:
        errors.append(f"row 10k spread {r10['spread_cost_usd']}")
    if abs(r10["single_wire_fee_cny"] - (66.919 + 150)) > 0.01:
        errors.append(f"row 10k fee {r10['single_wire_fee_cny']}")
    r400 = rows[-1]
    if abs(r400["single_wire_fee_cny"] - 410) > 0.001:
        errors.append("row 400k single fee should hit the CNY 260 cap + 150")
    if abs(r400["split_wire_fees_cny"] - 8 * 410) > 0.001:
        errors.append("row 400k split fee should be 8 x 410")
    if len({r["amount_usd"] for r in rows}) != 40:
        errors.append("amount ladder is not 40 unique rows")

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    csv_text = buf.getvalue()

    # ---- HTML -----------------------------------------------------------
    src_cell = (link(URL_BOARD, "BOC board") + " · " + link(URL_TARIFF, "BOC tariff")
                + " · " + link(URL_SAFE_QUOTA, "SAFE") + " · " + link(URL_IRS_RATES, "IRS rates"))
    ladder = []
    for r in rows:
        ladder.append(
            "<tr>"
            f'<td data-l="Amount"><b>{money(r["amount_usd"])}</b></td>'
            f'<td data-l="Known bank cost (1 wire)">{money(r["single_wire_known_cost_usd"], 2)}'
            f' <small>({r["single_wire_known_cost_pct"]:.3f}%)</small></td>'
            f'<td data-l="Known cost ($50k wires)">{money(r["split_known_cost_usd"], 2)}'
            f' <small>({r["wires_if_50k_chunks"]} wire{"s" if r["wires_if_50k_chunks"] > 1 else ""})</small></td>'
            f'<td data-l="Possible U.S. taxable FX gain (2024 CNY)">{money(r["fx_gain_if_cny_acquired_at_2024_irs_avg_usd"])}</td>'
            f'<td data-l="Years at $50k/yr">{r["years_if_only_convenience_amount"]}</td>'
            '<td data-l="Intermediary + receiving fees" class="blank"><span class="tag u">blank · unverified</span></td>'
            f'<td data-l="Sources">{src_cell}</td>'
            "</tr>")

    gain_rows = []
    for y in ("2021", "2022", "2023", "2024", "2025"):
        rate = irs[y]
        g = 1 - sell / rate
        label = "gain" if g > 0 else "loss"
        gain_rows.append(
            "<tr>"
            f'<td data-l="CNY acquired in"><b>{y}</b></td>'
            f'<td data-l="IRS yearly avg (CNY per USD)">{rate:.3f}</td>'
            f'<td data-l="Per $10,000 received">{money(10000 * g)} <small>{label}</small></td>'
            f'<td data-l="Per $100,000">{money(100000 * g)}</td>'
            f'<td data-l="Per $400,000">{money(400000 * g)}</td>'
            f'<td data-l="Sources">{link(URL_IRS_RATES, "IRS yearly averages")} · {link(URL_BOARD, "BOC board")} · {link(URL_988, "26 U.S.C. 988")}</td>'
            "</tr>")

    sev_class = {"high": "h", "medium": "m", "low": "l", "informational": "i"}
    find_rows = []
    for f in findings:
        sev = f["severity"].split(" ")[0]
        find_rows.append(
            "<tr>"
            f'<td data-l="ID"><b>{esc(f["id"])}</b> <span class="tag {sev_class.get(sev, "i")}">{esc(sev)}</span></td>'
            f'<td data-l="Where">{esc(f["target"])}<br><small>{esc(f["where"])}</small></td>'
            f'<td data-l="Finding">{esc(f["finding"])}</td>'
            f'<td data-l="Request to">{esc(f["request_to"])}</td>'
            f'<td data-l="Official evidence">{link(f["evidence_url"], "source ↗")}</td>'
            f'<td data-l="Status"><span class="tag u">{esc(f["status"])}</span></td>'
            "</tr>")

    in_rows = []
    for r in inputs:
        unv = r["status"].startswith("UNVERIFIED")
        in_rows.append(
            "<tr>"
            f'<td data-l="ID"><b>{esc(r["id"])}</b></td>'
            f'<td data-l="Input">{esc(r["input"])}</td>'
            f'<td data-l="Value"{" class=blank" if unv else ""}>{esc(r["value"])} <small>{esc(r["unit"]) if r["value"] else ""}</small></td>'
            f'<td data-l="As of">{esc(r["as_of"])}</td>'
            f'<td data-l="Verbatim (original language)"><q>{esc(r["verbatim_excerpt"])}</q></td>'
            f'<td data-l="Source">{link(r["source_url"], r["source_authority"])}</td>'
            f'<td data-l="Status"><span class="tag {"u" if unv else "v"}">{esc(r["status"])}</span></td>'
            "</tr>")

    g24_10k = 10000 * (1 - sell / irs["2024"])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cross-session review · official reference inputs · China3</title>
<meta name="description" content="Independent check of the CNY to USD cost numbers against official sources fetched 2026-11-09.">
<style>
:root{{--bg:#f7f8fa;--s:#fff;--p:#1f4e79;--t:#22303c;--m:#5d6b79;--b:#d5dde5;--r:8px}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--t);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
a{{color:var(--p)}}header{{background:var(--p);color:#fff;padding:14px 16px}}header a{{color:#fff}}
nav{{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:14px;margin-top:6px}}
main{{max-width:1150px;margin:auto;padding:16px}}h1{{font-size:1.45rem;margin:.2rem 0}}h2{{font-size:1.2rem;margin-top:2rem;border-bottom:2px solid var(--b);padding-bottom:4px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:14px 0}}
.card{{background:var(--s);border:1px solid var(--b);border-radius:var(--r);padding:12px}}.card b{{display:block;font-size:1.5rem;color:var(--p)}}.card small{{color:var(--m)}}
.note{{background:#fff7ed;border-left:4px solid #b45309;padding:10px 12px;border-radius:4px}}
.ok{{background:#e9f4ee;border-left:4px solid #1e6b44;padding:10px 12px;border-radius:4px}}
table{{width:100%;border-collapse:collapse;background:var(--s);font-size:14px}}th,td{{border-bottom:1px solid var(--b);padding:8px;text-align:left;vertical-align:top}}
th{{background:#eef2f6;position:sticky;top:0}}td.blank{{background:#fffbea}}small{{color:var(--m)}}q{{font-size:13px;color:#3b4652}}
.tag{{display:inline-block;font-size:11px;padding:1px 6px;border-radius:10px;white-space:nowrap}}.tag.u{{background:#fff3cd;color:#7a5b00}}.tag.v{{background:#e9f4ee;color:#1e6b44}}
.tag.h{{background:#fdeceb;color:#b3261e}}.tag.m{{background:#fff3cd;color:#7a5b00}}.tag.l,.tag.i{{background:#eef2f6;color:#3b4652}}
details{{background:var(--s);border:1px solid var(--b);border-radius:var(--r);padding:8px 12px;margin:10px 0}}summary{{cursor:pointer;font-weight:600}}
footer{{color:var(--m);font-size:13px;padding:20px 16px;max-width:1150px;margin:auto}}
@media (max-width:760px){{
 table,thead,tbody,tr,td{{display:block;width:100%}}thead{{display:none}}
 tr{{background:var(--s);border:1px solid var(--b);border-radius:var(--r);margin:0 0 10px;padding:6px 8px}}
 td{{border:0;padding:4px 0;display:flex;gap:10px;justify-content:space-between}}
 td::before{{content:attr(data-l);font-weight:600;color:var(--m);flex:0 0 44%;font-size:12px}}
 td>*{{text-align:right}}
}}
</style>
</head>
<body>
<header>
<div><a href="index.html">China3</a> · Cross-session review</div>
<nav><a href="index.html">Home</a><a href="costs.html">Cost comparison</a><a href="cost-review.html">Cost flags</a><a href="deep-review.html">Flagged for Review</a><a href="deep-sources.html">Sources</a><a href="#ladder">$10k–$400k check table</a><a href="#gain">U.S. FX-gain tax</a><a href="#findings">Findings</a><a href="#inputs">Official inputs</a></nav>
</header>
<main>
<h1>Cross-session review: official reference inputs and discrepancies</h1>
<p>Session <code>session-5e4816e0</code> · every number below was read from an official page on <b>2026-11-09</b> and carries its link and an original-language excerpt. This page checks the cost numbers that several parallel sessions are producing; it is not a bank quote and not tax advice.</p>

<div class="cards">
<div class="card"><small>BOC board half-spread (customer buys USD)</small><b>{spread_pct * 100:.3f}%</b><small>{link(URL_BOARD, "BOC board")} 2026-11-09 09:15:45: sell 669.19 vs. mid of 666.38/669.19</small></div>
<div class="card"><small>BOC personal e-banking wire to the U.S.</small><b>max ¥410/wire</b><small>1‰ (¥50–¥260) + ¥150 cable · {link(URL_TARIFF, "BOC tariff")}</small></div>
<div class="card"><small>Possible U.S. taxable currency gain if the CNY was acquired at the 2024 IRS average</small><b>{g24_10k / 100:.2f}% of USD received</b><small>{money(g24_10k)} per $10,000 · {link(URL_IRS_RATES, "IRS")} · {link(URL_988, "§988")}</small></div>
<div class="card"><small>Using only the USD 50,000 convenience amount (one person)</small><b>8 years for $400k</b><small>it is not a cap — documented transactions can exceed it · {link(URL_SAFE_QUOTA, "SAFE")}</small></div>
</div>

<p class="note"><b>Most important finding.</b> On the lawful bank route, the published bank costs are small — about 0.21% spread plus at most ¥410 per wire (intermediary and U.S. receiving fees are extra and unverified). The cost that can be large is <b>U.S. tax on currency gain</b>: the CNY has strengthened from an IRS yearly average of 7.189 per USD (2024) to a BOC selling rate of 6.6919 (2026-11-09). If your CNY was acquired near 2024 rates, converting it realises a currency gain of roughly 6.9% of the dollars received, and 26 U.S.C. 988 treats disposing of a foreign-currency bank deposit as a currency transaction. Whether the gain is excluded (personal transaction, gain ≤ $200), capital, or ordinary income depends on facts that were not supplied — so the tax amount is left blank. China has no tax on the conversion itself in any official source reviewed (see IR-011 on {link("deep-review.html", "Flagged for Review")}).</p>

<h2 id="ladder">Reference check table: USD 10,000 → 400,000</h2>
<p>Route assumed for the check: Bank of China personal e-banking, buy USD from a CNY account at the published 现汇卖出价, one cross-border wire to a U.S. bank (non-HK/Macau/Taiwan cable fee). "Known bank cost" = spread vs. BOC's own mid + BOC wire commission + cable fee, converted at the selling rate. "$50k wires" = the same amount sent as USD 50,000 wires (SAFE's daily documentation threshold for remitting from an FX account is USD 50,000 — {link(URL_SAFE_DAILY, "SAFE Tianjin")}). The FX-gain column is a <i>gain amount</i>, not a tax: it assumes the CNY cost basis equals the 2024 IRS yearly average and that none of it is excluded.</p>
<div class="table"><table>
<thead><tr><th>Amount</th><th>Known bank cost (1 wire)</th><th>Known cost ($50k wires)</th><th>Possible U.S. taxable FX gain (2024 CNY)</th><th>Years at $50k/yr</th><th>Intermediary + receiving fees</th><th>Sources</th></tr></thead>
<tbody>
{chr(10).join(ladder)}
</tbody></table></div>
<p><small>Machine-readable: <a href="data/reference_check_values.csv">data/reference_check_values.csv</a> (also includes the CNY debited and the 2025-basis gain). Formula: spread = A × (6.6919 / 6.67785 − 1); fee (CNY) = min(260, max(50, 0.001 × A × 6.6919)) + 150 per wire; gain = A × (1 − 6.6919 / basis rate).</small></p>

<h2 id="gain">U.S. currency-gain exposure by year the CNY was acquired</h2>
<p>Illustration using the IRS's own yearly average rates as the cost basis (your real basis is the spot rate on the day the CNY was received — {link(URL_IRS_RATES, "IRS")}). Positive = gain realised on conversion at 6.6919.</p>
<table>
<thead><tr><th>CNY acquired in</th><th>IRS yearly avg (CNY per USD)</th><th>Per $10,000 received</th><th>Per $100,000</th><th>Per $400,000</th><th>Sources</th></tr></thead>
<tbody>
{chr(10).join(gain_rows)}
</tbody></table>
<details><summary>How the tax law applies (what is verified, what is not)</summary>
<ul>
<li>Verified: disposing of nonfunctional currency, including "demand or time deposits … issued by a bank", is a section 988 transaction — {link(URL_988, "26 U.S.C. 988(c)(1)(C)")}.</li>
<li>Verified: for an individual's <i>personal</i> transaction, gain is not recognised unless it exceeds $200 on the transaction — {link(URL_988, "988(e)(2)")}.</li>
<li>Verified: a transaction is not "personal" to the extent its expenses qualify under section 162 (business) or 212 (investment) — {link(URL_988, "988(e)(3)")}; section 988 gain is ordinary income — {link(URL_988, "988(a)(1)(A)")}.</li>
<li><b>Unverified (blank):</b> whether CNY savings in a Chinese deposit account are "personal" or section-212 holdings for this taxpayer; the resulting character (capital vs. ordinary); the tax rate; whether a loss (2021 row) is deductible. These need a U.S. tax professional and the actual acquisition dates.</li>
</ul></details>

<h2 id="findings">Findings: discrepancies in the parallel sessions' work</h2>
<p>Logged as requests to the owning session (this session did not edit their files). All are published here as <b>needs review</b> and do not block anything.</p>
<table>
<thead><tr><th>ID</th><th>Where</th><th>Finding</th><th>Request to</th><th>Official evidence</th><th>Status</th></tr></thead>
<tbody>
{chr(10).join(find_rows)}
</tbody></table>

<h2 id="inputs">Official reference inputs (fetched 2026-11-09)</h2>
<p>Every cost model in this repository should agree with these values. Rows marked unverified are deliberately blank.</p>
<table>
<thead><tr><th>ID</th><th>Input</th><th>Value</th><th>As of</th><th>Verbatim (original language)</th><th>Source</th><th>Status</th></tr></thead>
<tbody>
{chr(10).join(in_rows)}
</tbody></table>
<p class="ok">Market structure note: BOC's selling rate (6.6919) was {abs(vs_parity) * 100:.2f}% <i>below</i> the CFETS central parity (6.7188, {link(URL_CFETS, "CFETS")}). A model that treats the parity or BOC's 中行折算价 as the "mid" will compute a negative spread; use the bank's own buy/sell mid.</p>
</main>
<footer>Generated by <code>scripts/build_cross_session_review.py</code> from <code>data/reference_inputs.csv</code> and <code>data/cross_session_findings.csv</code>. Board rates are "for reference only" per BOC; the executed rate on your account governs. Not legal, tax or banking advice.</footer>
</body>
</html>
"""
    return csv_text, page, errors


def main() -> int:
    check = "--check" in sys.argv
    csv_text, page, errors = build()
    if errors:
        print("FAIL:\n  " + "\n  ".join(errors))
        return 1
    if check:
        stale = []
        if not OUT_CSV.exists() or OUT_CSV.read_text(encoding="utf-8") != csv_text:
            stale.append(str(OUT_CSV.relative_to(ROOT)))
        if not OUT_HTML.exists() or OUT_HTML.read_text(encoding="utf-8") != page:
            stale.append(str(OUT_HTML.relative_to(ROOT)))
        if stale:
            print("STALE: " + ", ".join(stale) + " — run scripts/build_cross_session_review.py")
            return 1
        print("OK — cross-session review is up to date; all contract checks passed.")
        return 0
    OUT_CSV.write_text(csv_text, encoding="utf-8")
    OUT_HTML.write_text(page, encoding="utf-8")
    print(f"OK — wrote {OUT_CSV.relative_to(ROOT)} (40 rows) and {OUT_HTML.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
