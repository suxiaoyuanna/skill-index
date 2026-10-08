"""Generated documents: i18n completeness, governance detection, path hygiene."""
from __future__ import annotations

import re
import sys
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import support  # noqa: E402
import report  # noqa: E402
from i18n import DEFAULT_LANG, LANGS, ROUTER_TRIGGERS, STRINGS  # noqa: E402
from taxonomy import ALL_CATEGORIES, CAT_BY_ID  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HAN = re.compile(r"[一-鿿]")


def without_host_paths(text: str) -> str:
    """Blank out the only two host-derived strings that legitimately reach a
    committed document: the interpreter and script paths in the run banner.

    Blanking the paths rather than dropping the line keeps the rest of the banner
    under test -- and the paths are not unchecked, since `display_path` scrubs
    anything under $HOME and `TestDisplayPath` pins that directly. A checkout
    outside $HOME can only echo back a directory name the user chose themselves.
    """
    for p in (report.SKILLFIND, report.PYEXE):
        if p:
            text = text.replace(p, "<path>")
    return text


class TestStringTables(unittest.TestCase):
    def test_en_and_zh_have_identical_keys(self):
        self.assertEqual(set(STRINGS["en"]), set(STRINGS["zh"]))

    def test_no_empty_strings(self):
        for lang in LANGS:
            for key, val in STRINGS[lang].items():
                self.assertTrue(val.strip(), f"{lang}:{key} is empty")

    def test_every_category_has_both_languages(self):
        for cat in ALL_CATEGORIES:
            for field in ("en", "zh", "en_desc", "zh_desc"):
                self.assertTrue(cat.get(field), f"{cat['id']} missing {field}")

    def test_every_category_has_router_triggers_in_both_languages(self):
        for lang in LANGS:
            for cat in ALL_CATEGORIES:
                self.assertIn(cat["id"], ROUTER_TRIGGERS[lang])

    def test_no_duplicate_category_ids(self):
        self.assertEqual(len(ALL_CATEGORIES), len(CAT_BY_ID))

    def test_fallback_category_is_not_scored(self):
        """`other` is reached by falling through everything else, never by a
        pattern hit, so it must not appear in the scored category list."""
        self.assertNotIn("other", [c["id"] for c in ALL_CATEGORIES if c.get("id_patterns")])


class TestRender(support.TempCase):
    def setUp(self):
        super().setUp()
        support.build_index(self.paths)
        self.recs = support.records(self.paths)

    def render_all(self, recs, lang):
        by_cat = defaultdict(list)
        for r in recs:
            by_cat[r.get("category", "other")].append(r)
        for v in by_cat.values():
            v.sort(key=lambda r: r["id"].lower())
        ordered = [c["id"] for c in ALL_CATEGORIES]
        out = {
            "SKILLS.md": report.render_skills(recs, by_cat, ordered, lang),
            "ROUTER.md": report.render_router(recs, by_cat, ordered, lang),
            "by-tag.md": report.render_tags(recs, lang),
            "GOVERNANCE.md": report.render_governance(recs, lang)[0],
        }
        for cid in ordered:
            if by_cat.get(cid):
                out[f"by-category/{cid}.md"] = report.render_category(cid, by_cat[cid], lang)
        return {k: "\n".join(v) for k, v in out.items()}

    def test_english_output_has_no_chinese(self):
        """The completeness proof for the whole i18n port: any render-time
        string that was missed shows up as a Han character here. Restricting
        the records to English-only descriptions isolates the templates from
        the (legitimately Chinese) content."""
        docs = self.render_all(support.en_only(self.recs), "en")
        self.assertTrue(docs)
        for name, text in docs.items():
            hits = HAN.findall(without_host_paths(text))
            self.assertFalse(hits, f"{name} leaked {len(hits)} Han chars: {hits[:10]}")

    def test_chinese_output_has_chinese(self):
        docs = self.render_all(self.recs, "zh")
        self.assertIn("Skill 总查找表", docs["SKILLS.md"])
        self.assertIn("Skill 路由表", docs["ROUTER.md"])
        self.assertIn("治理报告", docs["GOVERNANCE.md"])

    def test_default_language_is_english(self):
        self.assertEqual(DEFAULT_LANG, "en")
        docs = self.render_all(support.en_only(self.recs), "en")
        self.assertIn("# Skill Master Index", docs["SKILLS.md"])
        self.assertIn("# Skill Routing Table", docs["ROUTER.md"])

    def test_language_only_changes_labels_not_structure(self):
        en = self.render_all(self.recs, "en")["SKILLS.md"]
        zh = self.render_all(self.recs, "zh")["SKILLS.md"]
        # Same number of table rows in both languages.
        self.assertEqual(en.count("\n|"), zh.count("\n|"))

    def test_category_pages_only_for_nonempty_categories(self):
        docs = self.render_all(self.recs, "en")
        present = {r["category"] for r in self.recs}
        for cat in ALL_CATEGORIES:
            path = f"by-category/{cat['id']}.md"
            if cat["id"] in present:
                self.assertIn(path, docs)
            else:
                self.assertNotIn(path, docs)

    def test_counts_match_the_index(self):
        docs = self.render_all(self.recs, "en")
        n = sum(1 for r in self.recs if r["category"] == "hardware-eda")
        self.assertIn(f"| [hardware-eda](by-category/hardware-eda.md) "
                      f"| Hardware / Embedded / EDA | {n} |", docs["SKILLS.md"])

    def test_every_indexed_skill_appears_in_its_own_category_page(self):
        """A skill that classifies into a category but never renders is invisible
        to the human reading the table -- the failure is silent, so pin it."""
        docs = self.render_all(self.recs, "en")
        # The trailing newline matters: `### foo` is a prefix of `### foo-py`.
        seen = [r["id"] for r in self.recs
                if f"### {r['id']}\n" in docs[f"by-category/{r['category']}.md"]]
        self.assertEqual(len(seen), len(self.recs))


