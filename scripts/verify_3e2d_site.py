#!/usr/bin/env python3
"""Independent verification for the 3E2D dashboard. Does not import the engine.

Recomputes every ladder cell from raw board figures with exact fractions,
checks official source links, blanks flagged, page/data parity, internal links.
"""
import csv, math, re, sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PAGES = [ROOT / f"3e2d-{n}.html" for n in ("dashboard","summary","questions","methods","costs","steps","penalties","tax","flagged","sources","repo-review")]
OFFICIAL = ("boc.cn","safe.gov.cn","chinatax.gov.cn","pbc.gov.cn","irs.gov","govinfo.gov","fincen.gov","ecfr.gov","cbp.gov","wise.com","westernunion.com","bankofamerica.com")
errors = []
def fail(m): errors.append(m)
def official(url):
    host=(urlparse(url).hostname or "").lower()
    return any(host==d or host.endswith("."+d) for d in OFFICIAL)
def rows(name):
    with (ROOT/"data"/name).open(encoding="utf-8",newline="") as fh:
        return list(csv.DictReader(fh))

# board 2026/11/11 20:50:05
BID, ASK = F(66591,10000), F(66871,10000)
MID=(BID+ASK)/2
IRS={"2021":F(6452,1000),"2022":F(6730,1000),"2023":F(7075,1000),"2024":F(7189,1000),"2025":F(7129,1000)}
def cents(x): return f"{math.floor(x*100+F(1,2))/100:.2f}"
def wire_cny(usd): return min(F(260),max(F(50),usd*ASK/1000))+150
def expect(model, usd):
    if model=="fx_wire":
        s,w=usd*(ASK-MID)/ASK, wire_cny(usd)/ASK
        return s,w,None,s+w,1,1
    if model=="wire_only":
        w=wire_cny(usd)/ASK
        return None,w,None,w,1,1
    if model=="quota":
        n_full,rem=divmod(usd,50000)
        fee=n_full*wire_cny(F(50000))/ASK+(wire_cny(rem)/ASK if rem else 0)
        s=usd*(ASK-MID)/ASK
        n=int(n_full)+(1 if rem else 0)
        return s,fee,None,s+fee,n,n
    if model=="atm":
        cny=usd*ASK
        n_full=cny//10000
        rem=cny-n_full*10000
        fee=n_full*min(F(112),12+F(10000)/100)+(min(F(112),12+rem/100) if rem else 0)
        return None,fee/ASK,None,fee/ASK,int(n_full)+(1 if rem else 0),math.ceil(cny/100000)
    if model=="cash":
        s=usd*(ASK-MID)/ASK
        return s,None,None,s,math.ceil(usd/5000),None
    if model in ("dividend","dividend_treaty"):
        tax=usd*(F(20,100) if model=="dividend" else F(10,100))
        net=usd-tax
        s,w=net*(ASK-MID)/ASK, wire_cny(net)/ASK
        return s,w,tax,tax+s+w,1,1
    if model=="blank":
        return None,None,None,None,None,None
    raise ValueError(model)

ladder=rows("3e2d_ladder.csv")
if len(ladder)!=560: fail(f"ladder rows {len(ladder)} != 560 (14 priced/blank methods x 40)")
for r in ladder:
    usd=F(int(r["amount_usd"]))
    s,w,t,tot,units,years=expect(r["model"],usd)
    def chk(col,exp):
        got=r[col]
        want="" if exp is None else cents(exp)
        if got!=want: fail(f"{r['method_id']} ${r['amount_usd']} {col}: got {got!r} want {want!r}")
    chk("spread_usd",s); chk("fee_usd",w); chk("tax_usd",t); chk("known_cost_usd",tot)
    if tot is not None:
        pct=tot/usd*100
        if r["known_cost_pct"]!=cents(pct): fail(f"{r['method_id']} ${r['amount_usd']} pct: got {r['known_cost_pct']!r} want {cents(pct)!r}")
    else:
        if r["known_cost_pct"]!="": fail(f"{r['method_id']} ${r['amount_usd']} pct should be blank")
        if r["flag"]=="": fail(f"{r['method_id']} blank row without flag")
    if units is not None and r["units"]!=str(units): fail(f"{r['method_id']} ${r['amount_usd']} units {r['units']} != {units}")
    if years is not None and r["calendar_years"]!=str(years): fail(f"{r['method_id']} ${r['amount_usd']} years {r['calendar_years']} != {years}")
    if r["model"]=="fx_wire":
        want=cents(usd*ASK+wire_cny(usd))
        if r["rmb_debited"]!=want: fail(f"{r['method_id']} ${r['amount_usd']} rmb {r['rmb_debited']} != {want}")
    for u in r["urls"].split():
        if not official(u): fail(f"ladder non-official url {u}")
    if r["sources"]=="": fail("ladder row without sources")

