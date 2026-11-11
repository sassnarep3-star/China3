# DFF3 executive-summary re-check (2026-11-11)

## Scope and outcome

This pass re-read the executive summary’s decision-critical claims about the alleged conversion tax, foreign-individual purchase eligibility, the BOC rate/tariff, U.S. currency gain, and U.S. foreign-account reporting. It changed only `EXECUTIVE_SUMMARY.md` and this audit record. It did not re-derive other methods, change the generated dashboard, or determine any individual's tax or eligibility.

**Outcome:** the summary now (a) does not treat the alleged charge as a verified tax, (b) avoids a blanket claim that currency conversion is tax-free, (c) presents the foreign-resident-card/“domestic individual” overlap as unresolved for the holder, (d) replaces the stale 10 November L01/L03 examples with the independently computed 11 November amounts, and (e) labels historical-rate currency differences as arithmetic scenarios—not tax due.

## Re-read primary sources and claims

| Claim checked | Official source and what it says | Use and limitation |
|---|---|---|
| Current conversion quote | [BOC USD exchange-rate board](https://www.boc.cn/sourcedb/whpj/enindex_1619.html): USD row, buying 666.30, selling 669.11, BOC “Middle Rate” 671.91; publication time 2026/11/11 10:25:02. | Treats 669.11 per 100 USD (=6.6911 CNY/USD) as an example BOC selling rate only. A published board is not the user's bank quote. The model uses arithmetic midpoint of bid/ask, not the separately published “Middle Rate.” |
| Example outgoing wire tariff | [BOC personal e-banking transfer/remittance tariff](https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html): cross-border telegraphic transfer at 1‰, minimum CNY 50, maximum CNY 260, plus CNY 150 cable fee for destinations outside Hong Kong/Macau/Taiwan. The tariff notes agreements/promotions/local differences may apply. | Used only for a comparable modeled outgoing wire. Does not establish the user's bank's price or intermediary/beneficiary bank charges. |
| Foreign individual's current-account income purchase | [SAFE Tianjin, 2026 Q&A (08)](https://www.safe.gov.cn/tianjin/2026/0713/3088.html): quotes Art. 59 of 汇发〔2020〕14号: a foreign individual’s lawful current-account RMB income earned in China can be bought into foreign currency at a bank using valid identity and transaction-specific source documents, including tax documents. | Supports a documented-income route; not a finding that the holder's funds qualify or that no tax on prior income is due. |
| Annual convenience-amount eligibility | [SAFE Tianjin, 2024 Q&A (09)](https://www.safe.gov.cn/tianjin/2024/0621/2529.html): says foreign individuals holding a Foreign Permanent Resident ID Card apply the annual purchase convenience amount. | Does not answer this user's status because no status/residence details were given. |
| Meaning and scope of the USD 50,000 annual amount | [SAFE Ningxia, 2022 Q&A (08)](https://www.safe.gov.cn/ningxia/2022/0929/1997.html): says the amount is a convenience-processing amount, not a general yearly transaction ceiling, and documents are required above it. The question and cited Arts. 54–57 are framed for 境内个人 (“domestic individuals”). | The general no-limit statement should not be silently extended to every foreign-individual category. The summary flags the scope question rather than resolving it. |
| Residence definition / review / penalties | [State Council Foreign Exchange Regulation, Decree 532](https://www.safe.gov.cn/safe/2008/0806/5321.html): Art. 5 states current international payments and transfers are not restricted; Art. 12 requires a real and lawful current-account basis and reasonable document review; Arts. 39–45 specify penalties for listed violations; Art. 52(2) defines 境内个人 to include Chinese citizens and foreigners who continuously reside in China at least one year. | Art. 5 does not by itself prove there is no tax on a specific underlying transaction. Art. 52(2), together with the SAFE foreign-individual guidance, raises a category/scope question that needs written bank/SAFE confirmation. |
| Full individual FX processing rules | [SAFE Current-Account FX Business Guidelines (2020 edition), full text republished by MOFCOM](https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html): Arts. 54–59 describe convenience amount, domestic/foreign individual purchasing rules, and source/tax evidence; Art. 60 permits re-conversion of unspent RMB with original exchange slip within 24 months; Arts. 64–65 give distinct remittance procedures for domestic and foreign individuals; Art. 68 allows banks to reject transactions they cannot verify. | Cited for route categories and documentation only. Rules do not determine the outcome of an unsubmitted personal case. |
| Sale of onshore commercial residential property by a foreign individual | [SAFE Anhui operating guide, section 8](https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf): §8 “境外个人转让境内商品房所得资金购汇汇出” lists identity, property-transfer contract/registration documents, and tax certificate. Net amount eligible to remit is limited to sale price less taxes included in the transfer; co-owners are limited to their share; ownership transfer must be registered. | Supports the property-sale row only for the official scope (foreign individual selling domestic 商品房). Does not apply to every property or owner. |
| Inheritance / emigrant-property route | [PBOC/SAFE Individual Property Transfer Measures](https://m.safe.gov.cn/safe/2004/1116/5461.html) (PBOC Announcement [2004] No. 16), Arts. 2, 5–11: defines emigration and inheritance transfers, jurisdiction by former hukou/decedent hukou, approval, proof of source/rights/tax, and remittance to applicant's own foreign account. [SAFE Tianjin updated notice](https://www.safe.gov.cn/tianjin/2024/0903/2594.html) (汇发〔2014〕2号 as modified): changes approval/processing steps, including removal of the prior >RMB 500,000 central filing step and emigration staged-remittance requirement. | Supports only the statutory immigrant-property/inherited-property categories and specified approval process—not general savings, gifts, or sale proceeds. |
| Underlying Chinese income-tax categories | [PRC Individual Income Tax Law, National Taxation Administration](https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html): Arts. 1–3 establish tax residence and income categories/rates; Art. 6 provides category-specific taxable-income calculations. | Supports the distinction between tax on the underlying income/transaction and bank FX/wire charges. No personal liability is computed here. |
| IRS exchange-rate handling | [IRS yearly average currency exchange rates](https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates): 2024 China Yuan annual average 7.189; IRS says it has no official exchange rate, generally accepts a posted exchange rate used consistently, and notes that some transactions can create FX gain/loss. | The yearly average is used only as a transparent hypothetical acquisition basis; it is not presumed to be the user's acquisition basis or the rate appropriate to every tax item. |
| U.S. tax characterization of currency | [26 U.S.C. §988, U.S. Government Publishing Office](https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm): §988(c)(1)(C) includes dispositions of nonfunctional currency, including bank deposits; subsection (e) has an individual personal-transaction rule and a $200 gain exception threshold. | The model’s gross exchange difference is not asserted to be taxable income. Actual characterization, personal/business purpose, tax basis, timing, and other rules require a qualified tax professional. |
| FBAR and Form 8938 | [IRS comparison of Form 8938 and FBAR](https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements): different reportable-person, threshold, filing, and asset rules; Form 8938 does not replace FBAR. [FinCEN FBAR page](https://www.fincen.gov/report-foreign-bank-and-financial-accounts): U.S. persons with a financial interest in or signature authority over foreign accounts file if aggregate value exceeds $10,000 at any time during the calendar year. | Summary points to the official comparison rather than applying thresholds without residence, account, filing status, signature authority, and tax-year facts. |

## Cost-model check

Inputs and convention are recorded in `data/76e_sources.csv`, `data/76e_costs.csv`, `scripts/build_76e_site.py`, and `research/76e-verification.md`. The 76e validator was run locally and passed: 40 increments were recomputed, and applying the same convention to the 10 November BOC board reproduces all 80 published L01/L03 cells to the cent.

For the 11 November BOC quote:

- `bid = 6.6630` and `ask = 6.6911` CNY/USD; model midpoint = `(bid + ask) / 2`.
- FX spread cost = `USD amount × (ask − midpoint) / ask`.
- CNY wire fee = `min(max(USD amount × ask × 0.001, 50), 260) + 150`.
- USD wire fee = `CNY wire fee / ask`; L01 total = spread + wire fee; L03 = wire fee only.
- The illustrative 2024-basis FX difference = `USD amount × (1 − 6.6911 / 7.189)`.

The key cent-exact outputs in `data/76e_costs.csv` are:

| Amount | L01 buy+wire | L03 wire-only | 2024-basis arithmetic difference |
|---:|---:|---:|---:|
| $10,000 | $53.42 | $32.42 | $692.59 |
| $50,000 | $166.27 | $61.28 | $3,462.93 |
| $100,000 | $271.26 | $61.28 | $6,925.86 |
| $200,000 | $481.24 | $61.28 | $13,851.72 |
| $300,000 | $691.22 | $61.28 | $20,777.58 |
| $400,000 | $901.20 | $61.28 | $27,703.44 |

All are modeled BOC known costs/exchange arithmetic, not a bank quote, transfer net-proceeds promise, or tax liability. The model excludes intermediary/recipient charges and any income/property tax. The 2024 basis is hypothetical.

## Verification performed

- Re-read the official pages listed above on 2026-11-11 using the connected page retrieval tool. It returns page content; it does not report HTTP response codes, so none are asserted.
- Ran `python3 scripts/verify_76e.py`: PASS (40 rows recomputed; previous 80 L01/L03 cells reconciled; page/CSV parity, citations, and local links checked).
- Ran `python3 scripts/e347_verify.py`: PASS (440 cost rows, 11 routes, 659 sourced table rows, 380 blank values flagged, local links resolved).
- Ran `python3 scripts/verify_final_integration.py`: PASS.
- Ran `python3 scripts/verify_m5f19_site.py`: PASS (10 checks, including 40 cost totals and 160 ladder components).
- Ran `python3 scripts/validate_data.py`: OK; `python3 scripts/check_links.py`: OK (external HTTP fetches skipped by this offline validator).

## Remaining unknowns / flags

- The source and legal name of the alleged “considerable taxes” are unknown. No assessment or quote was provided.
- The user’s account holder, residence/immigration category, CNY provenance, acquisition dates/basis, tax history, intended amount, bank, and receiving-bank details are unknown.
- BOC’s public tariff is an illustrative benchmark. Actual bank, local, agreement, correspondent and receiving-bank prices require a written quote.
- No conclusion is made about the user’s PRC or U.S. tax liability, SAFE eligibility, approval, penalties, or exact net amount.
- Other route cost estimates on the general dashboard are based on a 2026-11-10 rate snapshot and should be treated as dated examples; current rates require recalculation at execution.
