#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""n676 data pack — writes the five CSVs the n676 pages are built from.

Every row in SOURCES was opened on 2026-11-11 and the `quote` column is copied from
the page as it read that day. Rows marked fetched=no were NOT re-opened this pass and
are carried forward explicitly as unverified; nothing here is copied from an earlier
session's CSV.
"""

from __future__ import annotations

import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
TODAY = "2026-11-11"

# ------------------------------------------------------------------ source register
# id, url, publisher, title, fetched, http, quote, supports
SOURCES = [
    ("N01", "https://www.boc.cn/sourcedb/whpj/enindex_1619.html", "Bank of China",
     "BOC Exchange Rate — USD row", "yes", "200",
     "USD | 666.3 | 666.3 | 669.11 | 669.11 | 671.91 | 2026-11-11 10:25:02",
     "Buying 6.6630, selling 6.6911 RMB per USD. The bank's own 'Middle Rate' column "
     "(6.7191) is not the mid-point of buying and selling, so the pages compute their "
     "own mid-point and say so."),
    ("N02", "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "Bank of China",
     "中国银行电子银行个人服务转账汇款费率表 (personal e-banking transfer tariff)", "yes", "200",
     "跨境汇款（电汇）：每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。",
     "Cross-border wire: 1 per mille of the amount, floor RMB 50, ceiling RMB 260, plus a "
     "telegraph charge of RMB 150 outside HK/Macau/Taiwan and RMB 80 inside it."),
    ("N02b", "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html", "Bank of China",
     "Same tariff — domestic foreign-currency transfer line", "yes", "200",
     "中行内跨省、省内异地外币转账：每笔转账金额的1‰，最高200元/笔。",
     "Moving foreign currency between your own BOC accounts inside China costs 1 per mille "
     "capped at RMB 200 — a different, cheaper line from the cross-border wire."),
    ("N03", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html", "SAFE Tianjin branch",
     "2024年经常项目外汇政策问答案例（九）, 2024-06-21", "yes", "200",
     "境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇。持有外国人永久居留身份证的境外个人适用购汇年度便利化额度。",
     "A 境外个人 (foreign individual — a U.S. citizen) buys dollars on ID plus source-of-funds "
     "documents including tax certificates, under art. 59 of 汇发〔2020〕14号. The annual "
     "convenience amount applies ONLY to holders of a Foreign Permanent Resident ID."),
    ("N04", "https://www.safe.gov.cn/ningxia/2022/0929/1997.html", "SAFE Ningxia branch",
     "2022年外汇业务政策释疑（八）, 2022-09-29", "yes", "200",
     "目前，我国对于真实、合法的经常项目和已开放的资本项目下购汇和结汇都没有金额限制。…年度便利化额度不是个人每年购汇或者结汇的限额，只是超过等值5万美元的购汇或结汇不能仅凭本人有效身份证件办理。",
     "There is no amount limit on genuine, lawful current-account and opened capital-account "
     "purchases. The USD 50,000 figure is not a cap; above it you simply cannot proceed on ID "
     "alone (arts. 54-57 of 汇发〔2020〕14号)."),
    ("N05", "https://www.safe.gov.cn/tianjin/2026/0713/3088.html", "SAFE Tianjin branch",
     "2026年外汇管理互联网信息——个人外汇（08）, 2026-07-13", "yes", "200",
     "根据《国家外汇管理局关于印发〈经常项目外汇业务指引（2020年版）〉的通知》（汇发〔2020〕14号）第五十九条规定，“境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇”。",
     "Confirms art. 59 is still the operative rule in 2026 for remitting labour income earned "
     "in China. Note the answer is expressly about 境外个人在境内工作期间取得的劳动报酬."),
    ("N06", "https://www.safe.gov.cn/safe/2008/0806/5321.html", "State Council (via SAFE)",
     "中华人民共和国外汇管理条例 (国务院令第532号)", "yes", "200",
     "第五条 国家对经常性国际支付和转移不予限制。…第三十九条 …处逃汇金额30%以下的罚款；情节严重的，处逃汇金额30%以上等值以下的罚款；构成犯罪的，依法追究刑事责任。…第四十五条 私自买卖外汇、变相买卖外汇、倒买倒卖外汇或者非法介绍买卖外汇数额较大的…处违法金额30%以下的罚款；情节严重的，处违法金额30%以上等值以下的罚款。…第五十二条…（二）境内个人，是指中国公民和在中华人民共和国境内连续居住满1年的外国人…",
     "Current-account payments and transfers are not restricted (art. 5). Evasion (art. 39), "
     "illegal arbitrage on false documents (art. 40) and private or disguised FX dealing "
     "(art. 45) all carry fines up to 30%, rising to 30-100% in serious cases, with criminal "
     "liability possible. Art. 52(2) defines 境内个人 to include a foreigner resident in China "
     "for a full year — the definition conflict that decides whether art. 54 or art. 59 applies."),
    ("N06b", "https://www.safe.gov.cn/safe/2008/0806/5321.html", "State Council (via SAFE)",
     "Same regulation — arts. 15, 42, 48", "yes", "200",
     "第十五条 携带、申报外币现钞出入境的限额，由国务院外汇管理部门规定。…第四十二条 违反规定携带外汇出入境的，由外汇管理机关给予警告，可以处违法金额20%以下的罚款。…第四十八条 …对个人可以处5万元以下的罚款…（三）未按照规定提交有效单证或者提交的单证不真实的",
     "Carrying cash across the border is limited by rules SAFE sets (the limits themselves are "
     "not in this regulation and were not re-read this pass — see N676-U06). Carrying FX out in "
     "breach draws a warning and up to 20%. False or missing documents draw up to RMB 50,000 "
     "for an individual."),
    ("N07", "http://m.safe.gov.cn/safe/2004/1116/5461.html", "People's Bank of China",
     "中国人民银行公告[2004]第16号 — 《个人财产对外转移售付汇管理暂行办法》", "yes", "200",
     "第二条 …移民财产转移…继承财产转移…第五条 申请人办理移民转移需向移民原户籍所在地外汇管理分局…申请；申请人办理继承转移需向被继承人生前户籍所在地外汇局申请。…第十一条 外汇指定银行办理售汇后，应直接将外汇汇往移民或继承人居住国或地区申请人本人的账户，不得在境内提取外币现钞。…第十二条 …不能证明合法来源财产等的对外转移申请，外汇局不予受理。",
     "Two named routes exist: 移民财产转移 (emigrant property) and 继承财产转移 (inheritance). "
     "Apply at the SAFE branch of the emigrant's former hukou, or the decedent's last hukou. "
     "The bank must remit straight to the applicant's own account abroad — no cash in China. "
     "Property whose lawful source cannot be proven will not be accepted at all."),
    ("N07b", "http://m.safe.gov.cn/safe/2004/1116/5461.html", "People's Bank of China",
     "Same announcement — arts. 6 and 10 as originally enacted", "yes", "200",
     "第六条 移民转移必须一次性申请拟转移出境的全部财产金额，分步汇出。首次可汇出金额不得超过全部申请转移财产的一半；自首次汇出满一年后，可汇出不超过剩余财产的一半；自首次汇出满两年后，可汇出全部剩余财产。…第十条 …超过上述金额的，由所在地外汇局初审后，报国家外汇管理局审批。",
     "The 2004 text staged an emigrant transfer over two years and sent anything over RMB 500,000 "
     "to SAFE headquarters. BOTH requirements were cancelled in 2014 — see N08. Pages that still "
     "quote the staging are stale (flag N676-F01)."),
    ("N08", "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "SAFE (republished by Tianjin branch)",
     "（已修改）国家外汇管理局关于进一步改进和调整资本项目外汇管理政策的通知 (汇发〔2014〕2号)", "yes", "200",
     "六、简化个人财产转移售付汇管理（一）移民财产转移购付汇核准，由移民原户籍所在地外汇局负责审批。继承财产转移购付汇核准，由被继承人生前户籍所在地外汇局负责审批。取消财产转移总金额超过等值人民币50万元报国家外汇管理局备案的要求。（二）取消移民财产转移分次汇出的要求。申请人向原户籍所在地外汇局办理移民财产转移核准手续后，银行可在核准件审批额度内一次或分次汇出相关资金。（四）取消对有关财产权利文件…进行公证的要求；取消对委托代理协议、代理人身份证明进行公证的要求。",
     "Section 6 cancels the RMB 500,000 head-office filing, cancels the staged-remittance rule "
     "(the bank may remit once or in instalments inside the approved amount), and cancels "
     "notarisation of property documents and of the agency agreement. The page is marked 已修改; "
     "the amendment note (汇发〔2023〕28号 annex 4) changes only section 3, not section 6."),
    ("N08b", "https://www.safe.gov.cn/tianjin/2024/0903/2594.html", "SAFE (republished by Tianjin branch)",
     "Same notice — section 5(1), institutional profit remittance", "yes", "200",
     "五、简化境内机构利润汇出管理（一）银行为境内机构办理等值5万美元（含）以下利润汇出，原则上可不再审核交易单证；办理等值5万美元以上利润汇出…应按真实交易原则审核与本次利润汇出相关的董事会利润分配决议（或合伙人利润分配决议）及其税务备案表原件。",
     "Applies to institutions, not individuals: a company paying out profit needs a board "
     "resolution and the tax filing form above USD 50,000. Cited only to show what a dividend "
     "route requires; the USD 50,000 figure here is NOT the individual convenience amount."),
    ("N09", "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
     "State Taxation Administration", "中华人民共和国个人所得税法 (2018 amendment)", "yes", "200",
     "第三条 个人所得税的税率：（一）综合所得，适用百分之三至百分之四十五的超额累进税率…（三）利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十。",
     "Wages, labour remuneration, author's remuneration and royalties: 3-45% progressive. "
     "Interest, dividends, rent, property transfer and incidental income: flat 20%. This is the "
     "tax on the underlying income, not on the conversion."),
    ("N09b", "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
     "State Taxation Administration", "Same law — arts. 1, 10, 13, 15, 16", "yes", "200",
     "第一条 在中国境内有住所，或者无住所而一个纳税年度内在中国境内居住累计满一百八十三天的个人，为居民个人。…第十条 …（五）因移居境外注销中国户籍…第十三条 …纳税人因移居境外注销中国户籍的，应当在注销中国户籍前办理税款清算。…第十五条 个人转让不动产的…登记机构办理转移登记时，应当查验与该不动产转让相关的个人所得税的完税凭证。",
     "The 183-day resident test decides whether China taxes worldwide income. If you emigrate and "
     "cancel your hukou you must settle Chinese tax BEFORE the cancellation. On a property sale "
     "the registration authority must see the individual income tax payment certificate before it "
     "will register the transfer — the tax certificate is not optional paperwork, it is a step in "
     "the sale."),
    ("N10", "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates",
     "Internal Revenue Service", "Yearly average currency exchange rates", "yes", "200",
     "China | Yuan | 7.129 | 7.189 | 7.075 | 6.730 | 6.452   (columns 2025, 2024, 2023, 2022, 2021)",
     "The IRS yearly average RMB per USD used as the acquisition basis in the currency-gain "
     "column. The same page states: 'The Internal Revenue Service has no official exchange rate.'"),
    ("N11", "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm",
     "U.S. Government Publishing Office", "26 U.S.C. § 988 — Treatment of certain foreign currency transactions", "yes", "200",
     "(e)(1) The preceding provisions of this section shall not apply to any section 988 transaction entered into by an individual which is a personal transaction. (e)(2) If—(A) nonfunctional currency is disposed of by an individual in any transaction, and (B) such transaction is a personal transaction, no gain shall be recognized… The preceding sentence shall not apply if the gain which would otherwise be recognized on the transaction exceeds $200.",
     "Selling RMB is a section 988 transaction and the gain is ordinary income (a)(1)(A) and "
     "(c)(1)(C). For a personal transaction the gain is simply not recognised — UNLESS it exceeds "
     "$200, which at $10,000 and above it does. So the de minimis rule does not shelter these "
     "amounts. (e)(3) carves out transactions whose expenses meet §162 or §212."),
    ("N12", "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
     "FinCEN / eCFR", "31 CFR 1010.821 — Penalty adjustment and table", "yes", "200",
     "31 U.S.C. 5321(a)(5)(B)(i) Foreign Financial Agency Transaction—Non-Willful Violation of Transaction | 10,000 | 16,536 … 31 U.S.C. 5321(a)(5)(C)(i)(I) Foreign Financial Agency Transaction—Willful Violation of Transaction | 100,000 | 165,353 … 31 U.S.C. 5321(a)(1) General Civil Penalty Provision for Willful Violations of Bank Secrecy Act Requirements | 25,000−100,000 | 71,545−286,184",
     "FBAR civil penalty maxima for penalties assessed on or after 17 January 2025: USD 16,536 "
     "non-willful, USD 165,353 willful, and USD 71,545-286,184 for the general willful BSA "
     "provision. eCFR Title 31 was displayed as up to date as of 11/09/2026."),
    ("N13", "https://www.irs.gov/individuals/international-taxpayers/figuring-the-foreign-earned-income-exclusion",
     "Internal Revenue Service", "Figuring the foreign earned income exclusion", "yes", "200",
     "For tax year 2025, the maximum foreign earned income exclusion is the lesser of the foreign income earned or $130,000 per qualifying person. For tax year 2026, the maximum exclusion is $132,900 per person. … For 2025, the housing amount limitation is $39,000; for 2026, it is $39,870.",
     "FEIE ceiling and housing limitation. Applies to EARNED income only — it does not shelter "
     "dividends, rent, interest, property-sale gains or a currency gain."),
    ("N14", "https://www.irs.gov/businesses/gifts-from-foreign-person", "Internal Revenue Service",
     "Gifts from foreign person (International tax gap series)", "yes", "200",
     "For gifts or bequests from a nonresident alien or foreign estate, you are required to report… only if the aggregate amount received… exceeds $100,000 during the taxable year. … For purported gifts from foreign corporations or foreign partnerships… exceeds $20,116 for 2025, and $20,573 for 2026 … you may be subject to penalties under IRC section 6039F(c).",
     "Form 3520 Part IV reporting thresholds for foreign gifts, and the 6039F(c) penalty hook. "
     "Relevant because money received as a gift in China is reportable in the U.S. even where no "
     "Chinese route to remit it has been verified."),
    ("N15", "http://m.safe.gov.cn/safe/2020/0831/f0127756271c43ef9b3908d5d157bd91.pdf", "SAFE",
     "《经常项目外汇业务指引（2020年版）》 (annex to 汇发〔2020〕14号)", "no", "not fetched",
     "",
     "NOT RE-OPENED THIS PASS. Its arts. 54-59 are quoted verbatim inside the official SAFE branch "
     "answers N03, N04 and N05, which is why those articles are still cited; the PDF itself was "
     "not fetched on 2026-11-11 and no claim rests on text that is not quoted in N03-N05."),
    ("N16", "https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html", "State Taxation Administration",
     "财税〔2008〕132号 — savings-deposit interest exemption", "no", "not fetched",
     "",
     "NOT RE-OPENED THIS PASS. Carried forward as unverified: the claim that PRC individual income "
     "tax on bank-deposit interest is suspended rests on this notice, which was not fetched on "
     "2026-11-11. Treated as unverified on the tax page (flag N676-U05)."),
    ("N17", "https://www.cbp.gov/travel/us-citizens/know-before-you-go/foreign-currency", "U.S. Customs and Border Protection",
     "Foreign currency — FinCEN Form 105 declaration over USD 10,000", "no", "not fetched",
     "",
     "NOT RE-OPENED THIS PASS. The cash-carrying route is therefore described only by what N06b "
     "verifies (China's side), and every U.S.-side cash figure is left blank and flagged "
     "(N676-U06)."),
]

SRC_FIELDS = ["id", "url", "publisher", "title", "fetched_today", "http", "quote", "supports"]

# --------------------------------------------------------------- questions register
# The deliverable no earlier session produced: what must be answered before a decision,
# what is already known, what is missing, and exactly how to get the missing part.
# id, priority, question, why_it_decides, known, missing, how_to_get, owner, source_ids
QUESTIONS = [
    ("Q01", "critical",
     "Where did the money in the Chinese account come from?",
     "This single fact chooses the route. Documented Chinese income goes under art. 59 on ID plus "
     "source and tax documents. A home sale, an inheritance and a pre-emigration estate each have "
     "their own instrument and their own document list. A gift has no verified remittance route at "
     "all. Money you cannot document has none either.",
     "The six lawful routes and the exact document each one needs are established (see Methods).",
     "Which of the six the balance actually is. Nothing in the brief says.",
     "Pull the account's own history: every credit over the last 24 months with its counterparty, "
     "plus the underlying contract, invoice, payroll record, sale deed, inheritance document or "
     "gift letter. Ask the account branch in writing to list what it holds on file for you.",
     "You, then the bank branch in writing",
     "N03|N04|N05|N07"),
    ("Q02", "critical",
     "What exactly are the 'considerable taxes' you were told about?",
     "The brief is the only evidence for them. No tax, no rate, no assessment and no office is "
     "named. If they are unpaid Chinese individual income tax on the underlying income, they are "
     "owed whether or not the money ever moves, and 3-45% or 20% dwarfs every bank cost on this "
     "site. If they are a bank's paraphrase of a documentation requirement, there may be no tax at "
     "all.",
     "Decree 532 art. 5 does not restrict current-account transfers, and no official source read "
     "here taxes the conversion or the wire itself. The PRC rates that could apply are 3-45% and "
     "20%.",
     "The name of the tax, the rate, the amount, and which tax office said it.",
     "Ask the branch for the written rule it is applying, citing the document number. If a tax is "
     "claimed, ask the local 主管税务机关 for a written 完税凭证 or a written statement of what is "
     "outstanding. Do not accept a verbal figure.",
     "You, at the branch and the local tax office",
     "N06|N09"),
    ("Q03", "critical",
     "How is your account registered — as a 境内个人 or a 境外个人?",
     "The two instruments define 境内个人 differently. Decree 532 art. 52(2) counts a foreigner "
     "continuously resident in China for a full year as a 境内个人; the current-account guidelines "
     "route a 境外个人 through art. 59 instead. Which one the bank used when it opened the account "
     "decides whether you are dealing with art. 54's convenience amount or art. 59's document "
     "requirement.",
     "Both definitions exist and both instruments are in force. Art. 59 governs a 境外个人; arts. "
     "54-57 govern a 境内个人.",
     "Which classification the bank actually recorded for this account. It is not visible from "
     "outside.",
     "Ask the branch in writing which of arts. 54-57 or art. 59 of 汇发〔2020〕14号 it will apply to "
     "your account, and on what basis it classified you. Get the answer on paper before you file "
     "anything.",
     "You, at the account branch",
     "N06|N03|N04"),
    ("Q04", "high",
     "Was Chinese individual income tax actually paid on this money?",
     "The bank will not buy dollars for a foreign individual without tax evidence under art. 59. If "
     "the tax was never paid, settling it is a precondition, not a penalty for moving the money.",
     "Art. 59 requires 有交易额的购汇资金来源材料（含税务凭证）. Art. 15 of the IIT law makes the tax "
     "certificate a condition of registering a property transfer.",
     "Your own filing history in China, and whether an employer withheld.",
     "Request your 个人所得税 filing records from the local 主管税务机关 or from the 自然人电子税务"
     "局 app, for every year the money accrued.",
     "You, with the tax authority",
     "N05|N09|N09b"),
    ("Q05", "high",
     "Is any part of the balance already foreign currency?",
     "Dollars sitting in a Chinese foreign-currency account do not need converting. That removes "
     "the entire 0.21% spread and drops the bank cost to the wire fee alone — $32.42 on $10,000 "
     "instead of $53.42, and $61.28 on $400,000 instead of $901.20.",
     "Route R2 is priced and verified. The wire fee is the same tariff either way.",
     "Whether you hold an FX account at the bank and what is in it.",
     "Check the account list in mobile banking, or ask the branch for a statement of every account "
     "in your name and its currency.",
     "You, then the bank",
     "N01|N02"),
    ("Q06", "high",
     "Do you hold a Chinese Foreign Permanent Resident ID card (外国人永久居留身份证)?",
     "If you do, the USD 50,000 annual convenience amount applies to you and a documented purchase "
     "is not needed for that slice. If you do not — which is the normal case for a U.S. passport "
     "holder — every purchase needs source and tax documents regardless of size.",
     "The rule is explicit: 持有外国人永久居留身份证的境外个人适用购汇年度便利化额度.",
     "Whether you hold the card.",
     "Look at your documents. If you have lived in China long-term, ask whether you are eligible; "
     "eligibility is a separate process and is not retroactive.",
     "You",
     "N03"),
    ("Q07", "high",
     "Which bank, and what is its actual selling rate and fee schedule?",
     "Every number on this site is Bank of China's published board and published personal tariff. "
     "A different bank quotes a different spread, and a branch may apply local variations the "
     "tariff itself allows.",
     "BOC: 1 per mille, floor RMB 50, ceiling RMB 260, plus RMB 150 telegraph. Board stamped "
     "2026-11-11 10:25:02.",
     "Your bank's live quote for your amount, and whether it charges the OUR surcharge.",
     "Ask your bank for a written quote covering the selling rate, the wire fee, the telegraph "
     "charge and any intermediary deductions, for the exact amount and date you intend to move.",
     "You, at your bank",
     "N01|N02"),
    ("Q08", "high",
     "What did the intermediary and the receiving bank actually deduct?",
     "This is the largest unknown cost on the whole transfer and no bank publishes it. It is left "
     "blank on every page rather than estimated.",
     "Nothing. No official source read here publishes correspondent or receiving-bank charges.",
     "The actual deduction on your first real wire.",
     "Choose 'OUR' (sender pays) on the first wire if your bank offers it, then reconcile the "
     "received amount against the sent amount. The difference is your true intermediary cost, and "
     "you can then decide whether to route the rest differently.",
     "You, after the first wire",
     "N02"),
    ("Q09", "high",
     "When, and at what rate, was the RMB actually acquired?",
     "The U.S. currency gain is measured against your real basis, not against an IRS average. The "
     "averages are used here only because no basis was supplied. The true figure could be a gain or "
     "a loss.",
     "§988 makes the gain ordinary income and the $200 personal-transaction threshold is the only "
     "relief. At $10,000 with a 2024 basis the modelled gain is $692.59, so the threshold is passed.",
     "The date and rate of every credit into the account.",
     "Match each credit to the spot rate on that date. IRS's own page says it has no official rate "
     "and accepts any posted rate used consistently.",
     "You, with a U.S. tax adviser",
     "N10|N11"),
    ("Q10", "high",
     "Have FBAR, Form 8938 and Form 3520 been filed for every open year?",
     "These are the penalties that can exceed the whole balance. The FBAR maximum is $16,536 "
     "non-willful and $165,353 willful per violation, assessed per year, and the general willful "
     "BSA range runs to $286,184. A foreign gift over $100,000 is separately reportable on Form "
     "3520 Part IV.",
     "The thresholds and maxima are verified from eCFR and IRS.",
     "Which years you held over $10,000 aggregate in foreign accounts, and whether you received a "
     "reportable gift or bequest.",
     "Reconstruct foreign-account balances year by year from statements, then have a U.S. adviser "
     "assess whether the Streamlined or Delinquent FBAR procedures fit. Do not move the money "
     "before this is settled.",
     "You, with a U.S. tax adviser",
     "N12|N14"),
    ("Q11", "medium",
     "If it is a home sale, is the transfer registered and is the tax certificate issued?",
     "Art. 15 of the IIT law requires the registration authority to check the individual income tax "
     "payment certificate before it registers the transfer. Without it the sale is not complete and "
     "there is nothing to remit.",
     "The requirement is in the statute. The remittance route for property proceeds is the "
     "emigrant/inheritance framework.",
     "The registration certificate and the 完税凭证.",
     "Get both from the local 不动产登记机构 and 主管税务机关. The registered contract is also what "
     "the bank will ask for.",
     "You, with the registration office",
     "N09b|N07"),
    ("Q12", "medium",
     "If it is an inheritance or a pre-emigration estate, has hukou cancellation happened?",
     "Both routes require a household-registration cancellation certificate, and the IIT law "
     "requires Chinese tax to be settled before the cancellation. The application goes to the SAFE "
     "branch at the emigrant's former hukou or the decedent's last hukou.",
     "Since 2014 the bank may remit the approved amount in one lump; the RMB 500,000 head-office "
     "filing and the two-year staging are both cancelled.",
     "The hukou cancellation certificate, proof of settlement abroad, and the SAFE approval itself.",
     "Apply through the public security household-registration office first, then to the SAFE "
     "branch. Ask that branch for its written service standard and any fee — neither is published.",
     "You, with SAFE and the PSB",
     "N07|N08|N09b"),
    ("Q13", "medium",
     "Is the money inside a company rather than in your personal account?",
     "A dividend route exists but it is a different question entirely: corporate tax, a 20% "
     "dividend withholding, a board resolution and a tax filing form, then the remittance. None of "
     "the personal routes above applies to it.",
     "The institutional profit-remittance rule requires a board resolution and the tax filing form "
     "above USD 50,000.",
     "Whether the balance is corporate.",
     "Check whose name the account is in. If it is the company's, this site's personal routes do "
     "not apply and a corporate adviser is needed.",
     "You",
     "N08b|N09"),
    ("Q14", "medium",
     "How fast do you need the money?",
     "Speed changes the route. One wire settles in days. A SAFE approval for an emigrant or "
     "inheritance transfer has no published service standard, so it cannot be scheduled. The "
     "convenience-amount route can take one calendar year per USD 50,000.",
     "One wire is the fastest verified path. Approval timelines are not published anywhere read.",
     "A real service standard from the SAFE branch that would hear your application.",
     "Ask the branch in writing. Treat any verbal timeline as unverified.",
     "You, with SAFE",
     "N08|N02"),
    ("Q15", "medium",
     "Are you a U.S. citizen living abroad, and does the FEIE apply?",
     "The FEIE ceiling is $132,900 for 2026 and $130,000 for 2025, but it covers EARNED income "
     "only. It does nothing for a dividend, a rent receipt, a property gain or the §988 currency "
     "gain — which are the likely components of this balance.",
     "The ceilings and the earned-income scope are verified from IRS.",
     "Your tax home, your qualifying days, and the composition of the balance.",
     "Have a U.S. adviser run the bona fide residence or physical presence test against your actual "
     "days, then map each component of the balance to its category.",
     "You, with a U.S. tax adviser",
     "N13"),
    ("Q16", "medium",
     "Is any of the money traceable to a gift from a Chinese person?",
     "A gift has no verified remittance route on the Chinese side — the bank needs source documents "
     "that a gift does not generate. On the U.S. side it is separately reportable above $100,000 "
     "from a nonresident alien or foreign estate.",
     "No verified Chinese route; the U.S. Form 3520 thresholds are verified.",
     "Whether a gift is involved and its size.",
     "Get the donor's written statement and any transfer record. Then ask the branch in writing "
     "what it would accept — do not assume the answer.",
     "You, then the branch",
     "N05|N14"),
    ("Q17", "low",
     "Would routing through Hong Kong, Macau or Taiwan be cheaper?",
     "The telegraph charge on that leg is RMB 80 instead of RMB 150, which saves about $10.46 per "
     "wire. But the onward leg from Hong Kong to the U.S. is a second transfer with its own "
     "charges, and none of them are published here.",
     "The RMB 80 figure is in the same published BOC tariff. Route R4 is priced for the first leg "
     "only.",
     "The onward leg's cost and any reporting consequence of the intermediate stop.",
     "Price the full two-leg route with the receiving bank before using it. The first-leg saving "
     "alone is not a reason to route through a third jurisdiction.",
     "You, with both banks",
     "N02"),
    ("Q18", "low",
     "Should the balance move in one wire or several?",
     "One wire is cheapest because the 1 per mille fee is capped at RMB 260, so the marginal cost "
     "of a bigger single wire is zero above about $38,857. Eight $50,000 wires cost $1,330.12 on "
     "$400,000 against $901.20 for one.",
     "The cap and the resulting ladder are verified. Splitting a quota across DIFFERENT people is "
     "prohibited and is treated as evasion.",
     "Whether your bank or the receiving bank imposes a per-transfer limit.",
     "Ask both banks for their single-transfer and daily limits in writing.",
     "You, with both banks",
     "N02|N06"),
]

Q_FIELDS = ["id", "priority", "question", "why_it_decides", "known", "missing",
            "how_to_get", "owner", "source_ids"]

# ------------------------------------------------------------------ methods / routes
# id, name, lawful, eligibility, documents, cap, pros, cons, tax, route, source_ids, flags
METHODS = [
    ("M01", "Documented income earned in China (salary, fees, other current-account income)",
     "Lawful", "A 境外个人 with lawful current-account RMB income earned in China.",
     "Valid ID plus source-of-funds documents showing the transaction amount, including tax "
     "certificates (有交易额的购汇资金来源材料，含税务凭证).",
     "No amount limit in the rule for genuine, lawful current-account income.",
     "The standard route for a U.S. passport holder. One wire. The cheapest conversion route. No "
     "SAFE approval step.",
     "The bank will not proceed without tax evidence. If Chinese tax was never paid on the income "
     "it must be settled first, and that tax — not the transfer — is the large number.",
     "No tax on the conversion or the wire in any source read. PRC income tax applies to the "
     "underlying income if unpaid: 3-45% on comprehensive income, 20% flat on interest, dividends, "
     "rent and property gains.",
     "R1", "N03|N04|N05|N09", "N676-U01|N676-U02"),
    ("M02", "Foreign currency already in your Chinese FX account",
     "Lawful", "You hold a foreign-currency account in China with dollars in it.",
     "Valid ID. No conversion, so no purchase documents.",
     "Not stated in the sources read.",
     "No conversion at all, so no 0.21% spread. Cheapest thing on the whole site: $32.42 on "
     "$10,000 and $61.28 on $400,000, whatever the amount.",
     "Only helps to the extent dollars are actually there. Moving CNY into the FX account first "
     "would be a conversion and would attract the spread.",
     "No conversion means no disposition of nonfunctional currency at the wire, so no §988 gain "
     "arises on the transfer. The basis column is left blank rather than guessed.",
     "R2", "N01|N02", "N676-U04"),
    ("M03", "Annual USD 50,000 convenience amount on a Chinese Foreign Permanent Resident ID",
     "Lawful — only for card holders", "A 境外个人 who holds a 外国人永久居留身份证.",
     "The card alone, inside the annual amount. Above it, source-of-funds documents.",
     "USD 50,000 equivalent per person per year on ID alone. It is not a cap: above it you simply "
     "cannot proceed on ID alone.",
     "No document assembly inside the annual amount.",
     "A U.S. passport holder without the card does not qualify at all. Above USD 50,000 the "
     "balance has to be bought year by year, one wire and one telegraph charge each — $1,330.12 on "
     "$400,000 against $901.20 for a single wire.",
     "Same as M01 for the underlying income.",
     "R3", "N03|N04", "N676-U03"),
    ("M04", "Emigrant property transfer (移民财产转移)",
     "Lawful — needs SAFE approval", "A natural person who emigrated from the mainland and had a "
     "Chinese household registration that has been cancelled.",
     "Written application, the applicant form, ID, the hukou cancellation certificate and proof of "
     "settlement abroad certified by a Chinese embassy or consulate, property-right documents, and "
     "a tax payment certificate from the tax authority where the property sits.",
     "No amount ceiling. Approval sits with the SAFE branch at your former hukou location.",
     "Built for exactly this problem: the whole pre-emigration estate, converted and remitted. "
     "Since 2014 the bank may remit the approved amount in one lump, the RMB 500,000 head-office "
     "filing is cancelled, and notarisation of property documents and of the agency agreement is "
     "cancelled.",
     "Unavailable to a U.S. citizen who never held a Chinese hukou. Approval is a SAFE decision, "
     "not an entitlement, and no fee or service standard is published. Chinese tax must be settled "
     "before the hukou is cancelled.",
     "PRC tax on the underlying property gain (20% flat on property transfer) must be evidenced "
     "before approval.",
     "R1", "N07|N08|N09|N09b", "N676-U07|N676-U08"),
    ("M05", "Inheritance transfer (继承财产转移)",
     "Lawful — needs SAFE approval", "A foreign citizen or HK/Macau resident who inherited "
     "property located in the mainland.",
     "Written application stating the relationship, the applicant form, ID with settlement-abroad "
     "proof, proof of inheritance, the decedent's property-right documents and a tax payment "
     "certificate from the tax authority where the property sits.",
     "No amount ceiling. Approval sits with the SAFE branch at the decedent's last hukou location.",
     "The right route when the money arrived by inheritance. Since 2014 several inheritances can be "
     "combined at one decedent's hukou location and notarisation is no longer required.",
     "The bank must remit straight to your own account abroad — no cash withdrawal in China. "
     "Property whose lawful source cannot be proven will not be accepted. Approval timelines are "
     "not published.",
     "PRC tax on the underlying property must be evidenced before approval.",
     "R1", "N07|N08|N09", "N676-U07|N676-U08"),
    ("M06", "Change unused RMB back with the original exchange slip",
     "Lawful", "You brought foreign currency in, converted it to RMB yourself, and still hold the "
     "exchange slip.",
     "Valid ID plus the original exchange slip.",
     "Not re-verified this pass — see flag N676-U09.",
     "Avoids the income-documentation route entirely where it applies.",
     "Depends on holding the slip and on the conversion being recent. Not verified this pass.",
     "No tax on the conversion itself in the sources read.",
     "R1", "", "N676-U09"),
    ("M07", "Wire to Hong Kong, Macau or Taiwan as a first leg",
     "Lawful", "Same as M01, with a receiving account in HK, Macau or Taiwan.",
     "Same as M01.",
     "Same as M01.",
     "The telegraph charge on that leg is RMB 80 instead of RMB 150 — about $10.46 cheaper per wire.",
     "It is only a first leg. The onward transfer to the U.S. is a second transfer with its own "
     "charges, none of them published here, and the intermediate stop may have its own reporting "
     "consequences.",
     "Same as M01.",
     "R4", "N02", "N676-U10"),
    ("M08", "Carrying banknotes across the border",
     "Restricted", "Anyone, within the limits SAFE and customs set.",
     "Declaration where required.",
     "The limits are set by SAFE under Decree 532 art. 15 but the limits themselves were not "
     "re-read this pass.",
     "No wire fee.",
     "Carrying FX out in breach draws a warning and a fine of up to 20% of the amount. On the U.S. "
     "side the declaration threshold and the form were not re-read this pass. At these amounts "
     "this route is not competitive with a wire and carries real seizure risk.",
     "No conversion tax. Reporting failures are the exposure.",
     "", "N06|N06b", "N676-U06"),
    ("M09", "Dividend from your own Chinese company",
     "Lawful — corporate route", "The money is inside a Chinese company you own.",
     "Board profit-distribution resolution and the tax filing form (税务备案表) above USD 50,000.",
     "The USD 50,000 figure here is an institutional document-review threshold, NOT the individual "
     "convenience amount.",
     "A genuine route where the money is corporate.",
     "Entirely different question from the personal routes: corporate income tax first, then 20% "
     "dividend tax, then the remittance. Needs a corporate adviser.",
     "20% individual income tax on dividends, on top of corporate tax already paid.",
     "R1", "N08b|N09", "N676-U11"),
    ("M10", "Borrowing relatives' or friends' annual amounts ('ant moving')",
     "Prohibited", "n/a", "n/a", "n/a",
     "None. It is not a route.",
     "SAFE treats quota splitting as evasion. The people involved go on a watch list for the year "
     "of listing and the following two years, during which every conversion needs transaction "
     "documents. Fines run to 30% of the amount, 30-100% in serious cases, with criminal liability "
     "possible.",
     "Not applicable.",
     "", "N06", ""),
    ("M11", "Private swaps, money changers, false invoices, crypto",
     "Prohibited", "n/a", "n/a", "n/a",
     "None. It is not a route.",
     "Art. 45 covers private buying and selling, disguised dealing, reselling and illegally "
     "brokering FX: confiscation of illegal gains, fines up to 30%, 30-100% in serious cases, and "
     "criminal liability. Art. 40 covers buying FX on false documents.",
     "Not applicable.",
     "", "N06", ""),
    ("M12", "Leaving the balance in China",
     "Lawful", "n/a", "n/a", "n/a",
     "Costs nothing today.",
     "The U.S. reporting obligations do not stop because the money did not move. FBAR and Form "
     "8938 apply to the account itself, with maxima of $16,536 and $165,353 per violation.",
     "No conversion, so no §988 gain now — but the gain is deferred, not avoided.",
     "R2", "N12", "N676-U04"),
]

M_FIELDS = ["id", "name", "status", "eligibility", "documents", "cap", "pros", "cons",
            "tax", "route", "source_ids", "flags"]

# ------------------------------------------------------------------ step-by-step plays
STEPS = [
    ("M01", 1, "Settle the U.S. side before you move anything.",
     "Reconstruct foreign-account balances year by year and have a U.S. adviser assess FBAR, Form "
     "8938 and any Form 3520 exposure. The FBAR maximum is $16,536 non-willful and $165,353 willful "
     "per violation; moving the money first does not reduce it.", "N12|N14"),
    ("M01", 2, "Assemble the source-of-funds file.",
     "Employment contract or service agreement, payroll or invoice records, and the tax evidence — "
     "a tax payment certificate, an exemption certificate or the filing form. Art. 59 requires "
     "documents showing the transaction amount and including tax certificates.", "N05"),
    ("M01", 3, "Ask the branch in writing which article it will apply.",
     "Art. 59 for a 境外个人, or arts. 54-57 if the bank classified you as a 境内个人. The two "
     "definitions of 境内个人 differ and the bank's classification is not visible from outside.",
     "N06|N03|N04"),
    ("M01", 4, "Buy the dollars at the counter or in mobile banking.",
     "You pay the bank's selling rate. On the 2026-11-11 10:25:02 board that is 6.6911 against a "
     "buying rate of 6.6630, so 0.20998% of every dollar is the rate cost.", "N01"),
    ("M01", 5, "Instruct one wire for the whole amount.",
     "The fee is 1 per mille with a RMB 50 floor and a RMB 260 ceiling, plus a RMB 150 telegraph "
     "charge. Above about $38,857 the fee is pinned at the ceiling, so one wire is always cheapest.",
     "N02"),
    ("M01", 6, "Choose the charge option deliberately.",
     "'OUR' makes you pay the intermediary charges up front and is the only way to learn what they "
     "actually are. Intermediary and receiving-bank charges are not published anywhere and are left "
     "blank on this site.", "N02"),
    ("M01", 7, "Reconcile the received amount against the sent amount.",
     "The difference is your true intermediary cost. Record it; it is the one number on this page "
     "that no official source can give you.", "N02"),
    ("M02", 1, "Confirm what is actually in the FX account.",
     "Ask the branch for a statement of every account in your name and its currency. Dollars "
     "already there need no conversion.", "N01|N02"),
    ("M02", 2, "Wire it out on your passport.",
     "No purchase, so no spread. The wire fee is the same 1 per mille / RMB 50-260 plus RMB 150 "
     "telegraph.", "N02"),
    ("M02", 3, "Do not top the FX account up from RMB first.",
     "That would be a conversion and would attract the 0.20998% spread. Only the dollars genuinely "
     "already there avoid it.", "N01"),
    ("M03", 1, "Confirm you actually hold the 外国人永久居留身份证.",
     "Without the card this route does not exist for you; the annual convenience amount is "
     "expressly limited to card holders.", "N03"),
    ("M03", 2, "Plan one calendar year per USD 50,000.",
     "Above the annual amount you either need source documents (which makes this M01) or you buy "
     "year by year. Eight wires on $400,000 costs $1,330.12 against $901.20 for one.", "N03|N02"),
    ("M03", 3, "Never use anyone else's amount.",
     "Splitting a quota across people is treated as evasion under Decree 532 art. 39 and puts the "
     "people involved on a watch list for the year and the next two.", "N06"),
    ("M04", 1, "Cancel the Chinese household registration and settle tax first.",
     "The IIT law requires tax to be cleared BEFORE the hukou is cancelled. Get the cancellation "
     "certificate from the public security office.", "N09b|N07"),
    ("M04", 2, "Apply to the SAFE branch at your former hukou location.",
     "Written application, applicant form, ID, cancellation certificate, settlement-abroad proof "
     "certified by a Chinese embassy or consulate, property-right documents, and the tax payment "
     "certificate.", "N07"),
    ("M04", 3, "Note what 2014 removed.",
     "No RMB 500,000 head-office filing. No staged remittance — the bank may remit once or in "
     "instalments inside the approved amount. No notarisation of property documents or of the "
     "agency agreement.", "N08"),
    ("M04", 4, "Instruct the bank with the approval in hand.",
     "The bank must remit straight to your own account abroad; cash withdrawal in China is not "
     "permitted. Bank cost is the same 0.20998% spread plus the wire fee.", "N07|N02"),
    ("M05", 1, "Gather the inheritance evidence.",
     "Proof of inheritance, the decedent's property-right documents, and a tax payment certificate "
     "from the tax authority where the property sits. Notarisation is no longer required.", "N07|N08"),
    ("M05", 2, "Apply to the SAFE branch at the decedent's last hukou location.",
     "Since 2014 several inheritances can be combined at one decedent's hukou location instead of "
     "applying separately.", "N08"),
    ("M05", 3, "Remit to your own account abroad.",
     "Directly to the beneficiary's account in the country of residence. No cash in China.", "N07"),
    ("M07", 1, "Price the whole two-leg route before you start.",
     "The first leg saves about $10.46 per wire on the telegraph charge (RMB 80 not RMB 150). The "
     "onward leg from Hong Kong to the U.S. is unpriced here and could easily cost more than that.",
     "N02"),
    ("M09", 1, "Treat this as a corporate question, not a personal one.",
     "Corporate income tax first, then a 20% dividend, then the remittance on a board resolution "
     "and the tax filing form. Nothing on this site prices the corporate leg.", "N08b|N09"),
]

S_FIELDS = ["method_id", "n", "step", "detail", "source_ids"]

# ------------------------------------------------------------- flags and open items
# id, kind, severity, item, detail, why_blank_or_wrong, how_to_close, source_ids
FLAGS = [
    ("N676-F01", "irregularity", "high",
     "Two data layers still instruct a reader to stage an emigrant transfer over two years, which "
     "汇发〔2014〕2号 cancelled",
     "data/cost_steps.csv rows 20-22 (method M03, steps 5-7) read 'Take tranche 1 — up to half', "
     "'Take tranche 2 — up to half the remainder, after 1 year' and 'Take tranche 3 — the balance, "
     "after 2 years … Total elapsed time from first payment: two years'. data/d646_methods.csv row 6 "
     "(M05) states 'Staged: first half, then half of remainder after 1 year, rest after 2 years' and "
     "'Yes, but staged over 2+ years'. Neither file contains the string 2014 or 汇发〔2014〕2号 "
     "anywhere (grep count 0 in both).",
     "汇发〔2014〕2号 §6(2) cancels the staged remittance: 银行可在核准件审批额度内一次或分次汇出相关资金. "
     "§6(1) also cancels the RMB 500,000 head-office filing. A reader following those rows would wait "
     "two years for money that can lawfully be remitted in one lump. (data/reference_inputs.csv R30, "
     "data/cost_inputs.csv CI29 and data/verify_2026.csv V08 record the same 2004 text, but those "
     "files do also carry the 2014 cancellation elsewhere, so they are lower risk.)",
     "The owning sessions should correct or mark those rows superseded. This session did not edit "
     "their files; the request is logged in COORDINATION.md. The n676 pages state the 2014 position "
     "only, and quote both the 2004 text and the 2014 cancellation side by side in the source "
     "register so the supersession is visible.",
     "N08|N07b"),
    ("N676-F02", "irregularity", "high",
     "Nine different headline totals for the same two transfers are live at once, with no "
     "superseded banner and no board stamp on most pages",
     "Counted across the 98 published HTML files on this tree: the $10,000 wire appears as $53.38 "
     "(36 files), $53.42 (35), $53.45 (10), $53.47 (7) and $50.93 (2); the $400,000 wire appears as "
     "$901.30 (17), $901.20 (11), $901.81 (1) and $901.09 (1).",
     "Each figure is arithmetically correct for the intraday BOC board snapshot its layer was priced "
     "from. The defect is that a reader landing on any one page has no way to tell which snapshot it "
     "used or that a newer one exists. This is a presentation defect, not an arithmetic one.",
     "Every cost page should carry the board stamp it was priced from in its heading, and older "
     "layers should carry a superseded banner. The n676 pages carry the stamp. A cross-layer banner "
     "is a shared-file change, so it is logged as a request in COORDINATION.md rather than made here.",
     "N01"),
    ("N676-F03", "irregularity", "medium",
     "BOC's 'Middle Rate' column is not the mid-point of its own buying and selling rates",
     "On 2026-11-11 10:25:02 the board shows buying 6.6630, selling 6.6911 and 'Middle Rate' 6.7191. "
     "(6.6630 + 6.6911) / 2 = 6.67705, not 6.7191.",
     "Any page that calls the board's middle column a 'fair value' or uses it as a mid-point is "
     "mislabelling it. The n676 pages compute their own mid-point, state that they do, and record "
     "the board's column separately.",
     "Nothing to close — disclosed so a reader can reconcile the two numbers.",
     "N01"),
    ("N676-F04", "irregularity", "medium",
     "汇发〔2014〕2号 is published on a branch site marked （已修改）",
     "The page carries an amendment note: 汇发〔2023〕28号 annex 4 modifies items (一) and (二) of "
     "section 3.",
     "Section 6 — the part this site relies on for emigrant and inheritance transfers — is not "
     "among the amended items, but the page does not certify that the list is exhaustive.",
     "Confirm section 6 against the current consolidated text on the SAFE head-office site before "
     "filing. Logged as an open item.",
     "N08"),
    ("N676-F05", "irregularity", "medium",
     "The USD 50,000 figure is used for two unrelated rules across the tree",
     "One is the individual annual convenience amount (汇发〔2020〕14号 art. 55, ID-only purchases, "
     "card holders only). The other is the institutional profit-remittance document-review "
     "threshold in 汇发〔2014〕2号 §5(1), which applies to companies.",
     "Conflating them leads to the belief that a U.S. individual may remit USD 50,000 a year on ID "
     "alone, which art. 59 does not permit without a Foreign Permanent Resident ID.",
     "Keep the two labelled distinctly on every page. The n676 methods table separates them "
     "(M03 vs M09).",
     "N03|N08b"),
    ("N676-U01", "unverified", "high",
     "Where the money came from",
     "The brief does not say. Every route on this site is conditioned on it.",
     "No document, statement or account history was supplied.",
     "See question Q01.", "N03|N05"),
    ("N676-U02", "unverified", "high",
     "What the 'considerable amount of taxes' actually are",
     "No tax name, rate, amount, assessment or office is given anywhere in the brief.",
     "The phrase is user-reported and cannot be verified from any official source.",
     "See question Q02.", "N09"),
    ("N676-U03", "unverified", "medium",
     "Whether the reader holds a Chinese Foreign Permanent Resident ID",
     "Decides whether the USD 50,000 annual convenience amount is available at all.",
     "Not stated in the brief.",
     "See question Q06.", "N03"),
    ("N676-U04", "unverified", "medium",
     "Intermediary and receiving-bank charges, and the R2 currency-gain basis",
     "Left blank in every table on this site rather than estimated.",
     "No bank publishes correspondent charges, and route R2 involves no conversion, so there is no "
     "basis rate to cite.",
     "See questions Q08 and Q09.", "N02|N11"),
    ("N676-U05", "unverified", "medium",
     "PRC individual income tax on bank-deposit interest",
     "Left blank. The suspension rests on 财税〔2008〕132号, which was not re-opened this pass.",
     "Not fetched on 2026-11-11, so no verbatim quote exists for it in this register.",
     "Fetch the notice and record it before relying on the exemption.", "N16"),
    ("N676-U06", "unverified", "medium",
     "Cash-carrying limits on both sides of the border",
     "Left blank. Decree 532 art. 15 delegates the limits to SAFE without stating them, and the "
     "CBP declaration page was not re-opened this pass.",
     "Neither the Chinese limit nor the U.S. threshold and form were verified today.",
     "Fetch the SAFE cash-carrying rule and the CBP page before describing this route.", "N06b|N17"),
    ("N676-U07", "unverified", "medium",
     "SAFE approval fees and service standards for emigrant and inheritance transfers",
     "Left blank on every page.",
     "The 2014 notice sets the approval route but publishes neither a fee nor a service standard.",
     "Ask the SAFE branch in writing for both.", "N08"),
    ("N676-U08", "unverified", "medium",
     "No verified remittance route for money received as a gift or with no documents",
     "Left blank. The methods table records 'no verified route' rather than a cost.",
     "Art. 59 requires source documents that a gift does not generate, and 2004 No. 16 art. 12 "
     "refuses applications for property whose lawful source cannot be proven.",
     "Ask the branch in writing what it would accept. See question Q16.", "N05|N07"),
    ("N676-U09", "unverified", "low",
     "The 'change unused RMB back' route (M06)",
     "Listed with its cap left blank.",
     "The SAFE branch answer supporting it was not re-opened on 2026-11-11, so no verbatim quote "
     "is held for it in this register.",
     "Re-fetch the answer and record it, or drop the row.", ""),
    ("N676-U10", "unverified", "low",
     "The onward leg of a Hong Kong, Macau or Taiwan routing (M07)",
     "Only the first leg is priced.",
     "No source read here publishes the cost of the second leg or its reporting consequences.",
     "Price the full route with the receiving bank.", "N02"),
    ("N676-U11", "unverified", "low",
     "The corporate tax leg of a dividend remittance (M09)",
     "Left blank.",
     "Only the 20% individual dividend rate and the institutional document rule were verified. The "
     "corporate income tax computation was not read this pass.",
     "Needs a corporate adviser and the corporate tax return.", "N08b|N09"),
]

F_FIELDS = ["id", "kind", "severity", "item", "detail", "why_blank_or_wrong", "how_to_close",
            "source_ids"]


def write(name, fields, rows):
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        w.writerows(rows)
    return path, len(rows)


def main():
    out = []
    out.append(write("n676_sources.csv", SRC_FIELDS, SOURCES))
    out.append(write("n676_questions.csv", Q_FIELDS, QUESTIONS))
    out.append(write("n676_methods.csv", M_FIELDS, METHODS))
    out.append(write("n676_steps.csv", S_FIELDS, STEPS))
    out.append(write("n676_flags.csv", F_FIELDS, FLAGS))
    for path, n in out:
        print(f"wrote {os.path.relpath(path, ROOT)}: {n} rows")


if __name__ == "__main__":
    main()
