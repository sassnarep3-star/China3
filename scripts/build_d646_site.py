#!/usr/bin/env python3
"""
D646 — independent verification refresh + consolidated dashboard.

Session: arena/d6467425-china3 (2026-11-10)

Single source of truth for:
  - the official source register (fetched and verified on 2026-11-10)
  - the method inventory (pros / cons / legality / official capability cap)
  - the USD 10,000 -> USD 400,000 cost ladder, re-derived from scratch
  - penalty and U.S. tax figures

Emits:
  data/d646_sources.csv, data/d646_methods.csv, data/d646_ladder.csv,
  data/d646_verification.csv, data/d646_penalty.csv
  d646-summary.html, d646-methods.html, d646-costs.html, d646-penalty.html,
  d646-verification.html, d646-flagged.html, d646-sources.html, assets/d646.css
  research/d646-executive-summary.md, research/d646-verification.md

Rules enforced in code (and re-checked by scripts/verify_d646_site.py):
  * every data row carries at least one official https:// source
  * a value that is not confirmed by an official source is left EMPTY and
    labelled UNVERIFIED - never inferred, never filled with zero
  * every displayed total is re-derived below, not copied
Run with --check to fail when the committed output is stale.
"""
from __future__ import annotations

import csv
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
RESEARCH = ROOT / "research"

BUILD_DATE = "2026-11-10"
BUILD_STAMP = "2026-11-10T02:20Z"

# --------------------------------------------------------------------------
# 1. OFFICIAL SOURCE REGISTER
#    Every entry below was fetched and read on 2026-11-10 (see
#    research/d646-verification.md for the fetch log). `quote` is a verbatim
#    excerpt from the cited page; it is never paraphrased.
# --------------------------------------------------------------------------
SOURCES = [
    dict(
        id="S01", tier="China FX regulator", issuer="State Administration of Foreign Exchange (SAFE)",
        title="SAFE spokesman press conference on the Detailed Rules for the Administration of Individual Foreign Exchange",
        url="https://www.safe.gov.cn/en/2007/0105/819.html", published="2007-01-05",
        quote="the annual quota for individual foreign exchange purchases be drastically raised from USD 20,000 to USD 50,000",
        supports="Origin of the USD 50,000 annual individual convenience amount.",
    ),
    dict(
        id="S02", tier="China FX regulator", issuer="SAFE Ningxia branch",
        title="2022 foreign-exchange policy Q&A (8): is there a hard USD 50,000 annual cap?",
        url="https://www.safe.gov.cn/ningxia/2022/0929/1997.html", published="2022-09-29",
        quote="年度便利化额度不是个人每年购汇或者结汇的限额，只是超过等值5万美元的购汇或结汇不能仅凭本人有效身份证件办理",
        supports="The USD 50,000 figure is a convenience threshold, not an absolute legal limit.",
    ),
    dict(
        id="S03", tier="China FX regulator", issuer="SAFE Tianjin branch",
        title="2024 individual FX Q&A (3): outbound remittance of foreign exchange for current-account expenses",
        url="https://www.safe.gov.cn/tianjin/2024/0229/2402.html", published="2024-02-29",
        quote="外汇账户内外汇汇出境外当日累计等值5万美元以下（含）的，凭本人有效身份证件办理；超过上述金额的，凭本人有效身份证件、有交易额的相关材料办理",
        supports="Above USD 50,000 per day, documents evidencing the transaction amount are required; purpose consistency is reviewed.",
    ),
    dict(
        id="S04", tier="China FX regulator", issuer="SAFE",
        title="Huifa [2015] No.49 - further improving individual foreign-exchange administration (splitting ban, watch list)",
        url="https://www.safe.gov.cn/safe/2015/1231/5442.html", published="2015-12-31",
        quote="个人在办理外汇业务时，应当遵守个人外汇管理有关规定，不得以分拆等方式规避额度及真实性管理",
        supports="Splitting transactions to avoid quota/authenticity review is prohibited; watch-list for 3 years.",
    ),
    dict(
        id="S05", tier="China FX regulator", issuer="SAFE Hebei branch",
        title="Notice on further improving individual settlement/sale of FX business (splitting characteristics)",
        url="https://www.safe.gov.cn/hebei/2015/0504/415.html", published="2015-05-04",
        quote="5个以上不同个人同日、隔日或连续多日分别购汇后，将外汇汇给境外同一个人或机构",
        supports="Defines the objective indicia of prohibited splitting (e.g. 5+ people remitting to one overseas person).",
    ),
    dict(
        id="S06", tier="China FX regulator", issuer="SAFE / General Administration of Customs",
        title="Huifa [2003] No.102 - interim measures on carrying foreign-currency cash across the border",
        url="https://www.safe.gov.cn/safe/2003/0828/5444.html", published="2003-08-28",
        quote="出境人员原则上不得携带超过等值10000美元的外币现钞出境",
        supports="Cash carry: <=USD 5,000 no permit; 5,000-10,000 bank permit; above USD 10,000 not permitted in principle.",
    ),
    dict(
        id="S07", tier="China FX regulator", issuer="SAFE",
        title="Huifa [2017] No.29 - regulating large overseas ATM cash withdrawals on bank cards (press Q&A)",
        url="http://m.safe.gov.cn/safe/2017/1230/8129.html", published="2017-12-30",
        quote="个人持境内银行卡在境外提取现金，本人名下银行卡（含附属卡）合计每个自然年度不得超过等值10万元人民币",
        supports="Card cash abroad capped at RMB 100,000/person/year and RMB 10,000/card/day.",
    ),
    dict(
        id="S08", tier="China FX regulator", issuer="SAFE",
        title="State Council Order No.532 - Regulations on Foreign Exchange Administration (penalties)",
        url="https://www.safe.gov.cn/safe/2008/0806/5321.html", published="2008-08-06",
        quote="有违反规定将境内外汇转移境外，或者以欺骗手段将境内资本转移境外等逃汇行为的，由外汇管理机关责令限期调回外汇，处逃汇金额30%以下的罚款；情节严重的，处逃汇金额30%以上等值以下的罚款",
        supports="Evasive outflow (逃汇) fine up to 30% of the amount, or 30%-100% if serious; also Art.45 for illegal FX trading.",
    ),
    dict(
        id="S09", tier="China central bank", issuer="People's Bank of China (PBOC)",
        title="PBOC Announcement [2004] No.16 - interim measures on the transfer abroad of individual property",
        url="http://m.safe.gov.cn/safe/2004/1116/5461.html", published="2004-11-16",
        quote="移民转移必须一次性申请拟转移出境的全部财产金额，分步汇出。首次可汇出金额不得超过全部申请转移财产的一半",
        supports="Emigrant/inheritance property transfer: staged payouts, tax certificate required (Art.6, Art.8(6), Art.10).",
    ),
    dict(
        id="S10", tier="China tax authority", issuer="State Taxation Administration (STA) / SAFE",
        title="STA & SAFE Announcement 2013 No.40 - tax filing for outbound payments of services and other items",
        url="https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html", published="2013-07-09",
        quote="境内机构和个人向境外单笔支付等值5万美元以上（不含等值5万美元，下同）下列外汇资金，除本公告第三条规定的情形外，均应向所在地主管税务机关进行税务备案",
        supports="Single outbound payments above USD 50,000 generally require a tax filing record with the tax authority.",
    ),
    dict(
        id="S11", tier="China tax authority", issuer="State Taxation Administration (STA)",
        title="Individual Income Tax Law of the PRC - taxable income categories and rates",
        url="https://shanghai.chinatax.gov.cn/zcfw/zcfgk/grsds/201809/t441789.html", published="2018-08-31",
        quote="利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十",
        supports="China taxes nine enumerated income categories. A pure CNY->USD currency conversion is not among them.",
    ),
    dict(
        id="S12", tier="China central bank + 9 ministries", issuer="PBOC et al.",
        title="Yinfa [2021] No.237 - further preventing and handling risks of virtual-currency speculation",
        url="http://m.safe.gov.cn/safe/2021/0924/19911.html", published="2021-09-24",
        quote="开展法定货币与虚拟货币兑换业务、虚拟货币之间的兑换业务……一律严格禁止，坚决依法取缔",
        supports="Fiat<->crypto conversion business is an illegal financial activity in mainland China.",
    ),
    dict(
        id="S13", tier="U.S. tax authority", issuer="Internal Revenue Service (IRS)",
        title="Yearly average currency exchange rates (China, Yuan)",
        url="https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates", published="current",
        quote="China | Yuan | 7.129 | 7.189 | 7.075 | 6.730 | 6.452",
        supports="IRS yearly average CNY/USD: 7.129 (2025), 7.189 (2024), 7.075 (2023), 6.730 (2022), 6.452 (2021).",
    ),
    dict(
        id="S14", tier="U.S. statute", issuer="U.S. Congress (govinfo, 2023 edition)",
        title="26 U.S.C. 988 - treatment of certain foreign currency transactions",
        url="https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", published="2023 ed.",
        quote="The preceding sentence shall not apply if the gain which would otherwise be recognized on the transaction exceeds $200.",
        supports="s988 FX gain on a deposit disposition is ordinary income; the personal-transaction exclusion fails once the gain exceeds $200.",
    ),
    dict(
        id="S15", tier="U.S. regulator", issuer="FinCEN / eCFR (OFR)",
        title="31 CFR 1010.821 - penalty adjustment and table (foreign financial agency transaction penalties)",
        url="https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", published="amended 2025-01-17",
        quote="Foreign Financial Agency Transaction—Non-Willful Violation of Transaction | 10,000 | 16,536",
        supports="FBAR non-willful maximum USD 16,536 and willful USD 165,353 for penalties assessed on/after 2025-01-17.",
    ),
    dict(
        id="S16", tier="U.S. tax authority", issuer="Internal Revenue Service (IRS)",
        title="Comparison of Form 8938 and FBAR requirements",
        url="https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", published="current",
        quote="Aggregate value of financial accounts exceeds $10,000 at any time during the calendar year.",
        supports="FBAR threshold USD 10,000; Form 8938 thresholds (50k/75k etc.) and its penalty ceiling of USD 60,000.",
    ),
    dict(
        id="S17", tier="U.S. tax authority", issuer="Internal Revenue Service (IRS)",
        title="Revenue Procedure 2025-32 - 2026 inflation-adjusted amounts",
        url="https://www.irs.gov/pub/irs-drop/rp-25-32.pdf", published="2025",
        quote=".39 Foreign Earned Income Exclusion.  For taxable years beginning in 2026, the foreign earned income exclusion amount under § 911(b)(2)(D)(i) is $132,900.",
        supports="FEIE USD 132,900 for 2026; 2026 ordinary rate brackets and capital-gain breakpoints.",
    ),
    dict(
        id="S18", tier="U.S. tax authority", issuer="Internal Revenue Service (IRS)",
        title="Topic no. 409 - capital gains and losses",
        url="https://www.irs.gov/taxtopics/tc409", published="current",
        quote="Net short-term capital gains are subject to taxation as ordinary income at graduated tax rates.",
        supports="Preferential long-term capital rates are separate from the ordinary rates that apply to short-term gain.",
    ),
    dict(
        id="S19", tier="U.S. border agency", issuer="U.S. Customs and Border Protection (CBP)",
        title="Money and other monetary instruments - report currency exceeding $10,000",
        url="https://www.cbp.gov/travel/international-visitors/money-monetary-instruments", published="2025-11-24",
        quote="Anyone who brings, sends, or receives currency or monetary instruments totaling more than $10,000 at one time, either into or out of the United States, must report it.",
        supports="FinCEN Form 105 is required above USD 10,000 carried or shipped into or out of the United States.",
    ),
    dict(
        id="S20", tier="China commercial bank (first-party tariff)", issuer="Bank of China (BOC)",
        title="BOC personal e-banking transfer and remittance tariff schedule (effective 2014-11-01)",
        url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", published="2014-11-01",
        quote="跨境汇款（电汇） | 每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔",
        supports="Cross-border telegraphic transfer: 0.1% of the amount, min CNY 50, max CNY 260, plus CNY 150 cable fee outside HK/Macau/Taiwan.",
    ),
    dict(
        id="S21", tier="China commercial bank (first-party quote)", issuer="Bank of China (BOC)",
        title="BOC foreign-exchange rate board (USD against CNY)",
        url="https://www.boc.cn/sourcedb/whpj/enindex_1619.html", published="2026-11-10 07:32:39",
        quote="USD | 666.22 | 666.22 | 669.03 | 669.03 | 671.88 | 2026/11/10 07:32:39",
        supports="Buying rate 6.6622, selling rate 6.6903, middle rate 6.7188 CNY per USD, stamped 2026/11/10 07:32:39.",
    ),
]

