#!/usr/bin/env python3
"""Build the C5BF final-integration pages from the CSV registers.

Pages
  c5bf-rates.html             FX board snapshots, derived spread, and an
                              independently re-derived $10k-$400k ladder at the
                              LATEST published BOC board, with the delta against
                              the canonical snapshot the rest of the site uses.
  c5bf-integration-audit.html Line-by-line re-verification log: every claim
                              re-read against its official primary source today,
                              the verbatim quote, the verdict, the correction
                              register, and the disposition of open sibling PRs.

Deterministic: no timestamps are read from the clock, everything comes from the
CSVs, so `--check` can assert byte-identity.

Usage:  python3 scripts/build_c5bf_site.py [--check]
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

BOARD_URL = "https://www.boc.cn/sourcedb/whpj/"
TARIFF_URL = "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html"
OUR_URL = "https://www.boc.cn/pbservice/bi2/201412/t20141231_4404048.html"

NAV = [("index.html", "Main dashboard"),
       ("c5bf-rates.html", "FX board & sensitivity"),
       ("c5bf-integration-audit.html", "Integration audit"),
       ("s775-dashboard.html", "S775 audit"),
       ("s775-cost-10k-400k.html", "Cost $10k-$400k"),
       ("s775-methods.html", "All methods"),
       ("s775-steps.html", "Step playbooks"),
       ("s775-penalties-tax.html", "Tax & penalties"),
       ("flagged-review.html", "Flagged for review"),
       ("s775-flagged-review.html", "S775 flags"),
       ("s775-sources.html", "Official sources"),
       ("a058-flagged-review.html", "A058 review"),
       ("a502-review.html", "A502 review")]

VERDICT_BADGE = {
    "CONFIRMED": "badge-ok",
    "NEW (verified, previously uncatalogued)": "badge-ok",
    "NEW SOURCE (registered as S52)": "badge-ok",
    "CHANGED (intraday)": "badge-warn",
    "CORRECTED (scope was over-broad)": "badge-warn",
    "CONFIRMED - CHARACTERISATION CORRECTED": "badge-warn",
    "RECONCILED (convention, not an error)": "badge-warn",
    "IRREGULARITY - FIXED": "badge-no",
}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def read_csv(name):
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def money(x):
    return f"${x:,.2f}" if x != "" else ""


def ext(url, label):
    return f'<a class="src" href="{esc(url)}" rel="noopener">{esc(label)}</a>'


def src_cell(url, label):
    """A source cell: a real link when the register cites an official URL, an
    explicit blank marker when the row is a markup/process finding with no
    external source. Never emits href="n/a"."""
    u = (url or "").strip()
    if u.startswith("http://") or u.startswith("https://"):
        return ext(u, label)
    return '<span class="blank">' + esc(u or "no external source") + '</span>'


def table(headers, rows, classes=""):
    out = [f'<div class="tw"><table class="tbl {classes}"><thead><tr>']
    out += [f"<th>{esc(h)}</th>" for h in headers]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for i, cell in enumerate(r):
            if isinstance(cell, str) and cell.lstrip().startswith("<td"):
                out.append(cell)
            else:
                out.append(f"<td data-l='{esc(headers[i])}'>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def shell(title, current, body, subtitle):
    parts = []
    for u, t in NAV:
        cls = ' class="cur"' if u == current else ""
        parts.append('<a href="' + u + '"' + cls + ">" + esc(t) + "</a>")
    nav = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — CNY→USD final integration</title>
<link rel="stylesheet" href="assets/s775.css">
</head>
<body>
<header class="top">
<div class="wrap">
<span class="brand">C5BF · final integration</span>
<span class="sub">{esc(subtitle)}</span>
<nav class="main">{nav}</nav>
</div>
</header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>Final-integration session <code>arena/c5bf9ddc-china3</code> · all figures derived from
<a href="{BOARD_URL}" rel="noopener">the BOC FX board</a>,
<a href="{TARIFF_URL}" rel="noopener">the BOC personal wire tariff</a> and
<a href="{OUR_URL}" rel="noopener">the BOC personal OUR notice</a>, plus the SAFE and U.S.
official pages linked on each row · registers: <code>data/c5bf_board_observations.csv</code>,
<code>data/c5bf_cost_10k_400k_latest.csv</code>, <code>data/c5bf_cost_delta.csv</code>,
<code>data/c5bf_source_recheck.csv</code>, <code>data/c5bf_corrections.csv</code>.</p>
<p>Nothing on these pages is inferred. A value that cannot be confirmed from an official
source is left blank and flagged; it is never filled in with an estimate.</p>
</div></footer>
<script src="assets/s775.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------- rates page
def build_rates():
    obs = read_csv("c5bf_board_observations.csv")
    lat = read_csv("c5bf_cost_10k_400k_latest.csv")
    delt = {r["amount_usd"]: r for r in read_csv("c5bf_cost_delta.csv")}
    o0 = next(r for r in obs if r["obs_id"] == "OBS-0732")
    o1 = next(r for r in obs if r["obs_id"] == "OBS-1739")
    l10 = next(r for r in lat if r["amount_usd"] == "10000")
    l100 = next(r for r in lat if r["amount_usd"] == "100000")
    l400 = next(r for r in lat if r["amount_usd"] == "400000")
    d10, d400 = delt["10000"], delt["400000"]

    rows_obs = []
    for o in obs:
        rows_obs.append([
            f"<td data-l='Observation'><b>{esc(o['obs_id'])}</b></td>",
            f"<td data-l='BOC board stamp (Beijing)'>{esc(o['board_stamp_beijing'])}</td>",
            f"<td data-l='Fetched (UTC)'>{esc(o['fetched_utc'])}</td>",
            f"<td data-l='Bid (现汇买入价)' class='num'>{esc(o['bid'])}</td>",
            f"<td data-l='Ask (现汇卖出价)' class='num'>{esc(o['ask'])}</td>",
            f"<td data-l='Parity (中行折算价)' class='num'>{esc(o['parity'])}</td>",
            f"<td data-l='Half-spread (ask-mid)/ask' class='num'>{esc(o['half_spread_pct_of_ask'])}%</td>",
            f"<td data-l='Half-spread (ask-mid)/mid' class='num'>{esc(o['half_spread_pct_of_mid'])}%</td>",
            f"<td data-l='Full spread (ask-bid)/ask' class='num'>{esc(o['full_spread_pct_of_ask'])}%</td>",
            f"<td data-l='Role'>{esc(o['note'])}</td>",
            f"<td data-l='Source'>{ext(o['source_url'], 'BOC board')}</td>",
        ])

    rows_head = []
    for label, l, d in (("$10,000", l10, d10), ("$100,000", l100, delt["100000"]),
                        ("$400,000", l400, d400)):
        rows_head.append([
            f"<td data-l='Amount'>{label}</td>",
            f"<td data-l='CNY needed @ latest board' class='num'>{esc(l['cny_needed'])}</td>",
            f"<td data-l='FX spread' class='num'>{esc(l['spread_usd'])}</td>",
            f"<td data-l='Wire fee' class='num'>{esc(l['wire_usd'])}</td>",
            f"<td data-l='Total, latest board' class='num'><b>{esc(l['total_usd'])}</b></td>",
            f"<td data-l='Total, canonical board' class='num'>{esc(d['total_usd_obs0732'])}</td>",
            f"<td data-l='Delta' class='num'>{esc(d['delta_usd'])}</td>",
            f"<td data-l='Total incl. OUR US$25' class='num'>{esc(l['total_with_our_usd'])}</td>",
            f"<td data-l='You receive' class='num'>{esc(l['net_usd'])}</td>",
            f"<td data-l='Source'>{ext(BOARD_URL, 'board')} {ext(TARIFF_URL, 'tariff')}</td>",
        ])

    rows_lat = []
    for l in lat:
        d = delt[l["amount_usd"]]
        amt = int(l["amount_usd"])
        blank = '<span class="blank">blank — unverified</span>'
        rows_lat.append([
            f"<td data-l='Amount'>${amt:,}</td>",
            f"<td data-l='CNY needed' class='num'>{esc(l['cny_needed'])}</td>",
            f"<td data-l='Spread' class='num'>{esc(l['spread_usd'])}</td>",
            f"<td data-l='Wire CNY' class='num'>{esc(l['wire_cny'])}</td>",
            f"<td data-l='Wire USD' class='num'>{esc(l['wire_usd'])}</td>",
            f"<td data-l='Total' class='num'><b>{esc(l['total_usd'])}</b></td>",
            f"<td data-l='Canonical total' class='num'>{esc(d['total_usd_obs0732'])}</td>",
            f"<td data-l='Delta' class='num'>{esc(d['delta_usd'])}</td>",
            f"<td data-l='Total+OUR' class='num'>{esc(l['total_with_our_usd'])}</td>",
            f"<td data-l='%' class='num'>{esc(l['total_pct'])}%</td>",
            f"<td data-l='You receive' class='num'>{esc(l['net_usd'])}</td>",
            f"<td data-l='Intermediary fee'>{blank}</td>",
            f"<td data-l='US receiving fee'>{blank}</td>",
            f"<td data-l='Source'>{ext(BOARD_URL, 'board')} {ext(TARIFF_URL, 'tariff')} {ext(OUR_URL, 'OUR')}</td>",
        ])

    body = f"""
