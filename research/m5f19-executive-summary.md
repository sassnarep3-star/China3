# M5F19 — Executive summary

Session `5f1925df` · namespace `m5f19` · published 2026-11-10.

**Question:** how can a U.S. citizen move CNY held in a Chinese bank account out
to USD with the least tax penalty?

**Short answer:** the cost of moving the money is small — roughly **0.53%** at
USD 10,000 falling to **0.22%** at USD 400,000, all of it bank spread and wire
fees, none of it tax. The exposure that actually matters is not a tax at all: it
is a **U.S. reporting penalty** of up to **50% of the account balance**, and on
the Chinese side it is getting the **documents** and the **subject
classification** right. The reporting decision is worth about 220 times the
exchange decision.

Everything below is either quoted from an instrument fetched on 2026-11-10 or
left blank. Provenance: `research/m5f19-verification.md`.

---

## 1. The five things that decide the outcome

| # | What decides it | Why |
|---|---|---|
| 1 | **Which category the bank recorded you in** | Chinese FX rules are written separately for a 境内个人 (domestic individual) and a 境外个人 (overseas individual). Different articles, different documents, different thresholds. Two official instruments define the boundary **differently**. |
| 2 | **Whether the money is lawful current-account RMB income** | If yes, Art. 59 and PBOC Art. 13 allow purchase *and* remittance on documents. If no, a different route is needed and the money's legal character must be established first. |
| 3 | **Whether a tax certificate exists** | Art. 59 requires 含税务凭证 — source-of-funds documents **including a tax certificate**. Unpaid PRC tax on the underlying income blocks the route at the counter. |
| 4 | **Whether the balance is already in foreign currency** | If it is, **no purchase is needed and there is no spread at all**. Art. 65(1) then requires only an identity document. This is the cheapest outcome that exists. |
| 5 | **Whether the FBAR was filed** | Aggregate foreign accounts exceeding USD 10,000 at any time in the year triggers FinCEN Form 114. A willful failure costs up to 50% of the balance. |

---

## 2. The classification problem — read this before anything else

| Instrument | 境内个人 domestic individual | 境外个人 overseas individual |
|---|---|---|
| **State Council Order 532 Art. 52(2)** — administrative regulation | Chinese citizens **and foreigners continuously resident in the PRC for a full year** | not defined in terms |
| **PBOC Order [2006] No. 3 Art. 37** — departmental rule | Chinese citizens holding a PRC resident ID, military ID or armed-police ID | **foreign citizens holding a passport** (including stateless persons), plus Home Return Permit / Taiwan Travel Permit holders |

A U.S. citizen resident in China for over a year satisfies the first definition's
*domestic* test and the second's *overseas* test at the same time.

**PBOC Art. 28 resolves this operationally, not legally:** the bank determines the
category from the identity documents supplied at account opening. So the first
action is a written question to the bank — *which category does this account carry
in the personal FX monitoring system?* — not a legal argument.

What each category gets:

| Leg | Overseas individual | Domestic individual |
|---|---|---|
| **Purchase** CNY→USD | Art. 59: ID + amount-bearing source-of-funds documents **including a tax certificate**. The USD 50,000 convenience amount applies **only** with a Foreign Permanent Residence Identity Card. | Arts. 54–57: USD 50,000/year on ID alone; above that, ID + amount-bearing **purpose** documents + a completed 个人购汇申请书 |
| **Remit** FX from an FX account | **Art. 65(1): ID only. No amount threshold stated.** | Art. 64(1): up to USD 50,000 equivalent **per day** on ID; above that, ID + amount-bearing materials, and the bank reviews purchase-purpose against remittance-purpose consistency |
| **Remit** foreign cash | Art. 65(2): ≤ USD 10,000/day on ID | Art. 64(2): ≤ USD 10,000/day on ID |
| **Convert back** unused RMB | Art. 60: ID + original exchange slip, valid **24 months**; ≤ USD 500/day on ID alone | not the subject of Art. 60 |
| **Return** unused FX remitted in | PBOC Art. 14: **ID alone**, back along the original route | not the subject of PBOC Art. 14 |

Full decision tree, nine questions: `m5f19-classification.html`.

---

## 3. USD 50,000 is not a cap

SAFE Ningxia, 2022 政策释疑（八）, fetched verbatim:

> 目前，我国对于真实、合法的经常项目和已开放的资本项目下购汇和结汇都没有金额限制。……年度便利化额度不是个人每年购汇或者结汇的限额，只是超过等值5万美元的购汇或结汇不能仅凭本人有效身份证件办理。