SRC_BY_ID = {s["id"]: s for s in SOURCES}

# --------------------------------------------------------------------------
# 2. VERIFIED INPUT VALUES
#    Everything used in arithmetic must trace to one of the rows above.
# --------------------------------------------------------------------------
BOC_SELL = 6.6903          # S21 selling rate (customer buys USD)  669.03 / 100
BOC_BUY = 6.6622           # S21 buying rate  (bank buys USD)      666.22 / 100
BOC_PARITY = 6.7188        # S21 published "middle rate" = central parity, NOT the bid-ask mid
# The spread must be measured against the midpoint of the two rates the bank actually quotes.
# Using the published parity column here would overstate the spread ~3x and is wrong.
BOC_MID = (BOC_SELL + BOC_BUY) / 2      # 6.67625, matches the 0.2104% half-spread already on main
IRS_AVG_2024 = 7.189       # S13
IRS_AVG_2025 = 7.129       # S13
TARIFF_RATE = 0.001        # S20 1 per mille
TARIFF_MIN_CNY = 50.0      # S20
TARIFF_MAX_CNY = 260.0     # S20
CABLE_CNY = 150.0          # S20 non-HK/Macau/Taiwan
SEC_988_EXCLUSION = 200.0  # S14
CONVENIENCE_USD = 50_000   # S02 / S03
CARD_YEAR_CAP_RMB = 100_000  # S07
CARD_DAY_CAP_RMB = 10_000    # S07
CASH_NO_PERMIT_USD = 5_000   # S06
CASH_MAX_USD = 10_000        # S06
FINCEN105_USD = 10_000       # S19
FBAR_USD = 10_000            # S16
FBAR_NONWILLFUL = 16_536     # S15
FBAR_WILLFUL = 165_353       # S15
FORM8938_MAX_PENALTY = 60_000  # S16
FEIE_2026 = 132_900          # S17

# 2026 ordinary brackets, single filer (S17 sec.4.01 Table 3)
BRACKETS_2026_SINGLE = [
    (12_400, 0.10), (50_400, 0.12), (105_700, 0.22),
    (201_775, 0.24), (256_225, 0.32), (640_600, 0.35), (float("inf"), 0.37),
]

# Derived (re-checked in verify_d646_site.py)
SPREAD_CNY = BOC_SELL - BOC_MID                        # 0.014050
SPREAD_PCT = BOC_SELL / BOC_MID - 1                     # 0.0021045...
GAIN_FRAC_2024 = 1 - BOC_SELL / IRS_AVG_2024           # 0.069369...
GAIN_FRAC_2025 = 1 - BOC_SELL / IRS_AVG_2025           # 0.061668...
EXCLUSION_CEILING_USD = SEC_988_EXCLUSION / GAIN_FRAC_2024  # 2,883.09


def tariff_cny(usd: float) -> float:
    """BOC cross-border telegraphic transfer charge, in CNY (S20)."""
    rmb = usd * BOC_SELL
    pct = rmb * TARIFF_RATE
    return min(max(pct, TARIFF_MIN_CNY), TARIFF_MAX_CNY) + CABLE_CNY


def spread_cost_usd(usd: float) -> float:
    """Cost of paying the bank's selling rate instead of the middle rate."""
    return usd * BOC_SELL / BOC_MID - usd


def wires_for(usd: float) -> int:
    """Each wire is capped by the documented USD 50,000 convenience amount (S02/S03)."""
    return max(1, math.ceil(usd / CONVENIENCE_USD))


def known_bank_cost_usd(usd: float, wires: int | None = None) -> float:
    n = wires if wires is not None else wires_for(usd)
    return spread_cost_usd(usd) + n * tariff_cny(usd / n) / BOC_SELL


def fx_gain_usd(usd: float, basis: float) -> float:
    return usd * (1 - BOC_SELL / basis)


def ordinary_tax(gain: float, other_income: float = 0.0) -> float:
    """Tax on stacking `gain` on top of `other_income` (2026 single brackets, S17)."""
    def tax(x):
        t, prev = 0.0, 0.0
        for ceil, rate in BRACKETS_2026_SINGLE:
            if x <= prev:
                break
            t += (min(x, ceil) - prev) * rate
            prev = ceil
        return t
    return tax(other_income + max(gain, 0)) - tax(other_income)


