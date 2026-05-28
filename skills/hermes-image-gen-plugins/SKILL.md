---
name: hermes-image-gen-plugins
description: Hermes Agent image generation subsystem — plugin architecture, ImageGenProvider contract, dispatch chain, and parallel-maintenance pitfalls. Load when modifying image_gen tool, adding provider plugins, or debugging image generation routing.
version: 1.0.0
author: agent
tags: [hermes, image-generation, plugins, openai, openai-codex, fal]
---

# Hermes Image Generation Plugins

Internal architecture and maintenance guide for the image generation subsystem. Covers the tool layer → dispatch → plugin chain, the `ImageGenProvider` interface contract, and the critical pitfall of parallel plugin updates.

**Load this skill when:**
- Adding or modifying parameters on `image_generate` tool
- Adding a new image generation provider plugin
- Debugging why a plugin isn't receiving a new parameter
- Extending the `ImageGenProvider` interface

---

## 1. Architecture Overview

```
image_generate tool call
  │
  ▼
_image_generate_handler()          ← tools/image_generation_tool.py
  │  extracts args, calls dispatch
  ├─▶ _dispatch_to_plugin_provider()   ← if image_gen.provider is set
  │     │  reads image_gen.provider from config.yaml
  │     │  resolves provider from image_gen_registry
  │     └─▶ provider.generate(prompt, aspect_ratio, **kwargs)
  │           │
  │           ├─ openai/         ← REST API (images.generate)
  │           ├─ openai-codex/   ← Codex Responses API (streaming)
  │           └─ xai/            ← xAI API
  │
  └─▶ image_generate_tool()         ← FAL fallback (in-tree, legacy)
        └─ _build_fal_payload()
```

## 2. Plugin Directory Structure

```
plugins/image_gen/
├── openai/__init__.py         # OpenAI REST (requires OPENAI_API_KEY)
├── openai-codex/__init__.py   # OpenAI via Codex OAuth (no API key)
└── xai/__init__.py            # xAI / Grok image gen
```

## 3. ImageGenProvider Interface Contract

All plugins implement `ImageGenProvider` from `agent/image_gen_provider.py`:

```python
class ImageGenProvider:
    def generate(self, prompt: str, aspect_ratio: str = "landscape", **kwargs) -> Dict[str, Any]:
        """Return {"success": bool, "image": str|None, ...}"""
```

**When adding a new parameter to `image_generate`:**

1. Add it to `IMAGE_GENERATE_SCHEMA` in `tools/image_generation_tool.py`
2. Extract it in `_handle_image_generate()` → pass to both dispatch paths
3. Accept it in `_dispatch_to_plugin_provider()` → pass via `**kwargs`
4. **CRITICAL: Update EVERY plugin's `generate()` method to extract and use the new kwarg**

---

## 4. ⚠️ Parallel-Update Pitfall

The `openai/` and `openai-codex/` plugins are **mirrored implementations** of the same underlying model (gpt-image-2). They differ only in the transport layer (REST vs Codex Responses streaming), but share identical:

- Model catalog (`_MODELS` dict)
- Size mappings (`_SIZES` dict)
- Parameter handling logic

**When you add a parameter to one, you MUST add it to the other.** The dispatch layer passes `**kwargs` blindly — if a plugin ignores a kwarg, it silently falls back to defaults with no error.

**Example (the `size` parameter, May 2026):**
- `openai/` was updated with `_resolve_size()` + `size_kw = kwargs.pop("size", None)` ✅
- `openai-codex/` was **missed** — still used `_SIZES.get(aspect)` ❌
- Result: `size="720x1280"` was silently ignored, image generated at default landscape 1536x1024

**Checklist when extending the interface:**

| File | What to add |
|------|-------------|
| `tools/image_generation_tool.py::IMAGE_GENERATE_SCHEMA` | Schema entry for new param |
| `tools/image_generation_tool.py::_handle_image_generate` | Extract from args, pass downstream |
| `tools/image_generation_tool.py::_dispatch_to_plugin_provider` | Accept param, include in kwargs |
| `tools/image_generation_tool.py::image_generate_tool` | Accept param (FAL fallback path) |
| `plugins/image_gen/openai/__init__.py::generate()` | Extract from kwargs, use it |
| `plugins/image_gen/openai-codex/__init__.py::generate()` | **Same as openai/** |
| `plugins/image_gen/xai/__init__.py::generate()` | If applicable |

---

## 5. Dispatch Chain Detail

### How the active provider is selected

```python
# tools/image_generation_tool.py::_dispatch_to_plugin_provider()
configured = _read_configured_image_provider()  # reads image_gen.provider from config.yaml
if not configured or configured == "fal":
    return None  # fall through to in-tree FAL path
provider = get_provider(configured)  # from image_gen_registry
```

The `image_gen.provider` config key controls routing:
- `"fal"` or unset → in-tree FAL path (legacy)
- `"openai"` → `plugins/image_gen/openai/`
- `"openai-codex"` → `plugins/image_gen/openai-codex/`

### Kwargs passthrough

```python
# All kwargs not explicitly handled are passed to provider.generate()
kwargs = {"prompt": prompt, "aspect_ratio": aspect_ratio}
if size:
    kwargs["size"] = size
if configured_model:
    kwargs["model"] = configured_model
result = provider.generate(**kwargs)
```

Providers receive unknown kwargs via `**kwargs` — they MUST extract what they support and can safely ignore the rest (though ignoring causes silent fallback to defaults).

---

## 6. Plugin-Specific Notes

### openai/ (REST)
- Uses `client.images.generate()` — synchronous REST call
- `model` in payload is always `"gpt-image-2"`; quality is tier-dependent
- `_resolve_size()` handles custom dimensions

### openai-codex/ (Codex Responses)
- Uses `client.responses.stream()` — streaming via ChatGPT/Codex backend
- Image generation is invoked as a `tool` in the Responses API, not a direct REST call
- Chat model: `gpt-5.4`, image model: `gpt-image-2`
- **Needs `_resolve_size()` too** — add it when adding to openai/

### xai/
- Separate provider; check its implementation independently

---

## References

- `references/dispatch-chain-trace.md` — Line-by-line trace of the tool → plugin call chain with all file paths and line numbers.
