# n676 — verification log, 2026-11-11

Session `session-n676d2a67` (`arena/676d2a67-china3`), branched from `d9763dca` (PR #49 merged).

Every page opened below was fetched on **2026-11-11** and the quoted text is copied from the page
as it read that day. Nothing in this log is carried forward from an earlier session's CSV. Where a
page was *not* re-opened, that is stated explicitly and no claim rests on it.

Machine-readable version: `data/n676_sources.csv` (22 rows, 19 re-read today).

---

## 1. The two inputs every cost figure on the site is built from

### N01 — Bank of China exchange-rate board

<https://www.boc.cn/sourcedb/whpj/enindex_1619.html> · HTTP 200 · fetched 2026-11-11

USD row, verbatim:

```
USD | 666.3 | 666.3 | 669.11 | 669.11 | 671.91 | 2026-11-11 10:25:02
```

Buying 6.6630, selling 6.6911 RMB per USD. Column order is *Buying Rate | Cash Buying Rate |
Selling Rate | Cash Selling Rate | Middle Rate | Pub Time*.

**Irregularity recorded (N676-F03).** The board's "Middle Rate" of 6.7191 is **not** the mid-point
of its own buying and selling rates: (6.6630 + 6.6911) ÷ 2 = 6.67705. The n676 pages compute their
own mid-point, say so on the page, and record the board's column separately so a reader can
reconcile the two.

### N02 — Bank of China personal e-banking transfer tariff

<https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html> · HTTP 200 · fetched 2026-11-11

Verbatim, cross-border wire line:

> 跨境汇款（电汇）　每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。

1 per mille of the amount, floor RMB 50, ceiling RMB 260, plus a telegraph charge of RMB 150
outside Hong Kong / Macau / Taiwan and RMB 80 inside it. The schedule is titled
《中国银行电子银行个人服务转账汇款费率表》 — a **personal** tariff, effective 2014-11-01.

Verbatim, domestic foreign-currency transfer line (N02b):

> 中行内跨省、省内异地外币转账　每笔转账金额的1‰，最高200元/笔。

A different and cheaper line: 1 per mille capped at RMB 200 for moving foreign currency between
your own BOC accounts inside China.

---

## 2. Which route applies — the SAFE rules

### N03 — SAFE Tianjin, 2024-06-21

<https://www.safe.gov.cn/tianjin/2024/0621/2529.html> · HTTP 200 · fetched 2026-11-11

> 境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇。持有外国人永久居留身份证的境外个人适用购汇年度便利化额度。

A **境外个人** — a foreign individual, which is what a U.S. citizen is — buys dollars on valid ID
**plus** source-of-funds documents showing the transaction amount, **including tax certificates**,
under art. 59 of 汇发〔2020〕14号. The annual convenience amount applies **only** to holders of a
外国人永久居留身份证.

### N04 — SAFE Ningxia, 2022-09-29

<https://www.safe.gov.cn/ningxia/2022/0929/1997.html> · HTTP 200 · fetched 2026-11-11

> 目前，我国对于真实、合法的经常项目和已开放的资本项目下购汇和结汇都没有金额限制。
>
> 年度便利化额度不是个人每年购汇或者结汇的限额，只是超过等值5万美元的购汇或结汇不能仅凭本人有效身份证件办理。

Two things this settles. There is **no amount limit** on genuine, lawful current-account and opened
capital-account purchases. And the USD 50,000 figure is **not a cap** — above it you simply cannot
proceed on ID alone. The answer cites arts. 54, 55, 56 and 57 of the 2020 guidelines, all of which
read 境内个人, i.e. they are the *domestic individual* articles, not art. 59.

### N05 — SAFE Tianjin, 2026-07-13

<https://www.safe.gov.cn/tianjin/2026/0713/3088.html> · HTTP 200 · fetched 2026-11-11

> 根据《国家外汇管理局关于印发〈经常项目外汇业务指引（2020年版）〉的通知》（汇发〔2020〕14号）第五十九条规定，"境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇"。

Confirms art. 59 is still the operative rule in **2026**. The question it answers is expressly
境外个人在境内工作期间取得的劳动报酬如何购汇汇出 — labour remuneration earned while working in China.

### N06 — State Council Decree 532, the FX Regulations

<https://www.safe.gov.cn/safe/2008/0806/5321.html> · HTTP 200 · fetched 2026-11-11 · 国务院令第532号

Five articles that decide most of the answer, verbatim:

> 第五条　国家对经常性国际支付和转移不予限制。

> 第三十九条　有违反规定将境内外汇转移境外，或者以欺骗手段将境内资本转移境外等逃汇行为的，由外汇管理机关责令限期调回外汇，处逃汇金额30%以下的罚款；情节严重的，处逃汇金额30%以上等值以下的罚款；构成犯罪的，依法追究刑事责任。

> 第四十五条　私自买卖外汇、变相买卖外汇、倒买倒卖外汇或者非法介绍买卖外汇数额较大的，由外汇管理机关给予警告，没收违法所得，处违法金额30%以下的罚款；情节严重的，处违法金额30%以上等值以下的罚款；构成犯罪的，依法追究刑事责任。

> 第四十八条　…对机构可以处30万元以下的罚款，对个人可以处5万元以下的罚款：…（三）未按照规定提交有效单证或者提交的单证不真实的；

> 第五十二条　…（二）境内个人，是指中国公民和在中华人民共和国境内连续居住满1年的外国人，外国驻华外交人员和国际组织驻华代表除外。

Art. 5 is why the conversion itself is not restricted. Arts. 39, 40 and 45 are the penalty scale
for the prohibited routes: up to 30% of the amount, 30-100% in serious cases, criminal liability
possible. Art. 48 is the RMB 50,000 individual fine for missing or false documents.

**Art. 52(2) is the definition conflict** (question Q03). This regulation counts a foreigner
continuously resident in China for a full year as a **境内个人**; the current-account guidelines
route a **境外个人** through art. 59 instead. Which one the bank recorded when it opened the
account decides whether arts. 54-57 or art. 59 apply, and it is not visible from outside.

### N06b — same regulation, arts. 15 and 42

> 第十五条　携带、申报外币现钞出入境的限额，由国务院外汇管理部门规定。
>
> 第四十二条　违反规定携带外汇出入境的，由外汇管理机关给予警告，可以处违法金额20%以下的罚款。

The cash-carrying limit is **delegated** to SAFE and is not stated in the regulation itself. It was
not re-read this pass, so the limit is left blank (N676-U06). Breaching it draws a warning and up
to 20%.

---

## 3. Emigrant and inheritance transfers — and the 2014 change

### N07 — PBOC Announcement [2004] No. 16

<http://m.safe.gov.cn/safe/2004/1116/5461.html> · HTTP 200 · fetched 2026-11-11

> 第二条　本办法所称个人财产对外转移包括移民财产转移…和继承财产转移…
>
> 第五条　申请人办理移民转移需向移民原户籍所在地外汇管理分局、外汇管理部…申请；申请人办理继承转移需向被继承人生前户籍所在地外汇局申请。
>
> 第十一条　外汇指定银行办理售汇后，应直接将外汇汇往移民或继承人居住国或地区申请人本人的账户，不得在境内提取外币现钞。
>
> 第十二条　…法律规定不得对外转移的财产、不能证明合法来源财产等的对外转移申请，外汇局不予受理。

Two named routes exist, each with its own SAFE branch. The bank must remit **directly to the
applicant's own account abroad** — no cash withdrawal in China. Property whose lawful source cannot
be proven **will not be accepted at all**, which is the answer to "what if I cannot document it"
(N676-U08).

### N07b — same announcement, arts. 6 and 10 as originally enacted

> 第六条　移民转移必须一次性申请拟转移出境的全部财产金额，分步汇出。首次可汇出金额不得超过全部申请转移财产的一半；自首次汇出满一年后，可汇出不超过剩余财产的一半；自首次汇出满两年后，可汇出全部剩余财产。
>
> 第十条　申请财产对外转移总金额在等值人民币50万元以下（含50万元）的，由所在地外汇局审批。…超过上述金额的，由所在地外汇局初审后，报国家外汇管理局审批。

### N08 — 汇发〔2014〕2号 section 6, which supersedes both

<https://www.safe.gov.cn/tianjin/2024/0903/2594.html> · HTTP 200 · fetched 2026-11-11

> 六、简化个人财产转移售付汇管理
>
> （一）移民财产转移购付汇核准，由移民原户籍所在地外汇局负责审批。继承财产转移购付汇核准，由被继承人生前户籍所在地外汇局负责审批。**取消**财产转移总金额超过等值人民币50万元报国家外汇管理局备案的要求。
>
> （二）**取消**移民财产转移分次汇出的要求。申请人向原户籍所在地外汇局办理移民财产转移核准手续后，银行可在核准件审批额度内一次或分次汇出相关资金。
>
> （四）**取消**对有关财产权利文件…进行公证的要求；**取消**对委托代理协议、代理人身份证明进行公证的要求。

This is the most consequential single finding of the pass. Section 6(1) cancels the RMB 500,000
head-office filing. Section 6(2) cancels the staged remittance — the bank may remit **once** or in
instalments inside the approved amount. Section 6(4) cancels notarisation of property documents and
of the agency agreement.

The page is marked **（已修改）**. Its amendment note says 汇发〔2023〕28号 annex 4 modifies items
(一) and (二) of **section 3** only. Section 6 is not among the amended items — but the page does
not certify the list is exhaustive, so this is disclosed as N676-F04 rather than asserted.

### N08b — same notice, section 5(1)

> 五、简化境内机构利润汇出管理（一）银行为境内机构办理等值5万美元（含）以下利润汇出，原则上可不再审核交易单证；办理等值5万美元以上利润汇出…应按真实交易原则审核与本次利润汇出相关的董事会利润分配决议…及其税务备案表原件。

Recorded because the USD 50,000 figure here is an **institutional** document-review threshold, not
the individual convenience amount. Conflating the two is irregularity N676-F05.

---

## 4. The Chinese tax that actually applies

### N09 — PRC Individual Income Tax Law

<https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html> · HTTP 200 ·
fetched 2026-11-11 · seventh amendment, 2018-08-31

> 第三条　个人所得税的税率：（一）综合所得，适用百分之三至百分之四十五的超额累进税率…（二）经营所得，适用百分之五至百分之三十五的超额累进税率…（三）利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十。

### N09b — same law, arts. 1, 10, 13, 15

> 第一条　在中国境内有住所，或者无住所而一个纳税年度内在中国境内居住累计满一百八十三天的个人，为居民个人。居民个人从中国境内和境外取得的所得，依照本法规定缴纳个人所得税。

> 第十三条　…纳税人因移居境外注销中国户籍的，应当在注销中国户籍前办理税款清算。

> 第十五条　…个人转让不动产的，税务机关应当根据不动产登记等相关信息核验应缴的个人所得税，登记机构办理转移登记时，应当查验与该不动产转让相关的个人所得税的完税凭证。

Art. 13 means tax must be cleared **before** the hukou is cancelled — it is a precondition of the
emigrant route, not a consequence of moving money. Art. 15 means the tax payment certificate is a
step *inside* a property sale: the registration authority must see it before it will register the
transfer.

---

## 5. The U.S. side

### N10 — IRS yearly average currency exchange rates

<https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates> ·
HTTP 200 · fetched 2026-11-11

> China | Yuan | 7.129 | 7.189 | 7.075 | 6.730 | 6.452

Columns 2025, 2024, 2023, 2022, 2021. The same page states: *"The Internal Revenue Service has no
official exchange rate. Generally, it accepts any posted exchange rate that is used consistently."*
The averages are used here only because no real basis was supplied.

### N11 — 26 U.S.C. § 988

<https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm>
· HTTP 200 · fetched 2026-11-11 · 2023 edition

> (e)(1) The preceding provisions of this section shall not apply to any section 988 transaction
> entered into by an individual which is a personal transaction.
>
> (e)(2) If—(A) nonfunctional currency is disposed of by an individual in any transaction, and
> (B) such transaction is a personal transaction, no gain shall be recognized for purposes of this
> subtitle by reason of changes in exchange rates after such currency was acquired by such
> individual and before such disposition. **The preceding sentence shall not apply if the gain which
> would otherwise be recognized on the transaction exceeds $200.**

Together with (a)(1)(A) — the gain is ordinary income — and (c)(1)(C)(i)–(ii) — a disposition of
nonfunctional currency, which includes coin or currency and demand or time deposits, is a section
988 transaction.

**This is the single most important U.S.-side finding.** The personal-transaction relief exists, but
it disappears the moment the gain exceeds $200. At $10,000 with a 2024 basis the modelled gain is
$692.59, so at every amount in the $10,000-400,000 range the relief does **not** apply.

### N12 — 31 CFR 1010.821, the FBAR penalty table

<https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821> ·
HTTP 200 · fetched 2026-11-11 · *"Displaying title 31, up to date as of 11/09/2026"*

| U.S. Code citation | Description | As amended by statute | Assessed on or after 2025-01-17 |
|---|---|---|---|
| 31 U.S.C. 5321(a)(5)(B)(i) | Foreign Financial Agency Transaction — Non-Willful | 10,000 | **16,536** |
| 31 U.S.C. 5321(a)(5)(C)(i)(I) | Foreign Financial Agency Transaction — Willful | 100,000 | **165,353** |
| 31 U.S.C. 5321(a)(1) | General willful BSA violation | 25,000 − 100,000 | **71,545 − 286,184** |

### N13 — IRS, figuring the foreign earned income exclusion

<https://www.irs.gov/individuals/international-taxpayers/figuring-the-foreign-earned-income-exclusion>
· HTTP 200 · fetched 2026-11-11

> For tax year 2025, the maximum foreign earned income exclusion is the lesser of the foreign income
> earned or $130,000 per qualifying person. For tax year 2026, the maximum exclusion is $132,900 per
> person. … For 2025, the housing amount limitation is $39,000; for 2026, it is $39,870.

**Earned income only.** It does not shelter a dividend, rent, interest, a property gain, or the
§988 currency gain — which are the likely components of this balance.

### N14 — IRS, gifts from a foreign person

<https://www.irs.gov/businesses/gifts-from-foreign-person> · HTTP 200 · fetched 2026-11-11

> …you are required to report the receipt of such gifts or bequests only if the aggregate amount
> received from that nonresident alien or foreign estate… exceeds $100,000 during the taxable year.
>
> For purported gifts from foreign corporations or foreign partnerships… exceeds $20,116 for 2025,
> and $20,573 for 2026… you may be subject to penalties under IRC section 6039F(c).

---

## 6. Pages NOT re-opened this pass

Recorded as unverified in `data/n676_sources.csv` with `fetched_today = no`, and no claim on the
site rests on them.

| ID | Page | Why it matters | Handling |
|---|---|---|---|
| N15 | 《经常项目外汇业务指引（2020年版）》 PDF, annex to 汇发〔2020〕14号 | Arts. 54-59 are the operative rules | Not fetched. Every article relied on is quoted **verbatim inside** the official SAFE branch answers N03, N04 and N05, so the citations still stand; the PDF was not opened. |
| N16 | 财税〔2008〕132号, savings-deposit interest | The exemption on interest | Not fetched. The tax page leaves the value **blank** and flags it (N676-U05). |
| N17 | CBP foreign-currency declaration page | The U.S. cash threshold and form | Not fetched. Every U.S.-side cash figure is **blank** and flagged (N676-U06). |

---

## 7. Arithmetic convention, stated once

```
own_mid  = (6.6630 + 6.6911) / 2                = 6.67705      our own mid-point
spread   = USD * (6.6911 - 6.67705) / 6.6911    = 0.20998% of every dollar
CNY_sent = USD * 6.6911                                        you pay the SELLING rate
wire_cny = clamp(0.001 * CNY_sent, 50, 260) + 150
wire_usd = wire_cny / 6.6911
total    = round(spread, 2) + round(wire_usd, 2)               each part rounded once
gain988  = USD * (1 - 6.6911 / basis)                          a gain, not a tax
```

Worked example at $10,000: spread = 10,000 × 0.0020998 = **$21.00**; CNY_sent = 66,911; fee =
clamp(66.911, 50, 260) + 150 = 216.911 RMB ÷ 6.6911 = **$32.42**; total **$53.42**.

At $400,000: spread = **$839.92**; fee = clamp(2,676.44, 50, 260) + 150 = 410 RMB ÷ 6.6911 =
**$61.28**; total **$901.20**. The 1 per mille fee binds at its RMB 260 ceiling above about $38,857,
so from there the fee is flat and one wire always beats several.

`scripts/n676_verify.py` re-derives all 160 ladder rows from the board and tariff alone, checks
every rendered cell against the CSV, and confirms that the same convention on the 2026-11-10
17:39:58 board reproduces the $53.38 and $899.01 figures the site carried before.