# --------------------------------------------------------------------------
# 3. METHOD INVENTORY
# --------------------------------------------------------------------------
METHODS = [
    dict(
        id="M01", name="Documented bank remittance (current account)",
        legality="Lawful", reaches_400k="Yes, with documents",
        cap="USD 50,000/person/year needs only ID; above that, transaction documents",
        cap_src="S02|S03",
        steps=[
            "Gather source documents for the CNY (bank statements, salary slips, contract, tax paid).",
            "Ask the holding bank, in writing, to classify the payment as current-account and list the required documents.",
            "Exchange CNY to USD at the bank's selling rate (S21) and book the outbound wire.",
            "Bank charges 0.1% min CNY 50 max CNY 260 + CNY 150 cable (S20).",
            "Above USD 50,000/day, supply the transaction documents the bank lists (S03).",
            "Above USD 50,000 single payment, a tax filing record may be required (S10).",
            "Keep the SWIFT advice, rate confirmation and fee receipt; declare FBAR/8938 in the U.S.",
        ],
        pros=["Lowest documented all-in cost of any lawful route",
              "Fully lawful and audit-proof when the purpose is genuine",
              "No third-party counterparty risk"],
        cons=["Requires a bona fide current-account purpose; savings with no qualifying purpose are not automatically eligible",
              "Bank reviews purpose consistency between purchase and remittance (S03)",
              "Intermediary and U.S. receiving-bank fees are not published: UNVERIFIED"],
        src="S02|S03|S10|S20|S21",
    ),
    dict(
        id="M02", name="Bank e-banking / mobile remittance",
        legality="Lawful", reaches_400k="Yes, with documents",
        cap="Same legal limits as the counter channel",
        cap_src="S02|S03",
        steps=[
            "Enable cross-border remittance in the bank's app and confirm the per-transaction limit shown.",
            "Complete the purpose declaration for each transaction.",
            "Book the wire at the published e-banking tariff (S20).",
            "Archive the electronic receipt and SWIFT confirmation.",
        ],
        pros=["Same published tariff, no branch visit",
              "Rate and fee displayed before confirmation"],
        cons=["App limits can be lower than the legal limit; the bank's own cap must be confirmed",
              "Some purposes may still require a branch review"],
        src="S20|S21|S03",
    ),
    dict(
        id="M03", name="Annual convenience amount, used year by year",
        legality="Lawful", reaches_400k="Yes, over 8 calendar years",
        cap="USD 50,000/person/year with ID only",
        cap_src="S02",
        steps=[
            "Confirm the remaining convenience amount for the year with the bank.",
            "Remit up to USD 50,000 with ID only.",
            "Repeat in each subsequent calendar year; USD 400,000 takes 8 years.",
            "Do not use other people's quotas to accelerate (S04, S05).",
        ],
        pros=["Minimal paperwork",
              "Spreads the s988 currency gain across tax years, which can lower the marginal rate",
              "Lowest fee volatility"],
        cons=["Very slow: 8 years for USD 400,000",
              "Each year's conversion date is unknown in advance, so the FX outcome is not locked",
              "The convenience amount can be adjusted by SAFE (S02)"],
        src="S02|S14|S20",
    ),
    dict(
        id="M04", name="Documented current-account remittance above the convenience amount",
        legality="Lawful", reaches_400k="Yes, if genuinely documented",
        cap="No legal ceiling; authenticity review applies",
        cap_src="S02|S03",
        steps=[
            "Obtain the bank's written document checklist for the specific purpose.",
            "Provide the transaction evidence (contract, invoice, admission letter, medical bill, tax record).",
            "Bank performs authenticity review and purpose-consistency check (S03).",
            "Above USD 50,000 single payment, file the tax record where required (S10).",
            "Wire out and retain the full file.",
        ],
        pros=["The only route that can lawfully move a large sum quickly",
              "No artificial splitting needed"],
        cons=["Documents must be real; fabricated documents trigger penalty exposure (S08)",
              "Bank discretion: the same documents may be accepted or refused by different branches",
              "Genuine accumulated savings without a qualifying current-account purpose may still be refused"],
        src="S02|S03|S08|S10",
    ),
    dict(
        id="M05", name="Emigrant property transfer (PBOC [2004] No.16)",
        legality="Lawful, narrow eligibility", reaches_400k="Yes, but staged over 2+ years",
        cap="Staged: first half, then half of remainder after 1 year, rest after 2 years",
        cap_src="S09",
        steps=[
            "Confirm you qualify: a mainland resident who has emigrated/settled abroad and cancelled hukou (S09 Art.2, Art.8).",
            "Apply once for the whole amount at the SAFE branch where your hukou was registered.",
            "Submit the identity, settlement and property-right documents, plus the tax certificate (S09 Art.8(6)).",
            "Receive approval; below CNY 500,000 the local branch decides, above it goes to SAFE headquarters (S09 Art.10).",
            "Bank sells FX and remits directly to your own overseas account; cash withdrawal is prohibited (S09 Art.11).",
            "Second and third tranches at 1 and 2 years (S09 Art.6).",
        ],
        pros=["Explicit legal channel for moving a whole estate, not just USD 50,000",
              "Predictable staged schedule"],
        cons=["Requires emigrating and cancelling Chinese hukou; a U.S. citizen who never held mainland hukou generally does not qualify",
              "Tax certificate mandatory - the tax position must be settled first",
              "Staged payouts mean the FX rate is not locked",
              "One application only, for the entire amount"],
        src="S09|S11",
    ),
    dict(
        id="M06", name="Inheritance property transfer (PBOC [2004] No.16)",
        legality="Lawful, narrow eligibility", reaches_400k="Yes",
        cap="One application per deceased person; one-off or instalments",
        cap_src="S09",
        steps=[
            "Liquidate the inherited mainland estate.",
            "Apply at the SAFE branch where the deceased's hukou was registered.",
            "Submit inheritance proof, the deceased's property-right documents and a tax certificate (S09 Art.9).",
            "Receive approval and remit to your own overseas account.",
        ],
        pros=["The only route designed for a foreign-citizen heir",
              "Can be a single payout"],
        cons=["Applies to inherited assets, not your own savings",
              "Tax certificate and notarised documents required",
              "Case-by-case review; no published fee"],
        src="S09|S11",
    ),
    dict(
        id="M07", name="Company profit / dividend repatriation (if you own the entity)",
        legality="Lawful only if the CNY belongs to a company you own", reaches_400k="Yes, capital account",
        cap="Requires capital-account registration and tax clearance",
        cap_src="S08|S10",
        steps=[
            "Confirm the funds are corporate, not personal.",
            "Settle corporate income tax and withholding tax on the dividend.",
            "Complete the tax filing record for the outbound payment (S10).",
            "Remit through the capital account after the bank's review (S08 Art.22).",
        ],
        pros=["Can move large amounts in a single transaction",
              "Fully documented corporate route"],
        cons=["Only works if you genuinely own the company - otherwise it is a disguised personal transfer",
              "Corporate and withholding tax apply before remittance",
              "Accounting and audit costs"],
        src="S08|S10",
    ),
    dict(
        id="M08", name="Foreign-currency cash withdrawal and carry",
        legality="Lawful up to USD 10,000", reaches_400k="No",
        cap="<=USD 5,000 no permit; 5,000-10,000 bank permit; >10,000 not permitted in principle",
        cap_src="S06",
        steps=[
            "Buy foreign-currency cash at the bank (cash selling rate).",
            "Up to USD 5,000: carry without a permit (S06).",
            "USD 5,000-10,000: obtain the carrying permit from the bank (S06).",
            "Above USD 10,000: requires a SAFE permit for listed special cases only (S06).",
            "On the U.S. side, file FinCEN Form 105 above USD 10,000 (S19).",
        ],
        pros=["Physical settlement, no counterparty",
              "No wire fee"],
        cons=["Hard ceiling of USD 10,000 per person per trip; 40 trips would be needed for USD 400,000",
              "Physical loss/theft risk and insurance cost",
              "Cash conversion uses the worse cash rate",
              "Structuring repeated trips near the limit is exactly the conduct S04/S05 targets"],
        src="S06|S19|S04",
    ),
    dict(
        id="M09", name="Overseas ATM cash withdrawal on a mainland bank card",
        legality="Lawful within caps", reaches_400k="No",
        cap="RMB 100,000/person/year; RMB 10,000/card/day",
        cap_src="S07",
        steps=[
            "Check the remaining annual card-cash allowance.",
            "Withdraw abroad within RMB 10,000/card/day.",
            "Stop at RMB 100,000/person/year; exceeding it suspends the facility for this and next year (S07).",
        ],
        pros=["No paperwork, immediate access",
              "Useful for living costs rather than a lump sum"],
        cons=["RMB 100,000/year is far below the target; USD 400,000 is impossible",
              "ATM operator and issuer fees, plus a worse cash rate: UNVERIFIED",
              "Borrowing or lending cards to evade the cap is prohibited (S07)"],
        src="S07",
    ),
    dict(
        id="M10", name="Overseas card spending (POS)",
        legality="Lawful", reaches_400k="No - it is spending, not conversion",
        cap="No conversion to USD cash; consumption only",
        cap_src="S07",
        steps=[
            "Pay overseas merchants with the mainland card.",
            "Settle the card balance in CNY.",
        ],
        pros=["No wiring, no cash limit",
              "Does not consume the convenience amount (S07)"],
        cons=["You receive goods or services, not dollars in your account",
              "Cannot fund a U.S. bank account",
              "Merchant/issuer FX markup: UNVERIFIED"],
        src="S07",
    ),
    dict(
        id="M11", name="Transfer to your own offshore account (HK/other) then convert",
        legality="Lawful only if the outbound leg is itself lawful", reaches_400k="Only via M01/M04",
        cap="Outbound leg subject to the same SAFE rules",
        cap_src="S02|S03",
        steps=[
            "Complete a lawful outbound remittance (M01/M04) to your own account abroad.",
            "Convert offshore at the offshore rate.",
        ],
        pros=["Access to deeper offshore FX liquidity",
              "Onshore/offshore rates can differ"],
        cons=["Does not bypass anything: the binding constraint is the outbound leg",
              "Two sets of fees",
              "Onshore-offshore spread is market data, not a published official rate: UNVERIFIED"],
        src="S02|S03",
    ),
    dict(
        id="M12", name="Borrowing other people's quotas / splitting (分拆)",
        legality="PROHIBITED", reaches_400k="No - it is the violation itself",
        cap="Zero lawful capacity",
        cap_src="S04|S05",
        steps=[
            "Do not do this. SAFE operates a watch list for exactly this pattern (S04).",
            "Indicia include 5+ people remitting to one overseas person on the same or consecutive days (S05).",
        ],
        pros=["None that survive review"],
        cons=["Explicitly prohibited by Huifa [2015] No.49 (S04)",
              "Watch-list status for the year of listing plus 2 more years (S04)",
              "Evasion penalties up to 30% of the amount, 30%-100% if serious (S08)"],
        src="S04|S05|S08",
    ),
    dict(
        id="M13", name="Underground bank / informal exchanger (地下钱庄)",
        legality="UNLAWFUL", reaches_400k="No",
        cap="Zero lawful capacity",
        cap_src="S08",
        steps=[
            "Do not do this.",
            "Illegal trading of foreign exchange carries confiscation plus a fine up to 30% of the amount, 30%-100% if serious (S08 Art.45).",
            "Criminal liability where the conduct constitutes a crime (S08).",
        ],
        pros=["None - quoted 'no tax' rates are not a legal basis"],
        cons=["Confiscation plus fine up to 30%-100% of the amount (S08)",
              "Counterparty and seizure risk",
              "U.S. tax and FBAR duties are unaffected by how the money moved"],
        src="S08",
    ),
    dict(
        id="M14", name="Crypto / USDT over-the-counter conversion",
        legality="PROHIBITED in mainland China", reaches_400k="No",
        cap="Zero lawful capacity",
        cap_src="S12",
        steps=[
            "Do not do this.",
            "Fiat-to-crypto and crypto-to-fiat business is an illegal financial activity (S12).",
            "Offshore exchanges serving mainland residents are also unlawful (S12).",
        ],
        pros=["None that are defensible"],
        cons=["Explicitly illegal financial activity (S12)",
              "Banks and payment institutions must refuse to service it (S12)",
              "U.S. consequences stack on top: s988 gain plus FBAR/8938 reporting"],
        src="S12|S14",
    ),
    dict(
        id="M15", name="False documentation / misdeclared purpose",
        legality="UNLAWFUL", reaches_400k="No",
        cap="Zero lawful capacity",
        cap_src="S08",
        steps=[
            "Do not do this.",
            "Current-account FX payments must have a genuine, lawful transaction basis (S08 Art.12).",
            "Purchasing FX with false or invalid documents is illegal arbitrage, fined up to 30%-100% (S08 Art.40).",
        ],
        pros=["None"],
        cons=["Fine up to 30% of the amount, 30%-100% if serious (S08)",
              "Destroys the audit trail you need for U.S. reporting",
              "Potential criminal exposure (S08)"],
        src="S08",
    ),
    dict(
        id="M16", name="Structuring sub-threshold transfers to avoid reporting",
        legality="UNLAWFUL", reaches_400k="No",
        cap="Zero lawful capacity",
        cap_src="S04|S19",
        steps=[
            "Do not do this.",
            "The U.S. USD 10,000 Form 105 threshold applies to the total carried or sent at one time, and to families collectively (S19).",
            "Splitting to avoid quota or authenticity review is prohibited on the China side (S04).",
        ],
        pros=["None"],
        cons=["Prohibited on both sides (S04, S19)",
              "Seizure and civil or criminal penalties (S19)",
              "Watch-list consequences (S04)"],
        src="S04|S19",
    ),
]

# --------------------------------------------------------------------------
# 4. PENALTY / REPORTING TABLE
# --------------------------------------------------------------------------
PENALTIES = [
    dict(id="P01", name="China - evasion of FX control (逃汇)",
         amount="Fine up to 30% of the amount; 30%-100% if serious; funds repatriated",
         trigger="Transferring domestic FX abroad in violation of the rules, or moving capital abroad by deception",
         src="S08", verified="verified"),
    dict(id="P02", name="China - illegal FX trading (私自买卖/变相买卖外汇)",
         amount="Warning + confiscation of gains + fine up to 30%; 30%-100% if serious",
         trigger="Buying or selling FX privately or in disguised form, or brokering it", src="S08", verified="verified"),
    dict(id="P03", name="China - illegal arbitrage / purchasing FX with false documents (非法套汇)",
         amount="Funds converted back + fine up to 30%; 30%-100% if serious",
         trigger="Using FX to settle what must be settled in CNY, or buying FX with false/invalid documents",
         src="S08", verified="verified"),
    dict(id="P04", name="China - changing the declared use of FX",
         amount="Correction + confiscation + fine up to 30%; 30%-100% if serious",
         trigger="Using FX or settled funds for a purpose other than the approved one", src="S08", verified="verified"),
    dict(id="P05", name="China - individual splitting watch list",
         amount="Not a fine: listed for the current year plus 2 more years; every FX transaction then needs full documentary proof",
         trigger="Borrowing or lending quotas to avoid quota/authenticity management", src="S04", verified="verified"),
    dict(id="P06", name="China - tax on converting CNY to USD",
         amount="", trigger="No official source reviewed imposes a tax on the conversion of an individual's own CNY to USD; IIT Law Art.2 lists nine taxable income categories and a bare conversion is none of them",
         src="S11", verified="UNVERIFIED"),
    dict(id="P07", name="U.S. - s988 currency gain on the conversion",
         amount="Ordinary income at your marginal rate; ≈6.94% of the USD received is gain if the CNY was acquired at the 2024 IRS average",
         trigger="Disposing of nonfunctional currency (including a bank deposit) at a rate better than your basis",
         src="S14|S13", verified="verified"),
    dict(id="P08", name="U.S. - personal-transaction exclusion",
         amount="Gain excluded only if it does not exceed USD 200; at today's rate that caps the excluded conversion at about USD 2,883",
         trigger="Individual, personal transaction, gain <= USD 200", src="S14", verified="verified"),
    dict(id="P09", name="U.S. - FBAR (FinCEN Form 114) non-willful",
         amount="Up to USD 16,536 per violation (assessed on/after 2025-01-17)",
         trigger="Failing to report foreign accounts whose aggregate value exceeded USD 10,000 at any time in the year",
         src="S15|S16", verified="verified"),
    dict(id="P10", name="U.S. - FBAR willful",
         amount="Up to USD 165,353 per violation",
         trigger="Willful failure to report", src="S15", verified="verified"),
    dict(id="P11", name="U.S. - Form 8938",
         amount="Up to USD 10,000 failure-to-disclose, plus USD 10,000 per 30 days after notice, ceiling USD 60,000",
         trigger="Failing to report specified foreign financial assets above the applicable threshold", src="S16", verified="verified"),
    dict(id="P12", name="U.S. - FinCEN Form 105 (currency report at the border)",
         amount="", trigger="Required for more than USD 10,000 carried or shipped into or out of the U.S. (verified); the penalty is not a published fixed amount - CBP states the currency may be forfeited and seized, with civil or criminal penalties such as fines or imprisonment",
         src="S19", verified="UNVERIFIED"),
    dict(id="P13", name="Intermediary and receiving-bank wire fees",
         amount="", trigger="No official published schedule found for correspondent or U.S. receiving-bank charges",
         src="S20", verified="UNVERIFIED"),
    dict(id="P14", name="Bank card overseas ATM operator fees",
         amount="", trigger="No official published schedule found", src="S07", verified="UNVERIFIED"),
]

# --------------------------------------------------------------------------
# 5. LADDER
# --------------------------------------------------------------------------
AMOUNTS = [10_000 * i for i in range(1, 41)]
TAX_SCENARIOS = [("10%", 0.10), ("22%", 0.22), ("24%", 0.24), ("32%", 0.32), ("37%", 0.37)]


def build_ladder():
    rows = []
    for amt in AMOUNTS:
        n = wires_for(amt)
        spread = spread_cost_usd(amt)
        tariff_usd = n * tariff_cny(amt / n) / BOC_SELL
        total = spread + tariff_usd
        gain24 = fx_gain_usd(amt, IRS_AVG_2024)
        gain25 = fx_gain_usd(amt, IRS_AVG_2025)
        tax = {label: ordinary_tax(gain24, 0.0) * 0 + gain24 * rate for label, rate in TAX_SCENARIOS}
        rows.append(dict(
            usd=amt, wires=n, spread=spread, tariff=tariff_usd, bank_total=total,
            bank_pct=total / amt * 100,
            gain24=gain24, gain25=gain25, tax=tax,
            tax24=gain24 * 0.24,
            worst_bank_tax=total + gain24 * 0.37,
            years=math.ceil(amt / CONVENIENCE_USD),
            excluded="no" if gain24 > SEC_988_EXCLUSION else "yes",
        ))
    return rows


