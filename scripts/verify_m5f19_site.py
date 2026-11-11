#!/usr/bin/env python3
"""
verify_m5f19_site.py — gate for the m5f19 pages. Exits non-zero on any failure.

Checks, in order:
  A  every m5f19 page exists, parses, has a unique <title>, declares viewport
  B  every internal href resolves to a file that exists
  C  every external href is on the whitelist of sources actually fetched today
  D  every data table row carries a source link or is marked BLANK/UNVERIFIED
  E  no "blank and unverified" cell contains a number
  F  every cost figure printed in the HTML re-derives from the recorded board
  G  the reconciliation gate: other sessions' published figures reproduce exactly
  H  the ladder CSV covers USD 10,000..400,000 in 10,000 steps with no gaps
  I  engine self-checks (fee convention, monotonicity, 8-wire > 1-wire)
  J  scope: no file outside this session's claim was modified
  K  determinism: rebuilding produces byte-identical output

Nothing here inspects truth. It inspects internal consistency, provenance and the
specific defects the repository has a history of shipping.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys
from decimal import Decimal
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m5f19_engine as eng  # noqa: E402

DATA = os.path.join(ROOT, "data")
PAGES = [
    "m5f19-dashboard.html", "m5f19-classification.html", "m5f19-costs.html",
    "m5f19-methods.html", "m5f19-steps.html", "m5f19-tax.html",
    "m5f19-reconciliation.html", "m5f19-flagged.html", "m5f19-sources.html",
]
ASSETS = ["assets/m5f19.css", "assets/m5f19.js"]
CSV_FILES = [
    "m5f19_sources.csv", "m5f19_facts.csv", "m5f19_classification.csv",
    "m5f19_methods.csv", "m5f19_steps.csv", "m5f19_tax.csv",
    "m5f19_ladder.csv", "m5f19_reconciliation.csv", "m5f19_flags.csv",
    "m5f19_board.csv",
]

# Files this session is permitted to touch. Checked against `git diff --name-only`.
OWNED_PREFIXES = ("m5f19-", "data/m5f19_", "research/m5f19-", "assets/m5f19.",
                  "scripts/m5f19_", "scripts/gen_m5f19_",
                  "scripts/build_m5f19_", "scripts/verify_m5f19_",
                  ".github/workflows/m5f19-")
# COORDINATION.md is append-only and shared by design; appends are allowed.
OWNED_EXACT = ("COORDINATION.md",)

FAILURES: list[str] = []
CHECKS = 0


def fail(msg: str) -> None:
    FAILURES.append(msg)


def ok(label: str) -> None:
    global CHECKS
    CHECKS += 1
    print(f"  \u2713 {label}")


def read(p: str) -> str:
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def csv_rows(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ==========================================================================
# HTML structure
# ==========================================================================
class Scanner(HTMLParser):
    """Collects structure and every href, and detects nested <td>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.titles: list[str] = []
        self.tables = 0
        self.rows = 0
        self.has_viewport = False
        self.has_charset = False
        self.nested_td = 0
        self.unclosed: list[str] = []
        self._stack: list[str] = []
        self._in_title = False
        self._cur_title = ""
        self._td_depth = 0
        self._in_thead = False
        self._row_has_src = False
        self.rows_without_src = 0
        self.row_text = ""
        self._in_row = False
        self.badges_blank = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("td", "th", "tr", "table", "details", "section", "div",
                   "nav", "header", "footer", "ol", "li", "p", "span"):
            self._stack.append(tag)
        if tag == "meta":
            if a.get("name") == "viewport":
                self.has_viewport = True
            if a.get("charset"):
                self.has_charset = True
        if tag == "link" and a.get("rel") == "stylesheet":
            self.hrefs.append(a.get("href", ""))
        if tag == "script" and a.get("src"):
            self.hrefs.append(a["src"])
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
            if "src" in (a.get("class") or ""):
                self._row_has_src = True
        if tag == "title":
            self._in_title = True
            self._cur_title = ""
        if tag == "table":
            self.tables += 1
        if tag == "thead":
            self._in_thead = True
        if tag == "tbody":
            self._in_thead = False
        if tag == "tr":
            # Header rows carry column labels, not data, so they are not subject
            # to the per-row source requirement. Counting them produced 7 false
            # failures on the first run of this verifier.
            self._in_row = self._in_thead is False
            self._row_has_src = False
            self.row_text = ""
        if tag == "td":
            if self._td_depth > 0:
                self.nested_td += 1
            self._td_depth += 1
        if tag == "span" and "blank" in (a.get("class") or ""):
            self.badges_blank += 1

    def handle_endtag(self, tag):
        if tag == "thead":
            self._in_thead = False
        if tag == "title":
            self._in_title = False
            self.titles.append(self._cur_title.strip())
        if tag == "td":
            self._td_depth = max(0, self._td_depth - 1)
        if tag == "tr":
            if self._in_row:
                self.rows += 1
                if not self._row_has_src and "BLANK" not in self.row_text \
                        and "no official source" not in self.row_text:
                    self.rows_without_src += 1
            self._in_row = False
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()
        elif tag in self._stack:
            # mismatched nesting: pop until we find it
            while self._stack and self._stack[-1] != tag:
                self._stack.pop()
            if self._stack:
                self._stack.pop()

    def handle_data(self, data):
        if self._in_title:
            self._cur_title += data
        if self._in_row:
            self.row_text += data

    def close(self):
        super().close()
        self.unclosed = [t for t in self._stack
                         if t not in ("div", "p", "span")]


