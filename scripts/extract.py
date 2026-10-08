#!/usr/bin/env python3
"""Extract SKILL.md frontmatter metadata from all skill roots into a normalized JSON index.

Usage:
    python3 scripts/extract.py [--roots LABEL=PATH,...] [--out output/skills_index.json]

PyYAML is optional. Without it a small built-in parser handles the frontmatter
shapes SKILL.md files actually use; see _simple_yaml below.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent

# refresh.py captures this script's output and decodes it as UTF-8. Where the
# platform default is something else -- a GBK console is the usual case -- a
# skill path with non-ASCII in it round-trips as replacement characters, so the
# encoding is pinned here rather than left to the locale.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

FM_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", re.DOTALL)

# Directories that are not themselves skills but containers (scaffolding, docs, assets)
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv"}

_warned_no_yaml = False


_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "t": "\t", "r": "\r"}

# `>` folds, `|` preserves; the chomping suffix only governs trailing newlines,
# which are normalized away downstream, so it is accepted and ignored.
BLOCK_SCALAR = {">", "|", ">-", "|-", ">+", "|+"}

KEY_RE = re.compile(r"^([\w.\-]+):\s*(.*)$")

# A bare null literal means "no value". Read as text it becomes a tag or a
# category literally named "null". Quoted forms ("null") are strings and are
# left alone, which is why this is checked before unquoting, not after.
NULL_LITERALS = {"null", "Null", "NULL", "~"}


def _open_quote(value) -> bool:
    """True while a quoted scalar has been opened but not yet closed.

    Inside one, a line that looks like `key: value` is still just text:
    `memory: short-term (context window)` is a sentence, not a key, and reading
    it as one truncates the description at that point.
    """
    if not isinstance(value, str) or not value or value[0] not in "\"'":
        return False
    return len(value) < 2 or not value.endswith(value[0])


def _simple_yaml(block: str) -> dict:
    """Minimal frontmatter parser, used when PyYAML is not installed.

    Covers the shapes SKILL.md files actually contain: `key: value` scalars,
    `key: [a, b]` flow lists, `- item` block lists, nesting under `metadata:`,
    `>` / `|` block scalars, plain scalars wrapped across several lines, and the
    `\\"` escapes a quoted description picks up when it quotes something itself.

    It has to be *correct*, not merely present. In a real skill library roughly
    one description in fourteen is a block scalar or a wrapped line, and taking
    only the first line leaves `description: >` with the literal value `>` --
    a skill with no describable content, which nothing can route to.

    Still not a YAML implementation: anchors, aliases, tags, multi-document
    streams and type coercion are out of scope. Install PyYAML for those.
    """
    lines: list[tuple[int, str]] = []
    for raw in block.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append((len(raw) - len(raw.lstrip()), stripped))

    def scalar(s: str) -> str:
        s = s.strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
            body = s[1:-1]
            if s[0] == '"':
                # Only double-quoted scalars carry backslash escapes.
                body = re.sub(r"\\(.)", lambda m: _ESCAPES.get(m.group(1), m.group(1)), body)
            return body
        return s

    root: dict = {}
    # (frame_indent, dict, key, key_indent) per level, where `key` is the most
    # recent key opened in that dict -- the one a block list or a wrapped
    # continuation line belongs to. The key's own indent is what separates a
    # genuine continuation from a stray line at the same depth.
    frames: list[tuple[int, dict, str | None, int]] = [(-1, root, None, -1)]
    i = 0
    while i < len(lines):
        indent, line = lines[i]
        i += 1

        while len(frames) > 1 and indent <= frames[-1][0]:
            frames.pop()
        container, pending, key_indent = frames[-1][1], frames[-1][2], frames[-1][3]

        if line.startswith("- "):
            if pending is not None:
                if not isinstance(container.get(pending), list):
                    container[pending] = []
                container[pending].append(scalar(line[2:]))
            continue

        m = KEY_RE.match(line)
        # A wrapped line continuing the enclosing scalar, which by YAML's rules
        # must be indented past the key it belongs to. It continues the scalar
        # either because it is not `key: value` at all, or because a quote opened
        # earlier has not closed yet. Appending to a non-string would corrupt
        # structure, so anything else is ignored.
        if (pending is not None and indent > key_indent
                and isinstance(container.get(pending), str)
                and (_open_quote(container[pending]) or not m)):
            container[pending] = f"{container[pending]} {line}".strip()
            continue
        if not m:
            continue

        key, val = m.group(1), m.group(2).strip()

        if val in BLOCK_SCALAR:
            parts = []
            while i < len(lines) and lines[i][0] > indent:
                parts.append(lines[i][1])
                i += 1
            text = ("\n" if val.startswith("|") else " ").join(parts)
            # Default chomping ("clip") keeps exactly one trailing newline, and
            # `-` strips it. Only that newline is at stake, since blank lines
            # were dropped when the block was read. It survives only when some
            # line follows the block: the frontmatter body is captured up to the
            # closing `---`, so a block that ends the body has no newline left
            # to clip.
            if parts and not val.endswith("-") and i < len(lines):
                text += "\n"
            container[key] = text
        elif val.startswith("[") and val.endswith("]"):
            container[key] = [scalar(v) for v in val[1:-1].split(",") if v.strip()]
        elif val:
            container[key] = None if val in NULL_LITERALS else scalar(val)
        else:
            # An empty value introduces either a block list or a nested mapping;
            # the next line decides. A list may sit at the key's own indent.
            items = []
            j = i
            while j < len(lines) and lines[j][0] >= indent and lines[j][1].startswith("- "):
                items.append(scalar(lines[j][1][2:]))
                j += 1
            if items:
                i = j
                container[key] = items
            elif j < len(lines) and lines[j][0] > indent and not KEY_RE.match(lines[j][1]):
                # The value starts on the following line and may wrap from
                # there. Left unquoted here so _open_quote can see whether it
                # has closed.
                container[key] = lines[j][1]
                i = j + 1
                frames[-1] = (frames[-1][0], container, key, indent)
                continue
            else:
                container[key] = {}
                frames.append((indent, container[key], None, -1))
                continue  # the child frame now owns the pending slot

        frames[-1] = (frames[-1][0], container, key, indent)

    def unquote(node) -> None:
        """Strip quotes and resolve escapes once the whole block is assembled.

        Doing it at assignment time is wrong for a scalar that opens with `"` and
        closes several lines later: neither the first line nor any intermediate
        one is a quoted string on its own, so the quotes survive into the value.
        Running it here, exactly once, also means a backslash escape is never
        resolved twice.

        Only quoted values are touched. `scalar` trims whitespace, which would
        otherwise eat the trailing newline a block scalar is supposed to keep.
        """
        if isinstance(node, dict):
            items = node.items()
        elif isinstance(node, list):
            items = list(enumerate(node))
        else:
            return
        for k, v in items:
            if isinstance(v, str):
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    node[k] = scalar(v)
            else:
                unquote(v)

    unquote(root)
    return root


def parse_frontmatter(text: str) -> dict:
    global _warned_no_yaml
    m = FM_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    if yaml is not None:
        try:
            data = yaml.safe_load(block)
            return data if isinstance(data, dict) else {}
        except yaml.YAMLError:
            # Malformed frontmatter: salvage what we can rather than dropping
            # the whole skill.
            pass
    elif not _warned_no_yaml:
        _warned_no_yaml = True
        print("note: PyYAML not installed, using the built-in frontmatter parser.\n"
              "      `pip install pyyaml` for full YAML support.", file=sys.stderr)
    return _simple_yaml(block)


def flatten_meta(fm: dict) -> dict:
    """Pull known nested fields up to the top level."""
    md = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
    out = {
        "domain": md.get("domain") or fm.get("domain"),
        "role": md.get("role") or fm.get("role"),
        "scope": md.get("scope") or fm.get("scope"),
        "triggers": md.get("triggers") or fm.get("triggers"),
        "tags": md.get("tags") or fm.get("tags"),
        "category": md.get("category") or fm.get("category"),
        "related": md.get("related-skills") or md.get("related_skills") or fm.get("related-skills"),
    }
    # Normalize list-ish values
    for k, v in out.items():
        if isinstance(v, str):
            out[k] = [s.strip() for s in re.split(r"[,;|]", v) if s.strip()]
        elif isinstance(v, list):
            out[k] = [str(s).strip() for s in v if str(s).strip()]
    return out


def clean_desc(desc: str) -> str:
    if not desc:
        return ""
    desc = re.sub(r"\s+", " ", str(desc)).strip()
    # Strip boilerplate prefixes that add no signal
    desc = re.sub(r"^(?:Use (?:this|the) skill (?:when|whenever|for)|This skill (?:should be used|helps))[^.]*?\.\s*", "", desc, flags=re.I)
    return desc.strip()


def scan(root: Path, root_label: str) -> list[dict]:
    rows: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "SKILL.md" not in filenames:
            continue
        p = Path(dirpath) / "SKILL.md"
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"  !! unreadable: {p} ({e})", file=sys.stderr)
            continue
        fm = parse_frontmatter(text)
        rel = p.relative_to(root)
        # Skill id = the directory name holding SKILL.md; if that is the root itself, use root name
        skill_dir = rel.parent
        sid = skill_dir.name if str(skill_dir) != "." else root.name
        if str(skill_dir) != ".":
            # Prefix with parent group when nested one level (e.g. libreoffice/base)
            parent = skill_dir.parent.name
            if str(skill_dir.parent) != "." and parent not in {"skills"}:
                sid = f"{parent}/{sid}"
        meta = flatten_meta(fm)
        desc = clean_desc(meta.pop("description", None) or fm.get("description", ""))
        row = {
            "id": sid,
            "name": fm.get("name") or sid.split("/")[-1],
            "root": root_label,
            "path": str(p),
            "dir": str(p.parent),
            "description": desc,
            "desc_len": len(desc),
            "license": fm.get("license"),
            "risk": fm.get("risk"),
            "source": fm.get("source"),
            "allowed_tools": fm.get("allowed-tools"),
            "has_frontmatter": bool(fm),
            "extra_files": sorted(
                f for f in os.listdir(p.parent)
                if f != "SKILL.md" and not f.startswith(".")
            )[:20],
            "bytes": p.stat().st_size,
        }
        row.update({k: v for k, v in meta.items() if v})
        rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    home = Path.home()
    default_roots = [
        (home / ".claude" / "skills", "user"),
        (home / ".claude" / "plugins" / "marketplaces", "plugin"),
    ]
    ap.add_argument("--roots", default=None, help="comma-separated root paths (label=path)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if args.roots:
        roots = []
        for item in args.roots.split(","):
            if "=" in item:
                label, path = item.split("=", 1)
            else:
                label, path = "custom", item
            roots.append((Path(path), label))
    else:
        roots = default_roots

    all_rows: list[dict] = []
    for root, label in roots:
        if not root.exists():
            print(f"-- skip missing root: {root}", file=sys.stderr)
            continue
        found = scan(root, label)
        print(f"-- {label}: {root} -> {len(found)} skills", file=sys.stderr)
        all_rows.extend(found)

    # Drop duplicate ids across roots, preferring 'user' root
    order = {"user": 0, "plugin": 1, "custom": 2}
    all_rows.sort(key=lambda r: (r["id"], order.get(r["root"], 9)))
    seen: set[str] = set()
    deduped = []
    for r in all_rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        deduped.append(r)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(deduped, ensure_ascii=False, indent=1), encoding="utf-8")

    with_desc = sum(1 for r in deduped if r["description"])
    print(
        f"\nTOTAL={len(deduped)}  with_description={with_desc} "
        f"({with_desc * 100 // max(len(deduped), 1)}%)  -> {out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
