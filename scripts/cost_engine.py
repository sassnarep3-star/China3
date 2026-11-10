#!/usr/bin/env python3
"""Cost engine: CNY -> USD, $10,000 to $400,000 in $10,000 steps.

Every input below is either
  (a) a figure published by an official source, recorded with its URL and the
      date/time it was read, or
  (b) a formula coefficient derived by arithmetic from (a), labelled 'derived', or
  (c) blank, marked UNVERIFIED, and listed on the Flagged for Review page.

Nothing is estimated from market folklore. Where a real cost exists but no
published number can be cited (the receiving bank's fee, the correspondent
bank's deduction, notaries, ATM operators), the value stays blank and the
column says so.

Run `python3 scripts/build_cost_tables.py` to emit the CSVs and the page.
Run `python3 scripts/verify_cost_tables.py` to re-check every row.
"""
from __future__ import annotations

import math

# --------------------------------------------------------------------------
# 1. Amount ladder
# --------------------------------------------------------------------------
STEP = 10_000
AMOUNTS = [STEP * i for i in range(1, 41)]          # 10,000 .. 400,000

# --------------------------------------------------------------------------
# 2. Verified inputs
# --------------------------------------------------------------------------
BOC_URL = "https://www.boc.cn/sourcedb/whpj/"
BOC_HISTORY_URL = "https://www.boc.cn/sourcedb/whpjSearch/index.html"
BOC_TARIFF_URL = "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html"

# Bank of China 外汇牌价, USD, read 2026-11-09 09:15:45 from the official board.
# The board quotes CNY per 100 units of foreign currency.
BOC_ASK = 669.19 / 100      # 现汇卖出价 — the rate at which the bank SELLS USD
BOC_BID = 666.38 / 100      # 现汇买入价 — the rate at which the bank BUYS USD
BOC_MID = (BOC_ASK + BOC_BID) / 2                     # derived, arithmetic mean
HALF_SPREAD = (BOC_ASK - BOC_MID) / BOC_MID           # derived, 0.2104 %
FULL_SPREAD = (BOC_ASK - BOC_BID) / BOC_MID           # derived, bid-ask

WIRE_RATE = 0.001           # 1‰ of the remittance, per BOC tariff
WIRE_MIN_CNY = 50.0         # minimum CNY 50 per transfer
WIRE_MAX_CNY = 260.0        # maximum CNY 260 per transfer
CABLE_CNY = 150.0           # 电讯费, non-HK/Macau/Taiwan destination
CABLE_CNY_HKMOTW = 80.0     # 电讯费, HK/Macau/Taiwan destination

SAFE_CONVENIENCE_USD = 50_000.0   # annual convenience amount (not a cap on all routes)
ATM_YEAR_CNY = 100_000.0          # per natural year, all cards combined
ATM_DAY_CNY = 10_000.0            # per card per day
CASH_NO_PERMIT_USD = 5_000.0      # <= this: no 携带证 needed
CASH_PERMIT_MAX_USD = 10_000.0    # 5,000-10,000 needs 携带证; >10,000 not in principle
FINCEN105_USD = 10_000.0          # US: report currency > $10,000 on entry/exit
FBAR_WILLFUL_PCT = 0.50           # up to 50% of balance (greater of that or $165,353)
CNH_STRESS_BASIS = 0.0194         # HKMA-measured onshore/offshore basis, stress episode


def wire_fee_cny(amount_usd: float, ask: float = BOC_ASK) -> float:
    """BOC personal cross-border telegraphic transfer fee, in CNY."""
    raw = WIRE_RATE * amount_usd * ask
    return min(max(raw, WIRE_MIN_CNY), WIRE_MAX_CNY)


def wire_total_cny(amount_usd: float, ask: float = BOC_ASK, cable: float = CABLE_CNY) -> float:
    return wire_fee_cny(amount_usd, ask) + cable


def spread_cost_usd(amount_usd: float, ask: float = BOC_ASK, mid: float = BOC_MID) -> float:
    """Cost of crossing the bank's quoted spread, in USD."""
    return amount_usd * (ask / mid - 1.0)


