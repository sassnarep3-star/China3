# China Funds Transfer Guide

A static, official-source-backed research dashboard about lawful ways to move personally owned funds from a mainland China bank account to the United States. It separates the Chinese foreign-exchange process, tax on the source of funds, bank conversion/remittance pricing, and U.S. tax/account reporting.

## Site pages

- `index.html` — executive brief, recommended sequence, and unified navigation to all pages.
- `routes.html` — transfer-route comparison table, with source links in every row.
- `tax.html` — Chinese tax / FX costs / U.S. tax and reporting distinctions, with source links in every row.
- `review.html` — unresolved case facts and irregularities; unverified amounts remain blank.
- `sources.html` — official source register and research method.
- `methods.html` — 11 CNY→USD conversion methods with pros, cons, costs, U.S. impact, and official sources per row.
- `china-rules.html` — China FX rules: SAFE/PBOC quotas, documentation, cash limits, circumvention penalties.
- `us-tax.html` — U.S. tax &amp; reporting: FBAR, Form 8938, FEIE, Foreign Tax Credit, treaty, IRC §988.
- `penalties.html` — penalty &amp; cost breakdown with verified amounts and flagged blanks.
- `flagged-review.html` — 9 unverified items deliberately left blank, with suggested official sources.

## Core finding

SAFE’s equivalent USD 50,000 annual individual convenience amount is not itself a tax or a universal annual legal cap. Official SAFE guidance describes processing of authentic, eligible current-account transactions above that amount with transaction evidence. This does not establish that an arbitrary personal capital/savings transfer is eligible. SAFE also prohibits evading controls by splitting among people. Special outbound personal-property procedures apply only in qualifying emigration/inheritance cases and require approvals and supporting documents. No official source reviewed establishes a flat tax on converting the principal of every personal CNY bank balance to USD. Tax, FX spread, bank fees, and documentation requirements must be distinguished.

For a U.S. citizen, worldwide-income rules and independent foreign-account reporting may apply. FBAR and Form 8938 are not the same as income tax or permission to remit funds. See the linked IRS sources and consult a qualified China/U.S. cross-border tax adviser for individual facts.

## Run locally

This is plain static HTML/CSS and has no package install or build step. From the repo root:

```sh
python3 -m http.server 8000 --bind 0.0.0.0
```

Visit `http://localhost:8000` locally. GitHub Pages can serve the root directly. An Actions workflow is provided to publish from `main` when repository Pages settings use GitHub Actions.

## Research limits

This repository did not contain case records, tax assessments, bank fee schedules, account details or an existing app. No exact transfer amount, conversion rate, fee, Chinese tax, U.S. tax or approval eligibility can be confirmed without those records. Numerical values not established by official sources are left blank and surfaced on the **Flagged for review** page. This guide is informational, not legal, banking or tax advice. Sources and dates are listed on the source register; rules and local bank procedures should be reconfirmed before a transaction.