<h1>FX board &amp; cost sensitivity — the same ladder on two official boards</h1>
<p class="lead">Every cost figure on this site is derived from a <b>published BOC board</b> and
BOC's <b>published personal tariffs</b>. BOC republishes the board during the day, so this page
records both observations taken on 2026-11-10 and re-derives the whole $10,000–$400,000 ladder
on the later one. Nothing else on the site was re-based: the 07:32:39 board remains canonical so
that every existing page, table and validator stays internally consistent.</p>

<div class="cards">
<div class="card"><div class="n">{esc(o1['ask'])}</div><div class="l">Latest ask (现汇卖出价), board stamp {esc(o1['board_stamp_beijing'])}</div></div>
<div class="card"><div class="n">{esc(o1['bid'])}</div><div class="l">Latest bid (现汇买入价), same board</div></div>
<div class="card"><div class="n">{esc(o1['half_spread_pct_of_ask'])}%</div><div class="l">Half-spread (ask−mid)/ask on the latest board</div></div>
<div class="card"><div class="n">${esc(l10['total_usd'])}</div><div class="l">Total cost to remit $10,000 on the latest board</div></div>
<div class="card"><div class="n">${esc(l400['total_usd'])}</div><div class="l">Total cost to remit $400,000 on the latest board</div></div>
<div class="card"><div class="n">{esc(d400['delta_usd'])}</div><div class="l">Delta vs the canonical board at $400,000</div></div>
</div>

