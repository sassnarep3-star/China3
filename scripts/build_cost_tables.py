#!/usr/bin/env python3
"""Build the cost tables: CSVs + cost-tables.html.

Deterministic: no timestamps, no network. Run it, then run verify_cost_tables.py.
"""
from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

import cost_engine as E  # noqa: E402

# --------------------------------------------------------------------------
# Source register for this pass. `rechecked` records, honestly, whether the
# URL was fetched again during this session or only inherited from an
# earlier session's register.
# --------------------------------------------------------------------------
SOURCES = [
    ("CS01", "Bank of China — 外汇牌价 (official daily FX board)", "https://www.boc.cn/sourcedb/whpj/",
     "yes", "Read 2026-11-09 09:15:45: USD 现汇买入价 666.38, 现汇卖出价 669.19, per 100 USD."),
    ("CS03", "U.S. Customs and Border Protection — Money and Other Monetary Instruments",
     "https://www.cbp.gov/travel/international-visitors/money-monetary-instruments",
     "yes", "FinCEN Form 105 above USD 10,000, group total, seizure and 31 U.S.C. 5321/5322 exposure."),
    ("CS04", "PBOC Announcement [2004] No. 16 — 个人财产对外转移售付汇管理暂行办法 (SAFE text)",
     "http://m.safe.gov.cn/safe/2004/1116/5461.html",
     "yes", "Full text read: arts. 2, 6, 8, 10, 11, 13."),
    ("CS05", "State Council Gazette 2005 No. 22 — same measure (independent official copy)",
     "https://www.gov.cn/gongbao/content/2005/content_64294.htm",
     "yes", "Used to cross-check arts. 6 and 10 of CS04; wording agrees."),
    ("S01", "SAFE Ningxia — 2022 外汇业务政策释疑（八）", "https://www.safe.gov.cn/ningxia/2022/0929/1997.html",
     "yes", "USD 50,000 convenience amount is not a ceiling and not a tax; arts. 54–57 of the 2020 current-account guidelines."),
    ("S03", "SAFE Tianjin — 2024 经常项目外汇政策问答案例（九）", "https://www.safe.gov.cn/tianjin/2024/0621/2529.html",
     "yes", "境外个人 buys FX with ID plus source-of-funds evidence including tax evidence; the annual convenience amount applies to 境外个人 holding a foreigner permanent-residence ID."),
    ("S04", "SAFE Tianjin — 个人外汇管理办法实施细则", "https://www.safe.gov.cn/tianjin/2024/0430/2464.html",
     "no", "Inherited from the earlier register; not re-fetched in this pass."),
    ("S07", "State Council Order No. 532 — 中华人民共和国外汇管理条例", "https://www.safe.gov.cn/safe/2008/0806/5321.html",
     "yes", "Arts. 12, 39, 40, 42, 44, 45 and the art. 52 definitions read in full."),
    ("S09", "SAFE — 个人购汇申请书及填报说明（六不得）", "https://www.safe.gov.cn/safe/file/file/20210402/30fab7a9646f417ca9d2f67ff4c1e5f0.pdf",
     "no", "Inherited; not re-fetched."),
    ("S11", "SAFE Tianjin — 2025 个人外汇（八）关注名单", "https://www.safe.gov.cn/tianjin/2025/0613/2811.html",
     "no", "Inherited; not re-fetched."),
    ("S14", "SAFE Hebei — 七起个人分拆结售汇案", "https://www.safe.gov.cn/hebei/2016/0328/615.html",
     "no", "Inherited; not re-fetched."),
    ("S18", "SAFE — 就《个人财产对外转移售付汇管理暂行办法》答记者问", "http://m.safe.gov.cn/safe/2004/1116/4134.html",
     "yes", "Confirms the RMB 500,000 approval split and the RMB 200,000 one-payment threshold."),
    ("S19", "SAFE — 汇发〔2017〕3号", "https://www.safe.gov.cn/safe/2017/0126/12679.html",
     "no", "Inherited; not re-fetched."),
    ("S20", "SAFE Shanghai — 汇发〔2017〕3号 答记者问（利润汇出）", "https://www.safe.gov.cn/shanghai/2017/0126/76.html",
     "no", "Inherited; not re-fetched."),
    ("S21", "STA + SAFE Announcement 2013 No. 40 — 对外支付税务备案", "https://fgk.chinatax.gov.cn/zcfgk/c100012/c5194375/content.html",
     "no", "Inherited; not re-fetched."),
    ("S23", "State Taxation Administration — 中华人民共和国个人所得税法", "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html",
     "yes", "Art. 3 read in full: comprehensive 3%–45%, business 5%–35%, interest/dividends/rent/property-transfer/incidental 20%."),
    ("S24", "STA Shanghai — 财税〔2008〕132号 储蓄存款利息暂免征收个人所得税", "https://shanghai.chinatax.gov.cn/tax/zcfw/zcfgk/grsds/200810/t288953.html",
     "no", "Inherited; not re-fetched."),
    ("S27", "PBOC — 2014年中国货币政策大事记（取消挂牌买卖价差管理）", "https://www.pbc.gov.cn/zhengcehuobisi/125207/125227/125963/2810732/index.html",
     "no", "Inherited; this is the basis for saying the retail spread is market-set."),
    ("S29", "PBOC + 8 agencies — 银发〔2026〕42号 (virtual currency)", "https://www.pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html",
     "no", "Inherited; not re-fetched."),
    ("S32", "Supreme People's Court — 法释〔2019〕1号 非法买卖外汇解释", "http://www.hunan.gov.cn/zqt/zcsd/201901/t20190131_13641628.html",
     "no", "Inherited; not re-fetched."),
    ("S34", "Xuchang Intermediate People's Court — 刑法第225条 非法经营罪", "https://xczy.hncourt.gov.cn/public/detail.php?id=2739",
     "no", "Inherited; not re-fetched."),
    ("S35", "SAFE Hubei — 汇发〔2017〕29号 规范银行卡境外大额提取现金交易", "https://www.safe.gov.cn/hubei/2019/0305/851.html",
     "yes", "Art. 1: RMB 100,000 per natural year, all cards; art. 4: RMB 10,000 per card per day; breach suspends the facility for this and the next year."),
    ("S35b", "SAFE Hebei — 规范银行卡境外大额提取现金交易 答记者问", "https://www.safe.gov.cn/hebei/2018/0409/1010.html",
     "no", "Inherited; not re-fetched."),
    ("S37", "SAFE — 汇发〔2003〕102号 携带外币现钞出入境管理暂行办法", "https://www.safe.gov.cn/big5/big5/www.safe.gov.cn/tianjin/2024/0430/2466.html",
     "yes", "USD 5,000 free of permit; USD 5,000–10,000 needs a 携带证; above USD 10,000 not permitted in principle."),
    ("S38", "PBOC — 关于进一步优化跨境人民币政策", "https://www.pbc.gov.cn/tiaofasi/144941/3581332/4158143/index.html",
     "no", "Inherited; not re-fetched."),
    ("S39", "PBOC Guangzhou — 跨境理财通实施细则问题解答", "https://guangzhou.pbc.gov.cn/guangzhou/129196/4332364/4332374/4343888/index.html",
     "no", "Inherited; not re-fetched."),
    ("S40", "Guangdong Financial Supervision Administration — 跨境理财通解读", "http://gdjr.gd.gov.cn/gdjr/zwgk/jrzcfg/content/post_3520533.html",
     "no", "Inherited; not re-fetched."),
    ("S41", "SAFE Tianjin — QDII 账户开立、使用和关闭", "http://www.safe.gov.cn/tianjin/2019/0214/1098.html",
     "no", "Inherited; not re-fetched."),
    ("S43", "SAFE Chongqing — 常见外汇业务答疑手册", "https://www.safe.gov.cn/chongqing/file/file/20190311/87806e211bb74eb4a44e71395c31cda9.pdf",
     "no", "Inherited; carries the statement that foreign-individual FX purchase has no annual quota."),
    ("S46", "Bank of China — 电子银行个人服务转账汇款费率表", "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
     "yes", "Read in full: 跨境汇款（电汇）1‰, min CNY 50, max CNY 260, cable CNY 80 HK/Macau/Taiwan or CNY 150 elsewhere."),
    ("S50", "HKMA — Quarterly Bulletin 2012-03, ch. 4", "https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201203/chapter4.pdf",
     "partial", "Chunks 0 and 4 read; the 1.94% CNH figure the earlier register attributes to it was NOT located, so it is not used as a price."),
    ("S53", "SAFE Inner Mongolia — 个人外汇管理政策及常见问题解答", "https://www.safe.gov.cn/neimenggu/file/file/20200228/fa90770027ed4d919de981c09bc25751.pdf",
     "no", "Inherited; not re-fetched."),
    ("S56", "CSRC Shanxi — 虚拟货币 境内严禁、境外严管 (2026)", "https://www.csrc.gov.cn/shanxi/c106408/c7616553/content.shtml",
     "no", "Inherited; not re-fetched."),
    ("U02", "IRS — Publication 54, Tax Guide for U.S. Citizens Abroad", "https://www.irs.gov/publications/p54",
     "no", "Inherited; not re-fetched."),
    ("U05", "IRS — Publication 514, Foreign Tax Credit", "https://www.irs.gov/publications/p514",
     "no", "Inherited; not re-fetched."),
    ("U06", "IRS — Comparison of Form 8938 and FBAR requirements", "https://www.irs.gov/businesses/comparison-of-form-8938-and-fbar-requirements",
     "no", "Inherited; not re-fetched."),
    ("U09", "IRS — Gifts from foreign person (Form 3520)", "https://www.irs.gov/businesses/gifts-from-foreign-person",
     "no", "Inherited; not re-fetched."),
    ("U16", "IRS — US–PRC Income Tax Convention (1984)", "https://www.irs.gov/pub/irs-trty/china.pdf",
     "no", "Inherited; not re-fetched."),
    ("U20", "eCFR — 31 CFR 1010.821 (penalty table)", "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010/subpart-H/section-1010.821",
     "no", "Inherited; carries the FBAR willful ceiling."),
]
SRC = {s[0]: dict(id=s[0], authority=s[1], url=s[2], rechecked=s[3], note=s[4]) for s in SOURCES}