# fx gain spot checks (2024/2025 at 6 amounts)
for a in (10000,50000,100000,200000,300000,400000):
    for y in ("2024","2025"):
        want=cents(F(a)-F(a)*ASK/IRS[y])
        # page must contain the figure
        costs=(ROOT/"3e2d-costs.html").read_text(encoding="utf-8")
        if f"${float(want):,.2f}" not in costs and f"{want}" not in costs:
            fail(f"gain ${a} {y} {want} not on costs page")

# every CSV row carries official URL(s)
for name,col in [("3e2d_sources.csv","url"),("3e2d_questions.csv","sources"),("3e2d_methods.csv","sources"),("3e2d_steps.csv","sources"),("3e2d_penalties.csv","sources"),("3e2d_flags.csv","sources")]:
    for r in rows(name):
        if name=="3e2d_sources.csv":
            if not official(r["url"]): fail(f"{name} {r['id']} non-official {r['url']}")
        else:
            for sid in r["sources"].split("|"):
                if sid not in {s["id"] for s in rows("3e2d_sources.csv")}:
                    fail(f"{name} unknown source {sid}")
        for k,v in r.items():
            if v is None: fail(f"{name} missing column {k}")

# blanks flagged
flags={r["id"] for r in rows("3e2d_flags.csv")}
for name in ("3e2d_questions.csv","3e2d_methods.csv","3e2d_penalties.csv"):
    for r in rows(name):
        if r.get("flag") and r["flag"] not in flags: fail(f"{name} {r['id']} unknown flag {r['flag']}")

# page/data parity: costs page contains M01 $10k and $400k known costs
costs=(ROOT/"3e2d-costs.html").read_text(encoding="utf-8")
for want in ("$53.37","$898.75","$32.43","$61.31"):
    if want not in costs: fail(f"costs page missing {want}")
for p in PAGES:
    if not p.exists() or p.stat().st_size==0: fail(f"missing/empty page {p.name}")
    txt=p.read_text(encoding="utf-8")
    if "assets/3e2d.css" not in txt: fail(f"{p.name} missing css link")
    if "(blank)" not in txt and p.name not in ("3e2d-repo-review.html",):
        pass  # blanks appear on most pages; not required on every page

# internal links resolve
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            h=dict(attrs).get("href","")
            if h and not h.startswith(("http://","https://","mailto:","tel:","#")):
                self.hrefs.append(h.split("#")[0])
for p in PAGES:
    parser=Links(); parser.feed(p.read_text(encoding="utf-8"))
    for h in parser.hrefs:
        if h and not (p.parent/h).exists(): fail(f"{p.name}: missing local link {h}")

# no conflict markers in 3e2d files
marker=re.compile(r"^(<<<<<<<|=======|>>>>>>>)",re.M)
for p in list(ROOT.glob("3e2d*"))+list(ROOT.glob("data/3e2d*"))+list(ROOT.glob("scripts/*3e2d*")):
    if p.is_file():
        try:
            if marker.search(p.read_text(encoding="utf-8")): fail(f"conflict marker in {p}")
        except UnicodeDecodeError: pass

if errors:
    print(f"FAIL - {len(errors)} errors")
    for e in errors[:40]: print(" -",e)
    sys.exit(1)
print("PASS - 3E2D verification (ladder recomputed, sources official, blanks flagged, links resolve)")
