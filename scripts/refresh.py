#!/usr/bin/env python3
"""Rebuild the skill index end-to-end, incrementally.

    python3 scripts/refresh.py                # full pipeline, prints a summary
    python3 scripts/refresh.py --quiet        # silent unless something changed (hook mode)
    python3 scripts/refresh.py --check        # report drift only, write nothing
    python3 scripts/refresh.py --lang zh      # generate the lookup tables in Chinese
    python3 scripts/refresh.py --roots "user=~/.claude/skills,plugin=~/plugins"
    python3 scripts/refresh.py --no-cache    # ignore the classification cache

Stages: extract -> classify (hash-cached) -> merge -> report.

Incremental behaviour:
  * `classify.py` reuses cached rule results for unchanged SKILL.md files.
  * `merge.py` reuses LLM overrides while the file hash still matches.
  * New/changed skills that land in low confidence are listed for LLM refinement
    (scripts/make_batches.py + dispatch), and are searchable meanwhile.

Every stage is invoked as a subprocess with this interpreter, so a hook can run
refresh.py from any working directory.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from i18n import DEFAULT_LANG, LANGS, t  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
PY = sys.executable or "python3"
STATE = ROOT / "state"
MANIFEST = STATE / "last_run.json"

# Stages that read an index and write the next one. Names are used for the
# summary line; the files must exist next to this script.
STAGES = [
    ("extract", "extract.py", ["--out", str(ROOT / "output" / "skills_index.json")]),
    ("classify", "classify.py", []),
    ("merge", "merge.py", []),
    ("report", "report.py", []),
]


def run(script: str, *args: str, lang: str | None = None) -> subprocess.CompletedProcess:
    cmd = [PY, str(SCRIPTS / script), *args]
    if lang:
        cmd += ["--lang", lang]
    # No -I: it implies -E and -s, which would hide a user-installed PyYAML and
    # ignore PYTHONIOENCODING. The stages anchor their own paths, so the working
    # directory does not matter and neither does the isolated-import hardening.
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check", action="store_true", help="report drift, change nothing")
    ap.add_argument("--lang", choices=LANGS, default=DEFAULT_LANG,
                    help="language of the generated lookup tables (default: %(default)s)")
    ap.add_argument("--roots", default=None,
                    help="comma-separated skill roots as label=path (passed to extract.py)")
    ap.add_argument("--no-cache", action="store_true",
                    help="reclassify every skill, ignoring state/classify_cache.json. "
                         "Editing taxonomy.py already does this on its own; this is "
                         "the escape hatch for a cache you suspect is wrong")
    ap.add_argument("--allow-llm-gap", action="store_true",
                    help="do not flag skills awaiting LLM refinement as drift")
    a = ap.parse_args()

    t0 = time.time()
    prev = {}
    if MANIFEST.exists():
        try:
            prev = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = {}

    if a.check:
        idx = ROOT / "output" / "skills_index.json"
        if not idx.exists():
            print("no index yet - run: python3 scripts/refresh.py")
            return 1
        cur = len(json.loads(idx.read_text(encoding="utf-8")))
        old = prev.get("total_skills", 0)
        print(f"indexed={cur}  last_run={old}  delta={cur - old:+d}")
        return 0

    summaries: dict[str, str] = {}
    for name, script, extra in STAGES:
        if name == "extract" and a.roots:
            extra = extra + ["--roots", a.roots]
        if name == "classify" and a.no_cache:
            extra = extra + ["--no-cache"]
        r = run(script, *extra, lang=a.lang if name == "report" else None)
        if r.returncode != 0:
            print(f"[refresh] stage {name} FAILED (exit {r.returncode})", file=sys.stderr)
            print(r.stdout[-2000:], file=sys.stderr)
            print(r.stderr[-3000:], file=sys.stderr)
            return r.returncode
        combined = (r.stderr or r.stdout).strip()
        summaries[name] = combined.splitlines()[-1] if combined else ""
        if name == "extract" and a.lang == DEFAULT_LANG:
            # extract reports how many skills it found; surface it immediately
            # so a long first run is not silent.
            head = combined.splitlines()[0] if combined else ""
            if head and not a.quiet:
                print(f"[refresh] {head}", file=sys.stderr)

    final_path = ROOT / "output" / "skills_final.json"
    try:
        final = json.loads(final_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[refresh] stage report produced no index at {final_path}", file=sys.stderr)
        return 1
    total = len(final)
    pending_llm = sum(1 for r in final if r.get("confidence") == "low")

    manifest = {
        "last_run": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_skills": total,
        "pending_llm": pending_llm,
        "lang": a.lang,
        "duration_s": round(time.time() - t0, 1),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    prev_total = prev.get("total_skills", total)
    added = total - prev_total
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    if a.quiet and added == 0 and prev:
        return 0
    if a.quiet:
        print(f"[skill-index] {prev_total} -> {total} ({added:+d}) in {manifest['duration_s']}s")
        if pending_llm and not a.allow_llm_gap:
            print(f"[skill-index] {pending_llm} skills awaiting semantic refinement: "
                  f'"{PY}" "{SCRIPTS / "make_batches.py"}"')
        return 0

    print("\n" + t(a.lang, "refresh.done", secs=manifest["duration_s"]))
    print(f"skills          : {total}  (was {prev_total}, {added:+d})")
    print(f"awaiting LLM    : {pending_llm}")
    print(f"index           : {final_path}")
    print(f"lookup table    : {ROOT / 'docs' / 'SKILLS.md'}")
    print(f"routing table   : {ROOT / 'docs' / 'ROUTER.md'}")
    for k, v in summaries.items():
        if v:
            print(f"  {k:9}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
