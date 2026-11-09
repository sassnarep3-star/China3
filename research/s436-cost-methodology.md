# Official-Source Cost Estimation Methodology ($10,000 to $400,000 USD in $10,000 Increments)

**Session:** `session-43606a6b` (`arena/43606a6b-china3`) · **Verified Date:** `2026-11-09` (UTC)

---

## 1. Strict No-Hallucination Cost Rule

To satisfy **both** requirements in the brief without contradiction:
1. *"Need to estimate the costs of transferring and converting cny to usd in $10000 USD increments all the way up to $400000 USD ... Actually estimate the costs for every method and tell me exactly step by step how it would work."*
2. *"Verify line by line. Every table row must have a source link to an official site. If a value can't be confirmed from an official source, leave it blank and flag it as unverified. Never infer or fill in values."*

Every cost figure in `data/s436_cost_schedule.csv` and [`schedule-cost-10k-400k.html`](../schedule-cost-10k-400k.html) is computed **exclusively from fetched, timestamped official primary tariffs and statutory schedules**, while every unquoted commercial or fact-dependent variable is **explicitly left blank (`""`)** and flagged **`UNVERIFIED`** with a link to [`schedule-flagged-review.html`](../schedule-flagged-review.html).

---

## 2. Verified Official Tariff & Rate Inputs (All Fetched `2026-11-09`)

| Input Symbol | Exact Value Used | Official Authority & Document | Verified URL |
|---|---|---|---|
| $R_{\text{ask}}$ | **`6.6924` CNY/USD** (`669.24` / 100 USD) | Bank of China Official FX Board — USD Spot Selling Rate (`现汇卖出价`) & Cash Selling Rate (`现钞卖出价`), `2026/11/09 09:29:12` | https://www.boc.cn/sourcedb/whpj/enindex_1619.html |
| $R_{\text{bid}}$ | **`6.6643` CNY/USD** (`666.43` / 100 USD) | Bank of China Official FX Board — USD Spot Buying Rate (`现汇买入价`), `2026/11/09 09:29:12` | https://www.boc.cn/sourcedb/whpj/enindex_1619.html |
| $R_{\text{mid,BOC}}$ | **`6.67835` CNY/USD** | Arithmetic midpoint `(6.6643 + 6.6924) / 2` of simultaneous BOC USD Spot Bid & Ask (`2026/11/09 09:29:12`); one-way half-spread = `0.01405` CNY/USD (`0.2100%` of CNY paid = `$20.994` per `$10,000 USD`) | https://www.boc.cn/sourcedb/whpj/enindex_1619.html |
| $R_{\text{parity}}$ | **`6.7188` CNY/USD** (`671.88` / 100 USD) | Bank of China Official FX Board — Middle Rate (`中行折算价` / CFETS parity reference), `2026/11/09 09:29:12` (used for PRC statutory RMB criminal thresholds under `法释〔2019〕1号` Art. 11) | https://www.boc.cn/sourcedb/whpj/enindex_1619.html |
| $R_{\text{Fed}}$ | **`6.6538` CNY/USD** (`2026-10-30`) | Federal Reserve Board H.10 Weekly Release (`2026-11-02`), certified NY Fed noon buying rate | https://www.federalreserve.gov/releases/h10/current/ |
| $F_{\text{wire,pers}}(C)$ | **`min(260, max(50, 0.001 × C))` RMB/wire** | Bank of China Personal E-Banking Outward Remittance Commission (`1‰`, min `¥50`, max `¥260`) | https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html |
| $F_{\text{wire,corp}}(C)$ | **`min(1000, max(50, 0.001 × C))` RMB/wire** | Bank of China Corporate Outward TT Commission (`1‰`, min `¥50`, max `¥1,000`) | https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html |
| $F_{\text{cable}}$ | **`150` RMB/wire** (to USA); **`80` RMB/wire** (to HK) | Bank of China Outward Remittance Cable Fee (`电讯费`) | https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html |
| $F_{\text{OUR}}$ | **`$25.00` USD/wire** (standard U.S. bank); **`$15.00` USD/wire** (BOC NY) | Bank of China Official Settlement Notice Note 2 (`全额到账` fixed surcharge covering intermediary deductions for U.S. USD wires `< $100M`) | https://www.boc.cn/cbservice/bi2/201711/t20171109_10646775.html |
| $F_{\text{in,BOCUSA}}$ | **`$0.00` USD/wire** | Bank of China U.S.A. Published Incoming Wire Transfer Fee (`"no fees for incoming wire transfers"`) | https://www.bocusa.com/personal-banking/remittance-exchange |
| $F_{\text{ATM,UP}}(w)$ | **`min(112, 12 + 0.01 × w)` RMB/withdrawal** | Bank of China Cross-Border UnionPay Debit ATM Cash Withdrawal Fee (`2026-08-11` Notice, unchanged on/after `2026-11-11`) | https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html |
| $F_{\text{ATM,VM}}(u)$ | **`min(40, max(3, 0.025 × u))` USD/withdrawal** (eff. `2026-11-11`) | Bank of China Cross-Border Mastercard/Visa Debit ATM Fee (`2.5%`, min `$3`, max `$40/tx` eff. `2026-11-11`; `0.5%`, `$3–$5` prior) | https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html |
| $T_{\text{div,treaty}}$ | **`10%` of gross dividend** | U.S.–China Income Tax Treaty (1984) Art. 9(2) maximum source-country dividend withholding rate | https://www.irs.gov/pub/irs-trty/china.pdf |
| $P_{\text{PRC,admin}}$ | **`≤ 30%`** (ordinary) / **`30%–100%`** (serious) | PRC Foreign Exchange Administration Regulations (State Council Order 532) Arts. 39, 40, 44, 45 (`≤ 20%` cash carry under Art. 42) | https://www.safe.gov.cn/safe/2008/0806/5321.html |
| $P_{\text{FBAR,willful}}$ | **`max($165,353, 50% × Balance)`** | 31 CFR 1010.821 Table 1 (unchanged for 2026 per Federal Register `2026-13629` / OMB M-26-11) | https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821 |
| $P_{\text{SDOP}}$ | **`5% × Highest Balance`** | IRS Streamlined Domestic Offshore Procedures Title 26 miscellaneous offshore penalty (`0%` for Streamlined Foreign Offshore) | https://www.irs.gov/individuals/international-taxpayers/us-taxpayers-residing-in-the-united-states |
| $P_{\text{3520}}$ | **`5%/month` up to `25%` of gift `> $100,000`** | IRC §6039F(c) / IRS International Information Reporting Penalties | https://www.irs.gov/payments/international-information-reporting-penalties |

