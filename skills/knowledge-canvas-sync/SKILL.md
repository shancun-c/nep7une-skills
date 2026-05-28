---
name: knowledge-canvas-sync
description: Daily sync of Obsidian knowledge canvas — extract new knowledge from source notes, create/update knowledge notes, maintain the visual knowledge graph. Use when the user asks to update the knowledge canvas, when running daily knowledge extraction, or when new source notes have been ingested and need to be synthesized into knowledge.
---

# Knowledge Canvas Sync

## Mission

This skill maintains a living visual knowledge graph in the Obsidian vault. It extracts durable knowledge from source notes, creates or updates evergreen knowledge notes, and reflects all knowledge in a single `.canvas` file with relationships visualized as edges.

The canvas is the **central visual interface** for the user's knowledge. Every knowledge note lives in the canvas. Every day, new knowledge is added with a distinct color marker.

## Operating Principles

- **Knowledge is extracted, not copied.** A source note contains evidence; a knowledge note contains a durable conclusion. Never create a knowledge note that merely restates a source note.
- **The canvas is the truth.** Every knowledge note must have a corresponding node in the canvas. No orphan knowledge.
- **New ≠ duplicated.** Before creating a knowledge note, check if an existing one already covers the insight. Prefer updating existing knowledge over creating near-duplicates.
- **Color signals freshness.** New knowledge nodes use color `"3"` (yellow) for the first 24 hours. After 24 hours, they revert to `"5"` (cyan) — the standard knowledge color.
- **Edges show relationships.** When two knowledge notes are conceptually related or one builds on another, add an edge with a label describing the relationship.

## Execution Companions

- `obsidian-canvas-creator` for reading/writing `.canvas` files and layout algorithms
- `obsidian-markdown` for knowledge note creation
- `obsidian-wiki-skill` for vault orientation and source note processing
- Filesystem tools for reading source notes and existing knowledge notes
- `scripts/verify-canvas-colors.py` — run after every canvas write to validate color conventions

## Workflow

### 1. Orient

Load the current state:

- Read `99 System/Knowledge Canvas.canvas` — the existing knowledge graph
- Read `30 Knowledge/Knowledge Index.md` — the knowledge index
- List all knowledge notes in `30 Knowledge/` — current inventory
- Identify today's new source notes (created today in `40 Sources/`)

### 2. Scan New Sources

For each source note created today:

- Read the source note content (Summary, Key Points, My Take sections)
- Skip sources that are purely news reporting with no durable insight
- For sources containing a durable principle, pattern, or conclusion, extract the candidate knowledge:
  - What is the **one sentence** insight?
  - Does it **contradict** or **extend** existing knowledge?
  - Which existing knowledge notes might it relate to?

### 3. Create or Update Knowledge

For each candidate insight:

**If genuinely new** (no existing knowledge note captures it):
- Create a new knowledge note in `30 Knowledge/` with proper frontmatter
- Add a `## Source` section linking back to the source note(s)
- Add to the canvas as a new text node with color `"3"` (yellow = new today)
- Position near related knowledge in its cluster group

**If it extends existing knowledge** (an existing knowledge note is close but incomplete):
- Update the existing knowledge note with the new insight
- Add a `## Updates` subsection with date and source
- Update the canvas node text if needed
- Keep the node's existing color (don't re-mark as "new")

**If it's a repeat** (already fully captured by existing knowledge):
- Skip — no action needed

### 4. Update Canvas

After all knowledge processing:

- **Refresh node colors**: Any node with color `"3"` that was created more than 24 hours ago → change to `"5"` (cyan)
- **Add new edges**: For any new or updated knowledge notes, scan all knowledge notes for conceptual links and add edges
- **Reconcile**: Ensure every knowledge note in `30 Knowledge/` has a corresponding node in the canvas. If any are missing, add them
- **Remove stale**: If a knowledge note was deleted from `30 Knowledge/`, remove its node and edges from the canvas
- **Update Knowledge Index**: Add new knowledge notes to `30 Knowledge/Knowledge Index.md`
- **Verify colors**: After every canvas write, programmatically verify:
  - ALL group nodes have `color: "4"` (green) — no exceptions
  - Principle-level nodes (in `工程原则` group) have `color: "6"` (purple)
  - Remaining text nodes are `"5"` (cyan) or `"3"` (yellow if new today)
  - New edges for new nodes use `color: "3"` (yellow) to match node freshness
  - Print a color summary table before finalizing

