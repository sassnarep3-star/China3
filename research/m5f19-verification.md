# M5F19 — Verification log

Session `5f1925df` · namespace `m5f19` · all fetching performed **2026-11-10**.

This log records what was actually read, from where, on what date. It exists so
that any figure on the m5f19 pages can be traced to a passage that was fetched,
rather than to a memory or to another session's summary.

**Rule applied throughout:** every value on a page is either (a) quoted from a
document fetched on the date above, or (b) left *blank* and flagged
`unverified`. Nothing is inferred, interpolated, or carried forward from an
earlier layer of this repository without being re-read.

---

## 1. Documents fetched and read in full

| # | Document | Instrument | URL | What was read |
|---|---|---|---|---|
| S01 | BOC published FX board | live rate board | <https://www.boc.cn/sourcedb/whpj/> | USD row at the 2026-11-10 17:39:58 reading, plus the page's own reference-only declaration |
| S02 | BOC personal e-banking transfer tariff | published bank tariff | <https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html> | 跨境汇款（电汇） row and both 备注 notes |
| S03 | 中华人民共和国外汇管理条例 | State Council Order No. 532 | <https://www.safe.gov.cn/safe/2008/0806/5321.html> | Articles 1–54, all chapters |
| S04 | 个人外汇管理办法 | PBOC Order [2006] No. 3 | <https://www.gov.cn/zhengce/2006-11/30/content_5712728.htm> | Articles 1–42 plus the schedule of repealed rules |
| S05 | 经常项目外汇业务指引（2020年版） | 汇发〔2020〕14号 | <https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html> | Chapter 3 (Arts. 54–79) in full; also Arts. 47, 49, 86–94 |
| S06 | 2024 经常项目外汇政策问答案例（九） | SAFE Tianjin branch Q&A | <https://www.safe.gov.cn/tianjin/2024/0621/2529.html> | The Art. 59 answer on overseas individuals |
| S07 | 2024 个人外汇（三） | SAFE Tianjin branch Q&A | <https://www.safe.gov.cn/tianjin/2024/0229/2402.html> | The Art. 64 answer — and its question, which is about **domestic** individuals |
| S08 | 2026 个人外汇（08） | SAFE Tianjin branch Q&A | <https://www.safe.gov.cn/tianjin/2026/0713/3088.html> | The most recent restatement of Art. 59 |
| S09 | 2022 外汇业务政策释疑（八） | SAFE Ningxia branch Q&A | <https://www.safe.gov.cn/ningxia/2022/0929/1997.html> | The answer establishing that USD 50,000 is not a cap |
| S10 | 进一步改进和调整资本项目外汇管理政策的通知 | 汇发〔2014〕2号 | <https://www.safe.gov.cn/tianjin/2024/0903/2594.html> | Sections 5 and 6, and the printed amendment note |
| S11 | 中华人民共和国个人所得税法 | national law, 7th amendment | <https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html> | Articles 1–22 |
| S12 | 26 U.S.C. §988 | statute, GPO 2023 edition | <https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm> | Whole section including subsection (e) and the amendment notes |
| S13 | 31 U.S.C. §5321 | statute, GPO 2023 edition | <https://www.govinfo.gov/content/pkg/USCODE-2023-title31/html/USCODE-2023-title31-subtitleIV-chap53-subchapII-sec5321.htm> | §5321(a)(1)–(a)(7), (b), (d), (f), (g) |
| S14 | 31 CFR 1010.821 | regulation, eCFR | <https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821> | Whole section and the Table 1 penalty rows |
| S15 | Report of Foreign Bank and Financial Accounts (FBAR) | IRS guidance | <https://www.irs.gov/businesses/small-businesses-self-employed/report-of-foreign-bank-and-financial-accounts-fbar> | Who must file, when, how, recordkeeping, penalties |
| S16 | IR-2025-103, TY2026 inflation adjustments | IRS news release | <https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill> | FEIE, gift exclusions, standard deduction, rate schedules |
| S17 | Revenue Procedure 2025-32 | revenue procedure | <https://www.irs.gov/pub/irs-drop/rp-25-32.pdf> | Cited by S16 as the authoritative instrument; the PDF was **not** separately re-read, and the figures used come from the S16 release text |

Machine-readable register: `data/m5f19_sources.csv`.
Verbatim passages relied on (52): `data/m5f19_facts.csv`.

---

## 2. Sources tested and rejected

| URL | Result | Disposition |
|---|---|---|
| `https://www.irs.gov/individuals/international-taxpayers/fbar-reference-page` | HTTP 404 | Discarded. The path was constructed rather than found. Replaced by S15, which was fetched successfully. Recorded here so the failure is visible rather than silent. |
| Two `routify-file-proxy` object-store URLs | `SignatureDoesNotMatch` | Discarded. These are short-lived signed proxy artefacts returned by the fetch tool, not canonical sources. Every citation in this edition is a canonical publisher URL that was re-fetched directly. |

