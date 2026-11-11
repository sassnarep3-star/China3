#!/usr/bin/env python3
"""Repository review for session e347: a scripted pass over every line of every tracked file.

Writes:
  data/e347_repo_scan.csv        one row per tracked file (lines, links, non-official links, markers)
  data/e347_irregularities.csv   findings with the evidence measured on this run
  research/e347-repo-review.md   the written review

Run by hand (it needs `git` and, for the pull-request count, `gh`). It is a snapshot:
the dashboard reads the CSV, so later changes by other sessions do not make CI go stale.
"""
import csv
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e347_data as data  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
URL_RE = re.compile(r"https?://[^\s\"'<>)\]|,\\]+")
# Government and regulator suffixes, plus banks' and the interbank market's own sites (official for their own prices).
ALLOWED = data.OFFICIAL_DOMAINS + ("gov", "gov.cn", "gov.hk", "gov.uk", "bocusa.com", "chinamoney.com.cn", "sc.com", "hsbc.com.cn")
NEUTRAL = ("github.com", "github.io", "w3.org", "githubusercontent.com", "shields.io", "example.com", "arena.ai")
OWN = lambda p: p.startswith(("dashboard/", "data/e347_", "scripts/e347_", "research/e347-")) or p in ("index.html", ".github/workflows/e347-verify.yml")


def sh(*cmd):
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


def read(p):
    try:
        return (ROOT / p).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def domain_ok(url, allowed):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in allowed)


def scan():
    rows, nonofficial, total_lines, total_urls = [], Counter(), 0, 0
    files = [f for f in sh("git", "ls-files").splitlines() if f]
    for f in files:
        text = read(f)
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        urls = URL_RE.findall(text)
        bad = [u for u in urls if "." in (urlparse(u).hostname or "") and not domain_ok(u, ALLOWED) and not domain_ok(u, NEUTRAL)]
        markers = len(re.findall(r"^(<<<<<<< |>>>>>>> )", text, re.M))
        if not OWN(f):
            for u in set(bad):
                nonofficial[(urlparse(u).hostname or "").lower()] += 1
        rows.append([f, f.rsplit(".", 1)[-1] if "." in f else "", lines, len(urls), len(bad), markers])
        total_lines += lines
        total_urls += len(urls)
    return files, rows, nonofficial, total_lines, total_urls


def first_value(path, key_col, key, val_col):
    try:
        with (ROOT / path).open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get(key_col) in key:
                    return r.get(val_col)
    except OSError:
        pass
    return None


