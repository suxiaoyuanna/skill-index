#!/usr/bin/env python3
"""Merge LLM refinement results into the tagged index.

LLM output (state/batches/batch_*.result.json) is consolidated into a durable
state/llm_overrides.json keyed by skill id + the SKILL.md sha1 it was computed
from. On later incremental rebuilds the override is reused only while the hash
matches, so editing a SKILL.md automatically drops its stale override.

Note that the hash guard protects the overrides file, not the result files. A
batch_NN.result.json still sitting in the batches directory is input, and is
re-ingested on every run -- stamped with whatever hash the skill has at that
moment. Delete answers once they are merged, or they will re-classify a skill
you have since rewritten.

Writes output/skills_final.json.

Usage:
    python3 scripts/merge.py [--tagged ...] [--batches ...] [--overrides ...] [--out ...]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import CATEGORY_IDS, FALLBACK_ID  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

VALID = set(CATEGORY_IDS) | {FALLBACK_ID}


def norm_tags(raw) -> list[str]:
    """Coerce whatever the LLM produced into a tag list.

    A model handed `tags: "pcb"` returns the string, not a list. Iterating that
    yields eight single-character "tags", so normalize before the list
    comprehension rather than after.
    """
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return []
    return [str(t).strip().lower().replace(" ", "-") for t in raw if str(t).strip()][:8]


def load_overrides(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tagged", default=str(ROOT / "output" / "skills_tagged.json"))
    ap.add_argument("--batches", default=str(ROOT / "state" / "batches"))
    ap.add_argument("--overrides", default=str(ROOT / "state" / "llm_overrides.json"))
    ap.add_argument("--out", default=str(ROOT / "output" / "skills_final.json"))
    a = ap.parse_args()

    try:
        tagged = json.loads(Path(a.tagged).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no tagged index at {a.tagged}\nrun: python3 scripts/classify.py first",
              file=sys.stderr)
        return 1
    hash_by_id = {r["id"]: r.get("sha1", "") for r in tagged}

    ov_path = Path(a.overrides)
    overrides = load_overrides(ov_path)

    # Ingest new batch results
    ingested = 0
    for rf in sorted(Path(a.batches).glob("batch_*.result.json")):
        try:
            items = json.loads(rf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  !! skip {rf.name}: {e}", file=sys.stderr)
            continue
        if not isinstance(items, list):
            continue
        for it in items:
            sid = it.get("id")
            if not sid or sid not in hash_by_id:
                continue
            cat = it.get("category")
            if cat not in VALID:
                print(f"  !! bad category for {sid}: {cat}", file=sys.stderr)
                continue
            tags = norm_tags(it.get("tags"))
            overrides[sid] = {
                "category": cat,
                "tags": tags,
                "note": it.get("note", ""),
                "sha1": hash_by_id[sid],
            }
            ingested += 1

    ov_path.parent.mkdir(parents=True, exist_ok=True)
    ov_path.write_text(json.dumps(overrides, ensure_ascii=False, indent=1), encoding="utf-8")

    # Apply overrides whose hash still matches
    applied, stale = 0, 0
    out = []
    for r in tagged:
        ov = overrides.get(r["id"])
        if ov and ov.get("sha1") == r.get("sha1") and ov.get("sha1"):
            r = {**r,
                 "category": ov["category"],
                 # Normalize again on read: an overrides file written by an
                 # older version may still hold a bare string.
                 "tags": norm_tags(ov.get("tags")) or r["tags"],
                 "category_source": "llm",
                 "confidence": "llm"}
            applied += 1
        else:
            if ov:
                stale += 1
            r = {**r, "category_source": "rules"}
        out.append(r)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    import collections
    print(f"ingested={ingested}  overrides_total={len(overrides)}  applied={applied}  stale_hash={stale}",
          file=sys.stderr)
    print(f"category_source: {dict(collections.Counter(r['category_source'] for r in out))}", file=sys.stderr)
    cats = collections.Counter(r["category"] for r in out)
    print("\nfinal category distribution:", file=sys.stderr)
    for c, n in cats.most_common():
        print(f"  {c:22} {n:5}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
