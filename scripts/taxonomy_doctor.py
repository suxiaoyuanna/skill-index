#!/usr/bin/env python3
"""Report how well the shipped taxonomy fits *your* skill library.

`taxonomy.py` ships tuned against one library. Everybody's library is different,
so the honest question is not "is this taxonomy good" but "is it good *here*" --
and that should be a number, not a guess. This prints the three numbers that
answer it:

  * how much fell through to `other`, and whether that is a missing category
    (skills sharing a name family) or a long tail (skills sharing nothing),
  * which category is oversized enough that browsing it is useless,
  * how much of the library is still low confidence.

Every line it emits is a suggestion to a human. It changes nothing.

Usage: python3 scripts/taxonomy_doctor.py [index.json] [--lang en|zh]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from i18n import DEFAULT_LANG, LANGS, t  # noqa: E402
from taxonomy import FALLBACK_ID  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

# Heuristic thresholds, chosen to be readable rather than measured. They decide
# whether something is worth a second look; they never decide anything on their
# own, because every finding below ends in a suggestion to a human.
FAMILY_MIN = 5      # a name family this big in `other` suggests a real category
OTHER_SHARE = 0.02  # below this, an `other` bucket is not worth mentioning
BUCKET_X = 2.0      # a category this many times the average is too coarse
BUCKET_MIN = 40     # ...and only if it is big in absolute terms
LOW_SHARE = 0.25    # this much low confidence suggests running the LLM pass

# Language and runtime suffixes. They are not domains, so they are not answers
# to "what should I split this category by" -- `py (36)` inside cloud-infra
# means one capability shipped per-language, which the governance report
# already covers under language variants. The list is curated, not exhaustive:
# a miss costs a slightly noisier report, never a wrong suggestion, because
# nothing here acts on its own.
NOT_A_DOMAIN = {
    "py", "python", "ts", "js", "java", "dotnet", "net", "go", "golang", "rb",
    "ruby", "rs", "rust", "cpp", "csharp", "node", "php", "kotlin", "swift",
    "expo", "sdk", "cli", "api",
}

SPLIT = re.compile(r"[-_]")


def name_families(ids, min_size: int = 2, top: int = 5,
                  exclude: set[str] | None = None) -> list[tuple[str, int]]:
    """Name fragments that group skills, largest first.

    Two tokenizations, because the interesting family is not always in the same
    place: `cloud-infra` is dominated by `azure-ai-*-{py,java,ts}` (first
    segment), while `office-automation` is dominated by `*-automation`
    (last segment). Taking the larger of the two counts per token means a name
    is reported once, at its best reading.

    Only fragments at least 2 characters long count -- one-letter segments come
    from names like `x-y` and group things that have nothing to do with each
    other.

    `exclude` drops tokens the caller already knows are uninformative. For the
    split suggestion that is the category's own name: `office-automation` is
    dominated by `automation`, which only says the bucket contains what it is
    named after, and "split automation by automation" is not a suggestion.
    """
    skip = {t.lower() for t in (exclude or ())}
    first: collections.Counter = collections.Counter()
    last: collections.Counter = collections.Counter()
    for sid in ids:
        parts = [p for p in SPLIT.split(sid) if p]
        if not parts:
            continue
        first[parts[0]] += 1
        last[parts[-1]] += 1
    merged: collections.Counter = collections.Counter()
    for counter in (first, last):
        for token, n in counter.items():
            low = token.lower()
            if len(token) >= 2 and n >= min_size and low not in NOT_A_DOMAIN and low not in skip:
                merged[token] = max(merged[token], n)
    return merged.most_common(top)


def render_families(pairs, lang: str) -> str:
    return ", ".join(t(lang, "doc.fams", fam=f, n=n) for f, n in pairs)


def report(records: list[dict], lang: str, out=sys.stdout) -> int:
    total = len(records)
    cats = collections.Counter(r.get("category") or FALLBACK_ID for r in records)
    other = [r for r in records if (r.get("category") or FALLBACK_ID) == FALLBACK_ID]
    n_cats = len([c for c in cats if c != FALLBACK_ID])

    print(t(lang, "doc.title", n=total, cats=n_cats), file=out)
    print("=" * 62, file=out)
    pct = lambda n: (n * 100.0 / total) if total else 0.0  # noqa: E731
    print(t(lang, "doc.coverage", n=len(other), pct=pct(len(other)), cat=FALLBACK_ID),
          file=out)
    conf = collections.Counter(r.get("confidence") or "low" for r in records)
    print(t(lang, "doc.confidence", hi=conf["high"], med=conf["medium"], lo=conf["low"],
            lopct=pct(conf["low"])), file=out)

    # `other` has its own line above; repeating it as the "largest category"
    # just says the library is mostly unclassified, which that line already did.
    print(f"\n{t(lang, 'doc.h_buckets')}", file=out)
    for cid, n in cats.most_common(3):
        if cid != FALLBACK_ID:
            print(t(lang, "doc.bucket", cat=cid, n=n, pct=pct(n)), file=out)

    findings: list[str] = []
    families = name_families([r["id"] for r in other], min_size=FAMILY_MIN)
    if families:
        # A family this big is a domain the taxonomy has no word for, so naming
        # it as a category would claim those skills at a stroke.
        for token, n in families[:3]:
            findings.append(t(lang, "doc.f_add", fam=token, n=n, cat=FALLBACK_ID))
    elif len(other) >= 3 and total and len(other) / total >= OTHER_SHARE:
        # The size of the largest family is the number that matters -- it is
        # what fell short of FAMILY_MIN. Reporting a count of families instead
        # reads as "lots of variety" no matter what it says.
        named = name_families([r["id"] for r in other], min_size=2, top=1)
        findings.append(t(lang, "doc.f_longtail", cat=FALLBACK_ID, n=len(other),
                          fam=named[0][1] if named else 1, min=FAMILY_MIN))

    # Relative to this library, not to a fixed share: "too big to browse" is a
    # question about the shape of *your* distribution, and a library of 200
    # skills and a library of 5000 do not have the same answer. BUCKET_MIN
    # keeps a small library from flagging a 6-skill category for being 3x the
    # average of a 2-skill one.
    filled = [n for cid, n in cats.items() if cid != FALLBACK_ID]
    mean = (sum(filled) / len(filled)) if filled else 0
    for cid, n in cats.most_common(3):
        if cid == FALLBACK_ID or not mean or n < BUCKET_MIN or n / mean < BUCKET_X:
            continue
        fams = name_families([r["id"] for r in records
                              if (r.get("category") or FALLBACK_ID) == cid],
                             top=4, exclude=set(SPLIT.split(cid)))
        findings.append(t(lang, "doc.f_split", cat=cid, n=n, pct=pct(n),
                          fams=render_families(fams, lang)))

    if total and conf["low"] / total >= LOW_SHARE:
        findings.append(t(lang, "doc.f_low", n=conf["low"], pct=pct(conf["low"])))

    print(f"\n{t(lang, 'doc.h_findings')}", file=out)
    if findings:
        for line in findings:
            print("  " + line, file=out)
    else:
        print("  " + t(lang, "doc.f_none"), file=out)

    print(f"\n{t(lang, 'doc.hint')}", file=out)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("index", nargs="?", default=str(ROOT / "output" / "skills_final.json"))
    ap.add_argument("--lang", choices=LANGS, default=DEFAULT_LANG,
                    help="language of the report (default: %(default)s)")
    a = ap.parse_args()

    path = Path(a.index)
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no index at {path}\nrun: python3 scripts/refresh.py", file=sys.stderr)
        return 1

    if not records:
        # A machine with no skills installed lands here. There is nothing to
        # diagnose yet, and that is not a failure.
        print(t(a.lang, "doc.title", n=0, cats=0))
        print("=" * 62)
        print("Nothing indexed yet. Run refresh.py once there are skills to index.")
        return 0
    return report(records, a.lang)


if __name__ == "__main__":
    raise SystemExit(main())