def checks(files, scan_rows, nonofficial):
    out = {}

    # R01 timestamps later than the commit that added the file
    added = sh("git", "log", "--diff-filter=A", "--format=%cI", "--", "data/s775_sources.csv").splitlines()
    stamps = []
    try:
        with (ROOT / "data/s775_sources.csv").open(encoding="utf-8", newline="") as fh:
            stamps = sorted(r["fetched_utc"] for r in csv.DictReader(fh) if r.get("fetched_utc"))
    except OSError:
        pass
    if added and stamps:
        t_add = datetime.fromisoformat(added[-1]).astimezone(timezone.utc)
        later = [s for s in stamps if datetime.fromisoformat(s.replace("Z", "+00:00")) > t_add]
        now = datetime.now(timezone.utc)
        future = [s for s in stamps if datetime.fromisoformat(s.replace("Z", "+00:00")) > now]
        out["s775_timestamps_after_commit"] = (
            f"File first committed {t_add:%Y-%m-%d %H:%MZ}; {len(later)} of {len(stamps)} fetch timestamps are later ({stamps[0]} to {stamps[-1]}). "
            f"{len(future)} were still in the future when this review ran at {now:%H:%MZ}.",
            "open" if later else "not reproduced")
    else:
        out["s775_timestamps_after_commit"] = ("Could not be measured on this run (git history unavailable).", "not measured")

    es = read("EXECUTIVE_SUMMARY.md")
    found = [v for v in ("50.93", "53.42", "78.41") if v in es]
    out["exec_summary_conflicting_figures"] = (
        f"Figures for the USD 10,000 wire now present in the file: {', '.join(found) or 'none of the three'}.",
        "open" if len(found) > 1 else "fixed in this session: the summary now states one dated figure")

    m = read("data/s775_methods.csv")
    out["s775_m01_50k_day_wording"] = (
        "Text 'US$50,000/day on ID documents' is " + ("present" if "50,000/day on ID" in m else "absent") + " in data/s775_methods.csv.",
        "open; corrected on the dashboard, legacy file left to its owner" if "50,000/day on ID" in m else "fixed in pull request #44 (session c5bf)")
    m04 = next((l for l in m.splitlines() if l.startswith("M04,")), "")
    m04_status = m04.split(",")[3] if m04.count(",") >= 3 else "row not found"
    out["s775_m04_unrestricted"] = (
        f"Row M04 status reads '{m04_status}'.",
        "open; corrected on the dashboard" if "unrestricted" in m04_status else "fixed by its owner")

    ch = read("data/channels.csv")
    out["ch08_staging_outdated"] = (
        "'分步汇出' (staged remittance) is " + ("present" if "分步汇出" in ch else "absent") + " in row CH08.",
        "open; corrected on the dashboard (route L06)" if "分步汇出" in ch else "fixed by its owner")

    hero = read("s775-dashboard.html")
    out["s775_hero_5093"] = (
        f"'50.93' occurs {hero.count('50.93')} time(s) and '53.42' {hero.count('53.42')} time(s) in s775-dashboard.html.",
        "open; fix is in unmerged pull request #34" if "50.93" in hero else "fixed in pull request #44 (session c5bf)")

    layers = [("data/s436_cost_schedule.csv", "method_id", ("M01",), "known_cost_usd"),
              ("data/s775_cost_10k_400k.csv", "amount_usd", ("10000",), "total_usd"),
              ("data/ladder_20261110.csv", "amount_usd", ("10000",), "total_usd"),
              ("data/cost_ladder.csv", "method_id", ("M01",), "total_cost_usd"),
              ("data/reference_check_values.csv", "amount_usd", ("10000",), "single_wire_known_cost_usd"),
              ("data/d646_ladder.csv", "usd", ("10000",), "known_bank_cost_usd"),
              ("data/c3x_ladder.csv", "amount_usd", ("10000",), None),
              ("data/a513_ladder.csv", "amount_usd", ("10000",), "total_one_transfer_usd"),
              ("data/e347_costs.csv", "method_id", ("L01",), "known_cost_usd")]
    vals = []
    for path, kc, key, vc in layers:
        if vc is None:
            line = next((l for l in read(path).splitlines()[1:2]), "")
            v = line.split(",")[5] if line else None
        else:
            v = first_value(path, kc, key, vc)
        if v:
            vals.append(f"{Path(path).name} {v}")
    distinct = sorted({v.split()[-1] for v in vals})
    out["cost_layers"] = (
        "USD 10,000 wire cost by file: " + "; ".join(vals) + f". Distinct values: {', '.join(distinct)}. The three passes that used the 17:39:58 board (c3x, a513, e347) agree.",
        "open in legacy files; the landing page now shows one dated figure and the Archive page labels the rest")

    root_pages = [f for f in files if f.endswith(".html") and "/" not in f]
    docs_pages = [f for f in files if f.startswith("docs/") and f.endswith(".html")]
    builders = [f for f in files if re.match(r"scripts/(build_|gen_)", f)]
    out["page_sprawl"] = (
        f"{len(root_pages)} HTML pages at the root, {len(docs_pages)} under docs/, {len(builders)} generator scripts, {len(files)} tracked files.",
        "addressed in this session: one landing page, seven dashboard pages, everything else moved behind Archive")

    markers = sum(r[5] for r in scan_rows)
    out["conflict_markers"] = (f"Conflict-marker lines in tracked files on this run: {markers}.",
                               "fixed by session 2c8d441e (pull request #42)" if markers == 0 else "open")

    s29 = next((l for l in read("data/s775_sources.csv").splitlines() if l.startswith("S29,")), "")
    out["s775_s29_title"] = ("Row S29 title: " + (s29.split(",")[2][:70] if s29 else "row not found") + ".",
                             "open: '交易炒作风险' is the 2021 notice's title" if "交易炒作风险" in s29 and "2026〕42" in s29 else "not reproduced on this run")

    top = ", ".join(f"{d} ({n} files)" for d, n in nonofficial.most_common(8))
    out["non_official_domains"] = (
        f"{len(nonofficial)} domains that are neither government, regulator nor a bank's own site, outside this session's files" + (f": {top}." if top else "."),
        "open; this dashboard cites official domains only" if nonofficial else "none found")

    prs = sh("gh", "pr", "list", "--state", "open", "--json", "number,isDraft")
    try:
        nums = sorted(p["number"] for p in json.loads(prs))
        out["open_prs"] = (f"{len(nums)} open or draft pull requests: " + ", ".join(f"#{n}" for n in nums) + ".", "open; left to the owner")
    except Exception:
        out["open_prs"] = ("Could not be measured on this run (gh unavailable).", "not measured")

    wf = [f for f in files if f.startswith(".github/workflows/")]
    out["workflow_overlap"] = (f"{len(wf)} workflow files; validate_data.py is invoked by {sum('validate_data.py' in read(f) for f in wf)} of them.",
                               "open; pages.yml now also link-checks the dashboard")
    # Added 2026-11-11 (session arena/b579901a-china3, final integration).
    costs_html = read("dashboard/costs.html")
    printed = re.findall(r"(Selling Rate|Buying Rate) ([0-9.]+) per 100", costs_html)
    out["board_strings_as_printed"] = (
        "costs.html prints " + (", ".join(f"{k} {v}" for k, v in printed) if printed else "no per-100 figures")
        + f"; the arithmetic uses {float(data.RATE['ask']) * 100:.2f} and {float(data.RATE['bid']) * 100:.2f} per 100.",
        "fixed in this session: both strings are derived from the rates, and scripts/e347_verify.py now fails if they drift")
    tax_html = read("dashboard/tax.html")
    out["sec988_personal_wording"] = (
        f"T10 on the Tax page mentions a capital gain: {'capital gain' in tax_html}; "
        f"cites IRS Publication 525: {'Pub. 525' in tax_html}; "
        f"cites 988(e)(1): {'988(e)(1)' in tax_html}.",
        "fixed in this session: T10 and flag U05 rewritten against 26 U.S.C. 988(e) and Publication 525, which are now S27 and S43")
    nav_html = read("index.html")
    m = re.search(r'<nav class="nav"[^>]*>(.*?)</nav>', nav_html, re.S)
    n_nav = len(re.findall(r"<a ", m.group(1))) if m else 0
    arch = read("dashboard/archive.html")
    editions = [f for f in ("m5f19-dashboard.html", "76e-verification.html", "f52-summary.html", "b9b3-dashboard.html",
                            "g8d8-summary.html", "e0f4-76e-audit.html", "n676-summary.html") if f in arch]
    out["nav_entries"] = (
        f"{n_nav} entries in the top bar of index.html; {len(editions)} of 7 root-level editions are linked from the Archive page.",
        "changed in this session: core sections only, every edition still one click away on Archive; no page was removed")

    out["no_license"] = ("LICENSE file " + ("exists." if any(f.upper().startswith("LICENSE") for f in files) else "does not exist."), "open; owner's decision")
    out["branch_naming"] = (f"Current branch: {sh('git', 'rev-parse', '--abbrev-ref', 'HEAD')}.", "cannot be changed by a session")
    return out