# fail loudly if the engine cites a source that is not in this pass's register
_used = set()
for _m in E.METHODS:
    _used.update(x.strip() for x in _m["source_ids"].split(",") if x.strip())
for _i in E.INPUTS:
    _used.add(_i["source_id"])
for _v in E.STEPS.values():
    for _st in _v:
        _used.add(_st[2])
_missing = sorted(i for i in _used if i not in SRC)
if _missing:
    raise SystemExit("cost_engine cites sources missing from the register: " + ", ".join(_missing))


def money(x: float | None, digits: int = 0) -> str:
    if x is None:
        return "<span class='blank'>blank</span>"
    return f"{x:,.{digits}f}"


def pct(x: float | None) -> str:
    if x is None:
        return "<span class='blank'>blank</span>"
    return f"{x:.3f}%"


def cost_class(x: float | None) -> str:
    if x is None:
        return ""
    if x < 0.3:
        return "c-good"
    if x < 1.0:
        return "c-mid"
    return "c-bad"


def link(src_id: str) -> str:
    s = SRC[src_id]
    return f'<a href="{s["url"]}" rel="noopener">{src_id}</a>'


def links(src_ids: str) -> str:
    return " ".join(link(i.strip()) for i in src_ids.split(",") if i.strip())


# --------------------------------------------------------------------------
# CSV output
# --------------------------------------------------------------------------
DATA.mkdir(exist_ok=True)

