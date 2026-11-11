# 76e — source re-check, 11 November 2026

Session `arena/76e3e41f-china3`. Page: [`76e-verification.html`](../76e-verification.html).
Gate: `python3 scripts/verify_76e.py`. Builder: `python3 scripts/build_76e_site.py`.

## What this pass did

The repository already carried a source-checked dashboard built on 10 November 2026. This pass
re-opened eighteen load-bearing official pages on **11 November 2026**, quoted what each says now,
and recomputed the bank-cost ladder from that morning's Bank of China board. It did not edit any
page owned by another session; every finding is published instead of fixed (board rule).

## Results in one table

| Question | Answer on 11 Nov | Status |
|---|---|---|
| Did any official page change what it says? | No page changed its rule text. One rate board moved. | verified below |
| BOC USD selling rate | 6.6911 CNY/USD (669.11 per 100), pub 2026/11/11 10:25:02 | re-read |
| Bank cost, $10,000, documented-income route | $53.42 (published 11 Nov: $53.38) | recomputed |
| Bank cost, $400,000, one wire | $901.20 (published: $899.01) | recomputed |
| Bank cost, $400,000, balance already in FX | $61.28 (published: $61.33) | recomputed |
| U.S. currency gain on $400,000, 2024 basis | $27,703 (published: $28,037) | recomputed |
| Did the published arithmetic hold? | Yes — the same convention on the 10 Nov board reproduces all 80 published L01/L03 cells to the cent | checked |
| New fee schedule in force today | BOC ATM notice effective 2026-11-11: UnionPay unchanged; Great Wall International card 5‰/USD 5 cap → 2.5%/USD 40 cap | re-read |
| Problems found on published pages | 7, listed below; 2 are substantive | needs review |

## Sources re-read on 11 November 2026

| ID | Document | URL | Outcome |
|---|---|---|---|
| S01 | Bank of China, BOC Exchange Rate (USD row) | https://www.boc.cn/sourcedb/whpj/enindex_1619.html | values moved (rate only) |
| S02 | Bank of China, personal e-banking transfer tariff | https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html | unchanged |
| S03 | Bank of China, ATM fee announcement effective 2026-11-11 | https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html | unchanged text, now in force |
| S04 | SAFE Tianjin, 个人外汇（08）, 2026-07-13 | https://www.safe.gov.cn/tianjin/2026/0713/3088.html | verbatim match (Art. 59) |
| S05 | SAFE Tianjin, 政策问答（九）, 2024-06-21 | https://www.safe.gov.cn/tianjin/2024/0621/2529.html | verbatim match |
| S06 | SAFE Ningxia, 政策释疑（八）, 2022-09-29 | https://www.safe.gov.cn/ningxia/2022/0929/1997.html | match, scope note |
| S08 | 经常项目外汇业务指引（2020年版）, full text | https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html | Arts. 54-68 read in full |
| S09 | SAFE Tianjin, 个人外汇（10）, 2026-09-17 | https://www.safe.gov.cn/tianjin/2026/0917/3134.html | verbatim match (Art. 60) |
| S17 | 外汇管理条例, 国务院令第532号 | https://www.safe.gov.cn/safe/2008/0806/5321.html | verbatim match |
| S19 | 汇发〔2017〕29号, card cash abroad | https://www.safe.gov.cn/hubei/2019/0305/851.html | verbatim match |
| S20 | SAFE Hebei, cash carried out per trip | http://www.safe.gov.cn/hebei/2019/0521/1366.html | verbatim match |
| S23 | 银发〔2026〕42号, virtual currency | https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html | match; repeals 2021/237 |
| S25 | 个人所得税法 (2018) | https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html | verbatim match |
| S28 | IRS yearly average rates | https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates | unchanged (2025: 7.129) |
| S29 | IRS, Form 8938 vs FBAR | https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements | unchanged |
| S31 | 31 CFR 1010.821 | https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821 | amounts unchanged; as-of date moved |
| S33 | 26 U.S.C. § 6039F | https://www.govinfo.gov/content/pkg/USCODE-2021-title26/html/USCODE-2021-title26-subtitleF-chap61-subchapA-partIII-subpartA-sec6039F.htm | verbatim match |
| S27 | 26 U.S.C. § 988 | https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm | verbatim match |

## Arithmetic, stated so it can be checked

```
spread   = amount × (ask − (bid + ask)/2) / ask
wire CNY = min(260, max(50, amount × ask × 0.001)) + 150
total    = spread + wire CNY / ask          (rounded once, to the cent)
```

