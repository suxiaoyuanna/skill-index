"""Search: the alias table, the CJK bigram path, and the ranking gates.

The two negative controls below (``..._without_alias_table``) are what make this
a regression suite rather than a smoke test: they show that the feature under
test is what found the record, not a coincidence of shared vocabulary.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import support  # noqa: E402
import skillfind  # noqa: E402
from skillfind import Searcher, cjk_ngrams, expand_query, tokenize  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HAN = __import__("re").compile(r"[一-鿿]")


class TestTokenize(unittest.TestCase):
    def test_symbol_laden_tokens_survive(self):
        got = tokenize("c++ node.js gpt-4o x")
        for want in ("c++", "node.js", "gpt-4o"):
            self.assertIn(want, got)

    def test_single_letters_are_dropped(self):
        self.assertNotIn("x", tokenize("x"))

    def test_cjk_ngrams_split_on_non_cjk(self):
        # Runs are split, so no bigram spans the " v2 " gap.
        self.assertEqual(cjk_ngrams("版本 v2 变更"), ["版本", "变更"])

    def test_cjk_ngrams_need_at_least_two_characters(self):
        self.assertEqual(cjk_ngrams("中"), [])

    def test_cjk_ngrams_are_sliding_windows(self):
        self.assertEqual(cjk_ngrams("陀螺仪"), ["陀螺", "螺仪"])


class TestExpandQuery(unittest.TestCase):
    def test_pure_chinese_leaves_no_latin(self):
        latin, cjk, alias = expand_query("竞品分析")
        self.assertEqual(latin, [])
        self.assertEqual(cjk, [])
        self.assertEqual(alias, ["competitor", "competitive", "analysis"])

    def test_longest_alias_key_wins(self):
        """`竞品分析` is a compound key; it must beat the `竞品` key, which would
        otherwise also inject `alternatives` and dilute the match."""
        _, _, alias = expand_query("竞品分析")
        self.assertNotIn("alternatives", alias)

    def test_uncovered_chinese_stays_as_bigrams(self):
        latin, cjk, alias = expand_query("陀螺仪校准")
        self.assertEqual(latin, [])
        self.assertEqual(alias, [])
        self.assertEqual(cjk, ["陀螺", "螺仪", "仪校", "校准"])

    def test_mixed_query_keeps_latin_and_expands_chinese(self):
        latin, cjk, alias = expand_query("kicad 竞品分析")
        self.assertIn("kicad", latin)
        self.assertIn("competitor", alias)


class TestSearch(support.TempCase):
    def setUp(self):
        super().setUp()
        support.build_index(self.paths)
        self.s = support.searcher(self.paths)

    def search(self, q, limit=8, cat=None, tag=None):
        return support.ids(self.s.search(q, limit, cat, tag))

    # -- English ---------------------------------------------------------
    def test_plain_english_query(self):
        self.assertEqual(self.search("kicad pcb")[0], "kicad-board-layout")

    def test_multiword_english_query(self):
        self.assertIn("pdf-forms", self.search("pdf forms"))

    def test_no_match_returns_empty(self):
        self.assertEqual(self.search("nonsense zzzz"), [])

    # -- Chinese via the alias table -------------------------------------
    def test_alias_expansion_finds_english_skill(self):
        self.assertIn("competitor-analysis", self.search("竞品分析"))

    def test_alias_table_is_what_found_it(self):
        """Negative control: with the alias table emptied, the record the alias
        lookup found disappears, so that lookup is what found it.

        The assertion is about this record, not about an empty result set.
        Removing the table does not silence the query -- `分析` is also a
        substring of the `data-eng` label "数据工程与分析", which is enough for
        an incidental weak hit. That is a deliberate low-weight category prior,
        not a leak, so the control has to be specific.
        """
        with mock.patch.object(skillfind, "ZH_ALIASES", {}):
            self.assertNotIn("competitor-analysis", self.search("竞品分析"))

    def test_alias_expansion_into_another_skill(self):
        self.assertIn("changelog-writer", self.search("版本变更", limit=8))

    # -- Chinese via CJK bigrams -----------------------------------------
    def test_cjk_bigrams_match_chinese_description(self):
        self.assertEqual(self.search("陀螺仪校准"), ["kw-receiver"])

    def test_cjk_bigram_path_without_alias_table(self):
        """Negative control: this query is covered by no alias key, so the hit
        can only come from bigram matching against the Chinese description."""
        with mock.patch.object(skillfind, "ZH_ALIASES", {}):
            self.assertEqual(self.search("陀螺仪校准"), ["kw-receiver"])

    def test_cjk_hits_are_records_with_chinese_descriptions(self):
        for sid in self.search("陀螺仪校准"):
            rec = next(r for r in self.s.records if r["id"] == sid)
            self.assertTrue(HAN.search(rec["description"]), sid)

    # -- Ranking gates ---------------------------------------------------
    def test_a_named_latin_token_gates_out_expansions(self):
        """A query that names something concrete must match it; otherwise the
        expanded concept answers a question the user did not ask."""
        with mock.patch.object(skillfind, "ZH_ALIASES", {"陀螺仪校准": "kicad pcb"}):
            got = self.search("kicad 陀螺仪校准")
        self.assertEqual(got, ["kicad-board-layout"])

    def test_out_of_vocabulary_tokens_are_dropped_before_scoring(self):
        """A latin token no record contains has df 0, which would zero every
        score through the gate. Dropping it degrades to a CJK-only query."""
        got = self.search("schematic 陀螺仪校准")
        self.assertIn("kw-receiver", got)

    def test_results_are_ordered_and_bounded(self):
        results = self.s.search("foo", 3)
        scores = [s for s, _ in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertLessEqual(len(results), 3)

    # -- Browse and filters ----------------------------------------------
    def test_empty_query_returns_nothing(self):
        self.assertEqual(self.search(""), [])

    def test_empty_query_browses_a_category(self):
        got = self.search("", cat="hardware-eda")
        self.assertTrue(got)
        for sid in got:
            rec = next(r for r in self.s.records if r["id"] == sid)
            self.assertEqual(rec["category"], "hardware-eda")

    def test_tag_filter_is_case_insensitive(self):
        lower = self.search("pcb", tag="kicad")
        upper = self.search("pcb", tag="KICAD")
        self.assertEqual(lower, upper)

    def test_category_filter_restricts_results(self):
        for sid in self.search("security", cat="security"):
            rec = next(r for r in self.s.records if r["id"] == sid)
            self.assertEqual(rec["category"], "security")


class TestLabels(support.TempCase):
    def setUp(self):
        super().setUp()
        support.build_index(self.paths)
        self.s = support.searcher(self.paths)

    def test_load_injects_both_labels(self):
        rec = next(r for r in self.s.records if r["id"] == "kicad-board-layout")
        self.assertEqual(rec["category_en"], "Hardware / Embedded / EDA")
        self.assertEqual(rec["category_zh"], "硬件 / 嵌入式 / EDA")

    def test_unclassified_records_get_the_fallback_label(self):
        rec = next(r for r in self.s.records if r["id"] == "zombie-thing")
        self.assertEqual(rec["category_en"], "Other / Unclassified")
        self.assertEqual(rec["category_zh"], "其他")

    def test_auto_language_follows_the_query(self):
        self.assertEqual(skillfind.resolve_lang("auto", "web scraping"), "en")
        self.assertEqual(skillfind.resolve_lang("auto", "竞品分析"), "zh")

    def test_explicit_language_overrides_auto(self):
        self.assertEqual(skillfind.resolve_lang("en", "竞品分析"), "en")
        self.assertEqual(skillfind.resolve_lang("zh", "web scraping"), "zh")

    def test_language_does_not_change_what_is_findable(self):
        """--lang prints labels; it must never gate the alias table or the
        bigram index."""
        with_alias = support.ids(self.s.search("竞品分析", 8))
        self.assertIn("competitor-analysis", with_alias)
        with mock.patch.object(skillfind, "ZH_ALIASES", {}):
            self.assertNotIn("competitor-analysis", support.ids(self.s.search("竞品分析", 8)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
