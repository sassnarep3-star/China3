#!/usr/bin/env python3
"""R11 engine — the 2026-11-11 release.

This module is the single source of truth for:

  * the live re-verification register (data/r11_sources.csv, data/r11_facts.csv)
  * the $10,000 -> $400,000 cost ladder for every priced channel (data/r11_ladder.csv,
    data/r11_channels.csv)
  * the decision-gate question register (data/r11_questions.csv)
  * the repository review findings (data/r11_repo_review.csv)
  * the flag register (data/r11_flags.csv)

Arithmetic conventions (stated on every page that prints a number):

  M1  Convert-and-wire.  The customer buys USD at the bank's SELLING rate and pays the
      wire tariff on top.  "Spread" is the gap between the bank's own MID (the mean of
      its buying and selling rates) and the rate the customer actually gets.  It is an
      opportunity cost, not a fee the bank charges separately.
  M2  Wire only.  Foreign currency already in the account: no conversion, so no spread.
  M3  Quota (USD 50,000 a year, Foreign Permanent Resident ID holders only).  Spread is
      taken once on the whole amount; the wire tariff is paid once per yearly tranche.
  M4  Staging (immigrant property transfer).  The 2004 rule staged the money, but
      汇发〔2014〕2号 Art. 6(2) cancelled instalments, so the base model is one approval
      and one or more wires.  The staged scenario is shown as a what-if only.
  M5  Cash and ATM.  Only the published part of the cost is priced; everything else is
      blank and flagged.

Nothing here is inferred: every input carries the source id it was read from, and a
value that no official page publishes is None and renders blank with a flag.
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

CENT = D("0.01")
VERIFIED_ON = "2026-11-11"
UTC_STAMP = "2026-11-11T03:20:00Z"


def q(x, places=CENT):
    return x.quantize(places, rounding=ROUND_HALF_UP)


def usd(x, places=CENT):
    """Money for display. Always with thousands separators, never a bare float."""
    return f"${q(x, places):,}"


def pct(x, places=2):
    return f"{D(x).quantize(D('1.' + '0' * places), rounding=ROUND_HALF_UP)}%"


def ceil_int(x):
    return int(D(x).to_integral_value(rounding=ROUND_CEILING))


# --------------------------------------------------------------------------- inputs
# Every figure below was read from the official page named beside it on 2026-11-11.
RATE = {
    # S01 Bank of China FX board, page 1, USD row, Pub Time 2026/11/11 10:25:02
    # figures are CNY per 100 USD.
    "board_time": "2026/11/11 10:25:02 (Beijing)",
    "bid": D("6.6630"),        # Buying Rate   666.30
    "ask": D("6.6911"),        # Selling Rate  669.11
    "cash_ask": D("6.6911"),   # Cash Selling Rate 669.11
    "middle_col": D("6.7191"),  # BOC "Middle Rate" column 671.91 (reference rate, not used)
    # S02 Bank of China personal e-banking cross-border wire tariff
    "wire_rate": D("0.001"), "wire_min": D("50"), "wire_max": D("260"), "cable": D("150"),
    # S03 Bank of China ATM notice effective 2026-11-11 (UnionPay overseas)
    "atm_fixed": D("12"), "atm_pct": D("0.01"), "atm_max": D("112"),
    # S19 SAFE 汇发〔2017〕29号: per card per day, per person per year
    "atm_day_cap_cny": D("10000"), "atm_year_cap_cny": D("100000"),
    # S08 经常项目外汇业务指引 (2020) Art. 54; S05 Art. 59 second sentence
    "quota_usd": D("50000"),
    # S20 SAFE Hebei answer: 5,000 without permit / 10,000 with bank permit
    "cash_no_permit_usd": D("5000"), "cash_bank_permit_usd": D("10000"),
    # S25 Individual Income Tax Law Art. 3(3)
    "iit_flat": D("0.20"),
    # S28 IRS yearly average rates, CNY per USD. Read live 2026-11-11.
    "irs_avg": {"2021": D("6.452"), "2022": D("6.730"), "2023": D("7.075"),
                "2024": D("7.189"), "2025": D("7.129")},
    # S36 / S37 US statute
    "fb_nonwillful": D("16536"), "fb_willful_floor": D("165353"),
    "f8938_max": D("60000"), "f3520_pct": D("0.05"), "f3520_cap": D("0.25"),
    "s988_personal_gain": D("200"),
}

AMOUNTS = [D(n) for n in range(10000, 400001, 10000)]

# Rate scenarios for the sensitivity table (M1 formula, 1 wire, $100,000).
# A = today's board (S01). B and C are the two older board readings that earlier
# sessions published, kept so the reader can see how much of each headline figure is
# the clock rather than the channel.
SCENARIOS = [
    ("A", "2026-11-11 10:25:02", D("6.6630"), D("6.6911"), True,
     "This release. Bank of China board, read live."),
    ("B", "2026-11-10 17:39:58", D("6.6571"), D("6.6851"), False,
     "Previous release's reading (e347 layer). Same BOC board page, earlier snapshot."),
    ("C", "2026-11-10 (earlier)", D("6.6622"), D("6.6903"), False,
     "Reading published by the fbbd3b22 / s775 layers. Same page, earlier snapshot."),
]


def mid():
    return (RATE["bid"] + RATE["ask"]) / 2


def spread_usd(amount):
    """M1 spread: the gap between the operator's mid and the rate the customer pays."""
    return amount * (RATE["ask"] - mid()) / RATE["ask"]


def wire_cny(amount_usd):
    """S02: 0.1% of the RMB amount, floor 50, cap 260, plus 150 cable."""
    raw = amount_usd * RATE["ask"] * RATE["wire_rate"]
    return min(RATE["wire_max"], max(RATE["wire_min"], raw)) + RATE["cable"]


def wire_usd(amount_usd):
    return wire_cny(amount_usd) / RATE["ask"]


def wire_floor_cny():
    return RATE["wire_min"] + RATE["cable"]