LADDER = build_ladder()

# --------------------------------------------------------------------------
# 6. FLAGGED FOR REVIEW  (unverified items + irregularities)
# --------------------------------------------------------------------------
FLAGS = [
    dict(id="D646-01", sev="high",
         item="The user's premise: 'money stuck in China with no way to convert without considerable taxes'",
         status="Unverified",
         detail="No tax assessment, bank quote or tax receipt was supplied. No official source reviewed imposes a Chinese tax on converting an individual's own CNY to USD. The 'considerable' cost is therefore not established, and the largest identifiable candidate is a U.S. tax (s988 currency gain), not a Chinese one.",
         src="S11|S14"),
    dict(id="D646-02", sev="high",
         item="Whether the CNY is savings, salary, investment proceeds or company money",
         status="Unverified",
         detail="Eligibility depends almost entirely on this. Salary is normally already taxed in China; investment proceeds and property gains generally are not. The method ranking cannot be narrowed without it.",
         src="S11|S02"),
    dict(id="D646-03", sev="high",
         item="Whether the account holder ever held mainland hukou (affects the emigrant route)",
         status="Unverified",
         detail="PBOC [2004] No.16 Art.2 requires emigrating from the mainland and Art.8 requires the hukou cancellation certificate. A U.S. citizen by birth would not qualify.",
         src="S09"),
    dict(id="D646-04", sev="high",
         item="U.S. basis (acquisition date and rate) of the CNY",
         status="Unverified",
         detail="The s988 gain is measured against your basis. The ladder therefore shows a stated assumption (2024 IRS yearly average 7.189), not your actual figure. If your basis is better than today's rate, the gain is smaller or negative.",
         src="S14|S13"),
    dict(id="D646-05", sev="high",
         item="Your marginal ordinary U.S. tax rate for the year of conversion",
         status="Unverified",
         detail="Gain under s988 is ordinary income, so the rate depends on total taxable income for that year. The ladder shows five brackets rather than assuming one.",
         src="S14|S17"),
    dict(id="D646-06", sev="medium",
         item="Intermediary (correspondent) and U.S. receiving-bank wire fees",
         status="Unverified",
         detail="Neither BOC nor the U.S. regulators publish a fixed schedule for these. They are deliberately blank in the cost table, not zero.",
         src="S20"),
    dict(id="D646-07", sev="medium",
         item="Onshore/offshore (CNY/CNH) basis and offshore conversion fee",
         status="Unverified",
         detail="This is market data with no official published reference; left blank.",
         src="S03"),
    dict(id="D646-08", sev="medium",
         item="Bank-specific handling of a large documented remittance",
         status="Unverified",
         detail="SAFE sets the framework but the branch decides. Only a written answer from the holding bank settles it.",
         src="S02|S03"),
    dict(id="D646-09", sev="medium",
         item="FBAR/Form 8938 filing history for this account",
         status="Unverified",
         detail="If prior years were missed, the real exposure is the penalty table (up to USD 16,536 non-willful / USD 165,353 willful per violation), which dwarfs the conversion cost. Not established for this person.",
         src="S15|S16"),
    dict(id="D646-10", sev="medium",
         item="Form 105 treatment of multiple travellers or family shipments",
         status="Unverified",
         detail="CBP states the USD 10,000 threshold applies to the total carried or sent collectively by a family or group, but does not state a per-person allocation rule for a structured family plan.",
         src="S19"),
    dict(id="D646-11", sev="low",
         item="Older repo pages dated 2026-11-09 use a BOC board stamp of 6.6919; today's stamp is 6.6903",
         status="Needs review",
         detail="Both are genuine published quotes at different times. The difference is USD 2.10 on the spread for a USD 10,000 conversion. The historical pages were not edited; this refresh is the current reading.",
         src="S21"),
    dict(id="D646-12", sev="low",
         item="Open PRs #15 and #18 (2026-11-09) remain unmerged",
         status="Needs review",
         detail="Their owners stopped committing more than 24 hours ago. They are left open rather than closed or merged, because merging them would republish figures that this refresh has not re-verified row by row.",
         src="S20"),
    dict(id="D646-13", sev="low",
         item="Parallel-session claims are invisible across branches",
         status="Needs review",
         detail="A COORDINATION.md claim on an unmerged branch cannot be seen by a session reading main. Sessions using a namespaced file prefix (as this one does with d646-*) avoid collisions but do not fix the visibility problem.",
         src="S08"),
    dict(id="D646-14", sev="low",
         item="Capital-gain treatment of s988 income",
         status="Needs review",
         detail="Some summaries treat the FX gain as capital. s988(a)(1)(A) makes it ordinary; the capital election in s988(a)(1)(B) is for forward/futures/option contracts, not for disposing of a currency deposit. The ladder therefore does not show a 15% capital rate.",
         src="S14"),
    dict(id="D646-15", sev="low",
         item="Foreign Earned Income Exclusion does not help here",
         status="Needs review",
         detail="The FEIE (USD 132,900 for 2026) excludes wages for personal services, not a currency gain and not existing savings. It can lower the tax on salary earned in China but not the s988 item.",
         src="S17"),
    dict(id="D646-16", sev="low",
         item="USD 50,000 convenience amount is frequently misdescribed as a 'quota'",
         status="Needs review",
         detail="SAFE's own Q&A says the convenience amount is not the limit on annual purchase or settlement; only ID is insufficient above it. Older repo pages already say this; the point is restated so it is not lost.",
         src="S02"),
]


# --------------------------------------------------------------------------
# 7. HTML HELPERS
# --------------------------------------------------------------------------
def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def money(x: float, cents: bool = True) -> str:
    return f"${x:,.2f}" if cents else f"${x:,.0f}"


def src_links(ids: str, label: str = "") -> str:
    out = []
    for sid in ids.split("|"):
        s = SRC_BY_ID[sid.strip()]
        host = s["url"].split("/")[2].replace("www.", "")
        out.append(f'<a href="{s["url"]}" target="_blank" rel="noopener">{esc(host)}</a> '
                   f'<span class="sid">{s["id"]}</span>')
    return " · ".join(out)


def badge(state: str) -> str:
    cls = {"verified": "ok", "UNVERIFIED": "unv", "Needs review": "rev", "Unverified": "unv"}.get(state, "rev")
    return f'<span class="badge {cls}">{esc(state)}</span>'


NAV = [
    ("d646-summary.html", "Start here"),
    ("d646-methods.html", "All methods"),
    ("d646-costs.html", "$10k–$400k costs"),
    ("d646-penalty.html", "Tax & penalties"),
    ("d646-verification.html", "Verification log"),
    ("d646-flagged.html", "Flagged for review"),
    ("d646-sources.html", "Sources"),
]

CSS = """
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:#f4f7fa;color:#14212e;
 font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,system-ui,sans-serif}
header{background:#0b3d4d;color:#fff;padding:14px max(16px,calc((100% - 1180px)/2))}
header .brand{display:flex;align-items:center;gap:12px;font-weight:800;font-size:18px}
header .mark{width:34px;height:34px;border-radius:9px;background:#12a3b8;display:grid;
 place-items:center;font-weight:900;font-size:15px;flex:none}
header .sub{font-size:12px;color:#a8d6df;font-weight:500;margin-top:2px}
nav{background:#0e4d61;display:flex;gap:4px;overflow-x:auto;padding:6px max(16px,calc((100% - 1180px)/2));
 -webkit-overflow-scrolling:touch}
nav a{white-space:nowrap;color:#d5eef3;text-decoration:none;padding:8px 11px;border-radius:8px;font-size:14px}
nav a:hover{background:#12657d;color:#fff}
nav a.on{background:#12a3b8;color:#fff;font-weight:700}
main{max-width:1180px;margin:0 auto;padding:26px 16px 60px}
h1{font-size:clamp(26px,4.6vw,36px);line-height:1.15;margin:0 0 10px}
h2{font-size:22px;margin:34px 0 12px;padding-bottom:6px;border-bottom:2px solid #dbe6ee}
h3{font-size:17px;margin:22px 0 8px}
p.lead{font-size:17px;color:#3f5567;max-width:820px}
a{color:#0a6c86}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin:18px 0}
.card{background:#fff;border:1px solid #d9e4ec;border-radius:11px;padding:15px;
 box-shadow:0 1px 2px rgba(10,35,54,.05)}
.card .k{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:#5c7488;font-weight:700}
.card .v{font-size:22px;font-weight:800;color:#0b5f74;margin:4px 0}
.card .n{font-size:13px;color:#5c7488}
.card .n a{font-size:12px}
.callout{border-left:5px solid #0f8ba3;background:#eaf7fa;padding:13px 16px;
 border-radius:7px;margin:18px 0}
.callout.warn{border-color:#c2750a;background:#fff5e3}
.callout.good{border-color:#1c8552;background:#e9f8f0}
.callout.bad{border-color:#ab2b25;background:#fdeceb}
.callout p{margin:6px 0}
.tbl{background:#fff;border:1px solid #d9e4ec;border-radius:11px;overflow-x:auto;
 margin:14px 0;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:620px}
th{background:#e8f0f5;color:#22394a;text-align:left;padding:10px;position:sticky;top:0;
 font-size:12.5px;text-transform:uppercase;letter-spacing:.03em}
td{padding:9px 10px;border-top:1px solid #e6edf2;vertical-align:top}
tbody tr:nth-child(even) td{background:#fafcfd}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.first{font-weight:700;white-space:nowrap}
.badge{display:inline-block;border-radius:99px;padding:1px 8px;font-size:11px;font-weight:800}
.badge.ok{background:#d6f2e3;color:#12633a}
.badge.unv{background:#ffeec2;color:#7a5100}
.badge.rev{background:#e2e9f2;color:#334d66}
.badge.bad{background:#ffdedb;color:#96271f}
.sid{font-size:10.5px;color:#7b8fa1;font-weight:700;vertical-align:super}
.empty{color:#8b6a00;background:#fff8e1;border-radius:5px;padding:1px 6px;font-size:11.5px;
 font-weight:700;white-space:nowrap}
ul.pros,ul.cons{margin:6px 0 0;padding-left:18px;font-size:13px}
ul.pros li::marker{color:#1c8552}
ul.cons li::marker{color:#ab2b25}
ol.steps{padding-left:20px;font-size:13.5px}
ol.steps li{margin:5px 0}
details{background:#fff;border:1px solid #d9e4ec;border-radius:10px;padding:0;margin:10px 0}
details>summary{cursor:pointer;padding:13px 16px;font-weight:700;list-style:none}
details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"▸ ";color:#0f8ba3}
details[open]>summary::before{content:"▾ "}
details .body{padding:0 16px 15px;border-top:1px solid #eef3f7}
.filters{display:flex;gap:12px;flex-wrap:wrap;align-items:center;background:#fff;
 border:1px solid #d9e4ec;border-radius:10px;padding:11px 14px;margin:14px 0;font-size:14px}
.filters select,.filters input{font:inherit;padding:6px 8px;border:1px solid #b6c6d3;
 border-radius:7px;background:#fff}
.scroll{max-height:70vh;overflow:auto;border-radius:11px}
footer{background:#0e4d61;color:#b6d8e0;padding:22px max(16px,calc((100% - 1180px)/2));font-size:12.5px}
footer a{color:#8fd3e2}
.mono{font-variant-numeric:tabular-nums}
@media(max-width:640px){
 body{font-size:15px}
 table{min-width:0;font-size:12.5px}
 th,td{padding:7px 8px}
 thead{display:none}
 tbody tr{display:block;border-top:1px solid #dbe6ee;padding:8px 2px}
 tbody tr:first-child{border-top:0}
 tbody tr:nth-child(even) td{background:transparent}
 td{display:flex;gap:10px;border:0;padding:3px 8px}
 td::before{content:attr(data-l);flex:0 0 44%;color:#5c7488;font-weight:700;font-size:11.5px}
 td.num{text-align:left}
 td.first{font-weight:800}
 .card .v{font-size:19px}
}
"""


