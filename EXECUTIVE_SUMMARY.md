# Executive summary

Question: a U.S. citizen has money in a Chinese bank account and is told that turning it into dollars
means "a considerable amount of taxes". What is the best lawful way out, and what does it really cost?

All figures were read from official pages on 2026-11-10. Bank figures use the Bank of China board
published 2026/11/10 17:39:58 (Beijing). Live site: https://sassnarep3-star.github.io/China3/

## Read this with the decision register

A second pass on **11 November 2026** re-read 23 official pages and asked a different question: not "what
does it cost" but "what must be settled before any decision is reasonable". It is on
[`questions.html`](questions.html) (method in [`research/f52c-questions.md`](research/f52c-questions.md)).

- 45 questions: 27 have a sourced answer from a page read that day, 15 depend on facts only the account
  holder has, 3 have no official answer at all.
- Six facts decide everything: where the money came from, which currency it is, how much, when it was
  acquired, Chinese residence status, U.S. reporting history.
- Repriced at the 11 November board (selling 669.11): **$53.42** on $10,000 and **$901.20** on $400,000 on
  the convert-and-wire route, against $53.38 / $899.01 at the 10 November board used below.
- Newly flagged: the landing page attributes the 30 % fine to four pages that contain no fine (the fine is
  in Regulation arts 39, 40, 45); nine legacy pages cite the crypto notice repealed on 2026-02-06.

## The answer in five points

1. **Converting and wiring is not taxed.** No official source read here puts a tax on the conversion or the
   wire. China's Foreign Exchange Regulation says current payments and transfers are not restricted
   ([S17](https://www.safe.gov.cn/safe/2008/0806/5321.html)). What the bank must see is proof of where the money came from and that tax on it was handled
   ([S04](https://www.safe.gov.cn/tianjin/2026/0713/3088.html), [S11](https://www.safe.gov.cn/tianjin/2021/1102/1777.html)).
2. **The only large tax found is on the underlying income, not on the transfer.** If Chinese income tax
   was never paid on the money, it is owed whether or not the money moves: 3% to 45% on wages, 20% on dividends, rent and
   property gains ([S25](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html)). Bank-deposit interest is exempt ([S26](https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html)). Which of these applies to you
   is not known (flags U01, U02).
3. **The bank's own cost is small.** $53.38 on $10,000 and $899.01 on $400,000 in
   one wire ([S01](https://www.boc.cn/sourcedb/whpj/enindex_1619.html), [S02](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html)). Fees taken by intermediary and receiving banks are not published and
   are left blank (flag U04).
4. **A U.S. passport holder does not get the USD 50,000-a-year allowance** that Chinese citizens use on ID
   alone; only holders of the Chinese Foreign Permanent Resident ID do ([S05](https://www.safe.gov.cn/tianjin/2024/0621/2529.html), [S06](https://www.safe.gov.cn/ningxia/2022/0929/1997.html)). The lawful
   route depends on what the money is: documented income, a home sale, an inheritance, an emigrant's
   pre-departure property, money you brought in and can change back, or foreign currency already in the
   account.
5. **The U.S. side can be the bigger number.** Selling RMB for dollars is a currency sale ([S27](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm)). RMB
   acquired at the 2024 IRS average rate shows a gain of about 7% today ([S28](https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates)). FBAR, Form 8938 and
   Form 3520 each carry their own penalty if missed ([S31](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821), [S29](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements), [S32](https://www.irs.gov/businesses/gifts-from-foreign-person)).

## Cost at a glance

Known bank cost only. The last two columns are the U.S. currency gain (not the tax) if the RMB had been
acquired at that year's IRS average rate.

| Amount | Already USD: wire only | Convert and wire once | USD 50,000 a year (PR-ID holders) | Gain if acquired 2024 | Gain if acquired 2025 |
|---|---|---|---|---|---|
| $10,000 | $32.44 | $53.38 | $53.38 (1 yr) | $701 | $623 |
| $50,000 | $61.33 | $166.04 | $166.04 (1 yr) | $3,505 | $3,113 |
| $100,000 | $61.33 | $270.75 | $332.08 (2 yr) | $7,009 | $6,227 |
| $200,000 | $61.33 | $480.17 | $664.16 (4 yr) | $14,019 | $12,453 |
| $300,000 | $61.33 | $689.59 | $996.25 (6 yr) | $21,028 | $18,680 |
| $400,000 | $61.33 | $899.01 | $1,328.33 (8 yr) | $28,037 | $24,907 |

Every $10,000 step for every route: https://sassnarep3-star.github.io/China3/dashboard/costs.html (data: `data/e347_costs.csv`).

## Which route

| If the money is | Route | What the bank or SAFE needs | Source |
|---|---|---|---|
| Foreign currency already in the account | L03 wire out | Passport | [S08](http://m.safe.gov.cn/safe/file/file/20200831/f0127756271c43ef9b3908d5d157bd91.pdf), [S18](http://m.safe.gov.cn/safe/2006/1225/5319.html) |
| RMB you converted from your own foreign currency in the last 24 months | L02 change back | Passport and the original exchange slip | [S09](https://www.safe.gov.cn/tianjin/2026/0917/3134.html) |
| Income earned in China | L01 buy USD and wire | Passport, source documents, tax evidence | [S04](https://www.safe.gov.cn/tianjin/2026/0713/3088.html), [S11](https://www.safe.gov.cn/tianjin/2021/1102/1777.html) |
| Proceeds of selling your home in China | L04 | Registered contract, registration proof, tax certificate; capped at price minus taxes | [S15](https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf) |
| An inheritance | L05 | SAFE approval where the decedent was registered; inheritance proof; tax certificate | [S12](http://m.safe.gov.cn/safe/2004/1116/5461.html), [S13](https://www.safe.gov.cn/tianjin/2024/0903/2594.html) |
| Property from before you emigrated from China | L06 | SAFE approval at the former hukou location; hukou cancellation; tax certificates | [S12](http://m.safe.gov.cn/safe/2004/1116/5461.html), [S13](https://www.safe.gov.cn/tianjin/2024/0903/2594.html) |
| A gift, or money with no documents | none verified | See flag U07 | [S04](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) |

Do not use relatives' quotas, private swaps, money changers, false documents or crypto. Fines run up to 30%
of the amount, 30% to 100% in serious cases, with criminal liability possible ([S17](https://www.safe.gov.cn/safe/2008/0806/5321.html), [S10](https://www.safe.gov.cn/tianjin/2025/0613/2811.html),
[S21](https://www.safe.gov.cn/guangdong/2020/0304/1668.html), [S23](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html)).

## What is not known

19 items are open and listed at https://sassnarep3-star.github.io/China3/dashboard/flagged.html. The three that decide the answer:

- **U01** where the money came from;
- **U02** what the "considerable taxes" actually are (no tax, rate or office is named in the brief);
- **U07** no verified route exists for money received as a gift or without documents.

This is research from public official sources. It is not legal, tax or banking advice.

Earlier versions of this file are kept in `research/archive/executive-summary-before-e347.md`.
