"""Rule classifier and its hash-keyed incremental cache."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import support  # noqa: E402
import classify  # noqa: E402
from classify import classify_rules, extract_tags  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Pinned from the fixture corpus. Each row is (category, confidence); the point
# is that changing any of them is a deliberate act, not an accident.
EXPECTED = {
    "kicad-board-layout": ("hardware-eda", "high"),
    "security-audit": ("security", "high"),
    "pdf-forms": ("docs-writing", "high"),
    "playwright-e2e": ("testing-qa", "high"),
    "seo-audit": ("marketing-growth", "high"),
    "competitor-analysis": ("research", "high"),
    "changelog-writer": ("devops-cicd", "high"),
    "alias-pointer": ("docs-writing", "low"),
    "foo-py": ("languages", "low"),
    "foo-ts": ("languages", "low"),
    "kw-receiver": ("other", "low"),
    "zombie-thing": ("other", "low"),
    "nested-meta": ("other", "low"),
}


class TestRules(support.TempCase):
    def test_expected_category_and_confidence(self):
        support.build_index(self.paths)
        got = {r["id"]: (r["category"], r["confidence"]) for r in support.records(self.paths)}
        for sid, want in EXPECTED.items():
            self.assertEqual(got[sid], want, f"{sid}: got {got[sid]}, want {want}")

    def test_id_pattern_outranks_keyword_density(self):
        """An id hit is worth 10; a description keyword is worth 2. A kicad-*
        skill whose description is stuffed with security words stays hardware,
        because no security *id pattern* matches its name."""
        rec = _rec("kicad-review-tool",
                   "Vulnerability pentest OWASP threat model compliance audit secrets "
                   "exploit malware forensic encryption")
        self.assertEqual(classify_rules(rec)["category"], "hardware-eda")

    def test_unanchored_id_patterns_match_mid_name(self):
        """Documents a deliberate choice: several id patterns (notably
        `security`, and every `^foo` pattern's unanchored cousins) are not
        anchored, so `foo-security-audit` classifies as security without
        needing a pattern per prefix. The cost is that an ambiguous name like
        `kicad-security-thing` resolves by score, not by prefix -- here the
        security keywords outvote the hardware id hit."""
        rec = _rec("kicad-security-thing",
                   "Vulnerability pentest OWASP threat model compliance audit secrets")
        res = classify_rules(rec)
        self.assertEqual(res["category"], "security")
        self.assertGreater(res["category_score"], 0)

    def test_zero_signal_falls_back_to_other(self):
        res = classify_rules(_rec("qqq-zzz", "Wibble wobble."))
        self.assertEqual(res["category"], "other")
        self.assertEqual(res["confidence"], "low")
        self.assertEqual(res["category_score"], 0)

    def test_low_confidence_records_are_listed_for_refinement(self):
        support.build_index(self.paths)
        pending = json.loads(self.paths.needs_llm.read_text(encoding="utf-8"))
        low = {r["id"] for r in support.records(self.paths) if r["confidence"] == "low"}
        self.assertEqual({r["id"] for r in pending}, low)
        self.assertTrue(low)
        for item in pending:
            self.assertIn("category_guess", item)
            self.assertIn("description", item)

    def test_frontmatter_tags_come_before_derived_ones(self):
        tags = extract_tags(_rec("x", "react frontend", tags=["custom-one"]))
        self.assertEqual(tags[0], "custom-one")

    def test_tags_are_capped_and_deduplicated(self):
        tags = extract_tags(_rec("x", "react react react vue angular svelte next.js "
                                      "tailwind css html three.js webgl", tags=["a", "a"]))
        self.assertLessEqual(len(tags), 10)
        self.assertEqual(len(tags), len(set(tags)))


class TestCache(support.TempCase):
    def _classify(self, **extra):
        args = ["--index", self.paths.index, "--out", self.paths.tagged,
                "--needs-llm", self.paths.needs_llm, "--cache", self.paths.cache]
        for k, v in extra.items():
            args.append(f"--{k.replace('_', '-')}" if v is True else f"--{k.replace('_', '-')}={v}")
        real = classify.classify_rules
        with mock.patch.object(classify, "classify_rules", wraps=real) as spy:
            support._argv(classify.main, *args)
        return spy.call_count

    def setUp(self):
        super().setUp()
        from extract import main as extract_main
        support._argv(extract_main, "--roots", self.paths.roots_arg, "--out", self.paths.index)

    def test_second_run_reclassifies_nothing(self):
        first = self._classify()
        self.assertGreater(first, 0)
        self.assertEqual(self._classify(), 0)

    def test_editing_one_skill_reclassifies_exactly_that_one(self):
        self._classify()
        target = self.paths.user / "kicad-board-layout" / "SKILL.md"
        target.write_text(
            '---\nname: kicad-board-layout\ndescription: "Now it does something else."\n---\n',
            encoding="utf-8")
        self.assertEqual(self._classify(), 1)

    def test_no_cache_reclassifies_everything(self):
        count = len(json.loads(self.paths.index.read_text(encoding="utf-8")))
        self.assertEqual(self._classify(no_cache=True), count)

    def test_editing_the_taxonomy_reclassifies_everything(self):
        """The bug this guards: the cache carried only the SKILL.md hash, so
        editing taxonomy.py changed what the classifier should say while every
        skill still hit the cache and returned the old answer. The edit
        silently did nothing, and refresh.py gave no way to force it -- which
        is exactly the workflow the README recommends.

        RULES_PATH is redirected at a scratch copy rather than editing the
        shipped taxonomy, which the rest of the suite is running against.
        """
        rules = self.paths.tmp / "taxonomy.py"
        rules.write_text("# rules v1\n", encoding="utf-8")
        with mock.patch.object(classify, "RULES_PATH", rules):
            self.assertGreater(self._classify(), 0)
            self.assertEqual(self._classify(), 0)       # same rules -> cached
            rules.write_text("# rules v2\n", encoding="utf-8")
            self.assertGreater(self._classify(), 0)     # new rules -> rebuild

    def test_a_cache_written_before_fingerprints_is_discarded(self):
        """Self-migration: an existing cache has no fingerprint to compare, so
        it must be rebuilt once rather than trusted forever."""
        self._classify()
        cache = json.loads(self.paths.cache.read_text(encoding="utf-8"))
        cache.pop(classify.CACHE_FINGERPRINT_KEY)
        self.paths.cache.write_text(json.dumps(cache), encoding="utf-8")
        count = len(json.loads(self.paths.index.read_text(encoding="utf-8")))
        self.assertEqual(self._classify(), count)

    def test_the_fingerprint_sits_alongside_the_skill_entries(self):
        """A skill directory really could be named `__taxonomy__`, so the write
        path skips that id rather than assuming it cannot happen."""
        self._classify()
        cache = json.loads(self.paths.cache.read_text(encoding="utf-8"))
        self.assertEqual(cache[classify.CACHE_FINGERPRINT_KEY],
                         classify.rules_fingerprint())
        for sid, entry in cache.items():
            if sid != classify.CACHE_FINGERPRINT_KEY:
                self.assertIsInstance(entry, dict, sid)

    def test_the_fingerprint_is_taken_from_the_shipped_taxonomy(self):
        self.assertEqual(classify.RULES_PATH, ROOT / "scripts" / "taxonomy.py")
        self.assertTrue(classify.rules_fingerprint())

    def test_cache_is_keyed_by_content_not_by_id(self):
        self._classify()
        cache = json.loads(self.paths.cache.read_text(encoding="utf-8"))
        before = cache["kicad-board-layout"]["sha1"]
        (self.paths.user / "kicad-board-layout" / "SKILL.md").write_text(
            '---\nname: kicad-board-layout\ndescription: "Different."\n---\n',
            encoding="utf-8")
        self._classify()
        after = json.loads(self.paths.cache.read_text(encoding="utf-8"))
        self.assertNotEqual(before, after["kicad-board-layout"]["sha1"])


def _rec(sid: str, desc: str, **kw) -> dict:
    return {"id": sid, "name": sid, "description": desc, **kw}


if __name__ == "__main__":
    unittest.main(verbosity=2)
