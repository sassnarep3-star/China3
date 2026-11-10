#!/usr/bin/env python3
"""Canonical cost engine for the C3X edition (session arena/2c8d441e-china3).

Every number this module emits is arithmetic over one of two kinds of input:

  1. a figure read off an official document that this session fetched on
     2026-11-10 (registered in data/c3x_sources.csv with the verbatim quote and
     the fetch timestamp), or
  2. a blank.  A blank is written as an empty CSV field and is always paired
     with a flag id in data/c3x_flags.csv.  A blank is never zero and never an
     industry average.

The module writes the CSVs and exposes the same rows to the page builder, so
the HTML and the data cannot drift apart.  scripts/verify_c3x_site.py re-derives
the arithmetic from the raw inputs with its own code, independently of this one.

Rounding: money to whole cents, percentages to four decimal places,
ROUND_HALF_UP, Decimal only (no binary floats anywhere).
"""
from __future__ import annotations

import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

D = Decimal


def q(v: D, places: str = "0.01") -> D:
    return v.quantize(D(places), rounding=ROUND_HALF_UP)


def fmt(v: D) -> str:
    """Machine-readable: no thousands separators, two decimals."""
    return f"{q(v):.2f}"


def disp(v: D) -> str:
    """Display form with thousands separators."""
    return f"{q(v):,.2f}"


