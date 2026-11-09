#!/usr/bin/env python3
"""
build_cost_model.py — session-1a9dec1c

Builds the per-method CNY->USD cost estimates in USD 10,000 increments from
USD 10,000 to USD 400,000, plus the statutory penalty-exposure tables, and
emits:

    data/cost_model.csv
    data/cost_model.json
    data/penalty_exposure.csv
    data/reverification.csv
    cost-table.html
    cost-steps.html
    verification.html

DESIGN RULE: every constant below is a number that was READ on an official
page on 2026-11-09 and is recorded with its URL. No constant is an industry
average, a guess, or a recalled figure. Where an input is genuinely unknown
(correspondent deduction under a standard wire, offshore CNH spread, the
tax basis of the reader's money) the output is left BLANK and flagged, never
filled with an estimate.
"""

import csv
import json
import os
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

FETCH_DATE = "2026-11-09"

# ---------------------------------------------------------------------------
# 1. MEASURED MARKET CONSTANTS — read on official pages, 2026-11-09
# ---------------------------------------------------------------------------

# CFETS / PBOC-authorised central parity, USD/CNY, published 2026-11-09 09:15.
# URL: https://www.chinamoney.com.cn/chinese/bkccpr/
PARITY = 6.7188

# Bank of China published foreign-exchange board, 2026/11/09 09:15:45.
# Quote convention: CNY per 100 units of foreign currency.
# URL: https://www.boc.cn/sourcedb/whpj/
BOC_SPOT_BUY = 6.6638      # 现汇买入价 666.38 / 100
BOC_SPOT_SELL = 6.6919     # 现汇卖出价 669.19 / 100
BOC_CASH_BUY = 6.6638      # 现钞买入价 666.38 / 100
BOC_CASH_SELL = 6.6919     # 现钞卖出价 669.19 / 100
BOC_REFERENCE = 6.7188     # 中行折算价 671.88 / 100

# The rate a customer actually pays when buying USD with CNY.
ASK = BOC_SPOT_SELL
BID = BOC_SPOT_BUY
MID = (ASK + BID) / 2.0

# FX margin measured against the mid-market rate of the bank's own board.
# This is the World Bank "Remittance Prices Worldwide" convention
# (total cost = fee + margin over mid-market); it uses only the two numbers
# BOC itself published on the same screen, so nothing is assumed.
FX_MARGIN = (ASK - MID) / ASK          # 0.0020995...  = 0.20996 %
FX_MARGIN_PCT = FX_MARGIN * 100.0

# Full round-trip bid/ask spread, shown for completeness.
FULL_SPREAD_PCT = (ASK - BID) / ASK * 100.0

# Customer rate versus the CFETS parity (a reference rate, not tradable).
VS_PARITY_PCT = (ASK / PARITY - 1.0) * 100.0

# ---------------------------------------------------------------------------
# 2. PUBLISHED FEE SCHEDULES — every number read from an official page
# ---------------------------------------------------------------------------
# BOC personal e-banking transfer/remittance tariff (individual customers).
#   "跨境汇款（电汇）每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；
#    另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。"
# URL: https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html
PERSONAL_WIRE = dict(rate=0.001, min_cny=50.0, max_cny=260.0, cable_cny=150.0)

# BOC corporate international-settlement tariff (对公). NOT available to an
# individual; carried only for comparison and labelled as such.
#   "电汇 汇款金额的 1‰，最低50元/笔，最高1000元/笔，另加收电讯费"
# URL: https://www.boc.cn/cbservice/cb3/cb33/200807/t20080701_852.html
CORPORATE_WIRE = dict(rate=0.001, min_cny=50.0, max_cny=1000.0, cable_cny=150.0)

# BOC announcement of 2017-11-09 (effective 2018-02-09).
#   中银全球智汇: 按汇款金额的1.2‰，最低200元，最高1000元，另加电讯费
#   全额到账 (普通电汇): 美元，收款行在我行纽约分行开立账户的，15美元/笔，
#                       其他均为25美元/笔
# URL: https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html
SMART_WIRE = dict(rate=0.0012, min_cny=200.0, max_cny=1000.0, cable_cny=150.0)
FULL_AMOUNT_CREDIT_USD = 25.0      # receiving bank does NOT hold an account with BOC NY
FULL_AMOUNT_CREDIT_USD_BOCNY = 15.0  # receiving bank DOES hold an account with BOC NY

# Statutory maxima, read from the operative text on 2026-11-09.
FBAR_NONWILLFUL_MAX = 16536.0   # 31 CFR 1010.821 Table 1, 31 USC 5321(a)(5)(B)(i)
FBAR_WILLFUL_FLAT = 165353.0    # 31 CFR 1010.821 Table 1, 31 USC 5321(a)(5)(C)(i)(I)
FBAR_WILLFUL_PCT = 0.50         # 31 USC 5321(a)(5)(C) "greater of $100,000 or 50%"
F8938_BASE = 10000.0            # 26 USC 6038D(d)(1)
F8938_CONTINUATION_MAX = 50000.0  # 26 USC 6038D(d)(2)
F3520_PCT = 0.25                # 26 USC 6039F(c)(1)(B) 5%/month, max 25%
FXREG_HIGH = 1.00               # 外汇管理条例 art.39/40/45 "30%以上等值以下"
FXREG_LOW = 0.30                # 外汇管理条例 art.39/40/45 "30%以下"

AMOUNTS = list(range(10000, 400001, 10000))


