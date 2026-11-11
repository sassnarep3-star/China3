#!/usr/bin/env python3
"""Independent check of the 6da0 layer (session arena/6da06d4e-china3).

This file does not import scripts/build_6da0.py. It reads only what was published
(data/6da0_*.csv and 6da0-settle-up.html) and re-derives everything from there.

Checks
------
A. Sources      every passage is on an official domain, dated, quoted, and has a unique id.
B. Inputs       every number used in a calculation is tied to a source, the tying words appear
                character for character in that source's quotation, and the number equals what
                those words mean (this file keeps its own table of meanings).
C. Ladder       40 rows, $10,000 to $400,000 in $10,000 steps; every cell recomputed here with
                separate code; sanity relations hold.
D. Rows         every rule, step and flag row cites a registered source; a blank value always
                carries a flag that exists; a flag row always has a severity.
E. Page         mobile viewport, no scripts, no external assets; every table row carries an
                official link; every "not verified" points at a published flag; every flag is
                published; every internal link and anchor resolves; row counts match the data;
                every ladder cell on the page equals the data.
F. Freshness    the committed files equal a fresh build.

Exit status 0 = all checks pass. No third-party dependencies, no network access.
"""
from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal as D, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent.parent
# --self-test points this at a scratch copy of the repository to prove that each check can fail.
ROOT = Path(os.environ["SIXDA0_ROOT"]) if os.environ.get("SIXDA0_ROOT") else HERE
PAGE = ROOT / "6da0-settle-up.html"
READ_ON = "2026-11-11"

OFFICIAL = (
    "chinatax.gov.cn",      # State Taxation Administration (incl. fgk. policy database, provincial bureaus)
    "npc.gov.cn",           # National People's Congress
    "stats.gov.cn",         # National Bureau of Statistics (publishes national laws)
    "mofcom.gov.cn",        # Ministry of Commerce policy database
    "safe.gov.cn",          # State Administration of Foreign Exchange
    "boc.cn",               # Bank of China
    "irs.gov",              # Internal Revenue Service (incl. taxpayeradvocate.irs.gov)
    "govinfo.gov",          # U.S. Government Publishing Office
    "ecfr.gov",             # Electronic Code of Federal Regulations
    "supremecourt.gov",     # Supreme Court of the United States
)
REPO_HOST_PATH = ("github.com", "/sassnarep3-star/China3")

FAILS: list[str] = []
PASSES = 0