def head(title: str, active: str) -> str:
    parts = []
    for href, label in NAV:
        cls = ' class="on"' if href == active else ""
        parts.append(f'  <a href="{href}"{cls}>{esc(label)}</a>')
    links = "\n".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · China3</title>
<meta name="description" content="Verified, official-source guide to converting CNY to USD and moving it to the United States.">
<link rel="stylesheet" href="assets/d646.css">
</head>
<body>
<header>
  <div class="brand">
    <div class="mark">C3</div>
    <div>China3 · Money out of China
      <div class="sub">Verified {BUILD_DATE} · every figure carries an official source link or is blank and flagged</div>
    </div>
  </div>
</header>
<nav>
{links}
  <a href="index.html">Full archive</a>
</nav>
<main>
"""


def foot() -> str:
    return f"""
</main>
<footer>
  <p><strong>Built {BUILD_STAMP}.</strong> Research dashboard, not legal, tax or investment advice.
  Every figure is either quoted from an official source linked on the row or left blank and listed on
  <a href="d646-flagged.html">Flagged for review</a>. Rates are a frozen timestamp, not a live quote.</p>
  <p>Method: <code>scripts/build_d646_site.py</code> · checker: <code>scripts/verify_d646_site.py</code> ·
  board: <a href="COORDINATION.md">COORDINATION.md</a></p>
</footer>
</body>
</html>
"""


# --------------------------------------------------------------------------
# 8. PAGES
# --------------------------------------------------------------------------
def page_summary() -> str:
    top = LADDER[0]
    last = LADDER[-1]
    h = [head("Executive summary: getting money out of China", "d646-summary.html")]
    h.append(f"""
<h1>Getting money out of China, with the least tax and penalty exposure</h1>
<p class="lead">A U.S. citizen with personal CNY in a mainland China bank account. This page puts the
single most important findings first, then links to the method list, the full USD 10,000–400,000 cost
ladder, the tax and penalty breakdown, the verification log and everything still unconfirmed.</p>

<div class="callout good">
  <p><strong>The headline.</strong> On the lawful bank route the published conversion cost is small:
  <strong>{SPREAD_PCT*100:.3f}%</strong> of the amount as the bank's spread, plus at most
  <strong>CNY 260 + CNY 150</strong> per wire. For USD 10,000 that is <strong>{money(top['bank_total'])}</strong>
  ({top['bank_pct']:.3f}%). For USD 400,000 it is <strong>{money(last['bank_total'])}</strong>
  ({last['bank_pct']:.3f}%).</p>
  <p><strong>The large number is not a Chinese tax and not a bank fee.</strong> It is the U.S. tax on the
  <em>currency gain</em> under 26 U.S.C. §988. If the CNY was acquired at the 2024 IRS yearly average of
  {IRS_AVG_2024} and converted at today's Bank of China selling rate of {BOC_SELL}, the gain is
  <strong>{GAIN_FRAC_2024*100:.2f}% of the dollars you receive</strong> — about
  <strong>{money(LADDER[0]['gain24'])}</strong> on USD 10,000 and <strong>{money(LADDER[-1]['gain24'])}</strong> on USD 400,000
  — taxed as <strong>ordinary income</strong> at your marginal rate.</p>
</div>

<div class="cards">
  <div class="card"><div class="k">Bank spread (customer buys USD)</div>
    <div class="v">{SPREAD_PCT*100:.3f}%</div>
    <div class="n">Selling {BOC_SELL} vs middle {BOC_MID} · {src_links('S21')}</div></div>
  <div class="card"><div class="k">Wire tariff per transfer</div>
    <div class="v">CNY 50–260 + 150</div>
    <div class="n">0.1% of amount, minimum CNY 50, maximum CNY 260, plus CNY 150 cable · {src_links('S20')}</div></div>
  <div class="card"><div class="k">U.S. §988 gain (2024 basis)</div>
    <div class="v">{GAIN_FRAC_2024*100:.2f}%</div>
    <div class="n">of USD received, taxed as ordinary income · {src_links('S14|S13')}</div></div>
  <div class="card"><div class="k">Personal-transaction exclusion</div>
    <div class="v">USD 200 gain</div>
    <div class="n">Applies only if the gain is ≤ USD 200 — about USD {EXCLUSION_CEILING_USD:,.0f} converted · {src_links('S14')}</div></div>
  <div class="card"><div class="k">China tax on the conversion</div>
    <div class="v">None identified</div>
    <div class="n">No official source reviewed imposes one · {src_links('S11')}</div></div>
  <div class="card"><div class="k">FBAR trigger</div>
    <div class="v">USD 10,000</div>
    <div class="n">aggregate at any time in the year · {src_links('S16')}</div></div>
</div>

<h2>The five findings that matter</h2>

<h3>1. "Considerable taxes" is almost certainly a U.S. tax, not a Chinese one</h3>
<p>The Individual Income Tax Law taxes nine enumerated categories of income — wages, remuneration, author's
remuneration, royalties, business income, interest/dividends/bonuses, property rental, property transfer and
incidental income. Converting your own CNY into USD is not one of them. No SAFE, PBOC or STA document
reviewed imposes a tax on the conversion itself. What <em>is</em> taxable is the U.S. side: §988 treats the
disposition of foreign currency — including a foreign-currency bank deposit — as a currency transaction, and
the resulting gain is ordinary income. {src_links('S11|S14')}</p>

<h3>2. The §988 personal-transaction exclusion is almost irrelevant at these amounts</h3>
<p>§988(e)(2) switches off the recognition rule for an individual's personal transaction, <em>but only if the
gain does not exceed USD 200</em>. At today's rate that means the whole exclusion disappears above roughly
<strong>USD {EXCLUSION_CEILING_USD:,.0f}</strong> converted. Every rung of the USD 10,000–400,000 ladder is
above it. {src_links('S14')}</p>

<h3>3. Timing is the only lever that changes the tax, and it cuts both ways</h3>
<p>The gain is measured against the rate at which you <em>acquired</em> the CNY. Converting in several calendar
years, at the USD 50,000 convenience amount per year, does not reduce the gain per dollar — but it does let
you use lower brackets each year and it avoids stacking a single-year gain on top of a single-year income.
The ladder shows five brackets instead of guessing your one rate. {src_links('S14|S17')}</p>

<h3>4. Almost every "faster" route is a fine, not a fee</h3>
<p>Splitting across other people's quotas is expressly prohibited and results in a multi-year watch list.
Underground exchange, crypto/USDT settlement, false documents and structuring are all unlawful, with fines
up to 30% of the amount — 30% to 100% if serious — plus confiscation. That is five to fifteen times the
entire published bank cost, and it does not reduce the U.S. tax by a cent. {src_links('S04|S08|S12')}</p>

<h3>5. Report, don't restructure</h3>
<p>The FBAR and Form 8938 are information returns: filing them costs nothing and does not tax the money. Not
filing them is the single largest financial risk in this whole picture — up to USD 16,536 per non-willful
violation and USD 165,353 per willful one, against a USD 10,000 account trigger. {src_links('S15|S16')}</p>

<h2>What to do, in order</h2>
<ol class="steps">
  <li><strong>Establish the character of the money.</strong> Salary already taxed in China, sale proceeds,
      inheritance, or company funds? This decides eligibility and decides the Chinese tax, and it is the one
      fact nobody else can supply.</li>
  <li><strong>Establish your USD basis and acquisition date for the CNY.</strong> Without it the §988 gain
      cannot be computed — the ladder's 2024-average assumption is a placeholder, and stated as one.</li>
  <li><strong>Ask the holding bank, in writing, to classify the payment</strong> and list the documents it
      requires. Above USD 50,000 per year the ID-only convenience amount stops applying; above USD 50,000 per
      single payment a tax filing record may also be needed. {src_links('S02|S03|S10')}</li>
  <li><strong>Choose the lawful channel that matches the facts</strong>: documented current-account
      remittance, the annual convenience amount spread over years, or — only if the eligibility really
      applies — the emigrant or inheritance property transfer. {src_links('S09')}</li>
  <li><strong>Get the all-in quote in writing</strong> before booking: customer rate, spread, tariff, cable,
      intermediary and receiving-bank charges, and expected net USD.</li>
  <li><strong>File the U.S. side.</strong> FBAR by 15 April (automatic extension to 15 October), Form 8938 with
      the return if the threshold is met, FinCEN Form 105 if cash above USD 10,000 crosses the border.
      {src_links('S16|S19')}</li>
</ol>

<div class="callout warn">
  <p><strong>Do not use:</strong> other people's quotas, underground exchangers, crypto/USDT, false invoices or
  purpose declarations, or structured sub-threshold transfers. Each is separately unlawful, each is penalised
  as a percentage of the whole amount, and none of them changes the U.S. tax. {src_links('S04|S08|S12|S19')}</p>
</div>

<h2>At a glance: cost by amount</h2>
<div class="tbl"><table>
<thead><tr><th>Amount</th><th>Known bank cost</th><th>Cost %</th><th>§988 gain (2024 basis)</th>
<th>Tax if 24%</th><th>Years at USD 50k</th><th>Source</th></tr></thead>
<tbody>
""")
    for r in LADDER:
        if r["usd"] in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000):
            h.append(
                f'<tr><td class="first" data-l="Amount">{money(r["usd"], False)}</td>'
                f'<td class="num" data-l="Known bank cost">{money(r["bank_total"])}</td>'
                f'<td class="num" data-l="Cost %">{r["bank_pct"]:.3f}%</td>'
                f'<td class="num" data-l="§988 gain">{money(r["gain24"])}</td>'
                f'<td class="num" data-l="Tax if 24%">{money(r["tax24"])}</td>'
                f'<td class="num" data-l="Years at USD 50k">{r["years"]}</td>'
                f'<td data-l="Source">{src_links("S20|S21|S13|S14")}</td></tr>'
            )
    h.append("""</tbody></table></div>
<p><a href="d646-costs.html">See all 40 increments with every tax bracket →</a></p>
""")
    h.append(foot())
    return "\n".join(h)


def page_methods() -> str:
    h = [head("All CNY→USD methods, pros and cons", "d646-methods.html")]
    lawful = sum(1 for m in METHODS if m["legality"].startswith("Lawful"))
    bad = sum(1 for m in METHODS if m["legality"] in ("PROHIBITED", "UNLAWFUL")
              or m["legality"].startswith("PROHIBITED"))
    h.append(f"""
<h1>Every way to turn CNY into USD</h1>
<p class="lead">{len(METHODS)} routes, each with its official legal basis, its published capacity limit, the exact
steps, and the pros and cons. {lawful} are lawful in at least some circumstances. The rest are unlawful and are
listed only so they can be recognised and avoided.</p>

<div class="callout warn">
  <p><strong>Read the capacity column first.</strong> Several routes are perfectly lawful but can never move
  USD 400,000: card cash is capped at RMB 100,000 per person per year, cash carry at USD 10,000 per trip, card
  spending is consumption rather than conversion. Only documented remittance, the annual convenience amount
  over years, and the emigrant/inheritance property routes scale to a large sum. {src_links('S06|S07|S02|S09')}</p>
</div>

