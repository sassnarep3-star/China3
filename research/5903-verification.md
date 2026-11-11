# 5903 — independent audit of the published figures (11 November 2026)

Session `arena/5903db91-china3`. Branch `arena/5903db91-china3`, from `main` @ `b677a91`
(the merge of PR #83). Published page: `5903-audit.html`. Data: `data/5903_checks.csv`,
`data/5903_costs.csv`. Gate: `scripts/verify_5903_audit.py` + `.github/workflows/5903-verify.yml`.

## What this is, and what it is not

This session found the repository already carrying a complete answer — a canonical dashboard
(`index.html` + `dashboard/*.html`), an executive summary, a question register, a
$10,000–$400,000 cost ladder, step-by-step playbooks and a Flagged page — produced by earlier
sessions. Two sibling sessions were live at the same moment and had already claimed the shared
integration files (`arena/b579901a-china3`) and the `3e2d` namespace (`arena/3e2dbf57-china3`).

So this session did not build a fourteenth parallel edition and did not edit another session's
files. It did the one thing the board's own guidance asks for and nobody had done in this window:
it took the figures the live site publishes and checked them, one by one, against the official
pages, on the day the site was published — and it recomputed every published bank cost from the
raw board and tariff with exact arithmetic and no shared code.

Deliberately out of scope: any legal or tax conclusion for a particular person; live quotes;
intermediary and receiving-bank fees (not published anywhere official, so they stay blank); and
the property-transfer and inheritance document lists, which this pass did not re-read.

## Method

1. Read `COORDINATION.md` (2,397 lines), fetched all remote branches, listed them by commit time
   and read each live branch's own copy of the board. Two branches had commits inside the hour;
   their claims were respected and everything below was written into this session's own files.
2. Ran the inherited gates before touching anything: `e347_build.py --check` OK,
   `e347_verify.py` PASS (560 cost rows, 888 sourced rows, 554 blanks flagged, 2,911 links),
   `check_conflict_markers.py`, `check_links.py`, `validate_data.py`, `test_costs.py` PASS.
3. For each claim, opened the official page with a fetch tool, recorded a verbatim quote (trimmed
   with "…"), the URL and the UTC read time. Rows that were not re-read were marked
   *not re-checked* with a blank value — not copied from the dashboard.
4. Recomputed the published cost checkpoints from `BOARD` and `TARIFF` in `scripts/5903_data.py`:
   exact `Fraction` arithmetic in the builder, exact `Decimal` arithmetic in the verifier, no
   import of the dashboard's cost engine in either.
5. Corrupted one cell on purpose to prove the gate fails, then restored it.

## Official pages read on 11 November 2026

| Page | Read (UTC) | What it settles |
|---|---|---|
| Bank of China exchange-rate board, USD row <https://www.boc.cn/sourcedb/whpj/enindex_1619.html> | 12:50 | current buying/selling rate; no history view |
| Bank of China personal e-banking transfer tariff <https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html> | 12:46 | 1 ‰, min ¥50, max ¥260, cable ¥150 |
| Bank of China 11 Nov 2026 personal-tariff notice <https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html> | 12:45 | ATM ¥12 + 1 %, max ¥112 |
| SAFE Ningxia 2022 Q&A <https://www.safe.gov.cn/ningxia/2022/0929/1997.html> | 12:44 | USD 50,000 convenience amount, and that it is not a cap |
| SAFE Tianjin 2024 Q&A <https://www.safe.gov.cn/tianjin/2024/0621/2529.html> | 12:43 | Foreign Permanent Resident ID holders get the quota |
| SAFE Tianjin 2026 Q&A <https://www.safe.gov.cn/tianjin/2026/0713/3088.html> | 12:44 | Article 59 income route |
| SAFE 汇发〔2017〕29号 <https://www.safe.gov.cn/hubei/2019/0305/851.html> | 12:44 | card cash limits ¥10,000/day, ¥100,000/year |
| SAFE Hebei cash-carry Q&A <http://www.safe.gov.cn/hebei/2019/0521/1366.html> | 12:47 | USD 5,000 / 10,000 cash limits |
| SAFE Guangdong notice <https://www.safe.gov.cn/guangdong/2020/0304/1668.html> | 12:47 | private swaps and underground banks unlawful; no splitting |
| State Council Order 532 (FX Regulation) <https://www.safe.gov.cn/safe/2008/0806/5321.html> | 12:43 | Arts. 39, 40, 42, 45, 48 penalties; Art. 52(2) 境内个人 |
| Individual Income Tax Law <https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html> | 12:42 | rates; the nine taxable categories; 183-day residence |
| 财税〔2008〕132号 <https://fgk.chinatax.gov.cn/zcfgk/c102416/c5203286/content.html> | 12:48 | deposit interest exempt |
| U.S.–China treaty <https://www.irs.gov/pub/irs-trty/china.pdf> | 12:41 | Art. 9(2): dividends ≤ 10 % |
| 26 U.S.C. § 988 (2024 ed.) <https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm> | 11:56 | 988(a)(1)(A), (e)(1), (e)(2), (e)(3) |
| 26 U.S.C. § 165(c) <https://www.govinfo.gov/content/pkg/USCODE-2024-title26/html/USCODE-2024-title26-subtitleA-chap1-subchapB-partVI-sec165.htm> | 11:58 | individual loss limits |
| IRS Publication 525 <https://www.irs.gov/publications/p525> | 12:20 | personal currency gain over $200 is a capital gain |
| IRS yearly average exchange rates <https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates> | 11:59 | 2025 7.129, 2024 7.189, 2023 7.075, 2022 6.730, 2021 6.452 |
| Federal Reserve G.5A annual <https://www.federalreserve.gov/releases/g5a/current/> | 12:01 | 2025 7.1875, 2024 7.1957, 2023 7.0809, 2022 6.7290 |
| FinCEN FBAR page <https://www.fincen.gov/report-foreign-bank-and-financial-accounts> | 12:40 | USD 10,000 aggregate threshold |
| eCFR 31 CFR 1010.821 <https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821> | 12:39 | $16,536 non-willful, $165,353 willful |
| IRS Form 8938 / FBAR comparison <https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements> | 12:38 | 8938 thresholds; $10,000 → $60,000 penalty |
| PBOC 银发〔2026〕42号 <https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html> | 12:49 | crypto prohibition; repeals 银发〔2021〕237号 |

## Result

36 claims, 30 cost cells.

- **30 of 30 published cost cells recompute to the cent.** Six routes (L01, L03, L07, L09, L10,
  L11) at five amounts ($10,000 / $50,000 / $100,000 / $200,000 / $400,000). The published ladder
  is arithmetically sound.
- **Two rows contradict themselves** (A05, A06). `dashboard/costs.html`, table "What the numbers
  are built from", prints `6.6886 RMB per dollar` beside `Selling Rate 668.51 per 100` and
  `6.6606` beside `Buying Rate 665.71 per 100`. 668.51 ÷ 100 = 6.6851, 665.71 ÷ 100 = 6.6571.
  Cause: `scripts/e347_build.py` lines 245–246 type the per-100 figures while the value column is
  computed from the current board.
- **One tax statement is wrong and it points the wrong way** (A25). Tax row T10 reads "ordinary
  income, unless the conversion is a personal transaction with a gain of USD 200 or less". Under
  26 U.S.C. 988(e)(1) the ordinary rule does not apply to a personal transaction; IRS Publication
  525 says a personal-transaction gain over $200 is a **capital gain**, and 26 U.S.C. 165(c) means
  a personal loss is not deductible at all. The same request had already been filed as
  DF25-REQ-02 by the session that read these texts first.
- **One home-page sentence is more absolute than its sources** (A08). "A U.S. passport holder does
  not get the $50,000 a year that Chinese citizens convert on ID alone." Order 532 Art. 52(2)
  defines 境内个人 to include a foreigner resident in China for one continuous year, and SAFE
  Tianjin gives the convenience amount to a 境外个人 holding a Foreign Permanent Resident ID. The
  accurate statement is conditional.
- **One official number is missing** (A28). The 2025 IRS average is 7.129; the Federal Reserve's
  G.5A annual average for 2025 is 7.1875. On $400,000 the illustrated gain differs by about
  $3,055. Neither is wrong; only one is shown.
- **A "not verified" label is out of date** (A26). "Whether a loss is usable" is answered by
  26 U.S.C. 165(c) plus 988(a)(1)(A).
- **Two official definitions of the same word** (A35). SAFE's 境内个人 is one continuous year of
  residence; the IIT Law's 居民个人 is 183 days. Both are in force and answer different questions;
  a person between the two is in different categories in the two systems.
- **The board has moved** since the site was priced: 15:30:04 (666.06 / 668.86) → 20:50:05
  (665.91 / 668.71). Recomputing the standard route on the newer board moves the $10,000 cost from
  $53.36 to $53.37 and leaves the larger amounts within a few cents, because the cost is driven by
  the spread *ratio*, which barely moves. That is a useful thing for a reader to know: a 15-fen
  board move is not a reason to delay or to rush.

## Requests logged, not edited

The shared files belong to `arena/b579901a-china3` under a claim made before this session started,
so nothing below was edited here. Each is in `COORDINATION.md` and on the audit page:

| Request | File | Change |
|---|---|---|
| 5903-REQ-01 | `scripts/e347_build.py` | build the two per-100 strings from the rate values |
| 5903-REQ-02 | `scripts/e347_data.py` | T10: personal gain over $200 is a capital gain; personal loss not deductible |
| 5903-REQ-03 | `scripts/e347_data.py` | show the Federal Reserve's 2025 average beside the IRS's |
| 5903-REQ-04 | `scripts/e347_data.py` | make the USD 50,000 sentence conditional, and give both definitions |
| 5903-REQ-05 | `dashboard/archive.html` | regenerate so this page is listed, and add a nav entry |

## Verification performed

```bash
python3 scripts/build_5903_audit.py --check   # committed files are what the generator produces
python3 scripts/verify_5903_audit.py          # 36 rows, 30 cells, Decimal, links
```

The verifier fails if: a row has no official URL on the allowlist, a confirmed row has no quote,
a "not re-checked" row carries a value, the published column no longer matches
`data/e347_costs.csv` (a rate refresh in the dashboard forces a rebuild here), any cell differs
from the Decimal recomputation, the page omits a row or a total, a row on the page has no official
link, a local link or the stylesheet is missing, the page starts depending on JavaScript, or a
conflict marker appears. A deliberate one-cent corruption was inserted in two cells and caught:

```
FAIL — 3 problem(s)
  • ('L01', 10000) published_total_usd: audit records '53.35' but the canonical table now says '53.36' — rebuild the audit page
  • ('L01', 50000) recomputed_total_usd: file '84.28', Decimal recomputation '165.95'
  • cost L01 50000: recomputed total 84.28 is not printed
```

The full inherited suite was also run on the merged tree before the pull request; see
`COORDINATION.md` for the run and for the PR and deploy record.

## Limits

- A fetch tool returns the page's text, not a browser rendering. Layout and mobile behaviour were
  built for (stacked tables under 760 px, no JavaScript) but not visually inspected.
- `sassnarep3-star.github.io` is not reachable from this sandbox, so the live pages were not
  fetched; the deploy is verified through the GitHub Actions and Pages APIs instead.
- The audit is a snapshot. Where it says "confirmed", it means confirmed against the page as read
  at the UTC time in that row, not confirmed forever.
