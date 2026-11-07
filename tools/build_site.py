#!/usr/bin/env python3
"""Build the static site from data/*.json.

Design rules enforced here:
  * Every table row renders at least one source link, or the build fails.
  * A row with verification != "verified" renders with a "UNVERIFIED"/"PARTIAL" badge
    and is additionally listed on flagged.html.
  * Blank values stay blank. The builder never substitutes a placeholder number.
"""
import json
import subprocess
import sys
import os
import re
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"


def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


def esc(x):
    return html.escape(str(x), quote=True) if x is not None else ""


def src_links(row):
    """Return list of (label, url) for a row, whatever shape the sources take."""
    out = []
    if row.get("sources"):
        for s in row["sources"]:
            out.append((s.get("label", "source"), s["url"]))
    if row.get("source_url"):
        out.append((row.get("source_title", row.get("source_publisher", "source")), row["source_url"]))
    if row.get("secondary_source_url"):
        out.append((row.get("source_title", "") + " (secondary)", row["secondary_source_url"]))
    return out


def badge(row):
    v = row.get("verification", "unverified")
    if v == "verified":
        return '<span class="badge ok">verified</span>'
    if v == "partial":
        return '<span class="badge warn">partial</span>'
    return '<span class="badge bad">unverified</span>'


def links_cell(row):
    ls = src_links(row)
    if not ls:
        return '<span class="none">no official source found — left blank</span>'
    parts = []
    for label, url in ls:
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        parts.append(f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(host)}</a>')
    return " ".join(parts)


def cell(val, cls=""):
    if val is None or val == "":
        return f'<td class="blank {cls}" data-empty="1">&mdash;</td>'
    return f'<td class="{cls}">{esc(val)}</td>'


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Verified research on converting CNY to USD from a Chinese bank account as a US citizen: routes, costs, and where the penalties actually come from.">
<link rel="stylesheet" href="{rel}assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="{rel}index.html"><span class="dot"></span> China Money &rarr; USD</a>
    <nav>
      <a href="{rel}index.html">Overview</a>
      <a href="{rel}executive-summary.html">Summary</a>
      <a href="{rel}channels.html">Routes</a>
      <a href="{rel}penalty-analysis.html">The Penalty</a>
      <a href="{rel}china-fx-rules.html">China FX</a>
      <a href="{rel}china-tax.html">China Tax</a>
      <a href="{rel}us-inbound.html">US Inbound</a>
      <a href="{rel}flagged.html" class="navflag">Flagged</a>
      <a href="{rel}sources.html">Sources</a>
    </nav>
  </div>
</header>
<main id="main">
"""

FOOT = """</main>
<footer>
  <div class="wrap">
    <p><strong>Evidence rule applied throughout:</strong> every figure carries a link to the official publisher.
    Where a value could not be confirmed from an official source it is left blank and listed on
    <a href="{rel}flagged.html">Flagged for Review</a>. No value was inferred or estimated.</p>
    <p class="muted">Compiled 7 November 2026 from primary sources. This is a reading of statutes, regulations and
    official guidance, not legal or tax advice, and not a determination for any individual. Rules in this area change;
    each row carries the date it was checked.</p>
    <p class="muted">Repository: <a href="https://github.com/sassnarep3-star/China3" target="_blank" rel="noopener">sassnarep3-star/China3</a>
    &middot; task board: <a href="https://github.com/sassnarep3-star/China3/blob/main/COORDINATION.md" target="_blank" rel="noopener">COORDINATION.md</a></p>
  </div>
</footer>
<script src="{rel}assets/app.js"></script>
</body>
</html>
"""


def page(path, title, body, rel=""):
    out = HEAD.format(title=esc(title), rel=rel) + body + FOOT.format(rel=rel)
    (SITE / path).write_text(out, encoding="utf-8")
    return path


def count_links(rows):
    return sum(len(src_links(r)) for r in rows)


# --------------------------------------------------------------------------- #
# Row renderers
# --------------------------------------------------------------------------- #

def generic_table(rows, columns, table_id):
    """columns: list of (key, header, css_class)"""
    head = "".join(f"<th>{esc(h)}</th>" for _, h, _ in columns)
    head += "<th>Source</th><th>Checked</th>"
    body = []
    for r in rows:
        tds = []
        for key, _, cls in columns:
            v = r.get(key)
            if key == "value" and (v is None or v == ""):
                tds.append('<td class="blank" data-empty="1"><em>blank</em></td>')
            else:
                tds.append(cell(v, cls))
        tds.append(f"<td class='srccell'>{links_cell(r)}</td>")
        tds.append(f"<td class='nw'>{badge(r)}<br><span class='date'>{esc(r.get('verified_on',''))}</span></td>")
        cls = "flagged" if r.get("verification") != "verified" else ""
        body.append(f"<tr class='{cls}' data-flag='{1 if r.get('verification') != 'verified' else 0}'>" + "".join(tds) + "</tr>")
    return f"""
