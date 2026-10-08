#!/usr/bin/env python3
"""Print coverage stats for a skills index JSON.

Usage: python3 scripts/stats.py [index.json]
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output" / "skills_index.json"
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no index at {path}\nrun: python3 scripts/refresh.py")
        return 1

    print("total", len(records))
    if not records:
        # A machine with no skills installed lands here, so this is a normal
        # state, not an error -- the percentage and percentile maths below
        # would divide by zero and index an empty list.
        print("\nNothing indexed. Skill roots were empty or missing.")
        print("Pass --roots label=path to refresh.py to point at another directory.")
        return 0

    for k in ["description", "triggers", "tags", "category", "domain", "role",
              "scope", "license", "risk", "source", "related", "allowed_tools"]:
        n = sum(1 for r in records if r.get(k))
        print(f"{k:16} {n:5}  {n * 100 // len(records)}%")

    print("\nroot:", dict(collections.Counter(r["root"] for r in records)))
    print("no_frontmatter:", sum(1 for r in records if not r["has_frontmatter"]))
    lens = sorted(r["desc_len"] for r in records)
    print(f"desc_len  min={lens[0]} p25={lens[len(lens)//4]} median={lens[len(lens)//2]} "
          f"p75={lens[3*len(lens)//4]} max={lens[-1]}")

    print("\n--- sample rows (every 300th) ---")
    for r in records[::300]:
        print(f"* {r['id']}\n    {r['description'][:160]}")

    # Deliberately the BMP "CJK Unified Ideographs" block only: it is a cheap
    # heuristic for "does this description contain Chinese/Japanese text", and
    # widening it to extension planes would cost more than it is worth here.
    print("\n--- description non-ASCII (likely Chinese) ---")
    zh = [r["id"] for r in records if any("一" <= c <= "鿿" for c in r["description"])]
    print(len(zh), zh[:15])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
