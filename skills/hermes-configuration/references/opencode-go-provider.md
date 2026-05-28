# OpenCode Go Provider Configuration

OpenCode Go is a $10/month subscription providing OpenAI-compatible API access to open models. Base URL: `https://opencode.ai/zen/go/v1`

## Credential

```bash
# In ~/.hermes/.env
OPENCODE_GO_API_KEY=<your_key>
```

## Model Discovery

```bash
curl -s "https://opencode.ai/zen/go/v1/models" \
  -H "Authorization: Bearer $(grep OPENCODE_GO_API_KEY ~/.hermes/.env | grep -v '^#' | cut -d= -f2)" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['id']) for m in d.get('data',[])]"
```

## Current Model Catalog (May 2026)

| Model | Type | Best for |
|-------|------|----------|
| `deepseek-v4-pro` | Text | Main agent, compression, web extract, approval |
| `deepseek-v4-flash` | Text (fast) | Title generation, triage, lightweight tasks |
| `glm-5` / `glm-5.1` | Multimodal | Vision tasks |
| `kimi-k2.5` / `kimi-k2.6` | Text (likely vision) | General purpose |
| `minimax-m2.5` / `minimax-m2.7` | Text | General purpose |
| `mimo-v2-pro` / `mimo-v2.5-pro` | Text | General purpose |
| `mimo-v2-omni` | Multimodal | Vision tasks (alternative to glm-5) |
| `qwen3.6-plus` / `qwen3.5-plus` | Text (likely vision) | General purpose |
| `hy3-preview` | Text | Preview/evaluation |

## Configuration Pattern

When using opencode-go as the main provider, reuse it for all auxiliary tasks to avoid the `auto` provider silently failing:

```yaml
# ~/.hermes/config.yaml
model:
  default: deepseek-v4-pro
  provider: opencode-go
  base_url: https://opencode.ai/zen/go/v1
  api_mode: chat_completions

auxiliary:
  vision:
    provider: opencode-go
    model: glm-5              # Must be multimodal
  compression:
    provider: opencode-go
    model: deepseek-v4-pro
  web_extract:
    provider: opencode-go
    model: deepseek-v4-pro
  skills_hub:
    provider: opencode-go
    model: deepseek-v4-pro
  approval:
    provider: opencode-go
    model: deepseek-v4-pro
  mcp:
    provider: opencode-go
    model: deepseek-v4-pro
  title_generation:
    provider: opencode-go
    model: deepseek-v4-flash  # Lightweight saves cost
  triage_specifier:
    provider: opencode-go
    model: deepseek-v4-pro
  kanban_decomposer:
    provider: opencode-go
    model: deepseek-v4-pro
  profile_describer:
    provider: opencode-go
    model: deepseek-v4-pro
  curator:
    provider: opencode-go
    model: deepseek-v4-pro
```

## Why This Matters

When `auxiliary.*.provider` is `auto` (default), Hermes tries to auto-detect a suitable provider. Without `OPENROUTER_API_KEY` or `GOOGLE_API_KEY` set, it silently falls back — producing empty/error results for vision, session search, and compression tasks with no visible warning.