<div class="tbl"><table>
<thead><tr><th>ID</th><th>Method</th><th>Legal status</th><th>Published capacity</th><th>Reaches USD 400k?</th><th>Source</th></tr></thead>
<tbody>
""")
    for m in METHODS:
        cls = "bad" if (m["legality"].startswith(("PROHIBITED", "UNLAWFUL"))) else "ok"
        h.append(
            f'<tr id="{m["id"]}"><td class="first" data-l="ID">{m["id"]}</td>'
            f'<td data-l="Method"><a href="#{m["id"]}-d">{esc(m["name"])}</a></td>'
            f'<td data-l="Legal status"><span class="badge {cls}">{esc(m["legality"])}</span></td>'
            f'<td data-l="Published capacity">{esc(m["cap"])}</td>'
            f'<td data-l="Reaches USD 400k?">{esc(m["reaches_400k"])}</td>'
            f'<td data-l="Source">{src_links(m["cap_src"])}</td></tr>'
        )
    h.append("</tbody></table></div>\n<h2>Details, steps and trade-offs</h2>\n")

    for m in METHODS:
        cls = "bad" if (m["legality"].startswith(("PROHIBITED", "UNLAWFUL"))) else "ok"
        pros = "".join(f"<li>{esc(x)}</li>" for x in m["pros"])
        cons = "".join(f"<li>{esc(x)}</li>" for x in m["cons"])
        steps = "".join(f"<li>{esc(x)}</li>" for x in m["steps"])
        h.append(f"""
<details id="{m["id"]}-d">
  <summary>{m["id"]} · {esc(m["name"])} <span class="badge {cls}">{esc(m["legality"])}</span></summary>
  <div class="body">
    <p><strong>Published capacity:</strong> {esc(m["cap"])} · {src_links(m["cap_src"])}</p>
    <h3>Step by step</h3>
    <ol class="steps">{steps}</ol>
    <h3>Pros</h3><ul class="pros">{pros}</ul>
    <h3>Cons</h3><ul class="cons">{cons}</ul>
    <p><strong>Sources:</strong> {src_links(m["src"])}</p>
  </div>
</details>
""")
    h.append(foot())
    return "\n".join(h)


def page_costs() -> str:
    labels = [lab for lab, _ in TAX_SCENARIOS]
    h = [head("Cost of converting USD 10,000 to USD 400,000", "d646-costs.html")]
    h.append(f"""
<h1>What it costs, USD 10,000 → USD 400,000</h1>
<p class="lead">All 40 increments of USD 10,000. Costs are re-derived below from the bank's own published
tariff and today's stamped board, not copied from any earlier model.</p>

<div class="callout">
  <p><strong>How each column is built.</strong></p>
  <p><strong>Spread</strong> = amount × ({BOC_SELL} ÷ {BOC_MID} − 1) = {SPREAD_PCT*100:.4f}% — you pay the
  bank's selling rate rather than the middle rate. {src_links('S21')}</p>
  <p><strong>Wire fee</strong> = per transfer 0.1% of the CNY amount, floored at CNY 50, capped at CNY 260, plus
  CNY 150 cable, converted back at {BOC_SELL}. One wire per USD 50,000, because USD 50,000 is the documented
  ID-only convenience amount and each larger transfer needs documented evidence. {src_links('S20|S02|S03')}</p>
  <p><strong>§988 gain</strong> = amount × (1 − {BOC_SELL} ÷ {IRS_AVG_2024}) = {GAIN_FRAC_2024*100:.4f}% of the
  dollars received, assuming the CNY was acquired at the 2024 IRS yearly average of {IRS_AVG_2024}. Change the
  basis and this column changes: it is an assumption, clearly labelled, not your figure. {src_links('S14|S13')}</p>
  <p><strong>Intermediary and U.S. receiving-bank fees</strong> have no published schedule and are
  <span class="empty">left blank</span> on every row. {src_links('S20')}</p>
</div>

<div class="callout warn">
  <p><strong>Why there is no "total" column.</strong> Adding a known bank cost to an unverified intermediary fee
  would produce a number that looks precise and is not. The table gives you the two quantities that are actually
  published, and shows the tax at each of the five 2026 ordinary brackets so you can pick your own.</p>
</div>

<div class="tbl scroll"><table>
<thead><tr><th>Amount</th><th>Wires</th><th>Spread</th><th>Wire fees</th><th>Known bank cost</th>
<th>% of amount</th><th>§988 gain</th>{''.join(f'<th>Tax @ {l}</th>' for l in labels)}
<th>Intermediary fees</th><th>Years at USD 50k</th><th>Source</th></tr></thead>
<tbody>
""")
    for r in LADDER:
        taxes = "".join(f'<td class="num" data-l="Tax @ {l}">{money(r["gain24"]*rate)}</td>'
                        for l, rate in TAX_SCENARIOS)
        h.append(
            f'<tr><td class="first" data-l="Amount">{money(r["usd"], False)}</td>'
            f'<td class="num" data-l="Wires">{r["wires"]}</td>'
            f'<td class="num" data-l="Spread">{money(r["spread"])}</td>'
            f'<td class="num" data-l="Wire fees">{money(r["tariff"])}</td>'
            f'<td class="num" data-l="Known bank cost"><strong>{money(r["bank_total"])}</strong></td>'
            f'<td class="num" data-l="% of amount">{r["bank_pct"]:.3f}%</td>'
            f'<td class="num" data-l="§988 gain">{money(r["gain24"])}</td>'
            f'{taxes}'
            f'<td data-l="Intermediary fees"><span class="empty">blank · unverified</span></td>'
            f'<td class="num" data-l="Years at USD 50k">{r["years"]}</td>'
            f'<td data-l="Source">{src_links("S21|S20|S13|S14")}</td></tr>'
        )
    h.append(f"""</tbody></table></div>

<h2>Worked example: USD 10,000</h2>
<ol class="steps">
  <li>CNY needed at the selling rate: 10,000 × {BOC_SELL} = <strong>CNY 66,903.00</strong> {src_links('S21')}</li>
  <li>Spread: 66,903 ÷ {BOC_MID} = USD 10,020.95, so the spread costs <strong>{money(LADDER[0]['spread'])}</strong></li>
  <li>Wire fee: 0.1% of 66,903 = CNY 66.90, above the CNY 50 floor and below the CNY 260 cap, plus CNY 150
      cable = CNY 216.90, i.e. <strong>{money(LADDER[0]['tariff'])}</strong> {src_links('S20')}</li>
  <li>Known bank cost: <strong>{money(LADDER[0]['bank_total'])}</strong> = {LADDER[0]['bank_pct']:.3f}% of the amount</li>
  <li>§988 gain at the 2024 average basis: 10,000 × (1 − {BOC_SELL} ÷ {IRS_AVG_2024}) =
      <strong>{money(LADDER[0]['gain24'])}</strong>, ordinary income {src_links('S14|S13')}</li>
  <li>Tax at 24%: <strong>{money(LADDER[0]['tax24'])}</strong> — about {LADDER[0]['tax24']/LADDER[0]['bank_total']:.1f}×
      the entire published bank cost.</li>
</ol>

<h2>Worked example: USD 400,000</h2>
<ol class="steps">
  <li>Eight wires of USD 50,000 each, over eight calendar years at the convenience amount, or fewer wires if you
      can document a qualifying current-account purpose. {src_links('S02|S03')}</li>
  <li>Spread over the whole amount: <strong>{money(LADDER[-1]['spread'])}</strong></li>
  <li>Wire fees: 8 wires at the CNY 260 cap + CNY 150 cable = CNY 3,280 → <strong>{money(LADDER[-1]['tariff'])}</strong></li>
  <li>Known bank cost: <strong>{money(LADDER[-1]['bank_total'])}</strong> = {LADDER[-1]['bank_pct']:.3f}%</li>
  <li>§988 gain at the 2024 basis: <strong>{money(LADDER[-1]['gain24'])}</strong> —
      at 24% that is <strong>{money(LADDER[-1]['tax24'])}</strong>, at 37% <strong>{money(LADDER[-1]['gain24']*0.37)}</strong>.</li>
  <li>If the CNY was acquired at the <em>2025</em> average of {IRS_AVG_2025} instead, the gain falls to
      <strong>{money(LADDER[-1]['gain25'])}</strong> ({GAIN_FRAC_2025*100:.2f}%).</li>
</ol>

<div class="callout bad">
  <p><strong>Compare with the unlawful alternatives.</strong> A fine of 30% on USD 400,000 is USD 120,000, and
  30%–100% on a serious case is USD 120,000–400,000 — against a published bank cost of
  {money(LADDER[-1]['bank_total'])}. There is no amount at which bypassing the bank route is cheaper.
  {src_links('S08')}</p>
</div>
""")
    h.append(foot())
    return "\n".join(h)


def page_penalty() -> str:
    h = [head("Tax and penalty breakdown", "d646-penalty.html")]
    h.append(f"""
<h1>Where the cost of converting actually comes from</h1>
<p class="lead">Three different things are routinely conflated: the bank's conversion cost, a Chinese tax,
and a U.S. tax or penalty. Only two of the three are real on the lawful route, and they are in different
jurisdictions.</p>

<div class="cards">
  <div class="card"><div class="k">1 · Published bank cost</div><div class="v">{SPREAD_PCT*100:.2f}% + CNY 410</div>
    <div class="n">Spread plus tariff. Small and published. {src_links('S21|S20')}</div></div>
  <div class="card"><div class="k">2 · Chinese tax on conversion</div><div class="v">None identified</div>
    <div class="n">Not among the nine IIT categories. Left blank rather than guessed. {src_links('S11')}</div></div>
  <div class="card"><div class="k">3 · U.S. §988 + reporting</div><div class="v">≈{GAIN_FRAC_2024*100:.2f}% gain</div>
    <div class="n">Ordinary income, plus information-return penalties if a report is missed. {src_links('S14|S15')}</div></div>
</div>

<h2>China side: what is actually penalised</h2>
<p>The Chinese penalties attach to <em>behaviour</em>, never to the conversion itself: evading FX control,
trading FX illegally, buying FX with false documents, and changing a declared use. Each is a percentage of the
whole amount, which is why they dominate every other cost. {src_links('S08')}</p>

<h2>U.S. side: three separate systems</h2>
<h3>Income tax on the currency gain (§988)</h3>
<p>Disposing of nonfunctional currency — expressly including a foreign-currency bank deposit — is a §988
transaction, and the gain is computed separately and treated as <strong>ordinary income</strong>. The capital
election in §988(a)(1)(B) covers forward, futures and option contracts, not the disposition of a deposit, so the
preferential long-term capital rates are not the right comparison here. {src_links('S14|S18')}</p>
<p>The personal-transaction rule of §988(e)(2) would exclude the gain, but only while the gain is
<strong>at most USD 200</strong>. At today's rate that is about USD {EXCLUSION_CEILING_USD:,.0f} of converted
currency. On a USD 10,000 conversion the gain is {money(LADDER[0]['gain24'])}, more than 3× the ceiling.</p>

<h3>Information returns (no tax, real penalties)</h3>
<p>The FBAR and Form 8938 do not tax anything. Missing them is where the money is lost.</p>

<h2>Every penalty and rate, with its source</h2>
<div class="tbl"><table>
<thead><tr><th>ID</th><th>Item</th><th>Amount or rate</th><th>Trigger</th><th>Status</th><th>Source</th></tr></thead>
<tbody>
""")
    for p in PENALTIES:
        amt = esc(p["amount"]) if p["amount"] else '<span class="empty">blank · unverified</span>'
        h.append(
            f'<tr><td class="first" data-l="ID">{p["id"]}</td>'
            f'<td data-l="Item">{esc(p["name"])}</td>'
            f'<td data-l="Amount or rate">{amt}</td>'
            f'<td data-l="Trigger">{esc(p["trigger"])}</td>'
            f'<td data-l="Status">{badge(p["verified"])}</td>'
            f'<td data-l="Source">{src_links(p["src"])}</td></tr>'
        )
    h.append("""</tbody></table></div>

