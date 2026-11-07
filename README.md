# China Funds Transfer Guide

A static, official-source-backed research dashboard about lawful ways to move personally owned funds from a mainland China bank account to the United States. It separates the Chinese foreign-exchange process, tax on the source of funds, bank conversion/remittance pricing, and U.S. tax/account reporting.

## Site pages

- `index.html` — executive brief and recommended sequence.
- `routes.html` — transfer-route comparison table, with source links in every row.
- `tax.html` — Chinese tax / FX costs / U.S. tax and reporting distinctions, with source links in every row.
- `review.html` — unresolved case facts and irregularities; unverified amounts remain blank.
- `sources.html` — official source register and research method.

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

---

## Deep research pass (final integration session)

A second, deeper research pass was integrated from branch `arena/c703e38c-china3`.
All content above is preserved; the following pages and data were added.

### Added site pages

| Page | Contents |
|---|---|
| `executive-summary.html` | Executive summary of important details, ranked recommendation, full requirement-coverage map |
| `china-rules.html` | 50 China-side FX/tax rules, line by line, one official link per row |
| `us-tax.html` | 28 IRS / FinCEN / Treasury / eCFR rules, one official link per row |
| `channels.html` | 35 conversion channels with pros, cons, limits and penalty exposure |
| `penalty.html` | Conversion penalty decomposed into 35 separately verifiable cost layers |
| `findings.html` | Analysis and findings |
| `review.html` (appended) | Full "Flagged for Review" irregularity register (23 items) |
| `sources.html` (appended) | Official source register for the deep-research pass |

The first session's `routes.html` and `tax.html` remain published as complementary reading.

### Machine-readable data and verification

- `data/china_rules.csv`, `data/us_rules.csv`, `data/channels.csv`, `data/penalty.csv`,
  `data/findings.csv`, `data/flags.csv`, `data/sources.csv`, `data/sources.json`.
- `scripts/build_site.py` regenerates every deep-research table from those CSVs.
- `scripts/integrate.py` rebuilds shared navigation and the appended sections additively.
- `scripts/verify.py` audits every row for an official source link, rejects non-official
  domains, enforces blank values for UNVERIFIED rows, checks HTML/CSV row counts, checks
  every local link in every HTML page, and confirms all flags and source ids are published.

Run the checks locally with:

```sh
python3 scripts/build_site.py && python3 scripts/integrate.py && python3 scripts/verify.py
python3 -m http.server 8000 --bind 0.0.0.0
```

### Headline findings of the deep pass

- A passport-holding U.S. citizen is generally a **境外个人 (foreign individual)** under
  PBOC Decree [2006] No. 3 Art. 37. Under SAFE's Current Account Guidelines Art. 59, a
  foreign individual buys FX with an ID plus **source-of-funds** evidence (including a tax
  certificate), and SAFE's own Q&A handbook says this has **no annual quota limit**. The
  USD 50,000 figure that dominates online advice may therefore not be the binding
  constraint — but the 2008 State Council regulation defines 境内个人 differently, so the
  account-opening bank must confirm the classification (IR-007).
- No official source reviewed establishes a flat Chinese **tax on converting** personal
  savings principal. The perceived "considerable taxes" most plausibly combine
  source-of-funds income tax and tax-clearance documents, bank spread and wire fees, and
  U.S. information-reporting exposure.
- The largest single monetary risk is a **willful FBAR penalty of up to 50% of the account
  balance**; 2026 inflation adjustments were cancelled, so the 2025 amounts
  ($16,536 / $165,353) still apply.
- `银发〔2026〕42号` (in force 2026-02-06) **repealed** `银发〔2021〕237号`; any advice
  citing the 2021 notice is stale.
- Illegal channels turn a documentation problem into 30%–100% administrative fines plus
  criminal exposure under Criminal Law Art. 225.

### Coordination

`COORDINATION.md` is the shared task board. It records both sessions' claims, the
`add/add` conflict resolution (prior session's board preserved verbatim), the rebase
flattening incident, per-task verification logs, irregularities, PR link, merge result and
Pages deployment confirmation.
