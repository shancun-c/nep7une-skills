# Full-Scan Mode

When the cron prompt modifies the sync to scan ALL source notes (not just today's), the workload is 50+ notes vs the typical 0-3/day. This reference covers the strategy for efficient full scans.

## When To Use

- First sync after a period without daily runs (backlog of unprocessed sources)
- User explicitly modifies the prompt: "扫描 40 Sources/ 中的所有来源笔记（不仅是今天创建的）"
- Major vault reorganization or knowledge domain expansion

## Batching Strategy

Read source notes in parallel batches of 6 to maximize throughput while staying within context limits:

```
Batch 1: most-recent 6 (newest first, highest potential for novel insights)
Batch 2: next 6
Batch 3+: continue until hitting diminishing returns (notes already covered by existing knowledge)
```

Skip sources that are:
- Purely news reporting with no durable insight (e.g., "X released version Y, here are the specs")
- Already fully extracted — check existing knowledge notes' `source` frontmatter
- Technical how-to guides that don't contain a generalizable principle

## Group Creation Heuristics

During full scans, new knowledge domains emerge more frequently. Create a new group when:
- The insight belongs to a domain with NO existing group that captures it
- The domain has clear conceptual boundaries (e.g., "AI产业与经济" is distinct from "工具与执行")
- At least 2-3 candidate knowledge notes could live in the new group (not just one)

Do NOT create a new group when:
- The insight could reasonably fit an existing group with minor expansion
- Only a single note would live there (can always promote to a group later)

## 3-Note Daily Limit

Even during full scans, respect the "max 3 new knowledge notes per day" guardrail. When there are more than 3 candidates:
1. Prioritize cross-domain insights (span multiple source notes)
2. Prioritize genuinely new domains over extensions of existing knowledge
3. Save remaining candidates as extensions/updates to existing notes where possible
4. Flag remaining candidates in the report for next run

## Precedent

2026-05-29 full scan of ~50 source notes produced:
- 3 new knowledge notes (NVIDIA商业模式, Agent控制面/执行面分离, 模型静默降级)
- 1 updated existing note (AI编程工具竞争)
- 1 new group (AI产业与经济)
- ~15 source notes identified as "worth watching but not yet producing standalone knowledge" (flagged in report)
