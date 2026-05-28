---
name: feishu-formatting
description: Format agent output for Feishu/Lark rendering, and adapt communication style (language, tone). Use when the user's primary platform is Feishu — avoid Markdown tables, use separators and structured lists, and know which Markdown features Feishu supports well.
---

# Feishu Output Formatting

## Trigger

The user communicates via Feishu (Lark). Load this skill when responding on Feishu — it covers both formatting rules and communication style (language, tone). Apply the rules automatically; don't ask the user how they'd like things formatted.

## Communication Style (absorbed from feishu-communication)

### Language

The user communicates in Chinese. Respond in Chinese unless the user explicitly switches to English or the content being discussed is in another language.

### Tone

Concise but thorough. Technical depth is valued over hand-holding. Skip pleasantries and get to the point.

### Platform

The primary platform for this user is Feishu via the WebSocket gateway. **Every response** sent through Feishu must follow the formatting rules below and the communication style above unless the user explicitly asks for raw Markdown or a different format.

---

## Why This Matters

Feishu's Markdown renderer differs from GitHub/GitLab/standard Markdown. Markdown tables render as raw pipe characters with no alignment — borderline unreadable. Complex nested formatting collapses. The user has corrected this explicitly.

## Formatting Rules

### DO NOT use Markdown tables
Feishu renders `| col1 | col2 |` tables as literal text — no borders, no alignment. The user called this "特别混乱" (chaotic).

Instead, use one of these patterns:

**Pattern A — Separator blocks** (best for 3-5 items with 2-3 fields each):
```
━━━━━━━━━━━━━━━━━━
🔥 Section Header

▸ item-name
  field1 | field2 | field3
  description line
```

**Pattern B — Compact list** (best for 5+ items with minimal metadata):
```
• item-name — key data — one-line summary
• item-name — key data — one-line summary
```

**Pattern C — Numbered list with sub-details** (best for ranked lists):
```
1. item-name — one-line summary
   detail line, indented
```

### DO use these Feishu-friendly constructs
- **Bold** (`**text**`) — renders correctly
- *Italic* (`*text*`) — renders correctly
- `inline code` — renders correctly
- Code blocks (```) — renders correctly
- Bullet lists (`- ` or `• `) — renders correctly
- Numbered lists — renders correctly
- Horizontal rules (`---` or Unicode `━━━`) — renders correctly
- Blockquotes (`> `) — renders correctly
- Links `[text](url)` — renders correctly

### Use Unicode dividers over `---`
Feishu can render `---` but Unicode dividers (like `━━━━━━━━━━━━━━━━━━`) are more visually distinct and never trigger unintended horizontal-rule behavior.

### Keep structural depth shallow
Feishu's Markdown parser handles at most 2-3 levels of nesting. Avoid:
- Nested blockquotes beyond 2 levels
- Lists inside blockquotes inside lists
- Deeply indented structures

### For structured data
When you would naturally use a table, consider:
1. **Inline key-value** format: `field: value | field: value` on one line
2. **Separator blocks** (Pattern A above)
3. **Simple lists** with consistent indentation

## Pitfalls

- Tables are the #1 readability killer on Feishu — avoid them always
- Over-engineered layouts with heavy Unicode borders waste tokens without improving readability
- Don't pre-emptively ask "how would you like this formatted" — just apply these rules
- Feishu supports emoji (✅❌🔥⚠️📊💡) — use them sparingly as visual anchors

## Verification

After composing a Feishu-bound response, mentally scan: are there any pipe-character table borders? If yes, restructure.