# --------------------------------------------------------------------------- sources
# Fetched and read on 2026-11-10 (UTC).  `quote` is verbatim from the page.
SOURCES: list[dict] = [
    {
        "id": "S01",
        "issuer": "Bank of China",
        "title": "中国银行外汇牌价 (BOC FX board), USD row",
        "url": "https://www.boc.cn/sourcedb/whpj/",
        "doc_date": "2026-11-10 17:39:58 Beijing",
        "fetched_utc": "2026-11-10",
        "quote": "美元 665.71 665.71 668.51 668.51 671.67 2026/11/10 17:39:58",
        "proposition": "现汇买入价 6.6571, 现汇卖出价 6.6851, 中行折算价 6.7167 CNY per USD; the columns are 100 foreign-currency units to CNY.",
    },
    {
        "id": "S02",
        "issuer": "Bank of China",
        "title": "中国银行电子银行个人服务转账汇款费率表 (personal e-banking transfer tariff, effective 2014-11-01)",
        "url": "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
        "doc_date": "effective 2014-11-01",
        "fetched_utc": "2026-11-10",
        "quote": "跨境汇款（电汇） 每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。",
        "proposition": "Cross-border telegraphic transfer: 1 per mille of the remitted amount, minimum CNY 50, maximum CNY 260 per transfer, plus a cable fee of CNY 150 per transfer outside Hong Kong/Macau/Taiwan.",
    },
    {
        "id": "S03",
        "issuer": "SAFE Tianjin branch",
        "title": "2024年外汇管理互联网信息——个人外汇（三）, on 汇发〔2020〕14号 art. 64",
        "url": "https://www.safe.gov.cn/tianjin/2024/0229/2402.html",
        "doc_date": "2024-02-29",
        "fetched_utc": "2026-11-10",
        "quote": "外汇账户内外汇汇出境外当日累计等值5万美元以下（含）的，凭本人有效身份证件办理；超过上述金额的，凭本人有效身份证件、有交易额的相关材料办理。持外币现钞汇出当日累计等值1万美元以下（含）的，凭本人有效身份证件在银行办理",
        "proposition": "For a domestic individual's current-account remittance: up to USD 50,000 equivalent per day on ID alone; ABOVE that amount with ID plus documents showing the transaction amount. It is a documentation threshold, not a prohibition.",
    },
    {
        "id": "S04",
        "issuer": "SAFE Tianjin branch",
        "title": "2024年经常项目外汇政策问答案例（九）, on 汇发〔2020〕14号 art. 59",
        "url": "https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
        "doc_date": "2024-06-21",
        "fetched_utc": "2026-11-10",
        "quote": "境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇。持有外国人永久居留身份证的境外个人适用购汇年度便利化额度。",
        "proposition": "A foreign individual's lawful current-account RMB income is purchased with ID plus source-of-funds materials INCLUDING tax documents; only a holder of a Foreign Permanent Resident ID gets the annual convenience amount. This is the rule that decides a U.S. passport holder's route.",
    },
    {
        "id": "S05",
        "issuer": "State Council of the PRC",
        "title": "中华人民共和国外汇管理条例, 国务院令第532号 (Foreign Exchange Administration Regulations)",
        "url": "https://www.safe.gov.cn/safe/2008/0806/5321.html",
        "doc_date": "2008-08-06",
        "fetched_utc": "2026-11-10",
        "quote": "第三十九条 有违反规定将境内外汇转移境外…处逃汇金额30%以下的罚款；情节严重的，处逃汇金额30%以上等值以下的罚款 ／ 第五十二条（二）境内个人，是指中国公民和在中华人民共和国境内连续居住满1年的外国人",
        "proposition": "Art. 39 evading FX control: fine up to 30% of the amount, or 30%-100% if serious. Art. 42 border cash: up to 20%. Art. 45 unlicensed FX trading: up to 30%, 30%-100% if serious. Art. 48 false documents: individual up to CNY 50,000. Art. 52(2) defines 境内个人 to include a foreigner continuously resident in China for one year.",
    },
    {
        "id": "S06",
        "issuer": "People's Bank of China",
        "title": "个人财产对外转移售付汇管理暂行办法, 中国人民银行公告〔2004〕第16号",
        "url": "https://www.safe.gov.cn/safe/2004/1116/5461.html",
        "doc_date": "2004-11-16, effective 2004-12-01",
        "fetched_utc": "2026-11-10",
        "quote": "移民转移是指从中国内地移居外国…将其在取得移民身份之前在境内拥有的合法财产变现，通过外汇指定银行购汇和汇出境外的行为 ／ 第六条 移民转移必须一次性申请…分步汇出 ／ 第八条（六）申请转移财产所在地或收入来源地主管税务机关开具的税收证明或完税凭证",
        "proposition": "Emigrant property transfer: convert pre-emigration lawful domestic property into FX and remit it. Requires one application for the whole amount, a tax certificate or tax-payment receipt, and (for emigrants) cancellation of Chinese household registration plus proof of settlement abroad. Art. 11: the bank must remit to the applicant's own overseas account, no domestic FX cash withdrawal.",
    },
    {
        "id": "S07",
        "issuer": "SAFE",
        "title": "国家外汇管理局关于进一步改进和调整资本项目外汇管理政策的通知, 汇发〔2014〕2号, §六 (as republished, marked 已修改)",
        "url": "https://www.safe.gov.cn/tianjin/2024/0903/2594.html",
        "doc_date": "2014-01-10, effective 2014-02-10",
        "fetched_utc": "2026-11-10",
        "quote": "（一）…取消财产转移总金额超过等值人民币50万元报国家外汇管理局备案的要求。（二）取消移民财产转移分次汇出的要求。申请人向原户籍所在地外汇局办理移民财产转移核准手续后，银行可在核准件审批额度内一次或分次汇出相关资金。",
        "proposition": "Cancels both the over-RMB-500,000 head-office filing and the staged-remittance requirement: after approval the bank may remit in one lump or in instalments within the approved amount.",
    },
    {
        "id": "S08",
        "issuer": "State Taxation Administration",
        "title": "中华人民共和国个人所得税法 (Individual Income Tax Law), arts. 3, 6, 7, 13",
        "url": "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
        "doc_date": "2018-08-31 (seventh amendment)",
        "fetched_utc": "2026-11-10",
        "quote": "第三条（三）利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十。／ 第十三条 纳税人因移居境外注销中国户籍的，应当在注销中国户籍前办理税款清算。",
        "proposition": "20% proportional rate on property-transfer income, interest, dividends and incidental income; a taxpayer cancelling Chinese household registration to emigrate must settle tax before cancellation. Currency conversion as such is not one of the nine taxable income categories in art. 2.",
    },
    {
        "id": "S09",
        "issuer": "U.S. Government Publishing Office",
        "title": "26 U.S.C. §988 — Treatment of certain foreign currency transactions",
        "url": "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm",
        "doc_date": "U.S. Code 2023 edition",
        "fetched_utc": "2026-11-10",
        "quote": "§988(a)(1)(A) any foreign currency gain or loss attributable to a section 988 transaction shall be computed separately and treated as ordinary income or loss ／ §988(c)(1)(C)(i) the disposition of any nonfunctional currency shall be treated as a section 988 transaction ／ §988(e)(2) … The preceding sentence shall not apply if the gain which would otherwise be recognized on the transaction exceeds $200.",
        "proposition": "Disposing of a CNY deposit is a §988 transaction; the gain is ordinary income; an individual's personal transaction is excluded only if the gain does not exceed USD 200. The capital-gain election in (a)(1)(B) covers forwards, futures and options, not a currency deposit.",
    },
    {
        "id": "S10",
        "issuer": "eCFR / FinCEN",
        "title": "31 CFR 1010.821 — Penalty adjustment and table",
        "url": "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
        "doc_date": "eCFR current as of 2026-11-06",
        "fetched_utc": "2026-11-10",
        "quote": "31 U.S.C. 5321(a)(5)(B)(i) Foreign Financial Agency Transaction—Non-Willful Violation of Transaction 10,000 → 16,536 ／ 31 U.S.C. 5321(a)(5)(C)(i)(I) … Willful Violation of Transaction 100,000 → 165,353",
        "proposition": "For penalties assessed on or after 2025-01-17 the maximum is USD 16,536 for a non-willful FBAR violation and USD 165,353 for a willful one.",
    },
    {
        "id": "S11",
        "issuer": "Internal Revenue Service",
        "title": "Yearly average currency exchange rates",
        "url": "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates",
        "doc_date": "current page, 2021-2025 columns",
        "fetched_utc": "2026-11-10",
        "quote": "China | Yuan | 2025 7.129 | 2024 7.189 | 2023 7.075 | 2022 6.730 | 2021 6.452 ／ The Internal Revenue Service has no official exchange rate. Generally, it accepts any posted exchange rate that is used consistently.",
        "proposition": "IRS yearly average CNY/USD rates; the IRS has no official rate and accepts a consistently applied posted rate.",
    },
    {
        "id": "S12",
        "issuer": "Internal Revenue Service",
        "title": "Comparison of Form 8938 and FBAR requirements",
        "url": "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements",
        "doc_date": "current page",
        "fetched_utc": "2026-11-10",
        "quote": "Specified individuals living in the US: Unmarried … more than $50,000 on the last day of the tax year, or more than $75,000 at any time during the year ／ Penalties: Up to $10,000 … additional $10,000 for each 30 days … potential maximum penalty of $60,000",
        "proposition": "Form 8938 thresholds and its penalty ceiling; FBAR threshold is an aggregate exceeding USD 10,000 at any time in the calendar year.",
    },
    {
        "id": "S13",
        "issuer": "FinCEN",
        "title": "Report Foreign Bank and Financial Accounts (FBAR)",
        "url": "https://www.fincen.gov/report-foreign-bank-and-financial-accounts",
        "doc_date": "current page",
        "fetched_utc": "2026-11-10",
        "quote": "must file an FBAR if the aggregate value of the foreign financial accounts exceeds $10,000 at any time during the calendar year",
        "proposition": "The FBAR obligation attaches to the aggregate of foreign accounts exceeding USD 10,000 at any point in the year.",
    },
    {
        "id": "S14",
        "issuer": "U.S. Customs and Border Protection",
        "title": "Money and Other Monetary Instruments",
        "url": "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments",
        "doc_date": "last modified 2025-11-24",
        "fetched_utc": "2026-11-10",
        "quote": "when entering or leaving the United States you must report amounts exceeding $10,000 ／ When families or groups are involved, the $10,000 threshold applies to the total amount they are carrying or sending collectively, not per individual. ／ risk having their currency or monetary instruments forfeited and seized",
        "proposition": "Cross-border currency above USD 10,000 must be reported on FinCEN Form 105; the threshold is per family/group, not per person; failure risks seizure and civil or criminal penalties. The report is not itself a tax.",
    },
    {
        "id": "S16",
        "issuer": "SAFE Tianjin branch",
        "title": "2026年外汇管理互联网信息——个人外汇（08）: how a foreign individual remits labour remuneration earned in China",
        "url": "https://www.safe.gov.cn/tianjin/2026/0713/3088.html",
        "doc_date": "2026-07-13",
        "fetched_utc": "2026-11-10",
        "quote": "问：境外个人在境内工作期间取得的劳动报酬如何购汇汇出？答：根据…汇发〔2020〕14号…第五十九条规定，“境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇”。",
        "proposition": "The most recent branch guidance found on the exact case of a foreign individual remitting salary earned in China: art. 59 of the 2020 current-account guideline, ID plus source-of-funds materials including tax documents. It states no amount cap and no convenience amount for a non-PR-ID holder.",
    },
    {
        "id": "S15",
        "issuer": "SAFE",
        "title": "国家外汇管理局关于规范银行卡境外大额提取现金交易的通知, 汇发〔2017〕29号",
        "url": "https://www.safe.gov.cn/hubei/2019/0305/851.html",
        "doc_date": "2017, effective 2018-01-01",
        "fetched_utc": "2026-11-10",
        "quote": "本人名下银行卡（含附属卡）合计每个自然年度不得超过等值10万元人民币。超过年度额度的，本年及次年将被暂停持境内银行卡在境外提取现金。／ 外币卡由每卡每日不得超过等值1000美元调整为等值1万元人民币",
        "proposition": "Card cash withdrawals abroad: CNY 100,000 equivalent per person per calendar year across all own cards, and CNY 10,000 equivalent per card per day; exceeding the annual cap suspends the facility for the current and the following year.",
    },
]

