#!/usr/bin/env python3
"""Generator/consistency marker for e0f4-76e-audit.html.

The page is hand-authored; this builder verifies it exists, is non-empty and
carries the expected structure, and prints where its content comes from.
The binding content gate is scripts/verify_e0f4_audit.py. Exit 0 on pass, 1 on failure.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "e0f4-76e-audit.html")
REQUIRED = [
    "Independent audit",
    "data/e0f4_76e_audit.csv",
    "research/e0f4-76e-audit.md",
    "5cf46292",
    'id="arithmetic"',
    'id="sources"',
    'id="findings"',
    'id="defects"',
    "SAFE TO MERGE",
]

if not os.path.exists(PAGE):
    print("missing: e0f4-76e-audit.html")
    sys.exit(1)
text = open(PAGE, encoding="utf-8").read()
missing = [s for s in REQUIRED if s not in text]
if missing:
    print("page is missing required content: %s" % missing)
    sys.exit(1)
n_rows = len(re.findall(r"<tr", text))
print("e0f4-76e-audit.html present; %d table rows; content parity is enforced by verify_e0f4_audit.py" % n_rows)