with (DATA / "cost_sources.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "authority_and_title", "url", "rechecked_this_pass", "what_it_verifies"])
    for s in SOURCES:
        w.writerow([s[0], s[1], s[2], s[3], s[4]])

with (DATA / "cost_inputs.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "input", "value", "unit", "as_of", "source_id", "source_url", "status", "note"])
    for i in E.INPUTS:
        w.writerow([i["id"], i["name"], i["value"], i["unit"], i["as_of"],
                    i["source_id"], i["url"], i["status"], i["note"]])

with (DATA / "cost_methods.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "rank", "family", "name", "name_zh", "legality", "moves_money", "fee_model",
                "ceiling", "time_basis", "verdict", "source_ids", "source_url"])
    for m in E.METHODS:
        w.writerow([m["id"], m["rank"], m["family"], m["name"], m["name_zh"], m["legality"],
                    m["moves_money"], m["fee_model"], m["ceiling"], m["years_basis"], m["verdict"],
                    m["source_ids"], m["url"]])

with (DATA / "cost_ladder.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["method_id", "amount_usd", "cny_needed", "spread_usd", "bank_fee_usd",
                "total_cost_usd", "cost_pct", "net_usd", "units", "units_label",
                "penalty_max_usd", "coef_per_0p10_usd", "basis"])
    for m in E.METHODS:
        for a in E.AMOUNTS:
            r = E.cost_row(m, a)
            w.writerow([
                r["method_id"], f"{r['amount_usd']:.0f}",
                f"{r['cny_needed']:.2f}" if r["cny_needed"] is not None else "",
                f"{r['spread_usd']:.2f}" if r["spread_usd"] is not None else "",
                f"{r['bank_fee_usd']:.2f}" if r["bank_fee_usd"] is not None else "",
                f"{r['total_usd']:.2f}" if r["total_usd"] is not None else "",
                f"{r['cost_pct']:.4f}" if r["cost_pct"] is not None else "",
                f"{r['net_usd']:.2f}" if r["net_usd"] is not None else "",
                r["units"] if r["units"] is not None else "",
                r["units_label"],
                f"{r['penalty_max_usd']:.2f}" if r["penalty_max_usd"] is not None else "",
                f"{r['coef_usd']:.2f}",
                r["basis"],
            ])