# ------------------------------------------------------------------------- sources
# id, issuer, title, url, how read, verbatim quote or exact figure, what it establishes
SOURCES = [
    ("S01", "Bank of China", "BOC Exchange Rate board (USD row), page 1",
     "https://www.boc.cn/sourcedb/whpj/enindex_1619.html", "direct",
     "USD | Buying Rate 666.3 | Cash Buying Rate 666.3 | Selling Rate 669.11 | Cash Selling Rate 669.11 | Middle Rate 671.91 | Pub Time 2026/11/11 10:25:02",
     "The only exchange rate used in this release: 6.6630 buying, 6.6911 selling, per USD."),
    ("S02", "Bank of China", "中国银行电子银行个人服务转账汇款费率表 (personal e-banking transfer tariff)",
     "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "direct",
     "跨境汇款（电汇） 每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。",
     "Outbound wire fee: 0.1%, min RMB 50, max RMB 260, plus RMB 150 cable outside HK/Macau/Taiwan. Effective 2014-11-01. Note 1 permits agreed, promotional and local variations."),
    ("S03", "Bank of China", "关于调整部分个人服务收费内容的公告 (2026年11月11日起) — ATM cash withdrawal",
     "https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html", "direct",
     "国外及中国港澳台：银联：每笔（12 元+取现金额的1%）收取，最高 112 元/笔；万事达、VISA：取现金额的2.5%，最低等值3美元/笔，最高等值40美元/笔",
     "Overseas ATM: UnionPay RMB 12 + 1% of the withdrawal, capped at RMB 112. In force from 2026-11-11."),
    ("S04", "SAFE Tianjin", "2026年外汇管理互联网信息——个人外汇（08）, 2026-07-13",
     "https://www.safe.gov.cn/tianjin/2026/0713/3088.html", "direct",
     "境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇",
     "汇发〔2020〕14号 Art. 59: a foreign individual buying FX against income earned in China needs ID plus source-of-funds material including tax evidence."),
    ("S05", "SAFE Tianjin", "2024年经常项目外汇政策问答案例（九）, 2024-06-21",
     "https://www.safe.gov.cn/tianjin/2024/0621/2529.html", "direct",
     "持有外国人永久居留身份证的境外个人适用购汇年度便利化额度。",
     "Only a foreign individual holding the PRC Foreign Permanent Resident ID card gets the annual convenience amount for buying FX."),
    ("S06", "SAFE Ningxia", "2022年外汇业务政策释疑（八）, 2022-09-29",
     "https://www.safe.gov.cn/ningxia/2022/0929/1997.html", "direct",
     "个人结汇和境内个人购汇实行年度便利化额度管理，便利化额度分别为每人每年等值5万美元 … 年度便利化额度不是个人每年购汇或者结汇的限额，只是超过等值5万美元的购汇或结汇不能仅凭本人有效身份证件办理。",
     "The USD 50,000 is a convenience amount, not a ceiling: above it the same conversion is done with documents. The rule appends 境内个人 (domestic individual) to the buying side."),
    ("S07", "SAFE", "《经常项目外汇业务指引（2020年版）》 full text (annex to 汇发〔2020〕14号)",
     "http://m.safe.gov.cn/safe/file/file/20200831/f0127756271c43ef9b3908d5d157bd91.pdf", "direct",
     "第六十五条 境外个人经常项目外汇汇出境外：（一）外汇账户内外汇汇出，凭本人有效身份证件办理；（二）持外币现钞汇出，当日累计等值1万美元以下（含）的，凭本人有效身份证件办理。 第六十二条 … 关注期限为列入“关注名单”的当年及之后连续 2 年。",
     "Art. 65: a foreign individual's FX-account remittance needs only valid ID, with no amount threshold. Art. 62: watch-list period is the year of listing plus two."),
    ("S08", "People's Bank of China / SAFE", "中国人民银行公告[2004]第16号 —《个人财产对外转移售付汇管理暂行办法》",
     "http://m.safe.gov.cn/safe/2004/1116/5461.html", "direct",
     "移民转移必须一次性申请拟转移出境的全部财产金额，分步汇出。首次可汇出金额不得超过全部申请转移财产的一半；自首次汇出满一年后，可汇出不超过剩余财产的一半 … 全部申请转移财产在等值人民币20万元以下（含20万元）的，经批准后可一次性汇出。",
     "The dedicated route for an emigrant's own pre-departure property and for an inheritance; one application, staged remittance in the original rule."),
    ("S09", "SAFE Tianjin", "（已修改）汇发〔2014〕2号 关于进一步改进和调整资本项目外汇管理政策的通知",
     "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "direct",
     "六、简化个人财产转移售付汇管理 …（二）取消移民财产转移分次汇出的要求。申请人向原户籍所在地外汇局办理移民财产转移核准手续后，银行可在核准件审批额度内一次或分次汇出相关资金。",
     "Art. 6(2) removed the staging requirement: after approval the bank may remit once or in instalments. Art. 6(1) also removed the RMB 500,000 referral to SAFE headquarters."),
    ("S10", "SAFE Tianjin", "个人财产转移购付汇业务问答（七）, 2026-03-19",
     "https://www.safe.gov.cn/tianjin/2026/0319/3018.html", "direct",
     "根据《…资本项目外汇业务指引（2024年版）》（汇发〔2024〕12号）6.4，移民财产转移由移民原户籍所在地外汇局负责审批。继承财产转移由被继承人生前户籍所在地外汇局负责审批。",
     "Where the two property-transfer routes are approved: the former hukou for emigrant transfer, the decedent's hukou for inheritance."),
    ("S11", "SAFE Tianjin", "2026年外汇管理互联网信息——个人外汇（10）, 2026-09-17",
     "https://www.safe.gov.cn/tianjin/2026/0917/3134.html", "direct",
     "境外个人原兑换未用完的人民币兑回外汇，凭本人有效身份证件和原兑换水单办理，原兑换水单的兑回有效期为自兑换日起24个月；对于当日累计兑换不超过等值500美元（含）…的兑换，可凭本人有效身份证件办理。",
     "Change-back route: 24-month validity of the original exchange slip; USD 500 a day without one."),
    ("S12", "SAFE Tianjin", "2025年外汇管理互联网信息——个人外汇（八）, 2025-06-13",
     "https://www.safe.gov.cn/tianjin/2025/0613/2811.html", "direct",
     "外汇局对借用他人便利化额度及其他方式规避便利化额度及真实性管理的个人，列入“关注名单”管理",
     "Borrowing another person's convenience amount puts you on the watch list."),
    ("S13", "SAFE Hubei", "汇发〔2017〕29号 关于规范银行卡境外大额提取现金交易的通知",
     "https://www.safe.gov.cn/hubei/2019/0305/851.html", "direct",
     "个人持境内银行卡在境外提取现金，本人名下银行卡（含附属卡）合计每个自然年度不得超过等值10万元人民币。超过年度额度的，本年及次年将被暂停持境内银行卡在境外提取现金。… 人民币卡管理维持每卡每日不得超过等值1万元人民币",
     "ATM ceiling: RMB 10,000 per card per day, RMB 100,000 per person per year; breach suspends overseas cash withdrawals for the year and the next."),
    ("S14", "SAFE Hebei", "外汇知识问答：请问每次可带外币出境的限额是多少？, 2019-05-21",
     "http://www.safe.gov.cn/hebei/2019/0521/1366.html", "direct",
     "个人携带外币现钞金额在5000美元（含）以下的，海关直接放行；5000美元以上10000美元（含）以下的，应向银行申领《携带外汇出境许可证》；10000美元以上的，应向外汇局申领…但原则上…不得携带10000美元以上的外币现钞出境。",
     "Cash carrying: USD 5,000 free, 5,000-10,000 with a bank permit, above 10,000 in principle not allowed."),
    ("S15", "SAFE Guangdong", "关于个人网上办理外币兑换业务的温馨提示, 2020-03-04",
     "https://www.safe.gov.cn/guangdong/2020/0304/1668.html", "direct",
     "个人在银行办理结售汇业务…应通过银行等正规渠道办理，不得通过非法渠道买卖外汇",
     "Only banks and licensed outlets may convert currency; private FX trading is not a lawful channel."),
    ("S16", "State Council / SAFE", "中华人民共和国外汇管理条例 (国务院令第532号)",
     "https://www.safe.gov.cn/safe/2008/0806/5321.html", "direct",
     "第五条 国家对经常性国际支付和转移不予限制。 第三十九条 …处逃汇金额30%以下的罚款；情节严重的，处逃汇金额30%以上等值以下的罚款。 第四十五条 私自买卖外汇…处违法金额30%以下的罚款；情节严重的，处违法金额30%以上等值以下的罚款。 第五十二条（二）境内个人，是指中国公民和在中华人民共和国境内连续居住满1年的外国人",
     "No restriction on current international payments and transfers; the penalty ladder for evading, buying FX with false documents and private FX trading; and the Regulation's own definition of 境内个人."),
    ("S17", "People's Bank of China", "个人外汇管理办法 (中国人民银行令〔2006〕第3号)",
     "http://m.safe.gov.cn/safe/2006/1225/5319.html", "direct",
     "第十二条 …单笔或当日累计汇出在规定金额以上的，凭本人有效身份证件和有交易额的相关证明等材料在银行办理。 第十三条 境外个人在境内取得的经常项目项下合法人民币收入，可以凭本人有效身份证件及相关证明材料在银行办理购汇及汇出。 第三十七条（二）境外个人是指持护照…的外国公民",
     "The Measures classify by ID document: a passport holder is a 境外个人. Art. 13 permits buying FX and remitting against lawful current-account income."),
    ("S18", "State Taxation Administration / SAFE", "国家税务总局 国家外汇管理局公告2013年第40号 (tax filing for outbound payments)",
     "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html", "direct",
     "一、境内机构和个人向境外单笔支付等值5万美元以上…均应向所在地主管税务机关进行税务备案 … 六、…主管税务机关无须当场进行纳税事项审核，应编制《备案表》流水号，在《备案表》上盖章",
     "The 对外支付税务备案 is a filing, not a charge: the tax office issues the form without auditing the tax on the spot. It is triggered above USD 50,000 per payment in the listed categories."),
    ("S19", "SAFE Tianjin", "2021年服务贸易外汇管理问题解答（四）, 2021-11-02",
     "https://www.safe.gov.cn/tianjin/2021/1102/1777.html", "direct",
     "境外个人将其从境内取得的服务贸易、收益和经常转移项下的人民币收入购汇汇出的，可凭本人身份证件和有交易额的相关证明材料（含税务凭证）办理；税务凭证包括《服务贸易等项目对外支付税务备案表》或完税证明或免税证明。",
     "What counts as tax evidence: the filing form, a tax payment certificate, or an exemption certificate."),
    ("S20", "State Taxation Administration", "中华人民共和国个人所得税法 (2018 amendment)",
     "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html", "direct",
     "第三条（三）利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十。 第四条 lists the exempt categories (no inheritance clause); 第十八条 leaves savings-deposit interest to the State Council.",
     "The 20% flat rate on dividends, interest, rent, property gains and incidental income; 3%-45% progressive on wages and service income; nine taxable categories with no inheritance category."),
    ("S21", "Ministry of Finance / State Taxation Administration", "财税〔2008〕132号 关于储蓄存款利息所得有关个人所得税政策的通知",
     "https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html", "direct",
     "自2008年10月9日起，对储蓄存款利息所得暂免征收个人所得税 … 储蓄存款在2008年10月9日后（含10月9日）孳生的利息所得，暂免征收个人所得税。",
     "Interest on a savings deposit accrued from 9 October 2008 is exempt from individual income tax."),
    ("S22", "People's Bank of China et al.", "银发〔2026〕42号 关于进一步防范和处置虚拟货币等相关风险的通知, 2026-02-06",
     "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html", "direct",
     "在境内开展法定货币与虚拟货币兑换业务…属于非法金融活动，一律严格禁止 … 本通知自发布之日起施行。…《…》（银发〔2021〕237号）同时废止。",
     "Converting RMB into crypto or stablecoins inside mainland China is prohibited by the notice in force from 2026-02-06, which repealed the 2021 notice."),
    ("S23", "Bank of China", "个人金融服务收费 — 中银财互通 note / 外币现钞",
     "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "direct",
     "中行内跨省、省内异地外币转账 每笔转账金额的1‰，最高200元/笔。",
     "Domestic transfers between BOC foreign-currency accounts: 0.1% of the amount, max RMB 200."),
    ("S24", "SAFE Anhui", "深化跨境投融资外汇管理便利化政策操作指引 (operating guide to 汇发〔2025〕43号), §8",
     "https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf", "excerpt",
     "§8 lists the documents for a personal property-transfer remittance, including the registered property contract and the tax certificate, and caps the remittance at the sale price less the taxes of that sale.",
     "The document list and the cap for the home-sale route. Read as an excerpt (section 8 only); flag U17 remains open."),
    ("S25", "US Government Publishing Office", "26 U.S.C. § 988 — Treatment of certain foreign currency transactions (2023 ed.)",
     "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", "direct",
     "§988(c)(1)(C)(i) the disposition of any nonfunctional currency shall be treated as a section 988 transaction … §988(e)(2) The preceding sentence shall not apply if the gain which would otherwise be recognized on the transaction exceeds $200. §988(e)(3) 'personal transaction' … shall not include any transaction to the extent that expenses properly allocable to such transaction meet the requirements of section 162 … or section 212.",
     "Selling RMB is a §988 transaction. The personal-transaction relief only covers USD 200 or less of gain; above that the whole gain is ordinary income."),
    ("S26", "Internal Revenue Service", "Yearly average currency exchange rates",
     "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates", "direct",
     "China | Yuan | 2025 7.129 | 2024 7.189 | 2023 7.075 | 2022 6.730 | 2021 6.452. The IRS has no official exchange rate; it generally accepts any posted rate used consistently.",
     "The yearly average rate used to size a currency gain, and the IRS statement that it publishes no official rate."),
    ("S27", "Internal Revenue Service", "Comparison of Form 8938 and FBAR requirements",
     "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "direct",
     "Form 8938: Specified individuals living in the US … more than $50,000 on the last day of the tax year, or more than $75,000 at any time during the year … Penalties: Up to $10,000 for failure to disclose and an additional $10,000 for each 30 days of non-filing after IRS notice … potential maximum penalty of $60,000. FBAR: aggregate value … exceeds $10,000 at any time during the calendar year.",
     "FBAR threshold USD 10,000 on the aggregate; Form 8938 thresholds by filing status and residence; the USD 60,000 Form 8938 penalty ceiling."),
    ("S28", "eCFR (FinCEN)", "31 CFR 1010.821 — Penalty adjustment and table",
     "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "direct",
     "31 U.S.C. 5321(a)(5)(B)(i) Foreign Financial Agency Transaction—Non-Willful Violation … 10,000 -> 16,536. 31 U.S.C. 5321(a)(5)(C)(i)(I) Willful Violation … 100,000 -> 165,353. Column heading: Maximum penalty amount … for penalties assessed on or after January 17, 2025.",
     "The inflation-adjusted FBAR ceilings in force for assessments on or after 2025-01-17."),
    ("S29", "FinCEN", "Report Foreign Bank and Financial Accounts (FBAR page)",
     "https://www.fincen.gov/report-foreign-bank-and-financial-accounts", "direct",
     "A United States person must file an FBAR to report a financial interest in or signature authority over at least one financial account located outside of the United States if the aggregate value of all foreign financial accounts exceeds $10,000 at any time during the calendar year.",
     "Who must file an FBAR, and the calendar-year maximum-value basis."),
    ("S30", "US Government Publishing Office", "31 U.S.C. § 5321 — Civil penalties (2023 ed.)",
     "https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm", "direct",
     "§5321(a)(5)(C)(i) the maximum penalty … shall be increased to the greater of— (I) $100,000, or (II) 50 percent of the amount determined under subparagraph (D) … §5321(a)(5)(D)(ii) … the balance in the account at the time of the violation.",
     "The statutory willful alternative: the greater of USD 100,000 (as adjusted) or 50% of the account balance at the time of the violation."),
    ("S31", "Internal Revenue Service", "Gifts from foreign person (Form 3520, Part IV)",
     "https://www.irs.gov/businesses/gifts-from-foreign-person", "direct",
     "For gifts or bequests from a nonresident alien or foreign estate, you are required to report … only if the aggregate amount received … exceeds $100,000 during the taxable year. … For purported gifts from foreign corporations or foreign partnerships … exceeds $20,116 for 2025, and $20,573 for 2026.",
     "A foreign gift or bequest is not income to the recipient; the USD 100,000 threshold triggers Form 3520 reporting. USD 20,573 is the 2026 threshold for gifts from foreign corporations and partnerships."),
    ("S32", "US Government Publishing Office", "26 U.S.C. § 6039F — Notice of large gifts received from foreign persons",
     "https://www.govinfo.gov/content/pkg/USCODE-2021-title26/html/USCODE-2021-title26-subtitleF-chap61-subchapA-partIII-subpartA-sec6039F.htm", "direct",
     "§6039F(c) … an amount equal to 5 percent of the amount of such foreign gift for each month for which the failure continues (not to exceed 25 percent in the aggregate).",
     "The Form 3520 penalty: 5% of the gift per month, capped at 25%."),
    ("S33", "US Customs and Border Protection", "Money and Other Monetary Instruments",
     "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments", "direct",
     "There is no limit on the amount of money that may be brought into or taken out of the United States. However, if you transport or cause to be transported … more than $10,000 in monetary instruments on any occasion into or out of the United States … you must file a report (FinCEN 105).",
     "No limit on importing cash; more than USD 10,000 must be reported on FinCEN Form 105 on entry."),
    ("S34", "SAFE Tianjin", "2024年外汇管理互联网信息——个人外汇（三）, 2024-02-29",
     "https://www.safe.gov.cn/tianjin/2024/0229/2402.html", "direct",
     "第六十四条 境内个人外汇汇出境外用于经常项目支出 … 外汇账户内外汇汇出境外当日累计等值5万美元以下（含）的，凭本人有效身份证件办理；超过上述金额的，凭本人有效身份证件、有交易额的相关材料办理。",
     "Art. 64 shows that the same threshold logic (ID alone up to USD 50,000, documents above) is applied on the domestic-individual side of the same article set."),
]
SRC = {s[0]: s for s in SOURCES}