# --------------------------------------------------------------------------- inputs
# Kept as strings so the verifier can parse exactly what is published.
INPUTS: dict[str, dict] = {
    "ask": {"value": "6.6851", "unit": "CNY per USD", "source": "S01",
            "note": "现汇卖出价 — the rate at which you buy USD with CNY."},
    "bid": {"value": "6.6571", "unit": "CNY per USD", "source": "S01",
            "note": "现汇买入价."},
    "mid": {"value": "6.6711", "unit": "CNY per USD", "source": "S01",
            "note": "Arithmetic mean of the bid and the ask, computed here."},
    "parity": {"value": "6.7167", "unit": "CNY per USD", "source": "S01",
               "note": "中行折算价 — BOC's internal conversion reference; NOT a rate a customer can trade at."},
    "wire_per_mille": {"value": "0.001", "unit": "fraction of the CNY amount", "source": "S02",
                       "note": "每笔汇款金额的1‰."},
    "wire_min": {"value": "50", "unit": "CNY per transfer", "source": "S02", "note": "最低收取50元/笔."},
    "wire_max": {"value": "260", "unit": "CNY per transfer", "source": "S02", "note": "最高收取260元/笔."},
    "cable_non_hk": {"value": "150", "unit": "CNY per transfer", "source": "S02",
                     "note": "非港澳台地区人民币150元/笔."},
    "fbar_penalty_non_willful": {"value": "16536", "unit": "USD per violation", "source": "S10", "note": ""},
    "fbar_penalty_willful": {"value": "165353", "unit": "USD per violation", "source": "S10", "note": ""},
    "f888_penalty_max": {"value": "60000", "unit": "USD", "source": "S12", "note": ""},
    "f888_threshold_us_unmarried": {"value": "50000", "unit": "USD year-end", "source": "S12", "note": ""},
    "f888_threshold_us_unmarried_anytime": {"value": "75000", "unit": "USD any time", "source": "S12", "note": ""},
    "f888_threshold_abroad_unmarried": {"value": "200000", "unit": "USD year-end", "source": "S12", "note": ""},
    "f888_threshold_abroad_unmarried_anytime": {"value": "300000", "unit": "USD any time", "source": "S12", "note": ""},
    "fbar_threshold": {"value": "10000", "unit": "USD aggregate", "source": "S13", "note": "Exceeds, not equals."},
    "cbp_threshold": {"value": "10000", "unit": "USD", "source": "S14", "note": "Exceeds; family aggregate."},
    "sec988_200": {"value": "200", "unit": "USD of gain", "source": "S09", "note": "Personal-transaction exclusion ceiling."},
    "irs_avg_2025": {"value": "7.129", "unit": "CNY per USD", "source": "S11", "note": ""},
    "irs_avg_2024": {"value": "7.189", "unit": "CNY per USD", "source": "S11", "note": ""},
    "irs_avg_2023": {"value": "7.075", "unit": "CNY per USD", "source": "S11", "note": ""},
    "irs_avg_2022": {"value": "6.730", "unit": "CNY per USD", "source": "S11", "note": ""},
    "irs_avg_2021": {"value": "6.452", "unit": "CNY per USD", "source": "S11", "note": ""},
    "prc_property_rate": {"value": "0.20", "unit": "fraction", "source": "S08", "note": "20% proportional rate."},
    "atm_year_cny": {"value": "100000", "unit": "CNY per person per year", "source": "S15", "note": ""},
    "atm_day_cny": {"value": "10000", "unit": "CNY per card per day", "source": "S15", "note": ""},
    "conv_limit_doc_threshold": {"value": "50000", "unit": "USD per day", "source": "S03",
                                "note": "Above this, ID plus transaction documents — not a cap."},
}

ASK = D(INPUTS["ask"]["value"])
BID = D(INPUTS["bid"]["value"])
MID = (ASK + BID) / 2
WIRE_PM = D(INPUTS["wire_per_mille"]["value"])
WIRE_MIN = D(INPUTS["wire_min"]["value"])
WIRE_MAX = D(INPUTS["wire_max"]["value"])
CABLE = D(INPUTS["cable_non_hk"]["value"])

AMOUNTS = [str(10_000 * i) for i in range(1, 41)]  # 10,000 .. 400,000

MARGINAL_RATES = ["12", "22", "24", "32", "35", "37"]


def spread_pct() -> D:
    """Cost of buying USD at the ask, measured against the mid, per USD received.

    (ask - mid) / ask.  The repo's other models use the same convention; the
    half-spread is 0.2094% at this board.
    """
    return (ASK - MID) / ASK


