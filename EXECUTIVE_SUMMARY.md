# Executive summary

**Question.** A U.S. citizen has personal money sitting in a Chinese bank account. They have been told that turning
it into U.S. dollars means "a considerable amount of taxes". What are the lawful ways out, what does each really
cost, and what is still unknown?

**Release status.** Every figure below was read from an official page **on 11 November 2026**. The live page with
the full tables is [`r11-release.html`](https://sassnarep3-star.github.io/China3/r11-release.html); the dashboard
is [`index.html`](https://sassnarep3-star.github.io/China3/). Live site: https://sassnarep3-star.github.io/China3/

---

## 1. The answer in seven lines

1. **Converting and wiring is not taxed.** No official source read for this release imposes a tax on changing RMB
   into USD or sending it abroad. China's Foreign Exchange Regulation, Art. 5: the State does not restrict current
   international payments and transfers. ([S16](https://www.safe.gov.cn/safe/2008/0806/5321.html))
2. **What the bank asks for is proof, not payment.** For income earned in China, Art. 59 of the 2020 current-account
   guidelines requires identity plus source-of-funds material **including tax evidence**. If Chinese tax on the
   money was never paid, it is owed whether or not the money moves.
   ([S04](https://www.safe.gov.cn/tianjin/2026/0713/3088.html))
3. **The large number in these amounts is on the U.S. side, not the Chinese side.** USD 400,000 arriving today,
   converted from RMB acquired at the 2024 IRS average rate, carries a reported currency gain of **$27,703** —
   about 6.9% of the money — taxed as ordinary income. The bank's published cost on the same $400,000 is **$901.20**.
4. **A U.S. passport holder does not get the USD 50,000 a year convenience amount.** Only a holder of the PRC
   Foreign Permanent Resident ID card does. A passport holder converts against documents instead, and Art. 59
   sets no ceiling. ([S05](https://www.safe.gov.cn/tianjin/2024/0621/2529.html))
5. **The route is decided by what the money is, not by how much it is.** Income, a home sale, an inheritance, a
   former resident's pre-departure property, foreign currency already in the account, and company profit each have
   a different document list and a different tax position. For a gift, or money with no documents, **no lawful
   route was found** (flag U07).
6. **The cheapest lawful route is the one with no conversion at all.** If part of the balance is already in a
   foreign-currency account inside China, Art. 65(1) lets a foreign individual remit it on valid ID alone: the wire
   fee and nothing else — **$61.28** on $400,000 versus $901.20 to convert first.
7. **The reporting penalties dwarf every fee here.** One missed FBAR is a maximum of **$16,536** (non-willful) or,
   if willful, the greater of **$165,353** or **50% of the account balance**. Fix the reporting before moving
   anything. ([S28](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821),
   [S30](https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm))

## 2. What it costs: published cost at the Bank of China board of 2026-11-11 10:25:02

Rate: **6.6630 buying / 6.6911 selling** CNY per USD. Wire tariff: 0.1%, RMB 50 minimum, RMB 260 maximum, plus
RMB 150 cable. Spread is measured from the bank's own mid (6.6771) to the rate a customer actually pays. These are
the **published** components only; intermediary and receiving-bank fees are not published by anyone and are left
blank in every total (flag U04).

| Amount | Wire only (USD already in account) | Convert + wire, one wire | USD 50,000 a year (PR-ID holders) | ATM card (published fee only) |
|---|---|---|---|---|
| $10,000 | $32.42 | **$53.42** (0.53%) | $53.42 | $112.55 |
| $50,000 | $61.28 | **$166.27** (0.33%) | $166.27 | $560.98 |
| $100,000 | $61.28 | **$271.26** (0.27%) | $332.53 (2 years) | $1,120.16 |
| $200,000 | $61.28 | **$481.24** (0.24%) | $665.06 (4 years) | $2,240.32 |
| $400,000 | $61.28 | **$901.20** (0.23%) | $1,330.13 (8 years) | $4,480.64 |

All 40 increments from $10,000 to $400,000, for all eleven priced channels, are on
[`r11-release.html`](https://sassnarep3-star.github.io/China3/r11-release.html). The dividend route adds 20% Chinese
tax on the amount before the conversion: **$80,733.21** of published cost on $400,000.

## 3. Why the numbers on older pages differ

Four earlier layers published four different figures for the same $10,000 conversion. Reproduced from each one's own
board reading, they all come back to the cent:

| Board reading | Bid / ask | Cost at $10,000 | Cost at $400,000 | Where it came from |
|---|---|---|---|---|
| 2026-11-11 10:25:02 | 6.6630 / 6.6911 | **$53.42** | **$901.20** | this release |
| 2026-11-10 17:39:58 | 6.6571 / 6.6851 | $53.38 | $899.01 | the previous dashboard |
| 2026-11-10 (earlier) | 6.6622 / 6.6903 | $53.42 | $901.30 | the s775 / fbbd3b22 layers |

The difference is the clock, not the channel. That is why this release dates every figure and why the archive pages
are labelled rather than deleted.

## 4. The questions that must be answered before a decision

Seventeen questions in seven gates, each with what is already known, what is not, and how to find out:
[`dashboard/questions.html`](https://sassnarep3-star.github.io/China3/dashboard/questions.html). The five that
decide the answer:

| # | Question | Why it decides |
|---|---|---|
| Q01 | Is the account recorded under your passport or a Chinese ID? | Picks which half of the rule book applies. The Regulation and the PBOC Measures define "domestic individual" differently and they do not agree (flag U10). |
| Q03 | What is the money, line by line? | Sets the bank's document list, the Chinese tax and the route. |
| Q04 | Has Chinese income tax been paid or withheld on it? | If not, it is owed whether or not the money moves. No channel removes it. |
| Q06 | What exactly did the bank say would be charged — a tax, a fee, or a refusal? | The brief's "considerable taxes" is unverified. No source read imposes a conversion tax; if it is a spread or fee it is far smaller, and if it is unpaid income tax it is not a conversion penalty. |
| Q10 | Have FBARs and Form 8938 been filed for every year? | A single missed report can cost more than ten times the transfer fee. |

## 5. What is not known

Twenty items are open and published with their sources on
[`dashboard/flagged.html`](https://sassnarep3-star.github.io/China3/dashboard/flagged.html). The three that block an
answer: **U01** what the money is, **U02** what the "considerable taxes" actually are, **U07** money received as a
gift or with no documents. Nothing here is a finding about any actual account: no balance, currency mix, account
category, tax history or filing history is known (flag U20).

## 6. Repository review

Twelve findings are published with evidence on the Flagged page (R01–R12), including: source registers in three
earlier layers whose "fetched" timestamps cannot be real (R01); fourteen layers with colliding figures and colliding
flag ids (R02, R08); an earlier page that invited the reader to hope the §988 personal-transaction rule applied when
it only covers $200 of gain (R03 — corrected in this release); and fifteen validators, several of which only prove
consistency with their own inputs rather than truth (R10).

---

This is research from public official sources. It is not legal, tax or banking advice and makes no finding about
any person's case. Reproduce every figure with `python3 scripts/r11_engine.py && python3 scripts/r11_build_page.py`;
check them with `python3 scripts/r11_verify.py`.
