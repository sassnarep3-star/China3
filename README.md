# China3 — moving CNY out of China as a US citizen

A sourced research pack and dashboard answering one question:

> Money is sitting in a Chinese bank account and cannot be turned into USD without what looks like a large tax hit. What are the lawful ways to convert it, what does each really cost, and what is the least-penalty path for a US citizen?

**Live site:** published from `/docs` on `main` via GitHub Pages (see the repository's Pages URL).

---

## The finding, in one paragraph

There is no Chinese "conversion tax" and no US tax on wiring your own money home. The balance is expensive to move because three different things get confused with each other: (1) Chinese capital controls, which are a *permission* problem, not a tax problem; (2) PRC income tax on whatever created the money — 20% flat if it came from property, interest, rent or dividends; and (3) US **reporting** penalties, where a willful FBAR violation is capped at the greater of USD 165,353 or **50% of the account balance** — an order of magnitude larger than any FX spread. The cheapest lawful route is therefore: classify the money, fix US reporting first, then use the one Chinese channel with no amount ceiling (emigrant property transfer) or the one with no annual quota (non-resident conversion of current-account income).

Full reasoning: `docs/index.html` (executive summary) and `docs/playbook.html` (order of operations).

---

## What is in here

| Path | What it is |
|---|---|
| `data/sources.json` | 27 sources: publisher, tier, URL, the proposition each supports, date checked |
| `data/channels.json` | 22 CNY→USD routes: status, cap, requirements, pros, cons, verdict |
| `data/taxes.json` | 25 tax items split US / PRC / treaty, each labelled `rule` or `analysis` |
| `data/penalties.json` | Five cost layers, 15 penalty provisions, cost model, scenario table |
| `data/flagged.json` | 18 items that are blank, ambiguous, or dependent on the reader's facts |
| `docs/` | The generated dashboard (GitHub Pages serves this folder) |
| `scripts/validate_data.py` | Enforces the "official source or explicit flag" contract |
| `scripts/check_links.py` | Internal links, anchors, external URL hygiene, bundle freshness |
| `scripts/build_site.py` | Builds `docs/`, refusing to build on a contract violation |
| `COORDINATION.md` | Task board, claims, handoffs, PR record |
| `VERIFICATION.md` | The per-URL verification log |
| `REPO_AUDIT.md` | Audit of the repository as found |

---

## The rules this project obeys

1. **No number without an official source.** Every figure carries a link to a statute, regulation, agency page, treaty or CFR provision.
2. **Blank beats guessed.** If a value could not be confirmed, it is empty, marked `unverified`, and published on the *Flagged for review* page. No industry averages, no estimates, no "approximately".
3. **Analysis is labelled.** Where a row is reasoning rather than a quotation, it says `analysis` and is flagged.
4. **The check is executable.** `validate_data.py` fails the build if a row states a cap without marking it verified, or asserts a consequence without a source.

---

## Build and check

```bash
python3 scripts/validate_data.py      # data contract
python3 scripts/check_links.py        # internal links + anchors + bundle freshness
python3 scripts/build_site.py         # regenerate docs/
```

Optional, on a networked machine:

```bash
python3 scripts/check_links.py --fetch   # HTTP-check every external URL in the register
```

No third-party dependencies. The site is plain HTML/CSS/JS with the data inlined at build time, so it makes no runtime network calls.

---

## Scope and limits

- Covers **individual** balances held in a Chinese bank account. Corporate structures, `QDII` quotas and outbound-investment projects are described only to the extent they bear on an individual.
- Four determinations depend on documents only the account holder has: the bank's `境内个人`/`境外个人` classification, whether a cancelled PRC household registration exists, when the balance was acquired relative to any emigration, and what created the money. All four are itemised in `docs/flagged.html`.
- Retail FX spreads and wire fees are commercial, not regulatory, and were **not** estimated. The site ships a calculator with no default rates.
- This is a research pack, not legal, tax or investment advice. Have a US tax adviser and a PRC-qualified adviser review the specific file before filing or applying.

---

## Licence

No licence was present when this work started; none was added, because that is the repository owner's decision. Content is cited to its sources under those sources' own terms.