<h2>1. The two official board observations</h2>
{table(["Observation", "BOC board stamp (Beijing)", "Fetched (UTC)", "Bid (现汇买入价)",
        "Ask (现汇卖出价)", "Parity (中行折算价)", "Half-spread (ask-mid)/ask",
        "Half-spread (ask-mid)/mid", "Full spread (ask-bid)/ask", "Role", "Source"],
       rows_obs, "tbl-num")}
<div class="callout"><b>Why two half-spread columns?</b> Sibling builds on this site published
0.2104% and 0.2100% for the <i>same</i> board and it looked like a contradiction. It is not: both
come from bid 6.6622 / ask 6.6903 (mid 6.67625) and differ only in the denominator —
(ask−mid)/<b>mid</b> = 0.2104%, (ask−mid)/<b>ask</b> = 0.2100%. The cost ladder multiplies the USD
amount by (ask−mid)/<b>ask</b>, so 0.2100% is the figure consistent with every derived row. Both
are now published side by side so the convention can never be mistaken for a discrepancy again.
{ext(BOARD_URL, 'BOC board')}</div>

<h2>2. Headline amounts on both boards</h2>
{table(["Amount", "CNY needed @ latest board", "FX spread", "Wire fee",
        "Total, latest board", "Total, canonical board", "Delta", "Total incl. OUR US$25",
        "You receive", "Source"], rows_head, "tbl-num")}