### 5. Report

Summarize what changed:
- New knowledge notes created (with titles)
- Existing knowledge notes updated
- New edges added
- Any knowledge gaps identified (source notes that yielded no knowledge — worth flagging)

## Canvas Layout Convention

- **Group nodes** by knowledge domain. Current groups (see `99 System/Knowledge Canvas.canvas`):
  - **工程原则** (Engineering Principles) — foundational design philosophy
  - **工具与执行** (Tools & Execution) — implementation & tooling layer
  - **交互与自动化** (Interaction & Automation) — interaction paradigms
  - **记忆与知识** (Memory & Knowledge) — knowledge systems
  - **领域实践** (Domain Practice) — applied cases
- **Node size**: 360×170 for all knowledge nodes. This accommodates title + 2-3 sentence summary + wikilink. Do NOT use 320×100 — it causes text truncation and unreadable content.
- **Node content**: Every node MUST include three elements in order: (1) **bold title** on first line, (2) 2-3 sentence summary on subsequent lines, (3) wikilink to the note on the last line (`→ [[note path]]`)
- **Grid layout**: 2 columns per group, with GAP_X=50, GAP_Y=40. Groups of different heights placed row-by-row — row N's y position = sum of max heights of rows 0..N-1 plus GROUP_GAP=80 per row.
- **Row-based positioning**: Calculate y positions dynamically based on the tallest group in each row to prevent overlaps between rows. Never hardcode absolute y positions.
- **Spacing within group**: GROUP_PAD=50 on all sides of nodes inside the group boundary.
- **New node placement**: inside the relevant group cluster, at the first available grid slot (bottom-right continuation of the 2-column grid).
- **Layout verification**: After every canvas write, programmatically verify 0 node overlaps by checking bounding-box intersections across all text node pairs. If overlaps found, increase NODE_H or GAP_Y and re-layout.
- **Color scheme** (STRICT — verify after every canvas write):
  - `"3"` (yellow) — new knowledge, added today (temporary, returns to `"5"` after 24h)
  - `"5"` (cyan) — established knowledge (methodology, tools, interaction, memory)
  - `"6"` (purple) — foundational / principle-level knowledge (工程原则 group nodes only)
  - `"4"` (green) — applied domain practice nodes (领域实践 group)
- **Group color**: ALWAYS `"4"` (green) for ALL groups, regardless of conceptual layer. Never use `"5"` or `"6"` on group nodes — semantic layering is expressed through text node colors, not group backgrounds.

## Knowledge Note Template

```markdown
---
title: <one-sentence insight as title>
type: knowledge
status: active
created: <today>
updated: <today>
source:
  - "[[<source-note-path>]]"
tags: []
---

# <title>

<The core insight, 2-4 sentences. This is the "evergreen" part — it should make sense without reading the source.>

## Why It Matters

<1-2 sentences on why this is practically useful.>

## Source

- [[<source-note-path>]] — <what specifically was extracted>

## Related

- [[<related-knowledge-note>]]
```

## Guardrails

- Do not create knowledge notes that merely restate source summaries
- Do not create more than 3 new knowledge notes per day — if there are more candidates, prioritize the most durable ones
- Do not delete existing knowledge notes unless they are demonstrably wrong or superseded
- Do not rearrange the entire canvas layout on every run — only adjust positions for new nodes
- Knowledge notes must link back to their source notes (traceability)
- If no source notes were ingested today, skip the scan — nothing to do
- **NEVER mix group colors**: all groups are `"4"` (green). Do NOT use `"5"` or `"6"` on group nodes — semantic meaning is expressed through text node colors only
- **Always load `obsidian-canvas-creator` skill** before any canvas read/write operations — it provides the layout algorithms, spacing rules, and JSON format conventions

## Cron Integration

This skill is designed to run daily. The cron prompt should be:

```
Load knowledge-canvas-sync skill, then run the full workflow: scan today's source notes, extract new knowledge, update canvas, report changes.
```

- Schedule: daily at 09:00 (after any overnight ingests)
- Delivery: to the user's Feishu channel with a summary of what changed
