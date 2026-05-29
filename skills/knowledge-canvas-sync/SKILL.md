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
- **Knowledge domains are open.** Do NOT limit extraction to existing groups. When a source note contains durable insight in a new domain (economics, AI industry dynamics, model competition, open-source business models, tool evolution, etc.), create a new group rather than forcing it into an existing one. The canvas grows organically with the user's knowledge. Current groups are a snapshot, not a boundary.

## Execution Companions

**🚨 Canvas operations MUST use `obsidian-canvas-creator` — this is mandatory.** Do NOT use `json-canvas` for this workflow. The `obsidian-canvas-creator` skill provides the layout algorithms, spacing constants, and reorganization patterns that `json-canvas` does not. The `json-canvas` skill is a generic canvas tool; this workflow requires the domain-specific layout intelligence in `obsidian-canvas-creator`.

- **`obsidian-canvas-creator`** 🔒 MANDATORY — for ALL canvas read/write/layout operations. Always load this skill before touching the canvas. It provides: layout algorithms (2-col grid, row-based positioning, spacing constants NODE_W=360, NODE_H=170, GAP_X=50, GAP_Y=40, GROUP_PAD=50, GROUP_GAP=80, GROUP_W=970), color scheme enforcement, collision detection, and reorganization patterns.
- `obsidian-markdown` for knowledge note creation
- `obsidian-wiki-skill` for vault orientation and source note processing
- Filesystem tools for reading source notes and existing knowledge notes
- `scripts/verify-canvas-colors.py` — verification-only; run after canvas writes to catch color errors
- `scripts/fix-canvas-colors.py` — comprehensive fix + verify; use this for canvas maintenance (group colors, stale yellows, edge integrity). Pass `STALE_YELLOW_IDS=id1,id2` env var to revert stale nodes. Use `--dry-run` to preview without writing.
- `references/canvas-state.md` — current canvas layout, groups, node stats, and color scheme; consult before structural changes

## Workflow

### 1. Orient

Load the current state:

- Read `99 System/Knowledge Canvas.canvas` — the existing knowledge graph
- Read `30 Knowledge/Knowledge Index.md` — the knowledge index
- List all knowledge notes in `30 Knowledge/` — current inventory
- List ALL source notes in `40 Sources/` sorted by modification time (newest first). For daily runs, prioritize notes created/modified today; for full-scan mode (when the prompt says "所有来源笔记"), process all notes in batches — see `references/full-scan-mode.md`

### 2. Scan New Sources

For each source note (most recent first; in batches of 6 for full scans — see `references/full-scan-mode.md`):