# -------------------------------------------------------------------------- facts
# id, group, statement, value, used where, source ids, flags
FACTS = [
    ("F01", "Conversion", "A tax on changing RMB into USD or wiring it out",
     "no rate found", "the whole release", ["S16", "S04", "S17"], ["U02"]),
    ("F02", "Conversion", "Chinese individual income tax on wages and service income",
     "3% to 45% progressive", "Tax page", ["S20"], ["U01"]),
    ("F03", "Conversion", "Chinese individual income tax on dividends, interest, rent, property gains, incidental income",
     "20% flat", "Tax page, dividend route", ["S20"], ["U01"]),
    ("F04", "Conversion", "Chinese individual income tax on savings-deposit interest accrued from 2008-10-09",
     "exempt", "Tax page, single-deposit route", ["S21"], []),
    ("F05", "Conversion", "Outbound payment tax filing (对外支付税务备案) above USD 50,000 per payment",
     "a filing, no charge shown", "Steps, Tax page", ["S18", "S19"], []),
    ("F06", "Bank cost", "Bank of China USD selling rate on 2026-11-11",
     "6.6911 CNY per USD", "every conversion row", ["S01"], ["U15"]),
    ("F07", "Bank cost", "Bank of China outbound personal wire fee",
     "0.1%, RMB 50 min, RMB 260 max, plus RMB 150 cable", "every wire row", ["S02"], ["U03"]),
    ("F08", "Bank cost", "Intermediary and receiving-bank fees",
     "", "blank in every total", ["S02"], ["U04"]),
    ("F09", "Limits", "Annual convenience amount for buying FX",
     "USD 50,000 per person per year, PRC Foreign Permanent Resident ID holders only", "quota column", ["S06", "S05"], []),
    ("F10", "Limits", "Remittance from a foreign individual's FX account",
     "no amount threshold in Art. 65; valid ID required", "wire-only route", ["S07"], ["U11"]),
    ("F11", "Limits", "Overseas ATM withdrawal on a mainland card",
     "RMB 10,000 per card per day; RMB 100,000 per person per year", "ATM route", ["S13"], []),
    ("F12", "Limits", "Carrying foreign-currency cash out",
     "USD 5,000 free; 5,000-10,000 with a bank permit; above 10,000 in principle not allowed", "cash route", ["S14"], []),
    ("F13", "Limits", "Immigrant and inheritance property transfer",
     "one application; approval at the former hukou / decedent's hukou; instalments no longer required", "property routes", ["S08", "S09", "S10"], []),
    ("F14", "US tax", "Currency gain on selling RMB (26 U.S.C. § 988)",
     "ordinary income; personal-transaction relief only up to USD 200 of gain", "currency-gain table", ["S25", "S26"], ["U05"]),
    ("F15", "US tax", "A foreign gift or bequest in the hands of a U.S. recipient",
     "not income; Form 3520 above USD 100,000 (individuals) or USD 20,573 (2026, foreign corporations/partnerships)", "Tax page", ["S31", "S32"], []),
    ("F16", "US reporting", "FBAR (FinCEN 114) filing threshold",
     "USD 10,000 aggregate at any time in the calendar year", "Tax page", ["S27", "S29"], []),
    ("F17", "US reporting", "FBAR maximum penalties",
     "USD 16,536 non-willful per report; willful the greater of USD 165,353 or 50% of the balance", "Tax page", ["S28", "S30"], []),
    ("F18", "US reporting", "Form 8938 thresholds (unmarried, living in the US)",
     "USD 50,000 on the last day or USD 75,000 at any time; penalty ceiling USD 60,000", "Tax page", ["S27"], []),
    ("F19", "US reporting", "Form 3520 penalty for a late gift report",
     "5% of the gift per month, capped at 25%", "Tax page", ["S32"], []),
    ("F20", "US reporting", "Carrying more than USD 10,000 of monetary instruments into the US",
     "report on FinCEN Form 105", "Tax page, cash route", ["S33"], []),
    ("F21", "Prohibited", "Evading FX controls, buying FX with false documents, private FX trading",
     "fine up to 30% of the amount; 30% to 100% in serious cases; criminal liability possible", "Methods page", ["S16"], []),
    ("F22", "Prohibited", "Borrowing or lending the annual convenience amount",
     "watch list for the year of listing plus the next two years", "Methods page", ["S12", "S07"], []),
    ("F23", "Prohibited", "Converting RMB into crypto or stablecoins inside mainland China",
     "prohibited financial activity since 2026-02-06 (银发〔2026〕42号)", "Methods page", ["S22"], []),
    ("F24", "Prohibited", "Borrowing or lending bank cards to beat the overseas ATM cap",
     "expressly forbidden by 汇发〔2017〕29号", "Methods page", ["S13", "S16"], []),
]

