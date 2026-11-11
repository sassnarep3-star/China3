# BEA4 — independent re-verification, repricing and penalty breakdown (11 November 2026)

Session `arena/bea42a88-china3` · branch `arena/bea42a88-china3` · base `main` `64a5cdf` (PR #75 merge, 03:24Z)
Claim block: `COORDINATION.md` → `session-bea42a88-china3-bea4-v1`

Pages: [`bea4-audit.html`](../bea4-audit.html) and [`bea4-penalty.html`](../bea4-penalty.html).
Gate: `python3 scripts/verify_bea4_site.py`. Data: `data/bea4_*.csv`, `data/bea4_summary.json`.

---

## 1. Why this pass exists

The dashboard on `main` was built by session `ea347561` from official pages read on **2026-11-10**, and it
says so: flag U15 states that the figures were *not* repriced to the 11 November board. Three things were
therefore unproven and are proven here:

| Question | Answer after this pass |
|---|---|
| Is the 440-row cost ladder arithmetically right? | Yes — re-derived in separate code, **1,720 cells, 0 mismatches** |
| What did one day of board drift do to the numbers? | USD cost moves by pennies; the **RMB needed** rises **0.0523%** |
| Are the official pages still saying what the site says? | **24 of 35** re-read and confirmed; **1 dead link**; **10 not re-read** (labelled) |
| Is the "conversion penalty" really a tax? | No. The exposure is (a) bank cost ~0.27%, (b) Chinese fines **30%–100%**, (c) U.S. filing penalties up to **USD 165,353** |

Everything below is a record of what was fetched and what it said, not a summary of somebody else's summary.

## 2. Method

1. **Fetches.** Every citation in `data/e347_sources.csv` was re-requested on 2026-11-11. Where the page
   was retrieved, the quoted proposition was checked against the live text (Chinese text quoted verbatim
   where the source is in Chinese). Where it was not retrieved, the row says `NOT_RECHECKED` — it is not
   upgraded on the strength of a previous session's reading.
2. **Arithmetic.** `scripts/bea4_recheck.py` reimplements every cost model from the *published inputs only*
   (BOC buy/sell, the wire tariff, the ATM cap, the USD 50,000 quota, the 20% IIT rate). It does **not**
   import `scripts/e347_costs.py`, so a bug in one cannot be cancelled by the same bug in the other.
   Output: `data/bea4_cost_recheck.csv` (440 rows · 1,720 compared cells).
3. **Repricing.** The same models are run against both boards — 10 Nov `17:39:58` (buy 665.71 / sell
   668.51) and 11 Nov `15:30:04` (buy 666.06 / sell 668.86) — into `data/bea4_repricing.csv`.
4. **Penalty exposure.** Published statutory percentages are applied to the same 40 amounts into
   `data/bea4_penalty_exposure.csv`. No percentage is invented; every one is quoted in
   `data/bea4_source_audit.csv` against the page it came from.

## 3. Source-by-source result

Full register with the evidence for each row: `data/bea4_source_audit.csv` (37 rows = 35 dashboard
citations + 2 proposed replacements).

### 3.1 Confirmed on 2026-11-11 (24)

| ID | Official page | What was checked |
|---|---|---|
| S01 | [BOC exchange-rate board](https://www.boc.cn/sourcedb/whpj/enindex_1619.html) | USD row **666.06 / 666.06 / 668.86 / 668.86 / 671.91**, Pub Time **2026/11/11 15:30:04** |
| S02 | [BOC personal transfer tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html) | 跨境汇款（电汇）1‰, min CNY 50, max CNY 260, plus CNY 150 cable (non-HK/Macau/Taiwan) |
| S03 | [BOC fee change effective 2026-11-11](https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html) | UnionPay overseas ATM: CNY 12 + 1%, cap CNY 112 · **Mastercard/VISA: 2.5%, min USD 3, max USD 40 from today** |
| S04 | [SAFE Tianjin, 2026-07-13](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) | Art. 59 of 汇发〔2020〕14号, verbatim |
| S06 | [SAFE Ningxia, 2022-09-29](https://www.safe.gov.cn/ningxia/2022/0929/1997.html) | USD 50,000 annual convenience amount is **not** a ceiling; Arts 56–57 non-quota route |
| S07 | [SAFE Tianjin, 2024-02-29](https://www.safe.gov.cn/tianjin/2024/0229/2402.html) | Art. 64: USD 50,000/day on the ID; above that, transaction documents |
| S10 | [SAFE Tianjin, 2025-06-13](https://www.safe.gov.cn/tianjin/2025/0613/2811.html) | Watch list = the year of listing **plus two** |
| S12 | [PBOC 2004 No. 16](http://m.safe.gov.cn/safe/2004/1116/5461.html) | Arts 6, 10, 11, 13 — 2004 text, later amended by S13 |
| S13 | [汇发〔2014〕2号 (as amended)](https://www.safe.gov.cn/tianjin/2024/0903/2594.html) | RMB 500,000 HQ-report rule **removed**; staged-remittance requirement **removed**; notarisation **removed**; §5 >USD 50,000 profit remittance documents |
| S16 | [STA/SAFE 2013 No. 40](https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html) | Tax filing above USD 50,000 per payment; Art. 4, Art. 9 |
| S17 | [State Council Order 532](https://www.safe.gov.cn/safe/2008/0806/5321.html) | Arts 39/40/45: up to 30%, 30–100% serious; Art. 42: 20%; Art. 48: individual up to CNY 50,000; Art. 52(2) definition of 境内个人 |
| S19 | [汇发〔2017〕29号](https://www.safe.gov.cn/hubei/2019/0305/851.html) | RMB 100,000/year and RMB 10,000/card/day abroad |
| S20 | [SAFE Hebei on cash](http://www.safe.gov.cn/hebei/2019/0521/1366.html) | USD 5,000 free / 5,000–10,000 bank permit / >10,000 SAFE permit, in principle not allowed |
| S21 | [SAFE Guangdong](https://www.safe.gov.cn/guangdong/2020/0304/1668.html) | Only licensed banks and exchange institutions; other channels illegal; no splitting, no false documents |
| S23 | [银发〔2026〕42号](https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html) | Crypto business = illegal financial activity; repeals 银发〔2021〕237号 |
| S25 | [IIT Law 2018](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html) | Art. 3(3) 20% flat; Art. 6(5) gain = proceeds − cost − expenses; Art. 13 payment by 30 June next year |
| S27 | [26 U.S.C. § 988 (2023)](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm) | (e)(2) personal transaction, USD 200 test; (c)(1)(C)(ii) deposits are nonfunctional currency |
| S28 | [IRS yearly average rates](https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates) | China: 2025 7.129, 2024 7.189, 2023 7.075, 2022 6.730, 2021 6.452; "no official exchange rate" |
| S29 | [IRS 8938 vs FBAR](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements) | Thresholds and penalties as published |
| S30 | [FinCEN FBAR](https://www.fincen.gov/report-foreign-bank-and-financial-accounts) | Aggregate > USD 10,000 at any time in the calendar year |
| S31 | [31 CFR 1010.821](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821) | Non-willful **16,536**, willful **165,353**, assessed on/after 2025-01-17; no newer adjustment yet |
| S32 | [IRS gifts from foreign person](https://www.irs.gov/businesses/gifts-from-foreign-person) | Form 3520 Part IV; USD 100,000 (NRA) / 20,573 (2026, foreign corporations & partnerships) |
| S33 | [26 U.S.C. § 6039F (2021)](https://www.govinfo.gov/content/pkg/USCODE-2021-title26/html/USCODE-2021-title26-subtitleF-chap61-subchapA-partIII-subpartA-sec6039F.htm) | 5% per month, capped at 25%; reasonable-cause exception |
| S35 | [CBP monetary instruments](https://www.cbp.gov/travel/international-visitors/money-monetary-instruments) | Report > USD 10,000, family aggregate, FinCEN Form 105 |

### 3.2 Dead link (1) — flagged as D01

**S24** `http://beijing.pbc.gov.cn/beijing/132026/3660457/index.html` returns **HTTP 404** (nginx) today;
the https form of the same path also 404s. It was the **only** citation supporting route **L08**
(send the RMB itself abroad and convert outside the mainland).

Replacements read and verified today (offered, not applied — the file belongs to `ea347561`'s scope):

- **S36** [SAFE Shanghai, Q&A 162, 2018-05-15](https://www.safe.gov.cn/shanghai/2018/0515/783.html) —
  quotes 银发〔2018〕3号: banks may handle an individual's other current-account cross-border RMB
  settlement on the three "know your customer/business, due diligence" principles.
- **S37** [银发〔2020〕330号, effective 2021-02-04](https://www.pbc.gov.cn/tiaofasi/144941/3581332/4158143/index.html) —
  Art. 13 supports individual current-account cross-border RMB settlement, expressly including salary.

### 3.3 Not re-read in this pass (10)

S05, S08, S09, S11, S14, S15, S18, S22, S26, S34 — last read 2026-11-10; listed as `NOT_RECHECKED` on the
page. No row that depends on them is claimed as verified today.

## 4. Arithmetic re-derivation

`data/bea4_cost_recheck.csv`, 440 rows × 6 monetary fields, compared to the cent:

```
1,720 cells compared · 0 mismatches · maximum absolute delta 0.00
```

Consequences for the reader:

- The published ladder **is** the published inputs, applied correctly. Any dispute about a figure is a
  dispute about the input (rate, tariff, cap), not about the arithmetic.
- The bank's cut is a **percentage**: spread 0.4188% on the 10 Nov board, 0.4186% today (buy 666.06,
  sell 668.86 → CNY 2.80 per USD). It barely moves with the level of the rate.
- What does move is the **RMB price of a dollar**: +0.0523% overnight. To buy USD 10,000 you now hand
  over Rmb 35.04 more than yesterday; at USD 400,000, RMB 1,400 more, while the USD cost *falls* by
  USD 0.47 because the wire fee's USD equivalent is smaller.
- L03 (wire out foreign currency you already hold) is capped at CNY 260 + CNY 150, so its cost stops
  rising: USD 61.33 at 100,000 and at 400,000. Not a stale row (defect D06, informational).

## 5. Penalty breakdown (new analysis)

`data/bea4_penalty_exposure.csv`: 40 amounts × 9 columns, each column traceable to one instrument.

| At USD 100,000 | Figure | Source |
|---|---|---|
| Lawful bank cost (documented income) | USD 270.75 (0.2708%) | S01 + S02 |
| China, evading FX controls — ceiling 30% | USD 30,000 | S17 Art. 39/40/45 |
| China, serious cases — 30% to 100% | up to USD 100,000 | S17 Art. 39/40/45 |
| China, carrying cash in breach — 20% | up to USD 20,000 | S17 Art. 42 |
| China, untrue documents — fixed | up to CNY 50,000 | S17 Art. 48 |
| U.S. willful FBAR — greater of 165,353 or 50% | USD 165,353 (50% = 50,000) | S31 |
| U.S. non-willful FBAR | USD 16,536 per violation | S31 |
| U.S. Form 8938 maximum | USD 60,000 | S29 |
| U.S. Form 3520 — 25% of a gift | USD 25,000 | S33 |

Reading rules enforced on the page: these are **maxima**, they are **alternatives not additions**
(Chinese and U.S. exposures arise from different conduct), and the actual amount is discretionary.

## 6. Defects published (full table on the page)

| ID | Severity | Finding | Status |
|---|---|---|---|
| D01 | medium | S24 404; L08 loses its citation | replacements S36/S37 verified, filed as a request to the dashboard owner |
| D02 | low | `dashboard/sources.html` prints eCFR "as of 11/06/2026"; live page says 11/09/2026 | cosmetic, flagged |
| D03 | info | BOC Mastercard/VISA ATM cap changed today (2.5%, max USD 40); model prices UnionPay only | no figure changes |
| D04 | info | BOC "Middle Rate" column (671.91) ≠ midpoint of buy/sell (667.46) | dashboard already warns; restated |
| D05 | low | 10 citations not re-read today | labelled, not glossed |
| D06 | info | L03 cost appears frozen at large amounts (published cap) | explained |

## 7. Integration performed by this session

All other sessions were idle for ~4 hours at claim time (newest sibling commit 03:23Z, `main` 03:24Z;
`gh run list --branch main` all green; Pages `built`). Acting as the final integration session:

- `scripts/e347_build.py`: two additive `NAV` entries (`bea4audit`, `bea4penalty`) honouring
  **BEA4-REQ-01**, plus their `Ctx.page()` mappings and an `EXTERNAL_PAGE_KEYS` guard so the generator
  does not treat them as its own files; one new `ARCHIVE_GROUPS` rule so the archive labels this layer
  correctly instead of falling through to "First editorial pages".
- `scripts/e347_verify.py`: the nav-size assertion now compares against `len(e347_build.NAV)` instead of
  a hardcoded 11, so the check keeps catching lost/extra nav items without a second edit.
- Regenerated `index.html`, `dashboard/*.html` (nav line only) and `dashboard/archive.html` (the two new
  pages listed under their own layer). Diff: 9 files, +25/−12, no content change.

## 8. Reproduce

```bash
python3 scripts/bea4_recheck.py         # data/bea4_*.csv + bea4_summary.json
python3 scripts/build_bea4_site.py      # bea4-audit.html, bea4-penalty.html
python3 scripts/verify_bea4_site.py     # the gate described above
python3 scripts/e347_build.py --check && python3 scripts/e347_verify.py
```

## 9. Limits

- 10 citations were not re-read; the rows that depend on them are not claimed today.
- No bank quote, branch tariff, correspondent fee or receiving fee has been verified; those stay blank.
- The penalty table is arithmetic on published maxima, not a prediction or advice.
- Nothing here decides which route is lawful for a given person: that turns on the source of funds,
  which is not in this repository (dashboard flag U01).
