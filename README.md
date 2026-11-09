# China3 — getting money out of mainland China as a US citizen

A sourced research pack and two-part website answering one question:

> Personal money is sitting in a Chinese bank account and cannot be turned into USD without what looks like a large tax hit. What are the lawful ways to convert it, what does each really cost, and what is the least-penalty path for a US citizen?

**Live site:** https://sassnarep3-star.github.io/China3/
· editorial guide at `/`
· structured dashboard at [`/docs/`](https://sassnarep3-star.github.io/China3/docs/)
(published by GitHub Pages from `main`, root path).

---

## The finding

There is no Chinese "conversion tax", and no US tax on wiring your own money home. The balance is expensive to move because three unrelated things get confused with each other:

1. **Chinese capital controls** — a *permission* problem, not a tax problem.
2. **PRC income tax on whatever created the money** — 20% flat on property gains, interest, rent and dividends; nothing further on salary already taxed.
3. **US information-reporting penalties** — a willful FBAR violation is capped at the greater of **USD 165,353 or 50% of the account balance**, an order of magnitude larger than any FX spread.

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
| `review.html`, `sources.html` | Case facts, source register, method |

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

## The priced layer — `cost.html`  (session `arena/46c03a7d`)

**Live:** https://sassnarep3-star.github.io/China3/cost.html

The four layers above answer *which routes exist*. This layer answers *what they cost*, and it
is the only part of the site where a figure can be checked by arithmetic rather than by reading.

| Page | Content |
|---|---|
| `cost.html` | Landing: the four numbers, the summary table, links to everything |
| `cost-model.html` | **Every USD 10,000 step from USD 10,000 to USD 400,000**, spread / wire fee / all-in, plus the six-route matrix |
| `cost-methods.html` | 15 methods — who qualifies, the ceiling, pros, cons, cost at USD 400,000 |
| `cost-playbook.html` | Step-by-step execution per route, ordered so the eligibility check comes first; two-year phasing calendar |
| `cost-tax.html` | The seven cost layers separated, and where the six-figure risk actually sits |
| `cost-review.html` | 10 unverified items, 1 fixed, 3 defects found in the pre-existing pages |
| `cost-sources.html` | 26 sources with what each supports **and what it does not** |

**The anchor.** Bank of China 外汇牌价, snapshot `2026-11-09 09:15:45`: USD spot selling
669.19 vs its own reference 671.88 per 100 → a measured **0.4004 %** customer spread.
Wire fee: 1 ‰, floor CNY 50, cap CNY 260, plus CNY 150 cable. Both from boc.cn.

Why it is trustworthy rather than asserted:

- `scripts/build_cost.py` emits every figure; **no number is typed into HTML**. The source of
  truth is `data/fx_anchor.json`, which records what was literally on each official page.
- `scripts/verify_cost.py` re-implements the arithmetic from the published formulas, parses the
  generated HTML and **fails the build if any of the 40 × 6 cells is off by one cent**; it also
  asserts that every row carries an official link and that unverified cells are genuinely blank.
- `.github/workflows/cost-verify.yml` re-runs all four existing verifiers plus the staleness
  checks, so the older layers cannot drift while this one is rebuilt.

To re-anchor on a new day: edit the six BOC numbers in `data/fx_anchor.json`, run
`python3 scripts/build_cost.py && python3 scripts/verify_cost.py`, commit. See
[`COST_MODEL.md`](COST_MODEL.md) for the table and [`SUMMARY.md`](SUMMARY.md) for the executive summary.

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
| `deep-sources.html` | 84 official sources with verification method |

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
