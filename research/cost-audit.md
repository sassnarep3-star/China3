# 2026-11-09 integration and cost audit

## Repository actually inspected

This checkout was **not empty**. At starting commit b1dc441 it already contained multiple merged research passes, 84 entries in the deep source register, 35 channel rows, generated editorial/deep/docs dashboards, three workflows and six validation/build scripts. The historical REPO_AUDIT.md describes an earlier initial checkout, not today's state. No prior work was deleted. The current Pages API reports main:/ with legacy build type, not /docs-only deployment.

Inspected the coordination board before claiming work; claimed additive cost files and final integration scope and pushed claim commit before implementation. Fixed Arena branch requirement takes precedence over the requested alternate branch names. No competing current claim found for the cost-file scope. First pull of the assigned remote branch failed because it did not yet exist; pulled/rebased origin main before the initial branch push. No merge conflict and no work discarded.

## New research actually read

Retrieved with fetch_page on 2026-11-09:

* SAFE Tianjin, https://www.safe.gov.cn/tianjin/2024/0621/2529.html — full text. Overseas individuals' lawful current-account RMB income: valid identity and transaction-valued source materials including tax documents. Foreign permanent-resident ID holders have the annual convenience-amount provision. Does not certify any particular customer's eligibility or tax liability.
* SAFE Ningxia, https://www.safe.gov.cn/ningxia/2022/0929/1997.html — full text. USD 50,000 convenience amount is not an absolute annual limit for lawful documented current-account and opened capital-account transactions. Does not open unrestricted overseas investment/capital flight.
* BOC, https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html — full text fee table. Effective-date heading 2014-11-01. Wire charge 1‰, CNY 50 minimum/260 maximum; telecommunication CNY 80 HK/Macao/Taiwan, 150 elsewhere. Exceptions for agreements/promotions/local tariffs. Conditional derived single-wire formula only; no current quote, FX price, intermediary fee or tax established.
* IRS, https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates — full text. USD normally functional currency; relevant amounts translated at applicable transaction rates. Does not provide a flat tax on remittances.

Rejected exploratory URL https://www.boc.cn/en/pbservice/pb4/200806/t20080626_1323970.html: redirected to an official error page stating requested page does not exist. HTTP success is not substantive verification.

Publication 525 https://www.irs.gov/publications/p525 returned chunk 0 of 57; it was not fully read. No new foreign-currency-specific tax assertion verified from that partial retrieval. Earlier sources remain inherited with historical verification labels. This session does **not** certify every legal sentence in all earlier pages as currently correct.

Search results from nonofficial fee explainers were not used as numeric evidence. No retail FX rate, arbitrary spread percentage, promotion, hypothetical tax rate, or invented per-method total was inserted.

## Cost coverage and unresolved instructions

The request for exact USD estimates conflicts with the instruction to leave unconfirmed values blank. Source integrity takes priority: 40 amounts ($10,000 through $400,000), each for all 35 inherited channels, are present in data/cost-grid.csv with numeric unknowns blank and per-row official context links. Those links support context only, not a quote. All-in costs for prohibited, inapplicable or unquoted methods cannot be responsibly estimated. The conditional BOC tariff formula is explicitly labeled derived arithmetic and shown in 40 separate rows. No exchange rate is inferred.

Operational steps are conditional research checklists, not a certified bank procedure. Prohibited channels receive no execution instructions. Existing pros/cons are preserved as inherited research. Genuine transfers require identity, source documentation and bank authorization; the research session cannot execute a transfer without those.

## Tests

Ran existing validate_data.py, build_site.py, check_links.py and verify_deep.py: passed structural data and local-link checks. New test_costs.py checks 1,400 unique amount/channel pairs, blank unknowns, 1,446 individually linked data rows, tariff boundary arithmetic and deterministic regeneration. No test can establish substantive current legal accuracy from a domain allowlist. External validity is limited to the pages actually read above.

## Irregularities

Published COST-01 through COST-06 on cost-review.html, prominently linked from the landing page and costs page. Historic review pages remain reachable. Claims of a universally cheapest route, zero tax, current all-in USD price, or full fresh line-by-line verification are expressly not made. Full legal re-verification and bank/customer-specific pricing remain unresolved, non-blocking review items.
