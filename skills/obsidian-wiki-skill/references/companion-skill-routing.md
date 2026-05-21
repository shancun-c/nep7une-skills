# Companion Skill Routing

Use this file to map this orchestration skill onto the execution capabilities available in the current runtime. Do not assume every runtime exposes the same companion skills.

## `obsidian`

Use `obsidian` when running in Hermes or another runtime that exposes a filesystem-first Obsidian skill.

Good fit:

- reading and editing Markdown notes
- preserving vault-local folder and naming conventions
- searching within an Obsidian vault through filesystem tools
- applying safe, targeted note changes

If a lower-level Codex-style companion skill is unavailable, prefer the local `obsidian` skill over hand-rolling Obsidian conventions.

## `obsidian-markdown`

Use `obsidian-markdown` when writing or editing Obsidian notes that depend on:

- wikilinks
- embeds
- callouts
- frontmatter properties
- Obsidian-flavored Markdown details

This skill owns note-format correctness.

## `obsidian-cli`

Use `obsidian-cli` when the task needs:

- vault search
- note creation or append actions
- property reads or writes
- backlinks or tag inspection
- interaction with a running Obsidian instance

This skill owns live vault operations.

## `obsidian-bases`

Use `obsidian-bases` when working with `.base` files, structured note views, filters, formulas, or Base-powered dashboards.

This skill owns `.base` schema correctness.

## `json-canvas`

Use `json-canvas` when creating or editing `.canvas` files, note maps, or visual canvases.

This skill owns `.canvas` structure and edge/node integrity.

## `defuddle`

Use `defuddle` before ingest when a webpage should become a clean Markdown source note.

Use it to reduce clutter and preserve the source layer in a vault-friendly format.

If `defuddle` is unavailable, state that limitation before using a weaker fallback.

## `anysearch`

Use `anysearch` as an optional external search companion.

Good fit:

- fresh-checks for current, contested, or high-impact claims
- source discovery before ingest
- evidence-gap investigation during `audit -> lint`
- vertical searches for domains such as code, finance, academic, legal, business, IP, and security
- batch search for several independent source-discovery questions
- URL extraction when AnySearch is already the chosen search path

Do not use it for:

- local vault search
- private vault content search
- queries containing credentials, private notes, personal data, or business-sensitive details unless the user explicitly approves the disclosure

Routing rules:

- Use `obsidian-cli` for local vault search.
- Use `defuddle` for ordinary webpage cleanup when the user already provided a URL.
- Use `anysearch` when the task needs external discovery, freshness, vertical search, or batch search.
- Treat AnySearch results as candidate sources; route durable material back through the source-note and evidence workflow before writing knowledge notes.
