#!/usr/bin/env python3
"""Build the 6da0 layer: what settling up unpaid tax costs, in China and in the U.S.

Session arena/6da06d4e-china3. One page, five CSV files and one research note, all generated
from the literals in this file so that the page and the data cannot drift apart.

    python3 scripts/build_6da0.py           # write the files
    python3 scripts/build_6da0.py --check   # exit 1 if a committed file differs from a fresh build

Rules this file follows
-----------------------
* Every figure used in a calculation is listed in INPUTS with the source it was read from and a
  token that must appear, character for character, in that source's recorded quotation.
  scripts/verify_6da0.py enforces this and recomputes every ladder cell with its own code.
* A value that could not be read on an official page is None. It is rendered as "not verified"
  with a link to the flag that explains why. Nothing is estimated to fill a gap.
* "read" is "full" when the page itself was fetched and the passage read on it, and "excerpt"
  when the passage is the official page's own text as returned by a search of that URL.
* No third-party dependencies, no timestamps, no network access: the build is deterministic.
"""
from __future__ import annotations

import csv
import html
import io
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
READ_ON = "2026-11-11"
PAGE = "6da0-settle-up.html"
REPO = "https://github.com/sassnarep3-star/China3"

TCAL = "https://fgk.chinatax.gov.cn/zcfgk/c100009/c5195081/content.html"
TCAL_RULES = "https://fgk.chinatax.gov.cn/zcfgk/c100010/c5195082/content.html"
IIT = "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html"
P514 = "https://www.irs.gov/pub/irs-pdf/p514.pdf"
USC5321 = "https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm"
USC6501 = "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/pdf/USCODE-2023-title26-subtitleF-chap66-subchapA-sec6501.pdf"
ECFR = "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821"
VDP = "https://www.irs.gov/compliance/criminal-investigation/irs-criminal-investigation-voluntary-disclosure-practice"

NPC = "National People's Congress Standing Committee, on the State Taxation Administration policy database"
STC = "State Council, on the State Taxation Administration policy database"
STA = "State Taxation Administration"
IRS = "Internal Revenue Service"
GPO = "U.S. Government Publishing Office (United States Code)"