# ----------------------------------------------------------------------- channels
# id, kind, route, who it fits, cap, published cost part, what is blank, pros, cons,
# tax position, source ids, flags
CHANNELS = [
    dict(id="L01", kind="Lawful", model="fx_wire",
         name="Documented income earned in China (salary, fees, other current-account income)",
         fits="The RMB is your own lawful income from China and you can show where it came from and that Chinese tax on it was dealt with.",
         cap="No amount ceiling in the rule. Identity plus source-of-funds material including tax evidence (Art. 59). The filing rule bites above USD 50,000 per payment.",
         published="Exchange spread plus the 0.1% wire fee (RMB 50-260) and RMB 150 cable.",
         blank="Intermediary and receiving-bank fees. Time at the counter. Whether the branch accepts your particular documents.",
         pros="The standard route for a passport holder. One wire for the whole amount. The cheapest conversion route that involves an exchange.",
         cons="The bank must see source documents and tax evidence. If Chinese tax was never paid on the income, it is settled before the money moves.",
         tax="No tax on the conversion itself. Chinese income tax applies to the underlying income (3%-45% on wages, 20% on the flat categories).",
         src=["S04", "S17", "S19", "S18"], flags=["U01", "U03", "U04"]),
    dict(id="L02", kind="Lawful", model="fx_wire",
         name="Change back unused RMB with the original exchange slip (兑换水单)",
         fits="You brought foreign currency into China, changed it to RMB within the last 24 months, and still hold the bank's exchange slip.",
         cap="Up to the unused amount on the slip; the slip is valid 24 months from the exchange date. Without a slip, USD 500 a day on ID alone.",
         published="Exchange spread plus the same wire fee.",
         blank="Intermediary and receiving-bank fees; whether the branch will pay out the whole slip amount in one go.",
         pros="Only a passport and the slip. No income or tax documents.",
         cons="Useless for RMB earned or received in China, and for slips older than 24 months.",
         tax="None identified: your own money changed back.",
         src=["S11", "S07"], flags=["U03", "U04"]),
    dict(id="L03", kind="Lawful", model="wire_only",
         name="Wire out foreign currency already sitting in your Chinese foreign-currency account",
         fits="Part of the balance was never converted: dollars wired in from abroad and left in a USD account.",
         cap="Art. 65 names no amount threshold for a foreign individual's FX-account remittance: valid ID, nothing more.",
         published="The wire fee only. No conversion, so no spread.",
         blank="Intermediary and receiving-bank fees.",
         pros="Cheapest lawful route of all: the wire tariff and nothing else.",
         cons="Only helps the part of the balance that is already foreign currency. The bank still runs its own checks and can refuse.",
         tax="None identified: no conversion takes place.",
         src=["S07", "S17", "S02"], flags=["U04", "U11"]),
    dict(id="L04", kind="Lawful, needs bank documents", model="fx_wire",
         name="Proceeds of selling a home you owned in China",
         fits="The RMB is what you were paid for residential property registered in your name.",
         cap="Not more than the sale price less the taxes of that sale (your share if co-owned). Registered contract, registration proof and tax certificate.",
         published="Exchange spread plus the same wire fee.",
         blank="The 2025 operating guide was read only as an excerpt (flag U17). Other property taxes (VAT, deed tax, land appreciation tax) were not verified.",
         pros="Handled by the bank against a fixed document list. Large amounts possible in one remittance.",
         cons="Title transfer and tax payment have to be finished first, and the tax certificate caps what can be sent.",
         tax="20% Chinese individual income tax on the gain (sale price less original cost and reasonable expenses).",
         src=["S24", "S20", "S18"], flags=["U17", "U03", "U04"]),
    dict(id="L05", kind="Lawful, SAFE approval", model="fx_wire",
         name="Inheritance transfer (继承财产转移)",
         fits="You are a foreign citizen who inherited assets in China from someone whose household registration was there.",
         cap="One application for the whole estate at the decedent's last hukou; after approval the bank may remit once or in instalments.",
         published="Exchange spread plus the same wire fee.",
         blank="Whether any Chinese tax is charged on the inheritance itself (flag U08). Approval time.",
         pros="A dedicated legal route for a large sum, paid to your own account abroad.",
         cons="Needs SAFE approval, notarised inheritance and property papers, and a tax certificate.",
         tax="A tax certificate is required. Chinese inheritance tax was not confirmed either way in this release (flag U08). In the US a foreign bequest is not income but is reported on Form 3520 above USD 100,000.",
         src=["S08", "S09", "S10", "S31"], flags=["U08", "U03", "U04"]),
    dict(id="L06", kind="Lawful, SAFE approval", model="fx_wire",
         name="Emigrant property transfer (移民财产转移)",
         fits="You lived in mainland China, emigrated, and the assets were yours before you obtained emigrant status.",
         cap="One application for everything you will move, approved at your former hukou. Since 2014 the bank may remit once or in instalments.",
         published="Exchange spread plus the same wire fee.",
         blank="Approval time; the notarisation the local SAFE office will ask for.",
         pros="A dedicated route for a former resident's savings and property proceeds. No annual quota.",
         cons="Needs proof the Chinese hukou was cancelled, an embassy-certified settlement certificate, property papers and tax certificates. Not available to someone who never had mainland residency.",
         tax="Tax certificates from where the property or income arose. Unpaid Chinese tax on that income has to be settled first.",
         src=["S08", "S09", "S10"], flags=["U03", "U04"]),
    dict(id="L07", kind="Lawful, card holders only", model="quota",
         name="Annual USD 50,000 convenience amount with a PRC Foreign Permanent Resident ID card",
         fits="You hold the PRC Foreign Permanent Resident ID Card, not just a visa or a residence permit.",
         cap="USD 50,000 equivalent per person per calendar year on the card alone. Above it, the documented-income route (L01) applies.",
         published="Exchange spread once, plus one wire fee per yearly tranche.",
         blank="Intermediary and receiving-bank fees. Rates in future years.",
         pros="No source or tax documents inside the yearly amount.",
         cons="Slow for a large balance: USD 400,000 takes eight calendar years. A US passport alone does not qualify.",
         tax="None identified for the conversion.",
         src=["S05", "S06"], flags=["U15", "U03", "U04"]),
    dict(id="L08", kind="Lawful, costs not published", model="blank",
         name="Send the RMB itself abroad as cross-border RMB, convert outside the mainland",
         fits="The RMB is lawful current-account income and your bank offers personal cross-border RMB remittance.",
         cap="Current-account income only. The document list was not verified in this release.",
         published="",
         blank="Both legs: the outbound RMB wire fee and the offshore conversion rate.",
         pros="No onshore conversion step, so the onshore spread is avoided.",
         cons="You still convert at the receiving bank at a rate and fee that no official page publishes. Not every bank offers it to individuals.",
         tax="Same underlying-income position as L01.",
         src=["S15"], flags=["U09"]),
    dict(id="L09", kind="Lawful, company owners only", model="dividend",
         name="Dividend from your own Chinese company",
         fits="The money sits in a company you own, not in a personal account.",
         cap="Limited to genuine distributable profit. Above USD 50,000 the bank checks the profit-distribution resolution and the tax filing form.",
         published="20% Chinese tax on the dividend, then the exchange spread and the wire fee on what is left.",
         blank="The treaty rate (flag U06); intermediary and receiving-bank fees.",
         pros="The proper route for business profit. No annual quota.",
         cons="A fifth of the money goes in Chinese tax before it moves. Needs company accounts and a resolution. Not a route for personal savings.",
         tax="20% individual income tax on dividends. A lower treaty rate was not verified here. Chinese tax paid may be creditable in the US.",
         src=["S20", "S09", "S18"], flags=["U06", "U03", "U04"]),
    dict(id="L10", kind="Lawful, small amounts", model="atm",
         name="Overseas ATM withdrawals on a mainland UnionPay debit card",
         fits="You hold a UnionPay debit card on the RMB account and travel outside the mainland.",
         cap="RMB 10,000 per card per day and RMB 100,000 per person per calendar year. Breaching the year cap suspends overseas withdrawals for that year and the next.",
         published="Bank of China's card fee: RMB 12 + 1% per withdrawal, capped at RMB 112.",
         blank="The UnionPay conversion rate and any fee the foreign ATM operator charges.",
         pros="No documents and no application.",
         cons="About 27 calendar years for USD 400,000 at the annual cap, before the exchange rate.",
         tax="None identified. Cash brought into the US above USD 10,000 must be reported.",
         src=["S13", "S03", "S33"], flags=["U13", "U15"]),
    dict(id="L11", kind="Lawful, delivery only", model="cash",
         name="Carry foreign-currency banknotes out in person",
         fits="You can lawfully buy the foreign currency first (L01, L02 or L07) and you want it as cash.",
         cap="USD 5,000 per trip without a permit; USD 5,000-10,000 with a bank permit; above USD 10,000 in principle not allowed.",
         published="The cash selling rate (the same 6.6911 on this board), which carries the spread.",
         blank="The branch's fee for withdrawing foreign banknotes, and the travel cost.",
         pros="No wire and no receiving-bank fee.",
         cons="A delivery method, not a way round the document rules. The cash still has to be bought lawfully, and USD 400,000 is 80 trips.",
         tax="None identified. Entering the US with more than USD 10,000 requires FinCEN Form 105.",
         src=["S14", "S33", "S01"], flags=["U14"]),
    dict(id="P01", kind="Prohibited", model="none",
         name="Using relatives' or friends' USD 50,000 amounts (splitting, 蚂蚁搬家)",
         fits="", cap="", published="", blank="",
         pros="",
         cons="SAFE treats it as evading the convenience amount. Everyone involved goes on the watch list for the year of listing and the next two; the organiser can be fined as 逃汇.",
         tax="Fine up to 30% of the amount, 30%-100% in serious cases; criminal liability possible.",
         src=["S12", "S07", "S16"], flags=[]),
    dict(id="P02", kind="Prohibited", model="none",
         name="Private swaps, money changers, apps, underground banks",
         fits="", cap="", published="", blank="",
         pros="",
         cons="Only banks and licensed exchange outlets may convert currency. 'You pay me RMB in China, I pay you dollars abroad' is private FX trading.",
         tax="Warning, confiscation of gains, fine up to 30%; 30%-100% in serious cases; criminal liability possible.",
         src=["S15", "S16"], flags=[]),
    dict(id="P03", kind="Prohibited", model="none",
         name="False documents or a false purpose to buy foreign currency",
         fits="", cap="", published="", blank="",
         pros="",
         cons="Buying FX with false or invalid documents is 非法套汇. Unreal documents alone can draw a fine of up to RMB 50,000 for an individual.",
         tax="The bank must reverse the conversion; fine up to 30%, 30%-100% in serious cases.",
         src=["S16"], flags=[]),
    dict(id="P04", kind="Prohibited", model="none",
         name="Buying cryptocurrency or stablecoins with RMB to move value out",
         fits="", cap="", published="", blank="",
         pros="",
         cons="Exchanging RMB for virtual currency inside the mainland is an illegal financial activity under the notice in force since 2026-02-06.",
         tax="The activity is banned outright; there is no legal protection for the money.",
         src=["S22"], flags=[]),
    dict(id="P05", kind="Prohibited", model="none",
         name="Carrying more than USD 10,000 out of China, or entering the US without declaring it",
         fits="", cap="", published="", blank="",
         pros="",
         cons="Above USD 10,000 needs a SAFE permit that is in principle not granted. In the US, an undeclared amount over USD 10,000 can be seized.",
         tax="China: warning and a fine up to 20% of the amount. US: seizure and forfeiture, civil or criminal penalties.",
         src=["S14", "S16", "S33"], flags=[]),
    dict(id="P06", kind="Prohibited", model="none",
         name="Borrowing or lending bank cards to get round the overseas ATM cap",
         fits="", cap="", published="", blank="",
         pros="",
         cons="Expressly forbidden by 汇发〔2017〕29号.",
         tax="Punished under the Foreign Exchange Regulation.",
         src=["S13", "S16"], flags=[]),
]
CHANNEL = {c["id"]: c for c in CHANNELS}