---

## 3. Values deliberately left blank

Per the brief, a value that cannot be confirmed from an official source is left
empty and flagged — never estimated. Machine-readable: rows T22–T27 of
`data/m5f19_tax.csv`, and `BLANK_CELLS` in `scripts/build_m5f19_site.py`.

| Item | Why blank | What would close it |
|---|---|---|
| Executable bank spread | The published board is expressly reference-only and BOC disclaims results based on it | A written quotation from the executing bank |
| Intermediary and beneficiary bank charges | No official source reviewed publishes them for a personal CNY→USD wire | A written quotation naming the charge option and correspondent chain |
| Offshore CNY/CNH basis | No official source reviewed publishes a current basis | A live market source at execution time |
| Form 8938 threshold | Not fetched this session; earlier layers carry figures this edition did not read today | Fetch the IRS comparison page and the Form 8938 instructions |
| U.S.–China income tax treaty relief | The treaty text was not fetched, so no article or rate is asserted | Fetch the treaty and read the relevant article |
| State-level tax on a §988 gain | Depends on the state of residence, which was not supplied | The taxpayer's state of residence |
| The user's subject category | No account documents or residence history supplied, and two official definitions conflict | Written confirmation from the account-opening bank |
| PRC tax on the underlying income | No amount, source-of-funds history or tax filings supplied | The income's category under IIT Law Art. 2 and status under Art. 1 |

---

## 4. Cost model — inputs, convention and the double-count fix

### Inputs (all from S01 and S02, read 2026-11-10)

| Quantity | Value | Source |
|---|---|---|
| USD ask (现汇卖出价) | 6.6851 CNY per USD | S01, board reading 17:39:58 |
| USD bid (现汇买入价) | 6.6571 CNY per USD | S01 |
| BOC conversion rate (中行折算价) | 6.7167 CNY per USD | S01 |
| Midpoint | 6.6711 CNY per USD | derived, (ask+bid)/2 |
| Wire fee | 1‰ of the remittance amount | S02 |
| Wire fee floor | CNY 50 per transaction | S02 |
| Wire fee ceiling | CNY 260 per transaction | S02 |
| Telecom charge, non-HMT | CNY 150 per transaction | S02 |
| Telecom charge, HMT | CNY 80 per transaction | S02 |

Recorded in `data/m5f19_board.csv` so the ladder is reproducible against a
specific board reading.

### Convention

For a transfer of USD `X`:

```
CNY spent          = X × ask
spread (CNY)       = X × (ask − mid)
spread_pct_ask     = (ask − mid) / ask     = 0.209421 %
spread_pct_mid     = (ask − mid) / mid     = 0.209860 %
wire_fee_cny       = min(260, max(50, 0.001 × CNY spent))
total_known_usd    = spread/ask + (wire_fee_cny + 150)/ask
```

**The spread is an opportunity cost borne in the CNY spent. It is not deducted a
second time from the USD delivered.** Buying USD `X` at the ask delivers USD `X`.
This is the defect sessions a502 and a058 both flagged in earlier layers, where
`66,903 / 6.6903 = 10,000` exactly and a figure of `9,946.58` was nonetheless
labelled "net". The m5f19 model cannot reproduce that error because the USD
delivered is never reduced by the spread.

Both denominators are published side by side and never mixed in one column. The
denominator convention is printed on `m5f19-costs.html`.

### Derived thresholds

| Threshold | Value | Derivation |
|---|---|---|
| CNY 260 fee ceiling binds above | ≈ USD 38,892 of transfer | 260 / 0.001 / 6.6851 |
| CNY 50 fee floor binds below | ≈ USD 7,479 of transfer | 50 / 0.001 / 6.6851 |
| Fee ceiling in USD | USD 38.89 | 260 / 6.6851 |
| Telecom charge in USD | USD 22.44 | 150 / 6.6851 |

Both fee readings — 1‰ of the USD amount, and 1‰ of the CNY amount converted
back at the same ask — are computed and asserted equal at every increment, so
the convention cannot silently drift (`fee_usd` vs `fee_usd_via_cny` in
`scripts/m5f19_engine.py`).

---

## 5. Reconciliation gate

Five headline figures published by earlier sessions were re-derived from first
principles using the board reading each session recorded. **All five reproduce to
the cent.**

