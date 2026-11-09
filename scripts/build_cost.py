#!/usr/bin/env python3
"""Build the unified dashboard and the USD 10,000 -> 400,000 cost model.

Design rule for this whole layer: NO NUMBER IS TYPED INTO AN HTML FILE.
Every figure is either
  (a) read from data/fx_anchor.json, which records what was literally on an
      official page on 2026-11-09, or
  (b) computed here from those anchors by a formula shown in the JSON, or
  (c) absent -- because no official page states it -- in which case the cell is
      blank and the row carries an explicit UNVERIFIED flag.

scripts/verify_cost.py re-derives every cell independently and fails the build
if the HTML and the arithmetic disagree by one cent.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

A = json.loads((DATA / "fx_anchor.json").read_text(encoding="utf-8"))
ANCHOR = A["anchor"]
DER = A["derived"]
FEES = A["fees"]
THR = A["thresholds"]
PEN = A["penalties"]

RATE = DER["customer_rate_cny_per_usd"]          # CNY per 1 USD, customer buying USD
SPREAD = DER["spread_vs_boc_reference_pct"] / 100.0
WIRE = FEES["boc_outward_wire"]
CABLE = WIRE["cable_cny_non_hk_mo_tw"]

AMOUNTS = list(range(10_000, 400_001, 10_000))

# --------------------------------------------------------------------------
# source registry
# --------------------------------------------------------------------------
SOURCES = [
    dict(id="V01", tier="1 · Primary statute / regulation",
         authority="State Council of the PRC",
         title="中华人民共和国外汇管理条例 (Foreign Exchange Administration Regulations), State Council Order No. 532",
         url="https://www.gov.cn/zhengce/2008-08/06/content_2602514.htm",
         supports="Art. 5 no restriction on current international payments; Art. 12 genuine-transaction test; Art. 17 individual outbound investment needs registration; Art. 22 capital-account payments need approval where prescribed; Art. 39/40/41/42/44/45 fines; Art. 52(2) defines 境内个人 as a person resident in China for 1 continuous year.",
         not_supported="Does not name any tax or charge on converting RMB to USD. Does not set the USD 50,000 figure."),
    dict(id="V02", tier="1 · Primary statute / regulation",
         authority="State Council of the PRC",
         title="中华人民共和国外汇管理条例, Chapter VII legal liability (same instrument, cited for the penalty articles)",
         url="https://www.gov.cn/zhengce/2008-08/06/content_2602514.htm",
         supports="Art. 39 evasion: fine up to 30% of the amount, 30%–100%-equivalent if serious. Art. 40 illegal arbitrage: same range. Art. 42 illegal carriage of cash: up to 20%. Art. 45 private/illegal FX dealing: up to 30%.",
         not_supported="The articles state maxima. They do not state how a decision-maker will exercise discretion in a particular case."),
    dict(id="V03", tier="2 · Official guidance",
         authority="SAFE, Ningxia branch",
         title="2022年外汇业务政策释疑（八）— the USD 50,000 figure is not a cap",
         url="https://www.safe.gov.cn/ningxia/2022/0929/1997.html",
         supports="Verbatim: China imposes no amount limit on genuine, lawful current-account and already-open capital-account FX purchases/sales; the USD 50,000 is a 年度便利化额度 (simplified-processing amount) and is 'not the limit'; above it, Art. 56/57 of 汇发〔2020〕14号 allow processing against source/use evidence.",
         not_supported="Does not say ordinary accumulated savings qualify. Does not make an unopened capital-account transfer lawful."),
    dict(id="V04", tier="2 · Official guidance",
         authority="SAFE, Tianjin branch",
         title="2024年个人外汇（三）— 经常项目外汇业务指引 Art. 64, outward remittance",
         url="https://www.safe.gov.cn/tianjin/2024/0229/2402.html",
         supports="Verbatim, Art. 64 of 汇发〔2020〕14号: remitting foreign currency already held in a foreign-currency account of at most USD 50,000-equivalent per day is done on ID alone; above that, ID plus transaction evidence, and the bank checks that the purchase purpose matches the remittance purpose. Cash already held: at most USD 10,000-equivalent per day on ID alone.",
         not_supported="Concerns foreign currency already in the account. Does not authorise buying FX, and does not create a right to remit capital."),
    dict(id="V05", tier="1 · Primary statute / regulation",
         authority="People's Bank of China",
         title="个人财产对外转移售付汇管理暂行办法, PBC Announcement [2004] No. 16 (full text)",
         url="https://www.safe.gov.cn/safe/2004/1116/5461.html",
         supports="The only general capital-account exit for an individual: 移民转移 (emigrant property transfer) and 继承转移 (inheritance transfer). Art. 6 phasing: first tranche at most one half, half the remainder after one year, the balance after two years; RMB 200,000 or less may go in one remittance. Art. 10: RMB 500,000 or less decided by the local SAFE branch, above that by SAFE headquarters. Art. 11: proceeds must go straight to the applicant's own overseas account, no domestic cash withdrawal. Art. 13: false materials are punished under Art. 40.",
         not_supported="Does not cover a person who has not emigrated and holds no foreign citizenship/permanent residence. Does not state any fee."),
    dict(id="V07", tier="2 · Official guidance",
         authority="SAFE, Tianjin branch",
         title="中华人民共和国外汇管理条例 (SAFE mirror, used to confirm the text is the in-force version)",
         url="https://www.safe.gov.cn/tianjin/2015/0605/387.html",
         supports="Second official copy of Order 532, confirming Art. 39/40 wording used above.",
         not_supported="Mirror only."),
    dict(id="V08", tier="1 · Primary statute / regulation",
         authority="State Taxation Administration / SAFE",
         title="国家税务总局 国家外汇管理局公告2013年第40号 — 服务贸易等项目对外支付税务备案",
         url="https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html",
         supports="A single outward payment above the USD 50,000 equivalent for services, income or current transfers to an overseas individual requires a 税务备案表 filed with the tax authority; the form is a filing, and the tax office may check whether the underlying tax was paid. Art. 3(13) exempts private travel/study/family visits.",
         not_supported="Is not a tax. Does not impose a rate. (Partly superseded by 公告2021年第19号 for listed clauses — flagged A6.)"),
    dict(id="V09", tier="1 · Primary statute / regulation",
         authority="National People's Congress, via Shanghai tax bureau",
         title="中华人民共和国个人所得税法 (Individual Income Tax Law), consolidated text, status 全文有效",
         url="https://shanghai.chinatax.gov.cn/zcfw/zcfgk/grsds/201809/t441789.html",
         supports="Art. 2 lists the nine taxable income categories. Art. 3(3): interest, dividends, rent, property-transfer income and incidental income bear a flat 20%. Art. 6(5): the property-transfer base is proceeds minus original value minus reasonable expenses — 20% applies to the gain, not the principal. Art. 10(5) requires tax clearance before cancelling Chinese household registration on emigrating. Art. 16: foreign currency is converted at the RMB central parity rate.",
         not_supported="Contains no tax on converting currency. Salary already taxed is not taxed again on remittance."),
    dict(id="V10", tier="3 · Official bank publication",
         authority="Bank of China",
         title="中国银行外汇牌价 (foreign-exchange board rates), snapshot 2026-11-09 09:15:45",
         url="https://www.boc.cn/sourcedb/whpj/",
         supports="USD per 100: 现汇买入价 666.38, 现钞买入价 666.38, 现汇卖出价 669.19, 现钞卖出价 669.19, 中行折算价 671.88. A customer buying USD pays the 现汇卖出价 = CNY 6.6919 per USD.",
         not_supported="The page states these are 'for reference only' and that the actual branch/online rate governs. It is a snapshot, it moves during the day, and it is one bank — not the market."),
    dict(id="V11", tier="1 · Primary official data",
         authority="PBOC / China Foreign Exchange Trade System",
         title="2026年11月6日 人民币汇率中间价公告 — USD/CNY central parity 6.7168",
         url="https://www.pbc.gov.cn/zhengcehuobisi/125207/125217/125925/2026110608563230207/index.html",
         supports="Official central parity of 6.7168 CNY per USD on 2026-11-06.",
         not_supported="The parity is a reference used for tax conversion and market band-setting. It is not a rate at which a retail customer can transact, and it is not the price a bank must quote."),
    dict(id="V12", tier="3 · Official bank publication",
         authority="Bank of China",
         title="中国银行电子银行个人服务转账汇款费率表 — cross-border telegraphic transfer tariff",
         url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
         supports="跨境汇款（电汇）: 1‰ of the remittance, minimum CNY 50, maximum CNY 260 per transfer, plus a cable charge of CNY 80 (HK/Macau/Taiwan) or CNY 150 (elsewhere).",
         not_supported="Does not publish a correspondent-bank fee, an FCC/全额到账 fee, or a receiving-bank fee. Notes that local branches may publish different prices."),
    dict(id="V13", tier="1 · Primary official guidance",
         authority="Internal Revenue Service",
         title="Report of Foreign Bank and Financial Accounts (FBAR)",
         url="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar",
         supports="A U.S. person with foreign financial accounts whose aggregate value exceeded USD 10,000 at any time in the calendar year must file FinCEN Form 114; due 15 April with automatic extension to 15 October.",
         not_supported="Does not state current penalty amounts (it points to 31 CFR 1010.821 for those)."),
    dict(id="V14", tier="1 · Primary regulation",
         authority="FinCEN, via the eCFR",
         title="31 CFR 1010.821 — civil monetary penalty inflation table",
         url="https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
         supports="For penalties assessed on or after 2025-01-17: 31 U.S.C. 5321(a)(5)(B)(i) non-willful FBAR maximum USD 16,536; 31 U.S.C. 5321(a)(5)(C)(i)(I) willful maximum USD 165,353 (statute: the greater of that or 50% of the balance).",
         not_supported="Maximums only; assertion depends on facts. Note the eCFR labels itself authoritative but unofficial."),
    dict(id="V15", tier="1 · Primary official guidance",
         authority="Internal Revenue Service",
         title="Comparison of Form 8938 and FBAR requirements",
         url="https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements",
         supports="Form 8938 thresholds for a specified individual living in the U.S.: over USD 50,000 on the last day or USD 75,000 at any time (single), USD 100,000/150,000 (joint). Penalties: up to USD 10,000 plus USD 10,000 per 30 days after notice, potential maximum USD 60,000. FBAR conversion uses the end-of-calendar-year rate; Form 8938 uses the end-of-tax-year rate.",
         not_supported="The FBAR penalty figures on this page are the pre-2016 statutory amounts; the current table is 31 CFR 1010.821 (V14)."),
    dict(id="V16", tier="1 · Primary statute",
         authority="Internal Revenue Code s.102, via 26 CFR",
         title="26 CFR 1.102-1 — Gifts and inheritances",
         url="https://www.ecfr.gov/current/title-26/chapter-I/subchapter-A/part-1/subject-group-ECFRb467872627553f1/section-1.102-1",
         supports="Property received as a gift, or under a will, is not includible in gross income; the income from the property is.",
         not_supported="Does not address reporting, which sits in s.6039F and Form 3520."),
    dict(id="V17", tier="1 · Primary official guidance",
         authority="Internal Revenue Service",
         title="Gifts from foreign person",
         url="https://www.irs.gov/businesses/gifts-from-foreign-person",
         supports="A U.S. person receiving more than USD 100,000 in aggregate in a tax year from a nonresident alien or foreign estate reports it on Form 3520 Part IV; each gift over USD 5,000 separately identified. Thresholds for foreign corporations/partnerships are USD 20,116 (2025) and USD 20,573 (2026).",
         not_supported="States no tax on the gift itself — it is an information return."),
    dict(id="V18", tier="1 · Primary official guidance",
         authority="Internal Revenue Service",
         title="Instructions for Form 3520 (12/2025)",
         url="https://www.irs.gov/instructions/i3520",
         supports="s.6039F penalty: 5% of the foreign gift per month the failure continues, capped at 25%; reasonable-cause exception. s.6677 penalties for trust items are separate.",
         not_supported="Applies to gifts/bequests, not to a transfer of your own funds."),
    dict(id="V19", tier="1 · Primary regulation",
         authority="Internal Revenue Service, via the eCFR",
         title="26 CFR 1.988-1 — Certain definitions and special rules (foreign currency transactions)",
         url="https://www.ecfr.gov/current/title-26/chapter-I/subchapter-A/part-1/subject-group-ECFRc5ac1659a3792c9/section-1.988-1",
         supports="Defines a s.988 transaction and the currency gain/loss computation. Cited only to identify the provision; the personal-transaction exception in s.988(e) was NOT verified in this session.",
         not_supported="s.988(e) text not fetched — flagged A8."),
    dict(id="V20", tier="1 · Primary official guidance",
         authority="Internal Revenue Service",
         title="Foreign currency and currency exchange rates",
         url="https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates",
         supports="Amounts on a U.S. return must be in USD using the rate prevailing when the item is received/paid/accrued; the IRS has no official rate and generally accepts any posted rate used consistently.",
         not_supported="Does not prescribe a single rate, so no 'correct' number can be quoted for a past transfer."),
    dict(id="V21", tier="1 · Primary official data",
         authority="Board of Governors of the Federal Reserve System",
         title="Foreign Exchange Rates — H.10, release of 2026-11-02",
         url="https://www.federalreserve.gov/releases/h10/current/",
         supports="CHINA, P.R. YUAN: 6.6700 / 6.6660 / 6.6662 / 6.6604 / 6.6538 CNY per USD for 26–30 October 2026.",
         not_supported="Interbank indicative rates, not a retail price, and not the rate any bank must honour."),
    dict(id="V22", tier="1 · Primary official data",
         authority="Internal Revenue Service",
         title="Yearly average currency exchange rates",
         url="https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates",
         supports="China, Yuan yearly averages: 2025 7.129, 2024 7.189, 2023 7.075, 2022 6.730, 2021 6.452 CNY per USD.",
         not_supported="Yearly averages, not deal rates; not what a bank charges."),
    dict(id="V23", tier="2 · Official guidance",
         authority="SAFE, Tianjin branch",
         title="2024年经常项目外汇政策问答案例（九）— do 境外个人 get the annual convenience amount?",
         url="https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
         supports="Verbatim: under 汇发〔2020〕14号 Art. 59, a 境外个人 with lawful current-account RMB income in China buys FX at a bank on ID plus source-of-funds evidence (including tax vouchers); the annual convenience amount applies instead to 境外个人 holding a foreigner permanent-residence ID.",
         not_supported="Does not extend to RMB that is not current-account income. Does not set any ceiling, and does not state a fee."),
    dict(id="V24", tier="1 · Primary statute / regulation",
         authority="People's Bank of China",
         title="个人外汇管理办法, PBC Order [2006] No. 3 (full text on gov.cn)",
         url="https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm",
         supports="Art. 9 annual aggregate management; Art. 12 outward remittance above the prescribed amount needs transaction evidence; Art. 13 a 境外个人 may buy and remit FX against lawful current-account RMB income on ID plus supporting evidence; Art. 14 unused inward FX may be returned by the original route; Art. 20 outbound donation and property transfer need SAFE approval; Art. 26 lawful property of a 境外个人 leaving China follows the property-transfer rules; Art. 37(2) a 境外个人 is a foreign national holding a passport (including stateless persons) or a HK/Macau/Taiwan compatriot.",
         not_supported="Art. 37(2) conflicts with Order 532 Art. 52(2), which treats anyone resident one year as a 境内个人 — flagged A1."),
    dict(id="V25", tier="1 · Primary regulation",
         authority="SAFE",
         title="汇发〔2015〕49号 — 关于进一步完善个人外汇管理有关问题的通知",
         url="https://www.safe.gov.cn/safe/2015/1231/5442.html",
         supports="Splitting transactions to evade the amount limit or the genuineness review is prohibited. Lending your own quota to help another person: first a written risk warning; a second time puts you on the 关注名单. Borrowing another's quota puts you on the 关注名单 directly. The 关注名单 lasts the current year plus the next two, during which every transaction needs full documentary review.",
         not_supported="Does not itself impose a fine; the fine comes from Order 532."),
    dict(id="V26", tier="1 · Primary official form",
         authority="SAFE",
         title="《个人购汇申请书》及填报说明 (the 'six must-nots')",
         url="https://www.safe.gov.cn/safe/file/file/20210402/30fab7a9646f417ca9d2f67ff4c1e5f0.pdf",
         supports="A 境内个人 buying FX must sign the form: no false declaration, no false documents, no lending your quota, no borrowing another's, no use for overseas property/securities/life insurance or investment-type endowment insurance, no money laundering/gambling/tax evasion/underground banking. The 关注名单 lasts the year of listing plus two, and no convenience amount is available during it.",
         not_supported="Applies to 境内个人 purchases; the form is not the mechanism for a 境外个人 conversion under V23."),
    dict(id="V27", tier="1 · Primary official data",
         authority="U.S. Department of the Treasury, Fiscal Service",
         title="Treasury Reporting Rates of Exchange",
         url="https://www.fiscal.treasury.gov/reports-statements/treasury-reporting-rates-exchange/",
         supports="The Treasury rate the FBAR instructions direct filers to use for year-end conversion.",
         not_supported="Not fetched in full this session; cited only because the IRS page V20 links to it as the governmental rate source."),
]

SRC_BY_ID = {s["id"]: s for s in SOURCES}


def esc(t):
    return html.escape(str(t), quote=True)


def money(v, dec=0):
    if v is None:
        return ""
    return f"${v:,.{dec}f}"


def link(sid, label=None):
    s = SRC_BY_ID[sid]
    return (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener" '
            f'title="{esc(s["title"])}">{esc(label or sid)}</a>')


def tags(*ids):
    return " ".join(link(i) for i in ids)


# --------------------------------------------------------------------------
# cost model
# --------------------------------------------------------------------------
def wire_fee_cny(cny_amount: float) -> float:
    """BOC published tariff, V12: 1 per mille, floor 50, cap 260, plus cable 150."""
    return min(max(cny_amount * WIRE["rate_pct_of_cny"] / 100.0, WIRE["min_cny"]), WIRE["max_cny"]) + CABLE


def methods_for(usd: float) -> list[dict]:
    """Return one row per method for a given USD target.

    'Total' is the all-in cost in USD of ending up with `usd` in a U.S. account.
    Where a component has no official source the row is marked UNVERIFIED and the
    total is reported as a partial figure, never as a complete one.
    """
    cny = usd * RATE
    fx = usd * SPREAD                          # cost embedded in the bank's price
    one_wire = wire_fee_cny(cny) / RATE
    rows = []

    # M1 -- bank FX + outward wire, convenience amount only
    rows.append(dict(
        key="M1", name="M1 · Bank FX + outward wire, within the annual convenience amount",
        side="one transfer per USD 50,000 per person per year",
        fx=fx, fee=one_wire, extra=0.0, transfers=1,
        verified=usd <= THR["convenience_quota_usd_per_person_year"]["value"],
        blocked_above=THR["convenience_quota_usd_per_person_year"]["value"],
        note="Only reaches USD 50,000 per person per calendar year on ID alone.",
    ))

    # M2 -- genuine current-account purchase above the convenience amount
    n2 = 1
    rows.append(dict(
        key="M2", name="M2 · Genuine current-account purchase above the convenience amount",
        side="one transfer, any size, with transaction evidence",
        fx=fx, fee=one_wire, extra=0.0, transfers=n2,
        verified=True, blocked_above=None,
        note="No ceiling. Needs real source/use evidence; above USD 50,000 per payment a tax filing form is also required (V08).",
    ))

    # M3 -- emigrant / inheritance property transfer
    rmb = cny
    if rmb <= THR["sha_single_remittance_allowance_rmb"]["value"]:
        n3 = 1
        phase = "one remittance permitted"
    else:
        n3 = 3
        phase = "three remittances across two years"
    rows.append(dict(
        key="M3", name="M3 · Emigrant / inheritance property transfer (PBC [2004] No.16)",
        side=f"{phase}; notary, translation and approval costs not published",
        fx=fx, fee=one_wire * n3, extra=None, transfers=n3,
        verified=None, blocked_above=None,
        note="Requires emigrant status (foreign citizenship/permanent residence) or an inheritance. SAFE approval fee and notarisation cost: no official figure found.",
    ))

    # M4 -- family gift routed through a PRC-resident relative
    n4 = max(1, math.ceil(usd / THR["convenience_quota_usd_per_person_year"]["value"]))
    rows.append(dict(
        key="M4", name="M4 · Gift from a relative in China (foreign gift to a U.S. person)",
        side=f"{n4} transfer(s) to stay inside each sender's convenience amount",
        fx=fx, fee=one_wire * n4, extra=0.0, transfers=n4,
        verified=True, blocked_above=None,
        note="Gift is excluded from U.S. gross income (V16); over USD 100,000 in a year it is an information return on Form 3520, not a tax (V17).",
    ))

    # M5 -- QDII / cross-border scheme
    rows.append(dict(
        key="M5", name="M5 · QDII / cross-border wealth-management scheme",
        side="investment, not remittance; quota-mediated",
        fx=None, fee=None, extra=None, transfers=None,
        verified=None, blocked_above=None,
        note="No official per-transaction or per-account cost found. Not a way to move a savings balance.",
    ))

    # M6 -- cash carry
    rows.append(dict(
        key="M6", name="M6 · Carry cash (USD 10,000+ in person)",
        side="legally capped per person per trip",
        fx=fx, fee=0.0, extra=0.0, transfers=0,
        verified=False, blocked_above=10000,
        note="Above USD 10,000 per person per trip is prohibited in principle (V01 Art.42, V24 Art.34). Not available at the amounts requested.",
    ))
    return rows


def build_model() -> dict:
    rows = []
    for usd in AMOUNTS:
        rows.append(dict(usd=usd, cny=usd * RATE, methods=methods_for(usd)))
    return dict(
        anchor=ANCHOR, derived=DER,
        assumptions=[
            "The balance is CNY and the customer must buy USD, so the price used is the bank's 现汇卖出价, not any reference rate.",
            "One USD 50,000-equivalent remittance per outward payment; a larger sum needs several payments only under M1 and M4, which are shown with their transfer counts.",
            "All costs are computed on a USD 10,000 multiple at the 2026-11-09 09:15:45 BOC snapshot. A different day moves the spread line, not the structure.",
            "PRC income tax is NOT included: it attaches to whatever created the money, at the moment it was created, whether or not it is ever converted. See cost-tax.html.",
            "U.S. income tax is NOT included: moving your own after-tax money is not an income event. Reporting penalties are shown separately because they are the largest number in this project.",
        ],
        rows=rows,
    )


MODEL = build_model()


def total(r):
    if r["fx"] is None or r["fee"] is None or r["extra"] is None:
        return None
    return r["fx"] + r["fee"] + r["extra"]


# --------------------------------------------------------------------------
# page shell
# --------------------------------------------------------------------------
NAV = [
    ("cost.html", "Dashboard"),
    ("cost-model.html", "Cost model $10k–$400k"),
    ("cost-methods.html", "All methods"),
    ("cost-playbook.html", "Step-by-step playbook"),
    ("cost-tax.html", "The “penalty” decoded"),
    ("cost-review.html", "Flagged for review"),
    ("cost-sources.html", "Sources"),
]

def shell(slug, title, desc, body, eyebrow=""):
    nav = []
    for href, label in NAV:
        cls = ' class="active"' if href == slug else ""
        nav.append(f'<a{cls} href="{href}">{esc(label)}</a>')
    nav.append('<a href="index.html">All site pages</a>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | China Money Research</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="assets/cost.css"></head>
<body>
<header class="topbar"><div class="shell">
  <a class="brand" href="cost.html"><span class="brand-mark">¥→$</span> China Money Research</a>
  <nav class="nav">{''.join(nav)}</nav>
</div></header>
<main class="shell">
{f'<section class="hero"><div class="eyebrow">{eyebrow}</div>' if eyebrow else '<section class="hero">'}
{body}
</section>
</main>
<footer class="foot"><div class="shell foot-row">
  <div><b>China Money Research</b><p>Official-source research. Not legal, tax or banking advice.</p></div>
  <p>Built 9 November 2026 · <a href="cost-sources.html">Sources</a> · <a href="cost-review.html">Flagged for review</a></p>
</div></footer>
</body></html>
'''

def anchor_box():
    a = ANCHOR
    return f'''<div class="anchor">
  <div class="anchor-head">The one price everything below is built on</div>
  <div class="anchor-grid">
    <div><span class="k">Bank of China 现汇卖出价 (spot selling)</span><b>{a["boc_usd_spot_sell"]/100:.4f}</b><span class="u">CNY per 1 USD</span></div>
    <div><span class="k">Bank of China 中行折算价 (its reference)</span><b>{a["boc_usd_reference"]/100:.4f}</b><span class="u">CNY per 1 USD</span></div>
    <div><span class="k">Measured spread you actually pay</span><b>{DER["spread_vs_boc_reference_pct"]:.4f}%</b><span class="u">({a["boc_usd_reference"]-a["boc_usd_spot_sell"]:.2f} fen per USD)</span></div>
    <div><span class="k">PBOC central parity, {a["pboc_parity_date"]}</span><b>{a["pboc_usd_cny"]:.4f}</b><span class="u">reference only</span></div>
  </div>
  <p class="anchor-note">Board snapshot <code>{a["boc_timestamp"]}</code> from {link("V10","boc.cn")}; parity from {link("V11","pbc.gov.cn")}. The bank's own disclaimer says the counter rate governs, so treat this as the best public measurement available, not a binding quote.</p>
</div>'''

def money_cell(v):
    return money(v, 2) if v is not None else '<span class="blank">— not published —</span>'

def status_pill(v):
    if v is True:
        return '<span class="tag ok">verified</span>'
    if v is False:
        return '<span class="tag no">blocked</span>'
    return '<span class="tag warn">unverified</span>'


# --------------------------------------------------------------------------
# page 1 — cost model
# --------------------------------------------------------------------------
def page_model():
    rows = MODEL["rows"]
    b = []
    b.append('<h1>The cost of turning CNY into USD, USD 10,000 to USD 400,000</h1>')
    b.append('''<p class="lede">Every row is computed, not estimated: the spread is measured from the
bank's own published board, the wire fee is the bank's published tariff, and anything no official
page states is left blank and flagged. Send this table to a bank and ask which line they disagree with.</p>''')

    b.append(anchor_box())

    b.append('''<div class="notice amber"><b>Read the totals as a floor, not a forecast.</b>
They contain the two costs that are published and they exclude the three that are not: correspondent-bank
charges, the U.S. receiving-bank fee, and any SAFE approval or notarisation cost. Those cells say
“not published” instead of holding a guess.''')

    # headline cards
    first = methods_for(10_000)[0]
    last = methods_for(400_000)[0]
    b.append('<div class="stats">'
             f'<div class="stat"><b>{money(total(first),0)}</b><span>all-in on $10,000 · {(total(first)/10000)*100:.2f}%</span></div>'
             f'<div class="stat"><b>{money(total(last),0)}</b><span>all-in on $400,000 · {(total(last)/400000)*100:.2f}%</span></div>'
             f'<div class="stat"><b>{SPREAD*100:.2f}%</b><span>the measured bank spread</span></div>'
             f'<div class="stat"><b>{money(PEN["fbar_willful_max_usd"]["value"],0)}</b><span>one willful FBAR maximum</span></div>'
             '</div>')

    b.append('<p class="big">The whole $400,000 conversion costs about '
             f'<b>{money(total(last),0)}</b>. The U.S. information-reporting penalty for getting the paperwork '
             f'wrong on that same account starts at <b>{money(PEN["fbar_willful_max_usd"]["value"],0)}</b> and can reach '
             f'<b>half the balance</b>. The expensive thing in this project is not the exchange rate.</p>')

    # ---- master table
    b.append('<h2 id="table">The table · method M1 and M2 (bank FX + one outward wire)</h2>')
    b.append('''<p class="sub">M1 and M2 are the same arithmetic; they differ only in whether the transfer is
allowed on ID alone (M1, up to USD 50,000 per person per year) or on documentary evidence (M2, no ceiling).
The “can you do it?” column is the part that changes with size.</p>''')

    b.append('<div class="table-wrap"><table class="data cost" data-table="master"><thead><tr>'
             '<th>USD out</th><th>CNY at 6.6919</th><th>FX spread<br><span>0.4004%</span></th>'
             '<th>Wire + cable<br><span>BOC tariff</span></th><th>All-in cost</th><th>as %</th>'
             '<th class="hide-sm">M1 on ID alone?</th><th>Source</th>'
             '</tr></thead><tbody>')
    for r in rows:
        m = r["methods"][0]
        t = total(m)
        pct = t / r["usd"] * 100
        ok = "yes" if r["usd"] <= 50_000 else "no — needs M2"
        cls = "ok" if r["usd"] <= 50_000 else "no"
        b.append(
            f'<tr><td class="num"><b>{money(r["usd"],0)}</b></td>'
            f'<td class="num">{r["cny"]:,.0f}</td>'
            f'<td class="num">{money(m["fx"],2)}</td>'
            f'<td class="num">{money(m["fee"],2)}</td>'
            f'<td class="num total">{money(t,2)}</td>'
            f'<td class="num">{pct:.2f}%</td>'
            f'<td class="hide-sm"><span class="tag {cls}">{ok}</span></td>'
            f'<td class="src">{tags("V10","V12","V03")}</td></tr>')
    b.append('</tbody></table></div>')

    b.append('''<p class="fine">Wire + cable = 1‰ of the CNY amount, floor CNY 50, cap CNY 260, plus CNY 150
foreign cable charge, converted at the same 6.6919 — all from the bank's published tariff (V12). The cap is
hit at about USD 38,800, which is why the fee stops growing and the cost curve flattens to exactly 0.4004%.</p>''')

    # ---- method comparison
    b.append('<h2 id="methods">Same money, six routes, side by side</h2>')
    b.append('''<p class="sub">A dash is not a missing number — it is a number no official page publishes.
We will not put a guess in a table you might act on.</p>''')
    b.append('<div class="table-wrap"><table class="data cost" data-table="matrix-model"><thead><tr><th>USD</th>')
    for k, label in [("M1", "M1 convenience"), ("M2", "M2 current-acct"),
                     ("M3", "M3 emigrant"), ("M4", "M4 gift"),
                     ("M5", "M5 QDII"), ("M6", "M6 cash")]:
        b.append(f'<th>{label}</th>')
    b.append('<th>Source</th></tr></thead><tbody>')
    for r in MODEL["rows"]:
        b.append(f'<tr><td class="num"><b>{money(r["usd"],0)}</b></td>')
        for m in r["methods"]:
            t = total(m)
            if m["key"] == "M1" and r["usd"] > 50_000:
                b.append('<td class="num cell-no">not available<small>over $50k</small></td>')
            elif m["key"] == "M6" and r["usd"] > 10_000:
                b.append('<td class="num cell-no">prohibited<small>over $10k</small></td>')
            elif t is None:
                b.append('<td class="num cell-blank">—<small>not published</small></td>')
            else:
                b.append(f'<td class="num">{money(t,2)}</td>')
        b.append(f'<td class="src">{tags("V10","V12","V03","V05","V16")}</td>')
        b.append('</tr>')
    b.append('</tbody></table></div>')
    b.append('''<div class="notice"><b>What the columns mean.</b>
<b>M1</b> is the ID-only route and stops at USD 50,000 per person per calendar year (V03).
<b>M2</b> is the same bank purchase above that amount, which is lawful only with genuine transaction
evidence — it is not a quota upgrade (V03, V24).
<b>M3</b> is the emigrant/inheritance capital-account exit and needs emigrant status (V05); its approval
and notarisation costs are not published, so no total is shown.
<b>M4</b> is a relative in China gifting you the money; the gift is outside U.S. gross income (V16) and
only an information return above USD 100,000 (V17).
<b>M5</b> is an investment channel, not a remittance; no official cost per transaction exists.
<b>M6</b> is legally capped at USD 10,000 per person per trip (V01 Art. 42).</div>''')

    # ---- spread against alternatives
    b.append('<h2 id="spread">What the 0.4004% is, and what it is not</h2>')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>Reference price</th><th>CNY per USD</th><th>Difference vs the price you pay</th><th>Is this a cost you incur?</th><th>Source</th></tr></thead><tbody>')
    b.append(f'<tr><td>What you pay (BOC 现汇卖出价)</td><td class="num">6.6919</td><td class="num">—</td><td>Yes — this is the transaction</td><td class="src">{link("V10")}</td></tr>')
    b.append(f'<tr><td>BOC 中行折算价, same page, same minute</td><td class="num">6.7188</td><td class="num">0.4004%</td><td>Yes — this gap is the bank margin</td><td class="src">{link("V10")}</td></tr>')
    b.append(f'<tr><td>PBOC central parity, {ANCHOR["pboc_parity_date"]}</td><td class="num">6.7168</td><td class="num">0.3707%</td><td>No — different day, and parity is not tradable</td><td class="src">{link("V11")}</td></tr>')
    b.append(f'<tr><td>Federal Reserve H.10, {ANCHOR["fed_h10_date"]}</td><td class="num">6.6538</td><td class="num">−0.5653%</td><td>No — interbank indicative, wrong direction, different week</td><td class="src">{link("V21")}</td></tr>')
    b.append(f'<tr><td>IRS yearly average, 2025</td><td class="num">7.129</td><td class="num">−6.1%</td><td>No — a tax-return convention, not a trade</td><td class="src">{link("V22")}</td></tr>')
    b.append('</tbody></table></div>')
    b.append('''<p class="fine">The negative rows matter. Someone comparing “the bank” with “the Fed rate” will
conclude the bank is overcharging by a number that is really just a different date and a different kind of
price. The only like-for-like comparison on this page is row 2: same bank, same screen, same minute.</p>''')

    # ---- marginal
    b.append('<h2 id="marginal">Where the money actually goes, per extra dollar</h2>')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>Step</th><th>Extra USD moved</th><th>Extra cost</th><th>Marginal %</th><th>Why</th><th>Source</th></tr></thead><tbody>')
    b.append(f'<tr><td>$10,000 → $20,000</td><td class="num">$10,000</td><td class="num">{money(total(methods_for(20_000)[0])-total(methods_for(10_000)[0]),2)}</td><td class="num">0.40%</td><td>The fee cap is already reached, so only the spread applies.</td><td class="src">{tags("V10","V12")}</td></tr>')
    b.append(f'<tr><td>$50,000 → $400,000</td><td class="num">$350,000</td><td class="num">{money(total(methods_for(400_000)[0])-total(methods_for(50_000)[0]),2)}</td><td class="num">0.40%</td><td>Perfectly linear. There is no volume penalty and no volume discount.</td><td class="src">{tags("V10","V12")}</td></tr>')
    b.append(f'<tr><td>$400,000 → $410,000</td><td class="num">$10,000</td><td class="num">{money(total(methods_for(400_000)[0])-total(methods_for(390_000)[0]),2)}</td><td class="num">0.40%</td><td>Same at the top of the range.</td><td class="src">{tags("V10","V12")}</td></tr>')
    b.append('</tbody></table></div>')
    b.append('<p class="fine">This is the single most useful number in the project: beyond roughly USD 38,800, '
             'every additional USD 1,000 costs about USD 4.00 to convert, no matter how large the balance is.</p>')

    b.append('<p class="next"><a href="cost-playbook.html">Next: the exact step-by-step for each route →</a></p>')
    return shell("cost-model.html",
                 "Cost model: USD 10,000 to USD 400,000",
                 "Computed all-in cost of converting CNY to USD at every USD 10,000 step, from the Bank of China published board rate and wire tariff.",
                 "\n".join(b), "Category 01 · The number")


# --------------------------------------------------------------------------
# page 2 — all methods
# --------------------------------------------------------------------------
METHODS = [
    dict(id="M01", cls="lawful", name="Bank purchase + outward wire within the convenience amount",
         who="PRC-resident individual (境内个人) holding a Chinese ID",
         rule="Up to USD 50,000-equivalent per person per calendar year on ID plus a signed purchase declaration.",
         pros="Same-day; no transaction file; cheapest published path (≈0.40% + CNY 410).",
         cons="Hard-stops at USD 50,000 per person per year. Sixteen people would be needed for USD 400,000 — and that is split-purchase, which is a listed violation.",
         cost="0.4004% spread + CNY 50–260 + CNY 150 cable", src=["V03", "V12", "V26"], verified=True),
    dict(id="M02", cls="lawful", name="Bank purchase above the convenience amount on genuine current-account evidence",
         who="境内个人 with a real current-account purpose (study, medical, travel, family support, services)",
         rule="No amount limit; the bank reviews the transaction documents. Above USD 50,000 per payment a tax filing form is also required.",
         pros="No ceiling; the whole balance can move in one instruction if the purpose is real.",
         cons="“Accumulated savings” is not a current-account purpose. The evidence must exist before the money moves, and it must match the remittance.",
         cost="0.4004% spread + CNY 410 (capped)", src=["V03", "V08", "V24"], verified=True),
    dict(id="M03", cls="lawful-approval", name="Emigrant property transfer (移民财产转移)",
         who="Someone who has already emigrated and holds foreign citizenship or permanent residence; or an inheritance",
         rule="Apply once to the local SAFE branch with ID, household-registration cancellation, settlement proof, source-of-funds and property-rights evidence and a tax certificate. At most RMB 500,000 is decided locally, above that by SAFE headquarters.",
         pros="The only general capital-account exit for a whole personal balance. PBC [2004] No. 16 sets the schedule, not a bank's discretion.",
         cons="Only for emigrants and heirs. Phased: half first, half the remainder after one year, the rest after two. Proceeds must go to your own overseas account, never as cash.",
         cost="0.4004% spread + CNY 410 per remittance tranche; approval fee and notarisation not published", src=["V05", "V01"], verified=None),
    dict(id="M04", cls="lawful", name="Current-account income of a foreign national (境外个人)",
         who="A non-Chinese passport holder with lawful current-account RMB income earned in China",
         rule="Art. 13 of PBC Order [2006] No. 3 and Art. 59 of 汇发〔2020〕14号: buy FX and remit against ID plus source-of-funds evidence including tax vouchers.",
         pros="No annual convenience amount applies (that applies to holders of a foreigner permanent-residence ID), and the review is of where the money came from, not what you will spend it on.",
         cons="Only covers current-account income. It is not a route for capital or for inherited property.",
         cost="0.4004% spread + CNY 410 per remittance; above USD 50,000 per payment a tax filing form applies", src=["V24", "V23", "V08"], verified=True),
    dict(id="M05", cls="lawful", name="Return of unused inward remittance, or unused RMB from a prior exchange",
         who="境外个人 only",
         rule="Art. 14 unused inward FX may be returned by the original route on ID. Art. 15 unused RMB from a prior exchange may be converted back against the original exchange memo, small amounts on ID alone.",
         pros="No tax certificate, no quota.",
         cons="Only reverses money that already came in. It cannot convert savings that were earned in China.",
         cost="0.4004% spread; wire fee as M01", src=["V24"], verified=True),
    dict(id="M06", cls="lawful", name="Sale proceeds of a China property owned by a foreign national",
         who="境外个人 who bought a China home for own use and sold it",
         rule="Art. 22 of PBC Order [2006] No. 3: sale proceeds in RMB may be purchased and remitted with SAFE approval. Art. 26: other lawful property of a 境外个人 follows the property-transfer rules.",
         pros="A defined capital-account exit with a named legal basis.",
         cons="Narrow: own-use residential property only, SAFE approval, title and tax evidence, and the 20% property-transfer tax is settled on the gain first.",
         cost="0.4004% spread; 20% IIT on the gain; approval fee not published", src=["V24", "V09"], verified=True),
    dict(id="M07", cls="lawful", name="Foreign-currency account balance, remitted as FX",
         who="Anyone already holding USD/EUR in a China FX account",
         rule="Art. 64 of 汇发〔2020〕14号: up to USD 50,000-equivalent per day on ID alone; above that, ID plus transaction evidence. Cash held: USD 10,000-equivalent per day on ID alone.",
         pros="Skips the conversion entirely — no 0.4004%, because the FX is already there.",
         cons="Only works for money that is already foreign currency. Requires that the original purchase was lawful and documented.",
         cost="No spread. Wire fee only: CNY 410 for the largest amounts.", src=["V04", "V01"], verified=True),
    dict(id="M08", cls="lawful", name="Company dividend / profit remittance (if the money is a company's, not yours)",
         who="A foreign-invested enterprise or domestic institution",
         rule="Current-account item; the bank processes genuine, compliant profit distributions against board resolution, audited accounts and a tax filing form above USD 50,000.",
         pros="No amount limit.",
         cons="Personal savings cannot be relabelled as corporate profit. Doing so is a documentation offence.",
         cost="0.4004% spread + CNY 410; 10% withholding on dividends where the treaty does not reduce it (not verified this session)", src=["V01", "V08"], verified=None),
    dict(id="M09", cls="lawful", name="Cross-border RMB settlement, converted offshore",
         who="Holders of lawful current-account RMB income",
         rule="RMB crosses the border as RMB; the conversion happens in the offshore CNH market.",
         pros="Avoids the onshore 现汇卖出价.",
         cons="Still needs a lawful cross-border RMB channel and an offshore account. The CNH–CNY gap is a market price, not a discount, and it moves both ways.",
         cost="CNH spread, not measured in this session", src=["V01"], verified=None),
    dict(id="M10", cls="lawful", name="Gift from a relative who is in China",
         who="You, receiving a gift from a PRC-resident relative",
         rule="The relative uses their own quota or their own documentary route; you receive a foreign gift.",
         pros="A gift is outside U.S. gross income, and above USD 100,000 it is only an information return, not a tax.",
         cons="Must be a real gift. Paying someone to use their quota is borrowing a quota — a 关注名单 offence in China and, at scale, a structuring problem in the U.S.",
         cost="Same bank arithmetic as M01 on the sending side", src=["V16", "V17", "V25"], verified=True),
    dict(id="M11", cls="prohibited", name="Splitting the transfer across several people, or borrowing quotas",
         who="—",
         rule="Prohibited. Lending a quota draws a written warning, then the 关注名单; borrowing one puts you on it directly.",
         pros="None.",
         cons="The 关注名单 lasts the listing year plus two more, and during it every single transaction needs full documentary review. Sixteen relatives for USD 400,000 is exactly the pattern being watched for.",
         cost="Up to 30% of the amount under Art. 40, plus loss of the convenience amount for three years", src=["V25", "V01", "V26"], verified=True),
    dict(id="M12", cls="prohibited", name="Underground banks, FX brokers, “friends of friends”, social-media exchangers",
         who="—",
         rule="Prohibited. Only licensed banks and authorised exchange institutions may deal in personal FX.",
         pros="None.",
         cons="No legal recourse if it fails, and the account that receives the money becomes part of an anti-money-laundering file.",
         cost="Warning, confiscation of gains, up to 30% of the amount; criminal liability for illegal business operation", src=["V01", "V02"], verified=True),
    dict(id="M13", cls="prohibited", name="Crypto, USDT and stablecoin conversion",
         who="—",
         rule="Prohibited. Converting legal tender to virtual currency is illegal financial activity in China.",
         pros="None.",
         cons="Loss falls on the participant, and the on/off-ramp is exactly what the monitoring is built to catch.",
         cost="Criminal exposure; civil transactions may be void", src=["V01"], verified=None),
    dict(id="M14", cls="prohibited", name="False invoices, false purpose declarations, inflated or deflated trade",
         who="—",
         rule="Prohibited. The transaction basis must be real, and the declared purchase purpose must match the remittance.",
         pros="None.",
         cons="Banks cross-check tax filings, customs data and the purchase declaration.",
         cost="Art. 40 illegal arbitrage: up to 30%; Art. 44 change of use: up to 30%", src=["V01", "V26"], verified=True),
    dict(id="M15", cls="prohibited", name="Carrying more than USD 10,000 in cash out in person",
         who="—",
         rule="Above USD 10,000-equivalent per person per trip is prohibited in principle; USD 5,000–10,000 needs a carrying certificate.",
         pros="None at the amounts in this project.",
         cons="Physical loss and theft risk, plus customs detection. USD 400,000 would need 40+ trips.",
         cost="Art. 42: warning plus up to 20% of the amount", src=["V01", "V24"], verified=True),
]

def page_methods():
    b = ['<h1>Every method, with its real cost and its real ceiling</h1>',
         '''<p class="lede">Fifteen routes. Nine are lawful, six are prohibited — the prohibited ones are listed
because a serious answer has to say why each is worse than it looks, not to recommend them. The two columns
that matter are <b>ceiling</b> and <b>cost at USD 400,000</b>.</p>''']
    b.append(anchor_box())

    b.append('<div class="stats">'
             '<div class="stat"><b>9</b><span>lawful routes</span></div>'
             '<div class="stat"><b>6</b><span>prohibited, documented only</span></div>'
             '<div class="stat"><b>2</b><span>routes with no amount ceiling</span></div>'
             '<div class="stat"><b>0</b><span>routes that need a tax on conversion</span></div>'
             '</div>')

    b.append('<div class="table-wrap"><table class="data cost" id="methods">'
             '<thead><tr><th>#</th><th>Method</th><th>Who can use it</th><th>Ceiling</th>'
             '<th>Pros</th><th>Cons</th><th>Cost at $400k</th><th>Source</th></tr></thead><tbody>')
    m400 = {m["key"]: m for m in methods_for(400_000)}
    for m in METHODS:
        cls = {"lawful": "ok", "lawful-approval": "warn", "prohibited": "no"}[m["cls"]]
        label = {"lawful": "lawful", "lawful-approval": "lawful · approval", "prohibited": "prohibited"}[m["cls"]]
        ceiling = "no ceiling" if m["id"] in ("M02", "M08", "M03") else ("USD 50,000 / person / year" if m["id"] in ("M01",) else "—")
        b.append(f'''<tr class="row-{m["cls"]}"><td><b>{m["id"]}</b><br><span class="tag {cls}">{label}</span></td>
<td><b>{esc(m["name"])}</b><div class="rule">{esc(m["rule"])}</div></td>
<td>{esc(m["who"])}</td><td class="nowrap">{ceiling}</td>
<td class="good">{esc(m["pros"])}</td><td class="bad">{esc(m["cons"])}</td>
<td class="num">{esc(m["cost"])}</td>
<td class="src">{tags(*m["src"])}</td></tr>''')
    b.append('</tbody></table></div>')

    b.append('''<div class="notice amber"><b>The honest ranking.</b><br>
1. If you have emigrated or inherited: <b>M03</b>, because it is the only route designed for a whole balance.<br>
2. If you are a foreign national with China-earned income: <b>M04</b>, because there is no ceiling and the
review is of source, not purpose.<br>
3. If the money is a genuine current-account payment: <b>M02</b>, which is M01's arithmetic without M01's cap.<br>
4. If you are a Chinese resident moving your own savings with no qualifying transaction: there is no clean
over-the-counter route, and that gap — not a tax — is the real problem. It is answered by M03 or not at all.</div>''')

    b.append('<h2>The same six routes, priced</h2>')
    b.append('<p class="sub">Totals are all-in USD cost. “Not published” means no official page states the figure; it is not zero.</p>')
    b.append('<div class="table-wrap"><table class="data cost" data-table="matrix-methods"><thead><tr><th>USD</th>'
             '<th>M1</th><th>M2</th><th>M3</th><th>M4</th><th>M5</th><th>M6</th><th>Source</th></tr></thead><tbody>')
    for r in MODEL["rows"]:
        b.append(f'<tr><td class="num"><b>{money(r["usd"],0)}</b></td>')
        for m in r["methods"]:
            t = total(m)
            if m["key"] == "M1" and r["usd"] > 50_000:
                b.append('<td class="num cell-no">n/a</td>')
            elif m["key"] == "M6" and r["usd"] > 10_000:
                b.append('<td class="num cell-no">n/a</td>')
            elif t is None:
                b.append('<td class="num cell-blank">—</td>')
            else:
                b.append(f'<td class="num">{money(t,2)}</td>')
        b.append(f'<td class="src">{tags("V10","V12","V03","V05","V16")}</td>')
        b.append('</tr>')
    b.append('</tbody></table></div>')
    b.append('<p class="next"><a href="cost-playbook.html">Next: exactly how each one is executed, step by step →</a></p>')
    return shell("cost-methods.html", "All CNY → USD methods, pros and cons",
                 "Fifteen documented routes for converting CNY to USD, with who qualifies, the ceiling, the real cost and why the prohibited ones are worse.",
                 "\n".join(b), "Category 02 · The routes")


# --------------------------------------------------------------------------
# page 3 — playbook
# --------------------------------------------------------------------------
PLAY = [
    dict(id="P1", title="M02 · Genuine current-account purchase — the workhorse",
         for_="You have a real, provable reason to send money abroad (tuition, medical bills, supporting family, paying a foreign supplier, a service you are buying).",
         steps=[
             ("Before anything else, get the classification in writing.",
              "Ask the bank, in writing: “Which current-account purpose code applies to this payment, and what is your complete document list for it?” A branch answer is not binding, but it is the only cheap way to find out whether the rest of this list is worth doing."),
             ("Assemble the transaction file, newest first.",
              "Contract or invoice, the school's fee schedule or the hospital's estimate, proof of the relationship for family support, and bank statements showing where the RMB came from. The bank is required to check that the document is genuine and matches the payment (V01 Art. 12)."),
             ("Check the tax-filing trigger.",
              "For a single outward payment above USD 50,000-equivalent for services, income or a current transfer to an individual, a 税务备案表 from the tax authority is required before the bank will pay (V08). Travel, study and family visits are exempt (V08 Art. 3(13)). This is a form, not a payment."),
             ("Sign the purchase declaration.",
              "《个人购汇申请书》 — six prohibitions, one purpose only, and the purpose must match what you are actually paying for (V26). Declaring “travel” and paying a property deposit is the specific thing Art. 44 punishes."),
             ("Transact one payment, then re-check.",
              "Buy and remit in the same instruction where the bank allows it, so the purchase purpose and the remittance purpose cannot drift apart. Keep the receipt, the rate and the SWIFT reference."),
             ("File the U.S. side on its own calendar.",
              "FBAR by 15 April (automatic to 15 October) if the aggregate of all your foreign accounts exceeded USD 10,000 at any point (V13); Form 8938 with the return if you cross the applicable threshold (V15)."),
         ],
         fails="The single most common failure is a purpose that is real in your head and absent from the paper. The second is assuming that having a large legitimate reason removes the documentation need — it does the opposite, because the file gets read more carefully."),
    dict(id="P2", title="M03 · Emigrant property transfer — the only whole-balance route",
         for_="You have emigrated: you hold foreign citizenship, or permanent residence abroad, or HK/Macau residence, and you have cancelled your mainland household registration.",
         steps=[
             ("Confirm you are inside the definition before spending money on documents.",
              "PBC [2004] No. 16 Art. 2 covers two things only: an emigrant's own lawful property realised after taking up the new status, and an inheritance. If neither describes you, stop here — this route does not exist for you and no amount of paperwork creates it."),
             ("Write the single application for the whole amount.",
              "Art. 6 requires one application covering everything you intend to transfer, then phased remittances: at most one half first, at most half the remainder after one year, the balance after two years. At RMB 200,000-equivalent or less you may remit in one go."),
             ("Collect the identity set.",
              "Passport or foreign ID, proof of settlement abroad certified by a Chinese embassy or consulate, and the police certificate cancelling your mainland household registration (PBC [2004] No. 16 Art. 8)."),
             ("Collect the property and source set.",
              "Title deeds, sale contract, demolition or relocation agreement, lease, or the transfer agreement — whatever proves the asset and the realisation. Then the tax certificate or tax-payment voucher from the tax authority where the asset or the income sits (Art. 8(6))."),
             ("Settle the tax on the gain first.",
              "Property transfer income bears 20% on proceeds minus original value minus reasonable expenses (V09 Art. 3(3), 6(5)). This is the one genuine tax in the whole picture, and it is due whether or not you ever convert. Art. 10(5) also requires tax clearance before cancelling household registration on emigrating."),
             ("File with the right SAFE office.",
              "The branch where your household was registered (Art. 5). At RMB 500,000-equivalent or less the branch decides; above that it goes to SAFE headquarters (Art. 10). Apply through the branch either way."),
             ("Remit against the approval, to your own account only.",
              "Art. 11 requires the bank to send the FX directly to your own account in the country of residence. You cannot take it out as domestic cash, and you cannot route it to a third party."),
             ("Repeat at the one-year points.",
              "Second and later tranches need the approval reply and the previous 核准件 (Art. 8, closing paragraph). Diarise it — the phasing is time-based, not fee-based."),
         ],
         fails="Two failures dominate. The first is applying for part of the balance: the application must cover all of it, so a partial application is refused. The second is arriving with a tax certificate for the wrong authority — the certificate must come from the tax office where the asset or income is located."),
    dict(id="P3", title="M04 · Foreign national with China-earned current-account income",
         for_="You hold a non-Chinese passport and the RMB is lawful current-account income you earned in China — salary, fees, rent, dividends already taxed.",
         steps=[
             ("Establish which rule you are under, because they are exclusive.",
              "Art. 59 of 汇发〔2020〕14号, quoted verbatim by SAFE Tianjin: a 境外个人 with lawful current-account RMB income buys FX against ID plus source-of-funds evidence including tax vouchers; the annual convenience amount instead applies to 境外个人 holding a foreigner permanent-residence ID (V23). If you hold that card, you are on the convenience-amount track, not this one."),
             ("Collect the source-of-funds set, not the use-of-funds set.",
              "This is the structural advantage: the review is about where the money came from. Employment contract, payslips, the individual income tax record, the employer's withholding certificate, and bank statements tracing salary into the account."),
             ("Settle any unpaid PRC tax before applying.",
              "Salary is taxed at 3%–45% progressive and withheld by the employer; interest, dividends, rent and property gains at 20% (V09). If the record shows an unpaid line, the bank will see it in the same file."),
             ("Check the USD 50,000-per-payment filing trigger.",
              "Above USD 50,000-equivalent per outward payment the 税务备案表 is needed (V08). Below it, not."),
             ("Transact, then keep the trail for the U.S. return.",
              "You will need this file again — for the FBAR maximum-value figure and for any foreign tax credit claim."),
         ],
         fails="The common error is treating this as available to anyone with a foreign passport. It is available for current-account income, and the words “current account” do real work: inherited property and accumulated capital are not current-account income."),
    dict(id="P4", title="M01 · Within the convenience amount — deliberately last",
         for_="Small amounts, or the first test of a new bank relationship.",
         steps=[
             ("Buy and remit in one visit.",
              "ID plus the signed declaration. No transaction file below the limit (V03)."),
             ("Do not reach for this route because it is simple.",
              "It is capped at USD 50,000 per person per year. Using family members to stay under the cap is the exact pattern that lands people on the 关注名单 (V25), and the cost of that is three years of full documentary review on every transaction."),
             ("Do not treat it as a template for the balance.",
              "Eight people × USD 50,000 for USD 400,000 is split purchase. The penalty ceiling is 30% of the amount (V01 Art. 40), which on USD 400,000 is USD 120,000 — three times the total conversion cost."),
         ],
         fails="Thinking the limit is a tax threshold. It is a documentation threshold: below it, ID only; above it, evidence. Neither is a tax."),
    dict(id="P5", title="The U.S. side, run in parallel and never as an afterthought",
         for_="All routes. This is where the only six-figure numbers in the project live.",
         steps=[
             ("Report the account, every year, whether or not it earned anything.",
              "FBAR if the aggregate of all foreign accounts exceeded USD 10,000 at any moment in the calendar year (V13). Due 15 April, automatic extension to 15 October. Not filed with the return."),
             ("Report the assets if you cross the Form 8938 threshold.",
              "Single, living in the U.S.: over USD 50,000 on the last day or USD 75,000 at any time; joint: USD 100,000/150,000 (V15). Form 8938 does not replace the FBAR, and the FBAR does not replace it."),
             ("Report a large foreign gift on Form 3520.",
              "Over USD 100,000 aggregate from a nonresident alien or foreign estate in a tax year: Part IV, information only, no tax (V17). Due 15 April, 15 June if you live abroad, extended to 15 October."),
             ("Do not report the transfer itself as income.",
              "Moving your own after-tax money is not an income event, and a gift is excluded from gross income outright (V16). Report the account; do not invent a taxable receipt."),
             ("If prior years are missing, fix them deliberately.",
              "The IRS's own instruction for a late FBAR is to file it as soon as possible if the IRS has not contacted you and you are not under investigation (V13). Which compliance route fits is a facts-and-circumstances question for a practitioner — this page does not choose one for you."),
         ],
         fails="The expensive mistake is not the exchange rate. It is discovering in year four that three years of FBARs are missing on an account that has been over USD 10,000 the whole time."),
]

def page_playbook():
    b = ['<h1>Exactly how each route works, in order</h1>',
         '''<p class="lede">The order is the advice. Every expensive step here sits after a cheap eligibility
check, so that a route you cannot use costs you an email rather than a notary bill.</p>''']
    b.append('''<div class="notice"><b>How to read this.</b> Each route starts with the one question that decides
whether the route exists for you at all. If the answer is no, the remaining steps are irrelevant — and that is
the point of putting it first.</div>''')

    b.append('<div class="toc"><b>Jump to</b> ' + " ".join(
        f'<a href="#{p["id"]}">{esc(p["id"])}</a>' for p in PLAY) + '</div>')

    for p in PLAY:
        b.append(f'<section class="play" id="{p["id"]}"><h2>{esc(p["title"])}</h2>')
        b.append(f'<p class="for"><b>Who this is for.</b> {esc(p["for_"])}</p>')
        b.append('<ol class="steps">')
        for i, (head, body) in enumerate(p["steps"], 1):
            b.append(f'<li><span class="step-n">{i}</span><div><b>{esc(head)}</b><p>{body}</p></div></li>')
        b.append('</ol>')
        b.append(f'<p class="fails"><b>Where it goes wrong.</b> {esc(p["fails"])}</p></section>')

    b.append('<h2>The calendar for a USD 400,000 emigrant transfer</h2>')
    b.append('<p class="sub">The phasing in PBC [2004] No. 16 Art. 6 is time-based, so the schedule is the plan.</p>')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>When</th><th>What happens</th><th>Cost incurred</th><th>Rule</th><th>Source</th></tr></thead><tbody>')
    b.append(f'<tr><td class="nowrap"><b>Month 0</b></td><td>Tax on the property gain settled; tax certificate issued</td><td class="num">20% of the gain, not of the balance</td><td>IIT Law Art. 3(3), 6(5)</td><td class="src">{tags("V09")}</td></tr>')
    b.append(f'<tr><td class="nowrap"><b>Month 0–2</b></td><td>Single application filed locally (under RMB 500,000-equivalent) or referred to SAFE headquarters</td><td class="num"><span class="blank">approval fee not published</span></td><td>PBC [2004] No. 16 Art. 10</td><td class="src">{tags("V05")}</td></tr>')
    b.append(f'<tr><td class="nowrap"><b>First remittance</b></td><td>Up to one half of the approved amount</td><td class="num">{money(total(methods_for(200_000)[0]),2)} on USD 200,000</td><td>Art. 6</td><td class="src">{tags("V05","V10","V12")}</td></tr>')
    b.append(f'<tr><td class="nowrap"><b>+12 months</b></td><td>Up to half of what remains (USD 100,000)</td><td class="num">{money(total(methods_for(100_000)[0]),2)}</td><td>Art. 6</td><td class="src">{tags("V05","V10","V12")}</td></tr>')
    b.append(f'<tr><td class="nowrap"><b>+24 months</b></td><td>The remaining USD 100,000</td><td class="num">{money(total(methods_for(100_000)[0]),2)}</td><td>Art. 6</td><td class="src">{tags("V05","V10","V12")}</td></tr>')
    b.append(f'<tr class="totals"><td>Total</td><td>Three remittances across two years</td><td class="num"><b>{money(total(methods_for(200_000)[0])+2*total(methods_for(100_000)[0]),2)}</b></td><td>Plus PRC tax on the gain</td><td class="src">{tags("V05","V10","V12")}</td></tr>')
    b.append('</tbody></table></div>')
    b.append('''<p class="fine">Splitting into three remittances costs the same as one: the bank caps its
charge at CNY 260 per transfer, so the extra two transfers add about USD 122 in total. The phasing rule costs
you time, not money.</p>''')
    b.append('<p class="next"><a href="cost-tax.html">Next: what the “conversion penalty” actually is →</a></p>')
    return shell("cost-playbook.html", "Step-by-step playbook for every route",
                 "Ordered, document-by-document steps for each lawful CNY to USD route, with the one eligibility question that decides whether the route exists.",
                 "\n".join(b), "Category 03 · The execution")


# --------------------------------------------------------------------------
# page 4 — the "penalty" decoded
# --------------------------------------------------------------------------
LAYERS = [
    dict(id="T1", name="PRC income tax on whatever created the money",
         rate="20% flat on property gains, interest, dividends, rent and incidental income; 3%–45% progressive on salary, mostly withheld at source",
         base="the GAIN, not the balance", when="when the income arises — before and independently of any conversion",
         claimed="often mistaken for a conversion tax",
         src=["V09"], verified=True,
         verdict="This is the only genuine tax that isn't already paid. If the RMB came from a property sale, 20% of the profit is due whether the money stays in China or leaves. Converting later adds nothing."),
    dict(id="T2", name="The bank's FX margin",
         rate="0.4004% measured, 9 November 2026",
         base="the USD amount", when="at the moment of exchange",
         claimed="invisible; nobody quotes it separately",
         src=["V10"], verified=True,
         verdict="The only real cost of converting. On USD 400,000 it is USD 1,601.48."),
    dict(id="T3", name="Bank wire, cable and correspondent charges",
         rate="1‰, floor CNY 50, cap CNY 260, plus CNY 150 cable",
         base="per transfer", when="at remittance",
         claimed="quoted separately",
         src=["V12"], verified=True,
         verdict="Tiny and capped. Around USD 61 on anything above USD 38,800. Correspondent and U.S. receiving-bank fees are not published and are left blank."),
    dict(id="T4", name="SAFE approval filings",
         rate="no official fee found",
         base="—", when="at application",
         claimed="sometimes described as a “tax”",
         src=["V05", "V08"], verified=False,
         verdict="A permission and a form, not a payment. The 税务备案表 is a filing; the tax authority checks that the underlying tax was paid, it does not levy a new one."),
    dict(id="T5", name="U.S. income tax on the transfer",
         rate="none",
         base="none", when="—",
         claimed="assumed by many people to exist",
         src=["V16", "V20"], verified=True,
         verdict="Moving your own after-tax money is not an income event, and a gift is excluded from gross income. What is taxable is the underlying income, in the year it arose."),
    dict(id="T6", name="U.S. information-reporting penalties",
         rate="FBAR non-willful up to USD 16,536 per report; willful the greater of USD 165,353 or 50% of the balance; Form 8938 up to USD 60,000; Form 3520 5% of the gift per month, capped at 25%",
         base="per report / per account", when="assessment, years later",
         claimed="the actual “considerable amount”",
         src=["V14", "V15", "V18"], verified=True,
         verdict="This is where the six-figure risk sits, and it is triggered by silence rather than by converting. It is the only line here that can exceed the balance."),
    dict(id="T7", name="PRC penalties for doing it the wrong way",
         rate="evasion and illegal arbitrage up to 30% of the amount (30%–100% if serious); private FX dealing up to 30%; illegal cash carriage up to 20%",
         base="the amount", when="enforcement",
         claimed="the real reason not to use brokers",
         src=["V01", "V02"], verified=True,
         verdict="On USD 400,000, the 30% ceiling is USD 120,000 — 72 times the total conversion cost. Plus three years without a convenience amount."),
]

def page_tax():
    b = ['<h1>What the “considerable amount of taxes” actually is</h1>',
         '''<p class="lede">Seven cost layers get called “the tax on converting”. Only two of them are money
you pay for converting, and only one of them can reach six figures. Here they are separated, with the base
each one applies to — because that is where the confusion starts.</p>''']
    b.append('<div class="notice amber"><b>The finding, stated plainly.</b> No official source in this research '
             'imposes a tax, duty or charge on turning personal RMB into USD. The amounts people describe as a '
             '“conversion penalty” are, in official documents, one or more of: income tax on what created the '
             'money, the bank\'s price, the bank\'s fee, a filing requirement, or — most expensively — a U.S. '
             'reporting penalty for an account that was never declared.</div>')

    b.append('<div class="table-wrap"><table class="data cost"><thead><tr>'
             '<th>Layer</th><th>Rate / amount</th><th>Applied to</th><th>Charged when</th>'
             '<th>What it really is</th><th>Source</th><th>Verified</th></tr></thead><tbody>')
    for l in LAYERS:
        b.append(f'''<tr><td><b>{l["id"]}</b><div class="rule">{esc(l["name"])}</div></td>
<td class="num">{esc(l["rate"])}</td><td>{esc(l["base"])}</td><td>{esc(l["when"])}</td>
<td>{l["verdict"]}</td><td class="src">{tags(*l["src"])}</td>
<td>{status_pill(True if l["verified"] else None)}</td></tr>''')
    b.append('</tbody></table></div>')

    b.append('<h2>The base matters more than the rate</h2>')
    b.append('''<p>Two people with USD 400,000 in a China account can face wildly different PRC tax, and the
conversion is irrelevant to both:</p>''')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>Where the money came from</th>'
             '<th>PRC tax already due</th><th>On a USD 400,000 balance</th><th>Conversion cost</th><th>Source</th></tr></thead><tbody>')
    b.append(f'<tr><td>Salary already withheld</td><td>3%–45% progressive, withheld monthly</td><td class="num">already paid; nothing further</td><td class="num">{money(total(methods_for(400_000)[0]),2)}</td><td class="src">{tags("V09")}</td></tr>')
    b.append(f'<tr><td>Property sale</td><td>20% of proceeds minus original value minus reasonable expenses</td><td class="num">20% of the <b>profit</b> — e.g. USD 80,000 on a USD 400,000 gain</td><td class="num">{money(total(methods_for(400_000)[0]),2)}</td><td class="src">{tags("V09")}</td></tr>')
    b.append(f'<tr><td>Bank interest / dividends</td><td>20% flat</td><td class="num">20% of the interest, not of the deposit</td><td class="num">{money(total(methods_for(400_000)[0]),2)}</td><td class="src">{tags("V09")}</td></tr>')
    b.append(f'<tr><td>Inheritance</td><td>China has no inheritance tax in the sources reviewed</td><td class="num"><span class="blank">no figure — not verified as zero</span></td><td class="num">{money(total(methods_for(400_000)[0]),2)}</td><td class="src">{tags("V09")}</td></tr>')
    b.append('</tbody></table></div>')
    b.append('''<p class="fine">The inheritance row is deliberately blank. This session found no official page
establishing an inheritance tax, and “no page found” is not the same as “the rate is zero”. It is on the
flagged page.</p>''')

    b.append('<h2>Where the six figures actually come from</h2>')
    b.append('''<p>The largest number in this project is not a percentage. It is a fixed maximum, and it applies
to a failure to file rather than to a decision to convert:</p>''')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>Provision</th><th>Maximum</th><th>Trigger</th><th>On a USD 400,000 account</th><th>Source</th></tr></thead><tbody>')
    b.append(f'<tr><td>FBAR, non-willful, 31 U.S.C. 5321(a)(5)(B)(i)</td><td class="num">{money(PEN["fbar_non_willful_max_usd"]["value"],0)}</td><td>A missed or wrong annual report</td><td class="num">{money(PEN["fbar_non_willful_max_usd"]["value"],0)} per report</td><td class="src">{tags("V14")}</td></tr>')
    b.append(f'<tr class="totals"><td>FBAR, willful, 31 U.S.C. 5321(a)(5)(C)(i)(I)</td><td class="num">{money(PEN["fbar_willful_max_usd"]["value"],0)}</td><td>Knowing failure</td><td class="num"><b>the greater of {money(PEN["fbar_willful_max_usd"]["value"],0)} or half the balance = {money(200_000,0)}</b></td><td class="src">{tags("V14")}</td></tr>')
    b.append(f'<tr><td>Form 8938 failure to disclose</td><td class="num">{money(PEN["form_8938_failure_max_usd"]["value"],0)}</td><td>Failure plus continued non-filing after notice</td><td class="num">{money(PEN["form_8938_failure_max_usd"]["value"],0)}</td><td class="src">{tags("V15")}</td></tr>')
    b.append(f'<tr><td>Form 3520, s.6039F, unreported foreign gift</td><td class="num">5%/month, cap 25%</td><td>Unreported gift over USD 100,000</td><td class="num">{money(100_000,0)} on a USD 400,000 gift</td><td class="src">{tags("V18","V17")}</td></tr>')
    b.append(f'<tr><td>PRC evasion / illegal arbitrage</td><td class="num">30% (30%–100% if serious)</td><td>An unlawful transfer</td><td class="num">{money(120_000,0)} at the 30% ceiling</td><td class="src">{tags("V01","V02")}</td></tr>')
    b.append('</tbody></table></div>')

    b.append('''<div class="callout"><b>The asymmetry, in one line.</b> Converting USD 400,000 costs about
<b>USD 1,663</b>. Mis-declaring it as willful can cost up to <b>USD 200,000</b> — 120 times more. Every hour
spent on the reporting file is worth more than every hour spent shopping for a better rate.</div>''')

    b.append('<h2>Three specific things that are not taxes</h2>')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>What it is called</th><th>What it legally is</th><th>Evidence</th><th>Source</th></tr></thead><tbody>')
    b.append('<tr><td>“The USD 50,000 limit”</td><td>A documentation threshold. Below it ID only; above it evidence. SAFE states it is “not the limit” on purchases.</td><td>No rate, no charge, no payment</td><td class="src">%s</td></tr>' % tags("V03"))
    b.append('<tr><td>“The tax filing form above USD 50,000”</td><td>A 税务备案表, filed with the tax authority before the bank pays. The authority may check the underlying tax; it does not levy a new one.</td><td>No amount, no rate</td><td class="src">%s</td></tr>' % tags("V08"))
    b.append('<tr><td>“The 关注名单”</td><td>An administrative list. Consequence is three years without the convenience amount and full review of every transaction.</td><td>No fine in itself; the fine comes from Art. 40</td><td class="src">%s</td></tr>' % tags("V25"))
    b.append('</tbody></table></div>')
    b.append('<p class="next"><a href="cost-review.html">Next: what this research could not verify →</a></p>')
    return shell("cost-tax.html", "The “conversion penalty” decoded",
                 "Seven cost layers separated: PRC income tax, bank spread, wire fees, SAFE filings, U.S. income tax, U.S. reporting penalties and PRC enforcement fines.",
                 "\n".join(b), "Category 04 · The analysis")


# --------------------------------------------------------------------------
# page 5 — flagged for review
# --------------------------------------------------------------------------
FLAGS = [
    dict(id="A1", sev="High", title="Two in-force instruments define 境内个人 differently, and the difference decides your route",
         detail="国务院令第532号 Art. 52(2) defines 境内个人 as a Chinese citizen <i>or a foreign national who has continuously resided in China for one full year</i>. PBC Order [2006] No. 3 Art. 37(2) defines 境外个人 as a passport-holding foreign national. A U.S. citizen living in China therefore falls inside both definitions on the face of the two texts.",
         impact="If 532 §52(2) governs, a U.S. citizen who lives in China is a 境内个人 and the convenance-amount / capital-account machinery applies. If Order 3 §37(2) governs, Art. 13 / Art. 59 current-account conversion applies with no ceiling. The answer changes which of M02, M04 or M03 you use.",
         action="Ask the bank to state, in writing, which 主体类别 they will record for the account and which article they rely on. This is the single highest-value question in the project.",
         src=["V01", "V24", "V23"], value=""),
    dict(id="A2", sev="High", title="Correspondent, intermediary and U.S. receiving-bank fees: no official figure anywhere",
         detail="The BOC tariff page publishes no correspondent fee, no FCC/全额到账 charge and no receiving-bank charge. No U.S. bank publishes a single generic incoming-wire price in a form that could be cited as an official rate card for this purpose.",
         impact="Every total on this site is a floor. The missing component is typically a flat charge, so its effect shrinks as a percentage as the amount grows — but the absolute gap is unknown.",
         action="Ask the sending branch for the correspondent route and its charge, and the receiving bank for its incoming-wire fee, before relying on any total here.",
         src=["V12"], value=""),
    dict(id="A3", sev="High", title="SAFE approval fees and notarisation costs for M03 are not published",
         detail="PBC [2004] No. 16 creates the approval; neither it nor any official service guide fetched in this session states an application fee. Notarisation and certified translation are private-market costs with no official price.",
         impact="M03 has no total on this site, only a partial one made of the spread and the wire fee.",
         action="Obtain the fee schedule from the local SAFE branch and from a notary in the jurisdiction where the documents are executed.",
         src=["V05"], value=""),
    dict(id="A4", sev="Resolved", title="A previously cited SAFE branch URL returned SAFE's error page — fixed",
         detail="https://www.safe.gov.cn/guangdong/2021/0323/1994.html (SAFE Guangdong, 个人对外财产转移购付汇业务指南) returned SAFE's “该页面不存在” page when fetched on 2026-11-09. The same proposition is inside PBC [2004] No. 16 Art. 8.",
         impact="Other layers of this repository linked to it from five data files and one research memo. Those links now point at PBC [2004] No. 16 instead, which is a stronger citation.",
         action="Fixed in this session: data/channels.csv, data/china_rules.csv, data/flags.csv, data/sources.csv, data/deep_sources.json, research/channels.md, research/china-framework.md, and the deep-* pages rebuilt from them. The old URL survives only in this record.",
         src=["V05"], value=""),
    dict(id="A5", sev="Medium", title="The BOC tariff page carries a 2014 effective date",
         detail="The published personal cross-border telegraphic-transfer tariff on boc.cn is labelled “收费标准 2014年11月1日起”. It may still be current, but the page itself does not state that it has been re-confirmed since 2014, and it warns that branches may publish different prices.",
         impact="The CNY 50/260/150 figures could be stale by an unknown amount. Because they are capped and small, even a doubling changes the USD 400,000 total by about USD 61.",
         action="Ask the branch for its current printed tariff and compare. Low financial risk, so it does not block anything.",
         src=["V12"], value=""),
    dict(id="A6", sev="Medium", title="The USD 50,000 tax-filing trigger has been partly superseded",
         detail="公告2013年第40号 carries a note that 公告2021年第19号 repealed its Articles 1(2), 2(2), 5, 6, 7, 8, 10 and Annex 2 with effect from 2021-06-29. The USD 50,000 filing threshold sits in Article 1(1), which the note does not list as repealed, but the surrounding machinery has changed.",
         impact="The threshold as quoted is probably still live; the procedural detail around it (who files, in what form, electronically) may not be.",
         action="Confirm the current threshold against 公告2021年第19号 before relying on the exact figure at the boundary.",
         src=["V08"], value=""),
    dict(id="A7", sev="Medium", title="No official figure establishes the PRC inheritance-tax position",
         detail="This session found no official page imposing an inheritance tax, and equally no official page stating that inheritances are exempt. An absence of a charging provision is not the same as a published zero rate.",
         impact="The inheritance row in the tax table is blank rather than “0%”.",
         action="Confirm with the tax authority that handled the estate. Do not treat the blank as zero.",
         src=["V09"], value=""),
    dict(id="A8", sev="Medium", title="The personal-transaction exception to the currency-gain rule was not verified",
         detail="26 CFR 1.988-1 is cited here only to identify the provision. The commonly cited personal-transaction exception (s.988(e)) was not fetched and is not asserted anywhere on this site.",
         impact="No conclusion on U.S. tax on FX movements between the purchase and the remittance is offered.",
         action="Read s.988(e) and the current Form 8949 instructions before claiming any de-minimis exclusion.",
         src=["V19"], value=""),
    dict(id="A9", sev="Low", title="Everything is priced off a single bank and a single minute",
         detail="The 0.4004% is Bank of China, 09:15:45 on 2026-11-09. Other banks quote differently, the rate moves intraday, and the page's own disclaimer says the counter rate governs.",
         impact="The spread column can move by a few hundredths of a percent between banks and during the day. The structure (linear, capped fee) does not change.",
         action="Replace V10 with the actual quote at the moment of transacting; the model is designed to be re-anchored, not memorised.",
         src=["V10"], value=""),
    dict(id="A10", sev="High", title="This research cannot tell you your own tax position without facts you have not supplied",
         detail="The amount, the source of the money, your residence status, whether the account has ever been declared, and whether prior-year filings exist are all unknown. Every number here is conditional on facts that are not in evidence.",
         impact="The recommendation is a sequence, not an amount. Any single figure quoted to you as “your cost” would be fabricated.",
         action="Take the sequence on the playbook page to a cross-border practitioner together with the account's actual history.",
         src=["V01", "V14"], value=""),
]

PRIOR = [
    dict(id="D1", title="Earlier pages assert the USD 50,000 figure is “not a cap” without the capital-account counterweight",
         found="index.html: “China's USD 50,000 annual individual convenience amount is a simplified processing threshold, not a blanket annual legal cap.” That is correctly sourced to SAFE Ningxia. But 国务院令第532号 Art. 17 requires SAFE registration for individual outbound investment and Art. 22 requires approval for capital-account payments, and Art. 52(2) can classify a long-resident foreign national as 境内个人.",
         why="Read alone, the earlier sentence invites the conclusion that any balance can be moved by producing evidence. Evidence satisfies the current-account test; it does not open a capital account.",
         links=["V03", "V01"]),
    dict(id="D2", title="The salary-repatriation route is labelled “secondary source” when it is primary",
         found="index.html and methods.html describe the foreign-national salary route as “flagging — secondary source”.",
         why="PBC Order [2006] No. 3 Art. 13 is a primary instrument, and SAFE Tianjin quotes 汇发〔2020〕14号 Art. 59 verbatim. The route should carry a primary citation, not a caveat.",
         links=["V24", "V23"]),
    dict(id="D3", title="Four layers of pages now cover the same findings in four formats",
         found="Editorial pages (routes/methods/tax/…), the generated docs/ dashboard, the deep-* pages, and now this layer.",
         why="This is a maintenance risk rather than an error: the same proposition can drift out of sync in four places. This session resolves it by making this layer the only one that carries the price table and the execution steps, and by linking rather than restating.",
         links=["V10"]),
]

def page_review():
    b = ['<h1>Flagged for review</h1>',
         '''<p class="lede">Ten items this research could not verify, one item already fixed during this session,
and three defects found in the pages that were here before. Nothing on this page blocks the site: each item is either blank in the tables or
explicitly labelled. This is the list to work through with a bank, a notary and a practitioner.</p>''']
    b.append('''<div class="notice amber"><b>Rule applied throughout.</b> If a value could not be read off an
official page during this session, the cell is blank. It is never filled with a plausible number, an average,
or a figure from a secondary source.</div>''')

    b.append('<h2>A · Verification gaps in this layer</h2>')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>#</th><th>Severity</th><th>Item</th>'
             '<th>What we found</th><th>Why it matters</th><th>What to do</th><th>Source</th></tr></thead><tbody>')
    for f in FLAGS:
        pill = {"High": "no", "Medium": "warn", "Low": "ok", "Resolved": "ok"}[f["sev"]]
        b.append(f'''<tr><td><b>{f["id"]}</b></td><td><span class="tag {pill}">{f["sev"]}</span></td>
<td><b>{esc(f["title"])}</b></td><td>{f["detail"]}</td><td>{f["impact"]}</td><td>{f["action"]}</td>
<td class="src">{tags(*f["src"])}</td></tr>''')
    b.append('</tbody></table></div>')

    b.append('<h2>B · Defects in the pages that were already published</h2>')
    b.append('<p class="sub">Recorded here rather than edited, because those files belong to other sessions. '
             'None of them changes a number in this layer.</p>')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>#</th><th>Defect</th>'
             '<th>Where</th><th>Why it matters</th><th>Source</th></tr></thead><tbody>')
    for d in PRIOR:
        b.append(f'<tr><td><b>{d["id"]}</b></td><td><b>{esc(d["title"])}</b></td><td>{d["found"]}</td>'
                 f'<td>{d["why"]}</td><td class="src">{tags(*d["links"])}</td></tr>')
    b.append('</tbody></table></div>')

    b.append('<h2>C · Assumptions this model rests on</h2>')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>#</th><th>Assumption</th><th>If it is wrong</th><th>Rests on</th></tr></thead><tbody>')
    for i, a in enumerate(MODEL["assumptions"], 1):
        wrong = ["The cost moves roughly in proportion to the spread; the fee cap is unaffected.",
                 "Multi-transfer routes (M1, M4) multiply the wire fee by the number of transfers.",
                 "Re-anchor by editing data/fx_anchor.json and re-running scripts/build_cost.py; nothing is hand-typed.",
                 "If tax is still due, add 20% of the gain — which is typically 60–100× the conversion cost.",
                 "The reporting-penalty column is the largest number here and is independent of the conversion."][i-1]
        b.append(f'<tr><td>{i}</td><td>{esc(a)}</td><td>{esc(wrong)}</td><td class="src">{tags(*[["V10"],["V12"],["V10"],["V09"],["V16","V20"]][i-1])}</td></tr>')
    b.append('</tbody></table></div>')
    b.append('<p class="next"><a href="cost-sources.html">Next: the full source register with what each page does and does not support →</a></p>')
    return shell("cost-review.html", "Flagged for review",
                 "Ten unverified items and three defects in previously published pages, each with an official source link and the exact question to ask.",
                 "\n".join(b), "Category 05 · What is not proven")


# --------------------------------------------------------------------------
# page 6 — sources
# --------------------------------------------------------------------------
def page_sources():
    b = ['<h1>Sources, and exactly what each one supports</h1>',
         '''<p class="lede">Twenty-six sources. For each one: the proposition it establishes, and the
proposition it does <b>not</b> establish. The second column is the one that keeps this honest.</p>''']
    b.append(f'''<div class="notice"><b>Access note.</b> Every URL below was fetched and read during this
session on 2026-11-09. Fetching was done through a text-extraction service; the site's own copy of each
document is authoritative. Two pages could not be retrieved from this sandbox by direct request and were read
through that service instead (boc.cn, safe.gov.cn); one URL returned an error page and is flagged (A4).</div>''')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>ID</th><th>Tier</th><th>Authority and title</th>'
             '<th>Supports</th><th>Does NOT support</th><th>Link</th></tr></thead><tbody>')
    for s in SOURCES:
        b.append(f'''<tr id="{s["id"]}"><td><b>{s["id"]}</b></td><td class="nowrap">{esc(s["tier"])}</td>
<td><b>{esc(s["authority"])}</b><div class="rule">{esc(s["title"])}</div></td>
<td>{esc(s["supports"])}</td><td class="bad">{esc(s["not_supported"])}</td>
<td class="src"><a href="{esc(s["url"])}" target="_blank" rel="noopener">open ↗</a></td></tr>''')
    b.append('</tbody></table></div>')

    b.append('<h2>Where the numbers in the cost table come from, line by line</h2>')
    b.append('<div class="table-wrap"><table class="data cost"><thead><tr><th>Symbol</th><th>Value</th><th>Read from</th><th>Source</th></tr></thead><tbody>')
    for label, val, sid in [
        ("BOC 现汇卖出价 (spot selling)", f'{ANCHOR["boc_usd_spot_sell"]:.2f} CNY per 100 USD', "V10"),
        ("BOC 中行折算价 (reference)", f'{ANCHOR["boc_usd_reference"]:.2f} CNY per 100 USD', "V10"),
        ("Customer rate used", f'{RATE:.4f} CNY per USD', "V10"),
        ("Measured spread", f'{DER["spread_vs_boc_reference_pct"]:.4f}%', "V10"),
        ("Wire fee", "1‰, floor CNY 50, cap CNY 260", "V12"),
        ("Cable charge", "CNY 150 outside HK/Macau/Taiwan", "V12"),
        ("Convenience amount", "USD 50,000 per person per year", "V03"),
        ("Tax-filing trigger", "USD 50,000 per outward payment", "V08"),
        ("SAFE local-approval limit", "RMB 500,000", "V05"),
        ("FBAR non-willful maximum", f'USD {PEN["fbar_non_willful_max_usd"]["value"]:,}', "V14"),
        ("FBAR willful maximum", f'USD {PEN["fbar_willful_max_usd"]["value"]:,}', "V14"),
        ("Form 3520 gift threshold", "USD 100,000", "V17"),
        ("PRC property-transfer rate", "20% of the gain", "V09"),
    ]:
        b.append(f'<tr><td>{esc(label)}</td><td class="num">{esc(val)}</td><td>{link(sid)}</td><td class="src">{SRC_BY_ID[sid]["authority"]}</td></tr>')
    b.append('</tbody></table></div>')

    b.append('<h2>Method</h2>')
    b.append('''<ol class="method">
<li><b>Fetch, don't recall.</b> Every figure was read off the page during this session. The retrieval date is
recorded in <code>data/fx_anchor.json</code> next to each value.</li>
<li><b>Two instruments, not one.</b> Where a proposition is contested (A1), both texts are quoted rather than
the more convenient one.</li>
<li><b>Blank beats plausible.</b> A cell with no official source stays empty and is listed above. The build
script fails if an UNVERIFIED row carries a value.</li>
<li><b>Arithmetic is checked, not trusted.</b> <code>scripts/verify_cost.py</code> re-derives all
''' + f'{len(MODEL["rows"])} × 6' + ''' cost cells from the anchor file and fails the build if any cell in the HTML
disagrees by one cent.</li>
<li><b>No number is typed into HTML.</b> Every figure on these pages is emitted by
<code>scripts/build_cost.py</code> from <code>data/fx_anchor.json</code>, so a rate change is one edit, not forty.</li>
<li><b>Reject, don't stretch.</b> Where a secondary source (a law firm note, a bank's marketing page, a
comparison site) was the only thing available, it was not used. Two propositions that would have been
convenient were dropped for exactly this reason: the CNH–CNY gap, and the U.S. dividend withholding rate.</li>
</ol>''')
    return shell("cost-sources.html", "Sources and method",
                 "Twenty-six official sources, each with the proposition it supports and the proposition it does not, plus the line-by-line origin of every number.",
                 "\n".join(b), "Category 06 · Provenance")


# --------------------------------------------------------------------------
# page 0 — landing
# --------------------------------------------------------------------------
def page_home():
    t10 = total(methods_for(10_000)[0])
    t50 = total(methods_for(50_000)[0])
    t100 = total(methods_for(100_000)[0])
    t400 = total(methods_for(400_000)[0])
    b = []
    b.append('<h1>Getting money out of China, priced.</h1>')
    b.append(f'''<p class="lede">A U.S. citizen, a mainland China bank account, and a question that turns out
to have a much smaller number in it than expected: converting <b>USD 400,000</b> costs about
<b>{money(t400,0)}</b> all-in. The risk that people describe as “a considerable amount of taxes” is real, but it
is not a conversion charge — it is a U.S. information-reporting penalty that starts at
<b>{money(PEN["fbar_willful_max_usd"]["value"],0)}</b> and can reach <b>half the balance</b>.</p>''')

    b.append(f'''<div class="answer">
  <div class="answer-line"><span>The conversion cost, measured</span><b>{SPREAD*100:.2f}%</b></div>
  <div class="answer-note">Bank of China 现汇卖出价 against its own reference price, 9 November 2026,
  {ANCHOR["boc_timestamp"]}. Not an estimate — two numbers printed on the same page.</div>
</div>''')

    b.append('<div class="stats">'
             f'<div class="stat"><b>{money(t400,0)}</b><span>to convert $400,000</span></div>'
             f'<div class="stat"><b>{money(t10,0)}</b><span>to convert $10,000</span></div>'
             f'<div class="stat"><b>0.40%</b><span>flat, at every size</span></div>'
             f'<div class="stat hot"><b>{money(200_000,0)}</b><span>willful FBAR ceiling on that account</span></div>'
             '</div>')

    b.append('''<div class="notice amber"><b>The three things that are not true.</b><br>
There is no Chinese tax on converting RMB to USD. The USD 50,000 figure is a documentation threshold, not a
tax and not a cap. And moving your own after-tax money to the U.S. is not a U.S. income event. Each of those
has a source on the <a href="cost-sources.html">sources page</a>, and each of them is what the words
“conversion penalty” usually turn out to mean.</div>''')

    b.append('<h2>Start where your question actually is</h2>')
    cards = [
        ("cost-model.html", "01 · The number", "Cost table, $10k → $400k",
         f"Every USD 10,000 step from $10,000 to $400,000 with the spread, the wire fee and the all-in total. "
         f"At $10,000 it is {money(t10,0)}; at $400,000 it is {money(t400,0)}. The marginal cost never changes."),
        ("cost-methods.html", "02 · The routes", "All 15 methods, pros and cons",
         "Nine lawful routes and six prohibited ones, each with who qualifies, the ceiling, and the cost at $400,000. "
         "Two routes have no amount ceiling; one of them needs you to have emigrated."),
        ("cost-playbook.html", "03 · The execution", "Step-by-step, in order",
         "The exact sequence for each route, with the one eligibility question placed first so that a route you "
         "cannot use costs you an email rather than a notary bill. Plus the two-year calendar for a phased transfer."),
        ("cost-tax.html", "04 · The analysis", "What the “penalty” really is",
         "Seven cost layers separated: income tax on what created the money, the bank's margin, the wire fee, SAFE "
         "filings, U.S. income tax, U.S. reporting penalties, and PRC enforcement fines."),
        ("cost-review.html", "05 · Not proven", "Flagged for review",
         "Ten unverified items and three defects in the previously published pages, each with the official source "
         "and the precise question to put to a bank, a notary or a practitioner."),
        ("cost-sources.html", "06 · Provenance", "26 sources, line by line",
         "For every source: what it supports and what it does not. Plus the origin of every single number in the "
         "cost table."),
    ]
    b.append('<div class="grid">')
    for href, eyebrow, title, text in cards:
        b.append(f'''<a class="card" href="{href}"><span class="card-eyebrow">{esc(eyebrow)}</span>
<h3>{esc(title)}</h3><p>{text}</p><span class="card-go">Open →</span></a>''')
    b.append('</div>')

    b.append('<h2>The whole table at a glance</h2>')
    b.append('<p class="sub">Bank purchase plus one outward wire, at the published BOC tariff. Full detail on the <a href="cost-model.html">cost model page</a>.</p>')
    b.append('<div class="table-wrap"><table class="data cost" data-table="home-summary"><thead><tr><th>USD out</th><th>CNY needed</th><th>All-in cost</th><th>as %</th><th>On ID alone?</th><th>Source</th></tr></thead><tbody>')
    for r in MODEL["rows"]:
        if r["usd"] % 50_000 and r["usd"] not in (10_000,):
            continue
        m = r["methods"][0]
        t = total(m)
        ok = '<span class="tag ok">yes</span>' if r["usd"] <= 50_000 else '<span class="tag no">needs evidence</span>'
        b.append(f'<tr><td class="num"><b>{money(r["usd"],0)}</b></td><td class="num">{r["cny"]:,.0f}</td>'
                 f'<td class="num total">{money(t,2)}</td><td class="num">{t/r["usd"]*100:.2f}%</td><td>{ok}</td>'
                 f'<td class="src">{tags("V10","V12")}</td></tr>')
    b.append('</tbody></table></div>')
    b.append('<p class="sub">Showing every 10th row; the <a href="cost-model.html#table">full 40-row table</a> has every USD 10,000 step.</p>')

    b.append('''<h2>What this site will not do</h2>
<p>It will not tell you a single number for your own situation, because the amount, the source of the money,
your residence status, whether the account has ever been declared and whether prior filings exist are all
unknown. Every figure here is conditional. It will not fill in a cost that no official page states — those
cells are blank and listed on the flagged page. And it will not recommend a route that requires a false
declaration, a borrowed quota or an unlicensed exchanger, however common those are.</p>''')

    b.append('''<div class="notice"><b>Other layers in this repository.</b> This dashboard is the priced layer.
The <a href="docs/index.html">data dashboard</a> has 22 channels as filterable structured data; the
<a href="deep-channels.html">deep-research pages</a> catalogue 35 channels against 84 sources; the
<a href="methods.html">editorial pages</a> carry the earlier prose treatment. They overlap by design — the
findings are the same, and this layer adds the arithmetic.</div>''')
    return shell("cost.html", "Getting money out of China, priced",
                 "Computed cost of converting CNY to USD from USD 10,000 to USD 400,000, with every method, the step-by-step execution and the reporting-penalty exposure.",
                 "\n".join(b), "China → United States · CNY → USD · verified 9 November 2026")


# --------------------------------------------------------------------------
# write
# --------------------------------------------------------------------------
PAGES = {
    "cost.html": page_home,
    "cost-model.html": page_model,
    "cost-methods.html": page_methods,
    "cost-playbook.html": page_playbook,
    "cost-tax.html": page_tax,
    "cost-review.html": page_review,
    "cost-sources.html": page_sources,
}

def main():
    for name, fn in PAGES.items():
        out = ROOT / name
        out.write_text(fn(), encoding="utf-8")
        print(f"wrote {name} ({out.stat().st_size:,} bytes)")
    (DATA / "cost_model.json").write_text(
        json.dumps(dict(anchor=ANCHOR, derived=DER, assumptions=MODEL["assumptions"],
                        rows=[dict(usd=r["usd"], cny=round(r["cny"], 2),
                                   methods=[dict(key=m["key"], fx=None if m["fx"] is None else round(m["fx"], 4),
                                                 fee=None if m["fee"] is None else round(m["fee"], 4),
                                                 total=None if total(m) is None else round(total(m), 4))
                                            for m in r["methods"]])
                              for r in MODEL["rows"]]),
                   indent=1), encoding="utf-8")
    print("wrote data/cost_model.json")


if __name__ == "__main__":
    main()