<p class="lead">Formulas, identical to the canonical ladder: CNY needed = amount × ask ·
spread = amount × (ask − mid)/ask · wire fee = (clamp(1‰ × CNY needed, ¥50, ¥260) + ¥150) ÷ ask ·
OUR = US$25 per wire where an intermediary bank is required. Sources:
{ext(BOARD_URL, 'BOC FX board')} {ext(TARIFF_URL, 'BOC personal wire tariff')}
{ext(OUR_URL, 'BOC personal OUR notice')}</p>
<div class="callout ok"><b>Finding.</b> The estimate is stable across the day's boards: the total
moves by {esc(d10['delta_usd'])} at $10,000 ({esc(d10['delta_pct_of_total'])}% of the cost) and
{esc(d400['delta_usd'])} at $400,000 ({esc(d400['delta_pct_of_total'])}% of the cost). Planning
accuracy is therefore dominated by the <b>wire-fee cap</b> and by the
<span class="blank">unverified</span> intermediary and U.S. receiving-bank fees — not by intraday
rate movement.</div>

<h2>3. Full ladder, $10,000 to $400,000 in $10,000 steps (latest board)</h2>
<div class="callout warn"><b>Two columns are blank on every row on purpose.</b> BOC and the U.S.
receiving banks publish no official schedule for intermediary (correspondent) fees or U.S.
incoming-wire fees for this route, so they are left blank and flagged rather than estimated
(flag S775-F06). They are not zero.</div>
{table(["Amount", "CNY needed", "Spread", "Wire CNY", "Wire USD", "Total",
        "Canonical total", "Delta", "Total+OUR", "%", "You receive",
        "Intermediary fee", "US receiving fee", "Source"], rows_lat, "tbl-num")}