| Model | Session | Board ask/bid | Wires | Denominator | Amount | Published | Re-derived |
|---|---|---|---|---|---|---|---|
| 1 wire | fbbd3b22 (PR #24/#27) | 6.6903 / 6.6622 | 1 | ask | 10,000 | 53.42 | **53.42** ✓ |
| 1 wire | fbbd3b22 (PR #24/#27) | 6.6903 / 6.6622 | 1 | ask | 400,000 | 901.30 | **901.30** ✓ |
| 1 wire | d6467425 (PR #26) | 6.6903 / 6.6622 | 1 | mid | 10,000 | 53.47 | **53.47** ✓ |
| 8 wires | d6467425 (PR #26) | 6.6903 / 6.6622 | 8 | mid | 400,000 | 1332.05 | **1332.05** ✓ |
| 1 wire | 775c9619 (PR #33) | 6.6903 / 6.6622 | 1 | ask | 10,000 | 53.42 | **53.42** ✓ |

This settles a dispute that had been logged as a "convention difference" without
ever being demonstrated. There is **no data error** in any of those builds. The
divergence has exactly three causes:

1. **The board moved during the day.** Those sessions read ask 6.6903 at 07:32:39;
   this session read ask 6.6851 at 17:39:58, the same date. Identical code run at
   a different hour yields different dollars. This is a property of the source.
2. **Two spread denominators.** On the legacy board, `(ask−mid)/ask = 0.210005%`
   and `(ask−mid)/mid = 0.210446%`. That 0.00044-point gap *is* the USD 0.05
   difference between 53.42 and 53.47 at USD 10,000.
3. **A wire count.** The USD 400,000 gap between 901.30 and 1,332.05 is not a rate
   difference. The spread is proportional and does not change; the CNY 260 fee
   ceiling and the flat CNY 150 telecom charge are *per transaction*, so eight
   wires pay the fixed element eight times.

Machine-readable: `data/m5f19_reconciliation.csv`. Enforced by
`check_G_reconciliation` in `scripts/verify_m5f19_site.py`, which fails the build
if any legacy figure stops reproducing exactly.

---

## 6. Engine self-checks

`scripts/m5f19_engine.py::self_checks()` runs on every build and in CI:

1. Fee-convention independence at all 40 increments.
2. The CNY 260 ceiling binds at and above USD 40,000; the fee at USD 10,000 is
   exactly USD 10.00.
3. The half-spread is strictly positive and strictly less than the full bid/ask
   spread.
4. Total cost is strictly monotonic in the transfer amount for a fixed wire count.
5. All-in percentage falls with size (the ceiling bites).
6. Eight wires cost strictly more than one wire at every increment.
7. Both historical models reproduce to the cent (see §5).

---

## 7. Site verification

`scripts/verify_m5f19_site.py` — 10 checks, exit non-zero on any failure:

| Check | What it enforces |
|---|---|
| A | 9 pages exist, parse, have unique `<title>`, declare charset and viewport, contain **zero nested `<td>`**, link the namespaced stylesheet, and use no un-namespaced `id` that could collide with a sibling page |
| B | Every internal `href` resolves to a file that exists |
| C | Every external `href` is on the whitelist of sources fetched today — a URL that was not read cannot be cited |
| D | All **238 data rows across 16 tables** carry an official-source link or a BLANK/UNVERIFIED marker. Header rows are excluded. No exemptions. |
| E | No cell marked `unverified` contains a value — an unconfirmable value must be literally empty, with the explanation in an adjacent column |
| F | Every cost figure printed in the HTML re-derives from the recorded board; all 160 ladder rows checked across 4 components; the 40 primary totals must appear on the page |
| G | The reconciliation gate of §5 |
| H | The ladder covers USD 10,000–400,000 in 10,000 steps with no gaps, 40 increments × 4 scenarios = 160 rows |
| I | The engine self-checks of §6 |
| J | No file outside this session's claim was modified, checked against `git diff` versus the merge base |
| K | Rebuilding produces byte-identical output for all 11 generated files |

### Defects this verifier was written to exclude

Each of these exists somewhere in the repository today. None may appear on an
m5f19 page.

| Known defect | Where it exists | How it is blocked |
|---|---|---|
| Nested `<td>` elements | `s775-cost-10k-400k.html` | check A counts `td` depth and fails on any nesting |
| A headline card disagreeing with its own table ($50.93 vs $53.42) | `docs/index.html` | check F derives both from the same engine call |
| Two spread denominators mixed on one page | earlier cost tables | the ladder stores `denominator` per row; check F re-derives each row with its own |
| Cost rows with no per-row source link | earlier cost tables | check D, no exemptions |
| `check_links.py` passing while proving nothing about truth | repo-wide | checks C, F and G test provenance and arithmetic, not just link resolution |

---

## 8. No regression

All ten inherited validators, plus the audit script merged in PR #36, were run at
the m5f19 tip and all pass:

`validate_data` · `check_links` · `verify_deep` · `test_costs` ·
`verify_cost_tables` · `verify_s436_site` · `verify_d646_site` ·
`verify_dashboard` · `verify_s775_site` · `verify_final_integration` ·
`a502_audit`

No validator was edited. `scripts/verify_m5f19_site.py` runs alongside them.
