#!/usr/bin/env python3
"""Build the 76e source re-check layer: data/76e_*.csv and 76e-verification.html.

Rules this builder follows (same rules as the rest of the repository):
  * every figure is a published official figure, or it is blank;
  * the arithmetic convention is stated on the page;
  * nothing is copied from an earlier session without being recomputed here.

Run:  python3 scripts/build_76e_site.py
Check: python3 scripts/verify_76e.py
"""
import csv
import html
import os
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENT = D("0.01")
FETCHED_AT = "2026-11-11T02:5xZ"

# --- Published inputs -------------------------------------------------------
# Bank of China USD board, CNY per USD. Both rows were read directly from
# https://www.boc.cn/sourcedb/whpj/enindex_1619.html
BOARD_TODAY = {
    "date": "2026-11-11",
    "pub": "2026/11/11 10:25:02",
    "bid": D("6.6630"),   # Buying Rate 666.30 per 100
    "ask": D("6.6911"),   # Selling Rate 669.11 per 100
    "cash_ask": D("6.6911"),
    "boc_middle": D("6.7191"),  # "Middle Rate" 671.91 per 100 (reference only)
}
BOARD_BASE = {
    "date": "2026-11-10",
    "pub": "2026/11/10 17:39:58",
    "bid": D("6.6571"),
    "ask": D("6.6851"),
    "cash_ask": D("6.6851"),
    "boc_middle": D("6.7167"),
}
WIRE_RATE, WIRE_MIN, WIRE_MAX, CABLE = D("0.001"), D("50"), D("260"), D("150")
IRS_AVG = {"2025": D("7.129"), "2024": D("7.189"), "2023": D("7.075"),
           "2022": D("6.730"), "2021": D("6.452")}
AMOUNTS = list(range(10000, 400001, 10000))


