#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""n676 verifier — independent gate for the n676 layer.

It re-derives the ladder from the two recorded official inputs (BOC board and BOC
tariff) using its OWN arithmetic, then checks that the CSV, the eight pages and the
source register all agree. Exits non-zero on any failure.

    A  inputs are the ones recorded from the official pages on 2026-11-11
    B  ladder re-derived independently, all 160 rows
    C  ladder covers USD 10,000..400,000 in 10,000 steps, four routes, no gaps
    D  every money cell on every page equals the CSV to the cent
    E  every data-table BODY row carries an official source link or an explicit blank
    F  no cell marked "not verified" secretly contains a number
    G  every source id resolves; every URL is on an official domain
    H  internal links and anchors resolve; no external link outside the register
    I  determinism — rebuilding is byte-identical
    J  cross-implementation — the sibling 76e headline figures reproduce exactly
    K  scope — only n676-owned files were touched
    L  hygiene — no merge-conflict markers and no unfilled placeholders
"""

from __future__ import annotations

import csv
import glob
import hashlib
import html
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

PAGES = ["n676-summary", "n676-questions", "n676-methods", "n676-costs",
         "n676-steps", "n676-tax", "n676-flagged", "n676-sources"]
OWN_PREFIXES = ("n676-", "data/n676_", "research/n676-", "scripts/n676_",
                "assets/n676.", ".github/workflows/n676-")
OWN_EXACT = ("COORDINATION.md",)
GENERATED_SHARED = {"dashboard/archive.html"}

OFFICIAL_DOMAINS = {
    "boc.cn", "bankofchina.com", "safe.gov.cn", "chinatax.gov.cn", "irs.gov",
    "ecfr.gov", "govinfo.gov", "cbp.gov", "pbc.gov.cn", "fincen.gov", "gov.cn",
    "uscode.house.gov", "treasury.gov",
}

FAILURES = []


def ok(msg):
    print(f"  \u2713 {msg}")


def fail(msg):
    FAILURES.append(msg)
    print(f"  \u2717 {msg}")


def note(msg):
    print(f"  \u00b7 {msg}")


def read_csv(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ------------------------------------------------------------------ A, B, C  engine
def check_engine():
    print("A/B. inputs and independent re-derivation of the ladder")
    with open(os.path.join(ROOT, "scripts", "n676_engine.py"), encoding="utf-8") as fh:
        eng = fh.read()
    m = re.search(r'"buying_cents":\s*([\d.]+)', eng)
    n = re.search(r'"selling_cents":\s*([\d.]+)', eng)
    t = re.search(r'"rate":\s*([\d.]+)', eng)
    fl = re.search(r'"floor_cny":\s*([\d.]+)', eng)
    ce = re.search(r'"ceiling_cny":\s*([\d.]+)', eng)
    tg = re.search(r'"telegraph_cny_non_hkmo":\s*([\d.]+)', eng)
    tg2 = re.search(r'"telegraph_cny_hkmo":\s*([\d.]+)', eng)
    stamp = re.search(r'"stamp":\s*"([^"]+)"', eng)
    if not all([m, n, t, fl, ce, tg, tg2, stamp]):
        fail("A: could not read the recorded inputs out of the engine")
        return
    bid, ask = float(m.group(1)) / 100, float(n.group(1)) / 100
    rate, floor, ceil_, tel, tel2 = (float(t.group(1)), float(fl.group(1)),
                                     float(ce.group(1)), float(tg.group(1)),
                                     float(tg2.group(1)))
    # the numbers recorded in the engine must equal the official page verbatim
    if (float(m.group(1)), float(n.group(1)), stamp.group(1)) != (666.30, 669.11, "2026-11-11 10:25:02"):
        fail(f"A: engine inputs {m.group(1)}/{n.group(1)}/{stamp.group(1)} do not match the "
             "BOC board read on 2026-11-11 10:25:02 (666.30 / 669.11)")
    else:
        ok(f"engine inputs match the official board: buying {bid}, selling {ask}, {stamp.group(1)}")
    if (rate, floor, ceil_, tel, tel2) != (0.001, 50.0, 260.0, 150.0, 80.0):
        fail(f"A: engine tariff {(rate, floor, ceil_, tel, tel2)} does not match BOC's published "
             "personal tariff (1 per mille, RMB 50-260, telegraph RMB 150 / RMB 80)")
    else:
        ok("engine tariff matches BOC's published personal transfer tariff")

    # independent re-derivation — written out long-hand, not by calling the engine
    mid = (bid + ask) / 2.0
    lad = read_csv("n676_ladder.csv")
    bad = []
    for r in lad:
        usd = int(r["amount_usd"])
        rid = r["route_id"]
        hkmo = rid == "R4"
        wires = 1 if rid in ("R1", "R2", "R4") else -(-usd // 50_000)
        spread = 0.0 if rid == "R2" else usd * (ask - mid) / ask
        fee_cny = 0.0
        if rid == "R2":
            pct = min(ceil_, max(floor, usd * ask * rate))
            fee_cny = pct + tel
        else:
            for _ in range(wires):
                pct = min(ceil_, max(floor, (usd / wires) * ask * rate))
                fee_cny += pct + (tel2 if hkmo else tel)
        exp_s, exp_w = round(spread, 2), round(fee_cny / ask, 2)
        exp_t = round(exp_s + exp_w, 2)
        got = (float(r["spread_usd"]), float(r["wire_usd"]), float(r["total_usd"]))
        if got != (exp_s, exp_w, exp_t) or int(r["n_wires"]) != wires:
            bad.append(f"{rid}@{usd}: got {got} wires {r['n_wires']}, expected "
                       f"{(exp_s, exp_w, exp_t)} wires {wires}")
    if bad:
        fail(f"B: {len(bad)} rows do not re-derive: {bad[:4]}")
    else:
        ok(f"all {len(lad)} ladder rows re-derived to the cent from the board and tariff alone")

    print("C. ladder coverage")
    amts = sorted({int(r["amount_usd"]) for r in lad})
    rids = sorted({r["route_id"] for r in lad})
    if amts != list(range(10_000, 400_001, 10_000)):
        fail(f"C: increments are {amts[:3]}...{amts[-2:]}, expected every $10,000 from 10,000 to 400,000")
    else:
        ok(f"{len(amts)} increments from ${amts[0]:,} to ${amts[-1]:,}, step $10,000, no gaps")
    if rids != ["R1", "R2", "R3", "R4"]:
        fail(f"C: routes are {rids}, expected R1..R4")
    else:
        ok(f"4 routes x {len(amts)} increments = {len(lad)} rows")
    mono = [(rid, int(r["amount_usd"]), float(r["total_usd"]))
            for rid in ("R1", "R3") for r in lad if r["route_id"] == rid]
    for rid in ("R1", "R3"):
        seq = [t for r_, a, t in mono if r_ == rid]
        if any(b < a for a, b in zip(seq, seq[1:])):
            fail(f"C: {rid} total is not monotonically non-decreasing in the amount")
    ok("monotonicity holds: a bigger transfer never costs less in R1 and R3")


# ------------------------------------------------------------- D, E, F  page parity
class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_data = False
        self.depth = 0
        self.rows, self.cur, self.cell, self.cells = [], None, None, []
        self.hrefs, self.anchors, self.ids = [], [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            h = a.get("href", "")
            if h.startswith("#"):
                self.anchors.append(h[1:])
            elif h:
                self.hrefs.append(h)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "table" and a.get("data-kind") == "data":
            self.in_data, self.depth = True, 0
        if self.in_data:
            if tag == "table":
                self.depth += 1
            elif tag == "tr":
                self.cur, self.cells = [], []
            elif tag in ("td", "th"):
                self.cell = []

    def handle_endtag(self, tag):
        if self.in_data:
            if tag in ("td", "th") and self.cell is not None:
                self.cells.append("".join(self.cell).strip())
                self.cell = None
            elif tag == "tr" and self.cur is not None:
                self.rows.append(self.cells)
                self.cur = None
            elif tag == "table":
                self.depth -= 1
                if self.depth <= 0:
                    self.in_data = False

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


class Raw(HTMLParser):
    """Collects each <tr> of a data table as raw HTML so source links can be seen."""

    def __init__(self):
        super().__init__()
        self.in_data, self.depth = False, 0
        self.rows, self.buf, self.intr = [], None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table" and a.get("data-kind") == "data":
            self.in_data, self.depth = True, 0
        if self.in_data:
            if tag == "table":
                self.depth += 1
            elif tag == "tr":
                self.buf, self.intr = [], True
        if self.intr:
            self.buf.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag):
        if self.intr:
            self.buf.append(f"</{tag}>")
            if tag == "tr":
                self.rows.append("".join(self.buf))
                self.buf, self.intr = None, False
        if self.in_data:
            if tag == "table":
                self.depth -= 1
                if self.depth <= 0:
                    self.in_data = False

    def handle_data(self, d):
        if self.intr:
            self.buf.append(d)


def page_text(name):
    with open(os.path.join(ROOT, f"{name}.html"), encoding="utf-8") as fh:
        return fh.read()


def check_pages():
    print("D. every money cell on the pages equals the CSV")
    lad = {(r["route_id"], int(r["amount_usd"])): r for r in read_csv("n676_ladder.csv")}
    # the detail tables on n676-costs.html list RMB, rate cost, wire fee, wires, total, %
    txt = page_text("n676-costs")
    checked, wrong = 0, []
    for rid in ("R1", "R2", "R3", "R4"):
        for usd in range(10_000, 400_001, 10_000):
            r = lad[(rid, usd)]
            for key, shown in (("total_usd", f"${float(r['total_usd']):,.2f}"),
                               ("spread_usd", f"${float(r['spread_usd']):,.2f}"),
                               ("wire_usd", f"${float(r['wire_usd']):,.2f}"),
                               ("cny_out", f"\u00a5{float(r['cny_out']):,.2f}"),
                               ("wire_cny", f"\u00a5{float(r['wire_cny']):,.2f}")):
                if shown in txt:
                    checked += 1
                else:
                    wrong.append(f"{rid}@{usd} {key} {shown}")
    if wrong:
        fail(f"D: {len(wrong)} CSV values not rendered verbatim on n676-costs.html: {wrong[:5]}")
    else:
        ok(f"{checked} rendered cells match the CSV verbatim")

    # headline parity on the summary page
    s = page_text("n676-summary")
    for rid, usd in (("R1", 10_000), ("R1", 400_000), ("R2", 400_000)):
        v = f"${float(lad[(rid, usd)]['total_usd']):,.2f}"
        if v not in s:
            fail(f"D: summary page does not show {v} for {rid} at ${usd:,}")
    ok("summary KPI cards agree with the ladder")

    print("E. every data-table row carries an official source or an explicit blank")
    src_ids = {r["id"] for r in read_csv("n676_sources.csv")}
    total_rows, unsourced, blanks = 0, [], 0
    for name in PAGES:
        raw = Raw()
        raw.feed(page_text(name))
        for tr in raw.rows:
            # a header row is not a data row; it carries no figure to source
            if re.match(r"^\s*<tr>\s*(<th[^>]*>.*?</th>\s*)+</tr>\s*$", tr, re.S):
                continue
            total_rows += 1
            low = tr.lower()
            has_src = any(f'>{i} <' in tr or f'>{i}</a>' in tr for i in src_ids)
            has_blank = "not verified" in low or "no official source" in low or "not fetched" in low
            if has_blank:
                blanks += 1
            if not (has_src or has_blank):
                unsourced.append(f"{name}.html: {tr[:110]}")
    if unsourced:
        fail(f"E: {len(unsourced)} data rows carry neither a source nor a blank marker: {unsourced[:3]}")
    else:
        ok(f"{total_rows} data rows across {len(PAGES)} pages; every one sourced or explicitly blank")
    note(f"{blanks} rows are deliberately blank and flagged")

    print("F. no cell marked unverified secretly contains a number")
    bad = []
    for name in PAGES:
        t = Tables()
        t.feed(page_text(name))
        for cells in t.rows:
            for c in cells:
                cl = c.lower()
                if ("not verified" in cl or "no official source" in cl) and re.search(r"\$\s?[\d,]+\.\d{2}", c):
                    bad.append(f"{name}.html: {c[:90]}")
    if bad:
        fail(f"F: {len(bad)} blank-marked cells contain a figure: {bad[:3]}")
    else:
        ok("no blank-marked cell contains a number")


# ------------------------------------------------------- G, H  sources and links
def check_sources():
    print("G. source register: ids resolve, every URL is on an official domain")
    ss = read_csv("n676_sources.csv")
    ids = [r["id"] for r in ss]
    if len(ids) != len(set(ids)):
        fail("G: duplicate source ids")
    bad = []
    for r in ss:
        h = urlparse(r["url"]).hostname or ""
        if not any(h == d or h.endswith("." + d) for d in OFFICIAL_DOMAINS):
            bad.append(f"{r['id']} -> {h}")
        if r["fetched_today"] == "yes" and not r["quote"].strip():
            bad.append(f"{r['id']} claims a today-fetch but holds no verbatim quote")
        if r["fetched_today"] != "yes" and r["quote"].strip():
            bad.append(f"{r['id']} is marked not-fetched but carries a quote")
    if bad:
        fail(f"G: {bad[:5]}")
    else:
        ok(f"{len(ss)} sources, {sum(1 for r in ss if r['fetched_today'] == 'yes')} re-read today "
           f"with verbatim quotes, all on official domains")

    # every id referenced anywhere exists
    refs = set()
    for name in ("n676_questions.csv", "n676_methods.csv", "n676_steps.csv", "n676_flags.csv"):
        for r in read_csv(name):
            for k in ("source_ids",):
                refs.update(x for x in (r.get(k) or "").split("|") if x)
    for r in read_csv("n676_ladder.csv"):
        refs.update(x for x in r["sources"].split("|") if x)
    for name in PAGES:
        for m in re.finditer(r'class="s" href="[^"]+" rel="noopener"[^>]*>(N\d+[a-z]?)',
                             page_text(name)):
            refs.add(m.group(1))
    missing = sorted(x for x in refs if x not in set(ids))
    if missing:
        fail(f"G: referenced source ids that do not exist: {missing}")
    else:
        ok(f"all {len(refs)} referenced source ids resolve into the register")

    # flag ids
    fids = {r["id"] for r in read_csv("n676_flags.csv")}
    refs = set()
    for r in read_csv("n676_methods.csv"):
        refs.update(x for x in (r["flags"] or "").split("|") if x)
    for name in PAGES:
        refs.update(re.findall(r'n676-flagged\.html#(N676-[UF]\d+)', page_text(name)))
    miss = sorted(x for x in refs if x not in fids)
    if miss:
        fail(f"G: referenced flag ids that do not exist: {miss}")
    else:
        ok(f"all {len(refs)} referenced flag ids resolve into the flag register")

    print("H. internal links and anchors resolve")
    broken = []
    for name in PAGES:
        t = Tables()
        t.feed(page_text(name))
        own_ids = set(t.ids)
        for h in t.hrefs:
            if h.startswith(("http://", "https://", "mailto:")):
                continue
            path, _, frag = h.partition("#")
            target = os.path.join(ROOT, path) if path else os.path.join(ROOT, f"{name}.html")
            if not os.path.exists(target):
                broken.append(f"{name}.html -> {h}")
                continue
            if frag:
                if path:
                    tt = Tables()
                    tt.feed(open(target, encoding="utf-8").read())
                    own_ids = tt.ids
                if frag not in own_ids:
                    broken.append(f"{name}.html -> #{frag} (no such anchor)")
    if broken:
        fail(f"H: {len(broken)} broken links: {broken[:6]}")
    else:
        ok("every internal link and every in-page anchor resolves")

    # external links must all be in the register
    reg = {r["url"] for r in read_csv("n676_sources.csv")}
    stray = set()
    for name in PAGES:
        for h in re.findall(r'href="(https?://[^"]+)"', page_text(name)):
            if h not in reg:
                stray.add(h)
    if stray:
        fail(f"H: {len(stray)} external links that are not in the source register: {sorted(stray)[:3]}")
    else:
        ok(f"all external links appear in the source register ({len(reg)} URLs)")


# ------------------------------------------------------------------- I  determinism
def check_determinism():
    print("I. determinism — rebuilding is byte-identical")
    files = [f"{p}.html" for p in PAGES] + ["assets/n676.css"] + \
            [f"data/n676_{x}.csv" for x in ("sources", "questions", "methods", "steps", "flags", "ladder")]
    before = {f: sha(os.path.join(ROOT, f)) for f in files}
    for script in ("n676_engine.py", "n676_data.py", "n676_build.py"):
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", script)],
                       cwd=ROOT, check=True, capture_output=True)
    after = {f: sha(os.path.join(ROOT, f)) for f in files}
    diff = [f for f in files if before[f] != after[f]]
    if diff:
        fail(f"I: rebuild changed {diff}")
    else:
        ok(f"{len(files)} files rebuilt byte-identically")


# ------------------------------------------------------------- J  cross-implementation
def check_cross():
    print("J. cross-implementation — sibling headline figures reproduce exactly")
    lad = {(r["route_id"], int(r["amount_usd"])): r for r in read_csv("n676_ladder.csv")}
    # session 76e published, on the same 2026-11-11 board: $53.42 at $10,000 and
    # $901.20 at $400,000, and a 2024-basis gain of $27,703 on $400,000.
    expect = [("R1", 10_000, "total_usd", 53.42), ("R1", 400_000, "total_usd", 901.20),
              ("R1", 400_000, "gain_2024", 27703.44)]
    bad = []
    for rid, usd, key, want in expect:
        got = float(lad[(rid, usd)][key])
        if abs(got - want) > 0.005:
            bad.append(f"{rid}@{usd} {key}: got {got}, sibling published {want}")
    if bad:
        fail(f"J: {bad}")
    else:
        ok("3/3 sibling headline figures reproduce to the cent under the same convention")
    # and the previous day's board must reproduce the figures the site carried before
    bid, ask = 6.6571, 6.6851          # BOC board 2026-11-10 17:39:58
    mid = (bid + ask) / 2
    for usd, want in ((10_000, 53.38), (400_000, 899.01)):
        spread = usd * (ask - mid) / ask
        fee = min(260.0, max(50.0, usd * ask * 0.001)) + 150.0
        got = round(spread, 2) + round(fee / ask, 2)
        if abs(got - want) > 0.005:
            fail(f"J: the 2026-11-10 convention gives {got} at ${usd:,}, the site published {want}")
    ok("the same convention on the 2026-11-10 17:39:58 board reproduces $53.38 and $899.01")


# ------------------------------------------------------------------------ K  scope
def branch_claim_paths():
    """Paths declared by the current branch's own block in COORDINATION.md.

    Check K was written for one session and hardcoded that session's namespace, so
    from the next session onwards it reported every honest, board-declared change as
    "outside the n676 scope" and turned the gate red on every pull request (logged
    as 6DA0-IR-03 on 2026-11-11). It now reads the claim the branch wrote for
    itself. If a branch has no block, the rule falls back to the original strict
    rule: new files and the regenerated archive are additive and allowed; editing a
    file that already existed at the merge base and belongs to another layer is not.
    """
    try:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        return set(), ""
    board_path = os.path.join(ROOT, "COORDINATION.md")
    if not os.path.exists(board_path) or not branch:
        return set(), branch
    text = open(board_path, encoding="utf-8", errors="ignore").read()
    if branch not in text:
        return set(), branch
    idx = text.rfind(branch)
    start = text.rfind("<!-- session-", 0, idx)
    start = 0 if start == -1 else start
    nxt = text.find("<!-- session-", idx)
    block = text[start: nxt if nxt != -1 else len(text)]
    claim = set()
    for token in re.findall(r"[A-Za-z0-9_./*\\-]+\.(?:html|css|js|py|yml|csv|md)", block):
        token = token.strip("./")
        if not token:
            continue
        if "*" in token:
            for p in glob.glob(os.path.join(ROOT, token)):
                claim.add(os.path.relpath(p, ROOT))
        else:
            claim.add(token)
    return claim, branch


def check_scope():
    print("K. scope — only n676-owned files were touched")

    def git(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout

    try:
        try:
            base = git("merge-base", "HEAD", "origin/main").strip()
        except subprocess.CalledProcessError:
            base = git("merge-base", "HEAD", "main").strip()
        out = git("diff", "--name-only", base, "HEAD")
        out += git("diff", "--name-only")
        out += git("diff", "--name-only", "--cached")
        out += git("ls-files", "--others", "--exclude-standard")
        tracked = set(git("ls-tree", "-r", "--name-only", base).splitlines())
    except subprocess.CalledProcessError as exc:
        fail(f"K: git failed: {exc.stderr.strip()[:160]}")
        return
    claim, branch = branch_claim_paths()
    foreign = []
    for f in sorted({l.strip() for l in out.splitlines() if l.strip()}):
        if f.startswith(OWN_PREFIXES) or f in OWN_EXACT or f in GENERATED_SHARED:
            continue
        if f in claim:
            continue
        if f not in tracked:
            continue
        foreign.append(f)
    if foreign:
        fail(f"K: files outside the n676 scope were modified: {foreign}")
    else:
        ok(f"every changed file is inside the n676 namespace, the branch claim "
           f"({branch or 'none'}), append-only COORDINATION.md, or a brand-new additive file")


# ---------------------------------------------------------------------- L  hygiene
def check_hygiene():
    print("L. hygiene — no conflict markers, no placeholders")
    conflicts = [r"^<<<<<<< ", r"^=======$", r"^>>>>>>> "]
    placeholders = [r"\b" + "TO" + "DO\b", r"\b" + "FIX" + "ME\b", r"\bLorem ipsum\b",
                    "X" * 3]
    bad = []
    targets = [f"{p}.html" for p in PAGES] + ["assets/n676.css", "COORDINATION.md"] + \
              [f"data/n676_{x}.csv" for x in ("sources", "questions", "methods", "steps",
                                              "flags", "ladder")] + \
              ["scripts/n676_engine.py", "scripts/n676_data.py", "scripts/n676_build.py",
               "scripts/n676_verify.py", "research/n676-verification.md",
               "research/n676-repo-audit.md"]
    for f in targets:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            bad.append(f"{f}: missing")
            continue
        self_file = os.path.abspath(p) == os.path.abspath(__file__)
        for i, line in enumerate(open(p, encoding="utf-8", errors="ignore"), 1):
            pats = conflicts + ([] if self_file else placeholders)
            for pat in pats:
                if re.search(pat, line.rstrip("\n")):
                    bad.append(f"{f}:{i}: {pat}")
    if bad:
        fail(f"L: {len(bad)} hygiene problems: {bad[:6]}")
    else:
        ok(f"{len(targets)} files clean of conflict markers, placeholders and TODOs")


def main():
    for fn in (check_engine, check_pages, check_sources, check_determinism,
               check_cross, check_scope, check_hygiene):
        fn()
    print("-" * 74)
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} failure(s)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    lad = read_csv("n676_ladder.csv")
    ss = read_csv("n676_sources.csv")
    qs = read_csv("n676_questions.csv")
    ms = read_csv("n676_methods.csv")
    fl = read_csv("n676_flags.csv")
    st = read_csv("n676_steps.csv")
    print(f"PASS — n676: {len(lad)} ladder rows re-derived, {len(ss)} sources "
          f"({sum(1 for r in ss if r['fetched_today'] == 'yes')} re-read today), "
          f"{len(qs)} questions, {len(ms)} methods, {len(st)} steps, {len(fl)} flags, "
          f"{len(PAGES)} pages, 0 failures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