# id, side, issuer, document, url, read, quote, plain-English rendering (ours)
SOURCES = [
    ("C01.32", "China", NPC, "Tax Collection and Administration Law, art. 32", TCAL, "full",
     "纳税人未按照规定期限缴纳税款的，扣缴义务人未按照规定期限解缴税款的，税务机关除责令限期缴纳外，从滞纳税款之日起，按日加收滞纳税款万分之五的滞纳金。",
     "Tax not paid by the deadline carries a surcharge of 0.05% of the late tax per day, from the day it became late."),
    ("C01.44", "China", NPC, "Tax Collection and Administration Law, art. 44", TCAL, "full",
     "欠缴税款的纳税人或者他的法定代表人需要出境的，应当在出境前向税务机关结清应纳税款、滞纳金或者提供担保。未结清税款、滞纳金，又不提供担保的，税务机关可以通知出境管理机关阻止其出境。",
     "A taxpayer who owes tax must settle the tax and surcharge, or give a guarantee, before leaving the country; otherwise the tax office may ask the exit authority to stop the departure."),
    ("C01.52", "China", NPC, "Tax Collection and Administration Law, art. 52", TCAL, "full",
     "因税务机关的责任，致使纳税人、扣缴义务人未缴或者少缴税款的，税务机关在三年内可以要求纳税人、扣缴义务人补缴税款，但是不得加收滞纳金。因纳税人、扣缴义务人计算错误等失误，未缴或者少缴税款的，税务机关在三年内可以追征税款、滞纳金；有特殊情况的，追征期可以延长到五年。对偷税、抗税、骗税的，税务机关追征其未缴或者少缴的税款、滞纳金或者所骗取的税款，不受前款规定期限的限制。",
     "Shortfall caused by the tax office: tax may be recovered for three years, with no surcharge. Shortfall caused by the taxpayer's calculation mistake: tax and surcharge for three years, five in special circumstances. Evasion, resistance or fraud: no time limit."),
    ("C01.62", "China", NPC, "Tax Collection and Administration Law, art. 62", TCAL, "full",
     "纳税人未按照规定的期限办理纳税申报和报送纳税资料的，或者扣缴义务人未按照规定的期限向税务机关报送代扣代缴、代收代缴税款报告表和有关资料的，由税务机关责令限期改正，可以处二千元以下的罚款；情节严重的，可以处二千元以上一万元以下的罚款。",
     "Filing late: an order to correct and a possible fine of up to RMB 2,000, or RMB 2,000 to 10,000 in serious cases."),
    ("C01.63", "China", NPC, "Tax Collection and Administration Law, art. 63, first paragraph", TCAL, "full",
     "纳税人伪造、变造、隐匿、擅自销毁帐簿、记帐凭证，或者在帐簿上多列支出或者不列、少列收入，或者经税务机关通知申报而拒不申报或者进行虚假的纳税申报，不缴或者少缴应纳税款的，是偷税。对纳税人偷税的，由税务机关追缴其不缴或者少缴的税款、滞纳金，并处不缴或者少缴的税款百分之五十以上五倍以下的罚款；构成犯罪的，依法追究刑事责任。",
     "Evasion is forging, altering, hiding or destroying records, overstating expenses or leaving out income, refusing to file after the tax office's notice, or filing a false return. The tax office recovers the tax and surcharge and adds a fine of 50% to five times the unpaid tax; crimes are prosecuted."),
    ("C01.64", "China", NPC, "Tax Collection and Administration Law, art. 64, second paragraph", TCAL, "full",
     "纳税人不进行纳税申报，不缴或者少缴应纳税款的，由税务机关追缴其不缴或者少缴的税款、滞纳金，并处不缴或者少缴的税款百分之五十以上五倍以下的罚款。",
     "A taxpayer who does not file and so does not pay: the tax office recovers the tax and surcharge and adds a fine of 50% to five times the unpaid tax."),
    ("C01.68", "China", NPC, "Tax Collection and Administration Law, art. 68", TCAL, "full",
     "纳税人、扣缴义务人在规定期限内不缴或者少缴应纳或者应解缴的税款，经税务机关责令限期缴纳，逾期仍未缴纳的，税务机关除依照本法第四十条的规定采取强制执行措施追缴其不缴或者少缴的税款外，可以处不缴或者少缴的税款百分之五十以上五倍以下的罚款。",
     "Tax still unpaid after the tax office's order: enforced collection and a possible fine of 50% to five times the unpaid tax."),
    ("C01.69", "China", NPC, "Tax Collection and Administration Law, art. 69", TCAL, "full",
     "扣缴义务人应扣未扣、应收而不收税款的，由税务机关向纳税人追缴税款，对扣缴义务人处应扣未扣、应收未收税款百分之五十以上三倍以下的罚款。",
     "Where the withholding agent failed to withhold, the tax office recovers the tax from the taxpayer and fines the withholding agent 50% to three times the tax."),
    ("C01.86", "China", NPC, "Tax Collection and Administration Law, art. 86", TCAL, "full",
     "违反税收法律、行政法规应当给予行政处罚的行为，在五年内未被发现的，不再给予行政处罚。",
     "A violation that should be punished is no longer punished if it was not discovered within five years."),
    ("C01.88", "China", NPC, "Tax Collection and Administration Law, art. 88, first paragraph", TCAL, "full",
     "纳税人、扣缴义务人、纳税担保人同税务机关在纳税上发生争议时，必须先依照税务机关的纳税决定缴纳或者解缴税款及滞纳金或者提供相应的担保，然后可以依法申请行政复议；对行政复议决定不服的，可以依法向人民法院起诉。",
     "In a dispute over tax, the taxpayer must first pay the tax and surcharge or give a guarantee, and may then apply for administrative review, and after that sue."),
    ("C02.74", "China", STC, "Implementing Rules of the Tax Collection and Administration Law, art. 74", TCAL_RULES, "full",
     "欠缴税款的纳税人或者其法定代表人在出境前未按照规定结清应纳税款、滞纳金或者提供纳税担保的，税务机关可以通知出入境管理机关阻止其出境。阻止出境的具体办法，由国家税务总局会同公安部制定。",
     "If tax and surcharge are not settled or guaranteed before departure, the tax office may notify the exit-entry authority to stop the departure."),
    ("C02.75", "China", STC, "Implementing Rules of the Tax Collection and Administration Law, art. 75", TCAL_RULES, "full",
     "税收征管法第三十二条规定的加收滞纳金的起止时间，为法律、行政法规规定或者税务机关依照法律、行政法规的规定确定的税款缴纳期限届满次日起至纳税人、扣缴义务人实际缴纳或者解缴税款之日止。",
     "The surcharge runs from the day after the payment deadline to the day the tax is actually paid."),
    ("C02.80", "China", STC, "Implementing Rules of the Tax Collection and Administration Law, art. 80", TCAL_RULES, "full",
     "税收征管法第五十二条所称税务机关的责任，是指税务机关适用税收法律、行政法规不当或者执法行为违法。",
     "'The tax office's responsibility' means the office applied the law wrongly or enforced it unlawfully."),
    ("C02.81", "China", STC, "Implementing Rules of the Tax Collection and Administration Law, art. 81", TCAL_RULES, "full",
     "税收征管法第五十二条所称纳税人、扣缴义务人计算错误等失误，是指非主观故意的计算公式运用错误以及明显的笔误。",
     "'Calculation mistakes' means unintended misuse of a formula and obvious clerical errors."),
    ("C02.82", "China", STC, "Implementing Rules of the Tax Collection and Administration Law, art. 82", TCAL_RULES, "full",
     "税收征管法第五十二条所称特殊情况，是指纳税人或者扣缴义务人因计算错误等失误，未缴或者少缴、未扣或者少扣、未收或者少收税款，累计数额在１０万元以上的。",
     "'Special circumstances' means a shortfall from calculation mistakes that adds up to RMB 100,000 or more."),
    ("C02.83", "China", STC, "Implementing Rules of the Tax Collection and Administration Law, art. 83", TCAL_RULES, "full",
     "税收征管法第五十二条规定的补缴和追征税款、滞纳金的期限，自纳税人、扣缴义务人应缴未缴或者少缴税款之日起计算。",
     "The recovery periods in art. 52 are counted from the day the tax should have been paid."),
    ("C03", "China", STA, "Reply on the recovery period for undeclared tax, Guo Shui Han [2009] No. 326",
     "https://www.chinatax.gov.cn/chinatax/n810341/n810765/n812166/200906/c1188537/content.html", "full",
     "税收征管法第六十四条第二款规定的纳税人不进行纳税申报造成不缴或少缴应纳税款的情形不属于偷税、抗税、骗税，其追征期按照税收征管法第五十二条规定的精神，一般为三年，特殊情况可以延长至五年。",
     "Not filing, as described in art. 64 paragraph 2, is not evasion, resistance or fraud; its recovery period follows the spirit of art. 52: generally three years, up to five in special circumstances."),
    ("C04.2", "China", "National People's Congress Standing Committee, on the State Taxation Administration site", "Individual Income Tax Law (2018), art. 2", IIT, "full",
     "下列各项个人所得，应当缴纳个人所得税：（一）工资、薪金所得；（二）劳务报酬所得；（三）稿酬所得；（四）特许权使用费所得；（五）经营所得；（六）利息、股息、红利所得；（七）财产租赁所得；（八）财产转让所得；（九）偶然所得。",
     "Nine kinds of income are taxed: wages; fees for services; author's fees; royalties; business income; interest and dividends; rent; gains on selling property; incidental income."),
    ("C04.3", "China", "National People's Congress Standing Committee, on the State Taxation Administration site", "Individual Income Tax Law (2018), art. 3", IIT, "full",
     "（一）综合所得，适用百分之三至百分之四十五的超额累进税率（税率表附后）；（二）经营所得，适用百分之五至百分之三十五的超额累进税率（税率表附后）；（三）利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十。",
     "Wages and fees taken together: 3% to 45% progressive. Business income: 5% to 35% progressive. Interest, dividends, rent, property gains and incidental income: a flat 20%."),
    ("C04.6", "China", "National People's Congress Standing Committee, on the State Taxation Administration site", "Individual Income Tax Law (2018), art. 6", IIT, "full",
     "（一）居民个人的综合所得，以每一纳税年度的收入额减除费用六万元以及专项扣除、专项附加扣除和依法确定的其他扣除后的余额，为应纳税所得额。 […] （四）财产租赁所得，每次收入不超过四千元的，减除费用八百元；四千元以上的，减除百分之二十的费用，其余额为应纳税所得额。（五）财产转让所得，以转让财产的收入额减除财产原值和合理费用后的余额，为应纳税所得额。（六）利息、股息、红利所得和偶然所得，以每次收入额为应纳税所得额。",
     "A resident's yearly wages and fees are taxed after deducting RMB 60,000 and the other allowed deductions. Rent: deduct RMB 800 if the payment is RMB 4,000 or less, otherwise 20%. Property sale: proceeds minus original cost and reasonable expenses. Interest, dividends and incidental income: the full amount of each payment."),
    ("C04.9", "China", "National People's Congress Standing Committee, on the State Taxation Administration site", "Individual Income Tax Law (2018), art. 9", IIT, "full",
     "个人所得税以所得人为纳税人，以支付所得的单位或者个人为扣缴义务人。",
     "The person who receives the income is the taxpayer; the organisation or person who pays it is the withholding agent."),
    ("C04.10", "China", "National People's Congress Standing Committee, on the State Taxation Administration site", "Individual Income Tax Law (2018), art. 10", IIT, "full",
     "有下列情形之一的，纳税人应当依法办理纳税申报： […] （二）取得应税所得没有扣缴义务人；（三）取得应税所得，扣缴义务人未扣缴税款；",
     "The taxpayer must file a return when taxable income had no withholding agent, or when the withholding agent did not withhold."),
    ("C04.13", "China", "National People's Congress Standing Committee, on the State Taxation Administration site", "Individual Income Tax Law (2018), art. 13", IIT, "full",
     "纳税人取得应税所得没有扣缴义务人的，应当在取得所得的次月十五日内向税务机关报送纳税申报表，并缴纳税款。纳税人取得应税所得，扣缴义务人未扣缴税款的，纳税人应当在取得所得的次年六月三十日前，缴纳税款；税务机关通知限期缴纳的，纳税人应当按照期限缴纳税款。",
     "No withholding agent: file and pay within the first 15 days of the following month. Withholding agent did not withhold: pay by 30 June of the following year, or by the date in the tax office's notice."),
    ("C05", "China", "National People's Congress (npc.gov.cn)", "Individual Income Tax Law (2018), Rate Table 1, text version",
     "http://www.npc.gov.cn/zgrdw/npc/xinwen/2018-09/05/content_2060671.htm", "excerpt",
     "个人所得税税率表一（综合所得适用）级数 · 全年应纳税所得额 · 税率（％） 1 · 不超过36000元的 · 3 2 · 超过36000元至144000元的部分 · 10 3 · 超过144000元至300000元的部分 · 20 4 · 超过300000元至420000元的部分 · 25 5 · 超过420000元至660000元的部分 · 30 6 · 超过660000元至960000元的部分 · 35 7 · 超过960000元的部分 · 45",
     "Yearly taxable income: up to 36,000 at 3%; 36,000 to 144,000 at 10%; to 300,000 at 20%; to 420,000 at 25%; to 660,000 at 30%; to 960,000 at 35%; above 960,000 at 45%. On the tax administration's own page this table is an image, so the text was taken from the legislature's page."),
    ("C06", "China", NPC, "Criminal Law Amendment (VII), item 3, which sets the text of Criminal Law art. 201",
     "https://fgk.chinatax.gov.cn/zcfgk/c100009/c5211808/content.html", "excerpt",
     "纳税人采取欺骗、隐瞒手段进行虚假纳税申报或者不申报，逃避缴纳税款数额较大并且占应纳税额百分之十以上的，处三年以下有期徒刑或者拘役，并处罚金；数额巨大并且占应纳税额百分之三十以上的，处三年以上七年以下有期徒刑，并处罚金。 […] 有第一款行为，经税务机关依法下达追缴通知后，补缴应纳税款，缴纳滞纳金，已受行政处罚的，不予追究刑事责任；但是，五年内因逃避缴纳税款受过刑事处罚或者被税务机关给予二次以上行政处罚的除外。",
     "Evading a relatively large amount that is 10% or more of the tax due: up to three years' imprisonment and a fine. A huge amount that is 30% or more: three to seven years. No criminal liability if, after the tax office's recovery notice, the person pays the tax and surcharge and has received the administrative penalty, unless convicted of evasion or administratively punished twice or more for it within five years."),
    ("C07", "China", "National People's Congress Standing Committee, published by the National Bureau of Statistics", "Administrative Compulsion Law, art. 45",
     "https://www.stats.gov.cn/gk/tjfg/xgfxfg/202503/t20250306_1958900.html", "excerpt",
     "加处罚款或者滞纳金的数额不得超出金钱给付义务的数额。",
     "Added fines or surcharges may not exceed the amount of the payment obligation itself."),
    ("C08", "China", "State Taxation Administration, as republished in the Ministry of Commerce policy database", "Reply on individual income tax a government body failed to withhold, Guo Shui Han [2004] No. 1199, item 3",
     "https://policy.mofcom.gov.cn/claw/clawContent.shtml?id=43767", "excerpt",
     "按照《征管法》规定的原则，扣缴义务人应扣未扣税款，无论适用修订前还是修订后的《征管法》，均不得向纳税人或扣缴义务人加收滞纳金。",
     "Where a withholding agent failed to withhold, no surcharge may be charged to the taxpayer or to the withholding agent, under either version of the collection law."),
    ("C09", "China", STA, "Announcement [2018] No. 55: the Tax Payment Record (纳税记录) replaces the paper tax certificate",
     "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194832/content.html", "excerpt",
     "纳税人2019年1月1日以后取得应税所得并由扣缴义务人向税务机关办理了全员全额扣缴申报，或根据税法规定自行向税务机关办理纳税申报的，不论是否实际缴纳税款，均可以申请开具《纳税记录》。 […] 纳税人可以通过电子税务局、手机APP申请开具本人的个人所得税《纳税记录》，也可到办税服务厅申请开具。",
     "For income from 1 January 2019 that was reported by the withholding agent or declared by the taxpayer, a Tax Payment Record can be issued whether or not tax was actually paid. It is issued through the electronic tax bureau, the mobile app, or a tax service hall."),
    ("C09b", "China", STA, "Announcement [2018] No. 55, item 1, on the State Taxation Administration site",
     "https://www.chinatax.gov.cn/chinatax/n810341/n810765/n3359382/201812/c4183165/content.html", "excerpt",
     "纳税人申请开具税款所属期为2018年12月31日（含）以前个人所得税缴（退）税情况证明的，税务机关继续开具《税收完税证明》（文书式）。",
     "For tax periods up to 31 December 2018 the tax office still issues the older paper Tax Payment Certificate (税收完税证明)."),
    ("C10", "China", "State Administration of Foreign Exchange, Tianjin branch", "Personal foreign exchange Q&A (08), 13 July 2026, quoting art. 59 of the 2020 Current Account Guidelines",
     "https://www.safe.gov.cn/tianjin/2026/0713/3088.html", "full",
     "境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇",
     "A foreign individual buys foreign currency at a bank for lawful RMB current-account income earned in China with valid ID and documents showing the source of the funds and the amount, including tax evidence."),
    ("C11", "China", "Ministry of Finance and State Taxation Administration", "Cai Shui [2008] No. 132 on savings-deposit interest",
     "https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html", "excerpt",
     "自2008年10月9日起，对储蓄存款利息所得暂免征收个人所得税。",
     "From 9 October 2008, individual income tax on savings-deposit interest is temporarily not collected."),
    ("C12", "China", "Bank of China", "Exchange rate board, English page, published 2026/11/11 11:00:03",
     "https://www.boc.cn/sourcedb/whpj/enindex_1619.html", "full",
     "USD | 666.29 | 666.29 | 669.1 | 669.1 | 671.91 | 2026/11/11 11:00:03",
     "U.S. dollar per 100: buying 666.29, cash buying 666.29, selling 669.1, cash selling 669.1, middle 671.91."),
    ("U01", "U.S.", IRS, "Streamlined filing compliance procedures",
     "https://www.irs.gov/individuals/international-taxpayers/streamlined-filing-compliance-procedures", "full",
     "Non-willful conduct is conduct that is due to negligence, inadvertence, or mistake or conduct that is the result of a good faith misunderstanding of the requirements of the law […] If the IRS has initiated a civil examination of taxpayer's returns for any taxable year, regardless of whether the examination relates to undisclosed foreign financial assets, the taxpayer will not be eligible to use the streamlined procedures.",
     "The streamlined procedures need a certification that the failure was not willful, and close once the IRS has opened an examination of any year."),
    ("U02", "U.S.", IRS, "U.S. taxpayers residing outside the United States (Streamlined Foreign Offshore Procedures)",
     "https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-outside-the-united-states", "full",
     "in any one or more of the most recent three years for which the U.S. tax return due date (or properly applied for extended due date) has passed, the individual did not have a U.S. abode and the individual was physically outside the United States for at least 330 full days. […] (1) for each of the most recent 3 years for which the U.S. tax return due date (or properly applied for extended due date) has passed, file delinquent or amended tax returns, together with all required information returns (e.g., Forms 3520, 5471, and 8938) and (2) for each of the most recent 6 years for which the FBAR due date has passed, file any delinquent FBARs […] will not be subject to failure-to-file and failure-to-pay penalties, accuracy-related penalties, information return penalties, or FBAR penalties.",
     "Living abroad test: no U.S. home and 330 full days outside the U.S. in at least one of the last three years. File three years of returns and six years of FBARs and pay the tax and interest. No penalties."),
    ("U03", "U.S.", IRS, "U.S. taxpayers residing in the United States (Streamlined Domestic Offshore Procedures)",
     "https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-in-the-united-states", "full",
     "have previously filed a U.S. tax return (if required) for each of the most recent 3 years for which the U.S. tax return due date (or properly applied for extended due date) has passed […] The Title 26 miscellaneous offshore penalty is equal to 5 percent of the highest aggregate balance/value of the taxpayer’s foreign financial assets that are subject to the miscellaneous offshore penalty during the years in the covered tax return period and the covered FBAR period. […] will be subject only to the Title 26 miscellaneous offshore penalty and will not be subject to accuracy-related penalties, information return penalties, or FBAR penalties.",
     "For people living in the U.S. who filed returns for the last three years: amend three years, file six years of FBARs, pay tax, interest and a single penalty of 5% of the highest year-end total of the unreported foreign assets. No other penalties."),
    ("U04", "U.S.", "Taxpayer Advocate Service (an independent organization within the IRS)", "Foreign Bank and Financial Accounts (FBAR)",
     "https://www.taxpayeradvocate.irs.gov/get-help/international/foreign-bank-financial-accounts/", "full",
     "The IRS won’t impose a penalty for failure to file delinquent FBARs if you reported your foreign income properly and paid any associated taxes on your U.S. tax return and it hasn’t already contacted you about an audit or request for delinquent returns for the years covered by the delinquent FBARs.",
     "Late FBARs carry no penalty if the foreign income was reported and taxed and the IRS has not already been in touch about those years."),
    ("U05", "U.S.", IRS, "Delinquent international information return submission procedures",
     "https://www.irs.gov/individuals/international-taxpayers/delinquent-international-information-return-submission-procedures", "full",
     "should file the delinquent information returns through normal filing procedures. Penalties may be assessed in accordance with existing procedures.",
     "Other late international forms are filed the normal way, with a reasonable-cause statement if one applies; penalties may still be assessed."),
    ("U06", "U.S.", IRS, "IRS Criminal Investigation Voluntary Disclosure Practice", VDP, "full",
     "If you have willfully failed to comply with tax or tax-related obligations, submitting a voluntary disclosure may be a means to resolve your non-compliance and limit exposure to criminal prosecution. […] Review the news release, issued on Dec. 22, 2025, announcing a 90-day comment period on the Voluntary Disclosure Practice proposal. […] For amended returns, a 20 percent accuracy-related penalty applies to each year.",
     "The route for willful cases. Its penalty terms were put out for public comment on 22 December 2025; the page describes the proposed terms, not final ones."),
    ("U07", "U.S.", IRS, "Options available for U.S. taxpayers with undisclosed foreign financial assets",
     "https://www.irs.gov/individuals/international-taxpayers/options-available-for-us-taxpayers-with-undisclosed-foreign-financial-assets", "full",
     "the IRS offers the following options for addressing previous failures to comply with U.S. tax and information return obligations with respect to those investments: IRS Criminal Investigation Voluntary Disclosure Practice; Streamlined Filing Compliance Procedures; and Delinquent international information return submission procedures.",
     "The IRS lists three options: voluntary disclosure, the streamlined procedures, and the late information-return procedure."),
    ("U08", "U.S.", "Financial Crimes Enforcement Network, in the Electronic Code of Federal Regulations", "31 CFR 1010.821, Table 1 (page stated: up to date as of 11/09/2026)", ECFR, "full",
     "Maximum penalty amounts or range of minimum and maximum penalty amounts for penalties assessed on or after January 17, 2025 […] 31 U.S.C. 5321(a)(5)(B)(i) | Foreign Financial Agency Transaction—Non-Willful Violation of Transaction | 10,000 | 16,536 […] 31 U.S.C. 5321(a)(5)(C)(i)(I) | Foreign Financial Agency Transaction—Willful Violation of Transaction | 100,000 | 165,353",
     "Inflation-adjusted FBAR ceilings for penalties assessed on or after 17 January 2025: $16,536 for a non-willful violation, $165,353 as the fixed-dollar ceiling for a willful one."),
    ("U09", "U.S.", GPO, "31 U.S.C. 5321(a)(5) and (b)(1)", USC5321, "full",
     "(ii) Reasonable cause exception.—No penalty shall be imposed under subparagraph (A) with respect to any violation if— (I) such violation was due to reasonable cause, and (II) the amount of the transaction or the balance in the account at the time of the transaction was properly reported. […] (i) the maximum penalty under subparagraph (B)(i) shall be increased to the greater of— (I) $100,000, or (II) 50 percent of the amount determined under subparagraph (D) […] in the case of a violation involving a failure to report the existence of an account or any identifying information required to be provided with respect to an account, the balance in the account at the time of the violation. […] (1) Assessments.—The Secretary of the Treasury may assess a civil penalty under subsection (a) at any time before the end of the 6-year period beginning on the date of the transaction with respect to which the penalty is assessed.",
     "No non-willful penalty where there was reasonable cause and the balance was properly reported. A willful violation is capped at the greater of the fixed dollar amount or 50% of the account balance at the time of the violation. Penalties may be assessed for six years."),
    ("U10", "U.S.", "Supreme Court of the United States", "Bittner v. United States, No. 21-1195, decided 28 February 2023",
     "https://www.supremecourt.gov/opinions/22pdf/21-1195_h3ci.pdf", "excerpt",
     "The BSA’s $10,000 maximum penalty for the nonwillful failure to file a compliant report accrues on a per-report, not a per-account, basis.",
     "The non-willful FBAR penalty is counted once per annual report, not once per account."),
    ("U11", "U.S.", IRS, "Publication 514, Foreign Tax Credit for Individuals (current edition)", P514, "excerpt",
     "If you use the cash method of accounting, you can claim the credit only in the year in which you pay the tax. […] You make the choice by checking the “Accrued” box in Part II of Form 1116 on a timely filed original return. You cannot make this choice on an amended return. Once you make that choice, you must follow it in all later years and take a credit for foreign taxes in the year they accrue. […] If, because of the limit on the credit, you cannot use the full amount of qualified foreign taxes paid or accrued in the tax year, you are allowed a 1-year carryback and then a 10-year carryover of the unused foreign taxes. […] If you pay more foreign tax than you originally claimed a credit for, you have 10 years to file a claim for refund of U.S. taxes.",
     "A cash-method taxpayer credits foreign tax in the year it is paid. Choosing the year the tax accrued is possible only on a timely original return and then binds later years. There is a limit; unused credit goes back one year and forward ten. A refund claim for extra foreign tax paid can be made for ten years."),
    ("U12", "U.S.", IRS, "Failure to file penalty", "https://www.irs.gov/payments/failure-to-file-penalty", "full",
     "The penalty is 5% of the tax due (less any tax paid on time and available credits) for each month or partial month the return is late. The penalty accrues up to a maximum of 25%. […] the failure to file penalty is reduced by the amount of the failure to pay penalty (0.5% for each month).",
     "Late filing: 5% of the unpaid tax per month, up to 25%. Late payment: 0.5% per month."),
    ("U13", "U.S.", IRS, "Accuracy-related penalty", "https://www.irs.gov/payments/accuracy-related-penalty", "full",
     "In cases of substantial understatement, the accuracy-related penalty is 20% of the portion of the underpayment of tax.",
     "Understating tax substantially: 20% of the underpaid tax."),
    ("U14", "U.S.", IRS, "Quarterly interest rates", "https://www.irs.gov/payments/quarterly-interest-rates", "full",
     "Current year 2026 quarterly interest rates […] Underpayment (corporate and non-corporate) | 7% | 7% | 6% | 7% […] 2025 […] Underpayment (corporate and non-corporate) | 7% | 7% | 7% | 7% […] 2024 […] Underpayment (corporate and non-corporate) | 8% | 8% | 8% | 8%",
     "Interest on unpaid tax: 7% in the fourth quarter of 2026; 6% to 7% during 2026; 7% in 2025; 8% in 2024."),
    ("U15", "U.S.", IRS, "Interest", "https://www.irs.gov/payments/interest", "full",
     "Tax is due on the return filing date; extensions to file do not extend the date for payment of the tax. […] Interest will continue to accrue daily on any amount not paid, including on both penalties and interest.",
     "Interest runs from the original due date and accrues daily, on tax, penalties and earlier interest."),
    ("U16", "U.S.", GPO, "26 U.S.C. 6501(a), (c)(3) and (e)(1)(A)", USC6501, "excerpt",
     "the amount of any tax imposed by this title shall be assessed within 3 years after the return was filed […] In the case of failure to file a return, the tax may be assessed, or a proceeding in court for the collection of such tax may be begun without assessment, at any time. […] (II) is in excess of $5,000, the tax may be assessed, or a proceeding in court for collection of such tax may be begun without assessment, at any time within 6 years after the return was filed.",
     "Tax can be assessed for three years after a return is filed; at any time if no return was filed; for six years if more than $5,000 of income from reportable foreign assets was left out."),
    ("U17", "U.S.", IRS, "Instructions for Form 1040 (2025), Foreign-Source Income", "https://www.irs.gov/instructions/i1040gi", "excerpt",
     "You must report unearned income, such as interest, dividends, and pensions, from sources outside the United States unless exempt by law or a tax treaty. You must also report earned income, such as wages and tips, from sources outside the United States. […] You must complete Part III of Schedule B if you: Had a foreign account;",
     "Interest, dividends, wages and other income from outside the U.S. go on the return. A foreign account means completing Schedule B, Part III."),
    ("U18", "U.S.", IRS, "Internal Revenue Manual 4.63.3", "https://www.irs.gov/irm/part4/irm_04-063-003r", "excerpt",
     "Form 14653 Certification by U.S. Person Residing Outside of the United States for Streamlined Foreign Offshore Procedures […] Form 14654 Certification by U.S. Person Residing in the United States for Streamlined Domestic Offshore Procedures […] A civil fraud penalty or fraudulent failure to file penalty, under IRC 6663 or IRC 6651(f), respectively, will apply to at least one year of every voluntary disclosure.",
     "The two streamlined certification forms, and the existing voluntary-disclosure rule that a fraud penalty applies to at least one year."),
    ("U19", "U.S.", IRS, "Report of Foreign Bank and Financial Accounts (FBAR)",
     "https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar", "excerpt",
     "the aggregate value of those foreign financial accounts exceeded $10,000 at any time during the calendar year reported. […] The FBAR is an annual report, due April 15 following the calendar year reported. You’re allowed an automatic extension to October 15",
     "An FBAR is required when the foreign accounts together exceeded $10,000 at any time in the year. Due 15 April, automatically extended to 15 October."),
    ("U20", "U.S.", IRS, "Publication 514, Foreign Tax Credit for Individuals (2023 edition)", "https://www.irs.gov/pub/irs-prior/p514--2023.pdf", "excerpt",
     "Amounts paid to a foreign government to satisfy a liability for interest, fines, penalties, or any similar obligation are not taxes and do not qualify for the credit.",
     "Interest, fines and penalties paid to a foreign government are not creditable. The closing words of this sentence also appear in the current edition's text."),
]
SRC = {s[0]: s for s in SOURCES}