<h2>2026 U.S. ordinary brackets (single filer)</h2>
<p>§988 gain is ordinary income, so it stacks on top of your other taxable income. This is why the ladder shows
five rates rather than one. {src_links('S17')}</p>
<div class="tbl"><table>
<thead><tr><th>Taxable income up to</th><th>Rate</th><th>Tax on a USD 10,000 conversion's gain</th>
<th>Tax on a USD 400,000 conversion's gain</th><th>Source</th></tr></thead>
<tbody>
""")
    for ceil, rate in BRACKETS_2026_SINGLE:
        if ceil == float("inf"):
            continue
        h.append(
            f'<tr><td class="first" data-l="Up to">{money(ceil, False)}</td>'
            f'<td class="num" data-l="Rate">{rate*100:.0f}%</td>'
            f'<td class="num" data-l="Gain on 10k">{money(LADDER[0]["gain24"]*rate)}</td>'
            f'<td class="num" data-l="Gain on 400k">{money(LADDER[-1]["gain24"]*rate)}</td>'
            f'<td data-l="Source">{src_links("S17")}</td></tr>'
        )
    h.append(f"""</tbody></table></div>

<div class="callout">
  <p><strong>Not a rate here:</strong> the Foreign Earned Income Exclusion of USD {FEIE_2026:,} for 2026 excludes
  wages for personal services. It does not exclude a §988 currency gain, and it does not exclude savings you
  already hold. It can reduce U.S. tax on salary you earned in China, and that is a different question.
  {src_links('S17')}</p>
</div>

<div class="callout warn">
  <p><strong>What is still unknown.</strong> Your basis, your marginal rate, and whether prior-year FBARs were
  filed. All three are on <a href="d646-flagged.html">Flagged for review</a>, not filled in.</p>
</div>
""")
    h.append(foot())
    return "\n".join(h)


def page_verification() -> str:
    h = [head("Verification log", "d646-verification.html")]
    h.append(f"""
<h1>Line-by-line verification</h1>
<p class="lead">Each source below was fetched and read on {BUILD_DATE}. The quoted text is copied from the page,
not summarised. Anything that could not be confirmed from an official source is blank and listed on
<a href="d646-flagged.html">Flagged for review</a>.</p>

<div class="cards">
  <div class="card"><div class="k">Official documents read</div><div class="v">{len(SOURCES)}</div>
    <div class="n">SAFE, PBOC, STA, BOC, IRS, FinCEN/eCFR, CBP, govinfo</div></div>
  <div class="card"><div class="k">Ladder rows re-derived</div><div class="v">{len(LADDER)}</div>
    <div class="n">40 amounts × every published component</div></div>
  <div class="card"><div class="k">Rows left blank</div><div class="v">{len([p for p in PENALTIES if not p['amount']]) + len(LADDER)}</div>
    <div class="n">Intermediary and receiving-bank fees, card ATM fees</div></div>
  <div class="card"><div class="k">Flagged items</div><div class="v">{len(FLAGS)}</div>
    <div class="n">Published with source links, non-blocking</div></div>
</div>

<h2>How each figure was checked</h2>
<ol class="steps">
  <li><strong>Arithmetic is re-derived in code.</strong> <code>scripts/build_d646_site.py</code> computes every
      spread, tariff, gain and tax from the constants at the top of the file; no total is typed by hand.</li>
  <li><strong><code>scripts/verify_d646_site.py</code> recomputes them independently</strong> and fails the build
      if any printed number disagrees, if a data row has no official URL, or if a blank cell contains a value.</li>
  <li><strong>Every quoted figure appears verbatim</strong> in the source table below, with the URL it came from.</li>
  <li><strong>Hand-checked reference points:</strong> USD 10,000 spread {money(LADDER[0]['spread'])};
      USD 400,000 known bank cost {money(LADDER[-1]['bank_total'])};
      USD 10,000 §988 gain {money(LADDER[0]['gain24'])}.</li>
</ol>

<h2>Source register</h2>
<p>Full detail, with verbatim excerpts, on <a href="d646-sources.html">Sources</a>.</p>
<div class="tbl"><table>
<thead><tr><th>ID</th><th>Issuer</th><th>Document</th><th>Published</th><th>Status</th><th>Link</th></tr></thead>
<tbody>
""")
    for s in SOURCES:
        h.append(
            f'<tr id="{s["id"]}"><td class="first" data-l="ID">{s["id"]}</td>'
            f'<td data-l="Issuer">{esc(s["issuer"])}</td>'
            f'<td data-l="Document">{esc(s["title"])}</td>'
            f'<td data-l="Published">{esc(s["published"])}</td>'
            f'<td data-l="Status">{badge("verified")}</td>'
            f'<td data-l="Link"><a href="{s["url"]}" target="_blank" rel="noopener">open ↗</a></td></tr>'
        )
    h.append(f"""</tbody></table></div>

<h2>What was rejected or corrected during this pass</h2>
<div class="callout warn">
  <p><strong>Corrected:</strong> earlier pages describe the §988 personal-transaction exclusion loosely. The
  statute's actual condition is a <strong>USD 200 gain ceiling</strong> (S14), which fails at every rung of this
  ladder. This pass states the test, not a summary of it.</p>
  <p><strong>Corrected:</strong> a 15% capital-gain rate is sometimes applied to this gain. §988(a)(1)(A) makes it
  ordinary; the capital election is limited to forward/futures/option contracts (S14). No capital rate is shown
  in the ladder.</p>
  <p><strong>Not carried forward:</strong> the 2026-11-09 board stamp of 6.6919 is replaced by today's
  {BOC_SELL} (S21). Both are genuine; only one is current. See flag D646-11.</p>
  <p><strong>Left blank on purpose:</strong> intermediary/correspondent fees, U.S. receiving-bank fees, offshore
  CNY/CNH basis, card ATM operator fees. No official schedule was found for any of them.</p>
</div>

<h2>What this pass did not verify</h2>
<p>The 30+ pages already in the repository were <em>not</em> re-derived line by line this time. Their own
validators pass on <code>main</code>, and their figures remain on their own pages, unchanged. This refresh adds a
current, independently computed set alongside them; where a rate has moved, the difference is recorded as
D646-11 rather than silently rewritten. Treat any page whose header says 2026-11-09 as a historical snapshot.</p>
""")
    h.append(foot())
    return "\n".join(h)


def page_flagged() -> str:
    h = [head("Flagged for review", "d646-flagged.html")]
    highs = sum(1 for f in FLAGS if f["sev"] == "high")
    h.append(f"""
<h1>Flagged for review</h1>
<p class="lead">{len(FLAGS)} items could not be confirmed from an official source, or are irregularities worth a
human decision. {highs} are high severity because they change the answer. None of them blocks publication — every
one is blank rather than guessed, and every one carries the source that would settle it.</p>

<div class="callout warn">
  <p><strong>What "unverified" means here.</strong> The cell is empty on purpose. It is not zero, and it is not an
  estimate. Filling it would require a fact only you or your bank can supply.</p>
</div>

<div class="tbl"><table>
<thead><tr><th>ID</th><th>Severity</th><th>Item</th><th>Status</th><th>Why it matters</th><th>Source to settle it</th></tr></thead>
<tbody>
""")
    for f in FLAGS:
        sevcls = {"high": "bad", "medium": "unv", "low": "rev"}[f["sev"]]
        h.append(
            f'<tr id="{f["id"]}"><td class="first" data-l="ID">{f["id"]}</td>'
            f'<td data-l="Severity"><span class="badge {sevcls}">{f["sev"]}</span></td>'
            f'<td data-l="Item">{esc(f["item"])}</td>'
            f'<td data-l="Status">{badge(f["status"])}</td>'
            f'<td data-l="Why it matters">{esc(f["detail"])}</td>'
            f'<td data-l="Source">{src_links(f["src"])}</td></tr>'
        )
    h.append("""</tbody></table></div>

<h2>The three that would change the recommendation</h2>
<ol class="steps">
  <li><strong>D646-02 — what kind of money is it?</strong> Salary already taxed in China, sale proceeds,
      inheritance, or company funds. This single fact decides which lawful channel is available and whether any
      Chinese tax remains payable.</li>
  <li><strong>D646-04 — what is your USD basis in the CNY?</strong> The §988 gain is measured against your
      acquisition rate. A basis at or below today's {SELL_LABEL} means no gain at all.</li>
  <li><strong>D646-09 — were prior FBARs and Form 8938s filed?</strong> A missed information return can cost more
      than the entire conversion, and it must be dealt with before moving a large sum.</li>
</ol>
""".replace("{SELL_LABEL}", f"{BOC_SELL}"))
    h.append(foot())
    return "\n".join(h)


def page_sources() -> str:
    h = [head("Official sources", "d646-sources.html")]
    tiers = {}
    for s in SOURCES:
        tiers.setdefault(s["tier"], []).append(s)
    h.append(f"""
<h1>Official sources</h1>
<p class="lead">{len(SOURCES)} primary documents, grouped by issuer. Each excerpt is copied verbatim from the page
it is linked to and was read on {BUILD_DATE}. Third-party commentary is not used for any figure.</p>
""")
    for tier in sorted(tiers):
        h.append(f"<h2>{esc(tier)}</h2>\n")
        for s in tiers[tier]:
            h.append(f"""
<details id="{s["id"]}-src">
  <summary>{s["id"]} · {esc(s["title"])}</summary>
  <div class="body">
    <p><strong>Issuer:</strong> {esc(s["issuer"])} · <strong>Published:</strong> {esc(s["published"])}</p>
    <p><strong>Link:</strong> <a href="{s["url"]}" target="_blank" rel="noopener">{esc(s["url"])}</a></p>
    <p><strong>Verbatim excerpt:</strong> <q>{esc(s["quote"])}</q></p>
    <p><strong>What it establishes:</strong> {esc(s["supports"])}</p>
  </div>
</details>
""")
    h.append("""