def money_row(usd: D) -> dict:
    """One price for one documented remittance of `usd` dollars."""
    cny = usd * ASK
    spread = usd * spread_pct()
    raw_fee = cny * WIRE_PM
    fee_cny = min(max(raw_fee, WIRE_MIN), WIRE_MAX) + CABLE
    fee_usd = fee_cny / ASK
    total = spread + fee_usd
    return {
        "cny": cny,
        "raw_fee_cny": raw_fee,
        "fee_cny": fee_cny,
        "spread_usd": spread,
        "fee_usd": fee_usd,
        "total_usd": total,
        "total_pct": total / usd * 100,
    }


def staged_row(usd: D, chunk: D = D(50_000)) -> dict:
    """Same purchase, split into whole wires of `chunk` dollars or less."""
    n = int((usd / chunk).to_integral_value(rounding="ROUND_CEILING"))
    spread = usd * spread_pct()
    per = chunk if usd >= chunk else usd      # last chunk carries the remainder
    fee_each = min(max(per * ASK * WIRE_PM, WIRE_MIN), WIRE_MAX) + CABLE
    fee_cny = fee_each * n
    fee_usd = fee_cny / ASK
    total = spread + fee_usd
    return {"wires": n, "fee_cny": fee_cny, "spread_usd": spread, "fee_usd": fee_usd,
            "total_usd": total, "total_pct": total / usd * 100}


def sec988_gain_pct(basis_rate: D) -> D:
    """Gain on the disposition, as a fraction of the USD received.

    You hold CNY bought when USD cost `basis_rate` CNY.  Basis in USD per CNY is
    1/basis_rate; proceeds per CNY are 1/ask.  Gain / proceeds = 1 - ask/basis_rate.
    """
    return 1 - ASK / basis_rate


def ladder_rows() -> list[dict]:
    out = []
    for a in AMOUNTS:
        usd = D(a)
        one = money_row(usd)
        many = staged_row(usd)
        gain = sec988_gain_pct(D(INPUTS["irs_avg_2024"]["value"]))
        taxable_gain = max(D(0), usd * gain)
        tax37 = taxable_gain * D("0.37") if taxable_gain > D(INPUTS["sec988_200"]["value"]) else D(0)
        out.append({
            "amount_usd": a,
            "cny_needed": fmt(one["cny"]),
            "spread_usd": fmt(one["spread_usd"]),
            "fee_cny": fmt(one["fee_cny"]),
            "fee_usd": fmt(one["fee_usd"]),
            "single_total_usd": fmt(one["total_usd"]),
            "single_total_pct": str(q(one["total_pct"], "0.0001")),
            "staged_wires": str(many["wires"]),
            "staged_fee_usd": fmt(many["fee_usd"]),
            "staged_total_usd": fmt(many["total_usd"]),
            "staged_total_pct": str(q(many["total_pct"], "0.0001")),
            "sec988_tax_37_usd": fmt(tax37),
        })
    return out