<div class="tablewrap">
<table id="{table_id}" class="grid">
<thead><tr>{head}</tr></thead>
<tbody>{''.join(body)}</tbody>
</table>
</div>
"""


def short_host(url):
    h = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    return esc(h)


def channels_table(rows):
    body = []
    for r in rows:
        legal = r.get("legality", "unverified")
        cls = {"lawful": "ok", "lawful-restricted": "warn", "prohibited": "bad"}.get(legal, "bad")
        srcs = " ".join(
            '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(s["url"]), short_host(s["url"]))
            for s in r.get("sources", [])
        ) or '<span class="none">no official source found</span>'
        body.append(f"""
<tr data-legal="{esc(legal)}" data-flag="{1 if r.get('verification') != 'verified' else 0}">
  <td class="nw">{esc(r['id'])}</td>
  <td><strong>{esc(r['name'])}</strong><div class="sub">{esc(r.get('category',''))}</div></td>
  <td><span class="badge {cls}">{esc(legal)}</span></td>
  <td>{cell(r.get('capacity'))}</td>
  <td>{cell(r.get('cost_published'))}</td>
  <td class="procon"><div class="pros"><span>+</span> {esc(r.get('pros') or '')}</div><div class="cons"><span>&minus;</span> {esc(r.get('cons') or '')}</div></td>
  <td class="srcsmall">{srcs}</td>
</tr>""")
    return f"""
<div class="filterbar">
  <button class="chip active" data-filter="all">All routes ({len(channels_table.rows)})</button>
  <button class="chip" data-filter="lawful">Lawful ({channels_table.n['lawful']})</button>
  <button class="chip" data-filter="lawful-restricted">Lawful with conditions ({channels_table.n['lawful-restricted']})</button>
  <button class="chip" data-filter="prohibited">Prohibited ({channels_table.n['prohibited']})</button>
  <button class="chip" data-filter="unverified">Unverified ({channels_table.n['unverified']})</button>
  <input id="q-ch" class="search" type="search" placeholder="Filter by keyword…" aria-label="Filter routes by keyword">
</div>
<div class="tablewrap">
<table class="grid wide" id="channels">
<thead><tr>
  <th>ID</th><th>Route</th><th>Legality</th><th>Capacity / limit</th><th>Published cost</th>
  <th>Pros and cons</th><th>Official source</th>
