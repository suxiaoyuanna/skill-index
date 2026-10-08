"""The taxonomy fit report: what it counts, and what it refuses to say.

`report()` takes records directly, so most of these build a synthetic
distribution rather than going through the corpus -- the thresholds are about
library *shape*, and no fixture library is shaped like one that needs
splitting.
"""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import support  # noqa: E402
from taxonomy_doctor import name_families, report  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def rec(sid, cat, conf="high"):
    return {"id": sid, "name": sid, "description": sid,
            "category": cat, "confidence": conf}


def render(records, lang="en"):
    buf = io.StringIO()
    report(records, lang, out=buf)
    return buf.getvalue()


class TestNameFamilies(unittest.TestCase):
    def test_first_segment_families(self):
        got = dict(name_families(["azure-ai-a", "azure-ai-b", "azure-ai-c"]))
        self.assertEqual(got["azure"], 3)

    def test_last_segment_families(self):
        got = dict(name_families(["asana-automation", "gmail-automation"]))
        self.assertEqual(got["automation"], 2)

    def test_a_token_counts_once_at_its_best_reading(self):
        """`foo-bar` contributes foo to the first counter and bar to the last.
        A token that is both -- `foo-foo` -- must not be counted twice."""
        got = dict(name_families(["foo-foo", "foo-foo"]))
        self.assertEqual(got["foo"], 2)

    def test_language_suffixes_are_not_domains(self):
        """`py` and `dotnet` are not answers to "what should I split this by"."""
        got = dict(name_families(["a-py", "b-py", "c-py", "d-py"]))
        self.assertNotIn("py", got)

    def test_single_character_segments_are_dropped(self):
        self.assertEqual(name_families(["x-a", "y-a"]), [])

    def test_min_size_filters_singletons(self):
        self.assertEqual(name_families(["alpha-one", "bravo-two"], min_size=2), [])

    def test_exclude_drops_known_uninformative_tokens(self):
        """The category's own name is not a way to split the category."""
        ids = ["odoo-x", "odoo-y", "vendor-automation", "other-automation"]
        self.assertEqual(dict(name_families(ids, exclude={"automation"})),
                         {"odoo": 2})


class TestReport(unittest.TestCase):
    def test_a_diffuse_other_bucket_is_called_a_long_tail(self):
        # Hyphenated on purpose: families are `-`/`_` segments, so `alpha1`
        # would be a family of its own, one skill wide.
        records = ([rec(f"alpha-{i}", "other") for i in range(1, 4)]
                   + [rec(f"bravo-{i}", "other") for i in range(1, 4)]
                   + [rec(f"k{i}", "code-quality") for i in range(20)])
        text = render(records)
        self.assertIn("long tail", text)
        self.assertNotIn("[add]", text)
        # The size of the largest family is why it is a long tail. A count of
        # families reads as "lots of variety" regardless of what it says.
        self.assertIn("has 3 of them", text)

    def test_one_unclassified_skill_does_not_earn_a_sentence(self):
        """"holds 1 skills; its largest name family has 1 of them" is noise."""
        records = [rec("lonely", "other")] + [rec(f"k{i}", "code-quality") for i in range(9)]
        self.assertNotIn("long tail", render(records))

    def test_other_is_not_listed_again_as_a_category(self):
        """It has its own line under coverage; repeating it as the biggest
        bucket only restates that the library is mostly unclassified."""
        records = [rec(f"x{i}", "other") for i in range(30)]
        buckets = render(records).split("Largest categories")[1].split("Findings")[0]
        self.assertNotIn("other", buckets)

    def test_a_name_family_in_other_suggests_a_category(self):
        """Six skills sharing a name family is a domain the taxonomy has no
        word for -- the one case where "add a category" is the right advice."""
        records = ([rec(f"obsidian-{i}", "other") for i in range(6)]
                   + [rec(f"k{i}", "code-quality") for i in range(20)])
        text = render(records)
        self.assertIn("[add]", text)
        self.assertIn("obsidian", text)

    def test_an_oversized_category_suggests_a_split(self):
        records = ([rec(f"vendor{i}", "office-automation") for i in range(100)]
                   + [rec(f"a{i}", "database") for i in range(20)]
                   + [rec(f"b{i}", "security") for i in range(20)])
        text = render(records)
        self.assertIn("[split]", text)
        self.assertIn("office-automation", text)

    def test_a_uniform_library_is_not_told_to_split_anything(self):
        """Every category the same size means none is too coarse to browse.
        The check is relative to the library, not to a fixed share."""
        records = [rec(f"c{cid}-{i}", cid) for cid in ("alpha", "bravo", "charlie")
                   for i in range(50)]
        self.assertNotIn("[split]", render(records))

    def test_a_small_library_does_not_flag_a_small_category(self):
        """BUCKET_MIN exists so a 12-skill library is not told its 6-skill
        category is oversized for being 2x the average of a 3-skill one."""
        records = [rec(f"a{i}", "alpha") for i in range(6)] + [rec("b", "bravo")]
        self.assertNotIn("[split]", render(records))

    def test_low_confidence_share_is_reported(self):
        records = ([rec(f"a{i}", "alpha", "low") for i in range(30)]
                   + [rec(f"b{i}", "bravo") for i in range(70)])
        self.assertIn("make_batches.py", render(records))

    def test_a_healthy_library_gets_the_all_clear(self):
        records = ([rec(f"a{i}", "alpha") for i in range(50)]
                   + [rec(f"b{i}", "bravo") for i in range(50)])
        self.assertIn("[ok]", render(records))

    def test_the_two_languages_render(self):
        records = [rec(f"a{i}", "alpha") for i in range(10)]
        self.assertIn("taxonomy fit", render(records, "en"))
        self.assertIn("分类表适配度", render(records, "zh"))


class TestAgainstTheCorpus(support.TempCase):
    def test_it_runs_on_a_real_index(self):
        support.build_index(self.paths)
        from taxonomy_doctor import main as doctor_main
        rc = support._argv(doctor_main, self.paths.final, "--lang", "en")
        self.assertEqual(rc, 0)

    def test_an_empty_index_is_not_a_failure(self):
        """A machine with no skills installed is the first thing a new user
        runs, and there is nothing to diagnose -- but it must not crash."""
        empty = self.paths.tmp / "empty.json"
        empty.write_text("[]", encoding="utf-8")
        from taxonomy_doctor import main as doctor_main
        self.assertEqual(support._argv(doctor_main, empty), 0)

    def test_a_missing_index_explains_itself(self):
        from taxonomy_doctor import main as doctor_main
        rc = support._argv(doctor_main, self.paths.tmp / "nope.json")
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