# --------------------------------------------------------------------------
# 3. Input register (id, name, value, unit, source, status, note)
# --------------------------------------------------------------------------
INPUTS = [
    dict(
        id="CI01", name="USD/CNY 现汇卖出价 (bank sells USD to you)", value=f"{BOC_ASK:.4f}",
        unit="CNY per USD", as_of="2026-11-09 09:15:45", source_id="CS01", url=BOC_URL,
        status="verified",
        note="Published on Bank of China's official 外汇牌价 board as 669.19 CNY per 100 USD. "
             "Use this rate, not the mid, because you are the buyer of USD.",
    ),
    dict(
        id="CI02", name="USD/CNY 现汇买入价 (bank buys USD from you)", value=f"{BOC_BID:.4f}",
        unit="CNY per USD", as_of="2026-11-09 09:15:45", source_id="CS01", url=BOC_URL,
        status="verified",
        note="Published on the same board as 666.38 CNY per 100 USD.",
    ),
    dict(
        id="CI03", name="Mid rate used to price the spread", value=f"{BOC_MID:.6f}",
        unit="CNY per USD", as_of="2026-11-09", source_id="CS01", url=BOC_URL,
        status="derived",
        note="Arithmetic mean of CI01 and CI02 — a calculation on two published numbers, "
             "not an independent market quote.",
    ),
    dict(
        id="CI04", name="Customer-side spread paid when buying USD", value=f"{HALF_SPREAD*100:.4f}",
        unit="% of amount", as_of="2026-11-09", source_id="CS01", url=BOC_URL,
        status="derived",
        note="(CI01 − CI03) ÷ CI03. This is the genuine 'conversion' cost inside China, and it "
             "is the only regulatory-free, market-set charge in the chain. It is a one-day "
             "observation, not a constant — see IR-024.",
    ),
    dict(
        id="CI05", name="Full bid-ask spread on the board", value=f"{FULL_SPREAD*100:.4f}",
        unit="% of amount", as_of="2026-11-09", source_id="CS01", url=BOC_URL,
        status="derived",
        note="(CI01 − CI02) ÷ CI03. Half of this is what a customer pays on one side.",
    ),
    dict(
        id="CI06", name="Cross-border telegraphic transfer fee", value="1‰ of the amount",
        unit="CNY", as_of="2014-11-01 tariff", source_id="S46", url=BOC_TARIFF_URL,
        status="verified",
        note="Tariff text: 每笔汇款金额的1‰. Applies to 个人 跨境汇款（电汇）.",
    ),
    dict(
        id="CI07", name="Telegraphic transfer fee — minimum", value="50", unit="CNY",
        as_of="2014-11-01 tariff", source_id="S46", url=BOC_TARIFF_URL, status="verified",
        note="最低收取50元/笔. Binds only below about USD 7,472, i.e. outside the requested ladder.",
    ),
    dict(
        id="CI08", name="Telegraphic transfer fee — maximum", value="260", unit="CNY",
        as_of="2014-11-01 tariff", source_id="S46", url=BOC_TARIFF_URL, status="verified",
        note="最高收取260元/笔. Binds from about USD 38,855 upward, which is why the fee stops "
             "growing as the amount grows.",
    ),
    dict(
        id="CI09", name="Cable / telecom fee, destination outside HK-Macau-Taiwan", value="150",
        unit="CNY per transfer", as_of="2014-11-01 tariff", source_id="S46", url=BOC_TARIFF_URL,
        status="verified", note="另收电讯费…非港澳台地区人民币150元/笔.",
    ),
    dict(
        id="CI10", name="Cable / telecom fee, HK-Macau-Taiwan destination", value="80",
        unit="CNY per transfer", as_of="2014-11-01 tariff", source_id="S46", url=BOC_TARIFF_URL,
        status="verified", note="港澳台地区人民币80元/笔.",
    ),
    dict(
        id="CI11", name="Correspondent / intermediary bank deduction", value="",
        unit="USD", as_of="", source_id="S46", url=BOC_TARIFF_URL, status="unverified",
        note="The tariff states that overseas bank charges are passed through at actual cost, "
             "but no regulator or bank publishes the amount for a given corridor. Left blank.",
    ),
    dict(
        id="CI12", name="US receiving bank incoming international wire fee", value="",
        unit="USD", as_of="", source_id="S46", url=BOC_TARIFF_URL,
        status="unverified",
        note="The BOC tariff states that overseas bank charges are borne at actual cost, so a "
             "deduction exists, but no regulator publishes an amount and it varies by US bank and "
             "account tier. Left blank — read your own bank's fee schedule.",
    ),
    dict(
        id="CI13", name="Annual convenience amount for 境内个人 purchase of FX",
        value=f"{SAFE_CONVENIENCE_USD:,.0f}", unit="USD per person per year",
        as_of="current", source_id="S01", url="https://www.safe.gov.cn/ningxia/2022/0929/1997.html",
        status="verified",
        note="SAFE states expressly that this is not an annual ceiling on FX purchase or sale; "
             "it is the amount that can be handled on an ID document alone.",
    ),
    dict(
        id="CI14", name="Annual ceiling on overseas ATM cash withdrawal, all cards combined",
        value=f"{ATM_YEAR_CNY:,.0f}", unit="CNY equivalent per natural year",
        as_of="2018-01-01", source_id="S35", url="https://www.safe.gov.cn/hubei/2019/0305/851.html",
        status="verified",
        note="汇发〔2017〕29号 art. 1. Exceeding it suspends overseas cash withdrawal for the "
             "current and the following year (art. 1, second sentence).",
    ),
    dict(
        id="CI15", name="Daily ceiling on overseas ATM cash withdrawal", value=f"{ATM_DAY_CNY:,.0f}",
        unit="CNY equivalent per card per day", as_of="2018-01-01", source_id="S35",
        url="https://www.safe.gov.cn/hubei/2019/0305/851.html", status="verified",
        note="汇发〔2017〕29号 art. 4: foreign-currency cards cut from USD 1,000 to RMB 10,000 "
             "equivalent; RMB cards unchanged at RMB 10,000.",
    ),
    dict(
        id="CI16", name="Cash you may carry out without a 携带证", value=f"{CASH_NO_PERMIT_USD:,.0f}",
        unit="USD equivalent", as_of="2003 rule, republished 2024-04-30", source_id="S37",
        url="https://www.safe.gov.cn/big5/big5/www.safe.gov.cn/tianjin/2024/0430/2466.html",
        status="verified",
        note="汇发〔2003〕102号: up to and including USD 5,000, customs releases without a permit.",
    ),
    dict(
        id="CI17", name="Cash ceiling with a 携带证", value="5,000–10,000 (inclusive)",
        unit="USD equivalent", as_of="2003 rule, republished 2024-04-30", source_id="S37",
        url="https://www.safe.gov.cn/big5/big5/www.safe.gov.cn/tianjin/2024/0430/2466.html",
        status="verified",
        note="A permit from a designated FX bank is required in this band; in principle more than "
             "USD 10,000 may not be carried out, save for the listed special cases approved by SAFE.",
    ),
    dict(
        id="CI18", name="US currency-reporting threshold (FinCEN Form 105)", value=f"{FINCEN105_USD:,.0f}",
        unit="USD per person per trip", as_of="current", source_id="CS03",
        url="https://www.cbp.gov/travel/international-visitors/money-monetary-instruments",
        status="verified",
        note="More than USD 10,000 brought in or sent out must be reported; the threshold applies "
             "to the group total, not per traveller. Failure risks seizure and civil or criminal "
             "penalties under 31 U.S.C. 5321/5322.",
    ),
    dict(
        id="CI19", name="PRC individual income tax — comprehensive income", value="3%–45%",
        unit="progressive", as_of="current", source_id="S23",
        url="https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
        status="verified",
        note="Applies to the income that created the balance, not to the act of converting it. Business income (经营所得) is a separate 5%\u201335% progressive scale.",
    ),
    dict(
        id="CI20", name="PRC individual income tax — interest, dividends, rent, property transfer",
        value="20%", unit="proportional", as_of="current", source_id="S23",
        url="https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
        status="verified",
        note="Savings-deposit interest has been temporarily exempt since 2008-10-09 (S24).",
    ),
    dict(
        id="CI21", name="Penalty — 逃汇 (evading FX controls)", value="≤30%; serious 30%–100%",
        unit="% of amount", as_of="2008-08-05", source_id="S07",
        url="https://www.safe.gov.cn/safe/2008/0806/5321.html", status="verified",
        note="外汇管理条例 art. 39, read in full: 处逃汇金额30%以下的罚款；情节严重的，处逃汇金额"
             "30%以上等值以下的罚款.",
    ),
    dict(
        id="CI22", name="Penalty — 非法套汇 (fraudulent FX purchase)", value="≤30%; serious 30%–100%",
        unit="% of amount", as_of="2008-08-05", source_id="S07",
        url="https://www.safe.gov.cn/safe/2008/0806/5321.html", status="verified",
        note="art. 40. Also orders the funds returned (回兑).",
    ),
    dict(
        id="CI23", name="Penalty — carrying currency in or out in breach", value="≤20%",
        unit="% of amount", as_of="2008-08-05", source_id="S07",
        url="https://www.safe.gov.cn/safe/2008/0806/5321.html", status="verified",
        note="art. 42: warning plus a fine of up to 20% of the amount; customs penalties apply "
             "where a law or regulation so provides.",
    ),
    dict(
        id="CI24", name="Penalty — private/parallel FX dealing", value="≤30%; serious 30%–100%",
        unit="% of amount", as_of="2008-08-05", source_id="S07",
        url="https://www.safe.gov.cn/safe/2008/0806/5321.html", status="verified",
        note="art. 45: warning, confiscation of the illegal gain, fine of up to 30%; 30%–100% if "
             "serious; criminal liability if it constitutes a crime.",
    ),
    dict(
        id="CI25", name="FBAR willful penalty ceiling", value="greater of $165,353 or 50% of balance",
        unit="USD", as_of="2025 amounts, 2026 adjustment cancelled", source_id="U20",
        url="https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
        status="verified",
        note="31 CFR 1010.821. The ladder uses 50% of the balance shown in the row as the "
             "statutory maximum, which is the ceiling, not a prediction.",
    ),
    dict(
        id="CI26", name="Onshore/offshore CNY basis (CNH premium) for a personal conversion",
        value="", unit="%", as_of="", source_id="S50",
        url="https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201203/chapter4.pdf",
        status="unverified",
        note="The earlier source register recorded 1.94% from HKMA Quarterly Bulletin 2012-03 ch. 4. "
             "On re-check that chapter discusses HKD rates and Mainland credit, and the figure was not "
             "found in the sections read. It is therefore NOT used as a price here: the offshore "
             "column is left blank and the page gives the exact cost of each 1.00% of basis instead "
             "(see IR-026).",
    ),
    dict(
        id="CI27", name="Virtual-currency conversion route", value="prohibited",
        unit="—", as_of="2026-02-06", source_id="S29",
        url="https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html",
        status="verified",
        note="PBOC and eight other agencies: virtual-currency business activity is illegal "
             "financial activity. No lawful CNY->USDT->USD route exists.",
    ),
    dict(
        id="CI28", name="Notarisation, translation, apostille, courier for the approval routes",
        value="", unit="CNY", as_of="", source_id="CS04",
        url="http://m.safe.gov.cn/safe/2004/1116/5461.html", status="unverified",
        note="Art. 8 of PBC [2004] No. 16 requires notarised (and, for a foreign applicant, "
             "translated) documents but no authority publishes a price. Left blank; obtain a quote.",
    ),
    dict(
        id="CI29", name="Emigrant transfer — amount that may be paid in one go", value="200,000",
        unit="CNY equivalent", as_of="2004-12-01", source_id="CS04",
        url="http://m.safe.gov.cn/safe/2004/1116/5461.html", status="verified",
        note="PBC [2004] No.16 art. 6. Above this the payout is staged: at most half first, half the "
             "remainder after one year, the rest after two years.",
    ),
    dict(
        id="CI30", name="Emigrant / inheritance transfer — approval-level split", value="500,000",
        unit="CNY equivalent", as_of="2004-12-01", source_id="CS04",
        url="http://m.safe.gov.cn/safe/2004/1116/5461.html", status="verified",
        note="Art. 10: at or below RMB 500,000 the local SAFE branch decides; above it, local review "
             "then SAFE head office approval. The decision-maker changes with size, not the fee.",
    ),
    dict(
        id="CI31", name="Documents an emigrant-transfer applicant must file",
        value="户籍注销证明 + consular certification", unit="—", as_of="2004-12-01", source_id="CS04",
        url="http://m.safe.gov.cn/safe/2004/1116/5461.html", status="verified",
        note="Art. 8(4): a police-issued certificate that the mainland household registration was "
             "cancelled, plus a certificate of settlement abroad issued or authenticated by a Chinese "
             "embassy or consulate. Art. 8(6) adds the tax authority's 税收证明 or 完税凭证.",
    ),
    dict(
        id="CI32", name="Where the converted money must go", value="the applicant's own account abroad",
        unit="—", as_of="2004-12-01", source_id="CS04",
        url="http://m.safe.gov.cn/safe/2004/1116/5461.html", status="verified",
        note="Art. 11: the bank must remit directly to the applicant's own account in the country of "
             "residence, and may not pay out foreign cash inside China. Remittance is compulsory, so "
             "the wire and cable fees cannot be avoided on this route.",
    ),
]

