#!/usr/bin/env python3
"""
Build the m5f19 pages from data/m5f19_*.csv.

Generated, never hand-edited. Re-running this after
scripts/gen_m5f19_data.py + scripts/gen_m5f19_tables.py + scripts/m5f19_engine.py
must produce byte-identical output.
"""
from __future__ import annotations

import csv
import html
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m5f19_engine as eng  # noqa: E402

FETCHED = "2026-11-10"
PAGES = [
    ("m5f19-dashboard.html", "Summary"),
    ("m5f19-classification.html", "Which rules apply"),
    ("m5f19-costs.html", "Costs $10k\u2013$400k"),
    ("m5f19-methods.html", "Methods"),
    ("m5f19-steps.html", "Step by step"),
    ("m5f19-tax.html", "Tax & penalties"),
    ("m5f19-reconciliation.html", "Reconciliation"),
    ("m5f19-flagged.html", "Flagged for review"),
    ("m5f19-sources.html", "Sources"),
]


BOC_BOARD = "https://www.boc.cn/sourcedb/whpj/"
BOC_TARIFF = ("https://www.boc.cn/ebanking/service/cs1/200905/"
              "t20090506_990712.html")


def cost_src():
    """Per-row provenance for a derived cost figure.

    The brief requires an official-source link on EVERY table row. A cost row is
    derived rather than quoted, so it carries both inputs it derives from: the
    board that supplied the rate and the tariff that supplied the fees.
    """
    return (f'{src(BOC_BOARD, "board")} {src(BOC_TARIFF, "tariff")}'
            f' <span class="m5f19-fid">derived</span>')


