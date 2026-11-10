# C3X verification record — session `arena/2c8d441e-china3`

Date of every fetch: **2026-11-10**. Nothing in this pass is inherited from another
session's register without being re-read, except where a row below says so explicitly.

## 1. What was fetched, and what it settled

| ID | Document | Fetched | What it settled |
|----|----------|---------|-----------------|
| S01 | BOC FX board, USD row — `boc.cn/sourcedb/whpj/` | 2026-11-10, stamp **17:39:58 Beijing** | Bid 665.71 / ask 668.51 / 中行折算价 671.67 per 100 USD. Column set confirms the ask is what a customer buying USD pays. |
| S02 | BOC personal e-banking transfer tariff — `boc.cn/ebanking/service/cs1/200905/t20090506_990712.html` | 2026-11-10 | Cross-border telegraphic transfer **1‰, min ¥50, max ¥260, plus ¥150 cable** outside HK/Macau/Taiwan. Note 1 says local or negotiated prices may differ. |
| S03 | SAFE Tianjin, 2024-02-29, on 汇发〔2020〕14号 art. 64 | 2026-11-10 | Domestic-individual current-account remittance: **≤ USD 50,000/day on ID; above that with ID plus transaction documents**. A documentation threshold, not a cap. Cash remittance ≤ USD 10,000/day on ID. |
| S04 | SAFE Tianjin, 2024-06-21, on 汇发〔2020〕14号 art. 59 | 2026-11-10 | Foreign individual: lawful current-account RMB income purchased **with ID plus source-of-funds materials including tax documents**; the annual convenience amount applies **only** to a 外国人永久居留身份证 holder. |
| S05 | State Council Order 532 (FX Regulations) — `safe.gov.cn/safe/2008/0806/5321.html` | 2026-11-10 | Full text. Arts. 39/40/45 sanctions, art. 42 cash (≤20%), art. 48 false documents (individual ≤ ¥50,000), art. 52(2) definition of 境内个人 including a foreigner resident one continuous year. |
| S06 | PBOC Announcement [2004] No. 16 (个人财产对外转移售付汇管理暂行办法) | 2026-11-10 | Full text. Emigrant and inheritance transfers; art. 6 staging and the ¥200,000 one-off; art. 8 documents (cancelled household registration, embassy proof, **tax certificate**); art. 10 the ¥500,000 approval split; art. 11 no domestic FX cash payout. |
| S07 | 汇发〔2014〕2号 §六 (republished, marked 已修改) | 2026-11-10 | Cancels the over-¥500,000 head-office filing **(§6(1))** and the staged-remittance requirement **(§6(2))**: after approval the bank may remit once or in instalments. This is the correction that kills the "three purchases" pricing of the emigrant route. |
| S08 | PRC Individual Income Tax Law arts. 3, 6, 7, 13 | 2026-11-10 | 20% proportional rate on property transfer / interest / dividends; base = proceeds − original value − reasonable expenses; tax settlement before household registration is cancelled for emigration. Conversion is **not** one of the nine taxable categories in art. 2. |
| S09 | 26 U.S.C. §988 (GPO, 2023 edition) | 2026-11-10 | Disposition of nonfunctional currency is a §988 transaction (c)(1)(C)(i); gain is ordinary income (a)(1)(A); the capital election (a)(1)(B) covers forwards/futures/options only; personal-transaction exclusion lost if gain > **$200** (e)(2). |
| S10 | 31 CFR 1010.821 (eCFR, current to 2026-11-06) | 2026-11-10 | FBAR caps for penalties assessed on/after 2025-01-17: **$16,536** non-willful, **$165,353** willful. |
| S11 | IRS yearly average currency exchange rates | 2026-11-10 | CNY per USD: 2025 **7.129**, 2024 **7.189**, 2023 **7.075**, 2022 **6.730**, 2021 **6.452**. "The IRS has no official exchange rate… accepts any posted exchange rate used consistently." |
| S12 | IRS Form 8938 / FBAR comparison | 2026-11-10 | 8938 thresholds ($50k/$75k US-resident unmarried; $200k/$300k abroad) and penalty ceiling $60,000; FBAR threshold is aggregate **exceeding** $10,000. |
| S13 | FinCEN FBAR page | 2026-11-10 | Aggregate value exceeding $10,000 at any time in the calendar year triggers filing. |
| S14 | CBP Money and Other Monetary Instruments (modified 2025-11-24) | 2026-11-10 | > $10,000 in or out must be reported on FinCEN Form 105; **family/group aggregate**, not per person; failure risks seizure and forfeiture. |
| S15 | 汇发〔2017〕29号 (bank-card cash abroad) | 2026-11-10 | ¥100,000 equivalent per person per calendar year across own cards, ¥10,000 per card per day; exceeding the annual cap suspends the facility this year and next. |

