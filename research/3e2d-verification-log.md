# 3E2D verification log (2026-11-11)

Session `arena/3e2dbf57-china3`. All pages fetched via fetch_page on 2026-11-11.

## Direct (fetched and read in full)

| ID | Page | Key figure confirmed |
|----|------|----------------------|
| T01 | BOC board | Buying 665.91, Selling 668.71, Middle 671.91, 2026/11/11 20:50:05 |
| T02 | BOC tariff | Wire 1‰, min 50, max 260, cable 150 (non-HK/MO/TW) |
| T03 | BOC ATM notice | UnionPay 12 + 1%, max 112; MC/VISA 2.5% min 3 max 40 |
| T04 | SAFE Tianjin 2026-07-13 | Art. 59 ID + source materials incl. tax vouchers |
| T05 | SAFE Tianjin 2024-06-21 | Only green-card holders get convenience amount |
| T06 | SAFE Ningxia 2022-09-29 | $50k/yr convenience, not a cap |
| T07 | SAFE Tianjin 2024-02-29 | Art. 64: $50k/day ID; above needs materials |
| T09 | SAFE Tianjin 2026-09-17 | Art. 60 reconversion, 24 months, $500/day ID |
| T12 | PBOC Order 2004 No.16 | Emigrant/inheritance docs, own-account remittance |
| T13 | SAFE 2024-09-03 | Sec. 6 approval/instalments; Sec. 5 profit >$50k docs |
| T17 | Order 532 | Arts. 5, 12, 39, 40, 42, 45, 48, 52(2) verbatim |
| T19 | SAFE 2017 No.29 | ATM CNY 10k/day, 100k/yr |
| T20 | SAFE Hebei 2019-05-21 | Cash $5k / $10k permit |
| T25 | PRC IIT Law | Art. 3(3) flat 20%; Art. 6(5) base |
| T26 | IRS yearly averages | 2025 7.129; 2024 7.189; 2023 7.075; 2022 6.730; 2021 6.452 |
| T27 | US-China Treaty Art. 9 | 10% cap for beneficial owner (Art. 9(2)) |
| T28 | Wise from-CNY | Eligibility, 300k/50k caps, limit = salary − tax; fee/FX in-app only |
| T29 | Western Union China | Cash pickup only; fee/FX not published |
| T30 | Bank of America | Inbound may be $15; outbound USD $45 |
| T32 | 31 U.S.C. 5321 + eCFR 1010.821 | Willful FBAR: greater of $100k (→$165,353) or 50% |
| T35 | CBP money page | Report >$10,000 (FinCEN 105) |

## Excerpt (official text via search excerpt / contents read — Flag F11)

T08 (PDF Arts. 65/67), T10 (Art. 62), T11 (service trade), T14 (6.4), T15 (Sec. 8),
T16 (Announcement 40), T18 (Individual FX Measures), T21 (Guangdong reminder),
T22 (Zhu splitting case), T23 (virtual currency), T24 (cross-border RMB),
T31 (Pub. 525 $200/capital gain), T33 (FBAR $10k), T34 (Form 8938 $50k/$75k).

## Arithmetic

Engine `scripts/3e2d_engine.py` (Decimal) vs verifier `scripts/verify_3e2d_site.py`
(Fractions, no engine import): all 560 ladder rows recomputed to the cent;
fx-gain spot checks at 6 amounts × 2 years; page/data parity ($53.37, $898.75,
$32.43, $61.31 on costs page); official-domain check on every URL; blanks flagged;
internal links resolve. Result: PASS.

## Irregularities

3E2D-IR-01 (s.988 ordinary vs capital), 3E2D-IR-02 (IRS vs Fed 2025 average),
3E2D-IR-03 (stale archive). See `3e2d-flagged.html`.