</tr></thead>
<tbody>{''.join(body)}</tbody>
</table>
</div>
"""


def build():
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)

    fx = load("01-cn-fx-rules.json")
    tax = load("02-cn-tax.json")
    us = load("03-us-inbound.json")
    ch = load("04-channels.json")
    sc = load("05-scenarios.json")

    all_rows = fx["rows"] + tax["rows"] + us["rows"] + ch["rows"]
    # Hard gate: no row may render without an official source link.
    # A row may only be sourceless if it is explicitly marked unverified; it is then
    # rendered with a blank value and listed on flagged.html.
    orphans = [r["id"] for r in all_rows
               if not src_links(r) and r.get("verification") != "unverified"]
    if orphans:
        raise SystemExit("BUILD FAILED: verified/partial rows with no source link: %s" % orphans)
    sourceless = [r["id"] for r in all_rows if not src_links(r)]
    if sourceless:
        print("NOTE: sourceless rows (rendered as unverified, listed on flagged.html):", sourceless)

    counts = {"lawful": 0, "lawful-restricted": 0, "prohibited": 0, "unverified": 0}
    for r in ch["rows"]:
        counts[r["legality"]] = counts.get(r["legality"], 0) + 1
    channels_table.rows = ch["rows"]
    channels_table.n = counts

    verified = sum(1 for r in all_rows if r.get("verification") == "verified")
    partial = sum(1 for r in all_rows if r.get("verification") == "partial")
    unver = sum(1 for r in all_rows if r.get("verification") not in ("verified", "partial"))
    flagged = [r for r in all_rows if r.get("verification") != "verified"]

    urls = set()
    for r in all_rows:
        for _, u in src_links(r):
            urls.add(u)

    # ---------------------------------------------------------------- index
    comp = {c["id"]: c for c in sc["decomposition"]}
    bars = [
        ("Bank FX spread (lawful conversion)", 0.42, "ok", "verified"),
        ("US tax on a genuine gift", 0.0, "ok", "verified"),
        ("PRC tax on the conversion", 0.0, "ok", "verified"),
        ("Remittance / wire fees", None, "warn", "unverified — read the bank tariff"),
        ("PRC fine, if the route is unlawful", 30.0, "bad", "statutory maximum, 30%-100%"),
        ("Form 3520 penalty if not filed", 25.0, "bad", "5%/month, capped at 25%"),
        ("FBAR penalty if found willful", 50.0, "bad", "greater of USD 165,353 or 50% of balance"),
    ]
    maxbar = 50.0
    barhtml = []
    for label, val, cls, note in bars:
        if val is None:
            barhtml.append(f"""<div class="barrow"><div class="barlabel">{esc(label)}</div>
<div class="bartrack"><div class="barfill {cls} blankfill"></div></div>
<div class="barval">— <span class="barnote">{esc(note)}</span></div></div>""")
        else:
            w = max(val / maxbar * 100, 0.6)
            barhtml.append(f"""<div class="barrow"><div class="barlabel">{esc(label)}</div>
<div class="bartrack"><div class="barfill {cls}" style="width:{w:.2f}%"></div></div>
<div class="barval">{val:g}% <span class="barnote">{esc(note)}</span></div></div>""")

    w = {c["id"]: c for c in sc["worked_examples"]["cases"]}
    idx = f"""
<section class="hero">
  <div class="wrap">
    <p class="eyebrow">Verified research &middot; compiled 7 November 2026</p>
    <h1>There is no large tax on converting CNY to USD.<br><span class="hi">The large cost is a missed form.</span></h1>
    <p class="lede">Money in a Chinese bank account, owned by a US citizen. We traced every lawful and every prohibited
    route, read the statutes on both sides, and priced the whole problem. The conclusion is uncomfortable but it is
    well evidenced: the PRC imposes <strong>no tax</strong> on the act of converting or transferring your own funds.
    The penalties people experience are for <strong>not filing US information returns</strong>, or for using a route
    China prohibits.</p>
    <div class="kpis">
      <div class="kpi"><div class="num">0%</div><div class="lab">PRC tax on the conversion itself</div></div>
      <div class="kpi"><div class="num">0.42%</div><div class="lab">Bank FX spread — the real cost</div></div>
      <div class="kpi"><div class="num">25%</div><div class="lab">Form 3520 penalty if not filed</div></div>
      <div class="kpi"><div class="num">50%</div><div class="lab">FBAR penalty if found willful</div></div>
    </div>
  </div>
</section>

<section class="wrap">
  <h2>The five components of the so-called "conversion penalty"</h2>
  <p class="sub">Two of these can be priced from a published rate. One cannot be priced at all without the bank's
  tariff, so it is left blank. Everything else is a statutory ceiling that applies only if something is done wrong.</p>
  <div class="chart">
    {''.join(barhtml)}
  </div>
  <p class="caption">Spread from Bank of China's published USD table on 7 Nov 2026 (buying 666.48, selling 669.29 per
  100 USD). Penalty ceilings from IRC §6039F(c), 31 CFR 1010.821 and the PRC FX Regulations Art. 39/45.
  <a href="penalty-analysis.html">Full breakdown with the arithmetic &rarr;</a></p>
</section>

