#!/usr/bin/env python3
"""Final integration gate: independent arithmetic, provenance, blanks and links."""
from __future__ import annotations

import csv
import re
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASK = Decimal("6.6903")
BID = Decimal("6.6622")
MID = (ASK + BID) / 2
OFFICIAL = {
    "boc.cn", "bocusa.com", "safe.gov.cn", "pbc.gov.cn", "gov.cn",
    "chinatax.gov.cn", "irs.gov", "ecfr.gov", "govinfo.gov", "hkma.gov.hk",
    "home.treasury.gov", "hncourt.gov.cn", "fincen.gov", "federalreserve.gov",
    "federalregister.gov",
}


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def q(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def official(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https"} and any(
        host == domain or host.endswith("." + domain) for domain in OFFICIAL
    )


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def check_local_links(page: Path) -> int:
    parser = Links()
    parser.feed(page.read_text(encoding="utf-8"))
    for href in parser.hrefs:
        if href.startswith(("https://", "http://", "mailto:", "tel:", "#")):
            continue
        target = href.split("#", 1)[0]
        if target and not (page.parent / target).exists():
            raise AssertionError(f"broken local link in {page.name}: {href}")
    return len(parser.hrefs)


def main() -> None:
    costs = rows("s436_cost_schedule.csv")
    methods = rows("s436_methods.csv")
    steps = rows("s436_steps.csv")
    flags = rows("final_integration_flags.csv")
    assert len(costs) == 640, len(costs)
    assert len(methods) == 16, len(methods)
    assert len(steps) == 65, len(steps)
    assert len(flags) >= 7
    assert {(r["method_id"], r["target_usd"]) for r in costs} == {
        (f"M{i:02d}", f"{amount:.2f}")
        for i in range(1, 17)
        for amount in range(10_000, 400_001, 10_000)
    }
    for collection, label in ((costs, "cost"), (methods, "method"), (steps, "step"), (flags, "flag")):
        for number, row in enumerate(collection, 1):
            url = row["official_source_url"]
            assert official(url), f"{label} row {number}: unofficial/missing source {url}"
    for row in costs:
        model = next(m["cost_model"] for m in methods if m["method_id"] == row["method_id"])
        target = Decimal(row["target_usd"])
        if model in {"personal", "quota", "personal_unknown_tax", "usd_wire"}:
            assert row["our_usd"] == "", f"corporate OUR leaked into {model}: {row}"
        if row["status"] in {"UNVERIFIED", "PROHIBITED"}:
            assert row["known_cost_usd"] == "", f"unknown/prohibited all-in cost filled: {row}"
            assert row["net_after_known_cost_usd"] == ""
        if row["status"] in {"UNVERIFIED", "partial", "PROHIBITED"}:
            assert row["unverified_costs"], f"missing limitation disclosure: {row}"
    # Re-derive M01 independently at all 40 amounts, without importing the builder.
    m01 = [r for r in costs if r["method_id"] == "M01"]
    assert len(m01) == 40
    for row in m01:
        target = Decimal(row["target_usd"])
        spread = target * (ASK - MID) / ASK
        wire_cny = min(Decimal("260"), max(Decimal("50"), Decimal("0.001") * target * ASK))
        wire = (wire_cny + Decimal("150")) / ASK
        total = spread + wire
        assert row["fx_spread_usd"] == q(spread), row
        assert row["bank_wire_and_cable_usd"] == q(wire), row
        assert row["known_cost_usd"] == q(total), row
        assert row["net_after_known_cost_usd"] == q(target - total), row
    assert next(r for r in m01 if r["target_usd"] == "10000.00")["known_cost_usd"] == "53.42"
    assert next(r for r in m01 if r["target_usd"] == "400000.00")["known_cost_usd"] == "901.30"

    home = (ROOT / "index.html").read_text(encoding="utf-8")
    assert home.count("data-cost-row") == 40
    for amount in range(10_000, 400_001, 10_000):
        assert f"${amount:,.0f}" in home
    for url in (
        "https://www.boc.cn/sourcedb/whpj/enindex_1619.html",
        "https://www.boc.cn/ebanking/service/cs1/200905/t20090506_990712.html",
        "https://www.safe.gov.cn/tianjin/2026/0713/3088.html",
    ):
        assert home.count(url) >= 40, f"homepage row provenance missing: {url}"
    count = 0
    for name in ("index.html", "final-verification.html", *(f"schedule-{n}.html" for n in (
        "dashboard", "cost-10k-400k", "steps", "methods", "penalties", "flagged-review", "sources"
    ))):
        count += check_local_links(ROOT / name)
    print(
        "FINAL INTEGRATION PASS — 640 cost rows, 16 methods, 65 steps, "
        f"40 homepage increments, {len(flags)} final flags, {count} links checked; "
        "independent M01 arithmetic and blank-unknown rules verified."
    )


if __name__ == "__main__":
    main()