There is **no amount limit** on genuine, lawful current-account purchase and
settlement. The convenience amount is a **documentation threshold**: above it you
cannot proceed on an identity document alone, so you produce documents. It is not
a quota, it is not a tax, and it does not reset an entitlement.

---

## 4. Cost of moving the money

Inputs read 2026-11-10: BOC board at **17:39:58** — USD ask **6.6851**, bid
**6.6571**, midpoint **6.6711**. BOC personal wire tariff — **1‰** of the
remittance amount, floor **CNY 50**, ceiling **CNY 260**, plus a **CNY 150**
telecom charge outside Hong Kong, Macao and Taiwan.

One wire, China side only:

| Transfer | CNY spent | Spread | Wire fee | Telecom | **Total known cost** | All-in % |
|---|---|---|---|---|---|---|
| USD 10,000 | 66,851.00 | 20.94 | 10.00 | 22.44 | **USD 53.38** | 0.5338% |
| USD 25,000 | 167,127.50 | 52.36 | 25.00 | 22.44 | **USD 99.79** | 0.3992% |
| USD 50,000 | 334,255.00 | 104.71 | 38.89 | 22.44 | **USD 166.04** | 0.3321% |
| USD 100,000 | 668,510.00 | 209.42 | 38.89 | 22.44 | **USD 270.75** | 0.2708% |
| USD 200,000 | 1,337,020.00 | 418.84 | 38.89 | 22.44 | **USD 480.17** | 0.2401% |
| USD 300,000 | 2,005,530.00 | 628.26 | 38.89 | 22.44 | **USD 689.59** | 0.2299% |
| USD 400,000 | 2,674,040.00 | 837.68 | 38.89 | 22.44 | **USD 899.01** | 0.2248% |

Cost **falls** as a percentage of the transfer because the CNY 260 fee ceiling
binds above roughly **USD 38,892**, leaving only the proportional spread. All 40
increments from USD 10,000 to USD 400,000 are on `m5f19-costs.html`, in a
mobile-first table that collapses to stacked cards below 720px.

**If the balance is already in USD**, no purchase is needed, so the spread
disappears entirely and the known cost at USD 400,000 is **USD 61.33** — the fee
ceiling plus the telecom charge. That is route M03 and it is an order of
magnitude cheaper than any conversion route.

### The "conversion penalty", decomposed

What gets called a conversion penalty is four different things:

| Component | Size | What it is | Avoidable? |
|---|---|---|---|
| **Bank spread** | 0.2094% of the transfer | The gap between the ask you pay and a hypothetical midpoint. A **price**, not a penalty, and not a tax. | Only by not converting — i.e. route M03 |
| **Wire fee + telecom** | USD 38.89 + USD 22.44 at the ceiling | A published bank tariff | Partly: one wire instead of eight pays the flat element once |
| **PRC tax on the underlying income** | 0–45%, on the facts | IIT on how the money was **earned**. Due whether or not it ever leaves China. | Not a cost of moving money — already sunk by the time you reach the counter |
| **U.S. reporting penalty** | up to **50% of the balance** | The consequence of not filing FinCEN Form 114 | **Entirely** — file the FBAR |

The spread is an **opportunity cost borne in the CNY you spend**. It is *not*
deducted again from the USD you receive: buying USD X at the ask delivers USD X.
Earlier layers of this repository deducted both and labelled the result "net";
sessions a502 and a058 flagged that, and this model cannot reproduce it.

---

## 5. Tax

### China

- **No instrument reviewed taxes the act of converting your own CNY to USD.**
  IIT Law Art. 2 lists nine *closed* categories of taxable personal income and
  currency conversion is not among them. That is a statement about the closed
  list — **not** a universal exemption.
- **Tax on the income that created the money** (Art. 3): comprehensive income
  3–45% excess-progressive; business income 5–35%; interest, dividends, rent,
  **property transfer** and incidental income a flat **20%**.
- **Property transfer base** (Art. 6(5)): proceeds **less original value and
  reasonable expenses** — the gain, not the sale price.
- **The tax certificate Art. 59 demands is evidence this was already settled.** It
  is not a new levy at the counter.
- **Emigration gate** (Arts. 10(5), 13 para 4): a taxpayer cancelling a Chinese
  hukou because of emigrating abroad **must complete the tax clearance before the
  cancellation**. Since 汇发〔2014〕2号 §6 routes the emigrant property transfer
  through the SAFE branch at the **original** hukou location, that clearance gates
  the whole route and the sequence cannot be reversed.
- **Foreign tax credit** (Art. 7) for a PRC resident individual's foreign income,
  capped at the PRC tax on that income. **Currency for tax** (Art. 16): the RMB
  **midpoint** — note the contrast with the ask a customer actually pays.