# ------------------------------------------------------------------------- ladder
def channel_row(model, amount):
    """Return the published-cost row for one channel model at one USD amount."""
    ask = RATE["ask"]
    out = dict(spread=None, fee=None, tax=None, total=None, units=None, calendar_years=None,
               rmb=None, staged=None)
    if model in ("fx_wire", "property"):
        s, w = spread_usd(amount), wire_usd(amount)
        out.update(spread=s, fee=w, total=s + w, units=1, calendar_years=1, rmb=amount * ask + wire_cny(amount))
    elif model == "wire_only":
        w = wire_usd(amount)
        out.update(fee=w, total=w, units=1, calendar_years=1)
    elif model == "quota":
        cap = RATE["quota_usd"]
        full = int((amount / cap).to_integral_value(rounding="ROUND_FLOOR"))
        rem = amount - cap * full
        fee = wire_usd(cap) * full + (wire_usd(rem) if rem > 0 else D(0))
        n = full + (1 if rem > 0 else 0)
        s = spread_usd(amount)
        out.update(spread=s, fee=fee, total=s + fee, units=n, calendar_years=n)
    elif model == "atm":
        cny = amount * ask
        day = RATE["atm_day_cap_cny"]
        full = int((cny / day).to_integral_value(rounding="ROUND_FLOOR"))
        rem = cny - day * full
        per = min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * day)
        fee = per * full + (min(RATE["atm_max"], RATE["atm_fixed"] + RATE["atm_pct"] * rem) if rem > 0 else D(0))
        f = fee / ask
        out.update(fee=f, total=f, units=full + (1 if rem > 0 else 0),
                   calendar_years=ceil_int(cny / RATE["atm_year_cap_cny"]))
    elif model == "cash":
        s = amount * (RATE["cash_ask"] - mid()) / RATE["cash_ask"]
        out.update(spread=s, total=s, units=ceil_int(amount / RATE["cash_no_permit_usd"]))
    elif model == "dividend":
        tax = amount * RATE["iit_flat"]
        net = amount - tax
        s, w = spread_usd(net), wire_usd(net)
        out.update(tax=tax, spread=s, fee=w, total=tax + s + w, units=1, calendar_years=1)
    if model == "property":
        # M4 what-if: the original 2004 staging (half, then half a year later, then the rest).
        a = wire_usd(amount / 2)
        b = wire_usd(amount / 4)
        c = wire_usd(amount / 4)
        out["staged"] = spread_usd(amount) + a + b + c
    return out


def ladder():
    rows = []
    for c in CHANNELS:
        if c["model"] == "none":
            continue
        for a in AMOUNTS:
            rows.append((c["id"], a, channel_row(c["model"], a)))
    return rows


def fx_gain(amount, year):
    return amount - amount * RATE["ask"] / RATE["irs_avg"][year]


