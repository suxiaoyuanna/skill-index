"""Shared test helpers: materialize the fixture corpus and drive the pipeline.

Everything here takes paths from the caller. Nothing reads or writes the real
`output/`, `state/` or `docs/` directories, so running the suite can never
damage a working index.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = TESTS / "fixtures"

sys.path[:0] = [str(SCRIPTS), str(TESTS)]


def corpus() -> list[dict]:
    return json.loads((FIXTURES / "corpus.json").read_text(encoding="utf-8"))["skills"]


class Paths:
    """Every file a test may touch, derived from one temporary directory."""

    def __init__(self, tmp: Path):
        self.tmp = Path(tmp)
        self.user = self.tmp / "user"
        self.plugin = self.tmp / "plugin"
        self.output = self.tmp / "output"
        self.state = self.tmp / "state"
        self.batches = self.state / "batches"
        self.docs = self.tmp / "docs"
        for d in (self.user, self.plugin, self.output, self.state, self.batches, self.docs):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def roots_arg(self) -> str:
        return f"user={self.user},plugin={self.plugin}"

    @property
    def index(self) -> Path:
        return self.output / "skills_index.json"

    @property
    def tagged(self) -> Path:
        return self.output / "skills_tagged.json"

    @property
    def needs_llm(self) -> Path:
        return self.output / "needs_llm.json"

    @property
    def final(self) -> Path:
        return self.output / "skills_final.json"

    @property
    def cache(self) -> Path:
        return self.state / "classify_cache.json"

    @property
    def overrides(self) -> Path:
        return self.state / "llm_overrides.json"


def materialize(dest: Path) -> Paths:
    """Write the fixture corpus out as a real SKILL.md tree."""
    paths = Paths(dest)
    for entry in corpus():
        base = paths.user if entry["root"] == "user" else paths.plugin
        target = base / entry["relpath"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "SKILL.md").write_text(entry["raw"], encoding="utf-8", newline="")
    return paths


def run_script(name: str, *args: str) -> tuple[int, str]:
    """Invoke a pipeline stage in-process with a synthetic argv."""
    import importlib
    mod = importlib.import_module(name)
    old_argv = sys.argv
    sys.argv = [name, *[str(a) for a in args]]
    try:
        rc = mod.main()
    finally:
        sys.argv = old_argv
    return rc, ""


def build_index(paths: Paths) -> None:
    """Run extract -> classify -> merge, leaving skills_final.json on disk."""
    from classify import main as classify_main
    from extract import main as extract_main
    from merge import main as merge_main

    _argv(extract_main, "--roots", paths.roots_arg, "--out", paths.index)
    _argv(classify_main, "--index", paths.index, "--out", paths.tagged,
          "--needs-llm", paths.needs_llm, "--cache", paths.cache)
    _argv(merge_main, "--tagged", paths.tagged, "--batches", paths.batches,
          "--overrides", paths.overrides, "--out", paths.final)


def _argv(fn, *args) -> int:
    old = sys.argv
    sys.argv = [fn.__module__, *[str(a) for a in args]]
    try:
        return fn()
    finally:
        sys.argv = old


def records(paths: Paths) -> list[dict]:
    return json.loads(paths.final.read_text(encoding="utf-8"))


def searcher(paths: Paths):
    """A Searcher over the built index, with labels injected as load() does."""
    from skillfind import Searcher, load
    recs, cats = load(str(paths.final))
    return Searcher(recs, cats)


def ids(results) -> list[str]:
    return [r["id"] for _, r in results]


def en_only(recs: list[dict]) -> list[dict]:
    """Corpus subset with no Chinese anywhere, for the i18n completeness check."""
    import re
    han = re.compile(r"[一-鿿]")
    return [r for r in recs
            if not han.search(r.get("description", "") or "")
            and not han.search(r.get("name", "") or "")
            and not han.search(r.get("id", "") or "")]


class TempCase(unittest.TestCase):
    """Base class: a materialized corpus in a temporary directory, per test."""

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="skill-index-test-")
        self.paths = materialize(self._tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)