# id, value, unit, what it is, source id, token that must appear in that source's quotation
INPUTS = [
    ("surcharge_daily", "0.0005", "share of unpaid tax per day", "Chinese late-payment surcharge", "C01.32", "万分之五"),
    ("fine_min_multiple", "0.5", "times the unpaid tax", "Lowest fine for not filing", "C01.64", "百分之五十"),
    ("fine_max_multiple", "5", "times the unpaid tax", "Highest fine for not filing", "C01.64", "五倍"),
    ("flat_rate", "0.20", "share of taxable income", "Flat rate for interest, dividends, rent, property gains, incidental income", "C04.3", "百分之二十"),
    ("standard_deduction", "60000", "RMB per tax year", "Deduction from a resident's yearly wages and fees", "C04.6", "六万元"),
    ("bracket_1", "36000|3", "RMB upper limit | percent", "Rate Table 1, level 1", "C05", "不超过36000元的 · 3"),
    ("bracket_2", "144000|10", "RMB upper limit | percent", "Rate Table 1, level 2", "C05", "超过36000元至144000元的部分 · 10"),
    ("bracket_3", "300000|20", "RMB upper limit | percent", "Rate Table 1, level 3", "C05", "超过144000元至300000元的部分 · 20"),
    ("bracket_4", "420000|25", "RMB upper limit | percent", "Rate Table 1, level 4", "C05", "超过300000元至420000元的部分 · 25"),
    ("bracket_5", "660000|30", "RMB upper limit | percent", "Rate Table 1, level 5", "C05", "超过420000元至660000元的部分 · 30"),
    ("bracket_6", "960000|35", "RMB upper limit | percent", "Rate Table 1, level 6", "C05", "超过660000元至960000元的部分 · 35"),
    ("bracket_7", "|45", "no upper limit | percent", "Rate Table 1, level 7", "C05", "超过960000元的部分 · 45"),
    ("boc_usd_sell_per_100", "669.1", "RMB per 100 USD", "Bank of China selling rate, used only to turn the dollar ladder into RMB for the wage brackets", "C12", "669.1"),
    ("sfop_penalty_rate", "0", "share of balance", "Streamlined Foreign Offshore penalty", "U02", "will not be subject to failure-to-file and failure-to-pay penalties"),
    ("sdop_penalty_rate", "0.05", "share of highest year-end balance", "Streamlined Domestic Offshore penalty", "U03", "5 percent of the highest aggregate balance/value"),
    ("fbar_nonwillful_cap", "16536", "USD per annual report", "FBAR non-willful ceiling", "U08", "16,536"),
    ("fbar_willful_floor", "165353", "USD per violation", "FBAR willful fixed-dollar ceiling", "U08", "165,353"),
    ("fbar_willful_share", "0.5", "share of balance at the time of the violation", "FBAR willful ceiling as a share of the balance", "U09", "50 percent"),
]
INP = {i[0]: i for i in INPUTS}

