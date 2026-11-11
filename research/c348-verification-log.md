# c348 — verification log

Session `arena/3482441c-china3`, 2026-11-11, branch `arena/3482441c-china3`.
Claim PR #86 merged to `main` as `522eb7b` before any content file was written.

## What this session set out to do

The repository had fifteen parallel editions of the same answer with conflicting headline
figures and no reconciliation. It also had one specific answer to the user's question that
I could not find stated anywhere: that the USD 50,000 figure is a *convenience amount, not a cap*,
and that a U.S. passport holder does not get it. This session therefore built:

- an independently recomputable edition of the cost answer,
- a reconciliation of every previously published headline figure,
- a register of what is unknown and how to find it.

It touched no other session's files. Scope is `c348-*`, `data/c348_*`, `scripts/c348_*`,
`scripts/build_c348.py`, `scripts/verify_c348.py`, `assets/c348.css`, `.github/workflows/c348-verify.yml`,
and this log.

## Official pages read on 2026-11-11

Every row of `data/c348_sources.csv` records the URL, the UTC time of the read, how much of the page
was read, what it establishes, and a verbatim quotation. Twenty-two pages were read; three inherited
rows are marked *not read this session* and are used only with that flag.

| Code | Issuer | What it settles |
|---|---|---|
| C01 | Bank of China | the board: USD 665.91 / 668.71 per 100, Pub Time 2026/11/11 20:50:05 |
| C02 | Bank of China | the personal wire tariff: 1‰, min CNY 50, max CNY 260, cable CNY 150 |
| C03 | SAFE Tianjin | Art. 59: a foreign individual's current-account RMB income converts on ID + source documents + tax evidence |
| C04 | SAFE Tianjin | Arts. 55–56: the USD 50,000 annual convenience amount |
| C05 | SAFE Ningxia | the convenience amount is **not** an amount limit |
| C06 | State Council | 国务院令第532号: Art. 5 (no restriction on current payments), Art. 12, Arts. 39–45 (penalties) |
| C07 | SAFE | 汇发〔2017〕29号: overseas ATM ceiling CNY 100,000/year, CNY 10,000/card/day |
| C08 | STA + SAFE | 2013 No. 40: tax filing for outbound payments above USD 50,000 |
| C09 | SAFE Tianjin | which SAFE branch approves emigrant and inheritance property transfers |
| C10 | PBOC + 7 | 银发〔2026〕42号: virtual-currency conversion is an illegal financial activity |
| C11 | US GPO | 26 U.S.C. § 988 incl. (e)(1)–(3) |
| C12 | IRS | Pub. 525: a personal gain over USD 200 is reported as a capital gain |
| C13 | IRS | Topic 409: 0 / 15 / 20% long-term capital rates for 2025 |
| C14 | IRS | 2025 ordinary brackets |
| C15 | IRS | yearly average CNY per USD, 2021–2025 |
| C16 | IRS | FBAR and Form 8938 thresholds |
| C17 | eCFR | 31 CFR 1010.821: USD 16,536 non-willful, USD 165,353 willful |
| C18 | CBP | FinCEN 105 over USD 10,000, per family/group collectively |
| C22 | SAFE Tianjin | Art. 64: USD 50,000/day documentation threshold on the remittance leg |

`C19` (BOC ATM tariff) and `C20` (BOC corporate "full amount received" surcharge) were **not**
re-read and are marked as such; the ATM fee column and the receiving-fee sensitivity are left blank.

## How the arithmetic is verified

`scripts/c348_engine.py` builds `data/c348_costs.csv` (680 rows = 17 methods × 40 amounts),
`data/c348_tax.csv` (200 rows = 40 amounts × 5 acquisition years) and
`data/c348_penalty_ladder.csv` (440 rows = 11 rules × 40 amounts).

`scripts/verify_c348.py` shares no code with the builder. It re-reads the board figures out of the
verbatim quotation in `C01`, divides by 100 (the board prints CNY per 100 USD), and recomputes every
cell with exact fractions. It also checks:

- every source claiming to have been read has an official domain, a timestamp and a quotation;
- every input names a registered source;
- the total is the sum of the *displayed* (already rounded) components, so the columns on the page add up;
- every blank component names a flag, and that flag exists;
- every local link and anchor in all eleven pages resolves, and every external link is on the official allowlist;
- the page quotes the CSV: the USD 10,000 and USD 400,000 figures on the page equal the data;
- the method catalogue covers every plausible route by name.

Result: `PASS — 9350 checks, 0 failures`.

### Bugs the verifier caught in my own work

1. `Fraction("6.6591")` reads that as 66591/10000, which is **not** the same number as 665.91/100,
   and the wire fee came out 100× too small. Fixed by parsing through `Decimal`.
2. The verifier forgot that the BOC board prints CNY per **100** USD.
3. The engine summed exact components and the verifier summed rounded ones, so ten rows differed by a
   cent. Resolved by adopting one stated convention (round each component to cents, then add) and
   saying so on the page.
4. Method M03 initially reported a total of `0.00` built from all-blank components. Fixed: if nothing
   applicable is known, the total is BLANK, never zero.

## Two hypotheses I tested and rejected

Recorded because a rejected hypothesis belongs in an honest audit.

- **"53.47 and 53.42 must be double-counting the spread."** Rejected. Both reproduce exactly as
  half-spread + wire on two different board snapshots.
- **"76e's 53.42 and 901.20 use the full-spread convention."** Rejected. `76e-verification.html` states
  its formula in words: `spread = amount × (ask − (bid + ask)/2) / ask` — the same one-sided half-spread.
  My first draft of `data/c348_reconciliation.csv` asserted the double-count; it was corrected before
  publication.

## What survives, and is published

- **F01** several editions publish a *full-spread* sensitivity column; taken as the answer it overstates
  the cost by about USD 20.94 per USD 10,000 and USD 837.43 per USD 400,000.
- **F08** `methods.html` states the USD 50,000 convenience amount backwards — as a legal cap and a
  purchase quota — where SAFE says there is no amount limit for genuine current-account business and
  the annual amount belongs to domestic individuals and Foreign Permanent Resident ID holders.
- Ten further flags, each with source links, on the Flagged page.

## Limits, stated plainly

- No U.S. receiving-bank or intermediary fee is verified (F03).
- The cross-border RMB route is not priced at all (F02).
- The ATM tariff and the banknote-carrying threshold are inherited, not re-read (F04, F05).
- The PRC property and income tax rates were not re-read, and no figure from them is used.
- The capital-versus-ordinary character of a personal currency gain is unresolved on the official
  texts (F07); the edition prices the capital reading and states the ordinary figure beside it.
- This edition is additive. It does not claim the canonical dashboard, which a parallel integration
  session held throughout.