# ----------------------------------------------------------------------- questions
# id, gate, priority, question, why it decides the answer, what we know (sourced),
# what we do not know, how to discover it, source ids
QUESTIONS = [
    ("Q01", "Gate 1 — identity of the account", "high",
     "Is the Chinese bank account recorded under your foreign passport or under a Chinese ID?",
     "This one fact picks which half of the rule book applies. A passport account is a 境外个人 account; a Chinese-ID account is a 境内个人 account, and the two have different quota and document rules.",
     "The PBOC Measures classify by the ID document produced when the account was opened (Art. 37). The State Council Regulation, Art. 52, separately calls a foreigner who has lived in China for one continuous year a 境内个人. The two definitions do not line up.",
     "Which definition the bank actually applied to this account.",
     "Ask the branch in writing for the account subject category (账户主体类别) and keep the reply. Free of charge: 95566 or any branch counter.",
     ["S17", "S16"]),
    ("Q02", "Gate 1 — identity of the account", "medium",
     "How long have you lived in China in the current or last tax year; are you a Chinese tax resident?",
     "Residence decides whether China taxes your worldwide income or only China-source income, and whether you are a 居民个人 for the 3%-45% scale.",
     "Individual Income Tax Law Art. 1: resident if domiciled in China or present 183 days in a tax year; residents pay on worldwide income, non-residents on China-source income.",
     "Your actual day count and domicile position.",
     "Count days from entry stamps and your residence permit; confirm with the local tax office (12366).",
     ["S20"]),
    ("Q03", "Gate 2 — what the money is", "high",
     "What is the money, line by line: salary, business profit, a home sale, rent, a gift, an inheritance, or money you brought in from abroad?",
     "The bank's document list, the Chinese tax treatment and the available route all hang off this, not off the amount.",
     "Art. 59 requires source-of-funds material including tax evidence for income earned in China; Art. 65 needs only ID for FX already in the account; the 2004 announcement covers only pre-departure property and inheritances.",
     "The composition of your balance.",
     "Sort the bank statements by counterparty for the last 3-5 years and label every deposit. This is the single most useful document you can produce for the bank.",
     ["S04", "S07", "S08"]),
    ("Q04", "Gate 2 — what the money is", "high",
     "Has Chinese individual income tax already been paid or withheld on the money that is in the account?",
     "If it has, the bank's tax evidence is a formality. If it has not, the tax is owed whether or not the money ever leaves China, and no channel removes it.",
     "Art. 3: 3%-45% on wages and service income, 20% flat on dividends, interest, rent, property gains and incidental income. Savings-deposit interest accrued from 2008-10-09 is exempt.",
     "Whether the payer withheld, and whether you have the certificates.",
     "Pull a 完税证明 (tax payment certificate) for the last five years from the local tax office or the 个人所得税 app. It shows what was withheld, by whom, and when.",
     ["S20", "S21"]),
    ("Q05", "Gate 2 — what the money is", "high",
     "Is any part of the balance a gift, or money whose origin you cannot document?",
     "No lawful route was found for RMB received as a gift inside China by a passport holder, or for RMB with no traceable origin. This is the one case with no verified channel.",
     "Art. 59 requires source material. SAFE's answers describe income and property, not gifts. The Regulation lets the bank refuse a transaction whose authenticity it doubts (Art. 68 of the 2020 guidelines).",
     "Whether a gift is involved and, if so, the donor's own documents.",
     "Ask the branch in writing before converting anything. In parallel, the person who gave the money may be able to remit it themselves under one of the documented routes.",
     ["S04", "S07"]),
    ("Q06", "Gate 3 — what the bank quoted", "high",
     "What exactly did the bank say would be charged: a tax, a fee, a spread, or a refusal to convert? Which office said it, and in writing?",
     "The brief says 'a considerable amount of taxes'. No official source read for this release imposes a tax on converting or wiring. If the number is a spread or a fee, it is negotiable and much smaller than a tax. If it is unpaid income tax, it is not a conversion penalty at all.",
     "State Council Regulation Art. 5: no restriction on current international payments and transfers. No tax on the conversion itself was found in any source read.",
     "The actual words used, the rate, the amount, and who said them.",
     "Ask for the quote in writing with the tariff item or legal basis named. If a tax is asserted, ask for the assessment document (完税凭证 / 税务事项通知书).",
     ["S16", "S04", "S18"]),
    ("Q07", "Gate 3 — what the bank quoted", "medium",
     "Does the branch actually operate the route you qualify for, and at what rate and fee?",
     "All cost figures here are Bank of China's published board and its standard personal tariff. The tariff itself allows agreed, promotional and local variations.",
     "S02 note 1: 另有协议约定、价格优惠、地方性收费差异的，按照协议或当地公示的内容收取相关费用.",
     "This branch's executable rate, its fee, and whether it will run a large personal remittance at all.",
     "Get a dated written quote for the whole amount, including the correspondent and receiving bank. Compare at least two banks.",
     ["S01", "S02"]),
    ("Q08", "Gate 4 — the US side", "high",
     "When and at what rate did you acquire the RMB? Do you have the records?",
     "The U.S. currency gain depends entirely on your cost basis in the RMB. On USD 400,000 the spread between a 2024 and a 2025 acquisition is hundreds of dollars of gain and, at the top rate, hundreds of dollars of tax.",
     "§988(c)(1)(C): disposing of non-functional currency is a §988 transaction. IRS publishes yearly average rates (2024: 7.189, 2025: 7.129 CNY/USD).",
     "Your basis and acquisition dates.",
     "Reconstruct from bank statements and payslips by year, and use the IRS yearly average for each year, consistently.",
     ["S25", "S26"]),
    ("Q09", "Gate 4 — the US side", "medium",
     "Is moving this balance a 'personal transaction' for §988(e) purposes, and is any gain in the realistic range below USD 200?",
     "§988(e) relief only applies up to USD 200 of gain. Above that the whole gain is ordinary income, so for any balance of the size described here the relief does not apply.",
     "§988(e)(2) text: the exclusion does not apply if the gain would exceed $200.",
     "Your marginal rate this year, which sets the tax on the gain.",
     "Run the figure with your tax preparer before you convert, not after.",
     ["S25"]),
    ("Q10", "Gate 4 — the US side", "high",
     "Have you filed FBARs and Form 8938 for every year the account existed?",
     "A missed report is a separate exposure from any tax and is larger than every bank fee in this release combined: USD 16,536 non-willful per report, or the greater of USD 165,353 or 50% of the balance if willful.",
     "FBAR threshold USD 10,000 aggregate at any time in the calendar year; Form 8938 thresholds USD 50,000/75,000 for an unmarried filer living in the US, with a USD 60,000 penalty ceiling.",
     "Whether the account was ever reported, and for which years.",
     "Check your filed returns and the BSA E-Filing system. If anything is missing, get advice before you move the money: the move does not create the obligation, but it makes the account visible.",
     ["S27", "S28", "S29", "S30"]),
    ("Q11", "Gate 5 — the route", "high",
     "Were you ever a mainland resident with a Chinese hukou that has since been cancelled?",
     "If yes, the emigrant property transfer (L06) is the only route with no annual amount ceiling and no need to fit the money into a current-income category. If no, it is unavailable and the answer changes completely.",
     "The 2004 announcement covers 移民 (emigrants) and 继承人 (heirs) only; approval is at the former hukou.",
     "Your hukou history and whether you hold the cancellation certificate (户籍注销证明).",
     "The police station that held your hukou issues the cancellation certificate; the embassy or consulate certifies your settlement abroad.",
     ["S08", "S09", "S10"]),
    ("Q12", "Gate 5 — the route", "medium",
     "Do you hold the PRC Foreign Permanent Resident ID Card (not a visa, not a residence permit)?",
     "It is the only way a foreign passport holder gets the USD 50,000 a year convenience amount. Without it, every conversion needs documents.",
     "Art. 59 second sentence: 持有外国人永久居留身份证的境外个人适用购汇年度便利化额度.",
     "Card status.",
     "Check the card; the number is printed on it.",
     ["S05", "S06"]),
    ("Q13", "Gate 5 — the route", "medium",
     "Is any part of the balance already in a foreign-currency account inside China?",
     "Foreign currency already in the account can be wired out on ID alone with no conversion and no spread: the cheapest lawful route in this release.",
     "Art. 65(1): 外汇账户内外汇汇出，凭本人有效身份证件办理.",
     "The currency split of the balance.",
     "Look at the account statement: USD and CNY sub-accounts are listed separately.",
     ["S07"]),
    ("Q14", "Gate 6 — timing and size", "medium",
     "Do you need the whole amount at once, or can it move over several years?",
     "The quota route takes eight calendar years for USD 400,000 and the ATM route about 27. Everything else is limited by approval time, not by annual amounts.",
     "USD 50,000 a year per person on the PR-ID card; RMB 100,000 a year per person on overseas ATM withdrawals.",
     "Your liquidity needs.",
     "Decide the cash need first; it eliminates routes faster than the cost tables do.",
     ["S06", "S13"]),
    ("Q15", "Gate 6 — timing and size", "low",
     "Will the money move in one wire or several, and who pays the correspondent bank fee (OUR/SHA/BEN)?",
     "The wire tariff is capped at RMB 260 plus RMB 150, so splitting adds fees almost linearly, while the exchange spread is proportional and unchanged. The charge code decides who absorbs the correspondent fee.",
     "BOC tariff: 0.1%, min RMB 50, max RMB 260, plus RMB 150 cable.",
     "The receiving bank's incoming-wire fee and its charge code policy.",
     "Ask your US bank for its incoming international wire fee schedule in writing.",
     ["S02"]),
    ("Q16", "Gate 7 — the rest of the world", "medium",
     "Is the balance below the reporting thresholds, so that none of the U.S. reporting penalties can bite?",
     "Below USD 10,000 aggregate the FBAR question disappears; below USD 50,000/75,000 so does Form 8938 for a single filer in the US. Above them, the reporting is not optional.",
     "Thresholds as above.",
     "Peak balance in the account in each calendar year.",
     "Pull the year-end and peak statements for every year the account was open.",
     ["S27", "S29"]),
    ("Q17", "Gate 7 — the rest of the world", "low",
     "Are you a US citizen by birth or naturalisation, and do you hold any other passport?",
     "US citizenship drives the worldwide reporting. A second passport may open a receiving account in another currency, which changes the conversion leg but not the US tax on the gain.",
     "§988 applies to a US person wherever the conversion happens.",
     "Your citizenship set.",
     "No discovery needed; this is a fact you hold.",
     ["S25"]),
]