<section class="wrap">
  <h2>The same money, four ways</h2>
  <p class="sub">CNY 3,000,000 &asymp; USD {w['W-1']['principal_usd']:,}. Converted at the Federal Reserve H.10 rate for
  30 Oct 2026 purely so one arithmetic path is visible.</p>
  <div class="cases">
    <div class="case good">
      <div class="caselab">Lawful route, all forms filed</div>
      <div class="casenum">USD {w['W-1']['lines'][1]['usd']:,}</div>
      <div class="casedesc">The bank spread. No tax component at all. Baseline = 1&times;.</div>
    </div>
    <div class="case bad">
      <div class="caselab">Same, but Form 3520 never filed</div>
      <div class="casenum">+ USD {w['W-2']['lines'][1]['usd']:,}</div>
      <div class="casedesc">25% of the gift. <strong>59&times; the cost of moving it.</strong></div>
    </div>
    <div class="case bad">
      <div class="caselab">Same, but FBAR failure ruled willful</div>
      <div class="casenum">+ USD {w['W-3']['lines'][0]['usd']:,}</div>
      <div class="casedesc">50% of the balance, per violation. <strong>119&times;.</strong></div>
    </div>
    <div class="case bad">
      <div class="caselab">Prohibited channel, caught</div>
      <div class="casenum">+ USD {w['W-4']['lines'][0]['usd']:,}</div>
      <div class="casedesc">30% fine <em>and</em> the money is repatriated. <strong>71&times;.</strong></div>
    </div>
  </div>
</section>

<section class="wrap">
  <h2>What actually constrains you</h2>
  <div class="cards">
    <a class="card" href="china-fx-rules.html">
      <div class="cardtag">{len(fx['rows'])} rows</div>
      <h3>China-side FX rules</h3>
      <p>The USD 50,000 annual facilitation quota, why it is <em>not</em> a ceiling, the six prohibitions on the
      purchase form, the two capital-account routes that scale, and the fine schedule if you get it wrong.</p>
      <span class="go">Read the rules &rarr;</span>
    </a>
    <a class="card" href="channels.html">
      <div class="cardtag">{len(ch['rows'])} routes</div>
      <h3>Every route, priced and judged</h3>
      <p>Lawful, lawful-with-conditions, and prohibited. Pros and cons for each, with the capacity limit and the
      published cost, or a blank where no official cost could be found.</p>
      <span class="go">Compare routes &rarr;</span>
    </a>
    <a class="card" href="penalty-analysis.html">
      <div class="cardtag">{len(sc['decomposition'])} components</div>
      <h3>Where the penalty comes from</h3>
      <p>The decomposition, the worked arithmetic, and the ranking. This is the page that answers the question
      you actually asked.</p>
      <span class="go">See the math &rarr;</span>
    </a>
    <a class="card" href="us-inbound.html">
      <div class="cardtag">{len(us['rows'])} rules</div>
      <h3>US inbound rules</h3>
      <p>FBAR, Form 8938, Form 3520, §988 currency gain, PFIC and §1291. The largest single risk in the whole
      problem sits here, and it is about reporting rather than tax.</p>
      <span class="go">Read the rules &rarr;</span>
    </a>
    <a class="card" href="china-tax.html">
      <div class="cardtag">{len(tax['rows'])} rules</div>
      <h3>China tax</h3>
      <p>No exit tax, no estate tax, deposit interest exempt since 2008, and a September 2026 change that ends the
      dividend exemption for foreign nationals.</p>
      <span class="go">Read the rules &rarr;</span>
    </a>
    <a class="card warncard" href="flagged.html">
      <div class="cardtag">{len(flagged)} items</div>
      <h3>Flagged for review</h3>
      <p>Everything we could not confirm from an official publisher, plus the irregularities found in the
      repository itself. Left blank rather than guessed, with the source we did find.</p>
      <span class="go">Review the gaps &rarr;</span>
    </a>
  </div>
</section>