with (DATA / "cost_steps.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["method_id", "step_no", "action", "detail", "source_id", "source_url"])
    for mid, steps in E.STEPS.items():
        for n, (action, detail, sid, url) in enumerate(steps, 1):
            w.writerow([mid, n, action, detail, sid, url])

# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------
by_id = {m["id"]: m for m in E.METHODS}
LAWFUL_MOVERS = [m for m in E.METHODS if m["moves_money"] and m["fee_model"] not in ("unlawful", "offshore_unverified")]
UNLAWFUL = [m for m in E.METHODS if m["fee_model"] == "unlawful"]
KEY_AMOUNTS = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000]
m01 = by_id["M01"]
r400 = E.cost_row(m01, 400_000)
r10 = E.cost_row(m01, 10_000)

out: list[str] = []
A = out.append

A("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cost tables — CNY to USD, $10,000 to $400,000 · China money</title>
<meta name="description" content="Every lawful and unlawful CNY-to-USD route priced in USD 10,000 steps from 10,000 to 400,000, with the official source behind each fee.">
<link rel="stylesheet" href="assets/cost.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="index.html">China&nbsp;money<span>·</span>CNY&nbsp;→&nbsp;USD</a>
    <nav class="nav" aria-label="Sections">
      <a href="index.html">Home</a>
      <a href="deep-executive-summary.html">Summary</a>
      <a href="cost-tables.html" aria-current="page">Cost tables</a>
      <a href="deep-channels.html">All 35 routes</a>
      <a href="deep-penalty.html">Penalty</a>
      <a href="deep-review.html">Flagged</a>
      <a href="deep-sources.html">Sources</a>
    </nav>
  </div>
</header>
<main id="main">""")

# ---------------- hero ----------------
A(f"""
<section class="hero wrap">
  <p class="eyebrow">Cost estimate · generated from published tariffs</p>
  <h1>What it actually costs to turn CNY into USD,<br class="wide"> $10,000 to $400,000</h1>
  <p class="lede">Forty amount steps. Twenty routes. Every fee either comes from a published tariff with
  the link next to it, or it is left <strong>blank</strong> and flagged. No industry averages, no guessed spreads.</p>

  <div class="kpis">
    <div class="kpi">
      <span class="kpi-num">${money(r10['total_usd'])}</span>
      <span class="kpi-lab">all-in, China side, on $10,000</span>
      <span class="kpi-sub">{pct(r10['cost_pct'])} of the amount</span>
    </div>
    <div class="kpi">
      <span class="kpi-num">${money(r400['total_usd'])}</span>
      <span class="kpi-lab">all-in, China side, on $400,000</span>
      <span class="kpi-sub">{pct(r400['cost_pct'])} of the amount</span>
    </div>
    <div class="kpi">
      <span class="kpi-num">$0</span>
      <span class="kpi-lab">Chinese tax on converting your own principal</span>
      <span class="kpi-sub">no such tax found in any official source (P01)</span>
    </div>
    <div class="kpi kpi-warn">
      <span class="kpi-num">${money(400_000 * E.FBAR_WILLFUL_PCT)}</span>
      <span class="kpi-lab">willful FBAR ceiling on a $400,000 balance</span>
      <span class="kpi-sub">50% of the balance — {400_000 * E.FBAR_WILLFUL_PCT / r400['total_usd']:.0f}× the transfer cost</span>
    </div>
  </div>

  <div class="answer">
    <h2>The answer, before the tables</h2>
    <p>On the China side the honest, sourced cost of moving <strong>$400,000</strong> lawfully is about
    <strong>${money(r400['total_usd'])}</strong> — roughly <strong>{pct(r400['cost_pct'])}</strong> — made up of
    <strong>${money(r400['spread_usd'], 2)}</strong> of bank spread and <strong>${money(r400['bank_fee_usd'], 2)}</strong>
    of wire and cable charges. The number that can actually cost you six figures is not the conversion at all:
    it is a willful FBAR penalty, or a Chinese penalty on an unlawful route, both of which are percentage
    penalties on the whole amount.</p>
    <p>So the least-penalty strategy is not a clever conversion trick. It is: use one lawful route, document the
    source, and fix the US reporting. That ordering is worth more than every basis point in the tables below.</p>
  </div>
</section>""")

# ---------------- master ladder ----------------
A("""
<section class="wrap" id="ladder">
  <h2>1 · The route you should read first</h2>
  <p class="muted">Route <strong>M01 — non-resident converts documented onshore income and wires USD out</strong>.
  No annual quota for a 境外个人, one transfer, no approval queue. Cost = the bank's own quoted spread plus
  the tariff's 1‰ (capped at CNY 260) plus the CNY 150 cable charge. Rate: BOC board, 2026-11-09 09:15:45.</p>
""")

A("""  <div class="tablewrap">
  <table class="cost">
    <caption>$10,000 → $400,000 in $10,000 steps · route M01 · China-side cost only</caption>
    <thead><tr>
      <th scope="col">Amount (USD)</th>
      <th scope="col">CNY needed</th>
      <th scope="col">Bank spread</th>
      <th scope="col">Wire + cable</th>
      <th scope="col">Total cost</th>
      <th scope="col">Cost %</th>
      <th scope="col">You receive</th>
      <th scope="col">Src</th>
    </tr></thead><tbody>""")
for a in E.AMOUNTS:
    r = E.cost_row(m01, a)
    A(f"<tr><td class='amt'>${a:,}</td><td>{r['cny_needed']:,.0f}</td>"
      f"<td>${money(r['spread_usd'], 2)}</td><td>${money(r['bank_fee_usd'], 2)}</td>"
      f"<td class='{cost_class(r['cost_pct'])}'><strong>${money(r['total_usd'], 2)}</strong></td>"
      f"<td class='{cost_class(r['cost_pct'])}'>{pct(r['cost_pct'])}</td>"
      f"<td>${money(r['net_usd'], 2)}</td><td class='src'>{links('S46,CS01')}</td></tr>")
A("""  </tbody></table></div>
  <p class="note">Read the shape of it: the cost <em>falls</em> as a percentage as the amount rises, because the
  1‰ fee hits its CNY 260 cap at about <strong>$38,853</strong>. Above that, the whole cost is the spread
  0.2104% plus a fixed $61.27. Exact figures, not rounded: they are re-derived line by line by
  <code>scripts/verify_cost_tables.py</code>.</p>
</section>""")

# ---------------- all methods at a glance ----------------
A("""
<section class="wrap" id="methods">
  <h2>2 · Every route at six amounts</h2>
  <p class="muted">One row per route; the cell is the China-side all-in cost in USD at that amount.
  <span class="blank">blank</span> means no official source prices it — it is not zero, and it is flagged below.</p>
  <div class="tablewrap">
  <table class="cost keys">
    <thead><tr><th scope="col">Route</th>
""")
for a in KEY_AMOUNTS:
    A(f"<th scope='col'>${a//1000}k</th>")
A("<th scope='col'>Time</th><th scope='col'>Src</th></tr></thead><tbody>")
for m in E.METHODS:
    A(f"<tr><td class='route'><span class='rank'>{m['rank']}</span> <a href='#{m['id']}'>{html.escape(m['name'])}</a>"
      f"<span class='mini'>{html.escape(m['family'])}</span></td>")
    for a in KEY_AMOUNTS:
        r = E.cost_row(m, a)
        cls = cost_class(r["cost_pct"])
        txt = f"${money(r['total_usd'])}" if r["total_usd"] is not None else "<span class='blank'>blank</span>"
        A(f"<td class='{cls}'>{txt}</td>")
    t = E.cost_row(m, 400_000)
    A(f"<td class='time'>{html.escape(str(t['units_label']))}</td>")
    A(f"<td class='src'>{links(m['source_ids'])}</td></tr>")
A("""  </tbody></table></div>
  <p class="note">Yellow and red cells are the routes where the <em>penalty</em>, not the fee, is the cost.
  The next two tables give those numbers per amount.</p>
</section>""")

# ---------------- unlawful ----------------
A("""
<section class="wrap" id="unlawful">
  <h2>3 · What the unlawful routes cost if you are caught</h2>
  <p class="muted">These routes publish no fee, so the fee is blank. The statutory consequence is not blank.
  The figures are <strong>percentages of the amount moved</strong>, exactly as the provision reads — a ceiling,
  not a prediction.</p>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr><th scope="col">Amount</th><th scope="col">Base case ≤30%</th>
    <th scope="col">Serious 30%–100%</th><th scope="col">Criminal line</th><th scope="col">Provision</th></tr></thead><tbody>""")
for a in E.AMOUNTS:
    A(f"<tr><td class='amt'>${a:,}</td><td>${money(a*0.30)}</td>"
      f"<td class='c-bad'><strong>${money(a*1.00)}</strong></td>"
      f"<td>art. 225 exposure above the judicial threshold</td><td class='src'>{links('S07,S34')}</td></tr>")
A("""  </tbody></table></div>
  <p class="note">At $400,000 the serious-case ceiling is <strong>$400,000</strong> — the entire balance, plus
  confiscation of the gain, plus criminal referral. Compare with <strong>${money(r400['total_usd'], 2)}</strong>
  for doing it lawfully: the unlawful route risks {400_000 / r400['total_usd']:.0f}× the lawful cost in order to
  save {r400['total_usd']:.2f}. That gap, not the spread, is what the phrase "considerable tax" is describing.</p>

  <div class="tablewrap">
  <table class="cost">
    <caption>US reporting penalties on the same balances, for scale</caption>
    <thead><tr><th scope="col">Balance</th><th scope="col">Willful FBAR (50%)</th>
    <th scope="col">Form 8938 understatement (40%)</th><th scope="col">Src</th></tr></thead><tbody>""")
for a in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000):
    A(f"<tr><td class='amt'>${a:,}</td><td class='c-bad'>${money(a*0.50)}</td>"
      f"<td>${money(a*0.40)}</td><td class='src'>{links('U20,U06')}</td></tr>")
A("""  </tbody></table></div>
</section>""")

# ---------------- per method detail ----------------
A("""
<section class="wrap" id="detail">
  <h2>4 · Route by route, $10,000 to $400,000, with the steps</h2>
  <p class="muted">Open a route. Each one gives the full 40-step ladder, the exact figures behind it,
  and the numbered sequence you would actually follow.</p>
""")
for m in E.METHODS:
    t400 = E.cost_row(m, 400_000)
    summary_cost = f"${money(t400['total_usd'])}" if t400["total_usd"] is not None else "blank"
    A(f"""  <details id="{m['id']}" class="route-card">
    <summary>
      <span class="rank">{m['rank']}</span>
      <span class="rtitle">{html.escape(m['name'])}<span class="zh">{html.escape(m['name_zh'])}</span></span>
      <span class="rval {'bad' if m['fee_model']=='unlawful' else ''}">{summary_cost}<small>at $400k</small></span>
    </summary>
    <div class="rc-body">
      <p class="verdict"><strong>Verdict.</strong> {html.escape(m['verdict'])}</p>
      <dl class="facts">
        <dt>Family</dt><dd>{html.escape(m['family'])}</dd>
        <dt>Legality</dt><dd><span class="pill {m['legality']}">{m['legality']}</span></dd>
        <dt>Ceiling</dt><dd>{html.escape(m['ceiling'])}</dd>
        <dt>Mechanics</dt><dd>{html.escape(m['legs'])}</dd>
        <dt>Why it can win</dt><dd>{html.escape(m['why'])}</dd>
        <dt>What to watch</dt><dd>{html.escape(m['caveat'])}</dd>
        <dt>US side</dt><dd>{html.escape(m['us_side'])}</dd>
        <dt>Sources</dt><dd class="src">{links(m['source_ids'])}</dd>
      </dl>
""")
    # cost ladder table (only where a total exists)
    if any(E.cost_row(m, a)["total_usd"] is not None for a in E.AMOUNTS):
        A("""      <div class="tablewrap"><table class="cost inner">
        <thead><tr><th scope="col">Amount</th><th scope="col">Spread</th><th scope="col">Fees</th>
        <th scope="col">Total</th><th scope="col">Cost %</th><th scope="col">Net</th>
        <th scope="col">Payments / trips</th><th scope="col">Src</th></tr></thead><tbody>""")
        for a in E.AMOUNTS:
            r = E.cost_row(m, a)
            A(f"<tr><td class='amt'>${a:,}</td>"
              f"<td>{('$'+money(r['spread_usd'],2)) if r['spread_usd'] is not None else '<span class=blank>blank</span>'}</td>"
              f"<td>{('$'+money(r['bank_fee_usd'],2)) if r['bank_fee_usd'] is not None else '<span class=blank>blank</span>'}</td>"
              f"<td class='{cost_class(r['cost_pct'])}'><strong>${money(r['total_usd'],2)}</strong></td>"
              f"<td class='{cost_class(r['cost_pct'])}'>{pct(r['cost_pct'])}</td>"
              f"<td>${money(r['net_usd'],2)}</td><td class='time'>{r['units']}</td>"
              f"<td class='src'>{links(m['source_ids'])}</td></tr>")
        A("      </tbody></table></div>")
    else:
        # no priced total: give the exact coefficient instead of a guess
        A("""      <p class="noquote">No official source prices this route, so no total is printed.
        What <em>is</em> exact is the arithmetic of any percentage you are quoted:</p>
        <div class="tablewrap"><table class="cost inner">
        <thead><tr><th scope="col">Amount</th><th scope="col">Cost per 0.10% of spread</th>
        <th scope="col">Cost per 1.00% of spread</th><th scope="col">Constraint</th>
        <th scope="col">Src</th></tr></thead><tbody>""")
        for a in E.AMOUNTS:
            r = E.cost_row(m, a)
            A(f"<tr><td class='amt'>${a:,}</td><td>${money(r['coef_usd'],2)}</td>"
              f"<td>${money(r['coef_usd']*10,2)}</td><td class='time'>{html.escape(str(r['units_label']))}</td>"
              f"<td class='src'>{links(m['source_ids'])}</td></tr>")
        A("      </tbody></table></div>")

    steps = E.STEPS.get(m["id"])
    if steps:
        A("      <h4>Step by step</h4><ol class='steps'>")
        for action, detail, sid, _url in steps:
            A(f"<li><strong>{html.escape(action)}.</strong> {html.escape(detail)} <span class='src'>({link(sid)})</span></li>")
        A("      </ol>")
    else:
        A("      <p class='note'>This route has no operating procedure to give: it is either not open to the "
          "fact pattern or it is not a conversion.</p>")
    A("    </div>\n  </details>")
A("</section>")

# ---------------- inputs ----------------
A("""
<section class="wrap" id="inputs">
  <h2>5 · Every number in the model, and where it came from</h2>
  <p class="muted">This is the whole model. If a figure is not here, it is not in any table above.
  <code>derived</code> means arithmetic performed on a published number; <code>unverified</code> is blank.</p>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr><th scope="col">ID</th><th scope="col">Input</th><th scope="col">Value</th>
    <th scope="col">Unit</th><th scope="col">Status</th><th scope="col">Src</th></tr></thead><tbody>""")
for i in E.INPUTS:
    v = html.escape(i["value"]) or "<span class='blank'>blank</span>"
    A(f"<tr><td class='mono'>{i['id']}</td><td>{html.escape(i['name'])}<span class='mini'>{html.escape(i['note'])}</span></td>"
      f"<td class='mono'>{v}</td><td>{html.escape(i['unit'])}</td>"
      f"<td><span class='pill {i['status']}'>{i['status']}</span></td>"
      f"<td class='src'>{link(i['source_id'])}</td></tr>")
A("""  </tbody></table></div>
</section>""")

# ---------------- flagged ----------------
A("""
<section class="wrap" id="flagged">
  <h2>6 · Flagged for review</h2>
  <p class="muted">Published so you can check them yourself. None of these blocks anything above; each one
  marks a place where the honest answer is "not established".</p>
  <div class="flags">""")
FLAGS = [
    ("IR-024", "The spread is a one-day observation",
     "CI04 is derived from the BOC board at 2026-11-09 09:15:45. Retail spreads have been deregulated since "
     "2014 (S27), so every bank, branch and minute differs. Re-read the board before you rely on the figure; "
     "the historical search at the same site lets you re-derive it for any past date.",
     "CS01", "https://www.boc.cn/sourcedb/whpjSearch/index.html"),
    ("IR-025", "The PRC 20% is a rate, not an amount",
     "For property, dividends or rent the tax base is the gain or the gross receipt, neither of which is public "
     "for your file. The tables therefore show the rate and leave the amount to be computed from your own basis. "
     "No figure was invented.", "S23", "https://www.chinatax.gov.cn/n810219/n810744/n3752930/n3752974/c3970366/content.html"),
    ("IR-026", "The 1.94% offshore basis could not be re-verified",
     "The earlier register attributes 1.94% to HKMA Quarterly Bulletin 2012-03 ch. 4. On re-check the sections "
     "read cover HKD rates and Mainland credit, and the figure was not found. It is therefore not used as a "
     "price; route M10 shows the exact cost of each 1.00% of basis instead.",
     "S50", "https://www.hkma.gov.hk/media/eng/publication-and-research/quarterly-bulletin/qb201203/chapter4.pdf"),
    ("IR-027", "A cited official source is now a dead link",
     "Source S17 in the earlier register (SAFE Guangdong 个人对外财产转移购付汇业务指南, URL "
     "safe.gov.cn/guangdong/2021/0323/1994.html) returns the SAFE 404 page. The underlying rule was re-sourced "
     "to the primary text (CS04/CS05). Route M05's own governing notice still could not be re-verified.",
     "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
    ("IR-028", "The US receiving fee is genuinely unknown",
     "BOC's own tariff says overseas bank charges are passed on at actual cost, so a correspondent or receiving "
     "deduction exists — but no regulator publishes an amount, and it varies by US bank and account tier. Every "
     "total on this page is therefore a China-side figure; the last leg is excluded rather than estimated. Read "
     "your own bank's fee schedule and add it.",
     "S46", "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html"),
    ("IR-029", "Route M03 did not exist in the earlier cost model",
     "PBC [2004] No. 16 art. 6 stages the payout over two years and art. 8 requires a cancelled hukou plus "
     "consular certification. Earlier pages described the emigrant transfer as a single transfer; the ladder "
     "here prices three purchases instead. That is a correction, not a reinterpretation.",
     "CS04", "http://m.safe.gov.cn/safe/2004/1116/5461.html"),
]
for fid, title, body, sid, url in FLAGS:
    A(f"""    <article class="flag">
      <h3><span class="fid">{fid}</span> {title}</h3>
      <p>{body}</p>
      <p class="src">Source: <a href="{url}" rel="noopener">{sid}</a></p>
    </article>""")
A("  </div>\n</section>")

# ---------------- sources ----------------
A("""
<section class="wrap" id="sources">
  <h2>7 · Source register for this pass</h2>
  <p class="muted"><strong>Re-checked</strong> means this session fetched the URL and read the passage it is cited
  for. <strong>no</strong> means the source is inherited from an earlier session's register and was not re-read
  here — stated plainly rather than dressed up as fresh verification.</p>
  <div class="tablewrap">
  <table class="cost">
    <thead><tr><th scope="col">ID</th><th scope="col">Authority and title</th><th scope="col">Re-checked</th></tr></thead><tbody>""")
for s in SOURCES:
    cls = "yes" if s[3] == "yes" else ("partial" if s[3] == "partial" else "no")
    A(f"<tr><td class='mono'>{s[0]}</td><td><a href='{s[2]}' rel='noopener'>{html.escape(s[1])}</a>"
      f"<span class='mini'>{html.escape(s[4])}</span></td>"
      f"<td><span class='pill {cls}'>{s[3]}</span></td></tr>")
A("""  </tbody></table></div>
</section>

<section class="wrap disclaimer">
  <p><strong>What this is.</strong> Arithmetic on published fees and published penalty provisions. It is not a
  quote, not tax advice and not legal advice. The bank's rate at the counter governs; the statute governs the
  penalty. Have a US tax adviser and a PRC-qualified adviser check the actual file before you file or apply.</p>
  <p><a href="index.html">← Back to the guide</a> · <a href="deep-review.html">Full flagged register</a> ·
  <a href="deep-sources.html">Full 84-source register</a> · <a href="deep-executive-summary.html">Executive summary</a></p>
</section>
</main>
<footer class="foot"><div class="wrap">
  <p>Every row carries a source link. Blank means unverified, never zero. Generated by
  <code>scripts/build_cost_tables.py</code> and re-derived by <code>scripts/verify_cost_tables.py</code>.</p>
</div></footer>
</body></html>
""")

(ROOT / "cost-tables.html").write_text("".join(out), encoding="utf-8")
print(f"cost-tables.html written ({len(''.join(out)):,} bytes)")
print(f"CSVs: {len(E.INPUTS)} inputs, {len(E.METHODS)} methods, {len(E.ladder())} ladder rows")
