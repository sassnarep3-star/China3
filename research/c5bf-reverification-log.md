# C5BF — final-integration re-verification log (2026-11-10)

Session `arena/c5bf9ddc-china3`, acting as the **final integration session** defined in
`COORDINATION.md`. Base commit `cbb5a77` (PR #33); main advanced to `ff25d1f` (PR #35) while this
pass ran and the branch was rebased append-only, discarding nothing.

Rule followed throughout: **a claim is accepted only from its official primary source, quoted
verbatim below.** Nothing is accepted because another page in this repository says so. A value that
cannot be confirmed is left blank and flagged; it is never estimated.

Machine-readable versions: `data/c5bf_source_recheck.csv` (15 checks),
`data/c5bf_corrections.csv` (8 corrections), `data/c5bf_board_observations.csv` (2 board
observations), `data/c5bf_cost_10k_400k_latest.csv` (40 rows), `data/c5bf_cost_delta.csv` (40 rows).
Gate: `python3 scripts/verify_c5bf.py` · CI: `.github/workflows/c5bf-verify.yml`.

---

## 1. The correction that matters most: who the US$50,000/day rule actually applies to

Before this pass the site said, in four places, that a personal wire out of China needs "no approval
up to US$50,000/day on ID documents". Re-read at source, that is **over-broad**, and for this user —
a U.S. citizen — the applicable rule is a different article with a **higher paperwork bar**.

### 1.1 汇发〔2020〕14号 art. 64 — domestic individuals, from an FX account

Source: SAFE Tianjin, 《2024年外汇管理互联网信息——个人外汇（三）》, published 2024-02-29,
<https://www.safe.gov.cn/tianjin/2024/0229/2402.html> (fetched 2026-11-10T09:52Z).

> 问：境内个人外汇汇出境外用于经常项目支出，是否有额度限制？
>
> 答：根据《国家外汇管理局关于印发〈经常项目外汇业务指引（2020年版）〉的通知》（汇发〔2020〕14号）
> 第六十四条，**外汇账户内**外汇汇出境外**当日累计等值5万美元以下（含）的，凭本人有效身份证件办理**；
> 超过上述金额的，凭本人有效身份证件、有交易额的相关材料办理。境内个人办理外汇汇出业务时，应配合银行
> 购汇用途与付汇用途一致性审核。**持外币现钞汇出当日累计等值1万美元以下（含）的，凭本人有效身份证件在
> 银行办理**；超过上述金额的，凭本人有效身份证件、经海关签章的《海关申报单》或本人原存款银行外币现钞
> 提取单据、有交易额的相关材料办理。

Three things the site had not carried:

1. The question is expressly about **境内个人** (domestic individuals), not about everyone.
2. The US$50,000 same-day ID-only threshold is for FX remitted **from an FX account** (外汇账户内),
   for **current-account** expenditure (经常项目支出), and the bank must also run a
   purchase-purpose vs payment-purpose **consistency review** (购汇用途与付汇用途一致性审核).
3. Remitting **foreign-currency cash** is a different, much lower threshold: **US$10,000** same-day
   cumulative on ID, and above that a customs-stamped 《海关申报单》 or the original bank's cash
   withdrawal slip plus transaction documents.

### 1.2 汇发〔2020〕14号 art. 59 — foreign individuals (this user)

Source: SAFE Tianjin, 《2024年经常项目外汇政策问答案例（九）》, published 2024-06-21,
<https://www.safe.gov.cn/tianjin/2024/0621/2529.html> (fetched 2026-11-10T09:51Z). Registered as
**S52** in `data/s775_sources.csv`.

> **境外个人是否享受年度便利化额度购汇？**
>
> 根据……（汇发〔2020〕14号）第五十九条，**境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件
> 和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇。持有外国人永久居留身份证的境外个人适用购汇
> 年度便利化额度。**

So for a 境外个人 (foreign individual — a U.S. citizen):

- FX may be purchased out of **lawful current-account CNY income obtained in China**
  (在境内取得的经常项目合法人民币收入);
- on presentation of **valid ID + source-of-funds documents showing the transaction amount,
  including tax certificates** (有交易额的购汇资金来源材料（**含税务凭证**));
- the **annual purchase convenience quota applies only to holders of a 外国人永久居留身份证**
  (Foreign Permanent Resident ID card). A U.S. citizen without that card does not get the quota —
  they get the documented route.