<p class="lead">40 increments. The percentage falls as the amount rises because the ¥260 wire-fee
cap binds from about $38,862 of transfer — above that the wire fee is a constant ¥410
(¥260 + ¥150 cable) and only the spread keeps growing. {ext(TARIFF_URL, 'tariff cap')}</p>
"""
    return shell("FX board & cost sensitivity", "c5bf-rates.html", body,
                 "Two official BOC boards, 2026-11-10 · 40 increments re-derived")


# --------------------------------------------------------------------- audit page
def build_audit():
    recheck = read_csv("c5bf_source_recheck.csv")
    corr = read_csv("c5bf_corrections.csv")

    counts = {}
    for r in recheck:
        key = ("IRREGULARITY" if r["verdict"].startswith("IRREGULARITY")
               else "CORRECTED/CHANGED" if (r["verdict"].startswith("CORRECTED")
                                            or r["verdict"].startswith("CHANGED")
                                            or "CORRECTED" in r["verdict"]
                                            or r["verdict"].startswith("RECONCILED"))
               else "CONFIRMED/NEW")
        counts[key] = counts.get(key, 0) + 1

    rows_rc = []
    for r in recheck:
        badge = VERDICT_BADGE.get(r["verdict"], "badge-warn")
        rows_rc.append([
            f"<td data-l='Check'><b>{esc(r['check_id'])}</b></td>",
            f"<td data-l='Verdict'><span class='badge {badge}'>{esc(r['verdict'])}</span></td>",
            f"<td data-l='Claim as published'>{esc(r['claim_as_published'])}</td>",
            f"<td data-l='Official source'>{src_cell(r['official_source_url'], r['official_source_title'])}</td>",
            f"<td data-l='Fetched (UTC)'>{esc(r['fetched_utc'])}</td>",
            f"<td data-l='Verbatim quote'><q>{esc(r['verbatim_quote'])}</q></td>",
            f"<td data-l='Action taken'>{esc(r['action_taken'])}</td>",
            f"<td data-l='Files affected'><code>{esc(r['repo_files_affected'])}</code></td>",
        ])

    blank_na = '<span class="blank">n/a</span>'
    rows_cor = []
    for c in corr:
        links = " ".join(ext(u.strip(), u.strip().replace("https://", "").split("/")[0])
                         for u in c["official_source_urls"].split("|")
                         if u.strip().startswith("http"))
        links = links or blank_na
        rows_cor.append([
            f"<td data-l='ID'><b>{esc(c['id'])}</b></td>",
            f"<td data-l='Files'><code>{esc(c['files_touched'])}</code></td>",
            f"<td data-l='Before'>{esc(c['before'])}</td>",
            f"<td data-l='After'>{esc(c['after'])}</td>",
            f"<td data-l='Basis'>{esc(c['basis'])}</td>",
            f"<td data-l='Official source'>{links}</td>",
            f"<td data-l='Provenance'>{esc(c['provenance'])}</td>",
        ])

    pr_rows = [
        ["#34", "S775 correction: verified $53.42 hero figure, cost-page markup fix, guard validator rules",
         "arena/775c9619-china3", "OPEN — became unmergeable",
         "Diff read line by line; its arithmetic (21.00 + 32.42 = 53.42) and its markup fix were "
         "independently re-derived and confirmed correct. After main advanced through PRs #35/#36 the "
         "PR could no longer be merged cleanly (`gh pr merge 34` refused: \"the merge commit cannot be "
         "cleanly created\"), and Arena's single-branch binding prevents pushing to another session's "
         "branch. Its owner's last commit is 2026-11-10T01:47:56Z — over 60 minutes with no commits — "
         "so per the board's handoff rule this integration session carried the same corrections forward "
         "as COR-01, COR-02, COR-03 and COR-08 and logged the handoff."],
        ["#32", "Coordination record: PR #30 merged, Pages deploy confirmed",
         "arena/3fcb5029-china3", "OPEN — documentation only",
         "Touches COORDINATION.md only; all substantive checks green. Left open for its owner: the board "
         "convention recorded at PR #27 says later sessions should append their own block rather than "
         "keep re-recording previous PRs, so merging it is not required for a correct site and would only "
         "add another append-conflict for concurrent sessions."],
        ["#25", "Consolidated CNY→USD dashboard: 680-row cost ladder, §988 tax line, 17 methods, 27 flags",
         "arena/0fbc51c7-china3", "OPEN — stale base, would rewrite shared generator",
         "Rewrites index.html, scripts/build_dashboard.py, README.md and EXECUTIVE_SUMMARY.md from a base "
         "that predates several merges. Merging it would roll the shared dashboard generator back behind "
         "the version that verify_dashboard.py currently checks for byte-identity, i.e. it would break the "
         "build. Not merged; disposition logged for its owner."],
        ["#18", "Cost model: every CNY→USD method priced at USD 10k–400k, measured FX margin, verified sources",
         "arena/119a615f-china3", "OPEN — stale base, 25 shared legacy files",
         "Rewrites index.html, methods.html, routes.html, tax.html, us-tax.html, penalties.html, "
         "flagged-review.html, review.html, sources.html, ci.yml and pages.yml from an early base. Same "
         "break-the-site risk as #25. Not merged; left to its owner."],
        ["#15", "Computed CNY→USD cost model: 40 steps × 13 routes, step-by-step playbooks, verification gate",
         "arena/15d351fb-china3", "OPEN — stale base, rewrites data/*.csv shared by current validators",
         "Overwrites data/sources.csv, data/penalty.csv, data/china_rules.csv and data/us_rules.csv, which "
         "validate_data.py and several page builders read today. Not merged; left to its owner."],
        ["#8", "Verified CNY to USD research + GitHub Pages site (least-tax route, penalty decomposition)",
         "arena/46c03a7d-china3", "OPEN — incompatible site root",
         "Publishes its own index.html at the repository root plus a site/ tree; the root index.html is now "
         "generated by scripts/build_dashboard.py and gated by verify_dashboard.py. Merging would replace "
         "the live landing page with an older hand-built one. Not merged."],
        ["#6", "[DRAFT] F83: independent source verification, verified gap-fill, integration QA",
         "arena/f83a5122-china3", "OPEN — DRAFT", "Draft PRs are not merged by an integration session."],
        ["#35", "Publish independent review of conversion guidance and cost tables",
         "arena/058d6cd7-china3", "MERGED by its owner (ff25d1f) while this session worked",
         "Its logged cross-scope correction request was actioned by this session as COR-04/COR-06/COR-07."],
        ["#36", "Publish independent CNY repatriation accuracy review",
         "arena/50249649-china3", "MERGED by its owner (9bc2cde) while this session worked",
         "Additive a502-review.html + audit; no conflict with this session's namespace."],
        ["#37", "Independent completion audit: fresh BOC fee ladder and provenance flags",
         "arena/4a528a74-china3", "OPEN — concurrent, separate namespace",
         "Also records a fresh BOC fee ladder. Left entirely to its owner: this session's equivalent work "
         "lives in the c5bf-* namespace (data/c5bf_board_observations.csv, c5bf-rates.html) so the two do "
         "not collide. Both are published; they are independent observations of the same official board."],
    ]
    rows_pr = [[f"<td data-l='PR'>{esc(a)}</td>", f"<td data-l='Title'>{esc(b)}</td>",
                f"<td data-l='Branch'><code>{esc(c)}</code></td>",
                f"<td data-l='State'>{esc(d)}</td>",
                f"<td data-l='Integration disposition'>{esc(e)}</td>"]
               for a, b, c, d, e in pr_rows]

    body = f"""