AMOUNTS = [D(a) for a in range(10000, 400001, 10000)]
KEY_AMOUNTS = [D(10000), D(50000), D(100000), D(200000), D(400000)]
CENT = D("0.01")


def q2(x: D) -> D:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def brackets():
    out = []
    for n in range(1, 8):
        upper, rate = INP[f"bracket_{n}"][1].split("|")
        out.append((D(upper) if upper else None, D(rate) / 100))
    return out


def comprehensive_tax(taxable: D) -> D:
    """Progressive tax on yearly taxable income, straight from the bracket limits (no quick-deduction numbers)."""
    if taxable <= 0:
        return D(0)
    tax, lower = D(0), D(0)
    for upper, rate in brackets():
        if upper is None or taxable <= upper:
            tax += (taxable - lower) * rate
            break
        tax += (upper - lower) * rate
        lower = upper
    return tax


def ladder_row(a: D) -> dict:
    daily = D(INP["surcharge_daily"][1])
    flat = D(INP["flat_rate"][1])
    fmin, fmax = D(INP["fine_min_multiple"][1]), D(INP["fine_max_multiple"][1])
    rate = D(INP["boc_usd_sell_per_100"][1]) / 100
    ded = D(INP["standard_deduction"][1])
    tax20 = a * flat
    rmb = a * rate
    w1 = comprehensive_tax(rmb - ded)
    w5 = comprehensive_tax(rmb / 5 - ded) * 5
    share = D(INP["fbar_willful_share"][1])
    floor = D(INP["fbar_willful_floor"][1])
    return {
        "amount_usd": a,
        # A. flat 20% categories: currency-neutral, no exchange rate involved
        "cn20_tax_usd": q2(tax20),
        "cn20_tax_plus_surcharge_1y_usd": q2(tax20 * (1 + daily * 365)),
        "cn20_tax_plus_surcharge_3y_usd": q2(tax20 * (1 + daily * 1095)),
        "cn20_tax_plus_surcharge_5y_usd": q2(tax20 * (1 + daily * 1825)),
        "cn20_fine_min_usd": q2(tax20 * fmin),
        "cn20_fine_max_usd": q2(tax20 * fmax),
        # B. wages scenario: needs RMB because the brackets are in RMB
        "rmb_at_boc_sell": q2(rmb),
        "wage_tax_one_year_rmb": q2(w1),
        "wage_tax_one_year_usd": q2(w1 / rate),
        "wage_tax_one_year_pct": q2(w1 / rmb * 100),
        "wage_tax_five_years_rmb": q2(w5),
        "wage_tax_five_years_usd": q2(w5 / rate),
        "wage_tax_five_years_pct": q2(w5 / rmb * 100),
        "wage_surcharge_per_year_on_one_year_tax_usd": q2(w1 / rate * daily * 365),
        # C. U.S. penalty by procedure, amount taken as the highest year-end balance
        "us_streamlined_foreign_usd": q2(a * D(INP["sfop_penalty_rate"][1])),
        "us_streamlined_domestic_usd": q2(a * D(INP["sdop_penalty_rate"][1])),
        "us_fbar_nonwillful_cap_per_report_usd": q2(D(INP["fbar_nonwillful_cap"][1])),
        "us_fbar_willful_cap_per_violation_usd": q2(max(floor, a * share)),
    }


LADDER = [ladder_row(a) for a in AMOUNTS]
LADDER_SOURCES = "C04.3|C01.32|C02.75|C01.64|C04.6|C05|C12|U02|U03|U08|U09"

# ---------------------------------------------------------------------------- content
# Which case: id, case, what the law says, extra beyond the tax (None = blank), flag, how to find out, sources
CASES = [
    ("A", "Whoever paid you already withheld the tax",
     "The payer is the withholding agent. If it withheld and reported, the tax on that payment has been collected.",
     "Nothing.", None,
     "Download your Tax Payment Record (纳税记录). Each withheld payment appears on it.",
     ["C04.9", "C09"]),
    ("B", "The payer should have withheld and did not",
     "The tax is collected from you. You had until 30 June of the year after you were paid, or the date in the tax office's notice. The payer can be fined 50% to 3 times the tax.",
     None, "F02",
     "The payment is missing from your Tax Payment Record but the payer was a Chinese company or person.",
     ["C04.13", "C01.69", "C08"]),
    ("C", "Nobody was obliged to withhold",
     "You had to file and pay within the first 15 days of the month after you were paid.",
     "Surcharge of 0.05% a day from the next day, and a possible fine of 50% to 5 times the tax for not filing.", None,
     "The payment is missing from your record and there was no withholding agent.",
     ["C04.13", "C02.75", "C01.64"]),
    ("D", "The money is not one of the nine taxable kinds of income",
     "The law taxes nine listed kinds of income. Money that is none of them is outside this tax.",
     None, "F01",
     "Compare each deposit with the list. Whether a gift or an inheritance falls outside it is still open on the dashboard (flags U07 and U08 there).",
     ["C04.2", "C10"]),
    ("E", "It is interest the bank paid on the deposit",
     "China has not collected tax on savings-deposit interest since 9 October 2008. The U.S. does tax it: it belongs on Form 1040 each year, and a foreign account means Schedule B, Part III.",
     "No Chinese tax. U.S. tax at your own rate, with no Chinese tax to credit against it.", None,
     "Interest lines on the bank statement, year by year.",
     ["C11", "U17"]),
]

