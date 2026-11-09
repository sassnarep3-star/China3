# T2 — China-side foreign-exchange framework

Session `session-c703e38c` · branch `arena/c703e38c-china3` · reviewed 2026-11-07 (UTC)
Scope: `research/china-framework.md`. Structured data: `data/china_rules.csv` (50 rows, one official link each).

## Method

Primary sources only: 国家外汇管理局 (safe.gov.cn and its provincial branches), 中国人民银行
(pbc.gov.cn), 国务院 / 中国政府网 (gov.cn), 国家税务总局 (chinatax.gov.cn / fgk.chinatax.gov.cn),
人民法院 (hncourt.gov.cn), 中国证监会 (csrc.gov.cn), 香港金融管理局 (hkma.gov.hk), 中国银行
(boc.cn, for its own published fee schedules). Search-engine snippets were treated as leads
only. Pages opened in full during this task: SAFE 宁夏 2022 政策释疑（八）, SAFE 天津 2024
个人外汇（三）, SAFE 天津 2024 问答案例（九）, 中国政府网《个人外汇管理办法》,
SAFE《中华人民共和国外汇管理条例》2008 全文, PBOC 银发〔2026〕42号 全文,
PBOC 银发〔2021〕237号 全文 (historical). Other official pages were read as official
full-text excerpts; the exact quoted passage is recorded in the CSV row.

## 1. Classification — the decisive question

