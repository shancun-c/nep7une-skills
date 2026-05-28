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
6. **Update confidence** in frontmatter: `high` (all core claims ✅), `medium` (some unverified), `low` (contradictions found).
7. **Append table** to source note. Use a rich format with numbered claims, evidence URLs, and a key findings summary:

```markdown
## Cross-verification

_通过 anysearch 交叉验证 N 项核心主张，X 项 ✅ 确认，Y 项 ⚠️ 需修正_

| # | 主张 | 结果 | 证据 |
|---|------|------|------|
| 1 | claim text | ✅ | [Source Name](URL) — specific corroborating detail |
| 2 | claim text | ⚠️ | 数据有出入：actual finding with correction note |
| 3 | claim text | ❌ | 与 [Source](URL) 矛盾：contradiction detail |

### 关键发现

- **finding 1**：most important takeaway from cross-verification
- **finding 2**：second-order insight worth flagging
- **finding 3**：any correction to the original article's claims
```

The simpler format (claim / result / source, no numbering, no key findings) is also acceptable for short articles with few claims. Use the richer format when verifying 5+ claims or when corrections are found.

## anysearch CLI reference

```bash
# Batch search (up to 5 parallel) — use --queries with JSON array to set per-query flags
# IMPORTANT: --max_results and --freshness go INSIDE the JSON, not as global flags
python <skill_dir>/scripts/anysearch_cli.py batch_search --queries '[
  {"query":"claim 1 keywords", "max_results":3, "freshness":"month"},
  {"query":"claim 2 keywords", "max_results":3, "freshness":"month"},
  {"query":"claim 3 keywords", "max_results":3, "freshness":"month"}
]'

# Alternative: --query flag per query (no per-query flags possible)
python <skill_dir>/scripts/anysearch_cli.py batch_search \
  --query "claim 1" --query "claim 2" --query "claim 3"

# Fallback: individual search (accepts --max_results and --freshness as flags)
python <skill_dir>/scripts/anysearch_cli.py search "specific claim keywords" --max_results 3 --freshness month

# Node.js fallback (if Python requests not available)
node <skill_dir>/scripts/anysearch_cli.js search "specific claim keywords" --max_results 3 --freshness month

# Extract full content from a specific URL (for primary source comparison)
python <skill_dir>/scripts/anysearch_cli.py extract "https://example.com/original-post"
```

## Pitfalls

- **`batch_search` JSON format**: global flags like `--max_results` and `--freshness` are NOT accepted by `batch_search`. They must be set per-query inside the JSON array, e.g. `{"query":"...", "max_results":5, "freshness":"month"}`. Calling `batch_search --query "..." --max_results 5` will produce `error: unrecognized arguments`.
- `batch_search` with 3+ queries frequently times out at 30s. Always be ready to fall back to individual `search` calls.
- Both the Python CLI (`python scripts/anysearch_cli.py`) and Node.js CLI (`node scripts/anysearch_cli.js`) work. The Python CLI requires `requests` which may not be installed — fall back to Node.js CLI.
- `extract` is read-only and does not modify the vault — it fetches page content for comparison.