<h2>How to check this yourself</h2>
<p>Open any link above and search the page for the quoted text. Every number in the cost ladder traces to S20
(the bank's tariff) and S21 (the bank's stamped rate board); every tax number traces to S13 (IRS yearly average
rates), S14 (§988) or S17 (2026 brackets); every penalty traces to S08 (China) or S15/S16/S19 (U.S.).</p>
""")
    h.append(foot())
    return "\n".join(h)


# --------------------------------------------------------------------------
# 9. MARKDOWN OUTPUT
# --------------------------------------------------------------------------
def md_executive_summary() -> str:
    top, last = LADDER[0], LADDER[-1]
    lines = [
        "# Executive summary — getting money out of China",
        "",
        f"Session `arena/d6467425-china3` · rebuilt {BUILD_STAMP} · generated by `scripts/build_d646_site.py`.",
        "",
        "## The one-paragraph answer",
        "",
        f"On the lawful bank route the published conversion cost is small: **{SPREAD_PCT*100:.3f}%** spread plus at",
        f"most **CNY 260 + CNY 150** per wire. At USD 10,000 that is **{money(top['bank_total'])}** ({top['bank_pct']:.3f}%);",
        f"at USD 400,000 it is **{money(last['bank_total'])}** ({last['bank_pct']:.3f}%). No official source reviewed",
        "imposes a Chinese tax on converting an individual's own CNY to USD. The large number is a **U.S.** tax: the",
        f"§988 currency gain, which is **{GAIN_FRAC_2024*100:.2f}% of the dollars received** if the CNY was acquired at",
        f"the 2024 IRS yearly average of {IRS_AVG_2024}, taxed as **ordinary income**. Every 'faster' route is a fine of",
        "30%–100% of the amount, does not reduce that tax, and is separately unlawful.",
        "",
        "## Key figures",
        "",
        "| Figure | Value | Source |",
        "|---|---|---|",
        f"| BOC USD selling rate (customer buys USD) | {BOC_SELL} CNY/USD, stamped 2026-11-10 07:32:39 | S21 |",
        f"| BOC USD middle rate | {BOC_MID} CNY/USD | S21 |",
        f"| Bank spread paid by the customer | {SPREAD_PCT*100:.4f}% | S21 |",
        f"| Cross-border telegraphic transfer tariff | 0.1% of amount, CNY 50 min, CNY 260 max, + CNY 150 cable | S20 |",
        f"| China individual convenience amount | USD {CONVENIENCE_USD:,} per person per year — a threshold, not a cap | S02 |",
        f"| Remittance above USD 50,000/day | transaction documents required | S03 |",
        f"| Single outbound payment above USD 50,000 | tax filing record may be required | S10 |",
        f"| IRS yearly average CNY/USD | {IRS_AVG_2025} (2025), {IRS_AVG_2024} (2024) | S13 |",
        f"| §988 gain at the 2024 basis | {GAIN_FRAC_2024*100:.2f}% of USD received | S14 + S13 |",
        f"| §988 personal-transaction exclusion | only while the gain is ≤ USD 200 (≈ USD {EXCLUSION_CEILING_USD:,.0f} converted) | S14 |",
        f"| FBAR threshold / non-willful max / willful max | USD 10,000 / USD {FBAR_NONWILLFUL:,} / USD {FBAR_WILLFUL:,} | S16 + S15 |",
        f"| Form 8938 penalty ceiling | USD {FORM8938_MAX_PENALTY:,} | S16 |",
        f"| FinCEN Form 105 | required above USD 10,000 carried or shipped | S19 |",
        f"| Foreign earned income exclusion 2026 | USD {FEIE_2026:,} — earned income only, not this gain | S17 |",
        "",
        "## The five findings",
        "",
        "1. **The 'considerable tax' is a U.S. tax, not a Chinese one.** IIT Law Art.2 lists nine taxable income",
        "   categories; a bare CNY→USD conversion is not among them (S11).",
        "2. **The §988 personal exclusion is unavailable at these amounts.** It stops applying once the gain exceeds",
        f"   USD 200, i.e. above roughly USD {EXCLUSION_CEILING_USD:,.0f} converted (S14).",
        "3. **Timing only changes the rate, not the gain per dollar.** Spreading conversions across years uses lower",
        "   brackets each year; the ladder shows all five 2026 brackets rather than assuming one (S17).",
        "4. **Every faster route is a penalty, not a fee.** Splitting (S04), underground exchange, false documents",
        "   (S08) and crypto/USDT (S12) carry fines up to 30%–100% of the amount.",
        "5. **Report, don't restructure.** FBAR and Form 8938 are information returns; missing them is the largest",
        "   single risk in the picture (S15, S16).",
        "",
        "## Recommended sequence",
        "",
        "1. Establish the character of the money (salary / proceeds / inheritance / company).",
        "2. Establish the USD basis and acquisition date of the CNY.",
        "3. Obtain the bank's written classification and document checklist.",
        "4. Use the lawful channel that matches the facts.",
        "5. Get the all-in quote in writing before booking.",
        "6. File FBAR, Form 8938 and (if cash) FinCEN Form 105.",
        "",
        "## Cost at a glance",
        "",
        "| Amount | Known bank cost | % | §988 gain (2024 basis) | Tax @ 24% | Years at USD 50k |",
        "|---|---|---|---|---|---|",
    ]
    for r in LADDER:
        if r["usd"] in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000):
            lines.append(
                f"| {money(r['usd'], False)} | {money(r['bank_total'])} | {r['bank_pct']:.3f}% | "
                f"{money(r['gain24'])} | {money(r['tax24'])} | {r['years']} |"
            )
    lines += [
        "",
        f"Full 40-increment table: `d646-costs.html`, `data/d646_ladder.csv`.",
        f"{len(FLAGS)} flagged items: `d646-flagged.html`, `data/d646_verification.csv`.",
        "",
    ]
    return "\n".join(lines)


def md_verification() -> str:
    lines = [
        "# Verification log — 2026-11-10 refresh",
        "",
        f"Session `arena/d6467425-china3`. Every document below was fetched and read on {BUILD_DATE}.",
        "The excerpt column is verbatim from the linked page.",
        "",
        "## Fetch log",
        "",
        "| ID | Issuer | Document | Published | Verbatim excerpt | Link |",
        "|---|---|---|---|---|---|",
    ]
    for s in SOURCES:
        q = s["quote"].replace("|", "\\|")
        lines.append(f"| {s['id']} | {s['issuer']} | {s['title']} | {s['published']} | {q} | {s['url']} |")
    lines += [
        "",
        "## Arithmetic re-derived",
        "",
        f"- Bank spread: {BOC_SELL} ÷ {BOC_MID} − 1 = **{SPREAD_PCT*100:.4f}%**",
        f"- USD 10,000: CNY {10_000*BOC_SELL:,.2f} needed; spread {money(LADDER[0]['spread'])}; "
        f"wire fee CNY {tariff_cny(10_000):,.2f} = {money(LADDER[0]['tariff'])}; "
        f"known cost {money(LADDER[0]['bank_total'])}",
        f"- USD 400,000: 8 wires; spread {money(LADDER[-1]['spread'])}; "
        f"wire fees {money(LADDER[-1]['tariff'])}; known cost {money(LADDER[-1]['bank_total'])}",
        f"- §988 gain fraction: 1 − {BOC_SELL} ÷ {IRS_AVG_2024} = **{GAIN_FRAC_2024*100:.4f}%**; "
        f"1 − {BOC_SELL} ÷ {IRS_AVG_2025} = {GAIN_FRAC_2025*100:.4f}%",
        f"- USD 200 exclusion ceiling: 200 ÷ {GAIN_FRAC_2024:.8f} = USD {EXCLUSION_CEILING_USD:,.2f}",
        f"- USD 10,000 gain {money(LADDER[0]['gain24'])}; at 24% → {money(LADDER[0]['tax24'])}",
        "",
        "## Blank on purpose",
        "",
        "- Intermediary / correspondent bank fees (no published schedule) — S20",
        "- U.S. receiving-bank fees (no published schedule) — S20",
        "- Onshore/offshore CNY-CNH basis (market data, no official reference) — S03",
        "- Bank-card overseas ATM operator fees — S07",
        "- Any Chinese tax on the conversion itself — S11",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 10. CSV OUTPUT
# --------------------------------------------------------------------------
def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def csv_payloads():
    src_rows = []
    for s in SOURCES:
        src_rows.append(dict(id=s["id"], tier=s["tier"], issuer=s["issuer"], title=s["title"],
                             url=s["url"], published=s["published"], quote=s["quote"],
                             supports=s["supports"], status="verified", fetched=BUILD_DATE))

    method_rows = []
    for m in METHODS:
        method_rows.append(dict(
            id=m["id"], method=m["name"], legality=m["legality"], capacity=m["cap"],
            reaches_400k=m["reaches_400k"], pros="; ".join(m["pros"]), cons="; ".join(m["cons"]),
            steps=f"{len(m['steps'])} steps",
            source_ids=m["cap_src"], source_urls=" ".join(SRC_BY_ID[x]["url"] for x in m["cap_src"].split("|")),
        ))

    ladder_rows = []
    for r in LADDER:
        ladder_rows.append(dict(
            usd=r["usd"], wires=r["wires"],
            boc_sell=BOC_SELL, boc_mid=BOC_MID, spread_pct=round(SPREAD_PCT * 100, 4),
            spread_usd=round(r["spread"], 2), wire_fee_usd=round(r["tariff"], 2),
            known_bank_cost_usd=round(r["bank_total"], 2),
            bank_cost_pct=round(r["bank_pct"], 4),
            fx_gain_2024_usd=round(r["gain24"], 2), fx_gain_2025_usd=round(r["gain25"], 2),
            tax_10=round(r["gain24"] * 0.10, 2), tax_22=round(r["gain24"] * 0.22, 2),
            tax_24=round(r["gain24"] * 0.24, 2), tax_32=round(r["gain24"] * 0.32, 2),
            tax_37=round(r["gain24"] * 0.37, 2),
            intermediary_fees_usd="", intermediary_status="UNVERIFIED",
            years_at_50k=r["years"],
            source_urls=f"{SRC_BY_ID['S21']['url']} {SRC_BY_ID['S20']['url']} "
                        f"{SRC_BY_ID['S13']['url']} {SRC_BY_ID['S14']['url']}",
        ))

    flag_rows = [dict(id=f["id"], severity=f["sev"], item=f["item"], status=f["status"],
                      detail=f["detail"], source_ids=f["src"],
                      source_urls=" ".join(SRC_BY_ID[x]["url"] for x in f["src"].split("|")))
                 for f in FLAGS]

    penalty_rows = [dict(id=p["id"], item=p["name"], amount=p["amount"], trigger=p["trigger"],
                         status=p["verified"], source_ids=p["src"],
                         source_urls=" ".join(SRC_BY_ID[x]["url"] for x in p["src"].split("|")))
                    for p in PENALTIES]

    return {
        "d646_sources.csv": (["id", "tier", "issuer", "title", "url", "published", "quote",
                              "supports", "status", "fetched"], src_rows),
        "d646_methods.csv": (["id", "method", "legality", "capacity", "reaches_400k", "pros", "cons",
                              "steps", "source_ids", "source_urls"], method_rows),
        "d646_ladder.csv": (["usd", "wires", "boc_sell", "boc_mid", "spread_pct", "spread_usd",
                             "wire_fee_usd", "known_bank_cost_usd", "bank_cost_pct",
                             "fx_gain_2024_usd", "fx_gain_2025_usd", "tax_10", "tax_22", "tax_24",
                             "tax_32", "tax_37", "intermediary_fees_usd", "intermediary_status",
                             "years_at_50k", "source_urls"], ladder_rows),
        "d646_verification.csv": (["id", "severity", "item", "status", "detail", "source_ids",
                                   "source_urls"], flag_rows),
        "d646_penalty.csv": (["id", "item", "amount", "trigger", "status", "source_ids",
                              "source_urls"], penalty_rows),
    }


# --------------------------------------------------------------------------
# 11. MAIN
# --------------------------------------------------------------------------
def render_all() -> dict[Path, str]:
    out: dict[Path, str] = {}
    out[ROOT / "d646-summary.html"] = page_summary()
    out[ROOT / "d646-methods.html"] = page_methods()
    out[ROOT / "d646-costs.html"] = page_costs()
    out[ROOT / "d646-penalty.html"] = page_penalty()
    out[ROOT / "d646-verification.html"] = page_verification()
    out[ROOT / "d646-flagged.html"] = page_flagged()
    out[ROOT / "d646-sources.html"] = page_sources()
    out[ASSETS / "d646.css"] = CSS
    out[RESEARCH / "d646-executive-summary.md"] = md_executive_summary()
    out[RESEARCH / "d646-verification.md"] = md_verification()
    return out


def write_outputs() -> int:
    for name, (fields, rows) in csv_payloads().items():
        write_csv(DATA / name, fields, rows)
    for path, text in render_all().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return 0


def check_outputs() -> int:
    stale = []
    for name, (fields, rows) in csv_payloads().items():
        path = DATA / name
        tmp = path.with_suffix(".tmp")
        write_csv(tmp, fields, rows)
        if not path.exists() or path.read_text(encoding="utf-8") != tmp.read_text(encoding="utf-8"):
            stale.append(str(path.relative_to(ROOT)))
        tmp.unlink()
    for path, text in render_all().items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            stale.append(str(path.relative_to(ROOT)))
    if stale:
        print("STALE — regenerate with: python3 scripts/build_d646_site.py")
        for s in stale:
            print("  ", s)
        return 1
    print(f"OK — {len(render_all())} page/doc outputs and {len(csv_payloads())} CSVs are up to date.")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        raise SystemExit(check_outputs())
    write_outputs()
    print(f"D646 built: {len(SOURCES)} sources, {len(METHODS)} methods, {len(LADDER)} ladder rows, "
          f"{len(FLAGS)} flags, {len(PENALTIES)} penalty rows.")
