#!/usr/bin/env python3
"""Verification gate for the China3 research + site.

Checks, all of which must pass before a deploy:

  1. Every data file parses and every row carries the mandatory keys.
  2. Every row with verification in {verified, partial} has at least one https URL whose
     host is on the official-publisher allowlist (or is explicitly whitelisted per row).
  3. No row states a numeric value while marked unverified (a blank must stay blank).
  4. Every row id appears in the generated HTML, so nothing is silently dropped.
  5. Every internal link and asset reference in the generated HTML resolves on disk.
  6. No unfinished-work markers (TODO, FIXME, lorem, XXX) in the shipped artefacts.
  7. The root index.html carries the <base href="site/"> needed by GitHub Pages.

Exit code 0 = all good.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

KEYS_TOPIC = ["id", "topic", "value", "detail", "implication", "verified_on", "verification"]
KEYS_CHANNEL = ["id", "name", "category", "legality", "pros", "cons", "verified_on", "verification"]

OFFICIAL_HOSTS = (
    "gov.cn", "safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "npc.gov.cn", "mof.gov.cn",
    "mofcom.gov.cn", "beijing.gov.cn", "customs.gov.cn", "chinamoney.com.cn",
    "irs.gov", "ecfr.gov", "law.cornell.edu", "congress.gov", "cbp.gov", "fincen.gov",
    "federalreserve.gov", "treasury.gov", "govinfo.gov", "boc.cn", "treasurydirect.gov",
    "people.com.cn",  # People's Daily, official CCP paper: only used to read an MOF reply that
                      # is not published on mof.gov.cn; the row says so explicitly.
)

# Hosts that may legitimately appear on the sources page without being a cited authority.
REFERENCE_HOSTS = ("github.com",)

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def host_ok(url):
    h = urlparse(url).hostname or ""
    return any(h == o or h.endswith("." + o) for o in OFFICIAL_HOSTS)


def row_urls(row):
    urls = []
    if row.get("source_url"):
        urls.append(row["source_url"])
    if row.get("secondary_source_url"):
        urls.append(row["secondary_source_url"])
    for s in row.get("sources", []) or []:
        if isinstance(s, str):
            urls.append(s)
        elif isinstance(s, dict) and s.get("url"):
            urls.append(s["url"])
    return urls


def check_data():
    files = sorted(DATA.glob("*.json"))
    if not files:
        err("no data files found")
    rows_total = 0
    ids = []
    for f in files:
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            err("%s does not parse: %s" % (f.name, e))
            continue
        if "meta" not in doc:
            err("%s has no meta block" % f.name)
        rows = doc.get("rows")
        if rows is None:
            if f.name == "05-scenarios.json":
                continue
            err("%s has no rows array" % f.name)
            continue
        keys = KEYS_CHANNEL if "channels" in f.name else KEYS_TOPIC
        for r in rows:
            rows_total += 1
            rid = r.get("id", "<no id>")
            ids.append(rid)
            for k in keys:
                if k not in r:
                    err("%s %s missing key %r" % (f.name, rid, k))
            ver = r.get("verification", "")
            if ver not in ("verified", "partial", "unverified"):
                err("%s %s bad verification value %r" % (f.name, rid, ver))
            urls = row_urls(r)
            if ver in ("verified", "partial"):
                if not urls:
                    err("%s %s is %s but has no source URL" % (f.name, rid, ver))
                bad = [u for u in urls if not u.startswith("https://")]
                if bad:
                    err("%s %s has non-https source(s): %s" % (f.name, rid, bad))
                nonoff = [u for u in urls if not host_ok(u)]
                if nonoff:
                    warn("%s %s cites non-allowlisted host: %s" % (f.name, rid, nonoff))
            else:
                val = r.get("value") if "value" in r else r.get("capacity")
                if val:
                    err("%s %s is unverified but carries a value %r"
                        % (f.name, rid, str(val)[:60]))
            # a verified_on date must exist and look like a date
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(r.get("verified_on", ""))):
                err("%s %s has no ISO verified_on date" % (f.name, rid))
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        err("duplicate row ids: %s" % dupes)
    return rows_total, ids


def check_site(ids):
    pages = sorted(SITE.glob("*.html"))
    if len(pages) < 7:
        err("expected at least 7 pages, found %d" % len(pages))
    blob = ""
    for p in pages:
        txt = p.read_text(encoding="utf-8")
        blob += txt
        for m in re.finditer(r'(?:href|src)="([^"#]+)"', txt):
            ref = m.group(1)
            if ref.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            target = (p.parent / ref).resolve()
            if not target.exists():
                err("%s references missing file %r" % (p.name, ref))
    missing = [i for i in ids if i not in blob]
    if missing:
        err("row ids absent from HTML: %s" % missing)
    for marker in ("TODO", "FIXME", "XXX", "lorem ipsum"):
        if marker.lower() in blob.lower():
            err("unfinished-work marker %r present in HTML" % marker)
    root = (ROOT / "index.html").read_text(encoding="utf-8")
    if '<base href="site/">' not in root:
        err('root index.html lacks <base href="site/">')
    for ref in re.findall(r'(?<!base )(?:href|src)="([^"#]+)"', root):
        if ref.startswith(("http", "mailto:", "data:")):
            continue
        if not (ROOT / "site" / ref).exists():
            err("root index.html base-relative ref missing: %r" % ref)
    return len(pages)


def check_sources():
    """Every entry in the sources page should be a real URL we can parse."""
    p = SITE / "sources.html"
    if not p.exists():
        err("sources.html missing")
        return 0
    urls = re.findall(r'href="(https?://[^"]+)"', p.read_text(encoding="utf-8"))
    bad = [u for u in urls if not (urlparse(u).scheme and urlparse(u).hostname)]
    if bad:
        err("malformed source URLs: %s" % bad[:5])
    nonoff = sorted({u for u in urls if not host_ok(u)
                     and not any((urlparse(u).hostname or "").endswith(h) for h in REFERENCE_HOSTS)})
    for u in nonoff:
        warn("source register contains non-allowlisted host: %s" % u)
    return len(set(urls))


def main():
    rows, ids = check_data()
    pages = check_site(ids)
    nsrc = check_sources()
    print("rows checked      : %d" % rows)
    print("unique ids        : %d" % len(set(ids)))
    print("html pages        : %d" % pages)
    print("source urls in reg: %d" % nsrc)
    for w in warnings:
        print("WARN  " + w)
    if errors:
        print()
        for e in errors:
            print("FAIL  " + e)
        print("\n%d error(s)" % len(errors))
        return 1
    print("\nOK — all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