## 2. The arithmetic, so it can be checked by hand

Board 2026-11-10 17:39:58: bid **6.6571**, ask **6.6851**, mid = (bid+ask)/2 = **6.6711**.

    half-spread  = (ask − mid) / ask = 0.0140 / 6.6851 = 0.2094%
    spread(USD)  = amount × 0.2094%
    CNY to buy   = amount × 6.6851
    wire fee CNY = min(max(0.001 × CNY, 50), 260) + 150
    total USD    = spread + wire fee / 6.6851

Worked at both ends:

* $10,000 → CNY 66,851.00; fee 66.85 + 150 = **¥216.85** = $32.44; spread $20.94; **total $53.38 (0.5338%)**
* $50,000 → fee hits the ¥260 cap: 260 + 150 = **¥410** = $61.33; spread $104.71; **total $166.04 (0.3321%)**
* $400,000 → **total $899.01 (0.2248%)**; split into 8 × $50,000 → 8 × ¥410 = ¥3,280 = $490.64 + spread $837.68 = **$1,328.33 (0.3321%)**

The ¥260 cap binds at **$38,862**, which is why the all-in percentage falls with size.

U.S. §988, as a sensitivity only:

    gain% = 1 − ask / basis_rate
    at the 2024 IRS average 7.189: 1 − 6.6851/7.189 = 7.0093% of the dollars received
    $400,000 → gain $28,037.28 → 37% = $10,373.79
    $200 exclusion → about $2,853 converted at this gain rate

## 3. Two disagreements in the repository, and how this pass treats them

**3.1 One wire or eight?** `cost-tables.html` prices the USD 400,000 case as one transfer
($901.30 on its 2026-11-10 07:32 board); `d646-costs.html` prices eight ($1,332.05). Reading S03
settles the legal question: above USD 50,000 a day the rule requires **documents**, not splitting.
So one transfer is lawful and cheaper; eight is a fee-maximising assumption. This edition shows both
columns and says which is which. Nothing was deleted or silently reconciled.

**3.2 The 中行折算价 is not a rate you can trade at.** `D646-C1` already caught a build that used the
parity column (671.67 today) instead of the bid/ask mid; that overstates the spread roughly threefold
and can produce a negative cost. The parity column is recorded in `data/c3x_inputs.csv` for
transparency and used in **no** calculation.

## 4. Values deliberately left blank

* Card/ATM FX rate and operator fee, and the convenience-amount figure — not stated in the pages
  reviewed (S04 states the *entitlement*, not an amount; S15 states the card cap, not a price).
* The PRC cash-export figure — S05 art. 15 delegates it to SAFE; the specific number was not
  re-verified in this pass, so it is not restated.
* Receiving-bank and correspondent fees — commercial, no official publication.
* The property-transfer tax base (original value and reasonable expenses) — transaction-specific.

Each blank appears as an empty cell plus a flag id in `data/c3x_method_costs.csv`, and the verifier
fails if a blank ever carries a value or a flag id that does not resolve.

## 5. What this pass did **not** do

* No tax-treaty analysis (F14).
* No re-reading of the statutory percentage-of-balance alternative in 31 U.S.C. 5321(a)(5)(C) (F13).
* No verification of the crypto prohibition instrument; M12–M14 are catalogued from S05 only (F11).
* No bank quote, so all totals are China-side and every figure is a published tariff, not your price
  (F06).

## 6. Reproduction

```bash
python3 scripts/c3x_engine.py        # rebuild data/c3x_*.csv
python3 scripts/build_c3x_site.py    # rebuild the seven c3x-*.html pages + assets/c3x.css
python3 scripts/verify_c3x_site.py   # independent re-derivation, domain allowlist, links, freshness
```

`verify_c3x_site.py` re-implements the arithmetic rather than importing it, re-derives all 40 ladder
rows and all 200 priced method rows to the cent, checks that all 360 blank rows carry a live flag id,
checks every URL is on the official allowlist, resolves every local link and anchor, and fails if a
page on disk differs from a fresh build.
