#!/usr/bin/env python3
"""Peek at raw records in an index JSON.

Debugging aid for the pipeline stages -- for actually finding a skill, use
skillfind.py instead.

Usage: python3 scripts/peek.py <index.json> [--cat ID] [--conf LEVEL] [--limit N]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--conf", default=None, help="filter by confidence")
    ap.add_argument("--cat", default=None, help="filter by category")
    ap.add_argument("--fields", default="id,category,confidence,tags,description")
    ap.add_argument("--start", type=int, default=0)
    a = ap.parse_args()

    try:
        recs = json.loads(Path(a.path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no index at {a.path}\nrun: python3 scripts/refresh.py")
        return 1

    if a.conf:
        recs = [r for r in recs if r.get("confidence") == a.conf]
    if a.cat:
        recs = [r for r in recs if r.get("category") == a.cat]
    recs = recs[a.start:a.start + a.limit]
    fields = a.fields.split(",")

    for r in recs:
        extra = f"  [score={r.get('category_score')} margin={r.get('category_margin')}]" \
            if "category_score" in r else ""
        print(f"### {r['id']}{extra}")
        for f in fields:
            if f == "id":
                continue
            v = r.get(f)
            if not v:
                continue
            if f == "description":
                v = str(v)[:230]
            if f in ("evidence", "runners_up", "tags") and isinstance(v, list):
                v = ", ".join(str(x) for x in v)
            print(f"    {f}: {v}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
