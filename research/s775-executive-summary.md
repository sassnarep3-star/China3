# S775 Executive summary — CNY→USD repatriation for a U.S. citizen

**Live verification date: 2026-11-10.** All figures read from official sources this session
(register: `data/s775_sources.csv`; fetch timestamps included). Nothing below is inferred; where
a value cannot be confirmed from an official source it is left blank and flagged.

## The most important facts first

1. **There is no PRC tax on converting your own CNY to USD.** The "considerable taxes" premise is
   not established by any official source. The real, verified costs are: (a) the bank FX spread
   **0.2100%** of the USD amount at the 2026-11-10 BOC board (bid 6.6622 / ask 6.6903), (b) the
   BOC wire tariff **1‰ (min ¥50, max ¥260) + ¥150 cable**, and (c) any US tax consequence.
   ([S01](https://www.boc.cn/sourcedb/whpj/), [S03](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html), [S19](https://www.safe.gov.cn/safe/2008/0806/5321.html), [P11](data/s775_penalties.csv))
2. **The largest single exposure is usually the US side, not China.** Under **IRC §988**, currency
   gain/loss is measured against your **basis** (the CNY-per-USD rate when the CNY was acquired).
   Personal transactions are excluded from §988 and gains ≤$200 are excluded entirely;
   income-producing accounts are not "personal" and bear ordinary rates. Your basis was not
   provided — the cost tables show the gain **blank** and provide cohort sensitivities instead of
   guessing. ([S40](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm), [S42](https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates))
3. **Reporting duties dominate small amounts.** FBAR (FinCEN Form 114) is required when the
   aggregate foreign-account value **exceeds** $10,000 at any time in the year; penalties run
   $16,536 (non-willful) to the greater of $165,353 or 50% of the balance (willful), per
   `31 CFR 1010.821` current as of 2026-11-06. Form 8938 adds another threshold layer. A missed
   filing can exceed the entire conversion cost. ([S48](https://www.fincen.gov/report-foreign-bank-and-financial-accounts), [S49](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821), [S43](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements))
4. **The cleanest lawful route for most people is a personal bank wire** (M01): no approval needed
   up to US$50,000/day on ID documents; the annual US$50,000 convenience amount is **not** a hard
   limit — above it, transaction documents are required. ([S10](https://www.safe.gov.cn/ningxia/2022/0929/1997.html), [S13](https://www.safe.gov.cn/tianjin/2024/0229/2402.html))
5. **Big amounts have a dedicated lawful channel:** emigrant property transfer with SAFE approval
   (`汇发〔2014〕2号`) remits the approved amount in one or several instalments — the old two-year
   staging was cancelled. It requires mainland hukou history; a U.S. citizen by birth does not
   qualify. ([S14](https://www.safe.gov.cn/tianjin/2024/0903/2594.html))
6. **Illegal routes are catastrophic, not cheap:** illegal FX transfer or private trading draws
   fines up to 30% of the amount (30%–100% if serious) and, above the criminal thresholds
   (turnover ¥5,000,000 / gain ¥100,000), prison. Crypto conversion is prohibited by PBOC
   `银发〔2026〕42号`. ([S19](https://www.safe.gov.cn/safe/2008/0806/5321.html), [S39](https://www.hncourt.gov.cn/public/detail.php?id=176932), [S29](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html))

## Verified cost of the reference route (personal bank wire, one transfer)

| Amount | FX spread | Wire fee | Total (excl. OUR) | Total (incl. OUR) | Net USD |
|---|---|---|---|---|---|
| $10,000 | $21.00 | $32.42 | **$53.42** (0.53%) | $78.42 | $9,946.58 |
| $100,000 | $210.01 | $61.28 | **$271.29** (0.27%) | $296.29 | $99,728.71 |
| $400,000 | $840.02 | $61.28 | **$901.30** (0.23%) | $926.30 | $399,098.70 |

Arithmetic: spread = amount × (ask − mid)/ask with mid = (6.6903+6.6622)/2; wire fee =
(clamp(1‰ × CNY, ¥50, ¥260) + ¥150)/ask. OUR = US$25 per wire is **conditional** (corporate tariff
document; personal applicability must be confirmed with the branch). Intermediary and US
receiving-bank fees are **blank — no official schedule exists** (flag `S775-F06`).

## The decision framework

1. **What is the money?** Savings → M01/M02/M03/M04. Salary → M07–M09. Investment income → M10.
   Property → M05/M06/M15. Corporate → M16–M17. (Funds type not provided — `S775-F01`.)
2. **How much, and how fast?** Under US$50,000/day: bank wire on ID. Larger: documents; >US$50,000
   cross-border payments need the tax filing recordal (`S33`). Emigrant channel for large
   approved transfers (`S14`).
3. **What did you pay for the CNY?** If your basis is better than today's rate (6.6903), the §988
   gain is smaller or negative; a loss on a personal disposition is nondeductible. If the CNY sits
   in an interest-bearing investment account, the gain is ordinary income under §988(e)(3).
4. **Have you filed FBAR/8938 every year?** If prior years were missed, use the IRS streamlined
   procedures: SFOP 0% penalty (abroad) / SDOP 5% (US-based), non-willful only (`S45`).

## Flagged for review (full list: `data/s775_flags.csv`, page `s775-flagged-review.html`)

- `S775-F01`–`F04` (high): funds type, US basis, marginal rate, hukou history — unknown; never guessed.
- `S775-F05` (medium): OUR surcharge personal applicability — conditional.
- `S775-F06`–`F09` (medium): intermediary fees, cash price, CNH fee, exact 8938 penalties — blank.
- `S775-F10` (medium): capital vs ordinary characterisation of personal §988 gain — interpretation.
- `S775-IR-001/002` (process): Arena single-branch binding; cross-branch claim visibility.

## What this session changed in the repo

- Rebased onto `origin/main` (`e06ba6c`, PRs #23/#24/#26/#27/#29 merged) with an append-only
  `COORDINATION.md` resolution: 100% of sibling records kept, this session's block appended.
- All 51 registered sources were fetched live on 2026-11-10; the audit resolves the
  emigrant-staging, OUR-tariff, §988(e), FEIE-year, FBAR-threshold and penalty-ceiling conflicts
  documented in `research/s775-repo-audit.md`.