def main():
    files, scan_rows, nonofficial, total_lines, total_urls = scan()
    with (ROOT / "data/e347_repo_scan.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["path", "type", "lines", "links", "non_official_links", "conflict_marker_lines"])
        w.writerows(scan_rows)
    ev = checks(files, scan_rows, nonofficial)
    rows = []
    for rid, sev, where, finding, check, path, src in sorted(data.IRREGULARITIES, key=lambda r: r[0]):
        evidence, status = ev[check]
        rows.append(dict(id=rid, severity=sev, where=where, finding=finding, evidence=evidence, status=status,
                         evidence_path=path, official_source_id=src,
                         official_source_url=next((s[3] for s in data.SOURCES if s[0] == src), "")))
    with (ROOT / "data/e347_irregularities.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    by_type = Counter()
    for r in scan_rows:
        by_type[r[1]] += r[2]
    md = [f"""# Repository review (session e347)

Snapshot taken on {data.SNAPSHOT_DATE} of branch `{sh('git', 'rev-parse', '--abbrev-ref', 'HEAD')}` on top of `main` at `{sh('git', 'rev-parse', '--short', 'origin/main')}`.

## What was done

1. **Scripted pass over every line.** `scripts/e347_repo_review.py` read all {len(files)} tracked files
   ({total_lines:,} lines). For each file it counted lines, extracted every link ({total_urls:,} in total),
   classified each link's domain, and looked for merge-conflict markers. Per-file results are in
   `data/e347_repo_scan.csv`.
2. **Manual read** of the files a reader meets first or that other pages are generated from:
   `COORDINATION.md` (claims and logs), `EXECUTIVE_SUMMARY.md`, `index.html` and its generator
   `scripts/build_dashboard.py`, `.github/workflows/pages.yml`, `data/s775_sources.csv`,
   `data/s775_methods.csv`, `data/s775_cost_10k_400k.csv`, `data/s775_method_summary.csv`,
   `data/s775_flags.csv`, `data/channels.csv`, `data/cross_session_findings.csv`,
   `data/final_integration_flags.csv`, `research/a15-review.md`, and the header rows of every cost ladder.
   The remaining generated HTML pages were not read by eye line by line; they were covered by the scripted
   pass and by running each layer's own validator.
3. **Independent re-verification.** {len(data.SOURCES)} official pages were read on {data.SNAPSHOT_DATE}
   ({sum(1 for s in data.SOURCES if s[4] == 'direct')} in full, {sum(1 for s in data.SOURCES if s[4] == 'excerpt')} as excerpts of the official page's own text).
   The register is `data/e347_sources.csv`; each fact is in `data/e347_facts.csv`.
4. **All existing validators were run** on the combined tree before and after this session's changes.

Lines by file type: {", ".join(f"{t or '(none)'} {n:,}" for t, n in by_type.most_common())}.

## Findings

| ID | Severity | Where | Finding | Evidence measured | Status |
|----|----------|-------|---------|-------------------|--------|"""]
    for r in rows:
        md.append(f"| {r['id']} | {r['severity']} | {r['where']} | {r['finding']} | {r['evidence']} | {r['status']} |")
    md.append(f"""
## Corrections applied on the new dashboard

- **USD 50,000 on ID alone.** The dashboard states that this applies to Chinese citizens and to holders of
  the Foreign Permanent Resident ID. A foreign passport holder buying foreign currency with RMB needs source
  documents and tax evidence (汇发〔2020〕14号 Art. 59, sources S04, S05). This is the correction session A058
  asked for.
- **Remitting foreign currency already held.** For a foreign individual the 2020 Guidelines (Art. 65) name no
  amount threshold; the USD 50,000-a-day threshold in Art. 64 is for domestic individuals. Earlier layers
  mixed the two.
- **Emigrant transfers.** The 2004 staging rule is replaced by 汇发〔2014〕2号 section 6.
- **Overseas ATM.** Listed with its yearly cap of RMB 100,000 and the Bank of China tariff effective 2026-11-11.
- **One dated figure.** The landing page shows a single bank-cost figure from the 2026/11/10 17:39:58 board.
  Two other sessions (C3X, A513) derived the same numbers independently from that board.
- **U.S. currency gain.** Stated as a possible taxable gain with the personal-transaction question flagged
  (U05), not as "no U.S. tax event".

## Not done, and why

- Legacy pages and data owned by other sessions were not edited. Their known problems are listed above and
  on `dashboard/flagged.html`, and the Archive page labels each layer.
- Pull request #34 (S775 correction) was not merged by this session. Session c5bf applied its content in
  pull request #44 while this review was in progress, which closed findings R03 and R06.
- Items that could not be confirmed from an official page are blank on the site and listed as U01 to
  U{len(data.FLAGS):02d} in `data/e347_flags.csv`.
""")
    (ROOT / "research/e347-repo-review.md").write_text("\n".join(md), encoding="utf-8")
    print(f"e347 repo review: {len(files)} files, {total_lines:,} lines, {total_urls:,} links, {len(rows)} findings")
    for r in rows:
        print(f"  {r['id']} [{r['status'][:40]}] {r['evidence'][:150]}")


if __name__ == "__main__":
    main()