def e(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def src(url, label=None):
    if not url:
        return '<span class="m5f19-b blank">no official source</span>'
    txt = label or url.split("//", 1)[-1].split("/", 1)[0]
    return (f'<a class="src" href="{e(url)}" target="_blank" '
            f'rel="noopener noreferrer">{e(txt)} &#8599;</a>')


def blank_cell():
    return '<span class="m5f19-b blank">BLANK &#183; UNVERIFIED</span>'


# --------------------------------------------------------------------------
# shared shell
# --------------------------------------------------------------------------
def page(filename, title, kicker, h1, sub, body):
    nav = []
    for f, label in PAGES:
        cur = ' aria-current="page"' if f == filename else ""
        nav.append(f'<a href="{e(f)}"{cur}>{e(label)}</a>')
    nav.append('<a href="index.html">Repository home &#8594;</a>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(sub[:155])}">
<link rel="stylesheet" href="assets/m5f19.css">
</head>
<body class="m5f19">
<header class="m5f19-hd"><div class="m5f19-hd-in">
<p class="m5f19-kicker">{e(kicker)}</p>
<h1>{e(h1)}</h1>
<p class="m5f19-sub">{e(sub)}</p>
</div></header>
<nav class="m5f19-nav" aria-label="Sections"><div class="m5f19-nav-in">
{''.join(nav)}
</div></nav>
<div class="m5f19-wrap">
{body}
<footer class="m5f19-ft">
<p><strong>Scope.</strong> Independent re-verification by session
<code>5f1925df</code> on {FETCHED}. Every value on these pages was read from an
official source on that date; anything that could not be read is left
<em>blank</em> and listed on <a href="m5f19-flagged.html">Flagged for review</a>.
No value is inferred, and no personal fact about the reader is assumed.</p>
<p><strong>Not a quotation, not advice.</strong> Bank of China states on its own
board page that the table is for reference only and that the executable rate is
the one shown in its online banking, mobile banking, smart counter or branch
counter, and it accepts no responsibility for results based on the table. Every
dollar figure here is therefore a model. General research, not legal or tax
advice.</p>
<p><strong>Other editions in this repository.</strong> This edition is published
<em>alongside</em> the earlier dashboards, not in place of them:
<a href="index.html">consolidated dashboard</a> &#183;
<a href="d646-summary.html">d646 refresh</a> &#183;
<a href="s775-dashboard.html">S775 audit</a> &#183;
<a href="verify-2026.html">2026 verification register</a> &#183;
<a href="a15-review.html">a15 safety review</a> &#183;
<a href="a502-review.html">a502 accuracy audit</a>.
Where this edition disagrees with them, the disagreement is stated on
<a href="m5f19-reconciliation.html">Reconciliation</a> and
<a href="m5f19-flagged.html">Flagged for review</a> rather than resolved silently.</p>
</footer>
</div>
<script src="assets/m5f19.js" defer></script>
</body>
</html>
"""


def table(caption, headers, body_rows, tid=None):
    """headers: list of (label, css_class). body_rows: list of list of cell HTML."""
    idattr = f' id="{e(tid)}"' if tid else ""
    thead = "".join(f'<th class="{c}">{e(h)}</th>' for h, c in headers)
    out = []
    for r in body_rows:
        tds = []
        for i, cell in enumerate(r):
            label = headers[i][0] if i < len(headers) else ""
            cls = headers[i][1] if i < len(headers) else ""
            first = " first" if i == 0 else ""
            tds.append(f'<td class="{cls}{first}" data-l="{e(label)}">{cell}</td>')
        out.append("<tr>" + "".join(tds) + "</tr>")
    return (f'<div class="m5f19-tw"><table class="m5f19-t"{idattr}>'
            f'<caption>{caption}</caption><thead><tr>{thead}</tr></thead>'
            f'<tbody>{"".join(out)}</tbody></table></div>')


def sec(title, lead="", inner="", sid=None):
    i = f' id="{e(sid)}"' if sid else ""
    return (f'<section class="m5f19-sec"{i}><h2>{title}</h2>'
            + (f'<p class="m5f19-lead">{lead}</p>' if lead else "")
            + inner + "</section>")


def note(text, kind=""):
    k = f" {kind}" if kind else ""
    return f'<div class="m5f19-note{k}">{text}</div>'


# ==========================================================================
# 1. Dashboard / summary
# ==========================================================================
def build_dashboard(d):
    lad = d["ladder"]
    one_ask = {int(r["amount_usd"]): r for r in lad
               if r["wires"] == "1" and r["denominator"] == "ask"}
    lo, hi = one_ask[10_000], one_ask[400_000]
    facts = d["facts"]

    b = []
    b.append(note(
        "<strong>The headline answer, before anything else.</strong> For a U.S. "
        "citizen, the money does not move because of a tax. It moves because of "
        "<em>documents</em> and because of <em>which category the bank recorded "
        "you in</em>. The published cost of a documented transfer is "
        f"<strong>USD {lo['total_usd']} on USD 10,000</strong> and "
        f"<strong>USD {hi['total_usd']} on USD 400,000</strong> \u2014 bank "
        "spread plus one wire fee plus one telecom charge. The largest number in "
        "this whole subject is not an exchange rate at all: it is a "
        "<strong>U.S. reporting penalty</strong> of up to 50% of the account "
        "balance for a willful FBAR failure, which is <strong>USD 200,000 on a "
        "USD 400,000 balance</strong>.", "ok"))

    b.append(note(
        "<strong>What this edition corrects.</strong> Earlier layers of this "
        "repository tell a U.S. citizen that a personal wire needs no approval "
        "\u201cup to USD 50,000 per day on ID\u201d and cite a SAFE page whose own "
        "question is about a <em>domestic</em> individual "
        "(\u5883\u5185\u4e2a\u4eba). The article that actually governs a "
        "passport-holder remitting foreign currency out of an FX account is "
        "Article 65(1) of the 2020 Current-Account Guidelines, and it states "
        "<strong>no amount threshold at all</strong> \u2014 identity document "
        "only. Article 65 appears nowhere else in this repository. See "
        '<a href="m5f19-classification.html">Which rules apply</a> and flag G01 '
        'on <a href="m5f19-flagged.html">Flagged for review</a>.', "warn"))

    # ---- the six numbers ----
    cards = [
        ("Tax on the act of converting",
         "no such tax found",
         "Currency conversion is not among the nine closed categories of taxable "
         "personal income in PRC IIT Law Art. 2. This says nothing about tax on "
         "the income that created the money.",
         "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
         "F36"),
        ("Known China-side cost, small transfer",
         f"USD {lo['total_usd']}",
         f"On USD 10,000 = {lo['total_pct']}%. Spread USD {lo['spread_usd']} + "
         f"wire fee USD {lo['fee_usd']} + telecom USD {lo['telecom_usd']}.",
         "https://www.boc.cn/sourcedb/whpj/", "F01,F03"),
        ("Known China-side cost, large transfer",
         f"USD {hi['total_usd']}",
         f"On USD 400,000 = {hi['total_pct']}%. The wire fee caps at CNY 260, so "
         "the all-in percentage falls as the transfer grows.",
         "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
         "F03"),
        ("Willful FBAR penalty, per violation",
         "USD 200,000",
         "Greater of USD 165,353 (inflation-adjusted) or 50% of the balance in "
         "the account at the time of the violation. On USD 400,000 the 50% limb "
         "governs. A per-violation maximum, not a ceiling on total exposure.",
         "https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm",
         "F47,F48"),
        ("FBAR filing trigger",
         "aggregate &gt; USD 10,000",
         "Aggregate across all foreign accounts, at any time during the calendar "
         "year. Due 15 April, automatic extension to 15 October, e-filed with "
         "FinCEN and not with the return.",
         "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar",
         "F45,F46"),
        ("U.S. tax on the currency gain",
         "USD 0 if personal",
         "26 U.S.C. \u00a7988(e) excludes gain on a personal disposition of "
         "nonfunctional currency \u2014 unless the gain exceeds USD 200, or the "
         "transaction is not personal under \u00a7988(e)(3). Your facts are "
         "unknown, so this is conditional.",
         "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm",
         "F43"),
    ]
    card_html = []
    for h, big, p, u, fid in cards:
        card_html.append(
            f'<div class="m5f19-card"><h3>{h}</h3>'
            f'<div class="m5f19-big">{big}</div><p>{p}</p>'
            f'<p style="margin-top:8px">{src(u)} '
            f'<span class="m5f19-fid">{e(fid)}</span></p></div>')
    b.append('<div class="m5f19-grid m5f19-cards">' + "".join(card_html) + "</div>")

    # ---- ranked routes ----
    # Route 1 buys no FX, so its cost is the fixed elements only.
    full400 = eng.leg_cost(eng.Decimal(400_000), 1, eng.ASK, eng.BID, "ask")
    no_spread_400 = eng.money(full400["fee_usd"] + full400["telecom_usd"])

    b.append(sec(
        "The routes, ranked by what the text actually supports",
        "Cost column is today\u2019s published board, one transfer, China side "
        "only. Every row links to the instrument that decides it. Ranked by "
        "documentary burden and by whether the instrument names a ceiling \u2014 "
        "not by fee, because at the bank the fee is the same for all of them.",
        table("Ranked routes \u00b7 figures derived from the "
              f"{eng.BOARD_DATE} {eng.BOARD_TIME} BOC board",
              [("#", ""), ("Route", ""), ("Who it is for", ""),
               ("Ceiling stated in the text", ""),
               ("Cost on USD 400,000", "num"), ("Source", ""), ("Facts", "")],
              [
                  ['<span class="m5f19-b ok">1</span>',
                   "<strong>FX already in an FX account, remitted out</strong><br>"
                   "<span class=\"m5f19-fid\">No purchase, so no spread at all</span>",
                   "Overseas individual (\u5883\u5916\u4e2a\u4eba)",
                   '<span class="m5f19-b ok">None stated</span> Art. 65(1) requires '
                   "only a valid identity document",
                   f"USD {no_spread_400}"
                   " <span class=\"m5f19-fid\">fee + telecom only, no purchase</span>",
                   src("https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html"),
                   '<span class="m5f19-fid">F11</span>'],
                  ['<span class="m5f19-b ok">2</span>',
                   "<strong>Documented current-account RMB income, purchased and "
                   "wired out</strong><br><span class=\"m5f19-fid\">Salary, labour "
                   "remuneration, rent, royalties, service fees</span>",
                   "Overseas individual with lawful onshore current-account RMB income",
                   '<span class="m5f19-b ok">None stated</span> \u2014 but a tax '
                   "certificate is required evidence",
                   f"USD {hi['total_usd']} <span class=\"m5f19-fid\">{hi['total_pct']}%</span>",
                   src("https://www.safe.gov.cn/tianjin/2024/0621/2529.html"),
                   '<span class="m5f19-fid">F09,F10,F14</span>'],
                  ['<span class="m5f19-b info">3</span>',
                   "<strong>Same, but classified as a domestic individual</strong>",
                   "Chinese citizen, or a foreigner continuously resident one year "
                   "on the Order 532 reading",
                   '<span class="m5f19-b info">USD 50,000 / day</span> is a '
                   "documentation threshold on the remittance leg, not a cap on the "
                   "purchase leg",
                   f"USD {hi['total_usd']} <span class=\"m5f19-fid\">same bank cost</span>",
                   src("https://www.safe.gov.cn/tianjin/2024/0229/2402.html"),
                   '<span class="m5f19-fid">F06,F12,F15</span>'],
                  ['<span class="m5f19-b info">4</span>',
                   "<strong>Emigrant property transfer</strong><br>"
                   "<span class=\"m5f19-fid\">\u79fb\u6c11\u8d22\u4ea7\u8f6c\u79fb</span>",
                   "A person emigrating who is cancelling a Chinese household "
                   "registration \u2014 not available to a U.S. citizen who never "
                   "held a hukou",
                   '<span class="m5f19-b ok">None stated</span> \u2014 the RMB '
                   "500,000 head-office filing and the installment requirement were "
                   "both abolished in 2014",
                   f"USD {hi['total_usd']} <span class=\"m5f19-fid\">one lump sum permitted</span>",
                   src("https://www.safe.gov.cn/tianjin/2024/0903/2594.html"),
                   '<span class="m5f19-fid">F23,F24,F25,F37</span>'],
                  ['<span class="m5f19-b info">5</span>',
                   "<strong>Proceeds of selling onshore real property</strong>",
                   "Overseas individual who owns onshore commercial residential "
                   "property",
                   '<span class="m5f19-b info">SAFE approval required</span> before '
                   "the purchase and remittance",
                   f"USD {hi['total_usd']} <span class=\"m5f19-fid\">plus 20% IIT on the gain</span>",
                   src("https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm"),
                   '<span class="m5f19-fid">F20,F35,F38</span>'],
                  ['<span class="m5f19-b info">6</span>',
                   "<strong>Investor\u2019s share of a lawfully liquidated "
                   "foreign-invested enterprise</strong>",
                   "The foreign investor in a terminated FIE \u2014 capital, not "
                   "personal savings",
                   '<span class="m5f19-b ok">None stated</span> \u2014 conditional on '
                   "liquidation and tax payment",
                   f"USD {hi['total_usd']} <span class=\"m5f19-fid\">plus corporate taxes</span>",
                   src("https://www.safe.gov.cn/safe/2008/0806/5321.html"),
                   '<span class="m5f19-fid">F22</span>'],
                  ['<span class="m5f19-b bad">Avoid</span>',
                   "<strong>Splitting, informal brokers, tokens, false invoices</strong>",
                   "n/a",
                   '<span class="m5f19-b bad">Prohibited</span>',
                   blank_cell() + ' <span class="m5f19-fid">no lawful cost exists</span>',
                   src("https://www.safe.gov.cn/safe/2008/0806/5321.html"),
                   '<span class="m5f19-fid">F16,F28,F29,F30,F50</span>'],
              ])))

    # ---- quick cost strip ----
    strip = []
    for a in (10_000, 50_000, 100_000, 200_000, 400_000):
        r = one_ask[a]
        strip.append([f"USD {a:,}", f"USD {r['cny_spent']}",
                      f"USD {r['spread_usd']}", f"USD {r['fee_usd']}",
                      f"USD {r['telecom_usd']}",
                      f"<strong>USD {r['total_usd']}</strong>",
                      f"{r['total_pct']}%", cost_src()])
    b.append(sec("Cost at a glance",
                 "One transfer, China side, at the "
                 f"{eng.BOARD_DATE} {eng.BOARD_TIME} published board. The full 40-step "
                 'schedule with both spread conventions and the multi-wire scenario is on '
                 '<a href="m5f19-costs.html">Costs $10k\u2013$400k</a>.',
                 table("Selected increments \u00b7 one wire \u00b7 spread measured "
                       "against the ask",
                       [("Transfer", "num"), ("CNY spent", "num"),
                        ("Spread", "num"), ("Wire fee", "num"),
                        ("Telecom", "num"), ("Total known cost", "num"),
                        ("All-in %", "num"), ("Source", "")],
                       strip),
                 sid="cost-glance"))

    # ---- the reading order ----
    b.append(sec("Read in this order", "",
                 '<div class="m5f19-grid m5f19-cards">'
                 + "".join(
                     f'<div class="m5f19-card"><h3>{i}</h3>'
                     f'<div class="m5f19-big" style="font-size:16px">'
                     f'<a href="{e(f)}">{e(t)}</a></div><p>{dd}</p></div>'
                     for i, (f, t, dd) in enumerate([
                         ("m5f19-classification.html", "Which rules apply to you",
                          "Nine questions. The answer changes which SAFE article "
                          "governs you, and the two official definitions of "
                          "\u201cdomestic individual\u201d disagree."),
                         ("m5f19-methods.html", "Every route, lawful and prohibited",
                          "20 methods with eligibility, the documents each one "
                          "demands, the ceiling its own text states, and its pros "
                          "and cons."),
                         ("m5f19-costs.html", "USD 10,000 to USD 400,000",
                          "All 40 increments, both spread conventions, one-wire "
                          "and staged-wire scenarios, each component broken out."),
                         ("m5f19-steps.html", "Exactly how to do it",
                          "Numbered steps for the routes that matter, each step "
                          "linked to the article that requires it."),
                         ("m5f19-tax.html", "Where the money actually goes",
                          "27 rows decomposing PRC tax, U.S. tax, PRC penalties "
                          "and U.S. penalties \u2014 with the unknowable cells "
                          "left blank."),
                         ("m5f19-reconciliation.html", "Why four numbers circulate",
                          "Every headline figure published by earlier sessions, "
                          "re-derived to the cent, with the reason they differ."),
                     ], 1)) + "</div>"))

    b.append(sec("What is genuinely unknown", "",
                 note("The brief supplies no amount, no account documents, no "
                      "source-of-funds history, no residence history, no bank, no "
                      "receiving bank and no U.S. filing history. Those facts decide "
                      "the route, the tax and the total. Everything here is therefore "
                      "conditional, and the cells that depend on those facts are "
                      "<em>blank</em> rather than estimated. Intermediary and "
                      "beneficiary-bank charges, the executable spread, the offshore "
                      "CNY basis, the Form 8938 threshold, U.S.\u2013China treaty "
                      "relief and state tax are all blank on "
                      '<a href="m5f19-tax.html">Tax &amp; penalties</a>.', "warn")))
    return page(PAGES[0][0],
                "Getting money out of China \u2014 verified edition, 10 Nov 2026",
                f"Independent re-verification \u00b7 {FETCHED} \u00b7 session 5f1925df",
                "The cost is small. The classification and the reporting are everything.",
                "A U.S. citizen's CNY balance moves on documents, not on a quota. "
                "Every figure re-derived today from primary sources; the unknowable "
                "ones left blank.",
                "".join(b))


# ==========================================================================
# 2. Classification decision tree
# ==========================================================================
def build_classification(d):
    b = [note(
        "<strong>This is the question the repository never asked.</strong> Chinese "
        "FX rules are written separately for a <em>domestic individual</em> "
        "(\u5883\u5185\u4e2a\u4eba) and an <em>overseas individual</em> "
        "(\u5883\u5916\u4e2a\u4eba), and the two get different articles, different "
        "documents and different thresholds. Two official instruments define the "
        "boundary <em>differently</em>. Until you know which box your account sits "
        "in, no cost figure and no route on any page of this repository applies to "
        "you.", "warn")]

    b.append(table("The two official definitions, side by side",
                   [("Instrument", ""), ("Rank", ""),
                    ("\u5883\u5185\u4e2a\u4eba domestic individual", ""),
                    ("\u5883\u5916\u4e2a\u4eba overseas individual", ""),
                    ("Verbatim", ""), ("Source", "")],
                   [["\u300a\u4e2d\u534e\u4eba\u6c11\u5171\u548c\u56fd\u5916\u6c47"
                     "\u7ba1\u7406\u6761\u4f8b\u300b State Council Order No. 532, "
                     "Art. 52(2)",
                     '<span class="m5f19-b info">Administrative regulation '
                     "(\u884c\u653f\u6cd5\u89c4)</span>",
                     "Chinese citizens <em>and</em> foreigners who have resided "
                     "continuously in the PRC for a full year (excluding foreign "
                     "diplomats and international-organisation representatives)",
                     "Not defined in terms; the complement",
                     '<div class="m5f19-q">\u5883\u5185\u4e2a\u4eba\uff0c\u662f\u6307'
                     '\u4e2d\u56fd\u516c\u6c11\u548c\u5728\u4e2d\u534e\u4eba\u6c11'
                     '\u5171\u548c\u56fd\u5883\u5185\u8fde\u7eed\u5c45\u4f4f\u6ee1'
                     '1\u5e74\u7684\u5916\u56fd\u4eba</div>',
                     src("https://www.safe.gov.cn/safe/2008/0806/5321.html")],
                    ["\u300a\u4e2a\u4eba\u5916\u6c47\u7ba1\u7406\u529e\u6cd5\u300b "
                     "PBOC Order [2006] No. 3, Art. 37",
                     '<span class="m5f19-b info">Departmental rule '
                     "(\u90e8\u95e8\u89c4\u7ae0)</span>",
                     "Chinese citizens holding a PRC resident identity card, "
                     "military identity document or armed-police identity document",
                     "Foreign citizens (including stateless persons) holding a "
                     "<strong>passport</strong>, a Home Return Permit, or a Taiwan "
                     "Travel Permit, plus HK/Macao/Taiwan compatriots",
                     '<div class="m5f19-q">\u5883\u5916\u4e2a\u4eba\u662f\u6307\u6301'
                     '\u62a4\u7167\u3001\u6e2f\u6fb3\u5c45\u6c11\u6765\u5f80\u5185'
                     '\u5730\u901a\u884c\u8bc1\u3001\u53f0\u6e7e\u5c45\u6c11\u6765'
                     '\u5f80\u5927\u9646\u901a\u884c\u8bc1\u7684\u5916\u56fd\u516c'
                     '\u6c11\uff08\u5305\u62ec\u65e0\u56fd\u7c4d\u4eba\uff09</div>',
                     src("https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm")]],
                   tid="definitions"))

    b.append(note(
        "<strong>How the conflict is resolved in practice.</strong> PBOC Order "
        "[2006] No. 3 Art. 28 provides that <em>the bank</em> determines the "
        "account-holder\u2019s subject category from the identity documents "
        "supplied at account opening. So the operative answer is not a legal "
        "argument \u2014 it is a question to your bank: which category does this "
        "account carry in the personal FX monitoring system? This session does not "
        "resolve the conflict between the two instruments and does not claim that "
        "one overrides the other for banking purposes.", "ok"))

    nodes = []
    for r in d["classification"]:
        nodes.append(
            f'<div class="m5f19-node">'
            f'<p class="q"><span class="n">{e(r["order"])}</span>'
            f'<span>{e(r["question"])}</span></p>'
            f'<div class="m5f19-branches">'
            f'<div class="m5f19-br yes"><span class="lbl">If yes</span>'
            f'<p>{e(r["if_yes"])}</p></div>'
            f'<div class="m5f19-br no"><span class="lbl">If no</span>'
            f'<p>{e(r["if_no"])}</p></div>'
            f'</div>'
            f'<p class="gov">{e(r["governing_text"])} &#183; '
            f'{src(r["source_url"])} '
            f'<span class="m5f19-fid">{e(r["fact_ids"])}</span></p>'
            f'</div>')
    b.append(sec("The nine questions", "Work down the list. The first question "
                 "that you cannot answer from your own documents is the one to put "
                 "to the bank in writing.",
                 '<div class="m5f19-tree">' + "".join(nodes) + "</div>",
                 sid="tree"))

    b.append(sec("What each category gets", "",
                 table("Purchase and remittance rules by category",
                       [("Leg", ""), ("Overseas individual (\u5883\u5916\u4e2a\u4eba)", ""),
                        ("Domestic individual (\u5883\u5185\u4e2a\u4eba)", ""),
                        ("Source", "")],
                       [["<strong>Purchase</strong> CNY \u2192 USD",
                         "Art. 59: valid ID + amount-bearing source-of-funds documents "
                         "<strong>including a tax certificate</strong>. The annual "
                         "convenience amount applies <strong>only</strong> if you hold "
                         "a Foreign Permanent Residence Identity Card.",
                         "Arts. 54-57: USD 50,000 per person per year on ID alone; "
                         "above that, ID + amount-bearing documents on the "
                         "<em>purpose</em> of the purchase funds, and a completed "
                         "\u300a\u4e2a\u4eba\u8d2d\u6c47\u7533\u8bf7\u4e66\u300b.",
                         src("https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html")],
                        ["<strong>Remit</strong> FX already in an FX account",
                         "Art. 65(1): valid ID. <strong>No amount threshold is "
                         "stated.</strong>",
                         "Art. 64(1): up to USD 50,000 equivalent cumulative "
                         "<em>per day</em> on ID; above that, ID + amount-bearing "
                         "materials, and the bank reviews that the purchase purpose "
                         "and the remittance purpose are consistent.",
                         src("https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html")],
                        ["<strong>Remit foreign cash</strong>",
                         "Art. 65(2): up to USD 10,000 equivalent per day on ID; "
                         "above that, customs-stamped declaration or the original "
                         "deposit bank\u2019s cash withdrawal slip.",
                         "Art. 64(2): up to USD 10,000 equivalent per day on ID; "
                         "above that, the same documents <em>plus</em> amount-bearing "
                         "materials.",
                         src("https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html")],
                        ["<strong>Convert back</strong> unused RMB from an earlier "
                         "exchange",
                         "Art. 60: ID + the original exchange slip, valid 24 months. "
                         "Up to USD 500/day on ID alone, or USD 1,000/day at "
                         "pre-departure locations outside the customs area.",
                         "Not the subject of Art. 60.",
                         src("https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html")],
                        ["<strong>Return</strong> unused FX that was remitted in",
                         "PBOC Art. 14: ID alone, back along the original route.",
                         "Not the subject of PBOC Art. 14.",
                         src("https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm")]])))
    return page(PAGES[1][0],
                "Which Chinese FX rules apply to a U.S. citizen \u2014 m5f19",
                f"Classification \u00b7 verified {FETCHED}",
                "Domestic individual, or overseas individual? Everything downstream "
                "depends on it.",
                "Two official instruments define the boundary differently. Nine "
                "questions decide which article governs you, each linked to its text.",
                "".join(b))


# ==========================================================================
# 3. Costs
# ==========================================================================
def build_costs(d):
    lad = d["ladder"]
    b = [note(
        f"<strong>Inputs, all read on {FETCHED}.</strong> BOC published board "
        f"{eng.BOARD_DATE} {eng.BOARD_TIME}: USD ask <strong>{eng.ASK}</strong>, "
        f"bid <strong>{eng.BID}</strong>, midpoint <strong>{eng.MID}</strong> CNY per "
        "USD. BOC personal wire tariff: 1\u2030 of the remittance amount, floor CNY "
        "50, ceiling CNY 260, plus a CNY 150 telecom charge outside Hong Kong, "
        f"Macao and Taiwan. Fixed components at this board: ceiling CNY 260 = "
        f"<strong>USD {eng.money(eng.FEE_MAX_CNY / eng.ASK)}</strong>, telecom CNY "
        f"150 = <strong>USD {eng.money(eng.TELECOM_CNY_NON_HMT / eng.ASK)}</strong>.",
        "ok")]

    b.append(note(
        "<strong>The convention, stated once.</strong> To buy USD X you spend "
        "CNY <code>X \u00d7 ask</code>. Against a hypothetical zero-spread midpoint "
        "you overspend CNY <code>X \u00d7 (ask \u2212 mid)</code>. That overspend is "
        "an <em>opportunity cost borne in the CNY you pay</em>. It is "
        "<strong>not</strong> a second deduction from the USD you receive: buying "
        "USD X at the ask delivers USD X. Earlier layers of this repository deducted "
        "both, which is the double-count that sessions a502 and a058 flagged. Two "
        "denominators are reported and never mixed: "
        f"<code>(ask\u2212mid)/ask = {(eng.ASK - eng.MID) / eng.ASK * 100:.6f}%</code> "
        "and "
        f"<code>(ask\u2212mid)/mid = {(eng.ASK - eng.MID) / eng.MID * 100:.6f}%</code>.",
        "warn"))

    def block(wires, denom, caption, extra=""):
        rs = [r for r in lad if r["wires"] == str(wires) and r["denominator"] == denom]
        body = []
        for r in rs:
            body.append([
                f"USD {int(r['amount_usd']):,}",
                f"CNY {float(r['cny_spent']):,.2f}",
                f"{r['spread_usd']}",
                f"{r['fee_usd']}",
                f"{r['telecom_usd']}",
                f"<strong>{r['total_usd']}</strong>",
                f"{r['total_pct']}%",
                cost_src(),
            ])
        return (f'<details class="m5f19-d"{" open" if extra == "open" else ""}>'
                f'<summary>{caption} <span class="m5f19-fid">{len(rs)} rows</span>'
                f'</summary><div class="m5f19-dbody">'
                + table(caption + f" \u00b7 board {eng.BOARD_DATE} {eng.BOARD_TIME}",
                        [("Transfer", "num"), ("CNY spent", "num"),
                         ("Spread USD", "num"), ("Wire fee USD", "num"),
                         ("Telecom USD", "num"), ("Total USD", "num"),
                         ("All-in %", "num"), ("Source", "")], body)
                + "</div></details>")

    b.append(sec("Primary schedule \u2014 one wire, spread against the ask",
                 "USD 10,000 to USD 400,000 in USD 10,000 increments. This is the "
                 "text-supported case: Guidelines Art. 65(1) states no amount "
                 "threshold for an overseas individual remitting FX from an FX "
                 "account, and Art. 64(1) permits a domestic individual to exceed "
                 "USD 50,000 in a day on documents. Nothing in either article "
                 "requires staging across years.",
                 block(1, "ask", "One wire \u00b7 spread / ask", "open"),
                 sid="primary"))

    b.append(sec("Sensitivity \u2014 the other denominator",
                 "Same board, same wire count, spread divided by the midpoint "
                 "instead of the ask. This is the convention used by session "
                 "d6467425 and it is the entire reason its USD 10,000 figure is "
                 "USD 53.47 rather than USD 53.42.",
                 block(1, "mid", "One wire \u00b7 spread / mid")))

    b.append(sec("Scenario \u2014 eight staged wires",
                 "Priced because session d6467425 published it, and because a bank "
                 "or SAFE branch could require staging in a particular case. It is "
                 "<strong>not</strong> what Art. 64 or Art. 65 requires. The spread "
                 "is unchanged because it is proportional; the fixed CNY 150 "
                 "telecom charge and the CNY 260 fee ceiling are multiplied by "
                 "eight, which is the whole difference.",
                 block(8, "ask", "Eight wires \u00b7 spread / ask")
                 + note("At USD 400,000 the eight-wire scenario costs "
                        f"<strong>USD {eng.leg_cost(eng.Decimal(400000), 8, eng.ASK, eng.BID, 'ask')['total_usd']}</strong> "
                        f"against <strong>USD {eng.leg_cost(eng.Decimal(400000), 1, eng.ASK, eng.BID, 'ask')['total_usd']}</strong> "
                        "for one wire. The extra cost buys nothing: no instrument "
                        "reviewed requires the transfer to be split.", "bad")))

    b.append(sec("Reading the table", "",
                 "<ol class=\"m5f19-steps\">"
                 "<li><b>CNY spent</b> is what leaves your RMB account: "
                 "<code>transfer \u00d7 ask</code>. It is not a cost, it is the "
                 "consideration.</li>"
                 "<li><b>Spread</b> is the opportunity cost of paying the ask rather "
                 "than a hypothetical midpoint. It is what the bank earns.</li>"
                 "<li><b>Wire fee</b> is 1\u2030 of the remittance amount with a CNY "
                 f"50 floor and a CNY 260 ceiling. The ceiling binds above about "
                 f"USD {int(eng.FEE_MAX_CNY / eng.FEE_RATE / eng.ASK):,} of transfer, "
                 "which is why the all-in percentage falls as the amount grows.</li>"
                 "<li><b>Telecom</b> is a flat CNY 150 per transaction outside Hong "
                 "Kong, Macao and Taiwan. It is the only purely fixed element, so it "
                 "is what staging multiplies.</li>"
                 "<li><b>Total</b> is the sum of the three. It excludes intermediary "
                 "and beneficiary-bank charges, which no official source reviewed "
                 "publishes, and it excludes any tax on the underlying income.</li>"
                 "</ol>"))

    b.append(note("<strong>These are models, not quotes.</strong> BOC\u2019s own "
                  "declaration on the board page says the table is for reference "
                  "only, that the executable rate is the one in its online banking, "
                  "mobile banking, smart counter or branch counter, and that BOC "
                  "accepts no responsibility for results from using the table. "
                  "Tariff note 1 lets agreements, promotions and local charging "
                  "differences override the published charges. The board also moves "
                  "intraday: this session read ask 6.6851 at 17:39:58 where earlier "
                  "sessions read 6.6903 at 07:32:39 the same morning.", "bad"))
    return page(PAGES[2][0],
                "CNY\u2192USD cost schedule USD 10,000\u2013400,000 \u2014 m5f19",
                f"Cost model \u00b7 board {eng.BOARD_DATE} {eng.BOARD_TIME} \u00b7 "
                f"verified {FETCHED}",
                "Every USD 10,000 increment from 10,000 to 400,000, with each cost "
                "component broken out.",
                "40 increments, two spread conventions, one-wire and staged-wire "
                "scenarios, all re-derived from today's published board and tariff.",
                "".join(b))


# ==========================================================================
# 4. Methods
# ==========================================================================
def build_methods(d):
    ms = d["methods"]
    lawful = [m for m in ms if not m["legal_status"].startswith("PROHIBITED")]
    prohibited = [m for m in ms if m["legal_status"].startswith("PROHIBITED")]

    def status_badge(s):
        if s.startswith("PROHIBITED"):
            return f'<span class="m5f19-b bad">{e(s)}</span>'
        if "approval" in s or "only" in s:
            return f'<span class="m5f19-b warn">{e(s)}</span>'
        return f'<span class="m5f19-b ok">{e(s)}</span>'

    def detail(m):
        ceiling = m["amount_ceiling_stated_in_text"] or blank_cell()
        pros = m["pros"] or '<span class="m5f19-fid">None stated \u2014 this route ' \
                            'is recorded so its consequences are on the record.</span>'
        fids = m["fact_ids"]
        fact_html = ""
        if fids:
            for fid in fids.split(","):
                f = d["facts_by_id"].get(fid)
                if not f:
                    continue
                fact_html += (
                    f'<p style="margin:14px 0 4px;font-size:12.5px;color:var(--dim);'
                    f'font-family:var(--mono)">{e(fid)} \u00b7 '
                    f'{e(f["instrument"])} \u00b7 {e(f["article"])}</p>'
                    f'<div class="m5f19-q">{e(f["verbatim_original"])}</div>'
                    f'<p style="margin:6px 0 0;font-size:13.5px;color:var(--muted)">'
                    f'{e(f["english_gist"])}</p>')
        return (
            f'<details class="m5f19-d" id="{e(m["id"])}">'
            f'<summary><span class="m5f19-fid">{e(m["id"])}</span> '
            f'<span>{e(m["name"])}</span> {status_badge(m["legal_status"])}'
            f'</summary><div class="m5f19-dbody">'
            f'<p style="margin:12px 0 4px"><strong>Who it is for.</strong> '
            f'<span style="color:var(--muted)">{e(m["who"])}</span></p>'
            f'<p style="margin:8px 0 4px"><strong>Governing instrument.</strong> '
            f'<span style="color:var(--muted)">{e(m["governing_instrument"])}</span></p>'
            f'<p style="margin:8px 0 4px"><strong>Documents required.</strong> '
            f'<span style="color:var(--muted)">{e(m["documents_required"])}</span></p>'
            f'<p style="margin:8px 0 4px"><strong>Ceiling stated in the text.</strong> '
            f'<span style="color:var(--muted)">{ceiling}</span></p>'
            f'<p style="margin:12px 0 4px"><strong>Pros.</strong></p>'
            f'<p style="margin:0 0 4px;color:var(--muted)">{pros}</p>'
            f'<p style="margin:12px 0 4px"><strong>Cons and limits.</strong></p>'
            f'<p style="margin:0;color:var(--muted)">{e(m["cons"])}</p>'
            f'<p style="margin:14px 0 0">Source: {src(m["source_url"])}</p>'
            f'<p style="margin:16px 0 4px;font-size:12.5px;color:var(--dim);'
            f'font-family:var(--mono);letter-spacing:.06em">VERBATIM TEXT RELIED ON</p>'
            f'{fact_html or "<p class=m5f19-fid>none</p>"}'
            f'</div></details>')

    b = [note(f"<strong>{len(lawful)} lawful routes and {len(prohibited)} "
              "prohibited ones.</strong> The prohibited routes are listed rather "
              "than omitted, with the article that prohibits each and the penalty "
              "band it carries, so the consequences are on the record. No cost is "
              "shown for a prohibited route: there is no lawful price for it.",
              "warn")]
    b.append(sec("Lawful routes", "", "".join(detail(m) for m in lawful),
                 sid="lawful"))
    b.append(sec("Prohibited routes \u2014 recorded with their consequences", "",
                 "".join(detail(m) for m in prohibited), sid="prohibited"))

    b.append(sec("Index", "",
                 table("All 20 methods",
                       [("ID", "id"), ("Method", ""), ("Status", ""),
                        ("Ceiling in the text", ""), ("Source", "")],
                       [[f'<a href="#{e(m["id"])}">{e(m["id"])}</a>',
                         e(m["name"]), status_badge(m["legal_status"]),
                         e(m["amount_ceiling_stated_in_text"]) or "\u2014",
                         src(m["source_url"])] for m in ms])))
    return page(PAGES[3][0],
                "Every CNY\u2192USD route with pros and cons \u2014 m5f19",
                f"Method catalogue \u00b7 verified {FETCHED}",
                "20 routes: eligibility, documents, the ceiling each text states, "
                "pros and cons.",
                "Each method expands to the verbatim official text it relies on, "
                "with the source link.",
                "".join(b))


# ==========================================================================
# 5. Steps
# ==========================================================================
def build_steps(d):
    by_m = {}
    for s in d["steps"]:
        by_m.setdefault(s["method_id"], []).append(s)
    names = {m["id"]: m["name"] for m in d["methods"]}
    order = ["M01", "M03", "M05", "M07", "M17"]
    b = [note("<strong>Each step cites the article that requires it.</strong> Where "
              "a step depends on a fact this session does not have, the step says so "
              "instead of guessing. The order within a route is often mandatory, not "
              "suggested \u2014 most sharply in the emigrant route, where the tax "
              "clearance must be completed <em>before</em> the household registration "
              "is cancelled.", "warn")]
    parts = []
    for mid in order:
        st = sorted(by_m.get(mid, []), key=lambda r: int(r["step_no"]))
        if not st:
            continue
        lis = "".join(
            f'<li><b>Step {e(s["step_no"])}.</b> {e(s["instruction"])} '
            f'<br>{src(s["source_url"])}</li>' for s in st)
        parts.append(
            f'<details class="m5f19-d" id="{e(mid)}"{" open" if mid == "M01" else ""}>'
            f'<summary><span class="m5f19-fid">{e(mid)}</span> '
            f'<span>{e(names.get(mid, mid))}</span> '
            f'<span class="m5f19-fid">{len(st)} steps</span></summary>'
            f'<div class="m5f19-dbody"><ol class="m5f19-steps">{lis}</ol>'
            f'</div></details>')
    b.append(sec("Playbooks", "", "".join(parts), sid="playbooks"))
    return page(PAGES[4][0],
                "Step-by-step execution playbooks \u2014 m5f19",
                f"Playbooks \u00b7 verified {FETCHED}",
                "Exactly how each route works, step by step, with the article behind "
                "every step.",
                "Numbered playbooks for the documented routes and for the prohibited "
                "one, so the consequences are on the record too.",
                "".join(b))


# ==========================================================================
# 6. Tax and penalties
# ==========================================================================
def build_tax(d):
    tx = d["tax"]
    cn = [t for t in tx if t["jurisdiction"] == "CN"]
    us = [t for t in tx if t["jurisdiction"] == "US"]

    def rows_for(items):
        out = []
        for t in items:
            val = t["verified_rule_or_value"]
            val_html = blank_cell() if not val else e(val)
            badge = ('<span class="m5f19-b warn">unverified</span>'
                     if t["status"] != "verified"
                     else '<span class="m5f19-b ok">verified</span>')
            out.append([
                f'{e(t["id"])}<br><span class="m5f19-fid">{e(t["item"])}</span>',
                val_html,
                e(t["what_it_means"]),
                e(t["instrument"]) or "\u2014",
                src(t["source_url"]) if t["source_url"] else "\u2014",
                f'{badge} <span class="m5f19-fid">{e(t["fact_ids"])}</span>',
            ])
        return out

    hdrs = [("Item", ""), ("Verified rule or value", ""), ("What it means", ""),
            ("Instrument", ""), ("Source", ""), ("Status", "")]
    b = [note("<strong>The \u201cconsiderable amount of taxes\u201d in the brief is "
              "not identified in any instrument reviewed.</strong> No tax assessment, "
              "bank quotation, tax receipt, named tax or amount was supplied. What "
              "the sources do establish is narrower and more useful: no reviewed "
              "instrument taxes the <em>act</em> of converting your own CNY, while "
              "the income that <em>created</em> the money is taxable under PRC IIT "
              "Law Art. 3 at 3\u201345%, 5\u201335% or a flat 20% depending on its "
              "category. The tax certificate that Guidelines Art. 59 requires at the "
              "counter is <em>evidence that this was already settled</em> \u2014 it "
              "is not a new levy.", "warn")]
    b.append(sec(f"China side \u2014 {len(cn)} rows", "",
                 table("PRC tax and penalties", hdrs, rows_for(cn)), sid="cn"))
    b.append(sec(f"United States side \u2014 {len(us)} rows", "",
                 table("U.S. tax, reporting and penalties", hdrs, rows_for(us)),
                 sid="us"))

    b.append(sec("The conversion penalty, decomposed",
                 "What people call the \u201cconversion penalty\u201d is four "
                 "different things that are routinely added together. Separated, "
                 "only one of them is a recurring cost of moving the money.",
                 table("Four components, four different legal characters",
                       [("Component", ""), ("Size", "num"), ("What it actually is", ""),
                        ("Avoidable?", ""), ("Source", "")],
                       [["<strong>Bank spread</strong>",
                         f"{(eng.ASK - eng.MID) / eng.ASK * 100:.4f}% of the transfer",
                         "The difference between the ask you pay and a hypothetical "
                         "midpoint. A price, not a penalty, and not a tax.",
                         "Only by not converting, or by holding FX already \u2014 see "
                         "route M03, where there is no purchase and therefore no "
                         "spread at all.",
                         src("https://www.boc.cn/sourcedb/whpj/")],
                        ["<strong>Wire fee + telecom</strong>",
                         f"USD {eng.money(eng.FEE_MAX_CNY / eng.ASK)} + "
                         f"USD {eng.money(eng.TELECOM_CNY_NON_HMT / eng.ASK)} at the "
                         "ceiling",
                         "A published bank tariff. 1\u2030 with a CNY 260 ceiling, "
                         "plus a flat CNY 150 telecom charge per transaction.",
                         "Partly. The ceiling binds above roughly USD 38,900, and "
                         "sending one wire instead of eight pays the flat element "
                         "once.",
                         src("https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html")],
                        ["<strong>PRC tax on the underlying income</strong>",
                         "0% to 45%, on the facts",
                         "IIT on how the money was earned. Due whether or not the "
                         "money ever leaves China. The tax certificate demanded at "
                         "the counter is evidence that it was settled.",
                         "Not a cost of moving the money at all. It is a cost of "
                         "having earned it, and it is already sunk by the time you "
                         "reach the counter.",
                         src("https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html")],
                        ["<strong>U.S. reporting penalty</strong>",
                         "up to 50% of the balance",
                         "Not a tax and not an exchange cost. The consequence of not "
                         "filing FinCEN Form 114 where the aggregate of your foreign "
                         "accounts exceeded USD 10,000 at any time in the year.",
                         "Entirely. File the FBAR. The reasonable-cause exception at "
                         "\u00a75321(a)(5)(B)(ii) is unavailable once the violation "
                         "is willful.",
                         src("https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm")]]),
                 sid="decomposition"))

    b.append(note(
        "<strong>Worked example on a USD 400,000 balance.</strong> Reported "
        "correctly and moved on documents: the known China-side cost is "
        f"<strong>USD {eng.leg_cost(eng.Decimal(400000), 1, eng.ASK, eng.BID, 'ask')['total_usd']}</strong> "
        f"({eng.leg_cost(eng.Decimal(400000), 1, eng.ASK, eng.BID, 'ask')['total_pct']}%), "
        "plus whatever PRC tax was already due on the income, plus U.S. tax only if "
        "\u00a7988(e) does not exclude the gain. Not reported, and treated as "
        "willful: <strong>USD 200,000</strong>, being 50% of the balance, which "
        "exceeds the USD 165,353 adjusted fixed maximum \u2014 and that is a "
        "<em>per-violation</em> figure, since 31 CFR 1010.821(b) provides that the "
        "adjusted maxima do not limit the total where a penalty may be imposed for "
        "each day a violation continues. The reporting decision is worth roughly "
        "220 times the exchange decision.", "bad"))
    return page(PAGES[5][0],
                "Tax and penalty decomposition, PRC and U.S. \u2014 m5f19",
                f"Tax & penalties \u00b7 verified {FETCHED}",
                "Where the money actually goes, and which of it is a tax at all.",
                "27 rows across PRC and U.S. law, with the unknowable cells left "
                "blank rather than estimated.",
                "".join(b))


# ==========================================================================
# 7. Reconciliation
# ==========================================================================
def build_reconciliation(d):
    rec = d["reconciliation"]
    legacy = [r for r in rec if "this session" not in r["session"]]
    own = [r for r in rec if "this session" in r["session"]]
    b = [note("<strong>Four headline figures circulate in this repository for the "
              "same transfer.</strong> USD 53.42 and USD 901.30 on the consolidated "
              "dashboard; USD 53.47 and USD 1,332.05 on the d646 refresh; USD 53.42 "
              "again on the S775 pages. Sessions logged the disagreement as a "
              "\u201cconvention difference\u201d without ever demonstrating it. This "
              "page re-derives every one of them from first principles. All five "
              "published legacy figures reproduce <strong>to the cent</strong>, "
              "which settles the question: there is no data error, only a "
              "denominator choice and a wire count.", "ok")]

    def tbl(items, cap):
        return table(cap,
                     [("Model", ""), ("Session", ""), ("Board ask", "num"),
                      ("Board bid", "num"), ("Wires", "num"),
                      ("Denominator", ""), ("Amount", "num"),
                      ("Published", "num"), ("Re-derived", "num"),
                      ("Delta", "num"), ("Exact", ""), ("Appears in", ""),
                      ("Source", "")],
                     [[e(r["model"]), e(r["session"]), e(r["board_ask"]),
                       e(r["board_bid"]), e(r["wires"]),
                       f'<code>{e(r["spread_denominator"])}</code>',
                       f'USD {int(r["amount_usd"]):,}',
                       f'USD {r["published_usd"]}',
                       f'<strong>USD {r["reproduced_usd"]}</strong>',
                       e(r["delta_usd"]),
                       '<span class="m5f19-b ok">YES</span>'
                       if r["reproduced_exactly"] == "yes"
                       else '<span class="m5f19-b bad">NO</span>',
                       f'<span class="m5f19-fid">{e(r["appears_in"])}</span>',
                       cost_src()]
                      for r in items])

    b.append(sec("Figures published by earlier sessions", "",
                 tbl(legacy, "Re-derivation of merged headline figures \u00b7 all "
                     "reproduce exactly"), sid="legacy"))
    b.append(sec("This session\u2019s figures", "",
                 tbl(own, "m5f19 figures as published on m5f19-costs.html"),
                 sid="own"))

    b.append(sec("Why they differ, in full", "",
                 "<ol class=\"m5f19-steps\">"
                 "<li><b>The board moved during the day.</b> Sessions fbbd3b22, "
                 "d6467425 and 775c9619 all read the BOC board at 07:32:39 on "
                 f"{eng.BOARD_DATE} and used ask 6.6903 / bid 6.6622. This session "
                 f"read it at {eng.BOARD_TIME} and got ask {eng.ASK} / bid "
                 f"{eng.BID}. The board is a live page, so the same code run at a "
                 "different hour produces different dollars. This is a property of "
                 "the source, not an error in anyone\u2019s arithmetic.</li>"
                 "<li><b>Two spread denominators.</b> Dividing the half-spread by "
                 "the ask gives "
                 f"{(eng.ASK - eng.MID) / eng.ASK * 100:.6f}% at today\u2019s board; "
                 "dividing by the midpoint gives "
                 f"{(eng.ASK - eng.MID) / eng.MID * 100:.6f}%. On the legacy board "
                 "the same choice produced 0.210005% versus 0.210446%, which is "
                 "exactly the USD 0.05 gap between USD 53.42 and USD 53.47 at "
                 "USD 10,000. Neither is wrong; they measure against different "
                 "baselines and must never be mixed in one column.</li>"
                 "<li><b>A wire count.</b> The USD 400,000 gap between USD 901.30 "
                 "and USD 1,332.05 is not a rate difference at all. It is one wire "
                 "versus eight. The spread is proportional so it does not change; "
                 "the CNY 260 fee ceiling and the flat CNY 150 telecom charge are "
                 "per transaction, so eight wires pay the fixed element eight "
                 "times.</li>"
                 "<li><b>And the eight-wire premise itself does not survive the "
                 "text.</b> Guidelines Art. 65(1) states no amount threshold for an "
                 "overseas individual remitting FX from an FX account, and Art. "
                 "64(1) lets a domestic individual exceed USD 50,000 in a single day "
                 "on documents. SAFE Ningxia states there is no amount limit on "
                 "genuine, lawful current-account purchase and settlement. Nothing "
                 "in any of these requires eight transfers over eight years. The "
                 "scenario is legitimate as a <em>contingency</em> if a bank stages "
                 "the transfer, but it must not be presented as what the regulation "
                 "requires.</li>"
                 "</ol>", sid="why"))

    b.append(sec("Which number should you use?", "",
                 note(f"Use <strong>USD "
                      f"{eng.leg_cost(eng.Decimal(400000), 1, eng.ASK, eng.BID, 'ask')['total_usd']}</strong> "
                      "on USD 400,000 and <strong>USD "
                      f"{eng.leg_cost(eng.Decimal(10000), 1, eng.ASK, eng.BID, 'ask')['total_usd']}</strong> "
                      "on USD 10,000 \u2014 one wire, spread against the ask, on "
                      f"the {eng.BOARD_DATE} {eng.BOARD_TIME} board \u2014 and treat "
                      "both as models. Then get a written bank quotation, which is "
                      "the only thing that closes the gap between a model and a "
                      "price. The earlier figures are not wrong; they answer a "
                      "slightly different question, and now the difference is "
                      "documented instead of argued about.", "ok")))
    return page(PAGES[6][0],
                "Reconciling four conflicting cost figures \u2014 m5f19",
                f"Reconciliation \u00b7 verified {FETCHED}",
                "Why four different numbers circulate for the same transfer \u2014 "
                "and all of them reproduce exactly.",
                "Every published headline figure re-derived from first principles, "
                "with the three reasons they diverge.",
                "".join(b))


# ==========================================================================
# 8. Flagged for review
# ==========================================================================
# Cells left blank rather than estimated. Each one names what evidence would
# close it, so a reader can tell "unknown" from "zero".
BLANK_CELLS = [
    ("Executable bank spread",
     "The published board is expressly for reference only and BOC disclaims "
     "results based on it.",
     "A written quotation from the executing bank."),
    ("Intermediary and beneficiary bank charges",
     "No official source reviewed publishes them for a personal CNY\u2192USD "
     "wire; they are commercial and depend on the OUR/SHA/BEN charge option.",
     "A written quotation naming the charge option and the correspondent chain."),
    ("Offshore CNY/CNH basis",
     "No official source reviewed publishes a current basis.",
     "A live market source at execution time."),
    ("Form 8938 threshold",
     "Not fetched by this session; earlier layers carry figures this edition did "
     "not read today.",
     "Fetch the IRS Form 8938 comparison page and the instructions."),
    ("U.S.\u2013China income tax treaty relief",
     "The treaty text was not fetched, so no article, rate or relief is asserted.",
     "Fetch the treaty and read the relevant article."),
    ("State-level tax on a \u00a7988 gain",
     "Depends on the state of residence, which was not supplied.",
     "The taxpayer\u2019s state of residence."),
    ("The user\u2019s subject category (domestic or overseas individual)",
     "No account documents or residence history were supplied, and the two "
     "official definitions conflict.",
     "Written confirmation from the account-opening bank."),
    ("PRC tax on the underlying income",
     "No amount, source-of-funds history or tax filings were supplied.",
     "The income\u2019s category under IIT Law Art. 2 and the taxpayer\u2019s "
     "status under Art. 1."),
]

def build_flagged(d):
    fl = d["flags"]
    kinds = {"irregularity": "bad", "limitation": "warn", "process": "info",
             "observation": "ok"}
    order = {"irregularity": 0, "limitation": 1, "process": 2, "observation": 3}
    fl = sorted(fl, key=lambda r: (order.get(r["kind"], 9), r["id"]))
    items = []
    for f in fl:
        k = kinds.get(f["kind"], "info")
        items.append(
            f'<details class="m5f19-d" id="{e(f["id"])}">'
            f'<summary><span class="m5f19-fid">{e(f["id"])}</span> '
            f'<span class="m5f19-b {k}">{e(f["kind"])}</span> '
            f'<span>{e(f["finding"][:96])}\u2026</span></summary>'
            f'<div class="m5f19-dbody">'
            f'<p style="margin:12px 0"><strong>Finding.</strong> '
            f'<span style="color:var(--muted)">{e(f["finding"])}</span></p>'
            f'<p style="margin:10px 0"><strong>Recommended action.</strong> '
            f'<span style="color:var(--muted)">{e(f["recommended_action"])}</span></p>'
            f'<p style="margin:10px 0"><strong>Files affected.</strong> '
            f'<code style="font-family:var(--mono);font-size:12.5px;color:var(--dim)">'
            f'{e(f["files_affected"])}</code></p>'
            f'<p style="margin:10px 0"><strong>Source.</strong> '
            f'{src(f["source_url"]) if f["source_url"] else blank_cell()} '
            f'<span class="m5f19-fid">{e(f["fact_ids"])}</span></p>'
            f'<p style="margin:10px 0"><strong>Status.</strong> '
            f'<span class="m5f19-b {k}">{e(f["status"])}</span></p>'
            f'</div></details>')
    b = [note("<strong>Nothing on this page blocks anything.</strong> These are "
              "irregularities found in the repository, limitations of this "
              "edition\u2019s evidence, and process observations. Per the "
              "coordination rules, <code>needs review</code> means published here "
              "for the owner to act on. Where a fix belongs to a file another "
              "session owns, this session logged a request on the board instead of "
              "editing that file.", "warn")]
    b.append(table("Index",
                   [("ID", "id"), ("Kind", ""), ("Finding", ""),
                    ("Files affected", ""), ("Status", ""), ("Source", "")],
                   [[f'<a href="#{e(f["id"])}">{e(f["id"])}</a>',
                     f'<span class="m5f19-b {kinds.get(f["kind"], "info")}">'
                     f'{e(f["kind"])}</span>',
                     e(f["finding"][:150]) + "\u2026",
                     f'<span class="m5f19-fid">{e(f["files_affected"])}</span>',
                     e(f["status"]),
                     src(f["source_url"]) if f["source_url"]
                     else '<span class="m5f19-b blank">BLANK &#183; no official '
                          'source &#183; UNVERIFIED</span>'] for f in fl]))
    b.append(sec("Detail", "", "".join(items), sid="detail"))

    b.append(sec("Cells deliberately left blank", "",
table("Blank, not zero \u00b7 no value is inferred anywhere in this edition",
                       [("Item", ""), ("Value", ""), ("Why it is blank", ""),
                        ("What would close it", "")],
                       [[e(item), blank_cell(), e(why), e(closer)]
                        for item, why, closer in BLANK_CELLS])))
    return page(PAGES[7][0],
                "Flagged for review \u2014 m5f19",
                f"Flags \u00b7 {FETCHED} \u00b7 non-blocking",
                f"{len(fl)} irregularities, limitations and observations.",
                "What this session found wrong, what it could not verify, and what "
                "it deliberately left blank instead of estimating.",
                "".join(b))


# ==========================================================================
# 9. Sources and facts
# ==========================================================================
def build_sources(d):
    ss, ff = d["sources"], d["facts"]
    b = [note(f"<strong>{len(ss)} official documents, all fetched on {FETCHED} by "
              f"this session.</strong> Nothing here is inherited from another "
              "session\u2019s register. Below the register are the "
              f"{len(ff)} verbatim passages actually relied on, in the original "
              "language, with an English gist and the article number. A source that "
              "could not be read is absent from this list rather than cited from "
              "memory.", "ok")]

    b.append(sec("Source register", "",
                 table(f"Fetched {FETCHED}",
                       [("ID", "id"), ("Publisher", ""), ("Juris.", ""),
                        ("Document", ""), ("Type", ""), ("Official", ""),
                        ("Link", ""), ("What was read", "")],
                       [[e(s["id"]), e(s["publisher"]),
                         f'<span class="m5f19-b info">{e(s["jurisdiction"])}</span>',
                         e(s["title"]), e(s["doc_type"]),
                         '<span class="m5f19-b ok">yes</span>'
                         if s["official"] == "yes" else e(s["official"]),
                         src(s["url"]),
                         f'<span style="color:var(--muted)">{e(s["verbatim_notes"])}</span>']
                        for s in ss]), sid="register"))

    items = []
    for f in ff:
        st = ('<span class="m5f19-b ok">verified</span>'
              if f["status"] == "verified"
              else '<span class="m5f19-b warn">unverified</span>')
        s = d["sources_by_id"].get(f["source_id"], {})
        items.append(
            f'<details class="m5f19-d" id="{e(f["id"])}">'
            f'<summary><span class="m5f19-fid">{e(f["id"])}</span> '
            f'<span>{e(f["topic"])}</span> {st}</summary>'
            f'<div class="m5f19-dbody">'
            f'<p class="m5f19-fid" style="margin:12px 0 6px">'
            f'{e(f["instrument"])} &#183; {e(f["article"])} &#183; '
            f'source {e(f["source_id"])}</p>'
            f'<div class="m5f19-q"><b>verbatim</b><br>{e(f["verbatim_original"])}</div>'
            f'<p style="margin:8px 0 0;color:var(--muted);font-size:14px">'
            f'{e(f["english_gist"])}</p>'
            f'<p style="margin:10px 0 0">{src(s.get("url", ""))}</p>'
            f'</div></details>')
    b.append(sec(f"Verbatim passages relied on \u2014 {len(ff)}", "",
                 "".join(items), sid="facts"))

    b.append(sec("Sources deliberately NOT cited", "",
                 note("This edition cites nothing it did not read today. Where an "
                      "earlier layer of the repository relies on a source not in the "
                      "register above \u2014 including secondary commercial "
                      "commentary, bank marketing pages, and the U.S.\u2013China "
                      "treaty text \u2014 the corresponding cell in this edition is "
                      "blank and flagged rather than carried forward. Two URLs were "
                      "also tested and rejected during this session: an IRS FBAR "
                      "reference path returned HTTP 404 and was discarded in favour "
                      "of the FBAR guidance page at S15.", "warn")))
    return page(PAGES[8][0],
                "Official source register and verbatim texts \u2014 m5f19",
                f"Sources \u00b7 all fetched {FETCHED}",
                f"{len(ss)} official documents and the {len(ff)} verbatim passages "
                "relied on.",
                "Every source fetched and read today, with the exact text quoted in "
                "the original language.",
                "".join(b))


# ==========================================================================
def main(check_only: bool = False) -> int:
    """Build every page. With --check, rebuild in memory and fail if any page on
    disk differs, which is how CI detects a stale committed page."""
    d = {
        "sources": rows("m5f19_sources.csv"),
        "facts": rows("m5f19_facts.csv"),
        "classification": rows("m5f19_classification.csv"),
        "methods": rows("m5f19_methods.csv"),
        "steps": rows("m5f19_steps.csv"),
        "tax": rows("m5f19_tax.csv"),
        "ladder": rows("m5f19_ladder.csv"),
        "reconciliation": rows("m5f19_reconciliation.csv"),
        "flags": rows("m5f19_flags.csv"),
        "board": rows("m5f19_board.csv"),
    }
    d["facts_by_id"] = {f["id"]: f for f in d["facts"]}
    d["sources_by_id"] = {s["id"]: s for s in d["sources"]}

    builders = [build_dashboard, build_classification, build_costs, build_methods,
                build_steps, build_tax, build_reconciliation, build_flagged,
                build_sources]
    stale = []
    for (fname, _), fn in zip(PAGES, builders):
        out = os.path.join(ROOT, fname)
        rendered = fn(d)
        if check_only:
            if not os.path.exists(out):
                stale.append(f"{fname} (missing)")
            elif read(out) != rendered:
                stale.append(fname)
            else:
                print(f"  up to date {fname}")
        else:
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(rendered)
            print(f"  wrote {fname} ({os.path.getsize(out):,} bytes)")

    if check_only:
        if stale:
            print(f"STALE: {len(stale)} page(s) differ from a fresh build: "
                  f"{', '.join(stale)}")
            print("run: python3 scripts/build_m5f19_site.py")
            return 1
        print(f"all {len(builders)} pages match a fresh build")
        return 0
    print(f"built {len(builders)} pages")
    return 0


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


if __name__ == "__main__":
    sys.exit(main(check_only="--check" in sys.argv[1:]))