**Practical consequence, stated plainly:** the cost model on this site was already correct, but the
*documentary* bar for this user is higher than the site implied. The bank will want to see the
source of the CNY and the tax paid on it. If the CNY in the account is **not** current-account
income — e.g. it is the proceeds of a property sale, or old savings — art. 59 does not by itself
authorise the purchase, and the capital-account routes (emigrant property transfer under
汇发〔2014〕2号, property-sale repatriation) are the ones to examine. That distinction is now
carried in `data/s775_methods.csv` (M01), `data/s775_steps.csv` (M07 step 3), the dashboard's
"fact 4", and `research/s775-executive-summary.md`.

This correction was **requested on the board by session `arena/058d6cd7-china3`** (A058-T1 log
entry) and is actioned here as COR-04/COR-06/COR-07.

---

## 2. The OUR surcharge is BOC's *personal* tariff, not a corporate one

Source: BOC, 《关于调整部分个人业务收费标准的公示》, 2014-12-31, effective 2015-04-01,
<https://www.boc.cn/pbservice/bi2/201412/t20141231_4404048.html> (fetched 2026-11-10T09:50:30Z).

> | 编码 | 业务类别 | 服务项目 | 服务内容 | 收费标准 | 生效日期 |
> | 210104021 | **4.个人跨境本外币汇款** | **4.2全额到账** | 跨境汇款转汇过程中，转汇行收取的转汇费不再从
> 汇款本金中扣除，而是直接向汇款人收取固定金额费用，确保境外收款人能够全额收到汇款（**此服务仅适用于汇款行
> 与收款行无直接账户关系，需通过至少一家中转行办理的汇款业务**） | 在收取个人汇出境外汇款电汇手续费、电讯费
> 基础上，按以下标准加收：**1、美元：收款行在我行纽约分行开立账户的，15美元/笔，其他均为25美元/笔** | 2015年4月1日 |

The document title is a notice on **个人业务** (personal business)收费标准 and the line item sits
under **4.个人跨境本外币汇款** — personal cross-border local/foreign currency remittance. The
amounts the site published (US$15 / US$25) were right; the *characterisation* was wrong. It said
the surcharge "sits in BOC's corporate/trade-finance schedule" and that "personal applicability
must be confirmed with the branch". It does not, and it need not be.

What **is** genuinely conditional is the **routing**: the service applies only where the remitting
and beneficiary banks have **no direct account relationship** and at least one **intermediary bank**
is required. BOC publishes no list of which U.S. banks that covers, so that specific fact stays
**blank** (flag S775-F05, retitled and lowered from medium to low; COR-05).

---

## 3. The wire tariff, confirmed word for word

Source: BOC, 《中国银行电子银行个人服务转账汇款费率表》, standards effective 2014-11-01,
<https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html> (fetched 2026-11-10T09:50Z).

> | 跨境汇款（电汇） | 每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。 |

This is the most load-bearing number on the whole site — it appears in every one of the 40 ladder
rows. **CONFIRMED verbatim.** 1‰, floor ¥50, ceiling ¥260, plus a ¥150 cable fee (¥80 to HK/MO/TW).

Two further rows on the same table were **not** previously catalogued and matter for sequencing
(RC-03):

> | 中行内跨省、省内异地外币转账 | 每笔转账金额的1‰，最高200元/笔。 |
> | 国内跨行汇款（普通） | 每笔0.2万元以下（含0.2万元），2元；……5万元以上，按金额的0.03%，最高收费50元。 |

Moving **CNY domestically** between banks costs at most **¥50**, and moving **FX inside BOC**
between provinces costs at most **¥200** — both far below the **¥410** (¥260 + ¥150) that the
cross-border wire costs once the cap binds. That does not change any published ladder row (the
ladder prices the cross-border leg, which is unavoidable), but it is why consolidating balances
before converting is worth doing, and it is recorded here rather than inferred into a table.

---

## 4. The board moved during the day — and the estimate barely did

Source: BOC FX board, <https://www.boc.cn/sourcedb/whpj/> (fetched 2026-11-10T09:51:30Z).

> | 货币名称 | 现汇买入价 | 现钞买入价 | 现汇卖出价 | 现钞卖出价 | 中行折算价 | 发布日期 | 发布时间 |
> | 美元 | 665.71 | 665.71 | 668.51 | 668.51 | 671.67 | 2026-11-10 | 17:39:58 |

The board now publishes **17:39:58** quotes; the whole site was derived from the **07:32:39**
snapshot (bid 666.22 / ask 669.03 / parity 671.88 → 6.6622 / 6.6903 / 6.7188). Both are real
published boards. The 07:32:39 snapshot **stays canonical** — re-basing 40 rows across seven pages
and four sibling builds would destroy comparability for no gain — and the newer board is published
as a second observation (`OBS-1739`) with its own fully re-derived 40-row ladder on
[`c5bf-rates.html`](../c5bf-rates.html).

