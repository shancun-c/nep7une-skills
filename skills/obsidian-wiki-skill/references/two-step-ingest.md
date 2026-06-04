# Two-Step Chain-of-Thought Ingest

> Inspired by nashsu/llm_wiki's analysis → generation decoupling pattern.
> The goal: separate "what should be done" from "how to do it" to prevent semantic drift during ingest.

## Why Two Steps

Traditional single-pass ingest has the agent analyze content AND format output simultaneously. This creates risks:

- **Semantic drift**: the agent starts writing one conclusion, drifts to another mid-stream
- **Format collapse**: YAML frontmatter or wikilinks degrade as the agent juggles logic + syntax
- **Missed connections**: without a dedicated analysis pass, wikilink targets and contradictions with existing notes are discovered too late (or not at all)
- **Over-write / under-write**: without a blueprint, the agent may create too many or too few knowledge notes

Two-step decoupling solves this: Step 1 produces a **structured blueprint** (analysis only, no file writes), Step 2 executes the blueprint (writes only, no re-analysis).

## When to Apply Two-Step

**Always apply two-step** for sources that are:
- 2000+ words or 5+ distinct factual claims
- Technical, research, or analysis pieces
- Likely to connect to 3+ existing vault notes
- From a new domain the vault hasn't covered before

**Skip or simplify** for:
- Short news snippets (<500 words, single claim)
- Source notes that are purely for archival reference with no knowledge-layer impact
- Re-ingesting an updated version of an already-processed source

When in doubt, apply two-step — the overhead is low and the quality gain is meaningful.

## Step 1 — Cognitive Audit (分析蓝图)

Before writing any files, produce an analysis in the agent's internal reasoning (do NOT write this to disk).

### Blueprint Structure

```
## Ingest Analysis

### 1. Source Profile
- Type: [article / paper / video / report / tweet / ...]
- Author credibility: [official / reputable outlet / personal blog / unknown]
- Primary topic(s): [1-3 key topics]
- Length / complexity: [short / medium / long]

### 2. Entity & Concept Extraction
- New entities found: [person, org, product, project names]
- New concepts found: [ideas, frameworks, methods, terms]
- Entities already in vault: [existing note references]
- Concepts already in vault: [existing note references]

### 3. Connection Mapping
- Direct links to existing source notes: [[note A]], [[note B]]
- Potential knowledge note promotions: [which claims deserve 30 Knowledge elevation]
- Contradictions with existing knowledge: [any conflicts with current vault conclusions]
- Updates needed to existing notes: [notes that need augmentation]

### 4. Knowledge Gap Analysis
- Gaps this source fills: [what questions does it answer]
- Gaps this source reveals: [what new questions does it raise]
- Sparse areas this source connects to: [under-covered domains]

### 5. Write Plan
- Source note filename: [proposed filename following vault convention]
- Key sections to include: [Summary, Key Points, Quotes, My Take, ...]
- Wikilink targets: [[note X]], [[note Y]]
- Knowledge notes to create: [filename + 1-line rationale]
- Knowledge notes to update: [filename + specific change]
- Index files to update: [Sources Index, Knowledge Index, ...]
- Cross-verification claims: [3-8 specific, verifiable assertions]
```

### Analysis Rules

- **Be conservative**: when unsure whether a claim deserves a knowledge note, default to source-note-only.
- **Prefer connection over creation**: updating an existing knowledge note to include a new insight is better than creating a standalone note with one sentence.
- **Flag uncertainty**: if the source has credibility issues or the agent isn't confident about a connection, mark it for human review rather than guessing.
- **Respect vault conventions**: the blueprint must follow the vault's existing naming patterns, folder structure, and frontmatter conventions discovered during orientation.

### Quick Blueprint (for simpler sources)

When the full blueprint is overkill, use a compact version:

```
## Quick Ingest Analysis
- Type: [article], [N] claims
- New: [entity/concept names]
- Existing connections: [[note A]], [[note B]]
- Write: source note [filename] + update Sources Index
- Cross-verify: [2-4 claims]
```

## Step 2 — Atomic Write (原子化写入)

Execute the blueprint strictly. Do NOT re-analyze or change course mid-stream.

### Execution Order

1. **Create source note** — follow the blueprint's filename and section plan. Set `confidence: medium` initially.
2. **Cross-verify** — use anysearch (or equivalent) to verify each claim listed in the blueprint. After verification:
   - Update `confidence` in frontmatter
   - Append `## Cross-verification` table
3. **Update existing knowledge notes** — if the blueprint identified notes that need augmentation, apply targeted patches (never full rewrites).
4. **Create new knowledge notes** — only for insights that meet the "durable knowledge" bar: reusable beyond the source, synthesizes multiple sources, or represents a stable conclusion.
5. **Update indices** — Sources Index (always), Knowledge Index (if new knowledge notes created).
6. **Update log** — one concise entry summarizing what changed.
7. **Git push** — use the safe clone+rsync pattern.

### Write Discipline

- **One source note per ingest** (unless the source naturally splits into multiple independent units).
- **At most 1-2 new knowledge notes per ingest** — if the blueprint proposes more, re-evaluate whether they're truly durable or better kept as source-note "My Take" bullets.
- **Incremental updates preferred**: `patch` an existing knowledge note to add a new insight rather than rewriting it from scratch.
- **Verify index integrity**: after every index patch, read back the file to confirm the old entries are still present.

## Pitfalls

- **Over-analysis paralysis**: don't spend more time on analysis than writing. For a 2000-word article, the blueprint should take 1-2 paragraphs of reasoning, not 500 words.
- **Blueprint drift in execution**: the most common failure mode is that Step 2 discovers something new during writing and changes course. If this happens, STOP Step 2, return to Step 1 to update the blueprint, then resume. Never let Step 2 re-analyze.
- **Too many knowledge note promotions**: a single source rarely justifies more than 2 new knowledge notes. If the blueprint proposes 3+, flag them as candidates and pick the top 1-2.
- **Skipping cross-verification because the blueprint didn't list claims**: Step 1 must identify verifiable claims. If the source has none (pure opinion piece), note this explicitly in the blueprint and set confidence to `medium` without a cross-verification table.
- **Quick blueprint used for complex sources**: if a source has 5+ distinct claims, connections to 3+ existing notes, or technical depth, the full blueprint is required. Quick blueprints are for simple sources only.
