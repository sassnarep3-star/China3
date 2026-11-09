# Cross-session reconciliation review — session-5e4816e0 (2026-11-09)

Page: [`cross-session-review.html`](../cross-session-review.html) ·
Data: [`data/reference_inputs.csv`](../data/reference_inputs.csv) (29 official inputs),
[`data/cross_session_findings.csv`](../data/cross_session_findings.csv) (16 findings),
[`data/reference_check_values.csv`](../data/reference_check_values.csv) (40 rows, generated) ·
Generator + contract check: [`scripts/build_cross_session_review.py`](../scripts/build_cross_session_review.py)

## Why this review exists

When this session started, eight sessions had claimed the same "USD 10,000–400,000 cost estimate"
task within about three minutes, each on its own branch. The cost model was therefore already
claimed, so this session did **not** build one. It took the unclaimed job created by that
collision: fix one set of official, dated reference inputs and check every parallel session's
numbers against them.

## What was fetched (all on 2026-11-09, full page read)

| Source | Official URL | What it establishes |
|---|---|---|
| Bank of China FX board | https://www.boc.cn/sourcedb/whpj/ | USD 现汇买入 666.38 / 现汇卖出 669.19 / 现钞卖出 669.19 / 中行折算价 671.88 per 100 USD at 2026-11-09 09:15:45; board is "for reference only" |
| CFETS central parity | https://www.chinamoney.com.cn/chinese/bkccpr/ | USD/CNY 6.7188 on 2026-11-09 09:15; Oct-2026 monthly average 6.7223 |
| BOC personal e-banking tariff | https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html | cross-border wire 1‰, min ¥50, max ¥260, + cable ¥80 (HK/MO/TW) / ¥150 (elsewhere); agreements/promotions/local tariffs override |
| BOC 2017 tariff notice (corporate) | https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html | full-amount surcharge USD 15 (beneficiary bank has account at BOC New York) **or USD 25 otherwise**; only when ≥1 intermediary bank; overseas bank fees charged at actual cost |
| SAFE Ningxia Q&A 2022 | https://www.safe.gov.cn/ningxia/2022/0929/1997.html | USD 50,000 convenience amount is not an annual limit |
| SAFE Tianjin Q&A 2024 | https://www.safe.gov.cn/tianjin/2024/0229/2402.html | FX-account outward remittance: ≤ USD 50,000/day on ID; above needs transaction documents; cash ≤ USD 10,000/day |
| SAFE Hebei Q&A 2019 | http://www.safe.gov.cn/hebei/2019/0521/1366.html | carry-out cash: ≤5,000 released; 5,000–10,000 bank permit; >10,000 SAFE permit, in principle not allowed |
| SAFE 汇发〔2017〕29号 (Hubei mirror) | https://www.safe.gov.cn/hubei/2019/0305/851.html | overseas ATM: ¥100,000/person/year; ¥10,000/card/day |
| PBOC 2014 chronicle | https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/2810732/index.html | 2014-07-01 银发〔2014〕188号 abolished posted buy/sell spread management |
| U.S. CBP | https://www.cbp.gov/travel/international-visitors/money-monetary-instruments | FinCEN 105 for currency > USD 10,000 at one time |
| 26 U.S.C. 988 (govinfo, 2023 ed.) | https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm | (c)(1)(C) disposal of foreign-currency deposits is a §988 transaction; (a)(1)(A) ordinary; (e)(2) USD 200 personal exclusion; (e)(3) §162/§212 carve-out |
| IRS yearly average rates | https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates | China yuan: 2025 7.129 · 2024 7.189 · 2023 7.075 · 2022 6.730 · 2021 6.452; spot-rate translation rule; IRS has no official rate |

Rejected as evidence: `uscode.house.gov` §988 URLs (two forms) returned "Page Not Found" during
the site's temporary format; replaced by the GPO/govinfo edition. IRS Publication 525 is 57 chunks;
it was not fully read and is not used for any new proposition here.

## Reference check values (BOC personal e-banking route)

Arithmetic only, on the inputs above:

- spread vs. BOC's own mid = 6.6919 / ((6.6638 + 6.6919) / 2) − 1 = **+0.2104%**
- wire + cable (CNY) = min(260, max(50, 0.001 × CNY amount)) + 150 per wire — the ¥260 cap binds from about USD 38,853
- known bank cost: USD 53.45 at USD 10,000 (0.53%); USD 166.47 at USD 50,000 (0.33%); USD 902.86 at
  USD 400,000 in one wire (0.23%), or USD 1,331.73 if sent as eight USD 50,000 wires
- intermediary and U.S. receiving fees: **blank — unverified** (BOC says overseas bank fees are charged
  at actual cost; no fixed official amount)

## The finding that matters most

None of the cost tables reviewed quantified the potential **U.S. currency-gain** on converting CNY
that has appreciated since it was acquired. CNY acquired at the 2024 IRS average (7.189) and
converted at 6.6919 yields a gain of 6.91% of the dollars received — USD 691 per USD 10,000,
USD 27,659 at USD 400,000. That is 30–100× the bank costs, and it is the most plausible source of
the "considerable amount of taxes" in the brief. The tax on it is left blank: whether the gain is
excluded (personal, ≤ USD 200), capital, or ordinary (§988, if the deposit is a §212 investment)
depends on facts not supplied.

## Findings (X-01 … X-16)

See the table on the page / CSV. High-severity items: X-01 (spread sign error, 1a9dec1c),
X-06 (editorial pages state "not a U.S. taxable event" as fact, contradicting the deep layer and §988),
X-11 (FX-gain tax missing from every cost model), X-12 (file-name collisions between parallel sessions).

## Verification performed

- Every input row carries an official URL and a verbatim excerpt; UNVERIFIED rows have blank values
  (enforced by `scripts/build_cross_session_review.py`, which exits 1 otherwise).
- Hand-checked arithmetic is asserted in the generator (USD 10k spread 21.04; fee 216.92 CNY;
  USD 400k single-wire fee 410 CNY; eight-wire fee 3,280 CNY; 40 unique rows).
- `--check` mode fails if the HTML/CSV are stale relative to the inputs.
- Existing repository checks (`validate_data.py`, `check_links.py`, `verify_deep.py`, `test_costs.py`)
  still pass with the new files present.

Not legal, tax or banking advice.

## Re-check log

- 01:4x UTC: `origin/main` advanced to `d45f160` (PR #12, #14 merged). `main`'s `cost-tables.html`
  (7a636dce) reproduces the reference check values to the cent (USD 53.45 at USD 10,000) — only the tariff
  date is mistyped as 2024-11-01 (X-14). 1a9dec1c fixed its spread sign in code (X-01 downgraded).
  New findings X-15 (80597d10 base case charges the full bid-ask spread on a one-way purchase) and
  X-16 (PR #15 rewrites shared deep-layer table data).
