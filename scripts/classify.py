#!/usr/bin/env python3
"""Rule-based classifier: assign category + tags + confidence to each skill.

Reads skills_index.json, writes skills_tagged.json and a list of low-confidence
skills that need LLM refinement (needs_llm.json).

Incremental: results are cached by SKILL.md sha1 in state/classify_cache.json,
so re-running after adding a few skills only reclassifies those skills.

The cache also carries a fingerprint of taxonomy.py itself. A cached answer is
only valid for the (content, rules) pair that produced it; without the second
half, editing the taxonomy leaves every skill hitting the cache and returning
the answer the old rules gave, so the edit looks like it did nothing.

Usage:
    python3 scripts/classify.py [--index ...] [--out ...] [--needs-llm ...] [--cache ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from taxonomy import CATEGORIES, FALLBACK_ID, ID_W, TECH_TAGS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Precompile
CAT_COMPILED = [
    {
        **c,
        "_id_re": [re.compile(p, re.I) for p in c.get("id_patterns", [])],
        "_kw_re": [re.compile(p, re.I) for p in c.get("keywords", [])],
    }
    for c in CATEGORIES
]
TAG_COMPILED = [(tag, re.compile(pat, re.I)) for tag, pat in TECH_TAGS.items()]


def score_categories(rec: dict) -> tuple[list[tuple[str, float, list[str]]], list[tuple[str, float, list[str]]]]:
    """Return (id_scores, keyword_scores) as [(cat_id, score, matched_patterns)]."""
    sid = rec["id"]
    blob = f'{rec["id"]} {rec["name"]} {rec["description"]}'
    id_scores, kw_scores = [], []
    for c in CAT_COMPILED:
        hits = [p.pattern for p in c["_id_re"] if p.search(sid)]
        id_scores.append((c["id"], min(len(hits), 2) * ID_W, hits))
        kh = [p.pattern for p in c["_kw_re"] if p.search(blob)]
        kw_scores.append((c["id"], min(len(kh), 4) * 2, kh))
    return id_scores, kw_scores


def classify_rules(rec: dict) -> dict:
    id_scores, kw_scores = score_categories(rec)
    total: dict[str, float] = {}
    evidence: dict[str, list[str]] = {}
    for cat, sc, hits in id_scores:
        total[cat] = total.get(cat, 0) + sc
        if hits:
            evidence.setdefault(cat, []).extend(f"id:{h}" for h in hits)
    for cat, sc, hits in kw_scores:
        total[cat] = total.get(cat, 0) + sc
        if hits:
            evidence.setdefault(cat, []).extend(f"kw:{h}" for h in hits)

    ranked = sorted(total.items(), key=lambda kv: -kv[1])
    top_cat, top_score = ranked[0] if ranked else (FALLBACK_ID, 0)
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    if top_score == 0:
        top_cat, level = FALLBACK_ID, "low"
    else:
        margin = top_score - second_score
        if top_score >= 6 and margin >= 4:
            level = "high"
        elif top_score >= 4 and margin >= 2:
            level = "medium"
        else:
            level = "low"

    tags = extract_tags(rec)
    return {
        "category": top_cat,
        "category_score": top_score,
        "category_margin": top_score - second_score,
        "confidence": level,
        "evidence": evidence.get(top_cat, [])[:6],
        "runners_up": [{"category": c, "score": s} for c, s in ranked[1:4] if s > 0],
        "tags": tags,
    }


def extract_tags(rec: dict) -> list[str]:
    blob = f'{rec["id"]} {rec["name"]} {rec["description"]}'
    tags: list[str] = []
    # Frontmatter-provided tags win, keep them first
    for src in ("tags", "triggers"):
        for t in rec.get(src) or []:
            t = str(t).strip().lower()
            if 2 < len(t) < 24 and t not in tags:
                tags.append(t)
    for tag, rx in TAG_COMPILED:
        if tag in tags:
            continue
        if rx.search(blob):
            tags.append(tag)
    return tags[:10]


def sha1_of(path: str) -> str:
    try:
        return hashlib.sha1(Path(path).read_bytes()).hexdigest()
    except OSError:
        return ""


RULES_PATH = Path(__file__).resolve().parent / "taxonomy.py"

# Reserved top-level key in the cache holding the fingerprint. Never a skill id:
# the write path skips it explicitly rather than trusting that no directory is
# ever named `__taxonomy__`.
CACHE_FINGERPRINT_KEY = "__taxonomy__"


def rules_fingerprint() -> str:
    """Hash of the file that decides what the rules *are*.

    The whole file is hashed, not the parsed CATEGORIES/TECH_TAGS structures.
    Hashing the data would be more precise -- editing a display label would no
    longer force a rebuild -- but it silently misses anything signal-bearing
    that is not in those two lists (ID_W, FALLBACK_ID, whatever gets added
    next). Missing a signal is the bug this exists to prevent and it is
    invisible; hashing a comment is merely a few wasted seconds.
    """
    try:
        return hashlib.sha1(RULES_PATH.read_bytes()).hexdigest()[:16]
    except OSError:
        # Unreadable rules: an empty fingerprint never equals a stored one, so
        # the cache is dropped and everything is reclassified. Degrade toward
        # recomputing, never toward reusing an answer of unknown provenance.
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=str(ROOT / "output" / "skills_index.json"))
    ap.add_argument("--out", default=str(ROOT / "output" / "skills_tagged.json"))
    ap.add_argument("--needs-llm", default=str(ROOT / "output" / "needs_llm.json"))
    ap.add_argument("--cache", default=str(ROOT / "state" / "classify_cache.json"))
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    try:
        records = json.loads(Path(args.index).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no index at {args.index}\nrun: python3 scripts/extract.py first", file=sys.stderr)
        return 1
    cache_path = Path(args.cache)
    fingerprint = rules_fingerprint()
    cache: dict = {}
    if cache_path.exists() and not args.no_cache:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        if not fingerprint or cache.get(CACHE_FINGERPRINT_KEY) != fingerprint:
            stale = len(cache) - (1 if CACHE_FINGERPRINT_KEY in cache else 0)
            if stale:
                print(f"taxonomy changed -> reclassifying all {stale} cached skills",
                      file=sys.stderr)
            # Fingerprint mismatch covers a pre-fingerprint cache too, so the
            # first run after upgrading rebuilds once and is self-migrating.
            cache = {}
        cache.pop(CACHE_FINGERPRINT_KEY, None)

    new_cache: dict = {CACHE_FINGERPRINT_KEY: fingerprint}
    out_records, needs_llm = [], []
    reused = 0
    for rec in records:
        h = sha1_of(rec["path"])
        key = rec["id"]
        cached = cache.get(key)
        if cached and cached.get("sha1") == h and h:
            result = cached["result"]
            reused += 1
        else:
            result = classify_rules(rec)
        if key != CACHE_FINGERPRINT_KEY:
            new_cache[key] = {"sha1": h, "result": result}

        merged = {**rec, **result, "sha1": h}
        out_records.append(merged)
        if result["confidence"] == "low":
            needs_llm.append(
                {
                    "id": rec["id"],
                    "name": rec["name"],
                    "description": rec["description"],
                    "category_guess": result["category"],
                    "tags": result["tags"],
                }
            )

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out_records, ensure_ascii=False, indent=1), encoding="utf-8")
    Path(args.needs_llm).write_text(json.dumps(needs_llm, ensure_ascii=False, indent=1), encoding="utf-8")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(new_cache, ensure_ascii=False), encoding="utf-8")

    import collections
    conf = collections.Counter(r["confidence"] for r in out_records)
    cats = collections.Counter(r["category"] for r in out_records)
    print(f"total={len(out_records)}  reused_from_cache={reused}", file=sys.stderr)
    print(f"confidence: {dict(conf)}", file=sys.stderr)
    print(f"needs_llm : {len(needs_llm)}", file=sys.stderr)
    print("\ncategory distribution:", file=sys.stderr)
    for c, n in cats.most_common():
        print(f"  {c:22} {n:5}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
