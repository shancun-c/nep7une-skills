# CJK Search Routing: Code-Level Detail

Source: `hermes_state.py::search_messages()` (lines 2212-2315)

## Architecture

Hermes maintains TWO FTS5 tables on `messages`:

```sql
-- Default: unicode61 tokenizer (English-first, CJK per-character)
CREATE VIRTUAL TABLE messages_fts USING fts5(content);

-- Trigram: 3-byte sliding windows (CJK phrase matching)
CREATE VIRTUAL TABLE messages_fts_trigram USING fts5(
    content,
    tokenize='trigram'
);
```

Both tables are kept in sync via INSERT/UPDATE/DELETE triggers on `messages`.

## Routing Logic (Pseudocode)

```
search_messages(query):
    query = sanitize(query)           # strip FTS5 special chars
    
    if NOT contains_cjk(query):
        → unicode61 FTS5 path (standard English search)
        → snippet(messages_fts, ...)
        → MATCH with FTS5 boolean operators
        
    else:  # CJK detected
        raw = query.strip('"')
        cjk_count = count_cjk(raw)     # total CJK chars across all tokens
        tokens = [t for t in raw.split() if t not in {AND,OR,NOT} and contains_cjk(t)]
        any_short = any(count_cjk(t) < 3 for t in tokens)
        
        if cjk_count >= 3 AND NOT any_short:
            → Trigram FTS5 path
            → Each non-operator token quoted: "token"
            → snippet(messages_fts_trigram, ...)
            → Operators (AND/OR/NOT) preserved
            
        else:
            → LIKE fallback path
            → Per-token LIKE: content LIKE '%token%' OR tool_name LIKE '%token%' OR tool_calls LIKE '%token%'
            → Multiple tokens joined with OR
            → No ranking, no FTS5 snippet (manual substr extraction)
            → Ordered by timestamp DESC
```

## CJK Detection Range

```python
def _contains_cjk(text):
    for ch in text:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF      # CJK Unified Ideographs
            or 0x3400 <= cp <= 0x4DBF    # CJK Extension A
            or 0x20000 <= cp <= 0x2A6DF  # CJK Extension B
            or 0x3000 <= cp <= 0x303F    # CJK Symbols
            or 0x3040 <= cp <= 0x309F    # Hiragana
            or 0x30A0 <= cp <= 0x30FF    # Katakana
            or 0xAC00 <= cp <= 0xD7AF):  # Hangul
            return True
    return False
```

## Path Selection Examples

| Query | CJK count | Token check | Path | Behavior |
|-------|-----------|-------------|------|----------|
| `docker` | 0 | — | unicode61 | Standard FTS5 |
| `飞书` | 2 | `<3` → short | LIKE | `%飞书%` |
| `配置` | 2 | `<3` → short | LIKE | `%配置%` |
| `环境变量` | 4 | `≥3` → trigram | trigram | `"环境变量"` phrase match |
| `飞书 配置` | 4 | `飞书<3` → short | LIKE | `%飞书% OR %配置%` (OR!) |
| `大别山项目` | 5 | `≥3` → trigram | trigram | `"大别山项目"` |
| `广西 OR 桂林 OR 漓江` | 6 | each `<3` → short | LIKE | 3 separate LIKE clauses |

## Key Design Insight (#20494)

The per-token length check was added because trigram needs ≥3 CJK chars per token to produce any n-grams. Without it, multi-term queries like `广西 OR 桂林 OR 漓江` (6 total CJK chars but each token is only 2) would hit the trigram path and return 0 results — silently.

## LIKE Fallback: OR Semantics

When multiple short CJK tokens are present (e.g., `飞书 配置`), each token gets its own LIKE clause chained with OR:

```sql
(content LIKE '%飞书%' OR tool_name LIKE '%飞书%' OR tool_calls LIKE '%飞书%')
OR
(content LIKE '%配置%' OR tool_name LIKE '%配置%' OR tool_calls LIKE '%配置%')
```

This means `飞书 配置` matches messages containing EITHER term, not both. For AND semantics on short CJK, use a single quoted phrase or the trigram path (join terms without spaces).