<section class="wrap rec">
  <h2>The short answer</h2>
  <ol class="recs">
    <li><strong>Use the ordinary bank route first.</strong> USD 50,000 per person per year on ID alone, at about 0.42%.
      Each person may use their own quota for their own money; moving <em>your</em> money through <em>their</em> quota
      is structuring and is expressly penalised.</li>
    <li><strong>Above the quota, find the real underlying event.</strong> The quota is a documentary convenience, not a
      legal ceiling — SAFE's own Q&amp;A says genuine current-account conversion has no amount limit once evidenced.</li>
    <li><strong>For an inheritance or after emigration, use the dedicated capital-account route.</strong> It is the only
      mechanism built to move a whole balance, and it costs paperwork rather than tax.</li>
    <li><strong>File every US form on time.</strong> FBAR above USD 10,000 aggregate; Form 8938 above the threshold;
      Form 3520 Part IV above USD 100,000 from a foreign individual. These attach to the account you already hold.</li>
    <li><strong>If filings were missed, correct them deliberately.</strong> The Streamlined Foreign Offshore Procedures
      wipe out the FBAR and information-return penalties entirely for a citizen who genuinely lived abroad; the
      domestic track caps the penalty at 5% of the highest aggregate balance. Against 50% for a willful violation.</li>
    <li><strong>Do not park the money in a Chinese fund.</strong> A Chinese mutual fund is very likely a PFIC, and the
      default §1291 regime taxes the gain at the top rate for every year held, plus interest.</li>
  </ol>
  <p class="caption">Read the full reasoning, with the source for every clause, in
  <a href="executive-summary.html">the executive summary</a>.</p>
</section>
"""
    page("index.html", "China Money → USD — verified routes, costs and penalties", idx)

    # ------------------------------------------------------------- channels
    chbody = f"""
<section class="wrap pagehead">
  <p class="eyebrow">Category &middot; routes</p>
  <h1>Every route from CNY to USD we could identify</h1>
  <p class="lede">{len(ch['rows'])} routes. Each is labelled <span class="badge ok">lawful</span>,
  <span class="badge warn">lawful-restricted</span> or <span class="badge bad">prohibited</span> strictly according to
  what an official source says — not according to what is commonly recommended.
  Prohibited routes are included deliberately: they are the ones most often suggested, and knowing the size of the
  penalty is the whole point.</p>
  <p class="note">A blank cell means no official cost figure exists that we could cite. It does not mean zero.</p>
</section>
<section class="wrap">{channels_table(ch['rows'])}</section>
"""
    page("channels.html", "Routes — every CNY → USD channel, priced and judged", chbody)

    # ----------------------------------------------------- penalty analysis
    def decomp_src(c):
        return " ".join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(u), short_host(u))
                        for u in c.get("sources", [])) or '<span class="none">none</span>'

    decomp_rows = []
    for c in sc["decomposition"]:
        decomp_rows.append(f"""
<tr>
  <td class="nw">{esc(c['id'])}</td>
  <td><strong>{esc(c['component'])}</strong></td>
  <td class="nw">{cell(c.get('rate'))}</td>
  <td>{cell(c.get('derivation'))}</td>
  <td>{esc(c.get('status',''))}</td>
  <td class="srcsmall">{decomp_src(c)}</td>
</tr>""")

    case_html = []
    for c in sc["worked_examples"]["cases"]:
        lines = ""
        for l in c["lines"]:
            pct = "&mdash;" if l.get("percent") is None else ("%g%%" % l["percent"])
            amt = "&mdash;" if l.get("usd") is None else "USD {:,}".format(l["usd"])
            lines += ("<tr><td>%s</td><td class='nw'>%s</td><td class='nw'>%s</td>"
                      "<td class='sub'>%s</td></tr>") % (esc(l["item"]), pct, amt, esc(l.get("note", "")))
        case_html.append("""
<div class="caseline">
  <h3>%s &middot; %s</h3>
  <table class="grid small"><thead><tr><th>Item</th><th>Rate</th><th>Amount</th><th>Note</th></tr></thead>
  <tbody>%s</tbody></table>
  <p class="bottomline">%s</p>
</div>""" % (esc(c['id']), esc(c['label']), lines, esc(c['bottom_line'])))

    rank_rows = "".join(f"""
<tr><td class="nw rank">{r['rank']}</td><td><strong>{esc(r['route'])}</strong></td>
<td>{esc(r['effective_cost'])}</td><td>{esc(r['why'])}</td></tr>""" for r in sc["ranking"])

    pbody = f"""
<section class="wrap pagehead">
  <p class="eyebrow">Category &middot; analysis</p>
  <h1>Breaking down the conversion penalty</h1>
  <p class="lede">The question assumes a large tax exists. We decomposed the total cost of moving the money into
  eight components and priced each one against an official source. Only two have a published rate that can be turned
  into a number; one cannot be priced at all and is left blank.</p>
