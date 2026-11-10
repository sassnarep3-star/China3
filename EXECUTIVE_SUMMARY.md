# Executive summary — China money (CNY → USD)

> **Canonical edition, 2026-11-10 (session `arena/2c8d441e-china3`).** An independent pass re-fetched 16
> official documents on 10 November 2026 and re-derived the whole cost ladder from the 17:39:58 Beijing
> board (bid 6.6571 / ask 6.6851). Its answer, in one paragraph: there is **no PRC tax on converting CNY to
> USD** in any instrument reviewed; the charges that feel like one are the bank spread (0.2094% half-spread),
> the 1‰ wire tariff capped at ¥260 plus ¥150 cable (a total of **$53.38 on $10,000** and **$899.01 on
> $400,000**), the PRC income tax on whatever created the money (20% on property gains, interest, dividends),
> and — the only genuine conversion tax — the **U.S. §988 gain** on disposing of the CNY: **7.0093%** of the
> dollars received at a 2024-average cost basis, equal to **$10,373.79** of federal tax at 37% on $400,000 and
> unavoidable by changing channel. For a U.S. passport holder the decisive rule is SAFE's: the annual
> convenience amount belongs to a **外国人永久居留身份证** holder, and everyone else buys FX from lawful
> current-account RMB income with ID **plus source-of-funds materials including tax documents**
> ([2026-07-13 Q&A](https://www.safe.gov.cn/tianjin/2026/0713/3088.html), [2024-06-21 Q&A](https://www.safe.gov.cn/tianjin/2024/0621/2529.html)).
> Start at [`c3x-summary.html`](c3x-summary.html); method and formulas in
> [`research/c3x-verification.md`](research/c3x-verification.md).

**Final integration review:** 2026-11-10 · **Live guide:** `index.html` · **Full evidence schedule:** `schedule-dashboard.html`

Parallel integration work is preserved at `verify-2026.html` (17 verbatim source records), `a15-review.html` (independent safety review), `guide.html` (archived narrative) and `data/ladder_20261110.csv` (independent 40-row ladder).

**S775 audit addendum (2026-11-10):** an independent line-by-line pass catalogued **24 routes** (including the prohibited ones), registered **51 official sources** with fetch timestamps, re-derived the full **$10,000–$400,000 cost ladder** (40 steps) from the 2026-11-10 BOC board, and documented numbered step-by-step playbooks for every route. Its key verified results agree with the benchmark above: FX spread 0.2104%, personal wire 1‰ (¥50–¥260) + ¥150 cable, **$50.93 total at $10,000** (excl. conditional OUR) rising to **$903.08 at $400,000**. Pages: `s775-dashboard.html`, `s775-cost-10k-400k.html`, `s775-methods.html`, `s775-steps.html`, `s775-penalties-tax.html`, `s775-flagged-review.html` (18 flagged items), `s775-sources.html` (51 sources). Gate: `python3 scripts/verify_s775_site.py`, CI `.github/workflows/s775-verify.yml`.

## Bottom line

For a U.S. citizen, the lowest-penalty lawful route is usually the **ordinary licensed-bank route that matches the documented origin of the money**, not a workaround. If the bank classifies the holder as a foreign individual (`境外个人`) and the balance is lawful, documented, already-taxed current-account RMB income, SAFE’s 2026 guidance says the bank can handle the FX purchase using valid ID and transaction/source evidence, including tax evidence. Eligibility cannot be established from citizenship alone. [SAFE, 2026-07-13](https://www.safe.gov.cn/tianjin/2026/0713/3088.html)

No official source reviewed establishes a separate PRC “conversion tax” on already-taxed personal principal. That is not the same as saying every conversion is tax-free: unpaid PRC source-income tax, U.S. worldwide-income obligations, and foreign-currency gain are separate questions. [SAFE source-income Q&A](https://www.safe.gov.cn/tianjin/2024/0621/2529.html) · [IRS Publication 54](https://www.irs.gov/publications/p54) · [26 U.S.C. §988](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm)

## Current published-cost benchmark

The integrated schedule uses Bank of China’s official board timestamped **2026-11-10 07:32:39**: USD spot buying **6.6622**, selling **6.6903**, board midpoint **6.67625** CNY/USD. [BOC board](https://www.boc.cn/sourcedb/whpj/enindex_1619.html)

For M01 (documented foreign-individual current-account income), the reproducible published-component estimate is:

| Target USD | FX half-spread | Personal wire + cable | Known cost | Net after known cost |
|---:|---:|---:|---:|---:|
| $10,000 | $21.00 | $32.42 | **$53.42** | $9,946.58 |
| $100,000 | $210.01 | $61.28 | **$271.29** | $99,728.71 |
| $400,000 | $840.03 | $61.28 | **$901.30** | $399,098.70 |

Sources for every amount: [BOC board](https://www.boc.cn/sourcedb/whpj/enindex_1619.html) and [BOC personal e-banking tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html). Formula: `U × (ask − bid/ask midpoint) ÷ ask + [clamp(0.001 × U × ask, ¥50, ¥260) + ¥150] ÷ ask`.

These are **not all-in quotes**. Receiving/intermediary charges, account-specific execution, any optional full-amount service, underlying tax, and professional/compliance costs are not known and remain blank or disclosed. In particular, the inherited model’s automatic **$25 personal-wire OUR charge was removed**: its source is BOC’s corporate trade-services tariff and describes an optional service with conditions. [BOC corporate tariff, notes 1–2](https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html)

If the account already contains USD, no CNY→USD spread applies to that balance; the same personal wire/cable benchmark is **$32.42 at $10,000** and **$61.28 at $100,000–$400,000**, before unquoted receiving/intermediary charges. Eligibility and documentary review still apply.

## What may look like a “conversion penalty”

1. **FX spread:** the dated BOC one-way half-spread is about **0.2100%** against its own bid/ask midpoint. It is a benchmark, not the user’s guaranteed execution rate. [BOC](https://www.boc.cn/sourcedb/whpj/enindex_1619.html)
2. **Transfer charges:** BOC personal e-banking cross-border TT is **1‰, minimum ¥50, maximum ¥260**, plus **¥150** cable outside Hong Kong/Macao/Taiwan; agreements, discounts and local differences can apply. [BOC personal tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html)
3. **PRC tax/document gate:** a single outbound payment above USD 50,000 in listed categories generally requires tax recordal, subject to exceptions. Recordal is not itself a second tax; unpaid underlying tax is fact-dependent. [STA/SAFE Announcement 2013 No. 40](https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html)
4. **U.S. tax and currency gain:** U.S. citizens generally report worldwide income. Disposition of nonfunctional currency can be a §988 transaction. For a qualifying **personal** transaction, IRS Publication 525 says gain above $200 is capital gain; business/investment facts can produce a different §988 analysis. Acquisition basis and dates are missing, so this project does not invent a tax amount. [IRS Pub. 54](https://www.irs.gov/publications/p54) · [IRS Pub. 525](https://www.irs.gov/publications/p525) · [26 U.S.C. §988(c), (e)](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm)
5. **Reporting exposure:** FBAR generally applies when aggregate foreign financial accounts exceed **$10,000 at any time** in the year. Form 8938 has separate thresholds and does not replace FBAR. [IRS FBAR](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar) · [IRS comparison](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements)

## Route hierarchy

- **First:** wire an already-held USD balance if the bank accepts the account/remittance evidence.
- **Usually next:** M01, foreign-individual lawful current-account RMB income with ID, transaction/source evidence and tax evidence.
- **Only if the facts fit:** emigrant/inheritance property transfer, property-sale proceeds, re-conversion against an original FX memo, or company dividends. Do not relabel savings to fit a route.
- **If classified as a domestic individual:** the USD 50,000 annual convenience amount is simplified processing, not a universal legal cap. Genuine documented current-account transactions above it follow a documentary route. The schedule’s multi-year quota costs reuse today’s board and are scenarios, not forecasts. [SAFE Q&A](https://www.safe.gov.cn/ningxia/2022/0929/1997.html)
- **Do not use:** borrowed quotas/splitting, underground banks, false documents, or virtual currency to bypass controls.

## Exact action sequence

1. Establish the bank’s account-holder FX classification and obtain its current written checklist.
2. Match the balance to authentic source records: salary/service income, property sale, inheritance, company profit, gift, or original FX conversion.
3. Resolve source-income tax evidence and any required tax recordal/SAFE review before execution.
4. Obtain a live itemized quote: customer rate, timestamp, wire, cable, charge-bearer option, intermediary and receiving fees, and expected net USD.
5. Execute only the lawful route supported by those documents; keep the complete evidence and transfer trail.
6. Review U.S. income, §988 basis/holding-period facts, FBAR, Form 8938 and any foreign-gift reporting with a qualified cross-border tax professional.

## Deliverables

- `index.html` — clean landing page and the full M01 40-increment table.
- `schedule-cost-10k-400k.html` — **16 methods × 40 amounts = 640 rows**, mobile filters and per-row official links.
- `schedule-methods.html` — pros, cons, eligibility and prohibited routes.
- `schedule-steps.html` — step-by-step playbooks.
- `schedule-penalties.html` — tax, reporting and enforcement separated.
- `final-verification.html` and `schedule-flagged-review.html` — corrections, unknowns and irregularities.
- `research/final-integration-audit.md` — final audit and verification record.

For the documented foreign-individual current-account model (M01), the snapshot uses BOC's
USD selling rate `6.6924`, bid/ask midpoint `6.67835`, personal remittance tariff (1‰,
`¥50–¥260`) + `¥150` cable, and the published standard U.S. `OUR` option of `$25`. The
published-component result is `$78.41` at a `$10,000` target and `$926.02` at `$400,000`.
These are **not** a personalized all-in quote: receiving/intermediary fees, tax arrears,
eligibility, actual source documents and U.S. compliance/cure facts have no single official
number and are deliberately blank. The calculation and inputs are documented in
[`research/s436-cost-methodology.md`](research/s436-cost-methodology.md); all methods,
limitations and official source links are in
[`research/s436-methods-and-penalties.md`](research/s436-methods-and-penalties.md).

This is informational research, not legal, tax or banking advice. No manual input was
requested; all conclusions are conditional on case facts that were not provided (IR-014,
IR-018).

## Addendum — U.S. §988 currency-gain exposure (2026-11-10)

No Chinese "conversion tax" exists. The most likely candidate for the "considerable amount of taxes" the brief reports is a **U.S. tax on the currency gain embedded in the CNY itself** (IRC §988), not a Chinese fee. CNY acquired at the 2024/2025 IRS yearly averages (7.189 / 7.129) and converted at the recorded 2026-11-09 BOC selling rate (6.6919) carries a gain of about **6.9% / 6.1% of the USD received** — e.g. ≈$6,915 on $100,000 — before any China-side cost. Arithmetic, statute links and the full $10,000–$400,000 ladder: [`us-fx-gain.html`](us-fx-gain.html). Character and the $200 personal-transaction exclusion are conditional on facts only the account holder has (see `data/penalty.csv` P25; cross-check **X-11**). This does not change the recommended sequence — classify the funds, keep U.S. filings clean, use the narrowest lawful documentary route — it adds the missing U.S. line to the cost stack.

General educational research, not personalized legal, tax, immigration, investment or banking advice. Missing personal facts are flagged rather than inferred.