### United States

- **§988(e)** is the provision that matters. For an individual, the rest of §988
  does not apply to a **personal** transaction; on a personal disposition of
  nonfunctional currency **no gain is recognised** by reason of post-acquisition
  exchange-rate changes — **unless the gain exceeds USD 200**. Three conditions
  must hold, and none is determinable from the brief:
  1. the currency must be **nonfunctional** — §988(c)(1)(C)(ii) expressly includes
     bank deposits, so a CNY deposit qualifies for a USD-functional taxpayer;
  2. the transaction must be **personal**;
  3. the gain must not exceed **USD 200**.

  §988(e)(3) withdraws "personal" status to the extent allocable expenses meet
  §162 (other than §162(a)(2) travel) or §212 (other than the tax-related part).
  **USD 200 is not a general exemption.**
- If the exclusion does not hold, the gain is **ordinary**, not capital
  (§988(a)(1)(A)), and is **U.S.-source** for a U.S.-tax-home citizen
  (§988(a)(3)(B)(i)) — which matters because a foreign tax credit is generally
  unavailable against U.S.-source income.
- **TY2026 amounts** (IR-2025-103 / Rev. Proc. 2025-32): foreign earned income
  exclusion **USD 132,900**; annual gift exclusion **USD 19,000**; annual
  exclusion for gifts to a **non-citizen spouse USD 194,000** (up from 190,000).
  The FEIE applies to qualifying *foreign earned income* — it is not a mechanism
  for repatriating an existing balance.
- **FBAR** (IRS guidance, verbatim): a U.S. person must file where "the aggregate
  value of those foreign financial accounts **exceeded $10,000 at any time during
  the calendar year** reported." Aggregate, not per account; *exceeded*, not
  *reached*. Due **15 April**, automatic extension to **15 October**, e-filed with
  FinCEN and **not** with the return. Records kept **five years**.

### Penalties

| Provision | Consequence |
|---|---|
| **31 U.S.C. §5321(a)(5)(B)** — non-willful FBAR | ≤ USD 10,000 statutory, adjusted to **USD 16,536**. **Reasonable-cause exception** applies if the violation was due to reasonable cause *and* the amount or balance was properly reported |
| **§5321(a)(5)(C),(D)** — willful FBAR | The **greater of** USD 100,000 statutory (adjusted **USD 165,353**) **or 50% of the balance in the account at the time of the violation**. On USD 400,000 that is **USD 200,000**, so the 50% limb governs. The reasonable-cause exception does **not** apply |
| **31 CFR 1010.821(b)** | The adjusted maxima **do not limit the total** where a penalty may be imposed for each day a violation continues — so these are per-violation figures, not a ceiling on exposure |
| **§5321(a)(4)** — structuring | Up to the **full amount** of the currency involved |
| **§5321(b)(1), (d), (f)** | **Six years** to assess; civil penalties are **not exclusive** of criminal; repeat violators face an **additional** penalty up to the greater of **3× the profit gained or loss avoided** or **2× the maximum penalty** |
| **Order 532 Art. 39** — 逃汇, unlawful outward transfer | Repatriation order + fine **≤30%**; where 情节严重, **30%–100%**; criminal liability where a crime is constituted |
| **Art. 45** — 私自/变相买卖外汇, informal or disguised dealing | Warning + confiscation of gains + **≤30%**; serious **30%–100%**; criminal exposure |
| **Art. 40** — 非法套汇, fraudulent purchase on false documents | Reconversion order + **≤30%**; serious **30%–100%** |
| **Art. 42** — carrying FX across the border unlawfully | Warning + **≤20%**; Customs may be the enforcing authority |
| **Art. 48** — documentary failures | Correction + warning; institution ≤ CNY 300,000, **individual ≤ CNY 50,000** |
| **Guidelines Art. 62** — splitting | **Watch list** for the year of listing **plus two consecutive further years**, during which every settlement/purchase needs ID + amount-bearing materials |

Note that **30% is a ceiling in the ordinary case, not a floor** — the 30–100%
band applies only where circumstances are serious.

---

## 6. Routes, ranked by what the text supports

Full catalogue with verbatim text for each: `m5f19-methods.html` (20 routes).
Step-by-step playbooks: `m5f19-steps.html`.

