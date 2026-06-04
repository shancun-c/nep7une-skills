# Cross-verification Workflow

## When to cross-verify

Cross-verify when the source contains claims about:
- Real-world events, product releases, or company announcements
- Statistics, user numbers, market data
- Personnel changes (hires, departures, team assignments)
- Feature availability or deprecation
- Any claim that can be checked against an independent source

Skip cross-verification only for:
- Pure opinion/editorial pieces with no factual claims
- Personal narratives where the author is the primary source
- Source material that is itself the authoritative primary source (e.g. official docs)

## How to cross-verify

1. **Identify material claims** in the source — list 5-10 specific, verifiable assertions.
2. **Search with anysearch** using `batch_search` with `--query` (up to 5 queries in parallel). Each query should target a specific claim.
3. **Fallback**: if `batch_search` times out (common with 3+ queries), fall back to individual `search` calls. Individual calls have lower latency and better reliability. Do NOT skip verification because batch_search failed.
4. **Prefer primary sources**: if the article references a blog post, X thread, or official announcement, extract that URL directly and compare — don't just trust secondary reporting.
5. **Rate each claim**: ✅ confirmed / ⚠️ partially confirmed or unverifiable / ❌ contradicted.
   - When a claim cannot be verified through any available means and requires the user's domain knowledge to judge, mark it as ⚠️ AND append `review: true` to the table row (see table template below). This flags it for future audit aggregation.
6. **Update confidence** in frontmatter: `high` (all core claims ✅), `medium` (some unverified or `review: true` items present), `low` (contradictions found).
7. **Append table** to source note. Use a rich format with numbered claims, evidence URLs, and a key findings summary:

```markdown
## Cross-verification

_通过 anysearch 交叉验证 N 项核心主张，X 项 ✅ 确认，Y 项 ⚠️ 需修正_

| # | 主张 | 结果 | 证据 |
|---|------|------|------|
| 1 | claim text | ✅ | [Source Name](URL) — specific corroborating detail |
| 2 | claim text | ⚠️ | 数据有出入：actual finding with correction note |
| 3 | claim text | ⚠️ `review: true` | 无法独立验证：[reason] — 需人工判断 |
| 4 | claim text | ❌ | 与 [Source](URL) 矛盾：contradiction detail |

> When marking `review: true`, include a brief reason why the claim couldn't be independently verified (e.g., "非公开财务数据", "内部决策细节", "单一来源无法交叉验证"). These items will be surfaced during `audit` as pending human review.

### 关键发现

- **finding 1**：most important takeaway from cross-verification
- **finding 2**：second-order insight worth flagging
- **finding 3**：any correction to the original article's claims
```

The simpler format (claim / result / source, no numbering, no key findings) is also acceptable for short articles with few claims. Use the richer format when verifying 5+ claims or when corrections are found.

## anysearch CLI reference

The anysearch CLI scripts live in the `anysearch` skill directory (NOT in obsidian-wiki-skill). Discover the path with `search_files` or use the known location:

```bash
ANYSEARCH_DIR="$HOME/.hermes/skills/anysearch/scripts"

# Batch search (up to 5 parallel) — use --queries with JSON array to set per-query flags
# IMPORTANT: --max_results and --freshness go INSIDE the JSON, not as global flags
python $ANYSEARCH_DIR/anysearch_cli.py batch_search --queries '[
  {"query":"claim 1 keywords", "max_results":3, "freshness":"month"},
  {"query":"claim 2 keywords", "max_results":3, "freshness":"month"},
  {"query":"claim 3 keywords", "max_results":3, "freshness":"month"}
]'

# Alternative: --query flag per query (no per-query flags possible)
python $ANYSEARCH_DIR/anysearch_cli.py batch_search \
  --query "claim 1" --query "claim 2" --query "claim 3"

# Fallback: individual search (accepts --max_results and --freshness as flags)
python $ANYSEARCH_DIR/anysearch_cli.py search "specific claim keywords" --max_results 3 --freshness month

# Node.js fallback (if Python requests not available)
node $ANYSEARCH_DIR/anysearch_cli.js search "specific claim keywords" --max_results 3 --freshness month

# Extract full content from a specific URL (for primary source comparison)
python $ANYSEARCH_DIR/anysearch_cli.py extract "https://example.com/original-post"
```

## Pitfalls

- **`batch_search` JSON format (OBJECTS, not strings)**: Queries must be an array of objects `[{"query":"..."}, ...]`, NOT a string array `["query1", "query2"]`. Passing string arrays yields: `Error: batch_search supports a maximum of 5 queries` or `queries[0] must be an object`. Example correct: `--queries '[{"query":"NVIDIA RTX 2026"},{"query":"Claude 4 release"}]'`. The `--query` shorthand (repeatable flag) is an alternative that avoids JSON quoting issues: `--query "first" --query "second"`.
- **`batch_search` 5-query hard limit**: `batch_search` supports a maximum of 5 queries. Exceeding this returns `Error: batch_search supports a maximum of 5 queries`. Split into multiple `batch_search` calls or fall back to individual `search` calls for queries 6+.
- **`batch_search` global flag pitfall**: global flags like `--max_results` and `--freshness` are NOT accepted by `batch_search`. They must be set per-query inside the JSON array, e.g. `{"query":"...", "max_results":5, "freshness":"month"}`. Calling `batch_search --query "..." --max_results 5` will produce `error: unrecognized arguments`.
- `batch_search` with 3+ queries frequently times out at 30s. Always be ready to fall back to individual `search` calls.
- Both the Python CLI (`python scripts/anysearch_cli.py`) and Node.js CLI (`node scripts/anysearch_cli.js`) work. The Python CLI requires `requests` which may not be installed — fall back to Node.js CLI.
- `extract` is read-only and does not modify the vault — it fetches page content for comparison.
- **`anysearch` service unavailability**: The search service returns `Search is temporarily unavailable` for all queries simultaneously, including `batch_search`. This is a transient backend issue, not a client-side error. When this happens: wait 30-60 seconds and retry with individual `search` calls (lower latency), or fall back to `anysearch extract` for specific known URLs. Do not treat service unavailability as a permanent failure — cross-verification should still be attempted before marking confidence as final.
- **`extract` 403/429 on certain sites**: Some sites deliberately block automated extraction — e.g. `openai.com` returns HTTP 403, `substack.com` premium content returns 403, and high-traffic sites may rate-limit with HTTP 429. When `extract` fails: do NOT retry repeatedly (wastes tokens and won't succeed). Instead, fall back to the search results from `batch_search` or individual `search` calls — the snippets and linked URLs typically provide enough context to verify claims. Mark the claim ⚠️ (not ❌) if only search snippets are available for corroboration. For 429 (rate limit), a single retry after 5-10 seconds is acceptable before falling back to search snippets.