# --------------------------------------------------------------------- repo review
# id, severity, where, finding, evidence, what to do
REPO_REVIEW = [
    ("R01", "high", "data/s775_sources.csv, data/c5bf_source_recheck.csv, data/m5f19_sources.csv",
     "The 'fetched_utc' timestamps in these registers cannot be real fetch times: several are later than the commit that added the file to main, and several are in the future relative to this review. A timestamp is a claim like any other and none of these can be reproduced.",
     "`git log --format=%cI -- data/s775_sources.csv` gives the commit time; compare with the fetched_utc column. Recorded in research/m5f19-repo-review.md (flag R01 of that layer) and repeated here as unresolved.",
     "Treat every 'fetched live' label from those three layers as unverified. This release dates its own readings and does not reuse theirs."),
    ("R02", "high", "root: 89 HTML files, 4 dashboard pages, 7 docs pages, 15 CI workflows",
     "Fourteen earlier layers each published their own cost table from their own rate snapshot, with four different headline figures for the same $10,000 conversion: $53.38, $53.42, $53.47 and $901.30 at $400,000 against $899.01. A reader landing on an archived page cannot tell which reading is current.",
     "data/m5f19_reconciliation.csv records the four figures and reproduces each; this release recomputes them again in data/r11_reconciliation.csv at today's board.",
     "This release publishes one current figure and a scenario table showing what each older figure would be at today's rate. The archive pages are labelled."),
    ("R03", "medium", "dashboard/index.html (e347 layer), card 3",
     "The card said the currency gain is 'taxed at your ordinary rate unless the personal-transaction rule applies'. Read properly, §988(e)(2) gives relief only where the gain is USD 200 or less, so for any balance in this brief the rule cannot apply. The old wording invited the reader to hope otherwise.",
     "26 U.S.C. §988(e)(2)-(3), read in full on 2026-11-11 (S25).",
     "Corrected in this release: the $200 limit is stated explicitly on the home, tax and costs pages."),
    ("R04", "medium", "All layers",
     "Every rate-based figure was computed from a single intraday Board of China snapshot, but none of the published pages measured how much of the headline is the snapshot rather than the channel. The movement between two readings of the same board on successive days (see the scenario rows below) is of the same order as some of the differences the layers argued about.",
     "BOC board page read on 2026-11-10 17:39:58 (ask 6.69) and again on 2026-11-11 10:25:02 (ask 6.69): the same page moved by about 0.006 CNY per USD, which on $10,000 is about 5 cents of cost. S01.",
     "This release adds a scenario table (A/B/C) holding the channel fixed and moving only the clock."),
    ("R05", "medium", "dashboard/index.html 'Cost at a glance' vs the methods page",
     "The glance table presents the ATM and cash routes' costs next to the bank routes' costs without distinguishing that only the bank's own card fee is priced for ATM and only the spread for cash. A reader can compare figures that measure different things.",
     "dashboard/costs.html prints the caveat; the home page table does not carry it in the mobile layout.",
     "This release marks every partial figure as partial and prints the missing components beside it."),
    ("R06", "low", "data/e347_sources.csv",
     "Source S08 is labelled 'excerpt' in the data and 'direct' in the prose of the same layer: it was in fact read in full (Arts. 54-67 are present in the extract). The mismatch is a labelling error, not a false claim.",
     "The 2020 guidelines PDF, read in full on 2026-11-11 (S07).",
     "Reclassified as direct in this release's register."),
    ("R07", "low", "data/e347_sources.csv S03 and the e347 costs engine",
     "The ATM fee notice now in force took effect on 2026-11-11 (the date of this review). Costs computed before that date used the pre-change tariff. The published per-withdrawal numbers are identical before and after for UnionPay, so no figure changes; only the basis of the citation does.",
     "S03 read on 2026-11-11: 原收费标准 and 调整后收费标准 both give 银联 每笔（12元+1%）最高112元/笔.",
     "Cited as in force from today; figures unchanged."),
    ("R08", "medium", "README.md, index.html, dashboard/archive.html",
     "The site lists 30+ entry points (c3x, a513, s775, s436, d646, m5f19, c5bf, e347, completion-audit, cross-session-review, review, routes, tax, methods, penalties, guide, legacy-index...). Several declare themselves canonical in their own text. Nothing states which one a reader should start with, and two of them ('legacy-index.html' and 'verify-2026.html') say they are superseded on a page a reader only reaches after choosing them.",
     "grep of the H1 on each root page; dashboard/archive.html lists 60+ files.",
     "This release makes the landing page the single current answer and labels the rest as archive in one sentence at the top."),
    ("R09", "low", "COORDINATION.md (1,298 lines)",
     "The board grew to 1,298 lines of append-only session logs. Twelve sessions recorded that they could not use the per-task branch convention because the harness binds one branch per session; the board's own rule therefore could not be followed as written, and each session logged the same exception separately.",
     "COORDINATION.md sections for sessions 7e08715a, c703e38c, 5f1925df, 775c9619, 8c26329a.",
     "Recorded once here rather than again per session. The rule should say 'one branch per session, named by the harness'."),
    ("R10", "low", "scripts/ (40 files) and .github/workflows/ (15 files)",
     "There are 15 CI workflows and 15 local validators, several of which re-implement the same arithmetic independently. That is good for catching errors, but four of them only assert internal consistency against their own data module, so they cannot detect a wrong input that is consistently applied. Passing 15 validators is not evidence that a figure is true.",
     "scripts/verify_*.py: verify_completion.py restates a rate; verify_c3x_site.py imports its own inputs; neither fetches anything.",
     "This release separates the two questions: the validators prove internal consistency, and the source register (data/r11_sources.csv) with a dated quote proves provenance. Both are printed on the sources page."),
    ("R11", "low", "repository root",
     "There is still no LICENSE file and no statement of who may reuse the content, although the repository is public and is published as a web site. This was flagged in REPO_AUDIT.md (A3) and remains the owner's decision.",
     "`ls LICENSE` returns nothing; REPO_AUDIT.md A3.",
     "Left open. Not a blocker; recorded so it is not lost."),
    ("R12", "low", "docs/ (the separate /docs site)",
     "A second, older site is published under /docs with its own data model and its own 27 sources, reachable from the README. It is no longer the landing page but is still served, and it carries the same channel list with older figures.",
     "docs/index.html meta and docs/assets/data.js.",
     "Listed as archive in this release's navigation note; not edited."),
]

