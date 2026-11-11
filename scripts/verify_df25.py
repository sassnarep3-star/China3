#!/usr/bin/env python3
"""Independent verifier for the df25 layer (the U.S. tax on turning RMB into dollars).

It does NOT import scripts/build_df25.py. It reads only what was published
(data/df25_*.csv and df25-conversion-tax-review.html) and re-derives it:

  A  files      every published file exists
  B  sources    every source is an https page on an official host, read on one date, with a quotation
  C  rows       every row of every table carries a source link that is in the register
  D  blanks     a value that is blank or not verified carries a flag, and every flag exists
  E  ladder     every cell of the ladder is recomputed from data/df25_inputs.csv with exact fractions
  F  checks     the dashboard's published figures are reproduced; the two official averages are compared
  G  example    the three withdrawal methods are recomputed; the regulation's own example is reproduced
  H  page       every table row on the page links to an official source; page figures equal the data;
                internal links and anchors resolve; the Flagged for Review section lists every flag
  I  hygiene    no conflict markers, no placeholders, no scripts; the generator reports nothing stale

Exit code 0 = clean, 1 = at least one failure. Standard library only.
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PAGE = ROOT / "df25-conversion-tax-review.html"
READ_ON = "2026-11-11"
OFFICIAL = {"www.govinfo.gov", "www.ecfr.gov", "www.irs.gov", "www.federalreserve.gov",
            "fred.stlouisfed.org", "www.boc.cn"}
FILES = ["data/df25_sources.csv", "data/df25_rules.csv", "data/df25_inputs.csv", "data/df25_ladder.csv",
         "data/df25_example.csv", "data/df25_steps.csv", "data/df25_levers.csv", "data/df25_flags.csv",
         "data/df25_repo_review.csv", "research/df25-us-conversion-tax.md", "df25-conversion-tax-review.html",
         "assets/df25.css"]
ORD = ["10", "12", "22", "24", "32", "35", "37"]
CAP = ["15", "20"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]

FAIL: list[str] = []
CHECKS = 0


def ok(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAIL.append(msg)
    return cond


def rows(name):
    with open(DATA / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def half_up(x: Fraction, places: int) -> Fraction:
    """Round half away from zero, as the published figures are."""
    scale = 10 ** places
    sign = -1 if x < 0 else 1
    n = (abs(x) * scale * 2 + 1) // 2
    return Fraction(sign * n, scale)


def F(s: str) -> Fraction:
    return Fraction(s.strip())


def split_urls(s: str):
    return [u.strip() for u in s.split("|") if u.strip()]


# --------------------------------------------------------------------------- A
def check_files():
    print("A. files")
    for f in FILES:
        ok((ROOT / f).is_file() and (ROOT / f).stat().st_size > 0, f"A: missing or empty {f}")


# --------------------------------------------------------------------------- B
def check_sources():
    print("B. sources")
    src = rows("df25_sources.csv")
    ok(len(src) >= 25, f"B: only {len(src)} sources")
    ids = [s["id"] for s in src]
    ok(len(ids) == len(set(ids)), "B: duplicate source ids")
    seen_urls = set()
    for s in src:
        u = urlparse(s["url"])
        ok(u.scheme == "https", f"B: {s['id']} is not https")
        ok(u.netloc in OFFICIAL, f"B: {s['id']} host {u.netloc} is not on the official list")
        ok(s["url"] not in seen_urls, f"B: {s['id']} repeats a URL")
        seen_urls.add(s["url"])
        ok(s["read_on"] == READ_ON, f"B: {s['id']} read_on is {s['read_on']}")
        ok(len(s["how_read"]) > 5, f"B: {s['id']} does not say how it was read")
        if s["how_read"].startswith("searched, not read"):
            ok(s["quotation"] == "", f"B: {s['id']} was not read but carries a quotation")
        else:
            ok(len(s["quotation"]) >= 30, f"B: {s['id']} has no quotation")
    return {s["id"]: s for s in src}, seen_urls


# --------------------------------------------------------------------------- C, D
def check_rows(src, urls):
    print("C. every row is sourced   D. blanks carry flags")
    flags = rows("df25_flags.csv")
    flag_ids = {f["id"] for f in flags}
    ok(len(flag_ids) == len(flags) and len(flags) >= 10, "D: flag ids are not unique or too few")
    rules = rows("df25_rules.csv")
    rule_ids = {r["id"] for r in rules}
    ok(len(rules) >= 30 and len(rule_ids) == len(rules), "C: rule ids are not unique or too few")

    def sourced(name, row, key):
        us = split_urls(row["source_urls"])
        ok(len(us) >= 1, f"C: {name} {row.get(key)} has no source link")
        for u in us:
            ok(u in urls, f"C: {name} {row.get(key)} cites a URL that is not in the register: {u}")
            ok(urlparse(u).netloc in OFFICIAL, f"C: {name} {row.get(key)} cites a non-official host")
        if "source_ids" in row:
            for i in row["source_ids"].split("|"):
                ok(i in src, f"C: {name} {row.get(key)} cites unknown source id {i}")
            ok([src[i]["url"] for i in row["source_ids"].split("|") if i in src] == us,
               f"C: {name} {row.get(key)} ids and URLs disagree")

    for r in rules:
        sourced("rule", r, "id")
        ok("'" in r["official_words"] and len(r["official_words"]) > 40, f"C: rule {r['id']} has no official words")
        ok(r["status"] in ("verified", "flagged"), f"D: rule {r['id']} has status {r['status']}")
        if r["status"] != "verified":
            ok(r["flag"] in flag_ids, f"D: rule {r['id']} is not verified and has no flag")
        if r["flag"]:
            ok(r["flag"] in flag_ids, f"D: rule {r['id']} names unknown flag {r['flag']}")
    for name, key in (("df25_steps.csv", "step"), ("df25_levers.csv", "id")):
        for r in rows(name):
            sourced(name, r, key)
            for rid in r["rule_ids"].split("|"):
                ok(rid in rule_ids, f"C: {name} {r[key]} names unknown rule {rid}")
            if r["flag"]:
                ok(r["flag"] in flag_ids, f"D: {name} {r[key]} names unknown flag {r['flag']}")
            for col, val in r.items():
                if col != "flag":
                    ok(val.strip() != "", f"D: {name} {r[key]} has a blank {col}")
    ok([r["step"] for r in rows("df25_steps.csv")] == [str(i) for i in range(1, len(rows("df25_steps.csv")) + 1)],
       "C: steps are not numbered 1..n")
    for f in flags:
        sourced("flag", f, "id")
        ok(f["severity"] in ("high", "medium", "low"), f"D: flag {f['id']} severity {f['severity']}")
        ok(f["status"] == "needs review", f"D: flag {f['id']} status {f['status']}")
        ok(len(f["what_is_not_known"]) > 30 and len(f["how_to_settle_it"]) > 5, f"D: flag {f['id']} is not explained")
    for r in rows("df25_repo_review.csv"):
        sourced("review", r, "id")
        ok(re.fullmatch(r"[0-9a-f]{7,40}", r["read_at_commit"]) is not None, f"C: review {r['id']} has no commit")
        ok(len(r["what_it_says"]) > 10 and len(r["what_the_official_text_says"]) > 10, f"C: review {r['id']} is empty")
    for r in rows("df25_example.csv"):
        sourced("example", r, "method")
        ok("illustration" in r["nature"], f"C: example {r['method']} is not labelled an illustration")
    for r in rows("df25_inputs.csv"):
        ok(r["source_url"] in urls and r["source_id"] in src and src[r["source_id"]]["url"] == r["source_url"],
           f"C: input {r['key']} is not tied to a registered source")
        ok(r["value"].strip() != "", f"D: input {r['key']} is blank")
    return flag_ids, rule_ids


# --------------------------------------------------------------------------- E
def check_ladder(urls):
    print("E. ladder — every cell recomputed with exact fractions")
    inp = {r["key"]: r["value"] for r in rows("df25_inputs.csv")}
    sell = F(inp["boc_usd_selling_rate_per_100"]) / 100
    ok(sell == Fraction(66886, 10000), f"E: selling rate is {sell}")
    rate = {}
    for k, v in inp.items():
        if k.startswith("fed_annual_average_"):
            rate[("year", k.rsplit("_", 1)[1])] = F(v)
        elif k.startswith("fed_monthly_average_"):
            rate[("month", k.rsplit("_", 1)[1])] = F(v)
    ok(len([k for k in rate if k[0] == "year"]) == 32, "E: expected 32 annual averages (1994-2025)")
    ok(len([k for k in rate if k[0] == "month"]) == 34, "E: expected 34 monthly averages (2024-01 to 2026-10)")
    for (_, _), v in rate.items():
        ok(Fraction(5) < v < Fraction(9), f"E: implausible rate {v}")
    ladder = rows("df25_ladder.csv")
    ok(len(ladder) == len(rate) * 40, f"E: ladder has {len(ladder)} rows, expected {len(rate) * 40}")
    by_period = {}
    bad = 0
    over_disclosure = 0
    for r in ladder:
        key = (r["period_type"], r["period"])
        by_period.setdefault(key, []).append(int(r["usd_received"]))
        if key not in rate:
            bad += 1
            continue
        usd = Fraction(int(r["usd_received"]))
        rmb = usd * sell
        basis = half_up(rmb / rate[key], 2)
        gain = usd - basis
        exp = {"acquisition_rate_rmb_per_usd": rate[key], "rmb_sold": half_up(rmb, 2), "basis_usd": basis,
               "gain_or_loss_usd": gain}
        pos = max(gain, Fraction(0))
        for p in ORD:
            exp[f"tax_ordinary_{p}pct_usd"] = half_up(pos * Fraction(p) / 100, 2)
        for p in CAP:
            exp[f"tax_long_term_capital_{p}pct_usd"] = half_up(pos * Fraction(p) / 100, 2)
        exp["niit_3_8pct_if_it_applies_usd"] = half_up(pos * Fraction(38, 1000), 2)
        for col, want in exp.items():
            if F(r[col]) != want:
                bad += 1
                if bad <= 5:
                    FAIL.append(f"E: {key} ${r['usd_received']} {col}: published {r[col]}, recomputed {float(want):.2f}")
        want200 = "no gain" if gain <= 0 else ("not recognized if personal" if gain <= 200 else "recognized")
        if r["usd_200_rule"] != want200:
            bad += 1
        if gain <= -50000:
            over_disclosure += 1
        us = split_urls(r["source_urls"])
        if not us or any(u not in urls for u in us):
            bad += 1
    ok(bad == 0, f"E: {bad} ladder cells differ from the recomputation")
    for key, amts in by_period.items():
        ok(amts == list(range(10000, 400001, 10000)), f"E: {key} does not run 10,000..400,000 in 10,000 steps")
    ok(over_disclosure == 0, "E: a ladder loss reaches the $50,000 disclosure line; the page says none does")
    print(f"   {len(ladder)} rows x 14 computed cells recomputed")
    return inp, sell, rate, ladder


# --------------------------------------------------------------------------- F
def check_cross(inp, sell, rate):
    print("F. cross-checks")
    n = 0
    for k, v in inp.items():
        m = re.fullmatch(r"dashboard_gain_(\d+)_acquired_(\d{4})", k)
        if not m:
            continue
        usd, year = Fraction(int(m.group(1))), m.group(2)
        irs = F(inp[f"irs_yearly_average_{year}"])
        gain = usd - half_up(usd * sell / irs, 2)
        ok(gain == F(v), f"F: dashboard figure {k}={v} is not reproduced (got {float(gain):.2f})")
        n += 1
    ok(n == 10, f"F: expected 10 recorded dashboard figures, found {n}")
    for year in ("2024", "2025"):
        ms = [v for (t, p), v in rate.items() if t == "month" and p.startswith(year)]
        mean = sum(ms) / len(ms)
        ok(len(ms) == 12 and abs(mean - rate[("year", year)]) < Fraction(5, 10000),
           f"F: monthly averages for {year} do not agree with the annual average")
    flags = {f["id"]: f for f in rows("df25_flags.csv")}
    mean25 = sum(v for (t, p), v in rate.items() if t == "month" and p.startswith("2025")) / 12
    mean24 = sum(v for (t, p), v in rate.items() if t == "month" and p.startswith("2024")) / 12
    ok(f"{float(half_up(mean25, 4)):.4f}" in flags["DF25-F13"]["what_is_not_known"], "F: F13 quotes a wrong 2025 mean")
    ok(f"{float(half_up(mean24, 4)):.4f}" in flags["DF25-F13"]["what_is_not_known"], "F: F13 quotes a wrong 2024 mean")
    irs25, fed25 = F(inp["irs_yearly_average_2025"]), rate[("year", "2025")]
    ok(fed25 - irs25 == Fraction(585, 10000), "F: the 2025 gap between the two official averages is not 0.0585")
    for y in ("2021", "2022", "2023", "2024"):
        ok(abs(rate[("year", y)] - F(inp[f"irs_yearly_average_{y}"])) <= Fraction(7, 1000),
           f"F: {y} averages differ by more than 0.007")
    usd = Fraction(400000)
    diff = (usd - half_up(usd * sell / fed25, 2)) - (usd - half_up(usd * sell / irs25, 2))
    ok(f"${int(half_up(diff, 0)):,}" in flags["DF25-F01"]["what_is_not_known"],
       f"F: F01 does not quote the recomputed difference ${int(half_up(diff, 0)):,}")
    ok(F(inp["personal_transaction_gain_limit"]) == 200 and F(inp["section_988_loss_disclosure_threshold"]) == 50000,
       "F: statutory thresholds changed")
    ok(F(inp["net_investment_income_rate"]) == Fraction(38, 10), "F: NIIT rate is not 3.8")
    # 2026 brackets must rise with the rate for each filing status
    for st in ("single", "married_filing_jointly", "head_of_household", "married_filing_separately"):
        lows = [F(inp[f"2026_ordinary_{p}pct_starts_above_{st}"]) for p in ORD]
        ok(lows == sorted(lows) and lows[0] == 0, f"F: 2026 brackets for {st} are not increasing")
        ok(F(inp[f"2026_capital_zero_rate_max_{st}"]) < F(inp[f"2026_capital_15pct_rate_max_{st}"]),
           f"F: capital-gain limits for {st} are out of order")


# --------------------------------------------------------------------------- G
def check_example(inp, sell, rate):
    print("G. example — three withdrawal methods")
    # the regulation's own example first: 1,200 Sf with a basis of $600; 500 Sf withdrawn pro rata
    ok(Fraction(600) * 500 / 1200 == 250 and 600 - 250 == 350, "G: the regulation's example is not reproduced")
    lots = []
    for name, year in (("A", "2021"), ("B", "2023"), ("C", "2025")):
        rmb = F(inp[f"example_lot_{name}_rmb"])
        lots.append((rmb, rmb / rate[("year", year)]))
    sale = F(inp["example_rmb_sold_per_conversion"])
    total_rmb, total_basis = sum(l[0] for l in lots), sum(l[1] for l in lots)
    ok(total_rmb == 2 * sale, "G: the two conversions do not empty the account")
    proceeds = sale / sell

    def take(order):
        left, basis = sale, Fraction(0)
        for rmb, b in order:
            use = min(left, rmb)
            basis += b * use / rmb
            left -= use
        return basis

    want = {"First in, first out": take(lots), "Last in, first out": take(list(reversed(lots))),
            "Pro rata": total_basis * sale / total_rmb}
    ex = {r["method"]: r for r in rows("df25_example.csv")}
    ok(set(ex) == set(want), "G: methods differ from the three the regulation names")
    totals = set()
    for m, b1 in want.items():
        b2 = total_basis - b1
        g1, g2 = proceeds - b1, proceeds - b2
        r = ex.get(m, {})
        for col, val in (("conversion_1_basis_usd", b1), ("conversion_1_gain_or_loss_usd", g1),
                         ("conversion_2_basis_usd", b2), ("conversion_2_gain_or_loss_usd", g2),
                         ("total_gain_or_loss_usd", g1 + g2),
                         ("gain_taxed_if_losses_do_not_count_usd", max(g1, 0) + max(g2, 0))):
            ok(r and F(r[col]) == half_up(val, 2), f"G: {m} {col} is not reproduced")
        totals.add(g1 + g2)
    ok(len(totals) == 1, "G: the three methods do not give the same total")


# --------------------------------------------------------------------------- H
class Page(HTMLParser):
    """Collects table rows (text and links per cell), ids, links, and the summary above each ladder."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.tables = set(), [], []
        self.tags = []
        self.in_tbody = False
        self.row = self.cell = None
        self.summary = None
        self.summaries = []
        self.cur_summary = ""
        self.h2 = []
        self._h2 = None
        self.scripts = 0
        self.meta_viewport = False
        self.css = []
        self.title = ""
        self._title = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.add(d["id"])
        if tag == "a" and "href" in d:
            self.links.append(d["href"])
            if self.cell is not None:
                self.cell["links"].append(d["href"])
        if tag == "script":
            self.scripts += 1
        if tag == "meta" and d.get("name") == "viewport":
            self.meta_viewport = True
        if tag == "link" and d.get("rel") == "stylesheet":
            self.css.append(d.get("href", ""))
        if tag == "title":
            self._title = True
        if tag == "h2":
            self._h2 = ""
        if tag == "summary":
            self.summary = ""
        if tag == "table":
            self.tables.append({"class": d.get("class", ""), "rows": [], "summary": self.cur_summary})
            self.cur_summary = ""
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row = {"id": d.get("id", ""), "cells": []}
        if tag == "td" and self.row is not None:
            self.cell = {"text": "", "links": [], "label": d.get("data-label", "")}

    def handle_endtag(self, tag):
        if tag == "title":
            self._title = False
        if tag == "h2" and self._h2 is not None:
            self.h2.append(self._h2.strip())
            self._h2 = None
        if tag == "summary" and self.summary is not None:
            self.cur_summary = " ".join(self.summary.split())
            self.summaries.append(self.cur_summary)
            self.summary = None
        if tag == "td" and self.cell is not None:
            self.cell["text"] = " ".join(self.cell["text"].split())
            self.row["cells"].append(self.cell)
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.tables[-1]["rows"].append(self.row)
            self.row = None
        if tag == "tbody":
            self.in_tbody = False

    def handle_data(self, data):
        if self._title:
            self.title += data
        if self._h2 is not None:
            self._h2 += data
        if self.summary is not None:
            self.summary += data
        if self.cell is not None:
            self.cell["text"] += data


