---
name: skill-index
description: "Use at the start of any task a specialized skill might cover — before writing code, config, documents, or analysis from scratch, and whenever the user asks 'is there a skill for X' / 'which skill should I use'. Searches a local index of every installed skill and returns ranked candidates with category, tags and description, because only skill names reach the context, not what they do. Also use when several similarly-named skills exist and it is unclear which one applies."
license: MIT
---

# Skill Index — pick the right skill out of hundreds

A hundred-plus installed skills is past the point where you can enumerate them
from memory. Only the **names** reach the context, so `moyu`, `007` and `adhx`
are indistinguishable from noise, and choosing between twenty `seo-*` skills
comes down to guessing.

This skill closes that gap with a local index built by scanning every `SKILL.md`
on the machine: **search → select → invoke**.

## When to use

- Before starting a task, to check whether a skill already covers it
- When the user asks "is there a skill for…" or "which skill should I use"
- When several skills look alike (twenty `seo-*`, fifteen `kicad-*`) and one must be picked
- When the user describes a task in Chinese (the index carries a Chinese alias table, so Chinese queries work directly)

**Do not** use it for plain file reads and writes, pure question answering, or
when you already know the exact skill to call.

## Setup

The index is generated from your own skills, so it must be built once after
install. Scripts resolve their own paths, so the working directory does not
matter.

```bash
SKILL_DIR="$HOME/.claude/skills/skill-index"
python3 "$SKILL_DIR/scripts/refresh.py"
```

This scans `~/.claude/skills`, classifies every skill, and writes the lookup
tables to `docs/`. Takes a few seconds for ~2000 skills; unchanged skills hit a
content-hash cache and are not recomputed.

## 1. Search

```bash
S="$HOME/.claude/skills/skill-index/scripts/skillfind.py"

python3 "$S" "pcb layout" --limit 8         # keywords, English or Chinese
python3 "$S" "竞品分析" --limit 8            # Chinese works directly
python3 "$S" "" --cat hardware-eda --limit 40   # browse a category
python3 "$S" "pdf" --tag kicad              # filter by tag
python3 "$S" "seo audit" --json             # machine-readable
```

Results carry `id`, category, tags, a one-line description and a score. **The
`id` is the name you pass to the `Skill` tool.** Use `--lang zh` if the user is
working in Chinese and you want Chinese category labels back.

## 2. Locate by category

When no keyword comes to mind, read the routing table first — it maps each
category to its trigger words and representative skills:

```
docs/ROUTER.md
```

Then open the full listing for that category:

```
docs/by-category/<category-id>.md   # one page per category, full descriptions
docs/SKILLS.md                      # everything, by category
docs/by-tag.md                      # reverse tag lookup
```

## 3. Select

Once you have candidates, use these six rules — and **call only one or two**,
not the whole list:

1. **Check where the category came from.** `category_source: llm` was judged
   per-skill by a model and is more trustworthy than `rules`.
2. **Prefer the short name.** `kicad` is usually more general than `kicad-bom`;
   the long hyphenated names are the narrow variants.
3. **Take one of a language family.** `azure-ai-openai-dotnet` / `-py` / `-ts`
   are the same thing bound to different runtimes — pick the one matching the
   project at hand.
4. **Read meaningless names before trusting them.** `007`, `adhx`, `moyu`,
   `blockrun` say nothing; open the description rather than guessing from the id.
5. **When still unsure, read the whole `SKILL.md`** of a candidate (the `path`
   field in the search output), or just ask the user.
6. **When nothing fits, say so.** Report that no installed skill covers the task
   and proceed with general ability — never force an unrelated skill onto it.

## 4. Keep the index current

New or edited skills are not in the index until it is rebuilt. **After adding a
skill, or whenever a search misses something you know exists, run:**

```bash
python3 "$HOME/.claude/skills/skill-index/scripts/refresh.py"
```

`--quiet` suppresses output when nothing changed. The run prints which skills
still await optional semantic refinement.

## 5. Governance

`docs/GOVERNANCE.md` lists near-duplicate clusters, nested and aliased skills,
language-variant families, deprecated entries, and "zombie" skills with missing
descriptions. When a search lands on a duplicate cluster, prefer the most
general member. **Nothing in this system ever moves, edits or deletes a skill
file** — it only reads them and reports.

## 6. When the categories do not fit

The 28 categories in `scripts/taxonomy.py` ship tuned against one library, so
some users will have domains it has no word for. If the user asks why their
skills land in `other`, or wants categories matching their own work:

```bash
python3 "$SKILL_DIR/scripts/taxonomy_doctor.py"
```

It reports what this taxonomy misses or over-merges *for this library* — the
name families sitting in `other`, and any category too large to browse — then
the user edits `scripts/taxonomy.py` and re-runs `refresh.py`. The classifier
notices the rules changed and reclassifies everything; nothing needs clearing
by hand. Do not rewrite the category list yourself without asking: the
classifier, the routing table and the governance report all key off it.