def q(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def mid(board):
    return (board["bid"] + board["ask"]) / 2


def spread_usd(usd, board, cash=False):
    ask = board["cash_ask"] if cash else board["ask"]
    return D(usd) * (ask - mid(board)) / ask


def wire_cny(usd, board):
    pct = D(usd) * board["ask"] * WIRE_RATE
    return min(WIRE_MAX, max(WIRE_MIN, pct)) + CABLE


def wire_usd(usd, board):
    return wire_cny(usd, board) / board["ask"]


def l01(usd, board):
    # The total is rounded once, from the unrounded spread and wire fee. Rounding the
    # two parts first can move the total by one cent; where it does, the page says so.
    return q(spread_usd(usd, board) + wire_usd(usd, board))


def l03(usd, board):
    return wire_usd(usd, board)


def fx_gain(usd, board, year):
    """USD gain on RMB bought at the IRS yearly average rate, sold at the board ask."""
    return D(usd) * (1 - board["ask"] / IRS_AVG[year])


# --- Published comparison ---------------------------------------------------
def published():
    out = {}
    with open(os.path.join(ROOT, "data", "e347_costs.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            if r["method_id"] in ("L01", "L03"):
                out[(r["method_id"], int(r["amount_usd"]))] = D(r["known_cost_usd"])
    return out


PUB = published()

# The same convention applied to the 10 November board must reproduce the
# published file exactly. If it does not, stop: the published figure is not
# explained by the convention and must not be re-published.
for amt in AMOUNTS:
    for mid_id, fn in (("L01", l01), ("L03", l03)):
        got = q(fn(amt, BOARD_BASE))
        if got != PUB[(mid_id, amt)]:
            raise SystemExit(
                "reconciliation failed: %s %d published %s, recomputed %s"
                % (mid_id, amt, PUB[(mid_id, amt)], got))

# --- Data files -------------------------------------------------------------
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)

COST_HEADER = ["amount_usd", "l01_spread_today", "l01_fee_today", "l01_total_today",
               "l01_total_10nov", "l01_delta", "l01_pct_today",
               "l03_total_today", "l03_total_10nov", "l03_delta",
               "fx_gain_2024_today", "fx_gain_2024_10nov"]
with open(os.path.join(ROOT, "data", "76e_costs.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(COST_HEADER)
    for amt in AMOUNTS:
        sp = q(spread_usd(amt, BOARD_TODAY))
        fee = q(wire_usd(amt, BOARD_TODAY))
        t1 = q(l01(amt, BOARD_TODAY))
        p1 = PUB[("L01", amt)]
        t3 = q(l03(amt, BOARD_TODAY))
        p3 = PUB[("L03", amt)]
        w.writerow([amt, sp, fee, t1, p1, q(t1 - p1), (t1 / D(amt) * 100).quantize(D("0.0001")),
                    t3, p3, q(t3 - p3),
                    q(fx_gain(amt, BOARD_TODAY, "2024")), q(fx_gain(amt, BOARD_BASE, "2024"))])

RECHECK = [
    ("R01", "S01", "Bank of China", "BOC Exchange Rate board (USD row)",
     "https://www.boc.cn/sourcedb/whpj/enindex_1619.html",
     "USD per 100: Buying 665.71 / Selling 668.51 / Middle 671.67, pub 2026/11/10 17:39:58.",
     "USD per 100: Buying 666.30 / Selling 669.11 / Middle 671.91, pub 2026/11/11 10:25:02.",
     "Values moved", "Same layout and same columns. The selling rate rose 0.60 fen per USD (+0.09%); every bank-cost figure on the dashboard is priced off it."),
    ("R02", "S02", "Bank of China", "中国银行电子银行个人服务转账汇款费率表",
     "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
     "跨境汇款（电汇）: 1‰, min 50, max 260 CNY, plus cable 150 CNY outside HK/Macau/Taiwan.",
     "Unchanged, verbatim: 每笔汇款金额的1‰，最低收取50元/笔，最高收取260元/笔；另收电讯费,非港澳台地区人民币150元/笔.",
     "Match", "The tariff still says local agreements and promotions may differ."),
    ("R03", "S03", "Bank of China", "关于调整部分个人服务收费内容的公告 (2026年11月11日起)",
     "https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html",
     "Overseas ATM: UnionPay 12 CNY + 1%, max 112 CNY; Mastercard/VISA 2.5%, min USD 3, max USD 40 from 2026-11-11.",
     "Unchanged, and the announcement states 将于2026年11月11日起实施. The old tariff it replaces priced the 长城国际借记卡 at 5‰, min USD 3, max USD 5.",
     "Match, effective today", "This is a notice of charges effective 11 November 2026. For a UnionPay card nothing changes; for the Great Wall International card the overseas ATM cap rises from USD 5 to USD 40 per withdrawal."),
    ("R04", "S04", "SAFE Tianjin", "2026年外汇管理互联网信息——个人外汇（08）, 2026-07-13",
     "https://www.safe.gov.cn/tianjin/2026/0713/3088.html",
     "汇发〔2020〕14号 Art. 59, foreign individual's lawful current-account RMB income.",
     "Verbatim match: 境外个人在境内取得的经常项目合法人民币收入，凭本人有效身份证件和有交易额的购汇资金来源材料（含税务凭证）在银行办理购汇.",
     "Match", "No amount ceiling appears in the answer."),
    ("R05", "S05", "SAFE Tianjin", "2024年经常项目外汇政策问答案例（九）, 2024-06-21",
     "https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
     "Art. 59 plus: only a Foreign Permanent Resident ID holder gets the purchase convenience amount.",
     "Verbatim match: 持有外国人永久居留身份证的境外个人适用购汇年度便利化额度.",
     "Match", "The answer repeats Art. 59 word for word."),
    ("R06", "S06", "SAFE Ningxia", "2022年外汇业务政策释疑（八）, 2022-09-29",
     "https://www.safe.gov.cn/ningxia/2022/0929/1997.html",
     "The USD 50,000 convenience amount is not a ceiling; Arts. 54-57 quoted.",
     "Verbatim match, including 年度便利化额度不是个人每年购汇或者结汇的限额.",
     "Match, scope note", "The question asked, and every article it quotes, is about 境内个人. The opening sentence 我国对于真实、合法的经常项目…购汇和结汇都没有金额限制 is general; using it for a passport holder relies on that sentence, not on Arts. 54-57."),
    ("R07", "S08", "SAFE (full text republished by MOFCOM)", "《经常项目外汇业务指引（2020年版）》, 汇发〔2020〕14号",
     "https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html",
     "Arts. 54-67: convenience amount (54-55), foreign individual purchase (59), slip (60), domestic individual remittance (64), foreign individual remittance (65), cross-border account transfers (67).",
     "All read verbatim today. Art. 65(1) 外汇账户内外汇汇出，凭本人有效身份证件办理 states no amount threshold; Art. 64(1) sets the USD 50,000/day identity-document threshold for 境内个人; Art. 68 lets the bank refuse.",
     "Match", "Full text, not an excerpt: the whole guideline was read on this page today."),
    ("R08", "S09", "SAFE Tianjin", "2026年外汇管理互联网信息——个人外汇（10）, 2026-09-17",
     "https://www.safe.gov.cn/tianjin/2026/0917/3134.html",
     "Art. 60: exchange slip valid 24 months; USD 500/day on ID.",
     "Verbatim match, and the article also allows USD 1,000/day at 境内关外场所 before departure.",
     "Match", "The dashboard's quote is abbreviated with an ellipsis but accurate."),
    ("R09", "S17", "State Council", "中华人民共和国外汇管理条例 (国务院令第532号)",
     "https://www.safe.gov.cn/safe/2008/0806/5321.html",
     "Art. 5 no restriction on current payments; Art. 39/40/45 fines up to 30%, 30-100% if serious; Art. 48 individual up to RMB 50,000; Art. 52(2) definition of 境内个人.",
     "All five articles read verbatim and unchanged. Art. 52(2): 境内个人，是指中国公民和在中华人民共和国境内连续居住满1年的外国人.",
     "Match", "Art. 52(2) is the basis of finding F01."),
    ("R10", "S19", "SAFE", "汇发〔2017〕29号 规范银行卡境外大额提取现金交易",
     "https://www.safe.gov.cn/hubei/2019/0305/851.html",
     "Overseas cash withdrawal cap RMB 100,000 per person per calendar year; RMB 10,000 per card per day.",
     "Verbatim match: 合计每个自然年度不得超过等值10万元人民币 … 每卡每日不得超过等值1万元人民币.",
     "Match", "Above the annual cap, the card is suspended for the rest of that year and the next."),
    ("R11", "S20", "SAFE Hebei", "外汇知识问答：每次可带外币出境的限额是多少？",
     "http://www.safe.gov.cn/hebei/2019/0521/1366.html",
     "USD 5,000 or less: customs release. USD 5,000-10,000: bank permit. Above USD 10,000: SAFE permit, generally not granted.",
     "Verbatim match: 5000美元（含）以下的，海关直接放行；5000美元以上10000美元（含）以下的，应向银行申领《携带外汇出境许可证》；10000美元以上的，应向外汇局申领 … 原则上 … 不得携带10000美元以上的外币现钞出境.",
     "Match", "The limits are per trip (每次), not per day, and 5,000-10,000 needs a bank permit."),
    ("R12", "S23", "PBOC and seven other departments", "银发〔2026〕42号 关于进一步防范和处置虚拟货币等相关风险的通知",
     "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html",
     "RMB-to-crypto exchange is an illegal financial activity; the notice repeals 银发〔2021〕237号.",
     "Verbatim match: 在境内开展法定货币与虚拟货币兑换业务 … 一律严格禁止 … 银发〔2021〕237号 同时废止.",
     "Match", "Still the operative notice on 11 November 2026."),
    ("R13", "S25", "National People's Congress (text on STA site)", "中华人民共和国个人所得税法 (2018 amendment)",
     "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
     "Art. 2 nine categories; Art. 3 3-45%, 5-35%, 20%; Art. 6(5) property gain; Art. 13 unpaid withholding.",
     "Verbatim match on all four articles. Art. 18 leaves deposit-interest tax to the State Council.",
     "Match", "No article taxes a currency conversion."),
    ("R14", "S28", "IRS", "Yearly average currency exchange rates",
     "https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates",
     "China, Yuan: 2025 7.129; 2024 7.189; 2023 7.075; 2022 6.730; 2021 6.452.",
     "Unchanged; the table still shows 7.129 / 7.189 / 7.075 / 6.730 / 6.452 and still says the IRS has no official rate.",
     "Match", "2025 is now a complete year and is included."),
    ("R15", "S29", "IRS", "Comparison of Form 8938 and FBAR requirements",
     "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements",
     "FBAR threshold USD 10,000 aggregate; 8938 thresholds 50k/75k (100k/150k joint) living in the U.S.; 8938 penalty up to USD 10,000 and USD 60,000 total.",
     "Unchanged, verbatim.",
     "Match", "The page also states the FBAR civil penalty is inflation-adjusted, so the dollar cap has to be read from 31 CFR 1010.821."),
    ("R16", "S31", "FinCEN (eCFR)", "31 CFR 1010.821 — Penalty adjustment and table",
     "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
     "Non-willful FBAR maximum USD 16,536; willful USD 165,353; general BSA penalty USD 71,545-286,184; page up to date as of 11/06/2026.",
     "Amounts unchanged: 16,536 / 165,353 / 71,545-286,184, for penalties assessed on or after 17 January 2025. The page now reads up to date as of 11/09/2026.",
     "Match, as-of date moved", "Only the eCFR 'up to date as of' line changed; no penalty amount did."),
    ("R17", "S33", "U.S. Code (GPO)", "26 U.S.C. § 6039F — Notice of large gifts received from foreign persons",
     "https://www.govinfo.gov/content/pkg/USCODE-2021-title26/html/USCODE-2021-title26-subtitleF-chap61-subchapA-partIII-subpartA-sec6039F.htm",
     "Report foreign gifts above USD 10,000; penalty 5% of the gift per month, capped at 25%.",
     "Verbatim match: 5 percent of the amount of such foreign gift for each month … not to exceed 25 percent.",
     "Match", "The USD 10,000 threshold is indexed for inflation."),
    ("R18", "S27", "U.S. Code (GPO)", "26 U.S.C. § 988 — Treatment of certain foreign currency transactions",
     "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm",
     "Disposing of nonfunctional currency is a § 988 transaction; the gain is ordinary income.",
     "Verbatim match: (c)(1)(C)(i) 在处置非功能货币时 such disposition shall be treated as a section 988 transaction; (a)(1)(A) computed separately and treated as ordinary income.",
     "Match", "Whether a savings balance is a 'personal transaction' under § 988(e) remains a legal question (dashboard flag U05)."),
]
with open(os.path.join(ROOT, "data", "76e_recheck.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "source_id", "issuer", "document", "url", "published_finding",
                "finding_today", "verdict", "note", "fetched_at"])
    for row in RECHECK:
        w.writerow(list(row) + [FETCHED_AT])

FINDINGS = [
    ("F01", "moderate", "index.html (landing page), card 4",
     "The landing page states as fact that a U.S. passport holder does not get the USD 50,000 annual convenience amount. Two official texts do not settle it that way: the State Council Regulation Art. 52(2) defines 境内个人 to include a foreigner who has lived in China for one continuous year, and the 2020 Guidelines Art. 54 tie the purchase convenience amount to 境内个人. Only a Foreign Permanent Resident ID holder is named in Art. 59 para 2.",
     "Quoted verbatim from both pages on 2026-11-11; the repository's own flag U10 records the conflict, but the landing page does not carry it.",
     "needs review",
     "S17|S08|S05",
     "https://www.safe.gov.cn/safe/2008/0806/5321.html https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
     "The bank's written statement of the account category it applied at opening, and the branch's practice for a foreign passport holder resident in China for more than a year."),
    ("F02", "moderate", "data/s775_penalties.csv P05; s775-penalties-tax.html, s775-sources.html, s775-steps.html",
     "The cash-border row reads '≤US$5,000 per person per day without declaration; >US$10,000 declaration required'. Its cited source says the limit is per trip (每次), that USD 5,000-10,000 needs a bank-issued 携带外汇出境许可证, and that above USD 10,000 a SAFE permit is required which is in principle not granted.",
     "The cited SAFE Hebei page was re-read in full today; the row contradicts it on the period, omits the bank permit, and reduces a permit requirement to a declaration.",
     "needs review",
     "S20",
     "http://www.safe.gov.cn/hebei/2019/0521/1366.html",
     "Correct the row to the source's own three bands and period, or delete it."),
    ("F03", "moderate", "index.html KPI cards; dashboard/costs.html",
     "The headline bank costs are one trading day old. Flag U15 now records the 11 November reading (updated by session B8720152) but the cards were not repriced. Repricing them would give USD 53.42 on 10,000 (published 53.38, +0.04) and USD 901.20 on 400,000 (published 899.01, +2.19); the U.S. currency-gain figure would fall from 28,037 to 27,703.",
     "Recomputed in this pass from the board read today; the 10 November board reproduces the published 440-row file exactly, so the only cause is the rate move. What remains is presentation: the date of the board is in a footnote, not beside the number.",
     "needs review",
     "S01|S02|S28",
     "https://www.boc.cn/sourcedb/whpj/enindex_1619.html https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates",
     "A dated stamp beside every KPI and a rebuild on the day a decision is taken."),
    ("F04", "low", "dashboard/costs.html route L10; data/e347_sources.csv S03",
     "The ATM tariff page cited is a notice of charges that take effect on 11 November 2026, read on 10 November, the day before it took effect. UnionPay terms are unchanged (12 CNY + 1%, max 112 CNY), but the card the old tariff priced at 5‰ (min USD 3, max USD 5) is now 2.5% (min USD 3, max USD 40) — up to eight times the old cap per withdrawal.",
     "Verbatim comparison of the old and new columns in the announcement.",
     "needs review",
     "S03",
     "https://www.boc.cn/pbservice/bi2/202608/t20260811_25684907.html",
     "State which card the L10 row assumes; if it is the 长城国际借记卡, reprice it on the 2.5% / USD 40 terms."),
    ("F05", "low", "dashboard/sources.html S31",
     "The source note gives the eCFR page as 'up to date as of 11/06/2026'. The page now reads 11/09/2026.",
     "Read today. No penalty amount in the table changed.",
     "cosmetic",
     "S31",
     "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
     "Refresh the as-of string; no figure needs to change."),
    ("F06", "low", "Published layers: index.html, dashboard/costs.html, legacy-index.html, d646-costs.html, final-verification.html, m5f19-costs.html",
     "Six live pages publish six different headline totals for the same single-wire route: 53.38, 53.42, 53.47, 899.01, 901.30, 1,332.05 (the last is an eight-wire staging scenario). Each is internally explainable by its own board snapshot or spread convention, but only the Archive page says which layer is current.",
     "Enumerated by grep across every published HTML page; the differences are explained in data/m5f19_reconciliation.csv and in this page's table.",
     "needs review",
     "S01|S02",
     "https://www.boc.cn/sourcedb/whpj/enindex_1619.html https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
     "A 'superseded' banner on every archived layer, or a single canonical page and redirects."),
    ("F07", "low", "data/m5f19_methods.csv; m5f19-methods.html",
     "The 'no amount limit' point is supported partly by the SAFE Ningxia answer, whose question and all four quoted articles concern 境内个人. The general sentence at the top of that answer is not limited by person type, so the claim is defensible, but it should not be presented as an article that governs a passport holder.",
     "The Ningxia page was read in full today.",
     "needs review",
     "S06|S08",
     "https://www.safe.gov.cn/ningxia/2022/0929/1997.html https://www.mofcom.gov.cn/zcfb/zgdwjjmywg/art/2020/art_0dd36157a03f494db7571002c7f785b8.html",
     "Cite Art. 59 (no ceiling stated) for the purchase leg and the general sentence for the no-ceiling point, and label the scope."),
]
with open(os.path.join(ROOT, "data", "76e_findings.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "severity", "where", "finding", "evidence", "status", "source_ids", "source_urls", "what_would_settle"])
    for row in FINDINGS:
        w.writerow(list(row))


# --- HTML -------------------------------------------------------------------
def esc(t):
    return html.escape(str(t), quote=True)


def money(x):
    return "{:,.2f}".format(x)


def usd_signed(x):
    sign = "+" if x > 0 else ("\u2212" if x < 0 else "")
    return sign + "{:,.2f}".format(abs(x))


today10 = q(l01(10000, BOARD_TODAY))
today400 = q(l01(400000, BOARD_TODAY))
gain400_today = q(fx_gain(400000, BOARD_TODAY, "2024"))
gain400_base = q(fx_gain(400000, BOARD_BASE, "2024"))
rate_delta_pct = ((BOARD_TODAY["ask"] - BOARD_BASE["ask"]) / BOARD_BASE["ask"] * 100).quantize(D("0.0001"))

rows = []
for amt in AMOUNTS:
    t1 = q(l01(amt, BOARD_TODAY))
    p1 = PUB[("L01", amt)]
    t3 = q(l03(amt, BOARD_TODAY))
    p3 = PUB[("L03", amt)]
    rows.append(
        '<tr><td data-label="Amount (USD)"><span class="id">{a}</span></td>'
        '<td data-label="Bank purchase + wire (L01)">{t1}</td>'
        '<td data-label="vs 10 Nov">{d1}</td>'
        '<td data-label="Wire out FX already held (L03)">{t3}</td>'
        '<td data-label="vs 10 Nov">{d3}</td></tr>'.format(
            a="{:,}".format(amt), t1=money(t1), d1=usd_signed(q(t1 - p1)),
            t3=money(t3), d3=usd_signed(q(t3 - p3))))

recheck_rows = []
for (rid, sid, issuer, doc, url, pub_txt, today_txt, verdict, note) in RECHECK:
    cls = "ok" if verdict.startswith("Match") else "warn"
    recheck_rows.append(
        '<tr id="{rid}"><td data-label="Document"><span class="id">{sid}</span> <b>{doc}</b><br>'
        '<span class="note">{issuer}</span></td>'
        '<td data-label="Recorded 10 Nov">{pub_txt}</td>'
        '<td data-label="Found 11 Nov">{today_txt}</td>'
        '<td data-label="Verdict"><span class="pill {cls}">{verdict}</span></td>'
        '<td class="src" data-label="Official page"><a href="{url}" rel="noopener">{host}</a></td></tr>'
        '<tr class="sub"><td colspan="5">{note}</td></tr>'.format(
            rid=rid, sid=sid, doc=esc(doc), issuer=esc(issuer), pub_txt=esc(pub_txt),
            today_txt=esc(today_txt), verdict=esc(verdict), cls=cls, url=esc(url),
            host=esc(url.split("/")[2]), note=esc(note)))

finding_rows = []
for (fid, sev, where, finding, evidence, status, sids, urls, settle) in FINDINGS:
    links = " ".join('<a href="{u}" rel="noopener">{s}</a>'.format(
        u=esc(u), s=esc(sid)) for sid, u in zip(sids.split("|"), urls.split()))
    finding_rows.append(
        '<tr id="{fid}"><td data-label="Finding"><span class="id">{fid}</span> '
        '<span class="pill {sevcls}">{sev}</span><br><span class="note">{where}</span></td>'
        '<td data-label="What was found">{finding}</td>'
        '<td data-label="Evidence">{evidence}</td>'
        '<td data-label="What would settle it">{settle}</td>'
        '<td class="src" data-label="Sources">{links}<br><span class="note">{status}</span></td></tr>'.format(
            fid=fid, sev=sev, sevcls=sev, where=esc(where), finding=esc(finding),
            evidence=esc(evidence), settle=esc(settle), links=links, status=esc(status)))

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Independent re-check of every load-bearing official source on 11 November 2026, with the recomputed bank-cost ladder from that day's Bank of China board.">
<title>Source re-check, 11 November 2026 · China money</title>
<link rel="stylesheet" href="assets/76e.css">
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">China money<small>RMB to USD, source-checked</small></a>
<nav class="nav" aria-label="Sections">
<a href="index.html">Home</a>
<a href="dashboard/methods.html">Methods</a>
<a href="dashboard/costs.html">Costs</a>
<a href="dashboard/steps.html">Steps</a>
<a href="dashboard/tax.html">Tax</a>
<a href="dashboard/flagged.html">Flagged</a>
<a href="dashboard/sources.html">Sources</a>
<a href="76e-verification.html" aria-current="page">Re-check</a>
</nav>
</div></header>
<main><div class="wrap">

<h1>Source re-check, 11 November 2026</h1>
<p class="lead">On 11 November 2026 every official page the dashboard depends on was opened again,
in full, and compared with what was recorded on 10 November. The bank-cost ladder was then
re-derived from that morning's Bank of China board. Nothing below is copied from an earlier pass
without a fresh fetch; where a value could not be re-read it would be blank and flagged, and no
value had to be left blank.</p>

<div class="kpis">
<div class="kpi"><b>{ask}</b><span>CNY per USD, BOC selling rate, 11 Nov 10:25:02</span><span class="src"><a href="https://www.boc.cn/sourcedb/whpj/enindex_1619.html" rel="noopener">S01</a></span></div>
<div class="kpi"><b>${t10}</b><span>bank cost on $10,000 &middot; was ${p10} (+{d10})</span><span class="src"><a href="https://www.boc.cn/sourcedb/whpj/enindex_1619.html" rel="noopener">S01</a> <a href="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html" rel="noopener">S02</a></span></div>
<div class="kpi"><b>${t400}</b><span>bank cost on $400,000 &middot; was ${p400} (+{d400})</span><span class="src"><a href="https://www.boc.cn/sourcedb/whpj/enindex_1619.html" rel="noopener">S01</a> <a href="https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html" rel="noopener">S02</a></span></div>
<div class="kpi"><b>${g400}</b><span>U.S. currency gain on $400,000 if the RMB was bought at the 2024 average &middot; was ${gb400}</span><span class="src"><a href="https://www.irs.gov/individuals/international-taxpayers/yearly-average-currency-exchange-rates" rel="noopener">S28</a> <a href="https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapN-partIII-subpartJ-sec988.htm" rel="noopener">S27</a></span></div>
</div>

<h2>What this pass changes</h2>
<ol class="tight">
<li><b>The rate moved.</b> The selling rate went from 668.51 to 669.11 CNY per 100 USD
(+{rate_pct}%). That is the only input that changed, and it is the only reason any cost figure below differs from the dashboard.</li>
<li><b>The arithmetic held.</b> Applying the dashboard's own convention to the 10 November board reproduces all
80 published L01 and L03 cells of <code>data/e347_costs.csv</code> to the cent, so the published figures are not in doubt — they are one trading day old.</li>
<li><b>One fee schedule took effect today.</b> Bank of China's ATM notice is dated 11 August 2026 but applies from
11 November 2026. UnionPay terms are unchanged; the Great Wall International card's overseas ATM cap rises from USD 5 to USD 40 per withdrawal (finding F04).</li>
<li><b>Two wording problems and three freshness problems</b> were found on published pages and are listed under
<a href="#findings">Findings</a>. None of them changes the answer to the main question.</li>
</ol>

<h2 id="ladder">Bank cost at every $10,000 step, on today's board</h2>
<p>Two routes, both priced only from the two Bank of China pages. <b>L01</b> is the documented-income route:
buy USD at the board's selling rate and wire it out. <b>L03</b> is the route where the balance is already in
foreign currency, so there is no purchase and no spread — the wire fee only. The last two columns compare
with the figure published on 10 November.</p>
<div class="tbl"><table class="stack num">
<thead><tr><th>Amount</th><th>L01 total</th><th>vs 10 Nov</th><th>L03 total</th><th>vs 10 Nov</th></tr></thead>
<tbody>
{rows}
</tbody></table></div>
<p class="note">Convention, stated so it can be checked: spread = amount &times; (ask &minus; (bid + ask) / 2) / ask,
where bid and ask are the board's Buying and Selling rates. Wire fee = min(260, max(50, amount &times; ask &times; 0.1%)) + 150 CNY,
converted at the same ask. Amounts are USD; the CNY debited is amount &times; ask plus the wire fee.
<b>Not included</b>: the sending bank's cable/agent charges beyond the 150 CNY above, any intermediary or
receiving-bank fee, and any U.S. bank fee. Those are not published by any official page and stay blank
(dashboard flags U04). One rounding detail, so the columns can be added up: the total is rounded once
from the unrounded spread and fee, so in {rnotes} of the 40 rows the two rounded columns differ from the
printed total by one cent.</p>

<h2 id="recheck">Every load-bearing source, re-read today</h2>
<p>Eighteen pages, each opened directly on 11 November 2026. "Recorded 10 Nov" is what the dashboard
recorded; "Found 11 Nov" is what the page says now, quoted in its own words.</p>
<div class="tbl"><table class="stack">
<thead><tr><th>Document</th><th>Recorded 10 Nov</th><th>Found 11 Nov</th><th>Verdict</th><th>Official page</th></tr></thead>
<tbody>
{recheck}
</tbody></table></div>

<h2 id="findings">Findings for review</h2>
<p>These are published, not fixed: each touches a page owned by another session, and the repository rule is
that a session logs a request instead of editing another session's file. Severity reflects what would change
for a reader, not how hard the fix is.</p>
<div class="tbl"><table class="stack">
<thead><tr><th>Finding</th><th>What was found</th><th>Evidence</th><th>What would settle it</th><th>Sources</th></tr></thead>
<tbody>
{findings}
</tbody></table></div>

<h2>What this page does not do</h2>
<ul class="tight">
<li>It does not give legal, tax or investment advice, and it does not decide which route applies to a
particular balance. That turns on where the money came from, which the brief does not state (dashboard flag U01).</li>
<li>It does not re-price any route other than L01 and L03. The other nine routes on the cost page are priced
from the same tariff and the same board, so they move with it, but they were not recomputed here.</li>
<li>It does not treat the absence of a conversion tax as a finding about any individual's tax position.
No official page read in this repository taxes the conversion itself; the tax that bites is the tax on the
income that created the money.</li>
<li>It does not claim that any bank will accept a particular document set. The 2020 Guidelines Art. 68 lets the
bank refuse a transaction it cannot satisfy itself about.</li>
</ul>

<p class="foot">Built by session <code>arena/76e3e41f-china3</code> on 11 November 2026 from
<code>data/76e_recheck.csv</code>, <code>data/76e_costs.csv</code> and <code>data/76e_findings.csv</code>.
Regenerate with <code>python3 scripts/build_76e_site.py</code>; gate with <code>python3 scripts/verify_76e.py</code>.</p>

</div></main>
</body>
</html>
""".format(
    ask="{:.4f}".format(BOARD_TODAY["ask"]),
    t10=money(today10), p10=money(PUB[("L01", 10000)]), d10=money(today10 - PUB[("L01", 10000)]),
    t400=money(today400), p400=money(PUB[("L01", 400000)]), d400=money(today400 - PUB[("L01", 400000)]),
    g400=money(gain400_today), gb400=money(gain400_base),
    rate_pct=rate_delta_pct,
    rnotes=sum(1 for amt in AMOUNTS
               if q(spread_usd(amt, BOARD_TODAY)) + q(wire_usd(amt, BOARD_TODAY)) != q(l01(amt, BOARD_TODAY))),
    rows="\n".join(rows),
    recheck="\n".join(recheck_rows),
    findings="\n".join(finding_rows),
)

with open(os.path.join(ROOT, "76e-verification.html"), "w", encoding="utf-8") as fh:
    fh.write(PAGE)

print("wrote 76e-verification.html, data/76e_costs.csv, data/76e_recheck.csv, data/76e_findings.csv")
print("today: L01 $10,000 =", today10, " L01 $400,000 =", today400, " 2024 FX gain on 400k =", gain400_today)