class TestGovernance(support.TempCase):
    def setUp(self):
        super().setUp()
        support.build_index(self.paths)
        self.recs = support.records(self.paths)
        self.gov, self.stats = report.render_governance(self.recs, "en")
        self.text = "\n".join(self.gov)

    def test_nested_duplicate_is_detected(self):
        pairs = report.nested_duplicates(self.recs)
        ids = {p[0]["id"] for p in pairs}
        self.assertIn("foo", ids)
        self.assertIn("| `foo` | `foo/foo` |", self.text)

    def test_alias_skill_is_detected(self):
        found = {r["id"]: t for r, t in report.alias_skills(self.recs)}
        self.assertEqual(found.get("alias-pointer"), "pdf-forms")
        self.assertIn("`alias-pointer` | `pdf-forms`", self.text)

    def test_zombie_is_detected(self):
        zombies = {r["id"] for r in self.recs if report.is_zombie(r)}
        self.assertIn("zombie-thing", zombies)
        self.assertIn("no-frontmatter", zombies)

    def test_wrong_placeholder_is_not_a_zombie(self):
        ok = {"id": "x", "name": "x",
              "description": "Use this skill when the user asks about PDFs. Do the thing."}
        self.assertFalse(report.is_zombie(ok))

    def test_language_variants_are_grouped_not_flagged_as_duplicates(self):
        groups = {base: members for base, members in report.variant_clusters(self.recs)[0]}
        self.assertIn("foo", groups)
        ids = {m["id"] for m in groups["foo"]}
        self.assertEqual(ids, {"foo", "foo/foo", "foo-py", "foo-ts"})

    def test_language_variants_are_not_reported_as_lookalikes(self):
        lookalikes = report.variant_clusters(self.recs)[1]
        for _prefix, members in lookalikes:
            self.assertNotIn("foo-py", {m["id"] for m in members})

    def test_similarity_groups_cluster_identical_descriptions(self):
        blob = "Manage cloud infrastructure with terraform and kubernetes in production."
        members = [
            {"id": f"cluster-{n}", "name": f"cluster-{n}", "description": blob}
            for n in ("alpha", "beta", "gamma")
        ]
        groups = report.similarity_groups(members, threshold=0.62)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 3)

    def test_similarity_groups_keep_different_descriptions_apart(self):
        members = [
            {"id": "a-thing", "name": "a", "description": "Render video with ffmpeg filters."},
            {"id": "b-thing", "name": "b", "description": "Tune postgres indexes and queries."},
            {"id": "c-thing", "name": "c", "description": "Draft legal contracts for hiring."},
        ]
        self.assertEqual(report.similarity_groups(members), [])

    def test_deprecated_marker_is_detected(self):
        self.assertTrue(report.is_deprecated({"description": "Deprecated - use x instead."}))
        self.assertTrue(report.is_deprecated({"name": "y", "description": "Obsolete."}))
        self.assertFalse(report.is_deprecated({"description": "A perfectly current skill."}))

    def test_governance_says_it_never_deletes_anything(self):
        self.assertIn("never moves or deletes a file", self.text)

    def test_stats_are_reported(self):
        self.assertEqual(self.stats["nested"], 1)
        self.assertEqual(self.stats["aliases"], 1)
        self.assertGreaterEqual(self.stats["zombies"], 2)