---

## 3. Exact Per-Increment Formulas ($U \in \{\$10,000, \$20,000, \dots, \$400,000\}$)

For each target gross conversion amount $U$ (40 steps):
1. **Gross CNY Principal Required at BOC Spot Selling Rate:**
   $$C(U) = U \times 6.6924 \text{ RMB}$$
2. **BOC One-Way FX Conversion Spread Cost (vs simultaneous BOC Bid-Ask Midpoint `6.67835`):**
   $$S_{\text{CNY}}(U) = U \times (6.6924 - 6.67835) = U \times 0.01405 \text{ RMB}, \qquad S_{\text{USD}}(U) = \frac{S_{\text{CNY}}(U)}{6.6924} \approx 0.0020994 \times U$$
   *(For `M07` Existing USD Spot Account, $S_{\text{USD}}(U) = \$0.00$ because no FX conversion occurs. For `M08` Offshore CNH, `M10` UnionPay POS, `M11` Card Network FX, and `M14–M16` Illegal OTC, live non-BOC FX spread is left **blank / `UNVERIFIED`**.)*
3. **Number of Required Transactions $N(U)$ and Minimum Statutory Duration:**
   - `M01`, `M02` (post-`汇发〔2014〕2号`), `M04`, `M05`, `M06`, `M07`, `M08`, `M09`: **$N = 1$ wire** (`1` execution cycle).
   - `M03` (`境内个人` `$50,000/yr` convenience quota): **$N = \lceil U / 50,000 \rceil$ annual wires** across **$N$ calendar years** (`1` yr at `$10k–$50k`, ..., `8` yrs at `$360k–$400k`), with each wire carrying `min(U_i, $50,000)`.
   - `M11` (Overseas UnionPay ATM): Daily limit `¥10,000/card/day`, annual limit `¥100,000/person/yr` (`$14,942.32/yr` at `6.6924`). Withdrawals $N_{\text{ATM}} = \lceil C(U) / 10,000 \rceil$; minimum calendar years $Y_{\text{ATM}} = \lceil C(U) / 100,000 \rceil$ (`1` yr at `$10k`, `2` yrs at `$20k`, ..., **`27` calendar years at `$400k`**!).
   - `M12` (Physical USD Cash Carry with bank `《携带证》`): Max `$10,000/trip` → **$N_{\text{trips}} = U / 10,000$ international trips** (`1` trip at `$10k` → **`40` flights at `$400k`**).
4. **Published Bank Wire + Cable + `OUR` Cost in USD:**
   $$W_{\text{USD}}(U) = \sum_{i=1}^{N} \left( \frac{F_{\text{wire}}(C_i) + F_{\text{cable}}}{6.6924} + F_{\text{OUR}} \right)$$
   where standard U.S. `OUR` = `$25.00/wire` and BOC U.S.A. incoming = `$0.00` (if receiving at another U.S. bank without `OUR`, intermediary/incoming fees are left **blank / `UNVERIFIED`**).
5. **Published All-In Verified Cost & Net USD Delivered:**
   $$\text{Cost}_{\text{verified}}(U) = S_{\text{USD}}(U) + W_{\text{USD}}(U) + T_{\text{statutory}}(U), \qquad \text{Net USD}(U) = U - \text{Cost}_{\text{verified}}(U)$$
   *(Where $T_{\text{statutory}}(U) = \$0$ for already-taxed personal principal in `M01–M04, M06, M07`, and $T_{\text{statutory}}(U) = 0.10 \times U$ PRC Treaty dividend withholding for `M09` corporate profit distribution.)*
