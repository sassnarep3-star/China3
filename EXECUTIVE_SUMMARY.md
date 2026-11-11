# Executive summary

**Current integration:** 2026-11-11. **Live dashboard:** https://sassnarep3-star.github.io/China3/

**FX snapshot:** Bank of China board published **2026/11/11 15:30:04 Beijing** — USD buying 6.6606, selling 6.6886 CNY/USD ([S01](https://www.boc.cn/sourcedb/whpj/enindex_1619.html)). Costs below are dated estimates, not execution quotes.

## Bottom line

1. **No official source reviewed imposes a standalone Chinese tax merely on converting CNY or wiring your own principal.** The bank's document request can look like a “conversion tax,” but the sources distinguish conversion/remittance from Chinese income tax on the money's origin and from U.S. tax/reporting. The actual item behind the quoted “considerable taxes” remains unknown ([S04](https://www.safe.gov.cn/tianjin/2026/0713/3088.html), [S17](https://www.safe.gov.cn/safe/2008/0806/5321.html); flag U02).
2. **The least-penalty route is normally the lawful route that matches the money's documented origin.** For a foreign passport holder with legitimate Chinese current-account income, that is generally source documents + tax evidence → buy USD → one own-name international wire. If the balance is already foreign currency, wire it without converting. Other origins have dedicated routes; gifts or undocumented money have no verified route in this research.
3. **Published bank cost is modest relative to tax and compliance exposure.** At the current BOC snapshot, convert-and-wire costs an estimated **$53.36 on $10,000** and **$898.54 on $400,000**, excluding intermediary/receiving fees and all personal taxes ([S01](https://www.boc.cn/sourcedb/whpj/enindex_1619.html), [S02](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html)). Bank of America says an incoming wire **may** cost $15; the account's fee schedule controls ([S41](https://info.bankofamerica.com/en/digital-banking/wire-transfers)).
4. **A U.S. passport alone does not confer the annual $50,000 ID-only purchase convenience amount.** SAFE says foreign permanent-resident-ID holders receive it. It is a processing convenience amount, not a universal cap and not a tax ([S05](https://www.safe.gov.cn/tianjin/2024/0621/2529.html), [S06](https://www.safe.gov.cn/ningxia/2022/0929/1997.html)). Do not split through other people.
5. **Large exposures are separate from the wire fee:** unpaid Chinese income tax and late-payment charges; possible U.S. §988 currency gain; FBAR/Form 8938/Form 3520 reporting; and penalties for prohibited channels. A willful FBAR maximum is the greater of the inflation-adjusted amount or 50% of the account balance ([S31](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821), [S38](https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm)).

## Cost at a glance

Known BOC-side components only. Currency-gain columns are **gain, not tax**, using the stated IRS annual average as an illustrative acquisition rate; actual basis and personal-transaction treatment are unknown.

| Amount | Already USD: wire only | Convert + one wire | $50k/year convenience scenario | Gain if CNY acquired at 2024 average | Gain at 2025 average |
|---:|---:|---:|---:|---:|---:|
| $10,000 | $32.43 | **$53.36** | $53.36 (1 year) | $696.06 | $617.76 |
| $50,000 | $61.30 | $165.95 | $165.95 (1 year) | $3,480.32 | $3,088.79 |
| $100,000 | $61.30 | $270.61 | $331.91 (2 years) | $6,960.63 | $6,177.58 |
| $200,000 | $61.30 | $479.92 | $663.82 (4 years) | $13,921.27 | $12,355.17 |
| $300,000 | $61.30 | $689.23 | $995.72 (6 years) | $20,881.90 | $18,532.75 |
| $400,000 | $61.30 | **$898.54** | $1,327.63 (8 years) | $27,842.54 | $24,710.34 |

Every $10,000 increment for every priced route: [Costs](dashboard/costs.html) · [machine-readable data](data/e347_costs.csv). Provider routes L12/L13 remain blank at every increment because neither cited official provider page publishes a numeric fee/execution rate.

## Which lawful route matches the money?

| Money / situation | Route | Essential path | Official / first-party source |
|---|---|---|---|
| Already USD or other FX in your account | L03 | Passport → instruct own-name outward remittance → pay wire fee | [SAFE](http://m.safe.gov.cn/safe/file/file/20200831/f0127756271c43ef9b3908d5d157bd91.pdf) |
| Unused CNY from your own FX conversion within 24 months | L02 | Passport + original exchange slip → reconvert → wire | [SAFE](https://www.safe.gov.cn/tianjin/2026/0917/3134.html) |
| Legitimate Chinese salary, fees or other current-account income | L01 | Source documents + tax evidence → buy USD → one wire | [SAFE](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) |
| Eligible after-tax Chinese salary; own-name recipient | L12 Wise | Verify identity/tax records → fund from bank app (max CNY 300,000/transfer) → own account; fee/FX blank | [Wise](https://wise.com/help/articles/2955298/guide-to-cny-transfers) |
| Passport holder wanting overseas cash pickup | L13 Western Union | Partner bank → verify transaction → pay quoted fee → cash pickup; bank delivery unavailable; fee/FX blank | [Western Union](https://www.westernunion.com/cn/en/send-money.html) |
| Chinese home-sale proceeds | L04 | Registered sale/title documents + tax certificate → bank conversion/remittance, capped at price less taxes | [SAFE guide](https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf) |
| Inheritance | L05 | Inheritance/property/tax documents → SAFE approval → own-name overseas account | [PBOC](http://m.safe.gov.cn/safe/2004/1116/5461.html), [SAFE](https://www.safe.gov.cn/tianjin/2024/0903/2594.html) |
| Pre-emigration property; former mainland hukou | L06 | Hukou cancellation/settlement/property/tax documents → SAFE approval → remit once or in instalments | [PBOC](http://m.safe.gov.cn/safe/2004/1116/5461.html), [SAFE](https://www.safe.gov.cn/tianjin/2024/0903/2594.html) |
| Foreign permanent-resident-ID holder | L07 | Up to $50,000/calendar year on ID; above it use documented route | [SAFE](https://www.safe.gov.cn/tianjin/2024/0621/2529.html) |
| Current-account CNY sent offshore before conversion | L08 | Bank offers cross-border RMB → own offshore account → convert there; both price components blank | [PBOC Beijing](http://beijing.pbc.gov.cn/beijing/132026/3660457/index.html) |
| Dividend from your Chinese company | L09 / L09T | Profit resolution + tax filing → 20% statutory scenario or conditional 10% treaty-cap scenario → remit | [Treaty Art. 9](https://www.irs.gov/pub/irs-trty/china.pdf), [IIT law](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html) |
| Small cash needs abroad | L10 ATM | Mainland UnionPay card → observe CNY 10,000/card/day and CNY 100,000/person/year | [SAFE](https://www.safe.gov.cn/hubei/2019/0305/851.html) |
| Lawfully purchased FX banknotes | L11 cash | ≤$5,000/trip; $5,000–10,000 with bank permit; declare >$10,000 entering U.S. | [SAFE](http://www.safe.gov.cn/hebei/2019/0521/1366.html), [CBP](https://www.cbp.gov/travel/international-visitors/money-monetary-instruments) |
| Gift or undocumented origin | **No verified route** | Obtain bank's written determination; do not invent a purpose or use another person's quota | [SAFE](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) |

[All methods, pros/cons](dashboard/methods.html) · [numbered steps for every route](dashboard/steps.html) · [other bank tariffs, U.S. receiving fees and SAFE enforcement cases](g8d8-summary.html).

## Questions and missing information before a decision

The [Decide register](dashboard/decisions.html) contains 36 questions, answers, missing items and discovery steps. The decisive gaps are:

- **Origin and character of every major deposit:** salary, property sale, inheritance, emigrant property, gift, business profit, prior foreign-currency conversion, or existing FX.
- **The bank's written account classification:** 境外个人 versus 境内个人; two instruments use different definitions.
- **The exact “considerable tax” quote:** tax name, legal basis, rate, base, assessing office, and whether it is actually a document/compliance charge.
- **Chinese tax evidence and filing history:** paid, exempt, withheld, unpaid, or uncertain. If unpaid, review [late tax, surcharges and U.S. procedures](6da0-settle-up.html).
- **CNY acquisition dates/rates and U.S. returns:** §988 basis, personal-transaction analysis, worldwide-income reporting, foreign tax credit, FBAR, Form 8938 and Form 3520.
- **Actual transaction quotes:** sending-bank rate/fees, provider fee/FX, intermediary deductions and receiving-account fee. Unknown values are blank, never zero.
- **Route-specific eligibility:** hukou history, property documents, inheritance documents, treaty residence/beneficial ownership, or provider work/tax-record requirements.

## Avoid

Relatives' quotas, private swaps/underground banks, false invoices or purposes, crypto conversion in mainland China, excessive cash, and borrowed cards. Official rules provide fines up to 30% and 30%–100% in serious cases for several violations ([State Council Order 532](https://www.safe.gov.cn/safe/2008/0806/5321.html)). The [G8D8 enforcement register](g8d8-enforcement.html) adds 40 actual SAFE cases rather than hypothetical penalty estimates.

This is dated general research from public official and first-party sources, not legal, tax or banking advice. Earlier summaries and parallel research layers remain in the [Archive](dashboard/archive.html); they use older FX snapshots.