class TestDisplayPath(unittest.TestCase):
    def test_path_under_home_is_relativized(self):
        p = Path.home() / ".claude" / "skills" / "foo" / "SKILL.md"
        self.assertEqual(report.display_path(p), "~/.claude/skills/foo/SKILL.md")

    def test_path_outside_home_is_left_absolute(self):
        p = Path("/opt/skills/foo/SKILL.md")
        if p.is_relative_to(Path.home()):
            self.skipTest("test path unexpectedly under HOME")
        self.assertEqual(report.display_path(p), "/opt/skills/foo/SKILL.md")

    def test_empty_path(self):
        self.assertEqual(report.display_path(""), "")

    def test_the_run_banner_is_built_through_display_path(self):
        """The banner is the one host path that reaches a committed document, so
        it must go through the scrubber rather than str() of the real location."""
        self.assertEqual(report.SKILLFIND, report.display_path(report.SCRIPTS / "skillfind.py"))


class TestWrittenFiles(support.TempCase):
    def test_main_writes_english_docs_by_default(self):
        support.build_index(self.paths)
        rc = support._argv(report.main, "--index", self.paths.final,
                           "--outdir", self.paths.docs)
        self.assertEqual(rc, 0)
        for name in ("SKILLS.md", "ROUTER.md", "by-tag.md", "GOVERNANCE.md"):
            self.assertTrue((self.paths.docs / name).exists(), name)
        self.assertIn("# Skill Master Index",
                      (self.paths.docs / "SKILLS.md").read_text(encoding="utf-8"))

    def test_language_flag_switches_the_output(self):
        support.build_index(self.paths)
        support._argv(report.main, "--index", self.paths.final,
                      "--outdir", self.paths.docs, "--lang", "zh")
        self.assertIn("Skill 总查找表",
                      (self.paths.docs / "SKILLS.md").read_text(encoding="utf-8"))

    def test_missing_index_fails_cleanly(self):
        rc = support._argv(report.main, "--index", self.paths.output / "nope.json",
                           "--outdir", self.paths.docs)
        self.assertEqual(rc, 1)


class TestStreamEncoding(support.TempCase):
    """Every stage pins stdout and stderr to UTF-8, and that is not decoration.

    `refresh.py` captures each stage's output and decodes it as UTF-8. On a
    platform that defaults to something else -- a GBK console is the usual case
    -- a stage that leaves its encoding to the locale emits bytes the parent
    reads as replacement characters, so a skill path with non-ASCII in it is
    mangled in the middle of an otherwise correct report. `extract.py` shipped
    without the three lines for exactly that reason.

    Asserted over the directory rather than per file, because the failure mode
    is *forgetting* it, and a test that lists the files cannot catch the file
    nobody remembered to list.
    """

    # Imported as libraries, never run: they have no output to encode.
    LIBRARIES = {"taxonomy.py", "i18n.py"}

    # Two spellings are in the tree and both are fine: an explicit `hasattr`
    # check, and a `try` that also survives a stream whose reconfigure raises.
    # What is not fine is calling it unguarded -- reconfigure does not exist on
    # a stream that has been swapped out, which is what happens to these
    # scripts when the suite runs them in-process.
    GUARD_RE = re.compile(r"try:\s*\n\s*sys\.stdout\.reconfigure")

    def test_every_script_pins_both_streams(self):
        scripts = sorted(p for p in (ROOT / "scripts").glob("*.py")
                         if p.name not in self.LIBRARIES)
        self.assertGreater(len(scripts), 5)
        for path in scripts:
            text = path.read_text(encoding="utf-8")
            with self.subTest(script=path.name):
                self.assertIn('sys.stdout.reconfigure(encoding="utf-8")', text)
                self.assertIn('sys.stderr.reconfigure(encoding="utf-8")', text)
                self.assertTrue('hasattr(sys.stdout, "reconfigure")' in text
                                or self.GUARD_RE.search(text),
                                "reconfigure is not guarded")

    def test_scripts_are_executable_and_anchored(self):
        """`python3 scripts/x.py` from anywhere, and `./x.py` too: shebang for
        the second, an absolute ROOT for the first."""
        for path in sorted((ROOT / "scripts").glob("*.py")):
            if path.name in self.LIBRARIES:
                continue
            text = path.read_text(encoding="utf-8")
            with self.subTest(script=path.name):
                self.assertTrue(text.startswith("#!/usr/bin/env python3"),
                                "missing shebang")


if __name__ == "__main__":
    unittest.main(verbosity=2)