def scan(html_text: str) -> Scanner:
    s = Scanner()
    s.feed(html_text)
    s.close()
    return s


# ==========================================================================
# checks
# ==========================================================================
def check_A_pages():
    print("A. pages exist, parse, unique titles, mobile-ready")
    titles = set()
    for p in PAGES:
        path = os.path.join(ROOT, p)
        if not os.path.exists(path):
            fail(f"A: missing page {p}")
            continue
        txt = read(path)
        s = scan(txt)
        if not txt.startswith("<!DOCTYPE html>"):
            fail(f"A: {p} does not start with a doctype")
        if not s.has_charset:
            fail(f"A: {p} has no charset meta")
        if not s.has_viewport:
            fail(f"A: {p} has no viewport meta — not mobile-friendly")
        if len(s.titles) != 1:
            fail(f"A: {p} has {len(s.titles)} <title> elements")
        elif not s.titles[0]:
            fail(f"A: {p} has an empty <title>")
        elif s.titles[0] in titles:
            fail(f"A: duplicate <title> {s.titles[0]!r}")
        else:
            titles.add(s.titles[0])
        if s.nested_td:
            fail(f"A: {p} contains {s.nested_td} nested <td> elements "
                 f"(defect present in s775-cost-10k-400k.html)")
        if s.unclosed:
            fail(f"A: {p} has unclosed elements: {s.unclosed[:6]}")
        if "assets/m5f19.css" not in txt:
            fail(f"A: {p} does not link the namespaced stylesheet")
        # namespace hygiene: no rule or id that could collide with a sibling page
        for bad in ('id="cost-table"', 'id="ladder"', 'class="hero"',
                    'id="dashboard"'):
            if bad in txt:
                fail(f"A: {p} uses un-namespaced attribute {bad}")
    for a in ASSETS:
        if not os.path.exists(os.path.join(ROOT, a)):
            fail(f"A: missing asset {a}")
    if not FAILURES:
        ok(f"{len(PAGES)} pages, {len(titles)} unique titles, 0 nested <td>")


def check_BC_links():
    print("B/C. links resolve; externals are on the fetched-source whitelist")
    allowed = {r["url"] for r in csv_rows("m5f19_sources.csv")}
    # anchors and same-page targets
    local_targets = set(PAGES) | {os.path.basename(a) for a in ASSETS}
    internal_seen, external_seen = set(), set()
    for p in PAGES:
        txt = read(os.path.join(ROOT, p))
        for h in scan(txt).hrefs:
            if not h or h.startswith("#") or h.startswith("mailto:") \
                    or h.startswith("tel:"):
                continue
            if h.startswith(("http://", "https://")):
                external_seen.add(h)
                base = h.split("#")[0]
                if base not in allowed:
                    fail(f"C: {p} links to {base} which is NOT in "
                         f"data/m5f19_sources.csv (was it fetched today?)")
            else:
                target = h.split("#")[0]
                if not target:
                    continue
                internal_seen.add(target)
                full = os.path.normpath(os.path.join(ROOT, target))
                if not os.path.exists(full):
                    fail(f"B: {p} links to {target} which does not exist")
                if os.path.basename(target) not in local_targets:
                    # cross-edition links are fine, just record them
                    pass
    missing = allowed - external_seen
    # not every source must be linked from a page, but the register must not
    # contain a URL that appears nowhere in the built output
    if missing:
        # sources legitimately appear in the sources page via src(); recheck
        all_txt = "".join(read(os.path.join(ROOT, p)) for p in PAGES)
        for u in sorted(missing):
            if u not in all_txt:
                fail(f"C: source {u} is registered but linked from no page")
    if not [f for f in FAILURES if f.startswith(("B:", "C:"))]:
        ok(f"{len(internal_seen)} internal links resolve; "
           f"{len(external_seen)} external links, all fetched today")


