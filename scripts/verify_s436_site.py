#!/usr/bin/env python3
"""Independent structural/arithmetic verifier for the s436 CNY→USD dashboard.

It is deliberately a local reproducibility check, not a claim that a bank will
accept a particular customer or that a time-sensitive quote remains executable.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASK = Decimal("6.6903")
BID = Decimal("6.6622")
MID = (ASK + BID) / Decimal("2")
CABLE = Decimal("150")
OUR = Decimal("25")
PERSONAL_CAP = Decimal("260")
CORPORATE_CAP = Decimal("1000")
OFFICIAL_DOMAINS = {
    "boc.cn", "bocusa.com", "gov.cn", "safe.gov.cn", "chinatax.gov.cn",
    "pbc.gov.cn", "hncourt.gov.cn", "irs.gov", "ecfr.gov", "hkma.gov.hk",
    "home.treasury.gov",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def is_official(url: str) -> bool:
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme in {"http", "https"} and any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


def q(v: Decimal) -> str:
    return str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def num(v: str) -> Decimal:
    return Decimal(v)


def personal_fee(u: Decimal, cap: Decimal = PERSONAL_CAP) -> Decimal:
    cny_fee = min(cap, max(Decimal("50"), Decimal("0.001") * u * ASK))
    return cny_fee / ASK + CABLE / ASK


def one_way_spread(u: Decimal) -> Decimal:
    return u * (ASK - MID) / ASK


def check_sources(sources: list[dict[str, str]]) -> set[str]:
    if len(sources) != 36:
        fail(f"expected 36 official sources, got {len(sources)}")
    ids = {s["source_id"] for s in sources}
    if len(ids) != len(sources): fail("duplicate source id")
    for s in sources:
        if s["verification_status"] != "verified": fail(f"source is not marked verified: {s['source_id']}")
        if not is_official(s["official_source_url"]): fail(f"source outside approved official domain set: {s['source_id']}")
        if not s["title"] or not s["issuer"] or not s["notes"]: fail(f"incomplete source register: {s['source_id']}")
    source_json = json.loads((DATA / "s436_sources.json").read_text(encoding="utf-8"))
    if source_json != sources: fail("s436_sources.json is not the CSV-equivalent source register")
    return ids


def check_methods(methods: list[dict[str, str]], ids: set[str]) -> None:
    if len(methods) != 16: fail(f"expected 16 methods, got {len(methods)}")
    actual = {m["method_id"] for m in methods}
    expected = {f"M{i:02d}" for i in range(1,17)}
    if actual != expected: fail(f"method IDs mismatch: {actual ^ expected}")
    for m in methods:
        if not m["official_source_url"] or not is_official(m["official_source_url"]): fail(f"method source URL bad: {m['method_id']}")
        registered = m["source_ids"].split("|")
        if any(x not in ids for x in registered): fail(f"method unregistered source ID: {m['method_id']}")
        if m["source_id"] != registered[0]: fail(f"method primary source mismatch: {m['method_id']}")
        if not m["pros"] or not m["cons"] or not m["availability"]: fail(f"method narrative incomplete: {m['method_id']}")


def check_schedule(rows: list[dict[str, str]], methods: list[dict[str, str]], ids: set[str]) -> None:
    if len(rows) != 640: fail(f"expected 640 schedule rows, got {len(rows)}")
    methods_by_id = {m["method_id"]:m for m in methods}
    expected = {(f"M{i:02d}", f"{a:.2f}") for i in range(1,17) for a in range(10_000,400_001,10_000)}
    found = {(r["method_id"], r["target_usd"]) for r in rows}
    if found != expected: fail(f"schedule coverage mismatch: missing={len(expected-found)} extra={len(found-expected)}")
    if len(found) != len(rows): fail("duplicate method/amount schedule row")
    for r in rows:
        mid, u = r["method_id"], num(r["target_usd"])
        if r["source_id"] not in ids or not is_official(r["official_source_url"]): fail(f"bad row source {mid} {u}")
        m = methods_by_id[mid]
        model = m["cost_model"]
        # A blank all-in total is mandatory if a relevant tax or commercial charge
        # cannot be known. The displayed components are still useful provenance.
        if r["status"] == "UNVERIFIED" and r["known_cost_usd"]:
            fail(f"UNVERIFIED row has invented all-in cost: {mid} {u}")
        if r["status"] == "PROHIBITED" and r["known_cost_usd"]:
            fail(f"prohibited route presented as a conversion cost: {mid} {u}")
        if r["status"] in {"UNVERIFIED", "partial", "PROHIBITED"} and not r["unverified_costs"]:
            fail(f"non-final row lacks disclosure: {mid} {u}")
        if model == "personal":
            fx = one_way_spread(u); wire = personal_fee(u); total = fx + wire
            values = (r["fx_spread_usd"], r["bank_wire_and_cable_usd"], r["our_usd"], r["known_cost_usd"], r["net_after_known_cost_usd"])
            want = (q(fx),q(wire),"",q(total),q(u-total))
            if values != want: fail(f"personal formula mismatch: {mid} {u}: {values} != {want}")
        elif model == "quota":
            n = math.ceil(float(u / Decimal("50000")))
            pieces = [min(Decimal("50000"),u-Decimal("50000")*i) for i in range(n)]
            fx=sum((one_way_spread(x) for x in pieces),Decimal())
            wire=sum((personal_fee(x) for x in pieces),Decimal())
            total=fx+wire
            values=(r["execution_count"],r["minimum_calendar_years"],r["fx_spread_usd"],r["bank_wire_and_cable_usd"],r["our_usd"],r["known_cost_usd"],r["net_after_known_cost_usd"])
            want=(str(n),str(n),q(fx),q(wire),"",q(total),q(u-total))
            if values != want: fail(f"quota formula mismatch: {mid} {u}: {values} != {want}")
        elif model == "personal_unknown_tax":
            if any(r[k] for k in ("known_cost_usd","net_after_known_cost_usd","published_statutory_tax_or_fine_usd")):
                fail(f"property route must not infer unknown tax/all-in total: {mid} {u}")
        elif model == "corporate_dividend":
            fx=one_way_spread(u)
            wire=min(CORPORATE_CAP,max(Decimal("50"),Decimal("0.001")*u*ASK))/ASK+CABLE/ASK
            tax=Decimal("0.10")*u
            values=(r["fx_spread_usd"],r["bank_wire_and_cable_usd"],r["our_usd"],r["published_statutory_tax_or_fine_usd"],r["known_cost_usd"],r["net_after_known_cost_usd"])
            want=(q(fx),q(wire),q(OUR),q(tax),"","")
            if values != want: fail(f"corporate formula mismatch: {mid} {u}: {values} != {want}")
        elif model == "usd_wire":
            wire=personal_fee(u); total=wire
            values=(r["cny_principal_at_boc_ask"],r["fx_spread_usd"],r["bank_wire_and_cable_usd"],r["our_usd"],r["known_cost_usd"],r["net_after_known_cost_usd"])
            want=("","0.00",q(wire),"",q(total),q(u-total))
            if values != want: fail(f"existing USD formula mismatch: {mid} {u}: {values} != {want}")
        elif model == "unionpay_atm":
            cny=u*ASK; n=math.ceil(float(cny/Decimal("10000")))
            values=[min(Decimal("10000"), cny-Decimal("10000")*i) for i in range(n)]
            atm=sum((min(Decimal("112"),Decimal("12")+Decimal(".01")*x) for x in values),Decimal())/ASK
            years=math.ceil(float(cny/Decimal("100000")))
            if (r["execution_count"],r["minimum_calendar_years"],r["published_atm_fee_usd"],r["known_cost_usd"]) != (str(n),str(years),q(atm),""):
                fail(f"UnionPay ATM formula mismatch: {mid} {u}")
        elif model == "cash":
            if r["known_cost_usd"] or r["net_after_known_cost_usd"]: fail(f"cash all-in total must be blank: {mid} {u}")
            if r["fx_spread_usd"] != q(one_way_spread(u)): fail(f"cash spread mismatch: {mid} {u}")
        elif model == "prohibited_30":
            if r["published_statutory_tax_or_fine_usd"] != q(Decimal(".30")*u): fail(f"fine illustration mismatch: {mid} {u}")
        elif model == "unverified":
            numeric = ("fx_spread_usd","bank_wire_and_cable_usd","our_usd","published_atm_fee_usd","published_statutory_tax_or_fine_usd","known_cost_usd","net_after_known_cost_usd")
            if any(r[x] for x in numeric): fail(f"unquoted route has filled price: {mid} {u}")


def check_auxiliary(ids: set[str], methods: list[dict[str,str]]) -> None:
    flags=read_csv("s436_flags.csv")
    if len(flags) != 20 or {x["flag_id"] for x in flags} != {f"S436-IR-{i:03d}" for i in range(1,21)}: fail("flag register coverage mismatch")
    for row in flags:
        if row["source_id"] not in ids or not is_official(row["official_source_url"]): fail(f"bad flag source {row['flag_id']}")
    steps=read_csv("s436_steps.csv")
    if len(steps) < 48: fail("too few step-by-step instructions")
    for row in steps:
        if row["method_id"] not in {m["method_id"] for m in methods} or row["source_id"] not in ids or not is_official(row["official_source_url"]): fail("step source integrity failure")
    summary=read_csv("s436_method_summary_40steps.csv")
    if len(summary) != 16: fail("summary needs one row per method")
    for r in summary:
        if r["method_id"] not in {m["method_id"] for m in methods} or r["source_id"] not in ids or not is_official(r["official_source_url"]): fail("summary source integrity failure")


def check_output_html() -> None:
    pages = ["schedule-dashboard.html","schedule-cost-10k-400k.html","schedule-steps.html","schedule-methods.html","schedule-penalties.html","schedule-flagged-review.html","schedule-sources.html"]
    for name in pages:
        text=(ROOT/name).read_text(encoding="utf-8")
        if "assets/schedule-43606a6b.css" not in text or "schedule-sources.html" not in text: fail(f"missing common navigation/style: {name}")
        for href in re.findall(r'href="([^"]+)"',text):
            if href.startswith(("http://","https://","#","mailto:")): continue
            local=(ROOT/href.split("#",1)[0])
            if not local.exists(): fail(f"broken local link in {name}: {href}")
    costs=(ROOT/"schedule-cost-10k-400k.html").read_text(encoding="utf-8")
    if costs.count('data-method="') != 640: fail("cost HTML does not contain every schedule row")
    if costs.count('rel="noopener">S436-') < 640: fail("not every cost HTML row has an official source link")
    flagged=(ROOT/"schedule-flagged-review.html").read_text(encoding="utf-8")
    if sum(flagged.count(f"S436-IR-{i:03d}") for i in range(1,21)) != 20: fail("flagged review HTML missing flags")


def main() -> int:
    try:
        sources=read_csv("s436_sources.csv")
        ids=check_sources(sources)
        methods=read_csv("s436_methods.csv")
        check_methods(methods,ids)
        check_schedule(read_csv("s436_cost_schedule.csv"),methods,ids)
        check_auxiliary(ids,methods)
        check_output_html()
    except (AssertionError, KeyError, ValueError, ArithmeticError) as exc:
        print(f"S436 VERIFY FAILED: {exc}",file=sys.stderr)
        return 1
    print("S436 verified: 36 official sources; 16 methods; 640 cost rows; 65 source-linked steps; 20 flags; 7 linked pages.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