| | OBS-0732 (canonical) | OBS-1739 (latest) |
|---|---|---|
| Board stamp (Beijing) | 2026-11-10 07:32:39 | 2026-11-10 17:39:58 |
| Ask (现汇卖出价) | 6.6903 | 6.6851 |
| Bid (现汇买入价) | 6.6622 | 6.6571 |
| Half-spread (ask−mid)/ask | 0.2100% | 0.2094% |
| **Total cost at $10,000** | **$53.42** | **$53.38** |
| **Total cost at $400,000** | **$901.30** | **$899.01** |

**Finding:** the total moves **−$0.04** at $10,000 and **−$2.29** at $400,000 — about 0.08% and
0.25% of the cost respectively. Intraday rate movement is therefore **not** what drives the
answer. What drives it is (a) the ¥260 wire-fee cap, which binds from about $38,862 of transfer,
and (b) the intermediary and U.S. receiving-bank fees, which have **no official published schedule**
and are left blank on every row (flag S775-F06). Planning effort belongs there, not in timing the
rate.

### 4.1 The 0.2104% vs 0.2100% "contradiction" is a denominator, not an error

Sibling builds published both figures for the *same* board. With bid 6.6622 / ask 6.6903,
mid = 6.67625:

- (ask − mid) / **ask** = 0.01405 / 6.6903 = **0.2100%**
- (ask − mid) / **mid** = 0.01405 / 6.67625 = **0.2104%**

The cost ladder multiplies the **USD amount** by (ask − mid)/ask, so **0.2100%** is the figure
consistent with every derived row. `data/c5bf_board_observations.csv` now publishes **both**
denominators for each observation, P22 states the formula explicitly, and a validator guard fails
the build if `0.2104` reappears on a rendered S775 page (COR-03, COR-08, RC-13).

---

## 5. U.S.-side figures, re-read at the primary source

### 5.1 FBAR penalties — 31 CFR 1010.821

Source: eCFR, <https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821>,
"Displaying title 31, up to date as of **11/06/2026**. Title 31 was last amended 11/06/2026."
Column heading: *"Maximum penalty amounts or range of minimum and maximum penalty amounts for
penalties assessed on or after January 17, 2025"* (fetched 2026-11-10T09:53Z).

> | 31 U.S.C. 5321(a)(5)(B)(i) | Foreign Financial Agency Transaction—Non-Willful Violation of Transaction | 10,000 | **16,536** |
> | 31 U.S.C. 5321(a)(5)(C)(i)(I) | Foreign Financial Agency Transaction—Willful Violation of Transaction | 100,000 | **165,353** |
> | 31 U.S.C. 5321(a)(1) | General Civil Penalty Provision for Willful Violations of Bank Secrecy Act Requirements | 25,000 −100,000 | **71,545 −286,184** |

- **$16,536** non-willful and **$165,353** willful: **CONFIRMED** against the current table.
- The "or **50% of the account balance**, whichever is greater" prong of the willful penalty is
  **statutory** (31 U.S.C. 5321(a)(5)(C)) and is not a number in this table; the site keeps the
  "greater of" formulation and cites this row for the dollar figure only.
- **NEW (RC-09):** the general willful-BSA penalty range **$71,545–$286,184** was not catalogued
  anywhere in this repository. It is the backstop a prosecutor can reach for willful BSA violations
  generally, above and beyond the FBAR-specific rows, and it is now published on the audit page.

### 5.2 Foreign earned income exclusion

Source: IRS, *Figuring the foreign earned income exclusion*,
<https://www.irs.gov/individuals/international-taxpayers/figuring-the-foreign-earned-income-exclusion>
(fetched 2026-11-10T09:53:30Z).

> "For tax year 2025, the maximum foreign earned income exclusion is the lesser of the foreign
> income earned or **$130,000** per qualifying person. For tax year 2026, the maximum exclusion is
> **$132,900** per person."
>
> "For 2025, the housing amount limitation is **$39,000**; for 2026, it is **$39,870**."
>
> "……the **$126,500** maximum foreign earned income exclusion for 2024……"

- **$132,900 (2026) / $130,000 (2025): CONFIRMED.**
- **NEW (RC-11):** housing limitation $39,870 (2026) / $39,000 (2025), and the **2024** maximum
  **$126,500** — recorded so nobody back-fits the 2026 number onto an earlier cohort year.