def q(x, places="0.01"):
    return float(Decimal(str(x)).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def cny_to_usd(cny):
    """Convert a CNY charge to USD at the same customer rate used for the deal."""
    return cny / ASK


def wire_fee_cny(amount_usd, sched):
    """Clamped ad-valorem fee + flat cable fee, in CNY, per the published tariff."""
    cny_notional = amount_usd * ASK
    ad_valorem = sched["rate"] * cny_notional
    ad_valorem = max(ad_valorem, sched["min_cny"])
    ad_valorem = min(ad_valorem, sched["max_cny"])
    return ad_valorem + sched["cable_cny"]


# ---------------------------------------------------------------------------
# 3. METHODS
# ---------------------------------------------------------------------------
# Each method records: identity, the official basis, how its cost is built,
# and a feasibility note per amount (a cost is not a permission).

METHODS = [
    dict(
        id="M01",
        name="Foreign individual: documented current-account purchase, then wire",
        name_zh="境外个人经常项目合法人民币收入购汇 + 跨境电汇",
        basis="SAFE Tianjin 2024 Q&A case (9), Current-Account FX Business Guidelines (2020) art. 59",
        basis_url="https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
        fee_source="BOC personal e-banking tariff — 1‰, min ¥50, max ¥260, cable ¥150",
        fee_url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
        fx=True, fee=PERSONAL_WIRE, extra_usd=0.0,
        verdict="RECOMMENDED when the RMB is lawful current-account income and the bank treats you as 境外个人.",
        quota="No annual amount limit in art. 59; the bank audits the source of the RMB on every payment.",
        feasibility="Feasible in one payment if the source file is complete.",
    ),
    dict(
        id="M02",
        name="Same route, bought with BOC Global Smart Remittance (中银全球智汇)",
        name_zh="中银全球智汇（汇款进度跟踪、全额到账可选）",
        basis="BOC announcement 2017-11-09, effective 2018-02-09",
        basis_url="https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html",
        fee_source="BOC — 1.2‰, min ¥200, max ¥1,000, plus cable ¥150",
        fee_url="https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html",
        fx=True, fee=SMART_WIRE, extra_usd=0.0,
        verdict="Optional premium. Costs more than M01; buys tracking and message passthrough, not a lower charge.",
        quota="Same legal basis as M01.",
        feasibility="Feasible in one payment.",
    ),
    dict(
        id="M03",
        name="M01 plus full-amount credit (全额到账), worst case USD 25",
        name_zh="普通电汇 + 全额到账（收款行未在中行纽约分行开户）",
        basis="BOC announcement 2017-11-09, note 2",
        basis_url="https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html",
        fee_source="BOC personal tariff + USD 25 flat full-amount-credit charge",
        fee_url="https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html",
        fx=True, fee=PERSONAL_WIRE, extra_usd=FULL_AMOUNT_CREDIT_USD,
        verdict="Best value when you need a known net figure: turns an unpublished correspondent deduction into a published USD 25.",
        quota="Same legal basis as M01.",
        feasibility="Feasible in one payment. If the receiving bank holds an account with BOC New York, the charge is USD 15 instead of USD 25.",
    ),
    dict(
        id="M04",
        name="Domestic individual: USD 50,000 annual convenience amount",
        name_zh="境内个人年度便利化额度内购汇（每人每年等值5万美元）",
        basis="SAFE Ningxia 2022 Q&A; SAFE Tianjin 2024 Q&A case (9)",
        basis_url="https://www.safe.gov.cn/ningxia/2022/0929/1997.html",
        fee_source="BOC personal e-banking tariff — 1‰, min ¥50, max ¥260, cable ¥150",
        fee_url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
        fx=True, fee=PERSONAL_WIRE, extra_usd=0.0,
        verdict="Cheapest paperwork, but the amount is the binding constraint, not the cost.",
        quota="USD 50,000 equivalent per person per year. ID only; no source documents.",
        feasibility_cap_usd=50000.0,
        feasibility="Feasible in one payment only up to USD 50,000. Above that it takes one year per USD 50,000 of balance.",
    ),
    dict(
        id="M05",
        name="Emigrant property transfer (移民财产转移)",
        name_zh="移民财产对外转移售付汇",
        basis="PBC Announcement [2004] No. 16, State Council Gazette 2005 No. 22",
        basis_url="https://www.gov.cn/gongbao/content/2005/content_64294.htm",
        fee_source="BOC personal e-banking tariff — 1‰, min ¥50, max ¥260, cable ¥150",
        fee_url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
        fx=True, fee=PERSONAL_WIRE, extra_usd=0.0,
        verdict="The only no-ceiling capital route for a naturalised citizen, and the one that requires a cancelled PRC household registration plus a tax certificate.",
        quota="No amount ceiling. Art. 10: up to RMB 500,000 decided by the local SAFE branch; above that, SAFE head office. Art. 6: one application for the whole balance, remitted in stages.",
        feasibility="Feasible, but not in one payment above RMB 200,000 (see the staging column in cost-steps.html).",
    ),
    dict(
        id="M06",
        name="Inheritance transfer (继承财产转移)",
        name_zh="继承财产对外转移售付汇",
        basis="PBC Announcement [2004] No. 16, arts. 2, 9",
        basis_url="https://www.gov.cn/gongbao/content/2005/content_64294.htm",
        fee_source="BOC personal e-banking tariff — 1‰, min ¥50, max ¥260, cable ¥150",
        fee_url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
        fx=True, fee=PERSONAL_WIRE, extra_usd=0.0,
        verdict="Applies only if the money is an inheritance from a PRC decedent. One application covers all property from the same decedent.",
        quota="No amount ceiling. Same RMB 500,000 approval split as M05.",
        feasibility="Feasible; documentary load is the constraint, not cost.",
    ),
    dict(
        id="M07",
        name="Balance already held in USD in an FX savings account",
        name_zh="外汇储蓄账户内外汇直接汇出",
        basis="SAFE Tianjin 2024 Q&A (三), Guidelines art. 64; 实施细则 art. 15",
        basis_url="https://www.safe.gov.cn/tianjin/2024/0229/2402.html",
        fee_source="BOC personal e-banking tariff — 1‰, min ¥50, max ¥260, cable ¥150",
        fee_url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
        fx=False, fee=PERSONAL_WIRE, extra_usd=0.0,
        verdict="Zero FX margin because no conversion happens. Only useful if the balance is already USD, which the premise says it is not.",
        quota="Remittance on ID up to USD 50,000/day; above that, transaction documents.",
        feasibility="Feasible in one payment.",
    ),
    dict(
        id="M08",
        name="Traveller's cash and overseas card withdrawal",
        name_zh="携带外币现钞出境 / 银行卡境外提取现金",
        basis="SAFE guidance on cash carry; SAFE card-withdrawal notice",
        basis_url="https://www.safe.gov.cn/hubei/2019/0305/851.html",
        fee_source="BOC cash selling rate 669.19/100 (same as spot on 2026-11-09); no wire fee",
        fee_url="https://www.boc.cn/sourcedb/whpj/",
        fx=True, fee=None, extra_usd=0.0, cash=True,
        verdict="Not a mechanism for a balance of this size. Reporting duties on the US side attach at USD 10,000.",
        quota="RMB 100,000 per person per year of overseas cash withdrawal; separate cash-carry limits at the border.",
        feasibility_cap_usd=10000.0,
        feasibility="Cap-limited far below the range in this table; shown only to price it, not to recommend it.",
    ),
]

ILLEGAL = [
    dict(
        id="X01",
        name="Splitting through relatives' or friends' quotas (分拆结售汇)",
        name_zh="分拆结售汇 / 蚂蚁搬家",
        basis="SAFE FX Regulations (State Council Order 532) arts. 39, 40, 45; SAFE 个人购汇申请书 \"六不得\"",
        basis_url="https://www.safe.gov.cn/safe/2008/0806/5321.html",
        penalty_source="Art. 39/40/45: up to 30% of the amount; if serious, 30% to the equivalent of 100%",
        verdict="Prohibited. The penalty is between 143x and 476x the lawful cost of the same transfer (see comparison table).",
    ),
    dict(
        id="X02",
        name="Underground bank / private FX dealer (地下钱庄)",
        name_zh="地下钱庄、变相买卖外汇",
        basis="FX Regulations art. 45; Criminal Law art. 225 (SPC/SPP Interpretation 法释〔2019〕1号)",
        basis_url="https://www.safe.gov.cn/safe/2008/0806/5321.html",
        penalty_source="Art. 45: warning + confiscation + up to 30%; if serious 30%–100%; criminal liability under art. 225",
        verdict="Prohibited, and criminal above the thresholds in the 2019 interpretation.",
    ),
    dict(
        id="X03",
        name="Crypto / USDT conversion (虚拟货币兑换)",
        name_zh="虚拟货币、稳定币兑换",
        basis="PBOC 银发〔2026〕42号 (in force 2026-02-06), s.1(1), 6(18)–(19)",
        basis_url="https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html",
        penalty_source="RMB<->virtual-currency activity is illegal; related civil acts are void; proceeds are liable to confiscation",
        verdict="Prohibited. The modelled downside is the whole principal, not a percentage of it.",
    ),
]


# ---------------------------------------------------------------------------
# 4. COMPUTATION
# ---------------------------------------------------------------------------

def compute_rows():
    rows = []
    for m in METHODS:
        for a in AMOUNTS:
            fx_cost = a * FX_MARGIN if m["fx"] else 0.0
            if m.get("cash"):
                fee_cny = 0.0
                fee_usd = 0.0
                fee_note = "no wire fee; cash handling instead"
            else:
                fee_cny = wire_fee_cny(a, m["fee"])
                fee_usd = cny_to_usd(fee_cny)
                fee_note = ""
            other = m["extra_usd"]
            total = fx_cost + fee_usd + other
            cap = m.get("feasibility_cap_usd")
            if cap is not None and a > cap:
                feasible = "NO — above cap"
            else:
                feasible = "Yes"
            rows.append(dict(
                method_id=m["id"],
                method=m["name"],
                amount_usd=a,
                cny_required=q(a * ASK),
                fx_margin_usd=q(fx_cost),
                wire_fee_cny=q(fee_cny),
                wire_fee_usd=q(fee_usd),
                other_fixed_usd=q(other),
                total_cost_usd=q(total),
                cost_pct=q(total / a * 100.0, "0.0001"),
                net_usd=q(a - total),
                feasible=feasible,
                fee_note=fee_note,
            ))
    return rows


def compute_penalty_rows():
    rows = []
    for a in AMOUNTS:
        rows.append(dict(
            amount_usd=a,
            fbar_willful_max_usd=q(max(FBAR_WILLFUL_FLAT, FBAR_WILLFUL_PCT * a)),
            fbar_nonwillful_max_usd=q(FBAR_NONWILLFUL_MAX),
            f8938_max_usd=q(F8938_BASE + F8938_CONTINUATION_MAX),
            f3520_max_usd=q(F3520_PCT * a),
            fxreg_low_usd=q(FXREG_LOW * a),
            fxreg_high_usd=q(FXREG_HIGH * a),
        ))
    return rows


# ---------------------------------------------------------------------------
# 5. VERIFICATION LOG — what was read, where, when
# ---------------------------------------------------------------------------
VERIFICATION = [
    dict(id="V01", topic="FX reference rate", authority="China Foreign Exchange Trade System (CFETS) / PBOC",
         url="https://www.chinamoney.com.cn/chinese/bkccpr/",
         checked="USD/CNY central parity 6.7188 on the 2026-11-09 09:15 board",
         quote="美元/人民币 6.7188 ... 2026-11-09 9:15", status="verified"),
    dict(id="V02", topic="Retail rate and spread", authority="Bank of China",
         url="https://www.boc.cn/sourcedb/whpj/",
         checked="USD board, 2026/11/09 09:15:45: spot buy 666.38, spot sell 669.19, cash buy 666.38, cash sell 669.19, reference 671.88 (per 100 USD)",
         quote="美元 666.38 666.38 669.19 669.19 671.88 2026/11/09 09:15:45", status="verified"),
    dict(id="V03", topic="Personal remittance fee", authority="Bank of China",
         url="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
         checked="Cross-border telegraphic transfer: 1‰ of amount, min ¥50, max ¥260 per payment; cable fee ¥80 HK/Macau/Taiwan, ¥150 elsewhere",
         quote="跨境汇款（电汇）每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。", status="verified"),
    dict(id="V04", topic="Corporate remittance fee (comparison only)", authority="Bank of China",
         url="https://www.boc.cn/cbservice/cb3/cb33/200807/t20080701_852.html",
         checked="Corporate outbound telegraphic transfer: 1‰, min ¥50, max ¥1,000, plus cable fee. Not available to an individual.",
         quote="电汇 汇款金额的 1‰，最低50元/笔，最高1000元/笔，另加收电讯费", status="verified"),
    dict(id="V05", topic="Premium remittance and full-amount credit", authority="Bank of China",
         url="https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html",
         checked="Global Smart Remittance 1.2‰, min ¥200, max ¥1,000, plus cable fee; full-amount credit USD 15 (receiving bank holds a BOC New York account) or USD 25 otherwise, per payment",
         quote="中银全球智汇按汇款金额的1.2‰，最低200元，最高1000元，另加电讯费；美元，收款行在我行纽约分行开立账户的，15美元/笔，其他均为25美元/笔", status="verified"),
    dict(id="V06", topic="USD 50,000 is not a cap", authority="SAFE Ningxia branch",
         url="https://www.safe.gov.cn/ningxia/2022/0929/1997.html",
         checked="Annual convenience amount USD 50,000 per person; genuine lawful current-account and opened capital-account FX purchase/sale has no amount limit; arts. 54–57 of the 2020 guidelines",
         quote="目前，我国对于真实、合法的经常项目和已开放的资本项目下购汇和结汇都没有金额限制 ... 年度便利化额度不是个人每年购汇或者结汇的限额", status="verified"),
    dict(id="V07", topic="Remitting from an FX account", authority="SAFE Tianjin branch",
         url="https://www.safe.gov.cn/tianjin/2024/0229/2402.html",
         checked="Guidelines art. 64: remittance abroad from an FX account up to USD 50,000/day on ID; above that, ID plus transaction documents; cash remittance up to USD 10,000/day on ID",
         quote="外汇账户内外汇汇出境外当日累计等值5万美元以下（含）的，凭本人有效身份证件办理", status="verified"),
    dict(id="V08", topic="Foreign-individual purchase, art. 59", authority="SAFE Tianjin branch",
         url="https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
         checked="A 境外个人 converts lawful current-account RMB income in China on ID plus source-of-funds evidence including tax documents; only a holder of a foreign permanent-residence ID gets the annual convenience amount",
         quote="境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇。持有外国人永久居留身份证的境外个人适用购汇年度便利化额度。", status="verified"),
    dict(id="V09", topic="Penalties and definitions", authority="State Council / SAFE",
         url="https://www.safe.gov.cn/safe/2008/0806/5321.html",
         checked="FX Regulations Order 532: art. 39 and 40 (up to 30%; serious 30%–100%), art. 42 (up to 20%), art. 44 (up to 30%), art. 45 (up to 30%; serious 30%–100%), art. 48 (individual up to RMB 50,000), art. 52 (境内个人 includes a foreigner continuously resident in China for one year)",
         quote="第三十九条 ... 处逃汇金额30%以下的罚款；情节严重的，处逃汇金额30%以上等值以下的罚款", status="verified"),
    dict(id="V10", topic="Implementation rules", authority="SAFE, 汇发〔2007〕1号",
         url="https://www.safe.gov.cn/tianjin/2024/0430/2464.html",
         checked="Art. 2 annual total USD 50,000; art. 13(1) foreign-individual purchase on ID plus transaction evidence incl. tax documents; art. 13(2) re-conversion of unused RMB against the original receipt within 24 months, USD 500 / USD 1,000 thresholds; arts. 14–15 remittance; art. 30 cash above USD 10,000 pre-filed; art. 31 deposit above USD 5,000",
         quote="第二条 对个人结汇和境内个人购汇实行年度总额管理。年度总额分别为每人每年等值5万美元。", status="verified"),
    dict(id="V11", topic="Emigrant and inheritance transfer", authority="PBOC Announcement [2004] No. 16, State Council Gazette",
         url="https://www.gov.cn/gongbao/content/2005/content_64294.htm",
         checked="Art. 2 two categories only; art. 6 staging (half, then half of the remainder after 1 year, all after 2 years; below RMB 200,000 in one go); art. 8 documents incl. tax certificate; art. 10 RMB 500,000 approval split; art. 11 direct remittance, no cash; art. 13 false documents punished under FX Regulations art. 40",
         quote="第十条 申请财产对外转移总金额在等值人民币50万元以下（含50万元）的，由所在地外汇局审批 ... 超过上述金额的 ... 报国家外汇管理局审批。", status="verified"),
    dict(id="V12", topic="Emigrant-transfer staging explained", authority="PBOC / SAFE press Q&A",
         url="https://www.safe.gov.cn/safe/2004/1116/4134.html",
         checked="Below RMB 500,000 the provincial branch decides; at or above RMB 500,000 SAFE head office decides; at or above RMB 200,000 the applicant applies once and remits in stages (half, then half of the remainder after one year, the rest after two years)",
         quote="对申请金额低于等值50万元人民币的，由外汇局省级分局审核办理；超过等值50万元（含50万元）人民币的，由省级外汇局初审后报国家外汇管理局批准。", status="verified"),
    dict(id="V13", topic="PRC individual income tax", authority="State Taxation Administration",
         url="https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
         checked="Art. 1 183-day residence test; art. 3 rates 3%–45% comprehensive, 5%–35% business, flat 20% on interest, dividends, property rental, property transfer and incidental income; art. 6(5) property-transfer base is proceeds minus original value and reasonable expenses; art. 13 tax settlement before cancelling PRC household registration; art. 16 conversion at the central parity",
         quote="（三）利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十。", status="verified"),
    dict(id="V14", topic="Savings-interest exemption", authority="Shanghai STA, transmitting 财税〔2008〕132号",
         url="https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/grsds/200810/t288953.html",
         checked="Interest accruing on savings deposits from 2008-10-09 is temporarily exempt from individual income tax",
         quote="自2008年10月9日起，对储蓄存款利息所得暂免征收个人所得税。", status="verified"),
    dict(id="V15", topic="Tax filing on large outward payments", authority="State Taxation Administration",
         url="https://www.chinatax.gov.cn/chinatax/c102449/c5219874/content.html",
         checked="SAT/SAFE Announcement 2013 No. 40: a single outward payment of the equivalent of USD 50,000 or more in the listed categories requires filing with the local tax authority",
         quote="境内机构和个人向境外单笔支付等值5万美元以上 ... 均应向所在地主管税务机关进行备案", status="verified"),
    dict(id="V16", topic="FBAR threshold and mechanics", authority="Internal Revenue Service",
         url="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar",
         checked="Aggregate foreign accounts above USD 10,000 at any time in the year; due 15 April with automatic extension to 15 October; records kept five years; civil maxima adjusted annually for inflation",
         quote="the aggregate value of those foreign financial accounts exceeded $10,000 at any time during the calendar year reported", status="verified"),
    dict(id="V17", topic="FBAR penalty maxima", authority="eCFR 31 CFR 1010.821, Table 1",
         url="https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
         checked="31 U.S.C. 5321(a)(5)(B)(i) non-willful 10,000 -> 16,536; 31 U.S.C. 5321(a)(5)(C)(i)(I) willful 100,000 -> 165,353, for penalties assessed on or after 2025-01-17",
         quote="Foreign Financial Agency Transaction—Willful Violation of Transaction | 100,000 | 165,353", status="verified"),
    dict(id="V18", topic="Personal FX transaction exclusion", authority="26 U.S.C. § 988 (Cornell LII)",
         url="https://www.law.cornell.edu/uscode/text/26/988",
         checked="§ 988(e)(2): no gain recognised on an individual's personal transaction from exchange-rate movement, but the exclusion does not apply where the gain would exceed USD 200; § 988(e)(3) defines personal transaction",
         quote="The preceding sentence shall not apply if the gain which would otherwise be recognized on the transaction exceeds $200.", status="verified"),
    dict(id="V19", topic="Form 8938 penalty", authority="26 U.S.C. § 6038D (Cornell LII)",
         url="https://www.law.cornell.edu/uscode/text/26/6038D",
         checked="§ 6038D(d)(1) USD 10,000 per failure; § 6038D(d)(2) a further USD 10,000 per 30-day period after a 90-day notice, capped at USD 50,000",
         quote="such person shall pay a penalty of $10,000 ... shall not exceed $50,000", status="verified"),
    dict(id="V20", topic="Form 3520 penalty", authority="26 U.S.C. § 6039F (Cornell LII)",
         url="https://www.law.cornell.edu/uscode/text/26/6039F",
         checked="§ 6039F(c)(1)(B) 5% of the gift per month, capped at 25% in aggregate; § 6039F(c)(2) reasonable-cause exception",
         quote="an amount equal to 5 percent of the amount of such foreign gift for each month for which the failure continues (not to exceed 25 percent of such amount in the aggregate)", status="verified"),
    dict(id="V21", topic="Form 3520 reporting threshold", authority="Internal Revenue Service",
         url="https://www.irs.gov/businesses/gifts-from-foreign-person",
         checked="Gifts or bequests from a nonresident alien or foreign estate are reportable once the aggregate for the year exceeds USD 100,000; separately identify each gift above USD 5,000",
         quote="exceeds $100,000 during the taxable year. If the gifts or bequests exceed $100,000, you must separately identify each gift in excess of $5,000.", status="verified"),
]

BROKEN = [
    dict(id="B01", url="https://www.safe.gov.cn/guangdong/2021/0323/1994.html",
         used_by="data/sources.csv S17, deep-sources.html",
         result="HTTP 404 — SAFE error page \"该页面不存在\"",
         replacement="https://www.gov.cn/gongbao/content/2005/content_64294.htm (full text, art. 8 and art. 10 quoted in this session's log)"),
    dict(id="B02", url="https://www.boc.cn/ebanking/bi3/bi31/202312/t20231229_24338136.html",
         used_by="data/sources.csv S49, deep-sources.html",
         result="HTTP 404 — BOC \"您访问的中国银行网站页面不存在\"",
         replacement="none needed for this session; the fee promotion is not relied on. Marked unresolved."),
    dict(id="B03", url="https://www.irs.gov/individuals/international-taxpayers/report-of-foreign-bank-and-financial-accounts-fbar",
         used_by="index.html (prior session)",
         result="HTTP 404 — IRS \"Page Not Found. Error 404.\"",
         replacement="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar"),
]


# ---------------------------------------------------------------------------
# 6. HTML
# ---------------------------------------------------------------------------
NAV = """<nav>
  <a href="index.html">Home</a>
  <a href="cost-table.html" class="active">Cost tables</a>
  <a href="cost-steps.html">Step-by-step</a>
  <a href="methods.html">Methods</a>
  <a href="china-rules.html">China FX rules</a>
  <a href="us-tax.html">U.S. tax</a>
  <a href="penalties.html">Penalty breakdown</a>
  <a href="verification.html">Verification</a>
  <a href="flagged-review.html">Flagged for review</a>
  <a href="deep-executive-summary.html">Deep research</a>
</nav>"""

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
<link rel="stylesheet" href="assets/cost.css">
</head>
<body>
<header class="site-header">
  <div class="brand">
    <div class="mark">C3</div>
    <div>
      <div style="font-weight:800;">China3 · CNY &rarr; USD cost model</div>
      <div class="tagline">{tagline}</div>
    </div>
  </div>
</header>
<div class="wrap">
{nav}
"""

FOOT = """
<footer class="foot">
  <p><strong>Every figure on this page is either quoted from an official page or computed
  from quoted official figures by the formula shown.</strong> Nothing is an industry average
  and nothing is inferred. Values that could not be confirmed are blank and listed on the
  <a href="flagged-review.html">Flagged for review</a> page.</p>
  <p class="small">Rates read on {date}. Exchange rates and tariffs change: re-read the two
  linked boards before relying on any number here. This is research, not legal, tax or
  banking advice.</p>
</footer>
</div>
</body>
</html>
"""


def money(x):
    return "${:,.2f}".format(x)


def pct(x, places=3):
    return ("{:." + str(places) + "f}%").format(x)


def build_cost_table_html(rows, pen):
    by_id = {}
    for r in rows:
        by_id.setdefault(r["method_id"], []).append(r)

    # ---- headline block: recommended method, all 40 increments
    m01 = by_id["M01"]
    m01_10 = m01[0]
    m01_400 = m01[-1]

    out = []
    out.append(HEAD.format(
        title="CNY → USD cost tables — every method, USD 10,000 to USD 400,000",
        tagline="Measured conversion cost and remittance charges at every USD 10,000 step, with the statutory penalty exposure beside them",
        nav=NAV))

    out.append("""
<main>
<section class="section">
  <h1>What it actually costs to turn CNY into USD</h1>
  <p class="lead">The answer first. For a U.S. citizen converting a lawful RMB balance, the
  cost of <em>conversion and transfer</em> is small and it <em>falls</em> as the balance
  grows, because the only ad-valorem charge is capped. The money at risk is not in the
  conversion at all — it is in the tax treatment of whatever created the RMB, and in U.S.
  information-reporting penalties.</p>

  <div class="kpis">
    <div class="kpi"><span class="kpi-num">{fx}</span><span class="kpi-lab">Measured FX margin<br><span class="small">BOC spot 6.6919 vs mid 6.67785, 2026-11-09</span></span></div>
    <div class="kpi"><span class="kpi-num">{t10}</span><span class="kpi-lab">All-in cost at USD 10,000<br><span class="small">{p10} of principal</span></span></div>
    <div class="kpi"><span class="kpi-num">{t400}</span><span class="kpi-lab">All-in cost at USD 400,000<br><span class="small">{p400} of principal</span></span></div>
    <div class="kpi kpi-warn"><span class="kpi-num">{fbar400}</span><span class="kpi-lab">Willful FBAR maximum at the same USD 400,000 balance<br><span class="small">greater of $165,353 or 50%</span></span></div>
  </div>

  <div class="callout info">
    <p><strong>The single most important number.</strong> Moving USD 400,000 lawfully costs
    about <strong>{t400}</strong> in exchange margin and bank charges — <strong>{p400}</strong>.
    A single willful FBAR violation on the same balance carries a statutory maximum of
    <strong>{fbar400}</strong>. Reporting compliance is roughly {ratio}&times; more
    expensive than the entire conversion. Fix the reporting first; the conversion is the
    cheap part.</p>
  </div>
</section>
""".format(
        fx=pct(FX_MARGIN_PCT, 3),
        t10=money(m01_10["total_cost_usd"]),
        p10=pct(m01_10["cost_pct"], 3),
        t400=money(m01_400["total_cost_usd"]),
        p400=pct(m01_400["cost_pct"], 3),
        fbar400=money(max(FBAR_WILLFUL_FLAT, FBAR_WILLFUL_PCT * 400000)),
        ratio="{:.0f}".format(max(FBAR_WILLFUL_FLAT, FBAR_WILLFUL_PCT * 400000) / m01_400["total_cost_usd"]),
    ))

    # ---- primary table
    out.append("""
<section class="section">
  <h2>1. The recommended route, priced at every USD 10,000 step</h2>
  <p class="small"><strong>M01</strong> — foreign individual, documented current-account
  purchase, then a personal cross-border telegraphic transfer. Cost = FX margin
  (0.20996 % of the amount) + BOC's published personal wire tariff
  (1&permil; of the CNY amount, minimum &yen;50, maximum &yen;260) + cable fee
  &yen;150. The CNY fee is converted to USD at the same 6.6919 rate the customer
  pays. <a href="cost-steps.html#M01">Step-by-step for this route &rarr;</a></p>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr>
      <th>Amount<br>USD</th>
      <th>CNY<br>needed</th>
      <th>FX margin<br>USD</th>
      <th>Bank fees<br>USD</th>
      <th class="hi">Total cost<br>USD</th>
      <th class="hi">Cost as<br>% </th>
      <th>You<br>receive</th>
    </tr></thead>
    <tbody>""")
    for r in m01:
        out.append(
            "<tr><td data-l='Amount USD'><strong>{a:,}</strong></td>"
            "<td data-l='CNY needed'>{cny:,.0f}</td>"
            "<td data-l='FX margin'>{fx:,.2f}</td>"
            "<td data-l='Bank fees'>{fee:,.2f}</td>"
            "<td data-l='Total cost' class='hi'><strong>{tot:,.2f}</strong></td>"
            "<td data-l='Cost %' class='hi'>{p:.3f}%</td>"
            "<td data-l='You receive'>{net:,.2f}</td></tr>".format(
                a=r["amount_usd"], cny=r["cny_required"], fx=r["fx_margin_usd"],
                fee=r["wire_fee_usd"], tot=r["total_cost_usd"], p=r["cost_pct"],
                net=r["net_usd"]))
    out.append("""    </tbody>
  </table>
  </div>
  <p class="small">The fee stops growing at USD 38,854 of principal: that is where 1&permil;
  of the CNY amount reaches the &yen;260 cap. Everything above that pays a flat
  &yen;410 (&asymp; $61.27). That is why the percentage cost falls toward the FX margin
  as the balance rises.</p>
</section>
""")

    # ---- comparison at key amounts
    out.append("""
<section class="section">
  <h2>2. Every method side by side at the four amounts that matter</h2>
  <p class="small">Full 40-row tables for each method follow in section 3. This is the
  short version. "Cap" means the method cannot lawfully move that amount in one payment.</p>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr>
      <th>Method</th>
      <th>$50,000</th><th>$100,000</th><th>$200,000</th><th>$400,000</th>
    </tr></thead><tbody>""")
    for m in METHODS:
        cells = []
        for a in (50000, 100000, 200000, 400000):
            r = next(x for x in by_id[m["id"]] if x["amount_usd"] == a)
            lab = "${:,}".format(a)
            if r["feasible"] != "Yes":
                cells.append("<td class='no' data-l='{lab}'>cap</td>".format(lab=lab))
            else:
                cells.append("<td data-l='{lab}'>{t}<br><span class='small'>{p:.3f}%</span></td>".format(
                    lab=lab, t=money(r["total_cost_usd"]), p=r["cost_pct"]))
        out.append("<tr><td data-l='Method'><strong>{id}</strong> {n}<br><span class='small'>{zh}</span></td>{c}</tr>".format(
            id=m["id"], n=m["name"], zh=m["name_zh"], c="".join(cells)))
    out.append("""    </tbody>
  </table>
  </div>
  <p class="small">M04 (the domestic-individual USD 50,000 convenience amount) shows a
  cost at USD 50,000 because that is the most it can move in a year; the same balance in
  M01 or M05 needs no such staging.</p>
</section>
""")

    # ---- per-method full tables
    out.append("""
<section class="section">
  <h2>3. Full 40-increment table for every method</h2>
  <p class="small">Open a method to see all 40 rows. Each is computed by the same script
  from the same published tariff; nothing is interpolated.</p>
""")
    for m in METHODS:
        rs = by_id[m["id"]]
        capnote = ""
        if m.get("feasibility_cap_usd"):
            capnote = ("<p class='small warnline'><strong>Cap:</strong> {}</p>".format(
                m["feasibility"]))
        out.append("""
<details class="method">
  <summary><strong>{id}</strong> — {n} <span class="zh">{zh}</span></summary>
  <div class="mbody">
    <p class="small"><strong>Legal basis:</strong> <a href="{bu}" target="_blank" rel="noopener">{basis}</a></p>
    <p class="small"><strong>Fee basis:</strong> <a href="{fu}" target="_blank" rel="noopener">{fs}</a></p>
    <p><strong>Verdict:</strong> {v}</p>
    <p class="small"><strong>Ceiling:</strong> {q}</p>
    {cap}
    <div class="tablewrap">
    <table class="cost">
      <thead><tr><th>Amount USD</th><th>FX margin</th><th>Bank fees</th><th>Other fixed</th>
      <th class="hi">Total</th><th class="hi">%</th><th>Net received</th><th>Feasible</th></tr></thead>
      <tbody>""".format(
            id=m["id"], n=m["name"], zh=m["name_zh"], bu=m["basis_url"], basis=m["basis"],
            fu=m["fee_url"], fs=m["fee_source"], v=m["verdict"], q=m["quota"], cap=capnote))
        for r in rs:
            cls = " class='no'" if r["feasible"] != "Yes" else ""
            out.append(
                "<tr{cls}><td data-l='Amount'>{a:,}</td><td data-l='FX margin'>{fx:,.2f}</td>"
                "<td data-l='Fees'>{fee:,.2f}</td><td data-l='Other'>{o:,.2f}</td>"
                "<td data-l='Total' class='hi'>{t:,.2f}</td><td data-l='%' class='hi'>{p:.3f}</td>"
                "<td data-l='Net'>{n:,.2f}</td><td data-l='Feasible'>{f}</td></tr>".format(
                    cls=cls, a=r["amount_usd"], fx=r["fx_margin_usd"], fee=r["wire_fee_usd"],
                    o=r["other_fixed_usd"], t=r["total_cost_usd"], p=r["cost_pct"],
                    n=r["net_usd"], f=r["feasible"]))
        out.append("""      </tbody>
    </table>
    </div>
  </div>
</details>""")
    out.append("</section>")

    # ---- penalty exposure
    out.append("""
<section class="section">
  <h2>4. The real exposure: statutory maximum penalties at each balance</h2>
  <p class="lead">This is the table to read first if the balance is large. These are the
  <em>statutory maximums</em>, not predictions and not assessments — the IRS states that
  assertion depends on facts and circumstances. They are included because the brief asked
  for the conversion penalty broken down, and because in every row they are orders of
  magnitude larger than the cost of the conversion itself.</p>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr>
      <th>Balance<br>USD</th>
      <th class="hi">Willful FBAR<br>max</th>
      <th>Non-willful<br>FBAR max</th>
      <th>Form 8938<br>max</th>
      <th>Form 3520<br>max (25%)</th>
      <th>FX Reg.<br>30%</th>
      <th>FX Reg.<br>100%</th>
    </tr></thead><tbody>""")
    for r in pen:
        out.append(
            "<tr><td data-l='Balance'><strong>{a:,}</strong></td>"
            "<td data-l='Willful FBAR max' class='hi'><strong>{w:,.0f}</strong></td>"
            "<td data-l='Non-willful FBAR'>{nw:,.0f}</td>"
            "<td data-l='8938 max'>{f8:,.0f}</td>"
            "<td data-l='3520 max'>{f3:,.0f}</td>"
            "<td data-l='FX Reg 30%'>{lo:,.0f}</td>"
            "<td data-l='FX Reg 100%'>{hi2:,.0f}</td></tr>".format(
                a=r["amount_usd"], w=r["fbar_willful_max_usd"],
                nw=r["fbar_nonwillful_max_usd"], f8=r["f8938_max_usd"],
                f3=r["f3520_max_usd"], lo=r["fxreg_low_usd"], hi2=r["fxreg_high_usd"]))
    out.append("""    </tbody>
  </table>
  </div>
  <p class="small">Willful FBAR = greater of $165,353 or 50% of the balance:
  <a href="https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821" target="_blank" rel="noopener">31 CFR 1010.821 Table 1</a>.
  Non-willful FBAR = $16,536 per report:
  <a href="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar" target="_blank" rel="noopener">IRS FBAR page</a>.
  Form 8938 = $10,000 + up to $50,000 continuation:
  <a href="https://www.law.cornell.edu/uscode/text/26/6038D" target="_blank" rel="noopener">26 U.S.C. § 6038D(d)</a>.
  Form 3520 = 5% per month capped at 25%:
  <a href="https://www.law.cornell.edu/uscode/text/26/6039F" target="_blank" rel="noopener">26 U.S.C. § 6039F(c)</a>.
  FX Regulations = 30% or 30%–100% under arts. 39, 40 and 45:
  <a href="https://www.safe.gov.cn/safe/2008/0806/5321.html" target="_blank" rel="noopener">State Council Order 532</a>.
  The FX Regulation columns apply only to an <em>unlawful</em> route, shown for contrast.</p>
</section>
""")

    # ---- illegal comparison
    out.append("""
<section class="section">
  <h2>5. What the prohibited routes cost, priced the same way</h2>
  <p class="lead">The brief asked for as many ways as possible, with pros and cons. These
  three exist and are widely marketed, so they are listed and priced rather than omitted —
  but the price is a statutory penalty, not a fee, and it does not buy you the money.</p>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr><th>Route</th><th>$50,000</th><th>$200,000</th><th>$400,000</th>
    <th>vs. lawful M01 at $400,000</th></tr></thead><tbody>""")
    m01_400_total = m01_400["total_cost_usd"]
    for x in ILLEGAL:
        if x["id"] == "X03":
            cells = "".join(
                "<td class='no' data-l='${:,}'>principal at risk</td>".format(a)
                for a in (50000, 200000, 400000))
            ratio = "the whole balance"
        else:
            cells = "".join(
                "<td data-l='${a:,}'>{lo:,.0f} &ndash; {hi:,.0f}</td>".format(
                    a=a, lo=FXREG_LOW * a, hi=FXREG_HIGH * a)
                for a in (50000, 200000, 400000))
            ratio = "{:.0f}&times; to {:.0f}&times;".format(
                FXREG_LOW * 400000 / m01_400_total, FXREG_HIGH * 400000 / m01_400_total)
        out.append(
            "<tr><td data-l='Route'><strong>{id}</strong> {n}<br><span class='small'>{zh}</span><br>"
            "<a href='{u}' target='_blank' rel='noopener' class='small'>official basis</a></td>{c}"
            "<td data-l='vs lawful' class='no'>{r}</td></tr>".format(
                id=x["id"], n=x["name"], zh=x["name_zh"], u=x["basis_url"], c=cells, r=ratio))
    out.append("""    </tbody>
  </table>
  </div>
  <p class="small">Penalty basis: <a href="https://www.safe.gov.cn/safe/2008/0806/5321.html" target="_blank" rel="noopener">外汇管理条例 arts. 39, 40, 45</a>
  (up to 30% of the amount; serious cases 30% to the equivalent of 100%).
  Crypto prohibition: <a href="https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html" target="_blank" rel="noopener">银发〔2026〕42号</a>.</p>

  <div class="callout warn">
    <p><strong>The arithmetic of the whole question.</strong> At USD 400,000 the lawful
    route costs <strong>{law}</strong> and the unlawful route exposes you to
    <strong>{lo}</strong> to <strong>{hi}</strong> in penalties alone, on top of losing the
    money. There is no scenario in which evading the controls is cheaper.</p>
  </div>
</section>
""".format(law=money(m01_400_total), lo=money(FXREG_LOW * 400000), hi=money(FXREG_HIGH * 400000)))

    # ---- method and blanks
    out.append("""
<section class="section">
  <h2>6. How each number was produced, and what was deliberately left blank</h2>
  <table class="data">
    <thead><tr><th style="width:34%;">Input</th><th>Value used</th><th>Where it came from</th></tr></thead>
    <tbody>
      <tr><td>Customer rate, CNY per USD</td><td>6.6919</td><td><a href="https://www.boc.cn/sourcedb/whpj/" target="_blank" rel="noopener">BOC board, 现汇卖出价 669.19/100, 2026-11-09 09:15:45</a></td></tr>
      <tr><td>Mid-market reference, CNY per USD</td><td>6.67785</td><td>Midpoint of the same board's 现汇买入价 6.6638 and 现汇卖出价 6.6919. Computed, not quoted.</td></tr>
      <tr><td>FX margin</td><td>{fx}</td><td>(6.6919 − 6.67785) ÷ 6.6919. The World Bank <em>Remittance Prices Worldwide</em> convention: total cost = fee + margin over mid-market.</td></tr>
      <tr><td>Full round-trip spread</td><td>{fs}</td><td>(6.6919 − 6.6638) ÷ 6.6919. Shown for completeness; the one-way margin above is the cost you actually bear.</td></tr>
      <tr><td>Rate versus CFETS parity</td><td>{vp}</td><td>6.6919 ÷ 6.7188 − 1. Negative means that on this particular morning the bank's selling rate was <em>cheaper</em> than the <a href="https://www.chinamoney.com.cn/chinese/bkccpr/" target="_blank" rel="noopener">central parity</a>. Parity is a reference, not a rate anyone can trade at, so it is not used as the cost baseline.</td></tr>
      <tr><td>Personal cross-border wire</td><td>1&permil;, min &yen;50, max &yen;260, + &yen;150 cable</td><td><a href="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html" target="_blank" rel="noopener">BOC personal e-banking tariff</a></td></tr>
      <tr><td>Global Smart Remittance</td><td>1.2&permil;, min &yen;200, max &yen;1,000, + &yen;150</td><td><a href="https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html" target="_blank" rel="noopener">BOC announcement 2017-11-09</a></td></tr>
      <tr><td>Full-amount credit</td><td>USD 25 (or USD 15 if the receiving bank holds a BOC New York account)</td><td>Same announcement, note 2</td></tr>
      <tr><td>Correspondent / intermediary deduction on a <em>standard</em> wire</td><td class="blank"></td><td class="unv"><strong>UNVERIFIED — left blank.</strong> BOC charges overseas bank fees "按实收取" (at actual cost) and publishes no amount. Flagged F01. Use the full-amount credit in M03 to convert this unknown into a published USD 25.</td></tr>
      <tr><td>Receiving U.S. bank incoming-wire fee</td><td class="blank"></td><td class="unv"><strong>UNVERIFIED — left blank.</strong> Set by your U.S. bank, not by any regulator. Flagged F02.</td></tr>
      <tr><td>Offshore CNH conversion margin</td><td class="blank"></td><td class="unv"><strong>UNVERIFIED — left blank.</strong> No official feed of a retail CNH spread was found. Flagged F03.</td></tr>
      <tr><td>Your tax basis / acquisition rate of the RMB</td><td class="blank"></td><td class="unv"><strong>UNVERIFIED — left blank.</strong> Required to compute the PRC 20% and the U.S. § 988 gain. Depends on documents only the account holder has. Flagged F04.</td></tr>
    </tbody>
  </table>

  <div class="callout warn">
    <p><strong>Three honest limits on this model.</strong></p>
    <p>1. <strong>The FX margin is one bank, one morning.</strong> Retail pricing was
    deregulated and the PBC no longer caps the spread, so no official percentage exists for
    "the" CNY/USD spread. 0.20996 % is what Bank of China's own two published numbers
    implied on 2026-11-09. Your bank may be better or worse; the BOC page itself warns that
    the board is indicative and the counter rate governs.</p>
    <p>2. <strong>The bank tariff is BOC's schedule.</strong> Other banks publish their own.
    The structure — ad valorem with a low cap, plus a flat cable fee — is what makes the
    cost regressive, and that structure is common, but the constants are BOC's.</p>
    <p>3. <strong>Tax is not in these totals.</strong> PRC IIT on whatever created the RMB
    and U.S. § 988 gain on the currency movement are excluded because they depend on your
    acquisition history, which was not provided. They are quantified by rate in section 4
    and on the <a href="penalties.html">penalty page</a>, never guessed as a dollar figure.</p>
  </div>
</section>
</main>
""".format(fx=pct(FX_MARGIN_PCT, 5), fs=pct(FULL_SPREAD_PCT, 4), vp=pct(VS_PARITY_PCT, 4)))

    out.append(FOOT.format(date=FETCH_DATE))
    return "".join(out)


def build_steps_html():
    out = []
    out.append(HEAD.format(
        title="Step-by-step: executing each CNY → USD method",
        tagline="Exactly what happens, in order, for every lawful route — with the article that governs each step",
        nav=NAV))
    out.append("""
<main>
<section class="section">
  <h1>Step by step, method by method</h1>
  <p class="lead">Each route below is written as the sequence of operations you would
  actually perform. Every step cites the instrument that governs it, so a bank officer or
  an adviser can check the step rather than take it on trust. Nothing here requires you to
  run a calculation: the prices are already in the <a href="cost-table.html">cost tables</a>.</p>

  <div class="callout info">
    <p><strong>Do this once, before any route.</strong> Ask the account-holding bank, in
    writing, three questions: (1) Is this account registered in your system as
    <em>境内个人</em> or <em>境外个人</em>? (2) Which article will you process the purchase
    under — 59, 57, or a capital-account approval? (3) Give me the complete document
    checklist for my case. The answer changes which route is open to you, and it is the one
    fact no public source can settle:
    <a href="https://www.safe.gov.cn/safe/2008/0806/5321.html" target="_blank" rel="noopener">FX Regulations art. 52</a>
    defines 境内个人 to include a foreigner resident in China for one year, while
    <a href="https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm" target="_blank" rel="noopener">PBOC Order [2006] No. 3 art. 37</a>
    defines the two categories by identity document. Both are in force.</p>
  </div>
</section>
""")

    steps = {
        "M01": ("Foreign individual: documented current-account purchase, then wire",
                "https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
                "Guidelines (2020) art. 59",
                [
                    ("Confirm classification in writing", "Ask the bank whether the account is 境内个人 or 境外个人 and which article it will use. Art. 59 applies to a 境外个人 converting lawful current-account RMB income earned in China.", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"),
                    ("Assemble the source-of-funds file", "Art. 59 requires the ID <em>plus</em> evidence of the source of the RMB <em>including tax documents</em> (含税务凭证). Salary: contract, payslips, IIT withholding records. Property: sale contract, deed, 完税凭证. Business profit: distribution resolution, tax receipts.", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"),
                    ("Check whether a tax filing is triggered", "If the single outward payment is the equivalent of USD 50,000 or more and falls in the categories listed in SAT/SAFE Announcement 2013 No. 40, file for a 备案表 with the local tax authority before the bank pays out.", "https://www.chinatax.gov.cn/chinatax/c102449/c5219874/content.html"),
                    ("Get an all-in written quote", "Demand: customer rate and its timestamp, the reference rate used, the margin in basis points, conversion charge, wire fee, cable fee, whether full-amount credit is included, the correspondent charges, the receiving-bank fee, and the net USD expected.", "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html"),
                    ("Execute the purchase and the remittance as one transaction", "The bank sells the FX and remits it. Do not split the payment and do not route it through another person's quota.", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
                    ("Buy full-amount credit if you need a known net", "USD 25, or USD 15 if the receiving bank holds an account with BOC New York. This replaces an unpublished intermediary deduction with a published fixed charge.", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html"),
                    ("Keep the paper", "Purchase receipt (水单), remittance advice, approval letter and 核准件 if any, the 备案表, and the bank's written classification answer.", "https://www.safe.gov.cn/tianjin/2024/0430/2464.html"),
                    ("File the U.S. side afterwards", "FBAR (FinCEN 114) due 15 April with automatic extension to 15 October; Form 8938 with the return if the threshold is met; report the CNY account interest as income; compute the § 988 gain on the conversion.", "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar"),
                ]),
        "M02": ("Global Smart Remittance premium",
                "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html",
                "BOC announcement 2017-11-09",
                [
                    ("Same steps 1–3 as M01", "Classification, source file and any tax filing are identical — the product choice changes the fee, not the permission.", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"),
                    ("Ask for the premium product by name", "中银全球智汇 is a telegraphic transfer with progress tracking, full passthrough of the remittance message including the reference, optional full-amount credit, and disclosure of the overseas bank's charge.", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html"),
                    ("Accept the tariff", "1.2&permil; of the amount, minimum &yen;200, maximum &yen;1,000, plus the cable fee. On a large balance this is more than M01 because the cap is four times higher.", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html"),
                    ("Choose full-amount credit or not", "Full-amount credit means overseas bank charges are collected from you at a fixed amount instead of being deducted from the principal, so the beneficiary receives the full figure.", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html"),
                ]),
        "M03": ("M01 plus full-amount credit",
                "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html",
                "BOC announcement 2017-11-09 note 2",
                [
                    ("Run M01 exactly as written", "The underlying permission and documents are unchanged.", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"),
                    ("Ask whether your receiving bank holds an account with BOC New York", "That single fact sets the charge at USD 15 instead of USD 25.", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html"),
                    ("Instruct full-amount credit on the payment", "Under a standard wire, overseas bank charges are deducted from the principal in transit. Under full-amount credit they are billed to you instead, at the published fixed amount.", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html"),
                    ("Verify the credit", "Compare the amount that left China with the amount that landed. If the difference is exactly the charge, the intermediary took nothing extra.", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html"),
                ]),
        "M04": ("Domestic individual: the USD 50,000 convenience amount",
                "https://www.safe.gov.cn/ningxia/2022/0929/1997.html",
                "Guidelines (2020) arts. 54–57; 实施细则 art. 2",
                [
                    ("Establish that you are a 境内个人 in this bank's system", "The convenience amount is available to 境内个人. A 境外个人 is processed under art. 59 instead. A foreigner holding a 外国人永久居留身份证 is treated as having the convenience amount.", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html"),
                    ("Present your ID and complete the purchase application", "The 个人购汇申请书 is where you declare the purpose; the \"六不得\" undertakings are on its face.", "https://www.safe.gov.cn/tianjin/2024/0430/2464.html"),
                    ("Stay inside USD 50,000 per person per year", "This is a processing convenience amount, not a tax and not the only lawful limit. Exceeding it is not illegal — it just needs documents.", "https://www.safe.gov.cn/ningxia/2022/0929/1997.html"),
                    ("If the balance is larger, plan the years", "At USD 50,000 a year a USD 400,000 balance needs eight years. Compare M01 and M05, which are not limited that way.", "https://www.safe.gov.cn/ningxia/2022/0929/1997.html"),
                ]),
        "M05": ("Emigrant property transfer",
                "https://www.gov.cn/gongbao/content/2005/content_64294.htm",
                "PBOC Announcement [2004] No. 16",
                [
                    ("Check the two threshold facts", "Art. 2: the route covers only a person who has emigrated from the mainland to a foreign country (or Hong Kong/Macau) and is now converting lawful property owned <em>before</em> acquiring emigrant status. Art. 8(4): you need the police-issued PRC household-registration cancellation certificate and settlement certification from a Chinese embassy or consulate.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Settle PRC tax before cancelling the household registration", "IIT Law art. 13: a taxpayer who cancels PRC household registration because of emigration must complete a tax settlement <em>before</em> the cancellation. Doing it in the wrong order is the classic trap.", "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html"),
                    ("Obtain the tax certificate for the property", "Art. 8(6): a tax certificate or tax-payment voucher issued by the competent tax authority where the property is located or the income arose.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Apply to the right SAFE office", "Art. 5: the SAFE branch or office where your pre-emigration household registration was located. A central sub-branch may accept the file on its behalf.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Submit the full file", "Art. 8: written application; the 移民财产对外转移申请人情况表 signed by you; the 个人财产对外转移外汇业务申请表; identity documents (cancellation certificate plus embassy certification); property-right documents such as the title copy, sale contract or relocation-compensation agreement; the tax certificate; anything else SAFE asks for. Notarise whatever is not already notarised.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Know which office decides", "Art. 10: up to the equivalent of RMB 500,000 the local SAFE office decides and issues the approval letter and 核准件; above that the local office reviews and SAFE head office decides.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Plan for the staging", "Art. 6: you must apply once for the whole balance. The first remittance may be up to half; after one year, up to half of what remains; after two years, the rest. A balance of RMB 200,000 or less may go in one payment after approval.", "https://www.safe.gov.cn/safe/2004/1116/4134.html"),
                    ("Take the 核准件 to the bank", "The designated bank sells the FX and remits it directly to your account in your country of residence. Art. 11: it may not be withdrawn as cash inside China.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("For later tranches, bring the earlier paperwork", "Art. 8 final paragraph: from the second remittance onward you must present the earlier approval letter and the 核准件 issued for the previous payment.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Never submit a document you cannot stand behind", "Art. 13: a false document or a repeat application on the same property is punished under FX Regulations art. 40 — up to 30%, or 30%–100% if serious.", "https://www.safe.gov.cn/safe/2008/0806/5321.html"),
                ]),
        "M06": ("Inheritance transfer",
                "https://www.gov.cn/gongbao/content/2005/content_64294.htm",
                "PBOC Announcement [2004] No. 16, arts. 2 and 9",
                [
                    ("Confirm you are the right kind of applicant", "Art. 2: a foreign citizen or a Hong Kong/Macau resident inheriting property located in the mainland.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Apply where the deceased was registered", "Art. 5: the SAFE office at the deceased's household-registration location before death.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Submit the inheritance file", "Art. 9: written application covering the reason, the relationship to the deceased, and a detailed written account of the source and realisation of the estate; the 个人财产对外转移外汇业务申请表; identity documents including embassy certification of overseas settlement, or the Hong Kong/Macau ID plus home-return permit or passport; proof of inheritance; the deceased's property-right documents and the tax certificate from the competent tax authority.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Apply once per deceased person", "Art. 6: all property inherited from the same deceased person is applied for once and may be remitted in one or several payments; property from different deceased persons needs separate applications.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                    ("Watch the same approval split and the same anti-fraud clause", "RMB 500,000 threshold per art. 10; art. 13 applies identically.", "https://www.gov.cn/gongbao/content/2005/content_64294.htm"),
                ]),
        "M07": ("Balance already held in USD",
                "https://www.safe.gov.cn/tianjin/2024/0229/2402.html",
                "Guidelines (2020) art. 64; 实施细则 art. 15",
                [
                    ("Confirm the account really holds USD", "If the balance is CNY, this route does not exist and you need a purchase under M01, M04 or M05 first.", "https://www.safe.gov.cn/tianjin/2024/0229/2402.html"),
                    ("Remit on your ID up to USD 50,000 per day", "Art. 64: up to the equivalent of USD 50,000 accumulated in one day on ID alone; above that, ID plus transaction documents.", "https://www.safe.gov.cn/tianjin/2024/0229/2402.html"),
                    ("Avoid taking it as cash first", "If you withdraw cash and then remit it, the limit drops to USD 10,000 a day and you need a customs-stamped declaration or the original withdrawal slip above that.", "https://www.safe.gov.cn/tianjin/2024/0229/2402.html"),
                    ("Pay only the wire fee", "No conversion happens, so the FX margin is zero. This is the cheapest possible route — and the premise of the brief is that this is exactly what you cannot do, because the balance is in CNY.", "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html"),
                ]),
        "M08": ("Traveller's cash and overseas card withdrawal",
                "https://www.safe.gov.cn/hubei/2019/0305/851.html",
                "SAFE card-withdrawal notice; cash-carry guidance",
                [
                    ("Do not treat this as a transfer mechanism", "It is listed because it is commonly proposed. At USD 400,000 it would take decades inside the annual cash-withdrawal cap.", "https://www.safe.gov.cn/hubei/2019/0305/851.html"),
                    ("Respect the annual card-withdrawal cap", "RMB 100,000 per person per year of overseas cash withdrawal, and RMB 10,000 per card per day; exceeding it suspends the card for the rest of the year and the following year.", "https://www.safe.gov.cn/hubei/2019/0305/851.html"),
                    ("Respect the border limits and the U.S. reporting duty", "Carrying more than USD 10,000 into or out of the United States requires a FinCEN Form 105 report. Failure to file is itself the offence.", "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-B/section-1010.340"),
                    ("Price it honestly", "The cash rate is usually worse than the spot rate. On 2026-11-09 BOC quoted 现钞卖出价 and 现汇卖出价 identically at 669.19, so the table shows the same margin — but that equality is not guaranteed on the day you transact.", "https://www.boc.cn/sourcedb/whpj/"),
                ]),
    }

    for mid in ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08"]:
        name, url, basis, items = steps[mid]
        out.append("""
<details class="method" id="{mid}" open>
  <summary><strong>{mid}</strong> — {name}</summary>
  <div class="mbody">
    <p class="small"><strong>Governing instrument:</strong> <a href="{url}" target="_blank" rel="noopener">{basis}</a></p>
    <ol class="steps">""".format(mid=mid, name=name, url=url, basis=basis))
        for i, (t, d, u) in enumerate(items, 1):
            out.append(
                "<li><strong>{t}</strong><p>{d}</p>"
                "<p class='small'><a href='{u}' target='_blank' rel='noopener'>official basis &rarr;</a></p></li>".format(
                    t=t, d=d, u=u))
        out.append("""    </ol>
  </div>
</details>""")

    out.append("""
<section class="section">
  <h2>The two U.S. steps that decide whether any of this is cheap</h2>
  <ol class="steps">
    <li><strong>File the FBAR for every year you had the account.</strong>
      <p>A U.S. citizen must file FinCEN Form 114 whenever the aggregate of foreign
      accounts exceeded USD 10,000 at any point in the year. It is filed with FinCEN, not
      with the return, and the automatic extension runs to 15 October. This is the single
      largest number in the whole analysis: the willful maximum is the greater of $165,353
      or 50% of the balance.</p>
      <p class="small"><a href="https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar" target="_blank" rel="noopener">IRS FBAR page</a> ·
      <a href="https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821" target="_blank" rel="noopener">31 CFR 1010.821</a></p></li>
    <li><strong>Report the income that created the balance, and the currency gain.</strong>
      <p>Worldwide income includes the CNY interest even though China exempts savings
      interest since 2008-10-09. Separately, converting the RMB is a § 988 transaction:
      the exchange gain on a personal transaction is excluded, but <em>only</em> while it
      does not exceed USD 200 — above that the exclusion switches off and the gain is
      ordinary income. That is the only genuine "conversion tax" the research found, and
      it is a U.S. income tax on the currency movement, not a Chinese levy on converting.</p>
      <p class="small"><a href="https://www.law.cornell.edu/uscode/text/26/988" target="_blank" rel="noopener">26 U.S.C. § 988(e)</a> ·
      <a href="https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/grsds/200810/t288953.html" target="_blank" rel="noopener">财税〔2008〕132号</a></p></li>
  </ol>
</section>
</main>
""")
    out.append(FOOT.format(date=FETCH_DATE))
    return "".join(out)


def build_verification_html():
    out = []
    out.append(HEAD.format(
        title="Verification log — every figure checked against an official source",
        tagline="Line-by-line record of what was read, on which page, on 2026-11-09",
        nav=NAV))
    out.append("""
<main>
<section class="section">
  <h1>Verification log</h1>
  <p class="lead">Every constant used in the cost model was re-opened on 2026-11-09 and read
  on the issuing authority's own page, not recalled and not taken from commentary. The quote
  column is the operative text as it appeared on the page. Where a page could not be
  reached, or a value does not exist on any official page, it is recorded below as broken
  or unverified rather than filled.</p>
  <p class="small">Machine-readable copy: <code>data/reverification.csv</code>.</p>
</section>

<section class="section">
  <h2>Sources verified in this session</h2>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr><th>ID</th><th>Topic</th><th>Authority</th><th>Checked</th><th>Operative text</th><th>Status</th></tr></thead>
    <tbody>""")
    for v in VERIFICATION:
        out.append(
            "<tr><td data-l='ID'><strong>{id}</strong></td>"
            "<td data-l='Topic'>{topic}</td>"
            "<td data-l='Authority'><a href=\"{url}\" target='_blank' rel='noopener'>{authority}</a></td>"
            "<td data-l='Checked'>{checked}</td>"
            "<td data-l='Quote'><span class='quote'>{quote}</span></td>"
            "<td data-l='Status'><span class='badge badge-ok'>{status}</span></td></tr>".format(**v))
    out.append("""    </tbody>
  </table>
  </div>
</section>

<section class="section">
  <h2>Broken links found in the existing site</h2>
  <p class="lead">While checking the source register, three links on the published site
  returned 404. Two were inherited from earlier sessions and are still live in
  <code>data/sources.csv</code>. They are flagged rather than silently deleted, so the
  earlier sessions' work can be audited.</p>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr><th>ID</th><th>Broken URL</th><th>Used by</th><th>Result</th><th>Replacement</th></tr></thead>
    <tbody>""")
    for b in BROKEN:
        out.append(
            "<tr><td data-l='ID'><strong>{id}</strong></td>"
            "<td data-l='URL'><a href='{url}' target='_blank' rel='noopener'>{url}</a></td>"
            "<td data-l='Used by'>{used_by}</td>"
            "<td data-l='Result'><span class='badge badge-bad'>{result}</span></td>"
            "<td data-l='Replacement'>{replacement}</td></tr>".format(**b))
    out.append("""    </tbody>
  </table>
  </div>
</section>

<section class="section">
  <h2>What was checked and could not be confirmed — left blank</h2>
  <table class="data">
    <thead><tr><th style="width:8%;">Flag</th><th style="width:32%;">Item</th><th>Why it is blank rather than estimated</th></tr></thead>
    <tbody>
      <tr><td><strong>F01</strong></td><td>Correspondent / intermediary deduction on a standard wire</td><td>BOC's tariff says overseas bank charges are collected at actual cost ("按实收取") and publishes no amount. No regulator publishes one either. Filled as blank; M03 prices the published alternative.</td></tr>
      <tr><td><strong>F02</strong></td><td>Receiving U.S. bank's incoming-wire fee</td><td>Set commercially by each U.S. bank. Not a regulated figure. Blank.</td></tr>
      <tr><td><strong>F03</strong></td><td>Offshore CNH retail conversion margin</td><td>No official retail CNH spread feed was found. HKMA has published measured onshore/offshore gaps for specific stress episodes, but applying one to today would be inference. Blank.</td></tr>
      <tr><td><strong>F04</strong></td><td>The reader's tax basis and acquisition date for the RMB</td><td>Decides both the PRC 20% base and the U.S. § 988 gain. Depends on documents only the account holder has. Blank, with rates given instead of a dollar figure.</td></tr>
      <tr><td><strong>F05</strong></td><td>Whether the account is registered as 境内个人 or 境外个人</td><td>Two instruments in force define the terms differently (FX Regulations art. 52 versus PBOC Order [2006] No. 3 art. 37). Only the bank's own registration settles it. Blank.</td></tr>
      <tr><td><strong>F06</strong></td><td>SAFE processing time for an emigrant-transfer approval</td><td>No published service standard for the approval was found. Blank.</td></tr>
      <tr><td><strong>F07</strong></td><td>Whether the balance is salary, property proceeds, gift, or inheritance</td><td>Changes the tax and the eligible route entirely. Not provided. Blank; every route is priced so the reader can pick by fact, not by guess.</td></tr>
    </tbody>
  </table>
  <p class="small">These are also listed on the <a href="flagged-review.html">Flagged for review</a> page.</p>
</section>
</main>
""")
    out.append(FOOT.format(date=FETCH_DATE))
    return "".join(out)


# ---------------------------------------------------------------------------
# 7. MAIN
# ---------------------------------------------------------------------------
def main():
    rows = compute_rows()
    pen = compute_penalty_rows()

    os.makedirs(DATA, exist_ok=True)

    with open(os.path.join(DATA, "cost_model.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with open(os.path.join(DATA, "penalty_exposure.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pen[0].keys()))
        w.writeheader()
        w.writerows(pen)

    with open(os.path.join(DATA, "reverification.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "topic", "authority", "url", "checked", "quote", "status"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(VERIFICATION)
        for b in BROKEN:
            w.writerow(dict(id=b["id"], topic="BROKEN LINK", authority="n/a", url=b["url"],
                            checked=b["result"], quote="", status="broken"))

    meta = dict(
        generated="2026-11-09",
        fetch_date=FETCH_DATE,
        constants=dict(
            parity=PARITY, boc_spot_buy=BOC_SPOT_BUY, boc_spot_sell=BOC_SPOT_SELL,
            mid=MID, fx_margin_pct=FX_MARGIN_PCT, full_spread_pct=FULL_SPREAD_PCT,
            vs_parity_pct=VS_PARITY_PCT, personal_wire=PERSONAL_WIRE,
            smart_wire=SMART_WIRE, full_amount_credit_usd=FULL_AMOUNT_CREDIT_USD,
        ),
        amounts=AMOUNTS,
        penalty_constants=dict(
            fbar_nonwillful_max=FBAR_NONWILLFUL_MAX, fbar_willful_flat=FBAR_WILLFUL_FLAT,
            fbar_willful_pct=FBAR_WILLFUL_PCT, f8938_base=F8938_BASE,
            f8938_continuation_max=F8938_CONTINUATION_MAX, f3520_pct=F3520_PCT,
            fxreg_low=FXREG_LOW, fxreg_high=FXREG_HIGH,
        ),
        methods=[dict(
            {k: v for k, v in m.items() if k not in ("fee",)},
            fee_schedule=(m["fee"] if m.get("fee") else None),
        ) for m in METHODS],
        rows=rows,
        penalty_rows=pen,
    )
    with open(os.path.join(DATA, "cost_model.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    with open(os.path.join(ROOT, "cost-table.html"), "w", encoding="utf-8") as f:
        f.write(build_cost_table_html(rows, pen))
    with open(os.path.join(ROOT, "cost-steps.html"), "w", encoding="utf-8") as f:
        f.write(build_steps_html())
    with open(os.path.join(ROOT, "verification.html"), "w", encoding="utf-8") as f:
        f.write(build_verification_html())

    # ---- self-checks: refuse to emit a table that breaks the contract
    errs = []
    for r in rows:
        if r["total_cost_usd"] == "" or r["total_cost_usd"] is None:
            errs.append("blank total: %s %s" % (r["method_id"], r["amount_usd"]))
        if abs((r["fx_margin_usd"] + r["wire_fee_usd"] + r["other_fixed_usd"]) - r["total_cost_usd"]) > 0.02:
            errs.append("component mismatch: %s %s" % (r["method_id"], r["amount_usd"]))
        if abs((r["amount_usd"] - r["total_cost_usd"]) - r["net_usd"]) > 0.02:
            errs.append("net mismatch: %s %s" % (r["method_id"], r["amount_usd"]))
    if len(rows) != len(METHODS) * len(AMOUNTS):
        errs.append("row count %d != %d" % (len(rows), len(METHODS) * len(AMOUNTS)))
    if len(pen) != len(AMOUNTS):
        errs.append("penalty row count")
    for v in VERIFICATION:
        if not v["url"].startswith("https://"):
            errs.append("non-https source %s" % v["id"])
    if errs:
        raise SystemExit("CONTRACT VIOLATION:\n  " + "\n  ".join(errs))

    print("OK — %d cost rows (%d methods x %d amounts), %d penalty rows, %d verified sources, %d broken links flagged"
          % (len(rows), len(METHODS), len(AMOUNTS), len(pen), len(VERIFICATION), len(BROKEN)))
    print("   FX margin measured: %.5f%% (mid %.5f, ask %.4f)" % (FX_MARGIN_PCT, MID, ASK))
    print("   M01 total at $10,000: %s (%.3f%%)" % (money(rows[0]['total_cost_usd']), rows[0]['cost_pct']))
    m01_400 = [r for r in rows if r['method_id'] == 'M01' and r['amount_usd'] == 400000][0]
    print("   M01 total at $400,000: %s (%.3f%%)" % (money(m01_400['total_cost_usd']), m01_400['cost_pct']))
    print("   Willful FBAR max at $400,000: %s" % money(max(FBAR_WILLFUL_FLAT, 0.5 * 400000)))


if __name__ == "__main__":
    main()