# --------------------------------------------------------------------------- methods
# `price_model` says what the cost table does with the route:
#   single  -> priced as one documented remittance (same arithmetic as M01)
#   staged  -> priced as whole USD 50,000 transfers
#   cap     -> a ceiling exists in a verified source, the price does not
#   blank   -> no official price exists in the sources reviewed
METHODS: list[dict] = [
    {
        "id": "M01",
        "name": "Documented current-account bank remittance (one transfer)",
        "category": "Bank",
        "lawfulness": "Lawful",
        "eligibility": "Any holder of a mainland CNY account whose money is lawful current-account income, with ID and source documents. A foreign passport holder needs source-of-funds materials including tax documents (S04).",
        "pros": "Cheapest published price found: bank spread plus the 1‰ tariff. Bank files the FX and balance-of-payments return; the paper trail is what keeps you clear of art. 39 (S05). Above USD 50,000/day you add documents, not permission (S03).",
        "cons": "Requires documents you may not have. Only the China-side cost is published — the U.S. receiving and any correspondent deduction are blank (F06).",
        "price_model": "single",
        "prc_tax": "No PRC tax on the conversion itself was identified; PRC tax attaches to the underlying income, if any (S08).",
        "us_tax": "§988 ordinary gain on disposing of the CNY deposit, with the USD 200 personal-transaction ceiling (S09).",
        "sources": "S01|S02|S03|S04|S16|S05|S09",
    },
    {
        "id": "M02",
        "name": "Same remittance, split into whole USD 50,000 transfers",
        "category": "Bank",
        "lawfulness": "Lawful",
        "eligibility": "Same as M01.",
        "pros": "Stays inside the amount that needs no transaction documents (S03), which some branches find easier to process.",
        "cons": "Pays the CNY 260 cap plus CNY 150 cable on every transfer, so the fee scales with the number of wires. On today's tariff that is up to 8 × CNY 410 at USD 400,000. It is a fee-maximising assumption, not a legal requirement: S03 says above USD 50,000 you produce documents.",
        "price_model": "staged",
        "prc_tax": "As M01.",
        "us_tax": "As M01, but each transfer is its own §988 transaction — the USD 200 exclusion is tested per transaction (S09).",
        "sources": "S02|S03|S09",
    },
    {
        "id": "M03",
        "name": "Emigrant property transfer (移民财产转移)",
        "category": "Capital account",
        "lawfulness": "Lawful with SAFE approval",
        "eligibility": "A natural person who has moved from the mainland to a foreign country and who converts property they owned BEFORE acquiring emigrant status. Needs cancelled household registration, proof of settlement abroad, property-rights documents and a PRC tax certificate (S06 art. 8).",
        "pros": "Built for exactly this problem: the whole pre-emigration estate, converted and remitted once. The staging requirement and the over-RMB-500,000 head-office filing were both cancelled in 2014, so the bank may remit the approved amount in one lump (S07).",
        "cons": "Approval is a SAFE decision, not an entitlement, and the tax certificate must come first. A U.S. citizen who never held mainland household registration does not obviously meet art. 2's definition of an emigrant, so this route may be closed to them (flag F08). Art. 11 forbids paying it out as domestic FX cash.",
        "price_model": "single",
        "prc_tax": "20% on property-transfer income, base = proceeds less original value and reasonable expenses (S08 art. 6(5)); settled before household registration is cancelled (S08 art. 13).",
        "us_tax": "§988 on the conversion; the property gain itself is separately U.S. taxable and may carry a foreign tax credit (S08 art. 7 is the PRC side of that).",
        "sources": "S06|S07|S08|S09",
    },
    {
        "id": "M04",
        "name": "Inheritance transfer (继承财产转移)",
        "category": "Capital account",
        "lawfulness": "Lawful with SAFE approval",
        "eligibility": "A foreign citizen or HK/Macau resident who inherited mainland property and has realised it. Needs proof of inheritance, the deceased's property documents and a tax certificate (S06 art. 9).",
        "pros": "The route designed for a foreign heir; there is no household-registration requirement. Since 2014, applications relating to different deceased persons may be combined (S07 §6(3)).",
        "cons": "SAFE approval at the deceased's last registered locality; notarisation of the inheritance and property documents is still required (S06 art. 9). Price at the bank is the same tariff, but nothing about this route is fast.",
        "price_model": "single",
        "prc_tax": "PRC tax on the deceased's or the heir's gain depends on facts not in evidence here (F04).",
        "us_tax": "§988 on conversion; a U.S. inheritance is generally not income, but the FX gain is (S09).",
        "sources": "S06|S07|S09",
    },
    {
        "id": "M05",
        "name": "Foreign Permanent Resident ID holder — annual convenience amount",
        "category": "Bank",
        "lawfulness": "Lawful",
        "eligibility": "Only a foreign individual holding a 外国人永久居留身份证, purchasing FX from lawful current-account RMB income (S04).",
        "pros": "The one route where the documented convenience amount is expressly available to a foreign passport holder (S04). Same published tariff as M01.",
        "cons": "A permanent-resident card is a precondition, not a formality. The amount is an annual convenience allowance; the source does not state a figure on this page, so no number is put in the table (F05).",
        "price_model": "cap",
        "prc_tax": "As M01.",
        "us_tax": "As M01.",
        "sources": "S04|S02",
    },
    {
        "id": "M06",
        "name": "Foreign passport holder without a PR ID — documented income purchase",
        "category": "Bank",
        "lawfulness": "Lawful, document-driven",
        "eligibility": "Lawful current-account RMB income earned in China, with ID and source-of-funds materials including tax documents (S04).",
        "pros": "Open to a U.S. citizen who worked in China and can show the income and the tax paid. No approval file, no cap in the article quoted.",
        "cons": "The bank decides whether your documents establish a current-account income; the same page that grants PR-ID holders the convenience amount withholds it from everyone else. If the balance is savings or capital rather than documented income, this article does not authorise it.",
        "price_model": "single",
        "prc_tax": "PRC tax was already withheld or settled on the income; the conversion adds none (S08).",
        "us_tax": "As M01.",
        "sources": "S04|S16|S08|S09",
    },
    {
        "id": "M07",
        "name": "Overseas ATM / card cash withdrawal",
        "category": "Card",
        "lawfulness": "Lawful up to the cap",
        "eligibility": "Holder of a mainland-issued card.",
        "pros": "No SAFE application; the money arrives as cash. Hard cap published: CNY 100,000 equivalent per person per calendar year, CNY 10,000 per card per day (S15).",
        "cons": "The cap is about USD 14,960 a year at today's ask — nowhere near USD 400,000. The issuer's FX conversion rate and any ATM operator fee are not published in the sources reviewed, so the price column is blank, not zero (F05). Exceeding the cap suspends the facility for the current and the following year (S15).",
        "price_model": "blank",
        "prc_tax": "None identified on the withdrawal itself.",
        "us_tax": "Cash in hand is still a §988 disposition when the currency leaves your account (S09).",
        "sources": "S15|S09",
    },
    {
        "id": "M08",
        "name": "Carry cash across the border",
        "category": "Cash",
        "lawfulness": "Lawful only within the undeclared limit and with U.S. reporting",
        "eligibility": "Anyone, within the PRC export limit and with a FinCEN Form 105 on the U.S. side above USD 10,000.",
        "pros": "No wire fee. The U.S. side is a report, not a tax (S14).",
        "cons": "Two legal systems at once. The PRC limit is set by SAFE under art. 15 of S05 but the figure was not re-verified in this pass, so it is deliberately blank (F05) rather than restated from memory. Failure to file the U.S. report risks seizure and forfeiture (S14). Art. 42 of S05 fines illegal carriage up to 20% of the amount.",
        "price_model": "blank",
        "prc_tax": "None identified on the carriage itself.",
        "us_tax": "§988 gain is realised when the currency is disposed of, not when it is carried (S09).",
        "sources": "S05|S14|S09",
    },
    {
        "id": "M09",
        "name": "Offshore CNY (CNH) account, then convert outside the mainland",
        "category": "Offshore",
        "lawfulness": "Lawful where the offshore account is lawfully funded",
        "eligibility": "An existing offshore account that can lawfully receive the funds; not a way around the mainland transfer rules.",
        "pros": "Conversion then happens under the offshore jurisdiction's rules.",
        "cons": "Does not solve the hard part — getting the money from the mainland account to the offshore account is itself the regulated step. The CNH spread is not published in the sources reviewed, so no price is shown.",
        "price_model": "blank",
        "prc_tax": "The outbound leg is still governed by S05.",
        "us_tax": "§988 applies to the offshore disposal as well (S09).",
        "sources": "S05|S09",
    },
    {
        "id": "M10",
        "name": "QDII / cross-border fund product",
        "category": "Investment",
        "lawfulness": "Lawful product, but it invests, it does not repatriate your balance",
        "eligibility": "Eligibility and quota are set by the product and the distributor; not established here.",
        "pros": "A regulated outbound investment channel.",
        "cons": "You end up holding a fund, not your cash in a U.S. account; fees are commercial and unpublished in the sources reviewed. Not a conversion route for an existing balance.",
        "price_model": "blank",
        "prc_tax": "Investment income treatment depends on the product (S08).",
        "us_tax": "Depends on the fund; not analysed here.",
        "sources": "S08",
    },
    {
        "id": "M11",
        "name": "Licensed payment institution / remittance platform",
        "category": "Payment",
        "lawfulness": "Lawful only for genuine goods-and-services trade",
        "eligibility": "Set by the institution's licence and by the underlying trade documentation.",
        "pros": "Fast for trade payments.",
        "cons": "Not a personal-savings channel: the payment must correspond to a real transaction. Fees are commercial and not in the sources reviewed.",
        "price_model": "blank",
        "prc_tax": "As the underlying transaction.",
        "us_tax": "As M01 where a currency disposal occurs.",
        "sources": "S05",
    },
    {
        "id": "M12",
        "name": "Split the amount across relatives' quotas (分拆结售汇)",
        "category": "Prohibited",
        "lawfulness": "Prohibited",
        "eligibility": "None — this is the pattern the rules are written against.",
        "pros": "None that survives review.",
        "cons": "Art. 39 and art. 45 of S05 expose the amount to a fine of up to 30%, or 30%-100% where serious, plus confiscation of the gain. It is the single most expensive way to save a CNY 410 fee.",
        "price_model": "blank",
        "prc_tax": "The fine is not a tax and is not deductible anywhere.",
        "us_tax": "No U.S. relief for a PRC penalty.",
        "sources": "S05",
    },
    {
        "id": "M13",
        "name": "Undeclared cash above the reporting threshold",
        "category": "Prohibited",
        "lawfulness": "Unlawful on the U.S. side",
        "eligibility": "None.",
        "pros": "None.",
        "cons": "Seizure and forfeiture of the currency, plus civil or criminal exposure (S14).",
        "price_model": "blank",
        "prc_tax": "—",
        "us_tax": "—",
        "sources": "S14",
    },
    {
        "id": "M14",
        "name": "Unlicensed FX dealer / underground bank",
        "category": "Prohibited",
        "lawfulness": "Prohibited",
        "eligibility": "None.",
        "pros": "None.",
        "cons": "Art. 45 of S05: warning, confiscation of illegal gains, fine up to 30% of the amount or 30%-100% where serious; criminal liability where it constitutes a crime. No receipt, no recourse, and no defence if the U.S. side later asks where the money came from.",
        "price_model": "blank",
        "prc_tax": "—",
        "us_tax": "—",
        "sources": "S05",
    },
]


