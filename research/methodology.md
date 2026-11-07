# Research and verification methodology

**Checked:** 2026-11-07. **Repository:** China3. **Purpose:** provide a conservative, official-source overview of CNY-to-USD conversion and funds transfer from mainland China to the United States.

## Source standard

1. Prioritize primary Chinese regulators/tax authorities (SAFE, PBOC, State Taxation Administration) and U.S. authorities (IRS, FinCEN). Each finding in the site links to the relevant official source register entry and original webpage/document.
2. Do not use commercial blogs, forums, news articles or anecdotal bank reports as proof of a rule or tax rate.
3. Read official source text where accessible; search result snippets were used only to locate likely official pages. Retrieved source text was checked for the claims cited in the executive summary, route table, tax table and source register. Sources not directly confirmed with full text are marked by case-specific uncertainty or flagged in the review page.
4. The SAFE English pages contain an official notice that their English translation is reference-only and the Chinese original prevails if meaning differs. This is stated on the source page and highlighted in the dashboard.
5. Date all research as a snapshot. Older official rules are clearly dated and should be confirmed against current bank/SAFE practice before reliance.

## Claim discipline

- Every route/tax/review table row includes a source link. Where the site contains an unknown amount, eligibility, current fee, rate or checklist, it is left blank / labeled unverified and described on **Flagged for Review**.
- USD 50,000 is described as an individual FX facilitation quota (not a tax and not a universal hard cap), following SAFE sources. Transactions above the amount are not described as automatically approved: authenticity and transaction category matter.
- A general personal remittance tax was not identified in the official materials reviewed. This is worded as a bounded research finding, not proof that the user owes no tax. PRC individual income-tax law covers specified income categories; the source and tax history are unknown.
- The 2013 SAFE/SAT external-payment tax-filing rule is described narrowly: particular outward-payment categories by domestic payers over the threshold. It is explicitly not presented as a universal tax on a self-transfer.
- U.S. income tax and foreign account reports (FBAR, Form 8938, Form 3520) are separated. Reporting is not mislabeled as tax.
- Prohibited or risky options are not instructions; quota splitting, false documents and underground banks are excluded as non-compliant routes and flagged against official SAFE prohibitions/enforcement examples.
- No individual advice, legal conclusion, guaranteed bank outcome, tax calculation, or current quote is claimed.

## Repository review

The initial checkout contained only a short README and no existing code/data/site. No pre-existing calculations, tax assertions, conversion endpoints, or source files were found to verify. This session adds a static informational site and source-linked research. The site has no external runtime dependencies or user-data collection.

## Validation to run before publishing

- `python3 scripts/validate_site.py` checks required pages, local navigation targets/fragments, official source hosts, and that all data rows in the comparison/review tables cite a source.
- The local preview server returned HTTP 200 for all five HTML pages, the stylesheet, and the full analysis page; mobile behavior was reviewed through responsive CSS rules.
- GitHub Actions runs the validator on pull requests and pushes to `main`. The repository's pre-existing GitHub Pages configuration is legacy branch publishing from `main` at the repository root; the PR merge is the publishing event. Confirm the actual live URL after merge before claiming publication success.