<h1>Final-integration audit — every load-bearing claim re-read against its official source</h1>
<p class="lead">This is the line-by-line re-verification pass the board requires before shared
outputs change. Each row below was re-opened at the official primary source on 2026-11-10, quoted
verbatim, and given a verdict. Where the repository was wrong, the correction was applied and is
listed in section 3; where a value could not be confirmed, it stays <b>blank</b> and flagged.
No row was accepted on the strength of another page in this repository.</p>

<div class="cards">
<div class="card"><div class="n">{len(recheck)}</div><div class="l">Claims re-read against an official primary source today</div></div>
<div class="card"><div class="n">{counts.get('CONFIRMED/NEW', 0)}</div><div class="l">Confirmed verbatim or newly catalogued</div></div>
<div class="card"><div class="n">{counts.get('CORRECTED/CHANGED', 0)}</div><div class="l">Corrected, re-scoped, reconciled or moved intraday</div></div>
<div class="card"><div class="n">{counts.get('IRREGULARITY', 0)}</div><div class="l">Irregularities found on the live site — both fixed</div></div>
<div class="card"><div class="n">{len(corr)}</div><div class="l">Corrections applied in this integration pass</div></div>
<div class="card"><div class="n">0</div><div class="l">Values filled in by inference (the rule is blank, never guess)</div></div>
</div>

