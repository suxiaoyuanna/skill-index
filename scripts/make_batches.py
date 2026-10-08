#!/usr/bin/env python3
"""Split needs_llm.json into batch files for parallel LLM classification.

Optional step. Only needed if you want the semantic refinement pass: the rule
classifier handles most skills on its own, and this splits the ones it was not
confident about into chunks you (or an agent) can classify by hand or with a
model. See README "Optional: LLM refinement" for the round trip.

Writes batch_NN.json (inputs) and _manifest.json. Never touches
batch_NN.result.json -- those are your answers, and they are expensive to
reproduce.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from taxonomy import ALL_CATEGORIES, desc, label  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Pinned rather than left to the locale, like every other stage: batch files
# carry skill ids and descriptions that may not be ASCII.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Language of the category vocabulary handed to the classifier. English by
# default so the prompts this feeds are readable to most contributors.
CAT_LABELS = ("en", "zh")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(ROOT / "output" / "needs_llm.json"))
    ap.add_argument("--dir", default=str(ROOT / "state" / "batches"))
    ap.add_argument("--size", type=int, default=30)
    ap.add_argument("--out", default=None, help="manifest path (default: <dir>/_manifest.json)")
    ap.add_argument("--lang", default="en", choices=CAT_LABELS)
    a = ap.parse_args()

    outdir = Path(a.dir)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(a.out) if a.out else outdir / "_manifest.json"

    try:
        recs = json.loads(Path(a.inp).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no needs_llm.json at {a.inp}\n"
              f"run refresh.py first; if it reports 0 pending, there is nothing to refine.",
              file=sys.stderr)
        return 1

    # Only batch_NN.json -- never batch_NN.result.json. A bare "batch_*.json"
    # glob matches the result files too and would silently delete unmerged work.
    for old in outdir.glob("batch_[0-9][0-9].json"):
        old.unlink()

    cats = [{"id": c["id"], "label": label(c, a.lang), "desc": desc(c, a.lang)}
            for c in ALL_CATEGORIES]

    manifest = []
    for i in range(0, len(recs), a.size):
        chunk = recs[i:i + a.size]
        n = i // a.size
        p = outdir / f"batch_{n:02d}.json"
        p.write_text(
            json.dumps({"categories": cats, "skills": chunk}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        manifest.append({"batch": n, "path": p.name, "count": len(chunk)})

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(manifest)} batches, {len(recs)} skills -> {outdir}", file=sys.stderr)
    if recs:
        print(f"\nFill in your answers as {outdir}/batch_NN.result.json -- a bare JSON array of\n"
              f'  {{"id": "...", "category": "...", "tags": ["..."]}}\n'
              f"then re-run refresh.py to merge them.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
