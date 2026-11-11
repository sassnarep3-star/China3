# Session `f5a5` — re-verification log, 11 November 2026

Branch `arena/f5a5499c-china3`, branched from `main` @ `64a5cdf`.
Machine-readable twin: [`data/f5a5_recheck.csv`](../data/f5a5_recheck.csv) (9 rows, one per proposition checked).

Every row below was read **on the issuing body's own page on 2026-11-11**, not inherited from an earlier
session's register. Where a figure had moved, the row says `CHANGED` and gives both readings.

## What was checked, and what came back

| ID | Source | Proposition | Verdict |
|----|--------|-------------|---------|
| F5A5-V01 | Bank of China board | The USD row the site prices from | **CHANGED** — 666.06 / 668.86 at 2026/11/11 15:30:04 |
| F5A5-V02 | Bank of China board | Is the "Middle Rate" column the midpoint? | **No** — 671.91 against a 667.46 midpoint |
| F5A5-V03 | BOC personal tariff | 1‰, min CNY 50, max CNY 260, cable CNY 150 | **CONFIRMED** |
| F5A5-V04 | PBOC [2004] No. 16 | Art. 6 staging, art. 10 approval split, as enacted | **CONFIRMED but SUPERSEDED** |
| F5A5-V05 | 汇发〔2014〕2号 §6 | Both requirements cancelled | **CONFIRMED** |
| F5A5-V06 | IRS yearly averages | China 2025 7.129, 2024 7.189 … | **CONFIRMED** |
| F5A5-V07 | 31 CFR 1010.821 | FBAR USD 16,536 non-willful / USD 165,353 willful | **CONFIRMED** |
| F5A5-V08 | SAFE Ningxia FAQ | USD 50,000 is not a ceiling | **CONFIRMED** |
| F5A5-V09 | 个人所得税法 art. 3 | 3–45%, 5–35%, flat 20% | **CONFIRMED** |

## V01 — the board moved again, and the site has to say which reading it used

Bank of China's official board, read on 2026-11-11 at 15:30:04 Beijing time:

```
USD | Buying 666.06 | Cash Buying 666.06 | Selling 668.86 | Cash Selling 668.86 | Middle 671.91
```

Three earlier readings are in the repository: 2026-11-09 09:15:45 (666.38 / 669.19), 2026-11-10 17:39:58
(665.71 / 668.51) and 2026-11-11 10:25:02 (666.30 / 669.11). All four are genuine; none of them is wrong.
What is wrong is that a reader landing on the dashboard cannot tell which one priced the number in front of
them. This session makes the board reading a single named constant and stamps it on every page and every
exported CSV row, so a future re-reading is a one-line change and an out-of-date page is visible rather
than silent.

The `Middle Rate` column (671.91) is **not** the midpoint of the buying and selling rates (667.46). The
dashboard computes its own midpoint and states that it does. Nothing changed here; it is recorded because
it is the kind of thing a re-verification is for.

## V04 / V05 — the substantive defect

Two in-force texts sit side by side on safe.gov.cn:

- **PBOC Announcement [2004] No. 16, art. 6** — an emigrant property transfer is applied for once for the
  whole amount and then paid out in stages: at most half first, at most half of the remainder after one
  year, the rest after two years. Art. 10 sends anything above RMB 500,000 to SAFE head office.
- **汇发〔2014〕2号, §6** — *"取消移民财产转移分次汇出的要求"* (the requirement that an emigrant property
  transfer be remitted in instalments is cancelled) and *"取消财产转移总金额超过等值人民币50万元报国家外汇
  管理局备案的要求"* (the requirement to report a transfer above RMB 500,000 to SAFE head office is
  cancelled). §6(2) states the operative rule: *"银行可在核准件审批额度内一次或分次汇出相关资金"* — within
  the approved amount the bank may remit **once or in instalments**. The circular took effect on
  2014-02-10 and closes with *"以前规定与本通知不符的，以本通知为准"* (where an earlier rule conflicts with
  this one, this one governs).

So the 2004 staging is dead law, and the 2014 circular is the operative text. Four data files still
instruct the reader to wait two years, and one of them prices three wires that the applicant need not
make. That is `N676-F01` and `e347` irregularity `R05`, both still open when this session started. The
dashboard's own route page (L05/L06) already had it right, which is what makes the discrepancy a defect
rather than a gap.

Corrections are in the row-level tables, not in this file: see `data/cost_inputs.csv` CI29/CI30,
`data/cost_methods.csv` M03, `data/cost_steps.csv` M03 steps 5–7, `data/d646_methods.csv` M05 and the
regenerated `cost-tables.html` and `d646-methods.html`.

## What was not checked, stated plainly

- No Chinese bank branch was visited and no bank was asked for a quote. Branch practice can differ from
  the published circular; that is flag `U03`, unchanged.
- The intermediary/correspondent deduction and the U.S. receiving-bank fee stay **blank**. No regulator
  publishes either, and this pass did not guess. Flags `U04`, `CI11`, `CI12`.
- 财税〔2008〕132号 (the savings-interest exemption) was not re-fetched this pass; V09 notes that the
  exemption is not in art. 4 of the IIT Law and still rests on that separate notice.
- The 2026 IRS yearly average for China does not exist yet, so no 2026 basis is used anywhere.
- No page was opened in a browser: there is no browser in this sandbox. Link and anchor correctness is
  checked by `scripts/check_links.py` and `scripts/e347_verify.py`, not by eye.
- Nothing here is tax or legal advice for a specific person's facts.