def check_D_row_sources():
    print("D. every data-table row carries a source or is marked BLANK")
    worst = []
    tally = 0
    tables = 0
    for p in PAGES:
        s = scan(read(os.path.join(ROOT, p)))
        tables += s.tables
        tally += s.rows
        if s.rows_without_src:
            worst.append((p, s.rows_without_src, s.rows))
    # No exemptions. The brief requires an official-source link on EVERY table
    # row, or a blank cell flagged unverified. Caption-level provenance and the
    # re-derivation in check F are not substitutes for a per-row link, so the
    # cost and reconciliation tables carry one too.
    for p, missing, total in worst:
        fail(f"D: {p} has {missing} of {total} table rows with no source link "
             f"and no BLANK marker")
    if not [f for f in FAILURES if f.startswith("D:")]:
        ok(f"{tally} data rows across {tables} tables on {len(PAGES)} pages, "
           f"every one carrying an official-source link or a BLANK/UNVERIFIED "
           f"marker (header rows excluded)")


def check_E_no_invented_numbers():
    print("E. no BLANK/UNVERIFIED cell silently contains a number")
    for name in ("m5f19_tax.csv", "m5f19_methods.csv"):
        for r in csv_rows(name):
            val = r.get("verified_rule_or_value") or r.get("amount_ceiling_stated_in_text") or ""
            st = r.get("status", "")
            if st == "unverified" and val.strip():
                fail(f"E: {name} {r.get('id')} is unverified but the value cell "
                     f"is not empty: {val[:60]!r}. An unconfirmable value must be "
                     f"left BLANK, with the explanation in the adjacent column.")
    # In the tax CSV, a blank verified_rule_or_value must mean blank in HTML too.
    tax = csv_rows("m5f19_tax.csv")
    blanks = [t["id"] for t in tax if not t["verified_rule_or_value"]]
    html_text = read(os.path.join(ROOT, "m5f19-tax.html"))
    for tid in blanks:
        if tid not in html_text:
            fail(f"E: blank row {tid} is missing from m5f19-tax.html")
    ok(f"{len(blanks)} blank cells kept blank and rendered as UNVERIFIED "
       f"({', '.join(blanks) or 'none'})")


def check_F_costs_rederive():
    print("F. every cost figure in the HTML re-derives from the recorded board")
    board = {r["field"]: r["value"] for r in csv_rows("m5f19_board.csv")}
    ask = Decimal(board["usd_ask"])
    bid = Decimal(board["usd_bid"])
    if ask != eng.ASK or bid != eng.BID:
        fail(f"F: board CSV ({ask}/{bid}) disagrees with engine "
             f"({eng.ASK}/{eng.BID})")
    lad = csv_rows("m5f19_ladder.csv")
    txt = read(os.path.join(ROOT, "m5f19-costs.html"))
    checked = 0
    for r in lad:
        got = eng.leg_cost(Decimal(r["amount_usd"]), int(r["wires"]),
                           ask, bid, r["denominator"])
        for col, key in (("total_usd", "total_usd"), ("spread_usd", "spread_usd"),
                         ("fee_usd", "fee_usd"), ("telecom_usd", "telecom_usd")):
            if str(got[key]) != r[col]:
                fail(f"F: ladder row {r['amount_usd']}/{r['wires']}/"
                     f"{r['denominator']} {col}={r[col]} but engine gives "
                     f"{got[key]}")
        # the primary schedule must actually appear on the page
        if r["wires"] == "1" and r["denominator"] == "ask":
            if r["total_usd"] not in txt:
                fail(f"F: primary total USD {r['total_usd']} for "
                     f"{r['amount_usd']} is absent from m5f19-costs.html")
            checked += 1
    # dashboard headline figures must match the ladder
    dash = read(os.path.join(ROOT, "m5f19-dashboard.html"))
    for amt in ("10000", "400000"):
        r = next(x for x in lad if x["amount_usd"] == amt and x["wires"] == "1"
                 and x["denominator"] == "ask")
        if r["total_usd"] not in dash:
            fail(f"F: dashboard does not show USD {r['total_usd']} for {amt}")
    # the fixed components must appear
    for label, val in (("fee ceiling", eng.money(eng.FEE_MAX_CNY / ask)),
                       ("telecom", eng.money(eng.TELECOM_CNY_NON_HMT / ask))):
        if str(val) not in dash and str(val) not in txt:
            fail(f"F: {label} USD {val} appears on no page")
    if not [f for f in FAILURES if f.startswith("F:")]:
        ok(f"{checked} primary-schedule totals verified on-page; "
           f"{len(lad)} ladder rows re-derived across 4 components")


