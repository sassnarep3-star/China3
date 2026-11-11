# M5F19 — Repository review against primary sources

Session `5f1925df` · namespace `m5f19` · reviewed at `9bc2cde` (main, 2026-11-10).

This is a line-by-line review of the repository's substantive claims against the
official texts fetched on 2026-11-10. Where a claim is correct it is confirmed;
where it is wrong, the correcting text is quoted. Nothing here edits another
session's files — each finding names the owning files and is logged on the board
instead, per the coordination rules.

Machine-readable version: `data/m5f19_flags.csv` (13 entries, G01–G13).

---

## Summary

| Severity | Count | Meaning |
|---|---|---|
| Irregularity | 6 | A claim in the repository conflicts with the text of the instrument cited for it |
| Limitation | 4 | Something this edition could not verify, and left blank rather than estimate |
| Process | 1 | A coordination failure worth fixing structurally |
| Observation | 2 | Something that corroborates or sharpens an existing flag |

The single most consequential finding is **G01/G02**: the repository applies a
*domestic individual* rule to a U.S. citizen, and the article that actually
governs a passport-holder — Guidelines Art. 65 — appears nowhere in it.

---

## G01 · A domestic-individual rule is applied to a U.S. citizen

**Files:** `s775-dashboard.html`, `s775-cost-10k-400k.html`,
`research/s775-executive-summary.md`, `index.html`

Several merged pages state that a personal wire needs no approval "up to
USD 50,000 per day on ID", citing
<https://www.safe.gov.cn/tianjin/2024/0229/2402.html>.

That page was fetched. Its question is
「境内个人外汇汇出境外用于经常项目支出，是否有额度限制？」 — a **domestic
individual** (境内个人) remitting FX abroad. Its answer quotes Guidelines Art. 64.

The article governing an **overseas individual** (境外个人) is Art. 65:

> 第六十五条　境外个人经常项目外汇汇出境外，按下列规定在银行办理：（一）外汇账户内外汇汇出，凭本人有效身份证件办理；（二）持外币现钞汇出，当日累计等值1万美元以下（含）的，凭本人有效身份证件办理；超过上述金额的，凭本人有效身份证件、经海关签章的《海关申报单》或原存款银行外币现钞提取单据办理。

Art. 65(1) requires **only a valid identity document** for FX remitted from
within an FX account and **states no amount threshold**. The purchase leg for an
overseas individual is Art. 59, not Art. 55.

So the claim is wrong twice over: Art. 64's USD 50,000 is a *per-day
documentation threshold* for a domestic individual's existing FX, not a purchase
right; and it is not the applicable article for a passport-holder at all.

