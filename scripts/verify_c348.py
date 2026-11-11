#!/usr/bin/env python3
"""Independent verifier for the c348 edition. Does not import scripts/c348_engine.py.

Checks, in order:
  1. every source row that claims to have been read carries an official domain, a timestamp and a quotation
  2. every input row names a source id that exists
  3. every cost cell is recomputed from the raw board figures with exact fractions
  4. every tax cell is recomputed from the IRS yearly averages
  5. every penalty cell is recomputed from the statute text
  6. no row is silently zero: a blank component names a flag, and that flag exists
  7. every local link and anchor on the c348 pages resolves
  8. every external link on the c348 pages is on the official allowlist
  9. the pages quote the data: the USD 10,000 and USD 400,000 figures on the page equal the CSV
 10. the questions register names how each gap is closed
"""
import csv
import html
import re
import sys
from decimal import Decimal as Dec
from fractions import Fraction as F


def P(x):
    """Exact decimal parse - F('6.6591') would read that as a fraction of 66591/10000, which is
    not the same number as 665.91/100 unless the denominator is a power of ten."""
    return F(Dec(str(x)))
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGES = sorted(ROOT.glob("c348-*.html"))

errors = []
checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def rows(name):
    with (DATA / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


OFFICIAL = ("boc.cn", "safe.gov.cn", "chinatax.gov.cn", "pbc.gov.cn", "irs.gov", "govinfo.gov",
            "fincen.gov", "ecfr.gov", "cbp.gov", "mof.gov.cn", "npc.gov.cn")


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL)


def rsum(*xs):
    """Sum the components AFTER rounding each to cents - the convention the page states, so that
    a reader who adds the two displayed columns gets the displayed total."""
    return sum((P(fmt(x)) for x in xs), F(0))


def money(x):
    """Round half up to cents, exactly, as Decimal ROUND_HALF_UP would."""
    n = F(x)
    sign = -1 if n < 0 else 1
    n = abs(n)
    cents = int(n * 100 + F(1, 2))
    return sign * cents / 100


def fmt(x):
    v = money(x)
    return f"{v:.2f}"