- Read the source note content (Summary, Key Points, My Take sections)
- Skip sources that are purely news reporting with no durable insight
- Skip sources whose insights are already fully captured by existing knowledge notes (check `source` frontmatter)
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
- **Update canvas-state.md**: Update `references/canvas-state.md` with the current date, stats, and any new node IDs added today (for tomorrow's stale-yellow reversion)
- **Verify colors**: After every canvas write, run `scripts/fix-canvas-colors.py` to programmatically verify and fix:
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

- **Group nodes** by knowledge domain. Groups are created as new domains emerge — do not limit to predefined categories. Current groups (see `99 System/Knowledge Canvas.canvas` and `references/canvas-state.md`):
  - **工程原则** (Engineering Principles) — foundational design philosophy
  - **工具与执行** (Tools & Execution) — implementation & tooling layer
  - **交互与自动化** (Interaction & Automation) — interaction paradigms
  - **记忆与知识** (Memory & Knowledge) — knowledge systems
  - **领域实践** (Domain Practice) — applied cases
  - *Future groups may emerge for economics, industry dynamics, model competition, open-source ecosystems, etc.*
- **New group creation**: When creating a new group, follow the existing layout convention (2-column grid, GAP_X=50, GAP_Y=40, GROUP_PAD=50). Position it in a new row below existing groups. Group color is ALWAYS `"4"` (green).
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
- Do not create more than 3 new knowledge notes per day during normal daily runs — if there are more candidates, prioritize the most durable ones and flag the rest for next run. For full-scan mode, this limit can be relaxed; consult `references/full-scan-mode.md` for batching and prioritization strategy
- Do not delete existing knowledge notes unless they are demonstrably wrong or superseded
- Do not rearrange the entire canvas layout on every run — only adjust positions for new nodes and to resolve overlaps
- Knowledge notes must link back to their source notes (traceability)
- If no source notes were ingested today, skip the **scan** phase (step 2) — but still run canvas maintenance (step 4: color refresh, group fix, orphan reconciliation, stale-yellow reversion). Canvas color drift accumulates silently; maintenance must run daily regardless of new sources.
- **NEVER mix group colors**: all groups are `"4"` (green). Do NOT use `"5"` or `"6"` on group nodes — semantic meaning is expressed through text node colors only
- **Always load `obsidian-canvas-creator` skill** before any canvas read/write operations — it provides the layout algorithms, spacing rules, and JSON format conventions. This is NON-NEGOTIABLE — do not skip loading this skill.
- **Do NOT use `json-canvas` skill for this workflow.** The `json-canvas` skill lacks the domain-specific layout intelligence (2-col grid, row-based positioning, spacing constants) that `obsidian-canvas-creator` provides. Using `json-canvas` will result in incorrectly sized nodes (320×100 instead of 360×170), wrong group sizes, and layout overlaps.
- **Color rules apply to ALL canvas operations**, not just sync runs. When rebuilding or restructuring the canvas (even outside a sync workflow), the color scheme in this skill takes precedence over obsidian-canvas-creator's general-purpose color recommendations. Common mistake: assigning semantic colors to groups (purple for principles, cyan for tools) — this always violates the convention that ALL groups are green.

## Pitfalls

- **🚨 NEVER use `patch` tool to edit `.canvas` files.** This is the #1 failure mode. The `patch` tool encounters escape-drift errors with `\\\"` and `\\\\n` sequences in JSON canvas files — the error message says "Escape-drift detected" and the file is NOT modified. This will happen on EVERY attempt; retrying with different strings will also fail. Instead, write a Python script to a temp file (e.g. `/tmp/fix_canvas.py`) and run it via `terminal`. The script should: read the canvas JSON, apply color/node fixes programmatically, write back with `json.dump(..., indent=\"\\t\")`. This is the only reliable way to modify canvas JSON. The `scripts/fix-canvas-colors.py` script already exists for color fixes — prefer running it over writing ad-hoc scripts.

- **Group colors drift over time.** After multiple canvas edits (especially by other tools or workflows), groups can pick up wrong colors (e.g. \"5\" or \"6\"). Always verify ALL group colors are \"4\" (green) during every sync, even when no new knowledge was added. This is the most common canvas violation.

- **Stale yellow nodes accumulate.** Nodes added with color \"3\" must be reverted to \"5\" after 24 hours. Track node IDs from previous syncs (stored in `references/canvas-state.md`) and revert them programmatically. Yellow edges associated with those nodes must also be reverted.

- **Vault path not obvious.** The Obsidian vault is at a Google Drive path configured in `obsidian-wiki-skill/references/vault-config.md`. Always consult that reference first — the vault is NOT at `~/Documents/Obsidian Vault` or `~/Obsidian`.

- **canvas-state.md patch leaves stale trailing content.** When using `patch` to update `references/canvas-state.md`, old stats lines can survive the patch if the old_string doesn't extend far enough. The result is a file that has both the new stats AND the previous run's stats at the bottom. Always read back the file after patching and remove any leftover stale lines. The `## Today's New Nodes` section is the natural boundary — nothing should appear after the last new-node-ID bullet.

- **Cron execution: memory is UNAVAILABLE.** Cron-spawned agents run with `skip_memory=True`, so they cannot read the vault path from memory or user profile. The cron job's prompt MUST include the absolute vault path explicitly (e.g. "The Obsidian vault is at /Users/.../the_ai_obsidian"). Alternatively, set `workdir` on the cron job to the vault path — this also injects `AGENTS.md` context. Without this, the cron agent will search for files in `~/.hermes/hermes-agent/` (the scheduler's cwd) and fail with "File not found" errors.

## Cron Integration

This skill is designed to run daily via a cron job. The cron prompt MUST include the absolute vault path because cron agents run with `skip_memory=True` and cannot read it from memory.

### Recommended cron job configuration

```
# Prompt — include the vault path explicitly; cron agents have no memory
Vault 路径：/Users/<user>/Library/CloudStorage/GoogleDrive-<email>/其他计算机/我的计算机/the_ai_obsidian

Load knowledge-canvas-sync skill, then run the full workflow with these modifications:

## 1. 扫描范围
扫描 40 Sources/ 中的**所有**来源笔记（不仅是今天创建的），按修改时间倒序排列。对于每篇来源笔记：
- 提取其中包含的耐久知识洞察（原则、模式、结论），不仅仅是事实性新闻
- 关注跨领域的洞察：AI 产业经济、模型竞争格局、工具进化趋势、AI 可视化、开源商业模式、Agent 架构、记忆系统等
- 如果一篇来源笔记此前已提取过知识但有了新的理解角度，也应该补充更新

## 2. 分组策略
**不要局限于现有的分组。** 当来源笔记中包含全新的知识领域时，创建新的 group。当前分组是快照而非边界。

## 3. 执行步骤
1. 列出 40 Sources/ 中所有 .md 文件，按修改时间排序
2. 逐篇读取，识别耐久知识候选
3. 在 30 Knowledge/ 中创建或更新对应的知识笔记
4. 维护 99 System/Knowledge Canvas.canvas
5. 更新 30 Knowledge/Knowledge Index.md
6. 用中文输出完整变更报告

# Schedule
0 9 * * *  (daily at 09:00, after any overnight ingests)

# Delivery
origin  (delivers to the same Feishu DM where the job was created)

# Toolsets
file, terminal, skills  (minimal set — the skill loads obsidian-canvas-creator, obsidian-markdown, obsidian-wiki-skill)

# Skills (json-canvas is DEPRECATED — use obsidian-canvas-creator)
knowledge-canvas-sync, obsidian-canvas-creator, obsidian-markdown, obsidian-wiki-skill
```

### Alternative: use workdir

Instead of hardcoding the vault path in the prompt, set `workdir` to the vault path. This also injects the vault's `AGENTS.md` if present:

```
hermes cron edit 98246e49fcaa --workdir "/Users/<user>/Google Drive/其他计算机/我的计算机/the_ai_obsidian"
```

### Full-scan variant

When the prompt modifies the workflow to scan ALL source notes (not just today's), read `references/full-scan-mode.md` before starting. It covers batching strategy for 50+ notes, group-creation heuristics, and how to respect the 3-note daily limit during bulk scans.

### Delivery pitfall

Cron output is delivered via the gateway's live platform adapter. When the gateway is busy processing a user message in the same chat, the cron delivery can be silently dropped — the agent.log will say "delivered via live adapter" but the message never appears to the user. If the user reports not seeing cron output, check `~/.hermes/cron/output/<job_id>/` — the output file is saved there regardless of delivery success.