`个人外汇管理办法`（中国人民银行令〔2006〕第3号）第37条: 境内个人 = 持中国居民身份证、
军人身份证件、武装警察身份证件的中国公民；境外个人 = 持护照、港澳居民来往内地通行证、
台湾居民来往大陆通行证的外国公民（包括无国籍人）以及港澳台同胞. 第28条: 银行按照
个人开户时提供的身份证件等证明材料确定账户主体类别. On the stated facts (a U.S. citizen),
the passport route points to 境外个人. [S05](https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm),
[S06](https://www.pbc.gov.cn/zhengwugongkai/4081330/4406346/4406348/2025092319185421938/index.html).

**Irregularity IR-007.** 《外汇管理条例》（国务院令第532号）第52条（二）defines 境内个人 as
"中国公民和在中华人民共和国境内连续居住满1年的外国人" — a U.S. citizen resident in China
for a year could fall in that definition. [S07](https://www.safe.gov.cn/safe/2008/0806/5321.html).
The two definitions are in tension; the operative classification is set by the ID document
used at account opening, so the bank's system classification must be confirmed in writing.
No conclusion about the user's actual classification is asserted.

## 2. The USD 50,000 figure is not a cap and not a tax

SAFE 宁夏 2022《外汇业务政策释疑（八）》: "对于真实、合法的经常项目和已开放的资本项目下
购汇和结汇都没有金额限制…年度便利化额度不是个人每年购汇结汇的限额，只是超过等值
5万美元不能仅凭本人有效身份证件办理". The same Q&A states the facilitation amount is
每人每年等值5万美元 and describes 指引第57条 (不占额度的经常项目购汇, with ID + 有交易额的
购汇资金用途材料). [S01](https://www.safe.gov.cn/ningxia/2022/0929/1997.html).

Separately, 指引第64条 sets a **different** USD 50,000 threshold: for outward remittance
from an FX savings account for current-account spending, same-day cumulative ≤USD 50,000
needs ID only; above needs ID + transaction materials; the bank checks consistency between
the FX purchase purpose and the payment purpose. Foreign banknotes remitted: ≤USD 10,000/day
ID only; above needs the customs declaration or original withdrawal slip plus materials.
[S02](https://www.safe.gov.cn/tianjin/2024/0229/2402.html). Conflating the two USD 50,000
rules is a common error (F05).

## 3. Foreign-individual route (most relevant to this case)

指引第59条, quoted in SAFE 天津 2024 经常项目外汇政策问答案例（九）: "境外个人在境内
取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务
凭证）在银行办理购汇。持有外国人永久居留身份证的境外个人适用购汇年度便利化额度."
[S03](https://www.safe.gov.cn/tianjin/2024/0621/2529.html). SAFE 重庆《常见外汇业务答疑
手册》states "境外个人购汇本身无年度额度限制" [S43](https://www.safe.gov.cn/chongqing/file/file/20190311/87806e211bb74eb4a44e71395c31cda9.pdf).
SAFE 上海 问答（321）: the bank reviews the **RMB source**, not the FX use
[S45](https://www.safe.gov.cn/shanghai/2019/0215/988.html). SAFE 天津 2021 服务贸易问答（四）
clarifies that the source-of-funds evidence includes the tax-filing form (税务备案表, including
electronic), a tax-payment certificate or an exemption certificate
[S44](https://www.safe.gov.cn/tianjin/2021/1102/1777.html).

Related legal channels for a foreign individual in 《个人外汇管理办法》: Art. 13 (lawful
current-account RMB income → purchase and remit), Art. 14 (unused inward FX → return along
the original route), Art. 15 + 实施细则 Art. 13 (unused RMB from a prior conversion →
reconvert against the original exchange memo, valid 24 months), Art. 22 (proceeds from sale
of domestic real estate → purchase FX with SAFE approval), Art. 26 (lawful property transfer
under the dedicated rules). [S05], [S04](https://www.safe.gov.cn/tianjin/2024/0430/2464.html).

## 4. Tax is on the source of funds, not the act of conversion

《个人所得税法》第3条: comprehensive income 3%–45%; interest/dividends, property rental,
property transfer and incidental income 20%. [S23](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html).
财税〔2008〕132号: savings-deposit interest temporarily exempt from IIT since 2008-10-09
[S24](https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/grsds/200810/t288953.html).
国家税务总局/外汇局公告2013年第40号: a single outbound payment above USD 50,000 (exclusive)
in listed categories requires tax filing (备案); this is documentation, not a tax
[S21](https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html),
[S22](https://www.chinatax.gov.cn/chinatax/c102449/c5219874/content.html).
No official source reviewed establishes a flat tax on converting personal CNY principal
(F01, IR-011). China's CRS rules (公告2017年第14号) require domestic financial institutions
to identify and report non-resident accounts annually by 31 May
[S25](https://fgk.chinatax.gov.cn/zcfgk/c100012/c5207016/content.html).

## 5. Prohibitions, penalties and enforcement

- 《个人外汇管理办法》第7条: no splitting and no false documents. 《个人购汇申请书》'六不得'
  and SAFE 厦门 service tips prohibit false declarations, lending/borrowing quotas and
  un-opened capital items (overseas property, securities, life insurance, investment-return
  insurance). [S09](https://www.safe.gov.cn/safe/file/file/20210402/30fab7a9646f417ca9d2f67ff4c1e5f0.pdf),
  [S10](https://www.safe.gov.cn/xiamen/file/file/20211022/f4794075e84e40dd9394be523a52731b.pdf),
  [S53](https://www.safe.gov.cn/neimenggu/file/file/20200228/fa90770027ed4d919de981c09bc25751.pdf).
- SAFE 广东: only qualified banks / licensed exchange institutions / 代兑点 are legal;
  company, app, 朋友圈, 黄牛 and 地下钱庄 channels are not
  [S08](https://www.safe.gov.cn/guangdong/2020/0304/1668.html).
- 指引第62条: watch list = inclusion year + 2 consecutive years; during that period
  documented transactions are required. [S11](https://www.safe.gov.cn/tianjin/2025/0613/2811.html).
  **IR-006**: 汇发〔2009〕56号 and 汇发〔2015〕49号 are both marked 已废止 on SAFE
  [S13](https://www.safe.gov.cn/guangdong/2016/0104/216.html); old enforcement cases still
  quote the old numbers [S14](https://www.safe.gov.cn/hebei/2016/0328/615.html),
  [S15](https://www.safe.gov.cn/hebei/2016/0711/658.html).
- 《外汇管理条例》2008 修订版 第39条 逃汇: ≤30%, serious 30%–equal; 第40条 非法套汇:
  same range; 第44条 擅自改变用途: same range; 第45条 非法买卖外汇: warning + confiscation
  + ≤30%, serious 30%–equal; 第42条 违规携带外汇: warning + ≤20%
  [S07](https://www.safe.gov.cn/safe/2008/0806/5321.html).
  **IR-005**: the 1996 version of Art. 45 (30%–3x + compulsory conversion) is obsolete;
  the SAFE full-text 2008 revision is used here.
- 法释〔2019〕1号: illegal FX trading ≥RMB 5m turnover or ≥RMB 100k illegal gain = 情节严重;
  ≥RMB 25m or ≥RMB 500k = 情节特别严重; Criminal Law Art. 225 非法经营罪: ≤5 years + 1–5×
  illegal-gain fine, or ≥5 years + 1–5× / confiscation
  [S32](http://www.hunan.gov.cn/zqt/zcsd/201901/t20190131_13641628.html),
  [S33](https://www.hncourt.gov.cn/public/detail.php?id=176932),
  [S34](https://xczy.hncourt.gov.cn/public/detail.php?id=2739).

## 6. Other lawful channels, limits and pricing mechanics

- 汇发〔2017〕3号 profit remittance: genuine compliant profits can be remitted directly
  through a bank with no limit; >USD 50,000 requires board resolution, original tax-filing
  form, audited financial statements, and prior losses must be made up
  [S20](https://www.safe.gov.cn/shanghai/2017/0126/76.html), [S19](https://www.safe.gov.cn/safe/2017/0126/12679.html).
- 个人财产对外转移: emigration / inheritance only; <RMB 500k reviewed by the provincial
  SAFE branch, ≥RMB 500k approved by SAFE head office; ≥RMB 200k emigration transfers are
  "一次申请、分步汇出" over two years (half at approval, half of the remainder after one
  year, the rest after two years)
  [S18](http://m.safe.gov.cn/safe/2004/1116/4134.html), [S17](https://www.safe.gov.cn/safe/2004/1116/5461.html).
  **IR-021**: later amendments not exhaustively re-checked.
- Cash: ≤USD 5,000 without a permit; 5,000–10,000 with a bank-issued 《携带证》; >10,000
  generally not allowed except with SAFE approval [S36](http://www.safe.gov.cn/hebei/2019/0521/1366.html),
  [S37](https://www.safe.gov.cn/big5/big5/www.safe.gov.cn/tianjin/2024/0430/2466.html).
  Overseas ATM withdrawals: ≤RMB 100,000/person/year and ≤RMB 10,000/card/day; overage
  suspends the current and following year; card spending is unaffected and does not use
  the FX quota [S35](https://www.safe.gov.cn/hubei/2019/0305/851.html),
  [S35b](https://www.safe.gov.cn/hebei/2018/0409/1010.html).
- Cross-border RMB: PBOC supports banks handling current-account cross-border RMB
  settlement for individuals (e.g. legitimate salary income)
  [S38](https://www.pbc.gov.cn/tiaofasi/144941/3581332/4158143/index.html);
  Wealth Management Connect uses RMB throughout and the FX conversion happens offshore,
  so it does not consume an individual FX quota (RMB 1m individual quota, RMB 150bn each
  direction) [S39](https://guangzhou.pbc.gov.cn/guangzhou/129196/4332364/4332374/4343888/index.html),
  [S40](http://gdjr.gd.gov.cn/gdjr/zwgk/jrzcfg/content/post_3520533.html).
  跨境支付通 (2025) links the mainland IBPS with Hong Kong's FPS for bilateral local-currency
  remittance [S55](https://hangzhou.pbc.gov.cn/hangzhou/125264/5778339/index.html).
  QDII: cumulative net outflow ≤ approved quota [S41](http://www.safe.gov.cn/tianjin/2019/0214/1098.html).
  Cross-border e-commerce: with transaction materials/electronic information, no FX quota
  consumed (指引第66条) [S42](https://www.safe.gov.cn/shanghai/2026/0402/2412.html).
- Exchange-rate mechanics: since 2014-03-17 the interbank spot CNY/USD price may move ±2%
  around the daily central parity (PBOC 公告〔2014〕5号); the same notice widened the
  bank-customer spread cap to 3%, and 银发〔2014〕188号 abolished spread management entirely
  on 2014-07-01, leaving banks to price autonomously
  [S26](https://xining.pbc.gov.cn/zhengcehuobisi/125207/125217/125922/125945/2805761/index.html),
  [S27](https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/2810732/index.html),
  [S28](https://www.pbc.gov.cn/goutongjiaoliu/113456/113472/2827987/index.html).
  Therefore the ±2% band is **not** a retail spread cap.
- Virtual currency: 银发〔2026〕42号 (in force 2026-02-06) prohibits domestic virtual-currency
  business, fiat↔virtual-currency exchange, offshore services to mainland residents,
  RMB-pegged stablecoins issued offshore without approval, and unapproved RWA tokenisation;
  participating civil transactions may be void and losses self-borne. It **repeals**
  银发〔2021〕237号 [S29](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html),
  [S30](https://www.pbc.gov.cn/tiaofasi/144941/3581332/4348658/index.html),
  [S56](https://www.csrc.gov.cn/shanxi/c106408/c7616553/content.shtml). **IR-004**.

## Irregularities raised by this task

IR-004 (2021 notice repealed), IR-005 (two versions of Art. 45), IR-006 (two repealed
anti-splitting circulars), IR-007 (conflicting definitions of 境内/境外个人), IR-011
(no official "conversion tax"), IR-012 (current spread / correspondent fees / CNY-CNH basis
unverifiable), IR-015 (current central parity not verified), IR-016 (translations are ours),
IR-021 (2004 property-transfer rules), IR-022 (HKMA spreads are historical), IR-023
(several sources are provincial-branch Q&As). All are published on `deep-review.html`.

## Verification performed

- Full-text retrieval of 6 official pages; official full-text excerpts for the remainder,
  with the quoted passage recorded in `data/china_rules.csv`.
- Cross-check of every numeric value used (50,000; 10,000; 200,000; 500,000; 100,000;
  10,000 RMB/day; 100,000 RMB/year; 24 months; 30%/equal; 20%; 2%; 3%; 1%/4%; 5m/25m;
  100k/500k; 3%–45%; 20%; 150bn; 1m; 1–5×) against the linked official text.
- `scripts/verify_deep.py` enforces one official-domain link per row and blank values for
  unverified rows.
