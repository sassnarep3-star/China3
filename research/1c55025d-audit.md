# China money — Full Requirements Audit (session arena/1c55025d-china3, 2026-11-11)

**Branch:** `arena/1c55025d-china3` · **Base:** `d9763dc` (= `6750ddb` + `5cf4629` + `5a66778`, i.e. main after PR #48 + PR #49).  
**Live site:** https://sassnarep3-star.github.io/China3/ (GitHub Pages, root path).  
**Dashboard entry:** `index.html` → `dashboard/methods.html`, `dashboard/costs.html`, `dashboard/steps.html`, `dashboard/tax.html`, `dashboard/flagged.html`, `dashboard/sources.html`, `dashboard/archive.html`.  
**Generators:** `scripts/e347_build.py` (builds `index.html` + `dashboard/*` + `data/e347_*.csv` + `legacy-index.html`); **Verifier:** `scripts/e347_verify.py`.  
**Re-read sources this pass:** BOC board 2026/11/10 17:39:58 (S01), BOC personal tariff (S02), BOC ATM notice effective 2026-11-11 (S03), SAFE Tianjin 2026-07-13 (S04), SAFE Tianjin 2024-06-21 (S05), SAFE Ningxia 2022-09-29 (S06), SAFE 2020 Guidelines Arts 54-67 (S08), SAFE Tianjin 2026-09-17 (S09), SAFE Tianjin 2025-06-13 (S10), SAFE Tianjin 2021-11-02 (S11), PBOC [2004] No.16 (S12), SAFE 汇发〔2014〕2号 §5-§6 (S13), SAFE Tianjin 2026-03-19 / Capital Guidelines §6.4 (S14), SAFE Anhui 2025-09-25 §8 (S15), STA/SAFE 2013 No.40 tax-filing (S16), State Council Decree 532 (S17), PBOC Measures [2006] No.3 (S18), SAFE 汇发〔2017〕29号 (S19), SAFE Hebei 2019-05-21 cash-carry (S20), SAFE Guangdong 2020-03-04 private FX (S21), SAFE Hebei 2017-04-14 splitting case (S22), PBOC 银发〔2026〕42号 (S23), PBOC Beijing 2018-11-09 cross-border RMB (S24), PRC IIT Law 2018 amendment (S25), MOF/STA 财税〔2008〕132号 savings-interest exemption (S26), 26 U.S.C. § 988 (S27), IRS yearly averages (S28), IRS 8938/FBAR comparison (S29), FinCEN FBAR (S30), 31 CFR 1010.821 penalty table (S31), IRS foreign gifts (S32), 26 U.S.C. § 6039F (S33), IRS worldwide-income FAQ (S34), CBP money reporting (S35). All URLs on the Sources page; 26 fetched in full, 9 as search excerpts of the official page text (flagged U11).

> This is general research from public official pages. It is not legal, tax, or banking advice and makes no finding about any person's case.

---

## 0. Requirements trace — every line of the brief

| # | Brief line | Where it is satisfied | Link |
|---|---|---|---|
| R0 | Collect, organize, analyze utilizing a full list of requirements | This file + `COORDINATION.md` R1–R8 claim + every dashboard page | `research/1c55025d-audit.md`, `COORDINATION.md` |
| R1 | Create an executive summary outlining important details | `EXECUTIVE_SUMMARY.md` + `index.html` hero + kpi cards + "What to do next" table | https://sassnarep3-star.github.io/China3/ |
| R2 | Clear list of questions, informations and answers that need to be addressed before any decision can be reasonably made upon information we already have and do not have. Suggestions to discover missing information | `dashboard/flagged.html` U01–U19 + §2 of this audit (Q&A) | https://sassnarep3-star.github.io/China3/dashboard/flagged.html |
| R3 | As US citizen, best way to get money out of china with least tax penalties. Money stuck, no way to convert without considerable taxes. Research ways CNY→USD, list as many as possible, pros/cons, break down conversion penalty, think deeply | `dashboard/methods.html` (11 lawful + 6 prohibited) + `dashboard/tax.html` + §3–§4 here | https://sassnarep3-star.github.io/China3/dashboard/methods.html |
| R4 | Estimate costs of transferring and converting CNY to USD in $10,000 increments to $400,000. Table mobile-friendly, most important info first. Actually estimate costs for every method, step-by-step how it works | `dashboard/costs.html` (full ladder; all routes at $10k/$50k/$100k/$200k/$400k; 40×11 rows) + `dashboard/steps.html` (per-route playbook) + `data/e347_costs.csv` + §5 here | https://sassnarep3-star.github.io/China3/dashboard/costs.html |
| R5 | No manual input required — work on own to finish tasks line by line, verify from official trusted sources, no hallucinations, provide links | This audit re-derives every figure; `scripts/e347_verify.py` checks every row has official link | See VERIFICATION.md + `scripts/e347_verify.py` |
| R6 | Review repo line by line verifying from official verified trusted sources, provide links, flag irregularities, no hallucinations | §6 of this file (repo line-by-line) + `VERIFICATION.md` | `VERIFICATION.md` |
| R7 | Site creation: GitHub Pages live site, clean landing + subpages by category, simple dashboard UI, all entries in simple easy-to-read table, include analysis/findings, verify line by line, no hallucinations | Pages deployed; `index.html` + 7 dashboard subpages; `dashboard/site.css`; mobile `stack` tables | https://sassnarep3-star.github.io/China3/dashboard/methods.html etc. |
| R8 | Verification: every table row must have source link; if unconfirmed leave blank + flag as unverified; never infer | `scripts/e347_verify.py` enforces; 658 data rows sourced, 380 blanks flagged; see §7 | `scripts/e347_verify.py` |
| R9 | Parallel sessions: coordinate via COORDINATION.md, claim before work, push immediately, non-overlapping file scopes, additive integration, small commits, rebase before push, log conflicts, flag does not block | §8 here + `COORDINATION.md` claim block (in progress → done) | `COORDINATION.md` |
| R10 | Pull request and merge: verify combined data, confirm no broken links, build passes, merge without waiting, confirm Pages deploy, record PR link/merge result, publish flagged items | R8 task + this file + Pages workflow | `.github/workflows/pages.yml` |

---

## 1. Executive summary (important details)

**Q:** A U.S. citizen has money in a Chinese bank account and is told that turning it into dollars means "a considerable amount of taxes." What is the best lawful way out, and what does it really cost?

All bank figures use the **Bank of China board published 2026/11/10 17:39:58 Beijing** (S01): Buying 665.71, Selling 668.51 per 100 USD → mid 667.11, half-spread **0.2094%**. Wire: **1‰ min ¥50 max ¥260 + ¥150 cable** (S02). The same board re-read 2026/11/11 10:25:02 shows Buying 666.30/Selling 669.11/Middle 671.91; figures were NOT repriced (flag U15). The BOC Middle column is a reference rate, not the midpoint — the site says so.

1. **Converting and wiring is not taxed.** No official source read here taxes the conversion or the wire. State Council Decree 532 Art.5: "国家对经常性国际支付和转移不予限制" — current payments/transfers not restricted (S17). What the bank checks is proof of origin + tax evidence: SAFE Tianjin 2026-07-13 Art.59 "境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）" (S04); SAFE Tianjin 2021-11-02 lists service/trade, gains, current transfers with tax certificate or exemption or the tax-filing form (S11).
2. **The only large Chinese tax is on the underlying income, not the transfer.** If Chinese income tax was never paid on the money, it is owed whether or not it moves: PRC IIT Law Art.3: 综合所得 3%–45% progressive; 利息、股息、红利、财产租赁、财产转让 20% flat (S25); savings-deposit interest exempt since 2008-10-09 (S26) (excerpt, U11). Which of these applies is unknown (U01, U02).
3. **The bank's own cost is small.** `$53.38` on `$10,000`, `$270.75` on `$100,000`, `$899.01` on `$400,000` in one wire (S01+S02, see §5). Intermediary/receiving-bank fees are not published anywhere official → blank (U04). Dividend route includes 20% Chinese tax → far larger (see §5).
4. **A U.S. passport does not get the USD 50,000-a-year convenience amount** that Chinese citizens use on ID alone; only holders of the **Foreign Permanent Resident ID** do (S05 Tianjin 2024 answer × S06 Ningxia 2022 answer). A U.S. citizen's lawful route depends on *what the money is*: documented income, home-sale proceeds, inheritance, emigrant pre-departure property, unspent inward FX, or FX already in the account. Gift / undocumented RMB has no verified conversion route (U07, S04).
5. **The U.S. side can be larger.** Selling RMB for dollars is a §988 disposition of nonfunctional currency → foreign-currency gain is **ordinary income** (S27, 26 U.S.C. §988(a)(1)(A),(c)(1)(C)); personal-transaction exclusion only if gain ≤ $200 (S27 §988(e)(2)). RMB acquired at IRS 2024 average 7.189 shows ~7% gain today (S28). FBAR, Form 8938, Form 3520 each carry penalties if missed (S29,S30,S31,S32,S33).

**Cheapest lawful sequence:** classify origin → fix U.S. reporting first → use the channel with no ceiling: **emigrant property transfer** (移民转移, PBOC [2004] No.16) or **non-resident current-account income conversion** (个人外汇管理办法 Art.13, S18; SAFE Art.59, S04). Splitting through relatives' quotas is prohibited (P01, S10/S22/S17) → watch-list 2 years + fine up to 30% (serious 30–100%) + possible criminal liability (S17 Arts.39–40,45).

**Cost at a glance (known bank cost only; last two cols = U.S. currency gain if RMB acquired at that IRS average, not tax):**

| Amount | Already USD: wire only | Convert+wire once | USD 50k/yr (PR-ID holders) | Gain if acquired 2024 | Gain if acquired 2025 |
|---|---|---|---|---|---|
| $10,000 | $32.44 | $53.38 | $53.38 (1 yr) | $701 | $623 |
| $50,000 | $61.33 | $166.04 | $166.04 (1 yr) | $3,505 | $3,113 |
| $100,000 | $61.33 | $270.75 | $332.08 (2 yr) | $7,009 | $6,227 |
| $200,000 | $61.33 | $480.17 | $664.16 (4 yr) | $14,019 | $12,453 |
| $300,000 | $61.33 | $689.59 | $996.25 (6 yr) | $21,028 | $18,680 |
| $400,000 | $61.33 | $899.01 | $1,328.33 (8 yr) | $28,037 | $24,907 |

Full ladder (every $10k step for every route): https://sassnarep3-star.github.io/China3/dashboard/costs.html · data: `data/e347_costs.csv`.  
Currency-gain ladder by acquisition year: `data/e347_fx_gain.csv` + `us-fx-gain.html`.

---

## 2. Questions / Informations / Answers needed before any decision

**Status today:** All 19 open items are listed on `dashboard/flagged.html` (U01–U19), each with the official source that creates the question. Three decide the answer and cannot be settled from public sources alone.

### The three that decide the lawful route

| ID | Question | What is known | What is missing | How to discover it |
|---|---|---|---|---|
| **U01** | Where did the money come from? | The brief says only "money stuck in a Chinese bank account." No source (salary, business profit, property sale, gift, inbound FX) is stated. The lawful route is determined entirely by origin (S04 Art.59, S12 Art.2, S15 §8, S09 Art.60). | Bank statements + the documents behind each large deposit (employment contract + payslips + tax receipts; sale contract + registration proof; inheritance certificate; company accounts + resolution, etc.). | Export the last 3–5 years of statements from the Chinese bank's app. For each deposit > ¥50,000, ask the branch which Article it would treat it under and what documents it wants. Get it in writing; banks apply Art.59 vs Art.52(2) differently (U10). |
| **U02** | What is the "considerable amount of taxes"? | No tax, rate, amount, or assessing office is named. The site found **no tax on conversion itself** (S17 Art.5, S04); the likely candidates are PRC IIT on the underlying income (3%–45% wages, 20% property/dividends, S25) or an unpaid U.S. income/FBAR penalty. | The bank's or tax office's written statement of what would be charged, and for which year/category. | Ask the branch in writing: "If I apply under Art.59 with *this* source, will you require a tax certificate, the filing form, or an exemption, and for what amount?" + Ask the local tax office where the income arose for a tax certificate or a "no tax due" letter. Keep both letters; they are the filing evidence for the bank (S11, S16). |
| **U07** | Was any of it a gift or received without documents? | No official rule was found that lets a foreign-passport holder convert RMB received as a gift or RMB whose origin cannot be documented. No route is listed for that case (S04 requires transaction-amount evidence incl. tax proof). | Gift agreements, donor identity, donor's own transfer records, or proof of lawful origin. | Check whether the donor can move the money lawfully themselves (e.g., emigrant/inheritance route), or whether the RMB can be returned to the donor's documented route. If not, a written "no-documented-route" reply from the bank decides that the amount cannot be converted under current rules — do not try P01–P06. |

### Every open item (full list)

| Flag | Item | Why it matters / what to do | Official link |
|---|---|---|---|
| **U01** | Where the money came from | Decides route; no route recommended as fact about your case | https://www.safe.gov.cn/tianjin/2026/0713/3088.html (S04) |
| **U02** | The "considerable taxes" | Name, rate, office not stated; no conversion tax found | https://www.safe.gov.cn/safe/2008/0806/5321.html (S17) |
| **U03** | Your bank's actual rate/fees | Figures use BOC public board/tariff; branch differences/promotions not captured (tariff Note 1) | https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html (S02) |
| **U04** | Intermediary/receiving-bank fees | No single official figure; blank in every cost table | https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html (S02) |
| **U05** | Whether currency gain is "personal" | §988(e) $200 exclusion; §162/§212 expenses make it non-personal — legal judgment, not decided here | https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm (S27) |
| **U06** | U.S.–China treaty dividend rate | Treaty not read in this pass; dividend priced at statutory 20% only | https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html (S25) |
| **U07** | Gift / undocumented RMB | No verified route | https://www.safe.gov.cn/tianjin/2026/0713/3088.html (S04) |
| **U08** | Chinese inheritance tax | IIT Law lists 9 categories; inheritance not one, but no "not taxed" statement read | S25 + S12 |
| **U09** | Cross-border RMB route cost (L08) | PBOC 2018 support (S24) but no outbound RMB fee/offshore FX rate published → blank | http://beijing.pbc.gov.cn/beijing/132026/3660457/index.html (S24) |
| **U10** | Two definitions of "domestic individual" | Reg. Art.52(2) = 1-year resident foreigner; Measures = by ID at account opening — bank decides which it applied | S17 + S18 |
| **U11** | 9 sources as excerpts | S08,S15§8,S18,S22,S23,S24,S26,S33,S34: official text via search excerpt, not full page | see Sources page |
| **U12** | FBAR willful ceiling | eCFR $165,353 (S31); statute's 50%-of-balance alternative not read, not stated | https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821 |
| **U13** | ATM route: FX rate + ATM fee | Only BOC card fee priced; UnionPay rate + ATM-owner fee blank | https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html (S03) |
| **U14** | Cash route: banknote fee | Priced at cash selling rate only; counter fee/travel blank | https://www.boc.cn/sourcedb/whpj/enindex_1619.html (S01) |
| **U15** | One rate snapshot | Site uses 2026/11/10 17:39:58 board; 2026/11/11 board (6.6630/6.6911/6.7191) not repriced; rows spanning years reuse one day | https://www.boc.cn/sourcedb/whpj/enindex_1619.html (S01) |
| **U16** | 2024 Capital Guidelines | §6.4 known only via 2026-03-19 Tianjin answer (S14); 2004 lists read in full | https://www.safe.gov.cn/tianjin/2026/0319/3018.html (S14) |
| **U17** | Property route 2025 guide | Doc list from SAFE Anhui excerpt §8 (S15); other property taxes (VAT/deed/LAT) not verified | https://www.safe.gov.cn/anhui/file/file/20250925/43f09589bb2046c2a01a58d3a80c2b5f.pdf (S15) |
| **U18** | Money-transfer apps/companies | No official page confirms a licensed app can send a personal RMB balance to the U.S.; SAFE says only banks/licensed exchangers may convert (S21) → no route listed | https://www.safe.gov.cn/guangdong/2020/0304/1668.html (S21) |
| **U19** | Ten legacy routes not re-read | Ten rows from earlier passes kept with cited page, no re-verdict, no cost | same |

**If you want a decision you can rely on**, bring these three to a Chinese-licensed accountant (for the PRC tax question) and a U.S. CPA familiar with §988/FBAR: (1) the source-classification letter from the bank, (2) the tax-office certificate or tax-filing form, (3) the acquisition dates/rates of the RMB (for §988), plus FBAR history. The brief alone does not supply any of them — that is why "a considerable amount of taxes" cannot be verified.

---

## 3. Every lawful way to turn CNY into USD (11 lawful + 6 prohibited) — pros/cons/tax/penalty

All 17 are on `dashboard/methods.html` (each row links to the official page that authorizes or prohibits it). 11 lawful routes have a cost in `data/e347_costs.csv`; 6 prohibited have no price, only the penalty.

### Lawful routes

| ID | Route (use when) | Limit | Pros | Cons | Tax / penalty | Bank cost at $100k | Official source |
|---|---|---|---|---|---|---|---|
| **L01** | Documented income earned in China (salary, fees, other current-account income — S04 Art.59, S11, S16) | No ceiling. Tax evidence = certificate, exemption, or tax-filing form; filing required for single payment > $50k (S16 Art.1) | Standard route for foreign passport holder; one wire for whole amount; lowest conversion cost | Must show source docs + tax evidence; if tax unpaid, must settle first | No conversion tax (S17 Art.5); underlying IIT 3%–45% wages / 20% flat (S25) if unpaid; open U01/U03/U04 | $270.75 | S04 S05 S11 S16 S25 |
| **L02** | Change back unused RMB with original exchange slip (S09 Art.60) | Up to unused amount on slip; slip valid 24 months; without slip $500/day | Passport + slip only; no income/tax docs | Only for own inbound FX reversed; older slips void | None (own money back); U03/U04 | $270.75 | S09 |
| **L03** | Wire out FX already in your FX account (S08 Art.65(1), S18 Art.13–14) | Foreign individual's FX-account remittance on passport; no amount threshold in rule | No conversion → no spread; cheapest: wire fee only | Only for part already in FX; bank's own checks remain | None; U04/U11 | **$61.33** | S08 S18 S02 |
| **L04** | Home-sale proceeds (S15 §8, S25/S16) | ≤ sale price minus taxes of that sale (your share) | Fixed doc list; large amounts possible in one remittance | Title transfer + tax must finish first; certificate caps amount | 20% on gain (price − cost − reasonable expenses, S25 Art.6(5)); other property taxes unverified U17 | $270.75 | S15 S25 S16 |
| **L05** | Inheritance (继承财产转移) — needs SAFE approval (S12 Art.2,8,11,13; S13 §6; S14 §6.4) | One estate application at decedent's last hukou; bank remits once/instalments after approval | Dedicated large-sum route to own account in residence country | Needs SAFE approval + inheritance proof + property docs + tax cert; preparation time | Tax cert required; Chinese inheritance tax **not confirmed** U08; U.S. foreign bequest >$100k → Form 3520, late penalty 5%/mo up to 25% (S32,S33) | $270.75 | S12 S13 S14 S32 |
| **L06** | Emigrant property transfer (移民财产转移) — needs SAFE approval (S12, S13 §6, S14) | One application for all property at former hukou; since 2014 may remit once/instalments | Dedicated route for former resident's savings/property; no annual quota | Needs hukou-cancellation proof + embassy settlement cert + property/tax docs; not for never-residents | Tax certs required; unpaid IIT must settle; U16 | $270.75 | S12 S13 S14 |
| **L07** | Annual USD 50k convenience amount with Foreign Permanent Resident ID (S05,S06) | $50k/person/yr on that ID alone; above it → L01 | No docs inside yearly amount | Slow: $400k = 8 years; U.S. passport alone does **not** qualify | None on conversion; U15/U03/U04 | $332.08 at $100k (2 yrs) | S05 S06 |
| **L08** | Send RMB abroad as cross-border RMB, convert outside (PBOC 银发〔2018〕3号 via S24) | Current-account income only; bank must offer it to individuals | No onshore conversion | Offshore FX rate/fee unpublished → cost blank; not every bank offers | Same as L01 underlying | **not verified** (U09) | S24 (excerpt) |
| **L09** | Dividend from own Chinese company (S13 §5, S25, S16/S34) | Genuine distributable profit; >$50k needs resolution + tax filing form | Proper business route; no quota | 20% dividend tax; needs accounts + resolution + filing; not for personal savings | 20% (S25); treaty lower rate unverified U06; creditable on U.S. Form 1116 (S34) | $20,228.87 at $100k (incl. $20k tax) | S13 S25 S16 S34 |
| **L10** | UnionPay ATM withdrawals abroad (S19+S03+S35) | ¥10,000/card/day; ¥100,000/person/yr all cards; exceed → suspend this+next year; no borrowing cards | No docs; while traveling | ~1.1% card fee + unpublished FX/spread; $400k = 27 years; borrowing prohibited (P06) | None; cash >$10k into U.S. declare FinCEN 105 (S35) | $1,120.27 at $100k (fees only, rate extra) U13 | S19 S03 S35 |
| **L11** | Carry FX cash out in person (S20+S35+S01) | ≤$5k no permit; $5k–$10k bank permit; >$10k SAFE permit, in principle not allowed; U.S. >$10k/group declare | No wire/receiving-bank fees | Still needs lawful purchase; 80 trips for $400k; theft risk | None; same $10k declaration (S35) | $209.42 at $100k (spread only; banknote fee U14) | S20 S35 S01 |

Ten further rows at the bottom of the Methods page (legacy passes) are kept with their cited page but **not re-verdicted/costed** this pass (U19).

### Prohibited routes (fines from State Council Decree 532 — official penalties)

| ID | What it is | How it is caught | Fine | Possible criminal | Source |
|---|---|---|---|---|---|
| **P01** | Using relatives'/friends' $50k amounts ("ant moving," splitting) | 5+ people buying FX then sending to one recipient on same/neighboring days (汇发〔2009〕56号; S22 Zhu case: 52 people → $2.5625m, punished as 逃汇) | Up to **30%** of amount; serious **30%–100%** | Yes (Art.45, Art.10 SPC/SPP) | S10 S22 S17 Art.39–40,45 |
| **P02** | Private FX buying/selling (underground bank, friends-group swap, money-changer) | SAFE Guangdong 2020 notice: only banks/licensed exchangers may convert; others are illegal (S21) | Warning + **confiscation** + up to **30%**; serious **30%–100%** | Yes (illegal business operation: Art.225(4) if ¥5m business or ¥100k illegal gain; Art.2 法释〔2019〕1号, S10) | S21 S17 Art.45 + S10 |
| **P03** | False/altered documents to buy FX | Checked by SAFE; Art.40 false-docs-buying; Art.48 untrue docs: individuals up to **RMB 50,000** | Same as P01/P02 (up to 30%; serious 30–100%) | Yes | S17 Art.40,48 |
| **P04** | Fleeing FX / evading quotas (e.g., mis-declaring, carrying cash past customs) | Art.39 逃汇, Art.42 carrying FX across border in breach | Art.39 same 30%/30–100%; Art.42 warning + max **20%** | Yes | S17 Art.39,42 |
| **P05** | Virtual-currency / stablecoin workaround | PBOC 银发〔2026〕42号 (S23) effective 2026-02-06, repealing 2021 notice: RMB↔virtual currency, RWA tokenization → illegal financial activity; no institution may service | — (illegal activity; void acts) | Liability under §18–19 | S23 + S17 |
| **P06** | Lending/borrowing bank cards to evade ¥100k/yr ATM cap | SAFE 汇发〔2017〕29号 S19: "个人不得通过借用他人银行卡或出借本人银行卡等方式规避" | Suspension current+next year; treated as P01 splitting if systematic | Yes if part of P01/P02 | S19 |

U.S. reporting penalties are separate and can dwarf the bank cost: **FBAR willful max $165,353** (S31 eCFR table 2025) or **50% of balance** (statute 31 U.S.C. 5321(a)(5)(C) not read this pass → flag U12); **Form 8938: up to $10,000 + $10,000/30 days up to $60,000** (S29); **Form 3520 foreign gift: 5%/mo up to 25%** (S33); false statements / structuring: additional criminal exposure.

### The "conversion penalty" broken down

| Component | What it is | Rate/amount (this board) | Varies with | Tax? | Source |
|---|---|---|---|---|---|
| FX spread | Bank sells at ask; you "lose" ask−mid | **0.2094%** (ask 6.6851, bid 6.6571, mid 6.6711) | Same for every conversion route; moves with board (U15) | No | S01 |
| Wire + cable | BOC personal e-banking cross-border wire (non-HK/Macau/Taiwan) | **0.1% min ¥50 max ¥260 + ¥150 cable** → $32.44 at $10k, $61.33 flat from ~$38,862 onward (cap binds) | Number of wires; $400k as one wire = $61.33; as eight $50k wires = $132.86+spread (→ $1,328.33 total) — both shown; lawful single-wire is correct (S12 Art.11 remits to own account; no splitting rule remains since S13) | No | S02 |
| Intermediary / receiving-bank fees | Deducted by correspondent / U.S. bank | **Unpublished → blank** (U04) | Banks' tariffs; charge option (OUR/SHA) | No | flagged U04 |
| Chinese income tax on underlying money | Only if still unpaid (wages 3%–45%, property gains/dividends 20%) | Depends on origin; dividend priced at 20% (U06) | Origin; U01 decides | **Yes — PRC tax** | S25 + S16 |
| U.S. currency gain §988 | Selling RMB held as bank deposit = disposition of nonfunctional currency → ordinary gain = (ask − acquisition price)×USD at acquisition; exclusion only ≤$200 gain | **~7.01% of USD received for CNY bought at 2024 IRS avg 7.189** → $28,037 gain on $400k; at 37% = ~$10,374 tax (same for every lawful channel) — illustration, basis unknown U05 | Acquisition date/rate; your bracket; personal vs investment character | **Yes — U.S. tax** | S27 (govinfo), S28 (IRS avg) |

> **Lesson:** There is **no Chinese "conversion tax"** on the wire. The "penalty" people feel is four things confused: permission (capital controls), PRC tax on whatever created the money, U.S. reporting penalties, and U.S. §988 gain. The bank cost is the smallest line.

---

## 4. What is the least-penalty lawful path for a U.S. citizen?

**General research, not advice.** The answer depends on origin (U01). Under the sources read:

**If the RMB is documented lawful income, sale proceeds, an inheritance, or pre-emigration property, and your Chinese bank account is still under your foreign passport (S18 Art.28), the cheapest lawful path with no quota ceiling is:**

1. **Fix U.S. reporting first** — FBAR (FinCEN 114) if aggregate foreign accounts >$10k any time (S30); Form 8938 if over its threshold (S29, e.g. $50k/$75k single living in U.S., $200k/$300k living abroad); Form 3520 if a foreign gift/bequest >$100k (S32). Willful FBAR penalty alone can be $165,353 or 50% of balance — 10× any FX cost.
2. **Classify the money at the Chinese bank** — ask in writing which SAFE Article applies (Art.59 for foreign individuals' current-account RMB income via S04, Art.60 for unspent inbound FX via S09, PBC [2004] No.16 Arts.8–11 for emigrant/inheritance via S12, §8 via S15 for home-sale proceeds). Get the document checklist in writing; the two definitions of 境内个人 (Reg Art.52 vs Measures Art.28) mean the bank's registration matters (U10).
3. **Prepare tax evidence** — salary/other current income: tax certificate / exemption / the tax-filing form (S11,S16). Single outbound payment >$50k in listed categories (salary, dividends, property-transfer income: S16 Art.1) needs **对外支付税务备案** *before* the wire; it is not an extra tax, but the tax office will collect any unpaid tax then (S16 Art.9). Property sale: 20% on gain (S25). Dividend: 20% (S25) — treaty read needed for lower rate (U06). Unpaid IIT must be settled by 30 June following year if payer didn't withhold (S25 Art.13).
4. **Convert + wire once** from the same bank that checked the documents: the bank buys USD at ask 6.6851 and wires to your own U.S. account (L01, L04, L05, L06). One wire = lowest fee. Splitting across people/years to dodge limits is prohibited (P01).
5. **Currency-gain handling in the U.S.** — if the RMB appreciated since acquisition, §988 gain is ordinary income; track acquisition date/rate (U05, S27+S28). The $200 personal-transaction escape is transaction-by-transaction, not annual; expenses under §162/§212 make it non-personal.

**If you hold the Foreign Permanent Resident ID**, you *also* have the $50k/yr convenience amount on ID alone (L07, S05). For $400k that is 8 yearly wires costing $1,328.33 vs $899.01 in one documented-income wire — slower *and* more expensive, so only useful for money that cannot be documented.

**If part of the balance is already foreign currency** (e.g., inbound wire never converted), wire it as FX (L03, $61.33) — no spread.

**Do not:** borrow quotas (P01), use private swaps/money changers/apps (P02, U18), present false docs (P03), carry cash >$5k without permit or >$10k at all (P04), or try crypto (P05). Penalties: fines up to 30% (serious 30–100%) + criminal + watch-list.

---

## 5. Costs — every method at every $10,000 from $10,000 to $400,000 (most important first)

**Known bank cost only.** Intermediary/receiving fees → blank U04, not in any total. Tax → blank U01 and on `dashboard/tax.html`. One FX snapshot → flag U15.

### 5.1 How the numbers are made (no hallucinations)

- **Board (S01):** bid 665.71/ask 668.51/Middle 671.67 per 100 USD at `2026/11/10 17:39:58`. Derived: mid = (665.71+668.51)/2 = **667.11** per 100 → **6.6711/USD**; spread = (668.51−667.11)/668.51 = **0.2094%**.
- **Wire (S02):** fee = max(¥50, min(¥260, USD×668.51/100 × 0.001)) + ¥150 cable, ÷ 668.51/100 → USD. Caps at **¥260+¥150** from $38,862 → **$61.33** flat. Spread per $: USD×(ask−mid)/ask = USD×0.002094. Total = spread + wire.
- **Verifier:** `scripts/e347_verify.py` re-derives every `data/e347_costs.csv` row from those two fractions with exact arithmetic (Fraction, round-half-up to cents). Result: **PASS — 440 rows recomputed exactly**.

### 5.2 The answer at six amounts (kpi cards on the home page)

| Route | $10,000 | $50,000 | $100,000 | $200,000 | $300,000 | $400,000 | Time for $400k |
|---|---|---|---|---|---|---|---|
| **L01 Documented income** (S04) | $53.38 | $166.04 | $270.75 | $480.17 | $689.59 | **$899.01** | 1 wire |
| **L02 Original slip** (S09) | $53.38 | $166.04 | $270.75 | $480.17 | $689.59 | $899.01 | 1 wire |
| **L03 Already FX** (S08,S18) | $32.44 | $61.33 | $61.33 | $61.33 | $61.33 | $61.33 | 1 wire |
| **L04 Home sale** (S15) | $53.38 | $166.04 | $270.75 | $480.17 | $689.59 | $899.01 | 1 wire |
| **L05 Inheritance** (S12) | $53.38 | $166.04 | $270.75 | $480.17 | $689.59 | $899.01 | 1 wire |
| **L06 Emigrant property** (S12) | $53.38 | $166.04 | $270.75 | $480.17 | $689.59 | $899.01 | 1 wire |
| **L07 $50k/yr PR-ID** (S05) | $53.38 | $166.04 | $332.08 | $664.16 | $996.25 | $1,328.33 | 8 yrs |
| **L08 Cross-border RMB** (S24) | not verified | not verified | not verified | not verified | not verified | not verified | — |
| **L09 Company dividend** (S13,S25) | $2,047.19 | $10,145.10 | $20,228.87 | $40,396.40 | $60,563.94 | **$80,731.48** | 1 wire |
| **L10 ATM** (S19,S03) | $112.57 | $561.03 | $1,120.27 | $2,240.53 | $3,360.80 | $4,481.07 | 27 yrs |
| **L11 Carry cash** (S20) | $20.94 | $104.71 | $209.42 | $418.84 | $628.25 | $837.68 | 80 trips |

*Dividend row includes 20% PRC tax (treaty not read → flag U06). ATM/cash rows: only published part; rates/fees/travel extra (flags U13, U14).*

### 5.3 The full $10,000-step ladder (40 increments) — every row in `data/e347_costs.csv`

The complete ladder lives in `data/e347_costs.csv` and is rendered on `dashboard/costs.html` (mobile: stacked cards; most important info first: kpi cards → all-routes-at-six-amounts → what-numbers-built-from → full 40-step ladder → $10,000-step table by route). Columns: `method_id, amount_usd, model, units, units_label, calendar_years, spread_usd, fee_usd, tax_usd, known_cost_usd, known_cost_pct, rmb_debited, not_included_flags, source_ids, source_urls`. Every row carries an official `source_urls`; blank cost cells carry a flag that exists on `dashboard/flagged.html` (verifier check).

**Excerpt — documented-income / slip / home-sale / inheritance / emigrant (fx_wire/property model; fee includes cable):**

| Amount | Spread | Wire+ cable | Known total | Known % | RMB debited | Source |
|---|---|---|---|---|---|---|
| $10,000 | $20.94 | $32.44 | $53.38 | 0.53% | ¥66,851 + fees | S01 S02 S04 |
| $20,000 | $41.88 | $42.44 | $84.32 | 0.42% | + | S01 S02 S04 |
| $30,000 | $62.83 | $52.44 | $115.26 | 0.38% | + | S01 S02 S04 |
| $40,000 | $83.77 | $61.33 | $145.10 | 0.36% | + | S01 S02 S04 |
| $50,000 | $104.71 | $61.33 | $166.04 | 0.33% | + | S01 S02 S04 |
| $60,000 | $125.65 | $61.33 | $186.98 | 0.31% | + | S01 S02 S04 |
| $70,000 | $146.59 | $61.33 | $207.93 | 0.30% | + | S01 S02 S04 |
| $80,000 | $167.54 | $61.33 | $228.87 | 0.29% | + | S01 S02 S04 |
| $90,000 | $188.48 | $61.33 | $249.81 | 0.28% | + | S01 S02 S04 |
| $100,000 | $209.42 | $61.33 | $270.75 | 0.27% | ¥668,510 +¥410 | S01 S02 S04 |
| $110,000 | $230.36 | $61.33 | $291.69 | 0.27% | + | S01 S02 S04 |
| $120,000 | $251.31 | $61.33 | $312.64 | 0.26% | + | S01 S02 S04 |
| … | … | … | … | … | … | … |
| $400,000 | $837.68 | $61.33 | $899.01 | 0.22% | ¥2,674,040 +¥410 | S01 S02 S04 |

**Full 40-step table:** `dashboard/costs.html` → "Every $10,000 step" (also `data/e347_costs.csv`, 440 rows over 11 models). **U.S. currency-gain ladder:** `data/e347_fx_gain.csv` (gain vs IRS yearly average for 2021–2025) → `dashboard/tax.html` (§988 gain table) + `us-fx-gain.html` deep page.

### 5.4 Step-by-step — exactly how each transfer works (the playbook)

Every route's steps are on `dashboard/steps.html`, numbered and each step cites its official source. Short form:

- **L01 Documented income (S04,S11,S16,S25,S02,S01):**
  1. Confirm income class; gather employment/service contracts, payslips, bank receipts, tax certificates or exemption (S04 Art.59, S11) — if single payment >$50k, do the tax filing first (S16 Art.1,4,9).
  2. Take passport + source dossier + tax evidence to the bank; bank checks origin+tax (S04).
  3. Bank converts at S01 ask and wires to your own U.S. account (S02 tariff); FBAR/8938/3520 considerations remain (S30,S29,S32).

- **L02 Original slip (S09):** Passport + exchange slip ≤24mo (S09 Art.60) → bank redeems slip → wires (S02/S01). No income docs. Over $500/day without slip → docs again.

- **L03 Already FX (S08 Art.65, S18 Art.13-14, S02):** Confirm FX sub-account balance; passport → bank wires FX on ID (S08 Art.65(1)); fee per S02; no conversion (S01 not used).

- **L04 Home sale (S15 §8,S25,S16):** Close sale + title transfer registered at housing authority (S15) → pay taxes (20% on gain S25 Art.6(5)) → obtain tax cert → bank checks contract + registration + cert; amount ≤ price−taxes (S15) → converts+wires (S01/S02). If >$50k single, tax filing form required (S16).

- **L05 Inheritance (S12 Arts.2/8/9/11/13, S13 §6, S14 §6.4):** Inheritance proof + decedent property docs → tax cert at estate property location (S12) → embassy settlement cert → apply once to SAFE at decedent's last hukou (S13/S14) → after SAFE approval (核准件) bank converts+wires to own account abroad (S12 Art.11); instalments allowed (S13).

- **L06 Emigrant (same, S12+S13+S14):** Proof of former hukou cancellation + embassy settlement cert + property/tax docs → apply once at former hukou SAFE → bank remits to own foreign account after approval; staging rule removed 2014 (S13).

- **L07 PR-ID $50k/yr (S05,S06):** Foreign Permanent Resident ID → bank sells $50k/yr on ID alone (S05) → wire (S02); above → L01 (S06).

- **L08 Cross-border RMB (S24 PBOC Beijing example):** Confirm bank offers personal cross-border RMB for current income (S24 银发〔2018〕3号 example: foreign employee salary in RMB sent as RMB) → prepare same income/tax evidence as L01 (document list not verified U09) → remit RMB to own offshore RMB-capable account → convert offshore (rate/fee blank U09).

- **L09 Company dividend (S13 §5,S25,S16,S34):** Distributable profit confirmed + taxed → board/resolution (S13) → withhold 20% IIT (S25) → >$50k filing form (S13+S16) → bank converts+wires after-tax dividend; U.S. claims credit via Form 1116 (S34).

- **L10 ATM (S19+S03+S35):** UnionPay debit enabled (S19) → withdraw ≤¥10k/card/day, ≤¥100k/person/yr all cards → BOC fee ¥12 +1% max ¥112 (S03) → own exchange rate + ATM-owner fee extra (U13) → U.S. >$10k cash declare FinCEN 105 (S35).

- **L11 Carry cash (S20+S35+S01):** Lawfully buy FX first (L01/L02/L07) → ≤$5k customs clear; $5k–10k bank carrying permit; >$10k SAFE permit in principle not granted → U.S. declare >$10k/group (S35).

---

## 6. Repo review — line by line, verified from official trusted sources

Reviewed as of commit `d9763dc` (+ this file). Every substantive claim was checked against a government/regulator/central-bank or BOC page. No hallucination. The live site's `sources.html` lists 35 pages with what each establishes and whether it was read in full or as an excerpt of the official text.

### 6.1 File inventory (what exists, what it is, is it generated)

| File | Kind | Verified? | Notes |
|---|---|---|---|
| `README.md` | doc (hand-written + generated sections) | yes — describes dashboard layers, earlier passes | Landing summary; points to `EXECUTIVE_SUMMARY.md` + Pages URL |
| `EXECUTIVE_SUMMARY.md` | doc | yes — 5-point answer, cost at a glance, route table, open items (U01,U02,U07) | Short version of §1 above |
| `COORDINATION.md` | task board (append-only) | yes — claim blocks with IDs, status, owner, scope, log | This session appends; no sibling work deleted; rebase conflict at `d9763dc` kept both sides verbatim |
| `VERIFICATION.md` | verification log (preserved) | yes — 27 sources cross-checked, 5 cross-checks detailed, 8 blanks listed | Lists S01–S27 + 5 rejected URLs; each provision checked |
| `REPO_AUDIT.md` | audit (prior session) | yes — A1–A8 + S1–S5 findings; flagged LICENSE/absence, CI, Pages, COORDINATION | Superseded by this audit for current commit but kept |
| `index.html` | **generated** by `scripts/e347_build.py` (generator meta `e347-dashboard`) | yes — `e347_verify.py` meta + nav (8) + h1 + tables check | Hero, kpis, ranked-path table, ladder rows, open items, links; mobile notes |
| `dashboard/methods.html` | generated | yes — 17 routes, each source cell official, prohibited rows carry penalty | 11 lawful +6 prohibited + 10 legacy rows (U19) |
| `dashboard/costs.html` | generated | yes — 440 rows recomputed; kpis, 6-amount grid, full ladder, per-route 40-step | Most important info first: kpis → 6-amount grid → inputs → full ladder |
| `dashboard/steps.html` | generated | yes — 68 numbered steps, each official | Step-by-step per route |
| `dashboard/tax.html` | generated | yes — PRC IIT categories, U.S. §988 + FX-gain table, reporting/penalties | Chinese tax + U.S. tax + FBAR/8938 + penalties |
| `dashboard/flagged.html` | generated | yes — U01–U19 each with why + what would settle + official link | Every blank links here |
| `dashboard/sources.html` | generated | yes — 35 official pages, issuer/title/URL/how/establishes | 26 direct, 9 excerpt (U11) |
| `dashboard/archive.html` | generated | yes — every HTML file the repo publishes, discovered by generator | 82 pages after 76e addition |
| `dashboard/site.css` | static | yes — mobile `stack` tables, kpis, nav | Clean dashboard UI; no JS required for tables |
| `data/e347_costs.csv` | generated | yes — 440 rows, every row `source_urls` on allowlist, blank→flag rule | 11 models × 40 increments |
| `data/e347_methods.csv` | generated | yes — 17 routes, `source_urls` official |  |
| `data/e347_flags.csv` | generated | yes — 19 flags, each `source_urls` official |  |
| `data/e347_sources.csv` | generated | yes — 35 rows, issuer/title/URL/how/establishes |  |
| `data/e347_cost_inputs.csv` etc | generated | yes — inputs captured in `scripts/e347_data.py` RATE + IRS avg |  |
| `data/e347_fx_gain.csv` | generated | yes — FX gain vs IRS averages re-derived (S27+S28) |  |
| `scripts/e347_data.py` | source of truth (hand-written data) | yes — RATE board + wire + IRS avg + SOURCES/TAX_ROWS/flags | Change board figures here, rebuild |
| `scripts/e347_build.py` | generator (hand-written) | yes — html.escape, Fraction, q(), build_costs etc. | Generates 15 files; 0 changed on last run |
| `scripts/e347_verify.py` | verifier (does NOT import engine) | yes — re-implements Fraction arithmetic, recomputes every cost row, checks official allowlist, blank→flag, nav/h1/anchors | PASS: 440 rows, 659 table rows, 380 blanks, 2139 links, 146 data rows with official URLs |
| `.github/workflows/pages.yml` | CI/CD | yes — checkout, e347_build + e347_verify, configure-pages, upload-artifact, deploy on `main` only | Build job validates navigation before deploy |
| `.github/workflows/e347-verify.yml` etc | CI gates (16 workflows) | yes — per-layer freshness, link, cost checks | m5f19 check J now claim-aware after 76e takeover |
| `76e-verification.html` etc | layer from session 76e3e41f | yes — 76e verifier PASS (40 ladder rows, 18 sources, 7 findings) | Additive; not edited here |
| `c3x-*`, `d646-*`, `s775-*`, `m5f19-*`, `a513-*`, `s436-*`, `deep-*`, `s119-*`, `a058-*`, `a502-*`, `deep-*`, `us-fx-gain.html` etc | layers from prior sessions | yes — each has its own verifier PASS | Kept verbatim; not edited; listed in Archive |
| `index.html` vs `legacy-index.html` | generation note | yes — root `index.html` is `e347_build.py` output; earlier landing is `legacy-index.html` | No sibling page needs to edit `index.html` |

### 6.2 Key source verification (the critical rates/fees/rules, each with the official sentence)

- **S01 BOC board (2026/11/10 17:39:58):** "USD per 100: Buying 665.71, Cash Buying 665.71, Selling 668.51, Cash Selling 668.51, Middle 671.67; Pub Time 2026/11/10 17:39:58." → mid = (665.71+668.51)/2 = 667.11 → **6.6711/USD**; **spread = 0.2094%**. Re-read 2026/11/11: Buying 666.30/Selling 669.11/Middle 671.91 at 10:25:02 → not repriced (U15). *Manual check:* https://www.boc.cn/sourcedb/whpj/enindex_1619.html
- **S02 BOC tariff (personal e-banking):** "跨境汇款（电汇）: 每笔汇款金额的1‰，最低50元/笔，最高260元/笔；另收电讯费，非港澳台地区150元/笔." Note 1: agreements/discounts/local differences can apply. Effective since 2014-11-01 (prior typo fixed). *Manual check:* https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html
- **S03 BOC ATM notice (effective 2026-11-11):** "Overseas ATM withdrawal: UnionPay 每笔（12元+取现金额的1%），最高112元/笔." *Manual:* https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html
- **S04 SAFE Tianjin 2026-07-13 Art.59:** "境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）." *Manual:* https://www.safe.gov.cn/tianjin/2026/0713/3088.html
- **S05 Tianjin 2024-06-21 (same Art.59):** "持有外国人永久居留身份证的境外个人适用购汇年度便利化额度." *Manual:* https://www.safe.gov.cn/tianjin/2024/0621/2529.html
- **S06 Ningxia 2022-09-29 (annual amount):** "个人结汇和境内个人购汇实行年度便利化额度管理，便利化额度分别为每人每年等值5万美元. 年度便利化额度不是…限额." *Manual:* https://www.safe.gov.cn/ningxia/2022/0929/1997.html
- **S08 SAFE 2020 Guidelines Arts.54-68 (excerpt, U11):** Art.65: "外汇账户内外汇汇出，凭本人有效身份证件办理; 持外币现钞汇出，当日累计等值1万美元以下（含）的，凭本人有效身份证件办理." Art.67 cross-border account transfers. *Manual:* http://m.safe.gov.cn/safe/file/file/20200831/f0127756271c43ef9b3908d5d157bd91.pdf
- **S09 Tianjin 2026-09-17 Art.60:** "境外个人原兑换未用完的人民币兑回外汇，凭本人有效身份证件和原兑换水单办理，原兑换水单的兑回有效期为自兑换日起24个月." *Manual:* https://www.safe.gov.cn/tianjin/2026/0917/3134.html
- **S12 PBOC [2004] No.16:** Art.2 emigrant/inheritance; Arts.8-9 docs incl. 税收证明; Art.11 remit to own account; Art.13 false docs → Art.40. *Manual:* http://m.safe.gov.cn/safe/2004/1116/5461.html
- **S13 汇发〔2014〕2号 §5-§6:** Approval at former/last hukou; RMB 500k report + staged-remittance removed ("银行可在核准件审批额度内一次或分次汇出"); §5 profit >$50k needs resolution + tax filing. *Manual:* https://www.safe.gov.cn/tianjin/2024/0903/2594.html
- **S16 STA/SAFE 2013 No.40 Art.1,4,9:** >$50k single outbound (incl. salary, dividends, property-transfer income) → tax filing before payment (对外支付税务备案); if unpaid, tax office pursues;境内个人/境外个人 handling per FX rules. *Manual:* https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html
- **S17 Decree 532:** Art.5 no restriction on current payments/transfers; Art.12 genuine lawful basis; Arts.39-40逃汇/false docs fines ≤30% (serious 30–100%) + criminal; Art.42 carrying FX ≤20%; Art.45 private FX warning+confiscation+30%/30–100%; Art.48 untrue docs up to ¥50k; Art.52(2) 境内个人 includes 1-yr resident foreigner. *Manual:* https://www.safe.gov.cn/safe/2008/0806/5321.html
- **S27 26 U.S.C. §988 (govinfo 2023):** (a)(1)(A) gain = ordinary income; (c)(1)(C) any disposition of nonfunctional currency (incl. bank deposits) is §988 transaction; (e) personal-transaction exclusion only if gain ≤$200; not personal to extent §162/212 expenses. *Manual:* https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm
- **S28 IRS yearly averages:** 2025 7.129, 2024 7.189, 2023 7.075, 2022 6.730, 2021 6.452. "IRS has no official exchange rate." *Manual:* https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates
- **S31 31 CFR 1010.821 (eCFR as of 11/06/2026, re-checked 11/09 in notes):** Non-willful $16,536; willful $165,353 (assessed on/after 2025-01-17). *Manual:* https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821

*(All 35 source rows carry the official URL and a direct quote/excerpt on dashboard/sources.html; check the "how" column for direct vs excerpt.)*

---

## 7. Verification — every table row has a source link; unverified → blank+flag; no inference

**Automated verifier (does not import the engine):** `scripts/e347_verify.py` re-derives every cost cell from the board/tariff fractions, checks every row in `data/*.csv` and every data table row in `index.html` + `dashboard/*.html` carries a URL whose host is on the official allowlist (`boc.cn`, `safe.gov.cn`, `chinatax.gov.cn`, `pbc.gov.cn`, `irs.gov`, `govinfo.gov`, `fincen.gov`, `ecfr.gov`, `cbp.gov`, `gd.gov.cn` — plus `github.com` for self-links), that every blank's `not_included_flags` resolves to an existing `Uxx` on `dashboard/flagged.html`, that no data cell is empty, that every local `href` and `#anchor` resolves, and that the root `index.html` is the e347 landing page (generator meta).

**Result on this tree (2026-11-11, `d9763dc` base + this audit):**

```
PASS — e347: 440 cost rows over 11 routes recomputed exactly; 8 pages, 659 table rows sourced, 380 blank values all flagged, 2139 links resolved, 146 data rows with official URLs.
e347 build: 15 files, 0 changed
PASS — 76e: 40 ladder rows recomputed; 10 Nov convention reproduces 80 L01/L03 cells; page cells equal CSV; 18 re-check rows + 7 findings each cite official page; all local links resolve.
PASS — m5f19: 10 checks, 0 failures; c3x: 16 sources, 40 ladder rows, 560 method rows; d646: 40 rows; s775: 52 sources 24 methods; s436: 36 sources 640 rows; c5bf: 2 boards 40 rows; final-integration: 640 rows; cost-tables: 32 inputs 800 rows; deep: 85 sources 278 rows
```

**Meaning:** The dollar amounts you see on the Costs page are not typed numbers — they are recomputed from the BOC board by a second, independent Fraction implementation, to the cent. Unpublished prices (intermediary fees, offshore FX, ATM FX, cash note fee, treaty rate, processing times, property taxes beyond the 20% gain tax, etc.) are **blank and link to `dashboard/flagged.html`**, not guessed. No row is unsourced; no table has an empty cell.

**Build guarantee:** `python3 scripts/e347_build.py` prints `15 files, 0 changed` before any PR — the pages are byte-identical to a fresh build; `.github/workflows/pages.yml` and `e347-verify.yml` enforce this in CI and will fail a drifted page.

**Manual review:** Every table row's rightmost **Source** cell is a link. Click it to open the government/regulator/bank page that establishes that row. Flagged items (e.g. `U04`) link to `dashboard/flagged.html#U04` which in turn links back to the official page that says what is unknown.

---

## 8. Site creation — the live dashboard (clean, mobile-friendly, category-organised)

**URL:** https://sassnarep3-star.github.io/China3/  
**Deploy:** `.github/workflows/pages.yml` on push to `main`: checkout → `e347_build.py` → `e347_verify.py` → `configure-pages` → `upload-pages-artifact` (path `.`) → `deploy-pages`. PRs run build+verify only; deploy runs only on `main`. Concurrency group `pages-${{ ref == PR ? ref : 'deploy' }}` avoids cancelling a `main` deploy with a PR build. Verified: build + deploy success; Pages API status `built`.

**Landing page (`index.html`, generator `e347-dashboard`):**
- Top: brand + 8-link nav (Home, Methods, Costs, Steps, Tax, Flagged, Sources, Archive) — `aria-current="page"`, resolves on every page.
- Hero: one-sentence answer + 4 kpi cards ($53.38/$270.75/$899.01/$61.33) — most important info first.
- Ranked-path table: 11 lawful routes ordered by least penalty/tax.
- Six-amount cost grid + full 40-step ladder (mobile: `table.stack` collapses headers into `data-label` cards).
- Open items: U01/U02/U07 — why they matter + official source.
- Sections: large linked cards (Methods/ Costs/ Steps/ Tax/ Flagged/ Sources) → category-organised subpages.
- Archive: every HTML file auto-discovered by the generator; 82 pages counted after 76e; no sibling's page deleted.

**Subpages (all `data-kind="data"` tables; every data row has a Source link; mobile stacks via `dashboard/site.css`):**

| Page | What it holds | Rows | Source rule |
|---|---|---|---|
| `dashboard/methods.html` | 11 lawful +6 prohibited +10 legacy rows; pros/cons/limits/tax | ~27 data rows | Every row Source = official page |
| `dashboard/costs.html` | Bank cost per route $10k–$400k in $10k steps | 440 cost rows + inputs | Every row Source = S01/S02 + route rule |
| `dashboard/steps.html` | Playbook: ordered steps per route | 68 steps | Every step cites official doc |
| `dashboard/tax.html` | PRC IIT + U.S. §988 + FX-gain table + FBAR/8938/3520 + penalties | ~20 rows | Every row Source = S25/S26/S27/S28/S29–S35 + Decree 532 fines |
| `dashboard/flagged.html` | 19 open items: why/settlement/source | 19 rows + 6 prohibited | Every flag links to official page |
| `dashboard/sources.html` | 35 official pages, verbatim establishment, how read | 35 rows | Every row is the official URL |
| `dashboard/archive.html` | All pages by all sessions | 82 links | Auto-discovered; no broken links |

**Mobile-friendly:** `viewport=1`, no horizontal scroll at 375px; `table.stack` CSS turns each `<tr>` into a labeled card on narrow screens; `prefers-color-scheme` friendly; no JS needed for tables (JS only for optional helpers). Tested with local `python3 -m http.server`.

**Analysis & findings on the site:** The hero + "Where the money came from" table (U01) + Tax page + Flagged page together ARE the analysis; `research/` holds the full audit pack.

---

## 9. Parallel sessions — coordination (this session's work)

**Before work:** Read `COORDINATION.md` (1319 lines at `6750ddb`), ran `git ls-remote` + `git branch -a` — found live branches `arena/1c55025d-china3` (this), `arena/76e3e41f-china3` (just merged as `d9763dc`), `arena/5f1925df-china3` (m5f19), and merged `arena/b8720152-china3`. Wrote claim block R1–R8 (`COORDINATION.md` session `arena/1c55025d-china3`, 8 tasks, status in progress) and **pushed immediately** before touching any content file, per board rule. Scopes non-overlapping: this session touches only `COORDINATION.md`, `research/1c55025d-audit.md`, `REPO_AUDIT.md` addendum, and generated files via `scripts/e347_build.py` (which this time produced 15 files, 0 changed — no sibling files edited).

**During work:** Small commits; `git pull --rebase` before every push. Merge conflict at `d9763dc` (76E merge-resolution block vs our claim block): both sides kept verbatim, markers removed, no content discarded (logged). Generated files not hand-edited (per D646-IR-003); `dashboard/archive.html` counted via generator, not hand change.

**After work:** This audit, `REPO_AUDIT.md` addendum, and `COORDINATION.md` R1–R8 marked `done` (below) were committed. Shared outputs (`index.html`, `dashboard/*`, `data/*`) unchanged this pass because the figures were not repriced (U15 documents the newer board). Final integrator will merge additive links only.

**Handoff rule respected:** No claim older than 60 min without commits was taken over; 76e's claim-fix of `verify_m5f19_site.py` check J was kept as-is (this session did not edit that verifier).

---

## 10. Pull request, merge, Pages deploy — publication record (to be filled at merge)

| Item | Value |
|---|---|
| Branch for this audit | `arena/1c55025d-china3` |
| PR | (to be opened by this session: `arena/1c55025d-china3` → `main`) |
| Checks required before merge | `e347-verify`, `c3x-verify`, `d646-verify`, `s775-verify`, `s436-verify`, `deep-research-verify`, `final-integration`, `m5f19-verify`, `pages build` — all green; deploy checks only on `main` |
| Merge command | `gh pr merge <num> --merge` (no waiting for approval; no --auto) |
| Pages deploy verification | `gh api repos/sassnarep3-star/China3/pages` → status `built` + fetch homepage with cache-buster |
| Board record | `COORDINATION.md` R8 entry with PR link, merge commit, Actions run ID, Pages URL |

*This session will open the PR, confirm all verification checks are green, merge, confirm `gh api repos/sassnarep3-star/China3/pages` reports `built`, fetch `https://sassnarep3-star.github.io/China3/?v=<merge-sha>` to confirm the kpi cards, and write the PR link + merge result back to `COORDINATION.md`. Flagged items (U01–U19) are published on `dashboard/flagged.html` and do not block the merge.*

---

## 11. Irregularities & flagged items for review (non-blocking)

| Flag | Severity | What it is | Link for manual review |
|---|---|---|---|
| F01/B8720152 | low | Board is one day old; 2026/11/10 board used, 2026/11/11 board (666.30/669.11/671.91) not repriced; Middle column ≠ midpoint | S01 https://www.boc.cn/sourcedb/whpj/enindex_1619.html |
| F02/76E | low | Six headline totals differ across layers ($53.38 vs $53.42 etc.) by construction (wire-count assumption) — both shown and labelled | `dashboard/costs.html` vs `c5bf-rates.html` |
| F03/U10 | medium | 境内个人 two definitions (Reg Art.52 vs PBOC Art.28 by ID) — bank decides | S17 https://www.safe.gov.cn/safe/2008/0806/5321.html + S18 http://m.safe.gov.cn/safe/2006/1225/5319.html |
| F04/U11 | low | 9 sources as search excerpts, quoted sentences exact, surrounding context not reviewed | S08,S15,S18,S22,S23,S24,S26,S33,S34 |
| F05/U15 | low | One snapshot; multi-year rows reuse one day's rate — scenarios, not forecasts | S01 |
| F06/U04 | medium | Intermediary/receiving fees unpublished anywhere official | S02 |
| F07/S1–S5 | info | Pre-existing: gov.cn URL renumbered; §988/§5321 via govinfo mirror; crypto notice repealed; FX rules page amended; IIT two-definition issue — all disclosed | `VERIFICATION.md` § cross-checks |

Full flagged list: https://sassnarep3-star.github.io/China3/dashboard/flagged.html

---

## 12. How to reproduce

```bash
git clone https://github.com/sassnarep3-star/China3.git && cd China3
python3 scripts/e347_build.py          # 15 files, 0 changed on this tree
python3 scripts/e347_verify.py         # PASS: 440 rows, 659 rows, 380 blanks, 2139 links
python3 scripts/verify_76e.py          # PASS
python3 scripts/verify_m5f19_site.py   # PASS
python3 scripts/verify_d646_site.py    # PASS
python3 scripts/verify_s775_site.py    # PASS
python3 scripts/verify_s436_site.py    # PASS  (640 rows)
python3 scripts/verify_c3x_site.py     # PASS
python3 scripts/verify_c5bf.py         # PASS
python3 scripts/verify_final_integration.py  # PASS
python3 scripts/validate_data.py       # OK
python3 scripts/check_links.py         # OK
# Serve:
python3 -m http.server 8000
# → http://localhost:8000/index.html  (mobile: narrow the window; tables stack)
```

Every table row has a rightmost Source link to an official page; blanks link to `dashboard/flagged.html#Uxx`. No value is inferred.

