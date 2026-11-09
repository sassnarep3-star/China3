# Executive summary — China money (CNY → USD)

Prepared by integration session `session-c703e38c` · 2026-11-07 (UTC) · public, official-source research only.
Live version: [`deep-executive-summary.html`](deep-executive-summary.html) on the GitHub Pages site.

## The question

A U.S. citizen has CNY stuck in a mainland-China bank account and wants the best way to get
the money out / convert CNY→USD with the least tax penalties, reporting that conversion
"incurs considerable taxes". The brief asks for as many conversion methods as possible, pros
and cons of every method, a deep breakdown of the conversion penalty, a full requirement
list, verification from official sources with links, flagged irregularities, and a live
GitHub Pages dashboard.

## The short answer

**No official source reviewed establishes a Chinese "conversion tax" on converting one's own
CNY savings principal into USD.** The costs that actually bite are:

1. **Chinese tax on the *source* of the funds, and the tax-clearance documents a bank needs
   before it will sell FX.** PRC IIT is 3%–45% on comprehensive income and 20% on interest,
   dividends, property transfers and incidental income; savings-deposit interest has been
   temporarily exempt since 2008-10-09. A foreign individual buying FX must present evidence
   of the RMB source including tax evidence; a single outbound payment above USD 50,000 in
   listed categories requires a tax-filing form (备案). A document request is not a levy.
   [S23](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html)
   [S24](https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/grsds/200810/t288953.html)
   [S03](https://www.safe.gov.cn/tianjin/2024/0621/2529.html)
   [S21](https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html)
2. **Bank pricing.** The customer buy/sell spread has been deregulated since 2014-07-01, so
   the bank sets its own price. Bank of China's published personal e-banking wire fee is 1‰
   (min ¥50, max ¥260) plus a cable fee of ¥80 (HK/Macau/Taiwan) or ¥150 (elsewhere);
   correspondent/overseas bank charges are passed through at actual cost. If conversion
   happens offshore (CNH), an onshore/offshore basis applies — HKMA has officially measured
   it at 1.94% in a stress episode.
   [S27](https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/2810732/index.html)
   [S46](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html)
   [S47](https://www.boc.cn/cbservice/cb3/cb33/200807/t20080701_852.html)
   [S50](https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201203/chapter4.pdf)
3. **U.S. tax and information-reporting exposure — the largest single risk.** A U.S. citizen
   is taxed on worldwide income (so CNY account interest is reportable even though China
   exempts it). FBAR is required once aggregate foreign accounts exceed $10,000 at any time;
   the willful penalty is the greater of **$165,353 or 50% of the account balance**.
   Form 8938 ($10,000 + up to $50,000 additional; 40% understatement penalty) and Form 3520
   (5%/month up to 25% of a foreign gift) are independent. The 2026 inflation adjustment was
   cancelled, so the 2025 amounts still apply.
   [U01](https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-about-international-individual-tax-matters)
   [U06](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements)
   [U20](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821)
   [U21](https://www.federalregister.gov/documents/2026/07/07/2026-13629/no-adjustment-to-civil-monetary-penalty-amounts)
   [U09](https://www.irs.gov/businesses/gifts-from-foreign-person)

## The cost answer, in numbers

The brief asks for the cost at every USD 10,000 step from 10,000 to 400,000, for every
method. `deep-costs.html` (520 rows) does that. On the primary lawful route — foreign
individual, documented current-account income, one wire — the arithmetic is:

| Amount | All-in cost (base) | Effective % | Low | High |
|---|---|---|---|---|
| USD 10,000 | USD 99 | 0.995% | USD 53 | USD 657 |
| USD 50,000 | USD 297 | 0.593% | USD 166 | USD 1,086 |
| USD 100,000 | USD 507 | 0.507% | USD 272 | USD 1,586 |
| USD 200,000 | USD 928 | 0.464% | USD 482 | USD 2,586 |
| USD 400,000 | USD 1,769 | 0.442% | USD 903 | USD 4,586 |

Inputs: SAFE central parity 6.7188 (2026-11-09), BOC 现汇买入 6.6638 / 卖出 6.6919 the same
morning (measured spread 0.42%), BOC personal wire tariff 1‰ with a CNY 50–260 cap plus
CNY 150 cable, and the USD 25 full-amount guarantee. The low case is half the measured
spread plus the wire fee; the high case is a 1.00% spread plus USD 500 of documents. The
percentage falls as the amount rises because the wire fee is capped.

For comparison at USD 400,000: an unlawful route carries a 30%–100% fine plus confiscation
(USD 120,000–400,000), and a single willful FBAR violation is capped at the greater of
USD 165,353 or 50% of the balance (USD 200,000). **Compliance is worth two orders of
magnitude more than any rate negotiation.**

**What is still not determined:** tax on the source of the money (it depends on whether the
balance is salary, interest, a property gain, a gift or inheritance — see the tax table on
the cost page) and the user's actual US filing history. Those stay conditional (IR-014,
IR-018).

## The single most important structural finding

A U.S. citizen holding a passport is generally an **境外个人 (foreign individual)** under
PBOC Decree [2006] No. 3 Art. 37. Under SAFE's Current Account Guidelines Art. 59, a foreign
individual purchases FX with an ID plus evidence of the **source** of the RMB (including a
tax certificate), and SAFE's own Q&A handbook states that foreign-individual FX purchase has
**no annual quota limit**. Holders of a foreign permanent residence ID get the USD 50,000
convenience amount instead. So if the CNY is legitimately earned, tax-documented income, the
USD 50,000 "annual quota" that dominates online advice may not be the binding constraint at
all. [S05](https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm)
[S03](https://www.safe.gov.cn/tianjin/2024/0621/2529.html)
[S43](https://www.safe.gov.cn/chongqing/file/file/20190311/87806e211bb74eb4a44e71395c31cda9.pdf)

**Caveat (IR-007):** the 2008 State Council FX Regulation Art. 52 defines 境内个人 to include
foreigners resident in China for ≥1 year, and the PBOC measure says the ID used at account
opening determines the classification. The account-opening bank must confirm its system
classification in writing. [S07](https://www.safe.gov.cn/safe/2008/0806/5321.html)

Also note: SAFE explicitly says the USD 50,000 convenience amount is **not a legal cap** and
**not a tax**; genuine, documented current-account transactions have no official amount
limit. There is a *separate* USD 50,000 same-day threshold for outward remittance evidence.
[S01](https://www.safe.gov.cn/ningxia/2022/0929/1997.html)
[S02](https://www.safe.gov.cn/tianjin/2024/0229/2402.html)

## Recommended sequence (least penalty first)

1. **Classify the account holder and the money.** Which ID opened the account? Salary,
   business profit, property sale, inheritance, gift, or previously converted FX? Collect
   statements and Chinese tax receipts.
2. **Get the bank's written rule and checklist.** Ask whether it will process under Art. 59
   (foreign individual, source-of-funds evidence), Art. 57 (current-account purchase above
   the convenience amount), or a capital-account approval route.
3. **Clear the tax-document precondition** (税务凭证 / 备案表), not a "conversion tax".
4. **Demand an all-in written quote**: customer rate, reference mid-rate and timestamp,
   spread, conversion charge, wire fee, cable fee, correspondent charges, receiving fee and
   expected net USD.
5. **Use one lawful channel; never split.** Do not use relatives' quotas, underground banks,
   false invoices, or crypto/USDT. Illegal routes convert a paperwork problem into 30%–100%
   fines plus Criminal Law Art. 225 exposure (1–5× illegal-gain fine; up to 5+ years).
6. **Fix U.S. reporting before and after**: FBAR, Form 8938, worldwide income including CNY
   interest, the $200 personal FX-gain rule, and Form 3520 if the funds are a gift. If prior
   years were missed, use IRS Streamlined / delinquent FBAR procedures.

## Deliverables and counts

| Deliverable | Where |
|---|---|
| Executive summary | this file; `deep-executive-summary.html` |
| Full requirement list & coverage | `deep-executive-summary.html`; `COORDINATION.md` task board T1–T9 |
| China framework, 50 line-by-line rules | `research/china-framework.md`; `deep-china-rules.html`; `data/china_rules.csv` |
| U.S. tax & reporting, 28 line-by-line rules | `research/us-tax.md`; `deep-us-tax.html`; `data/us_rules.csv` |
| 35 conversion channels with pros/cons | `research/channels.md`; `deep-channels.html`; `data/channels.csv` |
| 35-component penalty breakdown | `research/penalty-breakdown.md`; `deep-penalty.html`; `data/penalty.csv` |
| 22 sourced findings + deep analysis | `research/analysis.md`; `deep-findings.html`; `data/findings.csv` |
| 23 flagged irregularities, all with links | `deep-review.html`; `data/flags.csv` |
| Official source register (84 sources) | `deep-sources.html`; `data/sources.csv`; `data/deep_sources.json`; `research/sources.md` |
| Per-task sources, verification, irregularities | `COORDINATION.md`; `research/*.md` |
| Live GitHub Pages dashboard | clean landing page + 10 category subpages, filterable tables |

## Verification statement

Every table row carries at least one direct link to an official site (SAFE, PBOC, State
Council, State Taxation Administration, courts/CSRC, HKMA, Bank of China, IRS, FinCEN,
eCFR, Federal Register, Treasury, or this repository's own project record). Values that
could not be confirmed from an official source are left **blank** and marked **UNVERIFIED**,
and appear on the clearly labelled "Flagged for Review" page. No value was inferred or
filled. `scripts/verify_deep.py` mechanically enforces row-level source links, official-domain
allowlisting, blank unverified values, HTML/CSV row-count agreement, all flagged ids being
published, and zero broken local links. `research/sources.md` records how each source was
verified. Chinese-language official documents are paraphrased in English; the linked original
controls (IR-016).

## Important irregularities (non-blocking)

- `银发〔2026〕42号` (in force 2026-02-06) **repealed** `银发〔2021〕237号`; advice citing the
  2021 notice is stale (IR-004).
- Conflicting official definitions of 境内个人 / 境外个人 (IR-007).
- `汇发〔2009〕56号` and `汇发〔2015〕49号` are both repealed; the current authority is the
  2020 Current Account Guidelines (IR-006).
- OMB M-26-11 cancelled the 2026 FBAR inflation adjustment (IR-008).
- No signed U.S.–mainland-China FATCA IGA was found — only a 2014 "agreement in substance"
  (IR-009).
- No official source establishes a conversion tax; the current bank spread, CNY/CNH basis,
  correspondent fees and the account's total cost could not be verified (IR-011, IR-012,
  IR-015).
- The brief's `session-<id>/<task>` branching is not possible in this Arena environment; the
  work is all on the fixed branch, and a parallel session's board/PR/deployment record is
  preserved verbatim in `COORDINATION.md` (IR-001, IR-013).

This is informational research, not legal, tax or banking advice. No manual input was
requested; all conclusions are conditional on case facts that were not provided (IR-014,
IR-018).