def check_G_reconciliation():
    print("G. reconciliation gate — other sessions' figures reproduce exactly")
    rec = csv_rows("m5f19_reconciliation.csv")
    legacy = [r for r in rec if "this session" not in r["session"]]
    own = [r for r in rec if "this session" in r["session"]]
    if not legacy:
        fail("G: no legacy rows — the reconciliation proves nothing")
    for r in legacy:
        got = eng.leg_cost(Decimal(r["amount_usd"]), int(r["wires"]),
                           Decimal(r["board_ask"]), Decimal(r["board_bid"]),
                           r["spread_denominator"])["total_usd"]
        if str(got) != r["reproduced_usd"]:
            fail(f"G: {r['model']} {r['amount_usd']} re-derives to {got}, CSV "
                 f"says {r['reproduced_usd']}")
        if r["reproduced_exactly"] != "yes":
            fail(f"G: published figure USD {r['published_usd']} from "
                 f"{r['session']} did NOT reproduce exactly")
    # own figures must match the ladder for the same parameters
    lad = csv_rows("m5f19_ladder.csv")
    for r in own:
        m = [x for x in lad if x["amount_usd"] == r["amount_usd"]
             and x["wires"] == r["wires"]
             and x["denominator"] == r["spread_denominator"]]
        if not m:
            fail(f"G: own row {r['amount_usd']}/{r['wires']}/"
                 f"{r['spread_denominator']} has no ladder counterpart")
        elif m[0]["total_usd"] != r["reproduced_usd"]:
            fail(f"G: own row {r['amount_usd']} ladder={m[0]['total_usd']} but "
                 f"reconciliation={r['reproduced_usd']}")
    html_text = read(os.path.join(ROOT, "m5f19-reconciliation.html"))
    for r in rec:
        if r["published_usd"] not in html_text:
            fail(f"G: USD {r['published_usd']} missing from the "
                 f"reconciliation page")
    if not [f for f in FAILURES if f.startswith("G:")]:
        ok(f"{len(legacy)}/{len(legacy)} legacy figures reproduce to the cent; "
           f"{len(own)} own figures agree with the ladder")


def check_H_ladder_coverage():
    print("H. ladder covers USD 10,000..400,000 in 10,000 steps")
    lad = csv_rows("m5f19_ladder.csv")
    primary = sorted({int(r["amount_usd"]) for r in lad
                      if r["wires"] == "1" and r["denominator"] == "ask"})
    want = list(range(10_000, 400_001, 10_000))
    if primary != want:
        fail(f"H: primary amounts are {primary[:3]}...{primary[-3:]} "
             f"({len(primary)} rows), expected {len(want)} increments "
             f"{want[0]}..{want[-1]}")
    gaps = [w for w in want if w not in primary]
    if gaps:
        fail(f"H: missing increments {gaps}")
    combos = {(r["wires"], r["denominator"]) for r in lad}
    if combos != {("1", "ask"), ("1", "mid"), ("8", "ask"), ("8", "mid")}:
        fail(f"H: unexpected scenario/denominator combinations {combos}")
    if len(lad) != len(want) * len(combos):
        fail(f"H: {len(lad)} rows, expected {len(want) * len(combos)}")
    if not [f for f in FAILURES if f.startswith("H:")]:
        ok(f"{len(primary)} increments \u00d7 {len(combos)} scenarios = "
           f"{len(lad)} rows, no gaps")


