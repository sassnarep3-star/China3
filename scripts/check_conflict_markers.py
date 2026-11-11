#!/usr/bin/env python3
"""Fail if any tracked text file still contains a Git merge-conflict marker.

Why this exists
---------------
Unresolved conflict markers were merged into `main` twice in this repository
(pull request #41 -> `scripts/build_dashboard.py`, `index.html`, `README.md`;
pull request #46 -> `COORDINATION.md`). The first broke the published landing
page; the second sat on the coordination board for about an hour. No existing
gate looked for them. This one does, on every push and every pull request.

What counts as a marker
-----------------------
A line that *starts* with seven '<' or seven '>' followed by a space or the end
of the line, or seven '|' followed by a space (the diff3 "base" marker). Prose
that merely mentions a marker inside a sentence or inside backticks does not
start a line with it and is not reported. A line of exactly seven '=' is only
reported when the same file also contains a start or end marker, because a bare
row of '=' is legitimate in Markdown, reStructuredText and code banners.

Usage
-----
    python3 scripts/check_conflict_markers.py            # check tracked files
    python3 scripts/check_conflict_markers.py --self-test  # prove the check bites

Exit status 0 = clean, 1 = marker found (or self-test failed).
No third-party dependencies.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Built from single characters so that this file never contains a marker itself.
START = "<" * 7
END = ">" * 7
BASE = "|" * 7
SEP = "=" * 7

BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz",
    ".woff", ".woff2", ".ttf", ".otf", ".mp3", ".mp4", ".wav", ".ogg",
}


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
    ).stdout
    return [p for p in out.decode("utf-8", errors="replace").split("\0") if p]


def is_marker(line: str, marker: str) -> bool:
    """True when `line` starts with `marker` followed by a space or nothing."""
    if not line.startswith(marker):
        return False
    rest = line[len(marker):]
    return rest == "" or rest.startswith(" ")


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return (line number, kind) for every conflict marker in `text`."""
    hard: list[tuple[int, str]] = []
    seps: list[int] = []
    for number, raw in enumerate(text.split("\n"), start=1):
        line = raw.rstrip("\r")
        if is_marker(line, START):
            hard.append((number, "start"))
        elif is_marker(line, END):
            hard.append((number, "end"))
        elif is_marker(line, BASE):
            hard.append((number, "base"))
        elif line == SEP:
            seps.append(number)
    if hard:
        hard.extend((n, "separator") for n in seps)
    return sorted(hard)


def scan_repo() -> list[str]:
    problems: list[str] = []
    for rel in tracked_files():
        path = ROOT / rel
        if path.suffix.lower() in BINARY_SUFFIXES or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data[:8192]:
            continue  # binary
        text = data.decode("utf-8", errors="replace")
        for number, kind in scan_text(text):
            problems.append(f"{rel}:{number}: conflict marker ({kind})")
    return problems


def self_test() -> int:
    """Negative and positive tests: the check must bite, and must not over-bite."""
    conflicted = "\n".join([
        "kept line",
        START + " HEAD",
        "ours",
        SEP,
        "theirs",
        END + " origin/main",
        "kept line",
    ])
    diff3 = "\n".join([START + " HEAD", "ours", BASE + " base", "old", SEP, "theirs", END + " x"])
    harmless = "\n".join([
        "Title",
        SEP,                                   # a bare underline is legitimate
        "the file shipped `" + START + " HEAD` and `" + END + " origin/main`",  # prose
        "    " + START + " indented, so not a marker",
        START + "<  eight characters, not seven",
        "> > > > > > > quoted seven deep with spaces",
    ])
    cases = [
        ("conflicted file is caught", [k for _, k in scan_text(conflicted)], ["start", "separator", "end"]),
        ("diff3 base marker is caught", [k for _, k in scan_text(diff3)], ["start", "base", "separator", "end"]),
        ("prose, underline and near-misses pass", scan_text(harmless), []),
        ("CRLF line endings are handled", [k for _, k in scan_text(conflicted.replace("\n", "\r\n"))], ["start", "separator", "end"]),
    ]
    failed = 0
    for name, got, want in cases:
        ok = got == want
        failed += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got}, want {want}"))
    print("self-test " + ("PASS" if not failed else "FAIL"))
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    problems = scan_repo()
    if problems:
        print(f"FAIL — {len(problems)} merge-conflict marker line(s) in tracked files:")
        for p in problems[:200]:
            print("  " + p)
        print("Resolve the conflict (keep both sessions' content), then commit again.")
        return 1
    print(f"PASS — no merge-conflict markers in {len(tracked_files())} tracked files.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
