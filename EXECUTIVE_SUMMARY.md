# Executive summary — getting CNY out of mainland China as a U.S. citizen

> **Current figures: 10 November 2026.** The first block was added by integration session
> `arena/fbbd3b22-china3`; the body below it is the consolidated view written by session
> `arena-0fbc51c7-china3` on the same day. Both are reconciled in the note on conventions below.
>
> **The answer in one paragraph.** Converting your own after-tax CNY principal into USD triggers
> no Chinese conversion tax in any instrument checked here. It costs bank spread plus the 1‰
> personal wire fee (capped at CNY 260) and a CNY 150 cable charge: **$53.42 on $10,000 and
> $901.30 on $400,000**, which is 0.534% falling to 0.225%, computed from the 2026-11-10 Bank of
> China board. The number that should drive the plan is not the exchange rate but the U.S.
> reporting penalty: a willful FBAR violation is capped at the greater of $165,353 or **50% of
> the account balance** (31 U.S.C. §5321(a)(5)(C)), i.e. $200,000 on a $400,000 balance. Fix
> reporting first, choose the route by the documents you can produce, and never split quotas.
>
> **Two corrections to earlier passes.** (1) The emigrant property transfer is **not** staged —
> SAFE 汇发〔2014〕2号 §6 cancels the PBC [2004] No.16 art. 6 instalment requirement and the
> over-RMB-500,000 head-office filing, so `cost-tables.html` route M03 ($1,025.39 at $400,000)
> overstates it by three wire fees. (2) Chinese FX fines under State Council Order 532 arts. 39
> and 45 are **30% or less** of the amount in an ordinary case, rising to 30%–100% only where the
> case is serious — a ceiling, not the floor an earlier pass described.
>
> Machine-readable register: `data/verify_2026.csv` (16 records: official URL, verbatim quote,
> fetch timestamp). Checks: `python3 scripts/verify_dashboard.py`. Live pages:
> [`index.html`](index.html) (dashboard) and [`verify-2026.html`](verify-2026.html).
>
> **Note on the two cost conventions (why $53.42 and $53.47 both appear).** The two models divide
> the same half-spread by a different denominator. Dividing by the **ask** (this block) expresses
> the spread as a share of the CNY you spend: 0.2100%, i.e. $21.00 per $10,000. Dividing by the
> **midpoint** (the consolidated model below) expresses it as a share of the USD you receive:
> 0.210447%, i.e. $21.05. The difference is $0.05 at $10,000 and $1.79 at $400,000 — a convention,
> not a fact. Everything else (wire 0.1% capped at CNY 260, cable CNY 150, no PRC conversion tax)
> agrees to the cent.


Prepared by integration session `session-c703e38c` · 2026-11-07 (UTC) · public, official-source research only.
Live version: [`deep-executive-summary.html`](deep-executive-summary.html) on the GitHub Pages site.
Consolidated by session `arena-0fbc51c7-china3` · 2026-11-10 (UTC) · official-source research only.
Live dashboard: [`index.html`](index.html) · consolidated summary: [`cn3-summary.html`](cn3-summary.html) · full figures: [`cn3-cost.html`](cn3-cost.html) ·
verification: [`cn3-review.html`](cn3-review.html) · sources: [`cn3-sources.html`](cn3-sources.html).
This replaces the earlier executive summaries as the current consolidated view. The prior versions
remain at [`deep-executive-summary.html`](deep-executive-summary.html),
[`research/s436-executive-summary.md`](research/s436-executive-summary.md) and in git history.

---

## 1. The question

A U.S. citizen has CNY sitting in a mainland-China bank account. They believe turning it into USD
means "paying a considerable amount of taxes". They want every lawful way to convert CNY to USD,
the pros and cons of each, an itemised breakdown of the conversion penalty, and the cost of moving
amounts from USD 10,000 to USD 400,000 in USD 10,000 steps.

## 2. The short answer

**No official source imposes a Chinese tax on converting your own savings.** The PRC Individual
Income Tax Law taxes nine categories of *income*; none of them is the act of exchanging your own
money. What the conversion actually costs is:

| Layer | Size (verified) | Paid to | Source |
|---|---|---|---|
| Bank FX spread, one way | **0.210447%** of the amount | Your Chinese bank | [BOC board](https://www.boc.cn/sourcedb/whpj/) |
| Wire fee | 0.1% of the CNY amount, **min CNY 50, max CNY 260** per transfer | Your Chinese bank | [BOC tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html) |
| Cable / telecom | **CNY 150** per transfer (CNY 80 to HK/Macau/Taiwan) | Your Chinese bank | same tariff |
| Correspondent bank deduction | *blank — not published* | Intermediary bank | same tariff |
| U.S. receiving-bank fee | *blank — not published* | Your U.S. bank | — |
| PRC tax on the conversion | **none found** | — | [IIT Law](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html) |
| **U.S. IRC §988 gain** | **≈6.94% of the USD received** (2024 basis), taxed as ordinary income | IRS | [26 USC §988](https://www.law.cornell.edu/uscode/text/26/988) |

So the "considerable tax" is almost certainly the **U.S.** tax on the currency gain, not a Chinese
charge. §988(e)(2) exempts a personal transaction only where the gain is **USD 200 or less**; above
that, the *whole* gain is ordinary income. At today's rate of 6.6903 CNY/USD, CNY acquired at the
IRS 2024 yearly average of 7.189 produces a gain of 6.94% of the dollars you receive — about
**1.67% of the amount** at a 24% marginal rate, and more in higher brackets.

## 3. What it costs, verified

Bank of China board read 2026-11-10 07:32:39 (ask 6.6903, bid 6.6622). "Bank cost" = spread + wire
+ cable. "U.S. tax" = 24% of the §988 gain at the 2024 average rate.

| Amount | Bank cost (W1) | Cost % | U.S. §988 tax* | **All-in** | All-in % |
|---|---|---|---|---|---|
| $10,000 | $53.47 | 0.535% | $166.49 | **$219.96** | 2.20% |
| $50,000 | $166.51 | 0.333% | $832.44 | **$998.95** | 2.00% |
| $100,000 | $271.73 | 0.272% | $1,664.88 | **$1,936.61** | 1.94% |
| $200,000 | $482.18 | 0.241% | $3,329.75 | **$3,811.93** | 1.91% |
| $300,000 | $692.62 | 0.231% | $4,994.63 | **$5,687.25** | 1.90% |
| $400,000 | $903.07 | 0.226% | $6,659.51 | **$7,562.58** | 1.89% |

The bank cost *falls* in percentage terms as the amount grows because the CNY 260 wire cap binds at
about USD 38,900 and the cable fee is fixed.

Every other lawful route, at USD 400,000 (known cost / calendar years needed):

| Route | Cost at $400k | Years |
|---|---|---|
| Wire out foreign currency already in your FX account (W7) | **$61.28** | 1 |
| Documented current-account income, one wire (W1) | **$903.07** | 1 |
| Emigrant / inheritance transfer after approval (W3/W4) | **$903.07** | 1 |
| Resident USD 50,000 convenience amount (W2) | $1,332.05 | 8 |
| Carry USD cash by hand, 40 trips (C1) | $841.79 | 40 |
| UnionPay ATM abroad (A1) | $4,486.50 | 27 |
| Visa/Mastercard ATM abroad (A2) | $10,014.50 | 27 |
| Offshore CNH in Hong Kong (O1) | *blank — no official price* | — |
| Licensed fintech (P1) | *blank — no official price* | — |

## 4. Least tax, least penalty — the actual ranking

1. **Any part of the balance already in USD: wire it out first (W7).** No CNY is disposed of, so
   there is no §988 gain at all, and the cost is the wire plus cable.
2. **Documented current-account income: one bank conversion and one wire (W1).** Lowest total cost
   among conversion routes; no annual amount limit if the bank accepts the source documents. The
   USD 50,000 figure is a documentation threshold, not a cap and not a tax — SAFE says so expressly:
   「年度便利化额度不是个人每年购汇或者结汇的限额」.
3. **Emigrant property transfer (W3)** if you moved abroad and cancelled your mainland hukou;
   **inheritance transfer (W4)** for inherited money. Since Huifa [2014] No. 2, the two-year staged
   payout and the >RMB 500,000 record-filing are gone, so this can be one remittance.
4. **Property-sale proceeds (W5)** are cheap to convert and expensive to own: the PRC taxes the gain
   at 20%, which dwarfs the FX cost.
5. **Company dividends (W8)**: 20% PRC dividend tax before any treaty relief, plus the same wire cost.
6. **Never** split quotas, use an underground bank, or convert through stablecoins. Each is
   prohibited, each carries a statutory fine of up to 30% (30%–100% if serious), and §988 still
   applies on top.

**Tax does not depend on the rail.** §988 follows the currency, not the bank, the ATM, Hong Kong or a
relative. What changes the tax is (a) the acquisition rate you can document, and (b) how many tax
years you spread the conversion across.

## 5. The requirements list (what "full" means here)

| # | Requirement | Status in this repository |
|---|---|---|
| 1 | List as many CNY→USD methods as possible | 17 methods, [`cn3-methods.html`](cn3-methods.html) |
| 2 | Pros and cons of every method | Per-method, with legality and requirements |
| 3 | Break down the conversion penalty | Seven layers, [`cn3-tax.html`](cn3-tax.html) |
| 4 | Costs at every USD 10,000 step to 400,000 | 40 × 17 = 680 rows, [`cn3-cost.html`](cn3-cost.html) |
| 5 | Exact step-by-step for each method | [`cn3-steps.html`](cn3-steps.html) |
| 6 | Every value traced to an official source | 23 sources, [`cn3-sources.html`](cn3-sources.html) |
| 7 | Unverifiable values blank, not guessed | 24 flags, [`cn3-review.html`](cn3-review.html) |
| 8 | Machine-checkable verification | `scripts/verify_cn3.py` re-derives all 680 rows |
| 9 | Clean mobile-first dashboard | [`index.html`](index.html) + 6 category pages |
| 10 | Executive summary | this file |

## 6. What you must confirm before acting (four facts)

1. **Source of the money** — salary, inheritance, property sale, company dividend, or untraceable
   savings. This alone selects the route.
2. **Your classification** — 境内个人 (Chinese citizen, or a foreigner resident in China for one
   continuous year) or 境外个人. It decides whether the USD 50,000 convenience amount applies.
3. **Acquisition dates and rates of the CNY** — this sets the §988 basis and therefore the only large
   tax number.
4. **What has been filed** — FBAR (aggregate > USD 10,000) and Form 8938 (USD 50,000/75,000 single,
   USD 100,000/150,000 joint, higher if living abroad).

## 7. Irregularities and corrections published

Two figures from earlier layers in this repository were wrong against the primary text and are
corrected here, not silently changed:

- **The emigrant-property payout is no longer staged.** Huifa [2014] No. 2 Art. 6(2) —
  「取消移民财产转移分次汇出的要求」 — repealed the two-year staging in PBC [2004] No. 16 Art. 6.
  Tables that still price the emigrant route with a two-year stage are superseded.
- **The BOC personal transfer tariff is effective 2014-11-01**, not 2024-11-01.

Twenty-seven further flags — every blank, every assumption, the residency question, the missing
U.S. bank fee, the unverified treaty rate, the PRC absence-of-provision finding — are listed with
their handling on [`cn3-review.html`](cn3-review.html). None of them blocks the analysis; each is
marked *needs review*.

## 8. Method and limits

- **Freshly fetched on 2026-11-10:** BOC FX board; BOC personal transfer tariff; BOC ATM tariff
  (effective 2026-11-11); SAFE 2022 convenience-amount Q&A; the personal-FX implementation rules
  (Huifa [2007] No. 1, as amended); the overseas-ATM cash notice (Huifa [2017] No. 29); Huifa [2014]
  No. 2; SAFE 2025 watch-list Q&A; SAFE 2026 foreign-individual salary Q&A; the FX Regulations (State
  Council Order 532); PBC [2004] No. 16; the PRC Individual Income Tax Law; IRS yearly average rates;
  26 USC §988; 31 CFR 1010.821; the IRS 8938/FBAR comparison; IRS gifts from a foreign person.
- **Carried forward** from prior sessions' registers, with the official URL and recorded excerpt:
  the cash-carry rule, CBP currency reporting, the tax-recordal rule, the 2026 virtual-currency
  notice, and the split-transaction enforcement cases.
- **Blank by design:** U.S. receiving-bank fee, correspondent deduction, card-network spread, PRC
  property-gain tax, treaty dividend rate, offshore CNH price, fintech price.
- **This is research, not advice.** Tax outcomes depend on facts this pack does not have. Confirm with
  a qualified U.S.–PRC tax adviser before converting.