def method_grid() -> list[dict]:
    """Every method at every $10,000 step, with blanks where unpublished."""
    rows = []
    for m in METHODS:
        for a in AMOUNTS:
            usd = D(a)
            if m["price_model"] == "single":
                r = money_row(usd)
                rows.append({"method_id": m["id"], "amount_usd": a,
                             "cost_usd": fmt(r["total_usd"]), "cost_pct": str(q(r["total_pct"], "0.0001")),
                             "flag": "", "basis": "spread + 1‰ wire (min 50, max 260) + CNY 150 cable, S01/S02"})
            elif m["price_model"] == "staged":
                r = staged_row(usd)
                rows.append({"method_id": m["id"], "amount_usd": a,
                             "cost_usd": fmt(r["total_usd"]), "cost_pct": str(q(r["total_pct"], "0.0001")),
                             "flag": "", "basis": f"{r['wires']} wire(s) at the CNY 260 cap + CNY 150 cable, S02"})
            elif m["price_model"] == "cap":
                rows.append({"method_id": m["id"], "amount_usd": a, "cost_usd": "", "cost_pct": "",
                             "flag": "F05", "basis": "cap/eligibility only; price not published"})
            else:
                rows.append({"method_id": m["id"], "amount_usd": a, "cost_usd": "", "cost_pct": "",
                             "flag": "F05", "basis": "no official price in the sources reviewed"})
    return rows


