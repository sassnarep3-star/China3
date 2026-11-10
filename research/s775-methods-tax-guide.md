# S775 CNY→USD methods & tax guide

Verification date: **2026-11-10**. Sources: `data/s775_sources.csv` (S01–S51). Every rule below is
cited by source id; unconfirmed values are blank and flagged in `data/s775_flags.csv`.

## A. The 24 routes

### Bank wires (cleanest for most people)

- **M01 Personal bank wire (SWIFT).** Unrestricted; up to US$50,000/day on ID documents
  ([S13](https://www.safe.gov.cn/tianjin/2024/0229/2402.html)). Cost: FX spread 0.2104% +
  1‰ (¥50–¥260) + ¥150 cable ([S03](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html)).
- **M02 OUR wire.** Full-amount-received adds US$15 (BOC NY) / US$25 (other US banks) per wire —
  corporate tariff document, personal applicability conditional ([S04](https://www.boc.cn/pbservice/bi2/201412/t20141231_4404048.html)).
- **M03 Cash + border carry.** ATM ≤¥100k/yr, ¥10k/day ([S20](https://www.safe.gov.cn/hubei/2019/0305/851.html));
  cash price ≠ spot board (blank); border carry ≤$10,000 without declaration ([S21](http://www.safe.gov.cn/hebei/2019/0521/1366.html), [S51](https://www.cbp.gov/travel/international-visitors/money-monetary-instruments)).
- **M04 Overseas ATM.** UnionPay ¥12 + 1% (max ¥112/tx); MC/Visa 2.5% ($3–$40) from 2026-11-11 ([S06](https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html)).

### Salary & employment

- **M07 Foreign permanent resident ID salary FX.** Convenience amount available ([S11](https://www.safe.gov.cn/tianjin/2025/1113/2926.html)).
- **M08 Foreign passport salary FX.** Taxed salary not subject to the annual convenience amount ([S16](https://www.safe.gov.cn/tianjin/2026/0713/3088.html)); PRC IIT 20% flat class ([S35](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html)).
- **M09 Employer payroll remittance.** Provider fees blank (unverified).
- **M18 Retained social insurance payout.** MOHRSS Order No.16 art. 5: account retained on departure;
  lump sum on written termination request ([S38](https://rst.shaanxi.gov.cn/sy/ztzl/rdzt/pfxczl/202501/t20250107_3296414.html)).

### Capital account (large, approved amounts)

- **M05 Emigrant property transfer.** SAFE approval at former hukou location; approved amount
  remitted once or in instalments — the 2004 two-year staging was cancelled by
  `汇发〔2014〕2号` ([S14](https://www.safe.gov.cn/tianjin/2024/0903/2594.html)). Requires hukou
  cancellation certificate; U.S. citizen by birth without mainland hukou does not qualify.
- **M06 Foreigner property purchase/inheritance.** PBOC `[2006] No.3` arts. 7/13/22/32/37
  ([S27](https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm)); 2025 reform
  ([S17](https://www.safe.gov.cn/safe/2025/0915/26536.html)).
- **M15 Property sale proceeds.** Repatriation with tax evidence; IIT 20% on transfer income ([S35](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html)).
- **M16 Company dividend.** Board resolution + audited financials; >US$50,000 requires the tax
  filing recordal ([S33](https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html), [S34](https://www.chinatax.gov.cn/chinatax/c102449/c5237521/content.html)); treaty 10% ([S50](https://www.irs.gov/pub/irs-trty/china.pdf)).
- **M17 Corporate financing/guarantee.** Capital-account registration required ([S25](https://www.safe.gov.cn/safe/file/file/20231116/698412b317c34542ae0dfa9075e7e6e8.pdf)).

### Investment income & products

- **M10 Dividends & interest.** Deposit interest IIT-exempt since 2008-10-09 ([S36](https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html));
  dividends 20% individual / 10% treaty ([S35](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html), [S50](https://www.irs.gov/pub/irs-trty/china.pdf)).
- **M11 Licensed payment platform.** `汇发〔2019〕13号` current-account scope ([S24](http://m.safe.gov.cn/safe/2019/0429/13115.html)); fees blank.
- **M12 Cross-border e-commerce.** Real transactions; FX purchase on evidence ([S24](http://m.safe.gov.cn/safe/2019/0429/13115.html)).
- **M13 QDII fund.** Institutional quota; no personal approval ([S25](https://www.safe.gov.cn/safe/file/file/20231116/698412b317c34542ae0dfa9075e7e6e8.pdf)); fees blank.
- **M14 GBA Wealth Management Connect.** ¥3M individual closed-loop quota (¥1.5M bank + ¥1.5M
  securities); eligibility: 2-year social insurance/tax or ¥400k income ([S30](https://guangzhou.pbc.gov.cn/guangzhou/129196/4332364/4332380/5221319/index.html), [S31](https://www.pbc.gov.cn/goutongjiaoliu/113456/113475/67fdfc7c586b49f4a6f1085ebb4f49b7/index.html)).
- **M23 Offshore RMB (CNH) + offshore conversion.** Eligibility not published nationally; fee blank.

### Planning & prohibited

- **M24 Staged annual conversions.** The convenience amount is not a limit — documents are
  ([S10](https://www.safe.gov.cn/ningxia/2022/0929/1997.html)).
- **M19 Crypto.** Prohibited by PBOC `银发〔2026〕42号` ([S29](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html)).
- **M20 Undeclared cash >$10,000.** FinCEN Form 105 ([S51](https://www.cbp.gov/travel/international-visitors/money-monetary-instruments)).
- **M21 Hawala / underground.** Decree 532 arts. 39/45; criminal thresholds
  ([S19](https://www.safe.gov.cn/safe/2008/0806/5321.html), [S39](https://www.hncourt.gov.cn/public/detail.php?id=176932)).
- **M22 Bypassing SAFE approval.** Illegal FX transfer ([S14](https://www.safe.gov.cn/tianjin/2024/0903/2594.html), [S19](https://www.safe.gov.cn/safe/2008/0806/5321.html)).

## B. Tax & penalty decomposition

### China side

| Item | Rule | Source |
|---|---|---|
| Conversion itself | **No PRC tax** (negative finding) | S19, S10, S03 |
| Illegal FX transfer / private trading | Fine ≤30% of amount; 30%–100% if serious | S19 |
| Criminal FX trading | Turnover ≥¥5,000,000 / gain ≥¥100,000 | S39 |
| IIT on dividends/interest/property transfer/rental | 20% flat | S35 |
| Deposit interest | IIT-exempt (since 2008-10-09) | S36 |
| Non-resident enterprise passive income | 10% withholding | S37 |
| US treaty rate | 10% dividends/interest/royalties | S50 |
| >US$50,000 remittance | Tax filing recordal (procedure) | S33, S34 |
| Convenience amount | US$50,000/yr — not a hard limit | S10 |
| 兑回 (convert back) | Receipt valid 24 months; ≤$500/$1,000 ID-only | S22, S23 |

### US side

| Item | Rule | Source |
|---|---|---|
| §988 ordinary gain/loss | Non-personal transactions; §162/§212 accounts excluded from "personal" | S40 |
| Personal exclusion | Personal transactions excluded; ≤$200 gain excluded; personal loss nondeductible (§165(c)) | S40 |
| FBAR | Aggregate >$10,000 at any time (strictly greater) | S48 |
| FBAR penalties | Non-willful $16,536; willful greater of $165,353 or 50% balance | S49 |
| Form 8938 | $50k/$75k US single; $200k/$300k abroad; penalties $10k–$60k+ | S43 |
| Form 3520 | >$100k foreign gift; >$20,573 (2026) corp/partnership | S44 |
| FEIE | $132,900 (2026) wages only — not currency gain | S41 |
| Foreign tax credit | Form 1116; PRC withholding may be creditable | S47 |
| Streamlined procedures | SFOP 0% (abroad) / SDOP 5% (US-based), non-willful | S45 |
| Border currency | >$10,000 FinCEN Form 105, collective per family/group | S51 |
| Saving Clause | Treaty preserves US worldwide taxation of US citizens | S50 |
| Basis measurement | IRS yearly average CNY: 7.129 (2025), 7.189 (2024), 7.075 (2023) | S42 |

### Cohort sensitivity (illustrative, not your tax)

| Acquired at IRS average | Gain per $10,000 at today's ask 6.6903 | Note |
|---|---|---|
| 2021 (6.452) | **−$369.34** | Personal loss — nondeductible ($0 tax) |
| 2024 (7.189) | **+$693.70** | Illustrative only; characterisation flagged (`S775-F10`) |
| 2025 (7.129) | **+$615.37** | Illustrative only |

Your actual basis was not provided; the user-specific tax cell stays **blank**.

## C. How to use the dashboard

1. `s775-dashboard.html` — executive dashboard: headline numbers, top routes, decision steps.
2. `s775-cost-10k-400k.html` — the 40-step cost ladder (filterable by amount).
3. `s775-methods.html` — all 24 routes with status, pros/cons, penalty anatomy.
4. `s775-steps.html` — numbered execution playbooks for every route.
5. `s775-penalties-tax.html` — the full China + US penalty/tax tables.
6. `s775-flagged-review.html` — every unverified/conditional item, with sources.
7. `s775-sources.html` — the 51 official sources with what each establishes.
