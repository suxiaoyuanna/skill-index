# skill-index

A searchable index of every skill installed on your machine, so the agent can
pick the right one instead of guessing from a name.

## The problem

Claude Code injects skill **names** into the context — not their descriptions.
With a handful of skills that is fine. With a few hundred it stops working:

- `moyu`, `007`, `adhx`, `blockrun` are indistinguishable from noise
- Twenty `seo-*` skills and fifteen `kicad-*` skills look equally plausible
- The agent re-implements something you already installed, because it never
  learned the skill existed

Nobody can fix this by remembering harder. It needs an index.

## What this does

Scans every `SKILL.md` under your skill roots, reads the frontmatter, sorts each
skill into one of 28 categories by rule — with an `other` bucket for whatever
matches nothing — and writes lookup tables you and the agent can search:

| File | What it is |
|---|---|
| `docs/ROUTER.md` | Compact routing table — read this first |
| `docs/by-category/<id>.md` | One page per category, full descriptions |
| `docs/SKILLS.md` | Everything, grouped by category |
| `docs/by-tag.md` | Reverse tag lookup |
| `docs/GOVERNANCE.md` | Duplicates, aliases, dead entries |

`scripts/skillfind.py` searches the same data from the command line, optionally
as JSON.

## Install

```bash
git clone https://github.com/suyuan/skill-index ~/.claude/skills/skill-index
cd ~/.claude/skills/skill-index
python3 scripts/refresh.py
```

That's it — the skill is live, because a skill is just a directory containing
`SKILL.md`. The index takes a few seconds to build for ~2000 skills.

**No dependencies.** PyYAML is used when present and a built-in frontmatter
parser takes over when it isn't. The two were compared over a 1802-skill
library and returned byte-identical records, so `requirements.txt` lists PyYAML
as optional and installing it changes nothing you can observe — only that a real
YAML parser is doing the work.

That equivalence is enforced by `TestFallbackMatchesPyYAML`, which parses every
fixture both ways and fails when the two disagree. It exists because the
fallback is otherwise dead code on any machine that has PyYAML: the first
version of it silently truncated one description in fourteen — leaving
`description: >` with the literal value `>` — and no test noticed.

## Search

```bash
S=~/.claude/skills/skill-index/scripts/skillfind.py

python3 $S "pcb layout"                  # keywords
python3 $S "竞品分析"                     # Chinese works directly
python3 $S "" --cat hardware-eda --limit 40   # browse a category
python3 $S "pdf" --tag kicad             # filter by tag
python3 $S "seo audit" --json            # machine-readable
python3 $S "react" --full                # untruncated descriptions
```

The `id` in the output is the name you pass to the `Skill` tool. Category labels
come back in English; `--lang zh` switches them, as does asking in Chinese — the
default `--lang auto` follows the language of the query. **The output language
never affects what is findable**: the Chinese alias table and the CJK bigram
index are always active.

Chinese queries resolve two ways. A query covered by the 162-entry alias table
is translated to its English keywords, so `竞品分析` finds `competitor-analysis`.
Anything else falls through to character-bigram matching against skill
descriptions, so a Chinese description is findable without any alias existing
for it.

## Keeping it current

The index is a snapshot. Rebuild it after installing, removing or editing a
skill:

```bash
python3 ~/.claude/skills/skill-index/scripts/refresh.py
```

The rebuild is incremental — unchanged files hit a content-hash cache, so only
what actually changed is reclassified. `--check` reports drift without writing
anything; `--quiet` prints only when the skill count changed.

The bundled `SKILL.md` tells the agent to run this itself when a search misses
something it expects to exist, which covers the common case with no
configuration. If you would rather it ran automatically, wire `--quiet` into a
Claude Code `SessionStart` hook — the trade-off is a few seconds added to every
session while it re-verifies the hashes.

## Make it yours

`scripts/taxonomy.py` holds the 28 categories, each with an English and Chinese
label, a description, `id_patterns` and `keywords`. **It was tuned against one
library, so it is a starting point, not an authority** — yours is probably
shaped differently. Before editing anything, ask it whether it fits:

```bash
python3 scripts/taxonomy_doctor.py
```