- **Source-selection caution:** the IRS *general* FEIE page
  (<https://www.irs.gov/individuals/international-taxpayers/foreign-earned-income-exclusion>) still
  enumerates only "$107,600 for 2020, $108,700 for 2021, $112,000 for 2022, and $120,000 for 2023".
  A reader who cites that page instead would publish a figure four years out of date. The "Figuring"
  page is the correct citation for 2025–2026 and must not be swapped for it.

Source: same general page, on scope (fetched 2026-11-10T09:53:15Z):

> "**Foreign-earned income** means wages, salaries, professional fees, or other amounts paid to you
> for personal services rendered by you."
> "**Not foreign earned income:** …… Pension or annuity payments, including social security benefits"

**CONFIRMED (RC-12):** the FEIE reaches **earned** income only. It cannot shelter a currency gain
under IRC §988, and it cannot shelter the conversion of existing savings. It is relevant here only
to the salary routes (M07–M09).

---

## 6. Irregularities found on the live deployed site (both fixed)

### 6.1 Hero card contradicted its own ladder — RC-14 / COR-01

`s775-dashboard.html` as deployed advertised **$50.93** as the total cost to remit $10,000 while the
ladder row directly beneath it said **$53.42**. Re-derived from the official inputs:

```
spread = 10,000 × (6.6903 − 6.67625) / 6.6903 = 21.00
wire   = (clamp(0.001 × 66,903, 50, 260) + 150) / 6.6903 = 216.90 / 6.6903 = 32.42
total  = 53.42
```

**$53.42 is correct**; $50.93 came from an earlier mis-derivation of the wire fee. The owner's own
fix is **PR #34**, but after main advanced through PRs #35/#36 that PR could no longer be merged
cleanly (`gh pr merge 34 --merge` refused: *"the merge commit cannot be cleanly created"*), and
Arena's single-branch binding prevents pushing to another session's branch. The owner's last commit
is `2026-11-10T01:47:56Z` — more than 60 minutes with no commits — so under the board's handoff
rule this session carried the same corrections forward and logged the handoff. The hero card is now
**emitted from the ladder row** rather than hand-typed, and a validator guard requires it.

### 6.2 40 rows shipped with a `<td>` nested inside a `<td>` — RC-15 / COR-02

`s775-cost-10k-400k.html` contained 40 instances of markup like:

```html
<td data-l='Amount'><td data-l='Amount'>$80,000</td></td>
```

The builder's generic `table()` wrapped cells that were already complete `<td>` elements. Browsers
recover from this by rendering a phantom extra column, so the most important table on the site was
mis-aligned on every device. `table()` now passes pre-wrapped cells through, and a guard fails the
build if a nested `<td>` reappears on any S775 or C5BF page.

---

## 7. What this pass did **not** do, and why

- **Did not re-base the site onto the newer board.** Comparability across four sibling builds and
  640+ published rows is worth more than a $0.04 improvement in precision; the newer board is
  published alongside instead, with the delta on every increment.
- **Did not fill in intermediary or U.S. receiving-bank fees.** No official schedule exists. They
  are blank on all 40 rows and flagged (S775-F06). They are **not** zero.
- **Did not infer any personal fact.** Source of the CNY, U.S. tax basis, marginal rate, hukou
  history, bank and account type were never supplied; every cell that depends on them is blank and
  flagged (S775-F01…F04). The §988 character of a gain on these facts remains an **interpretation**
  of the statute, flagged S775-F10, with the statutory text linked
  (<https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm>).
- **Did not merge PRs #25, #18, #15, #8 or #6.** Each rewrites shared files (`index.html`,
  `scripts/build_dashboard.py`, `data/sources.csv`, `ci.yml`, `pages.yml`) from a base that
  predates several merges, and each would put the tree into a state where the existing freshness
  validators fail — i.e. it would break the live site. The brief forbids merging a broken site.
  Full reasoning per PR is on [`c5bf-integration-audit.html`](../c5bf-integration-audit.html) §4.
- **Did not edit any other session's page.** The corrections in §1–§6 touch only the S775
  *generator and registers* (which the S775 validator re-derives and gates), the C5BF namespace,
  and — additively — the shared navigation through its own generator.

## 8. Cross-implementation check

`scripts/verify_c5bf.py` re-derives the OBS-0732 ladder from the recorded ask/bid using a
**separately written** implementation (`scripts/gen_c5bf_data.py`) and compares it against the
canonical `data/s775_cost_10k_400k.csv` produced by `scripts/gen_s775_data.py`:

> 40 canonical rows × 9 fields reproduce **exactly** (max difference on any USD field: **0**).

The only difference is representational: the canonical register stores the wire fee in CNY
unrounded to five decimals (`216.90300`), this one rounds to the fen (`216.90`). No published
dollar figure changes. Two independent implementations of the same official formula agreeing to the
cent is the strongest available evidence that the arithmetic — as opposed to the inputs — is right.
