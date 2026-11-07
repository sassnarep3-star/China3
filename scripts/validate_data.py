#!/usr/bin/env python3
"""Contract checks for the China3 data set.

Every rule here exists to enforce one promise made to the reader:
nothing is asserted without a source, and anything unconfirmed is blank
and flagged.

Exit code 0 = clean, 1 = violations (printed).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

STATUSES = {"lawful", "conditional", "prohibited", "criminal"}
TIERS = {"official", "official-secondary", "third-party"}
FLAG_STATUSES = {"Unverified", "Partially verified", "Needs your facts"}
JURISDICTIONS = {"US", "PRC", "US–PRC"}
KINDS = {"rule", "analysis"}


def load(name: str) -> dict:
    with (DATA / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    errs: list[str] = []
    warns: list[str] = []

    sources = load("sources.json")
    channels = load("channels.json")
    taxes = load("taxes.json")
    penalties = load("penalties.json")
    flagged = load("flagged.json")

    src_ids = [s["id"] for s in sources["sources"]]
    if len(set(src_ids)) != len(src_ids):
        errs.append("sources.json: duplicate source ids")
    for s in sources["sources"]:
        if not re.fullmatch(r"S\d{2}", s["id"]):
            errs.append(f"sources.json: bad id {s['id']}")
        if not str(s.get("url", "")).startswith("http"):
            errs.append(f"sources.json: {s['id']} has no http(s) url")
        if s.get("tier") not in TIERS:
            errs.append(f"sources.json: {s['id']} bad tier {s.get('tier')!r}")
        if not s.get("supports"):
            errs.append(f"sources.json: {s['id']} does not say what it supports")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s.get("checked", ""))):
            errs.append(f"sources.json: {s['id']} missing checked date")
    known = set(src_ids)

    def check_refs(where: str, ids) -> None:
        for i in ids or []:
            if i not in known:
                errs.append(f"{where}: unknown source id {i}")

    # ---------------- channels ----------------
    seen = set()
    for c in channels["channels"]:
        where = f"channels.json/{c.get('id')}"
        if not re.fullmatch(r"C\d{2}", c.get("id", "")):
            errs.append(f"channels.json: bad id {c.get('id')}")
        if c["id"] in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(c["id"])
        if c.get("status") not in STATUSES:
            errs.append(f"{where}: bad status {c.get('status')!r}")
        check_refs(where, c.get("sources"))
        if not c.get("sources"):
            errs.append(f"{where}: no sources at all")
        if "cap_verified" not in c:
            errs.append(f"{where}: cap_verified missing")
        cap = (c.get("cap") or "").strip()
        if cap and c.get("cap_verified") is not True:
            errs.append(f"{where}: cap stated but not marked verified")
        if not cap and c.get("cap_verified") is True:
            errs.append(f"{where}: cap empty but marked verified")
        for field in ("pros", "cons"):
            if not c.get(field):
                errs.append(f"{where}: {field} empty")
        if c.get("status") in {"prohibited", "criminal"} and c.get("cap"):
            warns.append(f"{where}: prohibited route has a cap text — check it reads correctly")

    # ---------------- taxes ----------------
    seen = set()
    for t in taxes["items"]:
        where = f"taxes.json/{t.get('id')}"
        if not re.fullmatch(r"T\d{2}", t.get("id", "")):
            errs.append(f"taxes.json: bad id {t.get('id')}")
        if t["id"] in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(t["id"])
        if t.get("jurisdiction") not in JURISDICTIONS:
            errs.append(f"{where}: bad jurisdiction {t.get('jurisdiction')!r}")
        if t.get("kind") not in KINDS:
            errs.append(f"{where}: bad kind {t.get('kind')!r}")
        check_refs(where, t.get("sources"))
        if t.get("verified") is False:
            if not t.get("flag"):
                errs.append(f"{where}: unverified but not flagged")
            if (t.get("amount") or "").strip() and not t.get("sources"):
                errs.append(f"{where}: unverified amount with no source and no explanation")

    # ---------------- penalties ----------------
    seen = set()
    for n in penalties["penalties"]:
        where = f"penalties.json/{n.get('id')}"
        if not re.fullmatch(r"N\d{2}", n.get("id", "")):
            errs.append(f"penalties.json: bad id {n.get('id')}")
        if n["id"] in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(n["id"])
        if n.get("layer") not in {1, 2, 3, 4, 5}:
            errs.append(f"{where}: bad layer {n.get('layer')!r}")
        check_refs(where, n.get("sources"))
        if n.get("verified") is False and not n.get("flag"):
            errs.append(f"{where}: unverified but not flagged")
        if n.get("verified") is False and (n.get("penalty") or "").strip() == "" and not n.get("flag"):
            errs.append(f"{where}: blank penalty with no flag")
        if n.get("max_pct") is not None or n.get("penalty"):
            if not n.get("sources"):
                errs.append(f"{where}: states a consequence with no source")

    for r in penalties["scenarios"]["rows"]:
        check_refs("penalties.json/scenarios", r.get("sources"))

    # ---------------- flagged ----------------
    seen = set()
    for f in flagged["items"]:
        where = f"flagged.json/{f.get('id')}"
        if not re.fullmatch(r"I\d{2}", f.get("id", "")):
            errs.append(f"flagged.json: bad id {f.get('id')}")
        if f["id"] in seen:
            errs.append(f"{where}: duplicate id")
        seen.add(f["id"])
        if f.get("status") not in FLAG_STATUSES:
            errs.append(f"{where}: bad status {f.get('status')!r}")
        check_refs(where, f.get("sources"))
        if not f.get("impact"):
            errs.append(f"{where}: no impact statement")

    # ---------------- coverage ----------------
    # every source should be cited at least once, otherwise it is dead weight
    cited = set()
    for coll, key in ((channels, "channels"), (taxes, "items"),
                      (penalties, "penalties"), (flagged, "items")):
        for row in coll[key]:
            cited.update(row.get("sources") or [])
    for row in penalties["scenarios"]["rows"]:
        cited.update(row.get("sources") or [])
    for sid in sorted(known - cited):
        warns.append(f"sources.json: {sid} is never cited")

    for w in warns:
        print(f"WARN  {w}")
    for e in errs:
        print(f"ERROR {e}")

    if errs:
        print(f"\n{len(errs)} error(s), {len(warns)} warning(s).")
        return 1
    print(f"OK — {len(src_ids)} sources, {len(channels['channels'])} channels, "
          f"{len(taxes['items'])} tax items, {len(penalties['penalties'])} penalties, "
          f"{len(flagged['items'])} flagged items, {len(warns)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
