# Executive summary

**Question.** A U.S. citizen has money sitting in a mainland China bank account. Converting
it to USD is believed to carry "a considerable amount of taxes". What are the lawful ways to
convert it, what does each one really cost, and what is the least-penalty path?

**Short answer.** There is no Chinese tax on converting CNY to USD. Converting **USD 400,000**
costs about **USD 1,663** — 0.42 % — and every figure in that number is printed on a bank's own
public web page. The "considerable amount" people describe is almost always something else:
income tax on whatever created the money, or a U.S. information-reporting penalty that starts
at **USD 165,353** and can reach **half the account balance**.

Live site: **https://sassnarep3-star.github.io/China3/** · priced dashboard: **/cost.html**

---

## The four numbers that decide everything

| # | Number | What it is | Source |
|---|---|---|---|
| 1 | **0.4004 %** | The bank's measured margin: its spot selling price vs its own reference price, same page, same minute | [boc.cn 外汇牌价](https://www.boc.cn/sourcedb/whpj/), 2026-11-09 09:15:45 |
| 2 | **USD 1,662.87** | All-in cost of converting USD 400,000, including the wire | derived from 1 + [boc.cn 费率表](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html) |
| 3 | **USD 165,353 / 50 %** | Maximum willful FBAR penalty: the greater of the fixed figure or half the balance | [31 CFR 1010.821](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821) |
| 4 | **USD 50,000** | Not a tax, not a cap — a documentation threshold above which evidence is required | [SAFE](https://www.safe.gov.cn/ningxia/2022/0929/1997.html) |

Numbers 2 and 3 differ by two orders of magnitude, and they are the whole story. The expensive
mistake in this project is a filing omission, not an exchange rate.

---

## The cost, in one line per size

| USD out | All-in cost | as % |
|---:|---:|---:|
| 10,000 | $72.46 | 0.72 % |
| 25,000 | $147.52 | 0.59 % |
| 50,000 | $261.47 | 0.52 % |
| 100,000 | $461.67 | 0.46 % |
| 200,000 | $862.07 | 0.43 % |
| 300,000 | $1,262.47 | 0.42 % |
| 400,000 | $1,662.87 | 0.42 % |

The wire fee caps at about USD 38,850 of value, so above that the marginal cost is exactly
0.4004 % — **about USD 4.00 per extra USD 1,000, at any size**. Full 40-row table at every
USD 10,000 step: [`COST_MODEL.md`](COST_MODEL.md) and `/cost-model.html`.

---

## The seven cost layers, separated

People conflate these. Only two of them are money you pay for converting.

| Layer | Amount | Base | When |
|---|---|---|---|
| PRC income tax on what created the money | 20 % flat on gains/interest/rent; 3–45 % on salary, mostly withheld | the **gain**, not the balance | when the income arose — unrelated to converting |
| The bank's FX margin | **0.4004 %** measured | the USD amount | at exchange |
| Bank wire + cable | 1 ‰, floor CNY 50, cap CNY 260, plus CNY 150 | per transfer | at remittance |
| SAFE filings (the form above USD 50,000) | a filing, no published fee | — | at application |
| U.S. income tax on the transfer | **none** | — | — |
| **U.S. information-reporting penalties** | up to USD 16,536 non-willful; **USD 165,353 or 50 % willful**; USD 60,000 Form 8938; 5 %/month Form 3520 | per report | years later, on silence |
| PRC enforcement fines | up to 30 % (30–100 % if serious); 20 % cash; 30 % private FX dealing | the amount | on enforcement |

---

## What actually is and is not true

**True, and sourced:**
- SAFE states there is no amount limit on genuine, lawful current-account FX business, and that
  the USD 50,000 figure is a *convenience* amount, "not the limit" on purchases
  ([safe.gov.cn, 2022](https://www.safe.gov.cn/ningxia/2022/0929/1997.html)).
- A U.S. person must file an FBAR when aggregate foreign accounts exceed USD 10,000 at any
  point in the year, whether or not the account earned anything
  ([irs.gov](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar)).
- A gift from a foreign person is excluded from U.S. gross income; above USD 100,000 it is an
  information return, not a tax ([irs.gov](https://www.irs.gov/businesses/gifts-from-foreign-person)).
- PRC individual income tax applies 20 % to property-transfer income on the gain
  ([IIT Law](https://shanghai.chinatax.gov.cn/zcfw/zcfgk/grsds/201809/t441789.html)).

**Not true, or not established:**
- ✗ There is no "conversion tax" in any official source reviewed.
- ✗ The USD 50,000 figure is not a cap on lawful current-account business — but it is also not
  a key that opens the capital account. Ordinary accumulated savings are not a current-account
  purpose, and individual outbound investment requires SAFE registration
  ([Order 532 Art. 17](https://www.gov.cn/zhengce/2008-08/06/content_2602514.htm)).
- ✗ Moving your own after-tax money to the U.S. is not a taxable event.
- ✗ No official figure exists for correspondent-bank, receiving-bank, SAFE-approval or
  notarisation costs. Those cells are blank on the site, not zero.

---

## The recommended sequence

Cheapest first, expensive steps last:

1. **Classify the money.** Whose is it, and what created it — salary, property sale, inheritance,
   business profit, or already-foreign-currency savings? The classification, not the balance,
   decides the route.
2. **Get the classification and the document list in writing from the bank.** One email. It
   resolves the single highest-value ambiguity in this research: two in-force instruments define
   `境内个人` differently, and the difference decides whether the USD 50,000 machinery applies at
   all (flagged A1).
3. **Settle any PRC income tax that is still due.** 20 % of the property gain is the one genuine
   tax in the picture, and it is due whether or not you convert.
4. **Choose the narrowest route that matches your facts:**
   - emigrated or inheriting → **emigrant/inheritance property transfer** (the only whole-balance
     route, phased over two years, [PBC [2004] No. 16](https://www.safe.gov.cn/safe/2004/1116/5461.html));
   - foreign national with China-earned current-account income → **Art. 13 / Art. 59 conversion**
     (no ceiling, reviewed on source not purpose);
   - genuine current-account payment → **documented purchase above the convenience amount**;
   - nothing above → there is no clean counter route, and that gap is the real problem.
5. **Fix the U.S. reporting before you touch the money.** FBAR, Form 8938 and Form 3520 are
   information returns with the largest penalties in this project. This is the step worth paying
   a professional for.
6. **Only then transact**, and price it against the measured 0.4004 % rather than against a
   headline rate from a different day.

---

## What could not be verified

Ten items, published with their sources on `/cost-review.html`. The five that matter:

| Flag | Item |
|---|---|
| A1 | Two in-force instruments define `境内个人`/`境外个人` differently. Decides which route you may use. |
| A2 | No official figure for correspondent, intermediary or U.S. receiving-bank fees. Every total is a floor. |
| A3 | No published SAFE approval fee or notarisation cost, so the emigrant route has no total. |
| A5 | The BOC personal wire tariff page still carries a 2014 effective date. |
| A10 | Your amount, source of funds, residence status and filing history are unknown. Every figure is conditional. |

Also published: three defects found in the pages that were already in this repository,
including one that overstated how far the "not a cap" reading goes.

---

## Scope and limits

This is sourced general research, not legal, tax or banking advice. It prices one bank
(Bank of China) on one day, because that is the only public price that can be cited at all;
other banks quote differently and the rate moves intraday. The model is designed to be
re-anchored, not memorised: change six numbers in `data/fx_anchor.json`, re-run
`scripts/build_cost.py`, and every table on the site is regenerated and re-verified.
