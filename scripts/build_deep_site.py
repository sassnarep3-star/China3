#!/usr/bin/env python3
"""Build the China money research dashboard from the verified dataset.

This script is the ONLY place new table content is defined. It writes:
  * data/*.csv           - machine-readable, auditable table data
  * <page>.html          - the category subpages of the GitHub Pages site

Rule enforced here: every table row carries at least one official source URL;
any row whose value could not be confirmed from an official source has an EMPTY
value and is marked UNVERIFIED (and is surfaced on deep-review.html).
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# OFFICIAL SOURCE REGISTER
# id -> (authority, short title, url, verification method)
# Every URL is a government / regulator / official-institution domain.
# ---------------------------------------------------------------------------
SOURCES = {
    # --- China: foreign exchange, tax, criminal law ---
    "S01": ("State Administration of Foreign Exchange (SAFE), Ningxia", "2022 外汇业务政策释疑（八）— USD 50,000 is not a cap", "https://www.safe.gov.cn/ningxia/2022/0929/1997.html", "full text fetched 2026-11-07"),
    "S02": ("SAFE, Tianjin", "2024 个人外汇（三）— 经常项目外汇业务指引 第64条 (outward remittance)", "https://www.safe.gov.cn/tianjin/2024/0229/2402.html", "full text fetched 2026-11-07"),
    "S03": ("SAFE, Tianjin", "2024 经常项目外汇政策问答案例（九）— 境外个人购汇", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html", "full text fetched 2026-11-07"),
    "S04": ("SAFE, Tianjin", "《个人外汇管理办法实施细则》(已修改) 全文", "https://www.safe.gov.cn/tianjin/2024/0430/2464.html", "official full-text page, quoted articles verified"),
    "S05": ("People's Bank of China / gov.cn", "《个人外汇管理办法》中国人民银行令〔2006〕第3号", "https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm", "full text fetched 2026-11-07"),
    "S06": ("People's Bank of China", "《个人外汇管理办法》PBOC mirror", "https://www.pbc.gov.cn/zhengwugongkai/4081330/4406346/4406348/2025092319185421938/index.html", "official page, quoted articles verified"),
    "S07": ("State Council / SAFE", "《中华人民共和国外汇管理条例》国务院令第532号 (2008 revision), full text", "https://www.safe.gov.cn/safe/2008/0806/5321.html", "full text fetched 2026-11-07"),
    "S08": ("SAFE, Guangdong", "关于个人网上办理外币兑换业务的温馨提示 (only legal channels)", "https://www.safe.gov.cn/guangdong/2020/0304/1668.html", "official excerpt verified"),
    "S09": ("SAFE", "《个人购汇申请书》及填报说明 (六不得)", "https://www.safe.gov.cn/safe/file/file/20210402/30fab7a9646f417ca9d2f67ff4c1e5f0.pdf", "official PDF excerpt verified"),
    "S10": ("SAFE, Xiamen", "个人外汇业务服务小贴士 (境外个人, 六不得)", "https://www.safe.gov.cn/xiamen/file/file/20211022/f4794075e84e40dd9394be523a52731b.pdf", "official PDF excerpt verified"),
    "S11": ("SAFE, Tianjin", "2025 个人外汇（八）— 关注名单有效期 (指引 第62条)", "https://www.safe.gov.cn/tianjin/2025/0613/2811.html", "official excerpt verified"),
    "S12": ("SAFE", "汇发〔2015〕49号 关于进一步完善个人外汇管理有关问题的通知", "https://www.safe.gov.cn/safe/2015/1231/5442.html", "official full-text page verified"),
    "S13": ("SAFE, Guangdong", "（已废止）汇发〔2015〕49号", "https://www.safe.gov.cn/guangdong/2016/0104/216.html", "official repeal marker verified"),
    "S14": ("SAFE, Hebei", "外汇违规案例：七起个人分拆结售汇案", "https://www.safe.gov.cn/hebei/2016/0328/615.html", "official enforcement case verified"),
    "S15": ("SAFE, Hebei", "外汇违规案例：曹某某个人分拆购付汇案", "https://www.safe.gov.cn/hebei/2016/0711/658.html", "official enforcement case verified"),
    "S16": ("SAFE, Shanghai", "个人用汇讲规矩 用好用活增便利", "https://www.safe.gov.cn/shanghai/2019/1213/1198.html", "official excerpt verified"),
    "S17": ("SAFE, Guangdong", "个人对外财产转移购付汇业务指南", "https://www.safe.gov.cn/guangdong/2021/0323/1994.html", "official guide verified"),
    "S18": ("People's Bank of China / SAFE", "有关负责人就《个人财产对外转移售付汇管理暂行办法》答记者问", "http://m.safe.gov.cn/safe/2004/1116/4134.html", "official press Q&A verified"),
    "S19": ("SAFE", "深入推进外汇管理改革 维护外汇市场健康有序发展 (汇发〔2017〕3号)", "https://www.safe.gov.cn/safe/2017/0126/12679.html", "official excerpt verified"),
    "S20": ("SAFE, Shanghai", "汇发〔2017〕3号 答记者问 — 利润汇出", "https://www.safe.gov.cn/shanghai/2017/0126/76.html", "official Q&A verified"),
    "S21": ("State Taxation Administration", "国家税务总局 国家外汇管理局公告2013年第40号 (税务备案)", "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html", "official full-text page verified"),
    "S22": ("State Taxation Administration", "如果我司需要向境外支付资金，哪些情形需要办理对外支付税务备案", "https://www.chinatax.gov.cn/chinatax/c102449/c5219874/content.html", "official Q&A verified"),
    "S23": ("State Taxation Administration", "《中华人民共和国个人所得税法》", "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html", "official full-text page verified"),
    "S24": ("State Taxation Administration, Shanghai", "财税〔2008〕132号 储蓄存款利息所得暂免征收个人所得税", "https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/grsds/200810/t288953.html", "official forwarding notice verified"),
    "S25": ("State Taxation Administration", "国家税务总局公告2017年第14号 非居民金融账户涉税信息尽职调查管理办法", "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5207016/content.html", "official full-text page verified"),
    "S26": ("People's Bank of China", "中国人民银行公告〔2014〕第5号 (±2% band; 3% spread)", "https://xining.pbc.gov.cn/zhengcehuobisi/125207/125217/125922/125945/2805761/index.html", "official announcement verified"),
    "S27": ("People's Bank of China", "2014年中国货币政策大事记 (银发〔2014〕188号 取消挂牌买卖价差管理)", "https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/2810732/index.html", "official chronology verified"),
    "S28": ("People's Bank of China", "2005 挂牌汇价管理答记者问 (historic 1%/4% spread caps)", "https://www.pbc.gov.cn/goutongjiaoliu/113456/113472/2827987/index.html", "official Q&A verified"),
    "S29": ("People's Bank of China + 7 agencies", "银发〔2026〕42号 关于进一步防范和处置虚拟货币等相关风险的通知", "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html", "full text fetched 2026-11-07"),
    "S30": ("People's Bank of China + 9 agencies", "银发〔2021〕237号 (now repealed)", "https://www.pbc.gov.cn/tiaofasi/144941/3581332/4348658/index.html", "full text fetched 2026-11-07"),
    "S31": ("State Council / gov.cn", "银发〔2021〕237号 国务院部门文件", "https://www.gov.cn/zhengce/zhengceku/2021-10/08/content_5641404.htm", "official page verified"),
    "S32": ("Supreme People's Court / Supreme People's Procuratorate (via Hunan gov)", "法释〔2019〕1号 非法买卖外汇司法解释", "http://www.hunan.gov.cn/zqt/zcsd/201901/t20190131_13641628.html", "official text verified"),
    "S33": ("Henan High People's Court", "法释〔2019〕1号 全文", "https://www.hncourt.gov.cn/public/detail.php?id=176932", "official court text verified"),
    "S34": ("Xuchang Intermediate People's Court", "刑法第225条 非法经营罪 条文与量刑 (official court publication)", "https://xczy.hncourt.gov.cn/public/detail.php?id=2739", "official court publication verified"),
    "S35": ("SAFE, Hubei", "关于规范银行卡境外大额提取现金交易的通知", "https://www.safe.gov.cn/hubei/2019/0305/851.html", "official full-text page verified"),
    "S35b": ("SAFE, Hebei", "规范银行卡境外大额提取现金交易 答记者问 (境外消费不占额度)", "https://www.safe.gov.cn/hebei/2018/0409/1010.html", "official Q&A verified"),
    "S36": ("SAFE, Hebei", "外汇知识问答：每次可带外币出境的限额", "http://www.safe.gov.cn/hebei/2019/0521/1366.html", "official Q&A verified"),
    "S37": ("SAFE, Tianjin (big5)", "携带外币现钞出入境管理暂行办法 (汇发〔2003〕102号)", "https://www.safe.gov.cn/big5/big5/www.safe.gov.cn/tianjin/2024/0430/2466.html", "official reprint verified"),
    "S38": ("People's Bank of China", "关于进一步优化跨境人民币政策 支持稳外贸稳外资的通知", "https://www.pbc.gov.cn/tiaofasi/144941/3581332/4158143/index.html", "official full-text page verified"),
    "S39": ("People's Bank of China, Guangzhou", "《粤港澳大湾区“跨境理财通”业务试点实施细则》问题解答（第一期）", "https://guangzhou.pbc.gov.cn/guangzhou/129196/4332364/4332374/4343888/index.html", "official Q&A verified"),
    "S40": ("Guangdong Provincial Financial Supervision Bureau", "跨境理财通实施细则 解读 (人民币跨境, 离岸兑换, 不占额度)", "http://gdjr.gd.gov.cn/gdjr/zwgk/jrzcfg/content/post_3520533.html", "official interpretation verified"),
    "S41": ("SAFE, Tianjin", "合格境内机构投资者（QDII）账户开立、使用和关闭", "http://www.safe.gov.cn/tianjin/2019/0214/1098.html", "official guide verified"),
    "S42": ("SAFE, Shanghai", "上海机制外汇及跨境人民币政策问答（2026年第一期）(指引 第66条)", "https://www.safe.gov.cn/shanghai/2026/0402/2412.html", "official Q&A verified"),
    "S43": ("SAFE, Chongqing", "常见外汇业务答疑手册 — 境外个人购汇本身无年度额度限制", "https://www.safe.gov.cn/chongqing/file/file/20190311/87806e211bb74eb4a44e71395c31cda9.pdf", "official PDF excerpt verified"),
    "S44": ("SAFE, Tianjin", "2021 服务贸易外汇管理问题解答（四）— 境外个人购汇税务凭证", "https://www.safe.gov.cn/tianjin/2021/1102/1777.html", "official Q&A verified"),
    "S45": ("SAFE, Shanghai", "外汇管理政策与业务问答（321）— 审核资金来源而非用途", "https://www.safe.gov.cn/shanghai/2019/0215/988.html", "official Q&A verified"),
    "S46": ("Bank of China", "中国银行电子银行个人服务转账汇款费率表 (个人跨境汇款)", "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "official bank fee table verified"),
    "S47": ("Bank of China", "国际结算业务资费标准 (对公)", "https://www.boc.cn/cbservice/cb3/cb33/200807/t20080701_852.html", "official bank fee table verified"),
    "S48": ("Bank of China", "关于调整部分贸易金融服务项目的公告 (全额到账 USD 15)", "https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html", "official bank notice verified"),
    "S49": ("Bank of China", "中行电子银行转账汇款大优惠(2024)", "https://www.boc.cn/ebanking/bi3/bi31/202312/t20231229_24338136.html", "official bank notice verified (expired promotion)"),
    "S50": ("Hong Kong Monetary Authority", "Half-yearly Monetary and Financial Stability Report, March 2012 (CNY/CNH disparity)", "https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201203/chapter4.pdf", "official HKMA report verified"),
    "S51": ("Hong Kong Monetary Authority", "Quarterly Bulletin, September 2014 (CNH premium +163 pips)", "https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201409/chapter4.pdf", "official HKMA report verified"),
    "S52": ("Hong Kong Monetary Authority", "Half-yearly Monetary and Financial Stability Report, March 2025 (CNY/CNH gap)", "https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb202503/E_Half-yearly_202503.pdf", "official HKMA report verified"),
    "S53": ("SAFE, Inner Mongolia", "个人外汇管理政策及常见问题解答 (资本项目未完全开放, QDII)", "https://www.safe.gov.cn/neimenggu/file/file/20200228/fa90770027ed4d919de981c09bc25751.pdf", "official PDF excerpt verified"),
    "S54": ("SAFE, Tianjin", "2025 个人外汇（18）— 指引 第61条 委托近亲属/他人代办", "https://www.safe.gov.cn/tianjin/2025/1223/2957.html", "official Q&A verified"),
    "S55": ("People's Bank of China, Hangzhou", "浙江跨境支付通累计结算金额破亿元 (2025)", "https://hangzhou.pbc.gov.cn/hangzhou/125264/5778339/index.html", "official PBOC branch article verified"),
    "S56": ("China Securities Regulatory Commission, Shanxi", "八部门联合发布新规，明确此类业务“境内严禁，境外严管” (2026)", "https://www.csrc.gov.cn/shanxi/c106408/c7616553/content.shtml", "official CSRC article verified"),
    # Added by session f5a5499c on 2026-11-11: the circular that cancels two of the 2004 rules
    # this page used to state as current. Read in full at source that day.
    "S57": ("SAFE", "汇发〔2014〕2号 关于进一步改进和调整资本项目外汇管理政策的通知 (已修改) — §6 简化个人财产转移售付汇管理", "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "full text fetched 2026-11-11"),
    # --- US: tax, reporting, treaty ---
    "U01": ("Internal Revenue Service", "Frequently asked questions about international individual tax matters", "https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-about-international-individual-tax-matters", "official FAQ verified"),
    "U02": ("Internal Revenue Service", "Publication 54, Tax Guide for U.S. Citizens and Resident Aliens Abroad", "https://www.irs.gov/publications/p54", "official publication verified"),
    "U03": ("Internal Revenue Service", "Publication 519, U.S. Tax Guide for Aliens", "https://www.irs.gov/publications/p519", "official publication verified"),
    "U04": ("Internal Revenue Service", "Publication 525, Taxable and Nontaxable Income (foreign currency transactions)", "https://www.irs.gov/publications/p525", "full text fetched 2026-11-07"),
    "U05": ("Internal Revenue Service", "Publication 514, Foreign Tax Credit for Individuals", "https://www.irs.gov/publications/p514", "official publication verified"),
    "U06": ("Internal Revenue Service", "Comparison of Form 8938 and FBAR requirements", "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements", "full text fetched 2026-11-07"),
    "U07": ("Internal Revenue Service", "Instructions for Form 8938", "https://www.irs.gov/instructions/i8938", "official instructions verified"),
    "U08": ("Internal Revenue Service", "FATCA information for individuals", "https://www.irs.gov/businesses/corporations/fatca-information-for-individuals", "official page verified"),
    "U09": ("Internal Revenue Service", "Gifts from foreign person (Form 3520, IRC 6039F)", "https://www.irs.gov/businesses/gifts-from-foreign-person", "full text fetched 2026-11-07"),
    "U10": ("Internal Revenue Service", "IRM 5.21.6 Foreign Financial Account Reporting", "https://www.irs.gov/irm/part5/irm_05-021-006", "official manual verified"),
    "U11": ("Internal Revenue Service", "IRM 4.26.16 Report of Foreign Bank and Financial Accounts (FBAR)", "https://www.irs.gov/irm/part4/irm_04-026-016", "official manual verified"),
    "U12": ("Internal Revenue Service", "Report of Foreign Bank and Financial Accounts (FBAR)", "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar", "official page verified"),
    "U13": ("Internal Revenue Service", "Streamlined Filing Compliance Procedures — U.S. taxpayers residing outside the United States", "https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-outside-the-united-states", "official page verified"),
    "U14": ("Internal Revenue Service", "Streamlined Filing Compliance Procedures — U.S. taxpayers residing in the United States", "https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-in-the-united-states", "official page verified"),
    "U15": ("Internal Revenue Service", "China — Tax treaty documents", "https://www.irs.gov/businesses/international-businesses/china-tax-treaty-documents", "official page verified"),
    "U16": ("Internal Revenue Service / U.S. Treasury", "United States–People's Republic of China Income Tax Convention (1984) + Protocol", "https://www.irs.gov/pub/irs-trty/china.pdf", "official treaty text verified"),
    "U17": ("U.S. Treasury / IRS", "Treasury Department Technical Explanation of the US–China Agreement", "https://www.irs.gov/pub/irs-trty/chintech.pdf", "official explanation verified"),
    "U18": ("Financial Crimes Enforcement Network", "FBAR Line Item Filing Instructions", "https://www.fincen.gov/system/files/shared/FBAR%20Line%20Item%20Filing%20Instructions.pdf", "official instructions verified"),
    "U19": ("Financial Crimes Enforcement Network", "Who Is A United States Person?", "https://www.fincen.gov/who-united-states-person", "official page verified"),
    "U20": ("eCFR / FinCEN, U.S. Treasury", "31 CFR 1010.821 Penalty adjustment and table", "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821", "full text fetched 2026-11-07"),
    "U21": ("Federal Register / U.S. SEC", "No Adjustment to Civil Monetary Penalty Amounts (2026) — OMB M-26-11", "https://www.federalregister.gov/documents/2026/07/07/2026-13629/no-adjustment-to-civil-monetary-penalty-amounts", "official notice verified"),
    "U22": ("U.S. Department of the Treasury", "Foreign Account Tax Compliance Act — Model Intergovernmental Agreements", "https://home.treasury.gov/policy-issues/tax-policy/foreign-account-tax-compliance-act", "official page verified"),
    "U23": ("U.S. Department of the Treasury", "U.S.–China Joint Fact Sheet, Sixth Meeting of the Strategic and Economic Dialogue (FATCA IGA in substance)", "https://home.treasury.gov/news/press-releases/jl2561", "official fact sheet verified"),
    "U24": ("Internal Revenue Service", "Offshore Income and Filing Information for Taxpayers with Foreign Accounts (FS-14-07)", "https://www.irs.gov/pub/irs-news/FS-14-07.pdf", "official IRS fact sheet verified"),
    "U25": ("Internal Revenue Service", "Foreign Gift and Trust Reporting on Forms 3520 and 3520-A", "https://www.irs.gov/pub/irs-npl/2023ntf-15-foreign-gift-and-trust-reporting-on-form-3520-and-3520-a.pdf", "official IRS training verified"),
    "U26": ("Financial Crimes Enforcement Network", "Report to Congress under §361(b) — 'The FBAR is not a tax return'", "https://www.fincen.gov/system/files/shared/ReportToCongress361.PDF", "official report verified"),
    "U27": ("U.S. Government Publishing Office (govinfo)", "26 U.S.C. §988 — Foreign currency transactions (2023 edition)", "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm", "official statute text; fetched 2026-11-09 (session-5e4816e0, reference_inputs.csv R18–R21)"),
    # --- project record ---
    "G01": ("GitHub — this repository (official project record)", "COORDINATION.md and branch/PR history", "https://github.com/sassnarep3-star/China3/blob/main/COORDINATION.md", "repository record verified via git + gh api"),
}

OFFICIAL_DOMAINS = (
    "safe.gov.cn", "pbc.gov.cn", "gov.cn", "chinatax.gov.cn", "moj.gov.cn",
    "hncourt.gov.cn", "csrc.gov.cn", "boc.cn", "hkma.gov.hk", "gd.gov.cn",
    "hunan.gov.cn", "zjwy.gov.cn", "hangzhou.pbc.gov.cn", "xining.pbc.gov.cn",
    "guangzhou.pbc.gov.cn", "shanghai.chinatax.gov.cn", "fgk.chinatax.gov.cn",
    "irs.gov", "fincen.gov", "ecfr.gov", "federalregister.gov", "govinfo.gov",
    "home.treasury.gov", "treasury.gov", "taxpayeradvocate.irs.gov",
    "github.com",
)

# ---------------------------------------------------------------------------
# TABLE DATA
# Every tuple: (id, ..., source_id, extra_source_ids, status)
# status: verified | unverified.  unverified rows MUST have an empty value field.
# ---------------------------------------------------------------------------

# china_rules: id, topic, value, scope_detail, source_id, extra, status
CHINA_RULES = [
    ("C01", "Who is a 'foreign individual'", "境外个人 = 持护照、港澳居民来往内地通行证、台湾居民来往大陆通行证的外国公民（含无国籍人）及港澳台同胞；境内个人 = 持中国居民身份证/军人证/武警证的中国公民", "《个人外汇管理办法》第37条；决定购汇规则适用哪一套", "S05", "", "verified"),
    ("C02", "Current vs capital account", "经常项目项下的个人外汇业务按可兑换原则管理；资本项目项下按可兑换进程管理", "《个人外汇管理办法》第3条；《外汇管理条例》第5条：国家对经常性国际支付和转移不予限制", "S05", "S07", "verified"),
    ("C03", "Annual FX facilitation amount", "个人结汇和境内个人购汇实行年度便利化额度管理，每人每年等值5万美元", "《经常项目外汇业务指引（2020年版）》第54/55条", "S01", "S04", "verified"),
    ("C04", "USD 50,000 is NOT a legal cap", "对真实、合法的经常项目和已开放的资本项目下购汇和结汇都没有金额限制；年度便利化额度不是限额，只是超过等值5万美元不能仅凭本人有效身份证件办理", "SAFE 宁夏 2022 政策释疑（八），引述指引第54–57条", "S01", "", "verified"),
    ("C05", "FX purchase above the convenience amount", "境内个人凭本人有效身份证件和有交易额的购汇资金用途材料，在银行办理不占用年度便利化额度的经常项目购汇", "指引第57条；须有真实交易背景", "S01", "", "verified"),
    ("C06", "Outward remittance from an FX account", "外汇账户内外汇汇出境外用于经常项目支出：当日累计等值5万美元以下（含）凭本人有效身份证件；超过的，凭身份证件和有交易额的相关材料；银行审核购汇用途与付汇用途一致性", "指引第64条（一）", "S02", "", "verified"),
    ("C07", "Outward remittance of foreign banknotes", "持外币现钞汇出：当日累计等值1万美元以下（含）凭身份证件；超过的须有海关申报单或原存款银行提钞单据及有交易额的相关材料", "指引第64条（二）", "S02", "", "verified"),
    ("C08", "Foreign individual — purchase of FX", "境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇", "指引第59条 —— 本课题最关键的一条", "S03", "", "verified"),
    ("C09", "Foreign individual — no annual quota on FX purchase", "境外个人购汇本身无年度额度限制", "SAFE 重庆《常见外汇业务答疑手册》问答；与指引第59条一致", "S43", "S03", "verified"),
    ("C10", "Permanent residence ID exception", "持有外国人永久居留身份证的境外个人适用购汇年度便利化额度", "指引第59条", "S03", "", "verified"),
    ("C11", "Foreign individual — what the bank checks", "境外个人购付汇审核的是人民币资金来源，而非外汇资金用途", "SAFE 上海 问答（321）；据此，资金来源合法性与完税凭证是关键", "S45", "", "verified"),
    ("C12", "Reconversion of unused RMB", "境外个人原兑换未用完的人民币兑回外汇，凭本人有效身份证件和原兑换水单办理；原兑换水单的兑回有效期为自兑换日起24个月", "《实施细则》第13条（二）；当日累计≤等值500美元（离境前境内关外≤1000美元）可仅凭身份证件", "S04", "", "verified"),
    ("C13", "Unused inward FX can be sent back", "境外个人未使用的境外汇入外汇，可以凭本人有效身份证件在银行办理原路汇回", "《个人外汇管理办法》第14条", "S05", "", "verified"),
    ("C14", "Sale of China real estate by a foreign individual", "境外个人出售境内商品房所得人民币，经外汇局核准可以购汇汇出", "《个人外汇管理办法》第22条 —— 资本项目，需核准", "S05", "", "verified"),
    ("C15", "Foreign individual's lawful property transfer", "境外个人在境内的合法财产对外转移，应当按照个人财产对外转移的有关外汇管理规定办理", "《个人外汇管理办法》第26条", "S05", "", "verified"),
    ("C16", "Tax evidence for foreign-individual FX purchase", "境外个人将境内取得的服务贸易、收益和经常转移项下人民币收入购汇汇出，可凭身份证件和有交易额的相关证明材料（含税务凭证）办理；税务凭证包括《服务贸易等项目对外支付税务备案表》（含电子）、完税证明或免税证明", "SAFE 天津 2021 服务贸易问答（四）", "S44", "", "verified"),
    ("C17", "Tax-filing (备案) threshold for outbound payments", "境内机构和个人向境外单笔支付等值5万美元以上（不含）特定项目外汇资金，应向所在地主管税务机关进行税务备案", "国家税务总局 国家外汇管理局公告2013年第40号 第一条 —— 备案不是税，但银行付汇前常要求", "S21", "S22", "verified"),
    ("C18", "The 'six prohibitions' for FX purchase", "不得虚假申报；不得提供不实材料；不得出借本人便利化额度；不得借用他人便利化额度实施分拆购汇；不得用于境外买房、证券投资、购买人寿保险和投资性返还分红类保险等尚未开放的资本项目；不得参与洗钱、赌博、逃税、地下钱庄交易", "《个人购汇申请书》及 SAFE 厦门服务小贴士", "S09", "S10", "verified"),
    ("C19", "FX purchase application form", "自2017年起境内个人购汇需如实填报《个人购汇申请书》；不涉及政策调整，年度便利化额度没有变化", "SAFE 官方申请表/填报说明", "S09", "", "verified"),
    ("C20", "Anti-splitting 'watch list'", "外汇局对借用他人便利化额度及其他方式规避便利化额度及真实性管理的个人列入'关注名单'；关注期限为列入当年及之后连续2年；关注期内办理结售汇须凭身份证件和有交易额的相关材料", "指引第62条；汇发〔2015〕49号已废止，现行依据为2020年指引", "S11", "S13", "verified"),
    ("C21", "Splitting is expressly prohibited", "银行和个人在办理个人外汇业务时，不得以分拆等方式逃避限额监管，也不得使用虚假商业单据或者凭证逃避真实性管理", "《个人外汇管理办法》第7条", "S05", "", "verified"),
    ("C22", "Penalty — evasion of FX (逃汇)", "责令限期调回外汇，处逃汇金额30%以下的罚款；情节严重的，处逃汇金额30%以上等值以下的罚款；构成犯罪的依法追究刑事责任", "《外汇管理条例》第39条", "S07", "", "verified"),
    ("C23", "Penalty — illegal FX trading (非法买卖外汇)", "私自买卖、变相买卖、倒买倒卖外汇或非法介绍买卖外汇数额较大的：警告、没收违法所得、处违法金额30%以下罚款；情节严重的30%以上等值以下；构成犯罪的依法追究刑事责任", "《外汇管理条例》第45条（2008修订版）", "S07", "", "verified"),
    ("C24", "Penalty — fraudulent FX purchase (非法套汇)", "以虚假、无效交易单证等骗购外汇：责令回兑，处非法套汇金额30%以下罚款；情节严重的30%以上等值以下", "《外汇管理条例》第40条", "S07", "", "verified"),
    ("C25", "Only legal conversion channels", "个人结售汇必须通过具备资格的外汇指定银行、本外币兑换特许机构及外币代兑机构办理；公司、中介网站/APP私下换汇、朋友圈换汇、外汇黄牛、地下钱庄等其他渠道都不合法", "SAFE 广东 2020 提示", "S08", "", "verified"),
    ("C26", "Criminal thresholds for illegal FX trading", "'情节严重'：非法经营数额500万元以上或违法所得10万元以上；'情节特别严重'：非法经营数额2500万元以上或违法所得50万元以上", "法释〔2019〕1号 第3、4条；另设250万/1250万+加重情节的次级标准", "S32", "S33", "verified"),
    ("C27", "Criminal offence", "实施倒买倒卖外汇或者变相买卖外汇等非法买卖外汇行为，扰乱金融市场秩序、情节严重的，依刑法第225条第4项以非法经营罪定罪处罚", "法释〔2019〕1号 第2条", "S33", "", "verified"),
    ("C28", "Criminal sentence", "非法经营罪情节严重：5年以下有期徒刑或拘役，并处或单处违法所得1倍以上5倍以下罚金；情节特别严重：5年以上有期徒刑，并处违法所得1倍以上5倍以下罚金或没收财产", "《刑法》第225条（官方法院文本）", "S34", "", "verified"),
    ("C29", "Personal property transfer — who approves it (2004 tiering cancelled in 2014)", "移民财产转移由移民原户籍所在地外汇局审批；继承财产转移由被继承人生前户籍所在地外汇局审批。汇发〔2014〕2号 §6(1)取消财产转移总金额超过等值人民币50万元报国家外汇管理局备案的要求，因此2004年答记者问所述'≥50万元报总局批准'的分级已不再适用", "汇发〔2014〕2号 §6(1)", "S57", "S18", "verified"),
    ("C30", "Personal property transfer — no forced staging since 2014", "2004年办法第六条曾规定移民财产转移'分步汇出'：首次不超过一半，满一年后不超过剩余的一半，满两年后可汇出全部余额。汇发〔2014〕2号 §6(2)取消移民财产转移分次汇出的要求：办理核准手续后，银行可在核准件审批额度内一次或分次汇出相关资金", "汇发〔2014〕2号 §6(2)（2004年第六条已被取消）", "S57", "S18", "verified"),
    ("C31", "Inheritance transfer", "外国公民或港澳台居民将依法继承的境内遗产变现，可购汇汇出；从同一被继承人继承的全部财产须一次性申请，可一次或分次汇出", "《个人财产对外转移售付汇管理暂行办法》及 SAFE 业务指南", "S17", "", "verified"),
    ("C32", "Company profit / dividend repatriation", "境内机构真实合规的利润，按程序出具证明材料可直接在银行办理汇出，没有任何限制；等值5万美元（不含）以上利润汇出须审核董事会利润分配决议、税务备案表原件、经审计财务报表，并先依法弥补以前年度亏损", "汇发〔2017〕3号；属于经常项目", "S20", "S19", "verified"),
    ("C33", "Overseas ATM cash withdrawals", "个人持境内银行卡在境外提取现金，本人名下银行卡（含附属卡）合计每个自然年度不得超过等值10万元人民币；超过则本年及次年暂停境外提现；每卡每日等值1万元人民币", "SAFE 2017 通知，2018-01-01起实施", "S35", "", "verified"),
    ("C34", "Overseas card spending", "个人持卡境外消费不受10万元提现额度影响，且不占用个人年度5万美元购汇额度", "SAFE 答记者问 —— 但消费并不产生可自由支配的境外USD存款", "S35b", "", "verified"),
    ("C35", "Carrying foreign banknotes out", "携带外币现钞出境：≤等值5000美元无需《携带证》；5000–10000美元（含）须向银行申领《携带证》；原则上不得携带超过等值10000美元，特殊情况须向外汇局申领", "汇发〔2003〕102号", "S36", "S37", "verified"),
    ("C36", "CNY/USD trading band", "自2014年3月17日起，银行间即期外汇市场人民币兑美元交易价可在中国外汇交易中心公布的当日中间价上下2%幅度内浮动", "中国人民银行公告〔2014〕第5号", "S26", "", "verified"),
    ("C37", "Bank customer spread is deregulated", "2014年3月将美元现汇买卖价差幅度由2%扩大至3%；2014年7月1日银发〔2014〕188号取消银行对客户各币种挂牌买卖价差管理，银行可根据市场供求自主定价", "PBOC 公告第5号 + 2014年货币政策大事记", "S26", "S27", "verified"),
    ("C38", "Virtual currency is prohibited", "虚拟货币相关业务活动属于非法金融活动；在境内开展法定货币与虚拟货币兑换业务一律严格禁止、坚决依法取缔；境外单位和个人不得以任何形式非法向境内主体提供虚拟货币相关服务", "银发〔2026〕42号 第（一）项 —— 现行有效", "S29", "S56", "verified"),
    ("C39", "2021 notice repealed", "银发〔2026〕42号自发布之日起施行；中国人民银行等十部门《关于进一步防范和处置虚拟货币交易炒作风险的通知》（银发〔2021〕237号）同时废止", "PBOC 2026-02-06 官方全文", "S29", "S30", "verified"),
    ("C40", "RMB-linked stablecoins", "未经相关部门依法依规同意，境内外任何单位和个人不得在境外发行挂钩人民币的稳定币", "银发〔2026〕42号 第（一）项", "S29", "", "verified"),
    ("C41", "Cross-border RMB settlement for individuals", "支持境内银行在'展业三原则'基础上，为个人办理经常项目下跨境人民币结算业务，进一步便利个人薪酬等合法合规收入的跨境收付", "PBOC 关于进一步优化跨境人民币政策的通知 第（十三）项", "S38", "", "verified"),
    ("C42", "Wealth Management Connect", "南向通/北向通总额度各1500亿元人民币；单个投资者额度100万元人民币；业务均使用人民币跨境划转，资金兑换在离岸市场完成，不占用个人外汇额度", "PBOC 广州 跨境理财通问答 + 广东省地方金融监管局解读", "S39", "S40", "verified"),
    ("C43", "QDII", "QDII境外投资累计净汇出额（含外汇及人民币资金）不得超过经批准的投资额度；境外投资本金及收益可以外汇或人民币形式汇回", "SAFE QDII 账户业务指南（国家外汇管理局公告2013年第1号）", "S41", "S53", "verified"),
    ("C44", "Cross-border e-commerce", "境内个人从事跨境电子商务，可通过本人外汇账户办理跨境电子商务外汇结算；提供有交易额的材料或交易电子信息的，不占用个人年度便利化额度", "指引第66条；SAFE 上海 2026 问答", "S42", "", "verified"),
    ("C45", "China individual income tax rates", "综合所得适用3%至45%超额累进税率；利息股息红利所得、财产租赁所得、财产转让所得和偶然所得适用20%比例税率", "《中华人民共和国个人所得税法》第3条", "S23", "", "verified"),
    ("C46", "Bank deposit interest exempt in China", "自2008年10月9日起，对储蓄存款利息所得暂免征收个人所得税", "财税〔2008〕132号", "S24", "", "verified"),
    ("C47", "CRS due diligence in China", "境内金融机构须识别非居民金融账户、收集并报送账户信息，每年5月31日前报送", "国家税务总局公告2017年第14号", "S25", "", "verified"),
    ("C48", "Capital account not fully open", "境外买房、购买人寿保险及返还分红类保险、股票投资等均不允许；个人对外投资只能通过规定渠道如QDII等实现", "SAFE 内蒙古 个人外汇管理政策问答", "S53", "S09", "verified"),
    ("C49", "Definition conflict — State Council regulation", "《外汇管理条例》第52条（二）：境内个人是指中国公民和在中华人民共和国境内连续居住满1年的外国人", "国务院令第532号 —— 与下一条的定义存在张力", "S07", "", "verified"),
    ("C50", "Definition conflict — PBOC measure", "《个人外汇管理办法》第37条（二）：境外个人是指持护照等证件的外国公民（包括无国籍人）以及港澳台同胞；第28条：银行按个人开户时提供的身份证件等证明材料确定账户主体类别", "人民银行令〔2006〕第3号 —— 实际操作以开户证件判定", "S05", "S06", "verified"),
]

# us_rules: id, topic, value, scope_detail, source_id, extra, status
US_RULES = [
    ("U01", "Worldwide income", "美国公民或居住在外国的居民外国人，其全球所得（worldwide income）须缴纳美国所得税，无论居住在哪里", "IRS 国际个人税务 FAQ 第1问", "U01", "U02", "verified"),
    ("U02", "Worldwide income (Publication 54)", "If you are a U.S. citizen or resident alien living and working abroad, you are taxed on your worldwide income", "IRS Publication 54 第4章", "U02", "", "verified"),
    ("U03", "FBAR filing trigger", "境外金融账户合计价值在日历年内任何时候超过10,000美元，须提交 FinCEN Form 114 (FBAR)", "IRS Form 8938 / FBAR 对照表", "U06", "U19", "verified"),
    ("U04", "FBAR due date", "4月15日前送达；自动延期6个月至10月15日", "IRS 对照表：Received by April 15 (6-month automatic extension to Oct 15)", "U06", "U18", "verified"),
    ("U05", "FBAR is not a tax return", "FBAR 不是纳税申报表，不与 Form 1040 一起提交；须通过 FinCEN BSA E-Filing System 电子提交", "IRS 对照表 / FinCEN 报告", "U06", "U26", "verified"),
    ("U06", "FBAR non-willful maximum penalty", "$16,536 per violation（2025-01-17 起评估的处罚，按 31 CFR 1010.821 通胀调整表）", "法定基础 $10,000（31 USC 5321(a)(5)(B)(i)），经通胀调整", "U20", "U11", "verified"),
    ("U07", "FBAR willful maximum penalty", "$165,353 或违规时账户余额的 50%，取较大者", "31 CFR 1010.821 表（31 USC 5321(a)(5)(C)(i)(I)）；无 reasonable cause 抗辩", "U20", "U18", "verified"),
    ("U08", "2026 inflation adjustment cancelled", "OMB M-26-11 取消 2026 年民事罚款通胀调整；各机构继续使用 2025 年金额", "因 2025 年 10 月 CPI-U 数据缺失；Federal Register 多机构公告一致", "U21", "U20", "verified"),
    ("U09", "Form 8938 thresholds — living in the U.S.", "未婚/已婚分开申报：年末 >$50,000 或年内任何时候 >$75,000；已婚合并申报：>$100,000 / >$150,000", "IRS Form 8938 / FBAR 对照表", "U06", "U07", "verified"),
    ("U10", "Form 8938 thresholds — living abroad", "未婚/已婚分开申报：年末 >$200,000 或年内任何时候 >$300,000；已婚合并申报：>$400,000 / >$600,000", "IRS 对照表；'living abroad' 有独立判定标准", "U06", "U07", "verified"),
    ("U11", "Form 8938 penalty", "未披露最高 $10,000；IRS 通知后每 30 天另加 $10,000，额外罚款上限 $50,000（合计潜在 $60,000）", "IRS 对照表 / IRM 5.21.6", "U06", "U10", "verified"),
    ("U12", "40% understatement penalty", "因未披露境外金融资产导致的少缴税款，另适用 40% 的重大少报罚款", "IRS FATCA information for individuals", "U08", "", "verified"),
    ("U13", "Both forms may be required", "Form 8938 的申报义务不替代也不影响 FBAR 义务；纳税人可能须同时提交两份表，且各自适用独立罚款", "IRS 对照表首段", "U06", "", "verified"),
    ("U14", "Foreign gifts are not income tax", "境外赠与/遗赠不属于所得税应税项目；若同一非居民外国个人或外国遗产在纳税年度内合计超过 $100,000，须提交 Form 3520 第四部分", "IRS Gifts from foreign person", "U09", "U25", "verified"),
    ("U15", "Form 3520 penalty", "未按时/完整申报：每月按赠与额的 5% 处罚，最高为赠与额的 25%（有合理事由可免责）", "IRC 6039F(c)；IRS 官方页面", "U09", "U25", "verified"),
    ("U16", "Form 3520 corporate/partnership gift threshold", "$20,116 for 2025；$20,573 for 2026（每年通胀调整）", "IRS Gifts from foreign person（2026 年更新）", "U09", "", "verified"),
    ("U17", "Personal foreign-currency gain ($200 rule)", "个人外币交易因汇率变动产生的收益，不超过 $200 的不计入所得；超过 $200 的，个人交易例外不适用； Pub. 525 的'按资本利得申报'以'个人交易'为前提（§988(e)(3) 排除 §162/§212 费用）；非个人交易按 §988(a)(1)(A) 作为普通收入", "IRS Publication 525 'Foreign currency transactions' + 26 U.S.C. §988 (govinfo)", "U04", "U27", "verified"),
    ("U18", "Foreign tax credit", "外国所得税抵免通过 Form 1116 申报；抵免额为已付外国税与 FTC 限额中的较小者", "IRS Publication 514", "U05", "", "verified"),
    ("U19", "Foreign earned income exclusion", "Form 2555 境外所得排除要求外国税务住所（tax home）；已排除所得对应的外国税不能再抵免或扣除", "IRS Publication 54 / 国际 FAQ", "U02", "U01", "verified"),
    ("U20", "US–China treaty source-country cap", "1984 年协定将缔约国对另一方居民取得的股息、利息、特许权使用费的来源国税率限制为不超过 10%", "IRS 托管的中美税收协定总统送交文本", "U16", "U15", "verified"),
    ("U21", "Saving clause", "Notwithstanding any provision of the Agreement, the United States may tax its citizens（议定书第2款）；技术解释重申美国可在任何情况下对其公民的股息/利息/特许权使用费征税", "协定议定书 + Treasury 技术解释", "U16", "U17", "verified"),
    ("U22", "Streamlined Foreign Offshore Procedures", "补报最近 3 年所得税申报表（含 3520/5471/8938 等信息表）+ 最近 6 年 FBAR；完全合规者不承担未申报/未缴纳、准确性、信息表或 FBAR 罚款", "须为非故意（non-willful）并签署 Form 14653 声明", "U13", "", "verified"),
    ("U23", "Streamlined Domestic Offshore Procedures", "补报最近 3 年修订申报表 + 最近 6 年 FBAR，并缴纳 Title 26 miscellaneous offshore penalty", "须签署 Form 14654 声明", "U14", "", "verified"),
    ("U24", "Delinquent FBAR filing", "若 IRS 尚未联系且未被民事/刑事调查，应尽快补交逾期 FBAR 以尽量降低潜在罚款", "IRS FBAR 页面", "U12", "", "verified"),
    ("U25", "FBAR valuation in USD", "按账户币种确定最大价值，并以日历年末汇率折算为美元申报", "IRS 对照表", "U06", "U18", "verified"),
    ("U26", "FATCA intergovernmental agreement status", "2014 年中美战略与经济对话联合成果单：双方就 FATCA 政府间协议达成'实质性一致'（agreement in substance），并承诺 2014 年底前签署；美方将中国金融机构视为 deemed-compliant", "美国财政部官方文件；本轮研究未找到已签署的中美大陆 IGA 全文", "U23", "U22", "verified"),
    ("U27", "No tax return → no Form 8938", "若某纳税年度无须提交所得税申报表，则无论境外金融资产价值多少都无须提交 Form 8938", "IRS FATCA information for individuals", "U08", "", "verified"),
    ("U28", "Criminal exposure", "FBAR 故意违规还可能承担刑事责任；Form 8938 未申报亦可能涉及刑事处罚", "IRS IRM 5.21.6 / FATCA 页面", "U10", "U08", "verified"),
]

# channels: id, group, channel, who, limit_or_condition, pros, cons, penalty_exposure, source_id, extra, status
CHANNELS = [
    ("CH01", "Lawful", "年度便利化额度内购汇 + 汇出（境内个人）", "持中国居民身份证的境内个人", "每人每年等值5万美元；凭身份证件；须填《个人购汇申请书》", "手续最简便；无需交易证明材料", "仅适用于境内个人；不得用于未开放资本项目；额度按人按年", "违规用途：条例第44条 30%以下/情节严重30%以上等值以下", "S01", "S09", "verified"),
    ("CH02", "Lawful", "不占用额度的经常项目购汇（凭真实交易材料）", "境内个人；有真实经常项目支出", "无金额上限，但须有交易额的购汇资金用途材料并经银行真实性审核", "不受5万美元便利化额度约束；合法合规", "必须有真实、可证明的经常项目用途；用途须与付汇一致；不能用于转移普通储蓄", "虚假材料构成非法套汇：30%以下/情节严重30%以上等值以下", "S01", "S02", "verified"),
    ("CH03", "Lawful", "外汇储蓄账户内已有外汇直接汇出", "账户内已持有外汇的个人", "当日累计≤等值5万美元凭身份证件；超过须有交易额相关材料", "无需再做人民币→美元兑换，省去一次买卖价差", "需先合法持有外汇；仍受用途真实性审核", "用途不符：条例第44条", "S02", "", "verified"),
    ("CH04", "Lawful", "境外个人以境内合法人民币收入购汇汇出（含税务凭证）", "境外个人（含持护照的美国公民）", "凭身份证件 + 有交易额的购汇资金来源材料（含税务凭证）；无年度额度限制", "本课题最贴合身份的合法通道；无5万美元年度额度；审核的是资金来源而非用途", "须证明人民币来源合法且已完税/免税；单笔>5万美元对外支付可能需税务备案表；银行逐笔审核", "材料不实 → 条例第40/45条及刑事责任", "S03", "S43", "verified"),
    ("CH05", "Lawful", "境外个人原兑换未用完的人民币兑回外汇", "境外个人，持有原兑换水单", "凭身份证件 + 原兑换水单；水单自兑换日起24个月内有效；小额当日≤500美元（离境前境内关外≤1000美元）可仅凭证件", "无需年度额度；不涉及新增完税证明", "仅适用于'原兑换未用完'的人民币；水单过期失效", "伪造水单 → 非法套汇", "S04", "S05", "verified"),
    ("CH06", "Lawful", "境外个人未使用的境外汇入外汇原路汇回", "境外个人", "凭本人有效身份证件即可办理", "手续简单", "仅适用于未使用的境外汇入外汇；不能把人民币储蓄变成美元", "—", "S05", "", "verified"),
    ("CH07", "Lawful (approval)", "境外个人出售境内商品房所得人民币购汇汇出", "境外个人出售境内自用商品房", "须经外汇局核准；按资本项目管理", "为资本性质的房产所得提供合法出口", "范围窄；需核准、产权与完税材料；耗时", "未经批准擅自转移 → 条例第39条 逃汇罚则", "S05", "", "verified"),
    ("CH08", "Lawful (approval)", "移民财产转移 / 继承财产转移", "取得外国永居或外国公民身份的移民；外国公民/港澳台居民继承人", "<等值50万元人民币由省级分局审核；≥50万元报国家外汇管理局批准；≥20万元移民转移'一次申请、分步汇出'（2年）", "为资本性质的个人财产提供法定通道；可一次性申请全部财产", "仅适用于移民/继承两类；须证明合法来源、无争议、税务证明；资金分批汇出、周期长", "虚假材料骗购外汇 → 条例第40条 30%以下/情节严重30%以上等值以下", "S17", "S18", "verified"),
    ("CH09", "Lawful", "服务贸易 / 收益 / 经常转移项下购汇汇出（境外个人）", "取得境内服务贸易、收益、经常转移收入的境外个人", "凭身份证件 + 有交易额证明材料（含税务备案表/完税证明/免税证明）", "与境外个人身份规则衔接；可汇出、可存入外汇账户或按规定携带出境", "须有明确收入性质与完税凭证", "单笔>5万美元未备案 → 无法付汇；虚假备案有法律风险", "S44", "S21", "verified"),
    ("CH10", "Lawful", "境内机构利润 / 股息汇出", "资金属于外商投资企业或境内机构（而非个人）", "真实合规利润按程序出具证明材料可直接在银行办理，无金额限制；>等值5万美元须董事会决议、税务备案表原件、经审计财务报表；须先弥补以前年度亏损", "经常项目，无金额上限", "仅适用于企业资金；个人不能直接套用；审计与税务材料要求高", "虚假单证 → 条例第40条", "S20", "S19", "verified"),
    ("CH11", "Lawful", "个人经常项目跨境人民币结算（薪酬等合法收入）", "境内个人/境外个人的合法经常项目人民币收入", "银行按'展业三原则'办理；人民币跨境，兑换在离岸市场完成", "不占用个人购汇便利化额度；可避开在岸结售汇环节", "仅覆盖真实经常项目收入；离岸兑换按 CNH 汇率，存在境内外价差", "虚构交易 → 逃汇/非法套汇", "S38", "S40", "verified"),
    ("CH12", "Lawful (offshore leg)", "离岸市场（CNH，如香港）兑换成美元", "已合法将人民币划转到离岸账户者", "资金兑换在离岸市场完成；需先有合法的跨境人民币划转通道", "离岸汇率由市场决定；不涉及个人5万美元购汇额度", "CNY 与 CNH 存在价差（HKMA 有官方观测）；需境外账户与合规资金通道；不能绕过境内资金来源审查", "绕过审查 → 条例第39条", "S40", "S52", "verified"),
    ("CH13", "Lawful", "跨境支付通（内地 IBPS 与香港 FPS 直连，2025）", "内地与香港居民；个人经常项目场景", "双边本币汇款、实时到账；内地居民可办理年度购汇额度内对港汇款及留学、就医、公共缴费等", "手续简便、实时到账、双边本币汇款可节省汇兑手续与费用", "2025 年新试点；有额度与场景限制；不是大额资本转移通道", "超额/虚假用途按现行外汇规定处理", "S55", "", "verified"),
    ("CH14", "Lawful (closed loop)", "粤港澳大湾区'跨境理财通'南向通", "大湾区内地9市户籍或连续缴社保/个税满5年；2年以上投资经历；近3个月家庭金融净资产≥100万元或金融资产≥200万元", "个人额度100万元人民币；南向通总额度1500亿元；闭环汇划；人民币跨境", "不占用个人外汇额度；资金兑换在离岸市场完成", "资金闭环、只能购买合资格投资产品，赎回后回到内地；不是取现通道；资格门槛高", "违规使用按外汇管理规定处理", "S39", "S40", "verified"),
    ("CH15", "Lawful (institutional)", "QDII / 商业银行代客境外理财 / 基金公司境外证券投资", "通过具备资格的境内机构投资的境内个人", "机构须有外汇局批准的投资额度；累计净汇出额不得超过批准额度；本金收益可汇回", "个人对外投资的法定开放渠道", "占用机构额度；是投资而非把储蓄换成美元现金；赎回资金回流境内账户", "超额度/违规汇兑可按条例处罚", "S41", "S53", "verified"),
    ("CH16", "Lawful (registration)", "境内个人对外直接投资（ODI）", "境内个人", "须符合有关规定并经外汇局核准/登记后方可购汇或以自有外汇汇出", "为资本项目资金出境提供登记通道", "须事先核准与外汇登记；不适用于单纯把个人储蓄换成美元", "未登记擅自汇出 → 条例第39/43条", "S05", "S07", "verified"),
    ("CH17", "Lawful", "个人货物贸易 / 跨境电子商务外汇结算", "个人对外贸易经营者、个体工商户、跨境电商个人", "可开立外汇结算账户；提供有交易额材料或交易电子信息的不占用年度便利化额度", "有真实贸易背景时不受个人额度限制", "须有真实货物贸易；账户视同机构管理", "虚假贸易单证 → 条例第40条", "S42", "S16", "verified"),
    ("CH18", "Lawful", "携带外币现钞出境", "出境人员", "≤等值5000美元无需《携带证》；5000–10000美元（含）向银行申领《携带证》；原则上不得>10000美元，特殊情况须外汇局批准", "无需银行汇款；手续直接", "金额极小；携带大额现钞有安全与申报风险；不产生境外银行存款", "违反携带规定：警告，可处违法金额20%以下罚款（条例第42条）", "S36", "S07", "verified"),
    ("CH19", "Lawful", "境内银行卡境外提取现金", "持有境内银行卡的个人", "本人名下所有卡合计每自然年度≤等值10万元人民币；每卡每日≤等值1万元人民币；超额本年及次年暂停", "便捷、无需购汇手续；境外消费不占额度", "仅能取得现钞；额度小；不产生可转账的美元存款", "超额/借用他人卡按条例处罚", "S35", "S35b", "verified"),
    ("CH20", "Lawful", "境外刷卡消费 / 移动支付", "持有境内银行卡的个人", "境外消费不占用个人年度便利化购汇额度，也不受10万元提现额度影响", "日常境外支出最便利", "不产生可自由支配的境外美元资金；不能用于转移本金", "—", "S35b", "", "verified"),
    ("CH21", "Lawful", "外币现钞汇出境外", "持有外币现钞的个人", "当日累计≤等值1万美元凭身份证件；超过须身份证件 + 海关申报单/原提钞单据 + 有交易额材料", "可直接汇出现钞", "金额门槛低；需来源证明；钞户与汇户价格通常不同", "来源不明 → 条例第39/45条", "S02", "", "verified"),
    ("CH22", "Lawful", "委托近亲属 / 他人代办购汇结汇", "个人（境内/境外）", "年度便利化额度内可委托近亲属；不占额度的可委托他人（含近亲属），须双方证件、委托书和有交易额材料", "本人不在境内时仍可办理", "委托书与关系材料要求；不改变额度与真实性规则", "借名办理 → 关注名单", "S54", "", "verified"),
    ("CH23", "Lawful", "个人外汇结算账户（对外贸易经营者）", "已办理工商登记/执业手续的个人", "购汇和结汇视同机构管理，不受年度总额限制，凭真实贸易单据办理", "经营性外汇不受5万美元额度约束", "须有真实贸易主体资格与单据", "虚假单据 → 非法套汇", "S16", "", "verified"),
    ("CH24", "Lawful (approval)", "境内个人境外合法资本项目收入结汇", "境内个人", "须经外汇局核准后方可结汇", "为境外资本项目收入的合法回流通道", "方向是流入而非流出；需核准", "擅自结汇 → 条例第41条", "S05", "", "verified"),
    ("CH25", "PROHIBITED", "分拆购汇 / '蚂蚁搬家' / 借用他人额度", "—", "5个以上不同个人同日、隔日或连续多日分别购汇后汇给境外同一人或机构，是 SAFE 列明的分拆特征", "无（被明确禁止）", "被列入'关注名单'、当年及之后连续2年不享受便利化额度；SAFE 已公布多起处罚案例", "逃汇：30%以下罚款，情节严重30%以上等值以下；构成犯罪追究刑事责任", "S14", "S11", "verified"),
    ("CH26", "PROHIBITED", "地下钱庄 / 换汇黄牛 / 朋友圈换汇 / 中介网站或 APP 私下换汇", "—", "SAFE 明确：这些渠道都不合法；个人结售汇只能通过具备资格的银行、特许兑换机构、代兑机构", "无（被明确禁止）", "资金无法律保障、易被骗；银行监测与反洗钱调查", "条例第45条：警告、没收违法所得、30%以下罚款，情节严重30%以上等值以下；非法经营罪 5年以下/5年以上 + 1–5倍罚金", "S08", "S07", "verified"),
    ("CH27", "PROHIBITED", "虚拟货币 / USDT / 稳定币兑换出境", "—", "法定货币与虚拟货币兑换业务属于非法金融活动，一律严格禁止；境外单位和个人不得非法向境内主体提供相关服务；金融机构不得提供账户、划转、清算服务", "无（被明确禁止）", "2026 年新规延续并强化禁令；民事法律行为可能无效、损失自担；涉洗钱/非法经营刑事风险", "银发〔2026〕42号第（十八）（十九）项；构成犯罪依法追究刑事责任", "S29", "S56", "verified"),
    ("CH28", "PROHIBITED", "虚假交易单证 / 虚开发票骗购外汇", "—", "以虚假、无效交易单证等向金融机构骗购外汇属于非法套汇", "无（被明确禁止）", "银行真实性审核 + 税务备案交叉核验", "条例第40条：责令回兑，30%以下罚款，情节严重30%以上等值以下；构成犯罪追刑责", "S07", "", "verified"),
    ("CH29", "PROHIBITED", "虚假申报购汇用途（如申报旅游实际用于境外购房）", "—", "《个人购汇申请书》'六不得'禁止虚假申报，且不得用于境外买房、证券投资、人寿保险及投资性返还分红类保险", "无（被明确禁止）", "购汇用途与付汇用途一致性审核；银行可拒绝", "条例第44条：擅自改变外汇或结汇资金用途，30%以下罚款，情节严重30%以上等值以下", "S09", "S07", "verified"),
    ("CH30", "PROHIBITED", "出借本人便利化额度协助他人购汇", "—", "首次予以风险提示，再次出现即列入'关注名单'", "无（被明确禁止）", "全国统一的个人外汇业务监测系统记录", "关注名单：当年及之后连续2年不享受便利化额度", "S12", "S11", "verified"),
    ("CH31", "PROHIBITED", "境外购房 / 证券投资 / 人寿保险 / 投资返还分红保险（用购汇额度）", "—", "资本项目尚未开放；个人对外投资只能通过规定渠道如 QDII 等实现", "无（未开放）", "汇款用途审核会拦截", "条例第44/45条", "S53", "S09", "verified"),
    ("CH32", "PROHIBITED", "贸易高低报 / 虚假贸易（over-/under-invoicing）转移资金", "—", "经常项目外汇收支应当具有真实、合法的交易基础；银行须审查单证真实性与一致性", "无（被明确禁止）", "海关、税务、外汇数据交叉比对", "逃汇（第39条）/ 非法套汇（第40条）；情节严重可构成犯罪", "S07", "", "verified"),
    ("CH33", "PROHIBITED", "未申报 / 超额携带外币现钞出境（现金走私）", "—", "≤5000美元免证；5000–10000美元须《携带证》；原则上不得>10000美元", "无（超额被禁止）", "海关查验；反洗钱申报", "条例第42条：警告，可处违法金额20%以下罚款；构成走私另论", "S07", "S36", "verified"),
    ("CH34", "PROHIBITED", "境外交易所向境内居民提供虚拟货币服务", "境外单位/个人", "境外单位和个人不得以任何形式非法向境内主体提供虚拟货币相关服务", "无（被明确禁止）", "2026 年新规明确'境内严禁、境外严管'；境内协助者同样追责", "银发〔2026〕42号第（十八）项：依法追责，构成犯罪追刑责", "S29", "", "verified"),
    ("CH35", "PROHIBITED (unless approved)", "RWA 代币化 / 以境内权益在境外发行代币或挂钩人民币稳定币", "境内主体及其控制的境外主体", "未经相关部门依法依规同意不得开展；境内开展 RWA 代币化活动原则上禁止", "无（未经批准即禁止）", "2026 年新规首次纳入；跨境穿透监管；发改/证监会/外汇局分工监管", "银发〔2026〕42号第（十三）（十四）（十八）项", "S29", "S56", "verified"),
]

# penalty: id, layer, component, verified_value, basis_and_note, source_id, extra, status
PENALTY = [
    ("P01", "China — alleged 'conversion tax'", "是否存在针对个人人民币本金兑换美元的统一定额税/税率", "", "本轮研究的官方来源未发现对'把个人储蓄本金兑换成美元'这一行为征收统一税种或税率的规定。该值无法从官方来源确认，留空并标记 UNVERIFIED。用户所述'可观的税'可能混淆了资金来源所得税、完税/备案材料、银行买卖价差与汇款费。", "S01", "S21", "unverified"),
    ("P02", "China — tax on the source of funds", "个人所得税税率", "综合所得 3%–45% 超额累进；利息股息红利、财产租赁、财产转让、偶然所得 20% 比例税率", "若 CNY 来源于尚未完税的工资、劳务、财产转让等，须先依法完税；这才是可能被感知为'税'的部分", "S23", "", "verified"),
    ("P03", "China — interest on the CNY account", "储蓄存款利息个人所得税", "自2008年10月9日起暂免征收", "中国暂免 ≠ 美国免税；该利息仍属美国公民的全球所得", "S24", "U01", "verified"),
    ("P04", "China — documentary preconditions", "税务备案 / 税务凭证门槛", "境内机构和个人向境外单笔支付等值5万美元以上（不含）特定项目外汇资金须税务备案；境外个人购汇需有交易额的购汇资金来源材料（含税务凭证）", "备案不是税，但是付汇前置条件；未完成则无法完成兑换/汇出", "S21", "S44", "verified"),
    ("P05", "China — bank exchange spread", "银行对客户 CNY/USD 买卖价差（当前实际值）", "", "2014-07-01 起取消挂牌买卖价差管理，银行自主定价；官方不公布某一客户在某日的实际价差，故无法确认该账户的数值。留空并标记 UNVERIFIED，须向银行取得书面报价。", "S27", "S26", "unverified"),
    ("P06", "China — exchange-rate band", "银行间即期 CNY/USD 交易价浮动幅度", "当日中间价上下 2%", "中国人民银行公告〔2014〕第5号，自2014-03-17起", "S26", "", "verified"),
    ("P07", "China — historical spread caps", "历史上被取消的价差上限", "2005年：美元现汇买卖价差≤中间价1%、现钞≤4%；2014年3月扩大至3%；2014年7月全部取消", "仅作历史背景，不能当作现行价格上限", "S28", "S26", "verified"),
    ("P08", "China — wire fee (personal e-banking)", "个人跨境汇款（电汇）手续费", "汇款金额 1‰，最低 ¥50/笔，最高 ¥260/笔；另收电讯费：港澳台 ¥80/笔，非港澳台 ¥150/笔", "中国银行电子银行个人服务费率表（2014-11-01起）；实际以银行公示/协议为准", "S46", "", "verified"),
    ("P09", "China — wire fee (corporate schedule)", "对公汇出境外汇款（电汇）", "汇款金额 1‰，最低 ¥50/笔，最高 ¥1,000/笔，另加电讯费", "中国银行国际结算业务资费表；注明为对公基准价，可按客户资信浮动", "S47", "", "verified"),
    ("P10", "China — correspondent/intermediary fees", "境外银行 / 中转行费用", "凡业务发生的境外银行收费，按实收取", "官方资费表备注；具体金额无官方统一数值，按实际发生", "S47", "", "verified"),
    ("P11", "China — 'full amount received' service", "全额到账服务加收（美元）", "收款行在中行纽约分行开立账户：15 美元/笔；其他情形：25 美元/笔；仅当至少经过一家中间行且收款人要求全额到账时适用（美国境内美元汇款金额须小于1亿美元）", "中国银行 2018 年公告（公司金融·贸易融资资费表）；属特定产品定价；对个人 e-banking 跨境汇款的适用性未经核实", "S48", "", "verified"),
    ("P12", "China — fee promotions", "历史优惠（已过期）", "2024-01-01 至 2024-12-31：手机银行个人外币跨境汇款（向境外中行汇款）手续费及电讯费免费；向境外他行汇款手续费及电讯费9折", "仅为 2024 年活动，不得视为当前费率；见 IR-020", "S49", "", "verified"),
    ("P13", "China — offshore basis (historical)", "CNY 与 CNH 价差（历史官方观测）", "2011-09-23 价差一度达 1.94%；2014 年一季度 CNH 对 CNY 平均溢价由 +163 pips 收窄", "香港金融管理局官方报告；为历史观测值，不是当前价差", "S50", "S51", "verified"),
    ("P14", "China — offshore basis (current)", "当前 CNY/CNH 价差", "", "HKMA 2025 年报告确认在岸/离岸汇率存在差距，但未给出可用于本账户的当前数值。留空并标记 UNVERIFIED。", "S52", "", "unverified"),
    ("P15", "China — cash vs account rate", "现钞价与现汇价差额（当前）", "", "官方来源确认历史上对现钞买卖价差另有管理，但当前具体差额无官方数值。留空并标记 UNVERIFIED。", "S28", "S27", "unverified"),
    ("P16", "China — administrative fine", "逃汇罚款", "逃汇金额 30% 以下；情节严重 30% 以上等值以下；并责令限期调回外汇", "《外汇管理条例》第39条；分拆购汇案例即按此条处罚", "S07", "S14", "verified"),
    ("P17", "China — administrative fine", "非法买卖外汇罚款", "违法金额 30% 以下；情节严重 30% 以上等值以下；警告 + 没收违法所得", "《外汇管理条例》第45条（2008修订版）", "S07", "", "verified"),
    ("P18", "China — administrative fine", "非法套汇 / 擅自改变用途", "30% 以下；情节严重 30% 以上等值以下", "《外汇管理条例》第40、44条", "S07", "", "verified"),
    ("P19", "China — criminal", "非法经营罪刑罚", "情节严重：5年以下有期徒刑或拘役 + 违法所得1–5倍罚金；情节特别严重：5年以上有期徒刑 + 1–5倍罚金或没收财产", "《刑法》第225条；违法所得难以确定时按非法经营额千分之一认定", "S34", "S32", "verified"),
    ("P20", "China — criminal thresholds", "非法买卖外汇入罪门槛", "非法经营数额 ≥500万元 或违法所得 ≥10万元 = 情节严重；≥2500万元 或违法所得 ≥50万元 = 情节特别严重", "法释〔2019〕1号 第3、4条；另有次级标准", "S32", "S33", "verified"),
    ("P21", "China — compliance cost", "'关注名单'期限", "列入当年及之后连续 2 年；期间办理结售汇须凭身份证件 + 有交易额材料", "指引第62条；是时间/便利成本，不是税款", "S11", "", "verified"),
    ("P22", "China — quota/time cost", "便利化额度与汇出审核门槛", "每人每年等值 5 万美元；外汇账户汇出当日累计等值 5 万美元以上须提交交易材料", "两个 5 万美元不是同一概念；额度不是法定上限", "S01", "S02", "verified"),
    ("P23", "US — tax on moving one's own principal", "把本人税后本金从中国账户转到美国账户这一行为的美国所得税", "", "官方来源确认美国对全球所得征税、FBAR 是信息申报而非纳税申报表；但本轮研究未找到直接表述'转移本金本身不产生所得税'的官方条文，故不填写数值或结论，留空并标记 UNVERIFIED。", "U01", "U26", "unverified"),
    ("P24", "US — income earned while funds sit in China", "CNY 账户利息 / 收益的美国税", "须计入全球所得并申报（即使中国暂免利息税）", "IRS 国际个人税务 FAQ / Publication 54；具体税额取决于个人情况，未填写", "U01", "U02", "verified"),
    ("P25", "US — currency gain on conversion", "个人外币交易汇兑收益", "不超过 $200 不计入所得；超过 $200，个人交易例外不适用（全部收益须确认）；非个人交易按 §988(a)(1)(A) 作为普通收入； Pub. 525 的'按资本利得申报'以属于个人交易为前提（§988(e)(3) 排除 §162/§212 费用）", "IRS Publication 525（个人外币交易）+ 26 U.S.C. §988(a)(1)(A)/(e)（govinfo）；是否属于'个人交易'取决于事实，请由税务师判断", "U04", "U27", "verified"),
    ("P26", "US — FBAR penalty (non-willful)", "FBAR 非故意违规最高罚款", "$16,536 / 每次违规", "31 CFR 1010.821 表，适用于 2025-01-17 起评估的处罚；2026 年通胀调整被取消", "U20", "U21", "verified"),
    ("P27", "US — FBAR penalty (willful)", "FBAR 故意违规最高罚款", "$165,353 或违规时账户余额的 50%（取较大者）", "本项目识别出的最大单项金钱风险：可达账户余额的一半", "U20", "U18", "verified"),
    ("P28", "US — Form 8938 penalty", "未提交 Form 8938", "$10,000；IRS 通知后每30天加 $10,000，上限额外 $50,000（潜在合计 $60,000）", "IRS 对照表 / IRM 5.21.6", "U06", "U10", "verified"),
    ("P29", "US — 40% penalty", "未披露境外资产导致的少缴税款", "额外 40% 重大少报罚款", "IRS FATCA information for individuals", "U08", "", "verified"),
    ("P30", "US — Form 3520 penalty", "境外赠与/遗赠未申报", "每月按赠与额 5%，最高为赠与额的 25%", "IRC 6039F(c)；IRS 页面；赠与本身不缴所得税但漏报有罚款", "U09", "U25", "verified"),
    ("P31", "US — treaty cap", "中美协定来源国税率上限", "股息、利息、特许权使用费各不超过 10%", "1984 协定；但 saving clause 保留美国对其公民征税的权利", "U16", "U17", "verified"),
    ("P32", "US — double-tax relief", "外国税收抵免", "Form 1116；抵免额为已付外国税与 FTC 限额中的较小者", "IRS Publication 514；不等于全额抵免", "U05", "", "verified"),
    ("P33", "US — remediation", "过去非故意漏报的补救程序", "Streamlined Foreign Offshore：补3年申报表 + 6年 FBAR，合规者不承担相关罚款；Delinquent FBAR：IRS 未联系时尽快补交", "降低已发生的历史罚款风险，而非转换成本", "U13", "U12", "verified"),
    ("P34", "US — 2026 penalty amounts", "2026 年 FBAR 罚款是否上调", "未上调：OMB M-26-11 取消 2026 年调整，继续适用 2025 年金额", "Federal Register 多机构公告一致", "U21", "U20", "verified"),
    ("P35", "All-in", "本账户的总转换惩罚（金额或百分比）", "", "需要账户余额、资金来源与完税记录、银行书面报价、汇路中转行费用、美国申报历史等个案数据；官方来源不提供该个案数值，故留空并标记 UNVERIFIED。", "S46", "U20", "unverified"),
]

# findings: id, finding, analysis, implication, source_id, extra, status
FINDINGS = [
    ("F01", "用户所说的'可观的税'在官方来源中没有对应税种", "官方文件规定的是外汇可兑换性、真实性审核、完税/备案材料与银行定价，没有对'把个人储蓄本金兑换成美元'设置统一税率", "先要求银行与税务机关书面写明被要求缴纳的究竟是税款、备案，还是价差/手续费；不要按'转换税'来优化", "S01", "S21", "verified"),
    ("F02", "美国公民通常属于'境外个人'，这是最关键的结构性发现", "《个人外汇管理办法》第37条把持护照的外国公民定义为境外个人；指引第59条规定境外个人凭身份证件 + 有交易额的购汇资金来源材料（含税务凭证）即可购汇，SAFE 答疑手册明确'境外个人购汇本身无年度额度限制'", "若资金是境内合法取得且已完税的人民币收入，5万美元便利化额度可能根本不是限制；应首先按境外个人路径与银行沟通", "S05", "S03", "verified"),
    ("F03", "'境内个人/境外个人'的两个官方定义存在张力", "《外汇管理条例》第52条把在境内连续居住满1年的外国人算作境内个人，而人民银行令第3号按开户证件把持护照者划为境外个人；第28条规定由开户身份证件确定主体类别", "必须先确认该账户开户所用证件及银行系统的主体分类，否则会选错规则；见 IR-007", "S07", "S05", "verified"),
    ("F04", "5 万美元是'简化办理门槛'，不是年度法定上限", "SAFE 明确：真实合法的经常项目和已开放资本项目下购汇结汇都没有金额限制，超过5万美元只是不能仅凭身份证件办理", "把问题从'如何绕过额度'改写为'如何准备真实性与资金来源材料'", "S01", "", "verified"),
    ("F05", "存在两个不同的 5 万美元门槛", "一个是每人每年的购汇/结汇便利化额度；另一个是外汇账户内外汇汇出境外当日累计 5 万美元的凭证门槛", "二者不可混用；同一天多笔汇出会累计计算", "S01", "S02", "verified"),
    ("F06", "完税凭证是前置条件，不是转换税", "境外个人购汇须有含税务凭证的资金来源材料；单笔>5万美元特定对外支付须税务备案，备案不是征税", "补齐完税/备案材料通常比寻找'低税通道'更有效且无罚款风险", "S44", "S21", "verified"),
    ("F07", "中国暂免存款利息税，但美国仍对全球所得征税", "财税〔2008〕132号自2008-10-09起暂免储蓄存款利息个税；IRS 规定美国公民全球所得须申报纳税", "账户停留期间的利息可能形成美国应税所得，即使中国不征税", "S24", "U01", "verified"),
    ("F08", "最大的单项金钱风险是美国故意 FBAR 违规罚款", "31 CFR 1010.821 表：故意违规最高为 $165,353 或账户余额的 50%（取较大者）", "'少交税'的优化收益远小于漏报风险；合规申报是降低总惩罚的首要动作", "U20", "", "verified"),
    ("F09", "非法通道会把文书问题放大为 30%–100% 罚款 + 刑事风险", "逃汇/非法买卖外汇罚款为违法金额30%以下、情节严重30%以上等值以下；非法经营罪可判5年以上并处罚金", "地下钱庄、分拆、虚拟货币等路径在经济上和刑事上都劣于合法通道", "S07", "S34", "verified"),
    ("F10", "2026 年虚拟货币规则已经替换 2021 年规则", "银发〔2026〕42号自2026-02-06施行并明文废止银发〔2021〕237号，同时新增 RWA 代币化与挂钩人民币稳定币规则", "仍引用 237 号文的建议已过时；见 IR-004", "S29", "S30", "verified"),
    ("F11", "分拆购汇是被专门监测并有公开处罚案例的行为", "SAFE 公布'七起个人分拆结售汇案'（60人、269.29万美元）等案例，并依条例第39条处罚", "'借用亲友额度'不是低风险技巧", "S14", "S15", "verified"),
    ("F12", "境内外人民币价差是官方记录过的真实成本", "HKMA 报告记录 2011-09-23 CNY/CNH 价差一度达 1.94%，2014 年一季度 CNH 平均溢价 +163 pips", "若走离岸兑换路径，须把 CNH 价差计入成本；但当前数值无法从官方来源确认", "S50", "S51", "verified"),
    ("F13", "银行定价组件可逐项核实，个案总价不可核实", "中国银行官方费率表给出 1‰（¥50–¥260）+ 电讯费（¥80/¥150）、境外银行费用按实收取、全额到账 USD 15 等", "向银行索取书面全包报价（客户价、中间价、价差、汇款费、中转行费、收款行费、预计到账净额）", "S46", "S47", "verified"),
    ("F14", "中美税收协定不保护美国公民免受美国征税", "协定把来源国税率限制在 10%，但议定书第2款 saving clause 明确美国仍可对其公民征税", "不能用协定主张'钱在中国所以美国不征税'", "U16", "U17", "verified"),
    ("F15", "境外赠与超过 $100,000 需报 Form 3520，虽不缴所得税但漏报罚 25%", "IRS Gifts from foreign person 明确赠与不是所得税应税项目，但未申报按每月5%、最高25%处罚", "若这笔钱在性质上是赠与/继承，须单独评估 3520 义务", "U09", "", "verified"),
    ("F16", "历史漏报有官方补救程序", "Streamlined Foreign Offshore（3年申报表 + 6年 FBAR）与 Delinquent FBAR 程序可降低非故意漏报的罚款", "在动钱之前先做申报健康检查，避免把历史问题带进新交易", "U13", "U12", "verified"),
    ("F17", "资本项目用途不能用便利化额度购汇", "《个人购汇申请书》'六不得'禁止用于境外买房、证券投资、人寿保险及投资性返还分红类保险；个人对外投资只能通过 QDII 等规定渠道", "若目标是'把钱变成境外资产'而非'换成美元现金'，规则完全不同", "S09", "S53", "verified"),
    ("F18", "个人财产对外转移通道存在但范围窄且分期", "仅适用于移民财产转移和继承财产转移；≥50万元人民币需国家外汇管理局批准；≥20万元移民转移须2年分步汇出", "只有符合身份条件时才可用，不能作为普通储蓄的通用出口", "S18", "S17", "verified"),
    ("F19", "企业利润可无上限汇出，但材料要求更高", "汇发〔2017〕3号：真实合规利润按程序出具证明材料可直接银行办理，没有任何限制；>5万美元须董事会决议、税务备案表、审计报告", "若资金实为公司所有，应走公司路径而非个人购汇", "S20", "", "verified"),
    ("F20", "跨境人民币通道在离岸完成兑换且不占个人外汇额度", "跨境理财通解读明确'业务均使用人民币进行跨境资金划转，资金兑换在离岸市场完成，因此不涉及占用个人的外汇额度'；PBOC 亦支持个人经常项目跨境人民币结算", "可比较在岸购汇与离岸 CNH 兑换两条路径的全包成本", "S40", "S38", "verified"),
    ("F21", "美国申报义务与中国购汇批准是两套独立义务", "IRS 对照表明确 Form 8938 不替代 FBAR，两者可同时适用独立罚款；中国侧则由银行/外汇局审核真实性", "钱成功汇出并不等于美国申报完成；反之亦然", "U06", "S02", "verified"),
    ("F22", "个人外币汇兑收益有 $200 的免计入门槛", "IRS Publication 525：个人外币交易因汇率变动产生的收益不超过 $200 不计入所得；超过 $200 个人例外不适用； Pub. 525 的'按资本利得申报'以属于个人交易为前提（§988(e)(3) 排除 §162/§212 费用）；非个人交易按 §988(a)(1)(A) 作为普通收入", "若 CNY 相对取得时升值，兑换本身可能产生应申报的美国所得（多为普通收入，取决于事实与 §988 定性）——见 us-fx-gain.html", "U04", "U27", "verified"),
]

# flags: id, item, why_flagged, needed, source_id, extra, status
FLAGS = [
    ("IR-001", "分支策略与任务书不一致", "任务书要求每个 session 使用 session-<id>/<task> 分支和独立 integration 分支；Arena 将本会话固定在 arena/c703e38c-china3 且禁止创建/推送其他分支。前一个并行会话也记录了同样偏差。", "若需要真正的多分支流程，需在 Arena 之外配置；本仓库所有工作已在固定分支上完成。", "G01", "", "needs review"),
    ("IR-002", "任务书引用的既有内容在会话开始时不存在", "任务书提到 COORDINATION.md 及'所有条目与发现'，但本会话开始时仓库只有 README.md（# China3），无 COORDINATION.md、无数据、无站点。", "确认是否存在预期由其他系统提供的初始数据；本次已从头建立全部内容。", "G01", "", "needs review"),
    ("IR-003", "GitHub Pages 来源设置与 Actions 部署并存", "Pages API 报告 build_type=legacy、source=main:/，同时仓库存在 Actions 部署工作流；前一会话已记录同一现象。", "部署成功后复核 Pages 设置，避免两种发布机制互相覆盖。", "G01", "", "needs review"),
    ("IR-004", "银发〔2021〕237号已被废止", "现行规则是银发〔2026〕42号（2026-02-06 施行），明文废止 237 号文；大量二手建议仍引用 237 号文。", "任何引用 237 号文的方案都应按 42 号文重新核对。", "S29", "S30", "needs review"),
    ("IR-005", "《外汇管理条例》第45条存在两个不同版本", "2008 修订版（国务院令532号）为'30%以下/情节严重30%以上等值以下'；1996 版条文为'30%以上3倍以下'。本站点采用 SAFE 官网 2008 修订版全文。", "如需引用条文原文，请以国务院令532号为准。", "S07", "", "needs review"),
    ("IR-006", "两份反分拆规范性文件均已标注废止", "汇发〔2009〕56号与汇发〔2015〕49号在 SAFE 官网均标注'已废止'；现行依据为《经常项目外汇业务指引（2020年版）》第62条。舊案例仍引用旧文号。", "以 2020 年指引为准；旧文号仅用于理解案例背景。", "S13", "S11", "needs review"),
    ("IR-007", "'境内个人/境外个人'官方定义互相不一致", "国务院令532号第52条把在境内连续居住满1年的外国人列为境内个人；人民银行令〔2006〕第3号第37条把持护照的外国公民列为境外个人，第28条按开户证件判定。", "需向开户银行确认该账户在个人外汇业务监测系统中的主体类别；这直接决定适用哪套购汇规则。", "S07", "S05", "needs review"),
    ("IR-008", "2026 年 FBAR 罚款通胀调整被取消", "OMB M-26-11 因 2025 年 10 月 CPI-U 数据缺失取消 2026 年调整，各机构继续适用 2025 年金额（$16,536 / $165,353）。", "确认后续年度是否有新调整；不要使用 $10,000 / $100,000 的法定基础金额作为当前上限。", "U21", "U20", "needs review"),
    ("IR-009", "未找到已签署的中美大陆 FATCA 政府间协议", "美国财政部 2014 年联合成果单只确认'达成实质性一致'并承诺年底前签署；本轮研究未在官方来源找到已签署的中美大陆 IGA 全文（香港、澳门另有协议）。", "如需据此判断银行报送义务，请向美国财政部/IRS 及开户银行核实。", "U23", "U22", "needs review"),
    ("IR-010", "eCFR 为权威但非官方版本", "eCFR 页面自述 'authoritative but unofficial'，正式公布版本为年度 CFR（govinfo.gov）。", "如用于法律程序，请核对 govinfo 上的正式版本。", "U20", "", "needs review"),
    ("IR-011", "未找到'货币兑换税'的官方依据", "本轮检索的 SAFE / PBOC / 税务总局官方文件未规定针对个人人民币本金兑换美元的统一税种或税率。用户所述'可观的税'缺少税种、金额与凭证。", "请提供银行或税务机关的书面收费/征税说明，才能判断其性质。所有相关数值已留空。", "S01", "S21", "needs review"),
    ("IR-012", "当前银行价差、中转行费用、CNY/CNH 基差不可核实", "已窄化（2026-11-10，final integration）：BOC 公开牌价给出带日期的官方半价差 — 2026-11-09 09:15:45 现汇卖出价 669.19 对 mid 667.785 → +0.2104%（board 仅'仅供参考'，执行价以实际成交为准）；账户执行价、中转行费用、当前 CNH 基差仍需银行书面报价，相关表格单元格继续留空并标记 UNVERIFIED。", "需银行书面报价与汇路说明；牌价半价差已对照 BOC 牌价表核对（见 cost-tables.html 与 cross-session-review.html X-10）。", "S27", "S47", "needs review"),
    ("IR-013", "合并冲突与 rebase 扁平化冲突", "两个会话同时创建 COORDINATION.md 造成 add/add 冲突；随后 git pull --rebase 试图扁平化合并提交并再次冲突。已停止并 git rebase --abort，未丢弃任何会话的工作。", "复核 COORDINATION.md 中保留的前一会话原始记录与本次合并日志。", "G01", "", "needs review"),
    ("IR-014", "缺少全部个案事实", "未提供：金额、资金来源与完税记录、账户开户证件、在中国的居住情况、持有银行、拟收款行、美国报税历史、是否为赠与/继承。", "所有结论均为条件式；在补齐事实前不能给出个性化路线或税额。", "G01", "", "needs review"),
    ("IR-015", "2026-11-07 当日 USD/CNY 中间价未核实", "已对 2026-11-09 关闭：CFETS（中国外汇交易中心，经 PBOC 授权）公布的 USD/CNY 中间价为 6.7188（2026-11-09 09:15，chinamoney.com.cn 记录于 data/reference_inputs.csv R06，session-5e4816e0 已核实）。其他日期的中间价仍须逐日查证；本行保留 S26（PBOC 2014 公告）作为带宽规则来源。", "逐日中间价请查 CFETS 官方公告（chinamoney.com.cn）；2026-11-09 数值见 R06。", "S26", "", "needs review"),
    ("IR-016", "中文官方文件的英文表述为本站点译文", "多数一手材料为中文法规、问答与公告；本站点英文表述为便于阅读的转述，不构成官方译本。", "请以链接中的中文原文为准。", "S05", "", "needs review"),
    ("IR-017", "跨境理财通 / QDII 资格适配性未确认", "跨境理财通要求大湾区内地9市户籍或连续5年社保/个税、2年投资经历及资产门槛；QDII 需机构额度。这些条件是否满足未知。", "确认居住地、投资经历与资产情况后再考虑。", "S39", "S41", "needs review"),
    ("IR-018", "'无需人工输入'与个案结论的矛盾", "任务书要求全程无人工输入，但最优路径、税额与全包成本都依赖个案事实；因此本站点只给出规则、通道、罚款组件与条件式分析，不填个案数值。", "如需确定数额，须由用户提供材料或授权专业人士调取。", "G01", "", "needs review"),
    ("IR-019", "资金性质是否为境外赠与/遗赠未确认", "若资金属于赠与或继承，美国 Form 3520 的 >$100,000 申报义务与 25% 罚款可能适用；中国侧继承转移另有专门程序。", "确认资金法律性质。", "U09", "S17", "needs review"),
    ("IR-020", "中国银行 2024 年费率优惠已过期", "官方公告的免费/9折优惠期间为 2024-01-01 至 2024-12-31，不能作为当前费率。", "以银行当前公示费率与书面报价为准。", "S49", "", "needs review"),
    ("IR-021", "2004 年个人财产转移办法是否有后续修订未逐条复核", "本轮依据 PBOC 2004 答记者问与 SAFE 2021 业务指南；未逐条排查其后所有修订。", "实际办理前请向原户籍所在地外汇局索取现行材料清单。", "S17", "S18", "needs review"),
    ("IR-022", "CNY/CNH 价差数据为历史观测值", "1.94%（2011）与 +163 pips（2014Q1）来自 HKMA 历史报告，不代表当前价差。", "当前价差需实时市场数据，本站点留空。", "S50", "S51", "needs review"),
    ("IR-023", "部分 SAFE 材料为地方分局问答而非国家层面法规", "多条结论来自天津/上海/厦门/重庆等分局的政策问答与业务指南，属于对上位规则的解释，可能存在地区执行差异。", "办理前向开户行所在地外汇局/银行确认执行口径。", "S03", "S44", "needs review"),
]

# ---------------------------------------------------------------------------
# CSV WRITERS
# ---------------------------------------------------------------------------
def write_csv(name, header, rows):
    with (DATA / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(header)
        w.writerows(rows)


def url_for(sid):
    return SOURCES[sid][2]


def source_col(sid, extra):
    ids = [sid] + ([x for x in extra.split() if x] if extra else [])
    links = []
    for s in ids:
        if s not in SOURCES:
            raise SystemExit(f"unknown source id {s}")
        links.append(f'<a href="{html.escape(url_for(s), quote=True)}" target="_blank" rel="noopener" title="{html.escape(SOURCES[s][1], quote=True)}">{html.escape(s)} ↗</a>')
    return " ".join(links)


write_csv("sources.csv", ["id", "authority", "title", "url", "verification"],
          [[k, v[0], v[1], v[2], v[3]] for k, v in sorted(SOURCES.items())])

write_csv("china_rules.csv", ["id", "topic", "value", "scope_detail", "source_id", "source_url", "extra_source_ids", "status"],
          [[r[0], r[1], r[2], r[3], r[4], url_for(r[4]), r[5], r[6]] for r in CHINA_RULES])

write_csv("us_rules.csv", ["id", "topic", "value", "scope_detail", "source_id", "source_url", "extra_source_ids", "status"],
          [[r[0], r[1], r[2], r[3], r[4], url_for(r[4]), r[5], r[6]] for r in US_RULES])

write_csv("channels.csv", ["id", "group", "channel", "who", "limit_or_condition", "pros", "cons", "penalty_exposure", "source_id", "source_url", "extra_source_ids", "status"],
          [[r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], url_for(r[8]), r[9], r[10]] for r in CHANNELS])

write_csv("penalty.csv", ["id", "layer", "component", "verified_value", "basis_and_note", "source_id", "source_url", "extra_source_ids", "status"],
          [[r[0], r[1], r[2], r[3], r[4], r[5], url_for(r[5]), r[6], r[7]] for r in PENALTY])

write_csv("findings.csv", ["id", "finding", "analysis", "implication", "source_id", "source_url", "extra_source_ids", "status"],
          [[r[0], r[1], r[2], r[3], r[4], url_for(r[4]), r[5], r[6]] for r in FINDINGS])

write_csv("flags.csv", ["id", "item", "why_flagged", "needed", "source_id", "source_url", "extra_source_ids", "status"],
          [[r[0], r[1], r[2], r[3], r[4], url_for(r[4]), r[5], r[6]] for r in FLAGS])

(DATA / "deep_sources.json").write_text(json.dumps(
    {k: {"authority": v[0], "title": v[1], "url": v[2], "verification": v[3]} for k, v in sorted(SOURCES.items())},
    ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# HTML GENERATION
# ---------------------------------------------------------------------------
NAV = [
    ("index.html", "Site home"),
    ("deep-executive-summary.html", "Executive summary"),
    ("deep-china-rules.html", "China rules"),
    ("deep-us-tax.html", "US tax & reporting"),
    ("deep-channels.html", "All channels"),
    ("deep-penalty.html", "Penalty breakdown"),
    ("deep-findings.html", "Analysis"),
    ("deep-review.html", "Flagged for review"),
    ("deep-sources.html", "Sources"),
    ("docs/index.html", "Docs dashboard"),
]


def nav_html(active):
    items = "".join(
        f'<a class="{"active" if p == active else ""}" href="{p}">{html.escape(t)}</a>'
        for p, t in NAV)
    return f'<header class="topbar"><div class="shell"><a class="brand" href="index.html"><span class="brand-mark">¥</span> China Money Research</a><nav class="nav">{items}</nav></div></header>'


def page(path, title, eyebrow, h1, intro, stats, body, active, note=None):
    stat_html = "".join(f'<div class="stat"><b>{html.escape(a)}</b><span>{html.escape(b)}</span></div>' for a, b in stats)
    note_html = f'<p class="page-note">{note}</p>' if note else '<p class="page-note">Every table row links to an official source. Blank values are UNVERIFIED and are listed on the <a href="deep-review.html">Flagged for review</a> page. Informational research only — not legal, tax or banking advice.</p>'
    doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{html.escape(intro[:150], quote=True)}">
<title>{html.escape(title)} | China Money Research</title>
<link rel="stylesheet" href="assets/deep-research.css"></head><body>
{nav_html(active)}
<main class="shell">
<section class="hero"><div class="eyebrow">{html.escape(eyebrow)}</div><h1>{html.escape(h1)}</h1><p>{html.escape(intro)}</p></section>
<div class="stats">{stat_html}</div>
{body}
{note_html}
</main>
<footer class="foot"><div class="shell foot-row"><div><b>China Money Research</b><p>Official-source research · two-session integration · no commercial providers.</p></div><p>Reviewed 7 November 2026 · <a href="deep-sources.html">Source register</a> · <a href="deep-review.html">Flagged for review</a></p></div></footer>
<script src="assets/deep-app.js"></script></body></html>
'''
    (ROOT / path).write_text(doc, encoding="utf-8")


def table(caption, columns, rows, tid):
    """rows: list of (cells..., source_id, extra, status). Last 3 handled specially."""
    th = "".join(f"<th>{html.escape(c)}</th>" for c in columns)
    trs = []
    for row in rows:
        cells, sid, extra, status = row[:-3], row[-3], row[-2], row[-1]
        tds = []
        for c in cells:
            if c == "":
                tds.append('<td class="blank">— <span class="tag warn">UNVERIFIED / blank</span></td>')
            else:
                tds.append(f"<td>{html.escape(str(c))}</td>")
        if status == "verified":
            badge = '<span class="tag ok">Verified</span>'
        elif status == "needs review":
            badge = '<span class="tag warn">Needs review</span>'
        else:
            badge = '<span class="tag warn">Unverified</span>'
        tds.append(f'<td class="src">{source_col(sid, extra)}</td>')
        tds.append(f'<td class="status">{badge}</td>')
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f'''<section class="section" id="{tid}">
<div class="section-head"><div><h2 class="section-title">{html.escape(caption)}</h2></div>
<div class="tools"><label class="filter-label">Filter <input type="search" class="filter" data-filter="{tid}" placeholder="type to filter rows"></label><span class="rowcount" data-count="{tid}">{len(rows)} rows</span></div></div>
<div class="table-wrap"><table class="data" data-table="{tid}"><thead><tr>{th}<th>Official source</th><th>Status</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div></section>'''


def stat_badge(n, label):
    return (str(n), label)


# ---- deep-executive-summary.html -------------------------------------------------
exec_body = '''
<section class="section"><div class="section-head"><div><h2 class="section-title">Executive summary</h2><p>The short answer, then the evidence.</p></div></div>
<div class="hero-band"><strong>Bottom line</strong><p>No official source reviewed establishes a Chinese "conversion tax" on moving your own already-owned CNY principal into USD. The costs that actually bite are (1) Chinese <b>source-of-funds income tax and the tax-clearance documents</b> a bank requires before it will sell you FX, (2) <b>bank spread, wire and correspondent fees</b>, and (3) <b>U.S. information-reporting penalties</b> — the largest of which is a willful FBAR penalty of up to 50% of the account balance. The cheapest-penalty strategy is therefore not a clever conversion trick: it is picking the lawful documentary channel that matches how the money was earned, obtaining a written all-in bank quote, and filing FBAR / Form 8938 / Form 3520 correctly. Informal brokers, quota splitting and crypto/USDT convert a paperwork problem into 30%–100% administrative fines plus criminal exposure.</p></div>
</section>
<section class="section"><h2 class="section-title">The single most important structural finding</h2>
<div class="card"><p>Under the <a href="https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm" target="_blank" rel="noopener">PBOC Individual Foreign Exchange Measures, Art. 37 (S05)</a>, a U.S. citizen holding a passport is an <b>境外个人 (foreign individual)</b>. Under <a href="https://www.safe.gov.cn/tianjin/2024/0621/2529.html" target="_blank" rel="noopener">SAFE Current Account Guidelines Art. 59 (S03)</a>, a foreign individual purchases FX using an ID plus evidence of the <i>source</i> of the RMB (including a tax certificate) — and SAFE's own <a href="https://www.safe.gov.cn/chongqing/file/file/20190311/87806e211bb74eb4a44e71395c31cda9.pdf" target="_blank" rel="noopener">Q&amp;A handbook (S43)</a> states that foreign-individual FX purchase has <b>no annual quota limit at all</b>. If the CNY is legitimately earned, tax-paid income, the USD 50,000 "annual quota" that dominates online advice may simply not be the binding constraint. This must be confirmed with the account-opening bank because the 2008 State Council regulation defines 境内个人 differently (see <a href="deep-review.html">IR-007</a>).</p></div></section>
<section class="section"><h2 class="section-title">Recommended sequence (least penalty first)</h2>
<div class="card">
<div class="step"><span class="stepnum">1</span><p><strong>Classify the account holder and the money.</strong> Which ID opened the account? Is the CNY salary, business profit, sale of property, inheritance, gift, or previously-converted FX? Collect bank statements, contracts, and Chinese tax receipts. Without this, no route can be selected (<a href="deep-review.html">IR-014</a>).</p></div>
<div class="step"><span class="stepnum">2</span><p><strong>Ask the bank, in writing, which rule applies.</strong> Ask it to state whether it will process the request under Art. 59 (foreign individual, source-of-funds evidence, no annual quota), Art. 57 (current-account purchase above the convenience amount), or a capital-account approval route — and list the exact documents.</p></div>
<div class="step"><span class="stepnum">3</span><p><strong>Clear the tax-document precondition.</strong> For single outbound payments above USD 50,000, a tax-filing form (税务备案表) may be required; for foreign individuals, a tax certificate / payment or exemption certificate is part of the source-of-funds evidence. This is paperwork, not a conversion tax (<a href="deep-china-rules.html">C16, C17</a>).</p></div>
<div class="step"><span class="stepnum">4</span><p><strong>Get an all-in written quote.</strong> Customer CNY/USD rate, reference mid-rate and timestamp, spread, conversion charge, wire fee, cable fee, correspondent/intermediary charges, receiving-bank fee and expected net USD. Verified published components are on the <a href="deep-penalty.html">Penalty breakdown</a> page; the account-specific total is deliberately blank (<a href="deep-review.html">IR-012</a>).</p></div>
<div class="step"><span class="stepnum">5</span><p><strong>Use one lawful channel; never split.</strong> Do not use relatives' quotas, underground banks, false invoices or crypto. Compare the onshore bank route with a lawful cross-border RMB / offshore CNH route only if the bank confirms eligibility.</p></div>
<div class="step"><span class="stepnum">6</span><p><strong>Fix U.S. reporting before and after the transfer.</strong> FBAR ($10,000 aggregate trigger), Form 8938, worldwide income (including CNY account interest), the $200 personal FX-gain rule, and Form 3520 if the funds are a foreign gift. If prior years were missed, use the IRS Streamlined or delinquent FBAR procedures (<a href="deep-us-tax.html">U22–U24</a>).</p></div>
</div></section>
<section class="section"><h2 class="section-title">Requirement coverage (full list of requirements)</h2>
<div class="grid">
<article class="card"><span class="pill blue">Research</span><h3>Collect, organize, analyze</h3><p>All findings are collected in structured CSV tables and rendered as filterable tables on the <a href="deep-china-rules.html">China rules</a>, <a href="deep-us-tax.html">US tax</a>, <a href="deep-channels.html">channels</a>, <a href="deep-penalty.html">penalty</a> and <a href="deep-findings.html">analysis</a> pages.</p></article>
<article class="card"><span class="pill green">Verification</span><h3>Line by line, official sources</h3><p>Each row carries a direct official link in the <a href="deep-sources.html">source register</a>. Unconfirmed values are blank and flagged on <a href="deep-review.html">Flagged for review</a>. <code>scripts/verify_deep.py</code> enforces this mechanically.</p></article>
<article class="card"><span class="pill amber">Repo work</span><h3>Audit + irregularity log</h3><p>Repository audit, merge/handoff log, task board and verification log are in <a href="https://github.com/sassnarep3-star/China3/blob/main/COORDINATION.md" target="_blank" rel="noopener">COORDINATION.md</a> and on this site's <a href="deep-review.html">flagged page</a>.</p></article>
<article class="card"><span class="pill blue">Site</span><h3>Live dashboard</h3><p>Clean landing page, category subpages, simple dashboard UI, filterable tables, and a clearly labeled Flagged for Review page, published on GitHub Pages.</p></article>
<article class="card"><span class="pill green">Coordination</span><h3>No duplicate work</h3><p>Shared task board, non-overlapping scopes, small frequent commits, conflict log, and a final integration session. See <a href="https://github.com/sassnarep3-star/China3/blob/main/COORDINATION.md" target="_blank" rel="noopener">COORDINATION.md</a>.</p></article>
<article class="card"><span class="pill amber">Publication</span><h3>PR → merge → Pages</h3><p>PR from the integration branch to main with sources and irregularities, merged without waiting, Pages deployment confirmed, links recorded in COORDINATION.md.</p></article>
</div></section>
<section class="section"><h2 class="section-title">Prior-session research (preserved)</h2><p>The first session's independent <a href="routes.html">transfer-route comparison</a> and <a href="tax.html">tax &amp; reporting distinctions</a> remain published and are linked here as complementary reading. This integration pass adds the foreign-individual rule, the 2026 virtual-currency notice, the 2026 FBAR penalty figures, bank fee components, the §988 $200 rule, Form 3520, and the full penalty-component decomposition.</p></section>
'''
page("deep-executive-summary.html", "Executive summary", "Category 01 · Executive summary", "Executive summary & recommended path",
     "The important details, the ranked recommendation, and how each requirement in the brief was addressed.",
     [stat_badge("0", "official sources establishing a conversion tax"), stat_badge("50%", "maximum willful FBAR penalty of account balance"), stat_badge("30–100%", "Chinese administrative fine range for illegal FX channels"), stat_badge(str(len(CHANNELS)), "conversion channels catalogued")],
     exec_body, "deep-executive-summary.html")

# ---- deep-china-rules.html -------------------------------------------------------
china_rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in CHINA_RULES]
page("deep-china-rules.html", "China FX framework", "Category 02 · China-side framework", "China foreign-exchange rules, line by line",
     "Official SAFE / PBOC / State Council / State Taxation Administration rules that determine whether CNY can be converted and remitted. Each row is quoted or closely paraphrased from the linked official page.",
     [stat_badge(str(len(CHINA_RULES)), "verified rule rows"), stat_badge("USD 50k", "annual convenience amount (not a cap)"), stat_badge("USD 50k/day", "outward-remittance evidence threshold"), stat_badge("30–100%", "administrative fine range")],
     table("China-side rules register", ["#", "Topic", "Verified rule / value", "Scope & basis"], china_rows, "china-table"),
     "deep-china-rules.html")

# ---- deep-us-tax.html ------------------------------------------------------------
us_rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in US_RULES]
page("deep-us-tax.html", "US tax & reporting", "Category 03 · US-side obligations", "U.S. tax and foreign-account reporting",
     "IRS, FinCEN, Treasury and eCFR rules that apply to a U.S. citizen holding a Chinese bank account, independent of whether China permits the transfer.",
     [stat_badge(str(len(US_RULES)), "verified rule rows"), stat_badge("$10,000", "FBAR aggregate trigger"), stat_badge("$16,536", "non-willful FBAR maximum"), stat_badge("50%", "willful FBAR maximum of balance")],
     table("U.S. tax & reporting register", ["#", "Topic", "Verified rule / value", "Scope & basis"], us_rows, "us-table"),
     "deep-us-tax.html")

# ---- deep-channels.html ----------------------------------------------------------
ch_rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10]) for r in CHANNELS]
lawful = sum(1 for r in CHANNELS if r[1].startswith("Lawful"))
banned = sum(1 for r in CHANNELS if r[1].startswith("PROHIBITED"))
channels_intro = ("Every CNY→USD route found in official sources, with eligibility, limits, pros, cons and penalty exposure. "
                  "'PROHIBITED' rows are documented only so they can be ruled out; they are not recommendations.")
page("deep-channels.html", "All conversion channels", "Category 04 · Route catalogue", "All ways to convert CNY into USD — pros & cons",
     channels_intro,
     [stat_badge(str(len(CHANNELS)), "channels catalogued"), stat_badge(str(lawful), "lawful / approval-based"), stat_badge(str(banned), "prohibited or unapproved"), stat_badge("0", "recommended prohibited routes")],
     '<div class="notice amber"><strong>Read this first.</strong> "Lawful" does not mean "available to you" — most routes depend on who owns the money, how it was earned, and which ID opened the account. Prohibited routes are listed for completeness and are explicitly not recommended.</div>'
     + table("Full channel comparison", ["#", "Class", "Channel", "Who", "Limit / condition", "Pros", "Cons", "Penalty exposure"], ch_rows, "channels-table"),
     "deep-channels.html")

# ---- deep-penalty.html -----------------------------------------------------------
pen_rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]) for r in PENALTY]
penalty_intro = ("A decomposition of the 'conversion penalty' into its separately verifiable layers: Chinese tax on the source of funds, "
                 "documentary preconditions, bank pricing, FX controls and their fines, offshore basis, U.S. penalties and the account-specific total. "
                 "Blank cells are values that could not be confirmed from an official source.")
page("deep-penalty.html", "Conversion penalty breakdown", "Category 05 · Cost decomposition", "What the 'conversion penalty' actually consists of",
     penalty_intro,
     [stat_badge(str(len(PENALTY)), "cost / penalty components"), stat_badge("1‰", "BOC personal wire fee (¥50–¥260 cap)"), stat_badge("±2%", "CNY/USD interbank trading band"), stat_badge("50%", "max willful FBAR penalty")],
     '<div class="hero-band"><strong>How to read this</strong><p>There is no single official number for "the penalty". It is a stack of independent items. Add only the items that actually apply to your facts; any item whose value cannot be confirmed is left blank rather than estimated. The total for this specific account is deliberately blank (IR-012 / IR-014).</p></div>'
     + table("Penalty / cost component register", ["#", "Layer", "Component", "Verified amount / rate", "Basis, caveat and note"], pen_rows, "penalty-table"),
     "deep-penalty.html")

# ---- deep-findings.html ----------------------------------------------------------
find_rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in FINDINGS]
page("deep-findings.html", "Analysis & findings", "Category 06 · Analysis", "Analysis and findings",
     "Deep analysis: what the rules mean when combined, where the user's premise appears to be mis-specified, and which risks dominate the arithmetic.",
     [stat_badge(str(len(FINDINGS)), "sourced findings"), stat_badge("23", "flagged irregularities"), stat_badge("2", "agent sessions integrated"), stat_badge("0", "invented values")],
     table("Findings register", ["#", "Finding", "Analysis", "Implication"], find_rows, "findings-table"),
     "deep-findings.html")

# ---- deep-review.html (clearly labelled Flagged for Review) ----------------
flag_rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in FLAGS]
review_body = (
    '<div class="notice amber"><strong>Flagged for Review.</strong> These items are '
    'published with source links and do not block publication. Every value that could not '
    'be confirmed from an official source is blank and marked UNVERIFIED in its table. '
    'Nothing has been inferred or filled in.</div>'
    + table("Flagged irregularities and unverified values",
            ["#", "Item", "Why it is flagged", "What would resolve it"], flag_rows, "flags-table"))
page("deep-review.html", "Flagged for Review", "Category 07 · Flagged for Review",
     "Flagged for Review — irregularities and unverified values",
     "All flagged and unverified items from this integration session, each with a direct official source link. This page is non-blocking by design.",
     [stat_badge(str(len(FLAGS)), "flagged items"), stat_badge("0", "invented values"),
      stat_badge("0", "blocked deployments"), stat_badge("100%", "rows with official links")],
     review_body, "deep-review.html")

# ---- deep-sources.html ------------------------------------------------------
src_trs = []
for sid in sorted(SOURCES):
    authority, title, url, method = SOURCES[sid]
    src_trs.append(
        f'<tr><td><strong>{html.escape(sid)}</strong></td><td>{html.escape(authority)}</td>'
        f'<td>{html.escape(title)}</td>'
        f'<td class="src"><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">Open official page ↗</a></td>'
        f'<td>{html.escape(method)}</td><td class="status"><span class="tag ok">Registered</span></td></tr>')
sources_body = (
    '<div class="hero-band"><strong>Audit trail</strong><p>One row per primary source used '
    'in the deep-research tables. All domains are government, regulator, central bank, '
    'official court or official bank sources; the single GitHub entry is this repository’s '
    'own project record. Search-engine snippets were used only as leads.</p></div>'
    + '<section class="section"><div class="section-head"><div><h2 class="section-title">Official source register (' + str(len(SOURCES)) + ' sources)</h2></div>'
    + '<div class="tools"><label class="filter-label">Filter <input type="search" class="filter" data-filter="sources-table" placeholder="type to filter rows"></label><span class="rowcount" data-count="sources-table">' + str(len(src_trs)) + ' rows</span></div></div>'
    + '<div class="table-wrap"><table class="data" data-table="sources-table"><thead><tr><th>#</th><th>Authority</th><th>Document</th><th>Official link</th><th>Verification performed</th><th>Status</th></tr></thead><tbody>'
    + "".join(src_trs) + '</tbody></table></div></section>')
page("deep-sources.html", "Official sources", "Category 08 · Audit trail", "Official source register",
     "Every primary source used by this session, with its authority, document title, direct official link and verification method.",
     [stat_badge(str(len(SOURCES)), "official sources"), stat_badge("100%", "rows with direct links"),
      stat_badge("0", "secondary sources used as evidence"), stat_badge("0", "invented values")],
     sources_body, "deep-sources.html")

# ---------------------------------------------------------------------------
# RESEARCH MEMO: source register with verification method
# ---------------------------------------------------------------------------
RESEARCH = ROOT / "research"
RESEARCH.mkdir(exist_ok=True)
lines = [
    "# Official source register and verification method",
    "",
    "Session `session-c703e38c` · reviewed 2026-11-07 (UTC). Generated by",
    "`scripts/build_deep_site.py` from `data/sources.csv` / `data/deep_sources.json`.",
    "",
    "All URLs are on official domains (SAFE / PBOC / State Council / State Taxation",
    "Administration / courts / CSRC / HKMA / Bank of China / IRS / FinCEN / eCFR /",
    "Federal Register / Treasury), plus one GitHub entry for this repository's own",
    "project record. Search-engine snippets were used only as leads; a row is marked",
    "verified only when the quoted passage appears in the linked official page.",
    "`full text fetched` means the page was opened in full during this session;",
    "`official ... verified` means the official page's full-text excerpt containing the",
    "quoted passage was retrieved and checked. Pages dated before 2026 are flagged in",
    "`data/flags.csv` wherever the rule may have been superseded (IR-004, IR-005,",
    "IR-006, IR-020, IR-021, IR-022, IR-023).",
    "",
    "| ID | Authority | Document | Official link | Verification performed |",
    "|---|---|---|---|---|",
]
for sid in sorted(SOURCES):
    authority, title, url, method = SOURCES[sid]
    lines.append(f"| {sid} | {authority} | {title} | {url} | {method} |")
lines += [
    "",
    "## Domain allowlist enforced by `scripts/verify_deep.py`",
    "",
    "`" + "`, `".join(OFFICIAL_DOMAINS) + "`",
    "",
    "## Excluded",
    "",
    "Commercial expat blogs, law-firm marketing pages, aggregator sites and currency",
    "conversion portals appeared in search results but were **not** used as evidence for",
    "any numeric value or legal conclusion. Obsolete official materials (the 1996 text of",
    "the FX Regulation, 2011 TD F 90-22.1 FBAR instructions, the June-30 FBAR due date,",
    "the 2021 virtual-currency notice, the 2024 BOC fee promotion, repealed anti-splitting",
    "circulars) are cited only as historical/repeal context and are flagged.",
    "",
]
(RESEARCH / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print("Generated: 8 category pages + 7 CSV files + deep_sources.json + research/sources.md")
print(f"Sources: {len(SOURCES)} | China rules: {len(CHINA_RULES)} | US rules: {len(US_RULES)} | Channels: {len(CHANNELS)} | Penalty: {len(PENALTY)} | Findings: {len(FINDINGS)} | Flags: {len(FLAGS)}")
