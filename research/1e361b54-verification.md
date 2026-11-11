# 1e361b54 verification log — fresh official-source re-read, 2026-11-11

Session: `arena/1e361b54-china3` (final integration). Task FIN-T2.
Method: every load-bearing figure the published dashboard prints was re-read at its
official primary source today. Each verdict is CONFIRMED / CHANGED / UNREACHABLE.
Nothing is overwritten; this file and `data/1e361b54_source_recheck.csv` record only.

All fetches succeeded (HTTP 200) on 2026-11-11 ~02:50–03:00Z.

| ID | Claim on the published site | Official source (fetched) | Verbatim found today | Verdict |
|----|---------------------------|---------------------------|----------------------|---------|
| V1 | BOC USD selling rate 6.6851 (RMB per USD) used for every figure; board snapshot 2026/11/10 17:39:58 | BOC Exchange Rate board, USD row | "USD | 666.3 | 666.3 | 669.11 | 669.11 | 671.91 | 2026/11/11 10:25:02" — the live board today reads buying 666.30 / selling 669.11 (per 100). The site's 6.6851 (668.51 per 100) is the 2026/11/10 17:39:58 snapshot and is NOT repriced. | CONFIRMED (snapshot valid; rate drift +0.09% recorded, not repricing — see flag U15) |
| V2 | BOC personal cross-border wire fee 1‰ (min RMB 50, max RMB 260) + telegraph RMB 150 (non-HK/MO/TW) | BOC e-banking personal transfer tariff | "跨境汇款（电汇）每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,港澳台地区人民币80元/笔,非港澳台地区人民币150元/笔。" | CONFIRMED |
| V3 | IRS yearly average CNY/USD: 2024 = 7.189, 2025 = 7.129 (used for the §988 currency-gain column) | IRS yearly average currency exchange rates | "China | Yuan | 7.129 | 7.189 | 7.075 | 6.730 | 6.452" (columns 2025, 2024, 2023, 2022, 2021) | CONFIRMED |
| V4 | FBAR civil penalty: non-willful USD 16,536; willful USD 165,353 (31 CFR 1010.821, penalties assessed on/after 2025-01-17) | eCFR 31 CFR 1010.821 Table 1 | "31 U.S.C. 5321(a)(5)(B)(i) … Non-Willful … $10,000 → $16,536" and "31 U.S.C. 5321(a)(5)(C)(i)(I) … Willful … $100,000 → $165,353". Title 31 up to date as of 11/09/2026, last amended 11/06/2026. | CONFIRMED |
| V5 | 境外个人 (foreign individual / U.S. citizen) buys FX with valid ID + source-of-funds documents including tax certificates; the annual USD 50,000 convenience amount applies only to holders of a Foreign Permanent Resident ID (汇发〔2020〕14号 art. 59) | SAFE Tianjin 2024 Q&A No. 9 | "根据…汇发〔2020〕14号第五十九条，境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇。持有外国人永久居留身份证的境外个人适用购汇年度便利化额度。" | CONFIRMED |

## Notes

- **Rate drift (flag U15).** The live BOC board moved from selling 668.51 (2026/11/10 17:39:58) to 669.11 (2026/11/11 10:25:02), +0.09%. The published figures are a dated snapshot and are deliberately NOT repriced; this matches the U15 flag text and PR #48's stated intent (its U15 refresh is accurate). Repricing would require a fresh dated board reading and a rebuild of every page — out of scope for this integration pass.
- **§988 gain arithmetic re-check.** With the confirmed IRS 2024 average 7.189 (RMB/USD) and the site's BOC selling rate 6.6851 (RMB/USD), the §988 gain on $400,000 = 400000 × (1 − 6.6851/7.189) = 400000 × 0.070093 = $28,037, i.e. 7.0093% — exactly the figure printed on `dashboard/tax.html#T10` and the landing page. ✓
- **No figure changed.** This pass only re-reads. The integration edits (FIN-T3/T4) change navigation/discoverability, not any number.
