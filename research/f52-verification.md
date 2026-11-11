# F52 verification log — every proposition re-read on 2026-11-11

Session `arena/4bfb6552-china3`. Method: each official page below was fetched
in full during this session (`direct`), except F-S13 (`excerpt`: the official
IRS treaty PDF's own text returned by search of that exact URL). No inherited
quote was copied without a today-fetch. Data module: `scripts/f52_data.py`;
gate: `python3 scripts/verify_f52.py`.

| ID | URL | What was read (verbatim core) | Used for |
|---|---|---|---|
| F-S01 | https://www.boc.cn/sourcedb/whpj/enindex_1619.html | USD: Buying 666.30, Selling 669.11, Middle 671.91, Pub Time 2026/11/11 10:25:02 | Spread 0.2100% vs computed midpoint 6.67705; all pricing |
| F-S02 | https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html | 跨境汇款（电汇）每笔汇款金额的1‰，最低50元/笔，最高260元/笔；另收电讯费，非港澳台地区150元/笔 (since 2014-11-01; local differences possible) | Wire fee formula |
| F-S03 | https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html | 国外及港澳台 银联：每笔（12元+取现金额的1%），最高112元/笔 (effective 2026-11-11) | F10 card fee |
| F-S04 | https://www.safe.gov.cn/tianjin/2026/0713/3088.html | 汇发〔2020〕14号第五十九条：境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇 | F01 eligibility |
| F-S05 | https://www.safe.gov.cn/tianjin/2024/0621/2529.html | Same Art. 59 + 持有外国人永久居留身份证的境外个人适用购汇年度便利化额度 | Q02, F07 eligibility |
| F-S06 | https://www.safe.gov.cn/ningxia/2022/0929/1997.html | 年度便利化额度（每人每年等值5万美元）不是限额；超过不能仅凭身份证件办理；真实合法经常项目和已开放资本项目没有金额限制 (Arts. 54–57) | Q03, F07 |
| F-S07 | https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html | IIT Law Art. 3: 综合所得 3%–45%；利息股息红利、财产租赁、财产转让、偶然所得 20%；Art. 6(5) property gain base; Art. 2 nine categories | Layer 4, F04/F09 tax |
| F-S08 | https://www.safe.gov.cn/safe/2008/0806/5321.html | FX Regulation: Art. 5 国家对经常性国际支付和转移不予限制；Art. 39/40 fines ≤30% (30%–100% serious); Art. 42 ≤20%; Art. 45 private trading; Art. 48 documents ≤CNY 50,000; Art. 52(2) residence definition | Q01, X01–X05, F52-U13 |
| F-S09 | https://www.safe.gov.cn/tianjin/2026/0917/3134.html | Art. 60: 凭身份证件和原兑换水单兑回；有效期自兑换日起24个月；当日≤500美元凭身份证件办理 | F02 |
| F-S10 | https://www.safe.gov.cn/hubei/2019/0305/851.html | 汇发〔2017〕29号：本人名下银行卡合计每自然年度境外提现≤等值10万元人民币；每卡每日≤等值1万元；不得借用/出借银行卡规避 | F10 caps, X06 |
| F-S11 | http://www.safe.gov.cn/hebei/2019/0521/1366.html | 5000美元（含）以下海关直接放行；5000–10000美元银行《携带外汇出境许可证》；10000美元以上外汇局许可、原则上不得携带出境 | F11, X04 |
| F-S12 | https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements | FBAR >$10,000 aggregate; 8938 US $50k/$75k, abroad $200k/$300k (unmarried), joint double; 8938 penalty $10k → max $60k | Q12, layers 6a/6b |
| F-S13 | https://www.irs.gov/pub/irs-trty/china.pdf | Treaty Art. 9(2): tax on dividends to a resident beneficial owner shall not exceed 10% of gross dividends (excerpt) | F09T ceiling, F52-U06 |
| F-S14 | https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821 | Up to date as of 11/09/2026; assessed on/after 2025-01-17: non-willful $16,536; willful $165,353 | Layer 6a |
| F-S15 | https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates | China Yuan: 2023 7.075, 2024 7.189, 2025 7.129; "The IRS has no official exchange rate"; §988 gain may need recognition | FX-gain table |
| F-S16 | https://www.irs.gov/businesses/gifts-from-foreign-person | Form 3520 Part IV if aggregate from a foreign individual/estate exceeds $100,000/year; corp/partnership $20,573 for 2026 | Q13, F05 U.S. side |
| F-S17 | https://www.irs.gov/instructions/i3520 | §6039F failure: 5% per month, max 25%; IRS may determine tax consequences | Layer 6c |
| F-S18 | https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm | §988(a) ordinary treatment; disposition of nonfunctional currency is a §988 transaction; §988(e) $200 personal-transaction rule (via official text + search read of the section) | Q14, layer 5 |
| F-S19 | https://www.irs.gov/publications/p525 | Personal FX gain over $200: Pub. 525 summary says report as capital gain — conflicts with F-S18 (flag F52-U05) | Layer 5 |
| F-S20 | https://www.safe.gov.cn/safe/file/file/20170726/3f982dfaf9384da5aec879b21ee08f23.pdf | Watch-list （关注名单） management: listing year + following 2 years under strict authenticity review | X01 |

## Cross-checks performed

- Independent hand recomputation of the ladder (spread, wire, quota, ATM,
  dividend, FX gain) matched `scripts/verify_f52.py` to the cent, including
  the drift versus yesterday's snapshot (F01: $53.38 → **$53.42** at $10,000;
  $899.01 → **$901.20** at $400,000), which independently confirms the prior
  session's finding F03 without reusing its numbers.
- Every HTML data row contains an official link; every source URL is on an
  official domain; F08 (cross-border RMB) is blank in all 40 rows by design.
- Unverified items are blank + flagged (15 flags, 4 irregularities) on
  `f52-flagged.html`. Nothing was inferred to fill a blank.
