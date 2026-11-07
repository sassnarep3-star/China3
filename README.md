# China3 — getting money out of China into USD, as a US citizen

A sourced answer to one question: **what is the best way to move CNY out of a Chinese bank
account into USD with the least tax penalty, for a US citizen?**

Live site: **https://sassnarep3-star.github.io/China3/**

---

## The finding, in one paragraph

There is no PRC tax on converting or transferring your own money. China has no exit tax on
individuals, no estate tax, and deposit interest has been exempt from individual income tax since
9 October 2008. There is also no US tax on receiving a genuine gift or inheritance. The unavoidable
cost of a lawful conversion is the bank's currency spread, **about 0.42%**. What people experience
as a "considerable conversion penalty" is almost always one of two things: a **US information-return
penalty** for a form that was not filed (25% of a gift under IRC §6039F, or up to 50% of the account
balance for a willful FBAR violation), or a **PRC exchange-control fine** of 30–100% for using a
route China prohibits. Both are avoidable. On a CNY 3,000,000 balance the lawful route costs about
USD 1,900; missing Form 3520 costs about USD 112,700 — 59 times more.

## What is in here

| Path | What it is |
|---|---|
| `site/` | The published site. Generated — do not hand-edit. |
| `index.html` | Root entry point for GitHub Pages, with `<base href="site/">`. Generated. |
| `data/01-cn-fx-rules.json` | 25 China-side foreign-exchange rules (SAFE, PBoC, State Council). |
| `data/02-cn-tax.json` | 12 China-side tax findings. |
| `data/03-us-inbound.json` | 21 US inbound rules (FBAR, 8938, 3520, §988, PFIC). |
| `data/04-channels.json` | 22 CNY→USD routes with legality, capacity, cost and pros/cons. |
| `data/05-scenarios.json` | The penalty decomposed into 8 components + worked arithmetic. |
| `content/executive-summary.md` | The executive summary (rendered to `site/executive-summary.html`). |
| `REQUIREMENTS.md` | Every requirement, its status, and where it is satisfied. |
| `COORDINATION.md` | Multi-session protocol, task board, log, irregularity register. |
| `schema/` | JSON Schema for the data files. |
| `tools/build_site.py` | Builds every page from `data/`. |
| `tools/md_to_html.py` | Renders the executive summary. |
| `tools/verify.py` | The gate: data integrity, source links, internal links, stale output. |
| `.github/workflows/pages.yml` | CI: rebuild, verify, fail on stale output, deploy to Pages. |

## Build and verify

No dependencies. Python 3.9+ and nothing else.

```bash
python3 tools/build_site.py    # regenerate site/ and index.html
python3 tools/verify.py        # gate — exits non-zero on any problem
```

`verify.py` enforces the rules that matter for this project:

- every row marked `verified` or `partial` must carry at least one `https://` URL on an
  official-publisher allowlist;
- a row marked `unverified` may not carry a value — a blank has to stay blank;
- every row id must appear in the generated HTML, so nothing is silently dropped;
- every internal link and asset must resolve on disk;
- no `TODO`/`FIXME`/placeholder text may ship;
- the committed HTML must match what the data produces, or CI fails.

## Evidence rules

1. Every figure links to the official publisher — ministry, regulator, statute database, or the
   issuing bank's own price page.
2. If a value cannot be confirmed, it is **left blank**, marked `unverified`, and listed on the
   Flagged for Review page. Nothing is inferred, interpolated, or filled from memory.
3. Statute and practice are kept separate; practice claims need an official source or they are
   flagged.
4. Every row carries the date it was checked.

## Limits

Not legal or tax advice, and not a determination for any individual. Out of scope: trusts,
corporate ownership, state tax, and the numeric outcome of a PFIC computation for a specific fund.
See `REQUIREMENTS.md` §G for the full list, and `site/flagged.html` for every open item.