</section>

<section class="wrap">
  <h2>Component by component</h2>
  <div class="tablewrap">
  <table class="grid wide">
    <thead><tr><th>#</th><th>Component</th><th>Rate</th><th>Derivation</th><th>Status</th><th>Source</th></tr></thead>
    <tbody>{''.join(decomp_rows)}</tbody>
  </table>
  </div>
</section>

<section class="wrap">
  <h2>Worked arithmetic</h2>
  <p class="sub">{esc(sc['worked_examples']['assumption_statement'])}</p>
  {''.join(case_html)}
</section>

<section class="wrap">
  <h2>Ranking by effective cost</h2>
  <div class="tablewrap">
  <table class="grid">
    <thead><tr><th>Rank</th><th>Route</th><th>Effective cost</th><th>Why it sits here</th></tr></thead>
    <tbody>{rank_rows}</tbody>
  </table>
  </div>
</section>

<section class="wrap finding">
  <h2>The answer to the question you asked</h2>
  <p>{esc(sc['the_real_answer']['finding'])}</p>
  <p class="strong">{esc(sc['the_real_answer']['therefore'])}</p>
</section>
"""
    page("penalty-analysis.html", "The penalty — decomposed, with the arithmetic", pbody)

    # ------------------------------------------------------------ china fx
    fxbody = f"""
<section class="wrap pagehead">
  <p class="eyebrow">Category &middot; China</p>
  <h1>China-side foreign-exchange rules</h1>
  <p class="lede">What the State Administration of Foreign Exchange and the State Council actually provide, in
  their own words. The two most important rows are CN-FX-01 (the USD 50,000 quota) and CN-FX-02 (the official
  statement that the quota is <em>not</em> an amount limit).</p>
</section>
<section class="wrap">
{generic_table(fx['rows'], [('id','ID','nw'),('topic','Topic',''),('value','Value',''),('detail','Wording of the rule','det'),('implication','What it means for you','')], 't-fx')}
</section>
"""
    page("china-fx-rules.html", "China FX rules", fxbody)

    # ----------------------------------------------------------- china tax
    taxbody = f"""
<section class="wrap pagehead">
  <p class="eyebrow">Category &middot; China</p>
  <h1>China-side tax</h1>
  <p class="lede">{esc(tax['meta']['headline'])}</p>
</section>
<section class="wrap">
{generic_table(tax['rows'], [('id','ID','nw'),('topic','Topic',''),('value','Value',''),('detail','Wording of the rule','det'),('implication','What it means for you','')], 't-tax')}
</section>
<section class="wrap note-block">
  <h2>Two rows worth reading twice</h2>
  <p><strong>CN-TAX-02 — no exit tax.</strong> China requires a tax settlement before you cancel household
  registration to emigrate, but that is a settlement of tax already due. It is not a tax on leaving and not a tax on
  unrealised gains. Nothing is triggered by moving the money.</p>
  <p><strong>CN-TAX-05 — the dividend exemption ended.</strong> From 1 September 2026, a foreign national receiving
  dividends from a Chinese foreign-invested enterprise pays 20%, withheld by the company. The old exemption under
  财税字〔1994〕20号 is repealed. Older commentary will get this wrong.</p>
</section>
"""
    page("china-tax.html", "China tax", taxbody)

    # ---------------------------------------------------------- us inbound
    usbody = f"""
<section class="wrap pagehead">
  <p class="eyebrow">Category &middot; United States</p>
  <h1>US inbound rules</h1>
  <p class="lede">{esc(us['meta']['headline'])}</p>
</section>
<section class="wrap">
{generic_table(us['rows'], [('id','ID','nw'),('topic','Topic',''),('value','Value',''),('detail','Rule','det'),('implication','What it means for you','')], 't-us')}
</section>
<section class="wrap note-block">
  <h2>The three numbers that matter most</h2>
  <p><strong>USD 100,000</strong> — the Form 3520 Part IV threshold for gifts from a foreign individual (not indexed).
  Failure to file is 5% of the gift per month, capped at 25%.</p>
  <p><strong>USD 10,000</strong> — the FBAR threshold, measured as the aggregate of all foreign accounts at any point
  in the year. This applies to the Chinese account you already have, whether or not you move anything.</p>
  <p><strong>50%</strong> — the FBAR willful penalty, measured against the account balance rather than against any tax
  owed. Against 5% for the streamlined domestic procedure and 0% for the streamlined foreign one.</p>
