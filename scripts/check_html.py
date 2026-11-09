#!/usr/bin/env python3
"""
check_html.py — balance and integrity check for every page the site publishes.

Fails if:
  - any HTML page has an unclosed or mismatched tag,
  - any local href/src target does not exist,
  - any page is missing the shared stylesheet,
  - any new cost page lost its source links.

Run: python3 scripts/check_html.py
"""

import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

errors = []


class Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.err = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.err.append("stray </%s> at line %d" % (tag, self.getpos()[0]))
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.err.append("</%s> at line %d closes over %d unclosed tag(s), innermost %s at line %d"
                                % (tag, self.getpos()[0], len(self.stack) - i - 1,
                                   self.stack[-1][0], self.stack[-1][1]))
                del self.stack[i:]
                return
        self.err.append("unmatched </%s> at line %d" % (tag, self.getpos()[0]))


def pages():
    out = []
    for base in (ROOT, os.path.join(ROOT, "docs")):
        for name in sorted(os.listdir(base)):
            if name.endswith(".html"):
                out.append(os.path.join(base, name))
    return out


def main():
    all_pages = pages()
    for path in all_pages:
        rel = os.path.relpath(path, ROOT)
        html = open(path, encoding="utf-8").read()

        b = Balance()
        try:
            b.feed(html)
        except Exception as exc:                     # malformed input
            errors.append("%s: parser error %s" % (rel, exc))
            continue
        for e in b.err:
            errors.append("%s: %s" % (rel, e))
        for tag, line in b.stack:
            errors.append("%s: unclosed <%s> opened at line %d" % (rel, tag, line))

        # local targets
        for href in re.findall(r'(?:href|src)="([^"]+)"', html):
            if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            target = href.split("#", 1)[0]
            if not target:
                continue
            full = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(full):
                errors.append("%s: missing local target %s" % (rel, href))

        # every page must load the base stylesheet
        if 'rel="stylesheet"' not in html and "<style" not in html:
            errors.append("%s: no stylesheet" % rel)

    # the cost pages must keep their official links
    for name, minimum in (("cost-table.html", 10), ("cost-steps.html", 10), ("verification.html", 15)):
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            errors.append("%s: missing" % name)
            continue
        html = open(p, encoding="utf-8").read()
        n = len(set(re.findall(r'href="(https://[^"]+)"', html)))
        if n < minimum:
            errors.append("%s: only %d distinct official links, expected at least %d"
                          % (name, n, minimum))
        if "boc.cn" not in html and "safe.gov.cn" not in html:
            errors.append("%s: lost its primary-source links" % name)

    print("HTML integrity check")
    print("  pages scanned: %d" % len(all_pages))
    if errors:
        print("\nFAIL — %d issue(s):" % len(errors))
        for e in errors:
            print("  -", e)
        return 1
    print("PASS — all pages balanced, all local targets exist, sources intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