```
taxonomy fit: 1802 skills across 28 categories
==============================================================
unclassified     100    5.5%   (category "other")
confidence     high  1399  medium    84  low   319  (17.7%)

Largest categories
  cloud-infra              183   10.2%
  office-automation        145    8.0%

Findings
  [ok]    "other" holds 100 skills; its largest name family has 4 of them,
          under the 5 that would suggest a category. A long tail, not a
          missing one. Nothing to add.
  [split] "cloud-infra" holds 183 skills (10.2%), too many to browse.
          Largest name families: azure (116), conductor (7), terraform (6)
```

Three things it can tell you:

- **[add]** — skills in `other` that share a name family are a domain the
  taxonomy has no word for. Naming it would claim them all at once.
- **[split]** — one category far above your library's average is too big to
  browse; the name families say how to divide it.
- **[llm]** — too much of the library is low confidence; run the refinement
  pass below.

**The findings are about your library's shape, not absolute numbers.** "Too
big" means twice *your* average category, so a 200-skill and a 5000-skill
library both get a sensible answer. Every line is a suggestion — the tool
changes nothing.

Edit it:

```python
{
    "id": "hardware-eda",
    "en": "Hardware / Embedded / EDA",
    "zh": "硬件 / 嵌入式 / EDA",
    "en_desc": "PCB design, KiCad/Altium, FPGA/Verilog, MCU/RTOS, firmware ...",
    "zh_desc": "PCB 设计、KiCad/Altium、FPGA/Verilog、MCU/RTOS、固件与选型",
    "id_patterns": [r"^kicad", r"^pcb", r"^altium", r"fpga", r"verilog"],
    "keywords": ["pcb", "schematic", "gerber", "footprint", "embedded", ...],
}
```

An `id_patterns` match is worth 10 points, a `keywords` match 2, so a name hit
beats a description stuffed with another category's vocabulary. Patterns are
matched against the skill id and are **not** anchored unless you anchor them —
`r"security"` matches `kicad-security-thing`. Scores are gated into `high`,
`medium` and `low` confidence; only `low` is offered up for refinement.

After editing, rebuild — the classifier notices the rules changed and re-runs
everything, so there is nothing to clear by hand:

```bash
python3 scripts/refresh.py
```

Categories you remove keep their skills — those records fall into `other`
rather than disappearing. If you ever want to reclassify regardless of what
changed, `refresh.py --no-cache` does that.

## Optional: LLM refinement

The rules classify most skills confidently. The rest are collected in
`output/needs_llm.json` and stay searchable meanwhile, just with a `low`
confidence mark.

To refine them, split the list into batches and answer them — by hand, or by
handing each batch to a model:

```bash
python3 scripts/make_batches.py --size 30
```

That writes `state/batches/batch_NN.json`. Answer with a sibling
`batch_NN.result.json` — a bare JSON array:

```json
[{"id": "kw-receiver", "category": "hardware-eda", "tags": ["gyroscope"]}]
```

Then rebuild, and merge picks them up. Answers are consolidated into
`state/llm_overrides.json`, keyed by skill id **and** the hash of the `SKILL.md`
they were written for — so editing a skill automatically retires an answer that
no longer describes it.

Delete each `batch_NN.result.json` once it has been merged. They are re-ingested
on every run, so an answer left lying around will re-apply itself to a skill you
have since rewritten, hash guard and all.

## Governance report

`docs/GOVERNANCE.md` flags what accumulates in a long-lived skill directory:

- **Nested duplicates** — `foo` and `foo/foo` are the same skill installed twice
- **Aliases** — a description that just points at another skill
- **Lookalike clusters** — descriptions similar past a Jaccard threshold
- **Language variants** — `x-py` / `x-ts` / `x-dotnet`, one idea, several runtimes
- **Deprecated** — marked obsolete
- **Zombies** — no description, or a placeholder one, so nothing can route to them

**Nothing in this project ever moves, edits or deletes a skill file.** It reads
them and reports. Deciding what to do about a duplicate is yours.

## Development

```bash
python3 -m unittest discover -s tests -t tests
```

The suite runs against a synthetic corpus in `tests/fixtures/corpus.json` and
never touches your real `output/`, `state/` or `docs/`. The fixtures are stored
as data rather than as checked-in `SKILL.md` files on purpose: anything shaped
like a skill inside `~/.claude/skills/` becomes one, so fixture skills would
install themselves into your real library.

## License

MIT — see [LICENSE](LICENSE).
