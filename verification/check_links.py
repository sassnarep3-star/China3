#!/usr/bin/env python3
"""Check internal links, anchors and local assets across every HTML page in the repository.
Standard library only.  Usage:  python3 verification/check_links.py   (exit 1 on any broken link)
External (http/https) links are not fetched here; see verification.html for the external-source audit."""
import html.parser, os, sys, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "research"}
class P(html.parser.HTMLParser):
    def __init__(s):
        super().__init__(); s.ids = set(); s.links = []; s.scripts = False
    def handle_starttag(s, tag, attrs):
        a = dict(attrs)
        if a.get("id"): s.ids.add(a["id"])
        if tag == "a" and a.get("name"): s.ids.add(a["name"])
        if tag == "script" and a.get("src"): s.scripts = True
        for k in ("href", "src"):
            if a.get(k) and tag in ("a", "link", "script", "img"): s.links.append((tag, a[k]))
pages = {}
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP_DIRS]
    for f in fn:
        if f.endswith(".html"):
            p = os.path.join(dp, f); pr = P(); pr.feed(open(p, encoding="utf-8", errors="ignore").read()); pages[os.path.relpath(p, ROOT)] = pr
bad = []; n = 0; js = 0
for rel, pr in sorted(pages.items()):
    for tag, href in pr.links:
        if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "data:", "//")): continue
        n += 1
        path, _, frag = href.partition("#"); path = urllib.parse.unquote(path.split("?")[0])
        tgt = rel if path == "" else os.path.normpath(os.path.join(os.path.dirname(rel), path))
        if tgt.endswith("/") or os.path.isdir(os.path.join(ROOT, tgt)): tgt = os.path.join(tgt, "index.html")
        if not os.path.exists(os.path.join(ROOT, tgt)): bad.append(f"{rel}: missing target {href}"); continue
        if frag and tgt.endswith(".html"):
            if tgt not in pages: continue
            if frag not in pages[tgt].ids:
                if pages[tgt].scripts: js += 1; continue   # target renders rows client-side; anchor cannot be checked statically
                bad.append(f"{rel}: missing anchor #{frag} in {tgt}")
print(f"{len(pages)} pages, {n} internal links checked, {len(bad)} broken, {js} anchors in client-rendered pages not checked")
for b in bad: print("  BROKEN:", b)
sys.exit(1 if bad else 0)