# --------------------------------------------------------------------------
# 4. Methods
# --------------------------------------------------------------------------
# fee_model values consumed by cost_row():
#   wire_fx            spread + one wire + cable, single transfer, no ceiling
#   wire_fx_quota      as above, but forced into USD 50,000 annual chunks
#   wire_fx_plus_docs  as wire_fx, plus an unverified document cost
#   wire_nofx          wire + cable only (balance already in USD)
#   atm_cash           RMB 100,000/yr ceiling, per-withdrawal fee unverified
#   carry_cash         USD 10,000 per trip with permit, no bank fee
#   offshore_cnh       HKMA stress basis, offshore fees unverified
#   unlawful           statutory penalty exposure, no published fee
#   unavailable        no lawful path for this fact pattern

METHODS = [
    dict(
        id="M01", rank=1, family="Lawful — documented current account",
        name="Non-resident converts documented onshore income and wires USD out",
        name_zh="境外个人经常项目合法人民币收入购汇 + 汇出",
        legs="FX purchase at your bank, then one outward telegraphic transfer",
        fee_model="wire_fx", ceiling="No annual quota for 境外个人 (S03, S43); bank evidence review applies",
        years_basis="1", verdict="Cheapest and fastest lawful route when the RMB is traceable to taxed income",
        legality="lawful", moves_money=True,
        source_ids="S03,S43,S46,CS01", url="https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
        us_side="Worldwide income already taxable; the transfer itself is not income. FBAR/8938 on the account.",
        why="One spread crossing plus one wire. No agent, no approval queue, no annual ceiling.",
        caveat="The bank must accept your source-of-funds file, and it sets its own rate. "
               "Rates are deregulated (S27), so this page's 0.2104% is a one-day BOC observation.",
    ),
    dict(
        id="M02", rank=2, family="Lawful — documented current account",
        name="Resident uses the USD 50,000 annual convenience amount, year after year",
        name_zh="境内个人年度便利化额度内购汇汇出",
        legs="One FX purchase and wire per year, up to USD 50,000 each",
        fee_model="wire_fx_quota", ceiling="USD 50,000 per person per year on an ID document alone",
        years_basis="ceil(amount / 50,000)", verdict="Lawful but slow: USD 400,000 needs 8 calendar years",
        legality="lawful", moves_money=True,
        source_ids="S01,S46,CS01", url="https://www.safe.gov.cn/ningxia/2022/0929/1997.html",
        us_side="Same as M01; each year's account balance must be reported on the FBAR.",
        why="Requires only an ID and the 个人购汇申请书. No evidence file.",
        caveat="The 六不得 declaration (S09) forbids using the quota for capital-account purposes; "
               "splitting across people is 分拆 and is penalised.",
    ),
    dict(
        id="M03", rank=3, family="Lawful — capital account with approval",
        name="Emigrant property transfer (whole estate, one application)",
        name_zh="移民财产转移",
        legs="One SAFE application for the whole balance, then FX purchase and wire in up to three tranches over two years",
        fee_model="emigrant_staged",
        ceiling="No statutory ceiling; up to RMB 500,000 decided locally, above that by SAFE head office",
        years_basis="2 if above RMB 200,000, else 0", verdict="No amount ceiling, but staged over two years and it needs a cancelled hukou",
        legality="lawful", moves_money=True,
        source_ids="CS04,S18,S46,CS01", url="http://m.safe.gov.cn/safe/2004/1116/5461.html",
        us_side="No US tax on moving your own principal; the source income was already taxable.",
        why="Written for exactly this fact pattern: a natural person who moved from the mainland to a "
            "foreign country, moving lawful property owned before acquiring that emigrant status.",
        caveat="Art. 2 confines it to property owned before you acquired emigrant status; art. 8 requires "
               "the police-issued 户籍注销证明 plus Chinese consular certification of your settlement abroad. "
               "Art. 6 forces one application and staged payout: at most half first, half the remainder after "
               "a year, the rest after two years (at or below RMB 200,000 may go in one payment). Art. 11 bars "
               "paying cash in China. Document costs are unverified (CI28).",
    ),
    dict(
        id="M04", rank=4, family="Lawful — capital account with approval",
        name="Inheritance transfer",
        name_zh="继承财产转移",
        legs="One SAFE application for the whole inherited estate, then FX purchase and wire",
        fee_model="wire_fx_plus_docs",
        ceiling="No statutory ceiling; same RMB 500,000 local / head-office split as M03",
        years_basis="0 (no staging required)", verdict="The right route if the money arrived by inheritance rather than as your own savings",
        legality="lawful", moves_money=True,
        source_ids="CS04,S18,S46,CS01", url="http://m.safe.gov.cn/safe/2004/1116/5461.html",
        us_side="Inheritance is not US income for a US person; the foreign account is still FBAR-reportable.",
        why="Same banking cost as M03, but the evidence file is an estate rather than a life's savings.",
        caveat="Requires notarised inheritance documents naming you. If the funds are a gift rather "
               "than an inheritance, this route does not fit.",
    ),
    dict(
        id="M05", rank=5, family="Lawful — capital account with approval",
        name="Non-resident remits the proceeds of selling China property",
        name_zh="境外个人出售境内商品房所得购汇汇出",
        legs="Property tax clearance, SAFE approval, then FX purchase and wire",
        fee_model="wire_fx_plus_docs", ceiling="No ceiling stated in the rule; self-use test applies",
        years_basis="1", verdict="Lawful for sale proceeds; the 20% PRC tax on the gain is the real cost, not the conversion",
        legality="lawful", moves_money=True,
        source_ids="CS04,S23,S46,CS01", url="http://m.safe.gov.cn/safe/2004/1116/5461.html",
        us_side="The gain is US capital gain too, with a foreign tax credit for the PRC 20% (S23, U05).",
        why="Converts the sale proceeds at the same banking cost as any other wire.",
        caveat="The taxable gain is not public information — it depends on your cost basis, so the tax "
               "amount is left blank (IR-025). The banking mechanics equal every other route, but the "
               "notice governing a non-resident's property-sale remittance could not be re-verified in "
               "this pass: the SAFE Guangdong guide the earlier register cited now returns 404 (IR-027).",
    ),
    dict(
        id="M06", rank=6, family="Lawful — documented current account",
        name="Re-convert unused RMB against the original exchange memo",
        name_zh="原兑换未用完的人民币兑回",
        legs="Present the original exchange memo, buy back the foreign currency",
        fee_model="wire_fx", ceiling="Limited to the original amount exchanged; memo valid 24 months",
        years_basis="1", verdict="Free of the quota problem but only if you personally brought the FX in",
        legality="lawful", moves_money=True,
        source_ids="S04,S46,CS01", url="https://www.safe.gov.cn/tianjin/2024/0430/2464.html",
        us_side="Reversing your own conversion; no income. Report the account as usual.",
        why="The clearest lawful path when the RMB is literally your own imported dollars.",
        caveat="Only covers RMB you converted from foreign currency yourself, within 24 months.",
    ),
    dict(
        id="M07", rank=7, family="Lawful — documented current account",
        name="Wire out foreign currency already sitting in your FX account",
        name_zh="境外个人外汇储蓄账户汇出境外",
        legs="One outward telegraphic transfer in USD; no conversion step at all",
        fee_model="wire_nofx", ceiling="No amount limit stated for account transfers",
        years_basis="1", verdict="If part of the balance is already USD, transfer that first: no spread to pay",
        legality="lawful", moves_money=True,
        source_ids="S04,S46", url="https://www.safe.gov.cn/tianjin/2024/0430/2464.html",
        us_side="Pure transfer of your own funds. FBAR still applies to the Chinese account.",
        why="Removes the single largest component of the cost — the spread — entirely.",
        caveat="Only works for the portion already held in foreign currency, which for most people is zero.",
    ),
    dict(
        id="M08", rank=8, family="Lawful — but capped far below the target",
        name="Withdraw USD cash abroad on your Chinese bank card",
        name_zh="银行卡境外提取现金",
        legs="Repeated ATM withdrawals outside mainland China",
        fee_model="atm_cash",
        ceiling="RMB 100,000 equivalent per natural year across all your cards; RMB 10,000 per card per day",
        years_basis="ceil(amount × 6.6919 / 100,000)", verdict="Costs more than it saves: 6 calendar years for USD 400,000, and the per-withdrawal fee is unpublished",
        legality="lawful", moves_money=True,
        source_ids="S35,S35b", url="https://www.safe.gov.cn/hubei/2019/0305/851.html",
        us_side="Cash brought into the US over USD 10,000 must be reported on FinCEN 105 (CI18).",
        why="No application and no evidence file.",
        caveat="The annual ceiling is RMB 100,000, not USD 100,000 — about USD 14,943 at this rate, "
               "so the ladder needs 27 calendar years to clear USD 400,000. Exceeding it suspends the "
               "facility for the rest of this year and all of next year. ATM operator and card fees are "
               "not published by SAFE, so the fee column is blank rather than guessed.",
    ),
    dict(
        id="M09", rank=9, family="Lawful — but capped far below the target",
        name="Carry cash out by hand",
        name_zh="携带外币现钞出境",
        legs="Physical carriage, permit above USD 5,000, US report above USD 10,000",
        fee_model="carry_cash",
        ceiling="≤ USD 5,000 no permit; USD 5,000–10,000 needs a 携带证; above USD 10,000 not in principle",
        years_basis="ceil(amount / 10,000)", verdict="No bank fee, but 40 trips for USD 400,000 and physical-loss risk",
        legality="lawful", moves_money=True,
        source_ids="S37,CS03", url="https://www.safe.gov.cn/big5/big5/www.safe.gov.cn/tianjin/2024/0430/2466.html",
        us_side="Every trip over USD 10,000 must be declared to CBP on FinCEN 105 (CI18).",
        why="Zero bank charges.",
        caveat="40 separate trips for USD 400,000, each declared at the US border. Breach of the "
               "carrying rules exposes up to 20% of the amount under art. 42 (CI23) plus seizure.",
    ),
    dict(
        id="M10", rank=10, family="Lawful — limited availability",
        name="Move RMB to Hong Kong and convert offshore at the CNH rate",
        name_zh="跨境人民币汇出后离岸兑换",
        legs="Cross-border RMB remittance, then an offshore conversion in CNH",
        fee_model="offshore_unverified", ceiling="Individual cross-border RMB remittance is subject to the same "
                                                  "current-account evidence rules; no open personal channel",
        years_basis="1", verdict="Possible in principle, but no official source prices a personal offshore conversion, so the cost is blank",
        legality="conditional", moves_money=True,
        source_ids="S50,S38", url="https://www.pbc.gov.cn/tiaofasi/144941/3581332/4158143/index.html",
        us_side="Depends on where the receiving account is; a HK account is itself FBAR-reportable.",
        why="Sometimes the only route open to a person whose documents only support a HK destination.",
        caveat="No authority publishes the retail CNH spread for a personal conversion. Rather than "
               "repeat a rumour, the cost column is blank and the page states the exact cost of each "
               "1.00% of basis at every amount (IR-026). Offshore bank fees are likewise blank (CI12).",
    ),
    dict(
        id="M11", rank=11, family="Not available to you as described",
        name="QDII fund quota",
        name_zh="合格境内机构投资者（QDII）",
        legs="Buy a QDII product with RMB, redeem offshore",
        fee_model="unavailable", ceiling="Institutional quota; the individual buys a fund, not a currency",
        years_basis="n/a", verdict="A retail investment product, not a currency-conversion tool; eligibility unverified",
        legality="conditional", moves_money=False,
        source_ids="S41,S53", url="http://www.safe.gov.cn/tianjin/2019/0214/1098.html",
        us_side="A US person holding a PRC fund has PFIC reporting exposure, which is a separate problem.",
        why="It does convert exposure to foreign assets, indirectly.",
        caveat="You would still hold a PRC fund, and a US citizen's PFIC filing burden is severe. "
               "Whether a given branch will sell you one is not established in any source here.",
    ),
    dict(
        id="M12", rank=12, family="Not available to you as described",
        name="Cross-boundary Wealth Management Connect",
        name_zh="跨境理财通",
        legs="GBA-resident-only scheme, closed-loop, RMB settled",
        fee_model="unavailable", ceiling="Residents of the nine Guangdong-Hong Kong-Macao GBA cities; quota per investor",
        years_basis="n/a", verdict="Closed to a US citizen who is not a GBA resident; eligibility unverified",
        legality="conditional", moves_money=False,
        source_ids="S39,S40", url="http://gdjr.gd.gov.cn/gdjr/zwgk/jrzcfg/content/post_3520533.html",
        us_side="PFIC and FBAR exposure if it were available.",
        why="Not a route for this fact pattern.",
        caveat="Scheme rules restrict eligibility to GBA residents; nothing here extends it to a "
               "foreign-passport holder living in the US.",
    ),
    dict(
        id="M13", rank=13, family="Not a conversion",
        name="Spend the RMB abroad on a UnionPay card instead of converting it",
        name_zh="境外刷卡消费",
        legs="Card spending outside mainland China, settled in RMB",
        fee_model="unavailable", ceiling="Card limits; spending abroad does not consume the FX convenience amount",
        years_basis="n/a", verdict="Avoids conversion entirely but produces goods, not USD",
        legality="lawful", moves_money=False,
        source_ids="S35b", url="https://www.safe.gov.cn/hebei/2018/0409/1010.html",
        us_side="No remittance; normal consumption.",
        why="Zero conversion cost because there is no conversion.",
        caveat="It does not put dollars in a US account. Listed so the comparison is complete.",
    ),
    dict(
        id="M14", rank=14, family="Not a conversion",
        name="Leave the balance in CNY and let it pass to heirs",
        name_zh="保留人民币余额",
        legs="No transfer at all",
        fee_model="unavailable", ceiling="None",
        years_basis="n/a", verdict="Zero cost now; the FX and reporting questions simply move to your estate",
        legality="lawful", moves_money=False,
        source_ids="S23", url="https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
        us_side="The account stays FBAR-reportable while you hold it; heirs face the same file later.",
        why="Costs nothing today, and no rule compels conversion.",
        caveat="Currency risk and the same documentation problem remain, plus an estate to administer.",
    ),
    dict(
        id="M15", rank=15, family="Unlawful",
        name="Split the balance across relatives' USD 50,000 quotas",
        name_zh="分拆结售汇",
        legs="Multiple people's quotas used for one person's money",
        fee_model="unlawful", ceiling="Not permitted at all",
        years_basis="n/a", verdict="Penalty exposure 30%–100% of the amount plus a spot on the watch list",
        legality="unlawful", moves_money=True,
        source_ids="S07,S14,S11", url="https://www.safe.gov.cn/safe/2008/0806/5321.html",
        us_side="Relatives receiving and forwarding funds can trigger gift reporting and their own FBAR issues.",
        why="It looks cheaper because the visible bank fees are the same.",
        caveat="SAFE publishes these cases and penalises them; art. 39/40 fines run to the whole "
               "amount in serious cases, and the 关注名单 blocks legitimate business for years.",
    ),
    dict(
        id="M16", rank=16, family="Unlawful",
        name="Underground bank / matched orders (对敲)",
        name_zh="地下钱庄",
        legs="Pay RMB to an agent in China, receive USD from an agent abroad",
        fee_model="unlawful", ceiling="Not permitted at all",
        years_basis="n/a", verdict="Art. 45 applies: up to 100% fine, plus criminal liability above the threshold",
        legality="criminal", moves_money=True,
        source_ids="S07,S32,S34", url="https://www.safe.gov.cn/safe/2008/0806/5321.html",
        us_side="Funds of unknown provenance arriving in a US account invite structuring and money-laundering exposure.",
        why="It is the route that looks like it 'just works'.",
        caveat="The commission quoted is an unverifiable number, so this page leaves it blank. The "
               "statutory downside is not blank: 30%–100% of the amount under art. 45, and "
               "非法经营 under Criminal Law art. 225 once the amount is large.",
    ),
    dict(
        id="M17", rank=17, family="Unlawful",
        name="Buy USDT or another stablecoin and sell it abroad",
        name_zh="虚拟货币",
        legs="RMB to an OTC desk, USDT to an exchange, USD out",
        fee_model="unlawful", ceiling="Prohibited",
        years_basis="n/a", verdict="Illegal financial activity since 2021 and still illegal under the 2026 notice",
        legality="criminal", moves_money=True,
        source_ids="S29,S56", url="https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html",
        us_side="US exchanges report; unexplained inflows create their own US problems.",
        why="Popular advice online, and wrong.",
        caveat="银发〔2021〕237号 was repealed and replaced by 银发〔2026〕42号, which keeps "
               "virtual-currency business activity illegal. The 2021 notice's repeal does not legalise anything.",
    ),
    dict(
        id="M18", rank=18, family="Unlawful",
        name="Manufacture trade or service documents to buy FX",
        name_zh="虚构交易单证购汇",
        legs="Invoices or contracts that do not describe a real transaction",
        fee_model="unlawful", ceiling="Not permitted at all",
        years_basis="n/a", verdict="Art. 40: 30%–100% of the amount, funds returned, criminal referral possible",
        legality="criminal", moves_money=True,
        source_ids="S07,S14", url="https://www.safe.gov.cn/safe/2008/0806/5321.html",
        us_side="False documents in a US bank's onboarding are a US crime in their own right.",
        why="It removes the evidence problem on paper only.",
        caveat="art. 40 covers 以虚假、无效的交易单证骗购外汇. Banks review the underlying documents (S07 art. 12).",
    ),
    dict(
        id="M19", rank=19, family="Unlawful",
        name="Route it through a US relative as a 'gift' to dodge the FX rules",
        name_zh="以赠与名义规避",
        legs="RMB to a relative, relative sends USD from outside China",
        fee_model="unlawful", ceiling="Depends on facts; a genuine gift from a foreign person is lawful",
        years_basis="n/a", verdict="Only lawful if it is a real gift of the relative's own money; otherwise art. 39",
        legality="conditional", moves_money=True,
        source_ids="S07,U09", url="https://www.irs.gov/businesses/gifts-from-foreign-person",
        us_side="A genuine foreign gift over USD 100,000 needs Form 3520; the penalty reaches 25% of the gift.",
        why="Sometimes lawful, and people use the label for arrangements that are not gifts.",
        caveat="If the money was always yours and the relative is a conduit, the arrangement is a "
               "transfer in disguise and the FX penalty applies to the whole amount.",
    ),
    dict(
        id="M20", rank=20, family="Lawful — only if you own the company",
        name="Take a dividend from your own PRC company, then remit it",
        name_zh="外商投资企业利润汇出",
        legs="Audited profit, dividend resolution, withholding, then FX purchase and wire",
        fee_model="wire_fx_plus_docs", ceiling="No ceiling; tax and audit clearance required",
        years_basis="1", verdict="Same banking cost as M01, plus PRC dividend withholding and audit work",
        legality="conditional", moves_money=True,
        source_ids="S19,S20,S46,CS01", url="https://www.safe.gov.cn/safe/2017/0126/12679.html",
        us_side="Dividend is US income; the treaty rate allows a foreign tax credit (U15, U16).",
        why="The only route if the balance is company profit rather than personal savings.",
        caveat="Requires a company, audited accounts and a tax certificate before the bank will act.",
    ),
]

