# Final integration audit — China Money

**Session:** `session-6907147a`  
**Branch:** `arena/6907147a-china3`  
**Review date:** 2026-11-10  
**Baseline:** `75b67d3` (`main`, merge of PR #21)

## 1. Scope and coordination

`COORDINATION.md` was read before work. The inherited `main` already contained multiple completed research layers and 640-row schedule. Open PRs #6, #8, #15 and #18 belong to earlier sessions and were not merged or overwritten. This session claimed only final integration, corrective schedule generation, the executive landing page, final review artifacts and deployment. Arena fixes the session to one branch, so the prompt’s per-task branch naming is not available; this remains logged as a process irregularity.

The inherited `S436-T8` was still marked in progress even though PR #21 had merged it. The final board update closes that administrative item.

## 2. Baseline verification performed

Before substantive edits, all of these completed successfully:

```text
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
python3 scripts/verify_deep.py
python3 scripts/test_costs.py
python3 scripts/build_cost_tables.py
python3 scripts/verify_cost_tables.py
python3 scripts/build_s436_site.py
python3 scripts/verify_s436_site.py
python3 scripts/build_cross_session_review.py --check
git diff --check
```

A passing inherited validator was not treated as proof that each narrative inference was correct. The substantive review below found two material problems that the structural checks had encoded rather than detected.

## 3. Material findings and corrections

| ID | Finding | Evidence reviewed | Integration action |
|---|---|---|---|
| FI-01 | The prior S436 model automatically added USD 25 `OUR` to personal, quota, property-sale and existing-USD wires. | [BOC corporate trade-services notice](https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html) is under `公司金融`; its notes describe optional full-amount service and conditions, including at least one intermediary for ordinary TT. It does not establish a universal personal e-banking charge. | Removed from all personal known-cost totals. Retained only as a conditional component for the corporate-dividend route, whose all-in total is now blank. |
| FI-02 | Narrative presented all individual CNY conversion gains over USD 200 as capital gain. | [IRS Pub. 525](https://www.irs.gov/publications/p525) states the capital-gain treatment for a **personal** foreign-currency transaction. [26 U.S.C. §988(c)(1)(C), (e)](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm) covers disposition of nonfunctional-currency deposits, exempts qualifying personal transactions, and excludes §162/§212 transactions from the personal definition. | Narrowed the dashboard and executive summary. Acquisition basis, dates, transaction character and tax remain unverified. |
| FI-03 | Bank board was a 2026-11-09 snapshot. | [BOC official board](https://www.boc.cn/sourcedb/whpj/enindex_1619.html), fetched in final review: timestamp `2026/11/10 07:32:39`; USD buying `666.22`, selling `669.03`, middle `671.88` per 100 USD. | Refreshed the primary schedule to ask `6.6903`, bid `6.6622`, computed bid/ask midpoint `6.67625`. All values remain explicitly dated. |
| FI-04 | A published-component total could be read as a guaranteed all-in personal cost. | [BOC personal tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html) states the personal wire/cable formula and notes agreements, discounts and local differences. [PBOC spread deregulation](https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/2810732/index.html) confirms bank pricing is not a fixed statutory spread. | Homepage and schedule disclose excluded receiving/intermediary/optional charges and fact-dependent tax. `Known cost` is never represented as a personalized all-in quote. |
| FI-05 | Multi-year resident quota calculations could be mistaken for forecasts. | [SAFE convenience-amount Q&A](https://www.safe.gov.cn/ningxia/2022/0929/1997.html) establishes documentary rules, not future exchange rates. | Labelled multi-year rows as constant-snapshot scenarios. They do not predict future bank quotes. |
| FI-06 | Operational steps previously inherited one route source even for U.S. reporting or BOC pricing statements. | IRS FBAR, STA/SAFE recordal, BOC board and U.S. CMIR official sources. | Step generator now assigns the proposition-relevant official source to those steps. |
| FI-07 | The repository retains conflicting historical pages from parallel sessions. | Inherited cross-session and S436 audit registers, plus current SAFE/IRS/BOC texts. | Primary navigation now uses the corrected schedule. Historical pages and their flags are preserved for review rather than silently rewritten. |

## 4. Official propositions directly re-fetched in this session

| Proposition | Official text checked | Result |
|---|---|---|
| Foreign-individual lawful RMB employment income | [SAFE Tianjin, 2026-07-13](https://www.safe.gov.cn/tianjin/2026/0713/3088.html) | Current Account Guidelines Art. 59: valid ID and transaction/source materials including tax evidence. The page does not itself prove an individual applicant’s bank classification. |
| USD 50,000 convenience amount | [SAFE Ningxia, 2022-09-29](https://www.safe.gov.cn/ningxia/2022/0929/1997.html) | SAFE says the annual convenience amount is not a universal annual limit; genuine lawful current-account transactions and open capital-account transactions have no amount limit, with documents above the convenience amount. |
| Personal BOC remittance charge | [BOC personal e-banking tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html) | Cross-border TT `1‰`, minimum `¥50`, maximum `¥260`; cable `¥80` HK/Macao/Taiwan and `¥150` elsewhere; notes allow agreement/discount/local differences. |
| BOC corporate full-amount option | [BOC corporate notice](https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html) | Standard U.S. `OUR` USD 25 and BOC-NY-account case USD 15 are conditional optional corporate-tariff components, not a verified universal personal-wire charge. |
| Emigrant-property staging | [SAFE Huifa [2014] No. 2, current modified text](https://www.safe.gov.cn/tianjin/2024/0903/2594.html) | Section VI removes the old SAFE-HQ filing and mandatory staged remittance; local approval remains, and a bank may remit once or in batches within approval. |
| Tax recordal | [STA/SAFE Announcement 2013 No. 40](https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html) | Listed single outbound payments above USD 50,000 generally require recordal, subject to Article 3 exceptions and later amendments. |
| FBAR | [IRS FBAR guidance](https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar) | U.S. person generally files when aggregate foreign accounts exceed USD 10,000 at any time in the calendar year; separate from Form 8938. |
| Form 8938 | [IRS comparison](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements) | Thresholds depend on filing status and U.S./abroad residence; Form 8938 does not replace FBAR. |
| Foreign earned income exclusion | [IRS FEIE](https://www.irs.gov/individuals/international-taxpayers/figuring-the-foreign-earned-income-exclusion) | 2026 maximum USD 132,900 per qualifying person; only qualifying foreign earned income and a filed return. It is not a deduction for moving savings. |
| U.S. personal FX gain | [IRS Pub. 525](https://www.irs.gov/publications/p525) and [26 U.S.C. §988](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm) | Qualifying personal gain over USD 200 is reported as capital gain under Pub. 525; §988 personal-transaction definition and facts control. |

Chinese-language official documents are paraphrased in English; the linked original controls.

## 5. Independent arithmetic verification

For target USD `U`, using only the timestamped BOC bid/ask and personal tariff:

```text
midpoint = (6.6622 + 6.6903) / 2 = 6.67625
spread USD = U × (6.6903 − 6.67625) / 6.6903
wire CNY = min(260, max(50, 0.001 × U × 6.6903))
wire + cable USD = (wire CNY + 150) / 6.6903
known cost = spread USD + wire + cable USD
```

`scripts/verify_final_integration.py` independently re-derives all 40 M01 rows with `Decimal`, rather than importing the generator. Reference results after rounding each displayed component to cents:

| Target | Spread | Personal wire/cable | Known cost | Net after known cost |
|---:|---:|---:|---:|---:|
| USD 10,000 | USD 21.00 | USD 32.42 | USD 53.42 | USD 9,946.58 |
| USD 100,000 | USD 210.01 | USD 61.28 | USD 271.29 | USD 99,728.71 |
| USD 400,000 | USD 840.03 | USD 61.28 | USD 901.30 | USD 399,098.70 |

Official sources for all rows: [BOC board](https://www.boc.cn/sourcedb/whpj/enindex_1619.html) and [BOC personal tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html). No corporate OUR fee is included.

## 6. Blank/unverified contract

The final gate checks:

- exactly 16 methods, 40 increments and 640 unique cost rows;
- 65 operational steps and at least seven final flags;
- every cost, method, step and final flag row has an official-domain URL;
- personal, quota, property and existing-USD rows have no corporate OUR charge;
- `UNVERIFIED` and `PROHIBITED` rows have blank all-in cost and blank net;
- partial/unverified/prohibited rows disclose missing variables;
- homepage contains all 40 M01 rows and per-row SAFE/BOC evidence links;
- local navigation in the homepage, final review and seven schedule pages resolves.

Existing validators separately check the inherited deep tables, source contracts, local links/anchors, tariff models and generated-page freshness.

## 7. Remaining irregularities (non-blocking)

Published on `final-verification.html`, `schedule-flagged-review.html`, `cross-session-review.html` and `deep-review.html`:

1. Personal bank/intermediary/receiver/optional-service all-in pricing is not universally published.
2. Account-holder FX classification and source-of-funds eligibility are unknown.
3. CNY acquisition basis/date and §988 transaction character are unknown; no U.S. FX-gain tax is invented.
4. Historical pages contain superseded/conflicting claims and remain visibly flagged.
5. Multi-year quota rows are constant-snapshot scenarios, not forecasts.
6. Some inherited official pages are HTTP-only or historical snapshots; link reachability is not a substitute for substantive review.

These items do not justify guessing and do not block publication of the corrected sourced model.
