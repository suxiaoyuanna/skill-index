"""Frontmatter extraction: the layer that breaks differently on every machine."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import extract  # noqa: E402
import support  # noqa: E402
from extract import clean_desc, flatten_meta, parse_frontmatter, scan  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class TestFrontmatter(unittest.TestCase):
    def test_basic_fields(self):
        fm = parse_frontmatter('---\nname: x\ndescription: "Hi there."\nlicense: MIT\n---\n')
        self.assertEqual(fm["name"], "x")
        self.assertEqual(fm["description"], "Hi there.")
        self.assertEqual(fm["license"], "MIT")

    def test_missing_frontmatter_is_empty(self):
        self.assertEqual(parse_frontmatter("# Just a heading\n"), {})

    def test_empty_frontmatter_is_empty(self):
        self.assertEqual(parse_frontmatter("---\n---\n"), {})

    def test_crlf_line_endings(self):
        fm = parse_frontmatter('---\r\nname: crlf\r\ndescription: "Uses CRLF."\r\n---\r\n')
        self.assertEqual(fm["name"], "crlf")
        self.assertEqual(fm["description"], "Uses CRLF.")

    def test_value_containing_a_colon(self):
        fm = parse_frontmatter('---\nname: x\ndescription: "Use when: the user asks."\n---\n')
        self.assertEqual(fm["description"], "Use when: the user asks.")

    def test_broken_yaml_still_yields_a_usable_description(self):
        """Malformed frontmatter is common in the wild; drop the file and the
        skill silently becomes unfindable."""
        text = ('---\nname: broken\ndescription: "Salvaged text"\n'
                'bad: [unclosed\n---\n')
        fm = parse_frontmatter(text)
        self.assertEqual(fm.get("description"), "Salvaged text")

    def test_frontmatter_not_a_mapping(self):
        self.assertEqual(parse_frontmatter("---\n- a\n- b\n---\n"), {})

    def test_block_and_flow_lists(self):
        fm = parse_frontmatter(
            "---\nname: x\nflow: [a, b]\nblock:\n  - c\n  - d\n---\n")
        self.assertEqual(fm["flow"], ["a", "b"])
        self.assertEqual(fm["block"], ["c", "d"])


class TestFlatten(unittest.TestCase):
    def test_nested_metadata_is_lifted(self):
        fm = parse_frontmatter(
            "---\nname: x\nmetadata:\n  domain: engineering\n  tags:\n    - alpha\n"
            "    - beta\n  triggers: \"one, two\"\n---\n")
        meta = flatten_meta(fm)
        # Every flattened field is normalized to a list, including scalars --
        # a one-element list for `domain` is the documented shape.
        self.assertEqual(meta["domain"], ["engineering"])
        self.assertEqual(meta["tags"], ["alpha", "beta"])
        # A comma string is split rather than treated as one tag.
        self.assertEqual(meta["triggers"], ["one", "two"])

    def test_nested_metadata_wins_over_top_level(self):
        """`metadata:` is the conventional location in SKILL.md, so it takes
        precedence and the top-level form is the fallback."""
        meta = flatten_meta({"tags": ["top"], "metadata": {"tags": ["nested"]}})
        self.assertEqual(meta["tags"], ["nested"])

    def test_top_level_is_used_when_metadata_is_absent(self):
        self.assertEqual(flatten_meta({"domain": "engineering"})["domain"],
                         ["engineering"])

    def test_blank_values_normalize_to_empty(self):
        meta = flatten_meta({"domain": "  ", "role": ""})
        self.assertEqual(meta["domain"], [])
        self.assertEqual(meta["role"], [])


class TestFallbackParser(unittest.TestCase):
    """The parser used when PyYAML is not installed.

    Exercising it means forcing it, because every other test in this file goes
    through PyYAML -- which is exactly how the block-scalar bug survived: on a
    machine with PyYAML installed, the fallback is dead code, and on a machine
    without it, seven percent of descriptions were silently truncated.
    """

    def fallback(self, text):
        with mock.patch.object(extract, "yaml", None):
            return parse_frontmatter(text)

    def test_folded_block_scalar(self):
        fm = self.fallback("---\nname: x\ndescription: >\n  One two\n  three.\n---\n")
        self.assertEqual(fm["description"], "One two three.")

    def test_literal_block_scalar_keeps_breaks(self):
        fm = self.fallback("---\nname: x\ndescription: |\n  One\n  two\n---\n")
        self.assertEqual(fm["description"], "One\ntwo")

    def test_a_block_that_ends_the_frontmatter_has_no_trailing_newline(self):
        """The captured body stops at the closing `---`, so a block scalar that
        ends it has no newline left to clip -- where the same block followed by
        another key does. Both cases come from PyYAML; see the differential test."""
        last = self.fallback("---\nname: x\ndescription: >\n  Text.\n---\n")
        followed = self.fallback("---\nname: x\ndescription: >\n  Text.\nrisk: safe\n---\n")
        self.assertEqual(last["description"], "Text.")
        self.assertEqual(followed["description"], "Text.\n")

    def test_chomping_indicator_is_not_part_of_the_value(self):
        """The headline failure: `description: >` used to yield the literal `>`."""
        fm = self.fallback("---\nname: x\ndescription: >-\n  Real text.\n---\n")
        self.assertEqual(fm["description"], "Real text.")

    def test_wrapped_plain_scalar_joins_its_continuation_lines(self):
        fm = self.fallback("---\nname: x\ndescription: Expert in 3D\n  on the web.\n---\n")
        self.assertEqual(fm["description"], "Expert in 3D on the web.")

    def test_backslash_escapes_are_unescaped(self):
        fm = self.fallback('---\nname: x\ndescription: "Use for \\"make slides\\"."\n---\n')
        self.assertEqual(fm["description"], 'Use for "make slides".')

    def test_single_quoted_scalars_keep_backslashes(self):
        """Only double-quoted scalars carry escapes; in single quotes a backslash
        is a literal backslash."""
        fm = self.fallback("---\nname: x\ndescription: 'a \\ b'\n---\n")
        self.assertEqual(fm["description"], "a \\ b")

    def test_block_list_at_the_keys_own_indent(self):
        fm = self.fallback("---\nname: x\ntags:\n- a\n- b\n---\n")
        self.assertEqual(fm["tags"], ["a", "b"])

    def test_block_list_deeper_than_the_key(self):
        fm = self.fallback("---\nname: x\nmetadata:\n  tags:\n    - a\n    - b\n---\n")
        self.assertEqual(fm["metadata"]["tags"], ["a", "b"])

    def test_a_list_does_not_swallow_the_next_key(self):
        fm = self.fallback("---\ntags:\n- a\nname: x\n---\n")
        self.assertEqual(fm["tags"], ["a"])
        self.assertEqual(fm["name"], "x")

    def test_continuation_does_not_overwrite_a_nested_mapping(self):
        """A wrapped line is only appended to a scalar. If the target is a
        mapping, appending would destroy the structure."""
        fm = self.fallback("---\nname: x\nmetadata:\n  a: 1\n  stray line\n---\n")
        self.assertEqual(fm["metadata"]["a"], "1")

    def test_nesting_is_still_two_levels_deep(self):
        fm = self.fallback("---\nname: x\nmetadata:\n  a: 1\n  b: 2\nname2: y\n---\n")
        self.assertEqual(fm["metadata"], {"a": "1", "b": "2"})
        self.assertEqual(fm["name2"], "y")


@unittest.skipIf(extract.yaml is None, "PyYAML not installed, nothing to compare against")
class TestFallbackMatchesPyYAML(unittest.TestCase):
    """Differential test: the fallback must agree with the real parser on every
    fixture. Cheap to run, and it fails the moment a new frontmatter shape is
    added that only one of the two parsers understands."""

    def test_every_corpus_entry_parses_identically(self):
        interesting = ("name", "description", "license", "risk", "source", "tags")
        for entry in support.corpus():
            with self.subTest(skill=entry["relpath"]):
                text = entry["raw"]
                with mock.patch.object(extract, "yaml", None):
                    got = parse_frontmatter(text)
                want = extract.parse_frontmatter(text)  # untouched, uses PyYAML
                for field in interesting:
                    if field in want or field in got:
                        self.assertEqual(got.get(field), want.get(field),
                                         f"{entry['relpath']}: {field}")


class TestCleanDesc(unittest.TestCase):
    def test_boilerplate_prefix_is_stripped(self):
        self.assertEqual(
            clean_desc("Use this skill when the user asks about PDFs. Do the thing."),
            "Do the thing.")

    def test_real_content_is_kept(self):
        self.assertEqual(clean_desc("Design PCB layouts."), "Design PCB layouts.")

    def test_whitespace_is_collapsed(self):
        self.assertEqual(clean_desc("a\n\n  b"), "a b")


class TestScan(support.TempCase):
    def test_node_modules_is_skipped(self):
        ids = [r["id"] for r in scan(self.paths.user, "user")]
        self.assertNotIn("ignored", ids)

    def test_nested_directory_becomes_parent_child_id(self):
        ids = [r["id"] for r in scan(self.paths.user, "user")]
        self.assertIn("foo", ids)
        self.assertIn("foo/foo", ids)

    def test_no_frontmatter_yields_empty_description(self):
        rows = {r["id"]: r for r in scan(self.paths.user, "user")}
        self.assertEqual(rows["no-frontmatter"]["description"], "")
        self.assertEqual(rows["no-frontmatter"]["desc_len"], 0)
        self.assertFalse(rows["no-frontmatter"]["has_frontmatter"])

    def test_scan_finds_every_fixture_except_skipped_dirs(self):
        ids = {r["id"] for r in scan(self.paths.user, "user")}
        self.assertIn("crlf-skill", ids)
        self.assertIn("broken-yaml", ids)

    def test_extra_files_are_recorded(self):
        rows = {r["id"]: r for r in scan(self.paths.user, "user")}
        self.assertEqual(rows["kicad-board-layout"]["license"], "MIT")


class TestCrossRootDedup(support.TempCase):
    def test_user_root_wins_over_plugin(self):
        support.build_index(self.paths)
        recs = {r["id"]: r for r in support.records(self.paths)}
        self.assertEqual(recs["kicad-board-layout"]["root"], "user")
        self.assertIn("KiCad", recs["kicad-board-layout"]["description"])

    def test_plugin_only_skill_is_still_indexed(self):
        support.build_index(self.paths)
        recs = {r["id"]: r for r in support.records(self.paths)}
        self.assertEqual(recs["plugin-only-skill"]["root"], "plugin")

    def test_duplicate_ids_collapse_to_one_row(self):
        support.build_index(self.paths)
        ids = [r["id"] for r in support.records(self.paths)]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