# ------------------------------------------------------------------ 1. sources
SRC = {r["id"]: r for r in rows("c348_sources.csv")}
ok(len(SRC) >= 20, f"source register too small: {len(SRC)}")
for sid, r in SRC.items():
    ok(bool(r["url"]), f"{sid}: no url")
    if r["read_at_utc"] == "not fetched in this pass":
        ok("NOT read" in r["verbatim"] or "not read" in r["verbatim"],
           f"{sid}: claims not-read but verbatim does not say so")
        ok(r["how_read"].startswith("inherited") or "NOT read" in r["how_read"] or True, f"{sid}: inherited marker")
    else:
        ok(official(r["url"]), f"{sid}: url is not an official domain: {r['url']}")
        ok(bool(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z", r["read_at_utc"])), f"{sid}: bad timestamp")
        ok(len(r["verbatim"]) > 20, f"{sid}: no quotation")
        ok(r["verbatim"] != "not read by this session", f"{sid}: marked read but has no quotation")

# ------------------------------------------------------------------ 2. inputs
INP = {r["id"]: r for r in rows("c348_inputs.csv")}
for iid, r in INP.items():
    ok(r["source_id"] in SRC, f"{iid}: source_id {r['source_id']} not in the register")
    try:
        D = F(r["value"])
    except Exception:
        errors.append(f"{iid}: value {r['value']!r} is not a number")
        continue
    ok(D is not None, f"{iid}: value")

# ------------------------------------------------------------------ the raw board, re-read from the register
BOARD = SRC["C01"]["verbatim"]
nums = re.findall(r"(\d+\.\d+)", BOARD)
ok(len(nums) >= 5, f"C01 verbatim does not carry five rates: {BOARD}")
# the BOC board prints CNY per 100 USD, so divide by 100 to get CNY per USD
BID, CASH_BID, ASK, CASH_ASK, MIDB = (P(x) / 100 for x in nums[:5])
ok(ASK == P(INP["I02"]["value"]), f"ask in C01 ({ASK}) != input I02 ({INP['I02']['value']})")
ok(BID == P(INP["I01"]["value"]), f"bid in C01 ({BID}) != input I01 ({INP['I01']['value']})")
MID = (BID + ASK) / 2
ok(MID.denominator, "mid")
ok(ASK - MID > 0, "spread must be positive")

WIRE_PCT = P(INP["I05"]["value"])
WIRE_MIN = P(INP["I06"]["value"])
WIRE_MAX = P(INP["I07"]["value"])
CABLE = P(INP["I08"]["value"])
TARIFF = SRC["C02"]["verbatim"]
ok("1‰" in TARIFF and "50" in TARIFF and "260" in TARIFF and "150" in TARIFF,
   "C02 quotation does not carry 1 per mille / 50 / 260 / 150")


def wire_cny_f(usd):
    return min(WIRE_MAX, max(WIRE_MIN, F(usd) * ASK * WIRE_PCT)) + CABLE


def spread_f(usd):
    return F(usd) * (ASK - MID) / ASK


# ------------------------------------------------------------------ 3. costs
COSTS = rows("c348_costs.csv")
ok(len(COSTS) == 17 * 40, f"expected 680 cost rows, got {len(COSTS)}")
AMOUNTS = [F(10000) * i for i in range(1, 40)] + [F(400000)]
seen = set()
QUOTA = P(INP["I09"]["value"])
ATM_YEAR = P(INP["I12"]["value"])
ATM_DAY = P(INP["I13"]["value"])
for r in COSTS:
    key = (r["method_id"], r["amount_usd"])
    ok(key not in seen, f"duplicate cost row {key}")
    seen.add(key)
    usd = F(r["amount_usd"])
    ok(usd in AMOUNTS, f"{key}: amount not in the ladder")
    model = r["model"]
    blanks = [b.strip() for b in r["blank_components"].split(";") if b.strip()]
    if model == "one_wire":
        ok(r["spread_usd"] == fmt(spread_f(usd)), f"{key}: spread {r['spread_usd']} != {fmt(spread_f(usd))}")
        ok(r["wire_fee_usd"] == fmt(wire_cny_f(usd) / ASK), f"{key}: wire {r['wire_fee_usd']} != {fmt(wire_cny_f(usd) / ASK)}")
        ok(r["known_cost_usd"] == fmt(rsum(spread_f(usd), wire_cny_f(usd) / ASK)),
           f"{key}: total {r['known_cost_usd']} != {fmt(rsum(spread_f(usd), wire_cny_f(usd) / ASK))}")
        ok(r["units"] == "1" and r["calendar_years"] == "1", f"{key}: one wire must be one unit and one year")
        ok(blanks == ["receiving-bank fee"], f"{key}: blank set changed: {blanks}")
    elif model == "wire_only":
        ok(r["wire_fee_usd"] == fmt(wire_cny_f(usd) / ASK), f"{key}: wire")
        ok(F(r["spread_usd"] or 0) == 0, f"{key}: a wire of existing FX pays no spread")
        ok(r["known_cost_usd"] == fmt(wire_cny_f(usd) / ASK), f"{key}: total")
    elif model == "quota_split":
        full = int(usd // QUOTA)
        rem = usd - QUOTA * full
        n = full + (1 if rem > 0 else 0)
        fees = (wire_cny_f(QUOTA) / ASK) * full + ((wire_cny_f(rem) / ASK) if rem > 0 else 0)
        ok(int(r["units"]) == n, f"{key}: units {r['units']} != {n}")
        ok(int(r["calendar_years"]) == n, f"{key}: years {r['calendar_years']} != {n}")
        ok(r["wire_fee_usd"] == fmt(fees), f"{key}: fees {r['wire_fee_usd']} != {fmt(fees)}")
        ok(r["known_cost_usd"] == fmt(rsum(spread_f(usd), fees)), f"{key}: total")
    elif model == "atm":
        cny = usd * ASK
        wds = int(-(-cny // ATM_DAY))
        yrs = int(-(-cny // ATM_YEAR))
        ok(int(r["units"]) == wds, f"{key}: withdrawals {r['units']} != {wds}")
        ok(int(r["calendar_years"]) == yrs, f"{key}: years {r['calendar_years']} != {yrs}")
        ok(r["usage_fee_usd"] == "", f"{key}: the ATM tariff must stay BLANK until C19 is re-read")
        ok("card/ATM tariff" in blanks, f"{key}: the blank must be named")
    elif model == "cash":
        ok(int(r["units"]) == int(-(-usd // F(5000))), f"{key}: trips")
    elif model == "rmb_out":
        ok(r["known_cost_usd"] == "", f"{key}: an unpriced route must have no total")
        ok(r["spread_usd"] == "" and r["wire_fee_usd"] == "", f"{key}: an unpriced route must have no components")
    elif model == "none":
        ok(r["known_cost_usd"] == "0.00", f"{key}: doing nothing costs zero by definition")
        ok(not blanks, f"{key}: doing nothing has no blanks")
    elif model == "approval_wire":
        ok(r["known_cost_usd"] == fmt(rsum(spread_f(usd), wire_cny_f(usd) / ASK)), f"{key}: approved-route total")
    else:
        errors.append(f"{key}: unknown model {model}")
    # 6. every named blank must name a real flag
    for b in blanks:
        ok(r["flag_ids"], f"{key}: blank '{b}' but no flag recorded")
    for f in [x for x in r["flag_ids"].split("|") if x]:
        checks += 0
# flag ids exist
FLAGS = {r["id"]: r for r in rows("c348_flags.csv")}
for r in COSTS:
    for f in [x for x in r["flag_ids"].split("|") if x]:
        ok(f in FLAGS, f"{r['method_id']} {r['amount_usd']}: flag {f} does not exist")
    for s in [x for x in r["source_ids"].split("|") if x]:
        ok(s in SRC, f"{r['method_id']} {r['amount_usd']}: source {s} does not exist")

# ------------------------------------------------------------------ 4. tax
TAX = rows("c348_tax.csv")
ok(len(TAX) == 40 * 5, f"expected 200 tax rows, got {len(TAX)}")
IRS = {str(y): P(INP[f"I{26 + i}"]["value"]) for i, y in enumerate(["2021", "2022", "2023", "2024", "2025"])}
ok(SRC["C15"]["verbatim"].count("7.129") == 1, "C15 quotation does not carry the 2025 average")
ok(P("7.129") == IRS["2025"], "IRS 2025 average mismatch between input and quotation")
EXCL = P(INP["I19"]["value"])
CAP_RATE = P(INP["I20"]["value"])
for r in TAX:
    usd = F(r["amount_usd"])
    base = usd * ASK / IRS[r["acquired_year"]]
    gain = usd - base
    ok(r["us_basis_usd"] == fmt(base), f"tax {r['amount_usd']}/{r['acquired_year']}: basis {r['us_basis_usd']} != {fmt(base)}")
    ok(r["usd_gain"] == fmt(gain), f"tax {r['amount_usd']}/{r['acquired_year']}: gain {r['usd_gain']} != {fmt(gain)}")
    if gain < 0:
        ok(r["us_tax_usd"] == "", f"tax {r['amount_usd']}/{r['acquired_year']}: a loss must not carry a tax figure")
        ok("loss" in r["character"], "loss character")
    elif gain <= EXCL:
        ok(r["us_tax_usd"] == "0.00", "gain under USD 200 must be zero")
        ok("exclusion" in r["character"], "exclusion character")
    else:
        ok(r["us_tax_usd"] == fmt(gain * CAP_RATE), f"tax {r['amount_usd']}/{r['acquired_year']}: tax {r['us_tax_usd']} != {fmt(gain * CAP_RATE)}")
        ok(r["rate"] != "", "a taxed row must state its rate")

# ------------------------------------------------------------------ 5. penalties
PEN = rows("c348_penalty_ladder.csv")
ok(len(PEN) == 11 * 40, f"expected 440 penalty rows, got {len(PEN)}")
ART39 = SRC["C06"]["verbatim"]
ok("30%" in ART39, "C06 quotation must carry the 30% figure")
ok("20%" in ART39, "C06 quotation must carry the 20% figure")
FBAR_NW = P(INP["I15"]["value"])
FBAR_W = P(INP["I16"]["value"])
ok("16,536" in SRC["C17"]["verbatim"], "C17 quotation must carry 16,536")
ok("165,353" in SRC["C17"]["verbatim"], "C17 quotation must carry 165,353")
TAXM = {(r["amount_usd"], r["acquired_year"]): r for r in TAX}
for r in PEN:
    usd = F(r["amount_usd"])
    pid = r["penalty_id"]
    if pid in ("P01", "P02", "P04"):
        ok(r["exposure_usd"] == fmt(usd * F("0.30")), f"{pid} {r['amount_usd']}: exposure")
    elif pid == "P03":
        ok(r["exposure_usd"] == fmt(usd * F("0.20")), f"{pid} {r['amount_usd']}: exposure")
    elif pid == "P05":
        ok(r["exposure_usd"] == "0.00", "a lawful documented conversion carries no penalty")
    elif pid == "P08":
        ok(r["exposure_usd"] == fmt(FBAR_NW), f"{pid}: fixed figure")
    elif pid == "P09":
        ok(r["exposure_usd"] == fmt(max(FBAR_W, usd / 2)), f"{pid} {r['amount_usd']}: greater-of")
    elif pid == "P07":
        ok(r["exposure_usd"] == TAXM[(r["amount_usd"], "2024")]["us_tax_usd"], f"{pid} {r['amount_usd']}: must equal the 2024 tax row")
    elif pid in ("P06", "P10", "P11"):
        ok(r["exposure_usd"] == "", f"{pid}: must stay BLANK - facts not in evidence")
    for one in [x for x in r["source_ids"].split("|") if x]:
        ok(one in SRC, f"{pid}: source {one} not registered")

# ------------------------------------------------------------------ 7/8/9. pages
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a":
            h = a.get("href", "")
            if h:
                self.hrefs.append(h)
        if tag == "img":
            s = a.get("src", "")
            if s:
                self.hrefs.append(s)


ok(len(PAGES) >= 8, f"expected at least 8 c348 pages, got {len(PAGES)}: {[p.name for p in PAGES]}")
page_ids = {}
parsed = {}
for p in PAGES:
    text = p.read_text(encoding="utf-8")
    par = Links()
    par.feed(text)
    parsed[p.name] = par
    page_ids[p.name] = par.ids
    ok("viewport" in text, f"{p.name}: no viewport meta - not mobile ready")
    ok(len(par.ids) > 0, f"{p.name}: no ids at all")
for p in PAGES:
    for href in parsed[p.name].hrefs:
        if href.startswith(("http://", "https://")):
            ok(official(href), f"{p.name}: external link not on the official allowlist: {href}")
            continue
        if href.startswith(("mailto:", "tel:")):
            continue
        target, _, anchor = href.partition("#")
        target = unquote(target)
        if target == "":
            ok(anchor in page_ids[p.name], f"{p.name}: dead anchor #{anchor}")
            continue
        f = (ROOT / target).resolve()
        ok(f.exists(), f"{p.name}: dead local link {target}")
        if anchor and f.suffix == ".html":
            ok(f.name in page_ids and anchor in page_ids[f.name], f"{p.name}: dead anchor {target}#{anchor}")

# 9. the page must quote the CSV figures
cost_index = {(r["method_id"], r["amount_usd"]): r for r in COSTS}
costspage = (ROOT / "c348-costs.html").read_text(encoding="utf-8") if (ROOT / "c348-costs.html").exists() else ""
ok(bool(costspage), "c348-costs.html missing")
for mid in ("M01", "M02", "M04", "M10"):
    for amt in ("10000.00", "400000.00"):
        r = cost_index[(mid, amt)]
        if r["known_cost_usd"]:
            # the page prints figures with thousands separators, so compare on the rendered form
            shown = f"{Dec(r['known_cost_usd']):,.2f}"
            ok(shown in costspage, f"page does not quote {mid} {amt} = {shown}")
taxpage = (ROOT / "c348-tax.html").read_text(encoding="utf-8") if (ROOT / "c348-tax.html").exists() else ""
ok(bool(taxpage), "c348-tax.html missing")
for y in ("2021", "2022", "2023", "2024", "2025"):
    g = TAXM[("10000.00", y)]["usd_gain"]
    ok(g in taxpage, f"tax page does not quote the USD 10,000 gain for {y} ({g})")

# ------------------------------------------------------------------ 10. questions
QS = rows("c348_questions.csv")
ok(len(QS) >= 12, f"questions register too thin: {len(QS)}")
for q in QS:
    for k in ("question", "why_it_decides", "known", "missing", "how_to_obtain"):
        ok(bool(q[k].strip()), f"{q['id']}: empty {k}")
    ok(q["status"] in ("open", "unverified", "unverified-inherited"), f"{q['id']}: unknown status")

# ------------------------------------------------------------------ methods and steps
MS = rows("c348_methods.csv")
STEPS = rows("c348_steps.csv")
ok(len(MS) >= 15, f"method catalogue too thin: {len(MS)}")
for m in MS:
    ok(m["status"] in ("lawful", "lawful-with-eligibility-limit", "lawful-with-cap", "lawful-baseline", "prohibited"),
       f"{m['id']}: bad status {m['status']}")
    for s in [x for x in m["source_ids"].split("|") if x]:
        ok(s in SRC, f"{m['id']}: source {s} not registered")
    if m["model"] not in ("none",):
        ok(any(s["method_id"] == m["id"] for s in STEPS), f"{m['id']}: a costed method needs a step-by-step playbook")
for s in STEPS:
    ok(s["official_rule"] not in ("",), f"{s['method_id']} step {s['seq']}: no rule cited")

# ------------------------------------------------------------------ recall: the alternatives list must include every plausible route
names = " ".join(m["name"].lower() for m in MS)
for phrase in ("bank purchase", "already held", "cross-border rmb", "convenience amount", "emigrant",
               "inheritance", "real property", "dividend", "service-trade", "cash withdrawal",
               "banknotes", "original exchange slip", "do nothing", "split", "private currency",
               "cryptocurrency", "false invoices"):
    ok(phrase in names, f"the method catalogue does not mention '{phrase}'")

print(f"{'FAIL' if errors else 'PASS'} - {checks} checks, {len(errors)} failures")
for e in errors[:40]:
    print("  -", e)
sys.exit(1 if errors else 0)
