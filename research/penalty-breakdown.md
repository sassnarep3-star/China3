# T4b — Breakdown of the "conversion penalty"

Session `session-c703e38c` · reviewed 2026-11-07 (UTC)
Scope: `research/penalty-breakdown.md`. Structured data: `data/penalty.csv` (35 components,
one official link per row). Rendered at `penalty.html`.

## The core analytical move

The user reports that "conversion currently incurs considerable taxes." Treating that as one
number would be the mistake. Official sources describe **at least eight distinct layers**,
each with its own legal basis, payer and arithmetic. None of them is a "tax on converting
your own principal":

| Layer | What it actually is | Official source |
|---|---|---|
| 1 | Chinese individual income tax on **how the money was earned** (3%–45% comprehensive; 20% for interest/dividends/property/incidental income) | [S23](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html) |
| 2 | Chinese tax **clearance documents** as a precondition to buy FX (税务凭证 / 备案表; single outbound payment >USD 50,000) | [S21](https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html), [S44](https://www.safe.gov.cn/tianjin/2021/1102/1777.html) |
| 3 | Bank **buy/sell spread** — deregulated since 2014-07-01; bank sets its own price | [S27](https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/2810732/index.html) |
| 4 | Bank **wire / cable / correspondent / full-amount fees** (verified published components) | [S46](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html), [S47](https://www.boc.cn/cbservice/cb3/cb33/200807/t20080701_852.html), [S48](https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html) |
| 5 | **Offshore basis** (CNY vs CNH) if the conversion happens offshore | [S50](https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201203/chapter4.pdf), [S51](https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201409/chapter4.pdf) |
| 6 | Chinese **administrative and criminal penalties** if a prohibited route is used (30%–100% of the illegal amount; 1–5× illegal-gain fine; up to 5+ years) | [S07](https://www.safe.gov.cn/safe/2008/0806/5321.html), [S32](http://www.hunan.gov.cn/zqt/zcsd/201901/t20190131_13641628.html) |
| 7 | U.S. **tax on income/currency gain** while the money is held or converted (worldwide income; §988(e) $200 de minimis) | [U01](https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-about-international-individual-tax-matters), [U04](https://www.irs.gov/publications/p525) |
| 8 | U.S. **information-reporting penalties** — FBAR, Form 8938, Form 3520 | [U20](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821), [U06](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements), [U09](https://www.irs.gov/businesses/gifts-from-foreign-person) |

## Verified numerical components (no estimates)

- CNY/USD interbank spot band: **±2%** of daily central parity (PBOC 公告〔2014〕5号,
  effective 2014-03-17) [S26](https://xining.pbc.gov.cn/zhengcehuobisi/125207/125217/125922/125945/2805761/index.html).
  Historical, now-repealed customer spread caps: 1% (spot) / 4% (cash) in 2005, widened to
  3% in March 2014, abolished July 2014 [S28](https://www.pbc.gov.cn/goutongjiaoliu/113456/113472/2827987/index.html).
  **The ±2% band is not a retail spread cap.**
- Bank of China personal e-banking cross-border wire: **1‰ of the amount, min ¥50 / max ¥260
  per transaction**, plus a cable fee of **¥80** (HK/Macau/Taiwan) or **¥150** (elsewhere)
  [S46]. The corporate schedule is 1‰, min ¥50 / max ¥1,000 [S47]. Overseas bank charges are
  passed through at actual cost [S47]. The 全额到账 service adds **USD 15** for a beneficiary
  bank holding an account at BOC New York [S48]. A 2024 promotional waiver (free / 10% off,
  2024-01-01 to 2024-12-31) is historical only — **IR-020** [S49](https://www.boc.cn/ebanking/bi3/bi31/202312/t20231229_24338136.html).
- HKMA recorded a CNY/CNH disparity of **1.94% on 2011-09-23** and an average CNH premium
  of **+163 pips in Q1 2014** [S50], [S51]. These are historical observations, not a current
  quote; the current basis is **blank / UNVERIFIED** (IR-012, IR-022).
- Chinese administrative fines: **≤30%** of the illegal amount, **30%–equal** for serious
  cases (逃汇 Art. 39, 非法套汇 Art. 40, 改变用途 Art. 44, 非法买卖外汇 Art. 45);
  **≤20%** for unlawful carrying of FX (Art. 42) [S07].
- Criminal thresholds: RMB **5m / 25m** turnover or RMB **100k / 500k** illegal gain;
  1–5× illegal-gain fine; ≤5 years / ≥5 years [S32], [S34](https://xczy.hncourt.gov.cn/public/detail.php?id=2739).
- U.S. FBAR: **$16,536** non-willful; **$165,353 or 50% of the account balance** willful —
  the largest single monetary risk identified. 2026 adjustment cancelled (IR-008)
  [U20], [U21](https://www.federalregister.gov/documents/2026/07/07/2026-13629/no-adjustment-to-civil-monetary-penalty-amounts).
- Form 8938: **$10,000**, plus **$10,000 per 30 days** after notice up to **$50,000**
  additional; **40%** understatement penalty [U06], [U08](https://www.irs.gov/businesses/corporations/fatca-information-for-individuals).
- Form 3520: **5% per month, capped at 25%** of the gift [U09].
- Personal foreign-currency gain: **$200** de minimis [U04].
- PRC treaty source-country cap **10%** on dividends/interest/royalties, but the saving
  clause preserves U.S. taxation of its citizens [U16](https://www.irs.gov/pub/irs-trty/china.pdf).
- Foreign tax credit is the lesser of foreign tax paid or the FTC limitation, so a Chinese
  tax payment is **not necessarily fully creditable** [U05](https://www.irs.gov/publications/p514).

## What is deliberately left blank

`data/penalty.csv` rows P01 (a general "conversion tax"), P05 (current bank spread), P14
(current CNY/CNH basis), P15 (cash vs account rate difference), P23 (U.S. tax character of
moving one's own principal) and P35 (the all-in total for this account) have **empty value
cells**, are marked UNVERIFIED, and are published on `review.html` with source links. The
brief prohibits inferring or filling values, so no worked numeric example with assumed
inputs is presented.

## Why "considerable taxes" is likely a mis-description

1. SAFE's own Q&A says the USD 50,000 convenience amount is an **administrative
   simplification threshold**, not a tax and not a hard cap [S01](https://www.safe.gov.cn/ningxia/2022/0929/1997.html).
2. The bank's obligation under Art. 59 is to verify the **source** of the RMB, including
   tax evidence [S03](https://www.safe.gov.cn/tianjin/2024/0621/2529.html). A request for tax
   clearance is easily misread as a demand for a conversion tax.
3. Chinese tax law taxes **income**, not the act of exchanging currencies [S23]; savings
   interest is temporarily exempt [S24](https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/grsds/200810/t288953.html).
4. Bank spreads and wire fees are **pricing**, not tax [S27], [S46].
5. U.S. FBAR/8938 are **information reports**, not tax returns [U06], [U26](https://www.fincen.gov/system/files/shared/ReportToCongress361.PDF).

Without the bank's written itemisation none of these can be ruled in or out for this
specific account (IR-011, IR-014). The practical instruction is therefore: ask the bank to
name the tax, its legal basis, its taxable base and rate, and to separate that from its rate
quote and fees.

## Verification performed

All 35 rows were checked against the linked official page; every numeric value above is
copied from an official text, and the four historical/expiry caveats (2014 spread caps,
2011/2014 CNH spreads, 2024 BOC promotion, 2026 FBAR non-adjustment) are explicitly labelled
so that stale numbers are not used as current prices. `scripts/verify.py` mechanically
rejects any UNVERIFIED row whose value cell is non-empty.
