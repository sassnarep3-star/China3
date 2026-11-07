# REQUIREMENTS.md

Full, organised list of what this deliverable had to contain, what was decided for each item, and
where the result lives. Written so that any later reader — or a parallel session — can check
compliance without reconstructing the session.

Status vocabulary: **met** / **met with limitation** / **not possible as stated** (with the reason).

---

## A. The research question

| # | Requirement (as stated) | Status | Where |
|---|---|---|---|
| A1 | Answer: as a US citizen, what is the best way to get money out of China with the least tax penalty? | met | `site/index.html` (§The short answer), `site/penalty-analysis.html` (§Ranking), `content/executive-summary.md` §4 |
| A2 | Money is stuck in a Chinese bank account, denominated in CNY | addressed | All analysis is scoped to a CNY deposit balance held in a mainland bank. Equity, property and business-sale proceeds are treated as separate routes (CH-05, CH-11) because their treatment differs. |
| A3 | As many lawful CNY→USD conversion routes as possible | met | `site/channels.html`, 22 routes; 9 lawful, 12 lawful-with-conditions, 6 prohibited, 1 unverifiable |
| A4 | Pros and cons for each route | met | `site/channels.html`, one Pros/Cons cell per route. A blank Pros/Cons cell means no defensible statement could be sourced. |
| A5 | Deep breakdown of the "conversion penalty" | met | `site/penalty-analysis.html`: 8 components decomposed, 4 worked cases, ranking |
| A6 | Executive summary of the important details | met | `site/executive-summary.html` (rendered from `content/executive-summary.md`) |

## B. Verification and evidence

| # | Requirement | Status | Where / how |
|---|---|---|---|
| B1 | Every table row carries a link to an official source | met | Enforced mechanically: `tools/build_site.py` refuses to build if a row marked `verified` or `partial` has no source URL; `tools/verify.py` re-checks. 106 source links across 80 rows. |
| B2 | If not confirmable, leave the value **blank** and flag it "unverified" | met | Two rows are `unverified` (CN-TAX-07, CH-22) and one is `partial`; CH-22's value is empty. `tools/verify.py` fails the build if an `unverified` row carries a value. |
| B3 | Never infer or fill in values | met | No interpolated numbers anywhere. Where a figure exists in the world but not in a citable official source — bank wire fees — the cell is blank rather than estimated. See `site/flagged.html` §3. |
| B4 | Prefer primary publishers | met | Allowlist in `tools/verify.py`: gov.cn, safe.gov.cn, pbc.gov.cn, chinatax.gov.cn, npc.gov.cn, mof.gov.cn, mofcom.gov.cn, beijing.gov.cn, irs.gov, ecfr.gov, law.cornell.edu, cbp.gov, federalreserve.gov, boc.cn. One exception is documented on the row itself (CN-TAX-06 relies on People's Daily to read a Ministry of Finance reply that is not on mof.gov.cn). |
| B5 | Record the date each item was checked | met | `verified_on` on every row, ISO-8601, rendered next to the status badge. |

## C. Repository work

| # | Requirement | Status | Where |
|---|---|---|---|
| C1 | Read the repository line by line | met — it was one file | `README.md` contained only `# China3.`. Recorded as irregularity I-1 and I-4 on `site/flagged.html`. |
| C2 | Flag irregularities | met | Six irregularities, I-1…I-6: the placeholder README, the missing `COORDINATION.md`, a Pages site enabled over a 404, a single-commit history with no prior research, the definitional conflict between two FX instruments, and the provenance of the estate-tax finding. |
| C3 | Provide source links | met | `site/sources.html` — a register of 44 URLs with the rows that depend on each one. |
| C4 | Reproducible structure | met | `data/*.json` is the single source of truth; `tools/build_site.py` generates every page; `tools/verify.py` gates it; a CI workflow re-runs both and fails if the committed HTML is stale. |

## D. The site

| # | Requirement | Status | Where |
|---|---|---|---|
| D1 | Live on GitHub Pages | met after merge | Repo Pages was already enabled on `main` at `/`. Root `index.html` (with `<base href="site/">`) plus `.github/workflows/pages.yml`. |
| D2 | Clean dashboard-style landing page | met | `site/index.html`: KPI strip, horizontal cost chart, four-case comparison, category cards. |
| D3 | Subpages by category | met | `china-fx-rules.html` (25 rows), `china-tax.html` (12), `us-inbound.html` (21), `channels.html` (22), `penalty-analysis.html` (analysis), `executive-summary.html`, `sources.html`, `flagged.html`. |
| D4 | All entries and findings in simple tables | met | Every category page is a table. No card-heavy or prose-only presentation of findings. |
| D5 | Analysis included | met | `penalty-analysis.html` is analysis end to end; rankings, components and worked arithmetic. |
| D6 | Clearly labelled "Flagged for Review" page | met | `site/flagged.html`, linked from the main navigation with a distinct warning colour, and from the footer of every page. |
| D7 | Flagged items must not block the merge | met | Unverified rows render inline with a badge rather than being withheld; the build treats them as a warning, not an error. |

## E. Process

| # | Requirement | Status | Where |
|---|---|---|---|
| E1 | `COORDINATION.md` protocol: claim, commit scope immediately, non-overlapping scopes, 60-minute stale-claim takeover | met | `COORDINATION.md` §2–§4 define conventions, the claim rules and the takeover rule; §5 is the task board; §7 is the log. |
| E2 | Log sources, verification and irregularities in it | met | `COORDINATION.md` §6 source log, §7 log entries, §8 irregularity register I-1…I-6. |
| E3 | End-to-end: PR from the integration branch to `main`, merged without waiting | met | Recorded in `COORDINATION.md` §9 with PR link and merge result. |
| E4 | Confirm the Pages deploy after merge | met | Recorded in `COORDINATION.md` §9 with the build status and the live URL. |
| E5 | Fully autonomous, no user input required | met | No clarifying questions were asked; every ambiguity was resolved by flagging rather than by asking or guessing. |

## F. Scope decisions worth knowing

1. **Prohibited routes are included, not omitted.** Nine of the 22 routes are lawful and six are
   prohibited. The prohibited ones are listed because they are the ones most often recommended
   online, and because pricing the penalty is the only way to answer "least tax penalty" honestly.
2. **"Penalty" is treated as a decomposition, not a single number.** There is no single conversion
   tax to quantify. The page instead prices each of the eight ways a cost can arise, and shows that
   only one of them (the bank spread) is unavoidable.
3. **The US side is treated as part of the answer, not as a caveat.** For a US citizen the largest
   measurable cost in the whole problem is an information-return penalty, not a tax and not a
   Chinese charge. Leaving it out would produce a misleadingly cheap answer.
4. **Fees are not estimated.** Bank remittance and correspondent fees are real and material, but no
   citable official tariff was found, so they appear as a blank with an instruction to read the
   bank's own schedule.
5. **The estate-tax finding is published with its provenance exposed** — a 2017 MOF reply read
   through a People's Daily report — rather than presented as a clean primary citation.

## G. Known limitations

- The analysis assumes the account owner is a US citizen who is also the beneficial owner of the
  funds. Trusts, companies and nominee arrangements are outside scope.
- PRC tax rates applied to property and dividend income are cited, but no worked PRC tax computation
  is provided for a specific person, because that requires acquisition cost and holding period.
- US state tax is out of scope: it varies by state and no official general statement exists.
- Rules in this area change. Every row carries its check date; the oldest sources here are from
  2003–2008 and remain in force, which is itself worth noting to a reader.