Sessions a502 (merged PR #36) and a058 (open PR #35) flagged the same defect
independently. It remains unfixed on main at `9bc2cde`.

**Recommended action:** fix the *generator and the source data*, not only the
generated HTML — as a502 asked. Replace the Art. 64 citation with Art. 59 plus
Art. 65(1) for an overseas individual, and delete "ID only up to USD 50,000/day"
as a general statement.

---

## G02 · Guidelines Art. 65 is absent from the repository entirely

**Files:** `data/china_rules.csv`, `deep-china-rules.html`, `d646-costs.html`,
`d646-summary.html`

A grep across every `.md`, `.html` and `.csv` file for `第六十五条`, `Article 65`
and `art. 65` returns **zero matches**, while Art. 64 is cited repeatedly.

Art. 65(1) is the mirror of Art. 64(1) and is materially more permissive for the
reader this repository is written for. Its absence is the direct cause of the
"8 wires over 8 years" framing in G03.

---

## G03 · The "8 wires over 8 years" scenario has no textual basis

**Files:** `d646-costs.html`, `d646-summary.html`, `index.html`

Session d6467425 published USD 1,332.05 at USD 400,000 on the basis of eight
wires, one per documented USD 50,000 convenience amount, framed as required.

No instrument reviewed requires this:

- Art. 65(1) states **no threshold** for an overseas individual remitting FX from
  an FX account.
- Art. 64(1) sets a USD 50,000 **per-day identity-document** threshold for a
  domestic individual; above it, documents are required — not a prohibition and
  not a multi-year wait.
- SAFE Ningxia 2022 states that there is **no amount limit** on genuine, lawful
  current-account purchase and settlement, and that the convenience amount is a
  documentation threshold rather than a quota.
- 汇发〔2014〕2号 §6(2) expressly **abolished** the installment requirement for
  emigrant property transfers in 2014.

The scenario remains legitimate *as a contingency* if a bank or SAFE branch
stages a transfer in a particular case. It must not be presented as what the
regulation requires. The cost difference is real and is priced on
`m5f19-costs.html`: USD 1,328.33 for eight wires versus USD 899.01 for one at
USD 400,000 on today's board.

---

## G04 · Two spread denominators circulate; both are now demonstrated

**Files:** `index.html`, `d646-costs.html`, `costs.html`,
`cross-session-review.html`

fbbd3b22 divides the half-spread by the **ask**; d6467425 divides by the **mid**.
The repository logged this as a "convention difference" (C3) without
demonstrating it arithmetically.

`data/m5f19_reconciliation.csv` now re-derives all five published headline
figures **to the cent**: 53.42, 901.30 (ask) and 53.47, 1,332.05 (mid). That
proves there is no data error in any build — only a denominator choice and a wire
count. `m5f19-reconciliation.html` publishes both conventions side by side with
the arithmetic shown, and never mixes them in one column.

---

## G05 · The emigrant route's tax-clearance gate is not carried into headlines

**Files:** `index.html`, `EXECUTIVE_SUMMARY.md`

PRC IIT Law Art. 13 para 4, fetched in full:

> 纳税人因移居境外注销中国户籍的，应当在注销中国户籍前办理税款清算。

A taxpayer cancelling a Chinese hukou because of emigrating abroad **must
complete the tax clearance before the cancellation**. Art. 10(5) makes the
cancellation itself a filing trigger. Because 汇发〔2014〕2号 §6(1) routes the
emigrant property transfer through the SAFE branch at the **original** hukou
location, that clearance gates the entire route and the sequence cannot be
reversed.

The repository does record this in `data/taxes.json` and `docs/playbook.html`,
which is to its credit. The finding is narrower: the sequencing trap does not
appear in any headline treatment, where a reader would most need it.

---

## G06 · "No PRC tax on converting your own CNY to USD" outruns its sources

**Files:** `s775-dashboard.html`, `index.html`,
`research/s775-executive-summary.md`

IIT Law Art. 2 lists **nine closed categories** of taxable personal income.
Currency conversion is not among them. That is what the text supports.

It does not support a universal exemption. Tax depends on how the money was
earned, on residence status under Art. 1 (domicile, or 183 days cumulatively in a
tax year), and on whether earlier PRC tax was paid and can be evidenced — which
is exactly why Art. 59 requires a tax certificate at the counter.

**Correct statement:** no instrument reviewed taxes the *act* of exchange; the
Art. 2 categories are closed and do not include it; tax on the *underlying
income* is a separate question that must be settled on the facts. Sessions a502
and a058 both flagged this.

---

## G07 · No cost figure anywhere in this repository is a quotation

**Files:** all cost pages

BOC's own declaration on the board page, fetched verbatim:

> 本汇率表单位为100外币换算人民币，仅供参考，客户办理结/购汇业务时，应以中国银行网上银行、手机银行、智能柜台或网点柜台实际交易汇率为准，对使用该汇率表所导致的结果，中国银行不承担任何责任

And tariff note 1:

> 另有协议约定、价格优惠、地方性收费差异的，按照协议或当地公示的内容收取相关费用。

The board also moves intraday. This session read ask **6.6851** at 17:39:58;
earlier sessions read **6.6903** at 07:32:39 the same morning. Every dollar
figure in this repository — including every figure this edition publishes — is
therefore a *model*. The m5f19 pages say so in the footer of all nine pages and
in a callout on the cost page.

---

## G08 · The reader's classification is unknowable from the brief, and it changes the answer

**Files:** all pages

Two official instruments define the boundary differently:

| Instrument | Rank | 境内个人 | 境外个人 |
|---|---|---|---|
| State Council Order 532 Art. 52(2) | administrative regulation | Chinese citizens **and foreigners continuously resident in the PRC for a full year** (excluding diplomats and international-organisation representatives) | not defined in terms |
| PBOC Order [2006] No. 3 Art. 37 | departmental rule | Chinese citizens holding a PRC resident ID, military ID or armed-police ID | **foreign citizens holding a passport** (including stateless persons), Home Return Permit or Taiwan Travel Permit holders, and HK/Macao/Taiwan compatriots |

A U.S. citizen who has lived in China for over a year satisfies the *first*
definition's domestic test and the *second* definition's overseas test
simultaneously.

PBOC Art. 28 resolves this operationally rather than legally: **the bank**
determines the subject category from the identity documents supplied at account
opening. So the actionable step is a question to the bank, not a legal argument.
This edition does not claim that one instrument overrides the other.

The repository already records this tension as `IR-007`, correctly. The m5f19
edition promotes it from a footnote to the **first page of the analysis**
(`m5f19-classification.html`), because nothing downstream can be applied until it
is answered.

---

## G09 · Intermediary and beneficiary charges are blank, and one earlier figure was imported from the wrong tariff

**Files:** `cost-tables.html`, `d646-costs.html`, `s775-cost-10k-400k.html`

No official source fetched publishes intermediary or U.S. beneficiary-bank
charges for a personal CNY→USD wire. They are commercial and depend on the
OUR/SHA/BEN option. Left **blank**.

Session 15d351fb correctly identified that the USD 15/25 "OUR" charge used in
earlier cost models comes from BOC's **trade-finance** tariff
(`boc.cn/pbservice/bi2/201412/t20141231_4404048.html`, a 2014 notice effective
2015 for specified cases), not from the **personal** e-banking tariff at S02. The
personal tariff lists only the 1‰ wire fee with CNY 50/260 bounds plus the
CNY 80/150 telecom charge. Importing a corporate tariff into a personal cost
model is the defect; this edition does not do it.

---

## G10 · Three tax cells are blank because this session did not fetch them

**Files:** `m5f19-tax.html`

Form 8938 threshold, U.S.–China income tax treaty relief, and state-level tax on
a §988 gain. Earlier layers carry figures for the first two, but this edition
will not restate a value it did not read on 2026-11-10. Blank cells must not be
read as zero — `m5f19-flagged.html` says so explicitly.

---

## G11 · Three sibling sessions independently claimed the same shared files

**Files:** `COORDINATION.md`

Six branches were pushed within five minutes of this session starting. Three of
them — `arena/05552f6e-china3` (S055-T7), `arena/2c8d441e-china3` (C3X-5) and
`arena/ea347561-china3` (E347-T5) — each separately claimed `index.html`,
`scripts/build_dashboard.py` and `README.md`. e347 additionally asserts the
*final-integrator* role and logs takeover of the `build_dashboard.py` output path
from `arena/fbbd3b22-china3`.

Under the board rule that shared outputs may be changed only by a final
integration session, and the rule never to start a task another session has
claimed, this session **declined all shared files**. It filed request
**M5F19-REQ-01** asking whichever integrator lands to add one navigation entry to
`m5f19-dashboard.html`.

The structural cause: claims live on unmerged branches, so sessions cannot see
each other until they merge. This is the same failure mode the board already
records as X-12 and D646-IR-002.

---

## G12 · Observation — IR-008 is corroborated from the regulation itself

**Files:** `data/flags.csv` (IR-008), `deep-china-rules.html`

The repository's IR-008 records that OMB M-26-11 cancelled the 2026 inflation
adjustment, leaving the 2025 amounts in force. This session confirmed it
independently from 31 CFR 1010.821 rather than from the OMB notice: the eCFR page
states it is up to date as of 11/06/2026, its amendment history **ends at 90 FR
5630, Jan. 17, 2025**, and the Table 1 column is headed "penalties assessed on or
after January 17, 2025".

The operative maxima are therefore **USD 16,536** (non-willful) and
**USD 165,353** (willful fixed component). No change is required; IR-008 is
upgraded from "needs review" to independently corroborated.

---

## G13 · Observation — the willful FBAR figure is per-violation, not a ceiling

**Files:** `index.html`, `penalties.html`, `d646-penalty.html`

31 CFR 1010.821(b), fetched verbatim:

> These maximum penalty amounts do not, however, limit the total amount of a
> penalty in the case of a penalty that may be imposed for each day a violation
> continues.

Combined with §5321(b)(1)'s **six-year** assessment window, §5321(d)'s
confirmation that civil and criminal penalties are **not exclusive**, and
§5321(f)'s repeat-violator uplift of up to the greater of **three times the
profit gained or loss avoided** or **twice the maximum penalty**, the
"USD 200,000 on a USD 400,000 account" figure on the landing page is a
*per-violation* maximum.

The arithmetic is right and worth keeping: §5321(a)(5)(C)(i) sets the willful
maximum at the **greater of** USD 100,000 statutory (adjusted to USD 165,353)
**or 50% of the balance in the account at the time of the violation**. On
USD 400,000, 50% = USD 200,000, which exceeds USD 165,353, so the 50% limb
governs. The refinement is that total exposure across years can exceed it.

Session a502 made the same point ("do not present a maximum penalty as the actual
one"). The m5f19 pages state both: the per-violation maximum, and the fact that
the maxima do not cap a continuing violation.

---

## Findings from earlier audits that this review confirms

Both sibling audits were read in full before this review began.

**a502 (`research/a502-audit.md`, merged PR #36)** — all seven findings
confirmed, and each is now either fixed in the m5f19 model or carried as a flag:

| a502 finding | Disposition here |
|---|---|
| 1. USD 50,000 rules mis-scoped | Confirmed → **G01/G02** |
| 2. CNY-input/net-USD incoherence; spread double-counted | Fixed by construction → §4 of the verification log |
| 3. "No PRC tax on conversion" is an unsupported universal | Confirmed → **G06** |
| 4. §988(e) needs exact conditions | Fetched and quoted in full → fact F43, row T07 |
| 5. Tax minimisation cannot be ranked without facts | Agreed; the m5f19 edition publishes no ranking of tax outcomes |
| 6. FBAR is aggregate > USD 10,000; 8938 differs; streamlined needs eligibility | F45 quotes the aggregate test verbatim; the 8938 threshold is left **blank** rather than restated (G10) |
| 7. Validators check links and formula consistency, not truth | Agreed → `verify_m5f19_site.py` checks provenance (C), arithmetic (F) and reconciliation (G) |

a502's request that the **generator and source data** be fixed rather than only
the generated HTML is adopted: every m5f19 figure is produced by
`scripts/m5f19_engine.py` from `data/m5f19_board.csv`, and the HTML is a build
artefact that CI verifies is not stale.

**a058 (`research/a058-independent-audit.md`, open PR #35)** — confirmed:

| a058 finding | Disposition here |
|---|---|
| FX purchase ≠ FX remittance | Central to `m5f19-classification.html`; the two legs are tabulated separately by category |
| The modelled spread is an opportunity cost, so amount actually received is unverified | Adopted verbatim as the m5f19 convention; "amount received" is never shown net of spread |
| The midpoint denominator matters | Both denominators published side by side → **G04** |
| The BOC USD 15/25 OUR charge is conditional, from a 2014 trade-finance notice | Confirmed → **G09**; not used |
| Card/table disagreement and nested `<td>` at `cbb5a77` | Both blocked by verifier checks A and F |

---

## Corrected regulatory positions carried forward

For the benefit of any later session, these are the positions the primary texts
support, several of which earlier layers state incorrectly:

1. SAFE Order 532 Arts. 39, 40 and 45 fines are **≤30%** in the ordinary case;
   the **30%–100%** band applies only 情节严重 (where circumstances are serious).
   30% is a ceiling ordinarily, not a floor.
2. The USD 50,000 annual convenience amount is **not a quota**, is **not a tax**,
   and for **purchase** is not available to a foreign-passport holder unless they
   hold a Foreign Permanent Residence Identity Card (Art. 59 para 2).
3. Quota splitting via relatives or multiple people is prohibited by Art. 62 and
   results in watch-list status for the year of listing **plus two consecutive
   further years**.
4. The crypto prohibition dates from **2021**, not 2026.
5. Art. 67 treats a domestic transfer between a domestic-individual account and an
   overseas-individual account **as a cross-border transaction**.
6. Transaction documents must be retained **5 years** (Order 532 Art. 12; PBOC
   Art. 6). The U.S. FBAR recordkeeping period is also five years, from the FBAR
   due date.