def ok(msg: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  ok   {msg}")


def fail(msg: str) -> None:
    FAILS.append(msg)
    print(f"  FAIL {msg}")


def read_csv(name: str) -> list[dict]:
    with (ROOT / "data" / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def official(url: str) -> bool:
    u = urlparse(url)
    host = (u.hostname or "").lower()
    return u.scheme in ("http", "https") and any(host == d or host.endswith("." + d) for d in OFFICIAL)


# ------------------------------------------------------------------------- A. sources
def check_sources():
    print("A. sources")
    rows = read_csv("6da0_sources.csv")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        fail("A: duplicate source id")
    bad = [r["id"] for r in rows if not official(r["url"])]
    if bad:
        fail(f"A: source not on an official domain: {bad}")
    for r in rows:
        if r["read_on"] != READ_ON:
            fail(f"A: {r['id']} read_on is {r['read_on']!r}")
        if r["read"] not in ("full", "excerpt"):
            fail(f"A: {r['id']} read is {r['read']!r}")
        if len(r["quote"].strip()) < 10:
            fail(f"A: {r['id']} has no quotation")
        if not r["plain_english_ours"].strip() or not r["document"].strip() or not r["issuer"].strip():
            fail(f"A: {r['id']} is missing its issuer, document or plain-English line")
        if r["side"] not in ("China", "U.S."):
            fail(f"A: {r['id']} side is {r['side']!r}")
    if not [f for f in FAILS if f.startswith("A:")]:
        n_full = sum(1 for r in rows if r["read"] == "full")
        ok(f"{len(rows)} passages on {len({r['url'] for r in rows})} official pages; {n_full} read on the page, "
           f"{len(rows) - n_full} as excerpts; all dated {READ_ON} and quoted")
    return {r["id"]: r for r in rows}


# -------------------------------------------------------------------------- B. inputs
# What the quoted words mean, kept here so that a typo in the builder's number is caught.
MEANING = {
    "万分之五": D("0.0005"),                       # five per ten thousand
    "百分之五十": D("0.5"),                        # fifty per cent
    "五倍": D("5"),                                # five times
    "百分之二十": D("0.20"),                       # twenty per cent
    "六万元": D("60000"),                          # sixty thousand yuan
    "5 percent of the highest aggregate balance/value": D("0.05"),
    "50 percent": D("0.5"),
    "will not be subject to failure-to-file and failure-to-pay penalties": D("0"),
}


def check_inputs(src):
    print("B. inputs")
    rows = read_csv("6da0_inputs.csv")
    inp = {}
    for r in rows:
        i, token = r["id"], r["token_in_quote"]
        if r["source_id"] not in src:
            fail(f"B: {i} cites unknown source {r['source_id']}")
            continue
        s = src[r["source_id"]]
        if r["source_url"] != s["url"]:
            fail(f"B: {i} source_url differs from the register")
        if not token or token not in s["quote"]:
            fail(f"B: {i}: the words {token!r} are not in the quotation of {r['source_id']}")
            continue
        value = r["value"]
        if i.startswith("bracket_"):
            upper, rate = value.split("|")
            # token looks like "超过36000元至144000元的部分 · 10" or "不超过36000元的 · 3" or "超过960000元的部分 · 45"
            left, _, right = token.partition(" · ")
            if right.strip() != rate:
                fail(f"B: {i}: rate {rate} is not the rate in {token!r}")
            nums = re.findall(r"\d+", left)
            if upper:
                if not nums or nums[-1] != upper:
                    fail(f"B: {i}: upper limit {upper} is not the limit in {token!r}")
            elif "至" in left or "不超过" in left:
                fail(f"B: {i}: the top level must have no upper limit, but {token!r} has one")
            inp[i] = (D(upper) if upper else None, D(rate) / 100)
            continue
        if token in MEANING:
            if D(value) != MEANING[token]:
                fail(f"B: {i}: value {value} does not equal what {token!r} means ({MEANING[token]})")
        else:
            # plain numeric tokens such as "16,536" or "669.1": the token itself is the number
            if D(token.replace(",", "")) != D(value):
                fail(f"B: {i}: value {value} differs from the quoted figure {token!r}")
        inp[i] = D(value)
    needed = {"surcharge_daily", "fine_min_multiple", "fine_max_multiple", "flat_rate", "standard_deduction",
              "boc_usd_sell_per_100", "sfop_penalty_rate", "sdop_penalty_rate", "fbar_nonwillful_cap",
              "fbar_willful_floor", "fbar_willful_share"} | {f"bracket_{n}" for n in range(1, 8)}
    missing = needed - set(inp)
    if missing:
        fail(f"B: inputs missing or rejected: {sorted(missing)}")
    if not [f for f in FAILS if f.startswith("B:")]:
        ok(f"{len(rows)} inputs; each tying phrase is in its quotation and each value equals what the phrase says")
    return inp


# -------------------------------------------------------------------------- C. ladder
def cents(x: D) -> D:
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def progressive(taxable: D, levels) -> D:
    """Sum, level by level, of (slice of income inside the level) x (the level's rate)."""
    if taxable <= 0:
        return D(0)
    total, floor = D(0), D(0)
    for ceiling, rate in levels:
        top = taxable if ceiling is None else min(taxable, ceiling)
        if top > floor:
            total += (top - floor) * rate
        if ceiling is None or taxable <= ceiling:
            break
        floor = ceiling
    return total


def expected_row(a: D, inp) -> dict:
    levels = [inp[f"bracket_{n}"] for n in range(1, 8)]
    day = inp["surcharge_daily"]
    tax = a * inp["flat_rate"]
    fx = inp["boc_usd_sell_per_100"] / D(100)
    yuan = a * fx
    one = progressive(yuan - inp["standard_deduction"], levels)
    five = D(5) * progressive(yuan / D(5) - inp["standard_deduction"], levels)
    return {
        "cn20_tax_usd": cents(tax),
        "cn20_tax_plus_surcharge_1y_usd": cents(tax + tax * day * 365),
        "cn20_tax_plus_surcharge_3y_usd": cents(tax + tax * day * 365 * 3),
        "cn20_tax_plus_surcharge_5y_usd": cents(tax + tax * day * 365 * 5),
        "cn20_fine_min_usd": cents(tax * inp["fine_min_multiple"]),
        "cn20_fine_max_usd": cents(tax * inp["fine_max_multiple"]),
        "rmb_at_boc_sell": cents(yuan),
        "wage_tax_one_year_rmb": cents(one),
        "wage_tax_one_year_usd": cents(one / fx),
        "wage_tax_one_year_pct": cents(one / yuan * 100),
        "wage_tax_five_years_rmb": cents(five),
        "wage_tax_five_years_usd": cents(five / fx),
        "wage_tax_five_years_pct": cents(five / yuan * 100),
        "wage_surcharge_per_year_on_one_year_tax_usd": cents(one / fx * day * 365),
        "us_streamlined_foreign_usd": cents(a * inp["sfop_penalty_rate"]),
        "us_streamlined_domestic_usd": cents(a * inp["sdop_penalty_rate"]),
        "us_fbar_nonwillful_cap_per_report_usd": cents(inp["fbar_nonwillful_cap"]),
        "us_fbar_willful_cap_per_violation_usd": cents(max(inp["fbar_willful_floor"], a * inp["fbar_willful_share"])),
    }


def check_ladder(src, inp):
    print("C. ladder")
    rows = read_csv("6da0_ladder.csv")
    want = [str(a) for a in range(10000, 400001, 10000)]
    got = [r["amount_usd"] for r in rows]
    if got != want:
        fail(f"C: amounts are not $10,000..$400,000 in $10,000 steps ({len(got)} rows)")
        return rows
    cells = 0
    for r in rows:
        exp = expected_row(D(r["amount_usd"]), inp)
        extra = set(r) - set(exp) - {"amount_usd", "source_ids", "source_urls"}
        if extra:
            fail(f"C: unexpected columns {sorted(extra)}")
        for col, value in exp.items():
            cells += 1
            if col not in r or D(r[col]) != value:
                fail(f"C: ${r['amount_usd']} {col}: file has {r.get(col)}, recomputed {value}")
        ids = r["source_ids"].split("|")
        if not ids or any(i not in src for i in ids):
            fail(f"C: ${r['amount_usd']} cites an unknown source")
        if r["source_urls"].split() != list(dict.fromkeys(src[i]["url"] for i in ids if i in src)):
            fail(f"C: ${r['amount_usd']} source_urls do not match its source ids")
    # sanity relations that must hold whatever the inputs are
    num_cols = [c for c in rows[0] if c not in ("source_ids", "source_urls")]
    for prev, cur in zip(rows, rows[1:]):
        for c in num_cols:
            if D(cur[c]) < D(prev[c]):
                fail(f"C: {c} falls between ${prev['amount_usd']} and ${cur['amount_usd']}")
    for r in rows:
        if D(r["wage_tax_five_years_rmb"]) > D(r["wage_tax_one_year_rmb"]):
            fail(f"C: ${r['amount_usd']}: spreading wages over five years cannot cost more than one year")
        if D(r["cn20_fine_max_usd"]) != D(r["cn20_fine_min_usd"]) * 10:
            fail(f"C: ${r['amount_usd']}: 5x fine is not ten times the 0.5x fine")
        if D(r["us_fbar_willful_cap_per_violation_usd"]) < inp["fbar_willful_floor"]:
            fail(f"C: ${r['amount_usd']}: willful ceiling is below the fixed-dollar amount")
    if not [f for f in FAILS if f.startswith("C:")]:
        ok(f"{len(rows)} rows x {len(num_cols) - 1} figures = {cells} cells recomputed and equal; "
           f"monotonic; five-year wage tax never above one-year")
    return rows


# ---------------------------------------------------------------------------- D. rows
def check_rows(src):
    print("D. rule, step and flag rows")
    flags = read_csv("6da0_flags.csv")
    flag_ids = {f["id"] for f in flags}
    for f in flags:
        if f["severity"] not in ("high", "medium", "low"):
            fail(f"D: flag {f['id']} severity {f['severity']!r}")
        for col in ("item", "why", "what_would_settle_it"):
            if not f[col].strip():
                fail(f"D: flag {f['id']} has an empty {col}")
    rules, steps = read_csv("6da0_rules.csv"), read_csv("6da0_steps.csv")
    blanks = 0
    for name, rows, key in (("rule", rules, "id"), ("step", steps, "step"), ("flag", flags, "id")):
        for r in rows:
            ids = [i for i in r["source_ids"].split("|") if i]
            if not ids:
                fail(f"D: {name} {r[key]} has no source")
            unknown = [i for i in ids if i not in src]
            if unknown:
                fail(f"D: {name} {r[key]} cites unknown source {unknown}")
            urls = r["source_urls"].split()
            if not urls or any(not official(u) for u in urls):
                fail(f"D: {name} {r[key]} has a missing or non-official source link")
            if urls != list(dict.fromkeys(src[i]["url"] for i in ids if i in src)):
                fail(f"D: {name} {r[key]} source_urls do not match its source ids")
    for r in rules:
        if not r["value"].strip():
            blanks += 1
            if r["flag_if_blank"] not in flag_ids:
                fail(f"D: rule {r['id']} is blank but has no published flag")
        elif r["flag_if_blank"]:
            fail(f"D: rule {r['id']} has both a value and a blank-flag")
    if len({r["id"] for r in rules}) != len(rules):
        fail("D: duplicate rule id")
    if not [f for f in FAILS if f.startswith("D:")]:
        ok(f"{len(rules)} rules, {len(steps)} steps, {len(flags)} flags: every row sourced on an official page; "
           f"{blanks} blank values, each with a flag")
    return rules, steps, flags


# ---------------------------------------------------------------------------- E. page
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.hrefs, self.scripts, self.styles, self.assets = [], [], 0, [], []
        self.viewport = False
        self.tables = []          # list of {"head": [...], "rows": [{"id":, "cells": [...], "links": [...], "blank": [...]}]}
        self._t = self._row = self._cell = None
        self._in_thead = False
        self._blank_open = False
        self._expect_flag_link = None
        self.blank_targets = []   # flag ids that a "not verified" marker points at
        self.blank_orphans = 0
        self.h2 = []
        self._h2 = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "script":
            self.scripts += 1
        if tag == "meta" and a.get("name") == "viewport" and "width=device-width" in a.get("content", ""):
            self.viewport = True
        if tag == "link" and a.get("rel") == "stylesheet":
            self.styles.append(a.get("href", ""))
        if tag in ("img", "iframe", "video", "audio", "object", "embed", "source"):
            self.assets.append(a.get("src", ""))
        if tag == "h2":
            self._h2 = ""
        if tag == "table":
            self._t = {"kind": a.get("data-kind", ""), "cls": a.get("class", ""), "head": [], "rows": []}
        elif tag == "thead":
            self._in_thead = True
        elif tag == "tr" and self._t is not None and not self._in_thead:
            self._row = {"id": a.get("id", ""), "cells": [], "links": [], "blank": 0}
        elif tag in ("td", "th") and self._t is not None:
            self._cell = ""
        if tag == "span" and "blank" in a.get("class", "").split():
            self._blank_open = True
            if self._row is not None:
                self._row["blank"] += 1
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
            if self._row is not None:
                self._row["links"].append(a["href"])
            if self._expect_flag_link:
                if a["href"].startswith("#"):
                    self.blank_targets.append(a["href"][1:])
                else:
                    self.blank_orphans += 1
                self._expect_flag_link = None

    def handle_endtag(self, tag):
        if tag == "span" and self._blank_open:
            self._blank_open = False
            self._expect_flag_link = True
        if tag == "h2" and self._h2 is not None:
            self.h2.append(self._h2.strip())
            self._h2 = None
        if tag == "thead":
            self._in_thead = False
        elif tag in ("td", "th") and self._t is not None and self._cell is not None:
            text = re.sub(r"\s+", " ", self._cell).strip()
            if self._in_thead:
                self._t["head"].append(text)
            elif self._row is not None:
                self._row["cells"].append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._t["rows"].append(self._row)
            self._row = None
            if self._expect_flag_link:
                self.blank_orphans += 1
                self._expect_flag_link = None
        elif tag == "table" and self._t is not None:
            self.tables.append(self._t)
            self._t = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell += data
        if self._h2 is not None:
            self._h2 += data


def money(x) -> str:
    return f"${D(x).quantize(D('1'), rounding=ROUND_HALF_UP):,}"


def yuan(x) -> str:
    return f"¥{D(x).quantize(D('1'), rounding=ROUND_HALF_UP):,}"


def check_page(src, ladder, rules, steps, flags):
    print("E. page")
    if not PAGE.exists():
        fail("E: 6da0-settle-up.html is missing")
        return
    text = PAGE.read_text(encoding="utf-8")
    p = Page()
    p.feed(text)
    if not p.viewport:
        fail("E: no mobile viewport meta tag")
    if p.scripts:
        fail(f"E: page contains {p.scripts} script element(s)")
    if p.assets:
        fail(f"E: page embeds external media: {p.assets[:3]}")
    for href in p.styles:
        if "://" in href or not (ROOT / href).exists():
            fail(f"E: stylesheet {href!r} is external or missing")
    if len(p.ids) != len(set(p.ids)):
        dup = sorted({i for i in p.ids if p.ids.count(i) > 1})
        fail(f"E: duplicate element ids {dup[:5]}")
    ids = set(p.ids)

    # links
    n_ext = n_int = 0
    for href in p.hrefs:
        if href.startswith("#"):
            n_int += 1
            if href[1:] not in ids:
                fail(f"E: anchor {href} does not exist on the page")
        elif "://" in href:
            n_ext += 1
            u = urlparse(href)
            is_repo = (u.hostname or "") == REPO_HOST_PATH[0] and u.path.rstrip("/") == REPO_HOST_PATH[1]
            if not (official(href) or is_repo):
                fail(f"E: external link is not on an official domain: {href}")
        else:
            n_int += 1
            path, _, frag = href.partition("#")
            target = ROOT / path
            if not target.exists():
                fail(f"E: local link {href} points at a missing file")
            elif frag and target.suffix == ".html":
                if not re.search(r'id="' + re.escape(frag) + '"', target.read_text(encoding="utf-8", errors="replace")):
                    fail(f"E: local link {href}: anchor not found in the target page")
    source_urls = {s["url"] for s in src.values()}
    unknown = {h for h in p.hrefs if "://" in h and official(h)} - source_urls
    if unknown:
        fail(f"E: official link on the page is not in the source register: {sorted(unknown)[:3]}")

    # every data row carries an official link; blanks point at published flags
    data_tables = [t for t in p.tables if t["kind"] == "data"]
    n_rows = 0
    for t in data_tables:
        if not t["head"] or t["head"][-1] not in ("Source", "Link"):
            fail(f"E: a table's last column is {t['head'][-1:]} instead of the source column")
        for r in t["rows"]:
            n_rows += 1
            if not any(official(h) for h in r["links"]):
                fail(f"E: table row without an official source link: {r['cells'][:1]}")
            if len(r["cells"]) != len(t["head"]):
                fail(f"E: row has {len(r['cells'])} cells for {len(t['head'])} columns: {r['cells'][:1]}")
    flag_ids = {f["id"] for f in flags}
    if p.blank_orphans:
        fail(f"E: {p.blank_orphans} 'not verified' marker(s) with no flag link beside them")
    for target in p.blank_targets:
        if target not in flag_ids or target not in ids:
            fail(f"E: 'not verified' points at {target}, which is not a published flag")
    n_blank_rules = sum(1 for r in rules if not r["value"].strip())
    if len(p.blank_targets) != n_blank_rules:
        fail(f"E: {len(p.blank_targets)} blank markers on the page, {n_blank_rules} blank values in the data")
    for f in flag_ids:
        if f not in ids:
            fail(f"E: flag {f} is not published on the page")
    if "Flagged for review" not in p.h2:
        fail("E: no 'Flagged for review' section heading")

    # row-count parity with the data
    by_first = {}
    for t in data_tables:
        by_first.setdefault(t["head"][0], []).append(t)

    def rows_of(first_header):
        return [r for t in by_first.get(first_header, []) for r in t["rows"]]

    expect = {
        "Case": sum(1 for r in rules if r["group"] == "Which case"),
        "Layer": sum(1 for r in rules if r["group"] == "China"),
        "Item": sum(1 for r in rules if r["group"] == "What comes back") + len(flags),
        "Your situation": sum(1 for r in rules if r["group"] == "U.S. procedure"),
        "Rule": sum(1 for r in rules if r["group"] == "U.S."),
        "Step": len(steps),
        "Passage": len(src),
        "Input": len(read_csv("6da0_inputs.csv")),
        "Untaxed income": 45, "Wages": 45, "Highest year-end balance": 45,
    }
    for head, n in expect.items():
        if len(rows_of(head)) != n:
            fail(f"E: table '{head}' has {len(rows_of(head))} rows, data has {n}")
    for r in rules + [{"id": f"STEP-{s['step']}"} for s in steps] + [{"id": f"SRC-{i}"} for i in src]:
        if r["id"] not in ids:
            fail(f"E: row {r['id']} is in the data but has no anchor on the page")

    # ladder parity: every one of the 40 rows, every cell, in all three tables
    lad = {money(r["amount_usd"]): r for r in ladder}
    seen = {"Untaxed income": set(), "Wages": set(), "Highest year-end balance": set()}
    for head in seen:
        for r in rows_of(head):
            c = r["cells"]
            d = lad.get(c[0])
            if d is None:
                fail(f"E: ladder row {c[0]} is not in the data")
                continue
            seen[head].add(c[0])
            if head == "Untaxed income":
                want = [money(d["cn20_tax_usd"]), money(d["cn20_tax_plus_surcharge_1y_usd"]),
                        money(d["cn20_tax_plus_surcharge_3y_usd"]), money(d["cn20_tax_plus_surcharge_5y_usd"]),
                        f'{money(d["cn20_fine_min_usd"])} to {money(d["cn20_fine_max_usd"])}']
            elif head == "Wages":
                want = [yuan(d["rmb_at_boc_sell"]),
                        f'{money(d["wage_tax_one_year_usd"])} ({D(d["wage_tax_one_year_pct"]):.2f}%)',
                        f'{money(d["wage_tax_five_years_usd"])} ({D(d["wage_tax_five_years_pct"]):.2f}%)',
                        money(d["wage_surcharge_per_year_on_one_year_tax_usd"])]
            else:
                want = [money(d["us_streamlined_foreign_usd"]), money(d["us_streamlined_domestic_usd"]),
                        money(d["us_fbar_nonwillful_cap_per_report_usd"]), money(d["us_fbar_willful_cap_per_violation_usd"])]
            if c[1:-1] != want:
                fail(f"E: {head} {c[0]}: page shows {c[1:-1]}, data gives {want}")
        if len(seen[head]) != 40:
            fail(f"E: table '{head}' shows {len(seen[head])} of the 40 amounts")
    if not [f for f in FAILS if f.startswith("E:")]:
        ok(f"{n_rows} table rows, each with an official link; {len(p.blank_targets)} blanks, each pointing at a published "
           f"flag; {len(flag_ids)} flags published; {n_ext} external and {n_int} internal links resolve; "
           f"135 ladder rows equal the data; viewport set, no scripts, no external assets")


# ----------------------------------------------------------------------- F. freshness
def check_fresh():
    print("F. freshness")
    if ROOT != HERE:
        print("  skip (self-test copy)")
        return
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_6da0.py"), "--check"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"F: {(r.stdout or r.stderr).strip()[-300:]}")
    else:
        ok(r.stdout.strip())


# ------------------------------------------------------------------------- self-test
def self_test() -> int:
    """Break one thing at a time in a scratch copy and require the matching check to fail.

    A check that cannot fail proves nothing, so each of the checks A to E is shown to bite.
    """
    def sub(old, new, count=1):
        def f(text):
            if old not in text:
                raise AssertionError(f"self-test fixture not found: {old[:50]!r}")
            return text.replace(old, new, count)
        return f

    def drop_line(marker):
        def f(text):
            lines = text.split("\n")
            kept = [l for l in lines if not l.startswith(marker)]
            if len(kept) == len(lines):
                raise AssertionError(f"self-test fixture not found: {marker!r}")
            return "\n".join(kept)
        return f

    cases = [
        ("A", "a source moved to a non-official domain", "data/6da0_sources.csv",
         sub("https://www.safe.gov.cn/tianjin/2026/0713/3088.html", "https://example.com/3088.html")),
        ("B", "an input changed without its quotation changing", "data/6da0_inputs.csv",
         sub("surcharge_daily,0.0005,", "surcharge_daily,0.0006,")),
        ("B", "a quotation edited so the tying words disappear", "data/6da0_sources.csv",
         sub("按日加收滞纳税款万分之五的滞纳金", "按日加收滞纳税款万分之三的滞纳金")),
        ("C", "one ladder cell off by a cent", "data/6da0_ladder.csv",
         sub("10000,2000.00,", "10000,2000.01,")),
        ("D", "a flag deleted while a blank still points at it", "data/6da0_flags.csv", drop_line("F03,")),
        ("D", "a rule row with its sources removed", "data/6da0_rules.csv",
         sub("R06,China,Fine for never filing,50% to 5 times the unpaid tax.,,Added to the tax and the surcharge.,C01.64,",
             "R06,China,Fine for never filing,50% to 5 times the unpaid tax.,,Added to the tax and the surcharge.,,")),
        ("E", "a ladder figure changed on the page only", "6da0-settle-up.html", sub(">$94,600<", ">$94,601<")),
        ("E", "a 'not verified' marker with its flag link removed", "6da0-settle-up.html",
         sub('<span class="blank">not verified</span> <a href="#F02">F02</a>', '<span class="blank">not verified</span>')),
        ("E", "an external link to a non-official site", "6da0-settle-up.html",
         sub('<p class="crumb">', '<p class="crumb"><a href="https://example.com/">x</a> ')),
        ("E", "a script element added", "6da0-settle-up.html", sub("</main>", "<script>1</script></main>")),
    ]
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "repo"
        shutil.copytree(HERE, base, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        env = dict(os.environ, SIXDA0_ROOT=str(base))
        run = lambda: subprocess.run([sys.executable, str(Path(__file__).resolve())], env=env, capture_output=True, text=True)
        clean = run()
        if clean.returncode != 0:
            print("  FAIL the untouched copy does not pass, so the self-test cannot start")
            print(clean.stdout[-600:])
            return 1
        print("  ok   untouched copy passes")
        for letter, what, rel, mutate in cases:
            path = base / rel
            original = path.read_text(encoding="utf-8")
            path.write_text(mutate(original), encoding="utf-8")
            r = run()
            path.write_text(original, encoding="utf-8")
            bites = r.returncode != 0 and f"FAIL {letter}:" in r.stdout
            failed += not bites
            print(f"  {'ok  ' if bites else 'FAIL'} check {letter} rejects {what}")
    print("self-test " + ("PASS" if not failed else "FAIL") + f" — {len(cases)} deliberate faults, {len(cases) - failed} caught")
    return 1 if failed else 0


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()
    print("6da0 verification — settling up unpaid tax")
    for name in ("6da0_sources.csv", "6da0_inputs.csv", "6da0_ladder.csv", "6da0_rules.csv", "6da0_steps.csv", "6da0_flags.csv"):
        if not (ROOT / "data" / name).exists():
            print(f"FAIL — data/{name} is missing")
            return 1
    src = check_sources()
    inp = check_inputs(src)
    if [f for f in FAILS if f.startswith("B:")]:
        print(f"FAIL — {len(FAILS)} problem(s); the ladder was not checked because the inputs were rejected")
        return 1
    ladder = check_ladder(src, inp)
    rules, steps, flags = check_rows(src)
    check_page(src, ladder, rules, steps, flags)
    check_fresh()
    if FAILS:
        print(f"FAIL — {len(FAILS)} problem(s)")
        return 1
    print(f"PASS — 6da0: {PASSES} check groups, 0 failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