# --------------------------------------------------------------------------
# 5. Step-by-step
# --------------------------------------------------------------------------
STEPS = {
    "M01": [
        ("Open the file", "Collect the bank statements covering the whole balance, the ID that opened the account, and the Chinese tax receipts or withholding slips for the income that created it.", "S03", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"),
        ("Ask the bank to classify you", "Get the branch to confirm in writing whether its system holds you as 境内个人 or 境外个人, because that decides which article it processes under.", "S07", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("Confirm the route in writing", "Ask which provision it will use: current-account purchase on source-of-funds evidence (no annual quota), or another route. Get the checklist.", "S03", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"),
        ("Do the tax-document step if asked", "If a 税务备案表 or tax certificate is requested, obtain it from the tax bureau. This is a document precondition, not a tax on converting.", "S21", "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html"),
        ("Demand an all-in quote", "Ask for the customer rate, the timestamp, the reference rate, the transfer fee, the cable fee and the correspondent-charge treatment, in writing.", "S46", BOC_TARIFF_URL),
        ("Execute the purchase and the wire", "Buy USD at 现汇卖出价 and send one telegraphic transfer. Do not split it across people or days.", "CS01", BOC_URL),
        ("Reconcile what arrived", "Compare the USD credited with the quote. Shortfalls beyond the stated correspondent cost are a dispute, not a fee you agreed to.", "S46", BOC_TARIFF_URL),
        ("File the US side", "FBAR by 15 April (automatic extension to 15 October), Form 8938 with the return if the thresholds are met, and the CNY interest as income.", "U06", "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements"),
    ],
    "M02": [
        ("Check the account's classification", "This route is only open if the bank treats you as 境内个人. A US passport holder is usually 境外个人, which makes M01 the better route.", "S07", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("File the 个人购汇申请书", "Complete the purchase application and the 六不得 undertaking at the branch or in the app.", "S09", "https://www.safe.gov.cn/safe/file/file/20210402/30fab7a9646f417ca9d2f67ff4c1e5f0.pdf"),
        ("Buy up to USD 50,000", "Purchase within the annual convenience amount on ID alone.", "S01", "https://www.safe.gov.cn/ningxia/2022/0929/1997.html"),
        ("Wire it out", "One telegraphic transfer; expect the 1‰ fee capped at CNY 260 plus the cable fee.", "S46", BOC_TARIFF_URL),
        ("Repeat next calendar year", "The allowance resets per person per year, so USD 400,000 takes eight years at one person.", "S01", "https://www.safe.gov.cn/ningxia/2022/0929/1997.html"),
        ("Keep each year's FBAR", "The balance stays above the reporting threshold throughout, so file every year, not only the year you moved money.", "U06", "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements"),
    ],
    "M03": [
        ("Confirm you qualify under art. 2", "You must have moved from the mainland to a foreign country, and the property must have been owned before you acquired that emigrant status. Property acquired afterwards is outside this rule.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("Assemble the art. 8 file", "Written application, the 移民财产对外转移申请人情况表, the 个人财产对外转移外汇业务申请表, the police-issued 户籍注销证明 plus Chinese consular certification of your settlement abroad, proof of the property, and the tax authority's 税收证明 or 完税凭证.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("File one application for the whole amount", "Art. 6: one application covering all of it, not one per transfer. At or below RMB 500,000 the local SAFE branch decides; above that it goes to SAFE head office (art. 10).", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("Collect the 核准件", "The approval letter and 核准件 are what let the bank sell the FX; the branch cannot process the amount without them.", "S18", "http://m.safe.gov.cn/safe/2004/1116/4134.html"),
        ("Take tranche 1 — up to half", "Art. 6 caps the first payment at half the approved amount. Anything at or below RMB 200,000 may be paid in a single go.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("Take tranche 2 — up to half the remainder, after 1 year", "A second purchase and wire, so a second set of the 1‰ fee and cable charge. Art. 8 requires the previous 核准件 each time.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("Take tranche 3 — the balance, after 2 years", "A third purchase and wire, and the same tariff again. Total elapsed time from first payment: two years.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("Receive into your own account", "Art. 11: the bank must remit straight to your own account in your country of residence, and may not hand you cash inside China.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("File the US side", "No income arises from moving your own principal. Report the account while you still hold it.", "U02", "https://www.irs.gov/publications/p54"),
    ],
    "M04": [
        ("Confirm you are an 继承人 under art. 2", "A foreign citizen (or HK/Macau resident) who has lawfully inherited assets inside the mainland.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("Assemble the art. 9 file", "Application form, identity, consular certification of your settlement abroad, proof you inherited, the deceased's title documents and the tax authority's certificate — notarised where required.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("File once for the whole estate", "Art. 6: one application per deceased person; it may be paid in one go or in several transfers, and there is no two-year staging. Different deceased people need separate applications.", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("Buy FX and remit", "Same bank mechanics and same published tariff as every other route.", "S46", BOC_TARIFF_URL),
        ("Check the US character", "Inheritance is generally not US gross income for a US person, but the account was reportable while it existed.", "U02", "https://www.irs.gov/publications/p54"),
    ],
    "M05": [
        ("Sell the property and clear PRC tax", "The 20% rate on property-transfer income applies to the gain, and the clearance is a precondition to remitting.", "S23", "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html"),
        ("Establish the governing notice before you rely on it", "The 2004 rule covers emigrant and inheritance transfers only. Ask the branch to name the notice it uses for a non-resident seller; the guide the earlier register cited is now a dead link (IR-027).", "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
        ("Buy FX and remit the net proceeds", "Standard tariff: 1‰, cap CNY 260, cable CNY 150.", "S46", BOC_TARIFF_URL),
        ("Claim the foreign tax credit in the US", "The PRC tax on the gain is creditable against the US tax on the same gain.", "U05", "https://www.irs.gov/publications/p514"),
    ],
    "M06": [
        ("Find the original memo", "The exchange memo from when you converted foreign currency into RMB; it is valid for 24 months.", "S04", "https://www.safe.gov.cn/tianjin/2024/0430/2464.html"),
        ("Present it at the bank", "Buy back up to the amount you originally exchanged — no more.", "S04", "https://www.safe.gov.cn/tianjin/2024/0430/2464.html"),
        ("Remit", "Same wire and cable tariff.", "S46", BOC_TARIFF_URL),
    ],
    "M07": [
        ("Check the currency of the balance", "Only the portion already held in USD or another foreign currency qualifies.", "S04", "https://www.safe.gov.cn/tianjin/2024/0430/2464.html"),
        ("Present ID and remit", "Outward remittance from an FX savings account; no conversion step, so no spread is paid.", "S04", "https://www.safe.gov.cn/tianjin/2024/0430/2464.html"),
        ("Pay the tariff", "1‰ capped at CNY 260 plus the cable fee, on the USD amount.", "S46", BOC_TARIFF_URL),
    ],
    "M08": [
        ("Confirm the annual room left", "RMB 100,000 equivalent per natural year across all your cards, RMB 10,000 per card per day.", "S35", "https://www.safe.gov.cn/hubei/2019/0305/851.html"),
        ("Withdraw abroad", "Use the card at ATMs outside mainland China.", "S35", "https://www.safe.gov.cn/hubei/2019/0305/851.html"),
        ("Do not exceed the ceiling", "Breach suspends overseas cash withdrawal for the rest of this year and all of next year.", "S35", "https://www.safe.gov.cn/hubei/2019/0305/851.html"),
        ("Declare at the US border", "Cash over USD 10,000 brought in must be reported on FinCEN 105, with seizure risk if not.", "CS03", "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments"),
    ],
    "M09": [
        ("Split nothing and pack nothing clever", "Carrying is lawful; concealment is not, and art. 42 fines up to 20% of the amount.", "S07", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("Get a 携带证 above USD 5,000", "A designated FX bank issues it for the 5,000–10,000 band.", "S37", "https://www.safe.gov.cn/big5/big5/www.safe.gov.cn/tianjin/2024/0430/2466.html"),
        ("Stay under USD 10,000 per trip", "Above that is not permitted in principle, save for the listed special cases.", "S37", "https://www.safe.gov.cn/big5/big5/www.safe.gov.cn/tianjin/2024/0430/2466.html"),
        ("Declare on entry to the US", "FinCEN 105 for anything over USD 10,000 per group per trip.", "CS03", "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments"),
    ],
    "M10": [
        ("Establish that a personal channel exists", "Individual cross-border RMB remittance runs on the same current-account evidence rules; there is no open personal capital channel.", "S38", "https://www.pbc.gov.cn/tiaofasi/144941/3581332/4158143/index.html"),
        ("Price the offshore side", "No official source prices a personal CNH conversion, so the table stays blank here and shows the cost of each 1.00% of basis instead.", "S50", "https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201203/chapter4.pdf"),
        ("Add the offshore bank charges", "Not published in any register here; the table leaves them blank.", "S46", BOC_TARIFF_URL),
    ],
    "M15": [
        ("Understand what is prohibited", "Using other people's quotas for one person's money is 分拆结售汇; SAFE publishes the cases and the penalties.", "S14", "https://www.safe.gov.cn/hebei/2016/0328/615.html"),
        ("Understand the penalty", "art. 39/40: up to 30%, and 30%–100% of the amount if serious.", "S07", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("Understand the collateral damage", "A 关注名单 entry follows you for years and blocks ordinary FX business.", "S11", "https://www.safe.gov.cn/tianjin/2025/0613/2811.html"),
    ],
    "M16": [
        ("The fee is unverifiable", "No official source publishes an underground-bank commission, so this page leaves it blank rather than repeat a rumour.", "S07", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("The penalty is not", "art. 45: confiscation of the illegal gain plus a fine of up to 30%, or 30%–100% if serious.", "S07", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
        ("The criminal line", "非法买卖外汇 becomes 非法经营 under Criminal Law art. 225 above the judicial threshold.", "S34", "https://xczy.hncourt.gov.cn/public/detail.php?id=2739"),
    ],
    "M17": [
        ("Read the 2026 notice", "银发〔2026〕42号 keeps virtual-currency business activity illegal; the older 2021 notice was repealed, not the prohibition.", "S29", "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html"),
        ("Note the enforcement direction", "Eight agencies, 境内严禁, 境外严管.", "S56", "https://www.csrc.gov.cn/shanxi/c106408/c7616553/content.shtml"),
    ],
    "M19": [
        ("A real gift is fine", "A genuine gift of the relative's own money to you is lawful, and over USD 100,000 needs Form 3520.", "U09", "https://www.irs.gov/businesses/gifts-from-foreign-person"),
        ("A conduit is not", "If the money was always yours, the label does not change the FX analysis and art. 39 applies.", "S07", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
    ],
    "M20": [
        ("Audit and resolve the dividend", "Audited accounts and a dividend resolution, and the PRC withholding is settled first.", "S19", "https://www.safe.gov.cn/safe/2017/0126/12679.html"),
        ("Present the tax certificate", "The bank needs the tax position before it will sell FX for a profit remittance.", "S20", "https://www.safe.gov.cn/shanghai/2017/0126/76.html"),
        ("Buy FX and remit", "Standard 1‰ / CNY 260 / cable tariff.", "S46", BOC_TARIFF_URL),
        ("Credit the US tax", "Dividend is US income; the treaty allows a credit for the PRC tax.", "U16", "https://www.irs.gov/pub/irs-trty/china.pdf"),
    ],
}

# --------------------------------------------------------------------------
# 6. Cost calculation
# --------------------------------------------------------------------------
def _wire_fx(amount: float) -> dict:
    fee_cny = wire_total_cny(amount)
    return dict(
        cny_needed=amount * BOC_ASK,
        fee_cny=fee_cny,
        spread_usd=spread_cost_usd(amount),
        fixed_usd=fee_cny / BOC_ASK,
        units=1,
    )


def cost_row(method: dict, amount: float) -> dict:
    """Return the cost components for one method at one amount.

    Every returned money figure is either computed from a published input or None
    (meaning 'not published — left blank').
    """
    model = method["fee_model"]
    row = dict(
        method_id=method["id"], amount_usd=amount, cny_needed=None, spread_usd=None,
        bank_fee_usd=None, docs_usd=None, total_usd=None, cost_pct=None, net_usd=None,
        units=None, units_label="", penalty_max_usd=None, basis="",
        coef_usd=amount * 0.001,      # exact cost of every extra 0.10% of spread/basis
    )

    if model in ("wire_fx", "wire_fx_quota", "wire_fx_plus_docs"):
        if model == "wire_fx_quota":
            # Force the balance through USD 50,000 annual chunks.
            remaining, years, total = amount, 0, 0.0
            while remaining > 0:
                chunk = min(remaining, SAFE_CONVENIENCE_USD)
                comp = _wire_fx(chunk)
                total += comp["spread_usd"] + comp["fixed_usd"]
                remaining -= chunk
                years += 1
            comp = _wire_fx(amount)
            sp = amount * (BOC_ASK / BOC_MID - 1)
            row.update(cny_needed=amount * BOC_ASK, spread_usd=sp,
                       bank_fee_usd=total - sp, total_usd=total, units=years,
                       units_label="years (one transfer each)", basis="fees summed over N annual transfers")
        else:
            comp = _wire_fx(amount)
            total = comp["spread_usd"] + comp["fixed_usd"]
            row.update(cny_needed=comp["cny_needed"], spread_usd=comp["spread_usd"],
                       bank_fee_usd=comp["fixed_usd"], total_usd=total, units=1,
                       units_label="transfer", basis="spread + 1 wire + cable")
        if model == "wire_fx_plus_docs":
            row["docs_usd"] = None      # not published
            row["basis"] += "; document costs blank"
        row["cost_pct"] = row["total_usd"] / amount * 100
        row["net_usd"] = amount - row["total_usd"]

    elif model == "wire_nofx":
        comp = _wire_fx(amount)
        row.update(cny_needed=amount * BOC_ASK, spread_usd=0.0, bank_fee_usd=comp["fixed_usd"],
                   total_usd=comp["fixed_usd"], units=1, units_label="transfer",
                   basis="no conversion, so no spread; wire + cable only")
        row["cost_pct"] = row["total_usd"] / amount * 100
        row["net_usd"] = amount - row["total_usd"]

    elif model == "atm_cash":
        years = math.ceil(amount * BOC_ASK / ATM_YEAR_CNY)
        row.update(cny_needed=amount * BOC_ASK, total_usd=None, cost_pct=None, net_usd=None,
                   units=years, units_label="years (RMB 100,000/yr ceiling)",
                   basis="per-withdrawal fee not published by SAFE or the card scheme")

    elif model == "carry_cash":
        trips = math.ceil(amount / CASH_PERMIT_MAX_USD)
        row.update(cny_needed=amount * BOC_ASK, total_usd=0.0, cost_pct=0.0, net_usd=amount,
                   units=trips, units_label="trips (USD 10,000 per trip)",
                   basis="no bank fee; physical carriage, permit and declaration required",
                   penalty_max_usd=amount * 0.20)

    elif model == "offshore_cnh":
        row.update(cny_needed=amount * BOC_ASK, spread_usd=amount * CNH_STRESS_BASIS,
                   bank_fee_usd=None, total_usd=amount * CNH_STRESS_BASIS,
                   cost_pct=CNH_STRESS_BASIS * 100, net_usd=amount * (1 - CNH_STRESS_BASIS),
                   units=1, units_label="conversion",
                   basis="HKMA-measured 1.94% stress basis; offshore fees blank")

    elif model == "emigrant_staged":
        # PBC [2004] No.16 art. 6: at most half, then half the remainder after 1 year,
        # then the rest after 2 years; anything <= RMB 200,000 may go in one payment.
        if amount * BOC_ASK <= 200_000:
            tranches, years = [1.0], 0
        else:
            tranches, years = [0.50, 0.25, 0.25], 2
        fee_usd = 0.0
        for share in tranches:
            fee_usd += wire_total_cny(amount * share) / BOC_ASK
        sp = amount * (BOC_ASK / BOC_MID - 1)
        row.update(cny_needed=amount * BOC_ASK, spread_usd=sp, bank_fee_usd=fee_usd,
                   total_usd=sp + fee_usd, units=len(tranches),
                   units_label="payments over 2 years" if years else "single payment",
                   basis="art. 6 staging: %d purchase(s), each paying the 1‰ fee and cable charge"
                         % len(tranches))
        row["cost_pct"] = row["total_usd"] / amount * 100
        row["net_usd"] = amount - row["total_usd"]

    elif model == "offshore_unverified":
        row.update(cny_needed=amount * BOC_ASK, total_usd=None, cost_pct=None, net_usd=None,
                   units=1, units_label="conversion",
                   basis="no published retail CNH spread; blank, with the 0.10% coefficient given")

    elif model == "unlawful":
        row.update(total_usd=None, cost_pct=None, net_usd=None, penalty_max_usd=amount * 1.00,
                   units=None, units_label="n/a",
                   basis="no published fee; statutory maximum 100% of the amount (art. 39/40/45)")

    elif model == "unavailable":
        row.update(total_usd=None, cost_pct=None, net_usd=None, units=None, units_label="n/a",
                   basis="no lawful or available path for this fact pattern")

    return row


def ladder():
    return [cost_row(m, a) for m in METHODS for a in AMOUNTS]