# --------------------------------------------------------------------------- steps
STEPS: list[dict] = [
    ("M01", 1, "Ask your branch, in writing, which rule it will apply to you: documented current-account income (S04 art. 59), or the domestic-individual remittance rule (S03 art. 64). The answer decides which documents you need.", "Written branch answer", "S03|S04"),
    ("M01", 2, "Assemble the source-of-funds file: the contract or sale document, the PRC tax certificate or receipt, and the bank statements showing the money arriving.", "Source-of-funds file", "S04|S06"),
    ("M01", 3, "Buy the USD at the branch's 现汇卖出价 and remit in one transfer. Above USD 50,000/day the bank takes the same ID plus the transaction documents — it does not require you to split the payment.", "ID + documents", "S03"),
    ("M01", 4, "Check the debit: 1‰ of the CNY amount, minimum CNY 50, capped at CNY 260, plus CNY 150 cable to a non-HK/Macau/Taiwan destination. Any other line on the receipt is a local or negotiated charge and should be queried against that tariff.", "Bank receipt", "S02"),
    ("M01", 5, "Record the USD amount received and the CNY amount debited. That pair is your starting point for the §988 computation, and the bank's rate is the consistently-applied posted rate the IRS accepts.", "Bank advice", "S09|S11"),
    ("M01", 6, "Report the account if the aggregate of your foreign accounts exceeded USD 10,000 at any point in the calendar year (FBAR) and if the Form 8938 threshold applies to you.", "FinCEN Form 114 / Form 8938", "S12|S13"),
    ("M02", 1, "Confirm with the branch that it will process a transfer above USD 50,000 with documents. If it will, M01 is cheaper; M02 is the fallback, not the default.", "Written branch answer", "S03"),
    ("M02", 2, "Divide the total into whole USD 50,000 transfers and schedule them.", "Transfer schedule", "S03"),
    ("M02", 3, "Expect the CNY 260 cap plus CNY 150 cable on every transfer, i.e. CNY 410 each, and budget the spread on each purchase.", "Bank receipts", "S02"),
    ("M02", 4, "Test the §988 USD 200 exclusion per transfer, because each disposal is its own transaction.", "Computation", "S09"),
    ("M03", 1, "Confirm you are an emigrant within art. 2 of the 2004 measures: you moved from the mainland to a foreign country and the property was yours before you acquired that status. A U.S. citizen who never held mainland household registration does not qualify.", "Status documents", "S06"),
    ("M03", 2, "Settle PRC tax first and obtain the tax certificate or payment receipt — it is a listed application document.", "PRC tax certificate", "S06|S08"),
    ("M03", 3, "Apply once, to the SAFE branch at your original household-registration locality, with the cancelled-registration certificate and the embassy/consulate proof of settlement abroad.", "Application file", "S06"),
    ("M03", 4, "After approval, instruct the bank to remit within the approved amount. Since 2014 it may be one lump sum or instalments — the old half/half/rest staging is cancelled.", "SAFE approval + bank instruction", "S07"),
    ("M03", 5, "Take payment into your own overseas account. The bank may not hand you domestic FX cash (art. 11).", "Remittance advice", "S06"),
    ("M04", 1, "Establish the inheritance with notarised documents: your status, the deceased's property rights, and the link between you.", "Notarised inheritance file", "S06"),
    ("M04", 2, "Obtain the tax certificate from the tax authority where the deceased's property is located.", "Tax certificate", "S06"),
    ("M04", 3, "Apply to the SAFE branch at the deceased's last registered locality. If you inherited from more than one person, the 2014 rules let you combine the applications.", "SAFE application", "S06|S07"),
    ("M04", 4, "Instruct the bank to remit within the approved amount, to your own account abroad.", "Bank instruction", "S06"),
    ("M05", 1, "Check the card: only a 外国人永久居留身份证 holder gets the annual convenience amount for FX purchase.", "Residence card", "S04"),
    ("M05", 2, "Buy FX within the convenience amount on ID; keep the income documents in case the branch asks.", "ID", "S04"),
    ("M06", 1, "Gather the evidence that the balance is lawful current-account income: employment or service contract, payslips, PRC tax withholding records. The 2026-07-13 branch answer addresses exactly this case — labour remuneration earned in China by a foreign individual.", "Income file", "S04|S16|S08"),
    ("M06", 2, "Present ID plus the source-of-funds materials including tax documents for the purchase. The bank tests whether the purpose of purchase matches the purpose of remittance.", "ID + income file", "S03|S04"),
    ("M06", 3, "Expect the same tariff as M01 and no published cap in the article quoted — but also no entitlement: the branch decides on the documents.", "Bank receipt", "S02|S04"),
    ("M07", 1, "Use your own card only. Lending or borrowing cards to get around the limit is expressly prohibited.", "Own card", "S15"),
    ("M07", 2, "Stay within CNY 10,000 per card per day and CNY 100,000 per person per calendar year; exceeding the annual figure suspends the facility this year and next.", "Withdrawal log", "S15"),
    ("M07", 3, "Price it from the issuer's own conversion rate and ATM fee — neither is published in the sources reviewed, so no number is shown.", "Issuer tariff", "S15"),
    ("M08", 1, "Check the PRC export limit with the bank or SAFE before carrying anything. The regulation delegates the figure to SAFE and it was not re-verified in this pass.", "SAFE guidance", "S05"),
    ("M08", 2, "File FinCEN Form 105 if the amount you carry exceeds USD 10,000; the threshold applies to the family or group total, not per person.", "FinCEN Form 105", "S14"),
    ("M08", 3, "Keep the declaration receipt. Failure to file risks seizure and forfeiture of the currency itself.", "CBP receipt", "S14"),
]


# --------------------------------------------------------------------------- penalties & flags
PENALTIES: list[dict] = [
    {"id": "P01", "side": "China", "rule": "Evading FX control (逃汇) — art. 39", "amount": "Fine up to 30% of the amount; where serious, from 30% up to the equivalent of the amount", "trigger": "Transferring domestic FX abroad, or moving domestic capital abroad by deception, in breach of the rules", "source": "S05"},
    {"id": "P02", "side": "China", "rule": "Illegal purchase of FX / illegal arbitrage (非法套汇) — art. 40", "amount": "Fine up to 30%; where serious, 30% up to the equivalent of the amount", "trigger": "False or void transaction documents used to buy FX", "source": "S05"},
    {"id": "P03", "side": "China", "rule": "Illegal carriage of FX across the border — art. 42", "amount": "Warning; fine up to 20% of the amount", "trigger": "Carrying FX in or out in breach of the limits", "source": "S05"},
    {"id": "P04", "side": "China", "rule": "Private or unlicensed FX trading — art. 45", "amount": "Warning, confiscation of illegal gains, fine up to 30%; where serious, 30% up to the equivalent of the amount", "trigger": "Buying and selling FX privately, in disguised form, or brokering it in size", "source": "S05"},
    {"id": "P05", "side": "China", "rule": "False or missing documents — art. 48", "amount": "Individual: fine up to CNY 50,000", "trigger": "Failing to submit valid documents, or submitting false ones", "source": "S05"},
    {"id": "P06", "side": "China", "rule": "Individual income tax on the underlying income — IIT Law art. 3(3)", "amount": "20% of the taxable gain on property transfer, interest, dividends, incidental income", "trigger": "The income or gain itself, not the conversion", "source": "S08"},
    {"id": "P07", "side": "U.S.", "rule": "FBAR — non-willful violation, 31 CFR 1010.821", "amount": "Maximum USD 16,536 per violation (assessed on or after 2025-01-17)", "trigger": "Failure to file FinCEN Form 114 when foreign accounts exceed USD 10,000 in aggregate", "source": "S10|S13"},
    {"id": "P08", "side": "U.S.", "rule": "FBAR — willful violation, 31 CFR 1010.821", "amount": "Maximum USD 165,353 per violation (a percentage-of-balance alternative in 31 U.S.C. 5321(a)(5)(C) was not re-read — F13)", "trigger": "Willful failure to file", "source": "S10"},
    {"id": "P09", "side": "U.S.", "rule": "Form 8938 — failure to disclose", "amount": "Up to USD 10,000, plus USD 10,000 per 30 days after notice, capped at USD 60,000", "trigger": "Not filing Form 8938 when the threshold is met", "source": "S12"},
    {"id": "P10", "side": "U.S.", "rule": "Currency reporting — FinCEN Form 105", "amount": "Seizure and forfeiture of the currency; civil or criminal penalties", "trigger": "Carrying more than USD 10,000 in or out without a report", "source": "S14"},
    {"id": "P11", "side": "U.S.", "rule": "§988 currency gain — no penalty, it is the tax itself", "amount": "Ordinary income on the gain; personal-transaction exclusion only if the gain is USD 200 or less", "trigger": "Disposing of the CNY deposit", "source": "S09"},
]

