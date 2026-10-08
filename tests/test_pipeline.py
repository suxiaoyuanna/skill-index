"""The optional LLM refinement round trip, end to end.

`build_index` (extract -> classify -> merge) is exercised by the other modules.
What is tested here is the part a human drives by hand: hand out batches, fill in
answers, merge them back -- and the two ways that goes wrong, namely losing the
answers and keeping an answer that no longer describes the file.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import support  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from make_batches import main as batches_main  # noqa: E402
from merge import main as merge_main  # noqa: E402


class TestBatchRoundTrip(support.TempCase):
    def setUp(self):
        super().setUp()
        support.build_index(self.paths)

    def make_batches(self, size=30):
        return support._argv(batches_main, "--in", self.paths.needs_llm,
                             "--dir", self.paths.batches, "--size", size)

    def merge(self):
        return support._argv(merge_main, "--tagged", self.paths.tagged,
                             "--batches", self.paths.batches,
                             "--overrides", self.paths.overrides,
                             "--out", self.paths.final)

    def answer(self, name, answers):
        (self.paths.batches / name).write_text(
            json.dumps(answers, ensure_ascii=False), encoding="utf-8")

    def category_of(self, sid):
        recs = {r["id"]: r for r in support.records(self.paths)}
        return recs[sid]

    def test_needs_llm_lists_the_low_confidence_skills(self):
        pending = json.loads(self.paths.needs_llm.read_text(encoding="utf-8"))
        self.assertTrue(pending)
        for item in pending:
            self.assertIn("category_guess", item)

    def test_batches_are_split_and_numbered(self):
        self.assertEqual(self.make_batches(size=5), 0)
        names = sorted(p.name for p in self.paths.batches.glob("batch_*.json"))
        self.assertEqual(names[0], "batch_00.json")
        # Derived rather than pinned: the corpus grows, and a hardcoded batch
        # count would fail for a reason that has nothing to do with splitting.
        pending = json.loads(self.paths.needs_llm.read_text(encoding="utf-8"))
        self.assertEqual(len(names), -(-len(pending) // 5))
        self.assertTrue((self.paths.batches / "_manifest.json").exists())

    def test_rerunning_does_not_delete_unmerged_answers(self):
        """The regression that motivated this test: the cleanup glob used to be
        `batch_*.json`, which also matched `batch_00.result.json` -- so rebuilding
        the batches silently destroyed the answers nobody had merged yet."""
        self.make_batches()
        self.answer("batch_00.result.json", [{"id": "kw-receiver", "category": "other"}])
        self.make_batches()
        self.assertTrue((self.paths.batches / "batch_00.result.json").exists())

    def test_an_answer_moves_the_skill_and_survives_into_the_index(self):
        self.make_batches()
        self.answer("batch_00.result.json", [
            {"id": "kw-receiver", "category": "hardware-eda",
             "tags": ["gyroscope", "calibration"]}])
        self.assertEqual(self.merge(), 0)
        rec = self.category_of("kw-receiver")
        self.assertEqual(rec["category"], "hardware-eda")
        self.assertEqual(rec["category_source"], "llm")
        self.assertEqual(rec["tags"], ["gyroscope", "calibration"])

    def test_a_string_of_tags_does_not_become_single_characters(self):
        """A model handed `tags: "pcb"` returns a string. Iterating it yields
        eight one-character tags, which is worse than no tags at all."""
        self.make_batches()
        self.answer("batch_00.result.json", [
            {"id": "kw-receiver", "category": "hardware-eda", "tags": "gyroscope"}])
        self.merge()
        self.assertEqual(self.category_of("kw-receiver")["tags"], ["gyroscope"])

    def test_editing_the_skill_drops_its_stale_answer(self):
        """Once the answer has been consolidated into `llm_overrides.json` -- the
        durable store -- replacing the SKILL.md it was written for retires it."""
        self.make_batches()
        self.answer("batch_00.result.json", [
            {"id": "kw-receiver", "category": "hardware-eda"}])
        self.merge()
        self.assertEqual(self.category_of("kw-receiver")["category"], "hardware-eda")
        (self.paths.batches / "batch_00.result.json").unlink()  # consumed

        self.rewrite_kw_receiver()
        support.build_index(self.paths)
        rec = self.category_of("kw-receiver")
        self.assertNotEqual(rec["category_source"], "llm")

    def test_a_lingering_answer_file_is_reapplied_to_the_edited_skill(self):
        """The flip side of the guard above, pinned so it is a known trade-off
        rather than a surprise: a result file left in the batches directory is
        input that merge ingests on *every* run, stamped with the hash of the
        content it found that time. Delete consumed answers, or they will follow
        a rewritten skill into its new life."""
        self.make_batches()
        self.answer("batch_00.result.json", [
            {"id": "kw-receiver", "category": "hardware-eda"}])
        self.merge()

        self.rewrite_kw_receiver()
        support.build_index(self.paths)
        rec = self.category_of("kw-receiver")
        self.assertEqual(rec["category"], "hardware-eda")
        self.assertEqual(rec["category_source"], "llm")

    def rewrite_kw_receiver(self):
        (self.paths.user / "kw-receiver" / "SKILL.md").write_text(
            '---\nname: kw-receiver\ndescription: "Rewritten to be about invoices."\n---\n',
            encoding="utf-8")

    def test_an_unknown_category_is_rejected_not_written(self):
        self.make_batches()
        self.answer("batch_00.result.json", [
            {"id": "kw-receiver", "category": "not-a-real-category"}])
        self.merge()
        overrides = json.loads(self.paths.overrides.read_text(encoding="utf-8"))
        self.assertNotIn("kw-receiver", overrides)
        self.assertNotEqual(self.category_of("kw-receiver")["category"], "not-a-real-category")

    def test_an_id_that_is_not_in_the_index_is_ignored(self):
        self.make_batches()
        self.answer("batch_00.result.json", [{"id": "ghost-skill", "category": "security"}])
        self.assertEqual(self.merge(), 0)
        self.assertNotIn("ghost-skill",
                         json.loads(self.paths.overrides.read_text(encoding="utf-8")))

    def test_a_malformed_result_file_does_not_abort_the_merge(self):
        self.make_batches()
        (self.paths.batches / "batch_00.result.json").write_text("{not json",
                                                                 encoding="utf-8")
        self.answer("batch_01.result.json", [
            {"id": "kw-receiver", "category": "hardware-eda"}])
        self.assertEqual(self.merge(), 0)
        self.assertEqual(self.category_of("kw-receiver")["category"], "hardware-eda")

    def test_merge_is_idempotent(self):
        self.make_batches()
        self.answer("batch_00.result.json", [
            {"id": "kw-receiver", "category": "hardware-eda", "tags": ["a"]}])
        self.merge()
        first = self.category_of("kw-receiver")
        self.merge()
        self.assertEqual(self.category_of("kw-receiver"), first)


class TestEmptyIndex(support.TempCase):
    """A machine with no skills installed is the first thing a new user runs."""

    def empty_roots(self) -> str:
        """TempCase materializes the corpus into the standard roots, so point the
        pipeline at a pair of directories nothing has written to."""
        dirs = []
        for label in ("user", "plugin"):
            d = self.paths.tmp / f"empty-{label}"
            d.mkdir()
            dirs.append(f"{label}={d}")
        return ",".join(dirs)

    def test_pipeline_survives_an_empty_skill_library(self):
        from classify import main as classify_main
        from extract import main as extract_main
        from report import main as report_main

        rc = support._argv(extract_main, "--roots", self.empty_roots(),
                           "--out", self.paths.index)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(self.paths.index.read_text(encoding="utf-8")), [])

        rc = support._argv(classify_main, "--index", self.paths.index,
                           "--out", self.paths.tagged, "--needs-llm", self.paths.needs_llm,
                           "--cache", self.paths.cache)
        self.assertEqual(rc, 0)

        rc = support._argv(merge_main, "--tagged", self.paths.tagged,
                           "--batches", self.paths.batches,
                           "--overrides", self.paths.overrides, "--out", self.paths.final)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(self.paths.final.read_text(encoding="utf-8")), [])

        # The report stage must render an empty index rather than divide by zero.
        rc = support._argv(report_main, "--index", self.paths.final,
                           "--outdir", self.paths.docs)
        self.assertEqual(rc, 0)
        self.assertTrue((self.paths.docs / "SKILLS.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
