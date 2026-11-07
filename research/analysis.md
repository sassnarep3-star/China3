# T7 — Analysis and findings (deep pass)

Session `session-c703e38c` · reviewed 2026-11-07 (UTC)
Scope: `research/analysis.md`. Structured data: `data/findings.csv` (22 sourced findings).
Rendered at `deep-findings.html`. Executive summary: `EXECUTIVE_SUMMARY.md` and
`deep-executive-summary.html`.

## Thinking about the problem

The user's problem is usually framed online as "how do I get around the $50,000 quota?" The
official texts show that this framing is wrong in three independent ways, and each error has a
cost.

**Error 1 — the identity assumption.** Almost every English-language guide to moving money
out of China is written for a Chinese national (境内个人). A U.S. citizen holding a passport
is, under 人民银行令〔2006〕第3号第37条, an 境外个人. That is not a cosmetic distinction.
指引第59条 gives foreign individuals a **different** purchase rule: ID + evidence of the
*source* of the RMB (including tax evidence), with **no annual quota limit** unless the person
holds a 外国人永久居留身份证. SAFE's own Q&A handbook says so explicitly. If the CNY is
legitimately earned and tax-documented income, the whole "$50,000 a year, so ask five
friends" narrative is inapplicable. The right question is "can I produce the source-of-funds
and tax documents the bank will ask for?" — not "how do I split the amount?" (F02, F04).
Caveat: 国务院令第532号第52条 defines 境内个人 to include foreigners resident in China for
one year or more, and 第28条 of the PBOC measure says the account-opening ID determines the
classification. So the bank's system classification must be obtained in writing before
relying on the foreign-individual route (F03, IR-007).

**Error 2 — treating documentation as taxation.** SAFE's Ningxia Q&A states in plain language
that the USD 50,000 amount is a facilitation threshold, not a tax and not a legal ceiling.
The bank's Art. 59 duty is to verify the RMB source; the tax certificate, or the 税务备案表
for a single payment above USD 50,000, is a precondition, not a levy. China's IIT law taxes
income (3%–45% comprehensive; 20% for interest/dividends/property transfers), and savings
interest has been temporarily exempt since 2008. Bank spread and wire fees are prices, not
taxes (PBOC abolished spread management in 2014). So "conversion currently incurs
considerable taxes" most plausibly describes a *combination* of (a) tax on the underlying
income if it was never cleared, (b) a tax-clearance document request, (c) spread and fees,
and possibly (d) a quote from an intermediary who is not an authorised FX dealer. No official
source establishes a general conversion tax, and this site refuses to invent one (F01, F06,
IR-011).

**Error 3 — ignoring that the biggest penalty is American, and is about reporting.** The
maximum willful FBAR penalty under 31 CFR 1010.821 is the greater of $165,353 (the 2025
inflation-adjusted amount, still applicable in 2026 because OMB M-26-11 cancelled the 2026
adjustment) or **50% of the account balance**. A person optimising a few basis points of
spread while holding an unreported Chinese account is optimising the wrong variable. Form
8938, the 40% understatement penalty and Form 3520's 25% cap are independent exposures, and
Form 8938 does not replace the FBAR. The 1984 U.S.–China treaty's 10% source-country cap is
irrelevant to a U.S. citizen because of the saving clause. Conversely, IRS remediation
procedures (Streamlined, delinquent FBAR) mean past non-willful failures can usually be fixed
before the transfer rather than discovered afterwards (F08, F14, F16, F21).

## Second-order observations

- **Two different USD 50,000 rules.** One is the annual purchase/settlement convenience
  amount; the other is the same-day cumulative outward-remittance evidence threshold under
  指引第64条. Confusing them produces bad "workarounds" (F05).
- **Cost arithmetic is multiplicative, not additive.** A bank spread applies to the whole
  principal; a wire fee has a cap (BOC personal e-banking: 1‰, ¥50–¥260, plus ¥80/¥150
  cable); correspondent fees are passed through; an offshore CNH leg adds a basis that HKMA
  has officially measured at 1.94% in a stress episode. None of these can be bounded from
  official sources for a specific account, hence blank cells (F12, F13, IR-012).
- **Time is a cost too.** A watch-list entry lasts the inclusion year plus two consecutive
  years; emigration property transfers above RMB 200,000 are staged over two years; approval
  above RMB 500,000 goes to SAFE head office. Any "fast" route that triggers these is slower
  than the documentary route (F18, P21).
- **Illegal routes strictly dominate in the wrong direction.** 30%–100% administrative
  fines, confiscation, 1–5× illegal-gain criminal fines and up to 5+ years imprisonment
  dwarf every lawful cost. SAFE publishes enforcement cases for exactly the "borrow relatives'
  quotas" pattern people propose, and the 2026 virtual-currency notice (which repealed the
  2021 notice) explicitly extends to offshore services to mainland residents and RWA
  tokenisation (F09, F10, F11).
- **There is a genuine legal nuance about the money's character.** If the CNY is a gift or
  inheritance, both the Chinese inheritance-transfer route and U.S. Form 3520 (> $100,000,
  25% penalty for non-filing) become relevant even though a foreign gift is not subject to
  U.S. income tax. If the CNY is corporate profit, 汇发〔2017〕3号 allows uncapped
  repatriation with audit/tax documents. If the CNY is the proceeds of a property sale by a
  foreign individual, 办法第22条 requires SAFE approval. Route selection is therefore a
  function of provenance, not of amount (F15, F17, F19, IR-014, IR-019).
- **The onshore/offshore split is real but not a loophole.** HKMA documents that CNY and CNH
  diverge because the onshore rate is managed while the offshore rate is market-determined.
  Wealth Management Connect and cross-border RMB settlement legitimately move CNY offshore
  and convert there without consuming an individual FX quota — but they still require a
  lawful cross-border RMB channel and bank authenticity review. They are cost-comparison
  options, not evasion (F20, F12).
- **A small U.S. tax item hides in the conversion itself.** IRS Publication 525 excludes
  personal foreign-currency gains up to $200 from income; above that, the gain is a capital
  gain. If CNY appreciated since the funds were acquired, the conversion itself can create a
  reportable U.S. gain (F22).

## Recommended strategy under the "no manual input" constraint

Because the user explicitly instructed "there should be no manual input on my part", the site
cannot collect the account facts needed to compute a number. The honest deliverable is
therefore a **decision procedure**, not a personalised figure:

1. Get the bank's written classification (境内个人 vs 境外个人) and its document checklist.
2. Assemble source-of-funds and tax-clearance evidence; treat that as the gating item.
3. Get a written all-in quote that separates spread, wire fee, cable fee, correspondent fee
   and receiving fee.
4. Choose one lawful channel from the 24 lawful/approval routes; never split.
5. Complete FBAR / Form 8938 / Form 3520 analysis and use IRS remediation if needed.
6. Keep every document; Chinese rules require banks to retain individual FX materials for at
   least 5 years (办法第6条), and U.S. records must support the FBAR valuation.

This is what "least tax penalties" means when the only verified inputs are official rules:
minimise the probability of triggering a penalty layer, then minimise the pricing layer with
a written quote. It does not mean finding a channel with a lower statutory tax, because no
such tax was found.

## Irregularities

All 23 flagged items (IR-001 … IR-023) are published with source links on `deep-review.html`;
the ones raised by this analysis are IR-001, IR-002, IR-003, IR-011, IR-012, IR-013,
IR-014, IR-015, IR-016, IR-018, IR-019, IR-022, IR-023. They do not block publication.