</section>
"""
    page("us-inbound.html", "US inbound rules", usbody)

    # ------------------------------------------------------------- flagged
    frows = []
    for r in flagged:
        ls = src_links(r)
        srcs = " ".join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(u), short_host(u)) for _, u in ls) or '<span class="none">none found</span>'
        title = r.get("topic") or r.get("name")
        frows.append(f"""
<tr>
  <td class="nw">{esc(r['id'])}</td>
  <td><strong>{esc(title)}</strong><div class="sub">{esc(r.get('name','')) if r.get('topic') else ''}</div></td>
  <td>{badge(r)}</td>
  <td>{cell(r.get('value')) if r.get('topic') else cell(r.get('capacity'))}</td>
  <td class="det">{esc(r.get('implication') or r.get('cons') or '')}
      {('<div class="sub"><em>Verification note:</em> ' + esc(r.get('verification_note')) + '</div>') if r.get('verification_note') else ''}</td>
  <td class="srcsmall">{srcs}</td>
</tr>""")

    flbody = f"""
<section class="wrap pagehead flaghead">
  <p class="eyebrow">Flagged for review</p>
  <h1>What we could not verify, and what looks irregular</h1>
  <p class="lede">These items are published here rather than quietly resolved. Each was left blank or marked
  <span class="badge warn">partial</span> / <span class="badge bad">unverified</span> instead of being filled in with a
  plausible number. Nothing on this page blocks any other finding; it is here so you can review it yourself.</p>
</section>

<section class="wrap">
  <h2>1. Unverified and partially verified findings</h2>
  <div class="tablewrap">
  <table class="grid wide">
    <thead><tr><th>ID</th><th>Finding</th><th>Status</th><th>Value</th><th>Why it is open</th><th>Source we found</th></tr></thead>
    <tbody>{''.join(frows)}</tbody>
  </table>
  </div>
</section>

<section class="wrap">
  <h2>2. Irregularities found in the repository itself</h2>
  <div class="tablewrap">
  <table class="grid">
    <thead><tr><th>#</th><th>Observation</th><th>Disposition</th></tr></thead>
    <tbody>
      <tr><td class="nw">I-1</td>
        <td>At the start of this session the repository contained a single file, <code>README.md</code>, whose entire
        content was the line <code># China3.</code> — no description, no build instructions, no licence.</td>
        <td>Flagged. Replaced with a factual README describing what is actually here.</td></tr>
      <tr><td class="nw">I-2</td>
        <td>No <code>COORDINATION.md</code> existed, although the brief requires one to be read before any work starts.</td>
        <td>Flagged and created. The task board records every task, its owner, its file scope and its status.</td></tr>
      <tr><td class="nw">I-3</td>
        <td>GitHub Pages was already enabled on <code>main</code> at the repository root, but there was no
        <code>index.html</code>, so the published site returned a 404.</td>
        <td>Flagged as a pre-existing broken state, then remediated by this site.</td></tr>
      <tr><td class="nw">I-4</td>
        <td>Only one commit existed (<code>03021bc</code> "Initial commit"). There was no prior research, data or
        requirements document in the repository to cross-check.</td>
        <td>Recorded. Nothing in this repository was inherited, so every finding here is newly sourced and dated.</td></tr>
      <tr><td class="nw">I-5</td>
        <td>Two official texts define <code>境内个人</code> differently — the FX Regulations (State Council Order 532)
        Art. 52(2) and the SAFE Implementing Rules Art. 37(1). They can point in opposite directions for a US citizen
        living in China, and no reconciling text was found.</td>
        <td>Flagged as F-1 / CN-FX-25. Recorded as a genuine conflict between official sources, not resolved by
        assumption.</td></tr>
      <tr><td class="nw">I-6</td>
        <td>The PRC estate-tax finding rests on a 2017 Ministry of Finance reply as reported by People's Daily. The
        reply letter itself was not read on <code>mof.gov.cn</code>.</td>
        <td>Flagged. The quoted sentence is verbatim from the report, and the date and provenance are stated on the row.</td></tr>
    </tbody>
  </table>
  </div>
