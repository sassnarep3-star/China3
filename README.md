# China3 — getting money out of mainland China as a US citizen

A sourced research pack and two-part website answering one question:

> Personal money is sitting in a Chinese bank account and cannot be turned into USD without what looks like a large tax hit. What are the lawful ways to convert it, what does each really cost, and what is the least-penalty path for a US citizen?

**Live site:** https://sassnarep3-star.github.io/China3/
· editorial guide at `/`
· structured dashboard at [`/docs/`](https://sassnarep3-star.github.io/China3/docs/)
(published by GitHub Pages from `main`, root path).

---

## The finding

There is no Chinese "conversion tax". Wiring your own money home is not itself U.S. taxable income — but converting appreciated CNY can recognize a **U.S. §988 currency gain** (roughly 6–7% of the USD received for CNY acquired at the 2024/2025 IRS yearly averages), which is separate from, and usually larger than, every China-side fee. See [`us-fx-gain.html`](us-fx-gain.html) for the $10,000–$400,000 arithmetic. The balance is expensive to move because four unrelated things get confused with each other:

1. **Chinese capital controls** — a *permission* problem, not a tax problem.
2. **PRC income tax on whatever created the money** — 20% flat on property gains, interest, rent and dividends; nothing further on salary already taxed.
3. **US information-reporting penalties** — a willful FBAR violation is capped at the greater of **USD 165,353 or 50% of the account balance**, an order of magnitude larger than any FX spread.
4. **US foreign-currency gain on the conversion (IRC §988)** — not a fee, but a real U.S. income-tax component when the CNY appreciated since acquisition; itemized on [`us-fx-gain.html`](us-fx-gain.html) and cross-check flag **X-11**.

The annual USD 50,000 figure is a *convenience processing amount*, not a tax and not a universal cap on every balance. The cheapest lawful sequence is therefore: classify the money → fix US reporting first → then use the one Chinese channel with no amount ceiling (**emigrant property transfer**, 移民财产转移, PBC Order [2004] No. 16) or the one with no annual quota (**non-resident conversion of current-account income**, 个人外汇管理办法 art. 13).

Full reasoning: the editorial guide (`/index.html`) and the dashboard's **Playbook** page.

---

## The site

One Pages deployment, two complementary layers:

**Editorial guide** (root) — prose-first pages produced by the earlier sessions:

| Page | Content |
|---|---|
| `index.html` | Landing page, executive brief, recommended sequence |
| `routes.html` | 8 documented transfer routes compared |
| `methods.html` | 11 CNY→USD methods with pros, cons, cost, US impact |
| `china-rules.html` | SAFE/PBOC quotas, documentation, cash limits, penalties |
| `us-tax.html` | FBAR, Form 8938, FEIE, foreign tax credit, treaty, §988 |
| `tax.html` | Tax vs FX cost vs reporting, separated |
| `penalties.html` | Penalty and cost breakdown |
| `flagged-review.html` | Unverified items, deliberately blank |
| `us-fx-gain.html` | U.S. §988 currency-gain on converting appreciated CNY; $10,000–$400,000 ladder, IRS yearly averages, BOC board |
| `review.html`, `sources.html` | Case facts, source register, method |

**Cost tables** (`cost-tables.html`) — the money answers, to the cent:

| Section | Content |
|---|---|
| Master ladder | $10,000 → $400,000 in $10,000 steps for the recommended route: CNY needed, spread, wire + cable, total, cost %, net received |
| Every route at six amounts | all 20 routes side by side at $10k / $50k / $100k / $200k / $300k / $400k |
| Penalty ladders | what each unlawful route costs if caught, at every amount, plus the US reporting ceilings |
| Route by route | a full 40-step ladder and a numbered step-by-step procedure per route |
| Model inputs | all 32 inputs (`CI01`–`CI32`) with value, status and source |
| Flagged | `IR-024`–`IR-029`, each with the official link |

Headline: **$53.45 on $10,000, $902.86 on $400,000** — 0.535% falling to 0.226%, because the 1‰ wire fee
hits its CNY 260 cap at about $38,853. No Chinese tax applies to converting your own principal; the
six-figure risk is a willful FBAR penalty (50% of the balance) or a Chinese 30%–100% penalty on an
unlawful route. Data: `data/cost_inputs.csv`, `data/cost_methods.csv`, `data/cost_ladder.csv`,
`data/cost_steps.csv`, `data/cost_sources.csv`. Checks: `scripts/verify_cost_tables.py`
(re-derives every cell from the inputs with independent arithmetic) and
`.github/workflows/cost-model-verify.yml`.

**Data dashboard** (`docs/`, generated) — every row is structured data that a script can check:

| Page | Content |
|---|---|
| `docs/index.html` | Executive summary, top-5 ranked routes, the four numbers |
| `docs/playbook.html` | Nine ordered steps and the sequencing table |
| `docs/channels.html` | 22 channels — searchable, filterable, expandable |
| `docs/taxes.html` | US / PRC / treaty exposure, `rule` vs `analysis` |
| `docs/penalties.html` | Five cost layers, 15 provisions, cost model, calculator |
| `docs/flagged.html` | 19 flagged items with status, impact and sources |
| `docs/sources.html` | 27 sources, tiered, with the proposition each supports |
| `docs/methodology.html`, `docs/audit.html` | Method, and the audit of this repository |

The dashboard makes no runtime network calls: `docs/assets/data.js` is generated with all five JSON files inlined, so there is no fetch, no CDN and no external font.

---

## Data and pipeline

| Path | What it is |
|---|---|
| `data/sources.json` | 27 sources: publisher, tier, URL, proposition supported, date checked |
| `data/channels.json` | 22 CNY→USD routes: status, cap, requirements, pros, cons, verdict |
| `data/taxes.json` | 25 tax items split US / PRC / treaty |
| `data/penalties.json` | Five cost layers, 15 provisions, cost model, scenarios |
| `data/flagged.json` | 19 items that are blank, ambiguous, or depend on the reader's facts |
| `scripts/validate_data.py` | Enforces the "official source or explicit flag" contract |
| `scripts/check_links.py` | Links, anchors, URL hygiene, bundle freshness |
| `scripts/build_site.py` | Builds `docs/`, refusing to build on a contract violation |
| `VERIFICATION.md` | Per-URL verification log, including rejected URLs |
| `REPO_AUDIT.md` | Audit of the repository as found |
| `COORDINATION.md` | Task board, claims, handoffs, PR record |

```bash
python3 scripts/validate_data.py      # data contract
python3 scripts/build_site.py         # regenerate docs/
python3 scripts/check_links.py        # links, anchors, freshness
python3 scripts/check_links.py --fetch  # optional: HTTP-check every source URL
python3 scripts/build_cost_tables.py    # regenerate the cost tables + CSVs
python3 scripts/verify_cost_tables.py   # re-derive every cost cell
```

No third-party dependencies. `.github/workflows/ci.yml` runs the contract check, fails if `docs/` is stale, and checks every external URL. `.github/workflows/pages.yml` validates root navigation and deploys to Pages.

To browse locally:

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```

---

## The rules this project obeys

1. **No number without an official source.** Every figure links to a statute, regulation, agency page or treaty provision.
2. **Blank beats guessed.** Unconfirmed values are empty, marked `unverified`, and published on the *Flagged for review* page — no industry averages, no estimates.
3. **Analysis is labelled.** Reasoning rather than quotation is marked `analysis` and flagged.
4. **The check is executable.** `validate_data.py` fails the build if a row states a cap without marking it verified, or asserts a consequence without a source.

---

## Scope and limits

- Covers **individual** balances in a Chinese bank account. Corporate structures, QDII quotas and outbound-investment projects appear only as they bear on an individual.
- Four determinations depend on documents only the account holder has: the bank's `境内个人`/`境外个人` classification, whether a cancelled PRC household registration exists, when the balance was acquired relative to any emigration, and what created the money. All four are itemised on the flagged page.
- Retail FX spreads and wire fees are commercial, not regulatory, and were deliberately **not** estimated. The calculator ships with no default rates.
- This is research, not legal, tax or investment advice. Have a US tax adviser and a PRC-qualified adviser review the specific file before filing or applying.

## S436 official-source schedule (2026-11-09 snapshot)

A separately namespaced, independently verified schedule is available at
[`schedule-dashboard.html`](schedule-dashboard.html) and is linked from the live landing page.
It adds **16 methods × 40 USD targets ($10,000 through $400,000) = 640 rows**, 65
source-linked compliance-first steps, 36 official sources, and 20 visible review flags.

- [`schedule-cost-10k-400k.html`](schedule-cost-10k-400k.html) — mobile-first filterable cost table; the most important fields (known published cost, net after known cost and missing-cost disclosure) appear first.
- [`schedule-methods.html`](schedule-methods.html), [`schedule-steps.html`](schedule-steps.html), and [`schedule-penalties.html`](schedule-penalties.html) — eligibility, pros/cons, procedure, tax/reporting and enforcement separation.
- [`schedule-flagged-review.html`](schedule-flagged-review.html) — 20 inherited/current irregularities and the official source for manual review.
- [`schedule-sources.html`](schedule-sources.html) — official source register.

This schedule uses the 2026-11-09 BOC board snapshot (USD ask `6.6924`, bid `6.6643` CNY/USD), BOC's published personal wire/cable tariff, and its published standard U.S. `OUR` option (`$25`) only where the source directly supports the component. Its M01 **published-component** result is **$78.41 at a $10,000 target** and **$926.02 at a $400,000 target**; these are not personalized all-in quotes. Receiving/intermediary charges, bank/account eligibility, underlying unpaid tax, tax-return/cure cost, live alternatives and other unquoted variables are blank, never assumed to be zero. This disclosure is intentional; it also explains why snapshots from the separately maintained historical cost tables should not be silently treated as interchangeable quotes.

Rebuild and verify it with no third-party dependency:

```bash
python3 scripts/build_s436_site.py
python3 scripts/verify_s436_site.py
```

The verifier checks every amount/method combination, re-derives published formula cells,
requires official-source domains and links, enforces blank unverified all-in amounts, verifies
the 20 flags, and checks the generated local navigation. GitHub Actions runs the same check in
`.github/workflows/s436-verify.yml`.

## Licence

No licence was present when this work started and none was added, because choosing one is the repository owner's decision. Content is cited to its sources under those sources' own terms.

---

## Deep research pass (integration session `session-c703e38c`)

A second, deeper research pass was integrated without altering any earlier page. All
deep-research outputs use distinct filenames so that merging `main` never overwrites
another session's files.

| Page | Contents |
|---|---|
| `deep-executive-summary.html` | Executive summary, ranked recommendation, requirement coverage |
| `deep-china-rules.html` | 50 China-side FX/tax rules, one official link per row |
| `deep-us-tax.html` | 28 IRS / FinCEN / Treasury / eCFR rules, one official link per row |
| `deep-channels.html` | 35 conversion channels with pros, cons, limits, penalty exposure |
| `deep-penalty.html` | Conversion penalty decomposed into 35 verifiable cost layers |
| `deep-findings.html` | 22 sourced findings and analysis |
| `deep-review.html` | Clearly labelled **Flagged for Review** register (23 items, each with a source link) |
| `deep-sources.html` | 85 official sources with verification method |

Machine-readable data: `data/china_rules.csv`, `data/us_rules.csv`, `data/channels.csv`,
`data/penalty.csv`, `data/findings.csv`, `data/flags.csv`, `data/sources.csv`,
`data/deep_sources.json`. Research memos: `research/*.md`. Full executive summary:
`EXECUTIVE_SUMMARY.md`.

Build and verify locally:

```sh
python3 scripts/build_deep_site.py && python3 scripts/integrate_deep.py && python3 scripts/verify_deep.py
python3 -m http.server 8000 --bind 0.0.0.0
```

Headline findings: a passport-holding U.S. citizen is generally a 境外个人 whose FX
purchase from legitimate, tax-documented RMB income is not limited by the USD 50,000
convenience amount (but the 2008 State Council regulation defines 境内个人 differently —
see IR-007); no official source establishes a general tax on converting personal CNY
principal; the largest single monetary risk is a willful FBAR penalty of up to 50% of the
account balance; and `银发〔2026〕42号` repealed `银发〔2021〕237号`.

## Final integration addendum (2026-11-10, session `arena/3fcb5029-china3`)

Additive only. New page [`us-fx-gain.html`](us-fx-gain.html) quantifies the potential U.S. §988 foreign-currency-gain tax on converting appreciated CNY at every $10,000 step from $10,000 to $400,000 (cross-session finding **X-11**), derived solely from recorded official values (IRS yearly averages, the dated 2026-11-09 BOC board, 26 U.S.C. §988 via govinfo, IRS Pub. 525/54). Editorial corrections applied: methods/us-tax wording on "not a taxable event" (X-06), the cash-carry limits row (X-08), the §988 personal-transaction character marked conditional in `data/penalty.csv` P25 / US-rules U17 / findings F22 (X-07), the BOC 全额到账 quote completed in P11 (X-05, corporate tariff; personal e-banking applicability still flagged unverified), and the BOC tariff date typo `2024-11-01` → `2014-11-01` (X-14, values unchanged). Flags IR-012 (board half-spread 0.2104%) and IR-015 (CFETS parity 6.7188 for 2026-11-09) are annotated as narrowed/closed for that date; both stay `needs review`. Open PRs #15 (flagged X-15/X-16), #18, #8 and #6 were left open for their owners; this session merged none of them.
