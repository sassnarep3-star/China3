# S775 line-by-line repository audit — CNY→USD repatriation research repo

Session: `arena/775c9619-china3` (branch fixed by Arena; irregularity `S775-IR-001` logged in
`data/s775_flags.csv`). Audit date: **2026-11-10**. All figures below were read from official
sources during this session; fetch timestamps are in `data/s775_sources.csv` and
`data/verify_2026.csv`.

## 1. What the audit checked

Every table row in this session's `s775` namespace (`data/s775_*.csv`) must either (a) link to an
official source or (b) be blank and flagged. The audit also compared the accumulated repo's
conflicting lines against the primary instruments and recorded the winner, with the losing text
kept visible for the record.

## 2. Regulatory conflicts resolved (line by line)

### 2.1 Emigrant property transfer staging — `汇发〔2014〕2号` vs PBOC `[2004] No.16`

- `data/verify_2026.csv` V08 (PBOC `[2004] No.16` art. 6) still publishes the old text: *first
  remittance ≤ half of the property; after one year ≤ half of the remainder; after two years the
  rest*.
- V07 (`汇发〔2014〕2号`, as amended, SAFE Tianjin) cancels it: *取消移民财产转移分次汇出的要求*,
  and the approved amount may be remitted *一次或分次汇出* (once or in several instalments).
- **Resolution:** the 2014 instrument is later and expressly cancels the staging. `M05` in
  `data/s775_methods.csv` states the approval-then-lump-sum rule and keeps the 2004 text cited only
  as historical record (`S28`). Nothing was deleted from `verify_2026.csv`.

### 2.2 Personal vs corporate BOC `OUR` tariff

- `data/verify_2026.csv` V05 cites BOC's corporate/trade-finance tariff (`S05` document family)
  for the US$15 (BOC NY) / US$25 (other US banks) full-amount-received charge.
- `S04` (BOC personal tariff code 210104021, effective 2015-04-01) carries the same US$15/$25
  figures but is published under the personal-service section.
- **Resolution:** both documents are official BOC publications. The `OUR` column in the cost ladder
  is presented as **conditional**: a personal customer must ask the branch whether OUR is offered
  and at what price (flag `S775-F05`). The ladder shows totals both with and without the OUR
  surcharge; neither is silently folded into the other.

### 2.3 IRC §988 vs §988(e) — personal transactions

- The statute (`S40`, govinfo 2023 US Code): `§988(a)(1)(A)` makes currency gain/loss ordinary;
  `§988(e)(1)` excludes personal transactions from §988; `§988(e)(2)` excludes personal FX gain
  unless it exceeds $200; `§988(e)(3)` removes §162/§212 income-producing accounts from the
  definition of personal transaction.
- **Resolution (`S775-F10`, interpretation flagged):**
  - Personal, non-income-producing CNY disposition: gain ≤$200 excluded; above $200, the personal
    exception keeps it out of ordinary §988 treatment and the residual is analysed under §1221
    (capital) while personal FX loss is nondeductible (§165(c)). The statute text is verified; the
    capital characterisation is a legal interpretation and is flagged, not silently applied.
  - Income-producing (§212, e.g. interest-bearing investment deposit) or trade/business (§162)
    disposition: no $200 exclusion; ordinary income/loss under §988(a)(1)(A).
- The cost ladder therefore shows **blank** for the user's personal tax cell (`S775-F02`,
  `S775-F03`): basis and marginal rate were not provided and are never inferred.

### 2.4 FEIE year

- `S41`: FEIE is US$132,900 for 2026 (up from US$130,000 for 2025). The 2025 figure appears in
  some older repo pages; the current-tax-year figure is 2026. FEIE covers wages for personal
  services only and does **not** reach currency gain or existing savings (`P18`).

### 2.5 FBAR threshold wording

- `S48` (FinCEN): the aggregate value of foreign financial accounts **exceeds** $10,000 at any
  time during the calendar year — strictly greater, aggregated across accounts. `P14`/`S775-F13`
  keep that wording; pages that say "at least $10,000" are wrong.

### 2.6 FBAR penalty ceilings

- Statute (`31 U.S.C. § 5321(a)(5)(C)`, V10 in `verify_2026.csv`): willful ceiling is the greater
  of $100,000 (statutory, inflation-adjusted) or 50% of the account balance.
- `S49` (eCFR `31 CFR 1010.821`, current as of 2026-11-06): non-willful $16,536; willful greater of
  $165,353 or 50% of the balance. The inflation-adjusted figures remain current; `P15` cites the
  eCFR table as the operative number.

### 2.7 PRC conversion tax — negative finding

- No official source imposes a PRC tax on converting an individual's own CNY to USD. The
  "considerable taxes" premise (as phrased by the user) is therefore **not established**; the
  largest identifiable candidate is the US §988 item plus the FX spread (`P11`, `S775-F01`). The
  audit records this as a negative finding, with sources, rather than inventing a conversion tax.

### 2.8 Form 3520 amounts

- `S44`: >$100,000 from a foreign person (individual); foreign corporation/partnership gifts
  >$20,573 for 2026. Older repo pages citing only $20,116 are the 2025 figure.

### 2.9 BOC ATM fee change (2026-11-11)

- `S06`: Mastercard/Visa overseas ATM fee rises from 0.5% ($3–$5) to 2.5% ($3–$40) effective
  2026-11-11; UnionPay stays ¥12 + 1% (max ¥112/tx). `M04` uses the UnionPay fee; the MC/Visa
  change is disclosed on the methods page.

### 2.10 Crypto prohibition

- `S29` (PBOC `银发〔2026〕42号`, 2026-02-06): crypto-related business activities are prohibited,
  RMB-pegged stablecoins and unapproved RWA banned; `银发〔2021〕237号` repealed. `M19` is listed as
  Prohibited with penalty anatomy `S19|S39`.

## 3. What is deliberately blank

- Intermediary/correspondent and US receiving-bank fees (`S775-F06`) — no official schedule.
- Counter cash price (`S775-F07`), offshore CNH spread (`S775-F08`) — not officially published.
- Exact Form 8938 penalty figures for a specific year (`S775-F09`) — range only.
- User's basis, marginal rate, funds type, hukou history (`S775-F01`–`F04`) — never inferred.

## 4. Verification method

- `scripts/verify_s775_site.py` re-reads every CSV, re-derives the cost ladder arithmetic from
  `S01` (ask 6.6903 / bid 6.6622), checks every `source_ids` value resolves to `s775_sources.csv`,
  checks that blank cells correspond to `UNVERIFIED`/conditional flags, audits the HTML pages for
  row counts, official-domain links and local anchors, and re-runs the site builder in `--check`
  mode for byte-identical freshness.
- The register is `data/s775_sources.csv` (51 records); the fetched-at timestamps are ISO-8601
  UTC on 2026-11-10.