# China stack: id, layer, amount (None = blank), flag, note, sources
CHINA = [
    ("R01", "The tax itself", "20% of interest, dividends, rent, property-sale gains and incidental income. 3% to 45% on wages and fees, worked out per year.", None,
     "For a property sale the tax base is the gain. For rent, 20% is deducted first (RMB 800 if the payment is RMB 4,000 or less).", ["C04.3", "C04.6"]),
    ("R02", "Late-payment surcharge (滞纳金)", "0.05% of the unpaid tax for every day. 365 days comes to 18.25% of the tax.", None,
     "Counted on the tax itself, from the day after the deadline to the day you pay.", ["C01.32", "C02.75"]),
    ("R03", "The deadline the surcharge is counted from", "Nobody obliged to withhold: the 15th of the month after you were paid. Payer failed to withhold: 30 June of the following year, or the date in the tax office's notice.", None,
     "", ["C04.13"]),
    ("R04", "No surcharge when the tax office caused the shortfall", "Tax only, and only three years back.", None,
     "Applies when the office applied the law wrongly or acted unlawfully.", ["C01.52", "C02.80"]),
    ("R05", "Surcharge when your payer failed to withhold", None, "F02",
     "A 2004 reply says no surcharge is charged to either side. The 2018 law then gave the taxpayer a deadline of their own. Which one governs was not found.", ["C08", "C04.13"]),
    ("R06", "Fine for never filing", "50% to 5 times the unpaid tax.", None,
     "Added to the tax and the surcharge.", ["C01.64"]),
    ("R07", "Fine for evasion", "50% to 5 times the unpaid tax, and prosecution if it amounts to a crime.", None,
     "Evasion covers forged or hidden records, a false return, and refusing to file after the tax office told you to.", ["C01.63"]),
    ("R08", "Fine for still not paying after an order", "50% to 5 times the unpaid tax, with enforced collection.", None,
     "", ["C01.68"]),
    ("R09", "Fine on a payer who failed to withhold", "50% to 3 times the tax, charged to the payer.", None,
     "The tax itself is still collected from you.", ["C01.69"]),
    ("R10", "Filing late when no tax is unpaid", "Up to RMB 2,000. RMB 2,000 to 10,000 in serious cases.", None,
     "", ["C01.62"]),
    ("R11", "Which multiple between 0.5 and 5 applies", None, "F04",
     "The law gives the range. The local tax office decides inside it.", ["C01.64"]),
    ("R12", "How far back: calculation mistake", "3 years. 5 years when the shortfall adds up to RMB 100,000 or more.", None,
     "Counted from the day the tax should have been paid. A calculation mistake means an unintended formula error or an obvious slip.", ["C01.52", "C02.81", "C02.82", "C02.83"]),
    ("R13", "How far back: never filed", "Generally 3 years. Up to 5 in special circumstances.", None,
     "The 2009 reply says that not filing is not evasion. It does not define the special circumstances.", ["C03"]),
    ("R14", "How far back: evasion", "No limit.", None,
     "", ["C01.52"]),
    ("R15", "Time limit on fines", "No fine if the violation was not discovered within 5 years.", None,
     "This limits the fine. The tax and surcharge follow the look-back rows above.", ["C01.86"]),
    ("R16", "Whether the surcharge can grow past the tax itself", None, "F03",
     "The collection law sets no ceiling. A separate law caps surcharges at the amount owed. No official text settling which applies to tax was read.", ["C01.32", "C07"]),
    ("R17", "Prison", "Up to 3 years for evading a relatively large amount that is 10% or more of the tax due. 3 to 7 years for a huge amount that is 30% or more.", None,
     "Not pursued if, after the tax office's recovery notice, you pay the tax and the surcharge and have taken the administrative penalty. That protection is lost by anyone convicted of evasion, or fined for it twice or more by the tax authorities, in the previous five years. The amounts that count as large and huge were not read: F10.", ["C06"]),
    ("R18", "Leaving China while tax is owed", "The tax office can ask border control to stop you leaving.", None,
     "Until the tax and surcharge are paid or a guarantee is given.", ["C01.44", "C02.74"]),
    ("R19", "If you disagree with the assessment", "Pay first, or give a guarantee. Then apply for review.", None,
     "", ["C01.88"]),
]

# What comes back: id, item, answer (None = blank), flag, sources
CREDIT = [
    ("K1", "Chinese income tax you pay", "Can be credited against U.S. tax on the same foreign income, up to a limit. Claimed on Form 1116.", None, ["U11"]),
    ("K2", "Chinese surcharge and fines", "Cannot be credited. Interest, fines and penalties paid to a foreign government are not taxes.", None, ["U20", "U11"]),
    ("K3", "Which year the credit belongs to", "The year you pay, for a cash-method taxpayer. Choosing the year the tax accrued is possible only on a timely original return, not an amended one, and then binds every later year.", None, ["U11"]),
    ("K4", "Credit you cannot use in that year", "Carried back 1 year, then forward 10 years.", None, ["U11"]),
    ("K5", "How long you have to claim", "10 years to claim a refund when you paid more foreign tax than you had claimed.", None, ["U11"]),
    ("K6", "Whether your credit lines up with the year the U.S. taxed the income", None, "F11", ["U11"]),
]

# U.S. paths: id, situation, procedure, penalty (None = blank), flag, condition/note, sources
PATHS = [
    ("P1", "The income and the interest were on your returns, and the FBARs were filed", "Nothing to fix.", "$0", None,
     "An FBAR is due for any year the foreign accounts together exceeded $10,000.", ["U17", "U19"]),
    ("P2", "The income was reported and taxed, but FBARs were not filed", "File the late FBARs online and give the reason they are late.", "$0, as long as the IRS has not already contacted you about those years.", None,
     "The IRS's own page for this procedure could not be opened: F06.", ["U04"]),
    ("P3", "The income was reported, but another international form is missing", "File it the normal way. Attach a reasonable-cause statement if you have one.", "Penalties may be assessed under the existing rules.", None,
     "Form 8938 and Form 3520 amounts are on the dashboard Tax page.", ["U05"]),
    ("P4", "Income or interest was not reported, it was not willful, and you live outside the U.S.", "Streamlined Foreign Offshore: 3 years of returns, 6 years of FBARs, Form 14653.", "$0 penalty. The tax and interest are still due.", None,
     "Test: in at least one of the last three years you had no U.S. home and spent 330 full days outside the U.S.", ["U02", "U18", "U01"]),
    ("P5", "Income or interest was not reported, it was not willful, and you live in the U.S.", "Streamlined Domestic Offshore: 3 years of amended returns, 6 years of FBARs, Form 14654.", "5% of the highest year-end total of the unreported foreign accounts, plus the tax and interest.", None,
     "You must have filed a return for each of the last three years.", ["U03", "U18", "U01"]),
    ("P6", "It was willful", "IRS Criminal Investigation Voluntary Disclosure Practice, Form 14457.", None, "F07",
     "Revised terms were put out for comment on 22 December 2025. Final terms were not found.", ["U06", "U18"]),
    ("P7", "You do nothing and the IRS finds it", "No procedure.", "5% of the unpaid tax per month of late filing, up to 25%. 20% of underpaid tax. FBAR: up to $16,536 for each missed annual report, or for a willful case the greater of $165,353 or half the balance.", None,
     "No time limit on the tax if no return was filed. No FBAR penalty where there was reasonable cause and the balance was properly reported.", ["U12", "U13", "U08", "U09", "U10", "U16"]),
]

# Other U.S. rules: id, item, value, note, sources
USRULES = [
    ("V1", "Interest on unpaid U.S. tax", "7% a year in the fourth quarter of 2026. Between 6% and 8% since 2024.", "Runs from the original due date and accrues daily. An extension to file does not move the payment date.", ["U14", "U15"]),
    ("V2", "When the streamlined procedures close", "Once the IRS has opened an examination of any of your years.", "They also need a signed statement that the failure was not willful.", ["U01"]),
    ("V3", "How long the IRS has for the tax", "3 years after a return is filed. 6 years if more than $5,000 of income from reportable foreign assets was left out. No limit if no return was filed.", "", ["U16"]),
    ("V4", "How long the IRS has for an FBAR penalty", "6 years.", "", ["U09"]),
    ("V5", "How the non-willful FBAR penalty is counted", "Once per missed annual report, not once per account.", "", ["U10"]),
]

# Steps: number, action, detail, sources
STEPS = [
    ("1", "Get your Chinese tax record", "Ask for the Tax Payment Record (纳税记录) through the electronic tax bureau, the tax administration's mobile app or a tax service hall. It covers income from 2019 on that was reported, whether or not tax was paid. For earlier years the office issues the older paper certificate (税收完税证明).", ["C09", "C09b"]),
    ("2", "Match the deposits to the record", "Go through the bank statement. A deposit that appears on the record with tax paid is settled: the bank asks for exactly this evidence.", ["C10", "C09"]),
    ("3", "Sort what is left into a case", "For each unmatched deposit decide whether it is one of the nine taxable kinds of income, and whether somebody should have withheld.", ["C04.2", "C04.9", "C04.13"]),
    ("4", "Work out the tax and the surcharge", "Apply the rate for that kind of income. Add 0.05% of the tax for every day since the deadline.", ["C04.3", "C01.32", "C02.75"]),
    ("5", "File and pay before the tax office asks", "File the missing return yourself. Refusing to file after the office has told you to is evasion, which has no time limit; not filing on your own is not evasion.", ["C04.10", "C01.63", "C03"]),
    ("6", "Get the fine decided in writing", "The fine is a range, not a number. Ask the tax office which multiple it applies and get the decision on paper. To dispute it you first pay or give a guarantee.", ["C01.64", "C01.88"]),
    ("7", "Take the updated record to the bank", "With your passport and the documents showing where the money came from. Then follow the route on the dashboard for that kind of money.", ["C10"]),
    ("8", "Check each U.S. year", "For every year: was the income on your Form 1040, was the bank interest on it, and was an FBAR filed when the accounts together passed $10,000?", ["U17", "U19"]),
    ("9", "Pick one U.S. procedure before filing anything", "Use the table above. The streamlined procedures stop being available once the IRS opens an examination.", ["U01", "U07"]),
    ("10", "Claim the credit for the Chinese tax", "On Form 1116, for the income tax only. The surcharge and the fine are not creditable.", ["U11", "U20"]),
]