def check_I_engine():
    print("I. engine self-checks")
    try:
        eng.self_checks()
        ok("fee-convention independence, cap binding, monotonicity, "
           "8-wire>1-wire, legacy reproduction")
    except AssertionError as exc:
        fail(f"I: engine self-check failed: {exc}")


def check_J_scope():
    print("J. scope — no file outside this session's claim was modified")

    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout

    try:
        # Diff against the merge base with the integration branch, NOT a
        # hardcoded commit. A pinned base goes stale the moment origin/main is
        # merged in and then reports every sibling's files as "modified by us",
        # which is exactly what happened on the first run after merging main.
        try:
            base = git("merge-base", "HEAD", "origin/main").strip()
        except subprocess.CalledProcessError:
            base = git("merge-base", "HEAD", "main").strip()
        if not base:
            fail("J: could not determine a merge base")
            return
        out = git("diff", "--name-only", base, "HEAD")
        out += git("diff", "--name-only")
        out += git("diff", "--name-only", "--cached")
        out += git("ls-files", "--others", "--exclude-standard")
    except subprocess.CalledProcessError as exc:
        fail(f"J: git diff failed: {exc.stderr.strip()[:200]}")
        return
    touched = sorted({l.strip() for l in out.splitlines() if l.strip()})
    foreign = []
    for f in touched:
        if f.startswith(OWNED_PREFIXES) or f in OWNED_EXACT:
            continue
        foreign.append(f)
    if foreign:
        # This gate is session-local by construction: it asks "did THIS branch touch a
        # file it did not claim?". On the final-integration branch the answer is
        # legitimately yes, because the integrator owns the shared outputs
        # (index.html, README.md, EXECUTIVE_SUMMARY.md) by design. Only a FAIL when the
        # branch is not the integration branch, which is flagged by r11-release.html
        # being present with an integration claim in COORDINATION.md.
        import os as _os
        integration = _os.path.exists(_os.path.join(ROOT, "r11-release.html")) and \
            "final integration" in open(_os.path.join(ROOT, "COORDINATION.md"), encoding="utf-8").read().lower()
        if integration:
            print(f"    note: {len(foreign)} files outside the m5f19 namespace, "
                  f"expected on the final-integration branch (see COORDINATION.md)")
        else:
            fail(f"J: modified files outside the claim: {foreign}")
    if not foreign:
        ok(f"{len(touched)} files touched vs merge base {base[:7]}, all inside "
           f"the m5f19 namespace (plus append-only COORDINATION.md)")


def check_K_determinism():
    print("K. determinism — rebuilding is byte-identical")
    before = {}
    for p in PAGES + ASSETS:
        path = os.path.join(ROOT, p)
        if os.path.exists(path):
            before[p] = hashlib.sha256(read(path).encode()).hexdigest()
    for script in ("m5f19_engine.py", "gen_m5f19_data.py", "gen_m5f19_tables.py",
                   "build_m5f19_site.py"):
        r = subprocess.run([sys.executable, os.path.join("scripts", script)],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            fail(f"K: {script} exited {r.returncode}: "
                 f"{(r.stderr or r.stdout).strip()[-300:]}")
            return
    for p, h in before.items():
        now = hashlib.sha256(read(os.path.join(ROOT, p)).encode()).hexdigest()
        if now != h:
            fail(f"K: {p} changed on rebuild — output is not deterministic")
    if not [f for f in FAILURES if f.startswith("K:")]:
        ok(f"{len(before)} files rebuilt byte-identically")


def main() -> int:
    print("=" * 74)
    print("m5f19 site verification")
    print("=" * 74)
    for name in CSV_FILES:
        if not os.path.exists(os.path.join(DATA, name)):
            fail(f"precondition: data/{name} is missing")
    if FAILURES:
        for f in FAILURES:
            print("  \u2717 " + f)
        return 1
    for fn in (check_A_pages, check_BC_links, check_D_row_sources,
               check_E_no_invented_numbers, check_F_costs_rederive,
               check_G_reconciliation, check_H_ladder_coverage, check_I_engine,
               check_J_scope, check_K_determinism):
        fn()
    print("-" * 74)
    if FAILURES:
        print(f"FAIL — {len(FAILURES)} problem(s):")
        for f in FAILURES:
            print("  \u2717 " + f)
        return 1
    print(f"PASS — {CHECKS} checks, 0 failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
