#!/usr/bin/env python3
"""Build the B9B3 verified research repository and mobile-first dashboard.

    python3 scripts/build_b9b3_site.py            write every claimed file
    python3 scripts/build_b9b3_site.py --check    fail if any generated file is stale

All figures come from the official pages in SOURCES.  Unknown commercial fees,
tax amounts, eligibility facts and all-in totals stay blank and link to the
Flagged for Review page.  The independent verifier does not import this module.
"""
from __future__ import annotations

import argparse
import csv
import html
import io
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import b9b3_engine as eng  # noqa: E402

SNAPSHOT = "2026-11-11 10:40:02"
DATE = "2026-11-11"
esc = html.escape

SOURCES = [
    {"source_id": "BS01", "issuer": "Bank of China", "title": "BOC foreign-exchange board (USD row)", "url": "https://www.boc.cn/sourcedb/whpj/enindex_1619.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Pub Time 2026/11/11 10:40:02; USD per 100: Buying 666.31, Cash Buying 666.31, Selling 669.12, Cash Selling 669.12, Middle 671.91.", "supports": "Live CNY/USD bid, ask and cash selling rates; board timestamp."},
    {"source_id": "BS02", "issuer": "Bank of China", "title": "Personal e-banking cross-border wire tariff", "url": "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "跨境汇款（电汇）: 1‰ of the remittance amount, minimum RMB 50/tx, maximum RMB 260/tx; cable fee RMB 150/tx outside HK/Macao/Taiwan. Note 1 permits agreed, promotional and local differences.", "supports": "Published wire fee, cap, floor and cable charge."},
    {"source_id": "BS03", "issuer": "Bank of China", "title": "2026-11-11 ATM fee revision", "url": "https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Effective 2026-11-11: overseas UnionPay ATM withdrawal RMB 12 + 1%, maximum RMB 112/tx; Mastercard/VISA 2.5%, minimum USD 3/tx, maximum USD 40/tx.", "supports": "Published BOC ATM card fees; not an FX conversion rate."},
    {"source_id": "BS04", "issuer": "Bank of China", "title": "2014 personal full-amount (全额到账) surcharge notice", "url": "https://www.boc.cn/pbservice/bi2/201412/t20141231_4404048.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "From 2015-04-01, in addition to wire fee and cable: USD full-amount service USD 15/tx when the receiving bank holds an account at BOC New York, otherwise USD 25/tx; applies where an intermediary bank is required.", "supports": "Historical OUR surcharge; current 2026 applicability is flagged, not assumed."},
    {"source_id": "BS05", "issuer": "Bank of China", "title": "Outbound foreign-currency remittance service", "url": "https://www.boc.cn/pbservice/pb4/200806/t20080626_760.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Wire form needs currency/amount, payee name/address, account number, bank name and SWIFT code or address; intermediary banks may deduct a transfer fee from the principal.", "supports": "Execution details and the official reason receiving/intermediary fees are left blank."},
    {"source_id": "BS06", "issuer": "Ministry of Commerce / SAFE", "title": "经常项目外汇业务指引（2020年版）, 汇发〔2020〕14号 (full text)", "url": "https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html", "read_on": DATE, "how_read": "direct: chunks 0-2", "verbatim_or_extract": "Arts. 54-57, 59-67, 86 and 89 read: USD 50,000 convenience amount; Art. 59 foreign individual documented RMB income; Art. 60 24-month reconversion; Art. 62 watch-list; Art. 64 outward wire; Art. 65 FX-account wire; Art. 67 own-account/relative transfers; Arts. 86/89 cash limits.", "supports": "Primary PRC current-account FX rules."},
    {"source_id": "BS07", "issuer": "SAFE Tianjin", "title": "2026 personal FX Q&A No. 08 — Art. 59", "url": "https://www.safe.gov.cn/tianjin/2026/0713/3088.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇.", "supports": "Documented-income route for a foreign passport holder."},
    {"source_id": "BS08", "issuer": "SAFE Tianjin", "title": "2024 current-account FX case Q&A No. 09", "url": "https://www.safe.gov.cn/tianjin/2024/0621/2529.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Art. 59; 持有外国人永久居留身份证的境外个人适用购汇年度便利化额度.", "supports": "Only PRC Foreign Permanent Resident ID holders get the purchase convenience amount."},
    {"source_id": "BS09", "issuer": "SAFE Ningxia", "title": "2022 FX policy Q&A No. 08", "url": "https://www.safe.gov.cn/ningxia/2022/0929/1997.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "每人每年等值5万美元; 年度便利化额度不是…限额，只是超过等值5万美元的购汇或结汇不能仅凭本人有效身份证件办理.", "supports": "USD 50,000 is a documentation threshold, not a hard cap."},
    {"source_id": "BS10", "issuer": "SAFE Tianjin", "title": "2024 personal FX Q&A No. 03 — Art. 64", "url": "https://www.safe.gov.cn/tianjin/2024/0229/2402.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "境内个人外汇账户内外汇汇出境外当日累计等值5万美元以下（含）的，凭本人有效身份证件办理；超过上述金额的，凭本人有效身份证件、有交易额的相关材料办理.", "supports": "Domestic-individual outward-wire documentation threshold."},
    {"source_id": "BS11", "issuer": "SAFE Tianjin", "title": "2026 personal FX Q&A No. 10 — Art. 60", "url": "https://www.safe.gov.cn/tianjin/2026/0917/3134.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "原兑换未用完的人民币兑回外汇，凭本人有效身份证件和原兑换水单办理；原兑换水单的兑回有效期为自兑换日起24个月；当日累计不超过等值500美元（含）…可凭本人有效身份证件办理.", "supports": "24-month exchange-slip reconversion and small ID-only amounts."},
    {"source_id": "BS12", "issuer": "SAFE Tianjin", "title": "2025 personal FX Q&A No. 08 — watch-list", "url": "https://www.safe.gov.cn/tianjin/2025/0613/2811.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "借用他人便利化额度及其他方式规避便利化额度及真实性管理的个人，列入“关注名单”…关注期限为列入当年及之后连续2年.", "supports": "Anti-smurfing watch-list current year plus two calendar years."},
    {"source_id": "BS13", "issuer": "SAFE Tianjin", "title": "2021 service-trade FX Q&A No. 04", "url": "https://www.safe.gov.cn/tianjin/2021/1102/1777.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "境外个人从境内取得的服务贸易、收益和经常转移项下人民币收入购汇汇出，可凭身份证件和有交易额的相关证明材料（含税务凭证）办理.", "supports": "Tax voucher forms for service income and current transfers."},
    {"source_id": "BS14", "issuer": "People's Bank of China", "title": "PBOC Announcement [2004] No. 16 — individual property transfer", "url": "http://m.safe.gov.cn/safe/2004/1116/5461.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Defines 移民转移 and 继承转移; Arts. 8-9 list inheritance/property/tax documents; Art. 11 remits directly to the applicant's own overseas account.", "supports": "Emigrant and inheritance approval routes."},
    {"source_id": "BS15", "issuer": "SAFE", "title": "汇发〔2014〕2号 capital-account reforms", "url": "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "§6: approval at former/decedent hukou; bank may remit once or in instalments within the approved amount; RMB 500,000 HQ reporting and staged-remittance requirement removed; property notarisation removed. §5: profit distribution above USD 50,000 needs resolution and tax filing form.", "supports": "Approval routes and dividend documentation."},
    {"source_id": "BS16", "issuer": "SAFE Tianjin", "title": "2026 personal property transfer Q&A No. 07", "url": "https://www.safe.gov.cn/tianjin/2026/0319/3018.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "汇发〔2024〕12号 6.4: 移民财产转移由移民原户籍所在地外汇局负责审批；继承财产转移由被继承人生前户籍所在地外汇局负责审批.", "supports": "Which SAFE office approves each transfer."},
    {"source_id": "BS17", "issuer": "SAFE Anhui", "title": "2025 operating guide to 汇发〔2025〕43号, §8 (PDF)", "url": "https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf", "read_on": DATE, "how_read": "direct: PDF §8 read in full", "verbatim_or_extract": "境外个人转让境内商品房所得资金购汇汇出: passport, registered transfer contract and title-transfer proof, tax voucher; tax filing form waived at ≤USD 50,000; remittance capped at transfer price minus taxes/fees.", "supports": "Property-sale document list and tax voucher."},
    {"source_id": "BS18", "issuer": "State Taxation Administration / SAFE", "title": "Announcement 2013 No. 40 (as amended 2021 No. 19)", "url": "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Art. 1: single outbound payment above USD 50,000 for salary, dividends, real-estate transfer income etc. requires tax record-filing (税务备案). Art. 4: foreign individuals follow personal FX rules.", "supports": "USD 50,000 tax-recordal threshold."},
    {"source_id": "BS19", "issuer": "State Council", "title": "Foreign Exchange Regulation, Decree No. 532", "url": "https://www.safe.gov.cn/safe/2008/0806/5321.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Art. 5 no restriction on current-account payments/transfers; Art. 12 genuine lawful basis; Arts. 39/40/45 fines up to 30%, 30%-100% if serious; Art. 42 border cash up to 20%; Art. 48 untrue documents up to RMB 50,000 for individuals; Art. 52(2) one-year residence definition.", "supports": "Core lawful basis and PRC penalties."},
    {"source_id": "BS20", "issuer": "People's Bank of China", "title": "个人外汇管理办法, PBOC Decree [2006] No. 3", "url": "http://m.safe.gov.cn/safe/2006/1225/5319.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Art. 13 foreign individual lawful current-account RMB income may be converted/remitted at a bank; Art. 14 unused inbound FX may be returned; Art. 28 bank sets account category from the ID used to open the account.", "supports": "Account classification and no-conversion FX return."},
    {"source_id": "BS21", "issuer": "SAFE Hubei", "title": "汇发〔2017〕29号 overseas bank-card cash withdrawals", "url": "https://www.safe.gov.cn/hubei/2019/0305/851.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "RMB 10,000 per card per day; RMB 100,000 per person per calendar year; exceeding the yearly cap suspends overseas cash withdrawals for the current and following year.", "supports": "ATM/card withdrawal caps."},
    {"source_id": "BS22", "issuer": "SAFE Hebei", "title": "Carrying foreign-currency cash out of China", "url": "http://www.safe.gov.cn/hebei/2019/0521/1366.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "≤USD 5,000 customs release; USD 5,000-10,000 bank carrying permit; above USD 10,000 SAFE permit in principle not granted.", "supports": "Cash-border limits."},
    {"source_id": "BS23", "issuer": "SAFE Guangdong", "title": "Warning on online/private FX exchange", "url": "https://www.safe.gov.cn/guangdong/2020/0304/1668.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Only qualified banks, licensed exchange institutions and authorised agencies may handle personal FX; apps, WeChat swaps, FX brokers and underground banks are illegal; splitting and false documents are prohibited.", "supports": "Prohibited private channels."},
    {"source_id": "BS24", "issuer": "SAFE Hebei", "title": "朱某 individual split-purchase penalty case", "url": "https://www.safe.gov.cn/hebei/2017/0414/774.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "52 people used to purchase/remit USD 2.5625 million; treated as 逃汇 under Decree 532 Art. 39 and fined.", "supports": "Real enforcement against quota splitting."},
    {"source_id": "BS25", "issuer": "PBOC and seven agencies", "title": "银发〔2026〕42号 virtual-currency risk notice", "url": "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Virtual-currency business is illegal financial activity; fiat/virtual-currency exchange, unapproved RMB stablecoins and RWA tokenisation are strictly prohibited; repeals 银发〔2021〕237号.", "supports": "No lawful CNY→USDT→USD route."},
    {"source_id": "BS26", "issuer": "PBOC Beijing", "title": "Cross-border RMB policy benefits (2018 article, live mirror)", "url": "https://beijing.pbc.gov.cn/beijing/132005/2025111421421910358/index.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "银发〔2018〕3号 supports individuals' other current-account RMB cross-border settlement; a foreign employee in Beijing remitted RMB salary directly to South Africa instead of first buying FX, saving the conversion charge.", "supports": "Live replacement for the inherited dead PBOC Beijing URL; personal cross-border RMB example."},
    {"source_id": "BS27", "issuer": "People's Bank of China", "title": "2018 monetary-policy chronicle: 银发〔2018〕3号", "url": "https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/b28b61e9f5234e388bbcb942ab9a0797/index.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "1月5日: PBOC issued 银发〔2018〕3号; any cross-border transaction that may lawfully be settled in FX may be settled in RMB.", "supports": "Official existence and scope of the 2018 RMB policy."},
    {"source_id": "BS28", "issuer": "National People's Congress / STA", "title": "PRC Individual Income Tax Law (2018)", "url": "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Art. 3: comprehensive income 3%-45%; business income 5%-35%; interest, dividends, rent, property transfer and incidental income 20%. Art. 6(5): property gain = proceeds less original value and reasonable expenses.", "supports": "PRC tax rates on underlying income, not on conversion."},
    {"source_id": "BS29", "issuer": "Ministry of Finance / STA", "title": "财税〔2008〕132号 savings-interest exemption", "url": "https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "自2008年10月9日起，对储蓄存款利息所得暂免征收个人所得税.", "supports": "RMB savings-deposit interest IIT exemption."},
    {"source_id": "BS30", "issuer": "NPC / Guangdong Tax", "title": "PRC Tax Collection Administration Law (2015 text)", "url": "https://guangdong.chinatax.gov.cn/gdsw/zjfg/2015-04/24/content_7585cb6a374c47cb92fafcdabc17e8de.shtml", "read_on": DATE, "how_read": "direct: chunks 0-1", "verbatim_or_extract": "Art. 32: daily late-payment surcharge 万分之五 (0.05%). Art. 63: tax evasion penalty 50%-500% of underpaid tax; criminal liability if a crime.", "supports": "PRC tax late-payment and evasion penalties."},
    {"source_id": "BS31", "issuer": "State Taxation Administration", "title": "STA Announcement 2019 No. 35 — treaty benefits", "url": "https://tianjin.chinatax.gov.cn/11200000000/0300/030004/03000418/20191024101530609.shtml", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "非居民纳税人享受协定待遇采取“自行判断、申报享受、相关资料留存备查”; Art. 7 requires tax-residency certificate, contracts/payment vouchers and beneficial-owner evidence where relevant.", "supports": "Treaty-rate self-assessment and retained documents."},
    {"source_id": "BS32", "issuer": "IRS / U.S. Treasury", "title": "U.S.–China Income Tax Convention (1984, PDF)", "url": "https://www.irs.gov/pub/irs-trty/china.pdf", "read_on": DATE, "how_read": "direct: chunks 0-6", "verbatim_or_extract": "Art. 9(2) dividends may be taxed in the source state up to 10% of gross if the recipient is the beneficial owner; Art. 10(2) interest 10%; Art. 22(2) U.S. credit for Chinese income tax; Protocol 1 ¶2 saving clause: the United States may tax its citizens.", "supports": "Treaty rates, foreign tax credit and saving clause."},
    {"source_id": "BS33", "issuer": "U.S. Government Publishing Office", "title": "26 U.S.C. § 988 (2023 ed.)", "url": "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", "read_on": DATE, "how_read": "direct: chunks 0-2", "verbatim_or_extract": "(a)(1)(A) ordinary FX gain/loss; (c)(1)(C) disposition of nonfunctional currency including bank deposits; (e)(2) no gain on a personal transaction unless it exceeds $200; (e)(3) §162/§212 expenses exclude personal treatment.", "supports": "U.S. currency-gain character and personal-transaction exclusion."},
    {"source_id": "BS34", "issuer": "IRS", "title": "Yearly average currency exchange rates", "url": "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "CNY per USD: 2025 7.129; 2024 7.189; 2023 7.075; 2022 6.730; 2021 6.452. 'The Internal Revenue Service has no official exchange rate.'", "supports": "Historical yearly rates used only as labelled scenarios, not as an official spot rate."},
    {"source_id": "BS35", "issuer": "IRS", "title": "Comparison of Form 8938 and FBAR requirements", "url": "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Form 8938 thresholds: single in U.S. $50,000 year-end / $75,000 any time; single abroad $200,000 / $300,000; joint filers double. Penalty up to $10,000, plus $10,000 per 30 days after notice, maximum $60,000.", "supports": "FATCA Form 8938 thresholds and penalty."},
    {"source_id": "BS36", "issuer": "FinCEN", "title": "Report of Foreign Bank and Financial Accounts (FBAR)", "url": "https://www.fincen.gov/report-foreign-bank-and-financial-accounts", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "A U.S. person must file an FBAR if aggregate foreign account value exceeds $10,000 at any time during the calendar year; due April 15 with automatic extension to October 15.", "supports": "FBAR filing threshold and due date."},
    {"source_id": "BS37", "issuer": "U.S. Government Publishing Office", "title": "31 U.S.C. § 5321 (2023 ed.)", "url": "https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm", "read_on": DATE, "how_read": "direct: chunks 0-1", "verbatim_or_extract": "(a)(5)(B)(i) non-willful FBAR penalty ≤$10,000; (a)(5)(C)(i) willful penalty greater of $100,000 or 50% of the account balance; reasonable-cause exception for non-willful violations.", "supports": "Statutory FBAR penalty ceiling, now independently verified."},
    {"source_id": "BS38", "issuer": "eCFR / FinCEN", "title": "31 CFR 1010.821 penalty adjustment table", "url": "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "read_on": DATE, "how_read": "direct: chunks 0-2", "verbatim_or_extract": "Penalties assessed on/after 2025-01-17: non-willful FBAR $16,536; willful FBAR $165,353.", "supports": "Current inflation-adjusted FBAR penalty amounts."},
    {"source_id": "BS39", "issuer": "U.S. Government Publishing Office", "title": "26 U.S.C. § 6039F (2021 ed.)", "url": "https://www.govinfo.gov/content/pkg/USCODE-2021-title26/html/USCODE-2021-title26-subtitleF-chap61-subchapA-partIII-subpartA-sec6039F.htm", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "(c)(1)(B): 5% of the foreign gift for each month the failure continues, not to exceed 25% in aggregate; reasonable-cause exception in (c)(2).", "supports": "Form 3520 late/incomplete filing penalty."},
    {"source_id": "BS40", "issuer": "IRS", "title": "Gifts from foreign persons", "url": "https://www.irs.gov/businesses/gifts-from-foreign-person", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Form 3520 Part IV reports gifts/bequests from a nonresident alien or foreign estate exceeding $100,000 in the taxable year; foreign corporation/partnership gifts use the §6039F inflation-adjusted threshold.", "supports": "Foreign gift/bequest reporting threshold."},
    {"source_id": "BS41", "issuer": "IRS", "title": "Foreign Tax Credit", "url": "https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "The foreign tax credit offsets foreign income tax paid or accrued, subject to limitations; Form 1116 is generally used by individuals.", "supports": "Crediting PRC income tax against U.S. tax on the same income."},
    {"source_id": "BS42", "issuer": "IRS", "title": "Streamlined Filing Compliance Procedures", "url": "https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures", "read_on": DATE, "how_read": "direct: chunks 0-1", "verbatim_or_extract": "Procedures for non-willful past noncompliance; links to U.S.-resident and foreign-resident instructions, delinquent international information return procedures, and IRS Criminal Investigation voluntary disclosure.", "supports": "Choosing a U.S. correction path."},
    {"source_id": "BS43", "issuer": "IRS", "title": "Streamlined Domestic Offshore Procedures (SDOP)", "url": "https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-in-the-united-states", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "3 years of amended returns, 6 years of delinquent FBARs, and a Title 26 miscellaneous offshore penalty equal to 5% of the highest aggregate foreign asset balance/value.", "supports": "SDOP 5% penalty and filing scope."},
    {"source_id": "BS44", "issuer": "IRS", "title": "Streamlined Foreign Offshore Procedures (SFOP)", "url": "https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-outside-the-united-states", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "3 years of delinquent/amended returns and 6 years of delinquent FBARs; compliant eligible taxpayers are not subject to failure-to-file, failure-to-pay, accuracy, information-return or FBAR penalties.", "supports": "SFOP no-penalty framework and non-residency test."},
    {"source_id": "BS45", "issuer": "IRS", "title": "Delinquent international information return procedures", "url": "https://www.irs.gov/individuals/international-taxpayers/delinquent-international-information-return-submission-procedures", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Taxpayers not under examination/investigation and not contacted by IRS should file delinquent international information returns through normal procedures, attaching a reasonable-cause statement where asserted.", "supports": "Delinquent Form 8938/3520 etc. correction path."},
    {"source_id": "BS46", "issuer": "IRS", "title": "IRM 4.26.16 — FBAR and delinquent FBAR procedures", "url": "https://www.irs.gov/irm/part4/irm_04-026-016", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "IRM 4.26.16.3.11: delinquent FBARs use the current electronic report and year-specific instructions; a penalty is not asserted where the failure was non-willful, due to reasonable cause and properly reported on the delinquent FBAR.", "supports": "Live IRS delinquent-FBAR procedure replacing the tested 404 URL."},
    {"source_id": "BS47", "issuer": "IRS", "title": "U.S. citizens and resident aliens abroad", "url": "https://www.irs.gov/individuals/international-taxpayers/u-s-citizens-and-resident-aliens-abroad", "read_on": "2026-11-11", "how_read": "direct", "verbatim_or_extract": "U.S. citizens and resident aliens are taxed on worldwide income; foreign accounts above the reporting threshold require FinCEN Form 114 even if they generate no taxable income; Form 3520 reports foreign gifts/bequests over $100,000.", "supports": "Worldwide-income, FBAR and Form 3520 overview."},
    {"source_id": "BS48", "issuer": "IRS", "title": "Foreign earned income exclusion", "url": "https://www.irs.gov/individuals/international-taxpayers/foreign-earned-income-exclusion", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "FEIE applies to foreign earned income from personal services; the page lists $107,600 (2020), $108,700 (2021), $112,000 (2022) and $120,000 (2023). Pension, annuity and investment/currency gains are not foreign earned income.", "supports": "FEIE does not shelter existing savings or currency gain; 2026 figure is flagged."},
    {"source_id": "BS49", "issuer": "U.S. Customs and Border Protection", "title": "Money and monetary instruments", "url": "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "Currency or monetary instruments exceeding $10,000 entering/leaving the U.S. must be reported on FinCEN Form 105; the threshold applies collectively to a family or group.", "supports": "U.S. cash declaration rule."},
    {"source_id": "BS50", "issuer": "SAFE", "title": "汇发〔2017〕15号 bank-card overseas transaction reporting", "url": "http://m.safe.gov.cn/safe/2017/0602/7572.html", "read_on": DATE, "how_read": "direct", "verbatim_or_extract": "From 2017-09-01 domestic issuers report all overseas cash withdrawals and single purchases above RMB 1,000; the policy does not change personal FX rules and adds no personal filing cost.", "supports": "Card transactions are reported by the bank, not by the individual."},
]

FLAGS = [
    {"flag_id": "B9B3-F01", "severity": "high", "item": "Source of the CNY balance", "why": "The brief does not say whether the money is salary, property proceeds, inheritance, a gift, prior FX or something else. The source selects the lawful route and any underlying PRC tax.", "what_would_settle_it": "Bank statements and the documents behind every large deposit; a written bank statement of which route it will accept.", "source_ids": "BS06|BS07|BS19", "affected_pages": "questions|methods|costs"},
    {"flag_id": "B9B3-F02", "severity": "high", "item": "Bank account classification", "why": "Decree 532 Art. 52(2) counts a foreigner resident in China for one continuous year as 境内个人; PBOC Decree [2006] No. 3 Art. 28 classifies by the ID used at account opening. The bank's classification of this account is unknown.", "what_would_settle_it": "Written confirmation from the account-holding bank of its 境内个人/境外个人 classification.", "source_ids": "BS19|BS20|BS08", "affected_pages": "questions|methods"},
    {"flag_id": "B9B3-F03", "severity": "medium", "item": "One intraday BOC board snapshot", "why": "All B9B3 figures use the 2026/11/11 10:40:02 board (666.31 / 669.12 / 671.91 per 100 USD). The board moves intraday and the tariff allows local/agreed/promotional differences.", "what_would_settle_it": "A dated written rate and fee quote from the executing branch.", "source_ids": "BS01|BS02", "affected_pages": "dashboard|costs|sources"},
    {"flag_id": "B9B3-F04", "severity": "medium", "item": "OUR / full-amount surcharge", "why": "BOC's 2014 personal notice published USD 15/25 full-amount surcharges, but current 2026 e-banking applicability, routing and the receiving bank's correspondent relationship are not confirmed.", "what_would_settle_it": "The branch's current personal tariff and a written charge-option confirmation for this wire.", "source_ids": "BS04|BS05|BS02", "affected_pages": "costs|penalties|questions"},
    {"flag_id": "B9B3-F05", "severity": "medium", "item": "Intermediary and receiving-bank fees", "why": "BOC's own page says intermediary banks may deduct transfer fees from the principal; no official single figure covers every U.S. receiving bank. These cells are blank, not zero.", "what_would_settle_it": "The U.S. bank's fee schedule and the sending bank's written charge option (OUR/SHA/BEN).", "source_ids": "BS05|BS02|BS04", "affected_pages": "costs|questions"},
    {"flag_id": "B9B3-F06", "severity": "high", "item": "The 'considerable taxes' and underlying PRC tax", "why": "No tax, rate, amount or assessing office was named in the brief. No official page read imposes a tax on the act of converting one's own CNY; PRC tax, if any, attaches to the underlying income or gain.", "what_would_settle_it": "A written tax-office/bank statement naming the tax and rate, plus PRC tax returns and 完税凭证.", "source_ids": "BS19|BS18|BS28|BS07", "affected_pages": "questions|penalties|costs"},
    {"flag_id": "B9B3-F07", "severity": "high", "item": "U.S. §988 basis and personal-transaction status", "why": "§988 treats disposition of nonfunctional currency as ordinary gain/loss, but §988(e) excludes personal transactions up to $200 and excludes §162/§212 expenses. Acquisition dates, USD basis and classification are unknown.", "what_would_settle_it": "A U.S. tax professional's determination using dated acquisition records and the account's use.", "source_ids": "BS33|BS34|BS47", "affected_pages": "questions|penalties|costs"},
    {"flag_id": "B9B3-F08", "severity": "high", "item": "Prior U.S. filing status", "why": "FBAR, Form 8938, Form 3520 and income-tax filing history are not stated. Prior noncompliance can dominate the cost of moving the money.", "what_would_settle_it": "Copies of prior-year returns, FinCEN Form 114 confirmations, Forms 8938/3520 and IRS account transcripts.", "source_ids": "BS35|BS36|BS40|BS47", "affected_pages": "questions|penalties|steps"},
    {"flag_id": "B9B3-F09", "severity": "medium", "item": "Cross-border RMB cost", "why": "PBOC sources confirm a personal current-account RMB remittance example and the 2018 policy, but publish no personal outbound RMB wire fee, offshore CNH conversion rate or receiving-bank fee for this case.", "what_would_settle_it": "Written quotes from the sending bank and the offshore receiving bank for the exact RMB amount.", "source_ids": "BS26|BS27|BS19", "affected_pages": "methods|costs|questions"},
    {"flag_id": "B9B3-F10", "severity": "medium", "item": "ATM exchange rate and ATM-owner fee", "why": "BOC publishes its own card fee, but the UnionPay conversion rate, foreign ATM-owner fee and exact transaction count for a personal itinerary are not officially published here.", "what_would_settle_it": "UnionPay's dated rate, the ATM's on-screen fee disclosure and a written bank simulation.", "source_ids": "BS03|BS21|BS50|BS49", "affected_pages": "methods|costs"},
    {"flag_id": "B9B3-F11", "severity": "medium", "item": "Cash banknote withdrawal fee and travel cost", "why": "The board gives a cash selling rate; no official personal fee for withdrawing foreign banknotes, permit cost or travel cost for these amounts was verified.", "what_would_settle_it": "The branch's counter tariff and written permit/declaration confirmation.", "source_ids": "BS01|BS22|BS49", "affected_pages": "methods|costs"},
    {"flag_id": "B9B3-F12", "severity": "medium", "item": "Approval-route eligibility and wire count", "why": "Emigrant/inheritance/liquidation routes require case-specific approval and may be remitted once or in instalments; the number of wires and timing are not known.", "what_would_settle_it": "The SAFE approval letter and the bank's remittance schedule.", "source_ids": "BS14|BS15|BS16|BS19", "affected_pages": "methods|costs|steps"},
    {"flag_id": "B9B3-F13", "severity": "medium", "item": "Property original cost and other property taxes", "why": "The 20% IIT applies to gain (proceeds less original value and reasonable expenses), not gross proceeds. Original cost, VAT, deed tax and land-appreciation tax were not provided or verified for this case.", "what_would_settle_it": "Purchase contract, tax receipts and a written tax-office computation.", "source_ids": "BS17|BS28|BS18", "affected_pages": "methods|penalties|costs"},
    {"flag_id": "B9B3-F14", "severity": "medium", "item": "Treaty 10% rate eligibility", "why": "The treaty caps source-state dividends/interest/royalties at 10% for a beneficial owner, but STA 2019 No. 35 requires self-assessment, a report form and retained tax-residency/beneficial-owner evidence. Eligibility is not established.", "what_would_settle_it": "A U.S. tax-residency certificate, beneficial-owner evidence and the withholding agent's written treatment.", "source_ids": "BS32|BS31|BS28", "affected_pages": "methods|penalties|questions"},
    {"flag_id": "B9B3-F15", "severity": "medium", "item": "Chinese tax on an inheritance", "why": "The IIT Law lists taxable categories and the inheritance route requires a tax certificate, but no official statement affirmatively saying 'inheritance is not taxed' was read.", "what_would_settle_it": "The tax certificate or written clearance issued for the estate.", "source_ids": "BS14|BS28|BS18", "affected_pages": "methods|penalties"},
    {"flag_id": "B9B3-F16", "severity": "high", "item": "USD 50,000 convenience amount scope", "why": "The convenience amount is not a hard cap, but for FX purchase a U.S. passport alone does not qualify an 境外个人; only PRC Foreign Permanent Resident ID holders get it on ID alone.", "what_would_settle_it": "The bank's written classification and the actual ID held.", "source_ids": "BS08|BS09|BS07|BS12", "affected_pages": "questions|methods|costs"},
    {"flag_id": "B9B3-F17", "severity": "medium", "item": "Original exchange slip", "why": "Art. 60 reconversion requires the original exchange slip within 24 months and only for the unused amount; no slip or unused amount was supplied.", "what_would_settle_it": "The original 兑换水单 and a bank statement showing the unused balance.", "source_ids": "BS11|BS20", "affected_pages": "questions|methods"},
    {"flag_id": "B9B3-F18", "severity": "high", "item": "Gift or undocumented funds", "why": "No official rule read here lets a foreign passport holder convert RMB received as a gift, or RMB whose origin cannot be documented, into USD and remit it. No route is asserted for this case.", "what_would_settle_it": "A written bank decision and, if relevant, the donor's own lawful remittance route; U.S. Form 3520 advice.", "source_ids": "BS06|BS07|BS40", "affected_pages": "questions|methods|costs"},
    {"flag_id": "B9B3-F19", "severity": "low", "item": "2026 FEIE inflation-adjusted amount", "why": "The IRS FEIE page read here lists figures through 2023 only. An inherited layer quotes 2026 $132,900; B9B3 does not reuse that figure.", "what_would_settle_it": "The current IRS 'Figuring the Foreign Earned Income Exclusion' page for the tax year in question.", "source_ids": "BS48", "affected_pages": "penalties|repo-audit"},
    {"flag_id": "B9B3-F20", "severity": "high", "item": "Prohibited routes", "why": "Quota splitting, private/app/underground FX swaps, crypto/stablecoin conversion, false documents and undeclared cash are prohibited by the cited PRC instruments. No execution steps or costs are supplied for them.", "what_would_settle_it": "Use only a qualified bank or licensed exchange institution and obtain written approval for the lawful route.", "source_ids": "BS12|BS19|BS23|BS24|BS25|BS49", "affected_pages": "methods|penalties|costs"},
    {"flag_id": "B9B3-F21", "severity": "low", "item": "Archive grouping note", "why": "scripts/e347_build.py auto-groups new root pages under 'First editorial pages' with an older note. That generator is owned by another session; B9B3 logged an integration request instead of editing it.", "what_would_settle_it": "An additive B9B3 archive group added by the shared-file integrator.", "source_ids": "BS01|BS02", "affected_pages": "repo-audit"},
    {"flag_id": "B9B3-F22", "severity": "low", "item": "Inherited e347 U12 FBAR ceiling", "why": "e347 flag U12 said the 50% willful FBAR ceiling was not read. B9B3 read 31 U.S.C. §5321(a)(5)(C) and eCFR 31 CFR 1010.821 in full; the older flag is historical, not edited.", "what_would_settle_it": "No action; resolved in this edition's Penalties and Sources pages.", "source_ids": "BS37|BS38", "affected_pages": "penalties|repo-audit"},
    {"flag_id": "B9B3-F23", "severity": "low", "item": "Inherited e347 U06 treaty rate", "why": "e347 flag U06 said the treaty text was not read. B9B3 read Articles 9, 10, 22 and Protocol 1 ¶2 from the IRS treaty PDF; treaty-rate eligibility remains separately flagged.", "what_would_settle_it": "No action for the rate; see B9B3-F14 for eligibility.", "source_ids": "BS32|BS31", "affected_pages": "penalties|repo-audit"},
    {"flag_id": "B9B3-F24", "severity": "low", "item": "Inherited e347 U17 property guide", "why": "e347 flag U17 said the 2025 SAFE Anhui guide was excerpt-only. B9B3 read §8 in full from the official PDF; other property taxes remain unverified.", "what_would_settle_it": "No action for §8; see B9B3-F13 for other taxes.", "source_ids": "BS17", "affected_pages": "methods|repo-audit"},
    {"flag_id": "B9B3-F25", "severity": "low", "item": "Board drift across three 2026-11 snapshots", "why": "e347 uses the 2026-11-10 17:39:58 board, b2d4ff40 quotes 2026-11-11 10:25:02, and B9B3 uses 10:40:02. Each is a different intraday observation; sibling layers were not repriced.", "what_would_settle_it": "A single dated board snapshot selected by the final integrator.", "source_ids": "BS01|BS02", "affected_pages": "dashboard|costs|repo-audit"},
    {"flag_id": "B9B3-F26", "severity": "medium", "item": "Cross-border RMB scope tension", "why": "m5f19 M15 says cross-border RMB needs a counterparty and genuine transaction; PBOC Beijing describes a foreign employee's personal RMB salary remittance. The instruments may describe different scopes; no personal fee was published.", "what_would_settle_it": "Written confirmation from the remitting bank that it offers personal outbound RMB for this exact income.", "source_ids": "BS26|BS27|BS19", "affected_pages": "methods|repo-audit"},
    {"flag_id": "B9B3-F27", "severity": "medium", "item": "Dead PBOC Beijing URL in inherited e347 cost rows", "why": "data/e347_costs.csv L08 rows cite http://beijing.pbc.gov.cn/beijing/132026/3660457/index.html, which returned HTTP 404 on 2026-11-11. B9B3 uses the live PBOC Beijing mirror instead.", "what_would_settle_it": "The e347 owner replacing the dead URL, or a note pointing to the live mirror.", "source_ids": "BS26|BS27", "affected_pages": "sources|repo-audit"},
    {"flag_id": "B9B3-F28", "severity": "low", "item": "Inherited e347 U09 source URL", "why": "data/e347_flags.csv U09 also points to the dead PBOC Beijing URL. The live PBOC Beijing article and PBOC 2018 chronicle were read here; the cost remains blank.", "what_would_settle_it": "An e347-owner URL correction; do not fill L08 costs without an official personal tariff.", "source_ids": "BS26|BS27", "affected_pages": "repo-audit"},
    {"flag_id": "B9B3-F29", "severity": "low", "item": "IRS delinquent-FBAR URL 404", "why": "https://www.irs.gov/individuals/international-taxpayers/delinquent-fbar-submission-procedures returned HTTP 404. B9B3 cites the live IRM 4.26.16 and the delinquent international information return procedures instead.", "what_would_settle_it": "No action; use the live IRS pages linked on the Sources page.", "source_ids": "BS46|BS45|BS42", "affected_pages": "sources|repo-audit"},
]

QUESTIONS = [
    {"question_id": "B9B3-Q01", "stage": "1. The money", "priority": "P0", "question": "Where did the CNY balance come from?", "status": "Open", "known_information": "Official rules select the route by source: documented current-account income, property sale, inheritance, emigrant property, prior FX, dividend, service payment or gift/no documents.", "missing_information": "The source of this specific balance.", "answer_needed": "Which lawful route, if any, fits this account?", "how_to_discover": "Collect bank statements and the document behind each large deposit; ask the bank in writing which route it will accept.", "source_ids": "BS06|BS07|BS19", "flag_ids": "B9B3-F01"},
    {"question_id": "B9B3-Q02", "stage": "1. The money", "priority": "P0", "question": "Which FX category did the bank assign to this account?", "status": "Open", "known_information": "Decree 532 Art. 52(2) and PBOC Decree [2006] No. 3 Art. 28 define 境内个人/境外个人 differently.", "missing_information": "The account-holding bank's classification.", "answer_needed": "Do the domestic-individual convenience rules apply, or the foreign-individual documented-income rules?", "how_to_discover": "Request written confirmation of the account's 境内个人/境外个人 classification and the ID used at opening.", "source_ids": "BS19|BS20|BS08", "flag_ids": "B9B3-F02"},
    {"question_id": "B9B3-Q03", "stage": "1. The money", "priority": "P0", "question": "What are the 'considerable taxes' referred to in the brief?", "status": "Open", "known_information": "No tax, rate, amount or office is named. No official page read imposes a tax on converting one's own CNY; PRC IIT attaches to underlying income/gain.", "missing_information": "The tax being quoted, its rate and assessing office.", "answer_needed": "Is there any PRC tax due before conversion, and on what income?", "how_to_discover": "Ask the bank/tax office for a written statement naming the tax and legal basis; obtain 完税凭证.", "source_ids": "BS19|BS18|BS28|BS07", "flag_ids": "B9B3-F06"},
    {"question_id": "B9B3-Q04", "stage": "1. The money", "priority": "P0", "question": "When and at what CNY/USD rate was the balance acquired?", "status": "Open", "known_information": "26 U.S.C. §988 treats disposition of nonfunctional currency as ordinary gain/loss; IRS yearly averages are labelled scenarios and 'IRS has no official exchange rate'.", "missing_information": "Acquisition dates and USD basis.", "answer_needed": "Is there a taxable U.S. currency gain, and how much?", "how_to_discover": "Reconstruct dated deposits and conversions; ask a U.S. tax professional to apply §988 and §988(e).", "source_ids": "BS33|BS34|BS47", "flag_ids": "B9B3-F07"},
    {"question_id": "B9B3-Q05", "stage": "1. The money", "priority": "P1", "question": "Is any part of the balance already foreign currency?", "status": "Open", "known_information": "A foreign-currency account can be wired out; no conversion means no bid/ask spread.", "missing_information": "Currency composition of the account.", "answer_needed": "Can the cheapest wire-only route be used for part of the balance?", "how_to_discover": "Obtain a currency-by-currency account statement from the bank.", "source_ids": "BS05|BS20|BS06", "flag_ids": "B9B3-F01|B9B3-F05"},
    {"question_id": "B9B3-Q06", "stage": "1. The money", "priority": "P1", "question": "Is there an original exchange slip less than 24 months old?", "status": "Partly answered", "known_information": "Art. 60 permits reconverting unused RMB with the original slip within 24 months; small ID-only amounts are ≤USD 500/day (≤USD 1,000/day airside).", "missing_information": "Whether this account has such a slip and unused amount.", "answer_needed": "Can B04 or B05 be used?", "how_to_discover": "Locate the original 兑换水单 and compare its date/unused amount with the bank statement.", "source_ids": "BS11|BS20", "flag_ids": "B9B3-F17"},
    {"question_id": "B9B3-Q07", "stage": "1. The money", "priority": "P1", "question": "Is the money a gift, bequest or undocumented funds?", "status": "Open", "known_information": "No official route for a foreign passport holder to convert undocumented/gift RMB was found; U.S. Form 3520 reports foreign gifts/bequests >USD 100,000.", "missing_information": "Donor, gift documents and bank's willingness.", "answer_needed": "Is there any lawful PRC conversion route at all?", "how_to_discover": "Ask the bank in writing; ask the donor about their own lawful remittance route; obtain U.S. Form 3520 advice.", "source_ids": "BS06|BS07|BS40", "flag_ids": "B9B3-F18"},
    {"question_id": "B9B3-Q08", "stage": "2. PRC rules", "priority": "P0", "question": "Does conversion itself create a PRC tax?", "status": "Answered", "known_information": "No official page read imposes a tax on the act of conversion or wire; Decree 532 Art. 5 does not restrict genuine current-account transfers. The bank requires evidence that tax on underlying income was handled.", "missing_information": "None identified from the official pages read.", "answer_needed": "Treat spread and bank fees as conversion cost, not a conversion tax.", "how_to_discover": "Not needed for this question; see Q03 for any underlying tax.", "source_ids": "BS19|BS06|BS07|BS02", "flag_ids": "B9B3-F06"},
    {"question_id": "B9B3-Q09", "stage": "2. PRC rules", "priority": "P0", "question": "What does the USD 50,000 annual convenience amount actually do?", "status": "Answered", "known_information": "It is a documentation threshold, not a hard cap; for FX purchase by an 境外个人, only PRC Foreign Permanent Resident ID holders get it on ID alone.", "missing_information": "None identified from the official pages read.", "answer_needed": "Do not assume a U.S. passport alone gives the purchase quota; documented transactions can exceed it.", "how_to_discover": "Not needed; see Q02 for the bank's classification.", "source_ids": "BS08|BS09|BS07|BS12", "flag_ids": "B9B3-F16"},
    {"question_id": "B9B3-Q10", "stage": "2. PRC rules", "priority": "P1", "question": "Is tax record-filing required before the wire?", "status": "Partly answered", "known_information": "STA/SAFE 2013 No. 40 requires tax filing for single outbound payments above USD 50,000 for salary, dividends, real-estate transfer income etc.; the property guide waives the form at ≤USD 50,000.", "missing_information": "The payment category and whether the recordal already exists.", "answer_needed": "Which tax form must be presented to the bank?", "how_to_discover": "Ask the bank and local tax office for the exact 税务备案表 or 完税/免税证明 required for this payment.", "source_ids": "BS18|BS17|BS13", "flag_ids": "B9B3-F06|B9B3-F13"},
    {"question_id": "B9B3-Q11", "stage": "2. PRC rules", "priority": "P1", "question": "Does a property-sale, inheritance or emigrant route apply?", "status": "Partly answered", "known_information": "Separate SAFE/PBOC routes exist for property sale, 继承转移 and 移民转移, each with approval/document list and tax certificate.", "missing_information": "Whether the facts fit any of those routes.", "answer_needed": "Which approval office and document set governs?", "how_to_discover": "Gather title/inheritance/hukou documents; ask the relevant SAFE office for a written eligibility decision.", "source_ids": "BS14|BS15|BS16|BS17", "flag_ids": "B9B3-F12|B9B3-F13|B9B3-F15"},
    {"question_id": "B9B3-Q12", "stage": "2. PRC rules", "priority": "P1", "question": "Which routes are prohibited?", "status": "Answered", "known_information": "Quota splitting, private/app/underground swaps, crypto/stablecoin/RWA conversion, false documents and excess undeclared cash are prohibited by the cited PRC instruments.", "missing_information": "None identified from the official pages read.", "answer_needed": "Exclude those routes from the decision.", "how_to_discover": "Not needed; use qualified banks/licensed institutions only.", "source_ids": "BS12|BS19|BS23|BS24|BS25|BS49", "flag_ids": "B9B3-F20"},
    {"question_id": "B9B3-Q13", "stage": "3. Bank cost", "priority": "P0", "question": "What is the executable rate and tariff for this branch?", "status": "Open", "known_information": "BOC published the 2026/11/11 10:40:02 board (666.31/669.12 per 100 USD) and 1‰ wire fee (RMB 50-260) + RMB 150 cable; local/agreed/promotional differences are allowed.", "missing_information": "A dated written quote from the executing branch.", "answer_needed": "What CNY amount and itemised fees will actually be charged?", "how_to_discover": "Request a written pre-trade quote with rate timestamp, wire fee, cable, OUR option and receiving-bank charges.", "source_ids": "BS01|BS02|BS05", "flag_ids": "B9B3-F03|B9B3-F04"},
    {"question_id": "B9B3-Q14", "stage": "3. Bank cost", "priority": "P1", "question": "What are OUR, intermediary and U.S. receiving fees?", "status": "Open", "known_information": "BOC's 2014 personal notice gives historical USD 15/25 OUR surcharges; BOC's service page says intermediaries may deduct fees from principal. No current all-in figure is official.", "missing_information": "Current charge option and U.S. bank schedule.", "answer_needed": "How much will the U.S. account actually receive?", "how_to_discover": "Get the sending bank's charge-option confirmation and the U.S. bank's incoming-wire/international fee schedule.", "source_ids": "BS04|BS05|BS02", "flag_ids": "B9B3-F04|B9B3-F05"},
    {"question_id": "B9B3-Q15", "stage": "3. Bank cost", "priority": "P1", "question": "Can the whole amount be sent in one wire?", "status": "Partly answered", "known_information": "Art. 65 states no amount threshold for an 境外个人's FX-account wire; Art. 64 requires documents above USD 50,000/day for 境内个人; approval routes may be remitted once or in instalments.", "missing_information": "Bank's approval and chosen route's wire schedule.", "answer_needed": "One wire or multiple wires/years?", "how_to_discover": "Ask the bank for a written remittance schedule after it reviews the documents.", "source_ids": "BS06|BS10|BS15|BS16", "flag_ids": "B9B3-F12|B9B3-F16"},
    {"question_id": "B9B3-Q16", "stage": "3. Bank cost", "priority": "P2", "question": "Is cross-border RMB cheaper?", "status": "Open", "known_information": "PBOC sources confirm a personal RMB salary remittance example and the 2018 policy, but publish no personal fee or offshore conversion rate.", "missing_information": "Sending and receiving bank quotes.", "answer_needed": "Can an all-in RMB→USD cost be computed?", "how_to_discover": "Request written RMB wire and offshore CNH conversion quotes for the exact amount.", "source_ids": "BS26|BS27|BS19", "flag_ids": "B9B3-F09|B9B3-F26"},
    {"question_id": "B9B3-Q17", "stage": "3. Bank cost", "priority": "P2", "question": "Are ATM or cash routes practical?", "status": "Open", "known_information": "ATM/card yearly cap RMB 100,000; cash export ≤USD 5,000 without permit, USD 5,000-10,000 with bank permit; U.S. declaration above USD 10,000.", "missing_information": "Itinerary, card fees, banknote fee, travel cost and time horizon.", "answer_needed": "Can these small-amount routes legally handle the balance?", "how_to_discover": "Ask the bank for its card/banknote tariff and compute the number of days/trips from the official caps.", "source_ids": "BS03|BS21|BS22|BS49", "flag_ids": "B9B3-F10|B9B3-F11"},
    {"question_id": "B9B3-Q18", "stage": "4. U.S. tax/reporting", "priority": "P0", "question": "Were prior FBARs filed?", "status": "Open", "known_information": "FBAR is required if aggregate foreign accounts exceed USD 10,000 at any time; due Apr 15 with automatic extension to Oct 15.", "missing_information": "Prior-year FinCEN Form 114 confirmations.", "answer_needed": "Is a delinquent/streamlined procedure needed before or alongside the transfer?", "how_to_discover": "Retrieve BSA e-filing confirmations and IRS transcripts; consult a U.S. tax professional.", "source_ids": "BS36|BS47|BS46|BS42", "flag_ids": "B9B3-F08"},
    {"question_id": "B9B3-Q19", "stage": "4. U.S. tax/reporting", "priority": "P0", "question": "Were Forms 8938/3520 and worldwide income reported?", "status": "Open", "known_information": "Form 8938 thresholds and penalties, Form 3520 foreign-gift threshold, and worldwide-income taxation are published by IRS.", "missing_information": "Copies of prior returns and information returns.", "answer_needed": "Which delinquent information-return procedure applies?", "how_to_discover": "Collect prior Forms 1040/8938/3520 and follow the IRS delinquent/streamlined pages with a professional.", "source_ids": "BS35|BS40|BS47|BS45|BS39", "flag_ids": "B9B3-F08"},
    {"question_id": "B9B3-Q20", "stage": "4. U.S. tax/reporting", "priority": "P1", "question": "Is any currency gain excluded as a personal transaction?", "status": "Partly answered", "known_information": "§988(e)(2) excludes personal-transaction gain up to USD 200; §988(e)(3) excludes §162/§212 expense transactions from personal treatment.", "missing_information": "Facts establishing the account's use and expense treatment.", "answer_needed": "Does §988 ordinary gain/loss apply?", "how_to_discover": "Have a U.S. tax professional document the account's use, acquisition basis and expense allocation.", "source_ids": "BS33|BS34", "flag_ids": "B9B3-F07"},
    {"question_id": "B9B3-Q21", "stage": "4. U.S. tax/reporting", "priority": "P1", "question": "Can PRC tax be credited in the U.S.?", "status": "Answered", "known_information": "The treaty Art. 22(2) allows a U.S. credit for Chinese income tax, and IRS explains the foreign tax credit/Form 1116, subject to limitations.", "missing_information": "None identified for the rule; the amount depends on Q03/Q04.", "answer_needed": "Claim the credit only for tax actually paid on the same income.", "how_to_discover": "Keep PRC tax certificates and have Form 1116 prepared with the U.S. return.", "source_ids": "BS32|BS41|BS28", "flag_ids": "B9B3-F06"},
    {"question_id": "B9B3-Q22", "stage": "4. U.S. tax/reporting", "priority": "P1", "question": "Which correction procedure fits past non-willful noncompliance?", "status": "Partly answered", "known_information": "SFOP (foreign residency) has no streamlined penalty; SDOP has a 5% miscellaneous offshore penalty; delinquent information-return and delinquent-FBAR procedures are also published.", "missing_information": "Residency, prior filings, willfulness and IRS contact status.", "answer_needed": "SFOP, SDOP, delinquent procedures or voluntary disclosure?", "how_to_discover": "Complete the IRS eligibility checks with a U.S. tax professional before filing.", "source_ids": "BS42|BS43|BS44|BS45|BS46", "flag_ids": "B9B3-F08"},
    {"question_id": "B9B3-Q23", "stage": "4. U.S. tax/reporting", "priority": "P2", "question": "Does the foreign earned income exclusion help?", "status": "Answered", "known_information": "FEIE applies to foreign earned income from personal services; pension, annuity and investment/currency gains are not foreign earned income.", "missing_information": "None identified for the rule.", "answer_needed": "Do not use FEIE to shelter existing savings or currency gain.", "how_to_discover": "Not needed for this question.", "source_ids": "BS48|BS33", "flag_ids": "B9B3-F19"},
    {"question_id": "B9B3-Q24", "stage": "5. Decision", "priority": "P0", "question": "Which method has the lowest lawful all-in cost?", "status": "Open", "known_information": "This edition computes only the published BOC bank benchmark. All-in totals require branch quote, intermediary/receiving fees, PRC tax and U.S. §988 treatment.", "missing_information": "Q01-Q23 answers.", "answer_needed": "A defensible, case-specific least-cost/lawful ranking.", "how_to_discover": "Complete the P0 questions first, then request written quotes for the two eligible routes and compare all-in USD received.", "source_ids": "BS01|BS02|BS05|BS33|BS19", "flag_ids": "B9B3-F01|B9B3-F03|B9B3-F05|B9B3-F06|B9B3-F07"},
    {"question_id": "B9B3-Q25", "stage": "5. Decision", "priority": "P0", "question": "What is the U.S. receiving account and payee identity?", "status": "Open", "known_information": "BOC's wire form requires currency/amount, payee name/address, account number, bank name and SWIFT code or address.", "missing_information": "Verified receiving-bank details.", "answer_needed": "Can the wire be addressed to the correct account without a return/reversal?", "how_to_discover": "Obtain the receiving bank's written wire instructions and confirm the payee name matches the PRC account holder.", "source_ids": "BS05|BS14", "flag_ids": "B9B3-F05"},
    {"question_id": "B9B3-Q26", "stage": "5. Decision", "priority": "P1", "question": "What is the deadline and urgency?", "status": "Open", "known_information": "Quota convenience amounts reset by calendar year; ATM/card cap is per calendar year; tax and reporting due dates are fixed by IRS/FinCEN.", "missing_information": "The user's deadline.", "answer_needed": "Can a multi-year quota/ATM route be considered, or is a documented single-wire route required?", "how_to_discover": "Write down the target date and compare it with the official calendar-year and filing deadlines.", "source_ids": "BS09|BS21|BS36|BS43", "flag_ids": "B9B3-F16|B9B3-F10"},
    {"question_id": "B9B3-Q27", "stage": "5. Decision", "priority": "P1", "question": "Which records must be retained?", "status": "Answered", "known_information": "Bank wire form, rate confirmation, source/tax evidence, approval letters, FBAR/8938/3520 filings and Form 1116 support are all documented requirements or consequences in the cited pages.", "missing_information": "None identified for the record types.", "answer_needed": "Keep a complete audit trail before and after the transfer.", "how_to_discover": "Create a dated folder with bank, tax and U.S. filing documents; retain per each form's instructions.", "source_ids": "BS05|BS18|BS36|BS35|BS41", "flag_ids": "B9B3-F06|B9B3-F08"},
    {"question_id": "B9B3-Q28", "stage": "5. Decision", "priority": "P2", "question": "Which inherited repo figures should be trusted?", "status": "Partly answered", "known_information": "Sibling layers use three different BOC board snapshots; some cite a dead PBOC Beijing URL and older flags. This edition uses its own dated snapshot and flags each discrepancy.", "missing_information": "A final integrator's chosen snapshot.", "answer_needed": "Which layer is the current source of truth?", "how_to_discover": "Compare the dated Sources pages; use the latest quoted board and live URLs, and keep older pages as historical.", "source_ids": "BS01|BS02|BS26|BS37|BS32", "flag_ids": "B9B3-F25|B9B3-F27|B9B3-F22|B9B3-F23"},
    {"question_id": "B9B3-Q29", "stage": "5. Decision", "priority": "P2", "question": "Is a licensed non-bank payment institution available?", "status": "Open", "known_information": "SAFE says personal FX must go through qualified banks, licensed exchange institutions or authorised agencies; no official page read confirms a named provider for this exact outbound personal balance or its price.", "missing_information": "Provider licence and written terms for mainland outbound transfers.", "answer_needed": "Is there a lawful non-bank channel at all?", "how_to_discover": "Ask the provider for its licence and written mainland-outbound personal RMB terms; verify the licence with the regulator.", "source_ids": "BS23|BS19", "flag_ids": "B9B3-F20"},
    {"question_id": "B9B3-Q30", "stage": "5. Decision", "priority": "P2", "question": "Should the 10% treaty rate be used for a dividend?", "status": "Partly answered", "known_information": "Treaty Art. 9(2) caps source-state dividend tax at 10% for a beneficial owner; STA 2019 No. 35 requires self-assessment, report form and retained tax-residency/beneficial-owner documents.", "missing_information": "Whether this balance is a dividend and whether the evidence exists.", "answer_needed": "20% statutory IIT or a valid 10% treaty position?", "how_to_discover": "Obtain the company resolution, tax-residency certificate and written withholding-agent treatment; consult a PRC/U.S. tax professional.", "source_ids": "BS32|BS31|BS28|BS15", "flag_ids": "B9B3-F14"},
]

METHODS = [
    {"method_id": "B01", "method": "Documented current-account income: buy USD and wire", "legal_status": "conditional", "who": "境外个人 / foreign passport holder with lawful PRC current-account RMB income", "when_to_use": "Salary, service fees, current transfers or other lawful income whose source and tax treatment can be documented.", "documents": "Valid ID, amount-bearing source-of-funds documents, tax voucher / 完税凭证 / 免税证明 or 税务备案表; wire form and receiving-bank details.", "limit": "Art. 59 states no amount ceiling; tax record-filing applies to single payments above USD 50,000.", "advantages": "The standard documented route for a foreign individual; whole amount can be handled as one bank wire; no annual quota needed when documents exist.", "drawbacks": "Bank must accept source and tax evidence; branch practice varies; unpaid underlying PRC tax blocks the route.", "conversion_tax_notes": "No conversion tax found; 20%/3%-45% PRC IIT may attach to the underlying income; U.S. §988 and reporting remain separate.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS05|BS06|BS07|BS13|BS18|BS19|BS28", "flag_ids": "B9B3-F01|B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06"},
    {"method_id": "B02", "method": "Domestic-individual documented purchase above the convenience amount", "legal_status": "conditional", "who": "境内个人 (Chinese citizen, or foreigner resident ≥1 year on the Decree 532 reading)", "when_to_use": "The bank classifies the account as 境内个人 and genuine purpose/amount documents exist.", "documents": "Valid ID, 个人购汇申请书, amount-bearing purpose documents; above USD 50,000/day outward wire needs transaction materials.", "limit": "USD 50,000/person/year is a convenience/documentation threshold, not a hard cap.", "advantages": "No ceiling when documents exist; counter or e-banking permitted under Art. 55.", "drawbacks": "Applicant is responsible for the accuracy of the purchase application; purchase and remittance purposes must be consistent; splitting is prohibited.", "conversion_tax_notes": "Same underlying-income and U.S. reporting rules as B01.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS06|BS09|BS10|BS18|BS19", "flag_ids": "B9B3-F02|B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06"},
    {"method_id": "B03", "method": "Wire foreign currency already held in a PRC FX account", "legal_status": "conditional", "who": "Holder of an existing foreign-currency savings account", "when_to_use": "Part or all of the balance is already USD/FX, not CNY.", "documents": "Valid ID and wire form; 境内个人 above USD 50,000/day also needs amount-bearing materials.", "limit": "Art. 65 states no amount threshold for an 境外个人's FX-account wire; Art. 64 sets the domestic-individual threshold.", "advantages": "No FX purchase, so no bid/ask spread; only published wire/cable cost.", "drawbacks": "Does not convert CNY; unavailable for a pure RMB balance.", "conversion_tax_notes": "No conversion; U.S. §988 disposition of nonfunctional currency and reporting still need review.", "cost_model": "wire_only", "source_ids": "BS02|BS05|BS06|BS10|BS20", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F07"},
    {"method_id": "B04", "method": "Reconvert unused RMB with the original exchange slip", "legal_status": "conditional", "who": "境外个人 who previously converted FX into RMB and did not use it all", "when_to_use": "Original 兑换水单 is dated within 24 months and the unused amount is identifiable.", "documents": "Valid ID, original exchange slip, wire form.", "limit": "Up to the unused amount on the slip; slip valid 24 months from exchange.", "advantages": "No income/tax source documents needed beyond the slip; simple bank workflow.", "drawbacks": "Useless for RMB earned/received in China or for old/missing slips.", "conversion_tax_notes": "Returning one's own unused FX is not identified as new income in the sources read.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS05|BS11|BS20", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F17"},
    {"method_id": "B05", "method": "Small ID-only reconversion without the original slip", "legal_status": "conditional", "who": "境外个人 with small unused RMB amounts", "when_to_use": "Only within the official daily ID-only limits; not a route for a large balance in one transaction.", "documents": "Valid ID.", "limit": "≤USD 500/day (≤USD 1,000/day at border-side outlets) on ID alone; larger amounts need the original slip.", "advantages": "Minimal paperwork for small amounts.", "drawbacks": "Cannot execute USD 10,000-400,000 as a single lawful transaction under this rule; no banknote fee published.", "conversion_tax_notes": "Not priced; all cost cells are blank and flagged.", "cost_model": "blank", "source_ids": "BS01|BS11|BS22", "flag_ids": "B9B3-F03|B9B3-F17|B9B3-F11"},
    {"method_id": "B06", "method": "USD 50,000 annual convenience amount (PRC Foreign Permanent Resident ID)", "legal_status": "conditional", "who": "境外个人 holding the PRC Foreign Permanent Resident ID Card", "when_to_use": "The user actually holds that ID and can wait one calendar year per USD 50,000 tranche.", "documents": "Valid ID inside the convenience amount; documents above it.", "limit": "USD 50,000 equivalent/person/calendar year on ID alone for purchase; not a hard total cap.", "advantages": "No source/tax documents inside the yearly amount.", "drawbacks": "USD 400,000 needs eight calendar years; a U.S. passport alone does not qualify.", "conversion_tax_notes": "No conversion tax found; U.S. reporting applies each year.", "cost_model": "quota", "source_ids": "BS01|BS02|BS06|BS08|BS09|BS12", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F16"},
    {"method_id": "B07", "method": "Proceeds from selling PRC real property", "legal_status": "conditional", "who": "境外个人 who owned and sold onshore commercial/residential property", "when_to_use": "Title transfer and tax payment are complete and the RMB is the sale proceeds.", "documents": "Passport, registered transfer contract, title-transfer proof, tax voucher; 税务备案表 above USD 50,000 unless waived.", "limit": "Remittance cannot exceed transfer price minus taxes/fees (and ownership share).", "advantages": "Direct bank handling for a genuine large capital-account exit; fixed document list.", "drawbacks": "20% IIT on gain and other property taxes are case-specific; original cost needed.", "conversion_tax_notes": "20% PRC IIT on gain; U.S. foreign tax credit may apply to the same income.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS17|BS18|BS28|BS32|BS41", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06|B9B3-F13"},
    {"method_id": "B08", "method": "Inheritance transfer (继承转移)", "legal_status": "conditional", "who": "Foreign citizen inheriting assets from a decedent with a PRC hukou", "when_to_use": "There is a genuine estate, inheritance proof and tax certificate.", "documents": "Application to SAFE at decedent's last hukou, inheritance/property documents, tax certificate, own overseas account details.", "limit": "One application for the estate; bank may remit once or in instalments within the approved amount.", "advantages": "Dedicated legal route for large inherited wealth.", "drawbacks": "Discretionary approval and evidence-heavy; Chinese inheritance-tax treatment not affirmatively confirmed.", "conversion_tax_notes": "PRC tax certificate required; U.S. Form 3520 reports foreign bequests >USD 100,000.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS14|BS15|BS16|BS40|BS28", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F12|B9B3-F15"},
    {"method_id": "B09", "method": "Emigrant property transfer (移民转移)", "legal_status": "conditional", "who": "Former mainland resident who emigrated and cancelled PRC hukou", "when_to_use": "Assets were owned before emigrant status and hukou cancellation/settlement proof exist.", "documents": "SAFE application at former hukou, cancellation certificate, certified settlement proof, property/source and tax documents.", "limit": "Approved amount; bank may remit once or in instalments since 2014.", "advantages": "No annual quota; dedicated route for a former resident's savings/property.", "drawbacks": "Unavailable to someone who never held mainland residence; approval is evidence-heavy.", "conversion_tax_notes": "Tax certificates from the place where income/gain arose are required.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS14|BS15|BS16|BS18", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F12"},
    {"method_id": "B10", "method": "Dividend / profit distribution from a PRC company", "legal_status": "conditional", "who": "Foreign shareholder of a domestic company, not a personal savings holder", "when_to_use": "Money is genuinely distributable corporate profit, not personal CNY savings.", "documents": "Board/partnership profit-distribution resolution, tax filing form above USD 50,000, company accounts, withholding evidence.", "limit": "Limited to genuine distributable profit; USD 50,000 is a review threshold.", "advantages": "Proper route for business profit; no personal annual quota.", "drawbacks": "Not a personal route; using it for savings is a disguised transfer; treaty eligibility needs evidence.", "conversion_tax_notes": "20% statutory IIT on dividends; treaty Art. 9(2) 10% cap for a beneficial owner, subject to self-assessment and retained documents.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS15|BS18|BS28|BS31|BS32", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06|B9B3-F14"},
    {"method_id": "B11", "method": "Cross-border RMB remittance, convert offshore", "legal_status": "conditional", "who": "Payer with genuine current-account RMB obligation and a bank offering personal outbound RMB", "when_to_use": "The underlying transaction can lawfully be settled in RMB and the offshore bank accepts CNY.", "documents": "Same authenticity documentation as the underlying current-account transaction; receiving-bank CNY details.", "limit": "Current-account/approved transaction only; no personal outbound RMB tariff or offshore CNH rate published.", "advantages": "Avoids the onshore conversion step; PBOC notes the 2018 reform allows RMB wherever FX is lawful.", "drawbacks": "Offshore conversion rate and receiving fee are unknown; no official personal cost; not every bank offers it.", "conversion_tax_notes": "Same underlying-income and U.S. §988 issues as B01.", "cost_model": "blank", "source_ids": "BS19|BS26|BS27", "flag_ids": "B9B3-F09|B9B3-F26"},
    {"method_id": "B12", "method": "Overseas UnionPay ATM cash withdrawals", "legal_status": "conditional", "who": "Holder of a mainland UnionPay debit card on the RMB account", "when_to_use": "Small amounts while travelling outside the mainland; not a practical single route for large balances.", "documents": "Card, PIN, ID; U.S. FinCEN Form 105 if physically carrying >USD 10,000.", "limit": "RMB 10,000/card/day; RMB 100,000/person/calendar year; breach suspends current+next year.", "advantages": "No branch FX paperwork for small withdrawals.", "drawbacks": "BOC fee is only one component; UnionPay rate and ATM-owner fee unknown; USD 400,000 would take decades.", "conversion_tax_notes": "Cash declaration and U.S. reporting still apply; no all-in cost is published.", "cost_model": "atm", "source_ids": "BS03|BS21|BS49|BS50", "flag_ids": "B9B3-F10"},
    {"method_id": "B13", "method": "Carry foreign-currency cash out in person", "legal_status": "conditional", "who": "Individual who first lawfully buys the foreign currency", "when_to_use": "Small amounts; a delivery method, not a way around source/tax documents.", "documents": "Valid ID; bank permit for USD 5,000-10,000; SAFE permit above USD 10,000 in principle not granted; U.S. FinCEN Form 105 above USD 10,000.", "limit": "≤USD 5,000 customs release; USD 5,000-10,000 bank permit; >USD 10,000 generally not allowed.", "advantages": "No wire or receiving-bank fee if cash already exists.", "drawbacks": "Banknote withdrawal fee and travel cost unknown; theft/loss risk; 80 trips for USD 400,000 at USD 5,000/trip.", "conversion_tax_notes": "Cash selling rate equals spot selling on this board; no conversion tax found.", "cost_model": "cash", "source_ids": "BS01|BS22|BS49|BS19", "flag_ids": "B9B3-F11"},
    {"method_id": "B14", "method": "Consolidate own/close-relative accounts before one outward wire", "legal_status": "conditional", "who": "Accounts of the same person or close relatives in the same subject category", "when_to_use": "Multiple domestic accounts need to be combined before the lawful outward remittance.", "documents": "Valid ID; account-category evidence; outward-wire documents for the chosen route.", "limit": "Transfers between 境内个人 and 境外个人 FX accounts are treated as cross-border.", "advantages": "One outward wire minimises fixed cable charges.", "drawbacks": "Does not itself move money out of China; wrong-category transfer triggers cross-border rules.", "conversion_tax_notes": "Same as the eventual outward route.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS06", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06"},
    {"method_id": "B15", "method": "Genuine service-trade outward payment", "legal_status": "conditional", "who": "Individual/institution paying for a real cross-border service", "when_to_use": "There is a genuine contract/invoice; not for exporting personal savings.", "documents": "Contract/invoice/settlement list, tax filing form above USD 50,000, wire form.", "limit": "USD 50,000 per transaction is a review/recordal threshold, not a cap.", "advantages": "Legitimate channel for genuine services; below USD 50,000 the bank need not ordinarily review documents.", "drawbacks": "Fabricated background is prohibited and engages Art. 40 penalties; personal savings do not qualify.", "conversion_tax_notes": "Underlying service income/payment tax rules apply.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS06|BS13|BS18|BS19", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06"},
    {"method_id": "B16", "method": "Foreign investor's share of a lawfully liquidated FIE", "legal_status": "conditional", "who": "Foreign investor in a terminated foreign-invested enterprise", "when_to_use": "Real enterprise, real liquidation and tax actually paid.", "documents": "Lawful termination, completed liquidation and tax-payment evidence; SAFE/bank approvals.", "limit": "No amount ceiling stated in Decree 532 Art. 22(3); limited to RMB belonging to the foreign investor.", "advantages": "Express State Council regulation; covers capital, not just income.", "drawbacks": "Only for a real liquidation; takes time and professional cost; personal savings out of scope.", "conversion_tax_notes": "Corporate/withholding tax and tax clearance precede remittance.", "cost_model": "fx_wire", "source_ids": "BS01|BS02|BS19|BS18", "flag_ids": "B9B3-F03|B9B3-F04|B9B3-F05|B9B3-F06|B9B3-F12"},
    {"method_id": "B17", "method": "Direct RMB salary remittance abroad (foreign employee)", "legal_status": "conditional", "who": "Foreign employee with lawful RMB salary and a bank offering personal outbound RMB", "when_to_use": "The underlying payment is genuine current-account remuneration and the bank supports the channel.", "documents": "Employment/income and tax evidence; receiving-bank CNY account details; bank's RMB cross-border form.", "limit": "No official personal outbound RMB tariff, offshore conversion rate or receiving fee published.", "advantages": "PBOC Beijing reports a real foreign employee's RMB salary remittance that avoided an onshore conversion charge.", "drawbacks": "Does not by itself produce USD; cost is blank; not every bank offers it to individuals.", "conversion_tax_notes": "Same underlying-income and U.S. §988 issues as B01.", "cost_model": "blank", "source_ids": "BS26|BS27|BS19", "flag_ids": "B9B3-F09|B9B3-F26"},
    {"method_id": "B18", "method": "Gift / undocumented RMB balance", "legal_status": "unverified", "who": "Recipient of a gift or funds whose origin cannot be documented", "when_to_use": "No verified lawful route was found; do not assume one.", "documents": "Not established.", "limit": "Not established.", "advantages": "None verified.", "drawbacks": "No official rule read here permits a foreign passport holder to convert and remit undocumented/gift RMB; bank may refuse.", "conversion_tax_notes": "U.S. Form 3520 may report a foreign gift/bequest >USD 100,000; PRC route unverified.", "cost_model": "blank", "source_ids": "BS06|BS07|BS40|BS19", "flag_ids": "B9B3-F18"},
    {"method_id": "B19", "method": "Quota splitting / 'ant moving' through relatives or friends", "legal_status": "prohibited", "who": "Not applicable", "when_to_use": "Never; prohibited.", "documents": "Not applicable.", "limit": "Not applicable.", "advantages": "None lawful.", "drawbacks": "Art. 62 watch-list for current year plus two; SAFE Hebei case treated 52-person splitting as 逃汇; fine up to 30%, 30%-100% if serious.", "conversion_tax_notes": "Penalty exposure, not a cost model.", "cost_model": "blank", "source_ids": "BS12|BS19|BS24", "flag_ids": "B9B3-F16|B9B3-F20"},
    {"method_id": "B20", "method": "Private FX swaps, apps, brokers, underground banks", "legal_status": "prohibited", "who": "Not applicable", "when_to_use": "Never; prohibited.", "documents": "Not applicable.", "limit": "Not applicable.", "advantages": "None lawful.", "drawbacks": "Only qualified banks/licensed institutions may convert FX; private channels are illegal; Decree 532 Art. 45 fine up to 30%, 30%-100% if serious.", "conversion_tax_notes": "Penalty/confiscation exposure, not a cost model.", "cost_model": "blank", "source_ids": "BS19|BS23|BS24", "flag_ids": "B9B3-F20"},
    {"method_id": "B21", "method": "Crypto / stablecoin / RWA conversion", "legal_status": "prohibited", "who": "Not applicable", "when_to_use": "Never; prohibited in the PRC under the 2026 notice.", "documents": "Not applicable.", "limit": "Not applicable.", "advantages": "None lawful.", "drawbacks": "银发〔2026〕42号 strictly forbids fiat/virtual-currency exchange, unapproved RMB stablecoins and RWA tokenisation; funds have no legal protection.", "conversion_tax_notes": "Prohibition and possible Art. 39/45 exposure, not a cost model.", "cost_model": "blank", "source_ids": "BS19|BS23|BS25", "flag_ids": "B9B3-F20"},
    {"method_id": "B22", "method": "False documents / false purpose / undeclared excess cash", "legal_status": "prohibited", "who": "Not applicable", "when_to_use": "Never; prohibited.", "documents": "Not applicable.", "limit": "Not applicable.", "advantages": "None lawful.", "drawbacks": "Art. 40 false-document FX purchase, Art. 48 untrue documents up to RMB 50,000, Art. 42 cash breach up to 20%; U.S. CBP seizure/penalties above USD 10,000 undeclared.", "conversion_tax_notes": "Penalty exposure, not a cost model.", "cost_model": "blank", "source_ids": "BS19|BS22|BS24|BS49", "flag_ids": "B9B3-F11|B9B3-F20"},
]

PENALTIES = [
    {"penalty_id": "B9B3-P01", "jurisdiction": "PRC", "rule": "No tax on conversion itself (negative finding)", "trigger": "Buying USD with one's own lawful CNY and wiring it out", "rate_or_amount": "No official conversion tax found", "conditions": "This is a negative finding from the official pages read; it is not a statement about tax on the underlying income or gain.", "source_ids": "BS19|BS06|BS07|BS02", "flag_ids": "B9B3-F06"},
    {"penalty_id": "B9B3-P02", "jurisdiction": "PRC", "rule": "IIT comprehensive/wage income", "trigger": "Underlying wages or comprehensive income", "rate_or_amount": "3%-45%", "conditions": "Progressive rates under IIT Law Art. 3; applies to income, not conversion.", "source_ids": "BS28", "flag_ids": "B9B3-F06"},
    {"penalty_id": "B9B3-P03", "jurisdiction": "PRC", "rule": "IIT business income", "trigger": "Underlying business income", "rate_or_amount": "5%-35%", "conditions": "IIT Law Art. 3.", "source_ids": "BS28", "flag_ids": "B9B3-F06"},
    {"penalty_id": "B9B3-P04", "jurisdiction": "PRC", "rule": "IIT flat categories", "trigger": "Interest, dividends, rent, property transfer, incidental income", "rate_or_amount": "20%", "conditions": "IIT Law Art. 3; property transfer is taxed on gain after original value and reasonable expenses.", "source_ids": "BS28|BS17", "flag_ids": "B9B3-F06|B9B3-F13"},
    {"penalty_id": "B9B3-P05", "jurisdiction": "PRC", "rule": "Savings-deposit interest exemption", "trigger": "RMB savings-deposit interest", "rate_or_amount": "0% (exempt since 2008-10-09)", "conditions": "财税〔2008〕132号.", "source_ids": "BS29", "flag_ids": ""},
    {"penalty_id": "B9B3-P06", "jurisdiction": "PRC", "rule": "Tax record-filing before large outbound payment", "trigger": "Single outbound payment >USD 50,000 for salary/dividends/real-estate income etc.", "rate_or_amount": "税务备案表 required; no fixed percentage", "conditions": "STA/SAFE 2013 No. 40; property guide waives the form at ≤USD 50,000.", "source_ids": "BS18|BS17", "flag_ids": "B9B3-F06|B9B3-F13"},
    {"penalty_id": "B9B3-P07", "jurisdiction": "PRC", "rule": "Late tax payment surcharge", "trigger": "Tax not paid by the deadline", "rate_or_amount": "0.05% per day (万分之五)", "conditions": "Tax Collection Administration Law Art. 32.", "source_ids": "BS30", "flag_ids": "B9B3-F06"},
    {"penalty_id": "B9B3-P08", "jurisdiction": "PRC", "rule": "Tax evasion penalty", "trigger": "False books/returns causing underpaid tax", "rate_or_amount": "50%-500% of underpaid tax", "conditions": "Tax Collection Administration Law Art. 63; criminal liability if a crime.", "source_ids": "BS30", "flag_ids": "B9B3-F06"},
    {"penalty_id": "B9B3-P09", "jurisdiction": "PRC", "rule": "逃汇 / unlawful outward transfer", "trigger": "Moving FX abroad in violation, or by deception", "rate_or_amount": "Up to 30% of amount; 30%-100% if serious", "conditions": "Decree 532 Art. 39; repatriation order and criminal liability possible.", "source_ids": "BS19|BS24", "flag_ids": "B9B3-F20"},
    {"penalty_id": "B9B3-P10", "jurisdiction": "PRC", "rule": "False documents to buy FX (非法套汇)", "trigger": "False/invalid transaction documents", "rate_or_amount": "Up to 30%; 30%-100% if serious", "conditions": "Decree 532 Art. 40; funds ordered converted back.", "source_ids": "BS19", "flag_ids": "B9B3-F20"},
    {"penalty_id": "B9B3-P11", "jurisdiction": "PRC", "rule": "Border cash breach", "trigger": "Carrying FX across the border in breach of rules", "rate_or_amount": "Warning and fine up to 20%", "conditions": "Decree 532 Art. 42; separate permit rules in BS22.", "source_ids": "BS19|BS22", "flag_ids": "B9B3-F11"},
    {"penalty_id": "B9B3-P12", "jurisdiction": "PRC", "rule": "Private/illegal FX trading", "trigger": "Private buying/selling, disguised forms, brokering", "rate_or_amount": "Warning/confiscation; up to 30%; 30%-100% if serious", "conditions": "Decree 532 Art. 45; SAFE Guangdong warning.", "source_ids": "BS19|BS23", "flag_ids": "B9B3-F20"},
    {"penalty_id": "B9B3-P13", "jurisdiction": "PRC", "rule": "Untrue documents / reporting", "trigger": "Individual provides untrue documents or fails reporting", "rate_or_amount": "Up to RMB 50,000", "conditions": "Decree 532 Art. 48.", "source_ids": "BS19", "flag_ids": ""},
    {"penalty_id": "B9B3-P14", "jurisdiction": "PRC", "rule": "Quota-splitting watch-list", "trigger": "Borrowing others' convenience amounts or evading authenticity review", "rate_or_amount": "Current year + 2 calendar years on 关注名单", "conditions": "汇发〔2020〕14号 Art. 62; while listed, documents are required.", "source_ids": "BS12|BS06|BS24", "flag_ids": "B9B3-F16|B9B3-F20"},
    {"penalty_id": "B9B3-P15", "jurisdiction": "PRC", "rule": "Overseas card cash cap", "trigger": "RMB 10,000/card/day or RMB 100,000/person/year exceeded", "rate_or_amount": "Overseas cash withdrawals suspended current + next year", "conditions": "汇发〔2017〕29号; bank reports transactions under 汇发〔2017〕15号.", "source_ids": "BS21|BS50", "flag_ids": "B9B3-F10"},
    {"penalty_id": "B9B3-P16", "jurisdiction": "PRC", "rule": "Cash export limits", "trigger": "Carrying foreign banknotes out of China", "rate_or_amount": "≤USD 5,000 release; USD 5,000-10,000 bank permit; >USD 10,000 SAFE permit in principle not granted", "conditions": "SAFE Hebei Q&A; Decree 532 Art. 42 penalty for breach.", "source_ids": "BS22|BS19", "flag_ids": "B9B3-F11"},
    {"penalty_id": "B9B3-P17", "jurisdiction": "PRC", "rule": "Crypto / stablecoin / RWA prohibition", "trigger": "Fiat↔virtual-currency exchange or unapproved stablecoin/RWA activity", "rate_or_amount": "Activity prohibited; no protective legal status", "conditions": "银发〔2026〕42号 repeals 银发〔2021〕237号.", "source_ids": "BS25|BS19", "flag_ids": "B9B3-F20"},
    {"penalty_id": "B9B3-P18", "jurisdiction": "PRC / treaty", "rule": "Dividend treaty cap", "trigger": "PRC-source dividend to U.S. beneficial owner", "rate_or_amount": "10% of gross", "conditions": "Treaty Art. 9(2); STA 2019 No. 35 self-assessment/report form and retained tax-residency/beneficial-owner documents.", "source_ids": "BS32|BS31", "flag_ids": "B9B3-F14"},
    {"penalty_id": "B9B3-P19", "jurisdiction": "PRC / treaty", "rule": "Interest and royalty treaty cap", "trigger": "PRC-source interest/royalty to U.S. beneficial owner", "rate_or_amount": "10% of gross", "conditions": "Treaty Arts. 10(2) and 11(2); saving clause preserves U.S. taxation of citizens.", "source_ids": "BS32", "flag_ids": "B9B3-F14"},
    {"penalty_id": "B9B3-P20", "jurisdiction": "US", "rule": "26 U.S.C. §988 ordinary FX gain/loss", "trigger": "Disposition of nonfunctional currency, including bank deposits", "rate_or_amount": "Ordinary income/loss; personal gain ≤USD 200 excluded", "conditions": "§988(e)(3) excludes §162/§212 expense transactions from personal treatment; exact basis unknown.", "source_ids": "BS33|BS34|BS47", "flag_ids": "B9B3-F07"},
    {"penalty_id": "B9B3-P21", "jurisdiction": "US", "rule": "FBAR filing", "trigger": "Aggregate foreign accounts >USD 10,000 at any time in the year", "rate_or_amount": "FinCEN Form 114; due Apr 15, auto-ext Oct 15", "conditions": "Electronic BSA e-filing; separate from Form 8938.", "source_ids": "BS36|BS35|BS47", "flag_ids": "B9B3-F08"},
    {"penalty_id": "B9B3-P22", "jurisdiction": "US", "rule": "FBAR non-willful penalty", "trigger": "Non-willful FBAR violation", "rate_or_amount": "Statutory ≤USD 10,000; current adjusted amount USD 16,536", "conditions": "31 U.S.C. §5321(a)(5)(B)(i) and 31 CFR 1010.821; reasonable-cause exception.", "source_ids": "BS37|BS38", "flag_ids": "B9B3-F22"},
    {"penalty_id": "B9B3-P23", "jurisdiction": "US", "rule": "FBAR willful penalty", "trigger": "Willful FBAR violation", "rate_or_amount": "Greater of USD 100,000 (adjusted USD 165,353) or 50% of account balance", "conditions": "31 U.S.C. §5321(a)(5)(C)-(D) plus eCFR adjusted table; Bittner-related IRM guidance is linked in BS46.", "source_ids": "BS37|BS38|BS46", "flag_ids": "B9B3-F22"},
    {"penalty_id": "B9B3-P24", "jurisdiction": "US", "rule": "Form 8938 threshold and penalty", "trigger": "Specified foreign financial assets exceed filing thresholds", "rate_or_amount": "USD 10,000, +USD 10,000/30 days after notice, max USD 60,000", "conditions": "Single in U.S. USD 50,000 year-end / USD 75,000 any time; single abroad USD 200,000 / USD 300,000; joint double.", "source_ids": "BS35", "flag_ids": "B9B3-F08"},
    {"penalty_id": "B9B3-P25", "jurisdiction": "US", "rule": "Form 3520 foreign gift/bequest", "trigger": "Gift/bequest from NRA/foreign estate >USD 100,000/year", "rate_or_amount": "Report on Form 3520 Part IV; late penalty 5%/month up to 25%", "conditions": "26 U.S.C. §6039F has a reasonable-cause exception; corp/partnership gifts use the inflation-adjusted threshold.", "source_ids": "BS40|BS39|BS47", "flag_ids": "B9B3-F08|B9B3-F18"},
    {"penalty_id": "B9B3-P26", "jurisdiction": "US", "rule": "Foreign tax credit / treaty saving clause", "trigger": "PRC income tax paid on income also taxed by the U.S.", "rate_or_amount": "Credit subject to Form 1116 limitations", "conditions": "Treaty Art. 22(2); Protocol 1 ¶2 preserves U.S. taxation of its citizens.", "source_ids": "BS32|BS41", "flag_ids": "B9B3-F06"},
    {"penalty_id": "B9B3-P27", "jurisdiction": "US", "rule": "Streamlined procedures", "trigger": "Past non-willful noncompliance", "rate_or_amount": "SFOP: no streamlined penalty; SDOP: 5% miscellaneous offshore penalty", "conditions": "SFOP non-residency test, 3 years returns and 6 years FBARs; SDOP has its own eligibility and certification.", "source_ids": "BS42|BS43|BS44", "flag_ids": "B9B3-F08"},
    {"penalty_id": "B9B3-P28", "jurisdiction": "US", "rule": "Foreign earned income exclusion", "trigger": "Foreign earned income from personal services", "rate_or_amount": "", "conditions": "FEIE does not apply to existing savings, pension/annuity or currency gain; 2026 inflation-adjusted figure is deliberately blank.", "source_ids": "BS48|BS33", "flag_ids": "B9B3-F19"},
    {"penalty_id": "B9B3-P29", "jurisdiction": "US", "rule": "Currency/monetary-instrument declaration", "trigger": "Physically carrying/shipping >USD 10,000 into/out of the U.S.", "rate_or_amount": "FinCEN Form 105 required", "conditions": "Threshold applies collectively to a family/group; failure risks seizure/forfeiture and civil/criminal penalties.", "source_ids": "BS49", "flag_ids": "B9B3-F11"},
    {"penalty_id": "B9B3-P30", "jurisdiction": "US", "rule": "Bank/correspondent deductions", "trigger": "Wire routed through one or more intermediary banks", "rate_or_amount": "", "conditions": "BOC says each intermediary may deduct a transfer fee; no official single figure. OUR historical surcharge is USD 15/25 but current applicability is unverified.", "source_ids": "BS05|BS04|BS02", "flag_ids": "B9B3-F04|B9B3-F05"},
]

STEP_TEXT = {
    "B01": [
        ("Identify each deposit and classify it as salary, service income, current transfer or another lawful current-account category; do not mix business, gift or capital funds into this route.", "BS06|BS07|BS19", "B9B3-F01"),
        ("Collect the valid ID, amount-bearing source-of-funds documents and the tax voucher, exemption certificate or 税务备案表 required for a single payment above USD 50,000.", "BS07|BS13|BS18", "B9B3-F06"),
        ("Ask the bank to confirm in writing that it accepts the documents, the purchase purpose matches the remittance purpose, and the account is classified as 境外个人; get the dated executable rate and itemised fee quote.", "BS02|BS05|BS20|BS19", "B9B3-F02|B9B3-F03|B9B3-F04"),
        ("Complete the international wire form with the verified payee account/SWIFT details, pay the CNY principal and fees, sign the application, and retain the rate confirmation, tax evidence and wire receipt.", "BS05|BS02|BS18", "B9B3-F05|B9B3-F06"),
    ],
    "B02": [
        ("Obtain the bank's written 境内个人 classification and confirm the genuine current-account purpose.", "BS19|BS20|BS10", "B9B3-F02"),
        ("Complete the 个人购汇申请书 and assemble amount-bearing purpose documents; above USD 50,000/day also assemble outward-remittance transaction materials.", "BS06|BS09|BS10", "B9B3-F16"),
        ("Check purchase/remittance purpose consistency with the bank and obtain the dated rate and fee quote; do not split the application across people.", "BS02|BS05|BS12", "B9B3-F03|B9B3-F16"),
        ("Sign the wire application, pay principal and fees, and retain the application, quote, tax recordal if applicable and receipt.", "BS05|BS18|BS02", "B9B3-F05|B9B3-F06"),
    ],
    "B03": [
        ("Obtain a currency-by-currency statement showing the balance is already USD/FX rather than CNY.", "BS05|BS20", "B9B3-F01"),
        ("Confirm the bank's 境外个人/境内个人 classification and whether the USD 50,000/day documentation threshold applies.", "BS06|BS10|BS20", "B9B3-F02|B9B3-F16"),
        ("Request the written wire/cable quote and verified receiving-bank/SWIFT details; no FX purchase means no bid/ask spread.", "BS02|BS05", "B9B3-F03|B9B3-F05"),
        ("Sign the wire application, pay the wire/cable fees and retain the receipt; review U.S. §988 and reporting separately.", "BS05|BS33|BS36", "B9B3-F07|B9B3-F08"),
    ],
    "B04": [
        ("Locate the original 兑换水单 and confirm its exchange date is within 24 months.", "BS11", "B9B3-F17"),
        ("Ask the bank to confirm the unused amount shown by the slip and that no income/tax documents are needed for this reconversion.", "BS11|BS20", "B9B3-F17"),
        ("Obtain the dated rate and wire/cable quote and the receiving-bank instructions.", "BS01|BS02|BS05", "B9B3-F03|B9B3-F04"),
        ("Sign the wire application, pay principal and fees, and retain the slip, quote and receipt.", "BS05|BS02", "B9B3-F05"),
    ],
    "B05": [
        ("Confirm the amount is within the official ID-only daily limit (≤USD 500/day; ≤USD 1,000/day at border-side outlets).", "BS11", "B9B3-F17"),
        ("Present valid ID at the bank/authorised outlet and ask for the written banknote rate and fee before transacting.", "BS11|BS23|BS01", "B9B3-F11"),
        ("If carrying cash, observe the PRC cash-export permit and U.S. Form 105 declaration rules; do not exceed them.", "BS22|BS49", "B9B3-F11"),
        ("Stop: this rule cannot execute USD 10,000-400,000 as one transaction; use a documented route or obtain the original slip.", "BS11|BS06", "B9B3-F17|B9B3-F11"),
    ],
    "B06": [
        ("Confirm you actually hold the PRC Foreign Permanent Resident ID Card; a U.S. passport alone does not qualify for purchase on ID alone.", "BS08|BS07", "B9B3-F16"),
        ("Confirm the remaining USD 50,000 equivalent convenience amount for the calendar year with the bank in writing.", "BS09|BS08", "B9B3-F16"),
        ("Obtain the dated rate and per-wire fee quote, then repeat one compliant wire per calendar year for each full USD 50,000 tranche plus the remainder.", "BS01|BS02|BS05", "B9B3-F03|B9B3-F04"),
        ("Retain each year's application, quote and receipt; do not borrow anyone else's quota.", "BS12|BS24|BS05", "B9B3-F16|B9B3-F20"),
    ],
    "B07": [
        ("Complete the property title transfer and obtain the registered transfer contract and title-transfer proof.", "BS17", "B9B3-F13"),
        ("Obtain the tax voucher and, for a single payment above USD 50,000, the applicable 税务备案表; compute the 20% IIT on gain using original cost and reasonable expenses.", "BS17|BS18|BS28", "B9B3-F13|B9B3-F06"),
        ("Ask the bank to confirm the remittance ceiling (transfer price minus taxes/fees and ownership share) and obtain the dated rate and wire quote.", "BS17|BS01|BS02", "B9B3-F03|B9B3-F04"),
        ("Sign the wire application and retain the property, tax, approval and wire records for PRC and U.S. credit/reporting purposes.", "BS05|BS41|BS32", "B9B3-F05|B9B3-F06"),
    ],
    "B08": [
        ("Gather inheritance proof, property documents and the tax certificate for the estate; confirm the decedent's last hukou location.", "BS14|BS16", "B9B3-F15|B9B3-F12"),
        ("File the 继承转移 application with the SAFE office at that hukou location and obtain the written approval amount.", "BS14|BS15|BS16", "B9B3-F12"),
        ("Give the bank the approval, your own overseas account details and tax certificate; ask whether it will remit once or in instalments and obtain the rate/fee quote.", "BS14|BS15|BS02|BS05", "B9B3-F12|B9B3-F03|B9B3-F04"),
        ("Retain every approval and wire record; report a foreign bequest above USD 100,000 on Form 3520 and review U.S. tax treatment.", "BS40|BS47|BS39", "B9B3-F08|B9B3-F15"),
    ],
    "B09": [
        ("Gather hukou-cancellation proof, certified settlement proof, property/source documents and tax certificates; confirm the former hukou location.", "BS14|BS16", "B9B3-F12"),
        ("File the 移民转移 application with the SAFE office at the former hukou location and obtain the written approval amount.", "BS14|BS15|BS16", "B9B3-F12"),
        ("Give the bank the approval and own overseas account details; ask for the one-or-instalment remittance schedule and dated rate/fee quote.", "BS14|BS15|BS02|BS05", "B9B3-F12|B9B3-F03|B9B3-F04"),
        ("Retain approvals, tax certificates and wire receipts; complete U.S. reporting and §988 review.", "BS47|BS33|BS36", "B9B3-F07|B9B3-F08"),
    ],
    "B10": [
        ("Confirm the money is genuine distributable corporate profit, not personal savings, and obtain the board/partnership resolution and accounts.", "BS15|BS18", "B9B3-F06"),
        ("Obtain the tax filing form for a payment above USD 50,000 and decide, with evidence, whether the 10% treaty position is supportable; otherwise use the 20% statutory IIT.", "BS15|BS18|BS28|BS31|BS32", "B9B3-F14"),
        ("Ask the bank for the written tax/document review, dated rate and wire quote; do not disguise personal funds as a dividend.", "BS02|BS05|BS19", "B9B3-F03|B9B3-F04|B9B3-F20"),
        ("Sign the wire application and retain resolution, tax recordal, treaty evidence, quote and receipt for Form 1116/U.S. reporting.", "BS05|BS41|BS35", "B9B3-F05|B9B3-F06"),
    ],
    "B11": [
        ("Confirm with the sending bank in writing that it offers personal outbound RMB for this exact genuine current-account transaction.", "BS26|BS27|BS19", "B9B3-F09|B9B3-F26"),
        ("Collect the same authenticity and tax documents required for the underlying transaction; obtain the receiving bank's CNY account instructions.", "BS19|BS18|BS26", "B9B3-F06"),
        ("Request written sending-bank fees and the offshore bank's CNY→USD conversion rate/fee; do not proceed until the all-in USD received is known.", "BS26|BS27|BS05", "B9B3-F09"),
        ("Only then authorise the RMB wire; retain both banks' quotes and receipts and complete U.S. §988/reporting review.", "BS33|BS36|BS47", "B9B3-F07|B9B3-F08"),
    ],
    "B12": [
        ("Confirm the card is a mainland UnionPay debit card on the RMB account and read BOC's current card fee.", "BS03|BS21", "B9B3-F10"),
        ("Check the RMB 10,000/card/day and RMB 100,000/person/calendar-year caps before choosing amounts.", "BS21|BS50", "B9B3-F10"),
        ("Obtain UnionPay's dated conversion rate and the foreign ATM owner's on-screen fee; leave the all-in cost blank until both are written.", "BS03|BS21|BS50", "B9B3-F10"),
        ("If physically carrying more than USD 10,000 into the U.S., file FinCEN Form 105; retain withdrawal and declaration records.", "BS49|BS47", "B9B3-F10|B9B3-F08"),
    ],
    "B13": [
        ("First lawfully buy the foreign currency through an eligible route and obtain the bank's cash-selling rate and banknote withdrawal fee.", "BS01|BS19|BS23", "B9B3-F11"),
        ("For USD 5,000-10,000 obtain the bank's 携带外汇出境许可证; do not carry more than USD 10,000 without the required SAFE permit.", "BS22|BS19", "B9B3-F11"),
        ("Before entering the U.S., determine whether the family/group carries more than USD 10,000 and prepare FinCEN Form 105.", "BS49", "B9B3-F11"),
        ("Retain the purchase, permit, declaration and banknote records; this is a delivery method, not a way around source/tax rules.", "BS05|BS18|BS49", "B9B3-F06|B9B3-F11"),
    ],
    "B14": [
        ("List the accounts to consolidate and confirm each belongs to the same person or a close relative in the same subject category.", "BS06|BS20", "B9B3-F02"),
        ("Ask the bank in writing whether a 境内个人↔境外个人 FX-account transfer would be treated as cross-border; do not make that transfer casually.", "BS06|BS20", "B9B3-F02"),
        ("Consolidate the balance, then select one lawful outward route (B01/B02/B04/B07 etc.) and obtain its documents and quote.", "BS06|BS01|BS02", "B9B3-F03|B9B3-F04"),
        ("Send one outward wire and retain consolidation and wire records.", "BS05|BS02", "B9B3-F05"),
    ],
    "B15": [
        ("Confirm there is a real cross-border service with a contract/invoice/settlement list; personal savings do not qualify.", "BS06|BS19", "B9B3-F20"),
        ("For a single payment above USD 50,000, obtain the tax record-filing form; below the threshold ask the bank what it reviews.", "BS18|BS06", "B9B3-F06"),
        ("Obtain the dated rate and itemised wire quote and confirm the purpose matches the service documents.", "BS01|BS02|BS05", "B9B3-F03|B9B3-F04"),
        ("Sign the wire application and retain contract, tax, quote and receipt; never fabricate a trade background.", "BS05|BS19", "B9B3-F20"),
    ],
    "B16": [
        ("Confirm a real foreign-invested enterprise termination, completed liquidation and tax payment; personal savings are out of scope.", "BS19|BS18", "B9B3-F12"),
        ("Obtain the liquidation/tax evidence and any SAFE/bank approvals for the RMB belonging to the foreign investor.", "BS19|BS18", "B9B3-F12"),
        ("Ask the bank for the dated FX rate and wire quote within the approved amount.", "BS01|BS02|BS05", "B9B3-F03|B9B3-F04"),
        ("Sign the wire application and retain liquidation, tax, approval and wire records.", "BS05|BS18", "B9B3-F05|B9B3-F06"),
    ],
    "B17": [
        ("Confirm the balance is lawful RMB salary and obtain employment/income and tax evidence.", "BS26|BS18|BS07", "B9B3-F06"),
        ("Ask the sending bank in writing whether it offers personal cross-border RMB salary remittance under 银发〔2018〕3号 and what documents it requires.", "BS26|BS27|BS19", "B9B3-F09|B9B3-F26"),
        ("Obtain the receiving bank's CNY account instructions and its written CNY→USD rate/fee; the PBOC article does not publish these costs.", "BS26|BS27|BS05", "B9B3-F09"),
        ("Only after both quotes, authorise the RMB wire, retain records, and complete U.S. §988/reporting review.", "BS33|BS36|BS47", "B9B3-F07|B9B3-F08"),
    ],
    "B18": [
        ("Stop: no official rule read here permits a foreign passport holder to convert and remit gift or undocumented RMB.", "BS06|BS07|BS19", "B9B3-F18"),
        ("Ask the bank in writing whether any lawful route exists for the exact facts and what document would be required.", "BS07|BS23", "B9B3-F18"),
        ("If the funds are a foreign gift/bequest, obtain U.S. Form 3520 advice before accepting or moving them.", "BS40|BS39|BS47", "B9B3-F18|B9B3-F08"),
        ("Do not use quota splitting, private swaps or false documents; choose a documented lawful route or leave the funds in place.", "BS12|BS23|BS19", "B9B3-F20"),
    ],
    "B19": [
        ("Do not split the purchase across relatives, friends or multiple people.", "BS12|BS24", "B9B3-F16|B9B3-F20"),
        ("Ask the bank which documented single-wire route fits the genuine source of funds.", "BS06|BS07|BS23", "B9B3-F01"),
        ("If past splitting occurred, obtain professional advice before any correction filing; the watch-list lasts current year plus two.", "BS12|BS24|BS19", "B9B3-F20"),
        ("Use only the lawful route with complete source/tax documents and retain the written bank decision.", "BS07|BS18|BS05", "B9B3-F06"),
    ],
    "B20": [
        ("Do not use an app, WeChat contact, broker, underground bank or private offset arrangement.", "BS23|BS19", "B9B3-F20"),
        ("Verify that the counterparty is a qualified bank, licensed exchange institution or authorised agency.", "BS23|BS19", "B9B3-F20"),
        ("Ask the licensed institution for the documented route and written quote; do not provide false purpose documents.", "BS23|BS07|BS05", "B9B3-F20"),
        ("Retain the licence verification, source/tax documents and official receipt.", "BS23|BS18|BS05", "B9B3-F06"),
    ],
    "B21": [
        ("Do not buy crypto, a stablecoin or an RWA token with RMB to move value out of China.", "BS25|BS19", "B9B3-F20"),
        ("Close any proposed fiat/virtual-currency conversion plan; the 2026 PBOC notice repeals the 2021 notice and prohibits the activity.", "BS25", "B9B3-F20"),
        ("Ask a qualified bank for a documented current-account or approval route instead.", "BS06|BS07|BS23", "B9B3-F01"),
        ("Retain the written bank decision and all source/tax documents.", "BS07|BS18|BS05", "B9B3-F06"),
    ],
    "B22": [
        ("Do not prepare false invoices, a false purchase purpose or false source documents.", "BS19|BS23", "B9B3-F20"),
        ("Do not carry undeclared currency/monetary instruments above USD 10,000 into/out of the U.S.; prepare FinCEN Form 105 if required.", "BS49|BS22", "B9B3-F11"),
        ("Ask the bank/tax office for the genuine document list and written decision for the lawful route.", "BS07|BS18|BS23", "B9B3-F06"),
        ("Retain genuine documents, declarations and receipts; never split to avoid review.", "BS12|BS24|BS05", "B9B3-F20"),
    ],
}

COMPLIANCE_STEPS = {
    "C01": ("FBAR", [
        ("For each calendar year, compute the aggregate maximum of all foreign accounts; FBAR is required if it exceeded USD 10,000 at any time.", "BS36|BS47", "B9B3-F08"),
        ("File FinCEN Form 114 electronically through the BSA e-filing system by April 15 (automatic extension to October 15).", "BS36|BS47", "B9B3-F08"),
        ("Keep the filing confirmation and account statements; if a year was missed, review IRM 4.26.16.3.11 and streamlined/delinquent options.", "BS46|BS42|BS43|BS44", "B9B3-F08"),
    ]),
    "C02": ("Form 8938", [
        ("Compare the year-end and anytime maxima against the IRS thresholds for filing status and residence.", "BS35", "B9B3-F08"),
        ("File Form 8938 with the income tax return when required; FBAR is separate and does not replace it.", "BS35|BS36", "B9B3-F08"),
        ("If a prior Form 8938 was missed, use the IRS delinquent international information return procedures with a reasonable-cause statement where appropriate.", "BS45|BS35", "B9B3-F08"),
    ]),
    "C03": ("Form 3520", [
        ("Identify whether any amount received was a gift/bequest from a nonresident alien/foreign estate exceeding USD 100,000 in the year.", "BS40|BS47", "B9B3-F08|B9B3-F18"),
        ("Report it on Form 3520 Part IV and keep donor/estate documents.", "BS40", "B9B3-F08"),
        ("If late, review the §6039F 5%/month (max 25%) penalty and reasonable-cause exception with a professional.", "BS39|BS45", "B9B3-F08"),
    ]),
    "C04": ("26 U.S.C. §988", [
        ("Reconstruct the date and USD basis of each CNY acquisition; IRS yearly averages are labelled scenarios, not an official spot rate.", "BS33|BS34", "B9B3-F07"),
        ("Determine with a professional whether the disposition is a personal transaction and whether §162/§212 expenses remove personal treatment.", "BS33", "B9B3-F07"),
        ("Report ordinary gain/loss where applicable; personal gain of USD 200 or less is excluded under §988(e)(2).", "BS33", "B9B3-F07"),
    ]),
    "C05": ("Foreign tax credit", [
        ("Obtain official PRC tax certificates for income tax actually paid on the same income.", "BS18|BS28", "B9B3-F06"),
        ("Have Form 1116 prepared, applying the foreign tax credit limitations.", "BS41|BS32", "B9B3-F06"),
        ("Retain the treaty and tax records; the saving clause preserves U.S. taxation of citizens.", "BS32|BS41", "B9B3-F06"),
    ]),
    "C06": ("Correction procedures", [
        ("Determine residency, prior filing history, willfulness and whether IRS has contacted you.", "BS42|BS43|BS44|BS45|BS46", "B9B3-F08"),
        ("Choose the published path: SFOP, SDOP, delinquent international information returns, delinquent FBARs, or IRS Criminal Investigation voluntary disclosure.", "BS42|BS43|BS44|BS45|BS46", "B9B3-F08"),
        ("File the required 3 years of returns and 6 years of FBARs, certifications and reasonable-cause statements with professional review.", "BS43|BS44|BS45|BS46", "B9B3-F08"),
    ]),
}


def make_steps() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    n = 0
    for method_id, steps in STEP_TEXT.items():
        for i, (instruction, source_ids, flag_ids) in enumerate(steps, 1):
            n += 1
            rows.append({
                "step_id": f"B9B3-S{n:03d}", "method_id": method_id,
                "step_no": str(i), "instruction": instruction,
                "source_ids": source_ids, "flag_ids": flag_ids,
            })
    for method_id, (label, steps) in COMPLIANCE_STEPS.items():
        for i, (instruction, source_ids, flag_ids) in enumerate(steps, 1):
            n += 1
            rows.append({
                "step_id": f"B9B3-S{n:03d}", "method_id": method_id,
                "step_no": str(i), "instruction": f"{label}: {instruction}",
                "source_ids": source_ids, "flag_ids": flag_ids,
            })
    return rows


STEPS = make_steps()

AUDIT_ROWS = [
    {"audit_id": "B9B3-A01", "area": "Sources", "finding": "Read 50 official PRC/U.S. pages live on 2026-11-11, including the 10:40:02 BOC board and the 2026-11-11 ATM tariff effective that day.", "resolution_or_request": "Recorded verbatim in data/b9b3_sources.csv and the verification log; every cost row links to the exact inputs.", "source_ids": "BS01|BS02|BS03", "flag_ids": "B9B3-F03"},
    {"audit_id": "B9B3-A02", "area": "Inherited e347 cost rows", "finding": "data/e347_costs.csv L08 rows cite the PBOC Beijing URL .../132026/3660457/index.html, which returned HTTP 404 on 2026-11-11.", "resolution_or_request": "B9B3 uses the live PBOC Beijing mirror; requested the e347 owner replace the dead URL. No sibling file was edited.", "source_ids": "BS26|BS27", "flag_ids": "B9B3-F27|B9B3-F28"},
    {"audit_id": "B9B3-A03", "area": "Inherited e347 flag U12", "finding": "U12 said the statutory 50% willful FBAR ceiling had not been read.", "resolution_or_request": "Read 31 U.S.C. §5321(a)(5)(C)-(D) and eCFR 1010.821; published both adjusted amounts and the statutory alternative. Older flag left untouched.", "source_ids": "BS37|BS38|BS46", "flag_ids": "B9B3-F22"},
    {"audit_id": "B9B3-A04", "area": "Inherited e347 flag U06", "finding": "U06 said the U.S.–China treaty text had not been read and priced dividends at statutory 20% only.", "resolution_or_request": "Read Articles 9, 10, 22 and Protocol 1 ¶2 of the IRS treaty PDF; published the 10% cap and separately flagged eligibility under STA 2019 No. 35.", "source_ids": "BS32|BS31", "flag_ids": "B9B3-F23|B9B3-F14"},
    {"audit_id": "B9B3-A05", "area": "Inherited e347 flag U17", "finding": "U17 said the 2025 SAFE Anhui property guide was excerpt-only.", "resolution_or_request": "Read §8 in full from the official PDF; other property taxes remain blank/flagged. Older flag left untouched.", "source_ids": "BS17|BS28", "flag_ids": "B9B3-F24|B9B3-F13"},
    {"audit_id": "B9B3-A06", "area": "Board snapshots", "finding": "e347 uses 2026-11-10 17:39:58; b2d4ff40 quotes 2026-11-11 10:25:02; B9B3 uses 10:40:02.", "resolution_or_request": "Each page is dated. B9B3 did not reprice sibling layers; requested the final integrator select one snapshot.", "source_ids": "BS01|BS02", "flag_ids": "B9B3-F25"},
    {"audit_id": "B9B3-A07", "area": "Cross-border RMB scope", "finding": "m5f19 M15 requires a counterparty and genuine transaction; PBOC Beijing reports a foreign employee's personal RMB salary remittance.", "resolution_or_request": "Published both, left personal cost blank and requested a written bank confirmation before any B11/B17 execution.", "source_ids": "BS26|BS27|BS19", "flag_ids": "B9B3-F26|B9B3-F09"},
    {"audit_id": "B9B3-A08", "area": "OUR surcharge", "finding": "BOC's 2014 personal notice publishes USD 15/25 full-amount surcharges, but no current 2026 personal e-banking applicability was confirmed.", "resolution_or_request": "Left OUR, intermediary and receiving-bank cells blank and flagged; cited the live BOC outbound-wire page explaining intermediary deductions.", "source_ids": "BS04|BS05|BS02", "flag_ids": "B9B3-F04|B9B3-F05"},
    {"audit_id": "B9B3-A09", "area": "U.S. delinquent-FBAR URL", "finding": "The IRS delinquent-FBAR-submission-procedures URL returned HTTP 404.", "resolution_or_request": "Cited the live IRM 4.26.16 and delinquent international information return procedures; did not cite the dead URL as a source.", "source_ids": "BS46|BS45|BS42", "flag_ids": "B9B3-F29"},
    {"audit_id": "B9B3-A10", "area": "FEIE amount", "finding": "An inherited s775 penalty row quotes 2026 FEIE USD 132,900; the IRS FEIE page read here lists figures through 2023 only.", "resolution_or_request": "B9B3 leaves the 2026 FEIE amount blank and flags it; FEIE is not used to shelter savings or currency gain.", "source_ids": "BS48|BS33", "flag_ids": "B9B3-F19"},
    {"audit_id": "B9B3-A11", "area": "COORDINATION.md", "finding": "Rebasing onto origin/main 1638a47 produced literal conflict markers from sibling append-only blocks.", "resolution_or_request": "Resolved by keeping both the 1c55025d/b2d4ff40 blocks and the B9B3 claim verbatim; no session's text was dropped.", "source_ids": "BS01", "flag_ids": "B9B3-F25"},
    {"audit_id": "B9B3-A12", "area": "Dashboard archive", "finding": "scripts/e347_build.py auto-groups new root pages under 'First editorial pages' with an older note.", "resolution_or_request": "Logged B9B3-REQ-01 and F21 instead of editing another session's generator; archive is regenerated only by e347_build.py.", "source_ids": "BS01|BS02", "flag_ids": "B9B3-F21"},
    {"audit_id": "B9B3-A13", "area": "Validators", "finding": "At base 1638a47 all 17 inherited validators passed; verify_m5f19_site.py check J reads the current branch's COORDINATION.md claim.", "resolution_or_request": "Kept every B9B3 file inside the pushed claim and regenerated only dashboard/archive.html.", "source_ids": "BS01", "flag_ids": "B9B3-F21"},
]

SRC = {s["source_id"]: s for s in SOURCES}
SRC_URL = {k: v["url"] for k, v in SRC.items()}
FLAG = {f["flag_id"]: f for f in FLAGS}
METHOD = {m["method_id"]: m for m in METHODS}
SOURCE_IDS = set(SRC)
FLAG_IDS = set(FLAG)
METHOD_IDS = set(METHOD)
OFFICIAL_DOMAINS = (
    "boc.cn", "safe.gov.cn", "pbc.gov.cn", "mofcom.gov.cn", "chinatax.gov.cn",
    "irs.gov", "fincen.gov", "ecfr.gov", "govinfo.gov", "cbp.gov", "gov.cn",
)


def split_pipe(value: str) -> list[str]:
    return [x for x in str(value).split("|") if x]


METHOD_SRC = {mid: split_pipe(m["source_ids"]) for mid, m in METHOD.items()}
METHOD_FLAGS = {mid: split_pipe(m["flag_ids"]) for mid, m in METHOD.items()}


def pipe(values) -> str:
    return "|".join(dict.fromkeys(v for v in values if v))


def as_ids(value) -> list[str]:
    if isinstance(value, str):
        return [x for x in value.split("|") if x]
    return [str(x) for x in value if x]


def official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return url.startswith(("http://", "https://")) and any(
        host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS
    )


def source_urls(ids) -> str:
    return "|".join(SRC_URL[i] for i in dict.fromkeys(as_ids(ids)))


def src_links(ids, max_links: int = 4) -> str:
    clean = [i for i in dict.fromkeys(as_ids(ids)) if i in SRC]
    shown = clean[:max_links]
    out = " ".join(
        f'<a href="{esc(SRC[i]["url"])}" rel="noopener" title="{esc(SRC[i]["title"])}">{i}</a>'
        for i in shown
    )
    if len(clean) > max_links:
        out += f' <span class="note">+{len(clean) - max_links} more on Sources</span>'
    return out


def flag_links(ids, max_links: int = 2) -> str:
    clean = [i for i in dict.fromkeys(as_ids(ids)) if i in FLAG]
    if not clean:
        clean = ["B9B3-F03"]
    shown = clean[:max_links]
    out = " ".join(f'<a href="b9b3-flagged.html#{i}">{i}</a>' for i in shown)
    if len(clean) > max_links:
        out += f' <a href="b9b3-flagged.html">+{len(clean) - max_links}</a>'
    return out


def blank(ids="") -> str:
    return f'<span class="blank">not verified</span> {flag_links(ids)}'


def money(value: str) -> str:
    from decimal import Decimal
    return f"${Decimal(value):,.2f}"


def cny(value: str) -> str:
    from decimal import Decimal
    return f"¥{Decimal(value):,.2f}"


def percent(value: str) -> str:
    from decimal import Decimal
    return f"{Decimal(value):.4f}%"


def usd0(value: str) -> str:
    return f"${int(value):,}"


def csv_text(rows: list[dict[str, str]], fields: list[str]) -> str:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fields})
    return buf.getvalue()


def csv_rows_from_text(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def validate_constants() -> None:
    assert len(SOURCES) == len(SOURCE_IDS) == 50, len(SOURCES)
    assert len(FLAGS) == len(FLAG_IDS) == 29, len(FLAGS)
    assert len(METHODS) == len(METHOD_IDS) == 22, len(METHODS)
    assert len(QUESTIONS) == 30, len(QUESTIONS)
    assert len(PENALTIES) == 30, len(PENALTIES)
    assert len(STEPS) == 106, len(STEPS)
    assert len(AUDIT_ROWS) == 13, len(AUDIT_ROWS)
    for s in SOURCES:
        assert official(s["url"]), s["source_id"]
    for collection, label in ((FLAGS, "flag"), (QUESTIONS, "question"), (METHODS, "method"),
                              (PENALTIES, "penalty"), (STEPS, "step"), (AUDIT_ROWS, "audit")):
        for row in collection:
            for key in ("source_ids", "flag_ids"):
                if key not in row:
                    continue
                for i in split_pipe(row[key]):
                    if key == "source_ids":
                        assert i in SOURCE_IDS, f"{label} {row.get('flag_id', row.get('question_id', row.get('method_id', row.get('penalty_id', row.get('step_id', row.get('audit_id'))))))}: unknown {i}"
                    else:
                        assert i in FLAG_IDS, f"{label}: unknown flag {i}"
    for mid, m in METHOD.items():
        spec = eng.METHOD_SPECS[mid]
        assert m["cost_model"] == spec[0], mid
        assert m["legal_status"] == spec[1], mid
    for mid in eng.METHOD_SPECS:
        assert any(s["method_id"] == mid for s in STEPS), f"missing steps for {mid}"


def table(headers: list[str], rows: list[list[str]], kind: str = "data",
          table_id: str | None = None, tr_attrs: list[str] | None = None) -> str:
    assert all(len(r) == len(headers) for r in rows), "row/header length mismatch"
    ident = f' id="{esc(table_id)}"' if table_id else ""
    out = [f'<div class="scroll"><table{ident} data-kind="{esc(kind)}"><thead><tr>']
    out.extend(f'<th scope="col">{esc(h)}</th>' for h in headers)
    out.append("</tr></thead><tbody>")
    for idx, cells in enumerate(rows):
        attrs = tr_attrs[idx] if tr_attrs and idx < len(tr_attrs) else ""
        if kind == "data":
            assert any('href="http' in c for c in cells), f"data row {idx + 1} has no official source link"
        out.append(f"<tr{attrs}>")
        for h, c in zip(headers, cells):
            assert c and c.strip(), f"empty cell in row {idx + 1}, column {h}"
            out.append(f'<td data-label="{esc(h)}">{c}</td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


NAV = [
    ("dashboard", "Overview"), ("questions", "Decision Q&A"), ("methods", "Methods"),
    ("costs", "$10k–$400k Costs"), ("steps", "Step-by-step"), ("penalties", "Tax & penalties"),
    ("flagged", "Flagged for Review"), ("sources", "Sources"),
]
PAGE_FILE = {k: f"b9b3-{k}.html" for k, _ in NAV}


def render(key: str, title: str, lead: str, body: str) -> str:
    nav = []
    for nav_key, label in NAV:
        cls = ' class="active"' if nav_key == key else ""
        nav.append(f'<a{cls} href="{PAGE_FILE[nav_key]}">{esc(label)}</a>')
    nav.append('<a href="index.html">Main site</a>')
    nav.append('<a href="dashboard/archive.html">Archive</a>')
    nav.append('<a href="COORDINATION.md">Coordination</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generator" content="b9b3-dashboard">
<title>{esc(title)} — B9B3 verified China3 brief</title>
<link rel="stylesheet" href="assets/b9b3.css">
<script src="assets/b9b3.js" defer></script>
</head>
<body id="top">
<header class="masthead">
<div class="wrap">
<p class="eyebrow">China3 · B9B3 · verified {DATE} · BOC board {SNAPSHOT} CST</p>
<h1>{esc(title)}</h1>
<p class="lead">{lead}</p>
<nav class="b9b3-nav" aria-label="B9B3 sections">{''.join(nav)}</nav>
</div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap">
<p><strong>Research only.</strong> Not legal, tax or banking advice. Every published number is recomputed from the dated official inputs on the <a href="b9b3-sources.html">Sources page</a>; unknown values are blank and linked to <a href="b9b3-flagged.html">Flagged for Review</a>.</p>
<p><a href="research/b9b3-executive-summary.md">Markdown executive summary</a> · <a href="research/b9b3-repo-audit.md">Repo audit</a> · <a href="research/b9b3-verification-log.md">Verification log</a> · <a href="#top">Back to top</a></p>
</footer>
</body>
</html>
"""


def page_dashboard(engine_outputs: dict[str, str]) -> str:
    ladder = {int(r["amount_usd"]): r for r in csv_rows_from_text(engine_outputs["data/b9b3_ladder.csv"])}
    key_amounts = [10000, 50000, 100000, 200000, 400000]
    rows = []
    for a in key_amounts:
        r = ladder[a]
        ids = split_pipe(r["source_ids"])
        fl = split_pipe(r["flag_ids"])
        rows.append([
            usd0(str(a)),
            f"<strong>{money(r['best_cny_to_usd_known_cost_usd'])}</strong>",
            percent(r["best_cny_to_usd_pct"]),
            money(r["wire_only_known_cost_usd"]),
            blank(fl),
            src_links(ids),
        ])
    blockers = []
    for f in FLAGS[:4]:
        blockers.append([
            f"<a href=\"b9b3-flagged.html#{f['flag_id']}\">{f['flag_id']}</a>",
            esc(f["item"]), esc(f["why"]), esc(f["what_would_settle_it"]),
            src_links(f["source_ids"]),
        ])
    shortlist = []
    for mid in ("B01", "B03", "B04", "B06"):
        m = METHOD[mid]
        shortlist.append([
            f'<a href="b9b3-methods.html#{mid}">{mid}</a>', esc(m["method"]),
            esc(m["legal_status"]), esc(m["when_to_use"]), esc(m["limit"]),
            src_links(m["source_ids"]), flag_links(m["flag_ids"]),
        ])
    counts = {s: sum(1 for q in QUESTIONS if q["status"] == s) for s in ("Answered", "Partly answered", "Open")}
    body = f"""<section class="banner">
<h2>Read this first</h2>
<p><strong>The lawful route is decided by the source of the CNY, not by the cheapest table row.</strong> This edition computes the published Bank of China bank cost for a single documented CNY→USD wire at the {SNAPSHOT} board. It does <em>not</em> know your source of funds, bank classification, PRC tax position, U.S. currency basis, OUR/intermediary/receiving fees, or prior U.S. filings. Those cells are blank and flagged — never inferred.</p>
</section>
<section class="kpis">
<div class="kpi"><b>{money(ladder[10000]['best_cny_to_usd_known_cost_usd'])}</b><span>known bank cost at $10,000</span></div>
<div class="kpi"><b>{money(ladder[400000]['best_cny_to_usd_known_cost_usd'])}</b><span>known bank cost at $400,000</span></div>
<div class="kpi"><b>{len(METHODS)}</b><span>methods: 17 conditional, 1 unverified, 4 prohibited</span></div>
<div class="kpi"><b>{counts['Open']}</b><span>open decision questions</span></div>
</section>
<section>
<h2>Most important numbers first</h2>
<p class="note">Known PRC bank cost = implied half-spread versus the bid/ask midpoint + BOC 1‰ wire fee (RMB 50–260) + RMB 150 cable, converted at the ask rate. It is a dated benchmark, not an executable quote or an all-in total.</p>
{table(["Amount", "Known bank cost", "% of amount", "Wire-only cost if already FX", "All-in total", "Official sources"], rows)}
<p><a href="b9b3-costs.html">Open the full 40-amount × {len(METHODS)}-method matrix</a> · <a href="b9b3-sources.html">Read the 50 official pages</a></p>
</section>
<section>
<h2>Decision blockers</h2>
{table(["Flag", "Item", "Why it is open", "What would settle it", "Official sources"], blockers)}
<p><a href="b9b3-questions.html">All {len(QUESTIONS)} questions</a> · <a href="b9b3-flagged.html">All {len(FLAGS)} flags</a></p>
</section>
<section>
<h2>Route shortlist (eligibility still required)</h2>
{table(["ID", "Method", "Status", "Use when", "Limit", "Official sources", "Flags"], shortlist)}
</section>
<section>
<h2>What to do next</h2>
<ol class="plain">
<li>Answer the <a href="b9b3-questions.html">P0 questions</a> with documents from the bank, tax office and your prior U.S. returns.</li>
<li>Ask the bank for a written, dated rate and all itemised charges; compare it with the <a href="b9b3-costs.html">published benchmark</a>.</li>
<li>Use the <a href="b9b3-steps.html">step-by-step playbook</a> for the one lawful route that fits the facts; never use a prohibited shortcut.</li>
<li>Complete the <a href="b9b3-penalties.html">U.S. compliance playbooks</a> before or alongside the transfer.</li>
</ol>
</section>"""
    return render("dashboard", "CNY → USD: verified decision brief", "A 2026-11-11 official-source dashboard for a U.S. citizen with CNY in a PRC bank account.", body)


def page_questions() -> str:
    counts = {s: sum(1 for q in QUESTIONS if q["status"] == s) for s in ("Answered", "Partly answered", "Open")}
    rows = []
    for q in QUESTIONS:
        rows.append([
            esc(q["priority"]), esc(q["question"]), f'<span class="pill {"ok" if q["status"] == "Answered" else "warn" if q["status"] == "Partly answered" else "bad"}">{esc(q["status"])}</span>',
            esc(q["known_information"]),
            blank(q["flag_ids"]) if q["status"] == "Open" and not q["missing_information"] else esc(q["missing_information"]),
            esc(q["answer_needed"]), esc(q["how_to_discover"]),
            src_links(q["source_ids"]), flag_links(q["flag_ids"]),
        ])
    body = f"""<section class="banner"><h2>Decision-readiness register</h2><p>{len(QUESTIONS)} questions: {counts['Answered']} answered by an official page, {counts['Partly answered']} partly answered pending your documents, {counts['Open']} open. An open row's blank cell is linked to a flag; every row carries official source links. Concrete discovery steps are procedural suggestions, not sourced facts about your account.</p></section>
<section><h2>Stage 1–5 questions</h2>{table(["Priority", "Question", "Status", "Known information", "Missing information", "Answer needed", "How to discover", "Official sources", "Flags"], rows)}</section>"""
    return render("questions", "Questions to settle before any decision", "Known facts, missing facts, the answer each question must produce, and exactly how to discover it.", body)


def page_methods() -> str:
    rows = []
    attrs = []
    for m in METHODS:
        rows.append([
            esc(m["method"]), esc(m["legal_status"]), esc(m["who"]), esc(m["when_to_use"]),
            esc(m["documents"]), esc(m["limit"]), esc(m["advantages"]), esc(m["drawbacks"]),
            esc(m["conversion_tax_notes"]), esc(m["cost_model"]),
            src_links(m["source_ids"]), flag_links(m["flag_ids"]),
        ])
        attrs.append(f' id="{m["method_id"]}"')
    body = f"""<section class="banner"><h2>{len(METHODS)} methods</h2><p>17 conditional lawful routes, 1 unverified/no-route case and 4 prohibited categories. Each has its own <a href="b9b3-steps.html">execution playbook</a>. Prohibited rows give no execution steps and no cost; they explain the official prohibition instead.</p></section>
<section>{table(["Method", "Status", "Who", "Use when", "Documents", "Limit", "Pros", "Cons", "Tax/conversion notes", "Cost model", "Official sources", "Flags"], rows, tr_attrs=attrs)}</section>"""
    return render("methods", "CNY → USD conversion methods", "Eligibility, documents, limits, pros/cons and tax/conversion notes for every sourced route.", body)


def page_costs(engine_outputs: dict[str, str]) -> str:
    ladder = {int(r["amount_usd"]): r for r in csv_rows_from_text(engine_outputs["data/b9b3_ladder.csv"])}
    costs = csv_rows_from_text(engine_outputs["data/b9b3_method_costs.csv"])
    key_amounts = [10000, 50000, 100000, 200000, 400000]
    summary = []
    for a in key_amounts:
        r = ladder[a]
        summary.append([
            usd0(str(a)), f"<strong>{money(r['best_cny_to_usd_known_cost_usd'])}</strong>",
            percent(r["best_cny_to_usd_pct"]), money(r["wire_only_known_cost_usd"]),
            blank(r["flag_ids"]), src_links(r["source_ids"]),
        ])
    rows, attrs = [], []
    for r in costs:
        fl = r["flag_ids"]
        ids = r["source_ids"]
        rows.append([
            money(r["known_bank_cost_usd"]) if r["known_bank_cost_usd"] else blank(fl),
            usd0(r["amount_usd"]),
            f'<a href="b9b3-methods.html#{r["method_id"]}">{r["method_id"]}</a> {esc(METHOD[r["method_id"]]["method"])}',
            esc(r["status"]),
            percent(r["known_bank_cost_pct"]) if r["known_bank_cost_pct"] else blank(fl),
            money(r["fx_spread_usd"]) if r["fx_spread_usd"] else blank(fl),
            money(r["bank_wire_and_cable_usd"]) if r["bank_wire_and_cable_usd"] else blank(fl),
            (r["wire_count"] + " / " + r["calendar_years"]) if r["wire_count"] else blank(fl),
            blank(fl),
            src_links(ids), flag_links(fl),
        ])
        attrs.append(f' class="cost-row" data-method="{r["method_id"]}" data-amount="{r["amount_usd"]}" data-status="{r["status"]}"')
    options = "".join(f'<option value="{mid}">{mid} — {esc(m["method"][:70])}</option>' for mid, m in METHOD.items())
    body = f"""<section class="banner"><h2>Published bank-cost benchmark only</h2><p>These are exact Fraction computations from the {SNAPSHOT} BOC board and the personal wire tariff. OUR/intermediary/receiving fees, PRC tax, U.S. §988 gain and every all-in total are blank and flagged. A blank cell is <strong>not zero</strong>.</p></section>
<section><h2>Key amounts (single documented B01 wire)</h2>{table(["Amount", "Known bank cost", "% of amount", "Wire-only cost if already FX", "All-in total", "Official sources"], summary)}</section>
<section><h2>Full matrix: {len(costs)} rows</h2>
<div class="filters"><label>Method <select id="method-filter"><option value="all">All {len(METHODS)} methods</option>{options}</select></label>
<label>Status <select id="status-filter"><option value="all">All statuses</option><option value="conditional">Conditional</option><option value="unverified">Unverified</option><option value="prohibited">Prohibited</option></select></label>
<label>Search <input id="cost-search" type="search" placeholder="amount or method id"></label>
<span id="visible-count" class="note"></span></div>
{table(["Known cost", "Amount", "Method", "Status", "%", "Spread", "Wire/cable", "Wires / years", "All-in total", "Official sources", "Flags"], rows, table_id="cost-table", tr_attrs=attrs)}
<details><summary>What the blank columns mean</summary><p>{esc(eng.LIMITS['fx_wire'])} {esc(eng.LIMITS['blank'])} See <a href="b9b3-flagged.html">Flagged for Review</a>.</p></details>
</section>"""
    return render("costs", "$10,000–$400,000 cost matrix", "40 USD amounts in $10,000 steps × every sourced method, with the most important number first.", body)


def page_steps() -> str:
    by_method: dict[str, list[dict[str, str]]] = {}
    for s in STEPS:
        by_method.setdefault(s["method_id"], []).append(s)
    parts = []
    for mid in sorted(set(by_method) | set(eng.METHOD_SPECS)):
        if mid in METHOD:
            heading = f'{mid} — {esc(METHOD[mid]["method"])}'
            sub = f'<a href="b9b3-methods.html#{mid}">Method detail</a> · <a href="b9b3-costs.html">Cost rows</a>'
        else:
            heading = esc(COMPLIANCE_STEPS[mid][0])
            sub = '<a href="b9b3-penalties.html">Tax & penalties</a>'
        rows = []
        for s in by_method.get(mid, []):
            rows.append([
                esc(s["step_no"]), esc(s["instruction"]), src_links(s["source_ids"]),
                flag_links(s["flag_ids"]) if s["flag_ids"] else f'<span class="pill ok">No open flag</span> {src_links(s["source_ids"])}',
            ])
        parts.append(f'<section><h2 id="{mid}">{heading}</h2><p class="note">{sub}</p>{table(["Step", "Instruction", "Official sources", "Flags"], rows)}</section>')
    body = f"""<section class="banner"><h2>Exact playbooks</h2><p>{len(STEPS)} sourced steps cover every method and six U.S. compliance playbooks. Prohibited methods receive safe refusal and rerouting steps, never execution instructions. Discovery suggestions are procedural; the official links establish the underlying rule.</p></section>
{''.join(parts)}"""
    return render("steps", "Step-by-step execution playbooks", "Ordered, source-linked instructions for every lawful method and U.S. compliance path.", body)


def page_penalties() -> str:
    rows = []
    for p in PENALTIES:
        rate = esc(p["rate_or_amount"]) if p["rate_or_amount"] else blank(p["flag_ids"])
        rows.append([
            esc(p["jurisdiction"]), esc(p["rule"]), esc(p["trigger"]), rate,
            esc(p["conditions"]), src_links(p["source_ids"]),
            flag_links(p["flag_ids"]) if p["flag_ids"] else '<span class="pill ok">No open flag</span>',
        ])
    playbook = []
    for cid, (label, steps) in COMPLIANCE_STEPS.items():
        ids = pipe(s[1] for s in steps)
        fl = pipe(s[2] for s in steps)
        playbook.append([
            f'<a href="b9b3-steps.html#{cid}">{esc(label)}</a>',
            esc(steps[0][0]), esc(steps[1][0]), esc(steps[2][0]),
            src_links(ids), flag_links(fl),
        ])
    body = f"""<section class="banner"><h2>PRC and U.S. tax/penalty breakdown</h2><p>{len(PENALTIES)} rules, each linked to the official text. Blank amounts are deliberate: no current 2026 OUR fee, FEIE amount, intermediary fee, PRC tax amount or U.S. §988 gain can be computed from the brief alone.</p></section>
<section><h2>Rules</h2>{table(["Jurisdiction", "Rule", "Trigger", "Rate / amount", "Conditions", "Official sources", "Flags"], rows)}</section>
<section><h2>U.S. compliance playbooks</h2>{table(["Playbook", "Step 1", "Step 2", "Step 3", "Official sources", "Flags"], playbook)}</section>"""
    return render("penalties", "Tax, penalties and reporting", "Deep PRC/U.S. breakdown with official links, plus the compliance steps that can dominate the real cost.", body)


def page_flagged() -> str:
    rows, attrs = [], []
    for f in FLAGS:
        rows.append([
            esc(f["flag_id"]), esc(f["severity"]), esc(f["item"]), esc(f["why"]),
            esc(f["what_would_settle_it"]), src_links(f["source_ids"]),
            esc(f["affected_pages"]),
        ])
        attrs.append(f' id="{f["flag_id"]}"')
    body = f"""<section class="banner"><h2>Flagged for Review</h2><p>{len(FLAGS)} irregularities, unverified values and inherited-repo discrepancies. Every blank cell in the cost, question, method and penalty tables links here. These flags do not block merging a structurally sound site; they prevent unverified numbers from being published.</p></section>
<section>{table(["Flag", "Severity", "Item", "Why it is unverified", "What would settle it", "Official sources", "Affected pages"], rows, tr_attrs=attrs)}</section>"""
    return render("flagged", "Flagged for Review", "Unverified values and repo irregularities, kept visible and source-linked rather than guessed.", body)


def page_sources() -> str:
    rows, attrs = [], []
    for s in SOURCES:
        rows.append([
            esc(s["source_id"]), esc(s["issuer"]),
            f'<a href="{esc(s["url"])}" rel="noopener">{esc(s["title"])}</a>',
            esc(s["read_on"]), esc(s["how_read"]), esc(s["verbatim_or_extract"]), esc(s["supports"]),
        ])
        attrs.append(f' id="{s["source_id"]}"')
    body = f"""<section class="banner"><h2>Primary sources only</h2><p>{len(SOURCES)} government, regulator, central-bank and Bank of China pages read live on {DATE}. No law-firm articles, forums or news sites. Direct links are on every row of every B9B3 table.</p></section>
<section>{table(["ID", "Issuer", "Document (direct link)", "Read on", "How read", "Verbatim / extract", "Supports"], rows, tr_attrs=attrs)}</section>"""
    return render("sources", "Official source register", "The exact primary pages behind every B9B3 figure, threshold and execution step.", body)


def md_link(ids) -> str:
    return " ".join(f"[{i}]({SRC[i]['url']})" for i in dict.fromkeys(as_ids(ids)))


def markdown_outputs(engine_outputs: dict[str, str]) -> dict[str, str]:
    ladder = {int(r["amount_usd"]): r for r in csv_rows_from_text(engine_outputs["data/b9b3_ladder.csv"])}
    source_lines = "\n".join(
        f"- **{s['source_id']}** — [{s['title']}]({s['url']}) ({s['issuer']}, {s['read_on']}, {s['how_read']}): {s['verbatim_or_extract']}"
        for s in SOURCES
    )
    log = f"""# B9B3 verification log — {DATE}

All {len(SOURCES)} URLs below were fetched and read live on {DATE}. Only primary PRC and U.S. government/regulator/bank pages are used. Fetched page text is not persisted separately; the exact load-bearing extracts are recorded in `data/b9b3_sources.csv` and below.

## Board, tariff and arithmetic

- BOC board {SNAPSHOT}: per 100 USD, Buying 666.31, Cash Buying 666.31, Selling 669.12, Cash Selling 669.12, Middle 671.91. {md_link('BS01')}
- Customer buys USD at 6.6912 CNY/USD; bid/ask midpoint is (6.6631 + 6.6912)/2 = 6.67715; implied half-spread = 0.01405 CNY/USD = 0.209977% of the selling rate. The displayed 671.91 "Middle Rate" is **not** the bid/ask midpoint and is not used as fair value. {md_link('BS01')}
- Personal e-banking wire: 1‰, RMB 50 minimum / RMB 260 maximum, plus RMB 150 cable outside HK/Macao/Taiwan; local/agreed/promotional differences are allowed. {md_link('BS02')}
- At $10,000: RMB 66,912.00 needed; wire + cable = RMB 216.912 = $32.42; half-spread = RMB 140.50 = $21.00; exact known bank cost = $53.42 (0.5342%), computed from Fractions before rounding rather than by adding rounded components. At $400,000: RMB 2,676,480.00; wire + cable plateaus at RMB 410.00 = $61.27; half-spread = RMB 5,620.00 = $839.91; exact known bank cost = $901.18 (0.2253%). {md_link('BS01|BS02')}
- All-in totals, OUR/intermediary/receiving fees, PRC tax and U.S. §988 gain are blank and flagged. {md_link('BS04|BS05|BS33|BS18')}

## Dead / moved URLs found while auditing

- `http://beijing.pbc.gov.cn/beijing/132026/3660457/index.html` returned HTTP 404; live mirror: {md_link('BS26')}. PBOC chronicle: {md_link('BS27')}.
- `https://www.irs.gov/individuals/international-taxpayers/delinquent-fbar-submission-procedures` returned HTTP 404; live IRM: {md_link('BS46')}; delinquent international information returns: {md_link('BS45')}.

## Source-by-source log

{source_lines}
"""
    summary = f"""# B9B3 executive summary — {DATE}

**Question:** how can a U.S. citizen with CNY in a PRC bank account convert and transfer it to USD with minimal lawful tax/conversion penalties?

1. **Eligibility before price.** The source of the CNY decides the lawful route. SAFE Art. 59 permits a foreign individual to buy FX against valid ID, amount-bearing source-of-funds documents and tax evidence; Art. 65 permits the FX-account outward wire. {md_link('BS06|BS07|BS13|BS18')}
2. **No conversion tax was found.** Decree 532 Art. 5 does not restrict genuine current-account transfers; no official page read imposes a tax on the act of converting one's own CNY. PRC IIT, if any, attaches to the underlying income/gain (3%-45% wages, 20% flat categories), and tax evidence is required for large payments. {md_link('BS19|BS28|BS18')}
3. **The USD 50,000 figure is not a hard cap and not a U.S.-passport entitlement.** It is an annual convenience/documentation threshold; for FX purchase by an 境外个人, only PRC Foreign Permanent Resident ID holders get it on ID alone. {md_link('BS08|BS09|BS07|BS12')}
4. **Known bank cost at the {SNAPSHOT} board:** $10,000 → **{money(ladder[10000]['best_cny_to_usd_known_cost_usd'])}** ({percent(ladder[10000]['best_cny_to_usd_pct'])}); $400,000 → **{money(ladder[400000]['best_cny_to_usd_known_cost_usd'])}** ({percent(ladder[400000]['best_cny_to_usd_pct'])}). This is the published single-wire BOC benchmark only, not an executable quote or all-in total. {md_link('BS01|BS02|BS05')}
5. **U.S. side can dominate.** Worldwide income, FBAR >$10,000, Form 8938, Form 3520, §988 ordinary currency gain/loss, and prior non-willful correction procedures all need review; PRC income tax may be creditable. {md_link('BS47|BS36|BS35|BS40|BS33|BS42|BS41|BS32')}
6. **Prohibited shortcuts.** Quota splitting, private/app/underground FX swaps, crypto/stablecoin/RWA conversion, false documents and undeclared excess cash are prohibited; Decree 532 fines reach 30% (30%-100% if serious). {md_link('BS12|BS19|BS23|BS24|BS25|BS49')}
7. **What remains unknown.** Source of funds, bank account classification, "considerable taxes", CNY acquisition basis, OUR/intermediary/receiving fees, prior U.S. filings and branch quote are blank and published on [Flagged for Review](../b9b3-flagged.html). See [Decision Q&A](../b9b3-questions.html) and the [repo audit](b9b3-repo-audit.md).

This is research, not legal, tax or banking advice.
"""
    qrows = [q for q in QUESTIONS if q["priority"] in ("P0", "P1")][:12]
    qlines = "\n".join(
        f"| {q['question_id']} | {q['priority']} | {q['question']} | {q['status']} | {q['missing_information']} | {q['how_to_discover']} | {md_link(q['source_ids'])} |"
        for q in qrows
    )
    questions = f"""# B9B3 decision-readiness questions — {DATE}

{len(QUESTIONS)} questions are published in `data/b9b3_questions.csv` and [b9b3-questions.html](../b9b3-questions.html): {sum(1 for q in QUESTIONS if q['status']=='Answered')} answered, {sum(1 for q in QUESTIONS if q['status']=='Partly answered')} partly answered, {sum(1 for q in QUESTIONS if q['status']=='Open')} open. Every open or partly answered row has a concrete discovery step and an official source link.

## Highest-priority questions

| ID | Priority | Question | Status | Missing information | How to discover | Official sources |
|---|---|---|---|---|---|---|
{qlines}

The P0 answers must exist before any "least-cost" ranking is defensible. All-in totals stay blank until the bank, tax office, U.S. tax basis and prior-filing facts are known.
"""
    method_lines = "\n".join(
        f"| {m['method_id']} | {m['legal_status']} | {m['method']} | {m['limit']} | {m['cost_model']} | {md_link(m['source_ids'])} |"
        for m in METHODS
    )
    penalty_lines = "\n".join(
        f"| {p['penalty_id']} | {p['jurisdiction']} | {p['rule']} | {p['rate_or_amount'] or 'BLANK / FLAGGED'} | {md_link(p['source_ids'])} |"
        for p in PENALTIES
    )
    methods_md = f"""# B9B3 methods, taxes and penalties — {DATE}

## Methods ({len(METHODS)})

| ID | Status | Method | Limit | Cost model | Official sources |
|---|---|---|---|---|---|
{method_lines}

Detailed pros/cons, documents and step-by-step playbooks: [b9b3-methods.html](../b9b3-methods.html), [b9b3-steps.html](../b9b3-steps.html), [b9b3-costs.html](../b9b3-costs.html).

## Tax and penalty rules ({len(PENALTIES)})

| ID | Jurisdiction | Rule | Rate / amount | Official sources |
|---|---|---|---|---|
{penalty_lines}

Blank rate/amount cells are deliberate and link to [Flagged for Review](../b9b3-flagged.html). No current 2026 OUR fee, FEIE amount, intermediary/receiving fee, PRC tax amount or U.S. §988 gain is inferred.
"""
    audit_lines = "\n".join(
        f"| {a['audit_id']} | {a['area']} | {a['finding']} | {a['resolution_or_request']} | {md_link(a['source_ids'])} |"
        for a in AUDIT_ROWS
    )
    audit = f"""# B9B3 line-by-line repository audit — {DATE}

This session re-read the inherited registers (`QNA.md`, `data/e347_sources.csv`, `data/e347_methods.csv`, `data/e347_costs.csv`, `data/e347_flags.csv`, `data/m5f19_methods.csv`, `data/s775_penalties.csv`, all 17 inherited validators and the 2026-11-11 `COORDINATION.md` claims), then checked each load-bearing URL live. No sibling-owned file was edited.

| ID | Area | Finding | Resolution / request | Official sources |
|---|---|---|---|---|
{audit_lines}

## Verification gates

- `python3 scripts/b9b3_engine.py` writes {len(eng.AMOUNTS) * len(eng.METHOD_SPECS)} exact-Fraction cost rows and {len(eng.AMOUNTS)} ladder rows.
- `python3 scripts/build_b9b3_site.py --check` is byte-idempotent for all claimed CSV, Markdown, HTML, CSS and JS outputs.
- `python3 scripts/verify_b9b3_site.py` independently recomputes every cost row from `Fraction`s without importing the engine, checks official URLs on every `<tr>`, blank-cell flag links, internal links/anchors, conflict markers and build idempotency.
- `python3 scripts/e347_build.py` regenerates `dashboard/archive.html`; `python3 scripts/e347_build.py --check` and all 17 inherited validators are run before the PR.

## Cross-scope requests

- **B9B3-REQ-01:** add one additive link on `index.html`/`README.md` to `b9b3-dashboard.html` and, if convenient, a dedicated B9B3 group in the archive generator. Not edited here because those files are owned by active sibling sessions.
"""
    return {
        "research/b9b3-verification-log.md": log,
        "research/b9b3-executive-summary.md": summary,
        "research/b9b3-decision-questions.md": questions,
        "research/b9b3-methods-and-penalties.md": methods_md,
        "research/b9b3-repo-audit.md": audit,
    }

CSS = """/* B9B3 mobile-first dashboard */
:root{--ink:#10233b;--muted:#53657a;--bg:#f4f7fb;--card:#fff;--line:#d9e3ee;--blue:#075ea4;--blue2:#eaf3fc;--amber:#a45a00;--red:#9b1c1c;--green:#176b45;--radius:14px}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--blue);text-decoration-thickness:1px;text-underline-offset:2px}
a:hover{text-decoration-thickness:2px}
.wrap{max-width:1180px;margin:0 auto;padding:18px}
.masthead{background:linear-gradient(135deg,#082b4d,#0b5a91);color:#fff;padding:26px 0 18px}
.masthead a{color:#d8ecff}
.masthead h1{font-size:clamp(1.7rem,4.2vw,2.8rem);line-height:1.12;margin:.15em 0 .3em}
.eyebrow{font-size:.82rem;letter-spacing:.05em;text-transform:uppercase;opacity:.85;margin:0}
.lead{font-size:1.05rem;max-width:80ch;margin:0 0 16px;color:#e7f2ff}
.b9b3-nav{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.b9b3-nav a{display:inline-block;padding:7px 10px;border:1px solid rgba(255,255,255,.38);border-radius:999px;background:rgba(255,255,255,.08);font-size:.9rem}
.b9b3-nav a.active{background:#fff;color:#082b4d;border-color:#fff;font-weight:700}
main section,footer p{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px;margin:16px 0;box-shadow:0 1px 2px rgba(16,35,59,.04)}
footer{background:transparent}footer p{font-size:.9rem;color:var(--muted)}
h2{font-size:1.3rem;line-height:1.25;margin:0 0 10px}h3{margin-top:18px}
.banner{border-left:6px solid var(--blue);background:var(--blue2)}
.note{color:var(--muted);font-size:.9rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0}
.kpi{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px}
.kpi b{font-size:1.55rem;color:var(--blue)}.kpi span{font-size:.86rem;color:var(--muted)}
.pill{display:inline-block;border-radius:999px;padding:2px 9px;font-size:.78rem;font-weight:700;white-space:nowrap}
.pill.ok{background:#e4f6ec;color:var(--green)}.pill.warn{background:#fff1d6;color:var(--amber)}.pill.bad{background:#fde5e5;color:var(--red)}
.blank{display:inline-block;background:#fff1d6;color:var(--amber);border-radius:6px;padding:1px 7px;font-weight:700;font-size:.84rem}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:.9rem;min-width:720px}
th,td{padding:10px 11px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
thead th{background:#eef4fa;position:sticky;top:0;z-index:1;font-size:.82rem;text-transform:uppercase;letter-spacing:.02em}
tbody tr:nth-child(even){background:#fbfdff}tbody tr:hover{background:#f0f7ff}
td a{white-space:nowrap}
.filters{display:flex;flex-wrap:wrap;gap:10px;align-items:end;margin:12px 0}
.filters label{display:flex;flex-direction:column;font-size:.82rem;color:var(--muted);gap:4px}
.filters select,.filters input{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;color:var(--ink);max-width:100%}
ol.plain{padding-left:1.3rem}ol.plain li{margin:8px 0}
details{margin-top:12px;background:#f8fbff;border:1px solid var(--line);border-radius:10px;padding:10px}
summary{cursor:pointer;font-weight:700}
code{background:#eef3f8;padding:1px 5px;border-radius:4px}
@media(max-width:760px){
  .wrap{padding:12px}.masthead{padding:18px 0 14px}
  main section{padding:14px;margin:12px 0}
  table{min-width:0;display:block}thead{display:none}tbody,tr,td{display:block;width:100%}
  tbody tr{border:1px solid var(--line);border-radius:10px;margin:10px 0;padding:6px;background:#fff}
  td{border:0;border-bottom:1px dashed var(--line);padding:8px 8px 8px 42%;position:relative;min-height:34px}
  td:last-child{border-bottom:0}
  td[data-label]::before{content:attr(data-label);position:absolute;left:8px;top:8px;width:36%;font-size:.74rem;font-weight:700;text-transform:uppercase;letter-spacing:.02em;color:var(--muted);white-space:normal}
  .filters{flex-direction:column;align-items:stretch}.filters label{width:100%}
}
"""

JS = """// B9B3 cost-table filters. No network calls; all data is already in the page.
(function(){
  'use strict';
  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded',fn); }
  ready(function(){
    var table=document.getElementById('cost-table');
    if(!table) return;
    var rows=Array.prototype.slice.call(table.querySelectorAll('tbody tr.cost-row'));
    var method=document.getElementById('method-filter');
    var status=document.getElementById('status-filter');
    var search=document.getElementById('cost-search');
    var count=document.getElementById('visible-count');
    function apply(){
      var m=method?method.value:'all', s=status?status.value:'all';
      var q=search?(search.value||'').trim().toLowerCase():'';
      var n=0;
      rows.forEach(function(r){
        var okM=m==='all'||r.getAttribute('data-method')===m;
        var okS=s==='all'||r.getAttribute('data-status')===s;
        var text=(r.textContent||'').toLowerCase();
        var okQ=!q||text.indexOf(q)!==-1;
        var show=okM&&okS&&okQ;
        r.style.display=show?'':'none';
        if(show) n++;
      });
      if(count) count.textContent=n+' of '+rows.length+' rows shown';
    }
    [method,status].forEach(function(el){ if(el) el.addEventListener('change',apply); });
    if(search) search.addEventListener('input',apply);
    apply();
  });
})();
"""


def with_urls(row: dict[str, str]) -> dict[str, str]:
    out = dict(row)
    out["source_urls"] = source_urls(row.get("source_ids", ""))
    return out


def csv_outputs(engine_outputs: dict[str, str]) -> dict[str, str]:
    specs = [
        ("data/b9b3_sources.csv", SOURCES, ["source_id", "issuer", "title", "url", "read_on", "how_read", "verbatim_or_extract", "supports"]),
        ("data/b9b3_questions.csv", QUESTIONS, ["question_id", "stage", "priority", "question", "status", "known_information", "missing_information", "answer_needed", "how_to_discover", "source_ids", "source_urls", "flag_ids"]),
        ("data/b9b3_methods.csv", METHODS, ["method_id", "method", "legal_status", "who", "when_to_use", "documents", "limit", "advantages", "drawbacks", "conversion_tax_notes", "cost_model", "source_ids", "source_urls", "flag_ids"]),
        ("data/b9b3_penalties.csv", PENALTIES, ["penalty_id", "jurisdiction", "rule", "trigger", "rate_or_amount", "conditions", "source_ids", "source_urls", "flag_ids"]),
        ("data/b9b3_steps.csv", STEPS, ["step_id", "method_id", "step_no", "instruction", "source_ids", "source_urls", "flag_ids"]),
        ("data/b9b3_flags.csv", FLAGS, ["flag_id", "severity", "item", "why", "what_would_settle_it", "source_ids", "source_urls", "affected_pages"]),
    ]
    out: dict[str, str] = {}
    for rel, rows, fields in specs:
        enriched = [with_urls(r) for r in rows] if "source_urls" in fields else rows
        out[rel] = csv_text(enriched, fields)
    out.update(engine_outputs)
    return out


def html_outputs(engine_outputs: dict[str, str]) -> dict[str, str]:
    return {
        PAGE_FILE["dashboard"]: page_dashboard(engine_outputs),
        PAGE_FILE["questions"]: page_questions(),
        PAGE_FILE["methods"]: page_methods(),
        PAGE_FILE["costs"]: page_costs(engine_outputs),
        PAGE_FILE["steps"]: page_steps(),
        PAGE_FILE["penalties"]: page_penalties(),
        PAGE_FILE["flagged"]: page_flagged(),
        PAGE_FILE["sources"]: page_sources(),
    }


def outputs() -> dict[str, str]:
    validate_constants()
    engine_outputs = eng.cost_outputs(SRC_URL, METHOD_SRC, METHOD_FLAGS)
    out: dict[str, str] = {}
    out.update(csv_outputs(engine_outputs))
    out.update(html_outputs(engine_outputs))
    out.update(markdown_outputs(engine_outputs))
    out["assets/b9b3.css"] = CSS
    out["assets/b9b3.js"] = JS
    conflict = re.compile(r"^(<<<<<<<|=======|>>>>>>>)", re.M)
    for rel, text in out.items():
        assert not conflict.search(text), f"conflict marker in generated {rel}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if any generated file is stale; write nothing")
    args = ap.parse_args()
    generated = outputs()
    stale: list[str] = []
    for rel, text in generated.items():
        path = ROOT / rel
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(rel)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check:
        if stale:
            print("STALE: " + ", ".join(stale) + " — run python3 scripts/build_b9b3_site.py")
            return 1
        print(f"OK — B9B3 build is byte-idempotent: {len(generated)} generated files, 0 stale.")
        return 0
    print(f"B9B3 build: {len(generated)} files, {len(stale)} changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
