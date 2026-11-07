#!/usr/bin/env python3
"""Tiny Markdown -> HTML renderer, enough for content/executive-summary.md.

Written in-repo on purpose: the Pages build must not depend on installing anything
(the workflow installs no packages), and the summary is published as a normal page.
Supports: headings, paragraphs, bold/italic/inline code, links, blockquotes, ordered and
unordered lists, tables, horizontal rules.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def inline(text):
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", out)
    return out


def convert(md):
    lines = md.split("\n")
    out = []
    i = 0
    in_list = None  # 'ol' | 'ul'
    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if not s:
            if in_list:
                out.append("</%s>" % in_list)
                in_list = None
            i += 1
            continue

        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            body = []
            head = cells[0]
            data = [c for c in cells[1:] if not re.match(r"^[\s:|-]+$", "|".join(c))]
            out.append('<div class="tablewrap"><table class="grid">')
            out.append("<thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in head) + "</tr></thead><tbody>")
            for r in data:
                out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            out.append("</tbody></table></div>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            if in_list:
                out.append("</%s>" % in_list)
                in_list = None
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1
            continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            if in_list:
                out.append("</%s>" % in_list)
                in_list = None
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            if in_list != "ol":
                if in_list:
                    out.append("</%s>" % in_list)
                out.append('<ol class="recs">')
                in_list = "ol"
            out.append("<li>%s</li>" % inline(m.group(2)))
            i += 1
            continue

        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            if in_list != "ul":
                if in_list:
                    out.append("</%s>" % in_list)
                out.append("<ul>")
                in_list = "ul"
            out.append("<li>%s</li>" % inline(m.group(1)))
            i += 1
            continue

        if s.startswith(">"):
            if in_list:
                out.append("</%s>" % in_list)
                in_list = None
            out.append("<blockquote>%s</blockquote>" % inline(s.lstrip("> ")))
            i += 1
            continue

        # paragraph: gather until blank / structural
        buf = [s]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(("#", "|", ">", "- ", "* "))
                    or re.match(r"^\d+\.\s", nxt) or re.match(r"^(-{3,})$", nxt)):
                break
            buf.append(nxt)
            i += 1
        if in_list:
            out.append("</%s>" % in_list)
            in_list = None
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    if in_list:
        out.append("</%s>" % in_list)
    return "\n".join(out)


def main():
    src = ROOT / "content" / "executive-summary.md"
    dst = ROOT / "site" / "executive-summary.html"
    md = src.read_text(encoding="utf-8")
    body = convert(md)
    template = (ROOT / "tools" / "page-template.html").read_text(encoding="utf-8")
    dst.write_text(template.replace("{{TITLE}}", "Executive summary")
                           .replace("{{BODY}}", body), encoding="utf-8")
    print("wrote", dst.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