def to_int(text: str):
    t = text.replace("*", "").replace(",", "").replace("$", "").replace("+", "").strip()
    neg = t.startswith("−")
    t = t.lstrip("−")
    return -int(t) if neg else int(t)


def check_page(urls, flag_ids, ladder, inp):
    print("H. page")
    text = PAGE.read_text(encoding="utf-8")
    p = Page()
    p.feed(text)
    ok(p.meta_viewport, "H: no viewport meta tag (mobile)")
    ok(p.scripts == 0, "H: the page contains a script")
    ok(p.css == ["assets/df25.css"], f"H: unexpected stylesheets {p.css}")
    ok("RMB" in p.title and "dollars" in p.title, "H: page title")
    ok(any("Flagged for Review" in h for h in p.h2), "H: no section headed 'Flagged for Review'")
    # every table row links to an official source
    total = 0
    for t in p.tables:
        for r in t["rows"]:
            total += 1
            ext = [l for c in r["cells"] for l in c["links"] if l.startswith("http")]
            if not ext or any(urlparse(l).netloc not in OFFICIAL for l in ext):
                FAIL.append(f"H: a table row has no official source link: {' | '.join(c['text'] for c in r['cells'])[:120]}")
    ok(total >= 900, f"H: only {total} table rows on the page")
    print(f"   {total} table rows, each with an official source link")
    # every external link is a registered source; internal links and anchors resolve
    for l in set(p.links):
        if l.startswith("http"):
            ok(l in urls, f"H: external link is not in the source register: {l}")
            ok(l.startswith("https://") and urlparse(l).netloc in OFFICIAL, f"H: external link is not official: {l}")
        elif l.startswith("#"):
            ok(l[1:] in p.ids, f"H: in-page anchor does not exist: {l}")
        else:
            target = l.split("#")[0]
            ok((ROOT / target).is_file(), f"H: internal link does not resolve: {l}")
    # flags: every flag has a row, and a blank cell carries a flag link
    for fid in flag_ids:
        ok(fid in p.ids, f"H: flag {fid} has no row in the Flagged for Review table")
    blanks = 0
    for t in p.tables:
        for r in t["rows"]:
            for c in r["cells"]:
                if c["text"].startswith(("Not stated in the texts read", "none — the page was searched")):
                    blanks += 1
                    ok(any(l.startswith("#DF25-F") for l in c["links"]), "H: a blank cell carries no flag")
    ok(blanks == 2, f"H: expected 2 blank-and-flagged cells, found {blanks}")
    # ladder tables: 40 rows each, figures equal the data
    by = {}
    for r in ladder:
        by[(r["period_type"], r["period"], int(r["usd_received"]))] = r
    n_tables = n_cells = 0
    for t in p.tables:
        m = re.match(r"RMB acquired in (?:(\w+) )?(\d{4})\b", t["summary"])
        if not m:
            continue
        n_tables += 1
        if m.group(1):
            kind, period = "month", f"{m.group(2)}-{MONTHS.index(m.group(1)) + 1:02d}"
        else:
            kind, period = "year", m.group(2)
        ok(len(t["rows"]) == 40, f"H: ladder {period} has {len(t['rows'])} rows")
        for r in t["rows"]:
            cells = [c["text"] for c in r["cells"]]
            usd = to_int(cells[0])
            d = by.get((kind, period, usd))
            if not ok(d is not None, f"H: ladder {period} ${usd} is not in the data"):
                continue
            gain = F(d["gain_or_loss_usd"])
            ok(to_int(cells[1]) == int(half_up(gain, 0)), f"H: ladder {period} ${usd} gain differs from the data")
            ok(("*" in cells[1]) == (d["usd_200_rule"] == "not recognized if personal"),
               f"H: ladder {period} ${usd} $200 mark differs from the data")
            cols = [f"tax_ordinary_{x}pct_usd" for x in ORD] + [f"tax_long_term_capital_{x}pct_usd" for x in CAP] + \
                   ["niit_3_8pct_if_it_applies_usd"]
            for cell, col in zip(cells[2:12], cols):
                n_cells += 1
                if gain > 0:
                    ok(to_int(cell) == int(half_up(F(d[col]), 0)), f"H: ladder {period} ${usd} {col} differs from the data")
                else:
                    ok(cell == "–", f"H: ladder {period} ${usd} shows a tax where there is no gain")
    ok(n_tables == 20, f"H: expected 20 ladder tables, found {n_tables}")
    print(f"   {n_tables} ladder tables, {n_cells} tax cells equal to the data")
    # 2026 brackets printed on the page equal the inputs
    for k, v in inp.items():
        if k.startswith("2026_") or k.startswith("niit_threshold_"):
            if int(v) > 0:
                ok(f"${int(v):,}" in text, f"H: {k} = {v} is not printed on the page")
    ok(inp["boc_usd_selling_rate_per_100"] in text, "H: the board rate is not printed on the page")
    ok("2026/11/11 15:30:04" in (DATA / "df25_sources.csv").read_text(encoding="utf-8"), "H: the board time stamp is missing")