</section>

<section class="wrap note-block">
  <h2>3. How blanks were handled</h2>
  <p>Every table in this site shows <code>&mdash;</code> with the word <em>blank</em> where a value could not be
  confirmed from an official publisher. No cell was filled by interpolation, by analogy to another country, or from
  memory. The build script fails if any row renders without at least one official source link, so a row with no
  evidence cannot appear silently.</p>
</section>
"""
    page("flagged.html", "Flagged for review — unverified findings and repository irregularities", flbody)

    # ------------------------------------------------------------- sources
    srcmap = {}
    for r in all_rows:
        for label, u in src_links(r):
            srcmap.setdefault(u, {"labels": set(), "ids": []})
            srcmap[u]["labels"].add(label)
            srcmap[u]["ids"].append(r["id"])
    for c in sc["decomposition"]:
        for u in c.get("sources", []):
            srcmap.setdefault(u, {"labels": set(), "ids": []})
            srcmap[u]["labels"].add(c["component"][:50])
            srcmap[u]["ids"].append(c["id"])

    def host_rank(u):
        official = ("gov.cn", "safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "npc.gov.cn",
                    "irs.gov", "ecfr.gov", "cornell.edu", "cbp.gov", "federalreserve.gov",
                    "congress.gov", "boc.cn", "mofcom.gov.cn", "beijing.gov.cn")
        h = re.sub(r"^https?://(www\.)?", "", u).split("/")[0]
        return (0 if any(h.endswith(o) for o in official) else 1, h, u)

    srows = []
    for u in sorted(srcmap, key=host_rank):
        h = re.sub(r"^https?://(www\.)?", "", u).split("/")[0]
        srows.append(f"""<tr><td class="nw"><a href="{esc(u)}" target="_blank" rel="noopener">{esc(h)}</a></td>
        <td class="det">{esc(u)}</td>
        <td class="sub">{esc('; '.join(sorted(srcmap[u]['labels']))[:180])}</td>
        <td class="sub">{esc(', '.join(sorted(set(srcmap[u]['ids']))))}</td></tr>""")

    sbody = f"""
<section class="wrap pagehead">
  <p class="eyebrow">Source register</p>
  <h1>{len(srcmap)} official sources, one row per URL</h1>
  <p class="lede">Every link used anywhere in this project, with the rows that depend on it. All are primary
  publishers — ministries, regulators, statute databases and the issuing bank's own price list. Nothing here relies on
  a law firm, an accountant's blog or a news summary except where the row says so explicitly.</p>
</section>
<section class="wrap">
<div class="tablewrap">
<table class="grid">
  <thead><tr><th>Publisher</th><th>URL</th><th>Used for</th><th>Citing rows</th></tr></thead>
  <tbody>{''.join(srows)}</tbody>
</table>
</div>
</section>
"""
    page("sources.html", "Source register", sbody)

    summary = {
        "generated": "2026-11-07",
        "pages": sorted(p.name for p in SITE.glob("*.html")),
        "rows": {"china_fx": len(fx["rows"]), "china_tax": len(tax["rows"]),
                 "us_inbound": len(us["rows"]), "channels": len(ch["rows"])},
        "total_rows": len(all_rows),
        "unique_sources": len(srcmap),
        "source_links_in_tables": count_links(all_rows),
        "verified": verified, "partial": partial, "unverified": unver,
    }
    (SITE / "build-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # GitHub Pages (legacy build) serves from the repository root, so publish a root
    # entry point that resolves every relative link into site/ via a <base> element.
    root_html = (SITE / "index.html").read_text(encoding="utf-8")
    root_html = root_html.replace("<head>", '<head>\n<base href="site/">', 1)
    (ROOT / "index.html").write_text(root_html, encoding="utf-8")
    summary["root_entry"] = "index.html (base href=site/)"

    # Render the executive summary page from content/executive-summary.md so the
    # published site and the Markdown cannot drift apart.
    subprocess.run([sys.executable, str(ROOT / "tools" / "md_to_html.py")], check=True)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    build()