FLAGS: list[dict] = [
    {"id": "F01", "item": "Your facts are not in evidence", "why": "No balance, account type, residency or household-registration status, acquisition date or cost basis, or tax filings were supplied. Every route therefore carries an eligibility condition that cannot be checked here.", "source": "S04|S06"},
    {"id": "F02", "item": "The 'considerable taxes' premise", "why": "No assessment, bank quote, withholding receipt or named tax was supplied, so the premise is neither confirmed nor denied. The penalties in this edition are the ones the cited instruments actually impose.", "source": "S05|S08"},
    {"id": "F03", "item": "§988 cost basis unknown", "why": "The U.S. currency-gain figure is a sensitivity over assumed acquisition rates, not a computation of your liability. It changes sign if the CNY was acquired when the yuan was weaker than today.", "source": "S09|S11"},
    {"id": "F04", "item": "PRC tax on the source of the money", "why": "The 20% rate on property-transfer income is verified; the deductible original value and reasonable expenses that produce the base are transaction-specific and blank.", "source": "S08"},
    {"id": "F05", "item": "Unpublished prices and limits left blank", "why": "Card FX rates and ATM fees, the PRC cash-export figure, and the convenience-amount figure are not stated in the pages reviewed. They are blank, never zero.", "source": "S05|S15"},
    {"id": "F06", "item": "Every total is China-side only", "why": "The U.S. receiving bank's incoming-wire fee and any correspondent deduction are commercial and not published in an official source, so they are absent from the total.", "source": "S02"},
    {"id": "F07", "item": "The board is one timestamped snapshot", "why": "The USD row moved between the 07:32:39 and 17:39:58 readings on 2026-11-10. The ladder is reproducible only against the recorded reading in data/c3x_inputs.csv.", "source": "S01"},
    {"id": "F08", "item": "Two official definitions of 境内个人", "why": "Order 532 art. 52(2) includes a foreigner resident in China for one continuous year; the current-account guidance separates 境外个人 and gives the convenience amount only to a permanent-resident-ID holder. Which one your branch applies — and whether an emigrant route is open to someone who never held mainland household registration — is a written answer to obtain before acting.", "source": "S04|S05"},
    {"id": "F09", "item": "Absence of a conversion tax is not a clearance", "why": "'No PRC tax on the conversion itself was found' is a statement about the instruments reviewed, not a ruling. The tax attaches to the underlying income and to the exit settlement in art. 13.", "source": "S08"},
    {"id": "F10", "item": "Parallel editions disagree at USD 400,000", "why": "One published model prices eight wires (USD 1,332.05) and another prices one (USD 901.30). This edition prices both and explains that the split is a fee assumption, not a rule (S03). Nothing was deleted.", "source": "S03"},
    {"id": "F11", "item": "Prohibited routes are catalogued, not priced", "why": "Crypto, underground banking and quota splitting appear so they can be recognised and refused. No cost is estimated because the sanction is a fine or confiscation, and the crypto prohibition instrument was not re-verified in this pass.", "source": "S05"},
    {"id": "F13", "item": "Willful FBAR percentage alternative not re-read",
     "why": "The eCFR table gives the adjusted USD 165,353 ceiling for 31 U.S.C. 5321(a)(5)(C)(i)(I). The statute also provides a percentage-of-the-balance alternative; only the table's figure was read in this pass, so the percentage is not stated as verified.", "source": "S10"},
    {"id": "F14", "item": "No tax-treaty analysis",
     "why": "The U.S.–China income tax treaty was not fetched or analysed in this pass, so no relief under it is asserted or denied. Nothing on these pages should be read as a treaty conclusion.", "source": "S09|S08"},
    {"id": "F12", "item": "Not tax or legal advice", "why": "This is source-based research on documents fetched on 2026-11-10. Bank practice, branch interpretation and the board itself change.", "source": "S01|S05"},
]


# --------------------------------------------------------------------------- writers
def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def build_data() -> None:
    write_csv(DATA / "c3x_sources.csv", SOURCES,
              ["id", "issuer", "title", "url", "doc_date", "fetched_utc", "quote", "proposition"])

    inputs = [{"id": k, **v} for k, v in INPUTS.items()]
    write_csv(DATA / "c3x_inputs.csv", inputs, ["id", "value", "unit", "source", "note"])

    write_csv(DATA / "c3x_ladder.csv", ladder_rows(),
              ["amount_usd", "cny_needed", "spread_usd", "fee_cny", "fee_usd",
               "single_total_usd", "single_total_pct", "staged_wires", "staged_fee_usd",
               "staged_total_usd", "staged_total_pct", "sec988_tax_37_usd"])

    write_csv(DATA / "c3x_methods.csv", METHODS,
              ["id", "name", "category", "lawfulness", "eligibility", "pros", "cons",
               "price_model", "prc_tax", "us_tax", "sources"])

    write_csv(DATA / "c3x_method_costs.csv", method_grid(),
              ["method_id", "amount_usd", "cost_usd", "cost_pct", "flag", "basis"])

    write_csv(DATA / "c3x_steps.csv",
              [{"method_id": a, "step": b, "action": c, "document": d, "source": e} for a, b, c, d, e in STEPS],
              ["method_id", "step", "action", "document", "source"])

    write_csv(DATA / "c3x_penalties.csv", PENALTIES,
              ["id", "side", "rule", "amount", "trigger", "source"])

    write_csv(DATA / "c3x_flags.csv", FLAGS, ["id", "item", "why", "source"])


def load(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    build_data()
    one = money_row(D(10_000))
    big = money_row(D(400_000))
    many = staged_row(D(400_000))
    print(f"ask {ASK}  bid {BID}  mid {MID:.4f}  half-sp(read) {spread_pct()*100:.4f}%")
    print(f"10k   single {one['total_usd']:.2f} ({one['total_pct']:.4f}%)")
    print(f"400k  single {big['total_usd']:.2f} ({big['total_pct']:.4f}%)")
    print(f"400k  staged {many['wires']}x {many['total_usd']:.2f} ({many['total_pct']:.4f}%)")
    print("wrote data/c3x_*.csv")