With `bid = 6.6571`, `ask = 6.6851` (the 10 November board) this reproduces
`data/e347_costs.csv` exactly: $10,000 → 20.94 + 32.44 = **53.38**; $100,000 → 209.42 + 61.33 = **270.75**;
$400,000 → 837.68 + 61.33 = **899.01** (the CNY 260 cap binds from about $38,900). With the 11 November
board (`6.6630 / 6.6911`) the same convention gives **53.42**, **271.26** and **901.20**.

Currency gain: `amount × (1 − ask / IRS_2024_average)`, i.e. the USD the RMB would have cost at the
IRS 2024 average rate minus the USD it fetches at today's ask. $400,000 → **27,703.44** on the 11 Nov
board, **28,037.34** on the 10 Nov board.

## Findings (published, not fixed)

1. **F01 — the landing page states the convenience-amount exclusion as fact.** State Council
   Regulation Art. 52(2) defines 境内个人 to include a foreigner resident in China for one continuous
   year, while Guidelines Art. 54 ties the purchase convenience amount to 境内个人 and Art. 59 para 2
   names only Foreign Permanent Resident ID holders. The dashboard's own flag U10 records the conflict;
   the landing page does not. → needs review.
2. **F02 — the cash-border row in the s775 layer misstates its own source.** It says
   "≤US$5,000 per person per day without declaration; >US$10,000 declaration required". The cited SAFE
   Hebei answer says per trip, requires a bank permit for USD 5,000–10,000, and a SAFE permit above
   USD 10,000 that is in principle not granted. → needs review.
3. **F03 — headline costs are one trading day old**, quantified on the page. Session `b8720152`
   (PR #48, merged the same morning) updated flag U15 to record the 11 November board but did not
   reprice; this pass quantifies what repricing would do. → needs review.
4. **F04 — the ATM tariff cited is a notice effective today**; the Great Wall International card's
   overseas ATM cap rises from USD 5 to USD 40 per withdrawal. → needs review.
5. **F05 — the eCFR "up to date as of" string has moved** from 11/06/2026 to 11/09/2026. → cosmetic.
6. **F06 — six live pages publish six different headline totals** for the same route (53.38 / 53.42 /
   53.47 / 899.01 / 901.30 / 1,332.05); each is explainable, but only the Archive says which is current.
   → needs review.
7. **F07 — scope note on the Ningxia answer**: its question and all four quoted articles concern
   境内个人; only its general opening sentence supports a no-ceiling reading. → needs review.

## Repository gate repaired (takeover, logged)

`scripts/verify_m5f19_site.py` check J hardcoded the `m5f19` namespace, so every later session's honest,
board-declared change turned that CI gate red — including this one. The owning session's last commit is
2026-11-10T10:26Z, more than the 60 minutes the board allows before a takeover, so the check was made
claim-aware: it now reads the current branch's own block in `COORDINATION.md`, treats brand-new files,
append-only `COORDINATION.md` and the regenerated `dashboard/archive.html` as additive, and still fails
if a file that existed at the merge base and belongs to another layer is modified without being declared.
All other checks in that file are untouched, and the gate passes on this branch.

## What was not done

* Only L01 and L03 were recomputed. The other nine routes use the same tariff and board and move with
  them, but were not re-derived here.
* No bank, tax office or SAFE branch was contacted, and no personal facts were assumed.
* No route is recommended. Which route applies turns on where the money came from (dashboard flag U01).

## Merge note (PR #48)

`main` advanced to `6750ddb` (PR #48, session `b8720152`) while this branch was open, and its
`COORDINATION.md` had been committed with literal merge-conflict markers (`<<<<<<< HEAD`, `=======`,
`>>>>>>> f6ae79e`) around the m5f19 block — a defect from that session's own merge, not from this one.
The conflict here was resolved by rebuilding the file from the two clean sides: every block kept
verbatim (`m5f19`, `76e`, `B8720152`), all marker lines removed. `dashboard/archive.html` was resolved
by running the generator (`scripts/e347_build.py`) rather than by hand, and lists 82 pages.

Session `b8720152` logged a request to the m5f19 owner to scope check J to its own branch. This session
took that task over (the m5f19 claim is more than 60 minutes old with no commits) and made the check
claim-aware instead of branch-name-based, so every future session that declares its files on this board
passes while edits to another layer's existing files are still blocked.