<h2>1. What changed for the reader, in one paragraph</h2>
<div class="callout warn"><b>The single most important correction is about documents, not money.</b>
The site previously said a personal wire out of China needs no approval "up to US$50,000/day on ID
documents". Re-read at source, that threshold is 汇发〔2020〕14号 <b>art. 64</b> and it applies to
<b>境内个人 (domestic individuals)</b> remitting FX <b>from an FX account</b> — and only
US$10,000/day when remitting foreign-currency cash. A <b>U.S. citizen is a 境外个人 (foreign
individual)</b>, and for them <b>art. 59</b> governs: to buy FX out of lawful current-account CNY
income earned in China the bank must see a valid ID <b>plus source-of-funds documents showing the
transaction amount, including tax certificates (含税务凭证)</b>. The annual purchase convenience
quota is available only to foreign individuals who hold a 外国人永久居留身份证 (Foreign Permanent
Resident ID card). Practically: the cost model was already right, but the paperwork bar for this
user is higher than the site implied, and that is now stated everywhere the threshold appears.
{ext('https://www.safe.gov.cn/tianjin/2024/0229/2402.html', 'SAFE art. 64')}
{ext('https://www.safe.gov.cn/tianjin/2024/0621/2529.html', 'SAFE art. 59')}</div>

<h2>2. Re-verification register ({len(recheck)} checks)</h2>
{table(["Check", "Verdict", "Claim as published", "Official source", "Fetched (UTC)",
        "Verbatim quote", "Action taken", "Files affected"], rows_rc)}

<h2>3. Corrections applied in this pass ({len(corr)})</h2>
{table(["ID", "Files", "Before", "After", "Basis", "Official source", "Provenance"], rows_cor)}

<h2>4. Disposition of every open sibling pull request</h2>
<p class="lead">The brief says to merge the finished work and never merge a broken site. Each open
PR was read in full and test-evaluated against the current tree; the reasoning is recorded here so
no session's work is silently dropped.</p>
{table(["PR", "Title", "Branch", "State", "Integration disposition"], rows_pr)}

<h2>5. Standing caveats that no source can close</h2>
<ul>
<li><b>The FX board moves.</b> Both 2026-11-10 observations are on
<a href="c5bf-rates.html">FX board &amp; sensitivity</a>; the bank quotes the rate at execution, not
the published board. {ext(BOARD_URL, 'BOC board')}</li>
<li><b>Intermediary and U.S. receiving-bank fees are blank, not zero.</b> No official schedule
exists; flag S775-F06. {ext(TARIFF_URL, 'BOC personal tariff')}</li>
<li><b>The user's own facts were never supplied</b> — source of the CNY, U.S. tax basis, marginal
rate, hukou history, bank and account type. Every cell that depends on them is blank and flagged
(S775-F01…F04). Nothing was assumed.</li>
<li><b>IRC §988 character is an interpretation of the statute, not a ruling.</b> The statutory text
is linked; the application to these facts is flagged S775-F10.
{ext('https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm', '26 U.S.C. 988')}</li>
<li><b>Regulatory text is Chinese-language primary law.</b> Where this site paraphrases 汇发〔2020〕14号
or the 外汇管理条例, the register above quotes the official Chinese sentence so a reader can check the
translation rather than trust it.</li>
</ul>
"""
    return shell("Final-integration audit", "c5bf-integration-audit.html", body,
                 "15 claims re-read at source · 8 corrections · 0 inferred values")


BUILDERS = {"c5bf-rates.html": build_rates, "c5bf-integration-audit.html": build_audit}


def main():
    check = "--check" in sys.argv
    rc = 0
    for name, fn in BUILDERS.items():
        out = fn()
        path = ROOT / name
        if check:
            cur = path.read_text(encoding="utf-8") if path.exists() else None
            if cur != out:
                print(f"  STALE: {name}")
                rc = 1
            else:
                print(f"  fresh: {name}")
        else:
            path.write_text(out, encoding="utf-8")
            print(f"  wrote {name} ({len(out):,} bytes)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