# Flags: id, severity, item, why, what would settle it, sources
FLAGS = [
    ("F01", "high", "Which case each deposit falls in",
     "The brief does not say where the money came from or whether tax was withheld. Every ladder below is a scale for one assumption, not a figure for this account.",
     "The Tax Payment Record set against the bank statement, deposit by deposit.", ["C09", "C10"]),
    ("F02", "medium", "Surcharge when the payer failed to withhold",
     "A 2004 reply from the tax administration says no surcharge is charged to the taxpayer or the payer. The 2018 law later gave the taxpayer a payment deadline of 30 June of the following year. No official text was found that says which one governs after that date. The 2004 reply was read on the Ministry of Commerce's database, not on the tax administration's own site.",
     "A written answer from the tax office in charge, or the tax administration's own copy of the reply showing its current status.", ["C08", "C04.13"]),
    ("F03", "medium", "Whether the surcharge can exceed the tax",
     "The collection law charges 0.05% a day with no ceiling. The Administrative Compulsion Law says a surcharge may not exceed the amount owed. No official text settling which applies to tax was read. The ladder uses the collection law as written, with no ceiling.",
     "A tax administration ruling or a court decision on this point, read on an official site.", ["C01.32", "C07"]),
    ("F04", "medium", "The size of the fine",
     "The law sets 50% to 5 times the unpaid tax. Where inside that range a case lands is for the local tax office. Local penalty benchmarks were not read. The ladder shows both ends and no middle.",
     "The penalty decision itself, or the benchmark table published by the provincial tax bureau.", ["C01.64", "C01.63"]),
    ("F05", "medium", "Income older than the look-back period",
     "The law limits how far back tax can be recovered. Whether a tax office will still accept payment and issue a record for an older year, and whether a bank accepts money for which no record can be issued, was not found on any official page.",
     "Ask the tax office and the bank in writing.", ["C01.52", "C03", "C10"]),
    ("F06", "low", "The IRS page on late FBARs is gone",
     "The address the National Taxpayer Advocate cites for the Delinquent FBAR Submission Procedures returned 'Page Not Found' on 11 November 2026, and the IRS options page now lists three options without it. The Taxpayer Advocate Service page still states the no-penalty rule, and that is the page cited here.",
     "An IRS statement of where the procedure now lives, or that it was withdrawn.", ["U04", "U07"]),
    ("F07", "medium", "Penalty under the Voluntary Disclosure Practice",
     "The IRS published proposed new terms on 22 December 2025 and took comments until 22 March 2026. The page describes them as proposed. Whether they are final was not found, so no figure is shown for the willful route.",
     "The final IRS announcement, or Form 14457 instructions dated after the comment period.", ["U06", "U18"]),
    ("F08", "low", "U.S. tax and interest are not computed",
     "They depend on the whole return for each year: other income, filing status, the foreign tax credit. Only the rates are given.",
     "A U.S. return prepared for each open year.", ["U14", "U15"]),
    ("F09", "low", "FBAR ceilings carry the January 2025 date",
     "The federal regulation page, stated up to date as of 9 November 2026, still shows the table for penalties assessed on or after 17 January 2025. No 2026 adjustment appears there. The January 2025 figures are used.",
     "A later Federal Register notice, if one exists.", ["U08"]),
    ("F10", "low", "Amounts that make evasion a crime",
     "The Criminal Law says 'relatively large' and 'huge' without figures. The judicial interpretation that sets the figures was not read.",
     "The Supreme People's Court and Supreme People's Procuratorate interpretation, read on an official site.", ["C06"]),
    ("F11", "medium", "Which U.S. year the credit lands in",
     "Chinese tax paid late is credited in the year it is paid unless an accrual choice was already made on a timely original return. If the U.S. taxed the income in an earlier year, the credit and the income may sit in different years, and the carryback is only one year. Whether that leaves tax paid twice depends on the return.",
     "A U.S. preparer, with the year of each Chinese payment and each U.S. return.", ["U11"]),
    ("F12", "low", "Repository review: the dashboard stops at 'the large number'",
     "The dashboard's Tax page says unpaid Chinese tax 'is the large number' and the decision register marks 'What happens if the money was never taxed?' as answered with nothing missing. Neither mentions the daily surcharge, the fine range or the look-back periods.",
     "A link from those two places to this page.", ["C01.32", "C01.64", "C01.52"]),
    ("F13", "low", "Repository review: 'interest is exempt' is only the Chinese half",
     "The dashboard's Tax page lists bank-deposit interest as exempt. That is the Chinese rule. Its U.S. rows do not say the same interest is taxable in the U.S., which decides whether the no-penalty FBAR route is open.",
     "One sentence on the dashboard's U.S. rows.", ["C11", "U17"]),
]
_EXCERPTS = [s[0] for s in SOURCES if s[5] == "excerpt"]
FLAGS.append(
    ("F14", "low", f"{len(_EXCERPTS)} passages were read as excerpts",
     "For " + ", ".join(_EXCERPTS[:-1]) + " and " + _EXCERPTS[-1] + " the quoted passage is the official page's own text as returned by a search of that address. The page was not opened in full, so the surrounding text was not reviewed.",
     "Open each link in the source list and read around the quoted passage.", _EXCERPTS))

SEVERITY_PILL = {"high": "bad", "medium": "warn", "low": ""}