# -------------------------------------------------------------------------- flags
# id, severity, item, why, what would settle it, source ids
FLAGS = [
    ("U01", "high", "Where the money came from",
     "Not stated in the brief. It decides the route, the document list and whether Chinese tax is still owed. No route is recommended as a fact about your case.",
     "Bank statements and the documents behind each large deposit (question Q03).", ["S04"]),
    ("U02", "high", "The 'considerable amount of taxes'",
     "The brief names no tax, rate, amount or office. No official source read for this release puts a tax on converting or wiring. Until the quote is produced, the premise cannot be tested.",
     "The written quote with its legal basis (question Q06).", ["S16"]),
    ("U03", "medium", "Your bank's actual rate and fees",
     "All bank costs use Bank of China's public board and public personal tariff. Other banks, branch differences, negotiated rates and promotions are not captured, and the tariff itself allows local variation.",
     "A dated written quote from the branch (question Q07).", ["S01", "S02"]),
    ("U04", "medium", "Intermediary and receiving-bank fees",
     "No official page publishes a single figure. Left blank in every total in this release and never estimated.",
     "Your US bank's incoming-wire schedule and the charge code (question Q15).", ["S02"]),
    ("U05", "medium", "Whether §988(e) relief could apply",
     "The relief applies only to gain of USD 200 or less, and a transaction is not personal to the extent its expenses fall under §162 or §212. For any balance in this brief the $200 limit decides it, but the characterisation of the holding is a legal judgement this release does not make.",
     "A US tax professional, with acquisition dates and rates (questions Q08, Q09).", ["S25"]),
    ("U06", "medium", "US-China treaty rate on dividends",
     "The treaty was not read in this release, so the dividend route is priced at the statutory 20% only.",
     "The treaty article on dividends, on irs.gov.", ["S20"]),
    ("U07", "high", "Money received as a gift, or with no documents",
     "No official rule was found that lets a foreign passport holder convert RMB received as a gift inside China, or RMB whose origin cannot be documented. No route is listed for this case.",
     "The branch's written answer, and the donor's own options (question Q05).", ["S04"]),
    ("U08", "medium", "Chinese tax on an inheritance",
     "The Individual Income Tax Law lists nine taxable categories and inheritance is not one of them, but no official statement saying 'inheritance is not taxed' was found. Left unconfirmed.",
     "The tax certificate issued for the estate, which route L05 needs anyway.", ["S20", "S08"]),
    ("U09", "medium", "Cost of the cross-border RMB route (L08)",
     "Neither the outbound RMB wire fee nor the offshore conversion rate was confirmed from an official page. Every cost cell for L08 is blank.",
     "Quotes from the sending and receiving banks.", ["S15"]),
    ("U10", "medium", "Two definitions of 'domestic individual'",
     "The State Council Regulation (Art. 52) counts a foreigner who has lived in China for one continuous year as a 境内个人; the PBOC Measures classify by ID document and say the bank decides from the ID used at account opening. They do not agree.",
     "The bank's written confirmation of the account category (question Q01).", ["S16", "S17"]),
    ("U11", "low", "Two sources read as excerpts",
     "S24 (only section 8) was read as an excerpt rather than in full. Every other source in this register was fetched and read in full on 2026-11-11.",
     "Reading the full operating guide.", ["S24"]),
    ("U12", "low", "Exact willful FBAR penalty for a given balance",
     "The statute gives the greater of the adjusted $100,000 (now $165,353) or 50% of the balance. Which alternative binds depends on the balance: below USD 330,706 the fixed figure binds, above it the percentage does. This release states both and does not pick one for you.",
     "The IRS mitigation guidelines and the balance at the time of each violation.", ["S28", "S30"]),
    ("U13", "medium", "ATM route: conversion rate and the ATM operator's fee",
     "Only Bank of China's own card fee is priced. The UnionPay conversion rate and any fee charged by the foreign ATM are blank.",
     "UnionPay's rate for the day and the ATM's on-screen fee.", ["S03"]),
    ("U14", "medium", "Cash route: banknote withdrawal fee and travel cost",
     "Priced at the board's cash selling rate only. Any fee for withdrawing foreign banknotes, and the travel cost of each trip, are blank.",
     "The branch counter tariff and an actual trip cost.", ["S01"]),
    ("U15", "low", "One rate snapshot",
     "Every figure uses the Bank of China board published 2026/11/11 10:25:02 Beijing. Rates move during the day; the scenario table shows how much the headline moves with the clock.",
     "Re-run scripts/r11_engine.py and rebuild after a new board reading.", ["S01"]),
    ("U16", "low", "Approval timelines",
     "No official service standard was found for how long SAFE approval of an emigrant or inheritance transfer takes, or how long a large documented-income remittance takes at the counter.",
     "SAFE's published service standards and a real branch timeline.", ["S09"]),
    ("U17", "low", "Home-sale route: 2025 operating guide read in part",
     "The document list comes from section 8 of SAFE Anhui's operating guide to 汇发〔2025〕43号, read as an excerpt. Other property taxes (VAT, deed tax, land appreciation tax) were not verified.",
     "Reading the whole guide and asking the local tax office.", ["S24"]),
    ("U18", "medium", "Money-transfer companies and apps",
     "No official page was read that confirms any named transfer company can send a personal RMB balance out of mainland China to the US, or at what price. None is listed as a route. SAFE's notice says only banks and licensed exchange institutions may convert currency.",
     "The provider's licence and its written terms for outbound personal transfers.", ["S15"]),
    ("U19", "low", "Routes listed by earlier layers not re-read here",
     "Eleven channels are priced in this release. Earlier layers catalogued up to 24, including insurance products, securities channels and QDII. Those were not re-read and carry no cost and no verdict here.",
     "Read each official page cited in the archive before relying on it.", ["S15"]),
    ("U20", "low", "No personal facts are known",
     "Nothing in this release is about your actual account: not the balance, the currency mix, the account category, the tax history, the residence history or the filing history. Every figure is a model of a hypothetical case at a published rate.",
     "Answers to questions Q01-Q17.", ["S04"]),
]


# ------------------------------------------------------------------------- writers
def _write(name, header, rows):
    path = DATA / name
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    return path


def write_all():
    DATA.mkdir(exist_ok=True)
    _write("r11_sources.csv",
           ["id", "issuer", "title", "url", "read_on", "how_read", "quote", "what_it_establishes"],
           [(s[0], s[1], s[2], s[3], VERIFIED_ON, s[4], s[5], s[6]) for s in SOURCES])
    _write("r11_facts.csv",
           ["id", "group", "statement", "value", "used_in", "source_ids", "flags", "source_urls"],
           [(f[0], f[1], f[2], f[3], f[4], "|".join(f[5]), "|".join(f[6]),
             " ".join(SRC[i][3] for i in f[5])) for f in FACTS])
    _write("r11_channels.csv",
           ["id", "kind", "model", "name", "fits", "cap", "published_cost", "blank", "pros", "cons",
            "tax", "cost_10k", "cost_100k", "cost_400k", "source_ids", "source_urls", "flags"],
           [(c["id"], c["kind"], c["model"], c["name"], c["fits"], c["cap"], c["published"], c["blank"],
             c["pros"], c["cons"], c["tax"],
             "" if channel_row(c["model"], D(10000))["total"] is None else str(q(channel_row(c["model"], D(10000))["total"])),
             "" if channel_row(c["model"], D(100000))["total"] is None else str(q(channel_row(c["model"], D(100000))["total"])),
             "" if channel_row(c["model"], D(400000))["total"] is None else str(q(channel_row(c["model"], D(400000))["total"])),
             "|".join(c["src"]), " ".join(SRC[i][3] for i in c["src"]), "|".join(c["flags"]))
            for c in CHANNELS])
    _write("r11_ladder.csv",
           ["channel_id", "amount_usd", "spread_usd", "fee_usd", "tax_usd", "published_cost_usd",
            "published_cost_pct", "units", "calendar_years", "rmb_debited", "staged_cost_usd", "flags"],
           [(cid, int(a),
             "" if r["spread"] is None else str(q(r["spread"])),
             "" if r["fee"] is None else str(q(r["fee"])),
             "" if r["tax"] is None else str(q(r["tax"])),
             "" if r["total"] is None else str(q(r["total"])),
             "" if r["total"] is None else str(q(r["total"] / a * 100, D("0.0001"))),
             "" if r["units"] is None else r["units"],
             "" if r["calendar_years"] is None else r["calendar_years"],
             "" if r["rmb"] is None else str(q(r["rmb"])),
             "" if r["staged"] is None else str(q(r["staged"])),
             "|".join(CHANNEL[cid]["flags"]))
            for cid, a, r in ladder()])
    _write("r11_fx_gain.csv",
           ["amount_usd", "ask", "gain_if_acquired_2021_usd", "gain_if_acquired_2022_usd",
            "gain_if_acquired_2023_usd", "gain_if_acquired_2024_usd", "gain_if_acquired_2025_usd",
            "tax_at_24pct_on_2024_gain", "tax_at_37pct_on_2024_gain"],
           [(int(a), str(RATE["ask"]), *(str(q(fx_gain(a, y))) for y in ("2021", "2022", "2023", "2024", "2025")),
             str(q(fx_gain(a, "2024") * D("0.24"))), str(q(fx_gain(a, "2024") * D("0.37"))))
            for a in AMOUNTS])
    _write("r11_questions.csv",
           ["id", "gate", "priority", "question", "why_it_decides", "known", "unknown", "how_to_discover",
            "source_ids", "source_urls"],
           [(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], "|".join(x[8]),
             " ".join(SRC[i][3] for i in x[8])) for x in QUESTIONS])
    _write("r11_repo_review.csv",
           ["id", "severity", "where", "finding", "evidence", "action"],
           [list(r) for r in REPO_REVIEW])
    _write("r11_flags.csv",
           ["id", "severity", "item", "why", "what_would_settle_it", "source_ids", "source_urls"],
           [(f[0], f[1], f[2], f[3], f[4], "|".join(f[5]), " ".join(SRC[i][3] for i in f[5]))
            for f in FLAGS])
    # reconciliation of every published headline figure against today's board
    # Each scenario is recomputed with its OWN ask, including the wire leg, because the
    # tariff is charged in RMB and converted at the rate of the day.
    def wire_at(amount_usd, ask):
        raw = amount_usd * ask * RATE["wire_rate"]
        return (min(RATE["wire_max"], max(RATE["wire_min"], raw)) + RATE["cable"]) / ask

    recon = []
    for tag, when, bid, ask, current, note in SCENARIOS:
        old_mid = (bid + ask) / 2
        old_spread = D(10000) * (ask - old_mid) / ask
        old_wire = wire_at(D(10000), ask)
        old_400_spread = D(400000) * (ask - old_mid) / ask
        old_400_wire = wire_at(D(400000), ask)
        recon.append([
            tag, when, str(bid), str(ask),
            str(q(old_spread)), str(q(old_spread + old_wire)),
            str(q(old_400_spread)), str(q(old_400_spread + old_400_wire)),
            "yes" if current else "no", note])
    _write("r11_reconciliation.csv",
           ["scenario", "board_time", "bid", "ask", "spread_10k_usd", "cost_10k_usd",
            "spread_400k_usd", "cost_400k_usd", "is_current", "note"], recon)
    return [p.name for p in sorted(DATA.glob("r11_*.csv"))]


if __name__ == "__main__":
    names = write_all()
    print("wrote", len(names), "files:", ", ".join(names))
    r = channel_row("fx_wire", D(10000))
    print("spot check L01 $10,000 =", usd(r["total"]), "| $400,000 =", usd(channel_row("fx_wire", D(400000))["total"]))
    print("ask", RATE["ask"], "bid", RATE["bid"], "mid", q(mid(), D("0.0001")))
