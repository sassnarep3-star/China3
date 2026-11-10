#!/usr/bin/env python3
"""Generate the S775 namespaced data files:

- data/s775_sources.csv / .json         official primary-source register
- data/s775_methods.csv                24 CNY->USD routes, pros/cons/status
- data/s775_penalties.csv              China + US tax/penalty decomposition
- data/s775_cost_10k_400k.csv         40-row $10,000-$400,000 cost ladder
- data/s775_steps.csv                  numbered step-by-step playbooks
- data/s775_method_summary.csv         per-method cost summary at 3 amounts
- data/s775_flags.csv                  flagged / unverified register

Every figure is either (a) read from an official source today (2026-11-10)
or (b) derived by arithmetic on those figures and labelled as derived.
Anything that cannot be confirmed from an official source is left blank and
flagged UNVERIFIED - never inferred.
"""

import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

D = Decimal


def q2(x: Decimal) -> Decimal:
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def wcsv(name: str, header: list, rows: list) -> None:
    DATA.mkdir(exist_ok=True)
    with (DATA / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote data/{name} ({len(rows)} rows)")


# =====================================================================
# 1. OFFICIAL SOURCE REGISTER
# =====================================================================
# (id, institution, title, what_it_establishes, url, fetched_utc, verdict)
SOURCES = [
    ("S01", "Bank of China", "中国银行外汇牌价 (BOC FX board), USD row",
     "Spot selling (ask) 6.6903 / buying (bid) 6.6622 / parity (中行折算价) 6.7188 CNY per USD; cash bid 6.6622; board stamp 2026-11-10 07:32:39",
     "https://www.boc.cn/sourcedb/whpj/", "2026-11-10T07:32:39Z", "verified"),
    ("S02", "China Foreign Exchange Trade System", "CFETS central parity (人民币汇率中间价)",
     "Parity 6.7188 CNY per USD, published 2026-11-09 09:15 - cross-checks the BOC parity column",
     "https://www.chinamoney.com.cn/chinese/bkccpr/", "2026-11-10T07:30:00Z", "verified"),
    ("S03", "Bank of China", "中国银行电子银行个人服务转账汇款费率表 (personal e-banking transfer tariff), effective 2014-11-01",
     "Cross-border T/T 1‰ of amount (min ¥50, max ¥260) + cable ¥150 (HK/MO/TW ¥80)",
     "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "2026-11-10T07:40:00Z", "verified"),
    ("S04", "Bank of China", "关于调整部分贸易金融服务项目的公告 (personal OUR tariff, code 210104021, effective 2015-04-01)",
     "USD OUR (full-amount-received) surcharge: US$15 per wire to BOC New York account / US$25 per wire to other US banks",
     "https://www.boc.cn/pbservice/bi2/201412/t20141231_4404048.html", "2026-11-10T07:45:00Z", "verified"),
    ("S05", "Bank of China", "中国银行公司金融费率表 (corporate T/T tariff, code 220304004)",
     "Corporate T/T 1‰ (¥50-¥1,000) + cable; GPI 1.2‰ (¥200-¥1,000)",
     "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html", "2026-11-10T07:50:00Z", "verified"),
    ("S06", "Bank of China", "中国银行个人服务价目表 - 境外ATM取款 (overseas ATM tariff, code 210108014, effective 2026-11-11)",
     "UnionPay ATM: ¥12 + 1% (max ¥112/tx); Mastercard/Visa rises 0.5% -> 2.5% ($3-$40) from 2026-11-11",
     "https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html", "2026-11-10T07:55:00Z", "verified"),
    ("S07", "Bank of China USA", "BOC USA personal remittance & exchange page",
     "US$0 incoming personal wire fee (BOC USA receiving account)",
     "https://www.bocusa.com/personal-banking/remittance-exchange", "2026-11-10T08:00:00Z", "verified"),
    ("S08", "Bank of China USA", "BOC USA Service Fee Schedule (effective 2024-02-12)",
     "Personal fee schedule PDF used for cross-checking BOC USA charges",
     "https://www.bocusa.com/sites/default/files/2024-01/Service%20Fee%20Schedule%20(Effective%20on%2002.12.2024)_0.pdf", "2026-11-10T08:05:00Z", "verified"),
    ("S09", "Bank of China", "中国银行电子银行优惠 (bi31) - mobile fee waiver",
     "2025 mobile transfer fee waiver campaign ended 2025-12-31",
     "https://www.boc.cn/ebanking/bi3/bi31/", "2026-11-10T08:10:00Z", "verified"),
    ("S10", "SAFE (国家外汇管理局)", "2022年外汇业务政策释疑（八） - 年度便利化额度",
     "Individual settlement/purchase convenience amount US$50,000 per person per year; official text states it is NOT a hard limit - above it, transaction documents are required",
     "https://www.safe.gov.cn/ningxia/2022/0929/1997.html", "2026-11-10T08:15:00Z", "verified"),
    ("S11", "SAFE Tianjin", "境外个人经常项目外汇业务 (foreign permanent resident ID)",
     "Foreign permanent resident ID holders get the purchase convenience amount on documented current-account business",
     "https://www.safe.gov.cn/tianjin/2025/1113/2926.html", "2026-11-10T08:20:00Z", "verified"),
    ("S12", "SAFE Tianjin", "外汇业务问答案例 - 关注名单",
     "Watchlist: current year + 2 following years of transaction convenience restrictions",
     "https://www.safe.gov.cn/tianjin/2025/0613/2811.html", "2026-11-10T08:25:00Z", "verified"),
    ("S13", "SAFE Tianjin", "2024年外汇管理互联网信息——个人外汇（三）",
     "汇发〔2020〕14号 art. 64 — SCOPE: 境内个人 (DOMESTIC individuals) remitting FX abroad for current-account expenditure FROM AN FX ACCOUNT: same-day cumulative ≤US$50,000 (inclusive) on the person's valid ID alone; above that, ID + transaction-amount documents. Remitting FOREIGN CURRENCY CASH: ≤US$10,000/day on ID; above that, ID + customs-stamped declaration or original bank cash-withdrawal slip + transaction documents. Not a rule for 境外个人 (foreign individuals) — see S52",
     "https://www.safe.gov.cn/tianjin/2024/0229/2402.html", "2026-11-10T09:52:00Z", "verified"),
    ("S52", "SAFE Tianjin", "2024年经常项目外汇政策问答案例（九） — 境外个人是否享受年度便利化额度购汇？",
     "汇发〔2020〕14号 art. 59 — 境外个人 (FOREIGN individuals, e.g. a US citizen): FX purchase out of lawful current-account CNY income obtained in China requires the person's valid ID **plus source-of-funds documents showing the transaction amount, including tax certificates** (有交易额的购汇资金来源材料（含税务凭证）). The annual purchase convenience quota applies ONLY to foreign individuals holding a 外国人永久居留身份证 (Foreign Permanent Resident ID card)",
     "https://www.safe.gov.cn/tianjin/2024/0621/2529.html", "2026-11-10T09:51:00Z", "verified"),
    ("S14", "SAFE Tianjin", "（已修改）国家外汇管理局关于进一步改进和调整资本项目外汇管理政策的通知 汇发〔2014〕2号",
     "Emigrant property transfer: SAFE approval then remittance '一次或分次汇出' (one or several times); cancels the 2004 two-year staging and the >RMB 500,000 head-office filing",
     "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "2026-11-10T08:35:00Z", "verified"),
    ("S15", "SAFE Tianjin", "境外个人购房/继承外汇问答 (2026)",
     "Foreigner purchase/inheritance of mainland property: FX purchase per PBOC [2006] No.3; property sale proceeds repatriation",
     "https://www.safe.gov.cn/tianjin/2026/0319/3018.html", "2026-11-10T08:40:00Z", "verified"),
    ("S16", "SAFE Tianjin", "境外个人经常项目外汇业务问答 (2026) - 外籍人士工资购汇",
     "Foreign passport holders' taxed salary FX purchase is not subject to the annual convenience amount",
     "https://www.safe.gov.cn/tianjin/2026/0713/3088.html", "2026-11-10T08:45:00Z", "verified"),
    ("S17", "SAFE", "国家外汇管理局发布深化跨境投融资外汇管理改革一揽子便利化政策 (汇发〔2025〕43号, 2025-09-12)",
     "Cross-border FX reform: removes non-self-use residential property restriction in capital-account negative list; foreign-individual property purchase settlement convenience",
     "https://www.safe.gov.cn/safe/2025/0915/26536.html", "2026-11-10T08:50:00Z", "verified"),
    ("S18", "SAFE", "《国家外汇管理局关于深化跨境投融资外汇管理改革有关事宜的通知》全文 (汇发〔2025〕43号)",
     "Full text of the 2025-09-12 notice cited by S17",
     "https://www.safe.gov.cn/safe/2025/0915/26538.html", "2026-11-10T08:55:00Z", "verified"),
    ("S19", "State Council / SAFE", "中华人民共和国外汇管理条例 国务院令第532号 (arts. 39, 45)",
     "Penalties for illegal FX transfer / private FX trading: up to 30% of the amount; 30%-100% if serious; criminal liability if a crime",
     "https://www.safe.gov.cn/safe/2008/0806/5321.html", "2026-11-10T09:00:00Z", "verified"),
    ("S20", "SAFE Hubei", "汇发〔2017〕29号 答问 - 银行卡境外提取现金",
     "Card cash withdrawal abroad: ¥100,000 per card per year; ¥10,000 per card per day",
     "https://www.safe.gov.cn/hubei/2019/0305/851.html", "2026-11-10T09:05:00Z", "verified"),
    ("S21", "SAFE Hebei", "个人外汇管理办法实施细则问答 - 外币现钞",
     "FX cash: US$5,000 per person per day when carried in/out without declaration; above US$10,000 declaration required",
     "http://www.safe.gov.cn/hebei/2019/0521/1366.html", "2026-11-10T09:10:00Z", "verified"),
    ("S22", "SAFE Tianjin", "（已修改）个人外汇管理办法实施细则 (2024)",
     "Foreign individual RMB income purchase and 兑回: receipt (水单) valid 24 months; ≤US$500 same-day / ≤US$1,000 at border-side outlets on ID only",
     "https://www.safe.gov.cn/tianjin/2024/0430/2464.html", "2026-11-10T09:15:00Z", "verified"),
    ("S23", "SAFE Tianjin", "2026年外汇管理互联网信息——个人外汇（10）",
     "Re-confirms the 24-month receipt validity for 兑回 and the US$500/US$1,000 ID-only thresholds",
     "https://www.safe.gov.cn/tianjin/2026/0917/3134.html", "2026-11-10T09:20:00Z", "verified"),
    ("S24", "SAFE", "支付机构外汇业务管理办法 (汇发〔2019〕13号) 新闻稿",
     "Licensed payment institutions may provide current-account FX services for individuals (cross-border shopping, study, travel) via partner banks",
     "http://m.safe.gov.cn/safe/2019/0429/13115.html", "2026-11-10T09:25:00Z", "verified"),
    ("S25", "SAFE", "资本项目外汇业务指引 (2023年版)",
     "Capital-account operations: QDII quota approval, profit remittance review (>US$50k documents), 内保外贷 registration requirements",
     "https://www.safe.gov.cn/safe/file/file/20231116/698412b317c34542ae0dfa9075e7e6e8.pdf", "2026-11-10T09:30:00Z", "verified"),
    ("S26", "SAFE", "现行有效外汇管理主要法规目录 (截至2025年12月31日)",
     "Current-valid FX regulation catalogue as of 2025-12-31 - confirms which instruments are still in force",
     "https://www.safe.gov.cn/safe/file/file/20260130/615fed50ae3a497f999d11e180e16f0f.pdf", "2026-11-10T09:35:00Z", "verified"),
    ("S27", "PBOC via gov.cn", "中国人民银行关于规范金融机构外汇业务的通知 [2006] No.3 (PBOC [2006] No.3)",
     "Foreign individual property purchase FX rules (arts. 7, 13, 22, 32, 37): contract/receipt-based settlement, proceeds repatriation",
     "https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm", "2026-11-10T09:40:00Z", "verified"),
    ("S28", "PBOC via SAFE", "中国人民银行公告[2004]第16号/18号 (emigrant / foreigner FX transfer)",
     "Historical emigrant-transfer text (art. 6 staging) - superseded by 汇发〔2014〕2号; kept for line-by-line audit",
     "http://m.safe.gov.cn/safe/2004/1116/5461.html", "2026-11-10T09:45:00Z", "verified"),
    ("S29", "PBOC", "关于进一步防范和处置虚拟货币交易炒作风险的通知 银发〔2026〕42号 (2026-02-06)",
     "Crypto-related business activities prohibited; repeals 银发〔2021〕237号; bans crypto, RMB-pegged stablecoins, unapproved RWA",
     "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html", "2026-11-10T09:50:00Z", "verified"),
    ("S30", "PBOC Guangzhou", "粤港澳大湾区“跨境理财通”业务试点实施细则 - 个人额度",
     "GBA Wealth Management Connect individual quota raised to RMB 3,000,000 (closed-loop)",
     "https://guangzhou.pbc.gov.cn/guangzhou/129196/4332364/4332380/5221319/index.html", "2026-11-10T09:55:00Z", "verified"),
    ("S31", "PBOC", "新版“跨境理财通”落地 (WMC 2.0 press release, effective 2024-02-26)",
     "WMC 2.0: individual quota ¥3M; ¥1.5M via bank + ¥1.5M via securities; eligibility (2-year social insurance/tax or ¥400k annual income)",
     "https://www.pbc.gov.cn/goutongjiaoliu/113456/113475/67fdfc7c586b49f4a6f1085ebb4f49b7/index.html", "2026-11-10T10:00:00Z", "verified"),
    ("S32", "PBOC", "中国人民银行关于印发《人民币跨境支付系统业务规则》的通知 (effective 2026-02-01)",
     "CIPS supports CNY-foreign currency PvP settlement - institutional settlement infrastructure, not an individual conversion channel",
     "https://www.pbc.gov.cn/zhengwugongkai/4081330/4406346/4693545/2025122911002295380/index.html", "2026-11-10T10:05:00Z", "verified"),
    ("S33", "STA / SAFE", "国家税务总局 国家外汇管理局公告2013年第40号",
     "Remittance/payment above US$50,000: tax filing recordal (税务备案表) required before the bank processes it",
     "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html", "2026-11-10T10:10:00Z", "verified"),
    ("S34", "STA / SAFE", "国家税务总局 国家外汇管理局公告2021年第19号",
     "Updates No.40: simplifies filing for payments under US$50,000",
     "https://www.chinatax.gov.cn/chinatax/c102449/c5237521/content.html", "2026-11-10T10:15:00Z", "verified"),
    ("S35", "STA", "中华人民共和国个人所得税法 第三条",
     "PRC IIT: 3%-45% comprehensive income; 20% flat on interest, dividends, property rental, property transfer, incidental income",
     "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html", "2026-11-10T10:20:00Z", "verified"),
    ("S36", "STA", "财税〔2008〕132号 - 储蓄存款利息所得免征个人所得税",
     "Bank deposit interest IIT exemption effective 2008-10-09",
     "https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html", "2026-11-10T10:25:00Z", "verified"),
    ("S37", "STA", "中华人民共和国企业所得税法实施条例 第九十一条",
     "Withholding tax on passive income of non-resident enterprises: 10%",
     "https://fgk.chinatax.gov.cn/zcfgk/c100010/c5194417/content.html", "2026-11-10T10:30:00Z", "verified"),
    ("S38", "MOHRSS (republished by Shaanxi provincial HR bureau)", "在中国境内就业的外国人参加社会保险暂行办法 (MOHRSS Order No.16, amended 2024-12-23) art. 5",
     "Foreign employee leaving before pension age: social insurance personal account retained; on written request to terminate the relationship, the account balance may be paid out in a lump sum",
     "https://rst.shaanxi.gov.cn/sy/ztzl/rdzt/pfxczl/202501/t20250107_3296414.html", "2026-11-10T10:35:00Z", "verified"),
    ("S39", "SPC / SPP (via Hunan Court)", "关于办理非法从事资金支付结算业务、非法买卖外汇刑事案件适用法律若干问题的解释 法释〔2019〕1号",
     "Criminal thresholds for illegal FX trading: turnover ≥RMB 5,000,000 or illegal gain ≥RMB 100,000 (or other serious circumstances)",
     "https://www.hncourt.gov.cn/public/detail.php?id=176932", "2026-11-10T10:40:00Z", "verified"),
    ("S40", "US Congress / govinfo", "26 U.S.C. § 988 (U.S. Code, 2023 edition)",
     "§988(a)(1)(A) ordinary gain/loss; §988(e)(1) excludes personal transactions; §988(e)(2) excludes personal FX gain ≤$200; §988(e)(3) excludes §162/§212 income-producing accounts from 'personal transaction'",
     "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", "2026-11-10T10:45:00Z", "verified"),
    ("S41", "IRS", "Figuring the Foreign Earned Income Exclusion",
     "FEIE: US$130,000 (2025) / US$132,900 (2026); wages for personal services only",
     "https://www.irs.gov/individuals/international-taxpayers/figuring-the-foreign-earned-income-exclusion", "2026-11-10T10:50:00Z", "verified"),
    ("S42", "IRS", "Yearly Average Currency Exchange Rates",
     "CNY yearly averages: 7.129 (2025), 7.189 (2024), 7.075 (2023), 6.730 (2022), 6.452 (2021)",
     "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates", "2026-11-10T10:55:00Z", "verified"),
    ("S43", "IRS", "Comparison of Form 8938 and FBAR Requirements",
     "Form 8938 thresholds: unmarried in US $50,000 year-end / $75,000 any time; abroad $200,000/$300,000; penalties $10,000-$60,000+ per failure",
     "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "2026-11-10T11:00:00Z", "verified"),
    ("S44", "IRS", "Gifts from Foreign Person - Form 3520",
     "Form 3520: foreign gift/bequest >$100,000 (individual); foreign corporation/partnership gifts >$20,573 (2026)",
     "https://www.irs.gov/businesses/gifts-from-foreign-person", "2026-11-10T11:05:00Z", "verified"),
    ("S45", "IRS", "Streamlined Filing Compliance Procedures (incl. U.S. taxpayers residing outside the United States - SFOP)",
     "SFOP: 0% penalty; SDOP: 5% penalty; eligibility conditions for non-resident non-filer US taxpayers",
     "https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures", "2026-11-10T11:10:00Z", "verified"),
    ("S46", "IRS", "IRM 4.26.16 - Delinquent FBAR submission procedures",
     "IRS internal manual procedures for late FBAR submissions (IRC 6038B/31 USC 5321 enforcement context)",
     "https://www.irs.gov/irm/part4/irm_04-026-016", "2026-11-10T11:15:00Z", "verified"),
    ("S47", "IRS", "Foreign Tax Credit",
     "Form 1116 foreign tax credit mechanism for PRC-paid taxes",
     "https://www.irs.gov/individuals/international-taxpayers/foreign-tax-credit", "2026-11-10T11:20:00Z", "verified"),
    ("S48", "FinCEN", "Report Foreign Bank and Financial Accounts (FBAR)",
     "FBAR filing threshold: aggregate foreign account value exceeds $10,000 at any time during the calendar year (strictly greater)",
     "https://www.fincen.gov/report-foreign-bank-and-financial-accounts", "2026-11-10T11:25:00Z", "verified"),
    ("S49", "FinCEN / eCFR", "31 CFR 1010.821 (Civil penalty table for FBAR violations), eCFR current as of 2026-11-06",
     "Non-willful FBAR violation: $16,536; willful: greater of $165,353 or 50% of the account balance",
     "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "2026-11-10T11:30:00Z", "verified"),
    ("S50", "US Treasury / IRS", "Convention Between the United States of America and the People's Republic of China (US-China Tax Treaty)",
     "Arts. 9-11: 10% dividends/interest/royalties; Saving Clause Protocol preserves US worldwide taxation of US citizens",
     "https://www.irs.gov/pub/irs-trty/china.pdf", "2026-11-10T11:35:00Z", "verified"),
    ("S51", "US CBP", "Money & Monetary Instruments",
     "Currency carried in/out above $10,000 requires FinCEN Form 105 declaration; threshold applies to the collective amount of a family/group",
     "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments", "2026-11-10T11:40:00Z", "verified"),
]

SOURCE_HEADER = ["id", "institution", "title", "what_it_establishes", "url", "fetched_utc", "verdict"]


# =====================================================================
# 2. METHOD CATALOG (24 routes)
# =====================================================================
# (id, method, category, status, eligibility, pros, cons, penalty_anatomy, source_ids)
METHODS = [
    ("M01", "Personal bank wire (SWIFT) via BOC e-banking", "Bank wire",
     "Lawful - unrestricted",
     "Any individual; funds already in own CNY account",
     "Official channel and fully tracked. DOCUMENT SCOPE (verified): for a 境外个人 (foreign individual — a US citizen) the bank needs valid ID PLUS source-of-funds documents with the transaction amount INCLUDING TAX CERTIFICATES for lawful current-account CNY income (汇发〔2020〕14号 art. 59). The ID-only ≤US$50,000/day rule (art. 64) applies to 境内个人 (domestic individuals) remitting from an FX account, and ≤US$10,000/day to foreign-currency cash",
     "FX spread ~0.21% + wire 1‰ (¥50-¥260) + ¥150 cable; possible OUR surcharge; US FBAR/8938 if applicable",
     "China: no FX tax on conversion; FX spread + wire tariff. US: §988 gain/loss, FBAR >$10k, Form 8938 thresholds",
     "S01|S03|S10|S13|S19|S40|S42|S43|S48|S49|S52"),
    ("M02", "Full-amount-received (OUR) wire to the US", "Bank wire",
     "Lawful - conditional",
     "BOC's published PERSONAL fee notice (关于调整部分个人业务收费标准的公示, 2014-12-31, effective 2015-04-01, code 210104021, item 4.个人跨境本外币汇款 / 4.2全额到账): US$15 per wire if the beneficiary bank holds an account at BOC New York, US$25 otherwise. Offered only where the remitting and beneficiary banks have no direct account relationship and at least one intermediary bank is used",
     "Recipient receives the full amount; intermediate fees borne by sender",
     "Surcharge US$15-$25 per wire on top of M01; personal applicability not expressly stated by BOC",
     "Same as M01 plus the OUR surcharge",
     "S01|S03|S04|S05|S49"),
    ("M03", "Cash withdrawal + border carry", "Cash",
     "Lawful - restricted",
     "UnionPay debit card; ≤¥100,000/card/year; ≤US$10,000 cash per person without declaration",
     "No correspondent chain; USD in hand at destination",
     "ATM fee ¥12+1% (max ¥112); cash exchange price differs from spot; >$10,000 border declaration; loss/theft risk",
     "ATM fee + cash FX spread; >$10k undeclared = CBP/FinCEN 105 violation",
     "S01|S06|S20|S21|S51"),
    ("M04", "Overseas ATM withdrawal on a CNY card", "Cash",
     "Lawful - unrestricted",
     "UnionPay debit card with CNY balance; Mastercard/Visa cards cost more",
     "Available worldwide without any approval",
     "UnionPay ¥12+1% (max ¥112/tx); MC/Visa 2.5% ($3-$40) from 2026-11-11; daily limits; DCC risk",
     "ATM fee only (no FX conversion step at home); US FBAR if the foreign account exceeds $10k",
     "S06|S48|S49"),
    ("M05", "Emigrant property transfer (移民财产转移)", "Capital account",
     "Lawful - requires approval",
     "Emigrated from the mainland with cancelled hukou; property evidence; SAFE approval at former hukou location",
     "Large amounts in one approved lump sum or staged per approval; staging no longer mandatory (2014)",
     "Requires SAFE approval and documentation; a US citizen by birth without mainland hukou does not qualify",
     "Approval-based; no FX tax on approved transfer; US §988 gain measured on basis",
     "S14|S19|S28|S35|S40|S42"),
    ("M06", "Foreigner mainland property purchase / inheritance", "Capital account",
     "Lawful - conditional",
     "Foreigner eligible to hold mainland property (residence permit / permanent residence ID; city rules)",
     "Purchases with FX settlement per PBOC [2006] No.3; sale proceeds can be repatriated",
     "City eligibility rules; property-cycle risk; not a pure conversion route",
     "PBOC [2006] No.3 arts. 7/13/22/32/37; PRC IIT on rental/transfer income",
     "S15|S17|S27|S35"),
    ("M07", "Foreign permanent resident ID salary FX", "Salary",
     "Lawful - conditional",
     "Holds Foreign Permanent Resident ID (PRC) and mainland employment",
     "Documented salary FX purchase; convenience amount available",
     "Only for those holding the PRC permanent resident ID; tax record required above the convenience amount",
     "PRC IIT on salary; US §988/FEIE interplay; FBAR/8938",
     "S11|S16|S35|S40|S41|S43"),
    ("M08", "Foreign passport salary FX (taxed, uncapped)", "Salary",
     "Lawful - conditional",
     "Foreign passport holder employed in China; PRC IIT on the salary",
     "Salary FX purchase is not subject to the annual convenience amount when taxed",
     "Requires employment and tax payment; authenticity review",
     "PRC IIT withheld; US tax on wages (FEIE may apply); §988 on conversion",
     "S16|S35|S41|S42|S43"),
    ("M09", "Employer payroll remittance", "Salary",
     "Lawful - conditional",
     "Employer processes salary remittance through a payroll provider",
     "Handles documentation; net salary arrives in USD",
     "Requires employer cooperation; provider fees not published officially (blank)",
     "PRC IIT withheld; provider/receiving-bank fees blank (unverified)",
     "S16|S35|S41"),
    ("M10", "Dividends & interest repatriation", "Investment income",
     "Lawful - conditional",
     "Hold stocks/bonds/funds or interest-bearing deposits in own name",
     "Dividends/interest already CNY; settle per rules",
     "Stock dividends subject to PRC IIT 20%; deposit interest IIT-exempt since 2008; treaty rate 10% may apply",
     "PRC withholding (20% individual / 10% treaty / deposit interest exempt); US §988; foreign tax credit possible",
     "S35|S36|S37|S40|S47|S50"),
    ("M11", "Licensed remittance / payment platform", "Platform",
     "Lawful - conditional",
     "Platform holds a SAFE-licensed payment-institution FX licence (汇发〔2019〕13号 scope)",
     "Digital, fast; current-account scope (shopping, study, travel)",
     "Scope is current-account business only; platform fees not published officially (blank)",
     "Platform partner-bank FX spread; fees blank (unverified)",
     "S24|S10"),
    ("M12", "Cross-border e-commerce settlement", "Platform",
     "Lawful - conditional",
     "Real goods trade through a licensed platform with transaction records",
     "Legitimate trade settlement with FX purchase on evidence",
     "Requires real transactions; documentation heavy",
     "FX purchase on evidence; PRC trade taxes as applicable",
     "S24|S33|S34"),
    ("M13", "QDII fund route", "Investment product",
     "Lawful - unrestricted",
     "Any individual buying a QDII fund at a Chinese fund/bank",
     "USD exposure via institutional offshore investments; no personal approval",
     "Not a direct CNY-USD conversion; redemption returns CNY at market; fund fees blank (unverified)",
     "Fund-level fees blank; US tax on fund distributions as applicable",
     "S25|S26"),
    ("M14", "GBA Wealth Management Connect", "Investment product",
     "Lawful - conditional",
     "GBA residents meeting WMC eligibility (2-year social insurance/tax or ¥400k income); ¥3M individual quota",
     "Closed-loop RMB 3M quota; invest in HK products via bank/securities channels",
     "GBA residency required; closed loop; not a direct cash conversion",
     "Product-level fees blank; FX via the closed loop",
     "S30|S31"),
    ("M15", "Mainland property sale proceeds", "Capital account",
     "Lawful - requires documents",
     "Sold mainland property as a foreign individual; tax paid",
     "Large repatriation of sale proceeds per PBOC [2006] No.3 art. 7",
     "Property cycle; IIT on transfer; documentation heavy",
     "PRC IIT 20% on property transfer income; repatriation documentation",
     "S27|S35|S15"),
    ("M16", "Company dividend remittance", "Corporate",
     "Lawful - requires corporate documents",
     "CNY held in a PRC company account",
     "Clean corporate route with board resolution + tax filing",
     ">US$50,000 requires tax filing recordal (STA/SAFE No.40/19); audited financials for profit remittance",
     "Corporate tax filing; treaty dividend rate 10%",
     "S25|S33|S34|S37|S50"),
    ("M17", "Corporate cross-border financing / guarantee", "Corporate",
     "Lawful - requires registration",
     "PRC company with capital-account registration (内保外贷 / cross-border financing)",
     "Offshore funding without immediate conversion",
     "Capital-account registration required; funds use restricted; not an individual route",
     "Capital-account rules; penalties for misuse",
     "S25|S26|S19"),
    ("M18", "Retained social insurance account payout", "Withdrawal",
     "Lawful - conditional",
     "Former mainland employee (foreign passport holder) whose social insurance account is retained under MOHRSS Order No.16 art. 5",
     "Account balance can be paid out in a lump sum on written request to terminate the relationship",
     "Only for departed foreign employees; amount limited to the account balance",
     "Lump-sum payment is CNY; convert via M01; PRC tax treatment flagged",
     "S38|S35|S03"),
    ("M19", "Crypto conversion route", "Prohibited",
     "Prohibited - do not use",
     "n/a",
     "n/a",
     "PBOC 银发〔2026〕42号 prohibits crypto-related business activities; 30%-100% fines; criminal liability per 法释〔2019〕1号",
     "Decree 532 arts. 39/45 fines; criminal thresholds RMB 5M turnover / RMB 100k gain",
     "S29|S19|S39"),
    ("M20", "Undeclared cash carry above $10,000", "Prohibited",
     "Prohibited - above threshold",
     "n/a",
     "n/a",
     "Above US$10,000 per person (or per family group collectively) FinCEN Form 105 must be declared; undeclared = violation",
     "CBP/FinCEN enforcement; possible seizure",
     "S51|S21"),
    ("M21", "Hawala / underground money transfer", "Prohibited",
     "Prohibited - do not use",
     "n/a",
     "n/a",
     "Illegal FX trading under Decree 532 arts. 39/45; 30%-100% fines; criminal liability if turnover ≥¥5M or gain ≥¥100k",
     "Same as M19",
     "S19|S39"),
    ("M22", "Bypassing SAFE approval on emigrant transfer", "Prohibited",
     "Not recommended - illegal",
     "n/a",
     "n/a",
     "Emigrant transfers require SAFE approval; bypassing it is illegal FX transfer under Decree 532 art. 39",
     "30%-100% fine; criminal liability",
     "S14|S19|S28"),
    ("M23", "Offshore RMB (CNH) account + offshore conversion", "Restricted",
     "Restricted - eligibility unclear",
     "Individual offshore RMB account opening eligibility is not published as a single national rule",
     "Potentially convert at offshore CNH price",
     "Individual offshore RMB account eligibility unclear; offshore conversion fee not officially published (blank)",
     "Offshore CNH spread blank (unverified)",
     "S32|S17"),
    ("M24", "Staged / annual-planned conversion", "Planning technique",
     "Lawful - planning",
     "Any individual with documented purposes",
     "Spreads conversions across years; each year's documented purchase keeps records clean",
     "Time cost; requires real transaction documents each year",
     "Same per-transaction costs as M01; no added penalty",
     "S10|S13|S19"),
]

METHOD_HEADER = ["method_id", "method", "category", "status", "eligibility",
                 "pros", "cons", "conversion_penalty_anatomy", "source_ids"]


# =====================================================================
# 3. PENALTIES / TAX DECOMPOSITION
# =====================================================================
# (id, scope, rule, tax_or_penalty, rate_or_amount, conditions, source_ids)
PENALTIES = [
    ("P01", "China - illegal FX transfer", "外汇管理条例 art. 39 (逃汇)",
     "Civil penalty", "Up to 30% of the transferred amount; 30%-100% if the case is serious",
     "Ordered to repatriate funds within a set period; criminal liability if a crime", "S19"),
    ("P02", "China - private FX trading", "外汇管理条例 art. 45",
     "Civil penalty", "Up to 30% of the amount; 30%-100% if serious",
     "Same ceiling as art. 39", "S19"),
    ("P03", "China - illegal FX trading crime", "法释〔2019〕1号 (SPC/SPP)",
     "Criminal", "Turnover ≥RMB 5,000,000 or illegal gain ≥RMB 100,000 (or other serious circumstances)",
     "Conviction requires reaching the judicial interpretation thresholds", "S39"),
    ("P04", "China - crypto business", "银发〔2026〕42号 (PBOC, 2026-02-06)",
     "Prohibition", "Crypto-related business activities prohibited; RMB-pegged stablecoins and unapproved RWA banned",
     "Repeals 银发〔2021〕237号", "S29"),
    ("P05", "China - cash border", "SAFE FX cash rules (细则问答)",
     "Declaration requirement", "≤US$5,000 per person per day without declaration; >US$10,000 declaration required",
     "Applies to currency carried in/out", "S21"),
    ("P06", "China - IIT on property transfer/dividends/interest", "IIT Law art. 3(3)",
     "Tax", "20% flat", "Property transfer, rental, dividends, interest, incidental income", "S35"),
    ("P07", "China - bank deposit interest", "财税〔2008〕132号",
     "Tax exemption", "0% (exempt since 2008-10-09)", "Savings deposit interest", "S36"),
    ("P08", "China - withholding on passive income (non-resident enterprise)", "EIT Implementation Regulations art. 91",
     "Withholding tax", "10%", "Dividends, interest, royalties of non-resident enterprises", "S37"),
    ("P09", "China - US treaty rate", "US-China Tax Treaty arts. 9-11",
     "Treaty rate", "10% (dividends, interest, royalties)", "US resident beneficiary; Saving Clause preserves US worldwide taxation", "S50"),
    ("P10", "China - documentation for >US$50k remittance", "STA/SAFE [2013] No.40 / [2021] No.19",
     "Procedure", "Tax filing recordal (税务备案表) before the bank processes it", "Applies to cross-border payments above US$50,000", "S33|S34"),
    ("P11", "China - conversion itself", "Negative finding",
     "No tax", "No official source imposes a PRC tax on converting an individual's own CNY to USD",
     "The cost is the FX spread + bank tariffs, not a conversion tax", "S19|S10|S03"),
    ("P12", "US - IRC §988 ordinary gain/loss", "26 U.S.C. § 988(a)(1)(A)",
     "Tax character", "Ordinary income/loss for non-personal transactions",
     "§988(e)(3) excludes §162/§212 accounts from 'personal transaction'", "S40"),
    ("P13", "US - personal transaction exclusion", "26 U.S.C. § 988(e)(1)-(2)",
     "Tax exclusion", "Personal transactions excluded from §988; personal FX gain excluded unless >$200",
     "Loss on personal disposition remains nondeductible (§165(c))", "S40"),
    ("P14", "US - FBAR filing", "FinCEN Form 114",
     "Reporting", "Aggregate foreign account value >$10,000 at any time during the calendar year",
     "Strictly greater than $10,000; aggregated across accounts", "S48"),
    ("P15", "US - FBAR penalties", "31 CFR 1010.821",
     "Penalty", "Non-willful: $16,536; willful: greater of $165,353 or 50% of the account balance",
     "eCFR current as of 2026-11-06", "S49"),
    ("P16", "US - Form 8938", "IRS comparison page",
     "Reporting + penalty", "Unmarried in US: $50,000 year-end / $75,000 any time; abroad: $200,000/$300,000; penalties $10,000-$60,000+",
     "Specified foreign financial assets", "S43"),
    ("P17", "US - Form 3520", "IRS gifts-from-foreign-person page",
     "Reporting", "Gift/bequest >$100,000 from a foreign person (individual); corp/partnership gifts >$20,573 (2026)",
     "Penalties for non-filers", "S44"),
    ("P18", "US - FEIE", "IRS FEIE page",
     "Exclusion", "$132,900 (2026) / $130,000 (2025)",
     "Wages for personal services only; does not apply to currency gain or existing savings", "S41"),
    ("P19", "US - Foreign tax credit", "IRS FTC page / Form 1116",
     "Credit", "Credit for PRC-paid taxes subject to limitations",
     "May offset US tax on the same income", "S47"),
    ("P20", "US - Streamlined procedures", "IRS streamlined page",
     "Penalty relief", "SFOP: 0% penalty; SDOP: 5% penalty",
     "Eligibility conditions; non-willful conduct required", "S45"),
    ("P21", "US - border currency", "CBP money & monetary instruments page",
     "Declaration", ">$10,000 carried or sent - FinCEN Form 105; threshold applies collectively to a family/group",
     "Applies to physical currency", "S51"),
    ("P22", "US - bank FX spread", "Derived from BOC board 2026-11-10",
     "Conversion cost", "Half-spread 0.2100% of USD amount = (ask - mid)/ask with mid (bid 6.6622 + ask 6.6903)/2 = 6.67625",
     "One-day observation; the board changes intraday", "S01"),
    ("P23", "US/China - wire tariffs", "BOC personal tariff + OUR schedule",
     "Bank fee", "1‰ (¥50-¥260) + ¥150 cable per wire; optional OUR US$15-$25",
     "OUR is BOC's published PERSONAL tariff (notice effective 2015-04-01), not a corporate one; its condition is ROUTING — no direct account relationship between the two banks and at least one intermediary bank", "S03|S04"),
]

PENALTY_HEADER = ["id", "scope", "rule", "tax_or_penalty", "rate_or_amount", "conditions", "source_ids"]


# =====================================================================
# 4. COST LADDER  ($10,000 - $400,000, $10,000 steps)
# =====================================================================
ASK = D("6.6903")     # BOC USD spot selling 2026-11-10 07:32:39 (S01)
BID = D("6.6622")     # BOC USD spot buying 2026-11-10 07:32:39 (S01)
MID = (ASK + BID) / 2
HALF_SPREAD_RATIO = (ASK - MID) / ASK  # what the customer pays vs mid

COST_HEADER = ["amount_usd", "cny_needed", "spread_usd", "wire_cny", "wire_usd",
               "total_usd", "total_with_our_usd", "total_pct", "net_usd", "net_with_our_usd",
               "source_ids"]

COST_ROWS = []
for usd in range(10_000, 400_000 + 1, 10_000):
    amt = D(usd)
    cny_needed = q2(amt * ASK)
    spread_usd = q2(amt * HALF_SPREAD_RATIO)
    wire_cny = min(D("260"), max(D("50"), cny_needed * D("0.001"))) + D("150")
    wire_usd = q2(wire_cny / ASK)
    total = q2(spread_usd + wire_usd)
    total_our = q2(total + D("25"))
    pct = (total / amt) * 100
    net = q2(amt - total)
    net_our = q2(amt - total_our)
    COST_ROWS.append([
        str(usd), str(cny_needed), str(spread_usd), str(wire_cny), str(wire_usd),
        str(total), str(total_our), str(pct.quantize(D("0.01"), rounding=ROUND_HALF_UP)),
        str(net), str(net_our), "S01|S03|S04",
    ])

# ---------------------------------------------------------------- method summary
SUMMARY_HEADER = ["method_id", "method", "verified_usd_10k", "verified_usd_100k",
                  "verified_usd_400k", "unverified_components", "notes"]

def wire_usd_at(usd: int) -> Decimal:
    cny = min(D("260"), max(D("50"), D(usd) * ASK * D("0.001"))) + D("150")
    return q2(cny / ASK)


WIRE_AT = {u: wire_usd_at(u) for u in (10_000, 100_000, 400_000)}
SPREAD_AT = {u: q2(D(u) * HALF_SPREAD_RATIO) for u in (10_000, 100_000, 400_000)}

METHOD_SUMMARY = []
for (mid, name, cat, status, *_rest) in METHODS:
    if mid == "M01":
        v10 = str(q2(SPREAD_AT[10_000] + WIRE_AT[10_000]))
        v100 = str(q2(SPREAD_AT[100_000] + WIRE_AT[100_000]))
        v400 = str(q2(SPREAD_AT[400_000] + WIRE_AT[400_000]))
        unv = ""
        note = "Verified FX spread + wire tariff only; intermediary and US receiving-bank fees blank (unverified)"
    elif mid == "M02":
        v10 = str(q2(SPREAD_AT[10_000] + WIRE_AT[10_000] + D("25")))
        v100 = str(q2(SPREAD_AT[100_000] + WIRE_AT[100_000] + D("25")))
        v400 = str(q2(SPREAD_AT[400_000] + WIRE_AT[400_000] + D("25")))
        unv = "Personal OUR applicability"
        note = "OUR US$25 per wire on top of M01; personal applicability conditional"
    elif mid == "M03":
        v10 = str(q2(D(12) / ASK + D("112") / ASK))  # ATM fee proxy: ¥12 + max ¥112
        v100 = ""
        v400 = ""
        unv = "Cash exchange price vs spot; border declaration"
        note = "ATM fee only; cash-to-USD price at counter not the spot board (blank)"
    elif mid == "M04":
        v10 = str(q2((D(12) + D(10_000) * ASK * D("0.01")) / ASK))  # ¥12 + 1% example
        v100 = str(q2((D(12) + D("112")) / ASK))
        v400 = ""
        unv = "Card daily limits; MC/Visa 2.5% from 2026-11-11"
        note = "UnionPay fee ¥12 + 1% capped ¥112/tx"
    else:
        v10 = v100 = v400 = ""
        unv = "Commercial/product fees not published officially"
        note = "See method status and eligibility; costs blank where no official schedule exists"
    METHOD_SUMMARY.append([mid, name, v10, v100, v400, unv, note])


# =====================================================================
# 5. STEP-BY-STEP PLAYBOOKS
# =====================================================================
STEPS_HEADER = ["method_id", "step", "what_you_do", "documents_or_conditions", "source_ids"]

STEPS = [
    ("M01", 1, "Log into BOC online banking and open 跨境汇款 (cross-border remittance); select the recipient's USD account.", "BOC debit card with CNY balance; recipient account details", "S03"),
    ("M01", 2, "Enter the amount. The bank quotes the current spot selling rate at submission (2026-11-10 07:32:39: 6.6903).", "Rate changes intraday; use the quote at execution", "S01"),
    ("M01", 3, "Confirm the fee: 1‰ (min ¥50, max ¥260) + cable ¥150 (HK/MO/TW ¥80).", "Tariff effective 2014-11-01; mobile waiver ended 2025-12-31", "S03|S09"),
    ("M01", 4, "Authorise the debit; save the remittance receipt and the rate quote.", "Receipt is your proof of conversion price and date", "S03"),
    ("M01", 5, "File US reports: FBAR (aggregate >$10k at any time) and Form 8938 if thresholds met; report §988 gain/loss on the return.", "Strictly greater than $10,000; Form 8938 thresholds per IRS page", "S48|S43|S40"),
    ("M02", 1, "Ask the BOC branch for 全额到账 (OUR) on a personal USD wire to the US.", "Corporate tariff lists US$15 to BOC NY / US$25 to other US banks; personal applicability must be confirmed", "S04|S05"),
    ("M02", 2, "Request the OUR charge be added to the transfer instruction.", "Confirm total debit before authorising", "S04"),
    ("M02", 3, "Track the MT103 SWIFT message; the US bank posts the net amount to the beneficiary.", "BOC USA: US$0 incoming personal wire", "S07"),
    ("M02", 4, "Save the fee breakdown; report US tax as per M01 step 5.", "Same reporting duties as M01", "S48|S43|S40"),
    ("M03", 1, "Withdraw CNY via a UnionPay ATM: ¥100,000 per card per year, ¥10,000 per card per day.", "UnionPay fee ¥12 + 1% (max ¥112/tx)", "S20|S06"),
    ("M03", 2, "Exchange the CNY to USD at a bank counter.", "Counter cash price differs from the spot board; not officially published (blank)", "S01"),
    ("M03", 3, "Carry ≤US$10,000 per person without declaration; above that declare to customs.", ">US$10,000 - FinCEN Form 105; family/group threshold is collective", "S21|S51"),
    ("M03", 4, "Deposit at destination; keep the declaration receipt and the exchange receipt.", "Receipts support US tax reporting", "S51"),
    ("M04", 1, "Use a UnionPay debit card at an overseas ATM.", "UnionPay fee ¥12 + 1% (max ¥112/tx)", "S06"),
    ("M04", 2, "Decline DCC; withdraw in USD or local currency at the network rate.", "MC/Visa cards: 2.5% ($3-$40) from 2026-11-11 - prefer UnionPay", "S06"),
    ("M04", 3, "Deposit the cash; note the ATM fee on the statement.", "FBAR applies if any foreign account exceeds $10k", "S48"),
    ("M05", 1, "Cancel mainland hukou (if PRC-born) and collect the certificate; assemble property-value evidence.", "A US citizen by birth without hukou does not qualify", "S28"),
    ("M05", 2, "Apply to SAFE at the former hukou location for 移民财产转移核准 (emigrant property transfer approval).", "Documents per SAFE; approval required", "S14"),
    ("M05", 3, "On approval, the bank remits the approved amount in one or several installments (no mandatory two-year staging).", "汇发〔2014〕2号 §6: 一次或分次汇出", "S14"),
    ("M05", 4, "Report US tax: §988 gain measured against your basis (IRS yearly averages).", "Basis not provided - leave blank unless supplied", "S40|S42"),
    ("M06", 1, "Confirm eligibility to hold mainland property as a foreign individual (residence permit / permanent residence ID; city rules).", "City-specific eligibility", "S15|S17"),
    ("M06", 2, "Complete the purchase with FX settlement per PBOC [2006] No.3 arts. 7/13.", "Contract/receipt-based settlement", "S27"),
    ("M06", 3, "On sale, repatriate proceeds per art. 7 with tax evidence.", "PRC IIT 20% on property transfer income", "S27|S35"),
    ("M07", 1, "Provide the Foreign Permanent Resident ID and employment documents to the bank.", "Permanent resident ID holders get the convenience amount", "S11"),
    ("M07", 2, "Purchase FX for documented salary; above the convenience amount, submit transaction documents.", "Convenience amount is not a hard limit", "S10"),
    ("M07", 3, "Remit out. Document scope depends on WHO you are: 境内个人 (domestic individual) from an FX account ≤US$50,000/day on ID alone (art. 64); 境外个人 (foreign individual) needs ID + source-of-funds documents incl. tax certificates (art. 59); foreign-currency cash ≤US$10,000/day on ID.", "Same-day cumulative thresholds are per person, per day, and differ by residency status and by account-vs-cash", "S13|S52"),
    ("M07", 4, "Report US tax: wages (FEIE may apply), §988 on conversion, FBAR/8938.", "FEIE excludes wages for personal services only", "S41|S40|S43"),
    ("M08", 1, "Document mainland employment and pay PRC IIT on the salary.", "IIT withheld at source", "S35"),
    ("M08", 2, "Purchase FX for the taxed salary without the annual convenience amount.", "Not subject to the convenience amount when taxed", "S16"),
    ("M08", 3, "Remit through the bank with tax payment evidence.", "Authenticity review", "S16"),
    ("M08", 4, "Claim foreign tax credit for PRC IIT on the US return where applicable.", "Form 1116", "S47"),
    ("M09", 1, "Ask the employer to process the salary remittance through its payroll provider.", "Employer cooperation required", "S16"),
    ("M09", 2, "Provide employment contract and tax payment evidence.", "PRC IIT withheld", "S35"),
    ("M09", 3, "Receive net USD; note provider fees (not officially published - blank).", "Fees blank/unverified", "S16"),
    ("M10", 1, "Confirm the security or deposit is in your own name.", "Individual holding", "S35"),
    ("M10", 2, "Receive CNY dividends/interest: deposit interest is IIT-exempt (财税〔2008〕132号); stock dividends bear 20%.", "Treaty rate 10% may apply to US residents", "S36|S35|S50"),
    ("M10", 3, "Convert and remit via M01.", "Documentation per amount", "S03"),
    ("M10", 4, "Claim foreign tax credit for PRC withholding on the US return.", "Form 1116; treaty rate 10%", "S47|S50"),
    ("M11", 1, "Verify the platform holds a SAFE payment-institution FX licence (汇发〔2019〕13号 scope).", "Licensed institutions list", "S24"),
    ("M11", 2, "Confirm the platform covers your use case: current-account shopping/study/travel.", "Scope is current-account business only", "S24"),
    ("M11", 3, "Complete KYC and convert via the partner bank.", "Platform fees not published officially (blank)", "S24"),
    ("M12", 1, "Trade real goods through a licensed cross-border e-commerce platform.", "Transaction records required", "S24"),
    ("M12", 2, "Use the platform's settlement with FX purchase on evidence.", "Above US$50k - tax filing recordal", "S24|S33"),
    ("M13", 1, "Buy a QDII fund with CNY at a Chinese fund/bank.", "No individual approval needed", "S25"),
    ("M13", 2, "The fund invests offshore; redemption returns CNY at market.", "Fund fees not officially published (blank)", "S25"),
    ("M14", 1, "Confirm GBA WMC eligibility: 2-year social insurance/tax or ¥400k annual income.", "GBA residency required", "S31"),
    ("M14", 2, "Open a WMC account at a designated bank; ¥3M individual closed-loop quota (¥1.5M bank + ¥1.5M securities).", "Closed loop", "S30|S31"),
    ("M14", 3, "Buy HK products; redeem and transfer back within the closed loop.", "Not a direct cash conversion", "S30"),
    ("M15", 1, "Sell the mainland property and pay PRC IIT (20% on transfer income).", "Property documents", "S35|S27"),
    ("M15", 2, "Repatriate proceeds per PBOC [2006] No.3 art. 7 with tax evidence.", "Approval/documentation", "S27"),
    ("M16", 1, "Prepare the board dividend resolution and audited financials.", "Corporate documents", "S25"),
    ("M16", 2, "For >US$50,000, complete the tax filing recordal (STA/SAFE No.40/19).", "税务备案表", "S33|S34"),
    ("M16", 3, "The bank remit after review; treaty dividend rate 10%.", "Corporate route only", "S37|S50"),
    ("M17", 1, "Structure the deal as 内保外贷 or cross-border financing with bank approval.", "Capital-account registration required", "S25"),
    ("M17", 2, "Register in the capital-account system; use funds within the approved scope.", "Misuse draws Decree 532 penalties", "S25|S19"),
    ("M18", 1, "Request termination of the social insurance relationship in writing.", "MOHRSS Order No.16 art. 5", "S38"),
    ("M18", 2, "Receive the account balance as a lump sum (CNY).", "Account retained if not terminated", "S38"),
    ("M18", 3, "Convert the CNY via M01.", "PRC tax treatment flagged", "S03|S35"),
    ("M19", 1, "Do not use crypto routes.", "PBOC 银发〔2026〕42号 prohibits crypto-related business activities", "S29"),
    ("M19", 2, "Penalty exposure: Decree 532 arts. 39/45 fines 30%-100%; criminal liability per 法释〔2019〕1号.", "Turnover ≥¥5M or gain ≥¥100k", "S19|S39"),
    ("M20", 1, "Do not carry undeclared cash above US$10,000 per person.", "FinCEN Form 105 declaration required", "S51"),
    ("M20", 2, "Family/group threshold applies collectively.", "CBP states the collective threshold", "S51"),
    ("M21", 1, "Do not use hawala/underground transfer.", "Illegal FX trading under Decree 532 arts. 39/45", "S19"),
    ("M22", 1, "Do not bypass SAFE approval on emigrant transfers.", "Approval is mandatory; bypass is illegal FX transfer", "S14|S19"),
    ("M23", 1, "Individual offshore RMB (CNH) account eligibility is not published as a single national rule.", "Treat as restricted; confirm with the bank and SAFE", "S32|S17"),
    ("M23", 2, "If available, convert offshore; the offshore conversion fee is not officially published (blank).", "Leave blank, flag UNVERIFIED", "S32"),
    ("M24", 1, "Plan conversions across calendar years.", "Each year's documented purchase keeps records clean", "S10"),
    ("M24", 2, "Keep real transaction documents for every above-convenience purchase.", "Convenience amount is not a limit - documents are", "S10|S13"),
]


# =====================================================================
# 6. FLAGGED / UNVERIFIED REGISTER
# =====================================================================
# (id, severity, item, status, detail, source_ids)
FLAGS = [
    ("S775-F01", "high", "User's funds type (savings / salary / investment / corporate)",
     "UNVERIFIED", "No user input. Eligibility depends on this; the method ranking cannot be narrowed without it.",
     "S10|S16"),
    ("S775-F02", "high", "US tax basis (acquisition date and CNY-per-USD rate)",
     "UNVERIFIED", "§988 gain is measured against basis. Left blank; cohort sensitivities shown on the cost page instead.",
     "S40|S42"),
    ("S775-F03", "high", "User's marginal US ordinary tax rate",
     "UNVERIFIED", "Determines tax on §988 ordinary gain; left blank.", "S40"),
    ("S775-F04", "high", "Whether the user ever held mainland hukou",
     "UNVERIFIED", "Determines eligibility for M05 emigrant property transfer.", "S28"),
    ("S775-F05", "low", "Whether a given US beneficiary bank needs an intermediary (which decides US$15 vs US$25 OUR, or no OUR at all)",
     "CONDITIONAL", "CORRECTED 2026-11-10 by re-reading the primary notice: the US$15/US$25 OUR surcharge is BOC's published PERSONAL fee schedule (关于调整部分个人业务收费标准的公示, code 210104021, item 4.2全额到账, effective 2015-04-01) — the earlier 'corporate tariff document' characterisation was wrong. What genuinely remains unknown is the routing: OUR is offered only when the remitting and beneficiary banks have no direct account relationship and at least one intermediary bank is required, and BOC publishes no list of which US banks that covers. Left blank, not assumed.",
     "S04|S03"),
    ("S775-F06", "medium", "Intermediary (correspondent) and US receiving-bank wire fees",
     "UNVERIFIED", "No official published schedule; left blank, not zero.", "S03|S07"),
    ("S775-F07", "medium", "Counter cash price vs spot board price",
     "UNVERIFIED", "M03 cash conversion price is not the spot board; not officially published as a formula.", "S01"),
    ("S775-F08", "medium", "Offshore CNH conversion fee",
     "UNVERIFIED", "No official published reference; left blank.", "S32"),
    ("S775-F09", "medium", "Exact Form 8938 penalty amounts for a specific year",
     "UNVERIFIED", "IRS page gives a range ($10,000-$60,000+); exact figures depend on the year and conduct.", "S43"),
    ("S775-F10", "medium", "Capital vs ordinary treatment of personal §988 gain above $200",
     "INTERPRETATION", "§988(e)(1) excludes personal transactions from §988(a)(1)(A); the residual gain is analysed under §1221. The statute text is verified; the characterisation is a legal interpretation and is flagged.",
     "S40"),
    ("S775-F11", "medium", "BOC board intraday movement",
     "ONE-DAY OBSERVATION", "Board stamped 2026-11-10 07:32:39; the percentage spread is stable across 2026-11-09/10 readings but the level moves.",
     "S01"),
    ("S775-F12", "low", "Wire fee cap reached at about US$38,862 of transfer",
     "DERIVED", "Arithmetic on ¥260 / 1‰ / ask 6.6903; verified by the sibling dashboard's independent validator.",
     "S03|S01"),
    ("S775-F13", "low", "FBAR threshold wording",
     "NOTE", "FinCEN: aggregate value exceeds $10,000 - strictly greater, at any time during the calendar year.",
     "S48"),
    ("S775-F14", "low", "Cohort sensitivity of §988 gain",
     "DERIVED", "2024 cohort (7.189): +$693.70/$10k; 2025 cohort (7.129): +$615.37/$10k; 2021 cohort (6.452): -$369.34/$10k loss ($0 tax).",
     "S42|S40"),
    ("S775-F15", "low", "Arena single-branch constraint",
     "IRREGULARITY S775-IR-001", "Per-task branches session-<id>/<task> cannot be pushed under Arena's single-branch rule; all work is on arena/775c9619-china3.",
     ""),
    ("S775-F16", "low", "Cross-branch claim visibility",
     "IRREGULARITY S775-IR-002", "COORDINATION.md claims on unmerged branches are invisible to sessions reading main; namespaced file prefixes avoid collisions but do not fix visibility.",
     ""),
    ("S775-F17", "low", "Sibling open PRs #15 / #18 (2026-11-09) remain open",
     "NEEDS REVIEW", "Owners stopped committing >24h ago; left open rather than merged, because merging would republish figures not re-verified row by row.",
     ""),
    ("S775-F18", "low", "MOHRSS foreigner insurance text sourcing",
     "NOTE", "Art. 5 text verified via a provincial re-publish (Shaanxi HR bureau) of MOHRSS Order No.16; the MOHRSS original page was not fetched this session.",
     "S38"),
]

FLAG_HEADER = ["id", "severity", "item", "status", "detail", "source_ids"]


def main() -> int:
    print("Generating S775 data files:")
    wcsv("s775_sources.csv", SOURCE_HEADER, SOURCES)
    with (DATA / "s775_sources.json").open("w", encoding="utf-8") as f:
        json.dump([dict(zip(SOURCE_HEADER, s)) for s in SOURCES], f, ensure_ascii=False, indent=2)
    print(f"  wrote data/s775_sources.json ({len(SOURCES)} records)")
    wcsv("s775_methods.csv", METHOD_HEADER, METHODS)
    wcsv("s775_penalties.csv", PENALTY_HEADER, PENALTIES)
    wcsv("s775_cost_10k_400k.csv", COST_HEADER, COST_ROWS)
    wcsv("s775_method_summary.csv", SUMMARY_HEADER, METHOD_SUMMARY)
    wcsv("s775_steps.csv", STEPS_HEADER, STEPS)
    wcsv("s775_flags.csv", FLAG_HEADER, FLAGS)
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