# ------------------------------------------------------------------------------ CSVs
def csv_text(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def urls(ids):
    seen = []
    for i in ids:
        u = SRC[i][4]
        if u not in seen:
            seen.append(u)
    return " ".join(seen)


def build_csvs():
    out = {}
    out["data/6da0_sources.csv"] = csv_text(
        ["id", "side", "issuer", "document", "url", "read_on", "read", "quote", "plain_english_ours"],
        [(s[0], s[1], s[2], s[3], s[4], READ_ON, s[5], s[6], s[7]) for s in SOURCES])
    out["data/6da0_inputs.csv"] = csv_text(
        ["id", "value", "unit", "what", "source_id", "token_in_quote", "source_url"],
        [i + (SRC[i[4]][4],) for i in INPUTS])
    rules = []
    for cid, case, law, extra, flag, how, src in CASES:
        rules.append((f"CASE-{cid}", "Which case", case, extra or "", flag or "", f"{law} How to tell: {how}", "|".join(src), urls(src)))
    for rid, layer, amount, flag, note, src in CHINA:
        rules.append((rid, "China", layer, amount or "", flag or "", note, "|".join(src), urls(src)))
    for kid, item, answer, flag, src in CREDIT:
        rules.append((kid, "What comes back", item, answer or "", flag or "", "", "|".join(src), urls(src)))
    for pid, sit, proc, pen, flag, note, src in PATHS:
        rules.append((pid, "U.S. procedure", sit, pen or "", flag or "", f"{proc} {note}".strip(), "|".join(src), urls(src)))
    for vid, item, value, note, src in USRULES:
        rules.append((vid, "U.S.", item, value, "", note, "|".join(src), urls(src)))
    out["data/6da0_rules.csv"] = csv_text(
        ["id", "group", "item", "value", "flag_if_blank", "note", "source_ids", "source_urls"], rules)
    cols = list(LADDER[0].keys())
    lsrc = LADDER_SOURCES.split("|")
    out["data/6da0_ladder.csv"] = csv_text(
        cols + ["source_ids", "source_urls"],
        [[str(r[c]) if c != "amount_usd" else str(int(r[c])) for c in cols] + [LADDER_SOURCES, urls(lsrc)] for r in LADDER])
    out["data/6da0_steps.csv"] = csv_text(
        ["step", "action", "detail", "source_ids", "source_urls"],
        [(n, a, d, "|".join(src), urls(src)) for n, a, d, src in STEPS])
    out["data/6da0_flags.csv"] = csv_text(
        ["id", "severity", "item", "why", "what_would_settle_it", "source_ids", "source_urls"],
        [(f, sev, item, why, settle, "|".join(src), urls(src)) for f, sev, item, why, settle, src in FLAGS])
    return out


# ------------------------------------------------------------------------------ HTML
def esc(s):
    return html.escape(str(s), quote=True)


def usd(x, cents=False):
    x = D(x)
    if cents:
        return f"${x:,.2f}"
    return f"${x.quantize(D('1'), rounding=ROUND_HALF_UP):,}"


def rmb(x):
    return f"¥{D(x).quantize(D('1'), rounding=ROUND_HALF_UP):,}"


def pct(x):
    return f"{D(x):.2f}%"


def src_links(ids, title=True):
    """Links to the official pages. Ladder rows drop the title attribute: 120 rows of it double the page weight."""
    if not title:
        return " ".join(f'<a href="{esc(SRC[i][4])}" rel="noopener">{i}</a>' for i in ids)
    return " ".join(f'<a href="{esc(SRC[i][4])}" rel="noopener" title="{esc(SRC[i][3])}">{i}</a>' for i in ids)


def blank(flag):
    return f'<span class="blank">not verified</span> <a href="#{flag}">{flag}</a>'


def table(head, rows, cls="stack"):
    """rows: (row id or None, [cell html]). The last column is always the source column."""
    out = [f'<div class="tbl"><table class="{cls}" data-kind="data">', "<thead><tr>"]
    src_cls = ' class="src"'
    out.append("".join(f'<th{src_cls if i == len(head) - 1 else ""}>{esc(h)}</th>' for i, h in enumerate(head)))
    out.append("</tr></thead><tbody>")
    for rid, cells in rows:
        tds = []
        for i, c in enumerate(cells):
            klass = ' class="src"' if i == len(cells) - 1 else ""
            label = "" if "num" in cls else f' data-label="{esc(head[i])}"'
            tds.append(f"<td{klass}{label}>{c}</td>")
        rid_attr = f' id="{rid}"' if rid else ""
        out.append(f"<tr{rid_attr}>" + "".join(tds) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def ladder_tables(amounts):
    by = {r["amount_usd"]: r for r in LADDER}
    a_rows, b_rows, c_rows = [], [], []
    for a in amounts:
        r = by[a]
        a_rows.append((None, [usd(a), usd(r["cn20_tax_usd"]), usd(r["cn20_tax_plus_surcharge_1y_usd"]),
                              usd(r["cn20_tax_plus_surcharge_3y_usd"]), usd(r["cn20_tax_plus_surcharge_5y_usd"]),
                              f'{usd(r["cn20_fine_min_usd"])} to {usd(r["cn20_fine_max_usd"])}',
                              src_links(["C04.3", "C01.32", "C01.64"], False)]))
        b_rows.append((None, [usd(a), rmb(r["rmb_at_boc_sell"]),
                              f'{usd(r["wage_tax_one_year_usd"])} ({pct(r["wage_tax_one_year_pct"])})',
                              f'{usd(r["wage_tax_five_years_usd"])} ({pct(r["wage_tax_five_years_pct"])})',
                              usd(r["wage_surcharge_per_year_on_one_year_tax_usd"]),
                              src_links(["C05", "C04.6", "C12", "C01.32"], False)]))
        c_rows.append((None, [usd(a), usd(r["us_streamlined_foreign_usd"]), usd(r["us_streamlined_domestic_usd"]),
                              usd(r["us_fbar_nonwillful_cap_per_report_usd"]), usd(r["us_fbar_willful_cap_per_violation_usd"]),
                              src_links(["U02", "U03", "U08", "U09"], False)]))
    ta = table(["Untaxed income", "Tax at 20%", "Tax + surcharge, paid 1 year late", "Paid 3 years late", "Paid 5 years late", "Fine, if one is imposed", "Source"], a_rows, "num")
    tb = table(["Wages", "In RMB", "Tax if earned in one year", "Tax if earned over five years", "Surcharge per year late, one-year case", "Source"], b_rows, "num")
    tc = table(["Highest year-end balance", "Streamlined, living abroad", "Streamlined, living in the U.S.", "Outside a procedure: non-willful ceiling per missed report", "Outside a procedure: willful ceiling per violation", "Source"], c_rows, "num")
    return ta, tb, tc


def build_page():
    by = {r["amount_usd"]: r for r in LADDER}
    r100, r400 = by[D(100000)], by[D(400000)]
    key_a, key_b, key_c = ladder_tables(KEY_AMOUNTS)
    all_a, all_b, all_c = ladder_tables(AMOUNTS)
    boc = D(INP["boc_usd_sell_per_100"][1]) / 100

    case_rows = [(f"CASE-{cid}", [f'<span class="id">{cid}</span>{esc(case)}', esc(law),
                                  esc(extra) if extra else blank(flag), esc(how), src_links(src)])
                 for cid, case, law, extra, flag, how, src in CASES]
    china_rows = [(rid, [f'<span class="id">{rid}</span>{esc(layer)}', f"<b>{esc(amount)}</b>" if amount else blank(flag),
                         esc(note), src_links(src)]) for rid, layer, amount, flag, note, src in CHINA]
    credit_rows = [(kid, [f'<span class="id">{kid}</span>{esc(item)}', esc(answer) if answer else blank(flag), src_links(src)])
                   for kid, item, answer, flag, src in CREDIT]
    path_rows = [(pid, [f'<span class="id">{pid}</span>{esc(sit)}', esc(proc), f"<b>{esc(pen)}</b>" if pen else blank(flag),
                        esc(note), src_links(src)]) for pid, sit, proc, pen, flag, note, src in PATHS]
    usrule_rows = [(vid, [f'<span class="id">{vid}</span>{esc(item)}', f"<b>{esc(value)}</b>", esc(note), src_links(src)])
                   for vid, item, value, note, src in USRULES]
    step_rows = [(f"STEP-{n}", [f'<span class="id">{n}</span>{esc(a)}', esc(d), src_links(src)]) for n, a, d, src in STEPS]
    flag_rows = [(f, [f'<span class="id">{f}</span>{esc(item)}', f'<span class="pill {SEVERITY_PILL[sev]}">{sev}</span>',
                      esc(why), esc(settle), src_links(src)]) for f, sev, item, why, settle, src in FLAGS]
    source_rows = [(f"SRC-{s[0]}", [f'<span class="id">{s[0]}</span><a href="{esc(s[4])}" rel="noopener">{esc(s[3])}</a>',
                                    esc(s[2]), f'<span class="quote" lang="{"zh" if s[1] == "China" and s[0] != "C12" else "en"}">{esc(s[6])}</span>',
                                    esc(s[7]), "Page read" if s[5] == "full" else f'Excerpt <a href="#F14">F14</a>',
                                    f'<a href="{esc(s[4])}" rel="noopener">open</a>']) for s in SOURCES]
    input_rows = [(None, [esc(i[3]), f'<b>{esc(i[1])}</b> <span class="note">{esc(i[2])}</span>',
                          f'<span class="quote">{esc(i[5])}</span>', src_links([i[4]])]) for i in INPUTS]

    n_full = sum(1 for s in SOURCES if s[5] == "full")
    body = f"""<p class="crumb"><a href="dashboard/tax.html">Tax</a> / Unpaid tax</p>
<h1>If tax on the money was never paid: what settling up costs</h1>
<p class="lead">For a U.S. citizen with RMB in a Chinese bank account. The dashboard says unpaid Chinese tax is "the large number". This page takes that number apart, layer by layer, on both sides, from the laws themselves as read on 11 November 2026.</p>
<div class="banner">This is a scale, not your figure. The brief does not say where the money came from or whether tax was withheld, so nothing here is a finding about this account. See <a href="#F01">F01</a>.</div>

<nav class="jump" aria-label="On this page"><a href="#case">Which case</a><a href="#china">China</a><a href="#ladder-cn">China ladder</a><a href="#back">What comes back</a><a href="#us">U.S.</a><a href="#ladder-us">U.S. ladder</a><a href="#steps">Steps</a><a href="#flagged">Flagged</a><a href="#sources">Sources</a></nav>

<div class="grid">
<div class="card"><h3>1. The tax is only the first layer</h3>
<p>Chinese tax that is paid late grows by 0.05% a day, which is 18.25% of the tax per year. A fine of half the tax to five times the tax can be added. On $100,000 of income taxed at 20% that is {usd(r100["cn20_tax_usd"])} of tax, {usd(r100["cn20_tax_plus_surcharge_3y_usd"])} if paid three years late, and a possible fine of {usd(r100["cn20_fine_min_usd"])} to {usd(r100["cn20_fine_max_usd"])}.</p>
<p class="src">{src_links(["C01.32", "C01.64", "C04.3"])} · <a href="#ladder-cn">Ladder</a></p></div>
<div class="card"><h3>2. Why it was unpaid decides how far back</h3>
<p>The tax office's own mistake: three years, no surcharge. Never filed: generally three years, up to five. Evasion: no limit. Not having filed is not evasion; refusing to file after the tax office tells you to is.</p>
<p class="src">{src_links(["C01.52", "C03", "C01.63"])} · <a href="#china">China rules</a></p></div>
<div class="card"><h3>3. Only the tax itself comes back</h3>
<p>Chinese income tax can be credited against U.S. tax on the same income. The surcharge and the fine cannot. The credit belongs to the year you pay, which may not be the year the U.S. taxed the income.</p>
<p class="src">{src_links(["U11", "U20"])} · <a href="#back">What comes back</a></p></div>
<div class="card"><h3>4. In the U.S. the procedure matters more than the tax</h3>
<p>If the income and the accounts were reported, there is nothing to settle. If not, and it was not willful, the penalty is nothing for someone living abroad and 5% of the highest balance for someone living in the U.S. Outside those procedures the ceiling is $16,536 for each missed yearly report, or for a willful case the greater of $165,353 or half the balance.</p>
<p class="src">{src_links(["U02", "U03", "U08", "U09"])} · <a href="#us">U.S. procedures</a></p></div>
</div>

<div class="kpis">
<div class="kpi"><b>18.25%</b><span>of the unpaid Chinese tax, added per year late</span><span class="src">{src_links(["C01.32"])}</span></div>
<div class="kpi"><b>0.5× to 5×</b><span>the unpaid tax: fine range for not filing</span><span class="src">{src_links(["C01.64"])}</span></div>
<div class="kpi"><b>3, 5 or no limit</b><span>years China can look back, by cause</span><span class="src">{src_links(["C01.52", "C03"])}</span></div>
<div class="kpi"><b>0% or 5%</b><span>U.S. streamlined penalty: abroad or at home</span><span class="src">{src_links(["U02", "U03"])}</span></div>
</div>

<h2 id="case">First find out which case you are in</h2>
<p>Everything below depends on this. The Tax Payment Record from the Chinese tax administration answers most of it.</p>
{table(["Case", "What the law says", "What you owe beyond the tax", "How to tell", "Source"], case_rows)}

<h2 id="china">China: the layers on top of the tax</h2>
{table(["Layer", "Amount", "Detail", "Source"], china_rows)}

<h2 id="ladder-cn">China ladder, $10,000 to $400,000</h2>
<h3>A. If the whole amount is untaxed income in a 20% category</h3>
<p>Interest, dividends and incidental income are taxed at 20% of the full amount. For rent and property sales the taxable part is smaller, so the figures would be lower. The surcharge is 0.05% of the tax per day for 365, 1,095 and 1,825 days. The fine is shown at both ends of the legal range because where it lands is not known: <a href="#F04">F04</a>. Percentages are the same in either currency, so no exchange rate is used.</p>
{key_a}
<details><summary>All 40 steps <span>$10,000 to $400,000 in $10,000 steps</span></summary>
{all_a}
</details>
<h3>B. If the whole amount is untaxed wages of a resident</h3>
<p>Wages are taxed on a yearly scale of 3% to 45% after a RMB 60,000 deduction. The same total is taxed far less when it was earned over several years, so both are shown: all in one tax year, and spread evenly over five. Only the RMB 60,000 deduction is applied. The dollar amount is turned into RMB at Bank of China's selling rate of {boc:.4f} published {esc(SRC["C12"][3].split("published ")[1])}, because the scale is in RMB.</p>
{key_b}
<details><summary>All 40 steps <span>$10,000 to $400,000 in $10,000 steps</span></summary>
{all_b}
</details>
<p class="note">Example: $400,000 is {rmb(r400["rmb_at_boc_sell"])}. Earned in one year the tax is {rmb(r400["wage_tax_one_year_rmb"])}, or {usd(r400["wage_tax_one_year_usd"])}. Earned over five years it is {rmb(r400["wage_tax_five_years_rmb"])}, or {usd(r400["wage_tax_five_years_usd"])}. Wages paid by a Chinese employer normally had tax withheld (case A), in which case none of this is owed.</p>

<h2 id="back">What comes back on the U.S. side</h2>
{table(["Item", "Answer", "Source"], credit_rows)}

<h2 id="us">U.S.: which procedure fits</h2>
<p>The U.S. taxes its citizens on income from anywhere, including interest on a Chinese deposit. What it costs to fix an omission depends almost entirely on which of these rows describes you.</p>
{table(["Your situation", "Procedure", "Penalty", "Condition", "Source"], path_rows)}
{table(["Rule", "What it is", "Detail", "Source"], usrule_rows)}

<h2 id="ladder-us">U.S. ladder, $10,000 to $400,000</h2>
<p>The amount is taken as the highest year-end total of the unreported accounts, and as the balance on the day a report was missed. The streamlined columns are what you pay. The last two columns are legal ceilings, not expected amounts. An FBAR is only required when the accounts together exceeded $10,000, so the $10,000 row sits on the threshold.</p>
{key_c}
<details><summary>All 40 steps <span>$10,000 to $400,000 in $10,000 steps</span></summary>
{all_c}
</details>
<p class="note">U.S. tax and interest are not in this table because they depend on the whole return: <a href="#F08">F08</a>. The willful route has no figure: <a href="#F07">F07</a>.</p>

<h2 id="steps">Step by step</h2>
{table(["Step", "What to do", "Source"], step_rows)}
<p>After that, the conversion and the wire follow the route for that kind of money on the <a href="dashboard/steps.html">Steps page</a>, and the currency gain on the conversion is on the <a href="dashboard/tax.html">Tax page</a>.</p>

<h2 id="flagged">Flagged for review</h2>
<p>{len(FLAGS)} items that are open, unverified or irregular. None of them is filled in with a guess anywhere on this page.</p>
{table(["Item", "Severity", "Why it is open", "What would settle it", "Source"], flag_rows)}

<h2 id="sources">Sources</h2>
<p>{len(SOURCES)} passages from {len({s[4] for s in SOURCES})} official pages, all read on 11 November 2026. {n_full} were read on the page itself; {len(SOURCES) - n_full} are the page's own text returned by a search of that address. The Chinese text is quoted as published; the English line is our rendering.</p>
<details><summary>Every passage, with its quotation <span>{len(SOURCES)} rows</span></summary>
{table(["Passage", "Published by", "Quotation", "What it says", "How it was read", "Link"], source_rows)}
</details>
<details><summary>Every number used in the ladders <span>{len(INPUTS)} inputs, each tied to a quotation</span></summary>
{table(["Input", "Value", "Words it was read from", "Source"], input_rows)}
</details>

<h2 id="method">How this was worked out</h2>
<ul class="plain">
<li>Tax at 20% is the amount times 0.20. The surcharge is that tax times 0.0005 times the number of days. Fines are the tax times 0.5 and times 5.</li>
<li>Wage tax is worked out from the seven levels of the yearly rate table, on the RMB amount minus RMB 60,000. The five-year case does the same on one fifth of the amount and multiplies by five.</li>
<li>The streamlined domestic penalty is the amount times 0.05. The willful ceiling is the larger of $165,353 and half the amount.</li>
<li>Every cell is recomputed by a second program that does not share code with the one that built this page, and each input must appear word for word in the quotation it is tied to. See <code>scripts/verify_6da0.py</code>.</li>
<li>Data: <a href="data/6da0_ladder.csv">ladder</a>, <a href="data/6da0_rules.csv">rules</a>, <a href="data/6da0_sources.csv">sources</a>, <a href="data/6da0_inputs.csv">inputs</a>, <a href="data/6da0_steps.csv">steps</a>, <a href="data/6da0_flags.csv">flags</a>.</li>
</ul>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="6da0-settle-up">
<meta name="description" content="What unpaid Chinese tax really costs a U.S. citizen: surcharge, fines, look-back periods, what the U.S. credits back, and the U.S. penalty by procedure, from $10,000 to $400,000.">
<title>Unpaid tax: what settling up costs · China money</title>
<link rel="stylesheet" href="dashboard/site.css">
<link rel="stylesheet" href="assets/6da0.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">China money<small>RMB to USD, source-checked</small></a>
<nav class="nav" aria-label="Sections"><a href="index.html">Home</a><a href="dashboard/methods.html">Methods</a><a href="dashboard/costs.html">Costs</a><a href="dashboard/steps.html">Steps</a><a href="dashboard/tax.html">Tax</a><a href="{PAGE}" aria-current="page">Unpaid tax</a><a href="dashboard/flagged.html">Flagged</a><a href="dashboard/sources.html">Sources</a><a href="dashboard/archive.html">Archive</a></nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>Laws and official pages read on {READ_ON}. Exchange rate: Bank of China board published 2026/11/11 11:00:03, used only for the wage table.</p>
<p>General research from public official pages. It is not legal, tax or banking advice and makes no finding about any person's case.</p>
<p><a href="index.html">Dashboard</a> · <a href="dashboard/flagged.html">Dashboard open items</a> · <a href="{REPO}">Repository</a> · built by <code>scripts/build_6da0.py</code>, checked by <code>scripts/verify_6da0.py</code></p>
</div></footer>
</body>
</html>
"""


CSS = """/* 6da0 additions to dashboard/site.css. No JavaScript, no external assets. */
.crumb{font-size:.86rem;color:var(--muted);margin:0 0 .2em}
.crumb a{color:var(--muted)}
.jump{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0 18px}
.jump a{font-size:.86rem;padding:4px 10px;border:1px solid var(--line);border-radius:999px;background:var(--surface);text-decoration:none;color:var(--ink)}
.jump a:hover{border-color:var(--accent);color:var(--accent)}
.quote{display:block;font-size:.86rem;color:var(--muted);overflow-wrap:anywhere}
.quote[lang=zh]{line-height:1.7}
h2[id],h3[id]{scroll-margin-top:96px}
tr[id]{scroll-margin-top:110px}
table.num thead th{white-space:normal;min-width:6.5rem;vertical-align:bottom}
table.num thead th:first-child{min-width:5.5rem}
"""


def build_note():
    by = {r["amount_usd"]: r for r in LADDER}
    lines = [
        "# Settling up unpaid tax: research note (session `arena/6da06d4e-china3`, namespace `6da0`)",
        "",
        "Generated by `scripts/build_6da0.py`. Do not edit by hand; edit the script and rebuild.",
        f"Sources read on {READ_ON}. Published page: [`6da0-settle-up.html`](../6da0-settle-up.html).",
        "",
        "## Why this exists",
        "",
        "The dashboard's answer to the brief's \"considerable amount of taxes\" ends at one sentence: unpaid Chinese",
        "tax \"is the large number\". A search of the repository on 11 November 2026 found no mention of the late-payment",
        "surcharge (滞纳金), the Tax Collection and Administration Law, the look-back periods, the fine range for",
        "non-filing, or the U.S. rule that surcharges and fines are not creditable. This note fills that gap and nothing else.",
        "",
        "## Findings",
        "",
        "1. Chinese tax paid late carries 0.05% of the tax per day (18.25% per 365 days) from the day after the deadline",
        "   to the day of payment (C01.32, C02.75).",
        "2. Not filing carries a fine of 50% to five times the unpaid tax (C01.64). The same range applies to evasion (C01.63).",
        "3. How far back the tax office can go depends on the cause: three years with no surcharge if the office caused it;",
        "   three years, or five for RMB 100,000 or more, for a calculation mistake; generally three and up to five for",
        "   never filing; no limit for evasion (C01.52, C02.82, C03). Fines lapse if the violation is not discovered within",
        "   five years (C01.86).",
        "4. Refusing to file after the tax office's notice is inside the definition of evasion; not filing on one's own is",
        "   not (C01.63, C03). That is the legal reason to file before being asked.",
        "5. A person who owes tax can be stopped from leaving China until it is settled or guaranteed (C01.44, C02.74).",
        "6. On the U.S. side only the Chinese income tax is creditable; interest, fines and penalties are not (U20). A",
        "   cash-method taxpayer takes the credit in the year of payment, and the accrual choice cannot be made on an",
        "   amended return (U11).",
        "7. The U.S. cost of an unreported account is set by the procedure: no penalty under the Streamlined Foreign Offshore",
        "   Procedures, 5% of the highest year-end balance under the Streamlined Domestic Offshore Procedures (U02, U03),",
        "   against ceilings of $16,536 per missed report (non-willful) or the greater of $165,353 or half the balance",
        "   (willful) outside them (U08, U09, U10).",
        "8. Interest on the Chinese deposit is exempt in China (C11) and taxable in the U.S. (U17). Unreported interest is",
        "   what moves a person from the no-penalty late-FBAR route (U04) into the streamlined procedures.",
        "",
        "## Ladder, key amounts",
        "",
        "| Amount | Tax at 20% | + surcharge, 3 years | Fine range | Wage tax, one year | Wage tax, five years | Streamlined domestic 5% | Willful FBAR ceiling |",
        "|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for a in KEY_AMOUNTS:
        r = by[a]
        lines.append(
            f"| {usd(a)} | {usd(r['cn20_tax_usd'])} | {usd(r['cn20_tax_plus_surcharge_3y_usd'])} | "
            f"{usd(r['cn20_fine_min_usd'])} to {usd(r['cn20_fine_max_usd'])} | {usd(r['wage_tax_one_year_usd'])} | "
            f"{usd(r['wage_tax_five_years_usd'])} | {usd(r['us_streamlined_domestic_usd'])} | "
            f"{usd(r['us_fbar_willful_cap_per_violation_usd'])} |")
    lines += [
        "",
        "All 40 rows: [`data/6da0_ladder.csv`](../data/6da0_ladder.csv). Assumptions are stated on the page above each table.",
        "",
        "## Flagged for review",
        "",
        "| ID | Severity | Item | Source |",
        "|---|---|---|---|",
    ]
    for f, sev, item, why, settle, src in FLAGS:
        lines.append(f"| {f} | {sev} | {item}. {why} | " + " ".join(f"[{i}]({SRC[i][4]})" for i in src) + " |")
    lines += [
        "",
        "## Sources",
        "",
        "| ID | Document | How read | Link |",
        "|---|---|---|---|",
    ]
    for s in SOURCES:
        lines.append(f"| {s[0]} | {s[3]} ({s[2]}) | {'page read' if s[5] == 'full' else 'excerpt'} | {s[4]} |")
    lines += [
        "",
        "## Verification performed",
        "",
        "- Every source address was fetched or searched on 11 November 2026 and the quoted passage copied from the result.",
        "- `scripts/verify_6da0.py` checks that every input token appears in its source quotation, recomputes all 40 ladder",
        "  rows with separate code, checks every table row on the page for an official link or a flagged blank, and checks",
        "  every internal link and anchor.",
        "- Not done: no page was read in a browser; pages marked 'excerpt' were not opened in full (flag F14); no Chinese",
        "  court decision or local penalty benchmark was read (flags F03, F04, F10).",
        "",
    ]
    return "\n".join(lines)


def outputs():
    out = build_csvs()
    out[PAGE] = build_page()
    out["assets/6da0.css"] = CSS
    out["research/6da0-settle-up.md"] = build_note()
    return out


def main(argv):
    out = outputs()
    if "--check" in argv:
        stale = [p for p, text in out.items()
                 if not (ROOT / p).exists() or (ROOT / p).read_text(encoding="utf-8") != text]
        if stale:
            print("STALE — run python3 scripts/build_6da0.py and commit: " + ", ".join(stale))
            return 1
        print(f"OK — {len(out)} generated 6da0 files match a fresh build.")
        return 0
    for p, text in out.items():
        path = ROOT / p
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"wrote {len(out)} files: " + ", ".join(sorted(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
