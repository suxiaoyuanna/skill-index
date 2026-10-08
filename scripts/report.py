#!/usr/bin/env python3
"""Generate the human/agent-facing lookup tables from skills_final.json.

Outputs (into docs/):
    SKILLS.md               master table, one section per category
    ROUTER.md               compact always-on routing index
    by-category/<id>.md     full listing per category
    by-tag.md               tag -> skills reverse index
    GOVERNANCE.md           duplicate clusters + undocumented skills

Usage:
    python3 scripts/report.py [--index output/skills_final.json] [--outdir docs] [--lang en]

`--lang` selects the language of the *generated documents*. It does not affect
what the index contains or what skillfind.py can find -- Chinese-language
search works the same either way.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from i18n import DEFAULT_LANG, LANGS, t, trigger  # noqa: E402
from taxonomy import ALL_CATEGORIES, CAT_BY_ID, desc, label  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent

ALL_CAT_IDS = [c["id"] for c in ALL_CATEGORIES]


def display_path(p) -> str:
    """Render a path relative to $HOME when possible.

    Generated docs are committed and read by other people, so they should not
    leak the absolute layout of the machine that produced them.
    """
    if not p:
        return ""
    path = Path(str(p))
    try:
        return "~/" + path.resolve().relative_to(Path.home().resolve()).as_posix()
    except (ValueError, OSError):
        return path.as_posix()


PYEXE = Path(sys.executable).as_posix() if sys.executable else "python3"
SKILLFIND = display_path(SCRIPTS / "skillfind.py")
RUN = f'"{PYEXE}" "{SKILLFIND}"'

ZOMBIE_PATTERNS = [
    re.compile(r"^one sentence", re.I),
    re.compile(r"^use when working with .* tasks or workflows\b", re.I),
    re.compile(r"^(a |an )?skill (that|for)\b.*\bdoes\b$", re.I),
]


def one_line(text: str, lang: str, limit: int = 130) -> str:
    if not text:
        return t(lang, "none")
    d = re.sub(r"\s+", " ", text).strip()
    # cut at first sentence boundary if the first sentence is short enough
    m = re.search(r"(?<=[.!?])\s", d)
    if m and 40 < m.start() < limit:
        d = d[: m.start()]
    if len(d) > limit:
        d = d[: limit - 1].rstrip() + "…"
    return d.replace("|", "\\|")


def is_zombie(r: dict) -> bool:
    d = (r.get("description") or "").strip()
    if len(d) < 25:
        return True
    return any(p.search(d) for p in ZOMBIE_PATTERNS)


def write(path: Path, lines: list[str]) -> None:
    # newline="\n" keeps a doc generated on Windows byte-identical to the same
    # doc generated on Linux, so diffs stay clean across platforms.
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------
# Renderers. Each takes plain data and returns the document as a string, so
# the i18n behaviour is testable without touching the filesystem.
# --------------------------------------------------------------------------

def render_skills(recs, by_cat, ordered_cats, lang) -> list[str]:
    present = [c for c in ordered_cats if by_cat.get(c)]
    L = [t(lang, "skills.title"), "",
         t(lang, "skills.summary", n=len(recs), cats=len(present)).replace("**", ""),
         "",
         t(lang, "skills.search_hint", run=RUN),
         "",
         t(lang, "skills.h2"), "",
         t(lang, "skills.th"),
         "|---|---|---:|---|"]
    for cid in present:
        items = by_cat[cid]
        c = CAT_BY_ID[cid]
        L.append(f"| [{cid}](by-category/{cid}.md) | {label(c, lang)} | {len(items)} "
                 f"| {desc(c, lang)} |")
    L.append("")

    for cid in present:
        items = by_cat[cid]
        c = CAT_BY_ID[cid]
        L += [t(lang, "skills.cat_heading", label=label(c, lang), cid=cid), "",
              t(lang, "skills.cat_meta", desc=desc(c, lang), n=len(items)), "",
              t(lang, "skills.th_skills"), "|---|---|---|"]
        for r in items:
            tags = " ".join(f"`{x}`" for x in (r.get("tags") or [])[:5])
            L.append(f"| [`{r['id']}`](by-category/{cid}.md#{anchor(r['id'])}) "
                     f"| {one_line(r.get('description', ''), lang)} | {tags} |")
        L.append("")
    return L


def render_category(cid, items, lang) -> list[str]:
    c = CAT_BY_ID[cid]
    M = [t(lang, "cat.title", label=label(c, lang), cid=cid), "",
         desc(c, lang), "",
         t(lang, "cat.triggers", n=len(items), triggers=trigger(cid, lang)), "",
         t(lang, "cat.back"), "", "---", ""]
    for r in items:
        M.append(f"### {r['id']}")
        M.append("")
        M.append(one_line(r.get("description", ""), lang, 400))
        meta = [f"`{r.get('category_source', 'rules')}`"]
        if r.get("tags"):
            meta.append(" ".join(f"`#{x}`" for x in r["tags"]))
        M.append("")
        M.append(" ".join(meta))
        if r.get("path"):
            M.append("")
            M.append(f"<sub>`{display_path(r['path'])}`</sub>")
        M.append("")
    return M


def render_router(recs, by_cat, ordered_cats, lang) -> list[str]:
    present = [c for c in ordered_cats if by_cat.get(c)]
    R = [t(lang, "router.title"), "",
         t(lang, "router.summary", n=len(recs), cats=len(present)).replace("**", ""),
         t(lang, "router.purpose"), "",
         "```",
         f'{t(lang, "router.cmd_search")} {RUN} "<keywords>" --limit 8',
         f'{t(lang, "router.cmd_cat")} {RUN} --cat hardware-eda --limit 50',
         f'{t(lang, "router.cmd_tag")} {RUN} "pcb" --tag kicad',
         "```", "",
         t(lang, "router.th"),
         "|---|---|---:|---|"]
    for cid in present:
        c = CAT_BY_ID[cid]
        R.append(f"| `{cid}` | {label(c, lang)} | {len(by_cat[cid])} | {trigger(cid, lang)} |")
    R += ["", t(lang, "router.reps_h2"), "", t(lang, "router.reps_note"), ""]
    for cid in present:
        items = by_cat[cid]
        # Representative picks: short ids tend to be the canonical, general-purpose
        # skill, while long hyphenated ones are narrow variants (azure-ai-...-dotnet).
        reps = sorted(items, key=lambda r: (len(r["id"]), r["id"].lower()))[:14]
        names = ", ".join(f"`{r['id']}`" for r in reps)
        more = t(lang, "router.more", n=len(items)) if len(items) > len(reps) else ""
        R.append(f"- **{label(CAT_BY_ID[cid], lang)}** — {names}{more}")
    R.append("")
    return R


def render_tags(recs, lang) -> list[str]:
    by_tag: dict[str, list[str]] = defaultdict(list)
    for r in recs:
        for x in r.get("tags") or []:
            by_tag[x].append(r["id"])
    T = [t(lang, "tag.title"), "",
         t(lang, "tag.summary", n=len(by_tag)).replace("**", ""), ""]
    for tag, ids in sorted(by_tag.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if len(ids) < 2:
            continue
        T.append(f"- **`#{tag}`** ({len(ids)}) — "
                 + ", ".join(f"`{i}`" for i in sorted(ids)[:30])
                 + (" …" if len(ids) > 30 else ""))
    T += ["", t(lang, "tag.h2"), "",
          " ".join(f"`#{x}`" for x, ids in sorted(by_tag.items()) if len(ids) == 1)]
    return T


def render_governance(recs, lang) -> tuple[list[str], dict]:
    zombies = [r for r in recs if is_zombie(r)]
    deprecated = [r for r in recs if is_deprecated(r)]
    nested = nested_duplicates(recs)
    aliases = alias_skills(recs)
    lang_variants, lookalikes = variant_clusters(recs)
    n_look = sum(len(g) for g in lookalikes)
    n_lang = sum(len(m) for _, m in lang_variants)

    G = [t(lang, "gov.title"), "",
         t(lang, "gov.warn"), "",
         t(lang, "gov.th"),
         "|---|---:|---|---|"]
    for cls, cnt, mean_k, act_k in [
        ("gov.r_nested", len(nested), "gov.r_nested_m", "gov.r_nested_a"),
        ("gov.r_alias", len(aliases), "gov.r_alias_m", "gov.r_alias_a"),
        ("gov.r_lookalike", n_look, "gov.r_lookalike_m", "gov.r_lookalike_a"),
        ("gov.r_langvar", n_lang, "gov.r_langvar_m", "gov.r_langvar_a"),
        ("gov.r_deprecated", len(deprecated), "gov.r_deprecated_m", "gov.r_deprecated_a"),
        ("gov.r_zombie", len(zombies), "gov.r_zombie_m", "gov.r_zombie_a"),
    ]:
        G.append(f"| {t(lang, cls)} | {cnt} | {t(lang, mean_k)} | {t(lang, act_k)} |")
    G.append("")

    G += [t(lang, "gov.h_nested"), "", t(lang, "gov.n_nested"), "",
          t(lang, "gov.th_dup"), "|---|---|---|"]
    for outer, inner in nested[:60]:
        G.append(f"| `{outer['id']}` | `{inner['id']}` | `{display_path(outer.get('path',''))}` |")
    if not nested:
        G.append(f"| {t(lang, 'gov.none')} | | |")
    G.append("")

    G += [t(lang, "gov.h_alias"), "", t(lang, "gov.th_alias"), "|---|---|"]
    for r, target in aliases:
        G.append(f"| `{r['id']}` | `{target}` |")
    if not aliases:
        G.append(f"| {t(lang, 'gov.none')} | |")
    G.append("")

    G += [t(lang, "gov.h_lookalike"), "", t(lang, "gov.n_lookalike"), ""]
    for prefix, members in lookalikes[:25]:
        G += [f"### `{prefix}*` — {len(members)}", ""]
        for r in members:
            G.append(f"- `{r['id']}` — {one_line(r.get('description', ''), lang, 110)}")
        G.append("")
    if not lookalikes:
        G += [t(lang, "gov.none"), ""]
    if len(lookalikes) > 25:
        G += [t(lang, "gov.more_lookalike", n=len(lookalikes) - 25), ""]

    G += [t(lang, "gov.h_langvar"), "", t(lang, "gov.n_langvar"), ""]
    for base, members in lang_variants[:40]:
        langs = " / ".join(sorted({lang_of(m["id"]) for m in members}))
        G.append(f"- **`{base}`** ({len(members)}) — {langs}")
    if len(lang_variants) > 40:
        G.append(t(lang, "gov.more_langvar", n=len(lang_variants) - 40))
    G.append("")

    G += [t(lang, "gov.h_deprecated"), "", t(lang, "gov.th_deprecated"), "|---|---|"]
    for r in sorted(deprecated, key=lambda x: x["id"]):
        G.append(f"| `{r['id']}` | {one_line(r.get('description', ''), lang, 110)} |")
    if not deprecated:
        G.append(f"| {t(lang, 'gov.none')} | |")
    G.append("")

    G += [t(lang, "gov.h_zombie"), "", t(lang, "gov.n_zombie"), "",
          t(lang, "gov.th_zombie"), "|---|---|---|"]
    for r in sorted(zombies, key=lambda x: x["id"]):
        G.append(f"| `{r['id']}` | {one_line(r.get('description', ''), lang, 80)} "
                 f"| `{display_path(r.get('path',''))}` |")
    G.append("")

    stats = {"nested": len(nested), "aliases": len(aliases), "lookalike_groups": len(lookalikes),
             "lang_variants": len(lang_variants), "deprecated": len(deprecated),
             "zombies": len(zombies)}
    return G, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=str(ROOT / "output" / "skills_final.json"))
    ap.add_argument("--outdir", default=str(ROOT / "docs"))
    ap.add_argument("--lang", choices=LANGS, default=DEFAULT_LANG,
                    help="language of the generated documents (default: %(default)s)")
    a = ap.parse_args()

    try:
        recs = json.loads(Path(a.index).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no index at {a.index}\nrun: python3 scripts/refresh.py", file=sys.stderr)
        return 1

    outdir = Path(a.outdir)
    (outdir / "by-category").mkdir(parents=True, exist_ok=True)

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        by_cat[r.get("category", "other")].append(r)
    for v in by_cat.values():
        v.sort(key=lambda r: r["id"].lower())

    # Categories the taxonomy knows about, then anything unexpected the index
    # carries (a hand-edited override, say) so nothing silently disappears.
    ordered = ALL_CAT_IDS + sorted(k for k in by_cat if k not in CAT_BY_ID)

    write(outdir / "SKILLS.md", render_skills(recs, by_cat, ordered, a.lang))
    for cid in ordered:
        if by_cat.get(cid):
            write(outdir / "by-category" / f"{cid}.md",
                  render_category(cid, by_cat[cid], a.lang))
    write(outdir / "ROUTER.md", render_router(recs, by_cat, ordered, a.lang))
    write(outdir / "by-tag.md", render_tags(recs, a.lang))
    gov, stats = render_governance(recs, a.lang)
    write(outdir / "GOVERNANCE.md", gov)

    print(f"wrote SKILLS.md, ROUTER.md, by-tag.md, GOVERNANCE.md, by-category/*.md "
          f"({len([c for c in ordered if by_cat.get(c)])} cats, lang={a.lang})", file=sys.stderr)
    print(" ".join(f"{k}={v}" for k, v in stats.items()), file=sys.stderr)
    return 0


# --------------------------------------------------------------------------
# Governance analysis
# --------------------------------------------------------------------------

def nested_duplicates(recs: list[dict]) -> list[tuple[dict, dict]]:
    """Find `X` / `X/X` pairs — the same skill installed at two nesting levels."""
    by_id: dict[str, list[dict]] = {}
    for r in recs:
        by_id.setdefault(r["id"], []).append(r)
    out = []
    for sid, items in by_id.items():
        if "/" not in sid:
            continue
        head, tail = sid.split("/", 1)
        if head == tail and head in by_id:
            out.append((by_id[head][0], items[0]))
    # also catch deeper repeats like a/b/b
    out.sort(key=lambda p: p[0]["id"])
    return out


ALIAS_RE = re.compile(r"alias for\s+([a-z0-9][\w/\-.]+)", re.I)


def alias_skills(recs: list[dict]) -> list[tuple[dict, str]]:
    """Skills whose description points at another skill instead of describing work.

    The target is stripped of trailing sentence punctuation first: the pattern
    has to admit `.` and `/` to match real ids like `node.js` or `foo/bar`, so
    it also swallows the full stop in "Alias for pdf-forms." -- which would
    otherwise report a target that does not exist.
    """
    out = []
    for r in recs:
        m = ALIAS_RE.search(r.get("description") or "")
        if not m:
            continue
        target = m.group(1).strip(".-/")
        if target and target.lower() != r["id"].lower():
            out.append((r, target))
    return out


def anchor(sid: str) -> str:
    return re.sub(r"[^a-z0-9\- ]", "", sid.lower().replace("/", "")).replace(" ", "-")


LANG_SUFFIX = {
    "py": "Python", "python": "Python", "ts": "TypeScript", "typescript": "TypeScript",
    "js": "JavaScript", "javascript": "JavaScript", "dotnet": ".NET", "net": ".NET",
    "java": "Java", "rust": "Rust", "rs": "Rust", "go": "Go", "golang": "Go",
    "cs": "C#", "csharp": "C#", "rb": "Ruby", "ruby": "Ruby", "php": "PHP",
    "kt": "Kotlin", "kotlin": "Kotlin", "swift": "Swift", "cpp": "C++", "c": "C",
    "r": "R", "scala": "Scala", "elixir": "Elixir",
}

DEPRECATED_RE = re.compile(
    r"\bdeprecat|\bobsolete\b|\brenamed to\b|\bsuperseded\b|\bno longer (supported|maintained)\b|⚠️",
    re.I,
)


def lang_of(sid: str) -> str:
    tail = sid.split("/")[-1].rsplit("-", 1)
    return LANG_SUFFIX.get(tail[-1].lower(), "") if len(tail) > 1 else ""


def base_of(sid: str) -> str:
    """Strip a trailing language token so `foo-py` and `foo-java` share a base."""
    parts = sid.split("/")[-1].rsplit("-", 1)
    if len(parts) > 1 and parts[-1].lower() in LANG_SUFFIX:
        return parts[0]
    return sid.split("/")[-1]


def variant_clusters(recs: list[dict]) -> tuple[list, list]:
    """Split prefix families into (language variants, likely true duplicates)."""
    fam: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        base = base_of(r["id"])
        head = base.split("-")[0].lower()
        if len(head) < 3:
            continue
        fam[head].append(r)

    lang_variants, true_dupes = [], []
    for head, members in fam.items():
        prefixed = [m for m in members if base_of(m["id"]).lower().startswith(head)]
        if len(prefixed) < 3:
            continue
        # Split by base name: same base across languages = a language-variant group
        by_base: dict[str, list[dict]] = defaultdict(list)
        for m in prefixed:
            by_base[base_of(m["id"]).lower()].append(m)
        for base, group in by_base.items():
            if len(group) < 2:
                continue
            langs = {lang_of(m["id"]) for m in group}
            if langs - {""} and len(group) >= 2 and len(langs) >= 2:
                lang_variants.append((base, sorted(group, key=lambda m: m["id"])))
            elif sum(1 for m in group if lang_of(m["id"])) == 0:
                true_dupes.append((base, sorted(group, key=lambda m: m["id"])))
    # Same-prefix families are NOT duplicates by themselves (odoo-* covers 22
    # distinct business modules). Real redundancy shows up as near-identical
    # *descriptions*, so compare text within each prefix family.
    families: dict[str, list[dict]] = defaultdict(list)
    for m in recs:
        sid = m["id"].split("/")[-1]
        head = sid.split("-")[0].lower()
        if len(head) >= 3 and sid.lower().startswith(head + "-"):
            families[head].append(m)

    for head, members in families.items():
        members = [m for m in members
                   if not lang_of(m["id"]) and len(m.get("description") or "") > 40]
        if len(members) < 3:
            continue
        for g in similarity_groups(members, threshold=0.62):
            if len(g) >= 2:
                true_dupes.append((head + "-*", sorted(g, key=lambda m: m["id"])))

    lang_variants.sort(key=lambda kv: -len(kv[1]))
    true_dupes.sort(key=lambda kv: -len(kv[1]))
    return lang_variants, true_dupes


def _desc_tokens(r: dict) -> set[str]:
    from skillfind import tokenize
    return set(tokenize(r.get("description", "")))


def similarity_groups(members: list[dict], threshold: float = 0.62) -> list[list[dict]]:
    """Union-find over description token Jaccard similarity."""
    toks = [_desc_tokens(m) for m in members]
    parent = list(range(len(members)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            a, b = toks[i], toks[j]
            if not a or not b:
                continue
            inter = len(a & b)
            if not inter:
                continue
            if inter / len(a | b) >= threshold:
                union(i, j)

    groups: dict[int, list[dict]] = defaultdict(list)
    for i, m in enumerate(members):
        groups[find(i)].append(m)
    return [g for g in groups.values() if len(g) >= 2]


def is_deprecated(r: dict) -> bool:
    blob = f'{r.get("description","")} {r.get("name","")}'
    return bool(DEPRECATED_RE.search(blob))


if __name__ == "__main__":
    raise SystemExit(main())