| Rank | Route | Ceiling stated in the text | Cost at USD 400,000 |
|---|---|---|---|
| 1 | **FX already in an FX account, remitted out** — Art. 65(1), ID only | **None stated** | **USD 61.33** — no purchase, so no spread |
| 2 | **Documented current-account RMB income**, purchased and wired — Art. 59 + Art. 65(1) | **None stated**; a tax certificate is required evidence | USD 899.01 |
| 3 | **Same, but classified as a domestic individual** — Arts. 54–57, 64(1) | USD 50,000/day is a documentation threshold, not a cap | USD 899.01 |
| 4 | **Emigrant property transfer** — 汇发〔2014〕2号 §6 | **None stated**; installment requirement and RMB 500,000 filing both abolished in 2014 | USD 899.01, one lump sum permitted |
| 5 | **Proceeds of selling onshore real property** — PBOC Art. 22 | **SAFE approval required** | USD 899.01 **plus 20% IIT on the gain** |
| 6 | **Investor's share of a lawfully liquidated FIE** — Order 532 Art. 22(3) | **None stated**; conditional on liquidation and tax payment | USD 899.01 plus corporate taxes |
| — | **Splitting, informal brokers, tokens, false invoices** | **Prohibited** | no lawful cost exists |

Prohibited routes are listed with their penalties rather than omitted, so the
consequences are on the record.

**2014 reforms worth knowing about** (汇发〔2014〕2号, still in force — the
printed amendment note shows 汇发〔2023〕28号 changed only §3): the installment
requirement for emigrant transfers was **abolished**, the RMB 500,000 head-office
filing was **abolished**, notarisation of property documents and agency agreements
was **abolished**, inheritances from different decedents may be **combined** in one
application, and for institutional profit remittances above USD 50,000 the
audit-report and capital-verification review was **abolished** in favour of the
board resolution plus the original tax filing form.

---

## 7. What is genuinely unknown

The brief supplies no amount, no account documents, no source-of-funds history, no
residence history, no bank, no receiving bank and no U.S. filing history. Those
facts decide the route, the tax and the total.

Left **blank** rather than estimated: the executable spread, intermediary and
beneficiary-bank charges, the offshore CNY/CNH basis, the Form 8938 threshold,
U.S.–China treaty relief, and state-level tax. **Blank does not mean zero.**

And no figure here is a quotation. BOC states on its own board page that the table
is 仅供参考, that the executable rate is the one in its online banking, mobile
banking, smart counter or branch counter, and that it accepts no responsibility
for results based on the table. Tariff note 1 lets agreements, promotions and
local differences override the published charges. The board moves intraday — this
session read 6.6851 at 17:39:58 where earlier sessions read 6.6903 at 07:32:39 the
same morning. **Get a written bank quotation before acting.**

---

## 8. What this edition corrects in the repository

Thirteen findings, G01–G13, with recommended actions and the owning files:
`m5f19-flagged.html` and `research/m5f19-repo-review.md`.

The two that matter most:

- **G01/G02** — merged pages apply a *domestic-individual* rule (Art. 64) to a
  U.S. citizen, citing a SAFE page whose own question is about 境内个人. The
  governing article for a passport-holder, **Art. 65**, appears **nowhere** in the
  repository. Sessions a502 and a058 flagged the same defect independently; it is
  unfixed on main.
- **G03** — the "8 wires over 8 years" scenario has no textual basis. Art. 65(1)
  states no threshold; Art. 64(1) requires documents above USD 50,000 per day
  rather than prohibiting the transfer; SAFE Ningxia confirms no amount limit; and
  the installment requirement for emigrant transfers was abolished in 2014. It
  remains legitimate *as a contingency*, and is priced as one.

Also resolved: **G04** re-derives all five conflicting published headline figures
**to the cent**, proving there is no data error anywhere — only a denominator
choice and a wire count. See `m5f19-reconciliation.html`.

---

## 9. Pages in this edition

| Page | Contents |
|---|---|
| `m5f19-dashboard.html` | This summary: the six numbers, ranked routes, cost at a glance, reading order |
| `m5f19-classification.html` | The two conflicting definitions, nine-question decision tree, per-category rule table |
| `m5f19-costs.html` | All 40 increments × two denominators × one-wire and eight-wire scenarios |
| `m5f19-methods.html` | 20 routes with eligibility, documents, stated ceiling, pros, cons, and the verbatim text behind each |
| `m5f19-steps.html` | Numbered playbooks, each step linked to the article requiring it |
| `m5f19-tax.html` | 27 rows across PRC and U.S. law, plus the four-part penalty decomposition |
| `m5f19-reconciliation.html` | Every conflicting published figure re-derived, with the three reasons they diverge |
| `m5f19-flagged.html` | 13 findings and the cells deliberately left blank |
| `m5f19-sources.html` | 17 documents fetched today and the 52 verbatim passages relied on |

---

*General research, not legal or tax advice. Outcomes turn on facts not in evidence
here. Confirm the account's subject category and obtain a written bank quotation
before acting.*
