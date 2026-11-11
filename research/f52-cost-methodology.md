# F52 cost methodology — how every $10,000 step is priced (2026-11-11)

Snapshot: BOC board 2026/11/11 10:25:02 (Beijing) — selling **6.6911**,
buying **6.6630** CNY/USD (F-S01). Tariff: BOC personal wire **1‰, min CNY 50,
max CNY 260, + CNY 150 cable** (F-S02). Recompute everything with
`python3 scripts/verify_f52.py`; rebuild with `python3 scripts/build_f52_site.py`.

## Definitions (T = USD amount to end up with before unpublished deductions)

- Midpoint `M = (6.6630 + 6.6911) / 2 = 6.67705`. BOC's printed "Middle Rate"
  (6.7191) is **not** this midpoint and is not used (flag F52-U14).
- Spread cost `S(T) = T × (6.6911 − M) / 6.6911` = **0.2100%** of T.
- Wire fee in USD `W(T) = [min(260, max(50, T×6.6911×0.001)) + 150] / 6.6911`.
- Known cost = only the published components named per row. Intermediary and
  receiving-bank fees, and personal tax unless a tax column is shown, are
  **blank and excluded** — known cost is a lower bound, never an all-in quote.

## Per-model formulas

| Series | Formula | Units/time |
|---|---|---|
| F01/F02/F04/F05/F06 (fx_wire) | `S(T) + W(T)`, one wire | 1 wire |
| F03 (wire_only) | `W(T)` | 1 wire |
| F07 (quota) | `S(T) + Σ W(each ≤$50,000 yearly chunk)` | ceil(T/50,000) years |
| F08 (blank) | — (no official price; all 40 cells blank) | unverified |
| F09S (dividend 20%) | `0.20T + S(0.80T) + W(0.80T)` | 1 wire |
| F09T (dividend 10% treaty ceiling) | `0.10T + S(0.90T) + W(0.90T)` | 1 wire |
| F10 (ATM, fee only) | CNY fee at CNY 10,000/day chunks: per chunk `min(112, 12 + 1%×chunk)`, summed, ÷ 6.6911. Conversion rate unpublished — excluded, flagged | ceil(T×6.6911/100,000) years |
| F11 (cash, spread only) | `S(T)` at the cash selling rate (equal to selling today) | ceil(T/5,000) trips |

## Headline results (known cost only)

| Route | $10,000 | $100,000 | $400,000 |
|---|---|---|---|
| F03 already-FX wire | $32.42 | $61.28 | $61.28 |
| F01 documented income (and F02/F04/F05/F06 bank part) | $53.42 | $271.26 | $901.20 |
| F07 $50k/year | $53.42 | $332.53* | $1,330.13* |
| F09S dividend incl. 20% tax | $2,047.22 | $20,229.26 | $80,733.21 |
| F09T dividend incl. 10% treaty ceiling | $1,050.32 | $10,250.26 | $40,817.20 |
| F10 ATM fee only | $112.55 | $1,120.16 | $4,480.64 (27 yrs) |
| F11 cash spread only | $21.00 | $209.98 | $839.92 (80 trips) |

*F07 intermediate values are generated in `data/f52_ladder.csv`; read them
there rather than interpolating. Worked example ($100,000, F01): spread
$209.98 + wire $61.28 = **$271.26**; RMB debited 669,110 + 410 = 669,520.

## U.S. §988 gain illustration (gain, not tax)

`Gain(T, year) = T − T×6.6911 / IRSavg(year)` with IRS averages 2023: 7.075,
2024: 7.189, 2025: 7.129 (F-S15). At $400,000: $21,705 (2023), **$27,703
(2024)**, $24,570 (2025). Tax on the gain is blank: it needs your marginal
rate and an adviser determination on character (F52-U05/U15). If the gain on
a personal transaction is ≤ $200, §988(e) recognises no gain (F-S18).

## What is deliberately not estimated

Your bank's rate/fees (F52-U03), intermediary/receiving fees (F52-U04),
offshore CNH and UnionPay conversion charges (F52-U09), SAFE approval times
(F05/F06), and all personal tax beyond the disclosed dividend rows. Any site
that fills these without a written quote is guessing.