# --------------------------------------------------------------------------- I
def check_hygiene():
    print("I. hygiene")
    marker = re.compile(r"^(<{7}|={7}|>{7})( |$)", re.M)
    for f in FILES + ["scripts/build_df25.py", "scripts/verify_df25.py"]:
        path = ROOT / f
        if not path.is_file():
            continue
        t = path.read_text(encoding="utf-8")
        ok(not marker.search(t), f"I: conflict marker in {f}")
        if not f.startswith("scripts/"):
            for w in ("TODO", "TBD", "lorem ipsum", "PLACEHOLDER"):
                ok(w not in t, f"I: placeholder '{w}' in {f}")
    gen = ROOT / "scripts" / "build_df25.py"
    if gen.is_file():
        r = subprocess.run([sys.executable, str(gen), "--check"], cwd=ROOT, capture_output=True, text=True)
        ok(r.returncode == 0, "I: generated files are stale — " + (r.stdout or r.stderr).strip()[-200:])


def main() -> int:
    print("=" * 72)
    print("df25 verification — the U.S. tax on turning RMB into dollars")
    print("=" * 72)
    check_files()
    if FAIL:
        print("\n".join(FAIL))
        return 1
    src, urls = check_sources()
    flag_ids, _ = check_rows(src, urls)
    inp, sell, rate, ladder = check_ladder(urls)
    check_cross(inp, sell, rate)
    check_example(inp, sell, rate)
    check_page(urls, flag_ids, ladder, inp)
    check_hygiene()
    print("-" * 72)
    if FAIL:
        for f in FAIL[:40]:
            print("FAIL", f)
        print(f"{len(FAIL)} failure(s) in {CHECKS} checks")
        return 1
    print(f"PASS — {CHECKS} checks, 0 failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
